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
from urllib.parse import urlsplit, parse_qs

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
    "/model/space-replay": 16 * 1024 * 1024,
    "/model/update-preview": 8 * 1024 * 1024,
    "/assembly/preview": 1024 * 1024,
    "/section-profile/preview": 1024 * 1024,
    "/section-profile/hosts": 16 * 1024 * 1024,
    "/assembly/generate-preview": 1024 * 1024,
    "/engineering/preview": 1024 * 1024,
    "/engineering/validate-project": 1024 * 1024,
    "/engineering/read": 1024 * 1024,
    "/sources/snapshot": 1024 * 1024,
    "/scenarios/verify-native": 9 * 1024 * 1024,
    "/scenarios/editor": 1024,
    "/rule-cases/binding": 2048,
    "/rule-cases/workbench": 8 * 1024 * 1024,
    "/rule-cases/prepare": 8 * 1024 * 1024,
}
# 預設用同目錄的 Windows 橋接器。GEOMETRY_BRIDGE 可覆寫，且可帶參數，例如：
#   GEOMETRY_BRIDGE="wsl.exe -d Ubuntu-24.04 --user root -- /opt/geometry/web_bridge"
# 讓 serve.py 跑在 Windows（瀏覽器連得到 localhost），橋接器跑在 WSL——
# Windows 端 web_bridge.exe 被 Smart App Control 封鎖時的解法，
# 且用的是當前核心而非舊二進位。搭配 GEOMETRY_BRIDGE_WSL=1 開啟路徑翻譯。
def bridge_command(environ=None):
    env = os.environ if environ is None else environ
    # A native executable path is one argv element, including spaces and quotes.
    # Keep the older command-string transport for Windows/WSL callers unchanged.
    # An explicitly invalid literal must not fall back to a different executable.
    literal = env.get("GEOMETRY_BRIDGE_EXECUTABLE")
    if literal is not None:
        if not literal or any(c in literal for c in "\r\n\0"):
            raise ValueError("GEOMETRY_BRIDGE_EXECUTABLE must be a nonempty literal executable path")
        return [literal]
    command = env.get("GEOMETRY_BRIDGE")
    return shlex.split(command, posix=False) if command else [str(HERE / "web_bridge.exe")]


BRIDGE_CMD = bridge_command()
BRIDGE_WSL = os.environ.get("GEOMETRY_BRIDGE_WSL") == "1"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765

from native_context import NativeContext

BRIDGE_TIMEOUT = 30.0
MAX_RECEIPTS = 256
root_context = NativeContext(BRIDGE_CMD)
request_context = threading.local()
scenario_contexts = {}
scenario_context_lock = threading.Lock()
MAX_SCENARIO_EDITORS = 8


