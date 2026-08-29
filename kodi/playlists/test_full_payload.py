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

# 2. X_() Definition im Bundle suchen
bundle_url = "https://play.waipu.tv/ui/App-LCOOEI3D.js"
req_b = urllib.request.Request(bundle_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req_b, context=ctx) as r:
    bundle_text = r.read().decode("utf-8", errors="ignore")

print("--- Definitionen rund um protocol / X_ ---")
matches = [m.start() for m in re.finditer(r'protocol:X_\(\)', bundle_text)]
for pos in matches:
    print(bundle_text[max(0, pos-200):min(len(bundle_text), pos+200)])
    print("-" * 50)

# 3. Teste vollständige Payloads
url = "https://stream-url-provider.waipu.tv/api/stream-url"

test_bodies = [
    # Variante 1: Full Web Payload HLS
    {
        "stream": {
            "station": "ard",
            "protocol": "HLS",
            "requestMuxInstrumentation": True,
            "processOutcomeField": True
        },
        "advertising": {
            "id": "00000000-0000-0000-0000-000000000000",
            "serverSideAdInsertion": True
        }
    },
    # Variante 2: Full Web Payload DASH
    {
        "stream": {
            "station": "ard",
            "protocol": "DASH",
            "requestMuxInstrumentation": True,
            "processOutcomeField": True
        },
        "advertising": {
            "id": "00000000-0000-0000-0000-000000000000",
            "serverSideAdInsertion": True
        }
    },
    # Variante 3: Minimal mit advertising
    {
        "stream": {
            "station": "ard",
            "protocol": "HLS"
        },
        "advertising": {
            "id": "00000000-0000-0000-0000-000000000000"
        }
    }
]

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/vnd.streamurlprovider.stream-url-request-v1+json",
    "Accept": "application/vnd.streamurlprovider.traditional-stream-url-v1+json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

print("\n--- Teste Payload-Varianten ---")
for i, b in enumerate(test_bodies, 1):
    try:
        req = urllib.request.Request(url, data=json.dumps(b).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, context=ctx) as r:
            body = r.read().decode("utf-8")
            print(f"[ERFOLG 200 OK] Variante {i}:")
            print(body)
            break
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="ignore")
        print(f"[HTTP {e.code}] Variante {i}: {err}")
