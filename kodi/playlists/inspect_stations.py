import urllib.request
import urllib.parse
import json
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 1. Token holen
import xml.etree.ElementTree as ET, os
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

req = urllib.request.Request(token_url, data=payload, headers={
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "okhttp/4.9.0",
    "Accept": "application/json"
})
with urllib.request.urlopen(req, context=ctx) as resp:
    access_token = json.loads(resp.read().decode()).get("access_token")

# 2. Genauere Fehlermeldung von /contents/stations abfangen
headers = {
    "Authorization": f"Bearer {access_token}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json"
}

print("--- Fehler-Details von /contents/stations ---")
try:
    req_s = urllib.request.Request("https://tuner.wpstr.tv/contents/stations", headers=headers)
    with urllib.request.urlopen(req_s, context=ctx) as r:
        print("[200 OK]:", r.read().decode("utf-8")[:200])
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8") if hasattr(e, "read") else ""
    print(f"HTTP {e.code}: {body}")

# 3. Bundle nach /contents/ und /stations durchsuchen
print("\n--- Code-Ausschnitte aus dem Bundle ---")
bundle_url = "https://play.waipu.tv/ui/App-LCOOEI3D.js"
req_b = urllib.request.Request(bundle_url, headers=headers)
with urllib.request.urlopen(req_b, context=ctx) as r:
    bundle_text = r.read().decode("utf-8", errors="ignore")

# Zeige Kontext um "contents/stations" oder "tuner.wpstr.tv"
for match in re.finditer(r'(?:contents/stations|tuner\.wpstr\.tv[^\s"\'`)]*)', bundle_text):
    start = max(0, match.start() - 100)
    end = min(len(bundle_text), match.end() + 100)
    print("Snippet:", bundle_text[start:end])
    print("-" * 50)
