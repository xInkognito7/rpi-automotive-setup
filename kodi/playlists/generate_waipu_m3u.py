import urllib.request
import urllib.parse
import json
import os
import xml.etree.ElementTree as ET

settings_path = os.path.expanduser("~/.kodi/userdata/addon_data/pvr.waipu/settings.xml")
token = None

if os.path.exists(settings_path):
    tree = ET.parse(settings_path)
    root = tree.getroot()
    for setting in root.findall("setting"):
        if setting.get("id") == "refresh_token":
            token = setting.text

if not token:
    print("Fehler: Kein Refresh-Token gefunden!")
    exit(1)

# 1. Access Token per form-urlencoded holen
auth_url = "https://auth.waipu.tv/oauth/token"
payload = urllib.parse.urlencode({
    "grant_type": "refresh_token",
    "refresh_token": token.strip(),
    "client_id": "waipu-firetv"
}).encode("utf-8")

req = urllib.request.Request(auth_url, data=payload, headers={
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "okhttp/4.9.0"
})

try:
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode("utf-8"))
        access_token = res.get("access_token")
        print("[OK] Access-Token erfolgreich bezogen!")
except Exception as e:
    # Falls Fehler, genaue Server-Antwort ausgeben
    if hasattr(e, 'read'):
        print(f"Auth-Fehler Detail: {e.read().decode('utf-8')}")
    else:
        print(f"Auth-Fehler: {e}")
    exit(1)

# 2. Kanalliste abrufen
channels_url = "https://api.waipu.net/channels"
req_ch = urllib.request.Request(channels_url, headers={
    "Authorization": f"Bearer {access_token}",
    "User-Agent": "okhttp/4.9.0"
})

try:
    with urllib.request.urlopen(req_ch) as response:
        data = response.read().decode("utf-8")
        channels_data = json.loads(data)
        
        channels = channels_data if isinstance(channels_data, list) else channels_data.get("channels", channels_data.get("items", []))
        
        m3u_file = os.path.expanduser("~/.kodi/userdata/playlists/waipu.m3u8")
        with open(m3u_file, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for ch in channels:
                name = ch.get("displayName") or ch.get("name") or "Sender"
                logo = ch.get("links", {}).get("logo", "") if isinstance(ch.get("links"), dict) else ""
                stream_url = ch.get("links", {}).get("stream", "") if isinstance(ch.get("links"), dict) else ch.get("streamUrl", "")
                
                if not stream_url and "playUrl" in ch:
                    stream_url = ch["playUrl"]
                
                f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="Waipu.tv",{name}\n')
                f.write(f'{stream_url}\n')
                
        print(f"[ERFOLG] {len(channels)} Waipu-Sender in waipu.m3u8 generiert!")
except Exception as e:
    if hasattr(e, 'read'):
        print(f"Kanalabruf-Detail: {e.read().decode('utf-8')}")
    else:
        print(f"Senderlisten-Fehler: {e}")
