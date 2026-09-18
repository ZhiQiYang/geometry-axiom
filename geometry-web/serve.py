# -*- coding: utf-8 -*-
"""geometry-web 的本地伺服器：靜態頁面 + 把指令轉發給 web_bridge 子程序。

    python serve.py [port]     # 預設 8765

橋接器是「stdin 一行一令 → stdout 一行一 JSON」的長駐行程；
World 狀態住在它裡面，所以所有請求用一支 lock 串行。
"""
import http.server
import json
import os
import pathlib
import queue
import re
import shlex
import subprocess
import sys
import tempfile
import threading

HERE = pathlib.Path(__file__).resolve().parent
SCENE_DIR = HERE.parent                      # *.scene 都在 knowledgebase 根目錄
# 預設用同目錄的 Windows 橋接器。GEOMETRY_BRIDGE 可覆寫，且可帶參數，例如：
#   GEOMETRY_BRIDGE="wsl.exe -d Ubuntu-24.04 --user root -- /opt/geometry/web_bridge"
# 讓 serve.py 跑在 Windows（瀏覽器連得到 localhost），橋接器跑在 WSL——
# Windows 端 web_bridge.exe 被 Smart App Control 封鎖時的解法，
# 且用的是當前核心而非舊二進位。搭配 GEOMETRY_BRIDGE_WSL=1 開啟路徑翻譯。
_bridge_env = os.environ.get("GEOMETRY_BRIDGE")
BRIDGE_CMD = (shlex.split(_bridge_env, posix=False) if _bridge_env
              else [str(HERE / "web_bridge.exe")])
BRIDGE_WSL = os.environ.get("GEOMETRY_BRIDGE_WSL") == "1"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765

bridge = subprocess.Popen(
    BRIDGE_CMD,
    stdin=subprocess.PIPE, stdout=subprocess.PIPE,
)
bridge_lock = threading.Lock()
bridge_responses = queue.Queue()
bridge_failure = None
BRIDGE_TIMEOUT = 30.0
_upload_temps = []


def read_bridge_responses():
    while True:
        try:
            response = bridge.stdout.readline()
        except OSError:
            response = b""
        bridge_responses.put(response)
        if not response:
            return


bridge_reader = threading.Thread(target=read_bridge_responses, daemon=True)
bridge_reader.start()

_WIN_PATH = re.compile(r"^([A-Za-z]):[\\/](.*)$")


def to_bridge_path(path: str) -> str:
    """橋接器跑在 WSL 時，把 Windows 路徑翻成 /mnt/<碟>/... ；否則原樣回傳。

    前端的場景路徑來自 /scenes（serve.py 以 Windows 視角產出）與 /upload 的
    暫存檔，兩者都是 Windows 路徑，Linux 端的橋接器直接開不了。
    """
    if not BRIDGE_WSL:
        return path
    m = _WIN_PATH.match(path)
    if not m:
        return path
    return "/mnt/" + m.group(1).lower() + "/" + m.group(2).replace("\\", "/")


def ask_bridge(cmd: str) -> bytes:
    """送一行指令、收一行 JSON（原樣回傳 bytes，不再解析）。"""
    global bridge_failure
    if not isinstance(cmd, str) or not cmd.strip():
        return err_json("橋接指令不得為空")
    if any(c in cmd for c in "\r\n\0"):
        return err_json("指令不得含換行或 NUL")
    if cmd.startswith("loadfile "):
        cmd = "loadfile " + to_bridge_path(cmd[len("loadfile "):])
    payload = cmd.encode("utf-8")
    if len(payload) > BRIDGE_MAX_CMD:
        return err_json("指令超過單行上限")
    if not bridge_lock.acquire(timeout=BRIDGE_TIMEOUT):
        return err_json("橋接器忙碌，請稍後再試")
    try:
        if bridge_failure is not None:
            return err_json(bridge_failure)
        try:
            bridge.stdin.write(payload + b"\n")
            bridge.stdin.flush()
            response = bridge_responses.get(timeout=BRIDGE_TIMEOUT)
        except queue.Empty:
            bridge_failure = "橋接器回應逾時，請重新啟動服務"
        except (OSError, ValueError):
            bridge_failure = "橋接器連線中斷，請重新啟動服務"
        else:
            if response:
                return response
            bridge_failure = "橋接器已結束，請重新啟動服務"
        return err_json(bridge_failure)
    finally:
        bridge_lock.release()


# bridge stdin 緩衝 4096 bytes：fgets 上限 4095 字元含換行，
# 所以指令本體最多 4094 bytes，超過會被截斷造成回應錯位。
BRIDGE_MAX_CMD = 4094
# L3 跨站防護：只收本機來源；無 Origin 的 curl/腳本照常放行。
LOCAL_ORIGINS = {f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"}
LOCAL_HOSTS = {"127.0.0.1", "localhost"}
# Explicit opt-in for the managed development preview; defaults stay local-only.
if os.environ.get("GEOMETRY_MANAGED_PREVIEW") == "1" and PORT == 4173:
    LOCAL_HOSTS.add("terminal.local")
    LOCAL_ORIGINS.add("http://terminal.local:4173")


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
        elif self.path in {"/app.js", "/reference-ui.js"}:
            self._send((HERE / self.path[1:]).read_bytes(),
                       "text/javascript; charset=utf-8")
        elif self.path == "/axioms":
            self._send((SCENE_DIR / "geometry-guide" / "公理層-閱讀器.html").read_bytes(),
                       "text/html; charset=utf-8")
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
            except (ValueError, KeyError, TypeError, UnicodeDecodeError):
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
            while len(_upload_temps) > 0:
                old = _upload_temps.pop(0)
                try:
                    os.unlink(old)
                except OSError:
                    pass
            _upload_temps.append(tmp)
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
    print(f"http://localhost:{PORT}  （Ctrl-C 結束；bridge={BRIDGE_CMD[0]}）")
    try:
        host = "0.0.0.0" if os.environ.get("GEOMETRY_MANAGED_PREVIEW") == "1" and PORT == 4173 else "127.0.0.1"
        http.server.ThreadingHTTPServer((host, PORT), Handler).serve_forever()
    finally:
        for path in _upload_temps:
            try:
                os.unlink(path)
            except OSError:
                pass
        bridge.terminate()
