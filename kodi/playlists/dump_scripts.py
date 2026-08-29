import urllib.request
import re
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

req = urllib.request.Request("https://app.waipu.tv/tv", headers=headers)
with urllib.request.urlopen(req, context=ctx) as r:
    html = r.read().decode("utf-8")

print("--- Gefundene <script>-Tags ---")
scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html)
for s in scripts:
    print(s)

print("\n--- Inline-Konfiguration / Environment-Variablen ---")
inline_matches = re.findall(r'https?://[a-zA-Z0-9.-]+\.waipu\.[a-z0-9/_-]+', html)
for m in sorted(set(inline_matches)):
    print(m)
