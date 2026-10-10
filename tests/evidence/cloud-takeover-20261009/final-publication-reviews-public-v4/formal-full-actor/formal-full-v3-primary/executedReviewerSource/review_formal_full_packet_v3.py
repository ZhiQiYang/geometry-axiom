"""Read-only independent formal FULL public packet integrity and inverse review.

Concrete machine path tokens only are projected. Generic detector prefixes,
punctuation, Chinese, numbers, Boolean values, and key/value associations stay.
This reviewer never executes a published source or any product/browser/service.
"""
import ast
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sys

B = Path('<workspace-path>')
P = B / 'f3b-durable-full-public-v3'
S = Path('<workspace-path>')
G = S / 'geometry-root-f3b82857-durable-full-cdp-gate'
L = S / 'geometry-root-f3b82857-durable-full-cdp-lifecycle'
D = S / 'geometry-root-f3b82857-durable-full-cdp-detached-launch'
K = S / 'geometry-ui-verification/f3b-durable-full-launch-kernel-review-v2'
OUT = Path(sys.argv[1])
HEAD = 'f3b8285729b42cd22451c98cba1e2ec4514517f3'
M = 'f33d0032d3bfd33cec02f9790a90104892e8a4bbd8803b8349105544571c7b93'
checks, findings, inputs, original_by_hash = [], [], {}, {}
TOKEN = re.compile(r'(?:/workspace/|/tmp/geometry-|/opt/codex/)[A-Za-z0-9._~%+@:=/\-]+')

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def read(path):
    path = Path(path)
    raw = path.read_bytes()
    inputs[str(path)] = {'bytes': len(raw), 'sha256': sha(raw)}
    return raw

def check(ok, name, detail=None):
    checks.append({'name': name, 'passed': bool(ok)})
    if not ok:
        findings.append({'name': name, 'detail': detail})

def pairs(values):
    result = {}
    for k, v in values:
        if k in result:
            raise ValueError('duplicate JSON key: ' + k)
        result[k] = v
    return result

def load(raw):
    return json.loads(raw, object_pairs_hook=pairs)

def project(text):
    def replace(m):
        t = m.group()
        return '<workspace-path>' if t.startswith('/workspace/') else '<execution-runtime-path>' if t.startswith('/opt/') else '<isolated-test-directory>'
    return TOKEN.sub(replace, text)

def tree(a, b, where):
    check(type(a) is type(b), 'JSON original/public exact type ' + where)
    if type(a) is not type(b):
        return
    if isinstance(a, dict):
        labels = [project(k) for k in a]
        repeated = {k for k in labels if labels.count(k) > 1}
        mapped = {}
        for k in a:
            label = project(k)
            if label in repeated:
                label += '|basename=' + Path(k).name + '|originalKeySha256=' + sha(k.encode())
            check(label not in mapped, 'JSON injective keys ' + where)
            mapped[label] = k
        check(set(mapped) == set(b), 'JSON all original keys retained ' + where)
        for label, k in mapped.items():
            if label in b:
                tree(a[k], b[label], where + '/' + label)
    elif isinstance(a, list):
        check(len(a) == len(b), 'JSON original list cardinality ' + where)
        for i, (x, y) in enumerate(zip(a, b)):
            tree(x, y, where + '/' + str(i))
    elif isinstance(a, str):
        check(project(a) == b, 'JSON all non-token string characters retained ' + where, None if project(a) == b else {'original': a, 'public': b})
    else:
        check(a == b, 'JSON original scalar association ' + where)

def collect(path):
    path = Path(path)
    items = sorted(x for x in path.rglob('*') if x.is_file()) if path.is_dir() else [path]
    for x in items:
        raw = read(x)
        original_by_hash.setdefault(sha(raw), (x, raw))

def ref(item):
    dest = P / item['path']
    pub = read(dest)
    identity = item['originalSha256']
    check(sha(pub) == item['sha256'] and len(pub) == item['bytes'], 'public ref byte identity ' + item['path'])
    check(identity in original_by_hash, 'retained original hash found ' + item['path'])
    if identity not in original_by_hash:
        return
    source, raw = original_by_hash[identity]
    check(len(raw) == item['originalBytes'], 'retained original size ' + item['path'])
    if item['byteIdenticalOriginal']:
        check(raw == pub and item['publicProjection'] is False, 'exact original bytes ' + item['path'])
    else:
        check(item['publicProjection'] is True, 'path projection declared ' + item['path'])
        if dest.suffix == '.json':
            tree(load(raw), load(pub), item['path'])
        else:
            check(project(raw.decode()) == pub.decode(), 'all non-token code/prose/log bytes preserved ' + item['path'])
    if dest.suffix == '.py':
        ast.parse(pub.decode())
        check(True, 'published Python parses but was not executed ' + item['path'])

