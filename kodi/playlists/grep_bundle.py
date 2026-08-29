import urllib.request
import re
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

bundle_url = "https://app.waipu.tv/ui/App-LCOOEI3D.js"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

req = urllib.request.Request(bundle_url, headers=headers)
with urllib.request.urlopen(req, context=ctx) as r:
    code = r.read().decode("utf-8", errors="ignore")

print(f"Bundle geladen ({len(code)} Zeichen). Suche relevante Codeblöcke...\n")

# 1. Suche nach Pfaden mit Anführungszeichen, die channels/stream/station/epg enthalten
string_matches = set(re.findall(r'["\'](/[a-zA-Z0-9/_.-]*(?:channel|station|stream|epg|guide|lineup)[a-zA-Z0-9/_.-]*)["\']', code, re.IGNORECASE))
print("--- Gefundene URL-Pfade ---")
for m in sorted(string_matches):
    print(" ", m)

# 2. Suche nach Fetch-/Axios-/API-Aufrufen
fetch_matches = set(re.findall(r'(?:fetch|get|post)\s*\(\s*["\']([^"\']+)["\']', code, re.IGNORECASE))
print("\n--- Gefundene direkte Request-Ziele ---")
for fm in sorted(fetch_matches):
    print(" ", fm)

# 3. Suche nach waipu.tv Domains im gesamten Code
all_domains = set(re.findall(r'[a-zA-Z0-9.-]+\.waipu\.[a-z]+', code, re.IGNORECASE))
print("\n--- Alle vorkommenden Waipu-Hostnamen ---")
for d in sorted(all_domains):
    print(" ", d)
