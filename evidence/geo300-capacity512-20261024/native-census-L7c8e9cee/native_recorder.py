#!/usr/bin/env python3
"""外部原生收件器草稿：不匯入或修改產品 runner；正式上限固定 2100 秒。"""
import argparse
import contextlib
import ctypes
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import shutil
import signal
import subprocess
import sys
import tarfile
import time
import traceback

LIMIT = 2100
STACK = 16 * 1024 * 1024
RESERVE = 64 * 1024 * 1024
BINROOT = Path('/tmp/geometry-tests')
BINARIES = ('core', 'bridge', 'pf3-algorithm', 'integrity', 'model-base', 'engineering-json-test')


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def save(path, value):
    temporary = Path(str(path) + '.writing')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def children(pid):
    """Read PPid and start ticks; this cloud kernel omits task/*/children.

    Scanning metadata does not confer ownership: only exact PPid descendants
    enter the kill list, and pidfd/open + start-tick recheck prevent PID reuse.
    """
    answer = []
    for path in Path('/proc').iterdir():
        if not path.name.isdecimal():
            continue
        try:
            fields = (path / 'stat').read_text().rsplit(')', 1)[1].split()
            if int(fields[1]) == pid:
                answer.append((int(path.name), fields[19]))
        except FileNotFoundError:
            pass
    return sorted(answer)


def stop_kill_owned(record):
    """Stop parents before enumerating children, then kill by stable pidfd.

    A separate session does not escape ancestry/subreaper ownership. No process
    selected by name, global PID list, or unrelated process group is signalled.
    """
    handles = []
    pending = children(os.getpid())
    seen = set()
    try:
        while pending:
            pid, start_ticks = pending.pop(0)
            if (pid, start_ticks) in seen:
                continue
            seen.add((pid, start_ticks))
            try:
                fd = os.pidfd_open(pid)
            except ProcessLookupError:
                continue
            handles.append((pid, fd))
            try:
                actual_ticks = Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]
            except FileNotFoundError:
                continue
            if actual_ticks != start_ticks:
                handles.pop()
                os.close(fd)
                record({'event': 'pid-reused-not-signalled', 'pid': pid})
                continue
            try:
                signal.pidfd_send_signal(fd, signal.SIGSTOP)
                record({'event': 'stop-owned', 'pid': pid})
            except ProcessLookupError:
                pass
            pending.extend(children(pid))
        for pid, fd in reversed(handles):
            try:
                signal.pidfd_send_signal(fd, signal.SIGKILL)
                record({'event': 'kill-owned', 'pid': pid})
            except ProcessLookupError:
                pass
    finally:
        for _, fd in handles:
            os.close(fd)