def current_native_context():
    return getattr(request_context, "native", root_context)


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
    native = current_native_context()
    if not isinstance(cmd, str) or not cmd.strip():
        return err_json("橋接指令不得為空")
    if any(c in cmd for c in "\r\n\0"):
        return err_json("指令不得含換行或 NUL")
    for prefix in ("loadfile ", "load-prepare ", "engineering-preview ", "engineering-validate ", "assembly-preview ", "assembly-generation-preview ", "section-profile-preview ", "source-inspect-file "):
        if cmd.startswith(prefix):
            cmd = prefix + to_bridge_path(cmd[len(prefix):])
            break
    payload = cmd.encode("utf-8")
    if len(payload) > BRIDGE_MAX_CMD:
        return err_json("指令超過單行上限")
    if not native.bridge_lock.acquire(timeout=BRIDGE_TIMEOUT):
        return err_json("橋接器忙碌，請稍後再試")
    try:
        if native.bridge_failure is not None:
            return err_json(native.bridge_failure)
        try:
            native.bridge.stdin.write(payload + b"\n")
            native.bridge.stdin.flush()
            response = native.bridge_responses.get(timeout=BRIDGE_TIMEOUT)
        except queue.Empty:
            native.bridge_failure = "橋接器回應逾時，請重新啟動服務"
        except (OSError, ValueError):
            native.bridge_failure = "橋接器連線中斷，請重新啟動服務"
        else:
            if response:
                return response
            native.bridge_failure = "橋接器已結束，請重新啟動服務"
        return err_json(native.bridge_failure)
    finally:
        native.bridge_lock.release()


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
    native = current_native_context()
    request_id = data.get("receipt", data.get("requestId"))
    if request_id is None:
        return ask_bridge(data["cmd"])
    if (not isinstance(request_id, str) or not re.fullmatch(r"[a-f0-9-]{36}", request_id)
            or data.get("session") != native.session):
        return err_json("操作結果無法確認：服務已重啟或請求識別不合法。")
    if not native.receipt_lock.acquire(timeout=BRIDGE_TIMEOUT):
        return err_json("操作結果仍在處理，請稍後重試。")
    try:
        for ack in data.get("ack", [])[:MAX_RECEIPTS]:
            if isinstance(ack, str) and native.api_receipts.get(ack, (None,))[0] is not None:
                native.api_receipts.pop(ack, None)
        cached = native.api_receipts.get(request_id)
        if cached is None:
            if len(native.api_receipts) >= MAX_RECEIPTS:
                return err_json("未確認的操作結果過多，已暫停新增操作。")
            if "receipt" in data:
                cached = (None, err_json("操作未送達，場景未變更；請重新操作。"))
            else:
                cached = (data["cmd"], ask_bridge(data["cmd"]))
            native.api_receipts[request_id] = cached
        elif "receipt" not in data and cached[0] not in (None, data["cmd"]):
            return err_json("同一操作識別不得用於不同指令。")
        if "receipt" in data:
            return json.dumps({"ok": True, "result": json.loads(cached[1])}, ensure_ascii=False).encode("utf-8")
        return cached[1]
    finally:
        native.receipt_lock.release()


def remember_upload_outcome(token, result):
    native = current_native_context()
    encoded = json.dumps(result, ensure_ascii=False).encode("utf-8")
    native.upload_outcomes[token] = encoded
    if len(native.upload_outcomes) > MAX_RECEIPTS:
        del native.upload_outcomes[next(iter(native.upload_outcomes))]
    return encoded


def upload_scene(body: bytes, phase=None) -> bytes:
    """Keep successful load order and source-file retirement in one transaction."""
    native = current_native_context()
    if not native.upload_lock.acquire(timeout=BRIDGE_TIMEOUT):
        return err_json("場景上傳仍在處理，請稍後再試。")
    # Include ordinary /api reloads in the ordering. ask_bridge re-enters this
    # lock; no request may load an old source between success and its retirement.
    if not native.bridge_lock.acquire(timeout=BRIDGE_TIMEOUT):
        native.upload_lock.release()
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
            if token in native.upload_outcomes:
                terminal = native.upload_outcomes[token]
                if phase == "confirm" and json.loads(terminal).get("state") == "cancelled":
                    return err_json("專案候選已取消，未變更目前專案。")
                return terminal
            if native.prepared_upload is None or native.prepared_upload[0] != token:
                return err_json("專案候選已失效，請重新開啟。")
            tmp = native.prepared_upload[1]
            native.prepared_upload = None
            resp = ask_bridge(f"load-{phase} {token}")
            if phase == "cancel":
                result = json.loads(resp)
                if result.get("ok") is True:
                    result["state"] = "cancelled"
                else:
                    result["state"] = "unknown"
                return remember_upload_outcome(token, result)
        else:
            if native.prepared_upload is not None:
                old_token, old_path = native.prepared_upload
                cancelled = json.loads(ask_bridge(f"load-cancel {old_token}"))
                cancelled["state"] = "cancelled" if cancelled.get("ok") is True else "unknown"
                remember_upload_outcome(old_token, cancelled)
                os.unlink(old_path)
                native.prepared_upload = None
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
            native.prepared_upload = (merged["token"], tmp)
            tmp = None
            return resp
        while native.upload_temps:
            stale = native.upload_temps.pop(0)
            try:
                os.unlink(stale)
            except OSError:
                pass
        native.upload_temps.append(tmp)
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
        native.bridge_lock.release()
        native.upload_lock.release()


