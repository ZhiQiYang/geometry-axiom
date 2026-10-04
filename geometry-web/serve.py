# -*- coding: utf-8 -*-
"""geometry-web 的本地伺服器：靜態頁面 + 把指令轉發給 web_bridge 子程序。

    python serve.py [port]     # 預設 8765

橋接器是「stdin 一行一令 → stdout 一行一 JSON」的長駐行程；
World 狀態住在它裡面，所以所有請求用一支 lock 串行。
"""
import http.server
import hashlib
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
SCENE_DIR = HERE.parent                      # *.scene 都在 knowledgebase 根目錄
sys.path.insert(0, str(HERE))
import feedback_store  # noqa: E402
from runtime_version import RuntimeSnapshot, RESTART_MESSAGE

RUNTIME = RuntimeSnapshot(SCENE_DIR)
FEEDBACK_MAX_BYTES = 32 * 1024 * 1024
API_MAX_BYTES = 64 * 1024  # Escaped 4094-byte command, 256 receipt acknowledgements.
UPLOAD_MAX_BYTES = 16 * 1024 * 1024
POST_MAX_BYTES = {
    "/api": API_MAX_BYTES,
    "/upload": UPLOAD_MAX_BYTES,
    "/upload/prepare": UPLOAD_MAX_BYTES,
    "/upload/confirm": 1024,
    "/upload/cancel": 1024,
    "/feedback": FEEDBACK_MAX_BYTES,
    "/model": 16 * 1024 * 1024,
    "/model/verify": 16 * 1024 * 1024,
    "/model/space-preview": 16 * 1024 * 1024,
    "/model/update-preview": 8 * 1024 * 1024,
    "/assembly/preview": 1024 * 1024,
    "/assembly/generate-preview": 1024 * 1024,
    "/engineering/preview": 1024 * 1024,
    "/engineering/validate-project": 1024 * 1024,
    "/engineering/read": 1024 * 1024,
    "/sources/snapshot": 1024 * 1024,
}
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
bridge_lock = threading.RLock()
bridge_responses = queue.Queue()
bridge_failure = None
BRIDGE_TIMEOUT = 30.0
_upload_temps = []
_prepared_upload = None
_upload_outcomes = {}  # Bounded terminal receipts; unknown tokens never authorize a commit.
upload_lock = threading.Lock()
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
    for prefix in ("loadfile ", "load-prepare ", "engineering-preview ", "engineering-validate ", "assembly-preview ", "assembly-generation-preview ", "source-inspect-file "):
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


def remember_upload_outcome(token, result):
    encoded = json.dumps(result, ensure_ascii=False).encode("utf-8")
    _upload_outcomes[token] = encoded
    if len(_upload_outcomes) > MAX_RECEIPTS:
        del _upload_outcomes[next(iter(_upload_outcomes))]
    return encoded


