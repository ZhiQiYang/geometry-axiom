"""Publish reviewed F38da evidence and its separate PR body with normal pushes."""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import os
import shutil

B = Path(__file__).resolve().parent
R = Path('/tmp/geo324-faces-work-20261024')
D = Path('/tmp/geo324-faces-prbody-work-20261024')
BRANCH = 'codex/geo324-faces-20261024'
PREFIX = 'evidence/geo339-final-F38da'
F = '38da31bcac91db631e6325e40b228f8604810e82'
M = '1f0ebd3e2108d6a4af6b436b5dd3f604df4b8599'
E = 'e9ee6d088b0cad4e3984aa2842a50acc311c2351'
OLD_D = 'e1b5b1716333223436c3ba232aafa27b1e938182'
REVIEW_HEAD = '1ddb1bb73b9bc0958cf488280412ba116c880a5e'
PACKAGE = Path('/workspace/geo339-F38da-affected-terminal-collection-20261024')
PRODUCER = Path('/workspace/geo339-F38da-terminal-collection-producer-20261024')
PEERS = Path('/workspace/train337-canvas-peer-resume')
ACTUAL_PEER = PEERS / 'GEO339_AFFECTED_ACTUAL_PACKAGE_PEER.json'
BODY_PEER = Path('/workspace/geo339-body-peer-combined-20261024/REVIEW.json')
CAP = Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')

def digest(body):
    return hashlib.sha256(body).hexdigest()

def need(value, message):
    if not value:
        raise RuntimeError(message)

def read(path):
    return json.loads(path.read_text())

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

need(digest(CAP.read_bytes()) == 'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762', 'capture pin')
need(digest(ACTUAL_PEER.read_bytes()) == 'c31ff9d2eb450fb68a5fbf55f29231481adefb2b340128131562f4e7affc8313', 'actual peer pin')
actual = read(ACTUAL_PEER)
need(actual['exit_code'] == 0 and not actual['findings'] and actual['source_sha'] == F, 'actual peer acceptance')
need(digest(BODY_PEER.read_bytes()) == '4b67143abafd275ab15a057dafb1ad29ef8c7c9e3d81205595e21ebe21bb5a00', 'body peer pin')
template = (B / 'PR_BODY.template.md').read_bytes()
need(digest(template) == '4bf2bfd32adb1f0e954975f3f40a24fb124ac33fcf7b770cb44cbe42e0c1bdfa', 'body template pin')
need(template.count(b'EVIDENCE_HEAD_PLACEHOLDER') == 1, 'one evidence head substitution only')
need(digest((B / 'payload/PROGRESS.md').read_bytes()) == '8f3f3ebc25279e6e09711a85f52a1590c7c386cfecae7c8c0b8163ba64bb6f7e', 'progress pin')
package = read(PACKAGE / 'PACKAGE.json')
archive = Path(package['archive']['path'])
archive_raw = archive.read_bytes()
need(len(archive_raw) == 4716492 and digest(archive_raw) == 'c2d2c75b39536d7e801cb31af2cc49d0de3aafd130a0a0cdd27b6701b8abc435', 'complete original package pin')
need(read(PRODUCER / 'RESULT.json')['actual_process_returncode'] == 0, 'original collector actual exit')
O = B / 'publication'
O.mkdir()
spec = importlib.util.spec_from_file_location('capture', CAP)
cap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cap)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
for key in ('PYTHONOPTIMIZE', 'GIT_INDEX_FILE', 'GIT_DIR', 'GIT_WORK_TREE', 'GIT_COMMON_DIR'):
    env.pop(key, None)
rec = cap.Recorder(O, env, F)
report = {'sourceSHA': F, 'evidenceParent': E, 'bodyParent': OLD_D, 'evidenceHead': None,
          'bodyHead': None, 'errors': [], 'exitCode': None, 'publisherSHA256': digest(Path(__file__).read_bytes()),
          'startedUTC': datetime.datetime.now(datetime.timezone.utc).isoformat()}

def run(argv, cwd=R, data=None):
    row, stdout, stderr = rec.run(argv, cwd=cwd, data=data, timeout=None, check=False,
        source_sha=F, source_variant='geo339-completed-affected-evidence-publication')
    need(row['actual_process_returncode'] == 0, 'original publication command failed: ' + str(row['directory']))
    return stdout

