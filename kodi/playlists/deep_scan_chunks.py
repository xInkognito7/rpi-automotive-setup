import urllib.request
import urllib.parse
import json
import re
import ssl
import os

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "*/*"
}

# 1. HTML laden
base_url = "https://app.waipu.tv"
req_html = urllib.request.Request(f"{base_url}/tv", headers=headers)
with urllib.request.urlopen(req_html, context=ctx) as r:
    html = r.read().decode("utf-8")

# Alle Skript-Pfade sammeln
script_urls = set()
for m in re.findall(r'src=["\']([^"\']+\.js)["\']', html):
    script_urls.add(m if m.startswith("http") else f"{base_url}/{m.lstrip('/')}")

# 2. Aus den Bootstrappern alle weiteren Chunk-Dateien extrahieren
chunk_names = set()
for s_url in list(script_urls):
    try:
        req_js = urllib.request.Request(s_url, headers=headers)
        with urllib.request.urlopen(req_js, context=ctx) as r_js:
            code = r_js.read().decode("utf-8", errors="ignore")
            
            # Suche nach Chunk-Namen / Hash-Dateien (z.B. "main.123abc.js", "123.chunk.js")
            found_chunks = re.findall(r'["\']([a-zA-Z0-9_.-]+\.js)["\']', code)
            for c in found_chunks:
                if ("chunk" in c or "main" in c or "bundle" in c or "app" in c or "vendor" in c) and not c.startswith("http"):
                    chunk_names.add(c)
    except Exception as e:
        print(f"Fehler bei {s_url}: {e}")

print(f"Gefundene dynamische Chunks: {len(chunk_names)}")

# Chunks laden und nach API-URLs durchsuchen
found_apis = set()
for c in chunk_names:
    c_url = f"{base_url}/{c.lstrip('/')}"
    try:
        req_c = urllib.request.Request(c_url, headers=headers)
        with urllib.request.urlopen(req_c, context=ctx) as r_c:
            c_code = r_c.read().decode("utf-8", errors="ignore")
            # URLs matchen
            for u in re.findall(r'https://[a-zA-Z0-9.-]+\.waipu\.[a-z0-9/_-]+', c_code):
                found_apis.add(u)
            for u in re.findall(r'["\'](/api/[a-zA-Z0-9/_-]+)["\']', c_code):
                found_apis.add(u)
            for u in re.findall(r'["\'](/v[0-9]/[a-zA-Z0-9/_-]+)["\']', c_code):
                found_apis.add(u)
    except Exception:
        continue

print("\n--- Alle gefundenen API-Routen ---")
for a in sorted(found_apis):
    print(a)
