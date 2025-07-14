import json
import os

# Rutas de tus archivos
VOTOS_JSON = "/var/azuracast/www/votacion/data/votos.json"
CANCIONES_JSON = "/var/azuracast/www/votacion/static/canciones.json"

def cargar_json(path, default=None):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] No se pudo cargar {path}: {e}")
        return default if default is not None else []

def main():
    print("🔍 Verificando archivos de votación...\n")

    canciones = cargar_json(CANCIONES_JSON, [])
    votos = cargar_json(VOTOS_JSON, {})

    if not canciones:
        print("❌ canciones.json está vacío o no válido.")
        return

    if not votos:
        print("⚠️ votos.json está vacío. Aún no se ha votado o no se ha guardado correctamente.")
    else:
        print(f"✅ votos.json cargado con {len(votos)} votos.\n")

    # Asignar votos a cada canción
    for c in canciones:
        c['votos'] = votos.get(c['archivo'], 0)

    canciones_ordenadas = sorted(canciones, key=lambda x: x['votos'], reverse=True)
    top10 = canciones_ordenadas[:10]

    print("🎵 TOP 10 canciones más votadas:\n")
    for i, c in enumerate(top10, 1):
        print(f"{i}. {c['titulo']} - {c['artista']}  ({c['votos']} votos) → archivo: {c['archivo']}")

    print("\n✅ Verificación completada.")

if __name__ == "__main__":
    main()
