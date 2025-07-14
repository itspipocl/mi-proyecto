APP_SECRET_KEY = "clave-super-secreta-123"

ADMIN_EMAIL = "felipeancatrio20@gmail.com"
ADMIN_PASSWORD = "FelipeA97-"

VOTOS_JSON = "/var/azuracast/www/votacion/data/votos.json"
COOLDOWN_JSON = "/var/azuracast/www/votacion/data/cooldowns.json"
CANCIONES_JSON = "/var/azuracast/www/votacion/static/canciones.json"

# Ruta física local donde están los MP3
MEDIA_BASE_PATH = "/var/lib/docker/volumes/azuracast_station_data/_data/venus_radio/media"

# Ruta pública para que el frontend acceda a los MP3
MEDIA_PUBLIC_URL_PREFIX = "http://74.208.78.4:5000/media"

PLAYLIST_FILE = "/var/azuracast/www/votacion/static/playlist_top10.m3u"

AZURACAST_API_KEY = "d1ff1a61beee3b5d:cbfb7c787596b0ec9c410549eb97c58c"
AZURACAST_API_URL = "https://streaming.venuseventos.com/api"
STATION_SHORT_NAME = "venus_radio"

LASTFM_API_KEY = "60d8c5b23ae0d2e47766a29f106ad698"
LASTFM_API_URL = "http://ws.audioscrobbler.com/2.0/"

VOTACION_COOLDOWN_SECONDS = 60
ADMIN_LOGOUT_TIMEOUT = 3600

# Nueva funcionalidad: archivo JSON con la programación de programas
PROGRAMACION_JSON = "/var/azuracast/www/votacion/data/programacion.json"
