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

# 2. Bundle nach device-capabilities Body durchsuchen
bundle_url = "https://play.waipu.tv/ui/App-LCOOEI3D.js"
req_b = urllib.request.Request(bundle_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req_b, context=ctx) as r:
    bundle_text = r.read().decode("utf-8", errors="ignore")

print("--- Device-Capabilities Definition im Bundle ---")
matches = [m.start() for m in re.finditer(r'application/vnd\.dc\.device-info-v1\+json', bundle_text)]
for pos in matches:
    print(bundle_text[max(0, pos-100):min(len(bundle_text), pos+300)])
    print("-" * 60)

# 3. Device Capabilities POST absenden
dc_url = "https://device-capabilities.waipu.tv/api/device-capabilities"
dc_headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/vnd.dc.device-info-v1+json",
    "Accept": "application/json, */*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# Standard Device-Info Payload
dc_body = {
    "clientId": "waipu",
    "deviceId": dev_id,
    "deviceType": "WEB",
    "capabilities": {
        "drm": ["widevine"],
        "videoCodecs": ["h264"],
        "audioCodecs": ["aac", "mp3"]
    }
}

device_token = ""
try:
    req_dc = urllib.request.Request(dc_url, data=json.dumps(dc_body).encode("utf-8"), headers=dc_headers, method="POST")
    with urllib.request.urlopen(req_dc, context=ctx) as res:
        dc_resp = json.loads(res.read().decode("utf-8"))
        print("\n[Device-Capabilities OK 200]:")
        print(json.dumps(dc_resp, indent=2))
        device_token = dc_resp.get("deviceToken") or dc_resp.get("token") or dc_resp.get("id")
except urllib.error.HTTPError as e:
    print(f"\n[Device-Capabilities HTTP {e.code}]: {e.read().decode('utf-8')}")

# 4. Falls Device-Token erhalten, Stream anfordern
if device_token:
    print(f"\nVerwende Device-Token: {device_token}")
    stream_url = "https://stream-url-provider.waipu.tv/api/stream-url"
    stream_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/vnd.streamurlprovider.stream-url-request-v1+json",
        "Accept": "application/vnd.streamurlprovider.traditional-stream-url-v1+json",
        "X-Device-Token": device_token,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    stream_body = {
        "stream": {
            "station": "ard",
            "protocol": "hls",
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
        req_st = urllib.request.Request(stream_url, data=json.dumps(stream_body).encode("utf-8"), headers=stream_headers, method="POST")
        with urllib.request.urlopen(req_st, context=ctx) as r:
            print("\n[STREAM ERFOLG 200 OK]:")
            print(json.dumps(json.loads(r.read().decode("utf-8")), indent=2))
    except urllib.error.HTTPError as e:
        print(f"\n[Stream HTTP {e.code}]: {e.read().decode('utf-8')}")
