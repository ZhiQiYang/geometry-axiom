"""Read-only independent public metadata-review history exact inverse audit."""
import ast
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sys

B = Path('<workspace-path>')
S = Path('<workspace-path>')
U = S / 'geometry-ui-verification'
P = B / 'final-publication-reviews-public-v3'
OUT = Path(sys.argv[1])
M = '0b448d857d76a02b0a7a464b4ec1574c34c85d8fc3311a834b4a4672b704c28c'
checks, findings, inputs, originals = [], [], {}, {}
TOKENS = re.compile(r'(?:/workspace/|/opt/codex/|/tmp/geometry-|/tmp/playwright_chromiumdev_profile-)[A-Za-z0-9._~%+@:=/\-]+')

def sha(raw): return hashlib.sha256(raw).hexdigest()

def read(p):
    p = Path(p)
    raw = p.read_bytes()
    inputs[str(p)] = {'sha256': sha(raw), 'bytes': len(raw)}
    return raw

def check(ok, name, detail=None):
    checks.append({'name': name, 'passed': bool(ok)})
    if not ok: findings.append({'name': name, 'detail': detail})

def pairs(items):
    d = {}
    for k, v in items:
        if k in d: raise ValueError('duplicate key ' + k)
        d[k] = v
    return d

def load(raw): return json.loads(raw, object_pairs_hook=pairs)

def text(t):
    return TOKENS.sub(lambda m: '<workspace-path>' if m.group().startswith('/workspace/') else '<execution-runtime-path>' if m.group().startswith('/opt/') else '<isolated-test-directory>', t)

def project(v):
    if isinstance(v, dict):
        labels = [text(k) for k in v]
        repeated = {k for k in labels if labels.count(k) > 1}
        d = {}
        for k, x in v.items():
            label = text(k)
            if label in repeated: label += '|basename=' + Path(k).name + '|originalKeySha256=' + sha(k.encode())
            if label in d: raise ValueError('noninjective projection')
            d[label] = project(x)
        return d
    if isinstance(v, list): return [project(x) for x in v]
    if isinstance(v, str): return text(v)
    return v

def inverse(original, public):
    if type(original) is not type(public): raise ValueError('type mismatch')
    if isinstance(original, dict):
        labels = [text(k) for k in original]
        repeated = {k for k in labels if labels.count(k) > 1}
        mapped = {}
        for k in original:
            label = text(k)
            if label in repeated: label += '|basename=' + Path(k).name + '|originalKeySha256=' + sha(k.encode())
            if label in mapped: raise ValueError('noninjective inverse')
            mapped[label] = k
        if set(mapped) != set(public): raise ValueError('key census mismatch')
        return {k: inverse(original[k], public[label]) for label, k in mapped.items()}
    if isinstance(original, list):
        if len(original) != len(public): raise ValueError('list mismatch')
        return [inverse(a, b) for a, b in zip(original, public)]
    if isinstance(original, str):
        if text(original) != public: raise ValueError('non-token string change')
        return original
    if original != public: raise ValueError('scalar changed')
    return public

def collect(p):
    p = Path(p)
    raw = read(p)
    originals[(sha(raw), sha(str(p).encode()))] = (p, raw)

started = datetime.datetime.now(datetime.timezone.utc).isoformat()
OUT.mkdir(parents=True, exist_ok=False)
m = load(read(P / 'manifest.json'))
check(sha(read(P / 'manifest.json')) == M, 'exact final-ready metadata historyv3 manifest')
names = [x['path'] for x in m['publicFiles']]
check(len(names) == len(set(names)) == 63, 'exact63 unique listed files')
check({p.relative_to(P).as_posix() for p in P.rglob('*') if p.is_file()} == set(names) | {'manifest.json'}, 'exact64 total no unlistedfiles')
check(not any(p.is_symlink() for p in P.rglob('*')), 'no symlinks')
for item in m['publicFiles']:
    raw = read(P / item['path'])
    check(sha(raw) == item['sha256'] and len(raw) == item['bytes'], 'manifest exact hash/size ' + item['path'])
    if Path(item['path']).suffix == '.json': load(raw)