def stat(raw):
    text = raw.decode().strip()
    x = text[text.rfind(') ') + 2:].split()
    return {'pid': int(text.split(' ', 1)[0]), 'state': x[0], 'pgid': int(x[2]), 'sid': int(x[3]), 'starttime': int(x[19]), 'wait': int(x[49])}

started = datetime.datetime.now(datetime.timezone.utc).isoformat()
OUT.mkdir(parents=True, exist_ok=False)
manifest = load(read(P / 'manifest.json'))
check(sha(read(P / 'manifest.json')) == M, 'exact FINAL-READY formal FULL manifest')
names = [x['path'] for x in manifest['publicFiles']]
check(len(names) == len(set(names)) == 193, 'exact193 unique manifest entries')
actual = {x.relative_to(P).as_posix() for x in P.rglob('*') if x.is_file()}
check(actual == set(names) | {'manifest.json'}, 'exact194 total files no undeclared files')
check(sum(x.stat().st_size for x in P.rglob('*') if x.is_file()) == 7697431, 'exact packet census7697431 bytes')
check(not any(x.is_symlink() for x in P.rglob('*')), 'no packet symlinks')
for item in manifest['publicFiles']:
    raw = read(P / item['path'])
    check(len(raw) == item['bytes'] and sha(raw) == item['sha256'], 'manifest exact hash and size ' + item['path'])
    if Path(item['path']).suffix == '.json':
        load(raw)

config = load(read(B / 'f3b-durable-full-config-v2.json'))
extras = load(read(B / 'f3b-durable-full-extra-v2.json'))
check(len(config) == 1 and config[0]['head'] == HEAD, 'only one formal original FULL execution')
for cfg in config:
    collect(cfg['receipt'])
    for path in cfg['logs'] + cfg['artifacts']:
        collect(path)
for item in extras:
    collect(item['path'])
collect(B / 'f3b-durable-full-source-reference-v3')
for item in manifest['historyReviewsAndExecutorSources']:
    ref(item)
for scope in manifest['rounds']:
    for item in scope['rawEvidence']:
        ref(item)
    receipt = load(read(P / scope['receiptPath']))
    check(set(receipt) == set(load(read(G / 'receipt.json'))) | {'publicProjection'}, 'public receipt adds only explicit projection provenance')
    note = receipt.pop('publicProjection')
    check(note['originalSha256'] == scope['originalReceiptSha256'] == sha(read(G / 'receipt.json')) and note['originalBytes'] == len(read(G / 'receipt.json')), 'public receipt exact original annotation')
    tree(load(read(G / 'receipt.json')), receipt, scope['receiptPath'])

