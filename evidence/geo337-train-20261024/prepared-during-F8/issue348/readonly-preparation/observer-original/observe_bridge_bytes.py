"""External Linux observer: retain original BridgeSession pipe bytes.

No Popen replacement, TextIOWrapper detach, retry, timeout change, JSON
reserialization or invented child return code. Original stream objects remain.
The only post-terminal read is a nonblocking raw stdout drain at original close.
An incomplete observation is reported separately from the subject outcome.
"""
from __future__ import annotations

import functools
import hashlib
import importlib.abc
import importlib.machinery
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ENV_KEYS = ('PATH', 'LANG', 'LC_ALL', 'TMPDIR', 'CC', 'CFLAGS', 'CPPFLAGS',
            'LDFLAGS', 'PYTHONOPTIMIZE', 'PYTHONDONTWRITEBYTECODE', 'PYTHONPATH')


def sha(body):
    return hashlib.sha256(body).hexdigest()


def serial(value):
    if isinstance(value, os.PathLike): return os.fspath(value)
    if value is None or isinstance(value, (str, int, float, bool)): return value
    if isinstance(value, (list, tuple)): return [serial(v) for v in value]
    if isinstance(value, dict): return {str(k): serial(v) for k, v in value.items()}
    if isinstance(value, bytes): return {'type': 'bytes', 'bytes': len(value), 'sha256': sha(value)}
    return {'type': type(value).__name__, 'repr': repr(value)}


def error_record(exc):
    return {'type': type(exc).__name__, 'repr': repr(exc)}


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


