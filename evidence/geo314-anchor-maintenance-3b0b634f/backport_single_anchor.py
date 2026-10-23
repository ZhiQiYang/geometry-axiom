#!/usr/bin/env python3
"""Normal no-commit cherry-pick retaining only the authorized test leaf."""
import ast
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

repo = Path('/tmp/g261-next314')
branch = 'codex/geo314-one-axis-stagger-20261022'
previous = '25c15f7b81de07d3c9c66a5553bf9bb43aa8f3fb'
original = '1cd2fc216299041a557654a874509a33884af819'
target = 'tests/test_geo261_wood_grid_application.py'
excluded = ['evidence/issue318-reading-a-20261023/PREDECESSOR_314_ANCHOR_MAINTENANCE.json',
            'evidence/issue318-reading-a-20261023/PROGRESS.md']
old = b'if(wood_grid_stagger_value_changed(&old->axis[axis],&now->axis[axis]))'
new = b'if(wood_grid_stagger_value_changed(&old->axis[axis],&now->axis[axis],now->id,(unsigned)axis,facts,count))'
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
out = Path('/workspace/geo314-owner-20261023') / ('leaf-backport-' + stamp)
out.mkdir()
helper = Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
if hashlib.sha256(helper.read_bytes()).hexdigest() != 'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762':
    raise RuntimeError('Recorder changed')
spec = importlib.util.spec_from_file_location('backport_capture', helper)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
capture = module.Recorder(out, dict(os.environ), previous)
report = {'scope': 'Single authorized test anchor maintenance cherry-pick; no test/compiler execution',
          'branch': branch, 'beforeHead': previous, 'originalCommit': original,
          'onlyRetainedPath': target, 'discardedIncoming318EvidencePaths': excluded,
          'ownershipConfirmedBy318': True, 'commands': capture.rows, 'errors': [],
          'sourceHead': None, 'remoteHead': None, 'testsExecuted': False}
def git(*args, check=True):
    return capture.run(['git', *args], cwd=repo, timeout=120, check=check)
def require(ok, message):
    if not ok:
        raise RuntimeError(message)
code = 1
try:
    require(git('rev-parse', 'HEAD')[1].decode().strip() == previous, 'Unexpected own HEAD')
    require(git('branch', '--show-current')[1].decode().strip() == branch, 'Unexpected own branch')
    require(not git('status', '--porcelain=v1', '--untracked-files=all')[1], 'Own worktree must start clean')
    before = git('show', previous + ':' + target)[1]
    changed = set(git('diff-tree', '--no-commit-id', '--name-only', '-r', original)[1].decode().splitlines())
    require(changed == {target, *excluded}, 'Original commit has an unexpected path')
    pick, _, _ = git('cherry-pick', '--no-commit', '-x', original, check=False)
    report['originalCherryPickExit'] = pick['actual_process_returncode']
    require(pick['actual_process_returncode'] in (0, 1), 'Cherry-pick did not reach an inspectable state')
    unmerged = set(git('diff', '--name-only', '--diff-filter=U')[1].decode().splitlines())
    require(unmerged <= set(excluded), 'Do not resolve unexpected source conflicts')
    report['excludedMetadataConflicts'] = sorted(unmerged)
    git('restore', '--source=HEAD', '--staged', '--worktree', '--', *excluded)
    require(not git('diff', '--name-only', '--diff-filter=U')[1], 'Unmerged paths remain')
    require(git('diff', '--cached', '--name-only')[1].decode().splitlines() == [target], 'Only the authorized leaf may be staged')
    after = (repo / target).read_bytes()
    require(before.count(old) == 1 and before.replace(old, new, 1) == after, 'Leaf is not the exact single reviewed replacement')
    def methods(raw):
        return [n.name for n in ast.walk(ast.parse(raw.decode('utf-8')))
                if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]
    require(methods(before) == methods(after), 'Test methods changed')
    report.update(testMethodsUnchanged=True, testMethodCount=len(methods(after)),
                  exactSingleReplacement=True, beforeTestSha256=hashlib.sha256(before).hexdigest(),
                  afterTestSha256=hashlib.sha256(after).hexdigest())
    git('diff', '--cached', '--check')
    git('diff', '--cached', '--', target)
    git('commit', '-m', 'Repair the inherited stagger control anchor', '-m',
        '(cherry picked from commit ' + original + ')\nOnly ' + target + ' is retained; incoming issue 318 evidence is excluded.')
    head = git('rev-parse', 'HEAD')[1].decode().strip()
    report['sourceHead'] = head
    require(git('diff-tree', '--no-commit-id', '--name-only', '-r', head)[1].decode().splitlines() == [target], 'Commit contains another path')
    require(not git('status', '--porcelain=v1', '--untracked-files=all')[1], 'Own worktree not clean after leaf commit')
    git('push', 'origin', 'HEAD:refs/heads/' + branch)
    remote = git('ls-remote', '--heads', 'origin', 'refs/heads/' + branch)[1].decode().splitlines()
    require(len(remote) == 1, 'Remote branch did not resolve uniquely')
    report['remoteHead'] = remote[0].split('\t', 1)[0]
    require(report['remoteHead'] == head, 'Remote branch differs from the new source head')
    code = 0
except BaseException as error:
    report['errors'].append(type(error).__name__ + ': ' + str(error))
finally:
    report['endedUtc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    report['maintenanceExit'] = code
    receipt = out / 'receipt.json'
    receipt.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'receipt': str(receipt), 'sourceHead': report['sourceHead'], 'remoteHead': report['remoteHead'],
                      'maintenanceExit': code, 'errors': report['errors']}, ensure_ascii=False))
raise SystemExit(code)
