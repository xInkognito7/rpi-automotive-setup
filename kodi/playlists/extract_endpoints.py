import urllib.request
import re
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

req = urllib.request.Request("https://play.waipu.tv/", headers=headers)
with urllib.request.urlopen(req, context=ctx) as r:
    html = r.read().decode("utf-8")

scripts = re.findall(r'src="([^"]+\.js)"', html)
print(f"Gefundene JS-Dateien: {len(scripts)}")

found_urls = set()
for s in scripts:
    url = s if s.startswith("http") else f"https://play.waipu.tv/{s.lstrip('/')}"
    try:
        req_js = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req_js, context=ctx) as r_js:
            content = r_js.read().decode("utf-8", errors="ignore")
            matches = re.findall(r'https://[a-zA-Z0-9.-]+\.waipu\.[a-z]+[^\s"\'`)]*', content)
            for m in matches:
                found_urls.add(m.split('?')[0])
            api_routes = re.findall(r'["\'](/api/[a-zA-Z0-9/_.-]+)["\']', content)
            for ar in api_routes:
                found_urls.add(ar)
    except Exception as e:
        print(f"Fehler bei {url}: {e}")

print("\n--- Gefundene Endpunkte ---")
for u in sorted(found_urls):
    if any(k in u.lower() for k in ["channel", "stream", "epg", "station", "guide", "tv", "api", "broadcast"]):
        print(u)
