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
import uuid

HERE = pathlib.Path(__file__).resolve().parent
VENDOR_FILES = {"/" + p.relative_to(HERE).as_posix(): p
                for p in (HERE / "vendor").rglob("*") if p.is_file()}
SCENE_DIR = HERE.parent                      # *.scene 都在 knowledgebase 根目錄
sys.path.insert(0, str(HERE))
import feedback_store  # noqa: E402
FEEDBACK_MAX_BYTES = 32 * 1024 * 1024
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
API_SESSION = uuid.uuid4().hex
api_receipts = {}
receipt_lock = threading.Lock()
MAX_RECEIPTS = 256


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
    for prefix in ("loadfile ", "engineering-preview ", "engineering-validate "):
        if cmd.startswith(prefix):
            cmd = prefix + to_bridge_path(cmd[len(prefix):])
            break
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


def recorded_api(data):
    """Recover a lost response without running a world-changing command again.

    Clients acknowledge received results on their next request. A lookup arriving
    before its command seals that id as cancelled, so a late command cannot run.
    Unacknowledged results are bounded; capacity failure never reaches the core.
    """
    request_id = data.get("receipt", data.get("requestId"))
    if request_id is None:
        return ask_bridge(data["cmd"])
    if (not isinstance(request_id, str) or not re.fullmatch(r"[a-f0-9-]{36}", request_id)
            or data.get("session") != API_SESSION):
        return err_json("操作結果無法確認：服務已重啟或請求識別不合法。")
    if not receipt_lock.acquire(timeout=BRIDGE_TIMEOUT):
        return err_json("操作結果仍在處理，請稍後重試。")
    try:
        for ack in data.get("ack", [])[:MAX_RECEIPTS]:
            if isinstance(ack, str) and api_receipts.get(ack, (None,))[0] is not None:
                api_receipts.pop(ack, None)
        cached = api_receipts.get(request_id)
        if cached is None:
            if len(api_receipts) >= MAX_RECEIPTS:
                return err_json("未確認的操作結果過多，已暫停新增操作。")
            if "receipt" in data:
                cached = (None, err_json("操作未送達，場景未變更；請重新操作。"))
            else:
                cached = (data["cmd"], ask_bridge(data["cmd"]))
            api_receipts[request_id] = cached
        elif "receipt" not in data and cached[0] not in (None, data["cmd"]):
            return err_json("同一操作識別不得用於不同指令。")
        if "receipt" in data:
            return json.dumps({"ok": True, "result": json.loads(cached[1])}, ensure_ascii=False).encode("utf-8")
        return cached[1]
    finally:
        receipt_lock.release()


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # 靜音
        pass

    def _send(self, body: bytes, ctype="application/json; charset=utf-8"):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Geometry-Session", API_SESSION)
        self.send_header("X-Geometry-Release", "engineering-spec-v1-20260928")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._send((HERE / "index.html").read_bytes(),
                       "text/html; charset=utf-8")
        elif self.path in {"/app.css", "/space-workspace.css", "/engineering-workspace.css"}:
            self._send((HERE / self.path[1:]).read_bytes(),
                       "text/css; charset=utf-8")
        elif self.path in {"/app.js", "/reference-ui.js", "/polydraft.js", "/feedback.js",
                           "/project-store.js", "/reference-workspace.js",
                           "/model-viewer.js", "/space-workspace.js", "/engineering-workspace.js", "/engineering-adapter.js"}:
            self._send((HERE / self.path[1:]).read_bytes(),
                       "text/javascript; charset=utf-8")
        elif self.path in VENDOR_FILES:
            path = VENDOR_FILES[self.path]
            ctype = {".js": "text/javascript; charset=utf-8",
                     ".mjs": "text/javascript; charset=utf-8",
                     ".wasm": "application/wasm"}.get(path.suffix, "application/octet-stream")
            self._send(path.read_bytes(), ctype)
        elif self.path == "/axioms":
            self._send((SCENE_DIR / "geometry-guide" / "公理層-閱讀器.html").read_bytes(),
                       "text/html; charset=utf-8")
        elif self.path == "/examples/engineering-spec-v1.gcanvas":
            self._send((HERE / "examples" / "engineering-spec-v1.gcanvas").read_bytes(),
                       "application/octet-stream")
        elif self.path == "/scenes":
            items = [{"name": p.name, "path": str(p)}
                     for p in sorted(SCENE_DIR.glob("*.scene"))]
            self._send(json.dumps(items, ensure_ascii=False).encode("utf-8"))
        elif self.path == "/model/space-examples":
            import space_modeling
            from modeling import ModelError, canonical_bytes
            try:
                self._send(canonical_bytes(space_modeling.examples()))
            except ModelError as exc:
                self._send(canonical_bytes(exc.as_dict()))
        elif self.path == "/model/capabilities":
            sys.path.insert(0, str(SCENE_DIR / "geometry-core"))
            from modeling import CAPABILITIES, PROFILE
            self._send(json.dumps({"profile": PROFILE, "capabilities": CAPABILITIES,
                                   "executor": "C scene validation + Python exact integer modeling",
                                   "release": "engineering-spec-v1-20260928",
                                   "space_preview_schemas": ["geometry-space-preview/1", "geometry-space-preview/2"],
                                   "max_cells": 200000}).encode("utf-8"))
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
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            self.send_error(400)
            return
        if length < 0 or (self.path.startswith("/model") and length > 16 * 1024 * 1024) or \
                (self.path.startswith("/engineering/") and length > 1024 * 1024) or \
                (self.path == "/feedback" and length > FEEDBACK_MAX_BYTES):
            self.send_error(413)
            return
        body = self.rfile.read(length)

        if self.path in {"/engineering/preview", "/engineering/validate-project"}:
            from engineering_transport import file_request
            try:
                self._send(file_request(body, ask_bridge, validate_scene=self.path.endswith('validate-project')))
            except OSError:
                self._send(err_json('無法建立工程資料暫存檔，場景未變更。'))
            return
        if self.path == "/engineering/read":
            self._send(ask_bridge('engineering-read'))
            return

        if self.path == "/feedback":
            # GEO-183:使用者回報收件匣。寫進 repo 的 feedback/(.gitignore 允許清單制,預設不進 git)。
            try:
                result = feedback_store.save(json.loads(body.decode("utf-8")))
            except (ValueError, UnicodeDecodeError) as exc:
                result = {"ok": False, "error": str(exc) or "bad request"}
            self._send(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            return

        if self.path in {"/model", "/model/verify", "/model/space-preview"}:
            sys.path.insert(0, str(SCENE_DIR / "geometry-core"))
            from modeling import (ModelError, build_package, verify_package,
                                  canonical_bytes, strict_json_loads)
            try:
                data = strict_json_loads(body)
                if self.path == "/model/space-preview":
                    import space_modeling
                    result = space_modeling.preview(data)
                elif self.path == "/model/verify":
                    result = verify_package(data)
                else:
                    if (not isinstance(data, dict) or not {"definitions", "request"} <= data.keys()
                            or set(data) - {"definitions", "request", "presentation"}):
                        raise ModelError("INVALID", "INPUT_SCHEMA", "D25", "Expected definitions and request")
                    result = build_package(data["definitions"], data["request"],
                                           presentation=data.get("presentation"))
                self._send(canonical_bytes(result))
            except ModelError as exc:
                self._send(canonical_bytes(exc.as_dict()))
        elif self.path == "/api":
            try:
                data = json.loads(body.decode("utf-8"))
                if not isinstance(data, dict) or not isinstance(data.get("ack", []), list):
                    raise ValueError("bad request")
                if "receipt" in data:
                    self._send(recorded_api(data))
                    return
                cmd = data["cmd"]
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
            self._send(recorded_api(data))
        elif self.path == "/upload":
            # 瀏覽器開檔 = 拿到內容而非路徑：寫暫存檔走 parse_scene_file 同一條路。
            with tempfile.NamedTemporaryFile(
                    "wb", suffix=".scene", delete=False) as f:
                f.write(body)
                tmp = f.name
            # GEO-154：**先載,成功了才動舊暫存**。
            # bridge 的 loadfile 是交易式的(失敗時 `g_world = before`),所以載入失敗後
            # 畫面上還是舊場景;先刪舊暫存的話,那個還活著的場景就沒有來源檔了,
            # 前端 curScene 指向一個已刪的路徑,「重新載入場景」從此壞掉。
            resp = ask_bridge("loadfile " + tmp)
            try:
                merged = json.loads(resp.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                merged = None
            if not isinstance(merged, dict) or merged.get("ok") is not True:
                # 新檔沒載起來:它自己才是該丟的那一個,舊暫存留著。
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
                self._send(resp)
                return
            while len(_upload_temps) > 0:
                stale = _upload_temps.pop(0)
                try:
                    os.unlink(stale)
                except OSError:
                    pass
            _upload_temps.append(tmp)
            # 回傳暫存檔路徑,前端 curScene 指到它,「重新載入場景」載回剛上傳的內容。
            merged["path"] = tmp
            self._send(json.dumps(merged, ensure_ascii=False).encode("utf-8"))
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
