import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET
import os
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 1. Access-Token holen
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
    print("[1/3] Bearer-Token bezogen!")

# 2. Exakten Fehlertext / Acceptable Representations von user-stations abfragen
stations_url = "https://user-stations.waipu.tv/api/stations"
candidate_headers = []

try:
    req_probe = urllib.request.Request(stations_url, headers={
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*"
    })
    with urllib.request.urlopen(req_probe, context=ctx) as r:
        pass
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", errors="ignore")
    print(f"Server-Rückmeldung bei 406:\n{body}\n")
    # Alle Typen aus den eckigen Klammern extrahieren
    match = re.search(r'\[([^\]]+)\]', body)
    if match:
        for item in match.group(1).split(","):
            candidate_headers.append(item.strip())

# Auch nach Vendor-Strings im Web-Bundle suchen
bundle_url = "https://play.waipu.tv/ui/App-LCOOEI3D.js"
req_b = urllib.request.Request(bundle_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req_b, context=ctx) as r:
    bundle_text = r.read().decode("utf-8", errors="ignore")

for v in set(re.findall(r'application/vnd\.waipu\.[a-zA-Z0-9.+_-]+', bundle_text)):
    candidate_headers.append(v)

print(f"[2/3] Teste {len(candidate_headers)} gefundene Accept-Header:\n{candidate_headers}\n")

# 3. Jeden Header durchprobieren
for h in candidate_headers:
    try:
        req_st = urllib.request.Request(stations_url, headers={
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": h
        })
        with urllib.request.urlopen(req_st, context=ctx) as r:
            res_body = r.read().decode("utf-8")
            print(f"[TREFFER 200 OK] Header '{h}' funktioniert!")
            print(f"Daten empfangen: {len(res_body)} Bytes")
            print("Vorschau:", res_body[:250])
            break
    except urllib.error.HTTPError as he:
        print(f"[Fail {he.code}] mit '{h}'")
    except Exception as ex:
        print(f"[ERR] mit '{h}': {ex}")
