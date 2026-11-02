"""Read-only audit of the downloaded R06 CI artifact; never executes its binaries."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path('/tmp/geometry-resume-20261102/pr363/ci-F4')
NAME = 'r06-browser-mutations-946ba6274e0cbcfab20b8fc0433386e187870d83'
HEAD = '7a876ed6a772f3bb5fff0f9644421d6ec6e6cea4'
EXTRACTED = ROOT / 'extracted' / '13120665899'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read(path):
    return json.loads(path.read_text())

metadata = read(ROOT / 'api/20261102T062301Z/41396262818-artifacts.json')
artifact = next(a for a in metadata['artifacts'] if a['id'] == 13120665899)
archive = ROOT / 'official-zips' / '13120665899.zip'
assert artifact['workflow_run']['head_sha'] == HEAD
assert artifact['workflow_run']['id'] == 41396262818
assert archive.stat().st_size == artifact['size_in_bytes']
assert 'sha256:' + sha(archive.read_bytes()) == artifact['digest']
with zipfile.ZipFile(archive) as package:
    entries = [i for i in package.infolist() if not i.is_dir()]
    for entry in entries:
        assert sha(package.read(entry)) == sha((EXTRACTED / entry.filename).read_bytes()), entry.filename

report = {'schema': 'r06-official-artifact-audit/1', 'reviewedHead': HEAD,
          'runId': 41396262818, 'jobId': 125118138993,
          'artifactId': artifact['id'], 'artifactSha256': artifact['digest'].split(':')[1],
          'zipApiDigestVerified': True, 'extractedEntriesMatchZip': len(entries),
          'scope': 'R06 native cancellation mutation and partial GEOMETRY_ASSEMBLY_ONLY browser mutations; not full canvas',
          'phases': []}
for part, kind in [('r06-native-cancel-evidence', 'native'), ('r06-browser-evidence', 'browser')]:
    folder = EXTRACTED / part
    assert (folder / 'head-sha.txt').read_text().strip() == HEAD
    assert (folder / 'runner-exit-code.txt').read_text().strip() == '0'
    summary_path = folder / 'mutations/summary.json'
    summary = read(summary_path)
    assert summary['ok'] is True and summary['checkoutUnchanged'] is True
    source_map = read(folder / 'mutations/sources.json')
    source_digest = sha(''.join('%s\0%s\n' % row for row in sorted(source_map.items())).encode())
    assert source_digest == summary['sourcesDigest']
    assert len(summary['phases']) == 1
    phase = summary['phases'][0]
    assert phase['kind'] == kind and phase['ok'] is True and phase['restoredBinaryMatches'] is True
    row = {'kind': kind, 'summarySha256': sha(summary_path.read_bytes()),
           'sourcesDigest': source_digest, 'sourceMapEntries': len(source_map),
           'reportedCheckoutUnchanged': True, 'cases': [], 'baselines': []}
    for label in ['baseline', 'restored']:
        observation = phase[label]
        assert observation == read(folder / 'mutations' / kind / label / 'observation.json')
        assert observation['exit'] == 0 and observation['timeout'] is False
        assert observation['verdict'] == 'pass' and observation['reason'] == 'green'
        result = observation['result']
        assert all(not result[k] for k in ['failures', 'errors', 'skipped', 'expectedFailures', 'unexpectedSuccesses'])
        detail = {'label': label, 'exit': 0, 'timeout': False}
        if kind == 'native':
            raw_dir = folder / 'mutations' / kind / label / 'tests'
            assert result == read(raw_dir / 'result.json')
            assert result['run'] == len(result['selected']) == 53
            assert 'Ran 53 tests' in (raw_dir / 'stderr').read_text()
            assert (raw_dir / 'stderr').read_text().rstrip().endswith('OK')
            detail.update(run=53, failures=0, errors=0, skips=0)
        else:
            raw = folder / 'mutations' / kind / label / 'tests/tests/stdout'
            footers = [json.loads(s[len('CDP_RESULT '):]) for s in raw.read_text().splitlines() if s.startswith('CDP_RESULT ')]
            assert footers == [observation['footer']]
            footer = footers[0]
            assert footer['scope']['mode'] == 'partial'
            assert footer['scope']['filters'] == ['GEOMETRY_ASSEMBLY_ONLY']
            assert footer['completed'] is True and footer['passedAssertions'] == 200 and footer['failedAssertions'] == 0
            assert footer['sections'] == {'P77': 134, 'P82': 16, 'R06': 50}
            assert footer['goldenCompare'] == 'not compared (partial mode)' and footer['uncaughtBrowserExceptions'] == 0
            detail.update(passed=200, failed=0, sections=footer['sections'], goldenCompare=footer['goldenCompare'])
        row['baselines'].append(detail)
        build = phase[label + 'Build']
        assert build['exit'] == 0 and build['timeout'] is False
        binary = folder / 'mutations' / kind / label / 'binary/bridge'
        assert sha(binary.read_bytes()) == build['sha256']
    assert phase['baselineBuild']['sha256'] == phase['restoredBuild']['sha256']
    row['baselineRestoredBinarySha256'] = phase['baselineBuild']['sha256']
    for case in phase['cases']:
        assert case['verdict'] == 'killed' and case['reason'] == 'exact-assertion' and case['sourcesRestored'] is True
        observed = case['observation']
        result = observed['result']
        assert observed['exit'] == 1 and observed['timeout'] is False
        assert result['run'] == 1 and result['selected'] == [case['expectedTest']]
        assert all(not result[k] for k in ['errors', 'skipped', 'expectedFailures', 'unexpectedSuccesses'])
        assert len(result['failures']) == 1
        failure = result['failures'][0]
        assert failure['test'] == case['expectedTest'] and failure['tags'] == [case['expectedAssertion']]
        assert failure['bridgeClosed'] is False
        case_dir = folder / 'mutations' / kind / 'cases' / case['name']
        assert case == read(case_dir / 'record.json')
        if kind == 'native':
            assert result == read(case_dir / 'tests/result.json')
            assert 'KILLER[' + case['expectedAssertion'] + ']' in (case_dir / 'tests/stderr').read_text()
        else:
            footers = [json.loads(s[len('CDP_RESULT '):]) for s in (case_dir / 'tests/tests/stdout').read_text().splitlines() if s.startswith('CDP_RESULT ')]
            assert footers == [observed['footer']]
            assert footers[0]['failedAssertions'] == 1 and footers[0]['completed'] is False
            assert case['expectedAssertion'] in footers[0]['fatal']
        assert case['build']['exit'] == 0 and case['build']['timeout'] is False
        assert sha((case_dir / 'binary/bridge').read_bytes()) == case['build']['sha256']
        row['cases'].append({'name': case['name'], 'uniqueExpectedAssertion': case['expectedAssertion'],
                             'verdict': 'killed', 'errors': 0, 'skips': 0, 'timeout': False,
                             'sourcesRestored': True, 'rawResultMatchesSummary': True})
    assert len(row['cases']) == (1 if kind == 'native' else 3)
    report['phases'].append(row)

joblog = ROOT / 'job-logs/125118138993.txt'
text = joblog.read_text()
assert 'node: v24.22.1' in text and HEAD in text
report.update(nodeVersion='v24.22.1', jobLogSha256=sha(joblog.read_bytes()), ok=True)
(ROOT / 'official-r06-browser-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
(ROOT / 'official-r06-browser-audit.txt').write_text(
    'PASS: official ZIP/API SHA256 and every extracted member match.\n'
    'HEAD ' + HEAD + '; Node v24.22.1.\n'
    'Native baseline/restored: 53/53, one cancellation mutation killed only by br13:cancelled-token.\n'
    'Browser baseline/restored: 200/0, P77=134 P82=16 R06=50; three exact assertion kills.\n'
    'Restored binaries match original bytes; source-restoration/checkout-unchanged reports are true.\n'
    'Coverage: partial GEOMETRY_ASSEMBLY_ONLY; golden not compared; not full canvas.\n')
print(json.dumps({'ok': True, 'reviewedHead': HEAD, 'artifactSha256': report['artifactSha256'],
                  'membersVerified': len(entries), 'receipt': str(ROOT / 'official-r06-browser-audit.json')}))
