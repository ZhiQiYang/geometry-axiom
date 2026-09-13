# -*- coding: utf-8 -*-
"""geometry-web 的本地伺服器：靜態頁面 + 把指令轉發給 web_bridge 子程序。

    python serve.py [port]     # 預設 8765

橋接器是「stdin 一行一令 → stdout 一行一 JSON」的長駐行程；
World 狀態住在它裡面，所以所有請求用一支 lock 串行。
"""
import http.server
import json
import pathlib
import subprocess
import sys
import tempfile
import threading

HERE = pathlib.Path(__file__).resolve().parent
SCENE_DIR = HERE.parent                      # *.scene 都在 knowledgebase 根目錄
BRIDGE = HERE / "web_bridge.exe"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765

bridge = subprocess.Popen(
    [str(BRIDGE)],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE,
)
bridge_lock = threading.Lock()


def ask_bridge(cmd: str) -> bytes:
    """送一行指令、收一行 JSON（原樣回傳 bytes，不再解析）。"""
    with bridge_lock:
        bridge.stdin.write(cmd.encode("utf-8") + b"\n")
        bridge.stdin.flush()
        return bridge.stdout.readline()


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # 靜音
        pass

    def _send(self, body: bytes, ctype="application/json; charset=utf-8"):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._send((HERE / "index.html").read_bytes(),
                       "text/html; charset=utf-8")
        elif self.path == "/app.css":
            self._send((HERE / "app.css").read_bytes(),
                       "text/css; charset=utf-8")
        elif self.path == "/app.js":
            self._send((HERE / "app.js").read_bytes(),
                       "text/javascript; charset=utf-8")
        elif self.path == "/scenes":
            items = [{"name": p.name, "path": str(p)}
                     for p in sorted(SCENE_DIR.glob("*.scene"))]
            self._send(json.dumps(items, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        if self.path == "/api":
            cmd = json.loads(body.decode("utf-8"))["cmd"]
            self._send(ask_bridge(cmd))
        elif self.path == "/upload":
            # 瀏覽器開檔 = 拿到內容而非路徑：寫暫存檔走 parse_scene_file 同一條路。
            with tempfile.NamedTemporaryFile(
                    "wb", suffix=".scene", delete=False) as f:
                f.write(body)
                tmp = f.name
            self._send(ask_bridge("loadfile " + tmp))
        else:
            self.send_error(404)


if __name__ == "__main__":
    print(f"http://localhost:{PORT}  （Ctrl-C 結束；bridge={BRIDGE.name}）")
    try:
        http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
    finally:
        bridge.terminate()
