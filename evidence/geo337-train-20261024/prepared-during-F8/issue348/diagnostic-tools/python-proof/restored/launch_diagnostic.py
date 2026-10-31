"""Draft external diagnostic launcher. Never compiles a product.

CLI refuses execution without a separately recorded calibration for the exact
diagnostic ELF and wrapper. Synthetic tests inject a Python runner only.
"""
import argparse, hashlib, json, os, subprocess, sys, time
from pathlib import Path
from sidecar import MAGIC, STATUS, TIMEOUT, inspect_events

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def capture(argv, payload, out, *, env, source_sha, bindings, runner=subprocess.run, synthetic=False):
    """Forward original argv/input/timeout/result/exception; observe afterwards."""
    out = Path(out)
    out.mkdir(mode=0o700)
    (out / 'stdin.bin').write_bytes(payload)
    event_fd = os.open(out / 'events.jsonl', os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
    status_fd = os.open(out / 'status.bin', os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(status_fd, STATUS.pack(MAGIC, 1, 0, 0, 0, 0, 0, 0))
        child_env = dict(env)
        child_env.update(GEO348_DIAG_EVENT_FD=str(event_fd), GEO348_DIAG_STATUS_FD=str(status_fd))
        request = {'schema': 'geo348-command-boundary-diagnostic/1', 'argv': argv,
                   'source_sha': source_sha, 'synthetic': synthetic, 'timeout': TIMEOUT,
                   'input_sha256': sha(payload), 'input_bytes': len(payload), 'bindings': bindings,
                   'environment': {k: child_env.get(k) for k in ['LANG', 'LC_ALL', 'TMPDIR', 'CC', 'CFLAGS',
                                   'CPPFLAGS', 'LDFLAGS', 'LD_PRELOAD', 'LD_LIBRARY_PATH',
                                   'GEO348_DIAG_EVENT_FD', 'GEO348_DIAG_STATUS_FD']},
                   'started_monotonic_ns': time.monotonic_ns(), 'product_gate_verdict': None}
        write_json(out / 'REQUEST.json', request)
        result, failure = None, None
        try:
            result = runner(argv, input=payload, capture_output=True, timeout=TIMEOUT,
                            env=child_env, pass_fds=(event_fd, status_fd))
            return result
        except BaseException as exc:
            failure = exc
            raise
        finally:
            # A recorder error must not replace an original TimeoutExpired (or
            # any other exception), nor turn one into CompletedProcess zero.
            try:
                terminal = dict(request)
                terminal.update(ended_monotonic_ns=time.monotonic_ns(),
                    completed_process_returned=result is not None,
                    returncode=result.returncode if result is not None else getattr(failure, 'returncode', None),
                    exception=None if failure is None else {'type': type(failure).__name__, 'repr': repr(failure)},
                    observer_errors=[])
                origin = result if result is not None else failure
                for name in ['stdout', 'stderr']:
                    value = getattr(origin, name, None)
                    if value is None:
                        terminal[name] = {'captured': False}
                    elif isinstance(value, bytes):
                        (out / (name + '.bin')).write_bytes(value)
                        terminal[name] = {'captured': True, 'bytes': len(value), 'sha256': sha(value)}
                    else:
                        terminal[name] = {'captured': False, 'unexpected_type': type(value).__name__}
                        terminal['observer_errors'].append('non-byte original ' + name)
                events = (out / 'events.jsonl').read_bytes()
                status = (out / 'status.bin').read_bytes()
                terminal['sidecar'] = inspect_events(events, status, payload, completed=result is not None)
                terminal['event_sha256'], terminal['status_sha256'] = sha(events), sha(status)
                terminal['diagnostic_observation_valid'] = terminal['sidecar']['valid'] and not terminal['observer_errors']
                terminal['root_cause'] = None
                write_json(out / 'RESULT.json', terminal)
            except BaseException as observation_error:
                try:
                    write_json(out / 'OBSERVER_ERROR.json', {'type': type(observation_error).__name__,
                        'repr': repr(observation_error), 'original_exception_preserved': failure is not None,
                        'product_gate_verdict': None})
                except BaseException:
                    pass
    finally:
        os.close(status_fd)
        os.close(event_fd)

def pinned(path, expected):
    raw = Path(path).read_bytes()
    if sha(raw) != expected:
        raise ValueError('Pinned input changed: ' + str(path))
    return raw

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute-diagnostic', action='store_true')
    p.add_argument('--source-root', type=Path, required=True)
    p.add_argument('--source-sha', required=True)
    for name in ['elf', 'fixture', 'stdin', 'build-binding', 'calibration']:
        p.add_argument('--' + name, type=Path, required=True)
        p.add_argument('--' + name + '-sha256', required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if not a.execute_diagnostic:
        p.error('Draft is inert by default; exact-ELF calibration and explicit --execute-diagnostic are required.')
    if a.out.exists():
        p.error('Fresh external output directory required.')
    bindings = {}
    raw = {}
    for name in ['elf', 'fixture', 'stdin', 'build_binding', 'calibration']:
        path = getattr(a, name)
        digest = getattr(a, name + '_sha256')
        raw[name] = pinned(path, digest)
        bindings[name] = {'path': str(path.resolve()), 'sha256': digest, 'bytes': len(raw[name])}
    if not raw['elf'].startswith(b'\x7fELF'):
        p.error('Exact diagnostic ELF required; scripts are only used by injected synthetic tests.')
    wanted = ('loadfile ' + str(a.fixture.resolve()) + '\ndump\nobjects\nreferences\n').encode()
    if raw['stdin'] != wanted:
        p.error('The same four commands and actual pinned fixture path are required.')
    wrapper = Path(__file__).with_name('trace_wrap.c')
    wrapper_sha = sha(wrapper.read_bytes())
    build = json.loads(raw['build_binding'])
    calibration = json.loads(raw['calibration'])
    for record, schema in [(build, 'geo348-diagnostic-build/1'), (calibration, 'geo348-wrap-calibration/1')]:
        if record.get('schema') != schema or record.get('source_sha') != a.source_sha or record.get('elf_sha256') != a.elf_sha256 or record.get('wrapper_sha256') != wrapper_sha:
            p.error('Build/calibration identity does not match exact source, wrapper and diagnostic ELF.')
        if record.get('exit') != 0 or not record.get('original_receipts'):
            p.error('Build/calibration requires successful original receipts, not only an assertion.')
        for item in record['original_receipts']:
            pinned(item['path'], item['sha256'])
    if '-O0' not in build.get('cflags', []) or any(x.startswith('-O') and x != '-O0' for x in build.get('cflags', [])):
        p.error('Original O0 compiler setting required.')
    if not all(x in build.get('ldflags', []) for x in ['-Wl,--wrap=fgets', '-Wl,--wrap=fflush']):
        p.error('Both external wrapper link flags required.')
    required = ['both_symbols_observed', 'four_input_boundaries', 'four_flush_returns',
                'stdout_bytes_equal_unwrapped', 'stderr_bytes_equal_unwrapped', 'io_fault_detected']
    if not all(calibration.get(k) is True for k in required):
        p.error('Exact-ELF runtime calibration is incomplete; static symbol guesses do not count.')
    cmd = ['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', '-C', str(a.source_root)]
    head = subprocess.run(cmd + ['rev-parse', 'HEAD'], capture_output=True, check=True)
    status = subprocess.run(cmd + ['status', '--porcelain=v1', '--untracked-files=all'], capture_output=True, check=True)
    if head.stdout.strip().decode() != a.source_sha or status.stdout:
        p.error('Exact clean source checkout required; diagnostic wrapper must remain outside product checkout.')
    bindings['wrapper'] = {'path': str(wrapper), 'sha256': wrapper_sha}
    env = dict(os.environ)
    if env.get('LD_PRELOAD') or env.get('LD_LIBRARY_PATH'):
        p.error('Unexpected dynamic-loader injection; use recorded original environment.')
    try:
        completed = capture([str(a.elf.resolve())], raw['stdin'], a.out, env=env,
                            source_sha=a.source_sha, bindings=bindings)
    except subprocess.TimeoutExpired:
        return 124
    report = json.loads((a.out / 'RESULT.json').read_bytes())
    return 0 if completed.returncode == 0 and report['diagnostic_observation_valid'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
