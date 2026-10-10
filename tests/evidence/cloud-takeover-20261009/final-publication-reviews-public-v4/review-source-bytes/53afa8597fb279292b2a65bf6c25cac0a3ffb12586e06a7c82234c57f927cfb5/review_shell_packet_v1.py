"""Independent read-only shell red/green packet and execution closure review."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

B = Path('<workspace-path>')
P = B / 'f3b-shell-return-scopes-public-v1'
ROOT = Path('<workspace-path>')
OUT = Path(sys.argv[1])
HEAD = 'f3b8285729b42cd22451c98cba1e2ec4514517f3'
MANIFEST = '4ec51be9a583d025d2a1cc06e78f3a260a2241dc295a1985efa14f4aa9d12867'
checks = []
findings = []
protected = {}
originals = {}


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


TOKEN = re.compile(r'(?:/workspace/|/tmp/geometry-|/opt/codex/|/tmp/playwright_chromiumdev_profile-)[A-Za-z0-9._~%+@:=/\-]+')


def text_projection(text):
    def replacement(match):
        token = match.group()
        return '<workspace-path>' if token.startswith('/workspace/') else '<execution-runtime-path>' if token.startswith('/opt/') else '<isolated-test-directory>'
    return TOKEN.sub(replacement, text)


def compare_tree(original, public, at):
    check(type(original) is type(public), 'JSON exact type ' + at)
    if type(original) is not type(public):
        return
    if isinstance(original, dict):
        labels = [text_projection(key) for key in original]
        repeats = {label for label in labels if labels.count(label) > 1}
        keys = {}
        for key in original:
            label = text_projection(key)
            if label in repeats:
                label += '|basename=' + Path(key).name + '|originalKeySha256=' + sha(key.encode())
            check(label not in keys, 'JSON injective path keys ' + at)
            keys[label] = key
        check(set(keys) == set(public), 'JSON exact key census ' + at)
        for label, key in keys.items():
            if label in public:
                compare_tree(original[key], public[label], at + '/' + label)
    elif isinstance(original, list):
        check(len(original) == len(public), 'JSON exact list census ' + at)
        for i, (a, b) in enumerate(zip(original, public)):
            compare_tree(a, b, at + '/' + str(i))
    elif isinstance(original, str):
        check(text_projection(original) == public, 'JSON all non-token string bytes unchanged ' + at)
    else:
        check(original == public, 'JSON scalar association unchanged ' + at)


def collect_original(path):
    path = Path(path)
    if path.is_dir():
        for child in path.rglob('*'):
            if child.is_file():
                raw = read(child)
                originals.setdefault(sha(raw), (child, raw))
    else:
        raw = read(path)
        originals.setdefault(sha(raw), (path, raw))


def review_copy(ref):
    name = ref['path']
    copied = read(P / name)
    check(sha(copied) == ref['sha256'] and len(copied) == ref['bytes'], 'public copy exact hash/bytes ' + name)
    check(ref['originalSha256'] in originals, 'original identity retained in declared roots ' + name)
    if ref['originalSha256'] not in originals:
        return
    path, raw = originals[ref['originalSha256']]
    check(len(raw) == ref['originalBytes'], 'original exact bytes ' + name)
    if ref.get('byteIdenticalOriginal'):
        check(raw == copied and not ref.get('publicProjection'), 'copy original bytes unchanged ' + name)
    else:
        check(bool(ref.get('publicProjection')), 'copy projection explicitly declared ' + name)
        if Path(name).suffix == '.json':
            compare_tree(load(raw), load(copied), name)
        else:
            check(text_projection(raw.decode()) == copied.decode(), 'copy all non-token prose/code/log bytes unchanged ' + name)


started = datetime.datetime.now(datetime.timezone.utc).isoformat()
OUT.mkdir(parents=True, exist_ok=False)
manifest_raw = read(P / 'manifest.json')
manifest = load(manifest_raw)
check(sha(manifest_raw) == MANIFEST, 'exact final-ready shell manifest')
files = manifest['publicFiles']
names = [item['path'] for item in files]
check(len(set(names)) == len(names) == 197, 'exact197 unique public entries')
actual = {path.relative_to(P).as_posix() for path in P.rglob('*') if path.is_file()}
check(actual == set(names) | {'manifest.json'}, 'exact198 total packet files')
check(not any(path.is_symlink() for path in P.rglob('*')), 'packet has no symlinks')
for item in files:
    raw = read(P / item['path'])
    check(sha(raw) == item['sha256'] and len(raw) == item['bytes'], 'public manifest bytes/hash ' + item['path'])
    if Path(item['path']).suffix == '.json':
        load(raw)

configs = load(read(B / 'f3b-shell-return-scopes-config-v1.json'))
extras = load(read(B / 'f3b-shell-return-scopes-extra-v1.json'))
for item in configs:
    collect_original(item['receipt'])
    for path in item['logs'] + item['artifacts']:
        collect_original(path)
for item in extras:
    collect_original(item['path'])

for item in manifest['historyReviewsAndExecutorSources']:
    review_copy(item)
for scope in manifest['rounds']:
    for item in scope['rawEvidence']:
        review_copy(item)
    compare_tree(load(read(configs[[item['name'] for item in configs].index(scope['name'])]['receipt'])), load(read(P / scope['receiptPath'])), scope['receiptPath'])
for item in manifest['sourceCopies']:
    original_hash = item['originalSHA256']
    check(original_hash in originals, 'source copy original identity available ' + item['publicPath'])
    if original_hash in originals:
        _, raw = originals[original_hash]
        copied = read(P / item['publicPath'])
        check(sha(copied) == item['publicSHA256'] and len(copied) == item['publicBytes'] and len(raw) == item['originalBytes'], 'source copy original/public byte bindings ' + item['publicPath'])
        check(text_projection(raw.decode()) == copied.decode(), 'source copy all non-token bytes preserved ' + item['publicPath'])
    check(item['publishedCopyWasExecuted'] is False, 'source publication not execution ' + item['publicPath'])

expected_cases = [{'width': w, 'family': f} for w in [1400, 390] for f in ['ASM', 'SP']]
expected_names = []
for width in [1400, 390]:
    for family, entry, close in [('ASM', '#btnNewAssembly', '#asmClose'), ('SP', '#btnNewSectionProfile', '#spClose')]:
        expected_names += ['unique visible original Create entry', 'one normal physical click precondition #btnCreateObject', 'one normal physical click precondition ' + entry, str(width) + ' ' + family + ' shared original row stays normal flow', str(width) + ' ' + family + ' actual return center hits original control']
        if family == 'SP':
            expected_names += ['one normal physical click precondition #spCancel', str(width) + ' SP original Cancel preserves exact native dump']
        expected_names += ['one normal physical click precondition ' + close, str(width) + ' ' + family + ' one original trusted return gesture', str(width) + ' ' + family + ' exact native full dump unchanged', str(width) + ' ' + family + ' same original project bar returns home']

product_maps = []
for config, declared in zip(configs, manifest['boundedScopes']):
    name = config['name']
    gate_path = Path(config['receipt'])
    gate = load(read(gate_path))
    artifact_dir = Path(config['artifacts'][1])
    helper = load(read(artifact_dir / 'results.json'))
    driver = load(read(artifact_dir / 'driver-receipt.json'))
    lifecycle_dir = Path('<workspace-path>') / ('geometry-root-f3b82857-normal-shell-return' + ('-completion-v2' if name.startswith('green') else '') + '-lifecycle')
    terminal = load(read(lifecycle_dir / 'terminal.json'))
    stop = load(read(lifecycle_dir / 'owned-stop/terminal-receipt.json'))
    expected_exit = 0 if name.startswith('green') else 1
    expected_pass, expected_fail = (40, 0) if expected_exit == 0 else (16, 1)
    check(sha(read(gate_path)) == declared['originalReceiptSHA256'] and sha(read(gate_path.parent / 'command.log')) == declared['originalCommandLogSHA256'] and sha(read(lifecycle_dir / 'terminal.json')) == declared['originalTerminalSHA256'], 'original gate/log/lifecycle identities ' + name)
    check(gate['execution']['exitCode'] == gate['gateExitCode'] == terminal['actualGateExitCode'] == declared['actualNodeExitCode'] == declared['actualGateExitCode'] == expected_exit, 'actual Node/gate terminal codes separate ' + name)
    check(gate['execution']['timedOut'] is False and gate['execution']['interrupted'] is False, 'original execution no timeout/interrupt ' + name)
    check(gate['acceptanceResult']['passed'] == driver['passed'] == declared['passedAssertions'] == expected_pass and gate['acceptanceResult']['failed'] == driver['failed'] == declared['failedAssertions'] == expected_fail, 'original separate bounded counts ' + name)
    check(gate['probeVerified'] == gate['acceptanceResult']['completed'] == driver['completed'] == helper['completed'] == (expected_exit == 0), 'bounded completion honest ' + name)
    check(declared['genericCompletionVerified'] is False and gate.get('evidence', {}).get('completionVerified', False) is False and ('evidence' in gate) == declared['genericCompletionRecordPresent'], 'generic incomplete or absent original record retained ' + name)
    check(driver['scope']['cases'] == declared['declaredCases'] == expected_cases, 'declared four cases exact ' + name)
    check(set(path.name for path in artifact_dir.iterdir()) == {'driver-receipt.json', 'results.json'}, 'only two actual artifact files no fabricated gcanvas ' + name)
    for side in ['before', 'after']:
        snapshot = gate[side]
        check(snapshot['git']['head'] == HEAD and snapshot['git']['status'] == '' and snapshot['runtime']['fresh'] is True, 'actual frozen clean native/runtime ' + name + '/' + side)
    for key in ['sourceSha256', 'executionFiles', 'executables', 'liveBridge', 'actualGatePython', 'native']:
        check(gate['before'][key] == gate['after'][key], 'actual before/after identical identity ' + name + '/' + key)
    product_maps.append(gate['before']['sourceSha256'])
    check(len(gate['before']['sourceSha256']) == 127 and len(gate['before']['executionFiles']) == 4, '127 committed and4 scratch captures ' + name)
    for repo_path, identity in gate['before']['sourceSha256'].items():
        raw = read(gate_path.parent / 'executed-harness-sources' / repo_path)
        check(sha(raw) == identity, 'actual archived committed capture ' + name + '/' + repo_path)
        result = subprocess.run(['git', '-C', str(ROOT), 'show', HEAD + ':' + repo_path], capture_output=True)
        check(result.returncode == 0 and result.stdout == raw, 'actual committed capture exact frozen Git object ' + name + '/' + repo_path)
    for source_path, identity in gate['before']['executionFiles'].items():
        check(sha(read(source_path)) == identity, 'actual captured scratch source identity ' + name + '/' + Path(source_path).name)
    actors = gate['executionIdentity']
    check(actors['errors'] == [] and actors['node']['pid'] == gate['execution']['pid'] and actors['node']['cmdline'] == gate['command'] == driver['started']['command'], 'actual observed test Node binding ' + name)
    check(actors['node']['sha256'] == driver['started']['node']['sha256'] and actors['browser']['sandboxDisabledFlagsAbsent'] is True and '--no-sandbox' not in actors['browser']['cmdline'] and '--disable-setuid-sandbox' not in actors['browser']['cmdline'], 'actual executable hashes/sandbox ' + name)
    check(terminal['expectedFullSHA'] == terminal['headAfter'] == HEAD and terminal['dirtyBefore'] == terminal['dirtyAfter'] == '', 'owned lifecycle clean original SHA ' + name)
    check(terminal['stopExitCode'] == stop['exitCode'] == declared['actualStopExitCode'] == 0 and terminal['actualServiceExitAfterStop'] == declared['actualServiceExitAfterStop'] == -15, 'stop0 versus serviceSIGTERM−15 ' + name)
    check(stop['processObservations'] == declared['processObservations'] and stop['portObservation'] == declared['portObservation'] and stop['portObservation']['accepting'] is False, 'actual stop raw states/absence/port retained ' + name)
    for item in terminal['rawFiles']:
        raw = read(lifecycle_dir / item['path'])
        check(len(raw) == item['bytes'] and sha(raw) == item['sha256'], 'original lifecycle exact raw binding ' + name + '/' + item['path'])
    if expected_exit == 0:
        check([item['name'] for item in helper['checks']] == expected_names and all(item['ok'] is True for item in helper['checks']), 'all original40 check names/order and positive results')
        check(len(helper['results']) == len(helper['measurements']) == len(helper['trusted']) == 4 and driver['started']['nativePrecondition']['profiles'] == 0 and driver['started']['finalNativeMatchesBaseline'] is True, 'all four original cases zero-profile fixture/exact native final')
        for item in helper['trusted']:
            events = item['events']
            check(len(events) == 3 and [e['type'] for e in events] == ['pointerdown', 'pointerup', 'click'] and all(e['isTrusted'] is True for e in events), 'one exact trusted physical return ' + str(item['width']) + item['family'])
        for item in helper['measurements']:
            button, row = item['button'], item['row']
            check(button['hit'] is True and button['disabled'] is False and button['insideViewport'] is True and button['rect']['height'] >= 44 and row['rect']['bottom'] <= button['rect']['top'] and row['position'] == 'relative' and all(item['identity'].values()), 'original control positive geometry and shared identity ' + str(item['width']) + item['family'])
    else:
        failed = [item for item in helper['checks'] if not item['ok']]
        check(len(helper['checks']) == 17 and [item['name'] for item in helper['checks']] == expected_names[:17] and len(failed) == 1 and failed[0]['name'] == 'one normal physical click precondition #spClose' and failed[0]['detail']['hit'] is True and failed[0]['detail']['disabled'] is True, 'original16/1 precisely enabled completion precondition failure')
        check(len(helper['results']) == 1, 'red only first desktopASM case complete')

check(product_maps[0] == product_maps[1], 'same original product source maps across red/green no product fix fabricated')
preparation = load(read('<workspace-path>'))
for scope in ['originalSources', 'newSources']:
    for path, identity in preparation[scope].items():
        check(sha(read(path)) == identity, 'immutable helper/driver/gate/controller source identity ' + scope + '/' + Path(path).name)
old_helper = read('<workspace-path>').decode()
new_helper = read('<workspace-path>').decode()
old_line = "        if(cancel&&await page.locator(cancel).isEnabled()){await normalClick(cancel);check(width+' SP original Cancel preserves exact native dump',await dump()===before);}\n"
new_block = "        if(cancel&&await page.locator(cancel).isEnabled()){await normalClick(cancel);\n          // Original cancel() reads five native responses before its finally\n          // restores controls. Observe that original completion once; do not\n          // retry the click or bypass a busy/dirty guard. Preserve all40 checks.\n          await page.waitForFunction(()=>document.getElementById('spStatus')?.textContent==='已取消修改，未改動世界。'&&document.getElementById('spCancel')?.disabled===true&&document.getElementById('spClose')?.disabled===false,null,{timeout:20000});\n          check(width+' SP original Cancel preserves exact native dump',await dump()===before);}\n"
check(old_helper.count(old_line) == 1 and old_helper.replace(old_line, new_block) == new_helper, 'entire source delta only original Cancel bounded20s completion precondition')
check('force: true' not in new_helper and 'force:true' not in new_helper and 'while(' not in new_helper, 'no force click or unbounded retry added')
review = load(read('<workspace-path>'))
check(sha(read('<workspace-path>')) == manifest['independentMetadataReview']['originalReportSHA256'] and review['exitCode'] == 0 and len(review['checks']) == 37 and all(review['checks'].values()), 'original different actor37 metadata review retained not product additions')
for path, identity in review['sourceHashes'].items():
    check(sha(read(path)) == identity, 'original different actor source closure ' + Path(path).name)
for item in manifest['fullTestedCommitSourceCopies']:
    result = subprocess.run(['git', '-C', str(ROOT), 'show', HEAD + ':' + item['repositoryPath']], capture_output=True)
    check(result.returncode == 0 and sha(result.stdout) == item['originalSHA256'] and item['originalExecutionSnapshotCaptured'] is False, 'extra exact frozen Git ref not actual capture ' + item['repositoryPath'])
check(manifest['countsAreNeverSummed'] is True and manifest['genericFullCompletionClaimed'] is False and manifest['releaseApproved'] is False, 'bounded scopes never aggregated into full/release claim')
for name, binding in list(protected.items()):
    current = Path(name).read_bytes()
    check((len(current), sha(current)) == binding, 'all original/public evidence unchanged after read-only audit ' + name)

exit_code = 0 if not findings else 1
actual_exe = Path('/proc/self/exe').resolve()
report = {'schema': 'geometry-independent-shell-red-green-packet-review/1', 'reviewerActor': '/root/publication_final_review', 'startedUtc': started, 'finishedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'manifestSHA256': sha(manifest_raw), 'testedProductFullSHA': HEAD, 'reviewCommand': [sys.executable, '-B', str(Path(__file__)), str(OUT)], 'reviewSourceSHA256': sha(Path(__file__).read_bytes()), 'actualReviewerPID': os.getpid(), 'actualPython': str(actual_exe), 'actualPythonSHA256': sha(actual_exe.read_bytes()), 'actualProcessCmdline': [item.decode() for item in Path('/proc/self/cmdline').read_bytes().split(b'\0')[:-1]], 'reviewDecisionExitCode': exit_code, 'metadataChecksPassed': sum(item['passed'] for item in checks), 'metadataChecksFailed': len(findings), 'checksAreProductAssertions': False, 'findings': findings, 'checks': checks, 'protectedInputBindings': [{'path': name, 'bytes': value[0], 'sha256': value[1]} for name, value in protected.items()], 'scope': 'Exact197+manifest198, separate original16/1 incomplete and four-case40/0, source/actual actor/command/exit/native/JSON/prose closure. Generic full completion false and missing original controller process-returncode fields are not fabricated.', 'browserExecuted': False, 'serviceStartedOrStopped': False, 'productOrRepositoryWritten': False, 'githubOrNetworkUsed': False}
output = OUT / 'report.json'
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'report': str(output), 'reportSHA256': sha(output.read_bytes()), 'manifestSHA256': sha(manifest_raw), 'metadataChecksPassed': report['metadataChecksPassed'], 'metadataChecksFailed': len(findings), 'reviewDecisionExitCode': exit_code, 'findings': findings}, ensure_ascii=False))
sys.exit(exit_code)