class Observer:
    def __init__(self, out, source_sha, root):
        self.out, self.root = Path(out).resolve(), Path(root).resolve()
        self.source_sha = source_sha
        self.out.mkdir(parents=True, exist_ok=False)
        self.errors, self.sessions, self.commands, self.patches = [], [], [], []
        self.classes = set()
        self.finder = None
        self.active = True

    def safe(self, operation, label):
        try: return operation()
        except Exception as exc:
            self.errors.append({'where': label, **error_record(exc)})
            return None

    def patch(self, obj, name, value):
        had_own = name in getattr(obj, '__dict__', {})
        old = getattr(obj, name)
        setattr(obj, name, value)
        self.patches.append((obj, name, had_own, old))

    def attach(self, session, bound):
        folder = self.out / ('session-%06d' % (len(self.sessions) + 1))
        folder.mkdir()
        process = session.process
        env = bound.get('env')
        if env is None: env = os.environ
        row = {'folder': str(folder), 'source_sha': self.source_sha,
               'started_epoch': time.time(), 'argv': serial(process.args),
               'pid': process.pid, 'cwd': serial(bound.get('cwd') or os.getcwd()),
               'environment': {k: env.get(k) for k in ENV_KEYS},
               'stop_timeout': session.stop_timeout, 'actual_returncode': None,
               'original_exceptions': [], 'wait_events': [], 'kill_events': [],
               'stdout_eof': False, 'stderr_retained': False,
               'post_terminal_drain': 'nonblocking, at original raw close only',
               'raw_stream_objects_preserved': True}
        self.sessions.append(row)
        binary = Path(session.bridge).resolve()
        body = binary.read_bytes()
        row['binary'] = {'path': str(binary), 'bytes': len(body), 'sha256': sha(body)}
        handles = {name: (folder / (name + '.bin')).open('wb')
                   for name in ('stdin', 'stdout', 'stderr')}
        hashes = {name: hashlib.sha256() for name in handles}
        counts = {name: 0 for name in handles}
        row['_handles'], row['_hashes'], row['_counts'] = handles, hashes, counts
        row['_process'] = process
        setattr(session, '_original_bytes_observation', row)

        def append(name, data):
            data = bytes(data)
            def save():
                handles[name].write(data)
                hashes[name].update(data)
                counts[name] += len(data)
            self.safe(save, name + '-raw-write')

        stdin_raw = process.stdin.buffer.raw
        stdout_raw = process.stdout.buffer.raw
        original_write = stdin_raw.write
        def observed_write(data):
            result = original_write(data)
            if type(result) is int and result > 0: append('stdin', memoryview(data)[:result])
            return result
        self.patch(stdin_raw, 'write', observed_write)
        original_readinto = stdout_raw.readinto
        def observed_readinto(buffer):
            result = original_readinto(buffer)
            if type(result) is int and result > 0: append('stdout', memoryview(buffer)[:result])
            elif result == 0: row['stdout_eof'] = True
            return result
        self.patch(stdout_raw, 'readinto', observed_readinto)
        for name in ('read', 'readall'):
            original = getattr(stdout_raw, name)
            def observed_read(*args, _original=original, **kwargs):
                result = _original(*args, **kwargs)
                if result: append('stdout', result)
                elif result == b'': row['stdout_eof'] = True
                return result
            self.patch(stdout_raw, name, observed_read)

        original_stdout_close = stdout_raw.close
        drained = False
        def observed_stdout_close():
            nonlocal drained
            if not drained and not stdout_raw.closed:
                drained = True
                def drain():
                    if type(process.returncode) is not int:
                        row['stdout_drain_incomplete_reason'] = 'original child not terminal at close'
                        return
                    fd = stdout_raw.fileno()
                    was_blocking = os.get_blocking(fd)
                    os.set_blocking(fd, False)
                    try:
                        while True:
                            try: data = os.read(fd, 65536)
                            except BlockingIOError:
                                row['stdout_drain_incomplete_reason'] = 'nonblocking EAGAIN after original child terminal'
                                break
                            if not data:
                                row['stdout_eof'] = True
                                break
                            append('stdout', data)
                    finally: os.set_blocking(fd, was_blocking)
                self.safe(drain, 'post-terminal-stdout-drain')
            return original_stdout_close()
        self.patch(stdout_raw, 'close', observed_stdout_close)

        original_stderr_close = session.stderr.close
        retained_stderr = False
        def observed_stderr_close():
            nonlocal retained_stderr
            if not retained_stderr and not session.stderr.closed:
                retained_stderr = True
                def retain_stderr():
                    if type(process.returncode) is not int:
                        row['stderr_incomplete_reason'] = 'original child not terminal at stderr close'
                        return
                    fd, offset = session.stderr.fileno(), 0
                    size = os.fstat(fd).st_size
                    while offset < size:
                        data = os.pread(fd, min(65536, size - offset), offset)
                        if not data: raise OSError('stderr shortened during retention')
                        append('stderr', data)
                        offset += len(data)
                    row['stderr_retained'] = type(process.returncode) is int
                    row['stderr_original_bytes'] = size
                self.safe(retain_stderr, 'stderr-before-original-close')
            return original_stderr_close()
        self.patch(session.stderr, 'close', observed_stderr_close)

        original_wait = process.wait
        def observed_wait(*args, **kwargs):
            event = {'args': serial(args), 'kwargs': serial(kwargs)}
            row['wait_events'].append(event)
            try:
                result = original_wait(*args, **kwargs)
            except BaseException as exc:
                event['exception'] = error_record(exc)
                raise
            event['result'] = result
            row['actual_returncode'] = process.returncode
            return result
        self.patch(process, 'wait', observed_wait)
        original_kill = process.kill
        def observed_kill(*args, **kwargs):
            event = {'args': serial(args), 'kwargs': serial(kwargs)}
            row['kill_events'].append(event)
            try: return original_kill(*args, **kwargs)
            except BaseException as exc:
                event['exception'] = error_record(exc)
                raise
        self.patch(process, 'kill', observed_kill)
        self.safe(lambda: self.flush_session(row), 'session-initial-metadata')

    def flush_session(self, row):
        row['actual_returncode'] = row['_process'].returncode
        row['streams'] = {}
        for name, handle in row['_handles'].items():
            if not handle.closed: handle.flush()
            row['streams'][name] = {'path': str(Path(row['folder']) / (name + '.bin')),
                                    'representation': 'original-predecode-pipe-bytes' if name != 'stderr' else 'original-stderr-file-bytes',
                                    'bytes': row['_counts'][name], 'sha256': row['_hashes'][name].hexdigest()}
        row['complete'] = (type(row['actual_returncode']) is int and
                           row['stdout_eof'] and row['stderr_retained'])
        write_json(Path(row['folder']) / 'receipt.json', {k: v for k, v in row.items() if not k.startswith('_')})

    def install_class(self, cls):
        if cls in self.classes: return
        self.classes.add(cls)
        original_init = cls.__init__
        @functools.wraps(original_init)
        def init(session, *args, **kwargs):
            original_init(session, *args, **kwargs)
            bound = inspect.signature(original_init).bind(session, *args, **kwargs)
            self.safe(lambda: self.attach(session, bound.arguments), 'attach-original-session')
        self.patch(cls, '__init__', init)
        original_command = cls.command
        @functools.wraps(original_command)
        def command(session, *args, **kwargs):
            try: return original_command(session, *args, **kwargs)
            except BaseException as exc:
                row = getattr(session, '_original_bytes_observation', None)
                if row is not None: row['original_exceptions'].append({'operation': 'command', **error_record(exc)})
                raise
        self.patch(cls, 'command', command)
        self.patch(cls, 'send', command)
        original_stop = cls.stop
        @functools.wraps(original_stop)
        def stop(session, *args, **kwargs):
            try: return original_stop(session, *args, **kwargs)
            except BaseException as exc:
                row = getattr(session, '_original_bytes_observation', None)
                if row is not None: row['original_exceptions'].append({'operation': 'stop', **error_record(exc)})
                raise
            finally:
                row = getattr(session, '_original_bytes_observation', None)
                if row is not None:
                    row['ended_epoch'] = time.time()
                    self.safe(lambda: self.flush_session(row), 'session-terminal-metadata')
        self.patch(cls, 'stop', stop)
        self.patch(cls, 'close', stop)

    def install_imports(self):
        observer = self
        names = {'tests._bridge', '_bridge'}
        def install(module):
            actual = Path(module.__file__).resolve()
            if actual != observer.root / 'tests/_bridge.py':
                raise RuntimeError('unexpected BridgeSession module source: ' + str(actual))
            observer.install_class(module.BridgeSession)
        class Loader(importlib.abc.Loader):
            def __init__(self, original): self.original = original
            def create_module(self, spec):
                method = getattr(self.original, 'create_module', None)
                return method(spec) if method else None
            def exec_module(self, module):
                self.original.exec_module(module)
                install(module)
        class Finder(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname not in names: return None
                spec = importlib.machinery.PathFinder.find_spec(fullname, path, target)
                if spec is not None and spec.loader is not None: spec.loader = Loader(spec.loader)
                return spec
        for name in names:
            if name in sys.modules: install(sys.modules[name])
        self.finder = Finder()
        sys.meta_path.insert(0, self.finder)

    def install_run(self):
        original = subprocess.run
        @functools.wraps(original)
        def observed(*args, **kwargs):
            number, started = len(self.commands) + 1, time.time()
            active_env = kwargs.get('env')
            if active_env is None: active_env = os.environ
            row = {'number': number, 'started_epoch': started, 'args': serial(args),
                   'kwargs': serial({k: v for k, v in kwargs.items() if k != 'env'}),
                   'selected_environment': {k: active_env.get(k) for k in ENV_KEYS}}
            self.commands.append(row)
            folder = self.out / ('command-%06d' % number)
            def retain_executable():
                argv = args[0] if args else kwargs.get('args')
                if not isinstance(argv, (list, tuple)) or not argv:
                    return {'retained': False, 'reason': 'original argv is not a nonempty sequence'}
                executable = kwargs.get('executable') or argv[0]
                path = Path(os.fsdecode(executable))
                if not path.is_absolute():
                    path = Path(kwargs.get('cwd') or os.getcwd()) / path
                path = path.resolve()
                private_tmp = Path(os.environ.get('TMPDIR', '/tmp')).resolve()
                if not (path.is_relative_to(self.root) or path.is_relative_to(private_tmp)):
                    return {'retained': False, 'reason': 'system executable outside original source/private TMPDIR', 'argv0': serial(executable)}
                if not path.is_file():
                    return {'retained': False, 'reason': 'no original executable at this explicit path before launch', 'path': str(path)}
                body = path.read_bytes()
                return {'retained': True, 'path': str(path), 'bytes': len(body), 'sha256': sha(body),
                        'event': 'before-original-subprocess.run', 'payload_retained': False}
            def retain(value, name):
                if value is None: return {'captured': False}
                if isinstance(value, bytes): body, representation = value, 'original-bytes'
                elif isinstance(value, str): body, representation = value.encode('utf-8'), 'original-decoded-text-encoded-utf8'
                else: raise TypeError('unsupported original stream type: ' + type(value).__name__)
                (folder / (name + '.bin')).write_bytes(body)
                return {'captured': True, 'representation': representation, 'bytes': len(body), 'sha256': sha(body)}
            self.safe(lambda: folder.mkdir(), 'run-folder')
            self.safe(lambda: row.update(executable=retain_executable()), 'run-original-executable-hash')
            self.safe(lambda: row.update(input=retain(kwargs.get('input'), 'input')), 'run-original-input')
            result, failure = None, None
            try:
                result = original(*args, **kwargs)
                return result
            except BaseException as exc:
                failure = exc
                raise
            finally:
                def finish():
                    row['ended_epoch'] = time.time()
                    row['completed_process_returned'] = result is not None
                    row['returncode'] = result.returncode if result is not None else getattr(failure, 'returncode', None)
                    row['exception'] = error_record(failure) if failure is not None else None
                    source = result if result is not None else failure
                    for name in ('stdout', 'stderr'): row[name] = retain(getattr(source, name, None), name)
                    write_json(folder / 'receipt.json', row)
                # Do not replace an original exception, including KeyboardInterrupt.
                try: self.safe(finish, 'run-original-result')
                except BaseException as observation_interrupt:
                    if failure is None: raise
                    self.errors.append({'preserving_original_exception': repr(observation_interrupt)})
        self.patch(subprocess, 'run', observed)

    def finish(self):
        for row in self.sessions:
            self.safe(lambda r=row: self.flush_session(r), 'final-session-metadata')
            for handle in row.get('_handles', {}).values(): self.safe(handle.close, 'close-retention-file')
        incomplete = [r['folder'] for r in self.sessions if not r.get('complete')]
        result = {'source_sha': self.source_sha, 'sessions': len(self.sessions),
                  'commands': len(self.commands), 'incomplete_sessions': incomplete,
                  'observation_errors': self.errors,
                  'observer_complete': not incomplete and not self.errors,
                  'not_a_product_test_verdict': True}
        write_json(self.out / 'OBSERVATION.json', result)
        return result

    def uninstall(self):
        self.active = False
        if self.finder is not None and self.finder in sys.meta_path: sys.meta_path.remove(self.finder)
        for obj, name, had_own, old in reversed(self.patches):
            if had_own: setattr(obj, name, old)
            else: delattr(obj, name)
        self.patches.clear()
