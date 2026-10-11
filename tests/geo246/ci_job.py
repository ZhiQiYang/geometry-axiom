"""Run one of the seven workflow jobs with owned services and exact-head receipts.

Invoke inside isolated_wsl.sh. Ports and output directories are isolated; suite
selection, native build entrypoints and the 16 MiB stack match the workflow.
The result is a Codex reproduction, not an independent WSL-reviewer approval.
"""
import argparse
import importlib.util
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time

from identity import capture, sha, write

ROOT = Path(__file__).resolve().parents[2]
SUITES = {
    'assembly': ('geometry-web/cdp_test.js', {'GEOMETRY_ASSEMBLY_ONLY': '1'}, 15),
    'documents': ('geometry-web/documents_browser_test.js', {}, 10),
    'grid': ('geometry-web/cdp_test.js', {'GEOMETRY_GRID_SYSTEM_ONLY': '1'}, 15),
    'canvas': ('geometry-web/cdp_test.js', {}, 35),
    'space': ('geometry-web/space_model_test.js', {}, 15),
    'timber': ('geometry-web/space_model_test.js', {'GEOMETRY_TIMBER_ONLY': '1'}, 20),
}


def port():
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        return probe.getsockname()[1]


def stop(proc):
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    if proc.poll() is None:
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('job', choices=['native', *SUITES])
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--native-timeout', type=int, default=1800,
                   help='Local wall-time allowance; CI native budget is 900s and any overrun is explicitly reported')
    args = p.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    before = capture(ROOT)
    assert not before['tracked_diff']
    write(out / 'checkout-before.json', before)
    env = {k: v for k, v in os.environ.items() if not k.startswith('GEOMETRY_')}
    commands = []
    procs = []

    def run(name, argv, timeout, command_env=env):
        start = time.monotonic()
        with (out / (name + '.log')).open('wb') as log:
            proc = subprocess.Popen(argv, cwd=ROOT, env=command_env, stdout=log,
                                    stderr=subprocess.STDOUT, start_new_session=True)
            timed_out = False
            try:
                code = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                stop(proc)
                code = 124
        record = {'name': name, 'argv': argv, 'exit_code': code,
                  'seconds': round(time.monotonic() - start, 3), 'timeout': timeout, 'timed_out': timed_out,
                  'log_sha256': sha((out / (name + '.log')).read_bytes())}
        commands.append(record)
        write(out / (name + '.json'), record)
        return code

    code = 1
    failure = None
    runtime = None
    try:
        if args.job == 'native':
            code = run('run-all', ['python3', 'tests/run_all.py', '--build'], args.native_timeout)
            native_dir = Path('/tmp/geometry-tests')
            spec = importlib.util.spec_from_file_location('geo246_native_registry', ROOT / 'tests/binaries.py')
            registry = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(registry)
            binary_paths = [info.path for info in registry.inspect_all().values() if info.state == 'fresh']
            write(out / 'binary-state.json', {name: {'state': info.state, 'reason': info.reason}
                  for name, info in registry.inspect_all().items()})
            required = ['core', 'bridge', 'integrity', 'model-base', 'engjson']
            if not all(registry.inspect_all()[name].state == 'fresh' for name in required):
                code = code or 2
        else:
            font = subprocess.run(['fc-match', 'sans:lang=zh-tw'], capture_output=True, text=True)
            write(out / 'font.json', {'command': ['fc-match', 'sans:lang=zh-tw'],
                  'exit_code': font.returncode, 'stdout': font.stdout, 'stderr': font.stderr})
            chrome = Path('/usr/bin/google-chrome')
            assert chrome.is_file() and font.returncode == 0
            assert 'CJK' in font.stdout, 'Chinese font is mandatory; not silently skipped'
            code = run('build', ['npm', 'run', 'build'], 300)
            if code:
                return code
            server_port = port()
            cdp_port = port()
            env.update(GEOMETRY_TEST_URL=f'http://127.0.0.1:{server_port}/',
                       GEOMETRY_FEEDBACK_DIR=str(Path(os.environ['TMPDIR']) / 'feedback'),
                       GEOMETRY_CHROME=str(chrome), GEOMETRY_CHROME_FLAGS='--no-sandbox',
                       GEOMETRY_BROWSER_SUITE=args.job, GEOMETRY_CDP_PORT=str(cdp_port),
                       GEOMETRY_GRID_SYSTEM_SCREENSHOT_DIR=str(out / 'grid-screens'),
                       GEOMETRY_DOCUMENT_SCREENSHOT_DIR=str(out / 'document-screens'))
            script, flags, minutes = SUITES[args.job]
            env.update(flags)
            argv = ['python3', '-u', 'geometry-web/start_local.py', '--port', str(server_port)]
            with (out / 'server.log').open('wb') as server_log:
                server = subprocess.Popen(argv, cwd=ROOT, env=env, stdout=server_log,
                                          stderr=subprocess.STDOUT, start_new_session=True)
                procs.append(server)
                probe = ['python3', 'geometry-web/runtime_version.py', '--probe', str(server_port)]
                for _ in range(30):
                    if server.poll() is not None:
                        raise RuntimeError('Owned server exited before runtime verification')
                    check = subprocess.run(probe, cwd=ROOT, env=env, capture_output=True)
                    if check.returncode == 0:
                        runtime = check.stdout.decode('utf8', errors='replace')
                        break
                    time.sleep(1)
                else:
                    raise RuntimeError('Owned runtime did not become fresh within 30 attempts')
                (out / 'runtime.json').write_text(runtime, encoding='utf8')
                code = run('browser', ['node', script], minutes * 60, env)
                stop(server)
            # start_local's root-keyed runtime directory is deterministic within TMPDIR.
            from hashlib import sha256
            native_dir = Path(os.environ['TMPDIR']) / 'geometry-runtime' / sha256(str(ROOT).encode()).hexdigest()[:20]
            binary_paths = [native_dir / name for name in ('core', 'bridge', 'model-base')]
        after = capture(ROOT, binary_paths)
        assert before['head'] == after['head'] and before['tree'] == after['tree']
        assert not after['tracked_diff']
        write(out / 'checkout-after.json', after)
    except Exception as error:
        failure = {'type': type(error).__name__, 'message': str(error)}
        code = code or 1
        print(failure, file=sys.stderr, flush=True)
    finally:
        for proc in procs:
            stop(proc)
        write(out / 'job.json', {'actor': 'Codex', 'job': args.job, 'head': before['head'], 'tree': before['tree'],
              'checkout': str(ROOT), 'exit_code': code, 'commands': commands,
              'workflow_sha256': sha((ROOT / '.github/workflows/integration-tests.yml').read_bytes()),
              'environment_differences': ['Owned free application/CDP ports and task-specific output paths',
                  'Existing installed Chrome/CJK fonts; no system package changes',
                  'Local native wall-time allowance is recorded; exceeding CI 900s is not a CI pass'],
              'ci_native_timeout_exceeded': args.job == 'native' and any(c['seconds'] > 900 for c in commands),
              'executor_error': failure,
              'approval': 'No independent WSL-reviewer or merge approval is implied.'})
    return code


if __name__ == '__main__':
    sys.exit(main())
