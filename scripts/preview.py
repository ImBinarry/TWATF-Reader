#!/usr/bin/env python3
"""Preview server mimicking Cloudflare Pages routing for dist/.
Stdlib only. Serves on 0.0.0.0:8765.
Rules:
- /x with no file but x.html present serves x.html (200)
- /x.html answers 308 to /x
- Unknown paths serve 404.html with status 404
"""

import http.server
import mimetypes
import os
import posixpath
import socket
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
PORT = 8765


class CloudflarePagesHandler(http.server.BaseHTTPRequestHandler):
    server_version = "CloudflarePagesPreview/1.0"

    def do_HEAD(self):
        self._handle(head_only=True)

    def do_GET(self):
        self._handle(head_only=False)

    def _handle(self, head_only=False):
        # Parse URL
        parsed = urllib.parse.urlsplit(self.path)
        raw_path = urllib.parse.unquote(parsed.path)

        # 1. If path ends with .html (except /index.html maybe, or any .html):
        # Cloudflare Pages redirects /x.html -> /x (308 Permanent Redirect)
        if raw_path.endswith(".html"):
            clean = raw_path[:-5]
            if clean == "/index":
                clean = "/"
            if not clean:
                clean = "/"
            query = f"?{parsed.query}" if parsed.query else ""
            target = f"{clean}{query}"
            self.send_response(308)
            self.send_header("Location", target)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        # Normalize relative path in DIST
        rel = raw_path.lstrip("/")
        if not rel:
            file_path = DIST / "index.html"
        else:
            file_path = DIST / rel

        # Check if direct file exists
        if file_path.is_file():
            self._serve_file(file_path, head_only=head_only)
            return

        # If /x does not exist, check if /x.html exists
        html_candidate = DIST / f"{rel}.html"
        if html_candidate.is_file():
            self._serve_file(html_candidate, head_only=head_only)
            return

        # Check directory index (e.g. /data/ or /)
        if file_path.is_dir() and (file_path / "index.html").is_file():
            self._serve_file(file_path / "index.html", head_only=head_only)
            return

        # Unknown path: serve 404.html with status 404
        not_found_file = DIST / "404.html"
        if not_found_file.is_file():
            self._serve_file(not_found_file, status=404, head_only=head_only)
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            msg = b"404 Not Found"
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            if not head_only:
                self.wfile.write(msg)

    def _serve_file(self, path, status=200, head_only=False):
        try:
            data = path.read_bytes()
        except OSError:
            self.send_response(500)
            self.end_headers()
            return

        ctype, encoding = mimetypes.guess_type(str(path))
        if not ctype:
            ctype = "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json", "application/xml"):
            ctype += "; charset=utf-8"

        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if not head_only:
            self.wfile.write(data)

    def log_message(self, format, *args):
        # Keep output clean, do not spam stdout during verification
        pass


def get_network_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def run():
    ip = get_network_ip()
    print(f"\n  Local:   http://localhost:{PORT}/\n  Network: http://{ip}:{PORT}/\n")
    server = http.server.HTTPServer(("0.0.0.0", PORT), CloudflarePagesHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
