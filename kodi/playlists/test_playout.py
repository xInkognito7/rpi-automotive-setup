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

# 2. Test-Sender (Das Erste: ard)
test_url = "https://playout-url-provider.waipu.tv/api/playout-url?stationId=ard"

headers = {
    "Authorization": f"Bearer {access_token}",
    "User-Agent": "okhttp/4.9.0",
    "Accept": "*/*"
}

print(f"Rufe Playout-URL für 'ard' ab...")
try:
    req_p = urllib.request.Request(test_url, headers=headers)
    with urllib.request.urlopen(req_p, context=ctx) as r:
        raw = r.read().decode("utf-8")
        print("\n[Antwort 200 OK]:")
        print(raw)
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", errors="ignore")
    print(f"\n[HTTP {e.code}]: {body}")
