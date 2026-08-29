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

# 2. Bundle App-LCOOEI3D.js laden & analysieren
bundle_url = "https://app.waipu.tv/ui/App-LCOOEI3D.js"
print(f"[2/3] Lade App-Bundle: {bundle_url}...")

req_bundle = urllib.request.Request(bundle_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
with urllib.request.urlopen(req_bundle, context=ctx) as r:
    code = r.read().decode("utf-8", errors="ignore")

# Endpunkte und Base-URLs extrahieren
found_urls = set(re.findall(r'https://[a-zA-Z0-9.-]+\.waipu\.[a-z0-9/_-]+', code))
api_routes = set(re.findall(r'["\'](/api/[a-zA-Z0-9/_-]+)["\']', code))
v_routes = set(re.findall(r'["\'](/v[0-9]/[a-zA-Z0-9/_-]+)["\']', code))

print("\n--- Gefundene Domains & URLs im Bundle ---")
for u in sorted(found_urls):
    print(" ", u)

print("\n--- Gefundene API-Routen im Bundle ---")
for r_path in sorted(api_routes | v_routes):
    print(" ", r_path)

# 3. Teste alle plausiblen Kombinationen mit dem Bearer-Token
print("\n[3/3] Frage gefundene Kanal-Endpunkte ab...")
headers = {
    "Authorization": f"Bearer {access_token}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json"
}

# Kombiniere Base-Domains mit den gefundenen Pfaden
test_targets = []
for u in found_urls:
    if "api" in u or "epg" in u or "play" in u or "tv" in u:
        for p in api_routes | v_routes:
            test_targets.append(f"{u.rstrip('/')}{p}")
        test_targets.append(u)

for target in sorted(set(test_targets)):
    if any(k in target.lower() for k in ["channel", "station", "stream", "epg", "program", "guide", "tv"]):
        try:
            req_t = urllib.request.Request(target, headers=headers)
            with urllib.request.urlopen(req_t, context=ctx) as r_t:
                body = r_t.read().decode("utf-8")
                print(f"\n[OK 200]: {target} (Länge: {len(body)})")
                print("Vorschau:", body[:200])
        except urllib.error.HTTPError as e:
            if e.code not in [404, 403]:
                print(f"[{e.code}] {target}")
        except Exception:
            pass
