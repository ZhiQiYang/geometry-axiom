"""Loopback-only independent #49 harness. NOT the formal app/save endpoint.

Uses exactly RuleCaseWorkbenchAdapter.dispatch and registry-verified real native
children. In-memory retain demonstrates the owner port, not .gcanvas/ZIP saving.
Run: python3 geometry-web/rule_case_workbench_standalone.py --port 8879
Build the bridge first through tests/binaries.py; this server never builds one.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import argparse
import json
from pathlib import Path
import threading
import uuid

from rule_case_workbench_adapter import MAX_DATA_BYTES, RuleCaseWorkbenchAdapter

PAGE = '''<!doctype html><html lang="zh-Hant"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>規則案例 · 獨立接線驗證</title>
<link rel="stylesheet" href="/rule-case-workbench.css">
<style>body{margin:0;background:#111724;color:#e8edf5;font:15px system-ui}body>p,body>div{max-width:1200px;margin:16px auto;padding:0 16px}body>div>button{font:inherit;padding:10px;min-height:44px;margin:4px}</style>
<p>獨立元件接線驗證；保留資料只在本頁記憶體，尚未接入正式專案 ZIP。</p>
<div><button id="reopen">重新開啟案例</button><button id="cancelopen">取消開啟</button><button id="restore">載回本頁保留資料</button><span id="retained">metadata history: 0</span></div>
<main id="workbench"></main><script src="/rule-case-workbench.js"></script>
<script>
'use strict';
const hostContext = __CONTEXT__;
let component, pending, openingSequence = 0, saved = null, history = 0;
const ports = {captureContext:()=>structuredClone(hostContext),
  transport:RuleCaseWorkbench.httpPort(),
  retainCaseData:async(data, original, lease)=>{
    if(!lease.isCurrent()||JSON.stringify(original)!==JSON.stringify(hostContext))return {ok:false};
    if(JSON.stringify(saved)===JSON.stringify(data))return {ok:true,changed:false};
    saved=structuredClone(data);history++;
    document.getElementById('retained').textContent='metadata history: '+history;
    return {ok:true,changed:true};
  }};
async function open(){const sequence=++openingSequence;pending?.teardown();component?.teardown();
  const operation=RuleCaseWorkbench.mount(document.getElementById('workbench'),ports);pending=operation;
  try{const result=await operation;if(sequence===openingSequence)component=result;else result.teardown();}
  catch(error){if(sequence===openingSequence)showError(error);}}
document.getElementById('reopen').onclick=()=>open().catch(showError);
document.getElementById('cancelopen').onclick=()=>{++openingSequence;pending?.teardown();component?.teardown();document.getElementById('workbench').replaceChildren();};
document.getElementById('restore').onclick=()=>{if(saved&&component)component.restore(saved).catch(showError);};
function showError(error){document.getElementById('workbench').textContent=error.message;}
open().catch(showError);
</script></html>'''


def make_handler(adapter, context):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def _send(self, status, body, mime="application/json; charset=utf-8"):
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_GET(self):
            if not self._local_request():
                self._send(403, b'{"ok":false,"code":"HOST_ORIGIN"}'); return
            if self.path == "/":
                body = PAGE.replace("__CONTEXT__", json.dumps(context)).encode()
                self._send(200, body, "text/html; charset=utf-8")
            elif self.path in {"/rule-case-workbench.js", "/rule-case-workbench.css"}:
                path = Path(__file__).with_name(self.path[1:])
                mime = "text/javascript" if path.suffix == ".js" else "text/css"
                self._send(200, path.read_bytes(), mime + "; charset=utf-8")
            elif self.path == "/favicon.ico":
                self._send(204, b"")
            else:
                self._send(404, b'{"ok":false}')

        def do_POST(self):
            if not self._local_request():
                self._send(403, b'{"ok":false,"code":"HOST_ORIGIN"}'); return
            length = self.headers.get("Content-Length", "")
            if (self.headers.get("Transfer-Encoding") or not length.isdecimal()
                    or int(length) > MAX_DATA_BYTES):
                self.close_connection = True
                self._send(413, b'{"ok":false,"code":"CAPACITY"}'); return
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                self._send(415, b'{"ok":false,"code":"FORMAT"}'); return
            try:
                body = self.rfile.read(int(length))
                if len(body) != int(length):
                    self.close_connection = True; return
                status, result = adapter.dispatch("POST", self.path, body)
                self._send(status, json.dumps(result, ensure_ascii=False, allow_nan=False).encode())
            except (TimeoutError, ConnectionResetError):
                self.close_connection = True

        def log_message(self, *_):
            pass

        def _local_request(self):
            allowed = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
            host = self.headers.get("Host")
            origin = self.headers.get("Origin")
            return (host in allowed and (not origin or origin == "http://" + host)
                    and self.headers.get("Sec-Fetch-Site") != "cross-site")
    return Handler


class WorkbenchServer(ThreadingHTTPServer):
    daemon_threads = True
    block_on_close = False

    def __init__(self, address, adapter, context):
        self.adapter = adapter
        self.request_slots = threading.BoundedSemaphore(16)
        super().__init__(address, make_handler(adapter, context))

    def process_request(self, request, client_address):
        if not self.request_slots.acquire(blocking=False):
            self.shutdown_request(request); return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self.request_slots.release(); raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.request_slots.release()

    def server_close(self):
        self.adapter.close()
        super().server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8879)
    args = parser.parse_args()
    context = {"projectId": "standalone-case-project", "generation": 0,
               "contextToken": uuid.uuid4().hex}
    adapter = RuleCaseWorkbenchAdapter(capture_context=lambda: context)
    with WorkbenchServer(("127.0.0.1", args.port), adapter, context) as server:
        print(f"Independent rule-case harness: http://127.0.0.1:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
