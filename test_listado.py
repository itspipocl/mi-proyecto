import os
from config import MEDIA_BASE_PATH

def listar_mp3():
    print(f"🔍 Explorando: {MEDIA_BASE_PATH}")
    encontrados = 0
    for root, _, files in os.walk(MEDIA_BASE_PATH):
        print(f"📁 Carpeta: {root}")
        for f in files:
            if f.lower().endswith(".mp3"):
                ruta_completa = os.path.join(root, f)
                print(f"🎵 MP3 encontrado: {ruta_completa}")
                encontrados += 1
    if encontrados == 0:
        print("❌ No se encontraron archivos MP3.")
    else:
        print(f"✅ Se encontraron {encontrados} archivos MP3.")

if __name__ == "__main__":
    listar_mp3()
