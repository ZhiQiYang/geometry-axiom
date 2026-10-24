"""Resume evidence publication after an upstream verbatim review whitespace finding."""
from pathlib import Path
import datetime
import gzip
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
E = 'e9ee6d088b0cad4e3984aa2842a50acc311c2351'
OLD_D = 'e1b5b1716333223436c3ba232aafa27b1e938182'
CAP = Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
TARGET = R / PREFIX

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def need(value, message):
    if not value:
        raise RuntimeError(message)

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

need(digest(CAP.read_bytes()) == 'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762', 'capture pin')
initial = json.loads((B / 'publication/RESULT.json').read_text())
need(initial['exitCode'] == 1 and initial['evidenceHead'] is None and initial['bodyHead'] is None, 'initial failure was precommit')
failed = B / 'publication/subcommands/000016'
need(json.loads((failed / 'result.json').read_text())['actual_process_returncode'] == 2, 'initial real diff-check exit')
need((failed / 'stdout.bin').read_bytes() == b'evidence/geo339-final-F38da/LATEST_REVIEW_339.md:45: new blank line at EOF.\n', 'sole original whitespace finding')
need((failed / 'stderr.bin').read_bytes() == b'', 'initial no other stderr')
template = (B / 'PR_BODY.template.md').read_bytes()
need(digest(template) == '4bf2bfd32adb1f0e954975f3f40a24fb124ac33fcf7b770cb44cbe42e0c1bdfa', 'reviewed body template unchanged')
need(template.count(b'EVIDENCE_HEAD_PLACEHOLDER') == 1, 'exact evidence placeholder')
O = B / 'publication-resume-v3'
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
          'resumerSHA256': digest(Path(__file__).read_bytes()),
          'startedUTC': datetime.datetime.now(datetime.timezone.utc).isoformat()}

