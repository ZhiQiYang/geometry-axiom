"""Bounded primary receipt audit; no product or downloaded ELF execution."""
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import urllib.request
import zipfile

ROOT = Path('/tmp/geometry-resume-20261102/pr363')
CI = ROOT / 'ci-F4'
OUT = ROOT / 'root-final-audit'
HEAD = '7a876ed6a772f3bb5fff0f9644421d6ec6e6cea4'
MERGE = '946ba6274e0cbcfab20b8fc0433386e187870d83'
TREE = 'b39c4d0f71d59097db6af5efd4732ad178e28c3c'


def get(path):
    req = urllib.request.Request('https://api.github.com/repos/ZhiQiYang/geometry-axiom/' + path,
        headers={'User-Agent': 'geometry-cloud-codex', 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.load(response)


started = time.monotonic()
acquired = json.loads((CI / 'artifact-acquisition-20261102T062301Z.json').read_text())
assert acquired['headF4'] == HEAD
parsed, fragments, zip_records = {}, [], []
for artifact in acquired['artifacts']:
    path = CI / 'official-zips' / f"{artifact['artifactId']}.zip"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert artifact['apiDigest'] == 'sha256:' + digest == 'sha256:' + artifact['actualZipSha256']
    expected = {member['path']: member for member in artifact['members']}
    with zipfile.ZipFile(path) as archive:
        members = [entry for entry in archive.infolist() if not entry.is_dir()]
        assert {entry.filename for entry in members} == set(expected)
        for entry in members:
            assert not entry.filename.startswith('/') and '..' not in Path(entry.filename).parts
            data, record = archive.read(entry), expected[entry.filename]
            assert len(data) == record['bytes'] and hashlib.sha256(data).hexdigest() == record['sha256']
            if entry.filename.endswith('.json'):
                value = json.loads(data)
                parsed[record['sha256']] = value
                if isinstance(value, dict) and value.get('schema') == 'geometry-native-shard/1':
                    fragments.append(value)
    zip_records.append({'id': artifact['artifactId'], 'sha256': digest, 'members': len(members)})

assert len(fragments) == 3
names, totals = [], dict(total=0, passed=0, failed=0, skipped=0, allowed_skips=0)
for fragment in fragments:
    assert fragment['commit_sha'] == MERGE and fragment['exit_code'] == 0
    assert not fragment['registry_errors'] and not fragment['expected_problems']
    assert fragment['expected_sha256'] == 'cba8aa2be2c2d252050634f88a9dfc1c03e498d1d938a30ee3c55ca513df4243'
    assert len(fragment['rows']) == len(fragment['selected'])
    names.extend(fragment['selected'])
    for row in fragment['rows']:
        assert row['ran'] and row['process_exit_code'] == 0
        assert not row['env_problem'] and not row['crashed'] and not row['expected_problem']
        if row['counted']:
            for key in totals:
                totals[key] += row[key]
assert len(names) == len(set(names)) == 232 and set(names) == set(fragments[0]['universe'])
assert totals == dict(total=5420, passed=5419, failed=0, skipped=1, allowed_skips=1)

browser_audit = json.loads((CI / 'official-r06-browser-audit.json').read_text())
assert browser_audit['reviewedHead'] == HEAD and browser_audit['ok']
for kind in browser_audit['phases']:
    original = parsed[kind['summarySha256']]
    assert original['ok'] and original['checkoutUnchanged']
    assert original['sourcesDigest'] == kind['sourcesDigest']
    phases = original['phases']
    assert len(phases) == 1 and phases[0]['kind'] == kind['kind']
    phase = phases[0]
    assert phase['ok'] and phase['restoredBinaryMatches']
    expected_cases = {case['name']: case['uniqueExpectedAssertion'] for case in kind['cases']}
    assert {case['name'] for case in phase['cases']} == set(expected_cases)
    for case in phase['cases']:
        assert case['verdict'] == 'killed' and case['reason'] == 'exact-assertion' and case['sourcesRestored']
        assert case['expectedAssertion'] == expected_cases[case['name']]
        observation = case['observation']
        assert observation['exit'] == 1 and not observation['timeout']
        result = observation['result']
        assert not result['errors'] and not result['skipped']
        assert case['expectedAssertion'] in json.dumps(result['failures'], ensure_ascii=False)
    for label in ('baseline', 'restored'):
        baseline = phase[label]
        assert baseline['exit'] == 0 and not baseline['timeout']
        assert not baseline['result']['failures'] and not baseline['result']['errors'] and not baseline['result']['skipped']
        if kind['kind'] == 'browser':
            assert baseline['footer']['passedAssertions'] == 200 and baseline['footer']['failedAssertions'] == 0

# Preserve the original per-case tags; the first audit's uniform-CR20 guess was wrong.
source = subprocess.check_output(['git', '-C', '/tmp/geometry-pr363-20261102', 'show',
    HEAD + ':geometry-core/card-reference/run_archive_mutations.py'], text=True)
tag_maps = [ast.literal_eval(node.value.value) for node in ast.walk(ast.parse(source))
    if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'expected' for target in node.targets)
    and isinstance(node.value, ast.Subscript) and isinstance(node.value.value, ast.Dict)]
assert len(tag_maps) == 1
card = json.loads((CI / 'official-card-native-audit.json').read_text())
assert card['ok'] and card['nativeShardingNegativeControl']['baseline_mutant_restored_exit'] == [0, 1, 0]
assert {case['name'] for case in card['cardCases']} == set(tag_maps[0])
for case in card['cardCases']:
    assert case['expectedTag'] == tag_maps[0][case['name']]
    assert case['verdict'] == 'killed' and case['redExit'] == 1 and case['restoredExit'] == 0

log = (CI / 'job-logs/125118139118.txt').read_text()
footers = [json.loads(match.group(1)) for line in log.splitlines()
    if (match := re.search(r'\bCDP_RESULT (\{.*\})\s*$', line))]
assert len(footers) == 1
full = footers[0]
assert full['scope']['mode'] == 'full' and not full['scope']['filters'] and not full['scope']['modifiers']
assert full['completed'] and full['passedAssertions'] == 2317 and full['failedAssertions'] == 0
assert full['skipped'] == [] and full['goldenCompare'] == 'matched'
assert full['sections']['P77'] == 134 and full['sections']['R06'] == 50
assert full['uncaughtBrowserExceptions'] == 1 and log.count('[EXPECTED EXCEPTION] Error: fb-auto-probe') == 1

small = json.loads((CI / 'full-canvas-small-artifact-proof.json').read_text())
path = CI / 'official-zips' / f"{small['artifactId']}.zip"
assert 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest() == small['apiDigest']
with zipfile.ZipFile(path) as archive:
    for member in small['members']:
        data = archive.read(member['path'])
        assert hashlib.sha256(data).hexdigest() == member['sha256']
        value = json.loads(data)
        assert value['head'] == MERGE and value['status'] == 'trace-disabled-for-this-runner' and value['records'] == 0

jobs = {}
for run, count in [(41396262836, 10), (41396262818, 2)]:
    record = get(f'actions/runs/{run}/jobs?per_page=100')
    assert len(record['jobs']) == count and all(job['status'] == 'completed' and job['conclusion'] == 'success' for job in record['jobs'])
    jobs[str(run)] = [{'id': job['id'], 'name': job['name'], 'conclusion': job['conclusion']} for job in record['jobs']]
commit = get('git/commits/' + MERGE)
assert commit['tree']['sha'] == TREE and HEAD in [parent['sha'] for parent in commit['parents']]
assert get('pulls/363')['head']['sha'] == HEAD

result = {'schema': 'geometry-primary-bounded-adversarial-audit/1', 'head': HEAD,
    'execution_sha': MERGE, 'tree': TREE, 'native_union': 232, 'native_totals': totals,
    'jobs': jobs, 'official_saved_zips_rehashed': 10, 'zip_records': zip_records,
    'full_canvas': {'passed': 2317, 'failed': 0, 'skip': 0, 'golden': 'matched', 'expected_P38': 1},
    'original_card_tags_from_immutable_source': tag_maps[0],
    'downloaded_elf_executions': 0, 'product_tests_rerun': 0,
    'reviewer': 'root primary; final artifact child-peer unavailable due unchanged-model service capacity',
    'source_peer': 'Existing final-F4-peer.json PASS preserved; no new child artifact-peer PASS claimed.',
    'images_metadata_only': small['remainingImageArtifactsMetadataOnly'],
    'status': 'PASS_PRIMARY_BOUNDED_REVIEW', 'elapsed_seconds': time.monotonic() - started}
(OUT / 'REVIEW.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({key: value for key, value in result.items() if key not in ('jobs', 'zip_records', 'images_metadata_only')}, ensure_ascii=False))
