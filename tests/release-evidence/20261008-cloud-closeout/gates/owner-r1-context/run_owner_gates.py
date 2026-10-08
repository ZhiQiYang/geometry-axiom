#!/usr/bin/env python3
"""Run the six existing owner/module gates serially on the pinned candidate.

Preparation/inspection: python run_owner_gates.py --list
Run only after the other browser driver is idle:
  python run_owner_gates.py --run-id owner-r1 all
Or replace 'all' with one or more names from --list. Never reuse a run ID.
After a reviewed clean commit, add --head <full 40-character SHA> explicitly.

The existing formal service on port 18971 is an auxiliary source/native identity
anchor for release_gate. Standalone rule-case commands target a separately owned
loopback service with no /runtime; this driver never invents that endpoint.
An exit-zero receipt verifies execution only, not complete product acceptance.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import sys
import time
from urllib.request import urlopen

sys.dont_write_bytecode = True
ROOT = Path('/workspace/geometry-axiom')
EXPECTED_HEAD = '9a4136da264249f76ba08258a7f14be926f96a95'
FORMAL_URL = 'http://127.0.0.1:18971/'
OUT = Path('/workspace/closure-evidence/owner-gates')
TEMP = Path('/tmp/geometry-closeout-owner-gates')
NODE_ADAPTER = Path('/workspace/closure-evidence/sandbox-launch.cjs')
PY_ADAPTER = Path('/workspace/closure-evidence/python-launch/sitecustomize.py')
ADAPTER_HASHES = {
    str(NODE_ADAPTER): 'c917611c821f63cea2e5ef3ed1c0ddde128dcf47fde65d1a7ace8ff24fba2b1e',
    str(PY_ADAPTER): 'e49545951bb661db0169e3d466c96321ee67c5f8a39fac3f7f0ed6954c22a7be',
}
GATES = {
    'scenario-grid-owner': {
        'command': ['node', '--test', 'tests/test_scenario_grid_interface.js'],
        'timeout': 600, 'browser': False, 'target': 'actual project-store module and native verifier'},
    'scenario-module-browser': {
        'command': ['node', 'tests/scenario_browser_check.cjs'],
        'timeout': 1200, 'browser': True, 'target': 'harness-owned ephemeral module HTTP server'},
    'evidence-component-browser': {
        'command': ['node', 'geometry-web/evidence_links_browser_check.js'],
        'timeout': 1200, 'browser': True, 'target': 'formal page with independent memory evidence adapter'},
    'rule-case-standalone-controller': {
        'command': ['node', '--test', 'tests/rule-case-workbench-controller.cjs'],
        'timeout': 600, 'browser': False, 'standalone': True, 'target': 'owned standalone rule-case HTTP service'},
    'rule-case-standalone-browser': {
        'command': ['node', 'tests/rule-case-workbench-browser.cjs'],
        'timeout': 1200, 'browser': True, 'standalone': True, 'target': 'owned standalone rule-case HTTP service'},
    'create-feedback-ui': {
        'command': [sys.executable, 'tests/test_issue123_create_feedback_browser.py'],
        'timeout': 1200, 'browser': True, 'target': 'formal page; all default widths, no repro-only filter'},
}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def environment():
    env = {key: value for key, value in os.environ.items() if not key.startswith('GEOMETRY_')}
    env.update(GEOMETRY_TEST_URL=FORMAL_URL,
               GEOMETRY_TEST_BRIDGE='/tmp/geometry-tests/bridge',
               GEOMETRY_BRIDGE='/tmp/geometry-tests/bridge',
               GEOMETRY_MODEL_BASE='/tmp/geometry-tests/model-base',
               GEOMETRY_FEEDBACK_DIR='/tmp/geometry-closeout-r2-feedback',
               GEOMETRY_CHROME='/usr/bin/chromium', GEOMETRY_REQUIRE_CLEAN='1',
               GEOMETRY_VERIFY_ROOT=str(ROOT), GEOMETRY_PYTHON=sys.executable,
               PYTHON=sys.executable, PYTHONDONTWRITEBYTECODE='1',
               PYTHONPATH=str(PY_ADAPTER.parent), NODE_OPTIONS='--require=' + str(NODE_ADAPTER))
    return env


def public_env(env):
    return {key: value for key, value in env.items()
            if key.startswith('GEOMETRY_') or key in
            {'PYTHON', 'PYTHONDONTWRITEBYTECODE', 'PYTHONPATH', 'NODE_OPTIONS'}}


def exact_source(expected_head):
    data = {}
    for key, args in [('head', ['rev-parse', 'HEAD']),
                      ('tree', ['rev-parse', 'HEAD^{tree}']),
                      ('status', ['status', '--porcelain=v1', '--untracked-files=all']),
                      ('dirtyDiff', ['diff', '--binary', 'HEAD'])]:
        result = subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True,
                                text=True, timeout=20)
        data[key] = {'command': result.args, 'stdout': result.stdout,
                     'stderr': result.stderr, 'exitCode': result.returncode}
        if result.returncode:
            raise RuntimeError('git inspection failed: ' + json.dumps(data))
    if data['head']['stdout'].strip() != expected_head or data['status']['stdout']:
        raise RuntimeError('Require exact clean ' + expected_head + ': ' + json.dumps(data))
    return data


def check_adapters():
    actual = {path: digest(path) for path in ADAPTER_HASHES}
    if actual != ADAPTER_HASHES:
        raise RuntimeError('Sandbox launch adapters changed; re-review before running: ' + json.dumps(actual))
    return actual


def load_release_gate():
    spec = importlib.util.spec_from_file_location('owner_release_gate', ROOT / 'tests/release_gate.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def proc_identity(pid):
    """Linux identity recorded while a subprocess belongs to this driver."""
    raw = Path('/proc', str(pid), 'stat').read_text()
    fields = raw[raw.rfind(')') + 2:].split()
    return {'pid': pid, 'ppid': int(fields[1]), 'pgid': int(fields[2]),
            'session': int(fields[3]), 'startTicks': int(fields[19])}


@contextlib.contextmanager
def standalone(folder, env):
    """Own exactly one new service; never stop the existing formal service."""
    command = [sys.executable, 'geometry-web/rule_case_workbench_standalone.py', '--port', '0']
    record = {'command': command, 'cwd': str(ROOT), 'started': now(),
              'runtimeEndpoint': None, 'identityBasis': 'clean pinned source + native sidecars + own PID + static bytes',
              'environment': public_env(env), 'signals': []}
    process = None
    stdout_path, stderr_path = folder / 'standalone.stdout', folder / 'standalone.stderr'
    with stdout_path.open('xb') as stdout, stderr_path.open('xb') as stderr:
        try:
            process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=stdout,
                                       stderr=stderr, start_new_session=True)
            record['identity'] = proc_identity(process.pid)
            write_json(folder / 'standalone.json', record)
            deadline = time.monotonic() + 20
            match = None
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError('Owned standalone server exited during startup')
                match = re.search(r'^Independent rule-case harness: (http://127\.0\.0\.1:\d+)\s*$',
                                  stdout_path.read_text(), re.MULTILINE)
                if match:
                    break
                time.sleep(0.05)
            if not match:
                raise TimeoutError('Owned standalone server did not announce its port within 20 seconds')
            url = match.group(1) + '/'
            record['url'] = url
            record['http'] = []
            for route in ['', 'rule-case-workbench.js', 'rule-case-workbench.css']:
                with urlopen(url + route, timeout=10) as response:
                    body = response.read(4 * 1024 * 1024 + 1)
                    if response.status != 200 or len(body) > 4 * 1024 * 1024:
                        raise RuntimeError('Owned standalone HTTP identity check failed')
                    row = {'url': url + route, 'status': response.status,
                           'headers': dict(response.headers), 'sha256': hashlib.sha256(body).hexdigest()}
                (folder / ('standalone-' + (route or 'index.html'))).write_bytes(body)
                if route and body != (ROOT / 'geometry-web' / route).read_bytes():
                    raise RuntimeError('Standalone static bytes differ from pinned source: ' + route)
                record['http'].append(row)
            record['ready'] = now()
            write_json(folder / 'standalone.json', record)
            yield url
        finally:
            # SIGINT invokes this service's documented adapter.close()/server_close().
            # Popen retains our direct child identity until wait/poll reaps it.
            if process is not None:
                for sig, timeout in [(signal.SIGINT, 15), (signal.SIGTERM, 5), (signal.SIGKILL, 5)]:
                    if process.poll() is not None:
                        break
                    try:
                        current = proc_identity(process.pid)
                        original = record['identity']
                        if current['startTicks'] != original['startTicks'] or current['pgid'] != process.pid:
                            record['cleanupError'] = 'Owned PID identity changed; refused signal'
                            break
                        os.killpg(process.pid, sig)
                    except (FileNotFoundError, ProcessLookupError):
                        if process.poll() is not None:
                            break
                        raise
                    record['signals'].append({'signal': sig.name, 'at': now(), 'identity': current})
                    try:
                        process.wait(timeout=timeout)
                    except subprocess.TimeoutExpired:
                        pass
                record['exitCode'] = process.poll()
                if record['exitCode'] is None:
                    record['cleanupError'] = record.get('cleanupError', 'Owned service failed to stop')
            record['finished'] = now()
            record['stdoutSha256'], record['stderrSha256'] = digest(stdout_path), digest(stderr_path)
            write_json(folder / 'standalone.json', record)
            if record.get('cleanupError'):
                raise RuntimeError(record['cleanupError'])


def gate_arguments(name, temporary):
    command = list(GATES[name]['command'])
    extra = {}
    if name == 'scenario-grid-owner':
        extra['GEOMETRY_SCENARIO_PROJECT_MODULE'] = str(ROOT / 'geometry-web/project-store.js')
    elif name == 'scenario-module-browser':
        extra['GEOMETRY_SCENARIO_TEST_DIR'] = str(temporary)
    elif name == 'evidence-component-browser':
        extra['GEOMETRY_EVIDENCE_TEST_DIR'] = str(temporary)
    elif name == 'rule-case-standalone-browser':
        extra['GEOMETRY_RULE_CASE_BROWSER_EVIDENCE'] = str(temporary)
    elif name == 'create-feedback-ui':
        command.extend(['--url', FORMAL_URL, '--out', str(temporary), '--chromium', '/usr/bin/chromium'])
    return command, extra


def run_one(release, name, folder, temporary, base_env, expected_head):
    folder.mkdir()
    command, extra = gate_arguments(name, temporary)
    env = dict(base_env, **extra)
    record = {'gate': name, 'started': now(), 'definition': GATES[name],
              'command': command, 'timeoutSeconds': GATES[name]['timeout'],
              'formalIdentityAnchor': FORMAL_URL, 'environment': public_env(env),
              'temporaryEvidence': str(temporary), 'driverSha256': digest(__file__),
              'releaseGateSha256': digest(ROOT / 'tests/release_gate.py'),
              'testScriptSha256': digest(ROOT / next(x for x in command if x.startswith(('tests/', 'geometry-web/')))),
              'expectedHead': expected_head, 'exitCode': 2, 'productAcceptanceClaim': False}
    try:
        record['sourceBefore'] = exact_source(expected_head)
        record['adapterHashes'] = check_adapters()
        record['preflight'] = release.snapshot(ROOT, FORMAL_URL, env)
        if record['preflight']['problems']:
            raise RuntimeError('Formal identity/native preflight rejected: ' + json.dumps(record['preflight']['problems']))
        context = standalone(folder, env) if GATES[name].get('standalone') else contextlib.nullcontext(None)
        with context as owner_url:
            if owner_url:
                env['GEOMETRY_RULE_CASE_TEST_URL'] = owner_url
                record['actualTargetUrl'] = owner_url
            record['environment'] = public_env(env)
            record['releaseGateApi'] = 'tests/release_gate.py:run_gate (unmodified)'
            write_json(folder / 'command.json', record)
            with (folder / 'wrapper.stdout').open('x') as stdout, (folder / 'wrapper.stderr').open('x') as stderr:
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    code, receipt = release.run_gate(ROOT, FORMAL_URL, folder / 'release-gate',
                                                     command, env, GATES[name]['timeout'])
            record['exitCode'] = code
            record['receiptStatus'] = receipt['status']
            record['executionVerified'] = receipt['executionVerified']
            if receipt['status'] in {'timed-out', 'interrupted'}:
                record['detachedNativeDescendants'] = (
                    'unknown: release_gate stops its owned command group; existing native helpers '
                    'can own separate sessions. Review exact owned PIDs before claiming all descendants exited.')
        record['sourceAfter'] = exact_source(expected_head)
    except (KeyboardInterrupt, InterruptedError) as error:
        record['exitCode'], record['interrupted'], record['error'] = 130, True, str(error)
    except Exception as error:
        record['exitCode'], record['error'] = 2, repr(error)
    finally:
        record['finished'] = now()
        write_json(folder / 'command.json', record)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--list', action='store_true', help='List definitions without HTTP, service, browser, or test execution')
    parser.add_argument('--run-id', help='Fresh output ID (letters/digits/underscore/hyphen only)')
    parser.add_argument('--head', default=EXPECTED_HEAD,
                        help='Expected full 40-character clean commit SHA; recorded and checked for every gate')
    parser.add_argument('gates', nargs='*', help='Explicit names, or all')
    args = parser.parse_args()
    if not re.fullmatch(r'[0-9a-f]{40}', args.head):
        parser.error('--head must be an explicit full lowercase 40-character commit SHA')
    if args.list:
        print(json.dumps({'expectedHead': args.head, 'formalIdentityAnchor': FORMAL_URL,
                          'gates': GATES}, indent=2))
        return 0
    if not args.run_id or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', args.run_id):
        parser.error('a fresh --run-id is required')
    names = list(GATES) if args.gates == ['all'] else args.gates
    if not names or len(set(names)) != len(names) or any(name not in GATES for name in names):
        parser.error('choose one or more distinct gate names, or all')
    OUT.mkdir(parents=True, exist_ok=True)
    TEMP.mkdir(parents=True, exist_ok=True)
    with (OUT / '.owner-driver.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error('another owner driver is active; do not run browser suites concurrently')
        folder, temporary = OUT / args.run_id, TEMP / args.run_id
        if folder.exists() or temporary.exists():
            parser.error('refuse overwriting output or temporary evidence; choose a new run ID')
        folder.mkdir()
        temporary.mkdir()
        run = {'started': now(), 'argv': sys.argv, 'driverSha256': digest(__file__),
               'expectedHead': args.head, 'selected': names, 'results': [],
               'limitations': ['Run only after other browser suites are idle; this lock covers only this driver.',
                   'Formal runtime is an auxiliary source/native identity anchor for standalone/module gates.',
                   'Owner/component results do not imply formal ZIP/save acceptance.',
                   'Process cleanup is limited to the service/test children this driver starts.',
                   'Timed-out/interrupted detached native descendants require separate exact-PID review.']}
        exit_code = 2
        try:
            run['source'] = exact_source(args.head)
            run['adapterHashes'] = check_adapters()
            old_soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
            minimum = 16 * 1024 * 1024
            if old_soft != resource.RLIM_INFINITY and old_soft < minimum:
                if hard != resource.RLIM_INFINITY and hard < minimum:
                    raise RuntimeError('Process stack hard limit is below documented 16 MiB floor')
                resource.setrlimit(resource.RLIMIT_STACK, (minimum, hard))
            run['stackBytes'] = {'before': [old_soft, hard], 'effective': list(resource.getrlimit(resource.RLIMIT_STACK))}
            release = load_release_gate()
            env = environment()
            exit_code = 0
            for name in names:
                print(json.dumps({'gate': name, 'phase': 'start', 'utc': now()}), flush=True)
                result = run_one(release, name, folder / name, temporary / name, env, args.head)
                run['results'].append({'gate': name, 'exitCode': result['exitCode'],
                                       'commandRecord': str(folder / name / 'command.json')})
                print(json.dumps(run['results'][-1]), flush=True)
                if result['exitCode']:
                    exit_code = 1
                if result.get('interrupted') or result.get('receiptStatus') == 'interrupted':
                    exit_code = 130
                    break
                write_json(folder / 'summary.json', run)
        except (KeyboardInterrupt, InterruptedError) as error:
            run['error'], exit_code = str(error), 130
        except Exception as error:
            run['error'], exit_code = repr(error), 2
        finally:
            run['finished'], run['exitCode'] = now(), exit_code
            write_json(folder / 'summary.json', run)
        return exit_code


if __name__ == '__main__':
    def interrupt(signum, _frame):
        raise InterruptedError('received signal ' + str(signum))
    signal.signal(signal.SIGTERM, interrupt)
    sys.exit(main())