def run(argv, cwd=R, data=None):
    row, stdout, stderr = rec.run(argv, cwd=cwd, data=data, timeout=None, check=False,
        source_sha=F, source_variant='geo339-evidence-publication-verbatim-review-recovery')
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
        need(remote(branch) == head, 'remote HEAD drift')
    need(run(['git', 'status', '--porcelain=v1', '--untracked-files=all'], D) == b'', 'body worktree clean')
    need(run(['git', 'diff', '--name-only', '-z']) == (PREFIX + '/LATEST_REVIEW_339.md\0').encode(), 'only retained raw moved outside worktree')
    staged = run(['git', 'diff', '--cached', '--name-only', '-z'])
    need(staged and all(p.startswith((PREFIX + '/').encode()) for p in staged.split(b'\0') if p), 'only our evidence staged')
    manifest = json.loads((TARGET / 'PUBLICATION_MANIFEST.json').read_text())
    for relative, meta in manifest['files'].items():
        raw = run(['git', 'show', ':' + PREFIX + '/' + relative])
        need(len(raw) == meta['bytes'] and digest(raw) == meta['sha256'], 'initial staged bytes changed: ' + relative)
    review_path = TARGET / 'LATEST_REVIEW_339.md'
    need(not review_path.exists(), 'raw review already retained outside checkout')
    review_raw = Path('/tmp/geo339-retained-LATEST_REVIEW_339.md').read_bytes()
    need(review_raw == run(['git', 'show', '1ddb1bb73b9bc0958cf488280412ba116c880a5e:handoff/pr-reviews/339.md']), 'original review exact bytes')
    compressed = gzip.compress(review_raw, mtime=0)
    need(gzip.decompress(compressed) == review_raw, 'review gzip roundtrip')
    (TARGET / 'LATEST_REVIEW_339.md.gz').write_bytes(compressed)
    retained = Path('/tmp/geo339-retained-LATEST_REVIEW_339.md')
    need(retained.read_bytes() == review_raw, 'retained raw exact bytes')
    run(['git', 'rm', '--cached', '--sparse', '--', PREFIX + '/LATEST_REVIEW_339.md'])
    recovery = TARGET / 'publication-recovery'
    recovery.mkdir()
    shutil.copyfile(B / 'publication/RESULT.json', recovery / 'INITIAL_PUBLISHER_RESULT.json')
    shutil.copyfile(B / 'publication-resume/RESULT.json', recovery / 'CROSS_DEVICE_RECOVERY_RESULT.json')
    shutil.copyfile(B / 'publication-resume-v2/RESULT.json', recovery / 'SPARSE_INDEX_RECOVERY_RESULT.json')
    shutil.copytree(B / 'publication-resume-v2/subcommands/000036', recovery / 'original-sparse-index-refusal')
    shutil.copyfile(B / 'resume_preserving_raw_review_v2.py', TARGET / 'tools/resume_preserving_raw_review_v2.py')
    shutil.copyfile(B / 'resume_preserving_raw_review.py', TARGET / 'tools/resume_preserving_raw_review.py')
    shutil.copytree(failed, recovery / 'original-diff-check')
    shutil.copyfile(Path(__file__), TARGET / 'tools' / Path(__file__).name)
    save(recovery / 'RECOVERY.json', {
        'classification': 'Evidence packaging: verbatim upstream review has a blank line at EOF.',
        'originalDiffCheckExit': 2,
        'originalReviewSHA256': digest(review_raw), 'originalReviewBytes': len(review_raw),
        'compressedReviewSHA256': digest(compressed),
        'action': 'Preserve original bytes in deterministic gzip; retain original local raw; rerun full staged diff-check.',
        'testsOrAssertionsChanged': False, 'originalReviewEdited': False,
        'originalPublisherFailureRetained': True,
        'sparseIndexRecovery': 'Original git rm refused outside sparse definition; same owned staged evidence path handled with documented --sparse.',
        'recoveryEnvironmentFailure': 'First raw retain rename crossed /tmp to /workspace and failed EXDEV before removal; second uses same filesystem destination.',
    })
    files = {p.relative_to(TARGET).as_posix(): {'bytes': p.stat().st_size, 'sha256': digest(p.read_bytes())}
             for p in sorted(TARGET.rglob('*')) if p.is_file() and p.name != 'PUBLICATION_MANIFEST.json'}
    archive_relative = 'raw/ORIGINAL_F38DA_IMPORTERS_142_AND_PREDICATE_PROOFS.tar.gz'
    files[archive_relative] = manifest['files'][archive_relative]
    save(TARGET / 'PUBLICATION_MANIFEST.json', {'sourceSHA': F, 'files': files, 'selfExcluded': True})
    run(['git', 'add', '--force', '--sparse', '--', PREFIX])
    run(['git', 'diff', '--cached', '--check'])
    run(['git', 'commit', '-m', 'test(geo339): verify final importer suites and predicate controls'])
    evidence = run(['git', 'rev-parse', 'HEAD']).decode().strip()
    report['evidenceHead'] = evidence
    run(['git', 'push', 'origin', 'refs/heads/' + BRANCH + ':refs/heads/' + BRANCH])
    report['remoteEvidenceHead'] = remote(BRANCH)
    need(report['remoteEvidenceHead'] == evidence, 'public evidence HEAD')
    need(digest(run(['git', 'show', evidence + ':' + PREFIX + '/' + archive_relative])) == 'c2d2c75b39536d7e801cb31af2cc49d0de3aafd130a0a0cdd27b6701b8abc435', 'public archive exact bytes')
    need(gzip.decompress(run(['git', 'show', evidence + ':' + PREFIX + '/LATEST_REVIEW_339.md.gz'])) == review_raw, 'public original review unchanged')
    body = template.replace(b'EVIDENCE_HEAD_PLACEHOLDER', evidence.encode())
    (B / 'PR_BODY.md').write_bytes(body)
    (D / 'PR_BODY.md').write_bytes(body)
    run(['git', 'add', '--force', '--sparse', '--', 'PR_BODY.md'], D)
    need(run(['git', 'diff', '--cached', '--name-only', '-z'], D) == b'PR_BODY.md\0', 'only body staged')
    run(['git', 'diff', '--cached', '--check'], D)
    run(['git', 'commit', '-m', 'docs(geo339): report final importer proof and remaining integration gates'], D)
    body_head = run(['git', 'rev-parse', 'HEAD'], D).decode().strip()
    report['bodyHead'] = body_head
    run(['git', 'push', 'origin', 'refs/heads/' + BRANCH + '-prbody:refs/heads/' + BRANCH + '-prbody'], D)
    report['remoteBodyHead'] = remote(BRANCH + '-prbody')
    need(report['remoteBodyHead'] == body_head, 'public body HEAD')
    need(run(['git', 'show', body_head + ':PR_BODY.md'], D) == body, 'public body exact bytes')
    for root in (R, D):
        need(run(['git', 'status', '--porcelain=v1', '--untracked-files=all'], root) == b'', 'owner worktrees finish clean')
    report.update(exitCode=0, bodySHA256=digest(body), archiveSHA256='c2d2c75b39536d7e801cb31af2cc49d0de3aafd130a0a0cdd27b6701b8abc435',
                  ordinaryPushOnly=True, productTestsLedgerArchitectureChanged=False)
except BaseException:
    import traceback
    report['errors'].append(traceback.format_exc())
    report['exitCode'] = 1
finally:
    report['endedUTC'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save(O / 'RESULT.json', report)
print(json.dumps(report, ensure_ascii=False))
raise SystemExit(report['exitCode'])
