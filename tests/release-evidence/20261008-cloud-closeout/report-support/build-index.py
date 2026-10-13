#!/usr/bin/env python3
"""Build a bounded report snapshot from existing receipts; never run product tests."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path('/workspace/geometry-axiom')
EVIDENCE = Path('/workspace/closure-evidence')
OUT = Path(__file__).resolve().parent
HEAD = '5174a8dafd8c48329d7166abbd3d104e3c28c0c4'
MAIN = '5cc1ffa1ee85120eca14258b86b715151cad274f'

def read(path):
    return json.loads(path.read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git(*args):
    completed = subprocess.run(['git', *args], cwd=ROOT, capture_output=True)
    return {'argv': ['git', *args], 'exitCode': completed.returncode,
            'stdout': completed.stdout.decode(), 'stderr': completed.stderr.decode()}

identity = {'pwd': str(ROOT), 'head': git('rev-parse', 'HEAD'),
            'status': git('status', '--short'), 'main': git('rev-parse', 'origin/main')}
assert identity['head']['exitCode'] == 0 and identity['head']['stdout'].strip() == HEAD
assert identity['status']['exitCode'] == 0 and not identity['status']['stdout']
assert identity['main']['exitCode'] == 0 and identity['main']['stdout'].strip() == MAIN

gate_names = ['full-space-r2', 'timber-r2', 'async-original-r2', 'save-reopen-synthetic',
              'save-roundtrip', 'model-history', 'scenario-lifecycle', 'scenario-workflow',
              'room-acceptance', 'room-pan', 'room-worker']
artifact_names = {'save-roundtrip': 'results.json', 'model-history': 'result.json',
                  'scenario-lifecycle': 'results.json', 'scenario-workflow': 'ui-complete-results.json',
                  'room-acceptance': 'results.json', 'room-pan': 'results.json',
                  'room-worker': 'results.json'}
gates = []
for name in ['full-cdp-r2', *gate_names]:
    source = EVIDENCE / 'gates' / name / 'receipt.json'
    receipt = read(source)
    tested = receipt['before']['git']['head']
    assert tested == ('458779f003e1f57fdc0f4420564a0b295227843e' if name == 'full-cdp-r2' else HEAD)
    assert receipt['before']['git']['status'] == receipt['after']['git']['status'] == ''
    log = Path(receipt['log']['path'])
    assert sha(log) == receipt['log']['sha256']
    script_hashes = {}
    for arg in receipt['command']:
        if not arg.endswith(('.js', '.py', '.cjs')):
            continue
        source_script = ROOT / arg
        if source_script.is_file() and not Path(arg).is_absolute():
            result = subprocess.run(['git', 'show', tested + ':' + arg], cwd=ROOT, capture_output=True)
            assert result.returncode == 0
            script_hashes[arg] = {'gitBlobBytesSha256': hashlib.sha256(result.stdout).hexdigest(),
                                  'basis': 'git show ' + tested + ':' + arg}
    canonical = receipt['evidence'].get('canonicalResult')
    artifact = None
    if name in artifact_names:
        ap = Path('/tmp/geometry-closeout-r2-gates') / name / artifact_names[name]
        a = read(ap)
        assertions = a.get('results', a.get('checks', []))
        truths = [x.get('ok', x.get('passed', x.get('pass'))) for x in assertions]
        assert all(v is True for v in truths)
        canonical = {key: a[key] for key in ['schema', 'completed', 'expected', 'passed', 'failed',
                                             'ok', 'expectedAssertions', 'expectedChecks'] if key in a}
        canonical.update({'recordedResults': len(assertions), 'allRecordedResultsTrue': all(truths)})
        artifact = {'sourcePath': str(ap), 'sha256': sha(ap), 'bytes': ap.stat().st_size}
    gates.append({'name': name, 'receipt': '../gates/' + name + '/receipt.json',
                  'receiptSourcePath': str(source), 'receiptSha256': sha(source),
                  'command': receipt['command'], 'cwd': receipt['cwd'],
                  'before': receipt['before'], 'after': receipt['after'],
                  'execution': receipt['execution'], 'gateExitCode': receipt['gateExitCode'],
                  'canonicalResult': canonical, 'sourceScriptHashes': script_hashes,
                  'rawLog': receipt['log'], 'artifactResult': artifact,
                  'limitations': receipt['limitations']})

pins_source = EVIDENCE / 'inventory/remote-refresh-final/open-prs-pins.json'
pins = read(pins_source)
assert len(pins) == 31
snapshot = {'schema': 'geometry-closeout-report-snapshot/1',
            'createdAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'scope': 'Report of twelve completed gates only (one historical 458 gate and eleven 5174 gates); subsequent batch results require a separate final update.',
            'main': MAIN, 'candidate': HEAD, 'identityCommandEvidence': identity,
            'builderSha256': sha(Path(__file__)), 'gateSnapshot': gates,
            'openPrMetadataObservedUntil': '2026-10-08T17:16:02.004297+00:00',
            'openPrMetadataSourceSha256': sha(pins_source), 'openPrs': pins,
            'productBranchPush': {'head': HEAD, 'verified': True,
                                  'receiptSource': str(EVIDENCE / 'integration/verify-product-push.json'),
                                  'receiptSha256': sha(EVIDENCE / 'integration/verify-product-push.json'),
                                  'stdoutSha256': sha(EVIDENCE / 'integration/verify-product-push.stdout')},
            'finalPublicationHead': None, 'remotePublicationVerified': False,
            'draftPr': None, 'finalDocumentationSourceEquivalence': 'pending after final commit'}
(OUT / 'receipt-index.json').write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'snapshot': str(OUT / 'receipt-index.json'), 'gates': len(gates), 'openPrs': len(pins),
                  'sha256': sha(OUT / 'receipt-index.json')}, ensure_ascii=False))