gate = load(read(G / 'receipt.json'))
terminal = load(read(L / 'terminal.json'))
stop = load(read(L / 'owned-stop/terminal-receipt.json'))
launch = load(read(D / 'launch.json'))
kernel = load(read(K / 'receipt.json'))
formal = manifest['formalFullResult']
raw_log = read(G / 'command.log')
lines = raw_log.decode().splitlines()
results = [load(x[len('CDP_RESULT '):]) for x in lines if x.startswith('CDP_RESULT ')]
check(len(results) == 1, 'exactly one original terminal CDP_RESULT')
canonical = results[0]
check(canonical == gate['evidence']['canonicalResult'], 'canonical raw result exact original receipt')
tree(canonical, load(read(P / 'rounds/f3b-durable-original-full-cdp-completed/canonical-original-result.public.json')), 'canonical public result')
check(canonical['completed'] is True and canonical['passedAssertions'] == 2207 and canonical['failedAssertions'] == 0 and canonical['skipped'] == [], 'one original completed2207/0/0 execution')
check(canonical['scope']['mode'] == 'full' and canonical['scope']['filters'] == canonical['scope']['modifiers'] == [], 'original full unfiltered scope no modifiers')
check(canonical['goldenCompare'] == 'matched' and len(canonical['sections']) == 84 and formal['originalGoldenSectionsMatched'] == 84, 'actual original golden84matched')
check(canonical['uncaughtBrowserExceptions'] == 1 and len([x for x in lines if 'EXPECTED EXCEPTION' in x and 'fb-auto-probe' in x]) == 1 and not any('UNEXPECTED EXCEPTION' in x for x in lines), 'original intentional P38 expected fb-auto-probe1 zero unexpected')
check(gate['executionVerified'] is True and gate['problems'] == [] and gate['evidence']['completionVerified'] is True, 'original execution identity and completion verified')
check(gate['command'] == ['node', 'geometry-web/cdp_test.js'] and gate['removedScopeEnvironment'] == {}, 'unchanged canonical Node command no scope environment override')
check(gate['execution']['exitCode'] == gate['gateExitCode'] == terminal['actualGateExitCode'] == stop['exitCode'] == 0 and not gate['execution']['timedOut'] and not gate['execution']['interrupted'], 'actual Node gate stop0 separate no interruption')
check(terminal['actualServiceExitAfterStop'] == -15 and terminal['serviceExitBeforeStop'] is None, 'owned serviceSIGTERM−15 separate from stop0')
check(formal['originalReceiptSHA256'] == sha(read(G / 'receipt.json')) and formal['rawLogOriginalSHA256'] == sha(raw_log) and formal['ownedTerminalOriginalSHA256'] == sha(read(L / 'terminal.json')), 'formal original receipt raw lifecycle full hashes')
check(formal['firstUnreceiptedRawRunReused'] is False and formal['testedSHA'] == HEAD and manifest['releaseApproved'] is False, 'earlier noReceipt remains separate and release unapproved')
for side in ['before', 'after']:
    snap = gate[side]
    check(snap['git']['head'] == HEAD and snap['git']['status'] == '' and snap['runtime']['fresh'] is True and snap['problems'] == [], 'actual frozen clean healthy runtime ' + side)
check(gate['before']['sourceSha256'] == gate['after']['sourceSha256'] and len(gate['before']['sourceSha256']) == 125, 'actual125 captured beforeafter sources identical')
for key in ['native', 'executables', 'liveBridge', 'runnerSha256', 'identityObserverSha256', 'launchAdapterSha256']:
    check(gate['before'][key] == gate['after'][key], 'actual beforeafter identity unchanged ' + key)
live = gate['executionIdentity']['liveBinding']
check(gate['executionIdentity']['errors'] == [] and live['cdpScope'] == canonical['scope'], 'actual live binding exact original CDP_SCOPE')
processes = live['processes']
check(len(processes) == 2 and {x['pid'] for x in processes} == {284641, 284692}, 'actual bound Node and Chromium PIDs')
for proc in processes:
    check(proc['executableMagicHex'] == '7f454c46', 'actual actor executable ELF magic ' + str(proc['pid']))
    check('--no-sandbox' not in proc['cmdline'] and '--disable-setuid-sandbox' not in proc['cmdline'], 'actual actor sandbox flags retained ' + str(proc['pid']))
    check(len(proc['sha256']) == 64, 'actual executable SHA256 present ' + str(proc['pid']))
check(launch['productGateExitCodeAtLaunch'] is None and launch['productCompletionAtLaunch'] == 'pending' and launch['launchExitCode'] == 0, 'original detached launch remains launchonly0 with null pending product exit')
oldstat = stat(read(D / 'launched-controller.stat.raw'))
newstat = stat(read(K / 'controller.terminal.stat.raw'))
check(oldstat['pid'] == oldstat['pgid'] == oldstat['sid'] == newstat['pid'] == newstat['pgid'] == newstat['sid'] == launch['actualControllerPID'] == 284534 and oldstat['starttime'] == newstat['starttime'], 'dated terminal kernel belongs to original PIDstarttime PGID SID')
check(newstat['state'] == 'Z' and newstat['wait'] == 0 and kernel['actualControllerTerminalObservation']['actualControllerExitCode'] == 0 and manifest['ownedLifecycleOutcome']['actualControllerExitCode'] == 0, 'actual controller kernel0 explicit zombie not absent')
check(manifest['ownedLifecycleOutcome']['originalWrapperSnapshotDirectoryAvailable'] is False, 'original absent executor snapshot directory limit preserved')
for observed in stop['processObservations']:
    if observed['exists']:
        raw = read(L / 'owned-stop' / ('proc-' + str(observed['pid']) + '.stat.raw'))
        check(sha(raw) == observed['statSHA256'] and stat(raw)['state'] == observed['state'] == 'Z', 'stop actual dated Z exists ' + str(observed['pid']))
    else:
        check(observed['pid'] == 284641 and observed['state'] == 'absent-at-observation', 'stop actual Node absent at observation')
