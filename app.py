from flask import Flask, render_template, request, jsonify, send_file, send_from_directory, session, redirect, url_for
from flask_socketio import SocketIO
import os
import json
import time
import logging
from datetime import timedelta, datetime
from functools import wraps
from config import (
    CANCIONES_JSON,
    VOTOS_JSON,
    PLAYLIST_FILE,
    ADMIN_LOGOUT_TIMEOUT,
    APP_SECRET_KEY,
    MEDIA_PUBLIC_URL_PREFIX,
    PROGRAMACION_JSON,
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    MEDIA_BASE_PATH,
    VOTACION_COOLDOWN_SECONDS
)
from fetch import actualizar_canciones_json

app = Flask(__name__, static_folder='static')
app.secret_key = APP_SECRET_KEY
app.permanent_session_lifetime = timedelta(seconds=ADMIN_LOGOUT_TIMEOUT)

logging.basicConfig(level=logging.INFO)
logging.getLogger('engineio').setLevel(logging.WARNING)
logging.getLogger('socketio').setLevel(logging.WARNING)

socketio = SocketIO(app, cors_allowed_origins="*")

last_update_timestamp = 0

def cargar_json(path, default=None):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.warning(f"Error cargando JSON {path}: {e}")
        return default if default is not None else {}

def guardar_json(path, data):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Error guardando JSON {path}: {e}")

def generate_playlist():
    canciones = cargar_json(CANCIONES_JSON, [])
    votos = cargar_json(VOTOS_JSON, {})
    for c in canciones:
        c['votos'] = votos.get(c.get('archivo', ''), 0)
    canciones_ordenadas = sorted(canciones, key=lambda x: x['votos'], reverse=True)
    top10 = canciones_ordenadas[:10]
    try:
        os.makedirs(os.path.dirname(PLAYLIST_FILE), exist_ok=True)
        with open(PLAYLIST_FILE, 'w', encoding='utf-8') as f:
            for c in top10:
                f.write(c.get('archivo', '') + '\n')
    except Exception as e:
        logging.error(f"Error generando playlist: {e}")

def generate_playlist_with_cooldown():
    global last_update_timestamp
    now = time.time()
    if now - last_update_timestamp >= VOTACION_COOLDOWN_SECONDS:
        generate_playlist()
        last_update_timestamp = now
        return True
    return False

@app.route('/media/<path:filename>')
def serve_media(filename):
    try:
        return send_from_directory(MEDIA_BASE_PATH, filename)
    except Exception as e:
        logging.error(f"Error sirviendo media {filename}: {e}")
        return "Archivo no encontrado", 404

@app.route('/')
def index():
    try:
        canciones = cargar_json(CANCIONES_JSON, [])
        votos = cargar_json(VOTOS_JSON, {})
        for c in canciones:
            c['votos'] = votos.get(c.get('archivo', ''), 0)
        canciones_ordenadas = sorted(canciones, key=lambda x: x['votos'], reverse=True)
        top10 = canciones_ordenadas[:10]
        return render_template('index.html', canciones=canciones, top10=top10, votos=votos, MEDIA_PUBLIC_URL_PREFIX=MEDIA_PUBLIC_URL_PREFIX)
    except Exception as e:
        logging.error(f"Error en index(): {e}")
        return "Error interno del servidor", 500

@app.route('/vote', methods=['POST'])
def vote():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "Formato inválido"}), 400
        archivo = data.get('archivo')
        if not archivo:
            return jsonify({"message": "Archivo inválido"}), 400
        votos = cargar_json(VOTOS_JSON, {})
        votos[archivo] = votos.get(archivo, 0) + 1
        guardar_json(VOTOS_JSON, votos)
        generate_playlist_with_cooldown()
        canciones = cargar_json(CANCIONES_JSON, [])
        for c in canciones:
            c['votos'] = votos.get(c.get('archivo', ''), 0)
        canciones_ordenadas = sorted(canciones, key=lambda x: x['votos'], reverse=True)
        top10 = canciones_ordenadas[:10]
        socketio.emit('update_votes', {'top10': top10})
        return jsonify({"success": True, "archivo": archivo, "votos_actuales": votos[archivo]})
    except Exception as e:
        logging.error(f"Error en /vote: {e}")
        return jsonify({"success": False, "message": "Error interno"}), 500