def remote(branch):
    raw = run(['git', 'ls-remote', '--heads', 'origin', 'refs/heads/' + branch])
    lines = raw.splitlines()
    need(len(lines) == 1 and lines[0].split(b'\t')[1] == ('refs/heads/' + branch).encode(), 'one exact remote branch')
    return lines[0].split(b'\t')[0].decode()

try:
    for root, head, branch in ((R, E, BRANCH), (D, OLD_D, BRANCH + '-prbody')):
        need(run(['git', 'rev-parse', 'HEAD'], root).decode().strip() == head, 'owner worktree head drift')
        need(run(['git', 'status', '--porcelain=v1', '--untracked-files=all'], root) == b'', 'dirty owner worktree refused')
        need(run(['git', 'symbolic-ref', '--short', 'HEAD'], root).decode().strip() == branch, 'wrong owner branch')
        need(remote(branch) == head, 'remote owner branch drift')
    inherited = run(['git', 'diff', '--name-only', '-z', F, E]).split(b'\0')
    need(all(not value or value.startswith(b'evidence/') for value in inherited), 'product/test closure differs from fixed F')
    target = R / PREFIX
    target.mkdir()
    for path in (B / 'payload').iterdir():
        shutil.copyfile(path, target / path.name)
    for name in ('PACKAGE.json', 'RAW_INVENTORY.json', 'SUMMARY.json', 'EXCLUDED_ELF_PAYLOADS.json'):
        shutil.copyfile(PACKAGE / name, target / name)
    shutil.copytree(PRODUCER, target / 'collector-original')
    peer_target = target / 'peer'
    peer_target.mkdir()
    for name in ('GEO339_AFFECTED_ACTUAL_PACKAGE_PEER.json', 'review_339_actual.py',
                 'GEO339_FORMAL_COLLECTOR_STATIC_PEER.json', 'review_339_formal_collector.py',
                 'GEO339_FORMAL_COLLECTOR_STATIC_PEER.initial-comment-substring.json', 'review_339_formal_collector.v1.py.txt'):
        shutil.copyfile(PEERS / name, peer_target / name)
    shutil.copyfile(BODY_PEER, peer_target / 'PR_BODY_TEMPLATE_PEER.json')
    (target / 'tools').mkdir()
    shutil.copyfile(Path(__file__), target / 'tools' / Path(__file__).name)
    shutil.copyfile(B / 'PR_BODY.template.md', target / 'tools/PR_BODY.template.md')
    latest_review = run(['git', 'show', REVIEW_HEAD + ':handoff/pr-reviews/339.md'])
    need(b'2026-10-24T00:39:36Z' in latest_review and b'40040764499' in latest_review, 'latest review context')
    (target / 'LATEST_REVIEW_339.md').write_bytes(latest_review)
    formal = []
    for gate in ('native-and-full-expected', 'canvas', 'assembly', 'documents', 'grid', 'space', 'timber'):
        formal.append({'gate': gate, 'status': 'UNRUN', 'originalExit': None, 'executionSHA': None})
    formal.append({'gate': 'mutation-check', 'status': 'RED', 'originalExit': 1, 'executionSHA': M,
                   'stale': 107, 'retired': 3, 'unrun': 13, 'rerunThisPublication': False})
    for gate in ('architecture-contract', 'architecture-tests', 'product-architecture-tests'):
        formal.append({'gate': gate, 'status': 'PASS', 'originalExit': 0, 'executionSHA': M, 'rerunThisPublication': False})
    save(target / 'CURRENT_STATE.json', {
        'schema': 'geo339-final-F38da-current-state/1', 'productSHA': F, 'evidenceParent': E,
        'formal11': formal, 'formalCounts': {'PASS': 3, 'RED': 1, 'UNRUN': 7},
        'affectedImporterSource': F, 'affectedImporterOriginalExits': [0] * 9,
        'affectedImporterMethods': 142, 'affectedImporterPassed': 142, 'affectedImporterSkipped': 0,
        'predicateSource': F, 'predicateOriginalExits': {'list': [0, 1, 0], 'dict': [0, 1, 0], 'feature': [0, 1, 0]},
        'latestReview': {'handoff': REVIEW_HEAD, 'path': 'handoff/pr-reviews/339.md', 'utc': '2026-10-24T00:39:36Z', 'head': E},
        'B1': 'Formal integration incomplete', 'B2': 'Run40040764499 remains failure; no CI repair/rerun claim',
        'B3': '142 and three predicates now rerun at F; aggregate native remains UNRUN',
        'C1': 'Visible formal takeover still pending', 'C2': 'Base340 remains unaccepted draft',
        'readyToMerge': False, 'productTestsLedgerArchitectureChangedThisPublication': False,
        'newAllowedSkips': [], 'archiveSHA256': package['archive']['sha256'],
    })
    files = {path.relative_to(target).as_posix(): {'bytes': path.stat().st_size, 'sha256': digest(path.read_bytes())}
             for path in sorted(target.rglob('*')) if path.is_file()}
    archive_relative = 'raw/' + archive.name
    files[archive_relative] = {'bytes': len(archive_raw), 'sha256': digest(archive_raw), 'workingCopyOmitted': True}
    save(target / 'PUBLICATION_MANIFEST.json', {'sourceSHA': F, 'files': files, 'selfExcluded': True})
    run(['git', 'add', '--force', '--sparse', '--', PREFIX])
    blob = run(['git', 'hash-object', '-w', '--stdin'], data=archive_raw).decode().strip()
    archive_repo_path = PREFIX + '/' + archive_relative
    run(['git', 'update-index', '--add', '--cacheinfo', '100644', blob, archive_repo_path])
    run(['git', 'update-index', '--skip-worktree', archive_repo_path])
    staged = run(['git', 'diff', '--cached', '--name-only', '-z'])
    need(staged and all(value.startswith((PREFIX + '/').encode()) for value in staged.split(b'\0') if value), 'only own evidence staged')
    run(['git', 'diff', '--cached', '--check'])
    run(['git', 'commit', '-m', 'test(geo339): verify final importer suites and predicate controls'])
    evidence = run(['git', 'rev-parse', 'HEAD']).decode().strip()
    report['evidenceHead'] = evidence
    run(['git', 'push', 'origin', 'refs/heads/' + BRANCH + ':refs/heads/' + BRANCH])
    report['remoteEvidenceHead'] = remote(BRANCH)
    need(report['remoteEvidenceHead'] == evidence, 'remote evidence verification')
    need(digest(run(['git', 'show', evidence + ':' + archive_repo_path])) == digest(archive_raw), 'public Git archive bytes')
    body = template.replace(b'EVIDENCE_HEAD_PLACEHOLDER', evidence.encode())
    (B / 'PR_BODY.md').write_bytes(body)
    (D / 'PR_BODY.md').write_bytes(body)
    run(['git', 'add', '--force', '--sparse', '--', 'PR_BODY.md'], D)
    need(run(['git', 'diff', '--cached', '--name-only', '-z'], D) == b'PR_BODY.md\0', 'only PR_BODY staged')
    run(['git', 'diff', '--cached', '--check'], D)
    run(['git', 'commit', '-m', 'docs(geo339): report final importer proof and remaining integration gates'], D)
    body_head = run(['git', 'rev-parse', 'HEAD'], D).decode().strip()
    report['bodyHead'] = body_head
    run(['git', 'push', 'origin', 'refs/heads/' + BRANCH + '-prbody:refs/heads/' + BRANCH + '-prbody'], D)
    report['remoteBodyHead'] = remote(BRANCH + '-prbody')
    need(report['remoteBodyHead'] == body_head, 'remote PR body verification')
    need(run(['git', 'show', body_head + ':PR_BODY.md'], D) == body, 'public Git PR body bytes')
    for root in (R, D):
        need(run(['git', 'status', '--porcelain=v1', '--untracked-files=all'], root) == b'', 'owner worktree must finish clean')
    report.update(exitCode=0, bodySHA256=digest(body), archiveSHA256=digest(archive_raw), ordinaryPushOnly=True,
                  productTestsLedgerArchitectureChanged=False)
except BaseException:
    import traceback
    report['errors'].append(traceback.format_exc())
    report['exitCode'] = 1
finally:
    report['endedUTC'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save(O / 'RESULT.json', report)
print(json.dumps(report, ensure_ascii=False))
raise SystemExit(report['exitCode'])
