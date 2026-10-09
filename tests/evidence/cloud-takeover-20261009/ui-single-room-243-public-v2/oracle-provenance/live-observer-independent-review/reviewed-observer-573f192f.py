"""Observe live executables around an unchanged existing scoped gate.

Only writes new scratch evidence. No probe, source, assertion or service edits.
The inner original gate keeps its own unchanged receipt and raw log.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback
from urllib.request import urlopen


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def live(pid, cache):
    root = Path('/proc') / str(pid)
    stat = (root / 'stat').read_text().rsplit(')', 1)[1].split()
    exe = (root / 'exe').resolve(strict=True)
    argv = (root / 'cmdline').read_bytes().decode(errors='replace').rstrip('\0').split('\0')
    cwd = str((root / 'cwd').resolve())
    with (root / 'exe').open('rb') as stream:
        before = os.fstat(stream.fileno())
        disk = exe.stat()
        key = (str(exe), before.st_dev, before.st_ino, before.st_size,
               before.st_mtime_ns, before.st_ctime_ns)
        assert (disk.st_dev, disk.st_ino) == (before.st_dev, before.st_ino)
        digest = cache.get(key)
        if digest is None:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        after = os.fstat(stream.fileno())
    current_stat = (root / 'stat').read_text().rsplit(')', 1)[1].split()
    current_argv = (root / 'cmdline').read_bytes().decode(errors='replace').rstrip('\0').split('\0')
    if not (stat[1] == current_stat[1] and stat[19] == current_stat[19] and
            exe == (root / 'exe').resolve(strict=True) and argv == current_argv and
            key[1:] == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)):
        raise ValueError('Process/executable identity changed during live capture; retry observation')
    cache[key] = digest
    parent = int(stat[1])
    try:
        parent_start = (Path('/proc') / str(parent) / 'stat').read_text().rsplit(')', 1)[1].split()[19]
    except OSError:
        parent_start = None
    return {'pid': pid, 'parent': parent, 'parentStartTicks': parent_start,
            'state': stat[0], 'startTicks': stat[19],
            'exe': str(exe), 'sha256': digest,
            'executableFileIdentity': {'device': before.st_dev, 'inode': before.st_ino,
                                       'size': before.st_size, 'mtimeNs': before.st_mtime_ns,
                                       'ctimeNs': before.st_ctime_ns},
            'argv': argv, 'cwd': cwd, 'observedAt': now()}


def children(ancestor):
    parents = {}
    for root in Path('/proc').iterdir():
        if not root.name.isdecimal():
            continue
        try:
            parents[int(root.name)] = int((root / 'stat').read_text().rsplit(')', 1)[1].split()[1])
        except (OSError, ValueError):
            pass
    selected = {ancestor}
    while True:
        added = {pid for pid, parent in parents.items() if parent in selected} - selected
        if not added:
            return selected
        selected |= added


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--expected-head', required=True)
    parser.add_argument('--url', required=True)
    parser.add_argument('--bridge', type=Path, required=True)
    parser.add_argument('--model-base', type=Path, required=True)
    parser.add_argument('--feedback-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--artifact-dir', type=Path, required=True)
    parser.add_argument('--expected-cases', type=int, required=True)
    parser.add_argument('--timeout', type=float, default=900)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    root, output = args.root.resolve(), args.output.resolve()
    probe = args.command[1:] if args.command[:1] == ['--'] else args.command
    assert probe and len(args.expected_head) == 40
    assert not output.is_relative_to(root)
    output.mkdir(parents=True, exist_ok=False)
    gate = Path('<original-evidence-root>/run_gate.py')
    before = {}
    cache = {}
    def snapshot(value):
        value['at'] = now()
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
        dirty = subprocess.check_output(['git', 'status', '--short'], cwd=root, text=True)
        value.update(fullSHA=head, dirty=dirty)
        assert head == args.expected_head and dirty == '', (head, dirty)
        with urlopen(args.url.rstrip('/') + '/runtime', timeout=10) as response:
            runtime = json.loads(response.read())
        value['runtime'] = runtime
        assert runtime['fresh'] is True and Path(runtime['root']).resolve() == root
        configured = {}
        for name, exe in [('python', sys.executable), ('node', shutil.which('node')),
                          ('chromeLauncher', '/usr/bin/chromium')]:
            configured[name] = {'path': str(exe), 'resolved': str(Path(exe).resolve()),
                                'sha256': sha(Path(exe).resolve()),
                                'version': subprocess.check_output([str(exe), '--version'], text=True,
                                                                   stderr=subprocess.STDOUT).strip()}
        service = []
        transient_service = []
        for pid in sorted(children(runtime['pid'])):
            try:
                service.append(live(pid, cache))
            except (OSError, ValueError) as error:
                transient_service.append({'pid': pid, 'error': repr(error)})
        bridge = args.bridge.resolve()
        native = [value for value in service if value['parent'] == runtime['pid'] and value['exe'] == str(bridge)]
        value.update(configuredExecutables=configured, actualServiceProcesses=service,
                     nativeActualChildren=native, transientServiceProcessCaptureErrors=transient_service)
        assert native and all(value['sha256'] == sha(bridge) for value in native)
        files = {str(Path(__file__).resolve()): sha(__file__), str(gate): sha(gate)}
        for argument in probe:
            source = Path(argument)
            if not source.is_absolute():
                source = root / source
            if source.is_file():
                files[str(source.resolve())] = sha(source)
                for sibling in source.parent.iterdir():
                    if sibling.is_file() and sibling.suffix in ['.py', '.js', '.json', '.cjs']:
                        files[str(sibling.resolve())] = sha(sibling)
        value.update(executionFiles=files, actualThisWrapper=live(os.getpid(), cache))
        return value
    after, observed, latest, transient = {}, {}, {}, []
    checks, inner = {}, {}
    probe_python, driver_node, main_chrome = [], [], []
    probe_pid, code, child, fatal = None, None, None, None
    result, started = 2, now()
    command = []
    inner_path = output / 'inner-gate' / 'receipt.json'
    try:
        before = snapshot(before)
        command = [sys.executable, str(gate), '--root', str(root), '--url', args.url,
                   '--bridge', str(args.bridge.resolve()), '--model-base', str(args.model_base.resolve()),
                   '--feedback-dir', str(args.feedback_dir.resolve()), '--output', str(output / 'inner-gate'),
                   '--artifact-dir', str(args.artifact_dir.resolve()), '--expected-cases', str(args.expected_cases),
                   '--timeout', str(args.timeout), '--', *probe]
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        observed, latest, transient = {}, {}, []
        started = now()
        with (output / 'wrapper.log').open('xb') as log:
            child = subprocess.Popen(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT,
                                     start_new_session=True)
            deadline = time.monotonic() + args.timeout + 60
            while child.poll() is None and time.monotonic() < deadline:
                for pid in sorted(children(child.pid)):
                    try:
                        value = live(pid, cache)
                        if value['state'] != 'Z':
                            # Retain exec transitions rather than permanently
                            # treating a first-seen launcher shell as its browser.
                            key = (pid, value['startTicks'], value['exe'], tuple(value['argv']))
                            observed.setdefault(key, value)
                            latest[pid] = value
                    except (OSError, ValueError) as error:
                        transient.append({'pid': pid, 'at': now(), 'error': repr(error)})
                time.sleep(.05)
            if child.poll() is None:
                # Inner release_gate gives its test a separate process group. Stop
                # only still-owned descendants if its timeout machinery stalled.
                for pid in sorted(children(child.pid), reverse=True):
                    try:
                        current = live(pid, cache)
                        saved = latest.get(pid)
                        if saved is None or current['startTicks'] == saved['startTicks']:
                            os.kill(pid, 15)
                    except ProcessLookupError:
                        pass
                try:
                    os.killpg(child.pid, 15)
                except ProcessLookupError:
                    pass
                child.wait(timeout=10)
            code = child.returncode
        after = snapshot(after)
        inner_path = output / 'inner-gate' / 'receipt.json'
        inner = json.loads(inner_path.read_text()) if inner_path.is_file() else {}
        probe_pid = inner.get('execution', {}).get('pid')
        probe_python = [v for v in observed.values() if v['pid'] == probe_pid and
                        v['argv'] == probe and v['exe'] == str(Path(probe[0]).resolve())]
        driver_node = [v for v in observed.values() if Path(v['exe']).name == 'node' and
                       any('playwright' in arg for arg in v['argv']) and
                       any(v['parent'] == p['pid'] and v['parentStartTicks'] == p['startTicks']
                           for p in probe_python)]
        main_chrome = [v for v in observed.values() if 'chromium' in Path(v['exe']).name and
                       '--remote-debugging-pipe' in v['argv'] and
                       not any(arg.startswith('--type=') for arg in v['argv']) and
                       any(v['parent'] == n['pid'] and v['parentStartTicks'] == n['startTicks']
                           for n in driver_node)]
        checks = {
            'fullSHAAndDirtyStable': before['fullSHA'] == after['fullSHA'] and before['dirty'] == after['dirty'] == '',
            'executionFilesStable': before['executionFiles'] == after['executionFiles'],
            'configuredExecutableBytesStable': before['configuredExecutables'] == after['configuredExecutables'],
            'exactRuntimeStable': before['runtime'] == after['runtime'],
            'nativePidBytesStable': [(v['pid'], v['startTicks'], v['exe'], v['sha256']) for v in before['nativeActualChildren']] ==
                                   [(v['pid'], v['startTicks'], v['exe'], v['sha256']) for v in after['nativeActualChildren']],
            'actualProbePythonObserved': bool(probe_python),
            'actualPlaywrightDriverNodeObserved': bool(driver_node),
            'actualMainChromeObserved': bool(main_chrome),
        }
        checks['innerOriginalGateVerified'] = (code == 0 and inner.get('probeVerified') is True and
                                             inner.get('probeCensus', {}).get('completed') is True and
                                             inner.get('probeCensus', {}).get('actualCases') == args.expected_cases)
        result = 0 if all(checks.values()) else (code or 2)
    except Exception as error:
        fatal = {'error': repr(error), 'traceback': traceback.format_exc()}
        result = 2
    finally:
        if child is not None and child.poll() is None:
            try:
                for pid in sorted(children(child.pid), reverse=True):
                    try:
                        current = live(pid, cache)
                        saved = latest.get(pid)
                        if saved is None or current['startTicks'] == saved['startTicks']:
                            os.kill(pid, 15)
                    except (OSError, ValueError):
                        pass
                child.wait(timeout=10)
            except Exception as cleanup_error:
                fatal = {**(fatal or {}), 'cleanupError': repr(cleanup_error)}
                result = 2
        if not (output / 'wrapper.log').exists():
            (output / 'wrapper.log').write_bytes(b'')
        if inner_path.is_file() and not inner:
            try:
                inner = json.loads(inner_path.read_text())
            except (OSError, ValueError) as receipt_error:
                fatal = {**(fatal or {}), 'innerReceiptReadError': repr(receipt_error)}
        if fatal:
            checks['noObserverFailure'] = False
    receipt = {'schema': 'geometry-scoped-live-interpreter-observation/1', 'actor': '/root/race_review',
               'started': started, 'finished': now(), 'command': command, 'cwd': str(root),
               'fatalObserverError': fatal, 'expectedFullSHA': args.expected_head,
               'probeCommand': probe, 'innerExitCode': code, 'exitCode': result,
               'before': before, 'after': after, 'observedActualOwnedProbeProcesses': list(observed.values()),
               'directActualProbeBindings': {'innerGateExecutionPid': probe_pid, 'probePython': probe_python,
                                            'ownedDriverNode': driver_node, 'ownedMainChrome': main_chrome,
                                            'rule': 'Exact inner execution pid and argv for probe Python; direct parent pid plus process startTicks bind Node to that Python and Chrome to that Node, observed live.'},
               'transientProcessCaptureErrors': transient, 'checks': checks,
               'innerOriginalGate': {'path': str(inner_path), 'sha256': sha(inner_path) if inner_path.is_file() else None},
               'rawLog': {'path': str(output / 'wrapper.log'), 'sha256': sha(output / 'wrapper.log')},
               'originalCommandRawLog': inner.get('log'), 'probeCensus': inner.get('probeCensus'),
               'scope': 'One unchanged scoped probe with actual live process bytes, not full CDP/Windows/golden. The inner original gate and probe are not modified.'}
    path = output / 'receipt.json'
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'exitCode': result, 'checks': checks, 'census': receipt['probeCensus'],
                      'receipt': str(path), 'sha256': sha(path)}, ensure_ascii=False))
    return result


if __name__ == '__main__':
    sys.exit(main())
