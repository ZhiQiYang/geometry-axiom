"""Publish bounded source-convergence evidence and truthful current-state bodies."""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import os
import shutil
import traceback

P = Path('/workspace/geo340-339-convergence-publication-20261024')
O = P / 'publication'
K = Path('/tmp/geo340-L-merge-work-20261024')
F = Path('/tmp/geo324-faces-work-20261024')
DB = Path('/tmp/geo324-faces-prbody-work-20261024')
KGIT = Path('/workspace/kernel-no-wood-prep/metadata.git')
INDEX = P / 'kernel-body-publication.index'
S340 = '175cee44c56c89871803d955c0c525236727ba65'
S339 = '616ce7538d23fbe7f3bbefae7f2a04e25ebd75a4'
D340 = '77a007711f48b47daa10fbe1cb594d25937e295a'
D339 = '71113ce739f6fe7c327b162e47e6fd7dba349824'
B340 = 'codex/kernel-without-woodworking-20261023'
B339 = 'codex/geo324-faces-20261024'
CAP = Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')

def need(value, message):
    if not value:
        raise RuntimeError(message)

def sha(b):
    return hashlib.sha256(b).hexdigest()

def dump(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

need(sha(CAP.read_bytes()) == 'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762', 'original capture pin')
manifest = json.loads((P / 'PUBLICATION_FILES.json').read_text())
need(manifest['readyAfterIndependentActualPeer'] is True, 'independent peers required')
need(sum(x['bytes'] for x in manifest['files']) < 1024 * 1024, 'bounded original payload below1MiB')
for entry in manifest['files']:
    b = Path(entry['source']).read_bytes()
    need(len(b) == entry['bytes'] and sha(b) == entry['sha256'], 'frozen publication input: ' + entry['source'])
for name, digest in manifest['bodyDraftPins'].items():
    need(sha((P / name).read_bytes()) == digest, 'fixed independently reviewed body draft')
need(not O.exists() and not INDEX.exists() and not Path(str(INDEX) + '.lock').exists(), 'fresh publication artifacts only')
O.mkdir()
spec = importlib.util.spec_from_file_location('cap', CAP)
cap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cap)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', GIT_OPTIONAL_LOCKS='0', GIT_NO_LAZY_FETCH='1')
for key in ('PYTHONOPTIMIZE', 'GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR'):
    env.pop(key, None)