def upload_scene(body: bytes, phase=None) -> bytes:
    """Keep successful load order and source-file retirement in one transaction."""
    global _prepared_upload
    if not upload_lock.acquire(timeout=BRIDGE_TIMEOUT):
        return err_json("場景上傳仍在處理，請稍後再試。")
    # Include ordinary /api reloads in the ordering. ask_bridge re-enters this
    # lock; no request may load an old source between success and its retirement.
    if not bridge_lock.acquire(timeout=BRIDGE_TIMEOUT):
        upload_lock.release()
        return err_json("橋接器忙碌，請稍後再試")
    tmp = None
    try:
        if phase in {"confirm", "cancel"}:
            try:
                token = json.loads(body.decode("utf-8"))
                if type(token) is not int or not 1 <= token <= 4294967295:
                    raise ValueError("Invalid import token")
            except (ValueError, UnicodeError):
                return err_json("無效的專案載入確認識別。")
            if token in _upload_outcomes:
                terminal = _upload_outcomes[token]
                if phase == "confirm" and json.loads(terminal).get("state") == "cancelled":
                    return err_json("專案候選已取消，未變更目前專案。")
                return terminal
            if _prepared_upload is None or _prepared_upload[0] != token:
                return err_json("專案候選已失效，請重新開啟。")
            tmp = _prepared_upload[1]
            _prepared_upload = None
            resp = ask_bridge(f"load-{phase} {token}")
            if phase == "cancel":
                result = json.loads(resp)
                if result.get("ok") is True:
                    result["state"] = "cancelled"
                else:
                    result["state"] = "unknown"
                return remember_upload_outcome(token, result)
        else:
            if _prepared_upload is not None:
                old_token, old_path = _prepared_upload
                cancelled = json.loads(ask_bridge(f"load-cancel {old_token}"))
                cancelled["state"] = "cancelled" if cancelled.get("ok") is True else "unknown"
                remember_upload_outcome(old_token, cancelled)
                os.unlink(old_path)
                _prepared_upload = None
        # Assign the path before writing, so a failed write also cleans its file.
            with tempfile.NamedTemporaryFile("wb", suffix=".scene", delete=False) as f:
                tmp = f.name
                f.write(body)
        # GEO-154: a rejected load leaves the previous world and its source alive.
            resp = ask_bridge(("load-prepare " if phase == "prepare" else "loadfile ") + tmp)
        try:
            merged = json.loads(resp.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            merged = None
        if not isinstance(merged, dict) or merged.get("ok") is not True:
            if phase == "confirm":
                rejected = merged if isinstance(merged, dict) else {"ok": False, "error": "無效的載入回應。"}
                rejected["state"] = "rejected" if rejected.get("code") else "unknown"
                return remember_upload_outcome(token, rejected)
            return resp
        if phase == "prepare":
            _prepared_upload = (merged["token"], tmp)
            tmp = None
            return resp
        while _upload_temps:
            stale = _upload_temps.pop(0)
            try:
                os.unlink(stale)
            except OSError:
                pass
        _upload_temps.append(tmp)
        merged["path"] = tmp
        tmp = None  # The successful scene owns this source until the next load.
        if phase == "confirm":
            merged["state"] = "committed"
            snapshot = json.loads(ask_bridge("dump"))
            if snapshot.get("ok") is True and isinstance(snapshot.get("text"), str):
                merged["scene_sha256"] = hashlib.sha256(snapshot["text"].encode("utf-8")).hexdigest()
            return remember_upload_outcome(token, merged)
        return json.dumps(merged, ensure_ascii=False).encode("utf-8")
    except OSError:
        return err_json("無法寫入場景暫存檔，請稍後再試。")
    finally:
        if tmp is not None:
            try:
                os.unlink(tmp)
            except OSError:
                pass
        bridge_lock.release()
        upload_lock.release()


class PreviewHTTPServer(http.server.ThreadingHTTPServer):
    # Browser preload/reload bursts can exceed the default five pending handshakes.
    # Leave room for those connections while the server accepts each request.
    request_queue_size = 128


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # 靜音
        pass

    def _send(self, body: bytes, ctype="application/json; charset=utf-8", status=200):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Geometry-Session", API_SESSION)
        self.send_header("X-Geometry-Version", RUNTIME.version)
        if status == 409:
            self.send_header("X-Geometry-Stale", "1")
        self.send_header("X-Geometry-Release", "engineering-spec-v1-20260928")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/runtime':
            self._send(json.dumps({'schema': 'geometry-runtime/1', 'version': RUNTIME.version,
                                   'fresh': RUNTIME.fresh(), 'root': str(SCENE_DIR),
                                   'pid': os.getpid(), 'session': API_SESSION}).encode())
            return
        if self.path == "/" or self.path == "/index.html":
            if not RUNTIME.fresh():
                self._send(('<!doctype html><html lang="zh-Hant"><meta charset="utf-8">'
                            '<title>應用程式需要重新啟動</title><h1>應用程式需要重新啟動</h1><p>'
                            + RESTART_MESSAGE + '</p></html>').encode(), 'text/html; charset=utf-8', status=409)
                return
            self._send(RUNTIME.index(),
                       "text/html; charset=utf-8")
        elif self.path in RUNTIME.assets and self.path.endswith(('.js', '.css')):
            self._send(RUNTIME.assets[self.path], 'text/css; charset=utf-8' if self.path.endswith('.css')
                       else 'text/javascript; charset=utf-8')
        elif self.path in RUNTIME.vendor:
            ctype = {".js": "text/javascript; charset=utf-8",
                     ".mjs": "text/javascript; charset=utf-8",
                     ".wasm": "application/wasm"}.get(pathlib.Path(self.path).suffix, "application/octet-stream")
            self._send(RUNTIME.vendor[self.path], ctype)
        elif self.path in RUNTIME.static:
            # The public catalog shares the versioned startup capture. Mutable
            # project/feedback data keeps its existing separate lifecycle.
            ctype = ('text/html; charset=utf-8' if self.path == '/axioms' else
                     'text/plain; charset=utf-8' if self.path.startswith('/documents/') else
                     'application/octet-stream')
            self._send(RUNTIME.static[self.path], ctype)
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
        limit = POST_MAX_BYTES.get(self.path)
        if limit is None:
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            self.send_error(400)
            return
        if length < 0 or length > limit:
            self.send_error(413)
            return
        body = self.rfile.read(length)

        # Keep dump/receipts available so a stale server can still be saved.
        # All geometry mutations and derived previews require a current runtime.
        readonly = False
        if self.path == '/api':
            try:
                data = json.loads(body.decode('utf-8'))
                readonly = isinstance(data, dict) and ('receipt' in data or
                           data.get('cmd', '').split(' ', 1)[0] in
                           {'dump', 'objects', 'surfaces', 'boundary', 'references', 'obstacles', 'render', 'pick', 'bhit', 'source-inspect'})
            except (ValueError, UnicodeDecodeError, AttributeError):
                pass
        client_version = self.headers.get('X-Geometry-Version')
        if (self.path != '/feedback' and not readonly and
                (not RUNTIME.fresh() or client_version and client_version != RUNTIME.version)):
            self._send(err_json(RESTART_MESSAGE), status=409)
            return

        if self.path in {"/assembly/preview", "/assembly/generate-preview", "/engineering/preview", "/engineering/validate-project"}:
            from engineering_transport import file_request
            try:
                self._send(file_request(body, ask_bridge, validate_scene=self.path.endswith('validate-project'), assembly=self.path == '/assembly/preview', generation=self.path == '/assembly/generate-preview'))
            except OSError:
                self._send(err_json('無法建立工程資料暫存檔，場景未變更。'))
            return
        if self.path == "/engineering/read":
            self._send(ask_bridge('engineering-read'))
            return
        if self.path == "/sources/snapshot":
            from source_inspector_transport import snapshot_request
            try:
                self._send(snapshot_request(body, ask_bridge))
            except OSError:
                self._send(err_json('無法讀取來源快照，專案未變更。'))
            return

        if self.path == "/feedback":
            # GEO-183:使用者回報收件匣。寫進 repo 的 feedback/(.gitignore 允許清單制,預設不進 git)。
            try:
                result = feedback_store.save(json.loads(body.decode("utf-8")))
            except (ValueError, UnicodeDecodeError, OSError) as exc:
                result = {"ok": False, "error": str(exc) or "bad request"}
            self._send(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            return

        if self.path in {"/model", "/model/verify", "/model/space-preview", "/model/update-preview"}:
            sys.path.insert(0, str(SCENE_DIR / "geometry-core"))
            from modeling import (ModelError, build_package, verify_package,
                                  canonical_bytes, strict_json_loads)
            try:
                data = strict_json_loads(body)
                if self.path == "/model/update-preview":
                    import model_update
                    program = os.environ.get("GEOMETRY_MODEL_UPDATE_BRIDGE")
                    if not program and len(BRIDGE_CMD) == 1 and not BRIDGE_WSL:
                        program = BRIDGE_CMD[0]
                    if not program:
                        raise ModelError("UNSUPPORTED", "UPDATE_EXECUTABLE", "I32", "An actual isolated native executable is required.")
                    result = model_update.prepare_update(data, bridge_executable=program)
                elif self.path == "/model/space-preview":
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
        elif self.path in {"/upload", "/upload/prepare", "/upload/confirm", "/upload/cancel"}:
            # Release upload_lock before sending a response to a slow client.
            self._send(upload_scene(body, self.path.rsplit("/", 1)[-1] if self.path != "/upload" else None))
        else:
            self.send_error(404)


if __name__ == "__main__":
    try:
        host = "0.0.0.0" if os.environ.get("GEOMETRY_MANAGED_PREVIEW") == "1" and PORT == 4173 else "127.0.0.1"
        server = PreviewHTTPServer((host, PORT), Handler)
        print(f"http://localhost:{PORT}  （Ctrl-C 結束；版本={RUNTIME.version[:12]}；bridge={BRIDGE_CMD[0]}）", flush=True)
        server.serve_forever()
    finally:
        for path in _upload_temps:
            try:
                os.unlink(path)
            except OSError:
                pass
        bridge.terminate()
