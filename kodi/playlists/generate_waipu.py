import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET
import os
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 1. Token & Device-ID aus Kodi-Settings laden
settings_path = os.path.expanduser("~/.kodi/userdata/addon_data/pvr.waipu/settings.xml")
dev_id = "cd8c2238-4e43-481b-8665-472ae21ae816"
token = ""

if os.path.exists(settings_path):
    tree = ET.parse(settings_path)
    for s in tree.getroot().findall("setting"):
        if s.get("id") == "device_id_uuid4": dev_id = s.text
        elif s.get("id") == "refresh_token": token = s.text

# 2. Access Token abrufen
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
    print("[1/2] Access-Token erfolgreich bezogen!")

# 3. Den genauen Accept-Header von user-stations ermitteln und Sender abrufen
stations_url = "https://user-stations.waipu.tv/api/stations"

# Ermittle den geforderten Accept-Header
accept_header = "application/json"
try:
    req_probe = urllib.request.Request(stations_url, headers={
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*"
    })
    with urllib.request.urlopen(req_probe, context=ctx) as r:
        raw_data = r.read().decode("utf-8")
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", errors="ignore")
    # Extrahiere Header-MIME-Type aus Fehlermeldung
    if "Acceptable representations:" in body:
        import re
        match = re.search(r'\[([^\]]+)\]', body)
        if match:
            # Ersten passenden Vendor-Header nehmen
            accept_header = match.group(1).split(",")[0].strip()
            print(f"Setze speziellen Header: Accept = {accept_header}")

# Eigentlicher Abruf der Senderliste
req_stations = urllib.request.Request(stations_url, headers={
    "Authorization": f"Bearer {access_token}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": accept_header
})

with urllib.request.urlopen(req_stations, context=ctx) as r:
    data = json.loads(r.read().decode("utf-8"))

stations = data if isinstance(data, list) else data.get("stations", data.get("channels", data.get("items", [])))
print(f"[2/2] {len(stations)} Sender von user-stations empfangen!")

# 4. waipu.m3u8 schreiben
m3u_file = "/home/pi/waipu.m3u8"
with open(m3u_file, "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    for s in stations:
        name = s.get("displayName") or s.get("name") or s.get("title") or "Sender"
        sid = s.get("id") or s.get("stationId") or ""
        
        # Logo ermitteln
        logo = s.get("logoUrl") or s.get("logo") or ""
        if not logo and "images" in s and isinstance(s["images"], dict):
            logo = s["images"].get("logo", "")
        if logo and not logo.startswith("http"):
            logo = f"https://images.wpstr.tv{logo}"

        # Stream-URL ermitteln / HLS Provider Target
        stream_url = s.get("streamUrl") or s.get("playUrl") or ""
        if not stream_url and "links" in s and isinstance(s["links"], dict):
            stream_url = s["links"].get("stream", "")
        if not stream_url and sid:
            stream_url = f"https://playout-url-provider.waipu.tv/api/playout-url?stationId={sid}"

        f.write(f'#EXTINF:-1 tvg-id="{sid}" tvg-name="{name}" tvg-logo="{logo}" group-title="Waipu.tv",{name}\n')
        f.write(f'{stream_url}|Authorization=Bearer {access_token}&User-Agent=okhttp/4.9.0\n')

print(f"\n[ERFOLG] /home/pi/waipu.m3u8 mit {len(stations)} Sendern geschrieben!")
