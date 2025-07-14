# generar_radio_player.py
"""
Genera un bonito reproductor HTML para la radio y lo guarda en /static/radio_player.html
"""

import os
from textwrap import dedent
from urllib.parse import quote
import config  # Asegúrate de que este script vive en la misma carpeta que config.py

# === 1.  Datos básicos =======================================================
# Si aún no has añadido tu stream a config.py, ponlo aquí:
RADIO_STREAM_URL = getattr(config, "RADIO_STREAM_URL", "http://74.208.78.4:8000/radio.mp3")

# Carpeta /static (reutilizamos la ruta donde está canciones.json)
STATIC_DIR = os.path.dirname(config.CANCIONES_JSON)
os.makedirs(STATIC_DIR, exist_ok=True)

# Construir URL para NowPlaying de AzuraCast
NOWPLAYING_API = (
    f"{config.AZURACAST_API_URL}/nowplaying/"
    f"{quote(config.STATION_SHORT_NAME)}"
    f"?api_key={quote(config.AZURACAST_API_KEY)}"
)

# === 2.  Plantilla HTML con CSS + JS (AJAX) ==================================
html = dedent(f"""\
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>Venus Radio – En Vivo</title>
      <link href="https://fonts.googleapis.com/css2?family=Rubik:wght@400;700&display=swap" rel="stylesheet" />
      <style>
        *{{box-sizing:border-box}}
        body{{
          margin:0;
          font-family:'Rubik',sans-serif;
          background:linear-gradient(135deg,#ffe4ec,#ffd3f3);
          display:flex;align-items:center;justify-content:center;min-height:100vh;
        }}
        .player{{
          background:#fff;border-radius:25px;padding:40px 30px;text-align:center;
          box-shadow:0 10px 30px rgba(0,0,0,.15);max-width:450px;width:90%;
        }}
        .cover{{width:100%;max-width:250px;border-radius:20px;box-shadow:0 4px 20px rgba(255,77,166,.3);margin-bottom:20px}}
        .song-title{{font-size:1.5em;font-weight:700;color:#ff4da6;margin:10px 0 5px}}
        .artist{{font-size:1em;color:#666;margin-bottom:15px}}
        .progress{{height:10px;background:#ffd3f3;border-radius:5px;overflow:hidden;margin:15px 0}}
        .progress-bar{{height:100%;width:0%;background:#ff4da6;transition:width .5s}}
        .meta{{font-size:.9em;color:#999}}
        .list{{margin-top:20px;text-align:left}}
        .list p{{margin:5px 0}}
        audio{{display:none}}
      </style>
    </head>
    <body>
      <div class="player">
        <img id="cover" class="cover" src="https://i.imgur.com/8swyE6J.png" alt="Carátula">
        <div id="title" class="song-title">Cargando…</div>
        <div id="artist" class="artist">Conectando…</div>

        <div class="progress"><div id="bar" class="progress-bar"></div></div>
        <div id="time" class="meta">0:00 / 0:00</div>

        <div class="list">
          <p><strong>Anterior:</strong> <span id="prev">-</span></p>
          <p><strong>Siguiente:</strong> <span id="next">-</span></p>
        </div>

        <audio id="radio" autoplay src="{RADIO_STREAM_URL}"></audio>
      </div>

      <script>
        const API  = "{NOWPLAYING_API}";
        const cover = document.getElementById("cover");
        const title = document.getElementById("title");
        const artist = document.getElementById("artist");
        const prev  = document.getElementById("prev");
        const next  = document.getElementById("next");
        const time  = document.getElementById("time");
        const bar   = document.getElementById("bar");

        function fmt(t){{
          const m=Math.floor(t/60),s=Math.floor(t%60);
          return m+":"+(s<10?'0':'')+s;
        }}

        async function tick(){{
          try{{
            const rsp = await fetch(API);
            if(!rsp.ok) throw new Error(rsp.status);
            const data = await rsp.json();
            const np   = data.now_playing;
            title.textContent  = np.song.title  || "Sin título";
            artist.textContent = np.song.artist || "Sin artista";
            cover.src = np.song.art || "https://i.imgur.com/8swyE6J.png";
            prev.textContent  = (data.song_history[0]?.song?.title) || "-";
            next.textContent  = (data.playing_next?.song?.title)   || "-";

            const dur = np.duration || 0, elap = np.elapsed || 0;
            time.textContent = fmt(elap)+" / "+fmt(dur);
            bar.style.width  = dur? (elap/dur*100)+"%":"0%";
          }}catch(e){{
            console.error("meta error",e);
          }}
        }}
        tick(); setInterval(tick,5000);
      </script>
    </body>
    </html>
    """)

# === 3.  Guardar =============================================================
out_file = os.path.join(STATIC_DIR, "radio_player.html")
with open(out_file, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ Reproductor generado en: {out_file}")
