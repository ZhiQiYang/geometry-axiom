from pathlib import Path
import datetime, hashlib, json, os, subprocess, sys

root = Path('<workspace-path>')
gate = Path('<workspace-path>')
life = Path('<workspace-path>')
out = Path('<workspace-path>')
assert not out.exists()
out.mkdir()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True)
assert head == 'f3b8285729b42cd22451c98cba1e2ec4514517f3' and dirty == ''
log = gate / 'command.log'
rows = [json.loads(l[len('CDP_RESULT '):]) for l in log.read_text().splitlines() if l.startswith('CDP_RESULT ')]
assert len(rows) == 1
canonical = rows[0]
assert canonical['completed'] is True and canonical['goldenCompare'] == 'matched'
golden = root / 'geometry-web/cdp_sections.golden.json'
floor = json.loads(golden.read_text())
assert canonical['sections'] == floor['sections'] and canonical['passedAssertions'] == floor['total'] == 2207
assert canonical['failedAssertions'] == 0 and canonical['skipped'] == []
assert log.read_text().count('[EXPECTED EXCEPTION] Error: fb-auto-probe') == 1
assert '[UNEXPECTED EXCEPTION]' not in log.read_text()
assert not (gate / 'receipt.json').exists() and not (life / 'terminal.json').exists()
states = []
for pid, role in [(254428, 'original owned gate Python PID, observed live at launch'),
                  (254496, 'original CDP_SCOPE Chromium PID'),
                  (254488, 'candidate Node PID derived from Chromium process group/session; live executable identity was not retained'),
                  (254424, 'original owned service PID'), (254425, 'original owned bridge PID')]:
    file = Path('/proc', str(pid), 'stat')
    if file.exists():
        raw = file.read_bytes()
        (out / ('proc-' + str(pid) + '.stat.raw')).write_bytes(raw)
        fields = raw.decode().split(') ', 1)[1].split()
        states.append({'pid': pid, 'role': role, 'state': fields[0], 'pgid': int(fields[2]), 'session': int(fields[3]),
                       'terminalWaitStatusEncoded': int(fields[49]) if fields[0] == 'Z' else None,
                       'terminalWaitStatusDecoded': os.waitstatus_to_exitcode(int(fields[49])) if fields[0] == 'Z' else None,
                       'statSHA256': sha(file), 'originalLiveExecutableIdentityRetained': False})
    else:
        states.append({'pid': pid, 'role': role, 'state': 'absent-at-observation', 'originalLiveExecutableIdentityRetained': False})
record = {'schema': 'geometry-root-unreceipted-complete-full-observation/1',
          'observedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'observedCurrentFullSHA': head, 'dirtyObserved': dirty,
          'originalPersistedExpectedSHA': json.loads((life / 'started.json').read_text())['expectedFullSHA'],
          'originalRawCanonicalResult': canonical,
          'canonicalMatchesCurrentFrozenGolden': True, 'currentGoldenSHA256': sha(golden),
          'originalProductNodeExitCode': None, 'originalProductNodeExitStatus': 'unknown; original wrapper receipt and live actor observer were lost',
          'originalWrapperExitCode': None, 'originalLifecycleExitCode': None,
          'originalWrapperReceiptAvailable': False, 'originalLifecycleTerminalAvailable': False,
          'originalLiveActualNodeExecutableSHA256': None, 'originalLiveActualChromeExecutableSHA256': None,
          'executionIdentityFullyVerified': False,
          'supervisorCause': 'unknown; original gate PID kernel stat shows signal9, which does not establish OOM or a product failure',
          'failedLateAttachmentActualExitCode': 1,
          'failedLateAttachmentSource': '<workspace-path>',
          'failedLateAttachmentSourceSHA256': sha('<workspace-path>'),
          'failedLateAttachmentReason': 'ROOT actual tool exit1 FileNotFoundError /proc/254496/exe; browser already zombie. No attachment.json or live executable attestation was written.',
          'processObservations': states,
          'expectedBrowserException': 'Original P38 declared auto-report injection fb-auto-probe; the raw contains exactly one EXPECTED and zero UNEXPECTED exception records.',
          'ownedServiceStopReceipt': '<workspace-path>',
          'ownedServiceStopReceiptSHA256': sha('<workspace-path>'),
          'nextStep': 'Purposeful same-frozen-candidate full rerun under detached durable owned supervisor to retain actual live Node/browser identity and complete original wrapper receipts. No source, assertion, floor or golden changes.',
          'command': sys.argv, 'scriptSHA256': sha(__file__), 'actualPython': str(Path('/proc/self/exe').resolve()),
          'actualPythonSHA256': sha('/proc/self/exe'), 'observationExitCode': 0,
          'rawFiles': [{'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in [log, life / 'started.json', life / 'ready-runtime.json', life / 'gate.stdout.raw.log', life / 'gate.stderr.raw.log', life / 'service.stdout.raw.log', life / 'service.stderr.raw.log']],
          'limitations': ['This new post-completion observation never fabricates an original receipt or startup executable identity.',
                          'Canonical2207/0/0 completed/golden-matched is preserved, but cannot replace missing actual execution identity and original wrapper exit.',
                          'Current PID/kernel observations are dated now; candidate Node binding is explicitly inferred, not a live executable attestation.']}
(out / 'observation.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'observation': str(out / 'observation.json'), 'sha256': sha(out / 'observation.json'), 'fullExecutionIdentityVerified': False}))
