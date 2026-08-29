import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET
import os
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 1. Token holen
settings_path = os.path.expanduser("~/.kodi/userdata/addon_data/pvr.waipu/settings.xml")
dev_id, token = "cd8c2238-4e43-481b-8665-472ae21ae816", ""

if os.path.exists(settings_path):
    tree = ET.parse(settings_path)
    for s in tree.getroot().findall("setting"):
        if s.get("id") == "device_id_uuid4": dev_id = s.text
        elif s.get("id") == "refresh_token": token = s.text

token_url = "https://auth.waipu.tv/oauth/token"
payload = urllib.parse.urlencode({
    "grant_type": "refresh_token",
    "refresh_token": token,
    "client_id": "waipu",
    "waipu_device_id": dev_id
}).encode("utf-8")

req_t = urllib.request.Request(token_url, data=payload, headers={
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "okhttp/4.9.0",
    "Accept": "application/json"
})
with urllib.request.urlopen(req_t, context=ctx) as resp:
    access_token = json.loads(resp.read().decode()).get("access_token")
    print("[1/2] Token aktiv!")

# 2. Gezielte Vendor-MIME-Types für user-stations
headers_to_test = [
    "application/vnd.waipu.user-stations-stations.v1+json",
    "application/vnd.waipu.user-stations-stations-v1+json",
    "application/vnd.waipu.user-stations-stations.v2+json",
    "application/vnd.waipu.user-stations-stations-v2+json",
    "application/vnd.waipu.user-stations.v1+json",
    "application/vnd.waipu.user-stations-v1+json",
    "application/vnd.waipu.stations-v1+json",
    "application/vnd.waipu.stations.v1+json"
]

stations_url = "https://user-stations.waipu.tv/api/stations"
success = False

for h in headers_to_test:
    req = urllib.request.Request(stations_url, headers={
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": h
    })
    try:
        with urllib.request.urlopen(req, context=ctx) as r:
            body = r.read().decode("utf-8")
            print(f"\n[2/2] [ERFOLG] 200 OK mit Header: '{h}' ({len(body)} Bytes)")
            
            data = json.loads(body)
            stations = data if isinstance(data, list) else data.get("stations", data.get("channels", []))
            
            m3u_file = "/home/pi/waipu.m3u8"
            with open(m3u_file, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                for st in stations:
                    name = st.get("displayName") or st.get("name") or "Sender"
                    sid = st.get("id") or st.get("stationId") or ""
                    
                    logo = st.get("logoUrl") or ""
                    if not logo and "images" in st and isinstance(st["images"], dict):
                        logo = st["images"].get("logo", "")
                    if logo and not logo.startswith("http"):
                        logo = f"https://images.wpstr.tv{logo}"
                        
                    stream_url = st.get("streamUrl") or st.get("playUrl") or ""
                    if not stream_url and "links" in st and isinstance(st["links"], dict):
                        stream_url = st["links"].get("stream", "")
                    if not stream_url and sid:
                        stream_url = f"https://playout-url-provider.waipu.tv/api/playout-url?stationId={sid}"

                    f.write(f'#EXTINF:-1 tvg-id="{sid}" tvg-name="{name}" tvg-logo="{logo}" group-title="Waipu.tv",{name}\n')
                    f.write(f'{stream_url}|Authorization=Bearer {access_token}&User-Agent=okhttp/4.9.0\n')

            print(f"[PLAYLIST] /home/pi/waipu.m3u8 mit {len(stations)} Sendern geschrieben!")
            success = True
            break
    except urllib.error.HTTPError as e:
        err_content = e.read().decode("utf-8", errors="ignore")
        print(f"[{e.code}] mit '{h}': {err_content[:120]}")

if not success:
    print("\nKeiner der Standard-Vendor-Header hat direkt gematcht.")
