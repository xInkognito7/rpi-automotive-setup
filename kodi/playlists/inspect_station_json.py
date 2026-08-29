import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET
import os
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 1. Token holen
settings_path = os.path.expanduser("~/.kodi/userdata/addon_data/pvr.waipu/settings.xml")
dev_id, token = "cd8c2238-4e43-481b-8665-472ae21ae816", ""
if os.path.exists(settings_path):
    tree = ET.parse(settings_path)
    for s in tree.getroot().findall("setting"):
        if s.get("id") == "device_id_uuid4": dev_id = s.text
        elif s.get("id") == "refresh_token": token = s.text

token_url = "https://auth.waipu.tv/oauth/token"
payload = urllib.parse.urlencode({
    "grant_type": "refresh_token",
    "refresh_token": token,
    "client_id": "waipu",
    "waipu_device_id": dev_id
}).encode("utf-8")

req_t = urllib.request.Request(token_url, data=payload, headers={
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "okhttp/4.9.0",
    "Accept": "application/json"
})
with urllib.request.urlopen(req_t, context=ctx) as resp:
    access_token = json.loads(resp.read().decode()).get("access_token")

# 2. Stations abrufen
stations_url = "https://user-stations.waipu.tv/api/stations"
req = urllib.request.Request(stations_url, headers={
    "Authorization": f"Bearer {access_token}",
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/vnd.waipu.user-stations-stations.v1+json"
})

with urllib.request.urlopen(req, context=ctx) as r:
    data = json.loads(r.read().decode("utf-8"))

# Erstes Element (z. B. ARD / Pastewka) komplett formatiert ausgeben
stations = data if isinstance(data, list) else data.get("stations", data.get("channels", []))

print(f"Insgesamt {len(stations)} Sender gefunden.\n")
print("--- Vollständiges JSON für Sender 1 ---")
print(json.dumps(stations[0], indent=2))

if len(stations) > 1:
    print("\n--- Vollständiges JSON für Sender 2 ---")
    print(json.dumps(stations[1], indent=2))