def case_host():
    from rule_case_host import RuleCaseHost
    native = current_native_context()
    with native.bridge_lock:
        if not hasattr(native, 'case_host'):
            native.case_host = RuleCaseHost(native, read_native=lambda: json.loads(ask_bridge('assembly-read')),
                version=RUNTIME.version, fresh=RUNTIME.fresh, binary=BRIDGE_CMD[0] if len(BRIDGE_CMD)==1 else None)
        return native.case_host


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
        self.send_header("X-Geometry-Session", current_native_context().session)
        self.send_header("X-Geometry-Version", RUNTIME.version)
        if status == 409:
            self.send_header("X-Geometry-Stale", "1")
        self.send_header("X-Geometry-Release", "engineering-spec-v1-20260928")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # Same Host rule as POST, before any dispatch: a DNS-rebinding page is same-origin with its
        # own name, so only the Host header tells it apart from the real local UI.
        if not self._host_allowed():
            self.send_error(403)
            return
        route = urlsplit(self.path)
        self.path = route.path
        query = parse_qs(route.query)
        if not self._select_native(query.get('scenario', [None])[0]):
            return
        if self.path == '/runtime':
            self._send(json.dumps({'schema': 'geometry-runtime/1', 'version': RUNTIME.version,
                                   'fresh': RUNTIME.fresh(), 'root': str(SCENE_DIR),
                                   'pid': os.getpid(), 'session': current_native_context().session}).encode())
            return
        if self.path == '/rule-cases/binding':
            from rule_case_workbench_adapter import AdapterError
            try:
                self._send(json.dumps(case_host().next_sequence()).encode())
            except AdapterError as exc:
                self._send(json.dumps({'ok':False,'code':exc.code,'error':str(exc)}).encode(), status=409)
            return
        if self.path == '/scenarios/editor':
            if current_native_context() is not root_context:
                self._send(err_json('方案編輯只能由主方案建立或結束。'))
                return
            with scenario_context_lock:
                self._send(json.dumps({'ok':True,'session':root_context.session,
                                       'sequence':root_context.editor_sequence+1}).encode())
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

    def _host_allowed(self) -> bool:
        """GET 與 POST 共用的 Host 規則（防 DNS rebinding）：不帶 Host 放行，否則主機名須在 LOCAL_HOSTS。"""
        host = self.headers.get("Host")
        return host is None or host.rsplit(":", 1)[0] in LOCAL_HOSTS

    def _local_only(self) -> bool:
        """L3：跨站 POST 一律 403；回傳 True = 已拒絕。"""
        origin = self.headers.get("Origin")
        if origin is not None and origin not in LOCAL_ORIGINS:
            self.send_error(403)
            return True
        if not self._host_allowed():
            self.send_error(403)
            return True
        return False

    def _select_native(self, query_context=None):
        request_context.native = root_context
        key = self.headers.get('X-Geometry-Scenario') or query_context
        if key is None:
            return True
        with scenario_context_lock:
            native = scenario_contexts.get(key)
        if not native or native.closed:
            self._send(err_json('方案編輯已失效，未使用目前主方案。'), status=410)
            return False
        request_context.native = native
        return True

    def do_POST(self):
        if self._local_only():
            return
        if not self._select_native():
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

        if self.path.startswith('/rule-cases/'):
            from rule_case_host import prepare_data
            from rule_case_workbench_adapter import AdapterError
            from rule_cases.definition import CaseDefinitionError
            from rule_cases.executor import ReceiptValidationError
            try:
                if self.path == '/rule-cases/binding':
                    status, result = 200, case_host().bind(body)
                elif self.path == '/rule-cases/prepare':
                    status, result = 200, prepare_data(body, BRIDGE_CMD[0] if len(BRIDGE_CMD)==1 else None)
                else:
                    status, result = case_host().dispatch(body)
                self._send(json.dumps(result,ensure_ascii=False,allow_nan=False).encode(),status=status)
            except (AdapterError, CaseDefinitionError, ReceiptValidationError, ValueError) as exc:
                self._send(json.dumps({'ok':False,'code':getattr(exc,'code','SCHEMA'),'error':str(exc)}).encode(),status=409)
            return

        if self.path == '/scenarios/editor':
            from scenario_verify import _program
            from modeling import ModelError, canonical_bytes
            try:
                data = json.loads(body)
                if current_native_context() is not root_context:
                    raise ValueError('方案編輯只能由主方案建立或結束。')
                resolving = type(data) is dict and data.get('action') == 'resolve'
                keys = {'action','requestId','sequence','session'} | ({'context'} if resolving else set())
                if not (type(data) is dict and set(data)==keys and
                        data['action'] in {'create','close','resolve'} and isinstance(data['requestId'],str) and
                        re.fullmatch(r'[a-f0-9-]{36}',data['requestId']) and
                        type(data['sequence']) is int and 0<data['sequence']<=9007199254740991 and
                        data['session']==root_context.session and
                        (not resolving or isinstance(data['context'],str) and re.fullmatch(r'[a-f0-9]{32}',data['context']))):
                    raise ValueError('無效的方案編輯請求。')
                if resolving:
                    # Inspect the exact existing tuple. Never use create as a
                    # probe, allocate a process, ask a native command or retire B.
                    with scenario_context_lock:
                        previous = root_context.editor_creations.get(data['requestId'])
                        if previous:
                            if previous['sequence'] != data['sequence'] or previous['context'] != data['context']:
                                raise ValueError('方案編輯請求身分不一致。')
                            native = scenario_contexts.get(previous['context'])
                            active = bool(native and not native.closed and not native.bridge_failure and native.bridge.poll() is None)
                            result = {'ok':True,'state':'active' if active else 'unavailable',
                                      'session':root_context.session,'requestId':data['requestId'],
                                      'sequence':data['sequence'],'context':data['context']}
                        else:
                            # High water fences old allocations; it does not
                            # prove that this unknown UUID was specifically retired.
                            result = {'ok':True,'state':'absent','fenced':data['sequence']<=root_context.editor_sequence,
                                      'session':root_context.session,'requestId':data['requestId'],
                                      'sequence':data['sequence'],'context':data['context']}
                    self._send(canonical_bytes(result))
                elif data['action']=='create':
                    if BRIDGE_WSL or len(BRIDGE_CMD) != 1:
                        raise ValueError('目前環境缺少可隔離的原生執行器。')
                    command, _ = _program(BRIDGE_CMD[0])
                    with scenario_context_lock:
                        previous=root_context.editor_creations.get(data['requestId'])
                        if previous and previous['sequence']!=data['sequence']:
                            raise ValueError('方案編輯請求身分不一致。')
                        if not previous and data['sequence']<=root_context.editor_sequence:
                            raise ValueError('這次方案編輯已結束，請重新開啟。')
                        if not previous and data['sequence']!=root_context.editor_sequence+1:
                            raise ValueError('方案編輯序號已變更，請重新開啟。')
                        if not previous and len(scenario_contexts) >= MAX_SCENARIO_EDITORS:
                            raise ValueError('方案編輯數量已達上限，請先結束其他編輯。')
                        if previous:
                            native=scenario_contexts[previous['context']]
                        else:
                            native = NativeContext([command])
                            scenario_contexts[native.session] = native
                            root_context.editor_sequence=data['sequence']
                            root_context.editor_creations[data['requestId']]={'sequence':data['sequence'],'context':native.session}
                    self._send(canonical_bytes({'ok': True, 'context': native.session}))
                else:
                    with scenario_context_lock:
                        previous=root_context.editor_creations.get(data['requestId'])
                        if previous:
                            if previous['sequence']!=data['sequence']:
                                raise ValueError('方案編輯請求身分不一致。')
                            native=scenario_contexts[previous['context']]
                            native.close()
                            scenario_contexts.pop(previous['context'])
                            root_context.editor_creations.pop(data['requestId'])
                        elif data['sequence']==root_context.editor_sequence+1:
                            # Cancellation can arrive before an uncertain create.
                            # The scalar high water rejects all later old creates;
                            # no unbounded retired UUID ledger is necessary.
                            root_context.editor_sequence=data['sequence']
                        elif data['sequence']>root_context.editor_sequence:
                            raise ValueError('無效的方案編輯序號。')
                    self._send(canonical_bytes({'ok': True,'state':'retired'}))
            except (ValueError, TypeError, OSError) as exc:
                self._send(err_json(str(exc)))
            except ModelError as exc:
                self._send(canonical_bytes(exc.as_dict()))
            return
        if self.path == '/scenarios/verify-native':
            from scenario_verify import verify_bytes
            from modeling import ModelError, canonical_bytes
            try:
                if BRIDGE_WSL or len(BRIDGE_CMD) != 1:
                    raise ValueError('目前環境缺少可隔離的原生執行器。')
                self._send(canonical_bytes(verify_bytes(body, bridge_executable=BRIDGE_CMD[0])))
            except ValueError as exc:
                self._send(err_json(str(exc)))
            except ModelError as exc:
                self._send(canonical_bytes(exc.as_dict()))
            return
        if self.path in {"/section-profile/preview", "/assembly/preview", "/assembly/generate-preview", "/engineering/preview", "/engineering/validate-project"}:
            from engineering_transport import file_request
            try:
                self._send(file_request(body, ask_bridge, validate_scene=self.path.endswith('validate-project'), assembly=self.path == '/assembly/preview', generation=self.path == '/assembly/generate-preview', section_profile=self.path == '/section-profile/preview'))
            except OSError:
                self._send(err_json('無法建立工程資料暫存檔，場景未變更。'))
            return
        if self.path == "/section-profile/hosts":
            from section_profile_transport import saved_hosts
            from modeling import ModelError, canonical_bytes, strict_json_loads
            try:
                self._send(canonical_bytes(saved_hosts(strict_json_loads(body))))
            except ModelError as exc:
                self._send(canonical_bytes(exc.as_dict()))
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

        if self.path in {"/model", "/model/verify", "/model/space-preview", "/model/space-replay", "/model/update-preview"}:
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
                elif self.path == "/model/space-replay":
                    import space_modeling
                    if type(data) is not dict or set(data) != {"input", "result"}:
                        raise ModelError("INVALID", "INPUT_SCHEMA", "D25", "Expected saved input and result")
                    result = space_modeling.replay_stored(data["input"], data["result"])
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


