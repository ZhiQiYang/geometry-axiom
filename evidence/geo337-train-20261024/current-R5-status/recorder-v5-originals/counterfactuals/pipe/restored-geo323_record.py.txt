"""只在正式呼叫時錄製原子程序；本模組匯入不執行產品。"""
import contextlib
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

SAFE_NAMES = (
    'PATH', 'LANG', 'LC_ALL', 'TMPDIR', 'GITHUB_SHA', 'GITHUB_WORKSPACE',
    'PYTHONDONTWRITEBYTECODE', 'PYTHONIOENCODING', 'PYTHONOPTIMIZE',
    'PYTHONPATH', 'PYTHONSTARTUP', 'NODE_OPTIONS', 'CC', 'CXX', 'CFLAGS',
    'CXXFLAGS', 'CPPFLAGS', 'LDFLAGS', 'CPATH', 'C_INCLUDE_PATH',
    'LIBRARY_PATH', 'LD_LIBRARY_PATH', 'GCC_EXEC_PREFIX', 'COMPILER_PATH',
    'GEO261_GRAPH', 'GEO261_GUARDS', 'GEO261_REAPER_LOG',
    'GEO261_HOST_FACTS_EXECUTION_LOG', 'GEO261_CONTACT_SOURCES_EXECUTION_LOG',
    'GEO261_LOAD_RESIDUAL_EXECUTION_LOG',
    'GEO323_ROOT', 'GEO323_WORK', 'GEO323_EVIDENCE',
    'GEO323_BASE_SHA', 'GEO323_MAIN_SHA',
)
ACTIVE = None
_ORIGINAL_RUN = subprocess.run


def sha(data):
    return hashlib.sha256(data).hexdigest()


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.writing')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def safe_env(env):
    return {name: env.get(name) for name in SAFE_NAMES}