actor_path = S / 'geometry-publication-final-review-20261009/actor-index-v1/actor-index.json'
actor = load(read(actor_path))
check(sha(read(actor_path)) == m['originalActorIndexSHA256'] == '304f7db805963db8a5b03b1603d4bd1cb52c75f05abc64493c0a67e3bb878eef', 'immutable prior12review actor index exact304f')
collect(actor_path)
collect(S / 'geometry-publication-final-review-20261009/seal_review_actor_index_v1.py')
collect(S / 'geometry-publication-final-review-20261009/actor-index-v1.raw.log')
for review in actor['reviews']:
    for key in ['report', 'rawLog', 'executedReviewerSource', 'readonlyParserDependency']:
        if key in review: collect(review[key]['path'])
for folder in ['source43-v3-independent-inverse-r2', 'source43-v4-independent-inverse']:
    d = U / folder
    for p in d.iterdir():
        if p.is_file() and p.suffix in {'.log', '.json', '.py'}: collect(p)
    original = load(read(d / 'receipt.json'))
    for arg in original.get('actualCommand', []):
        if isinstance(arg, str) and arg.endswith('.py') and Path(arg).exists(): collect(arg)
for filename in ['review_source43_public_v3_inverse.py', 'review_source43_public_v3_inverse_r2.py', 'review_source43_public_v4_inverse.py', 'diagnose_source43_inverse_v3.py', 'source43-v3-independent-inverse-diagnostic.json', 'package_source43_inverse_execution_index.py']:
    if (U / filename).exists(): collect(U / filename)
source_index = U / 'source43-inverse-execution-source-index/index.json'
collect(source_index)
for role in load(read(source_index))['roles']:
    collect(role['immutableCopy'])
    if role.get('originalRaw'): collect(role['originalRaw']['path'])
for status in m['rootSourceStatus']:
    p = S / status['report']; collect(p)
    identity = load(read(p)).get('executionIdentity', {})
    source, pin = identity.get('script'), identity.get('scriptSHA256')
    available = bool(source and Path(source).exists() and sha(read(source)) == pin)
    check(available == status['matchingRetainedOriginalSourceAvailable'] and not available == status['missingSourceIsUnknownNotBackfilled'], 'ROOT original source pin availability honest ' + status['report'])
    if available: collect(source)

for item in m['sourceAndArtifactReferences']:
    key = (item['originalSha256'], item['originalPathSHA256'])
    check(key in originals, 'exact original source hash and pathhash available ' + item['path'])
    if key not in originals: continue
    path, raw = originals[key]
    public = read(P / item['path'])
    check(len(raw) == item['originalBytes'] and path.name == item['originalBasename'], 'original identity/bytes/basename ' + item['path'])
    check(len(public) == item['bytes'] and sha(public) == item['sha256'], 'ref exact public identity ' + item['path'])
    check(item['publicSourceWasExecuted'] is False and item['genericDetectorPrefixLiteralsPreserved'] is True and item['byteIdenticalOriginal'] == (raw == public) and item['publicProjection'] == (raw != public), 'sourcepublication versus execution distinct ' + item['path'])
    if path.suffix == '.json':
        a, b = load(raw), load(public)
        check(project(a) == b and inverse(a, b) == a, 'complete decoded JSON inverse all keys values types and characters ' + item['path'])
    elif path.suffix == '.jsonl':
        a = [load(x) for x in raw.decode().splitlines() if x.strip()]
        b = [load(x) for x in public.decode().splitlines() if x.strip()]
        check(project(a) == b and inverse(a, b) == a, 'complete JSONL row/key/scalar inverse ' + item['path'])
    else:
        check(text(raw.decode()) == public.decode(), 'all non-token source/log/prose bytes inverse ' + item['path'])
    if path.suffix == '.py':
        ast.parse(public.decode())
        check(True, 'public source syntax only never executed ' + item['path'])

