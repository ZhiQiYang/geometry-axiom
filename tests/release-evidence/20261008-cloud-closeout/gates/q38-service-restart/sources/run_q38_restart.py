#!/usr/bin/env python3
"""Prepare exact bindings, restart only an owned service, then run the original 13-check Q38 probe.

This script starts services/browser ONLY when explicitly executed with all required
arguments. --help performs no execution. Use a fresh output directory and a free
loopback port distinct from the shared 18971. Native binaries are verified, never
built. Producer must be the successful existing q38_save_roundtrip.py gate on the
same clean full SHA. This is restart recovery, not a new product feature or an OS
save-dialog acceptance claim.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen

sys.dont_write_bytecode = True
ROOT = Path('/workspace/geometry-axiom')
PROBE = Path(__file__).with_name('q38_restart_probe.py')


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source(expected_head):
    result = {}
    for key, argv in [('head', ['rev-parse', 'HEAD']), ('tree', ['rev-parse', 'HEAD^{tree}']),
                      ('status', ['status', '--porcelain=v1', '--untracked-files=all'])]:
        p = subprocess.run(['git', '-C', str(ROOT), *argv], capture_output=True, text=True, timeout=20)
        if p.returncode:
            raise RuntimeError('git failed: ' + p.stderr)
        result[key] = p.stdout.strip()
    if result['head'] != expected_head or result['status']:
        raise RuntimeError('Require exact clean expected head: ' + json.dumps(result))
    return result


def proc(pid):
    raw = Path('/proc', str(pid), 'stat').read_text()
    f = raw[raw.rfind(')') + 2:].split()
    return {'pid': pid, 'ppid': int(f[1]), 'pgid': int(f[2]), 'startTicks': int(f[19])}


def service_environment(folder, bridge, model):
    env = {k: v for k, v in os.environ.items() if not k.startswith('GEOMETRY_')}
    env.update(GEOMETRY_TEST_BRIDGE=bridge, GEOMETRY_BRIDGE=bridge,
               GEOMETRY_BRIDGE_EXECUTABLE=bridge, GEOMETRY_MODEL_UPDATE_BRIDGE=bridge,
               GEOMETRY_SCENARIO_BRIDGE=bridge, GEOMETRY_MODEL_BASE=model,
               GEOMETRY_SCENARIO_BASE=model, GEOMETRY_FEEDBACK_DIR=str(folder / 'feedback'),
               GEOMETRY_REQUIRE_CLEAN='1', GEOMETRY_CHROME='/usr/bin/chromium',
               GEOMETRY_VERIFY_ROOT=str(ROOT), GEOMETRY_PYTHON=sys.executable,
               PYTHON=sys.executable, PYTHONDONTWRITEBYTECODE='1')
    return env


@contextlib.contextmanager
def owned_service(folder, port, env, expected_source):
    folder.mkdir()
    # Bind check never stops an existing occupant. serve.py's bind is authoritative.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', port))
    url = f'http://127.0.0.1:{port}/'
    command = [sys.executable, str(ROOT / 'geometry-web/serve.py'), str(port)]
    record = {'command': command, 'cwd': str(ROOT), 'url': url, 'started': now(), 'signals': [],
              'environment': {k: v for k, v in env.items() if k.startswith('GEOMETRY_') or k in ['PYTHON', 'PYTHONDONTWRITEBYTECODE']}}
    child = None
    with (folder / 'stdout').open('xb') as stdout, (folder / 'stderr').open('xb') as stderr:
        try:
            child = subprocess.Popen(command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
            record['process'] = proc(child.pid)
            write(folder / 'service.json', record)
            deadline, runtime = time.monotonic() + 30, None
            while time.monotonic() < deadline:
                if child.poll() is not None:
                    raise RuntimeError('Owned service exited before readiness')
                try:
                    with urlopen(url + 'runtime', timeout=1) as response:
                        runtime = json.load(response)
                    if runtime.get('pid') != child.pid:
                        raise RuntimeError('Port reports a different process; refusing to attach')
                    break
                except URLError:
                    time.sleep(0.1)
            if runtime is None:
                raise TimeoutError('Owned service did not become ready in 30 seconds')
            if runtime.get('root') != str(ROOT) or runtime.get('fresh') is not True:
                raise RuntimeError('Owned runtime root/source mismatch')
            current = source(expected_source['head'])
            if current != expected_source:
                raise RuntimeError('Source changed while starting own service')
            record['runtime'], record['ready'] = runtime, now()
            # These are the actual direct native children, not an inferred bridge identity.
            ps = subprocess.run(['ps', '-eo', 'pid=,ppid='], capture_output=True, text=True, check=True)
            (folder / 'processes.stdout').write_text(ps.stdout)
            (folder / 'processes.stderr').write_text(ps.stderr)
            children = [int(line.split()[0]) for line in ps.stdout.splitlines() if int(line.split()[1]) == child.pid]
            record['children'] = []
            for pid in children:
                exe = Path('/proc', str(pid), 'exe')
                record['children'].append({**proc(pid), 'executable': str(exe.resolve()), 'sha256': sha(exe)})
            bridges = [p for p in record['children'] if p['executable'] == env['GEOMETRY_BRIDGE']]
            if len(bridges) != 1 or bridges[0]['sha256'] != sha(env['GEOMETRY_BRIDGE']):
                raise RuntimeError('Require exactly one owned source-verified live bridge')
            write(folder / 'service.json', record)
            yield runtime
        finally:
            if child is not None:
                for sig, timeout in [(signal.SIGINT, 15), (signal.SIGTERM, 5), (signal.SIGKILL, 5)]:
                    if child.poll() is not None:
                        break
                    try:
                        current = proc(child.pid)
                        if current['startTicks'] != record['process']['startTicks'] or current['pgid'] != child.pid:
                            raise RuntimeError('Owned server PID identity changed; refused signal')
                        os.killpg(child.pid, sig)
                        record['signals'].append({'signal': sig.name, 'at': now(), 'identity': current})
                    except (ProcessLookupError, FileNotFoundError):
                        if child.poll() is not None:
                            break
                        raise
                    try:
                        child.wait(timeout=timeout)
                    except subprocess.TimeoutExpired:
                        pass
                record['exitCode'] = child.poll()
                record['originalChildrenRemaining'] = []
                for member in record.get('children', []):
                    try:
                        current = proc(member['pid'])
                        if current['startTicks'] == member['startTicks']:
                            record['originalChildrenRemaining'].append(current)
                    except FileNotFoundError:
                        pass
            record['finished'] = now()
            record['stdoutSha256'], record['stderrSha256'] = sha(folder / 'stdout'), sha(folder / 'stderr')
            write(folder / 'service.json', record)
            if record.get('originalChildrenRemaining') or (child is not None and record.get('exitCode') is None):
                raise RuntimeError('Owned service/bridge did not finish; inspect saved exact PID identities')


def producer_binding(args, current, folder):
    directory = args.producer_dir.resolve()
    gate = json.loads(args.producer_gate.read_text())
    run = json.loads((directory / 'run.json').read_text())
    result = json.loads((directory / 'result.json').read_text())
    if not (gate.get('executionVerified') is True and gate.get('gateExitCode') == 0
            and gate.get('execution', {}).get('exitCode') == 0
            and run.get('exitCode') == 0 and result.get('completed') is True
            and result.get('expected') == result.get('passed') == 18 and result.get('failed') == 0):
        raise RuntimeError('Need successful complete existing 18-check Q38 producer')
    if not any(str(x).endswith('tests/integration/q38_save_roundtrip.py') for x in gate.get('command', [])):
        raise RuntimeError('Producer receipt is not the canonical Q38 save gate')
    for observed in [run['before'], run['after'], gate['before']['git'], gate['after']['git']]:
        if {k: observed[k] for k in ['head', 'tree', 'status']} != current:
            raise RuntimeError('Producer must have the same exact clean source; rerun producer after product changes')
    if run['before'] != run['after']:
        raise RuntimeError('Producer before/after identities differ')
    if Path(run.get('environment', {}).get('GEOMETRY_Q38_SAVE_OUT', '')).resolve() != directory:
        raise RuntimeError('Producer run receipt belongs to a different output directory')
    if not (run['before']['runtime'] == gate['before']['runtime'] == gate['after']['runtime']):
        raise RuntimeError('Producer run and release receipt runtime identities differ')
    if run.get('environment', {}).get('GEOMETRY_TEST_URL', '').rstrip('/') != gate.get('url', '').rstrip('/'):
        raise RuntimeError('Producer run and release receipt URLs differ')
    if run['harnessSha256'] != sha(ROOT / 'tests/integration/q38_save_roundtrip.py'):
        raise RuntimeError('Producer script is not the currently reviewed canonical script')
    if sha(gate['log']['path']) != gate['log']['sha256']:
        raise RuntimeError('Producer raw log hash mismatch')
    # New binding records current files and their original successful execution
    # receipts. It does not pretend the old harness emitted hashes it did not emit.
    copied = folder / 'producer'
    copied.mkdir()
    files = [directory / name for name in ['q38-full.gcanvas', 'original-model.json', 'manifest.json', 'run.json', 'result.json']]
    files.append(args.producer_gate.resolve())
    mapping = []
    for n, path in enumerate(files):
        destination = copied / ('release-receipt.json' if n == 5 else path.name)
        shutil.copyfile(path, destination)
        mapping.append({'originalPath': str(path), 'copy': str(destination), 'sha256': sha(path), 'bytes': path.stat().st_size})
    archive, baseline = copied / 'q38-full.gcanvas', copied / 'original-model.json'
    binding = {**current, 'runtime': run['before']['runtime'], 'gate': 'q38-fresh-save',
               'artifactsSha256': {str(archive): sha(archive), str(baseline): sha(baseline)},
               'recordedAt': now(), 'bindingOrigin': 'current private wrapper after validating producer receipt/result; not inherited historical delivery',
               'files': mapping, 'sourceProducerGate': str(args.producer_gate), 'producerGateSha256': sha(args.producer_gate)}
    write(folder / 'producer-binding.json', binding)
    return binding, archive, baseline


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--head', required=True, help='Expected full 40-character SHA')
    parser.add_argument('--producer-dir', required=True, type=Path)
    parser.add_argument('--producer-gate', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--port', type=int, default=18973)
    args = parser.parse_args()
    if not re.fullmatch(r'[0-9a-f]{40}', args.head):
        parser.error('--head must be a full lowercase SHA')
    if args.port in (8765, 18971) or not 1024 <= args.port <= 65535:
        parser.error('use an isolated unprivileged port, never 8765/shared 18971')
    folder = args.out.resolve()
    if not args.out.is_absolute() or folder == ROOT or ROOT in folder.parents or folder.exists():
        parser.error('--out must be a fresh absolute directory outside the repository')
    folder.mkdir(parents=True)
    record = {'started': now(), 'command': [sys.executable, *sys.argv], 'driverSha256': sha(__file__),
              'probeSha256': sha(PROBE), 'expectedHead': args.head, 'exitCode': 2,
              'limitations': ['Q38 section-profile fixture only; no assembly drafts, live placement host, or OS save dialog.',
                  'Exactly the original 13 product checks; current-run binding and owned restart are new preconditions.',
                  'No existing service is stopped; shared 18971 is never used by this wrapper.']}
    try:
        current = source(args.head)
        record['sourceBefore'] = current
        producer, archive, baseline = producer_binding(args, current, folder)
        registry = load_module(ROOT / 'tests/binaries.py', 'restart_binaries')
        bridge = str(Path(registry.require_fresh('bridge', Path('/tmp/geometry-tests/bridge'))).resolve())
        model = str(Path(registry.require_fresh('model-base', Path('/tmp/geometry-tests/model-base'))).resolve())
        soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
        if soft != resource.RLIM_INFINITY and soft < 16 * 1024 * 1024:
            if hard != resource.RLIM_INFINITY and hard < 16 * 1024 * 1024:
                raise RuntimeError('Stack hard limit is below documented 16 MiB floor')
            resource.setrlimit(resource.RLIMIT_STACK, (16 * 1024 * 1024, hard))
        record['stackBytes'] = list(resource.getrlimit(resource.RLIMIT_STACK))
        env = service_environment(folder, bridge, model)
        release = load_module(ROOT / 'tests/release_gate.py', 'restart_release_gate')
        url = f'http://127.0.0.1:{args.port}/'
        with owned_service(folder / 'service-before-restart', args.port, env, current) as first:
            first_snapshot = release.snapshot(ROOT, url, env)
            if first_snapshot['problems']:
                raise RuntimeError('First own-service source/native preflight failed')
            write(folder / 'before-restart-identity.json', first_snapshot)
        with owned_service(folder / 'service-after-restart', args.port, env, current) as second:
            after_snapshot = release.snapshot(ROOT, url, env)
            if after_snapshot['problems'] or first['pid'] == second['pid'] or first['session'] == second['session']:
                raise RuntimeError('Owned restart identity/native preflight failed')
            write(folder / 'after-restart-identity.json', after_snapshot)
            binding = {**current, 'root': str(ROOT), 'url': url, 'output': str(folder / 'probe'),
                       'archive': str(archive), 'baseline': str(baseline), 'archiveSha256': sha(archive),
                       'chromium': '/usr/bin/chromium', 'producer': producer,
                       'producerBindingPath': str(folder / 'producer-binding.json'),
                       'restart': {'before': first_snapshot, 'after': after_snapshot}}
            binding_path = folder / 'binding.json'
            write(binding_path, binding)
            command = [sys.executable, str(PROBE), '--binding', str(binding_path)]
            with (folder / 'wrapper.stdout').open('x') as stdout, (folder / 'wrapper.stderr').open('x') as stderr:
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    code, receipt = release.run_gate(ROOT, url, folder / 'release-gate', command, env, 1200)
            record['gateExitCode'], record['gateStatus'] = code, receipt['status']
            if code:
                raise RuntimeError('Restart probe failed; preserve original raw failure')
            observed = json.loads((folder / 'probe/result.json').read_text())
            if not (observed.get('completed') is True and observed.get('expected') == observed.get('passed') == 13
                    and observed.get('failed') == 0):
                raise RuntimeError('Restart probe is not a complete 13-check result')
            record['result'] = observed
        record['sourceAfter'] = source(args.head)
        if record['sourceAfter'] != current or sha(PROBE) != record['probeSha256']:
            raise RuntimeError('Source or private probe changed during execution')
        for item in producer['files']:
            if sha(item['originalPath']) != item['sha256'] or sha(item['copy']) != item['sha256']:
                raise RuntimeError('Producer evidence changed during restart run')
        record['exitCode'] = 0
    except (KeyboardInterrupt, InterruptedError) as error:
        record['exitCode'], record['error'] = 130, str(error)
    except Exception as error:
        record['error'] = repr(error)
    finally:
        record['finished'] = now()
        write(folder / 'driver-receipt.json', record)
    print(json.dumps({'exitCode': record['exitCode'], 'receipt': str(folder / 'driver-receipt.json')}, ensure_ascii=False))
    return record['exitCode']


if __name__ == '__main__':
    def interrupted(signum, _frame):
        raise InterruptedError('received signal ' + str(signum))
    signal.signal(signal.SIGTERM, interrupted)
    sys.exit(main())
