"""只在正式呼叫時錄製原子程序；本模組匯入不執行產品。"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
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

    def run(self, command, *, cwd=None, input=None, env=None,
            preexec_fn=None, timeout=None, capture_output=True,
            read_output=True, check=False, text=False, **kwargs):
        if kwargs:
            raise TypeError('尚未支援的錄製參數：' + repr(sorted(kwargs)))
        if text or not capture_output:
            raise ValueError('此工具只錄製原始bytes，不接受text或未捕捉輸出')
        command = [os.fspath(x) for x in command]
        directory = self.root / f'{len(self.rows) + 1:06d}'
        directory.mkdir()
        actual_env = self.env if env is None else dict(env)
        role = self.role(command, cwd)
        row = {
            'command': command, 'cwd': str(Path(cwd or Path.cwd()).resolve()),
            'acceptance_sha': self.sha, 'source_sha': role['sha'],
            'source_role': role,
            'environment': safe_env(actual_env), 'started_utc': utc(),
            'started_epoch': time.time(), 'stdin_provided': input is not None,
            'stdin_sha256': sha(input or b''), 'timeout_seconds': timeout,
            'directory': str(directory), 'actual_process_returncode': None,
            'timeout_expired': False,
        }
        self.rows.append(row)
        dump(directory / 'request.json', row)
        if input is not None:
            (directory / 'stdin.bin').write_bytes(input)
        print(f'執行命令 {len(self.rows)}：{command[0]}（完整argv見收據）', flush=True)
        process = None
        failure = None
        try:
            with (directory / 'stdout.bin').open('wb') as stdout, \
                    (directory / 'stderr.bin').open('wb') as stderr:
                process = subprocess.Popen(
                    command, cwd=row['cwd'], env=actual_env,
                    stdin=subprocess.PIPE if input is not None else subprocess.DEVNULL,
                    stdout=stdout, stderr=stderr, preexec_fn=preexec_fn,
                    start_new_session=True,
                )
                try:
                    process.communicate(input=input, timeout=timeout)
                except subprocess.TimeoutExpired:
                    row['timeout_expired'] = True
                    os.killpg(process.pid, signal.SIGKILL)
                    process.communicate()
                row['actual_process_returncode'] = process.returncode
        except BaseException as exc:
            failure = exc
            row['launch_or_recording_error'] = repr(exc)
            if process is not None and process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                row['actual_process_returncode'] = process.returncode
        finally:
            row['ended_utc'] = utc()
            row['ended_epoch'] = time.time()
            row['seconds'] = row['ended_epoch'] - row['started_epoch']
            for stream in ('stdout', 'stderr'):
                path = directory / (stream + '.bin')
                if path.exists():
                    row[stream + '_bytes'] = path.stat().st_size
                    digest = hashlib.sha256()
                    with path.open('rb') as handle:
                        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
                            digest.update(chunk)
                    row[stream + '_sha256'] = digest.hexdigest()
            dump(directory / 'result.json', row)
            dump(self.root / 'commands.json', self.rows)
        if failure is not None:
            raise failure
        stdout = (directory / 'stdout.bin').read_bytes() if read_output else b''
        stderr = (directory / 'stderr.bin').read_bytes() if read_output else b''
        if row['timeout_expired']:
            raise subprocess.TimeoutExpired(command, timeout, output=stdout, stderr=stderr)
        result = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
        if check:
            result.check_returncode()
        return result

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
