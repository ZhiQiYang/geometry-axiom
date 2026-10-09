from pathlib import Path
import datetime, hashlib, importlib.util, json, os, subprocess, sys, time, urllib.request

root = Path('<workspace-path>')
full = 'f3b8285729b42cd22451c98cba1e2ec4514517f3'
gate = Path('<workspace-path>')
life = Path('<workspace-path>')
out = Path('<workspace-path>')
assert not out.exists()
out.mkdir()
base = Path('<workspace-path>')
spec = importlib.util.spec_from_file_location('original_actual_identity', base / 'cdp_execution_identity_v2.py')
identity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(identity)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
git = lambda a: subprocess.check_output(['git', *a], cwd=root, text=True).strip()
now = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
log = gate / 'command.log'
scopes = [json.loads(l[len('CDP_SCOPE '):]) for l in log.read_text().splitlines() if l.startswith('CDP_SCOPE ')]
assert len(scopes) == 1
scope = scopes[0]
assert scope['mode'] == 'full' and scope['filters'] == [] and scope['modifiers'] == []
assert scope['url'] == 'http://127.0.0.1:19182/'
chrome_pid = scope['browserPid']
status = Path('/proc', str(chrome_pid), 'status').read_text()
node_pid = int(next(l.split()[1] for l in status.splitlines() if l.startswith('PPid:')))
processes = [identity.process_snapshot('actual surviving canonical Chromium', chrome_pid),
             identity.process_snapshot('actual surviving canonical Node', node_pid)]
assert identity.is_main_chromium(processes[0]['exe'], processes[0]['cmdline'], scope['browserProfile'], scope['cdpPort'])
assert processes[0]['executableMagicHex'] == processes[1]['executableMagicHex'] == '7f454c46'
assert processes[1]['cmdline'] == ['node', 'geometry-web/cdp_test.js'] and processes[1]['cwd'] == str(root)
assert all(a not in processes[0]['cmdline'] for a in ['--no-sandbox', '--disable-setuid-sandbox'])
assert str(Path('/proc', str(node_pid), 'fd/1').resolve()) == str(log)
assert str(Path('/proc', str(node_pid), 'fd/2').resolve()) == str(log)
def snapshot(label):
    assert git(['rev-parse', 'HEAD']) == full and git(['status', '--porcelain']) == ''
    raw = urllib.request.urlopen(scope['url'] + 'runtime', timeout=3).read()
    (out / (label + '-runtime.raw.json')).write_bytes(raw)
    runtime = json.loads(raw)
    assert runtime['root'] == str(root) and runtime['pid'] == 254424 and runtime['fresh'] is True
    assert runtime['version'] == 'efbcfff4ca94d6a1844228ea59628ee5de24dcd5e337c62f9c0587f5a38c8a11'
    assert runtime['session'] == 'c70dcdead1244676b9f9ba4f68782661'
    paths = [p for p in sorted((root / 'geometry-web').iterdir()) if p.is_file() and p.suffix in {'.js', '.css', '.html'}]
    paths += [root / 'geometry-web/cdp_sections.golden.json', root / 'tests/release_gate.py', root / 'tests/binaries.py']
    sources = {str(p.relative_to(root)): sha(p) for p in paths}
    for p in paths:
        assert hashlib.sha256(subprocess.check_output(['git', 'show', full + ':' + str(p.relative_to(root))], cwd=root)).hexdigest() == sha(p)
    native = []
    for pid, exe in [(254424, str(Path('/proc/254424/exe').resolve())), (254425, '<isolated-test-directory>')]:
        record = identity.process_snapshot('actual surviving owned service/native', pid)
        assert record['exe'] == exe
        native.append(record)
    return {'observedUtc': now(), 'head': full, 'dirty': '', 'runtime': runtime, 'sources': sources, 'serviceNative': native}
before = snapshot('attachment-before')
for pid in [254428, chrome_pid, node_pid, 254424, 254425]:
    (out / ('attachment-before-proc-' + str(pid) + '.stat.raw')).write_bytes(Path('/proc', str(pid), 'stat').read_bytes())
