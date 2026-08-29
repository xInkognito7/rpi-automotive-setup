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

# 1. Bearer Token holen
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

# 2. Release-Version aus dem Bundle extrahieren
bundle_url = "https://play.waipu.tv/ui/App-LCOOEI3D.js"
req_b = urllib.request.Request(bundle_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req_b, context=ctx) as r:
    bundle_text = r.read().decode("utf-8", errors="ignore")

app_version = "1.0.0"
v_match = re.search(r'RELEASE\s*:\s*["\']([^"\']+)["\']', bundle_text)
if v_match:
    app_version = v_match.group(1)
print(f"Gefundene App-Version: {app_version}")

# 3. Device-Capabilities anfordern
dc_url = "https://device-capabilities.waipu.tv/api/device-capabilities"
dc_headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/vnd.dc.device-info-v1+json",
    "Accept": "application/vnd.dc.device-capabilities-v1+json, application/json, */*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

dc_body = {
    "appVersion": app_version,
    "type": "web",
    "platform": "Linux",
    "manufacturer": "",
    "model": ""
}

req_dc = urllib.request.Request(dc_url, data=json.dumps(dc_body).encode("utf-8"), headers=dc_headers, method="POST")
with urllib.request.urlopen(req_dc, context=ctx) as r_dc:
    dc_res = json.loads(r_dc.read().decode("utf-8"))
    device_token = dc_res.get("token")
    print(f"[2/3] Device-Token erfolgreich generiert: {device_token[:20]}...")

# 4. Stream-URL für ARD abrufen
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

req_st = urllib.request.Request(stream_url, data=json.dumps(stream_body).encode("utf-8"), headers=stream_headers, method="POST")
with urllib.request.urlopen(req_st, context=ctx) as r_st:
    stream_data = json.loads(r_st.read().decode("utf-8"))
    print("\n[3/3] [STREAM-DATEN ERFOLGREICH EMPFANGEN]:")
    print(json.dumps(stream_data, indent=2))
