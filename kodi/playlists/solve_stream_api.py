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

# 1. Token & Settings laden
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
    token_json = json.loads(resp.read().decode())
    access_token = token_json.get("access_token")
    # Device Token falls vorhanden
    device_token = token_json.get("device_token", dev_id)

# 2. X_() und Funktion im JS-Bundle suchen
bundle_url = "https://play.waipu.tv/ui/App-LCOOEI3D.js"
req_b = urllib.request.Request(bundle_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req_b, context=ctx) as r:
    bundle_text = r.read().decode("utf-8", errors="ignore")

print("--- Definition von X_ und Umgebung ---")
for m in re.finditer(r'(?:var\s+X_|function\s+X_|X_=\(\))', bundle_text):
    start = max(0, m.start() - 50)
    end = min(len(bundle_text), m.end() + 200)
    print(bundle_text[start:end])
    print("-" * 50)

# 3. Teste mit X-Device-Token und verschiedenen Protokoll-Strings
protocols = ["HLS", "DASH", "hls", "dash", "HLS_TS", "HLS_FMP4", "DASH_CENC"]
url = "https://stream-url-provider.waipu.tv/api/stream-url"

base_headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/vnd.streamurlprovider.stream-url-request-v1+json",
    "Accept": "application/vnd.streamurlprovider.traditional-stream-url-v1+json",
    "X-Device-Token": device_token,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

print("\n--- Teste Protokoll-Strings mit X-Device-Token ---")
for proto in protocols:
    body_data = {
        "stream": {
            "station": "ard",
            "protocol": proto,
            "requestMuxInstrumentation": True,
            "processOutcomeField": True
        },
        "advertising": {
            "id": "00000000-0000-0000-0000-000000000000",
            "gdprConsent": "",
            "serverSideAdInsertion": True
        }
    }
    try:
        req = urllib.request.Request(url, data=json.dumps(body_data).encode("utf-8"), headers=base_headers, method="POST")
        with urllib.request.urlopen(req, context=ctx) as r:
            res_text = r.read().decode("utf-8")
            print(f"[ERFOLG 200 OK] mit protocol='{proto}':")
            print(res_text)
            break
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="ignore")
        print(f"[HTTP {e.code}] mit protocol='{proto}': {err}")
