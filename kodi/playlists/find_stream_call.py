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

# 2. Bundle nach Stream-/Playout-URL durchsuchen
bundle_url = "https://play.waipu.tv/ui/App-LCOOEI3D.js"
req_b = urllib.request.Request(bundle_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req_b, context=ctx) as r:
    bundle_text = r.read().decode("utf-8", errors="ignore")

print("--- Gefundene Stream-/Playout-Snippets im Bundle ---")
patterns = [
    r'stream-url-provider[^\s"\'`)]*',
    r'playout-url-provider[^\s"\'`)]*',
    r'https?://[a-zA-Z0-9.-]+\.waipu\.[a-z0-9/_-]*stream[a-zA-Z0-9/_-]*',
    r'https?://[a-zA-Z0-9.-]+\.wpstr\.[a-z0-9/_-]*stream[a-zA-Z0-9/_-]*'
]

candidates = set()
for p in patterns:
    for m in re.findall(p, bundle_text, re.IGNORECASE):
        candidates.add(m)

for c in sorted(candidates):
    print(" ", c)

# 3. Teste reale Playout-Anfragen für 'ard'
test_endpoints = [
    "https://stream-url-provider.waipu.tv/api/v1/stream-url?stationId=ard",
    "https://stream-url-provider.waipu.tv/api/stream-url?stationId=ard",
    "https://playout.waipu.tv/api/v1/playout-url?stationId=ard",
    "https://tuner.wpstr.tv/v1/streams/ard",
    "https://tuner.wpstr.tv/api/v1/streams/ard"
]

print("\n--- Teste Playout-Endpunkte für 'ard' ---")
headers = {
    "Authorization": f"Bearer {access_token}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "*/*"
}

for ep in test_endpoints:
    try:
        req = urllib.request.Request(ep, headers=headers)
        with urllib.request.urlopen(req, context=ctx) as r:
            body = r.read().decode("utf-8")
            print(f"[OK 200] {ep} ->\n{body}\n")
            break
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")[:100]
        print(f"[{e.code}] {ep} -> {body}")
    except Exception as ex:
        print(f"[ERR] {ep} -> {ex}")
