import urllib.request
import re
import ssl
import json
import xml.etree.ElementTree as ET
import os

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 1. Bundle laden
bundle_url = "https://play.waipu.tv/ui/App-LCOOEI3D.js"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
req = urllib.request.Request(bundle_url, headers=headers)
with urllib.request.urlopen(req, context=ctx) as r:
    bundle_text = r.read().decode("utf-8", errors="ignore")

# 2. Config-Block isolieren
pos = bundle_text.find("TUNER_BASE_URL")
if pos != -1:
    config_chunk = bundle_text[max(0, pos-400):min(len(bundle_text), pos+600)]
    print("--- Gefundener Service-Konfigurationsblock ---")
    print(config_chunk, "\n")

# 3. Token holen
settings_path = os.path.expanduser("~/.kodi/userdata/addon_data/pvr.waipu/settings.xml")
dev_id, token = "cd8c2238-4e43-481b-8665-472ae21ae816", ""
if os.path.exists(settings_path):
    tree = ET.parse(settings_path)
    for s in tree.getroot().findall("setting"):
        if s.get("id") == "device_id_uuid4": dev_id = s.text
        elif s.get("id") == "refresh_token": token = s.text

import urllib.parse
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
    print("[Token OK]")

# 4. Relevante Service-URLs auf waipu.tv und exaring.de testen
api_headers = {
    "Authorization": f"Bearer {access_token}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json"
}

services_to_test = [
    "https://epg.waipu.tv/api/stations",
    "https://epg.waipu.tv/api/v1/stations",
    "https://epg.exaring.de/api/stations",
    "https://channels.waipu.tv/api/channels",
    "https://channels.exaring.de/api/channels",
    "https://tuner.wpstr.tv/contents/stations?stationType=TV",
    "https://tuner.wpstr.tv/contents/stations?type=linear",
    "https://tuner.wpstr.tv/stations"
]

print("\n--- Teste Microservice-Endpunkte ---")
for s_url in services_to_test:
    try:
        req_s = urllib.request.Request(s_url, headers=api_headers)
        with urllib.request.urlopen(req_s, context=ctx) as res:
            data = res.read().decode("utf-8")
            print(f"[OK 200]: {s_url} -> {len(data)} Bytes")
            print("  Vorschau:", data[:150], "\n")
    except urllib.error.HTTPError as e:
        print(f"[{e.code}]: {s_url}")
    except Exception as ex:
        print(f"[ERR]: {s_url} -> {ex}")
