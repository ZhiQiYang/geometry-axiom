"""Opt-in diagnostic events. Never alter a command, timeout or response."""
import json
import os
from pathlib import Path
import threading
import time
import uuid
import queue
import atexit

ENABLED = os.environ.get('GEOMETRY_WAIT_TRACE') == '1'
DIRECTORY = os.environ.get('GEOMETRY_FEEDBACK_DIR')
_local = threading.local()

class Writer:
    """Bounded non-waiting handoff; only this thread accesses the file sink."""
    def __init__(self, directory, capacity=256, run_id=None):
        self.directory = directory
        self.run_id = run_id or str(uuid.uuid4())
        self.pending = queue.Queue(maxsize=capacity)
        self.stats_lock = threading.Lock()
        self.dropped = self.errors = self.written = 0
        self.sink_seconds = 0.0
        self.closed = False
        self.thread = threading.Thread(target=self.run, name='wait-trace-writer', daemon=True)
        self.thread.start()

    def statistics(self):
        with self.stats_lock:
            return dict(droppedEvents=self.dropped, writeErrors=self.errors,
                        writtenEvents=self.written, sinkSeconds=self.sink_seconds,
                        incomplete=bool(self.dropped or self.errors))

    def submit(self, row):
        if not self.closed:
            try:
                self.pending.put_nowait(dict(row, traceRunId=self.run_id))
                return True
            except queue.Full:
                pass
        with self.stats_lock:
            self.dropped += 1
        return False

    def write(self, row):
        # Neither queue nor stats mutex is held during encoding or file I/O.
        started = time.monotonic()
        try:
            row = dict(row, traceRunId=self.run_id, sinkThread=threading.get_ident(),
                       sinkStartedMonotonic=started,
                       queueDelaySeconds=max(0, started - row.get('monotonic', started)))
            Path(self.directory).mkdir(parents=True, exist_ok=True)
            with (Path(self.directory) / 'wait-trace.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(row, ensure_ascii=False) + '\n')
            with self.stats_lock:
                self.written += 1
        except (OSError, ValueError, TypeError):
            with self.stats_lock:
                self.errors += 1
        finally:
            with self.stats_lock:
                self.sink_seconds += max(0, time.monotonic() - started)

    def run(self):
        self.write(dict(stage='trace_start', monotonic=time.monotonic(), pid=os.getpid()))
        while True:
            try:
                row = self.pending.get(timeout=.02)
            except queue.Empty:
                if self.closed:
                    break
                continue
            if isinstance(row, threading.Event):
                row.set()
            else:
                self.write(row)
            self.pending.task_done()
        self.write(dict(stage='trace_complete', monotonic=time.monotonic(), **self.statistics()))

    def flush(self, timeout=5):
        # Explicit diagnostic/test barrier. Never called by business operations.
        barrier = threading.Event()
        try:
            self.pending.put_nowait(barrier)
        except queue.Full:
            return False
        return barrier.wait(timeout)

    def close(self, timeout=1):
        if self.closed:
            return not self.thread.is_alive() and not self.statistics()['incomplete']
        self.closed = True
        self.thread.join(timeout)
        return not self.thread.is_alive() and not self.statistics()['incomplete']


_writer = Writer(DIRECTORY, run_id=os.environ.get('GEOMETRY_WAIT_TRACE_RUN_ID')) if ENABLED and DIRECTORY else None


def flush(timeout=5):
    return _writer.flush(timeout) if _writer else True


def close(timeout=1):
    return _writer.close(timeout) if _writer else True


if _writer:
    atexit.register(close)


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
    _writer.submit(row)


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
        metadata_seconds = time.monotonic() - started
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
        emit(self.name, seconds=finished - wait_started, acquired=acquired, holder=holder,
             metadataSeconds=metadata_seconds, acquiredMonotonic=finished,
             prePublishAcquireSeconds=time.monotonic() - started)
        return acquired

    def release(self):
        holder = None
        with self.metadata:
            # Snapshot ownership while guarded; publish only after both unlocks.
            if self.depth == 1 and self.owner:
                holder = dict(self.owner)
            self.lock.release()
            released = time.monotonic()
            self.depth -= 1
            if not self.depth:
                self.owner = None
        if holder:
            held_seconds = released - holder.pop('since')
            emit(self.name + '_release', holder=holder, heldSeconds=held_seconds,
                 releasedMonotonic=released)

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