# ------------------------------------------------------------------ 區網測試模式（P-008／P-041／P-043）
# 預設關閉；只有 `serve.py <port> --lan <IPv4>` 明示才開（設計 W-B DESIGN r2）。上面的 loopback
# 監聽器與 Handler 不變；區網守門全在 LanHandler.parse_request——早於任何 do_* 分派、
# _select_native 與讀 body。沒有任何旗標能讓區網監聽器走 http 或綁 loopback。
import socket  # noqa: E402
import time  # noqa: E402
import lan_guard  # noqa: E402


def _cut(sock):
    """從別的執行緒切斷連線（含 TLS 連線：直接對底層 fd 做 shutdown，不碰 SSL 物件）。"""
    try:
        socket.socket.shutdown(sock, socket.SHUT_RDWR)
    except (OSError, ValueError):
        pass


def _linger(sock, limit=65536, seconds=1.0):
    """拒絕後的 lingering close：先送 FIN，再丟棄對端已送出的少量資料（≤64 KiB、≤1 秒）才關閉。

    直接關閉時，未讀的 body 會讓 OS 送 RST，對端（Windows 尤其）連已收到的 403 一起丟掉，
    看起來像「連不上」。丟棄的資料不解析、不轉交；這不是讀 body——回應早已送出。
    """
    try:
        socket.socket.shutdown(sock, socket.SHUT_WR)
        deadline = time.monotonic() + seconds
        while limit > 0:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            sock.settimeout(remaining)
            chunk = socket.socket.recv(sock, min(limit, 8192))
            if not chunk:
                break
            limit -= len(chunk)
    except (OSError, ValueError):
        pass


