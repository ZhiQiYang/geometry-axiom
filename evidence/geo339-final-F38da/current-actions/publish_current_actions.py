"""Append only independently reviewed public Actions evidence to the owned branch."""
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
E = 'dcff3a696d409db5dab9352b9f9d2ce2f76624e6'
OLD_D = '3776f2f06138ad402055a2c308392ad7ea190b80'
PUBLIC = Path('/workspace/pr338-pr339-current-actions-publication-v2-20261024')
PEER = Path('/workspace/train337-canvas-peer-resume/CURRENT_ACTIONS_SAFE_PACKAGE_PEER.json')
CAP = Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def need(value, message):
    if not value:
        raise RuntimeError(message)

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

need(digest(CAP.read_bytes()) == 'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762', 'capture pin')
need(digest(PEER.read_bytes()) == '50a59abac96c3f36af5aea9520596715455e15137ec97c0b00afa7309b1e493a', 'safe actual peer pin')
peer = json.loads(PEER.read_text())
need(peer['exit_code'] == 0 and peer['checks'] == 114024 and peer['findings'] == [], 'safe package accepted')
package = json.loads((PUBLIC / 'PACKAGE.json').read_text())
archive = Path(package['archive'])
need(archive.parent == PUBLIC and archive.stat().st_size == 4334205, 'only approved public archive')
need(digest(archive.read_bytes()) == '40567a58ce19e563245b109736ee1417a28e8d77308ce0027df19dfc6fd361c8', 'safe archive bytes')
template = (B / 'PR_BODY.current-actions.template.md').read_bytes()
need(digest(template) == '16ca4eddad598d1530a20a987179a2ade2df34125f30d5e04dfe6a508829b156', 'body template pin')
need(template.count(b'EVIDENCE_HEAD_PLACEHOLDER') == 1, 'one evidence placeholder')
body_peer_path = B / 'CURRENT_ACTIONS_BODY_PEER.json'
body_peer = json.loads(body_peer_path.read_text())
need(digest(body_peer_path.read_bytes()) == '1e8d98ad07c4cc78f46e480fd756f338714e662576e58761519ebda6f6f42788', 'B2 wording peer pin')
need(body_peer['checks_total'] == 11 and body_peer['failed_checks'] == 0 and all(c['passed'] for c in body_peer['checks']), 'new B2 wording independently accepted')
publisher_peer_root = Path('/workspace/geo339-body-peer-combined-20261024')
supplement = json.loads((publisher_peer_root / 'CURRENT_ACTIONS_PUBLISHER_SUPPLEMENT.json').read_text())
need(supplement['subject_sha256'] == digest(Path(__file__).read_bytes()) and supplement['failed_checks'] == 0,
     'publisher metadata-only supplement independently accepted at exact source')
O = B / 'current-actions-publication'
O.mkdir()
spec = importlib.util.spec_from_file_location('capture', CAP)
cap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cap)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
for key in ('PYTHONOPTIMIZE', 'GIT_INDEX_FILE', 'GIT_DIR', 'GIT_WORK_TREE', 'GIT_COMMON_DIR'):
    env.pop(key, None)
rec = cap.Recorder(O, env, F)
report = {'sourceSHA': F, 'evidenceParent': E, 'bodyParent': OLD_D, 'evidenceHead': None,
          'bodyHead': None, 'errors': [], 'exitCode': None,
          'publisherSHA256': digest(Path(__file__).read_bytes()),
          'startedUTC': datetime.datetime.now(datetime.timezone.utc).isoformat()}

def run(argv, cwd=R):
    row, stdout, stderr = rec.run(argv, cwd=cwd, timeout=None, check=False,
        source_sha=F, source_variant='geo339-public-safe-current-actions-evidence-publication')
    need(row['actual_process_returncode'] == 0, 'publication command failed: ' + str(row['directory']))
    return stdout

def remote(branch):
    rows = run(['git', 'ls-remote', '--heads', 'origin', 'refs/heads/' + branch]).splitlines()
    need(len(rows) == 1 and rows[0].split(b'\t')[1] == ('refs/heads/' + branch).encode(), 'exact remote branch')
    return rows[0].split(b'\t')[0].decode()

