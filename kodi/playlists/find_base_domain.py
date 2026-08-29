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

# 1. Wo wird $n oder ähnliches deklariert?
print("--- Zuweisungen um $n / Base-Domain ---")
matches = [m.start() for m in re.finditer(r'PERMISSION_MANAGEMENT', bundle_text)]
for pos in matches:
    start = max(0, pos - 300)
    end = min(len(bundle_text), pos + 300)
    print(bundle_text[start:end])
    print("-" * 60)

# 2. Alle echten Hostnamen mit https:// finden
hosts = set(re.findall(r'https://([a-zA-Z0-9.-]+)', bundle_text))
print("\n--- Alle im JS-Bundle vorkommenden Hostnamen ---")
for h in sorted(hosts):
    print(" ", h)
