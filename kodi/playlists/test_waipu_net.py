import urllib.request
import urllib.parse
import json
import ssl
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
    print("[1/2] Token aktiv!")

# 2. Reale Endpunkte auf waipu.net testen
headers = {
    "Authorization": f"Bearer {access_token}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json"
}

services = [
    "https://epg-channels.waipu.net/api/channels",
    "https://epg-channels.waipu.net/api/v1/channels",
    "https://epg-cache.waipu.net/api/channels",
    "https://user-stations.waipu.net/api/stations",
    "https://user-stations.waipu.net/api/v1/stations",
    "https://playout-url-provider.waipu.net/api/playout-url",
    "https://epg-channels.waipu.tv/api/channels",
    "https://user-stations.waipu.tv/api/stations"
]

print("\n[2/2] Teste Services auf waipu.net...")
for s_url in services:
    try:
        req_s = urllib.request.Request(s_url, headers=headers)
        with urllib.request.urlopen(req_s, context=ctx) as r:
            body = r.read().decode("utf-8")
            print(f"[OK 200]: {s_url} -> {len(body)} Bytes")
            print("  Vorschau:", body[:180], "\n")
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="ignore")[:80] if hasattr(e, "read") else ""
        print(f"[{e.code}] {s_url} -> {err}")
    except Exception as ex:
        print(f"[ERR] {s_url} -> {ex}")
