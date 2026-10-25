from pathlib import Path
import hashlib, importlib.util, json, os, subprocess, sys

ROOT = Path('/workspace/issue320-work-20261024')
OUT = Path('/tmp/geo344-manifest-source-publication-20261025')
BASE = 'a5ec136baf3909453867b3eed50f1b93b229ca59'
BRANCH = 'codex/issue320-connection-recovery-20261024'
LEAF = 'geometry-core/domain-decoupling/product-architecture.json'
CAP = Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
PATCH = Path('/tmp/geo344-exclusion-digest-preparation-20261025/fix-exclusion-digest.patch')
def digest(b): return hashlib.sha256(b).hexdigest()
assert digest(CAP.read_bytes()) == 'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
assert digest(PATCH.read_bytes()) == '73c0379d0860a84032257092d8c46d5eb7702b7f0400ccfcd3ab9e4ec91f236f'
assert not OUT.exists()
OUT.mkdir()
(OUT/'PREPARER.py').write_bytes(Path(__file__).read_bytes())
(OUT/'capture.py').write_bytes(CAP.read_bytes())
(OUT/'fix-exclusion-digest.patch').write_bytes(PATCH.read_bytes())
spec = importlib.util.spec_from_file_location('capture', CAP)
cap = importlib.util.module_from_spec(spec); spec.loader.exec_module(cap)
env = dict(os.environ)
for key in list(env):
    if key.startswith(('GIT_', 'MUTATE_')) or key in ('PYTHONOPTIMIZE', 'PYTHONPATH', 'PYTHONSTARTUP', 'NODE_OPTIONS'):
        env.pop(key)
env.update(PYTHONDONTWRITEBYTECODE='1', LANG='C.UTF-8', LC_ALL='C.UTF-8', PYTHONIOENCODING='utf-8')
rec = cap.Recorder(OUT, env, BASE)
def run(*args, data=None):
    return rec.run(list(args), cwd=ROOT, data=data, timeout=1200, source_sha=rec.sha,
                   source_variant='owned #344 single LF exclusion digest publication; no formal acceptance')[1]
def git(*args, **kwargs): return run('git', *args, **kwargs)
assert git('rev-parse', 'HEAD').decode().strip() == BASE
assert git('branch', '--show-current').decode().strip() == BRANCH
assert not git('status', '--porcelain=v1', '--untracked-files=all')
assert git('ls-remote', 'origin', 'refs/heads/'+BRANCH).decode().split() == [BASE, 'refs/heads/'+BRANCH]
patterns = Path(git('rev-parse', '--git-path', 'info/sparse-checkout').decode().strip())
index = Path(git('rev-parse', '--git-path', 'index').decode().strip())
before = patterns.read_bytes()
(OUT/'sparse-before.bin').write_bytes(before)
cap.dump(OUT/'BEFORE.json', {'head': BASE, 'branch': BRANCH, 'index': str(index),
    'index_bytes': index.stat().st_size, 'index_sha256': digest(index.read_bytes()),
    'sparse_path': str(patterns), 'sparse_sha256': digest(before),
    'free': {p:os.statvfs(p).f_bavail*os.statvfs(p).f_frsize for p in ['/workspace','/tmp']}})
git('sparse-checkout', 'add', '--stdin', data=('/'+LEAF+'\n').encode())
after = patterns.read_bytes(); (OUT/'sparse-after.bin').write_bytes(after)
assert set(after.splitlines()) == set(before.splitlines()) | {('/'+LEAF).encode()}
assert digest((ROOT/LEAF).read_bytes()) == '81882184010b5ddb9aa8e8d45467be788a65a79b378037ba6c99268f99bfa975'
assert not git('status', '--porcelain=v1', '--untracked-files=all')
git('apply', '--check', str(PATCH))
git('apply', str(PATCH))
assert digest((ROOT/LEAF).read_bytes()) == 'f0c0b4db4ca01d4825883b73d73bf8644af313cd2bcab4c9b23638b9bbd93d32'
git('diff', '--check')
assert git('diff', '--name-only').decode().splitlines() == [LEAF]
git('diff', '--', LEAF)
git('add', '--', LEAF)
git('commit', '-m', 'fix(architecture): refresh recovery test exclusion digest')
head = git('rev-parse', 'HEAD').decode().strip(); rec.sha = head
assert git('rev-parse', 'HEAD^').decode().strip() == BASE
assert git('diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD').decode().splitlines() == [LEAF]
assert not git('status', '--porcelain=v1', '--untracked-files=all')
git('push', 'origin', 'HEAD:refs/heads/'+BRANCH)
assert git('ls-remote', 'origin', 'refs/heads/'+BRANCH).decode().split() == [head, 'refs/heads/'+BRANCH]
cap.dump(OUT/'RESULT.json', {'exit_code': 0, 'source_sha': head, 'parent': BASE, 'branch': BRANCH,
    'normal_push_verified': True, 'changed_paths': [LEAF], 'manifest_sha256': digest((ROOT/LEAF).read_bytes()),
    'formal_architecture': 'UNRUN', 'strict9': 'not rerun', 'browser': 'not rerun',
    'commands': len(rec.rows), 'free': {p:os.statvfs(p).f_bavail*os.statvfs(p).f_frsize for p in ['/workspace','/tmp']}})
print(json.dumps({'exit_code': 0, 'source_sha': head, 'normal_push_verified': True, 'result':str(OUT/'RESULT.json')}))