class Recorder:
    def __init__(self, root, repo, source_sha, environment):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.repo, self.sha = str(repo), source_sha
        self.env = dict(environment)
        self.rows = []
        self.recording_errors = []
        self._pending = []
        self._defer_depth = 0

    def _record_error(self, error, row=None):
        value = {'error_type': type(error).__name__, 'error': repr(error),
                 'directory': row['directory'] if row is not None else None}
        self.recording_errors.append(value)
        if row is not None:
            row['recording_complete'] = False
            row['recording_error'] = value
        # Best effort only: never replace an original child exception when
        # recording itself fails (for example because the disk became full).
        try:
            dump(self.root / 'RECORDING_ERRORS.json', self.recording_errors)
        except BaseException:
            pass
        try:
            print('RECORDING_FAILED ' + repr(value), file=sys.stderr, flush=True)
        except BaseException:
            pass

    def flush(self):
        """Persist pending original results outside the original perf timer."""
        for pending in self._pending:
            row = pending['row']
            if pending['attempted']:
                raise RuntimeError('Prior recording failed; no automatic overwrite/retry: ' + row['directory'])
            pending['attempted'] = True
            try:
                directory = Path(row['directory'])
                directory.mkdir()
                row.update(
                    started_utc=datetime.datetime.fromtimestamp(row['started_epoch'], datetime.timezone.utc).isoformat(),
                    ended_utc=datetime.datetime.fromtimestamp(row['ended_epoch'], datetime.timezone.utc).isoformat(),
                    stdin_sha256=sha(pending['input'] or b''),
                    subprocess_semantics='original subprocess.run capture_output=True PIPE; no added process session/group',
                    evidence_flush_deferred=pending['deferred'],
                    seconds_scope='original subprocess.run wall; serialization/flush excluded',
                )
                dump(directory / 'request.json', {k: v for k, v in row.items()
                     if k not in ('recording_complete', 'recording_error')})
                if pending['input'] is not None:
                    (directory / 'stdin.bin').write_bytes(pending['input'])
                for stream in ('stdout', 'stderr'):
                    exposed = pending[stream]
                    body = exposed if exposed is not None else b''
                    if not isinstance(body, bytes):
                        raise TypeError('Original subprocess stream is not bytes: ' + stream)
                    (directory / (stream + '.bin')).write_bytes(body)
                    row[stream + '_available_from_original'] = exposed is not None
                    row[stream + '_representation'] = ('original-exposed-bytes' if exposed is not None
                                                        else 'not-exposed; empty retention file is not a child-output claim')
                    row[stream + '_bytes'] = len(body)
                    row[stream + '_sha256'] = sha(body)
                row['recording_complete'] = True
                dump(directory / 'result.json', row)
            except BaseException as exc:
                self._record_error(exc, row)
                raise
        if self._pending:
            try:
                dump(self.root / 'commands.json', self.rows)
            except BaseException as exc:
                self._record_error(exc)
                raise
        self._pending.clear()

    @contextlib.contextmanager
    def defer_flush(self):
        """Scope surrounds original perf(), never changes its timer or judge."""
        self._defer_depth += 1
        original_failure = None
        try:
            yield
        except BaseException as exc:
            original_failure = exc
            raise
        finally:
            self._defer_depth -= 1
            if not self._defer_depth:
                try:
                    self.flush()
                except BaseException:
                    if original_failure is None:
                        raise
                    # flush already retained/reported its own error. The same
                    # original perf/assert/timeout exception continues outward.

    def run(self, command, *, cwd=None, input=None, env=None,
            preexec_fn=None, timeout=None, capture_output=True,
            read_output=True, check=False, text=False, **kwargs):
        if kwargs:
            raise TypeError('尚未支援的錄製參數：' + repr(sorted(kwargs)))
        if text or not capture_output:
            raise ValueError('此工具只錄製原始bytes，不接受text或未捕捉輸出')
        command_snapshot = [os.fspath(x) for x in command]
        directory = self.root / f'{len(self.rows) + 1:06d}'
        actual_env = self.env if env is None else env
        role = self.role(command_snapshot, cwd)
        row = {
            'command': command_snapshot, 'cwd': os.fspath(cwd) if cwd is not None else os.getcwd(),
            'acceptance_sha': self.sha, 'source_sha': role['sha'],
            'source_role': role,
            'environment': safe_env(actual_env),
            'started_epoch': time.time(), 'stdin_provided': input is not None,
            'timeout_seconds': timeout,
            'directory': str(directory), 'actual_process_returncode': None,
            'timeout_expired': False, 'recording_complete': False,
        }
        self.rows.append(row)
        original_input = bytes(input) if input is not None else None
        result = None
        failure = None
        try:
            result = _ORIGINAL_RUN(command, cwd=cwd, input=input, env=actual_env,
                preexec_fn=preexec_fn, timeout=timeout, capture_output=True,
                check=check, text=False)
            if read_output:
                return result
            # read_output is the recorder's pre-existing storage-only option;
            # original bytes are retained, but archive/outer callers need no
            # duplicate returned payload. Ordinary judge calls return the same
            # original CompletedProcess object above.
            return subprocess.CompletedProcess(result.args, result.returncode, b'', b'')
        except BaseException as exc:
            failure = exc
            raise
        finally:
            row['ended_epoch'] = time.time()
            row['seconds'] = row['ended_epoch'] - row['started_epoch']
            exposed = result if result is not None else failure
            row['actual_process_returncode'] = getattr(exposed, 'returncode', None)
            row['timeout_expired'] = isinstance(failure, subprocess.TimeoutExpired)
            row['original_exception_type'] = type(failure).__name__ if failure is not None else None
            row['original_exception'] = repr(failure) if failure is not None else None
            row['original_process_completed'] = result is not None or isinstance(failure, subprocess.CalledProcessError)
            if row['timeout_expired']:
                row['timeout_returncode_scope'] = 'stdlib TimeoutExpired does not expose reaped child returncode; null is not success'
                row['timeout_output_scope'] = 'only bytes exposed by the original TimeoutExpired; not a claim of all bytes after kill'
            self._pending.append({'row': row, 'input': original_input,
                'stdout': getattr(exposed, 'stdout', None),
                'stderr': getattr(exposed, 'stderr', None),
                'deferred': bool(self._defer_depth), 'attempted': False})
            if not self._defer_depth:
                try:
                    self.flush()
                except BaseException:
                    if failure is None:
                        raise

    def role(self, command, cwd):
        value = ' '.join(command) + ' ' + str(cwd or '')
        base = self.env['GEO323_BASE_SHA']
        main = self.env['GEO323_MAIN_SHA']
        if base in value or 'source-base' in value or '/base/' in value or '/base-' in value:
            return {'label': 'base', 'sha': base}
        if main in value or 'source-main' in value or '/main/' in value:
            return {'label': 'main', 'sha': main}
        return {'label': 'fix-or-orchestration', 'sha': self.sha}


def recorded_run(command, **kwargs):
    if ACTIVE is None:
        raise RuntimeError('請透過run.py設定錄製器，不直接執行適配模組')
    return ACTIVE.run(command, **kwargs)
