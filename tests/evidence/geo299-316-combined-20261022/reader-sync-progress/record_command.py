"""Record an authorized repair command with its exact source variant and original streams."""
from pathlib import Path
import hashlib
import json
import os
import resource
import shutil
import subprocess
import sys
import time

ROOT = Path('/tmp/g261-next299316')
OUT = Path(sys.argv[1])
COMMAND = sys.argv[2:]
OUT.mkdir(parents=True, exist_ok=False)

def digest(body):
    return hashlib.sha256(body).hexdigest()

def git(label, args):
    argv = ['git', *args]
    result = subprocess.run(argv, cwd=ROOT, capture_output=True)
    (OUT / (label + '.stdout')).write_bytes(result.stdout)
    (OUT / (label + '.stderr')).write_bytes(result.stderr)
    (OUT / (label + '.json')).write_text(json.dumps({'command': argv, 'exit': result.returncode}) + '\n')
    assert result.returncode == 0
    return result.stdout

before = {name: (ROOT / name).read_bytes() for name in ('公理層.md', '決策佇列.md', 'BACKLOG.md')}
sha = git('before-head', ['rev-parse', 'HEAD']).decode().strip()
status = git('before-status', ['status', '--porcelain']).decode()
patch = git('before-patch', ['diff', '--binary', 'HEAD'])
env = os.environ.copy()
env.update({'PATH': '/workspace/geo261-environment/bin:' + env['PATH'], 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8',
            'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8', 'GITHUB_SHA': sha,
            'GITHUB_WORKSPACE': str(ROOT), 'GEO261_REAPER_LOG': str(OUT / 'reaper.jsonl')})
stack = resource.getrlimit(resource.RLIMIT_STACK)
resource.setrlimit(resource.RLIMIT_STACK, (16777216, stack[1]))
reaper = Path('/workspace/geo261-environment/reap_children.py')
actual = [sys.executable, '-B', str(reaper), *COMMAND]
for tool in (Path(__file__), reaper):
    shutil.copy2(tool, OUT / tool.name)
receipt = {'schema': 'geo299316-recorded-repair/1', 'sha': sha, 'cwd': str(ROOT), 'command': COMMAND,
           'source_variant': 'exact HEAD with explicit before/after Git patch; dirty repair generation is not a final clean acceptance',
           'status_before': status, 'patch_before_sha256': digest(patch), 'reaper_command': actual,
           'environment': {name: env.get(name) for name in ('PATH', 'LANG', 'LC_ALL', 'TMPDIR', 'CC', 'CFLAGS',
                'GITHUB_SHA', 'GITHUB_WORKSPACE', 'PYTHONOPTIMIZE', 'PYTHONDONTWRITEBYTECODE', 'PYTHONIOENCODING', 'GEO261_REAPER_LOG')},
           'protected_before': {name: digest(body.replace(b'\r\n', b'\n')) for name, body in before.items()},
           'started_epoch': time.time(), 'actual_process_returncode': None}
(OUT / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
with (OUT / 'command.stdout').open('wb') as stdout, (OUT / 'command.stderr').open('wb') as stderr:
    result = subprocess.run(actual, cwd=ROOT, env=env, stdout=stdout, stderr=stderr)
receipt.update(actual_process_returncode=result.returncode, ended_epoch=time.time(),
               head_after=git('after-head', ['rev-parse', 'HEAD']).decode().strip(),
               status_after=git('after-status', ['status', '--porcelain']).decode(),
               patch_after_sha256=digest(git('after-patch', ['diff', '--binary', 'HEAD'])),
               stdout_sha256=digest((OUT / 'command.stdout').read_bytes()),
               stderr_sha256=digest((OUT / 'command.stderr').read_bytes()))
receipt['protected_after'] = {name: digest((ROOT / name).read_bytes().replace(b'\r\n', b'\n')) for name in before}
assert receipt['protected_before'] == receipt['protected_after']
(OUT / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'out': str(OUT), 'sha': sha, 'actual_process_returncode': result.returncode}))
sys.exit(result.returncode)
