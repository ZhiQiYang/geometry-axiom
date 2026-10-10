"""Independent read-only review of the qualified, unreceipted first f3b full.

Only this review's fresh scratch report is written. No producer import,
browser/native/server/GitHub invocation, or evidence repair is performed.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile

B = Path('<workspace-path>')
P = B / 'f3b-unreceipted-full-public-v1'
OUT = Path(sys.argv[1])
ROOT = Path('<workspace-path>')
HEAD = 'f3b8285729b42cd22451c98cba1e2ec4514517f3'
EXPECTED_MANIFEST = '5279b00e7b2425e582af5c8ce62cea2675eb7f54aeffa85e86a40049ee7b5ea8'
checks = []
findings = []
protected = {}
token_counts = {}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    path = Path(path)
    raw = path.read_bytes()
    protected[str(path)] = (len(raw), sha(raw))
    return raw


def check(condition, name, detail=None):
    checks.append({'name': name, 'passed': bool(condition)})
    if not condition:
        findings.append({'name': name, 'detail': detail})


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('duplicate JSON key: ' + key)
        result[key] = value
    return result


def load(raw):
    return json.loads(raw, object_pairs_hook=pairs)


TOKEN = re.compile(r'/workspace/[A-Za-z0-9._~%+@:=/\-]+|/tmp/geometry-[A-Za-z0-9._~%+@:=/\-]+|/opt/codex/[A-Za-z0-9._~%+@:=/\-]+')


def project_string(text):
    matches = list(TOKEN.finditer(text))
    parts = []
    previous = 0
    for match in matches:
        parts.append(text[previous:match.start()])
        token = match.group()
        label = '<workspace-path>' if token.startswith('/workspace/') else '<isolated-test-directory>' if token.startswith('/tmp/') else '<execution-runtime-path>'
        parts.append(label)
        previous = match.end()
    parts.append(text[previous:])
    return ''.join(parts)


def compare_tree(original, public, at):
    check(type(original) is type(public), 'JSON type preserved ' + at)
    if type(original) is not type(public):
        return
    if isinstance(original, dict):
        labels = [project_string(key) for key in original]
        duplicates = {key for key in labels if labels.count(key) > 1}
        mapping = {}
        for key in original:
            label = project_string(key)
            if label in duplicates:
                label += '|basename=' + Path(key).name + '|originalKeySha256=' + sha(key.encode())
            check(label not in mapping, 'injective original key binding ' + at)
            mapping[label] = key
        check(set(mapping) == set(public), 'JSON exact key census ' + at)
        for label, key in mapping.items():
            if label in public:
                compare_tree(original[key], public[label], at + '/' + label)
    elif isinstance(original, list):
        check(len(original) == len(public), 'JSON exact list census ' + at)
        for i, (a, b) in enumerate(zip(original, public)):
            compare_tree(a, b, at + '/' + str(i))
    elif isinstance(original, str):
        check(project_string(original) == public, 'JSON all non-path string bytes preserved ' + at)
    else:
        check(original == public, 'JSON scalar preserved ' + at)


def procstat(raw):
    text = raw.decode()
    after = text[text.rfind(')') + 2:].split()
    return {'state': after[0], 'pgid': int(after[2]), 'session': int(after[3]), 'wait': int(after[49])}


started = datetime.datetime.now(datetime.timezone.utc).isoformat()
OUT.mkdir(parents=True, exist_ok=False)
manifest_raw = read(P / 'manifest.json')
manifest = load(manifest_raw)
check(sha(manifest_raw) == EXPECTED_MANIFEST, 'exact final-ready manifest SHA')
public = manifest['publicFiles']
public_paths = [item['path'] for item in public]
check(len(set(public_paths)) == len(public_paths) == 45, 'exact unique45 listed public files')
actual_paths = {item.relative_to(P).as_posix() for item in P.rglob('*') if item.is_file()}
check(actual_paths == set(public_paths) | {'manifest.json'}, 'exact46 total file census')
check(not any(item.is_symlink() for item in P.rglob('*')), 'no evidence symlinks')
for item in public:
    name = item['path']
    check(not Path(name).is_absolute() and '..' not in Path(name).parts, 'safe public path ' + name)
    raw = read(P / name)
    check(len(raw) == item['bytes'] and sha(raw) == item['sha256'], 'public bytes/hash ' + name)
    if Path(name).suffix == '.json':
        load(raw)
    elif Path(name).suffix == '.gcanvas':
        with zipfile.ZipFile(P / name) as archive:
            check(len(set(archive.namelist())) == len(archive.namelist()), 'archive unique entries ' + name)
            check(all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in archive.namelist()), 'archive safe paths ' + name)
            check(archive.testzip() is None, 'archive CRC ' + name)

extras = load(read(B / 'f3b-unreceipted-full-extra-v1.json'))
origin = {}
for item in extras:
    source = Path(item['path'])
    destination = item['destination']
    if source.is_dir():
        for child in source.rglob('*'):
            if child.is_file():
                origin[destination + '/' + child.relative_to(source).as_posix()] = child
    else:
        origin[destination] = source

refs = manifest['historyReviewsAndExecutorSources']
check(len(refs) == 44 and len({item['path'] for item in refs}) == 44, 'exact44 original source/artifact refs')
check(set(public_paths) == {'README.md'} | {item['path'] for item in refs}, 'all non-authored public files have source refs')
for item in refs:
    name = item['path']
    check(name in origin, 'original origin available ' + name)
    if name not in origin:
        continue
    raw = read(origin[name])
    copied = read(P / name)
    check(sha(raw) == item['originalSha256'] and len(raw) == item['originalBytes'], 'original bytes/hash ' + name)
    check(sha(copied) == item['sha256'] and len(copied) == item['bytes'], 'reference public bytes/hash ' + name)
    if item.get('byteIdenticalOriginal'):
        check(raw == copied and not item.get('publicProjection'), 'exact original/public bytes ' + name)
    else:
        check(bool(item.get('publicProjection')), 'changed bytes projection declared ' + name)
        if Path(name).suffix == '.json':
            compare_tree(load(raw), load(copied), name)
        else:
            before = raw.decode('utf-8')
            after = copied.decode('utf-8')
            check(project_string(before) == after, 'all non-token code/prose/log bytes preserved ' + name)
            token_counts[name] = len(list(TOKEN.finditer(before)))

gate = Path('<workspace-path>')
life = Path('<workspace-path>')
observation_dir = Path('<workspace-path>')
stop_dir = Path('<workspace-path>')
raw_log = read(gate / 'command.log')
lines = raw_log.decode().splitlines()
results = [load(line[len('CDP_RESULT '):]) for line in lines if line.startswith('CDP_RESULT ')]
check(len(results) == 1, 'unique original canonical CDP_RESULT')
result = results[0]
check(result['completed'] is True and result['passedAssertions'] == 2207 and result['failedAssertions'] == 0 and result['skipped'] == [], 'original raw2207/0/0 completed')
check(result['scope']['mode'] == 'full' and result['scope']['filters'] == [] and result['scope']['modifiers'] == [], 'original full mode unfiltered unmodified')
golden = load(read(B / 'f3b-unreceipted-full-original-candidate-reference-v1/geometry-web/cdp_sections.golden.json'))
check(result['sections'] == golden['sections'] and len(result['sections']) == 84 and sum(result['sections'].values()) == 2207, 'raw84 sections exact frozen golden')
check(result['goldenCompare'] == 'matched', 'raw original goldenCompare matched')
check(len([line for line in lines if '[EXPECTED EXCEPTION]' in line]) == 1 and len([line for line in lines if '[UNEXPECTED EXCEPTION]' in line]) == 0 and result['uncaughtBrowserExceptions'] == 1, 'one original EXPECTED and zero UNEXPECTED exception')
check(any('[EXPECTED EXCEPTION]' in line and 'fb-auto-probe' in line for line in lines), 'EXPECTED exception is original fb-auto-probe')
cdp_source = read(B / 'f3b-unreceipted-full-original-candidate-reference-v1/geometry-web/cdp_test.js').decode()
check("throw new Error('fb-auto-probe')" in cdp_source, 'existing source declares expected injection')

started_record = load(read(life / 'started.json'))
observation = load(read(observation_dir / 'observation.json'))
stop = load(read(stop_dir / 'terminal-receipt.json'))
check(started_record['expectedFullSHA'] == HEAD and started_record['dirtyBefore'] == '', 'original persisted expected clean candidate')
check(observation['observedCurrentFullSHA'] == HEAD and observation['dirtyObserved'] == '', 'later dated clean candidate observation separately identified')
check(not (gate / 'receipt.json').exists() and not (life / 'terminal.json').exists(), 'missing original receipts not manufactured')
history = manifest['rawExecutionHistory']
for key in ['originalActualNodeExitCode', 'originalActualWrapperExitCode', 'originalActualLifecycleExitCode', 'originalLiveActualNodeExecutableSHA256', 'originalLiveActualChromeExecutableSHA256']:
    check(history[key] is None, 'unreceived original identity/exit remains unknown ' + key)
check(history['originalWrapperReceiptAvailable'] is False and history['originalLifecycleTerminalAvailable'] is False and history['formalExecutionIdentityAcceptance'] is False, 'raw completion not formal execution identity acceptance')
check(observation['originalProductNodeExitCode'] is None and observation['originalWrapperExitCode'] is None and observation['originalLifecycleExitCode'] is None and observation['executionIdentityFullyVerified'] is False, 'observation does not reconstruct original actor exits')
compare_tree(result, history['originalCanonicalResult'], 'manifest canonical raw')
compare_tree(result, load(read(P / 'canonical-original-raw-extraction.public.json')), 'public canonical extraction')
check(sha(raw_log) == history['originalRawLogSHA256'] and len(raw_log) == history['originalRawLogBytes'], 'raw log declared original exact identity')
check(sha(read(observation_dir / 'observation.json')) == history['postObservationOriginalSHA256'], 'new observation declared exact identity')
check(history['failedLateAttachmentActualToolExit'] == 1 and history['failedLateAttachmentProducedReceipt'] is False, 'failed late attachment separately retained without manufactured receipt')
check(not (Path('<workspace-path>') / 'attachment.json').exists(), 'failed attachment output remains absent')
check(stop['exitCode'] == history['separateOwnedStopExit'] == 0 and stop['productTestExecution'] is False, 'separate stop0 no product execution')
check([item['state'] for item in stop['processObservations']] == history['immediateOwnedStopStates'] == ['R', 'R'], 'immediate actual stop two R remain R')
check(stop['portObservation']['accepting'] is False and stop['receiptSources'] == [], 'owned stop no missing gate receipt synthesized and port refused')
for item in stop['processObservations']:
    raw = read(stop_dir / ('proc-' + str(item['pid']) + '.stat.raw'))
    check(sha(raw) == item['statSHA256'] and procstat(raw)['state'] == item['state'], 'immediate stop original stat binding ' + str(item['pid']))
for item in observation['processObservations']:
    raw = read(observation_dir / ('proc-' + str(item['pid']) + '.stat.raw'))
    fields = procstat(raw)
    check(sha(raw) == item['statSHA256'] and fields['state'] == item['state'] == 'Z' and fields['pgid'] == item['pgid'] and fields['session'] == item['session'] and fields['wait'] == item['terminalWaitStatusEncoded'], 'dated later proc/kernel exact binding ' + str(item['pid']))
    check(item['originalLiveExecutableIdentityRetained'] is False, 'kernel evidence never live executable evidence ' + str(item['pid']))
check('does not establish OOM' in observation['supervisorCause'], 'SIG9 cause explicitly unknown')
check([item for item in observation['processObservations'] if item['pid'] == 254428][0]['terminalWaitStatusEncoded'] == 9, 'original wrapper inferred kernelSIG9 preserved')
check('candidate Node' in [item for item in observation['processObservations'] if item['pid'] == 254488][0]['role'], 'Node PID binding explicitly inferred')

for item in observation['rawFiles']:
    original = Path(item['path'])
    raw = read(original)
    check(len(raw) == item['bytes'] and sha(raw) == item['sha256'], 'observation original raw binding ' + original.name)
for item in stop['rawFiles']:
    raw = read(stop_dir / item['path'])
    check(len(raw) == item['bytes'] and sha(raw) == item['sha256'], 'stop original raw binding ' + item['path'])

sources = {
    'controllerSHA256': Path('<workspace-path>'),
    'runnerSHA256': Path('<workspace-path>'),
    'launchSHA256': Path('<workspace-path>'),
}
for key, path in sources.items():
    check(sha(read(path)) == started_record[key], 'configured original source identity ' + key)
check(sha(read('<workspace-path>')) == stop['wrapperSHA256'], 'actually executed stop wrapper source identity')
check(sha(read('<workspace-path>')) == stop['helperSHA256'], 'actually executed stop inner helper source identity')
check(sha(read('<workspace-path>')) == observation['scriptSHA256'], 'actually executed new observation sealer source identity')
check(sha(read('<workspace-path>')) == observation['failedLateAttachmentSourceSHA256'], 'failed late attachment source identity')
for item in manifest['candidateReferenceSources']:
    command = ['git', '-C', str(ROOT), 'show', HEAD + ':' + item['repositoryPath']]
    run = subprocess.run(command, capture_output=True)
    check(run.returncode == 0 and sha(run.stdout) == item['originalSHA256'] and len(run.stdout) == item['bytes'], 'exact frozen Git candidate source reference ' + item['repositoryPath'])
    check(item['head'] == HEAD and item['actualLostCaptureRestored'] is False, 'candidate references never restored live capture ' + item['repositoryPath'])
check(manifest['historicalFullCdp']['testedHead'] == '5174a8dafd8c48329d7166abbd3d104e3c28c0c4' and manifest['historicalFullCdp']['rebound'] is False, 'historical full remains5174 never9029')
check(manifest['windows173']['pass'] == 1692 and manifest['windows173']['fail'] == 2 and manifest['windows173']['exitCode'] == 1 and manifest['windows173']['completed'] is False and manifest['windows173']['cloudOriginalsReceived'] is False and manifest['windows173']['partialsAggregated'] is False, 'Windows original incomplete1692/2 unreceived nonaggregated')
check(manifest['releaseApproved'] is False and manifest['rounds'] == [], 'qualified history not formal product receipt or release approval')

for name, binding in list(protected.items()):
    current = Path(name).read_bytes()
    check((len(current), sha(current)) == binding, 'original/public input unchanged after read-only review ' + name)

actual_exe = Path('/proc/self/exe').resolve()
exit_code = 0 if not findings else 1
report = {
    'schema': 'geometry-independent-qualified-unreceipted-full-review/1',
    'reviewerActor': '/root/publication_final_review',
    'startedUtc': started,
    'finishedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'manifestSHA256': sha(manifest_raw),
    'testedProductFullSHA': HEAD,
    'reviewCommand': [sys.executable, '-B', str(Path(__file__)), str(OUT)],
    'reviewSourceSHA256': sha(Path(__file__).read_bytes()),
    'actualReviewerPID': os.getpid(),
    'actualPython': str(actual_exe),
    'actualPythonSHA256': sha(actual_exe.read_bytes()),
    'actualProcessCmdline': Path('/proc/self/cmdline').read_bytes().split(b'\0')[:-1],
    'reviewDecisionExitCode': exit_code,
    'metadataChecksPassed': sum(item['passed'] for item in checks),
    'metadataChecksFailed': len(findings),
    'checksAreProductAssertions': False,
    'findings': findings,
    'checks': checks,
    'projectionTokenCounts': token_counts,
    'protectedInputBindings': [{'path': name, 'bytes': binding[0], 'sha256': binding[1]} for name, binding in protected.items()],
    'scope': 'Exact public45+manifest46, original source/projection byte closure, qualified raw completion/unknown original actor exits, dated kernel/stop observations, no original receipts recreated.',
    'browserExecuted': False,
    'serviceStartedOrStopped': False,
    'productOrRepositoryWritten': False,
    'githubOrNetworkUsed': False,
}
report['actualProcessCmdline'] = [item.decode() for item in report['actualProcessCmdline']]
output = OUT / 'report.json'
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'report': str(output), 'reportSHA256': sha(output.read_bytes()), 'manifestSHA256': sha(manifest_raw), 'metadataChecksPassed': report['metadataChecksPassed'], 'metadataChecksFailed': len(findings), 'reviewDecisionExitCode': exit_code, 'findings': findings}, ensure_ascii=False))
sys.exit(exit_code)
