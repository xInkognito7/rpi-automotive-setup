import urllib.request
import re
import ssl
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

bundle_url = "https://play.waipu.tv/ui/App-LCOOEI3D.js"
headers = {"User-Agent": "Mozilla/5.0"}
req = urllib.request.Request(bundle_url, headers=headers)
with urllib.request.urlopen(req, context=ctx) as r:
    bundle_text = r.read().decode("utf-8", errors="ignore")

# 1. Wo wird eA() aufgerufen?
print("--- Aufrufe von eA() im Bundle ---")
matches = [m.start() for m in re.finditer(r'eA\(', bundle_text)]
for pos in matches:
    start = max(0, pos - 300)
    end = min(len(bundle_text), pos + 300)
    print(bundle_text[start:end])
    print("-" * 60)

# 2. Suche nach Zuweisungen mit Typen wie application/vnd.dc.device-info
print("\n--- Device-Info Strukturen / Felder ---")
for m in re.finditer(r'(?:deviceInfo|deviceCapabilities|capabilities)\s*:\s*\{', bundle_text):
    start = max(0, m.start() - 50)
    end = min(len(bundle_text), m.end() + 250)
    print(bundle_text[start:end])
    print("-" * 40)
