"""Commit and normally push only the reviewed combined ledger or architecture metadata."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
import traceback

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--kind', choices=('ledger', 'architecture'), required=True)
parser.add_argument('--source', required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
ROOT = Path('/tmp/g261-next299316')
BRANCH = 'codex/geo299-316-combined-20261022'
assert len(args.source) == 40 and not args.out.exists()
args.out.mkdir()
shutil.copy2(__file__, args.out / 'publish_metadata.py')
rows = []
report = {'schema': 'geo299316-metadata-publication/1', 'kind': args.kind,
          'source_before': args.source, 'branch': BRANCH, 'started_epoch': time.time(),
          'force_push': False, 'merge_performed': False, 'commands': rows, 'errors': [],
          'environment': {key: os.environ.get(key) for key in ('PATH', 'LANG', 'LC_ALL', 'GIT_PAGER')}}


def save():
    (args.out / 'receipt.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')


def run(argv, check=True):
    number = len(rows) + 1
    row = {'command': argv, 'cwd': str(ROOT), 'started_epoch': time.time()}
    result = subprocess.run(argv, cwd=ROOT, capture_output=True)
    (args.out / (f'{number:03d}.stdout')).write_bytes(result.stdout)
    (args.out / (f'{number:03d}.stderr')).write_bytes(result.stderr)
    row.update(actual_process_returncode=result.returncode, ended_epoch=time.time(),
               stdout_sha256=hashlib.sha256(result.stdout).hexdigest(),
               stderr_sha256=hashlib.sha256(result.stderr).hexdigest())
    rows.append(row)
    save()
    assert not check or result.returncode == 0, argv
    return result.stdout


try:
    assert run(['git', 'rev-parse', 'HEAD']).decode().strip() == args.source
    assert run(['git', 'branch', '--show-current']).decode().strip() == BRANCH
    run(['git', 'diff', '--cached', '--quiet'])
    run(['git', 'diff', '--check'])
    if args.kind == 'ledger':
        prefix = 'tests/evidence/geo299-316-combined-20261022/ledger-e40762e9/'
        exact = {'.gitignore', 'tests/mutants_results.json', 'geometry-guide/公理層-閱讀器.html'}
        paths = [*sorted(exact), prefix.rstrip('/')]
        message = 'test: regenerate combined mutation ledger with cloud recovery evidence'
    else:
        prefix = 'tests/evidence/geo299-316-combined-20261022/architecture-' + args.source[:8] + '/'
        exact = {'geometry-core/domain-decoupling/' + name for name in
                 ('product-architecture.json', 'product-architecture-scan.json',
                  'PRODUCT-ARCHITECTURE.md', 'product-architecture-receipt.json')}
        paths = [*sorted(exact), prefix.rstrip('/')]
        message = 'docs: refresh combined product architecture receipts on Linux'
    run(['git', 'add', '--', *paths])
    staged = set(run(['git', 'diff', '--cached', '--name-only', '-z']).decode().split('\0')) - {''}
    assert staged and all(path in exact or path.startswith(prefix) for path in staged), staged
    run(['git', 'commit', '-m', message])
    head = run(['git', 'rev-parse', 'HEAD']).decode().strip()
    report['artifact_commit'] = head
    run(['git', 'merge-base', '--is-ancestor', args.source, head])
    run(['git', 'push', 'origin', 'HEAD:refs/heads/' + BRANCH])
    remote = run(['git', 'ls-remote', 'origin', 'refs/heads/' + BRANCH]).decode().split()
    assert remote == [head, 'refs/heads/' + BRANCH], remote
    assert run(['git', 'status', '--porcelain=v1', '--untracked-files=all']) == b''
    report.update(public_head=head, source_after_clean=True, passed=True, finished_epoch=time.time())
except BaseException:
    report['errors'].append(traceback.format_exc())
    report.update(passed=False, finished_epoch=time.time())
    save()
    raise
save()
print(json.dumps({'kind': args.kind, 'public_artifact_sha': report['public_head'],
                  'receipt': str(args.out / 'receipt.json')}, ensure_ascii=False))
