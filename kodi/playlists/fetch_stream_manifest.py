import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET
import os
import ssl

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

# 2. Exakte Payload laut JS-Bundle abschicken
url = "https://stream-url-provider.waipu.tv/api/stream-url"

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/vnd.streamurlprovider.stream-url-request-v1+json",
    "Accept": "application/vnd.streamurlprovider.traditional-stream-url-v1+json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

post_body = {
    "stream": {
        "station": "ard",
        "protocol": "HLS"
    }
}

print(f"Fordere HLS-Stream für ARD an...")
try:
    req = urllib.request.Request(url, data=json.dumps(post_body).encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req, context=ctx) as r:
        res = json.loads(r.read().decode("utf-8"))
        print("\n[ERFOLG 200 OK]:")
        print(json.dumps(res, indent=2))
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode('utf-8')}")