rec = cap.Recorder(O, env, S339)
report = {'schema':'geo340-339-bounded-evidence-publication/1', 'sources':{'340':S340,'339':S339},
          'evidence':{}, 'bodies':{}, 'pushed':{}, 'errors':[], 'exitCode':None,
          'sourceOrTestModified':False, 'ledgerRegenerated':False, 'formalRerunByPublisher':False,
          'startedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}

def run(args, cwd=F, data=None):
    row, out, err = rec.run(args, cwd=cwd, data=data, timeout=None, check=False,
        source_sha=S339, source_variant='evidence-and-body-publication-only-no-subject-run')
    need(row['actual_process_returncode'] == 0, 'publication command failed: ' + row['directory'])
    return out

def git(*args, cwd=F, data=None, index=False):
    cmd = ['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', *args]
    if index:
        cmd = ['env', 'GIT_INDEX_FILE=' + str(INDEX), *cmd]
    return run(cmd, cwd=cwd, data=data)

def clean(cwd, head, branch):
    need(git('rev-parse', 'HEAD', cwd=cwd).decode().strip() == head, 'unexpected owned HEAD')
    need(git('symbolic-ref', '--short', 'HEAD', cwd=cwd).decode().strip() == branch, 'unexpected owner branch')
    need(git('status', '--porcelain=v1', '--untracked-files=all', cwd=cwd) == b'', 'dirty owned checkout')
    need(git('diff', '--cached', '--exit-code', '--name-status', 'HEAD', cwd=cwd) == b'', 'index drift/deletion')
    need(git('diff', '--exit-code', '--name-status', cwd=cwd) == b'', 'working source drift')

def remote(branch, cwd=F):
    rows = git('ls-remote', '--heads', 'origin', 'refs/heads/' + branch, cwd=cwd).decode().splitlines()
    need(len(rows) == 1 and rows[0].split('\t')[1] == 'refs/heads/' + branch, 'one exact remote owner branch')
    return rows[0].split('\t')[0]

def space(stage):
    values = {p:shutil.disk_usage(p).free for p in ('/workspace','/tmp')}
    report.setdefault('freeBytes', []).append({'stage':stage, **values})
    need(values['/workspace'] >= 20*1024*1024 and values['/tmp'] >= 10*1024*1024,
         'publication disk guard: preserve index peak plus root collector reserve')

def evidence(number, cwd, source, branch, prefix):
    space('before-evidence-' + number)
    clean(cwd, source, branch)
    need(remote(branch, cwd) == source, 'remote source drift')
    need(git('ls-tree', source, '--', prefix, cwd=cwd) == b'', 'only entirely new evidence prefix')
    target = cwd / prefix
    need(not target.exists(), 'new owned evidence directory')
    target.mkdir(parents=True)
    names = []
    for entry in manifest['files']:
        dst = target / entry['name']
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(entry['source'], dst)
        need(sha(dst.read_bytes()) == entry['sha256'], 'exact publication bytes')
        names.append(prefix + '/' + entry['name'])
    state = {'source':source,'scope':'ordinary source convergence; kernel aggregate execution remains S175',
             'manifest':manifest,'noOldExecutionShaRelabelled':True,'readyToMerge':False}
    dump(target / 'PUBLICATION_INDEX.json', state)
    names.append(prefix + '/PUBLICATION_INDEX.json')
    git('add', '--force', '--sparse', '--', *names, cwd=cwd)
    staged = git('diff', '--cached', '--name-status', '--no-renames', cwd=cwd).decode().splitlines()
    need(sorted(staged) == sorted('A\t' + p for p in names), 'only exact new evidence files staged; no old path deletion')
    git('diff', '--cached', '--check', cwd=cwd)
    git('commit', '-m', 'Record source convergence and original kernel aggregate acceptance', cwd=cwd)
    e = git('rev-parse', 'HEAD', cwd=cwd).decode().strip()
    need(git('show', '-s', '--format=%P', e, cwd=cwd).decode().strip() == source, 'ordinary evidence parent')
    changed = git('diff', '--name-only', source, e, cwd=cwd).decode().splitlines()
    need(sorted(changed) == sorted(names), 'no source/test/ledger changes')
    clean(cwd, e, branch)
    git('push', 'origin', 'refs/heads/' + branch + ':refs/heads/' + branch, cwd=cwd)
    need(remote(branch, cwd) == e, 'evidence remote exact')
    report['evidence'][number] = e
    report['pushed']['evidence' + number] = True
    dump(O / 'LIVE.json', report)
    return e

def body_bytes(number, e):
    text = (P / ('PR_BODY_' + number + '.draft.md')).read_text()
    need(text.count('__EVIDENCE_HEAD__') == 1, 'exact one body evidence placeholder')
    body = text.replace('__EVIDENCE_HEAD__', e).encode()
    (O / ('PR_BODY_' + number + '.md')).write_bytes(body)
    return body

try:
    need(remote(B340 + '-prbody', KGIT) == D340 and remote(B339 + '-prbody') == D339,
         'both remote body parents fixed')
    clean(DB, D339, B339 + '-prbody')
    e340 = evidence('340', K, S340, B340, 'evidence/geo340-convergence-175cee44')
    e339 = evidence('339', F, S339, B339, 'evidence/geo339-convergence-616ce753')
    space('before-body-340')
    b340 = body_bytes('340', e340)
    need(remote(B340 + '-prbody', KGIT) == D340, 'kernel body remote unchanged')
    refs = git('worktree', 'list', '--porcelain', cwd=KGIT).decode()
    need('branch refs/heads/' + B340 + '-prbody\n' not in refs, 'no kernel body checkout to disturb')
    local_d = git('rev-parse', 'refs/heads/' + B340 + '-prbody', cwd=KGIT).decode().strip()
    git('merge-base', '--is-ancestor', local_d, D340, cwd=KGIT)
    git('read-tree', D340, cwd=KGIT, index=True)
    oid = git('hash-object', '-w', '--stdin', cwd=KGIT, data=b340).decode().strip()
    git('update-index', '--add', '--cacheinfo', '100644,' + oid + ',PR_BODY.md', cwd=KGIT, index=True)
    tree = git('write-tree', cwd=KGIT, index=True).decode().strip()
    delta = git('diff-tree', '--no-commit-id', '--name-status', '-r', D340, tree, cwd=KGIT).decode().splitlines()
    need(delta == ['M\tPR_BODY.md'], 'kernel body only PR_BODY changed, no source/receipt deletion')
    d340 = git('commit-tree', tree, '-p', D340, cwd=KGIT,
               data=b'Update kernel review status with original aggregate acceptance\n').decode().strip()
    need(git('show', '-s', '--format=%P', d340, cwd=KGIT).decode().strip() == D340, 'kernel normal body parent')
    git('update-ref', 'refs/heads/' + B340 + '-prbody', d340, local_d, cwd=KGIT)
    git('push', 'origin', 'refs/heads/' + B340 + '-prbody:refs/heads/' + B340 + '-prbody', cwd=KGIT)
    need(remote(B340 + '-prbody', KGIT) == d340, 'kernel body remote exact')
    need(git('show', d340 + ':PR_BODY.md', cwd=KGIT) == b340, 'kernel published body bytes')
    report['bodies']['340'] = d340
    report['pushed']['body340'] = True
    INDEX.unlink()  # Only this publisher's recreatable temporary index; no source/receipt removed.
    space('before-body-339')
    clean(DB, D339, B339 + '-prbody')
    need(remote(B339 + '-prbody') == D339, 'faces body remote unchanged')
    b339 = body_bytes('339', e339)
    (DB / 'PR_BODY.md').write_bytes(b339)
    git('add', '--force', '--sparse', '--', 'PR_BODY.md', cwd=DB)
    need(git('diff', '--cached', '--name-status', cwd=DB).decode().splitlines() == ['M\tPR_BODY.md'], 'faces body one exact file')
    git('diff', '--cached', '--check', cwd=DB)
    git('commit', '-m', 'Update faces review status after ordinary train convergence', cwd=DB)
    d339 = git('rev-parse', 'HEAD', cwd=DB).decode().strip()
    need(git('show', '-s', '--format=%P', d339, cwd=DB).decode().strip() == D339, 'faces body ordinary parent')
    git('push', 'origin', 'refs/heads/' + B339 + '-prbody:refs/heads/' + B339 + '-prbody', cwd=DB)
    need(remote(B339 + '-prbody') == d339, 'faces body remote exact')
    clean(DB, d339, B339 + '-prbody')
    need(git('show', d339 + ':PR_BODY.md') == b339, 'faces published body bytes')
    report['bodies']['339'] = d339
    report['pushed']['body339'] = True
    report['exitCode'] = 0
except BaseException:
    report['errors'].append(traceback.format_exc())
    report['exitCode'] = 1
finally:
    report['endedUTC'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    dump(O / 'RESULT.json', report)
print(json.dumps(report, ensure_ascii=False))
raise SystemExit(report['exitCode'])
