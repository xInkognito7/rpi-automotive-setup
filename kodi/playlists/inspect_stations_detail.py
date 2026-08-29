import urllib.request
import urllib.parse
import json
import ssl
import re
import xml.etree.ElementTree as ET
import os

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

# 2. Exakten Fehlerbody von /contents/stations abfangen
headers = {
    "Authorization": f"Bearer {access_token}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json"
}

print("--- Fehlertext von /contents/stations ---")
try:
    req = urllib.request.Request("https://tuner.wpstr.tv/contents/stations", headers=headers)
    with urllib.request.urlopen(req, context=ctx) as r:
        print("[200 OK]:", r.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    err_body = e.read().decode("utf-8", errors="ignore") if hasattr(e, "read") else ""
    print(f"Status: {e.code}")
    print(f"Header: {dict(e.headers)}")
    print(f"Body: {err_body}\n")

# 3. Den genauen Aufruf im Bundle suchen
bundle_url = "https://play.waipu.tv/ui/App-LCOOEI3D.js"
req_b = urllib.request.Request(bundle_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req_b, context=ctx) as r:
    bundle_text = r.read().decode("utf-8", errors="ignore")

# Kontext um "contents/stations" herum anzeigen
print("--- JavaScript-Kontext um contents/stations ---")
matches = [m.start() for m in re.finditer(r'contents/stations', bundle_text)]
for pos in matches:
    start = max(0, pos - 150)
    end = min(len(bundle_text), pos + 250)
    print(bundle_text[start:end])
    print("-" * 60)
