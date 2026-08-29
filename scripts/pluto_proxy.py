import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import time
import uuid
import base64
import re

PORT = 8088
DEVICE_ID = str(uuid.uuid4())
SESSION_CACHE = {}
JWT_TOKEN = ""

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Origin": "https://pluto.tv",
    "Referer": "https://pluto.tv/"
}

def get_channel_stream_url(channel_id):
    global JWT_TOKEN
    now = time.time()
    if channel_id in SESSION_CACHE and now < SESSION_CACHE[channel_id]["expires"]:
        return SESSION_CACHE[channel_id]["url"]

    try:
        url = f"https://boot.pluto.tv/v4/start?appName=web&appVersion=8.0.0&deviceVersion=124.0.0&deviceModel=web&deviceMake=chrome&deviceType=web&clientID={DEVICE_ID}&clientModelNumber=1.0.0&channelId={channel_id}"
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            stitcher = data.get("stitcherParams", "")
            JWT_TOKEN = data.get("sessionToken", "")

            if stitcher:
                master_url = f"https://service-stitcher.clusters.pluto.tv/stitch/hls/channel/{channel_id}/master.m3u8?{stitcher}&jwt={JWT_TOKEN}&masterJWTPassthrough=true"
            else:
                master_url = f"https://service-stitcher.clusters.pluto.tv/stitch/hls/channel/{channel_id}/master.m3u8?jwt={JWT_TOKEN}&masterJWTPassthrough=true"

            req_m = urllib.request.Request(master_url, headers=HEADERS)
            with urllib.request.urlopen(req_m, timeout=5) as resp_m:
                lines = resp_m.read().decode("utf-8", errors="ignore").splitlines()
                sub_urls = [l.strip() for l in lines if l.strip() and not l.startswith("#")]
                chosen_url = sub_urls[-1] if sub_urls else master_url
                if not chosen_url.startswith("http"):
                    chosen_url = urllib.parse.urljoin(master_url, chosen_url)

            SESSION_CACHE[channel_id] = {
                "url": chosen_url,
                "expires": now + 1800
            }
            return chosen_url
    except Exception as e:
        print(f"[Boot Error] {e}")
        return None

class PlutoHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        self.handle_request(is_head=False)

    def do_HEAD(self):
        self.handle_request(is_head=True)

    def handle_request(self, is_head=False):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path.startswith("/channel/"):
            channel_id = parsed.path.split("/")[2].replace(".m3u8", "")
            stream_url = get_channel_stream_url(channel_id)
            if not stream_url:
                self.send_response(503)
                self.end_headers()
                return
            self.fetch_and_serve(stream_url, is_head)

        elif parsed.path.startswith("/proxy"):
            qs = urllib.parse.parse_qs(parsed.query)
            target_b64 = qs.get("url", [""])[0]
            if not target_b64:
                self.send_response(400)
                self.end_headers()
                return
            try:
                target_url = base64.urlsafe_b64decode(target_b64.encode("utf-8")).decode("utf-8")
                self.fetch_and_serve(target_url, is_head)
            except Exception:
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def fetch_and_serve(self, target_url, is_head):
        global JWT_TOKEN
        req_headers = dict(HEADERS)
        if JWT_TOKEN:
            req_headers["Authorization"] = f"Bearer {JWT_TOKEN}"

        try:
            req = urllib.request.Request(target_url, headers=req_headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                raw_data = resp.read()
                content_type = resp.headers.get("Content-Type", "application/octet-stream")

                # Playlist Parsing
                if ".m3u8" in target_url or raw_data.startswith(b"#EXTM3U"):
                    base_url = target_url.rsplit("/", 1)[0] + "/"
                    lines = []
                    for line in raw_data.decode("utf-8", errors="ignore").splitlines():
                        sline = line.strip()
                        if not sline:
                            continue
                        if sline.startswith("#"):
                            if "URI=" in sline:
                                def replace_uri(match):
                                    u = match.group(1).strip("\"'")
                                    full_u = u if u.startswith("http") else urllib.parse.urljoin(base_url, u)
                                    b64 = base64.urlsafe_b64encode(full_u.encode("utf-8")).decode("utf-8")
                                    return f'URI="http://127.0.0.1:{PORT}/proxy?url={b64}"'
                                sline = re.sub(r'URI="?([^",\s]+)"?', replace_uri, sline)
                            lines.append(sline)
                        else:
                            full_url = sline if sline.startswith("http") else urllib.parse.urljoin(base_url, sline)
                            b64 = base64.urlsafe_b64encode(full_url.encode("utf-8")).decode("utf-8")
                            lines.append(f"http://127.0.0.1:{PORT}/proxy?url={b64}")

                    body = ("\n".join(lines) + "\n").encode("utf-8")
                    content_type = "application/vnd.apple.mpegurl"
                else:
                    body = raw_data

                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                if not is_head:
                    self.wfile.write(body)
        except Exception as e:
            print(f"[Fetch Error] {e}")
            self.send_response(502)
            self.end_headers()

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

if __name__ == "__main__":
    server = ThreadedHTTPServer(("127.0.0.1", PORT), PlutoHandler)
    server.serve_forever()