class LanHTTPServer(PreviewHTTPServer):
    """區網監聽器：連線數非阻塞上限、標頭總期限巡檢、TLS 交握在工作執行緒（DESIGN §2.4）。"""
    block_on_close = False

    def __init__(self, address, gate, ssl_context=None, ca_der=None):
        self.gate = gate
        self.ssl_context = ssl_context
        self.ca_der = ca_der
        self.slots = threading.BoundedSemaphore(gate.config.max_connections)
        self.pending = {}      # 原始連線 → [目前的 socket 物件, 標頭期限]；標頭（配對 POST 含 body）讀完即移出
        self.active = {}       # 原始連線 → 目前的 socket 物件；關閉區網模式時一併切斷
        self.table_lock = threading.Lock()
        self.worker = threading.local()
        self.stopped = threading.Event()
        super().__init__(address, LanHandler)
        threading.Thread(target=self._watch, name="lan-header-deadline", daemon=True).start()

    def process_request(self, request, client_address):
        # 在 accept 迴圈執行：拿不到名額就立即關閉這條連線，accept 迴圈從不阻塞。
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        with self.table_lock:
            self.pending[request] = [request, time.monotonic() + self.gate.config.header_deadline]
            self.active[request] = request
        try:
            super().process_request(request, client_address)
        except BaseException:
            self._release(request)
            raise

    def process_request_thread(self, request, client_address):
        self.worker.request = request
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._release(request)

    def _release(self, request):
        with self.table_lock:
            self.pending.pop(request, None)
            owned = self.active.pop(request, None) is not None
        if owned:
            self.slots.release()

    def finish_request(self, request, client_address):
        connection = request
        if self.ssl_context is not None:
            # TLS 交握在工作執行緒，受標頭總期限約束；交握失敗就丟例外結束這條連線。
            connection = self.ssl_context.wrap_socket(request, server_side=True)
            with self.table_lock:
                expired = request not in self.pending
                if not expired:
                    self.pending[request][0] = connection
                if request in self.active:
                    self.active[request] = connection
            if expired:
                _cut(connection)
                connection.close()
                return
        try:
            self.RequestHandlerClass(connection, client_address, self)
        finally:
            if connection is not request:
                _cut(connection)
                connection.close()

    def headers_complete(self):
        """移出標頭期限表；回傳 False 表示這條連線已被期限切斷。"""
        with self.table_lock:
            return self.pending.pop(getattr(self.worker, "request", None), None) is not None

    def _watch(self):
        while not self.stopped.wait(self.gate.config.poll):
            now = time.monotonic()
            with self.table_lock:
                late = [request for request, (_, deadline) in self.pending.items() if deadline <= now]
                cut = [self.pending.pop(request)[0] for request in late]
            for sock in cut:
                _cut(sock)

    def stop(self):
        """停止巡檢並切斷所有進行中的區網連線（listener 由呼叫端 shutdown／server_close）。"""
        self.stopped.set()
        with self.table_lock:
            current = list(self.active.values())
        for sock in current:
            _cut(sock)

    def handle_error(self, request, client_address):
        error = sys.exc_info()[1]
        if isinstance(error, OSError):  # 交握失敗、被期限切斷、對端中斷：預期中的，不印
            return
        print(f"區網連線處理錯誤（{client_address[0]}）：{type(error).__name__}", file=sys.stderr, flush=True)


