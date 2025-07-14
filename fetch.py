import os
import json
import mutagen
import requests
import urllib.parse
import unicodedata
from config import (
    MEDIA_BASE_PATH,
    MEDIA_PUBLIC_URL_PREFIX,
    CANCIONES_JSON,
    LASTFM_API_KEY,
    LASTFM_API_URL
)

def limpiar_texto(texto):
    try:
        texto = str(texto)
        texto = unicodedata.normalize('NFKD', texto).encode('utf-8', 'replace').decode('utf-8')
        texto = texto.replace('\uFFFD', '')
        return texto.strip()
    except Exception:
        return "Desconocido"

def obtener_portada(artista, titulo):
    try:
        params = {
            "method": "track.getInfo",
            "api_key": LASTFM_API_KEY,
            "artist": artista,
            "track": titulo,
            "format": "json"
        }
        r = requests.get(LASTFM_API_URL, params=params, timeout=5)
        data = r.json()
        imagenes = data.get("track", {}).get("album", {}).get("image", [])
        if imagenes:
            url = imagenes[-1].get('#text', '')
            if url:
                print(f"  [Portada encontrada] {titulo} - {artista}")
                return url
    except Exception as e:
        print(f"  [Error portadas] {titulo} - {artista}: {e}")
    print(f"  [Portada no encontrada] Usando placeholder para {titulo} - {artista}")
    return "https://i.imgur.com/8swyE6J.png"

def extraer_datos(mp3_path):
    try:
        audio = mutagen.File(mp3_path, easy=True)
        titulo = audio.get('title', [os.path.basename(mp3_path).replace('.mp3', '')])[0]
        artista = audio.get('artist', ['Desconocido'])[0]
    except Exception as e:
        print(f"  [Error metadatos] {mp3_path}: {e}")
        titulo = os.path.basename(mp3_path).replace('.mp3', '')
        artista = "Desconocido"
    return limpiar_texto(titulo), limpiar_texto(artista)

def generar_json():
    if os.path.exists(CANCIONES_JSON):
        with open(CANCIONES_JSON, 'r', encoding='utf-8') as f:
            canciones = json.load(f)
        archivos_existentes = {c['archivo'] for c in canciones}
        print(f"🎵 Cargando {len(canciones)} canciones existentes para evitar duplicados")
    else:
        canciones = []
        archivos_existentes = set()
        print("🎵 No se encontró archivo previo, creando lista nueva")

    print(f"Iniciando escaneo de música en: {MEDIA_BASE_PATH}")
    nuevas_canciones = 0

    for root, _, files in os.walk(MEDIA_BASE_PATH):
        for file in files:
            if file.lower().endswith(".mp3"):
                ruta_completa = os.path.join(root, file)
                ruta_relativa = os.path.relpath(ruta_completa, MEDIA_BASE_PATH)
                ruta_codificada = urllib.parse.quote(ruta_relativa)
                url_publica = f"{MEDIA_PUBLIC_URL_PREFIX}/{ruta_codificada}"

                if url_publica in archivos_existentes:
                    print(f" → Saltando ya existente: {url_publica}")
                    continue

                print(f"Procesando archivo nuevo: {file}")
                titulo, artista = extraer_datos(ruta_completa)
                cover = obtener_portada(artista, titulo)
                canciones.append({
                    "titulo": titulo,
                    "artista": artista,
                    "archivo": url_publica,
                    "cover": cover
                })
                nuevas_canciones += 1
                print(f" → Añadida canción: '{titulo}' de '{artista}'")

    os.makedirs(os.path.dirname(CANCIONES_JSON), exist_ok=True)
    with open(CANCIONES_JSON, "w", encoding="utf-8") as f:
        json.dump(canciones, f, indent=2, ensure_ascii=False)

    print(f"✅ Archivo generado: {CANCIONES_JSON} con {len(canciones)} canciones (añadidas {nuevas_canciones} nuevas).")

def actualizar_canciones_json():
    generar_json()

def listar_canciones():
    if not os.path.exists(CANCIONES_JSON):
        print("No existe el archivo de canciones.")
        return
    with open(CANCIONES_JSON, 'r', encoding='utf-8') as f:
        canciones = json.load(f)
    for c in canciones:
        print(f"{c['titulo']} - {c['artista']} [{c['archivo']}]")

if __name__ == "__main__":
    generar_json()

