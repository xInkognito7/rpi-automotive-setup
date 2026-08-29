import urllib.request
import re
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# 1. HTML von play.waipu.tv abrufen
req = urllib.request.Request("https://play.waipu.tv/", headers=headers)
with urllib.request.urlopen(req, context=ctx) as r:
    html = r.read().decode("utf-8")

# Alle Skripte finden
scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html)
print(f"Gefundene Skripte auf play.waipu.tv: {scripts}\n")

found_urls = set()
for s in scripts:
    s_url = s if s.startswith("http") else f"https://play.waipu.tv/{s.lstrip('/')}"
    try:
        req_s = urllib.request.Request(s_url, headers=headers)
        with urllib.request.urlopen(req_s, context=ctx) as rs:
            code = rs.read().decode("utf-8", errors="ignore")
            print(f"Analysiere {s_url} ({len(code)} Zeichen)...")
            
            # Subdomains von waipu, wpstr und exaring finden
            for u in re.findall(r'https?://[a-zA-Z0-9.-]+\.(?:waipu|wpstr|exaring)\.[a-z0-9/._-]+', code):
                found_urls.add(u.split('?')[0])
                
            # Auch generische API-Pfade finden
            for p in re.findall(r'["\'](/api/[a-zA-Z0-9/._-]+)["\']', code):
                found_urls.add(p)
    except Exception as e:
        print(f"Fehler bei {s_url}: {e}")

print("\n--- Gefundene Endpunkte & Gateways ---")
for u in sorted(found_urls):
    print(" ", u)