class LanHandler(Handler):
    """區網請求：每個請求先經 LanGate.check()，通過才進既有 do_GET／do_POST。"""
    timeout = 60           # 標頭之後（只剩已驗證者）每次讀取的上限
    lan_route = None
    lan_headers_done = False
    lan_linger = False     # 送出錯誤回應後要 lingering close

    def finish(self):
        super().finish()
        if self.lan_linger:
            _linger(self.connection)

    def send_error(self, code, message=None, explain=None):
        self.lan_linger = True
        super().send_error(code, message, explain)

    def parse_request(self):
        if not super().parse_request():
            return False
        route, _reason = self.server.gate.check(self.command, self.path, self.headers)
        if route is None:
            self._lan_reply(403)
            return False
        if route != "pair-submit" and not self._lan_finish_headers():
            self.close_connection = True
            return False
        self.lan_route = route
        return True

    def _lan_finish_headers(self):
        if self.lan_headers_done:
            return True
        self.lan_headers_done = True
        return self.server.headers_complete()

    def _host_allowed(self) -> bool:
        # S9 的 loopback Host 規則（只認 LOCAL_HOSTS）；區網的 Host 已在 parse_request 逐字比對 <ip>:<P>。
        return True

    def _local_only(self) -> bool:
        # L3 的 loopback 來源規則；區網的 Origin／Fetch-Metadata 已在 parse_request 守門。
        return False

    def end_headers(self):
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        super().end_headers()

    def _lan_reply(self, status, body=b"", ctype=None, extra=()):
        """區網專用回應：不帶 session／版本標頭，一律 Connection: close；拒絕是空白 403。"""
        if status >= 400:
            self.lan_linger = True
        self.send_response(status)
        if ctype:
            self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for name, value in extra:
            self.send_header(name, value)
        self.send_header("Connection", "close")
        self.end_headers()
        if body and self.command != "HEAD":
            self.wfile.write(body)

    def do_GET(self):
        if self.lan_route == "pair-page":
            self._lan_reply(200, lan_guard.PAIR_PAGE, "text/html; charset=utf-8",
                            [("Content-Security-Policy", lan_guard.PAIR_PAGE_CSP)])
        elif self.lan_route == "ca":
            self._lan_reply(200, self.server.ca_der, "application/pkix-cert",
                            [("Content-Disposition", 'attachment; filename="geometry-lan-ca.cer"')])
        else:
            super().do_GET()

    def do_POST(self):
        if self.lan_route == "pair-submit":
            self._lan_pair()
        else:
            super().do_POST()

    def _lan_pair(self):
        gate = self.server.gate
        if not self.headers.get_all("Origin"):  # 配對 POST 必帶 Origin（值已在守門逐字比對）
            return self._lan_reply(403)
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            return self._lan_reply(403)
        if not 0 <= length <= lan_guard.PAIR_MAX_BYTES:
            return self._lan_reply(403)
        if not gate.take_pair_slot():
            return self._lan_reply(429)
        body = self.rfile.read(length)
        if not self._lan_finish_headers():  # body 也在標頭總期限內讀完
            self.close_connection = True
            return
        result = gate.redeem(body, peer=self.client_address[0], user_agent=self.headers.get("User-Agent", ""))
        if result is None:
            return self._lan_reply(403)
        token, max_age = result
        self._lan_reply(204, extra=[("Set-Cookie", f"{lan_guard.COOKIE_NAME}={token}; Secure; HttpOnly; "
                                                   f"SameSite=Strict; Path=/; Max-Age={max_age}")])