check(stop['portObservation']['accepting'] is False, 'actual owned port refused after stop')
for item in terminal['rawFiles']:
    raw = read(L / item['path'])
    check(sha(raw) == item['sha256'] and len(raw) == item['bytes'], 'original lifecycle raw source binding ' + item['path'])
for path, identity in kernel['sourceHashes'].items():
    check(sha(read(path)) == identity, 'independent kernel proof actual source/input binding ' + Path(path).name)
check(sha(read(K / 'review.raw.log')) == kernel['rawReviewLogSHA256'] and kernel['exitCode'] == 0 and kernel['productTestsExecuted'] is False, 'independent kernel review metadata-only actual0/raw')
build = load(read(B / 'f3b-durable-full-package-build-v2.json'))
check(build['actualExitCode'] == 0 and build['productExecuted'] is False and load(build['stdout'])['manifestSha256'] == manifest['supersededScratchV2ManifestSHA256'], 'actual inherited adapter subprocess0 older packet bound')
impl = manifest['publicationImplementation']
source_roles = [('prepare_formal_f3_durable_full_packet_v2.py', 'actualBuilderSHA256'), ('prepare_ui_history_packet_v8.py', 'projectionEngineOriginalSHA256'), ('finalize_formal_f3_full_source_closure_v3.py', 'actualFinalSourceClosureReviserSHA256'), ('f3b-durable-full-adapter-v2.py', 'finalProjectionAdapterOriginalSHA256')]
for filename, field in source_roles:
    check(sha(read(B / filename)) == impl[field], 'publication implementation exact original source role ' + field)
for filename, field in [('f3b-durable-full-config-v2.json', 'inheritedConfigSHA256'), ('f3b-durable-full-extra-v2.json', 'inheritedExtrasSHA256'), ('f3b-durable-full-metadata-v2.json', 'inheritedMetadataSHA256')]:
    check(sha(read(B / filename)) == impl[field], 'publication exact inherited input closure ' + field)
check('publisher.p.private = lambda text: bool(publisher._BOUNDED_MACHINE_PATH.search(text))' in read(B / 'f3b-durable-full-adapter-v2.py').decode(), 'adapter classifies actual concrete tokens without consuming generic regex prefixes')
for path, identity in list(inputs.items()):
    raw = Path(path).read_bytes()
    check(len(raw) == identity['bytes'] and sha(raw) == identity['sha256'], 'all read original/public inputs unchanged after review ' + path)
failed = len(findings)
report = {'schema': 'geometry-independent-formal-full-public-packet-review/1', 'actor': '/root/publication_final_review', 'startedUTC': started, 'finishedUTC': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'actualCommand': [sys.executable, '-B', str(Path(__file__).resolve()), str(OUT)], 'actualPython': os.readlink('/proc/self/exe'), 'actualPythonSHA256': sha(Path('/proc/self/exe').read_bytes()), 'actualPID': os.getpid(), 'actualCmdlineHex': Path('/proc/self/cmdline').read_bytes().hex(), 'reviewerSourceSHA256': sha(Path(__file__).read_bytes()), 'manifestSHA256': M, 'passedMetadataChecks': len(checks) - failed, 'failedMetadataChecks': failed, 'finalPacketAccepted': failed == 0, 'computedReviewerExitCode': 1 if failed else 0, 'productTestsExecuted': False, 'checks': checks, 'findings': findings, 'inputs': inputs, 'limits': ['Metadata checks never add to product2207; no product/browser/service/native/CLI/GH/API execution.', 'Original actor125capture versus exact frozen Git7Python/vendor/golden/sixfixture references are distinct; sibling sourcepin review binds them.', 'Fresh v3 finalizer command return is author tool-reported unless an original execution receipt is independently retained; no original PID/exe/closure was invented.', 'Original old unreceipted raw full actor/exits stay unknown; new formal evidence does not backfill it.', 'Original launch null pending is retained; later PID/starttime-bound zombie kernel0 is dated separate evidence.']}
(OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ['manifestSHA256', 'passedMetadataChecks', 'failedMetadataChecks', 'finalPacketAccepted', 'computedReviewerExitCode']}))
for finding in findings:
    print(json.dumps(finding, ensure_ascii=False))
sys.exit(1 if failed else 0)