@app.route('/get_results')
def get_results():
    try:
        query = request.args.get('q', '').strip()
        canciones = cargar_json(CANCIONES_JSON, [])
        votos = cargar_json(VOTOS_JSON, {})
        for c in canciones:
            c['votos'] = votos.get(c.get('archivo', ''), 0)
        if query == "":
            canciones_ordenadas = sorted(canciones, key=lambda x: x['votos'], reverse=True)
            top10 = canciones_ordenadas[:10]
        elif len(query) < 3:
            top10 = []
        else:
            query_lower = query.lower()
            canciones_filtradas = [c for c in canciones if query_lower in c.get('titulo', '').lower() or query_lower in c.get('artista', '').lower()]
            canciones_ordenadas = sorted(canciones_filtradas, key=lambda x: x['votos'], reverse=True)
            top10 = canciones_ordenadas[:10]
        return jsonify({'top10': top10})
    except Exception as e:
        logging.error(f"Error en /get_results: {e}")
        return jsonify({'top10': []})

@app.route('/fetch_songs')
def fetch_songs():
    try:
        actualizar_canciones_json()
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error en /fetch_songs: {e}")
        return jsonify({'success': False}), 500

@app.route('/playlist_top10.m3u')
def playlist_top10():
    try:
        if os.path.exists(PLAYLIST_FILE):
            return send_file(PLAYLIST_FILE, mimetype='audio/x-mpegurl')
        else:
            return "Playlist no encontrada", 404
    except Exception as e:
        logging.error(f"Error en /playlist_top10.m3u: {e}")
        return "Error interno", 500

@app.route('/time_until_next_update')
def time_until_next_update():
    try:
        now = time.time()
        remaining = VOTACION_COOLDOWN_SECONDS - (now - last_update_timestamp)
        if remaining < 0:
            remaining = 0
        return jsonify({'seconds_until_next_update': int(remaining)})
    except Exception as e:
        logging.error(f"Error en /time_until_next_update: {e}")
        return jsonify({'seconds_until_next_update': 0})

@app.route('/programa_actual')
def programa_actual():
    try:
        ahora = datetime.now().strftime("%H:%M")
        dia_actual = datetime.now().strftime("%A").lower()
        programacion = cargar_json(PROGRAMACION_JSON, {})
        for programa in programacion.get(dia_actual, []):
            if programa.get("inicio") <= ahora <= programa.get("fin"):
                return jsonify(programa)
        return jsonify({})
    except Exception as e:
        logging.error(f"Error en /programa_actual: {e}")
        return jsonify({})

@app.route('/nowplaying')
def nowplaying():
    try:
        canciones = cargar_json(CANCIONES_JSON, [])
        votos = cargar_json(VOTOS_JSON, {})
        canciones_ordenadas = sorted(canciones, key=lambda x: votos.get(x.get('archivo', ''), 0), reverse=True)
        cancion_actual = canciones_ordenadas[0] if canciones_ordenadas else {}
        ahora = datetime.now().strftime("%H:%M")
        dia_actual = datetime.now().strftime("%A").lower()
        programa_actual = {}
        for p in cargar_json(PROGRAMACION_JSON, {}).get(dia_actual, []):
            if p.get("inicio") <= ahora <= p.get("fin"):
                programa_actual = p
                break
        caratula = cancion_actual.get('caratula') or f"{MEDIA_PUBLIC_URL_PREFIX}/default_cover.png"
        archivo = cancion_actual.get('archivo', '')
        if archivo and not archivo.startswith('http'):
            archivo = f"{MEDIA_PUBLIC_URL_PREFIX}/{archivo}"
        return jsonify({
            "song": {
                "title": cancion_actual.get('titulo', 'Desconocido'),
                "artist": cancion_actual.get('artista', 'Varios'),
                "art": caratula,
                "archivo": archivo
            },
            "programa_actual": programa_actual,
            "elapsed": 0,
            "duration": 180,
            "playlist_name": "Venus Radio",
            "song_history": [],
            "playing_next": None
        })
    except Exception as e:
        logging.error(f"Error en /nowplaying: {e}")
        return jsonify({})

