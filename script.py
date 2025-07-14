import requests
from config import AZURACAST_API_KEY, AZURACAST_BASE_URL, STATION_ID

HEADERS = {"Authorization": f"Bearer {AZURACAST_API_KEY}"}
url = f"{AZURACAST_BASE_URL}/station/{STATION_ID}/files"

r = requests.get(url, headers=HEADERS)
print("Status code:", r.status_code)
print("Response JSON:")
print(r.json())  # Esto debe mostrarte toda la data que devuelve AzuraCast
