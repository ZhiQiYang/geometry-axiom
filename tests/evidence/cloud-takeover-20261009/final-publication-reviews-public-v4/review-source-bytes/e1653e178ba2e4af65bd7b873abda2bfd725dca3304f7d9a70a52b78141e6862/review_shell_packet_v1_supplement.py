"""Resolve exactly three reviewer assumptions; original failed review stays intact."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys

BASE = Path('<workspace-path>')
B = Path('<workspace-path>')
P = B / 'f3b-shell-return-scopes-public-v1'
OUT = Path(sys.argv[1])
checks, findings, bindings = [], [], {}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    path = Path(path)
    raw = path.read_bytes()
    bindings[str(path)] = {'bytes': len(raw), 'sha256': sha(raw)}
    return raw


def load(path):
    return json.loads(read(path))


def check(value, name):
    checks.append({'name': name, 'passed': bool(value)})
    if not value:
        findings.append(name)


OUT.mkdir(parents=True, exist_ok=False)
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
prior_path = BASE / 'shell-packet-v1-review/report.json'
prior = load(prior_path)
check(sha(read(prior_path)) == 'b397d66eb42692a1f8c911b32ed62b045eda582dd02b37800d4d4cb6c7616452', 'original14075/3 review retained exact hash')
check(prior['reviewDecisionExitCode'] == 1 and len(prior['findings']) == 3 and prior['metadataChecksPassed'] == 14075, 'original failed review not rewritten or called zero')
expected = ['JSON exact key census rounds/red-original/receipt.public.json', 'JSON exact key census rounds/green-completion-v2/receipt.public.json', 'all original40 check names/order and positive results']
check([item['name'] for item in prior['findings']] == expected, 'exact only three assumption findings')
for item in prior['protectedInputBindings']:
    raw = read(item['path'])
    check(len(raw) == item['bytes'] and sha(raw) == item['sha256'], 'every previously reviewed source/artifact remains immutable ' + item['path'])
manifest = load(P / 'manifest.json')
check(sha(read(P / 'manifest.json')) == prior['manifestSHA256'] == '4ec51be9a583d025d2a1cc06e78f3a260a2241dc295a1985efa14f4aa9d12867', 'same frozen final-ready shell packet')
configs = load(B / 'f3b-shell-return-scopes-config-v1.json')
for scope, config in zip(manifest['rounds'], configs):
    original = load(config['receipt'])
    dedicated = load(P / scope['receiptPath'])
    artifact = load(P / ('rounds/' + scope['name'] + '/artifacts/' + Path(config['receipt']).parent.name + '/receipt.json'))
    check(set(dedicated) - set(original) == {'publicProjection'} and set(original) - set(dedicated) == set(), 'only declared publicProjection annotation is additive ' + scope['name'])
    note = dedicated.pop('publicProjection')
    check(dedicated == artifact, 'all original fields precisely equal independently inverse-checked artifact projection ' + scope['name'])
    check(note['originalSha256'] == sha(read(config['receipt'])) and note['originalBytes'] == len(read(config['receipt'])) and note['originalRetainedOutsideGit'] is True, 'new annotation original byte binding ' + scope['name'])
    check(note['dictionaryKeyAudit'] == [item for item in scope['rawEvidence'] if item['path'].endswith('/' + Path(config['receipt']).parent.name + '/receipt.json')][0]['projectionDictionaryKeyAudit'], 'additive annotation exact injective key audit ' + scope['name'])

helper = load('<isolated-test-directory>')
names = []
for width in [1400, 390]:
    create = '#mobileCreateObject' if width == 390 else '#btnCreateObject'
    for family, entry, close in [('ASM', '#btnNewAssembly', '#asmClose'), ('SP', '#btnNewSectionProfile', '#spClose')]:
        names.extend(['unique visible original Create entry', 'one normal physical click precondition ' + create, 'one normal physical click precondition ' + entry, str(width) + ' ' + family + ' shared original row stays normal flow', str(width) + ' ' + family + ' actual return center hits original control'])
        if family == 'SP':
            names.extend(['one normal physical click precondition #spCancel', str(width) + ' SP original Cancel preserves exact native dump'])
        names.extend(['one normal physical click precondition ' + close, str(width) + ' ' + family + ' one original trusted return gesture', str(width) + ' ' + family + ' exact native full dump unchanged', str(width) + ' ' + family + ' same original project bar returns home'])
check([item['name'] for item in helper['checks']] == names and len(names) == 40 and all(item['ok'] is True for item in helper['checks']), 'exact original40 names/order use actual desktop and original390 Create controls')
for offset, create in [(0, '#btnCreateObject'), (9, '#btnCreateObject'), (20, '#mobileCreateObject'), (29, '#mobileCreateObject')]:
    check(helper['checks'][offset]['detail'] == [create] and helper['checks'][offset + 1]['detail']['hit'] is True and helper['checks'][offset + 1]['detail']['disabled'] is False and helper['checks'][offset + 1]['detail']['insideViewport'] is True, 'each original visible Create route positively hit ' + str(offset))
original_helper = read('<workspace-path>').decode()
check("document.querySelectorAll('#btnCreateObject,#mobileCreateObject')" in original_helper, 'original unchanged helper declares both normal visible Create routes')

outer = load(B / 'f3b-shell-return-scopes-builder-execution-v1.json')
inner = load(B / 'f3b-shell-return-scopes-package-build-v1.json')
check(outer['actualExitCode'] == inner['actualExitCode'] == 0 and inner['manifestSHA256'] == prior['manifestSHA256'], 'actual outer and inner builder0 separately bind this exact packet')
check(outer['actualCommand'] == inner['builderCommand'] and outer['actualPython'] == inner['actualPython'] and outer['actualPythonSHA256'] == inner['actualPythonSHA256'], 'actual producer source/executable command chain preserved')
for item in outer['executorSources'] + outer['rawStreams'] + inner['publicationSourceClosure'] + inner['inputFiles'] + inner['rawStreams']:
    raw = read(item['path'])
    check(len(raw) == item['bytes'] and sha(raw) == item['sha256'], 'actual producer source/input/raw stream identity ' + item['path'])
check(outer['savedSourceSnapshotsBefore'] == outer['savedSourceSnapshotsAfter'], 'publication preserves all saved22 source snapshot identities and mtimes')
for path, item in outer['savedSourceSnapshotsBefore'].items():
    raw = read(path)
    check(sha(raw) == item['sha256'] and Path(path).stat().st_mtime_ns == item['mtimeNs'], 'saved source snapshot still exactly preserved ' + path)
check(inner['productExecuted'] is False and inner['validatorExecuted'] is False and inner['browserOrServiceUsed'] is False and inner['repoWritten'] is False and inner['independentQA'] is False, 'producer self-checks do not become independent or product execution')

exit_code = 0 if not findings else 1
actual_exe = Path('/proc/self/exe').resolve()
report = {'schema': 'geometry-shell-packet-independent-assumption-resolution/1', 'actor': '/root/publication_final_review', 'startedUtc': started, 'finishedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'reviewCommand': [sys.executable, '-B', str(Path(__file__)), str(OUT)], 'sourceSHA256': sha(Path(__file__).read_bytes()), 'actualReviewerPID': os.getpid(), 'actualPython': str(actual_exe), 'actualPythonSHA256': sha(actual_exe.read_bytes()), 'manifestSHA256': prior['manifestSHA256'], 'priorReviewReportSHA256': sha(read(prior_path)), 'priorActualExitCode': 1, 'priorMetadataChecksPassed': 14075, 'priorMetadataChecksFailed': 3, 'originalFindingsPreserved': prior['findings'], 'resolvedAssumptions': ['Dedicated public receipt intentionally adds one explicitly declared non-product publicProjection annotation; all original fields match the raw artifact projection.', 'Original390 route uses mobileCreateObject while desktop1400 uses btnCreateObject. Original helper, source assertions, actual40 count/order and positive trusted/native checks remain unchanged.'], 'metadataChecksPassed': sum(item['passed'] for item in checks), 'metadataChecksFailed': len(findings), 'findings': findings, 'checks': checks, 'reviewDecisionExitCode': exit_code, 'finalPacketAccepted': exit_code == 0, 'countsAreProductAssertions': False, 'sourceAndRawBindings': bindings, 'browserOrNativeExecuted': False, 'serviceOrRepositoryOrGitHubWritten': False, 'productTestsRepeated': False}
path = OUT / 'report.json'
path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'report': str(path), 'reportSHA256': sha(path.read_bytes()), 'manifestSHA256': prior['manifestSHA256'], 'metadataChecksPassed': report['metadataChecksPassed'], 'metadataChecksFailed': len(findings), 'reviewDecisionExitCode': exit_code, 'findings': findings}, ensure_ascii=False))
sys.exit(exit_code)