@app.route('/radio')
def radio_player():
    return send_file("static/radio_player.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Datos inválidos"}), 400
        if data.get("email") == ADMIN_EMAIL and data.get("password") == ADMIN_PASSWORD:
            session['logged_in'] = True
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "Email o contraseña incorrectos"}), 401

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/admin')
@login_required
def admin_panel():
    return render_template('admin.html',
                           votos=cargar_json(VOTOS_JSON, {}),
                           canciones=cargar_json(CANCIONES_JSON, []),
                           programacion=cargar_json(PROGRAMACION_JSON, {}))

@app.route('/reset_votes', methods=['POST'])
@login_required
def reset_votes():
    try:
        votos_actuales = cargar_json(VOTOS_JSON, {})
        guardar_json(f"{VOTOS_JSON}.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}", votos_actuales)
        guardar_json(VOTOS_JSON, {})
        generate_playlist()
        socketio.emit('update_votes', {'top10': []})
        return jsonify({"success": True})
    except Exception as e:
        logging.error(f"Error al reiniciar votos: {e}")
        return jsonify({"success": False}), 500

@app.route('/system_status')
def system_status():
    try:
        ahora = datetime.now().strftime("%H:%M:%S")
        dia_actual = datetime.now().strftime("%A").lower()
        programa_actual = {}
        for p in cargar_json(PROGRAMACION_JSON, {}).get(dia_actual, []):
            if p.get("inicio") <= ahora <= p.get("fin"):
                programa_actual = p
                break
        return jsonify({
            "hora_actual": ahora,
            "dia_actual": dia_actual.capitalize(),
            "programa_actual": programa_actual
        })
    except Exception as e:
        logging.error(f"Error en /system_status: {e}")
        return jsonify({})

@app.route('/api/programas', methods=['GET', 'POST'])
@login_required
def api_programas():
    try:
        dia_actual = datetime.now().strftime("%A").lower()
        if request.method == 'GET':
            return jsonify(cargar_json(PROGRAMACION_JSON, {}).get(dia_actual, []))
        data = request.get_json()
        programacion = cargar_json(PROGRAMACION_JSON, {})
        programacion[dia_actual] = data
        guardar_json(PROGRAMACION_JSON, programacion)
        return jsonify({"success": True})
    except Exception as e:
        logging.error(f"Error en /api/programas: {e}")
        return jsonify({"success": False}), 500

@app.route('/api/canciones', methods=['GET', 'POST'])
@login_required
def api_canciones():
    try:
        if request.method == 'GET':
            return jsonify(cargar_json(CANCIONES_JSON, []))
        guardar_json(CANCIONES_JSON, request.get_json())
        return jsonify({"success": True})
    except Exception as e:
        logging.error(f"Error en /api/canciones: {e}")
        return jsonify({"success": False}), 500

@app.route('/api/upload', methods=['POST'])
@login_required
def api_upload():
    try:
        file = request.files.get('file')
        if not file or file.filename == '':
            return jsonify({"error": "Archivo no recibido"}), 400
        filename = file.filename.replace(" ", "_")
        filepath = os.path.join(MEDIA_BASE_PATH, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)
        return jsonify({"url": f"{MEDIA_PUBLIC_URL_PREFIX}/{filename}"})
    except Exception as e:
        logging.error(f"Error en /api/upload: {e}")
        return jsonify({"error": "Error al subir archivo"}), 500

@app.route('/api/emit_metadata', methods=['POST'])
@login_required
def api_emit_metadata():
    try:
        data = request.get_json()
        socketio.emit("metadata_update", {
            "titulo": data.get("titulo"),
            "artista": data.get("artista"),
            "caratula": data.get("caratula")
        })
        return jsonify({"success": True})
    except Exception as e:
        logging.error(f"Error en /api/emit_metadata: {e}")
        return jsonify({"success": False}), 500

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