class LanMode:
    """跑一個 LanHTTPServer：服務執行緒 + 計時執行緒（TTL、閒置、配對碼過期且零裝置 → 關閉）。"""

    def __init__(self, gate, server, log=None):
        self.gate = gate
        self.server = server
        self.log = log or (lambda line: print(line, file=sys.stderr, flush=True))
        self.stop_request = threading.Event()
        self.closed = threading.Event()
        self.reason = None
        self.stop_reason = "服務結束"

    def start(self):
        threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.2},
                         name="lan-serve", daemon=True).start()
        threading.Thread(target=self._lifecycle, name="lan-lifecycle", daemon=True).start()
        return self

    def _lifecycle(self):
        reason = None
        while reason is None:
            if self.stop_request.wait(self.gate.config.poll):
                reason = self.stop_reason
                self.gate.close(reason)
                break
            reason = self.gate.poll()
        self.reason = reason
        self.server.stop()
        self.server.shutdown()
        self.server.server_close()
        self.log(f"區網測試模式已關閉（{reason}）；本機 http://localhost:{self.gate.config.port}/ 照常")
        self.closed.set()

    def stop(self, reason="服務結束"):
        if not self.closed.is_set():
            self.stop_reason = reason
            self.stop_request.set()
        self.closed.wait(10)