started = json.loads((life / 'started.json').read_text())
ready = json.loads((life / 'ready-runtime.json').read_text())
assert started['expectedFullSHA'] == full and started['dirtyBefore'] == ''
assert ready == before['runtime']
attached = {'schema': 'geometry-live-surviving-canonical-full-attachment/1', 'attachedUtc': now(),
            'command': sys.argv, 'actualPython': str(Path('/proc/self/exe').resolve()),
            'actualPythonSHA256': sha('/proc/self/exe'), 'actualMonitorPID': os.getpid(),
            'monitorSourceSHA256': sha(__file__), 'originalScope': scope, 'actualProcesses': processes,
            'before': before, 'originalStartedPath': str(life / 'started.json'), 'originalStartedSHA256': sha(life / 'started.json'),
            'originalReadyPath': str(life / 'ready-runtime.json'), 'originalReadySHA256': sha(life / 'ready-runtime.json'),
            'originalWrapperReceiptAvailableAtAttachment': (gate / 'receipt.json').exists(),
            'originalLifecycleTerminalAvailableAtAttachment': (life / 'terminal.json').exists(),
            'originalWrapperExitCode': None, 'originalLifecycleExitCode': None,
            'limitations': ['Attached late to the original still-live canonical command; startup observer in the lost wrapper is not reconstructed.',
                            'Original wrapper/lifecycle receipts remain missing. This new monitor records only its own actual observations and kernel terminal status.',
                            'Initial clean candidate and ready runtime are original persisted launch records; complete source/executable census is measured at late attachment and terminal.',
                            'No product code, test, golden, scope flag, browser or native service is restarted/changed. Cause of supervisor termination is unknown.']}
(out / 'attachment.json').write_text(json.dumps(attached, indent=2) + '\n')
print(json.dumps({'attachedNode': node_pid, 'attachedChrome': chrome_pid, 'head': full, 'attachment': str(out / 'attachment.json')}), flush=True)
deadline = time.monotonic() + 600
while time.monotonic() < deadline:
    raw = Path('/proc', str(node_pid), 'stat').read_bytes()
    fields = raw.decode().split(') ', 1)[1].split()
    if fields[0] == 'Z':
        (out / 'actual-node-terminal.stat.raw').write_bytes(raw)
        encoded = int(fields[49])
        node_exit = os.waitstatus_to_exitcode(encoded)
        break
    time.sleep(.1)
else:
    raise TimeoutError('Surviving Node did not reach kernel zombie terminal status')
after = snapshot('attachment-after')
assert before['sources'] == after['sources'] and before['runtime'] == after['runtime']
rows = [json.loads(l[len('CDP_RESULT '):]) for l in log.read_text().splitlines() if l.startswith('CDP_RESULT ')]
golden = json.loads((root / 'geometry-web/cdp_sections.golden.json').read_text())
passed = (node_exit == 0 and len(rows) == 1 and rows[0]['completed'] is True
          and rows[0]['scope'] == scope and rows[0]['passedAssertions'] == golden['total']
          and rows[0]['failedAssertions'] == 0 and rows[0]['skipped'] == []
          and rows[0]['sections'] == golden['sections'] and rows[0]['goldenCompare'] == 'matched'
          and rows[0]['uncaughtBrowserExceptions'] == 0)
source = out / 'executed-candidate-sources'
for relative, digest in before['sources'].items():
    target = source / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((root / relative).read_bytes())
    assert sha(target) == digest
terminal = {'schema': 'geometry-surviving-canonical-full-terminal/1', 'observedUtc': now(), 'before': before, 'after': after,
            'actualNodePID': node_pid, 'actualKernelWaitStatusEncoded': encoded,
            'actualNodeExitCode': node_exit, 'exitSource': 'Field52 of actual owned Node /proc/PID/stat at observed zombie terminal; raw bytes saved, decoded by os.waitstatus_to_exitcode',
            'originalScope': scope, 'canonicalResult': rows[0] if len(rows) == 1 else None,
            'fullCanonicalAndKernelExitVerified': passed, 'monitorExitCode': 0 if passed else 1,
            'originalWrapperExitCode': None, 'originalWrapperReceiptAvailable': (gate / 'receipt.json').exists(),
            'originalLifecycleExitCode': None, 'originalLifecycleTerminalAvailable': (life / 'terminal.json').exists(),
            'attachmentPath': str(out / 'attachment.json'), 'attachmentSHA256': sha(out / 'attachment.json'),
            'rawLogPath': str(log), 'rawLogSHA256': sha(log), 'rawLogBytes': log.stat().st_size,
            'command': sys.argv, 'monitorSourceSHA256': sha(__file__), 'actualPython': str(Path('/proc/self/exe').resolve()),
            'actualPythonSHA256': sha('/proc/self/exe'), 'limitations': attached['limitations']}
(out / 'terminal.json').write_text(json.dumps(terminal, indent=2) + '\n')
print(json.dumps({'actualNodeExitCode': node_exit, 'fullCanonicalAndKernelExitVerified': passed, 'canonicalResult': terminal['canonicalResult'], 'terminal': str(out / 'terminal.json')}), flush=True)
sys.exit(terminal['monitorExitCode'])