def record_process(command, cwd, out, env, *, timeout=LIMIT):
    """Private function; alternate timeout is used only by the synthetic test.

    Public CLI never accepts another limit. All primary execution, including
    build, counts from fork to exit; timeout remains red after cleanup.
    """
    if not hasattr(os, 'pidfd_open') or not hasattr(signal, 'pidfd_send_signal'):
        raise RuntimeError('Linux pidfd required; no unsafe PID-only kill fallback')
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0):
        raise OSError(ctypes.get_errno(), 'PR_SET_CHILD_SUBREAPER')
    flag = ctypes.c_int()
    if libc.prctl(37, ctypes.byref(flag), 0, 0, 0) or flag.value != 1:
        raise RuntimeError('PR_GET_CHILD_SUBREAPER did not return 1')
    # Fail before launch if pidfd is unavailable in this kernel.
    probe = os.pidfd_open(os.getpid())
    os.close(probe)
    out = Path(out)
    interrupted = []
    original_signals = {}
    def receive(sig, _frame):
        interrupted.append(sig)
    for sig in (signal.SIGINT, signal.SIGTERM):
        original_signals[sig] = signal.signal(sig, receive)
    result = {'command': command, 'cwd': str(cwd), 'limit_seconds': timeout,
              'started_utc': utc(), 'stack_bytes': STACK, 'subreaper': flag.value,
              'timed_out': False, 'orphan_cleanup_required': False, 'cleanup_complete': False,
              'actual_process_returncode': None, 'errors': []}
    started = time.monotonic()
    primary = None
    cleanup_started = None
    primary_done = False
    with (out / 'stdout.bin').open('xb', buffering=0) as stdout, \
         (out / 'stderr.bin').open('xb', buffering=0) as stderr, \
         (out / 'process-events.jsonl').open('x') as events:
        def record(row):
            events.write(json.dumps({'utc': utc(), 'elapsed_seconds': time.monotonic() - started, **row}) + '\n')
            events.flush()
        try:
            primary = os.fork()
            if primary == 0:
                try:
                    for sig in original_signals:
                        signal.signal(sig, signal.SIG_DFL)
                    os.setsid()
                    hard = resource.getrlimit(resource.RLIMIT_STACK)[1]
                    resource.setrlimit(resource.RLIMIT_STACK, (STACK, hard))
                    os.chdir(cwd)
                    os.dup2(stdout.fileno(), 1)
                    os.dup2(stderr.fileno(), 2)
                    with open(os.devnull, 'rb') as null:
                        os.dup2(null.fileno(), 0)
                    os.execvpe(command[0], command, env)
                except BaseException:
                    os.write(2, traceback.format_exc().encode())
                    os._exit(127)
            result['primary_pid'] = primary
            record({'event': 'started', 'pid': primary})
            while True:
                no_children = False
                while True:
                    try:
                        pid, status = os.waitpid(-1, os.WNOHANG)
                    except ChildProcessError:
                        no_children = True
                        break
                    except InterruptedError:
                        continue
                    if not pid:
                        break
                    code = os.waitstatus_to_exitcode(status)
                    record({'event': 'reaped', 'pid': pid, 'primary': pid == primary, 'returncode': code})
                    if pid == primary:
                        primary_done = True
                        result['actual_process_returncode'] = code
                        result['primary_ended_utc'] = utc()
                        result['primary_elapsed_seconds'] = time.monotonic() - started
                elapsed = time.monotonic() - started
                if no_children:
                    if elapsed >= timeout:
                        result['timed_out'] = True
                    result['cleanup_complete'] = True
                    break
                if cleanup_started is None:
                    if interrupted:
                        result['interrupted_signals'] = list(interrupted)
                        cleanup_started = time.monotonic()
                    elif elapsed >= timeout:
                        result['timed_out'] = True
                        cleanup_started = time.monotonic()
                    elif primary_done:
                        result['orphan_cleanup_required'] = True
                        cleanup_started = time.monotonic()
                if cleanup_started is not None:
                    stop_kill_owned(record)
                    if time.monotonic() - cleanup_started > 10:
                        result['errors'].append('Owned descendants could not be reaped within cleanup window')
                        break
                time.sleep(min(0.05, max(0.001, timeout - elapsed)) if cleanup_started is None else 0.01)
        except BaseException:
            result['errors'].append(traceback.format_exc())
            # An unexpected recorder failure must not leave an unguarded test running.
            if primary is not None:
                stop_kill_owned(record)
                until = time.monotonic() + 10
                while time.monotonic() < until:
                    try:
                        pid, status = os.waitpid(-1, os.WNOHANG)
                    except ChildProcessError:
                        result['cleanup_complete'] = True
                        break
                    if pid:
                        code = os.waitstatus_to_exitcode(status)
                        record({'event': 'exception-reaped', 'pid': pid, 'returncode': code})
                        if pid == primary:
                            result['actual_process_returncode'] = code
                    else:
                        time.sleep(0.01)
        finally:
            for sig, previous in original_signals.items():
                signal.signal(sig, previous)
            result['ended_utc'] = utc()
            result['elapsed_with_cleanup_seconds'] = time.monotonic() - started
    result['stdout_sha256'] = digest(out / 'stdout.bin')
    result['stderr_sha256'] = digest(out / 'stderr.bin')
    result['exit_code'] = (124 if result['timed_out'] else
                          1 if result['errors'] or not result['cleanup_complete'] or
                          result['orphan_cleanup_required'] or interrupted else
                          result['actual_process_returncode'])
    save(out / 'PROCESS.json', result)
    return result


def git(repo, *arguments):
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_NO_LAZY_FETCH='1', GIT_OPTIONAL_LOCKS='0')
    proc = subprocess.run(['git', *arguments], cwd=repo, env=env, capture_output=True, timeout=30)
    if proc.returncode:
        raise RuntimeError('Read-only git failed: ' + repr(arguments) + '\n' + proc.stderr.decode(errors='replace'))
    return proc.stdout


