import urllib.request
import re
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

bundle_url = "https://play.waipu.tv/ui/App-LCOOEI3D.js"
headers = {"User-Agent": "Mozilla/5.0"}
req = urllib.request.Request(bundle_url, headers=headers)
with urllib.request.urlopen(req, context=ctx) as r:
    bundle_text = r.read().decode("utf-8", errors="ignore")

print("--- Analyse: Woher kommt deviceToken? ---")
matches = [m.start() for m in re.finditer(r'fetchPlayoutUrl', bundle_text)]
for pos in matches:
    start = max(0, pos - 400)
    end = min(len(bundle_text), pos + 100)
    print(bundle_text[start:end])
    print("-" * 60)

print("\n--- Suche nach device-token / deviceCapabilities Aufrufen ---")
for m in re.finditer(r'(?:device-capabilities|deviceToken|device_token)', bundle_text):
    start = max(0, m.start() - 60)
    end = min(len(bundle_text), m.end() + 100)
    print(bundle_text[start:end])
    print("-" * 40)
