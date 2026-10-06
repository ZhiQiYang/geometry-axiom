"""Loopback-only, read-only dashboard. Mutations are explicit local CLI commands."""
from __future__ import annotations

import json
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from store import Store

STATIC = Path(__file__).resolve().parent / "static"


def code_fingerprint():
    root = Path(__file__).resolve().parent
    return hashlib.sha256(b"\0".join((root / name).read_bytes() for name in
                                     ("store.py", "cli.py", "server.py"))).hexdigest()


ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
}


def make_server(data_dir, host="127.0.0.1", port=8765):
    if host not in {"127.0.0.1", "localhost"}:
        raise ValueError("工作面板只能綁定 127.0.0.1 / localhost")
    data_dir = Path(data_dir).resolve()
    startup_fingerprint = code_fingerprint()

    class Handler(BaseHTTPRequestHandler):
        server_version = "GeometryWorkManager/1"

        def log_message(self, format, *args):
            # No request paths, source bodies or task data in HTTP access logs.
            pass

        def respond(self, status, body, content_type="application/json; charset=utf-8", extra=None):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Work-Manager-Code", startup_fingerprint)
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
            for key, value in (extra or {}).items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)

        def json(self, status, value, extra=None):
            self.respond(status, json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8"), extra=extra)

        def trusted_request(self):
            port_number = self.server.server_port
            allowed_hosts = {f"127.0.0.1:{port_number}", f"localhost:{port_number}"}
            if self.headers.get("Host", "") not in allowed_hosts:
                return False
            origin = self.headers.get("Origin")
            if origin and origin not in {"http://" + h for h in allowed_hosts}:
                return False
            return self.headers.get("Sec-Fetch-Site", "none") in {"none", "same-origin"}

        def do_GET(self):
            if not self.trusted_request():
                return self.json(403, {"error": "僅允許本機同源讀取"})
            path = urlsplit(self.path).path
            if path in {"/api/state", "/api/export"}:
                try:
                    if code_fingerprint() != startup_fingerprint:
                        return self.json(503, {"error": "工具程式已更新，請重啟 serve 後再讀取；已保存的資料不變。"})
                    store = Store(data_dir)
                    try:
                        value = store.reconcile() if path == "/api/state" else store.export_snapshot()
                    finally:
                        close = getattr(store, "close", None)
                        if close:
                            close()
                    headers = {}
                    if path == "/api/export":
                        headers["Content-Disposition"] = 'attachment; filename="geometry-work-backup.json"'
                    return self.json(200, value, headers)
                except Exception:
                    return self.json(503, {"error": "狀態暫時無法讀取；原資料保留，請用 CLI reconcile 查核。"})
            if path in ASSETS:
                filename, content_type = ASSETS[path]
                try:
                    body = (STATIC / filename).read_bytes()
                except OSError:
                    return self.json(503, {"error": "面板檔案尚未就緒"})
                return self.respond(200, body, content_type)
            if path == "/favicon.ico":
                return self.respond(204, b"")
            return self.json(404, {"error": "找不到此工具資源"})

        def do_POST(self):
            self.json(405, {"error": "唯讀 API；請使用 CLI 登記事件"}, {"Allow": "GET"})

        do_PUT = do_POST
        do_PATCH = do_POST
        do_DELETE = do_POST
        do_OPTIONS = do_POST

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(data_dir, host="127.0.0.1", port=8765):
    with make_server(data_dir, host=host, port=port) as server:
        print(json.dumps({"url": f"http://127.0.0.1:{server.server_port}", "mode": "loopback-read-only", "persistent_service": False}), flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
