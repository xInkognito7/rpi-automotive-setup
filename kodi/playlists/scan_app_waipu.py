import urllib.request
import urllib.parse
import json
import re
import ssl
import xml.etree.ElementTree as ET
import os

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 1. Access-Token holen
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
    print("[1/3] Bearer-Token bezogen!")

# 2. HTML von app.waipu.tv/tv laden und alle Scripts holen
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Authorization": f"Bearer {access_token}"
}

req_html = urllib.request.Request("https://app.waipu.tv/tv", headers=headers)
try:
    with urllib.request.urlopen(req_html, context=ctx) as r:
        html = r.read().decode("utf-8")
except Exception as e:
    print(f"Fehler beim Laden von app.waipu.tv/tv: {e}")
    html = ""

scripts = re.findall(r'src="([^"]+\.js)"', html)
print(f"[2/3] Gefundene Skripte auf app.waipu.tv: {len(scripts)}")

endpoints = set()
for s in scripts:
    url = s if s.startswith("http") else f"https://app.waipu.tv/{s.lstrip('/')}"
    try:
        req_js = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req_js, context=ctx) as r_js:
            content = r_js.read().decode("utf-8", errors="ignore")
            # Extrahiere Pfade und APIs
            for m in re.findall(r'https://[a-zA-Z0-9.-]+\.waipu\.[a-z0-9/_-]+', content):
                endpoints.add(m)
            for m in re.findall(r'["\'](/api/[a-zA-Z0-9/_-]+)["\']', content):
                endpoints.add(m)
    except Exception as e:
        continue

# 3. Teste gefundene Endpunkte gegen Token
print("\n[3/3] Gefundene Endpunkte testen:")
api_headers = {
    "Authorization": f"Bearer {access_token}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json"
}

for ep in sorted(endpoints):
    if any(k in ep.lower() for k in ["channel", "station", "stream", "tv", "program", "guide", "epg"]):
        test_url = ep if ep.startswith("http") else f"https://app.waipu.tv{ep}"
        try:
            req_test = urllib.request.Request(test_url, headers=api_headers)
            with urllib.request.urlopen(req_test, context=ctx) as rt:
                body = rt.read().decode("utf-8")
                print(f"[OK 200] {test_url} -> {len(body)} Bytes")
                print("  Vorschau:", body[:140], "\n")
        except urllib.error.HTTPError as he:
            print(f"[{he.code}] {test_url}")
        except Exception as ex:
            print(f"[ERR] {test_url}: {ex}")
