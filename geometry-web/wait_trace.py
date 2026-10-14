"""Opt-in diagnostic events. Never alter a command, timeout or response."""
import json
import os
from pathlib import Path
import threading
import time
import uuid

ENABLED = os.environ.get('GEOMETRY_WAIT_TRACE') == '1'
DIRECTORY = os.environ.get('GEOMETRY_FEEDBACK_DIR')
_local = threading.local()
_output_lock = threading.Lock()


def begin(route):
    if ENABLED:
        _local.request = {'traceRequestId': str(uuid.uuid4()), 'route': route,
                          'command': None, 'businessRequestId': None}
        emit('request_begin')


def command(value, business_id=None):
    if ENABLED and getattr(_local, 'request', None) is not None:
        _local.request.update(command=value, businessRequestId=business_id)


def end():
    if ENABLED:
        emit('request_end')
        _local.request = None


def emit(stage, **fields):
    request = getattr(_local, 'request', None)
    if not ENABLED or not DIRECTORY or request is None:
        return
    row = dict(request, stage=stage, monotonic=time.monotonic(),
               wallTime=time.time(), pid=os.getpid(), thread=threading.get_ident(), **fields)
    # Diagnostic I/O failure must never turn a successful mutation into a retry.
    try:
        with _output_lock:
            Path(DIRECTORY).mkdir(parents=True, exist_ok=True)
            with (Path(DIRECTORY) / 'wait-trace.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(row, ensure_ascii=False) + '\n')
    except (OSError, ValueError):
        pass


def call(stage, operation):
    if not ENABLED:
        return operation()
    emit(stage + '_begin')
    started = time.monotonic()
    error = None
    try:
        return operation()
    except BaseException as exc:
        error = type(exc).__name__
        raise
    finally:
        emit(stage, seconds=time.monotonic() - started, error=error)


class TracedLock:
    def __init__(self, lock, name):
        self.lock, self.name = lock, name
        self.metadata = threading.Lock()
        self.owner = None
        self.depth = 0

    def acquire(self, *args, **kwargs):
        started = time.monotonic()
        with self.metadata:
            holder = dict(self.owner) if self.owner else None
        if holder:
            holder['heldSeconds'] = started - holder.pop('since')
        emit(self.name + '_begin', holder=holder)
        wait_started = time.monotonic()
        acquired = self.lock.acquire(*args, **kwargs)
        finished = time.monotonic()
        if acquired:
            with self.metadata:
                if self.owner and self.owner['thread'] == threading.get_ident():
                    self.depth += 1
                else:
                    self.owner = dict(getattr(_local, 'request', None) or {},
                                      thread=threading.get_ident(), since=finished)
                    self.depth = 1
        emit(self.name, seconds=finished - wait_started, acquired=acquired, holder=holder)
        return acquired

    def release(self):
        with self.metadata:
            # Clear metadata before unlock so the next acquirer cannot overwrite it.
            self.lock.release()
            self.depth -= 1
            if not self.depth:
                self.owner = None

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *args):
        self.release()


def wrap_lock(lock, name):
    return TracedLock(lock, name) if ENABLED else lock


def native(context):
    if ENABLED:
        context.bridge_lock = wrap_lock(context.bridge_lock, 'bridge_lock')
        context.receipt_lock = wrap_lock(context.receipt_lock, 'receipt_lock')
    return context
