#!/usr/bin/env python3
"""P78 diagnostic host. Wrap I/O boundaries; do not edit serve/native sources.

Usage: p78_server.py PORT OUTPUT_DIRECTORY BRIDGE HOLD_SECONDS
The optional, one-shot hold is BEFORE native stdin write, under the real lock.
It models queue occupancy, not native CPU work or the historical WSL incident.
"""
import hashlib
import json
import os
from pathlib import Path
import queue
import signal
import sys
import threading
import time

ROOT = Path(os.environ.get('P78_SOURCE_ROOT', Path(__file__).resolve().parents[2])).resolve()
PORT, OUT, BRIDGE, HOLD = int(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], float(sys.argv[4])
os.environ['GEOMETRY_BRIDGE_EXECUTABLE'] = BRIDGE
os.environ['GEOMETRY_FEEDBACK_DIR'] = str(OUT / 'feedback')
sys.path.insert(0, str(ROOT / 'geometry-web'))
sys.argv = [str(ROOT / 'geometry-web/serve.py'), str(PORT)]
import serve  # noqa: E402

sink = (OUT / 'server.jsonl').open('x', encoding='utf-8')
write_lock = threading.Lock()
local = threading.local()
active = None  # The existing bridge lock serializes stdin/response pairing.
held = False


def emit(event, **fields):
    row = dict(event=event, mono_ns=time.monotonic_ns(), epoch_ns=time.time_ns(),
               pid=os.getpid(), thread=threading.get_ident(),
               rid=getattr(local, 'rid', None), cmd=getattr(local, 'cmd', None), **fields)
    with write_lock:
        sink.write(json.dumps(row, ensure_ascii=False) + '\n')
        sink.flush()


class Lock:
    def __init__(self, lock):
        self.lock = lock

    def acquire(self, *args, **kwargs):
        emit('bridge.queue.enter')
        result = self.lock.acquire(*args, **kwargs)
        emit('bridge.lock.acquired', acquired=result)
        return result

    def release(self):
        self.lock.release()
        emit('bridge.lock.released')

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *_):
        self.release()


class Input:
    def __init__(self, stream):
        self.stream = stream

    def write(self, value):
        global held, active
        if HOLD and not held and value.startswith(b'grid-trial-query '):
            held = True
            emit('injection.hold.begin', seconds=HOLD, location='before stdin.write, lock held')
            time.sleep(HOLD)
            emit('injection.hold.end')
        active = {'rid': getattr(local, 'rid', None), 'cmd': getattr(local, 'cmd', None)}
        emit('bridge.stdin.write', bytes=len(value), bridge_pid=serve.root_context.bridge.pid)
        return self.stream.write(value)

    def flush(self):
        result = self.stream.flush()
        emit('bridge.stdin.flushed')
        return result

    def __getattr__(self, name):
        return getattr(self.stream, name)


class Responses:
    def __init__(self, original):
        self.original = original

    def put(self, value, *args, **kwargs):
        emit('bridge.stdout.received', correlation=active, bytes=len(value),
             sha256=hashlib.sha256(value).hexdigest(),
             trial_payload=value.decode('utf-8') if (active or {}).get('cmd', '').startswith('grid-trial-query ') else None)
        return self.original.put(value, *args, **kwargs)

    def get(self, *args, **kwargs):
        try:
            result = self.original.get(*args, **kwargs)
        except queue.Empty:
            emit('bridge.response.timeout')
            raise
        emit('bridge.response.delivered', bytes=len(result))
        return result


native = serve.root_context
native.bridge_lock = Lock(native.bridge_lock)
native.bridge.stdin = Input(native.bridge.stdin)
native.bridge_responses = Responses(native.bridge_responses)
original_ask = serve.ask_bridge


def ask(cmd):
    local.cmd = cmd
    emit('bridge.call.begin')
    try:
        return original_ask(cmd)
    finally:
        emit('bridge.call.end')


serve.ask_bridge = ask


class Handler(serve.Handler):
    def do_POST(self):
        local.rid = self.headers.get('X-P78-Request-ID')
        local.cmd = None
        emit('server.request.begin', path=self.path)
        try:
            return super().do_POST()
        except (BrokenPipeError, ConnectionResetError) as error:
            emit('server.client.disconnected', error=repr(error))
        finally:
            emit('server.request.end')
            local.rid = local.cmd = None

    def _send(self, *args, **kwargs):
        emit('server.response.begin', status=kwargs.get('status', 200))
        result = super()._send(*args, **kwargs)
        emit('server.response.end')
        return result


def stop(*_):
    raise KeyboardInterrupt


signal.signal(signal.SIGTERM, stop)
server = serve.PreviewHTTPServer(('127.0.0.1', PORT), Handler)
emit('server.ready', port=PORT, root=str(ROOT), bridge_pid=native.bridge.pid,
     bridge_path=BRIDGE, bridge_sha256=hashlib.sha256(Path(BRIDGE).read_bytes()).hexdigest(),
     runtime=serve.RUNTIME.version, bridge_timeout=serve.BRIDGE_TIMEOUT)
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    server.server_close()
    native.close()
    emit('server.closed', bridge_exit=native.bridge.returncode)
    sink.close()
