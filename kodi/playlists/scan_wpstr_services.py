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

# 2. Bundle nach der Service-Config durchsuchen
bundle_url = "https://play.waipu.tv/ui/App-LCOOEI3D.js"
req_b = urllib.request.Request(bundle_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req_b, context=ctx) as r:
    bundle_text = r.read().decode("utf-8", errors="ignore")

print("--- Extrahierte Service-Templates aus dem Bundle ---")
for m in re.finditer(r'([A-Z_]+_BASE_URL|[A-Z_]+_URL)\s*:\s*[`"\']([^`"\']+)[\'"`]', bundle_text):
    print(f"  {m.group(1)}: {m.group(2)}")

# 3. Teste potentielle Endpunkte auf wpstr.tv
headers = {
    "Authorization": f"Bearer {access_token}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json"
}

endpoints_to_test = [
    "https://epg.wpstr.tv/api/channels",
    "https://epg.wpstr.tv/api/v1/channels",
    "https://epg.wpstr.tv/api/stations",
    "https://channels.wpstr.tv/api/channels",
    "https://stream-url-provider.wpstr.tv/api/stream-url",
    "https://permission-management.wpstr.tv/api/permissions",
    "https://tuner.wpstr.tv/programs",
    "https://tuner.wpstr.tv/channels/linear"
]

print("\n--- Teste wpstr.tv Endpunkte ---")
for ep in endpoints_to_test:
    try:
        req_test = urllib.request.Request(ep, headers=headers)
        with urllib.request.urlopen(req_test, context=ctx) as r:
            body = r.read().decode("utf-8")
            print(f"[OK 200] {ep} -> {len(body)} Bytes")
            print("  Vorschau:", body[:160], "\n")
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="ignore")[:80] if hasattr(e, "read") else ""
        print(f"[{e.code}] {ep} -> {err}")
    except Exception as ex:
        print(f"[ERR] {ep} -> {ex}")