check(len(m['reviewOutcomes']) == 14 and m['formalFullReviewIncluded'] is False, 'dated14review outcomes no premature formalFULL')
byname = {x['name']: x for x in m['reviewOutcomes']}
for review in actor['reviews']:
    outcome = byname[review['name']]
    for key in ['actor', 'actualReviewExitCode', 'passedMetadataChecks', 'failedMetadataChecks', 'originalFindingsPreserved']:
        check(outcome[key] == project(review.get(key, [])), 'original historical reviewer outcome preserved ' + review['name'] + '/' + key)
    check(outcome['reportOriginalSHA256'] == review['report']['sha256'] and outcome['countsAreProductAssertions'] is False, 'reviewer metadata never product counts ' + review['name'])
for name, folder in [('source43-v3-failed', 'source43-v3-independent-inverse-r2'), ('source43-v4-accepted', 'source43-v4-independent-inverse')]:
    a = load(read(U / folder / 'receipt.json')); o = byname[name]
    selected = {k: v for k, v in a.items() if k in {'schema', 'actor', 'checkedUTC', 'actualCommand', 'actualPython', 'actualPythonSHA256', 'scriptSHA256', 'manifestSHA256', 'passedChecks', 'failedChecks', 'checksPassed', 'checksFailed', 'accepted', 'passed', 'failed', 'exitCode', 'actualReviewExitCode', 'ok'}}
    check(project(selected) == o['originalResult'] and o['reportOriginalSHA256'] == sha(read(U / folder / 'receipt.json')) and o['countsAreProductAssertions'] is False, 'original source43 failed/accepted outcome exact ' + name)
for filename, field in [('prepare_final_publication_review_addendum_v3.py', 'publicationBuilderOriginalSHA256'), ('prepare_final_publication_review_addendum_v1.py', 'inheritedPublicationRecipeSHA256'), ('prepare_final_publication_review_addendum_v2.py', 'intermediateWrapperSHA256')]:
    check(sha(read(B / filename)) == m[field], 'history builder actual versus legacy recipe source identity ' + field)
check('exec(' not in read(B / 'prepare_final_publication_review_addendum_v3.py').decode(), 'actual v3 builder directsource no legacy dynamic exec')
for p, identity in list(inputs.items()):
    raw = Path(p).read_bytes()
    check(sha(raw) == identity['sha256'] and len(raw) == identity['bytes'], 'all original/public inputs unchanged after review ' + p)
failed = len(findings)
r = {'schema': 'geometry-independent-publication-history-v3-inverse-review/1', 'actor': '/root/publication_final_review', 'startedUTC': started, 'finishedUTC': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'actualCommand': [sys.executable, '-B', str(Path(__file__).resolve()), str(OUT)], 'actualPython': os.readlink('/proc/self/exe'), 'actualPythonSHA256': sha(Path('/proc/self/exe').read_bytes()), 'actualPID': os.getpid(), 'actualCmdlineHex': Path('/proc/self/cmdline').read_bytes().hex(), 'reviewerSourceSHA256': sha(Path(__file__).read_bytes()), 'manifestSHA256': M, 'passedMetadataChecks': len(checks)-failed, 'failedMetadataChecks': failed, 'finalPacketAccepted': failed == 0, 'computedReviewerExitCode': 1 if failed else 0, 'productTestsExecuted': False, 'checks': checks, 'findings': findings, 'inputs': inputs, 'limits': ['Metadata reviewer counts never product assertions; no original reviewer/product/browser/service/GH/API rerun.', 'Actual currentbuilder is directv3; manifestv1/v2 recipe identities are retained historical roles, not current dynamic execution.', 'No original missing process/executable/exit gap is filled from a current source; SHA-matching original source copies only.', 'Old metadata red and legitimate supplements stay unchanged; actual historical prose-loss repairs and initial reviewer assumptions remain separate.', 'FormalFULL is dated excluded from v3; a fresh successor may append it, without altering this mothermanifest.']}
(OUT / 'report.json').write_text(json.dumps(r, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({k: r[k] for k in ['manifestSHA256', 'passedMetadataChecks', 'failedMetadataChecks', 'finalPacketAccepted', 'computedReviewerExitCode']}))
for f in findings: print(json.dumps(f, ensure_ascii=False))
sys.exit(1 if failed else 0)
