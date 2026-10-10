from pathlib import Path
import datetime, hashlib, json, os, subprocess, sys, time, urllib.request

mode, stem = sys.argv[1:]
assert mode in ('cdp', 'space')
root = Path('<workspace-path>')
expected = '9eb670110379ec0d726914f3e5b2d8e7237f2b9c'
runtime_version = '7c6a3a77c727ec51537923b5accfb69e1e3acefcf59a553749bc986b82f87cd7'
base = Path('<original-evidence-root>')
output = Path('<workspace-path>') / (stem + '-gate')
control = Path('<workspace-path>') / (stem + '-lifecycle')
assert not output.exists() and not control.exists()
control.mkdir()
port = 19182 if mode == 'cdp' else 19180
native = Path('<isolated-test-directory>' if mode == 'cdp' else '<isolated-test-directory>')
url = 'http://127.0.0.1:' + str(port) + '/'
git = lambda args: subprocess.check_output(['git', *args], cwd=root, text=True).strip()
assert git(['rev-parse', 'HEAD']) == expected and git(['status', '--porcelain=v1', '--untracked-files=all']) == ''
python = Path('/proc/self/exe').resolve()
launch = Path('<workspace-path>')
runner = base / ('run_full_cdp_identity.py' if mode == 'cdp' else 'run_full_space_identity.py')
expected_runner = '5ce8212de96e45d0b613b17888a053a7a679024dc1a230f4c734a6170cc5da89' if mode == 'cdp' else '8b9729cb300347361b2f6bf507e08fd6fab662ec2bc9f0fca107fb2da02dadae'
assert hashlib.sha256(runner.read_bytes()).hexdigest() == expected_runner
service_command = [str(python), str(launch), str(root), str(port), str(native)]
test_command = [str(python), str(runner), '--root', str(root), '--url', url, '--output', str(output),
                '--expected-head', expected, '--bridge', str(native / 'bridge'), '--model-base', str(native / 'model-base'),
                '--feedback-dir', '<isolated-test-directory>' + str(port), '--timeout', '2400']
record = {'schema': 'geometry-root-owned-integration-lifecycle/1', 'startedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'mode': mode, 'expectedFullSHA': expected, 'dirtyBefore': '', 'serviceCommand': service_command,
          'testCommand': test_command, 'actualPython': str(python), 'actualPythonSHA256': hashlib.sha256(python.read_bytes()).hexdigest(),
          'controllerSHA256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'runnerSHA256': expected_runner,
          'launchSHA256': hashlib.sha256(launch.read_bytes()).hexdigest(),
          'reason': 'Recover necessary same-SHA full integration after original independent services disappeared; raw incomplete results and missing original exits remain unchanged.'}
(control / 'started.json').write_text(json.dumps(record, indent=2) + '\n')
with (control / 'service.stdout.raw.log').open('wb') as service_stdout, (control / 'service.stderr.raw.log').open('wb') as service_stderr:
    service = subprocess.Popen(service_command, cwd=root, stdout=service_stdout, stderr=service_stderr, start_new_session=True)
    try:
        deadline = time.monotonic() + 30
        runtime = None
        while time.monotonic() < deadline:
            assert service.poll() is None, 'Owned service exited during readiness'
            try:
                runtime = json.load(urllib.request.urlopen(url + 'runtime', timeout=1))
                break
            except Exception:
                time.sleep(.1)
        assert runtime and runtime['pid'] == service.pid and runtime['root'] == str(root)
        assert runtime['fresh'] is True and runtime['version'] == runtime_version
        (control / 'ready-runtime.json').write_text(json.dumps(runtime, indent=2) + '\n')
        print(json.dumps({'readyOwnedService': service.pid, 'mode': mode, 'fullSHA': expected}), flush=True)
        with (control / 'gate.stdout.raw.log').open('wb') as stdout, (control / 'gate.stderr.raw.log').open('wb') as stderr:
            test = subprocess.Popen(test_command, cwd=root, stdout=stdout, stderr=stderr)
            record['gateProcessPID'] = test.pid
            heartbeat = time.monotonic()
            while test.poll() is None:
                if time.monotonic() - heartbeat >= 20:
                    print(json.dumps({'ownedServicePID': service.pid, 'serviceExitObserved': service.poll(), 'gatePID': test.pid,
                                      'rawLog': str(output / 'command.log')}), flush=True)
                    heartbeat = time.monotonic()
                time.sleep(.1)
        record['actualGateExitCode'] = test.returncode
        record['serviceExitBeforeStop'] = service.poll()
        assert (output / 'receipt.json').exists(), 'Original gate did not seal its receipt'
        print((control / 'gate.stdout.raw.log').read_text(), flush=True)
        stop = Path('<workspace-path>')
        helper = Path('<workspace-path>' if mode == 'cdp' else '<workspace-path>')
        stop_command = [str(python), str(stop), str(helper), str(root), str(port), str(control / 'owned-stop'), str(output)]
        result = subprocess.run(stop_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (control / 'stop-controller.stdout.raw.log').write_bytes(result.stdout)
        (control / 'stop-controller.stderr.raw.log').write_bytes(result.stderr)
        record['stopCommand'] = stop_command
        record['stopExitCode'] = result.returncode
        try:
            record['actualServiceExitAfterStop'] = service.wait(timeout=10)
        except subprocess.TimeoutExpired:
            record['actualServiceExitAfterStop'] = None
        assert result.returncode == 0, result.stderr.decode(errors='replace')
    except BaseException as exc:
        record['controllerError'] = repr(exc)
        record['serviceExitAtError'] = service.poll()
        (control / 'controller-error.json').write_text(json.dumps(record, indent=2) + '\n')
        raise
record['finishedUtc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
record['headAfter'] = git(['rev-parse', 'HEAD'])
record['dirtyAfter'] = git(['status', '--porcelain=v1', '--untracked-files=all'])
assert record['headAfter'] == expected and record['dirtyAfter'] == ''
record['rawFiles'] = [{'path': str(p.relative_to(control)), 'bytes': p.stat().st_size,
                      'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(control.rglob('*')) if p.is_file()]
(control / 'terminal.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'lifecycleReceipt': str(control / 'terminal.json'), 'gateExitCode': record['actualGateExitCode']}), flush=True)
sys.exit(record['actualGateExitCode'])
