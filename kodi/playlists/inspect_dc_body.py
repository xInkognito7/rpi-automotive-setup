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

# Exakte Umgebung um device-capabilities anzeigen
print("--- JavaScript-Funktion für device-capabilities ---")
matches = [m.start() for m in re.finditer(r'device-capabilities', bundle_text)]
for pos in matches:
    start = max(0, pos - 250)
    end = min(len(bundle_text), pos + 400)
    print(bundle_text[start:end])
    print("=" * 60)