try:
    for root, head, branch in ((R, E, BRANCH), (D, OLD_D, BRANCH + '-prbody')):
        need(run(['git', 'rev-parse', 'HEAD'], root).decode().strip() == head, 'owner HEAD drift')
        need(run(['git', 'symbolic-ref', '--short', 'HEAD'], root).decode().strip() == branch, 'owner branch drift')
        need(run(['git', 'status', '--porcelain=v1', '--untracked-files=all'], root) == b'', 'owner worktree clean')
        need(remote(branch) == head, 'remote HEAD drift')
    target = R / PREFIX
    ci = target / 'current-actions'
    ci.mkdir()
    for name in ('PACKAGE.json', 'PUBLIC_REDACTIONS.json'):
        shutil.copyfile(PUBLIC / name, ci / name)
    shutil.copyfile(PEER, ci / PEER.name)
    for name in ('CURRENT_ACTIONS_SAFE_PACKAGE_PEER.initial-schema-assumptions.json',
                 'review_current_actions_safe_package.py', 'review_current_actions_safe_package.v1.py.txt'):
        shutil.copyfile(PEER.parent / name, ci / name)
    for name in ('CURRENT_ACTIONS_PUBLISHER_REVIEW.json', 'CURRENT_ACTIONS_PUBLISHER_SUPPLEMENT.json'):
        shutil.copyfile(publisher_peer_root / name, ci / name)
    shutil.copyfile(body_peer_path, ci / body_peer_path.name)
    shutil.copyfile(B / 'PR_BODY.current-actions.template.md', ci / 'PR_BODY.current-actions.template.md')
    shutil.copyfile(Path(__file__), ci / Path(__file__).name)
    save(ci / 'SCOPE.json', {
        'runId': 40040764499, 'runSourceSHA': 'e9ee6d088b0cad4e3984aa2842a50acc311c2351',
        'classification': 'All seven required jobs were not scheduled: payment failure OR spending limit; exact account cause is not distinguished.',
        'ciRepairClaim': False, 'ciRerunClaim': False, 'B2Resolved': False,
        'actionsProductExecution': False, 'allowedSkip': False,
        'readExits': {'0': 63, '1': 2}, 'signedDownloadFailures': 2,
        'publicRedactions': 2, 'privateOriginalsNotPublished': True,
        'completeOriginalReadsCapturedWith': 'c387 capture.py',
        'packager': 'Direct exec_command true exit 0; no separate c387 packager outer streams exist.',
        'originalRuntimeSHAUnchanged': F,
        'sourceTreeEqualityIsNotExecutionEvidence': True,
    })
    progress = target / 'PROGRESS.md'
    progress.write_text(progress.read_text() + '\n補充（本次 Actions 原件）：run `40040764499` 的七個 job annotations 均指向 payment failed 或 spending limit；每個 job 都未獲 runner、steps 為空，未執行產品。這是本次 run 的環境分類，尚未修復帳戶或重跑 CI，B2 仍未解除。安全包位於 `current-actions/`，SHA-256 `40567a58ce19e563245b109736ee1417a28e8d77308ce0027df19dfc6fd361c8`，獨立審查 114024／0。65 次原讀取中 63 個退出 0、2 個 signed log 下載 Forbidden 退出 1；公開副本只遮蔽兩個簽章值、原完整內容留雲端，其餘 bytes 相同。完整 tree 比對證 F→舊 E 的 20 個變更皆為 evidence，不移標實際測試 SHA，也不改整合 3 PASS／1 RED／7 UNRUN。\n')
    state = json.loads((target / 'CURRENT_STATE.json').read_text())
    state['B2'] = 'Current-run annotations prove payment failure OR spending-limit scheduler block; no repair/rerun and not resolved.'
    state['currentActionsProof'] = {'run': 40040764499, 'runSourceSHA': 'e9ee6d088b0cad4e3984aa2842a50acc311c2351', 'archiveSHA256': package['archive_sha256'], 'peerChecks': 114024, 'peerExit': 0}
    save(target / 'CURRENT_STATE.json', state)
    old_manifest = json.loads((target / 'PUBLICATION_MANIFEST.json').read_text())
    files = {p.relative_to(target).as_posix(): {'bytes': p.stat().st_size, 'sha256': digest(p.read_bytes())}
             for p in sorted(target.rglob('*')) if p.is_file() and p.name != 'PUBLICATION_MANIFEST.json'}
    for relative, meta in old_manifest['files'].items():
        if meta.get('workingCopyOmitted'):
            files[relative] = meta
    archive_relative = 'current-actions/' + archive.name
    files[archive_relative] = {'bytes': archive.stat().st_size, 'sha256': package['archive_sha256'], 'workingCopyOmitted': True}
    save(target / 'PUBLICATION_MANIFEST.json', {'sourceSHA': F, 'files': files, 'selfExcluded': True})
    run(['git', 'add', '--force', '--sparse', '--', PREFIX])
    blob = run(['git', 'hash-object', '-w', str(archive)]).decode().strip()
    archive_repo_path = PREFIX + '/' + archive_relative
    run(['git', 'update-index', '--add', '--cacheinfo', '100644', blob, archive_repo_path])
    run(['git', 'update-index', '--skip-worktree', archive_repo_path])
    staged = run(['git', 'diff', '--cached', '--name-only', '-z'])
    need(staged and all(p.startswith((PREFIX + '/').encode()) for p in staged.split(b'\0') if p), 'only owned evidence staged')
    preserved = []
    for relative, meta in old_manifest['files'].items():
        if not meta.get('workingCopyOmitted'):
            continue
        path = PREFIX + '/' + relative
        original_blob = run(['git', 'rev-parse', E + ':' + path]).decode().strip()
        rows = run(['git', 'ls-files', '--stage', '-z', '--', path]).split(b'\0')
        need(len(rows) == 2 and rows[1] == b'', 'retained omitted receipt has one index entry')
        stage, indexed_path = rows[0].split(b'\t', 1)
        mode, indexed_blob, conflict_stage = stage.split(b' ')
        need(indexed_path.decode() == path and mode == b'100644' and conflict_stage == b'0', 'retained omitted receipt index identity')
        need(indexed_blob.decode() == original_blob, 'old omitted receipt must not be deleted or rewritten')
        preserved.append({'path': path, 'gitBlob': original_blob})
    report['preservedOriginalOmittedReceipts'] = preserved
    run(['git', 'diff', '--cached', '--check'])
    run(['git', 'commit', '-m', 'docs(geo339): preserve current CI scheduling evidence'])
    evidence = run(['git', 'rev-parse', 'HEAD']).decode().strip()
    report['evidenceHead'] = evidence
    need(run(['git', 'rev-parse', evidence + ':' + archive_repo_path]).decode().strip() == blob, 'public archive exact Git blob')
    run(['git', 'push', 'origin', 'refs/heads/' + BRANCH + ':refs/heads/' + BRANCH])
    report['remoteEvidenceHead'] = remote(BRANCH)
    need(report['remoteEvidenceHead'] == evidence, 'public evidence HEAD')
    body = template.replace(b'EVIDENCE_HEAD_PLACEHOLDER', evidence.encode())
    (B / 'PR_BODY.current-actions.md').write_bytes(body)
    (D / 'PR_BODY.md').write_bytes(body)
    run(['git', 'add', '--force', '--sparse', '--', 'PR_BODY.md'], D)
    need(run(['git', 'diff', '--cached', '--name-only', '-z'], D) == b'PR_BODY.md\0', 'only body staged')
    run(['git', 'diff', '--cached', '--check'], D)
    run(['git', 'commit', '-m', 'docs(geo339): classify current Actions scheduling failure'], D)
    body_head = run(['git', 'rev-parse', 'HEAD'], D).decode().strip()
    report['bodyHead'] = body_head
    run(['git', 'push', 'origin', 'refs/heads/' + BRANCH + '-prbody:refs/heads/' + BRANCH + '-prbody'], D)
    report['remoteBodyHead'] = remote(BRANCH + '-prbody')
    need(report['remoteBodyHead'] == body_head, 'public body HEAD')
    need(run(['git', 'show', body_head + ':PR_BODY.md'], D) == body, 'public body exact bytes')
    changed = run(['git', 'diff', '--name-only', '-z', F, evidence])
    need(all(p.startswith(b'evidence/') for p in changed.split(b'\0') if p), 'all changes from F are evidence only')
    for root in (R, D):
        need(run(['git', 'status', '--porcelain=v1', '--untracked-files=all'], root) == b'', 'owner worktrees finish clean')
    report.update(exitCode=0, bodySHA256=digest(body), archiveSHA256=package['archive_sha256'], ordinaryPushOnly=True, productTestsLedgerArchitectureChanged=False)
except BaseException:
    import traceback
    report['errors'].append(traceback.format_exc())
    report['exitCode'] = 1
finally:
    report['endedUTC'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save(O / 'RESULT.json', report)
print(json.dumps(report, ensure_ascii=False))
raise SystemExit(report['exitCode'])