def state(repo):
    actual_root = Path(git(repo, 'rev-parse', '--show-toplevel').decode().strip()).resolve()
    if actual_root != Path(repo).resolve():
        raise RuntimeError('Git worktree root differs from the execution cwd')
    return {'head': git(repo, 'rev-parse', 'HEAD').decode().strip(),
            'status_z': git(repo, 'status', '--porcelain=v1', '-z', '--untracked-files=all').decode()}


def manifest(paths):
    result = []
    for path in sorted(set(paths)):
        if path.is_symlink():
            raise RuntimeError('Archive inputs must be regular files, not symlinks: ' + str(path))
        if not path.is_file():
            result.append({'path': str(path), 'missing': True})
            continue
        st = path.stat()
        result.append({'path': str(path), 'bytes': st.st_size, 'mode': st.st_mode,
                       'mtime_ns': st.st_mtime_ns, 'sha256': digest(path)})
    return result


def archive(out, label, paths, root):
    rows = manifest(paths)
    needed = sum(r.get('bytes', 0) for r in rows) + 2048 * len(rows) + 10240
    if shutil.disk_usage(out).free < needed + RESERVE:
        raise RuntimeError('Archive space insufficient; originals retained; required bytes=' + str(needed + RESERVE))
    target = out / (label + '.tar')
    with tarfile.open(target, 'x') as tar:
        for row in rows:
            if not row.get('missing'):
                path = Path(row['path'])
                tar.add(path, arcname=path.relative_to(root).as_posix(), recursive=False)
    if rows != manifest(paths):
        raise RuntimeError('Archive inputs changed while copying: ' + label)
    with tarfile.open(target, 'r') as tar:
        for row in rows:
            if not row.get('missing'):
                member = tar.extractfile(Path(row['path']).relative_to(root).as_posix())
                h = hashlib.sha256()
                for chunk in iter(lambda: member.read(1024 * 1024), b''):
                    h.update(chunk)
                if h.hexdigest() != row['sha256']:
                    raise RuntimeError('Archive readback hash mismatch: ' + row['path'])
    save(out / (label + '-manifest.json'), rows)
    return {'file': target.name, 'bytes': target.stat().st_size, 'sha256': digest(target), 'inputs': rows}