def bind_lan_listeners(config, gate, ssl_context, ca_der=None):
    """先綁區網介面（由 OS 證明該 IP 屬本機），再綁 127.0.0.1；任一失敗就全部關閉並拒絕。"""
    try:
        lan = LanHTTPServer((config.ip, config.port), gate, ssl_context, ca_der)
    except OSError as exc:
        raise lan_guard.LanRefused(f"無法綁定 {config.ip}:{config.port}（{exc.strerror or exc}）；"
                                   "該 IP 可能不屬本機介面，或埠已被占用") from None
    try:
        loopback = PreviewHTTPServer(("127.0.0.1", config.port), Handler)
    except OSError as exc:
        lan.stop()
        lan.server_close()
        raise lan_guard.LanRefused(f"無法綁定 127.0.0.1:{config.port}（{exc.strerror or exc}）") from None
    return lan, loopback


class LanRuntime:
    def __init__(self, config, gate, material, mode, loopback):
        self.config, self.gate, self.material, self.mode, self.loopback = config, gate, material, mode, loopback


def lan_prepare(argv, log):
    """解析與驗證旗標、取得 TLS 材料、綁定兩個監聽器；任何拒絕都是 LanRefused 且不留任何監聽。"""
    import lan_tls
    args = lan_guard.parse_args(argv)
    if args.lan_forget:
        removed = lan_tls.forget()
        log(f"已刪除 {removed}" if removed else "沒有保存的區網伺服器憑證")
        return None
    config = lan_guard.validate(args, port=PORT, repo_root=SCENE_DIR, crypto_check=lan_tls.require)
    material = lan_tls.load_or_issue(config.ip, config.port, config.cert_days,
                                     lan_tls.state_directory(config.ip, config.port))
    gate = lan_guard.LanGate(config, log=log)
    lan, loopback = bind_lan_listeners(config, gate, lan_tls.server_context(material),
                                       material.ca_der if config.serve_ca else None)
    return LanRuntime(config, gate, material, LanMode(gate, lan, log), loopback)


def lan_main(argv):
    """`serve.py <port> --lan <IPv4> …`；拒絕時回傳 2，區網與 loopback 都不開。"""
    def log(line):
        print(line, file=sys.stderr, flush=True)
    try:
        runtime = lan_prepare(argv, log)
    except lan_guard.LanRefused as exc:
        log(f"拒絕開啟區網測試模式：{exc}（未開任何監聽，含本機 http）")
        return 2
    if runtime is None:
        return 0
    import lan_tls
    runtime.mode.start()
    loopback = threading.Thread(target=runtime.loopback.serve_forever, name="loopback-serve", daemon=True)
    loopback.start()
    print(f"http://localhost:{PORT}  （Ctrl-C 結束；版本={RUNTIME.version[:12]}；bridge={BRIDGE_CMD[0]}）", flush=True)
    try:
        lan_guard.announce(runtime.config, runtime.gate, ca_path=runtime.material.ca_path,
                           fingerprint=runtime.material.fingerprint, reused=runtime.material.reused,
                           pairing_path=runtime.material.pairing_path, tty=sys.stderr.isatty(), log=log)
        while loopback.is_alive():
            loopback.join(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        runtime.mode.stop("服務結束")
        runtime.loopback.shutdown()
        runtime.loopback.server_close()
        lan_tls.discard_pairing(runtime.material.directory)
    return 0


if __name__ == "__main__":
    try:
        if lan_guard.lan_requested(sys.argv[2:]):  # 區網測試模式只在明示 --lan 旗標時進入；無旗標路徑不變
            sys.exit(lan_main(sys.argv[2:]))
        host = "0.0.0.0" if os.environ.get("GEOMETRY_MANAGED_PREVIEW") == "1" and PORT == 4173 else "127.0.0.1"
        server = PreviewHTTPServer((host, PORT), Handler)
        print(f"http://localhost:{PORT}  （Ctrl-C 結束；版本={RUNTIME.version[:12]}；bridge={BRIDGE_CMD[0]}）", flush=True)
        server.serve_forever()
    finally:
        root_context.close()
        for context in list(scenario_contexts.values()):
            context.close()
