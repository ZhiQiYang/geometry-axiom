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


# bridge stdin 緩衝 4096 bytes：fgets 上限 4095 字元含換行，
# 所以指令本體最多 4094 bytes，超過會被截斷造成回應錯位。
BRIDGE_MAX_CMD = 4094
# L3 跨站防護：只收本機來源；無 Origin 的 curl/腳本照常放行。
LOCAL_ORIGINS = {f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"}
LOCAL_HOSTS = {"127.0.0.1", "localhost"}


def err_json(msg: str) -> bytes:
    return json.dumps({"ok": False, "error": msg},
                      ensure_ascii=False).encode("utf-8")


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

    def _local_only(self) -> bool:
        """L3：跨站 POST 一律 403；回傳 True = 已拒絕。"""
        origin = self.headers.get("Origin")
        if origin is not None and origin not in LOCAL_ORIGINS:
            self.send_error(403)
            return True
        host = self.headers.get("Host")
        if host is not None and host.rsplit(":", 1)[0] not in LOCAL_HOSTS:
            self.send_error(403)
            return True
        return False

    def do_POST(self):
        if self._local_only():
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        if self.path == "/api":
            try:
                cmd = json.loads(body.decode("utf-8"))["cmd"]
            except (ValueError, KeyError, UnicodeDecodeError):
                self._send(err_json("bad request"))
                return
            if not isinstance(cmd, str):
                self._send(err_json("bad request"))
                return
            # 含換行的 cmd 會被拆成多行送進 bridge → 回應錯位；直接拒絕。
            if "\n" in cmd or "\r" in cmd:
                self._send(err_json("指令不得含換行"))
                return
            if len(cmd.encode("utf-8")) > BRIDGE_MAX_CMD:
                self._send(err_json("指令超過單行上限"))
                return
            self._send(ask_bridge(cmd))
        elif self.path == "/upload":
            # 瀏覽器開檔 = 拿到內容而非路徑：寫暫存檔走 parse_scene_file 同一條路。
            with tempfile.NamedTemporaryFile(
                    "wb", suffix=".scene", delete=False) as f:
                f.write(body)
                tmp = f.name
            resp = ask_bridge("loadfile " + tmp)
            # 回傳暫存檔路徑,前端 curScene 指到它,「重新載入場景」載回剛上傳的內容。
            try:
                merged = json.loads(resp.decode("utf-8"))
                merged["path"] = tmp
                self._send(json.dumps(merged, ensure_ascii=False).encode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                self._send(resp)
        else:
            self.send_error(404)


if __name__ == "__main__":
    print(f"http://localhost:{PORT}  （Ctrl-C 結束；bridge={BRIDGE.name}）")
    try:
        http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
    finally:
        bridge.terminate()
