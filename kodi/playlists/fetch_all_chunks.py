import urllib.request
import re
import ssl
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

base_url = "https://app.waipu.tv/ui"
loader_url = f"{base_url}/App-LCOOEI3D.js"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

req = urllib.request.Request(loader_url, headers=headers)
with urllib.request.urlopen(req, context=ctx) as r:
    loader_code = r.read().decode("utf-8", errors="ignore")

# 1. Alle relativen .js Chunk-Dateinamen aus dem Loader extrahieren
chunks = set(re.findall(r'["\'](\.?/?[a-zA-Z0-9_.-]+\.js)["\']', loader_code))
# Auch nach esbuild/vite-Hashes wie chunk-XXXXX.js oder App-XXXX.js suchen
chunks.update(re.findall(r'([a-zA-Z0-9_.-]+-[A-Z0-9]{8}\.js)', loader_code))

print(f"Gefundene Chunk-Dateien im Loader: {chunks}\n")

all_domains = set()
all_paths = set()
fetch_calls = set()

for c in sorted(chunks):
    c_clean = c.lstrip("./")
    target_url = f"{base_url}/{c_clean}" if not c_clean.startswith("http") else c_clean
    try:
        req_c = urllib.request.Request(target_url, headers=headers)
        with urllib.request.urlopen(req_c, context=ctx) as rc:
            content = rc.read().decode("utf-8", errors="ignore")
            print(f"-> Analysiere {c_clean} ({len(content)} Bytes)...")
            
            # Domains & URLs finden
            for d in re.findall(r'https?://[a-zA-Z0-9.-]+\.waipu\.[a-z0-9/_-]+', content):
                all_domains.add(d)
            for d in re.findall(r'https?://[a-zA-Z0-9.-]+\.wpstr\.[a-z0-9/_-]+', content):
                all_domains.add(d)
            for d in re.findall(r'https?://[a-zA-Z0-9.-]+\.exaring\.[a-z0-9/_-]+', content):
                all_domains.add(d)
                
            # Pfade finden
            for p in re.findall(r'["\'](/[a-zA-Z0-9/_.-]*(?:channel|station|stream|epg|guide|lineup|token|auth)[a-zA-Z0-9/_.-]*)["\']', content, re.IGNORECASE):
                all_paths.add(p)
    except Exception as e:
        print(f"Fehler bei {target_url}: {e}")

print("\n--- Gefundene Domains & Service-URLs ---")
for d in sorted(all_domains):
    print(" ", d)

print("\n--- Gefundene API- & Kanal-Pfade ---")
for p in sorted(all_paths):
    print(" ", p)