@contextlib.contextmanager
def registry_locks():
    handles = []
    try:
        for name in ('run_all', 'build'):
            handle = (BINROOT / (name + '.lock')).open('a+b')
            handles.append(handle)
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        for handle in reversed(handles):
            handle.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--sha', required=True)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--heavy-lock', required=True, type=Path)
    parser.add_argument('--mode', required=True, choices=('census', 'native'))
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.out.resolve()
    if not repo.is_dir() or out.exists() or out.is_relative_to(repo):
        raise RuntimeError('Require an existing source and a new external output directory')
    if not args.heavy_lock.is_file():
        raise RuntimeError('Require the existing coordinated heavy-test lock')
    if sys.flags.optimize or os.environ.get('PYTHONOPTIMIZE') not in (None, '', '0'):
        raise RuntimeError('Optimized Python is not allowed')
    out.mkdir(parents=True)
    report = {'schema': 'pr348-original-native-execution/1', 'mode': args.mode,
              'execution_sha': args.sha, 'started_utc': utc(), 'errors': [], 'archives': [],
              'platform': platform.platform(), 'python': sys.version, 'limit_seconds': LIMIT,
              'tool_sha256': digest(__file__), 'source_before': None, 'source_after': None}
    save(out / 'RESULT.json', report)
    code = 1
    with args.heavy_lock.open('r+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            report['source_before'] = state(repo)
            if report['source_before'] != {'head': args.sha, 'status_z': ''}:
                raise RuntimeError('Source must be exactly the requested SHA and clean before launch')
            expected = repo / 'tests/run_all.expected.json'
            shutil.copy2(expected, out / 'expected-before.json')
            report['ledger_before_sha256'] = digest(repo / 'tests/mutants_results.json')
            report['space_before'] = {str(p): shutil.disk_usage(p)._asdict() for p in (Path('/tmp'), out)}
            BINROOT.mkdir(parents=True, exist_ok=True)
            binary_paths = [BINROOT / (name + suffix) for name in BINARIES for suffix in ('', '.fingerprint.json')]
            logroot = BINROOT / 'run_all-logs'
            with registry_locks():
                save(out / 'binary-before.json', manifest(binary_paths))
                if logroot.exists():
                    report['archives'].append(archive(out, 'prior-run-all-logs',
                        [p for p in logroot.rglob('*') if p.is_file() or p.is_symlink()], BINROOT))
            cleared = sorted(k for k in os.environ if k.startswith(('GEOMETRY_', 'GIT_')) or k in
                             ('PYTHONPATH', 'PYTHONHOME', 'PYTHONSTARTUP', 'NODE_OPTIONS', 'PYTHONOPTIMIZE',
                              'LD_PRELOAD', 'MUTATE_RESULTS', 'MUTATE_CACHE'))
            env = {k: v for k, v in os.environ.items() if k not in cleared}
            (out / 'tmp').mkdir()
            env.update(LANG='C.UTF-8', LC_ALL='C.UTF-8', PYTHONIOENCODING='utf-8',
                       PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1', TMPDIR=str(out / 'tmp'),
                       GITHUB_SHA=args.sha, GITHUB_WORKSPACE=str(repo))
            report['cleared_environment_names'] = cleared
            report['environment'] = {k: env.get(k) for k in ('PATH', 'LANG', 'LC_ALL', 'PYTHONIOENCODING',
                'PYTHONDONTWRITEBYTECODE', 'PYTHONUNBUFFERED', 'TMPDIR', 'GITHUB_SHA', 'GITHUB_WORKSPACE',
                'CC', 'CFLAGS', 'CPPFLAGS', 'LDFLAGS', 'C_INCLUDE_PATH', 'CPATH', 'LIBRARY_PATH',
                'LD_LIBRARY_PATH', 'GCC_EXEC_PREFIX', 'COMPILER_PATH')}
            command = ['python3', 'tests/run_all.py', '--build']
            if args.mode == 'census':
                command.append('--update-expected')
            save(out / 'RESULT.json', report)
            report['process'] = record_process(command, repo, out, env)
            code = report['process']['exit_code']
        except BaseException:
            report['errors'].append(traceback.format_exc())
            code = 1
        finally:
            try:
                report['source_after'] = state(repo)
                accepted = ('', ' M tests/run_all.expected.json\0') if args.mode == 'census' else ('',)
                if report['source_after']['head'] != args.sha or report['source_after']['status_z'] not in accepted:
                    raise RuntimeError('Unexpected source/index/untracked changes')
                shutil.copy2(repo / 'tests/run_all.expected.json', out / 'expected-after.json')
                report['ledger_after_sha256'] = digest(repo / 'tests/mutants_results.json')
                if report['ledger_after_sha256'] != report.get('ledger_before_sha256'):
                    raise RuntimeError('Ledger changed during original command')
            except BaseException:
                report['errors'].append(traceback.format_exc())
                code = 1
            try:
                with registry_locks():
                    paths = [BINROOT / (name + suffix) for name in BINARIES for suffix in ('', '.fingerprint.json')]
                    logs = BINROOT / 'run_all-logs'
                    paths += [p for p in logs.rglob('*') if p.is_file() or p.is_symlink()]
                    report['archives'].append(archive(out, 'actual-binaries-sidecars-logs', paths, BINROOT))
                    # Preserve partial originals above even when a failed build
                    # left a missing executable or stale credential.
                    credential_errors = []
                    for name in BINARIES:
                        binary = BINROOT / name
                        sidecar = BINROOT / (name + '.fingerprint.json')
                        if not binary.is_file() or not sidecar.is_file():
                            credential_errors.append(name + ': binary or sidecar missing')
                            continue
                        metadata = json.loads(sidecar.read_text())
                        st = binary.stat()
                        if (metadata.get('exe_sha256') != digest(binary) or
                                metadata.get('exe_size') != st.st_size or
                                metadata.get('exe_mtime_ns') != st.st_mtime_ns):
                            credential_errors.append(name + ': sidecar does not identify archived binary')
                    if credential_errors:
                        raise RuntimeError('; '.join(credential_errors))
            except BaseException:
                report['errors'].append(traceback.format_exc())
                code = 1
            report.update(exit_code=code, ended_utc=utc())
            save(out / 'RESULT.json', report)
    print(json.dumps({'result': str(out / 'RESULT.json'), 'exit_code': code}, ensure_ascii=False))
    return code if code is not None and code >= 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
