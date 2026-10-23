#!/usr/bin/env python3
"""Complete only the known incoming-evidence exclusion after Git rejected restore."""
import ast
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path

repo = Path('/tmp/g261-next314')
previous = '25c15f7b81de07d3c9c66a5553bf9bb43aa8f3fb'
original = '1cd2fc216299041a557654a874509a33884af819'
branch = 'codex/geo314-one-axis-stagger-20261022'
target = 'tests/test_geo261_wood_grid_application.py'
excluded = ['evidence/issue318-reading-a-20261023/PREDECESSOR_314_ANCHOR_MAINTENANCE.json',
            'evidence/issue318-reading-a-20261023/PROGRESS.md']
old = b'if(wood_grid_stagger_value_changed(&old->axis[axis],&now->axis[axis]))'
new = b'if(wood_grid_stagger_value_changed(&old->axis[axis],&now->axis[axis],now->id,(unsigned)axis,facts,count))'
prior = Path('/workspace/geo314-owner-20261023/leaf-backport-20261023T110224684157Z/receipt.json')
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
out = Path('/workspace/geo314-owner-20261023') / ('leaf-backport-completion-' + stamp)
out.mkdir()
helper = Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
if hashlib.sha256(helper.read_bytes()).hexdigest() != 'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762':
    raise RuntimeError('Recorder changed')
spec = importlib.util.spec_from_file_location('backport_completion_capture', helper)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
capture = module.Recorder(out, dict(os.environ), previous)
report = {'scope': 'Complete the same single-leaf cherry-pick; no product/test execution',
          'priorReceipt': str(prior), 'priorReceiptSha256': hashlib.sha256(prior.read_bytes()).hexdigest(),
          'priorNonzeroPreserved': True, 'sourceHead': None, 'remoteHead': None,
          'commands': capture.rows, 'errors': [], 'testsExecuted': False}
def git(*args):
    return capture.run(['git', *args], cwd=repo, timeout=120)[1]
def require(ok, message):
    if not ok:
        raise RuntimeError(message)
code = 1
try:
    require(git('rev-parse', 'HEAD').decode().strip() == previous, 'Unexpected HEAD')
    require(git('branch', '--show-current').decode().strip() == branch, 'Unexpected branch')
    require(not git('ls-tree', '--name-only', 'HEAD', '--', *excluded), 'Excluded incoming files existed at own HEAD; do not remove')
    require(set(git('diff', '--name-only', '--diff-filter=U').decode().splitlines()) <= set(excluded), 'Unexpected source conflict')
    # These two paths are proven absent in the original HEAD and were introduced
    # only by the incoming 318 metadata. Removing them resolves the exclusion.
    git('rm', '-f', '--', *excluded)
    require(not git('diff', '--name-only', '--diff-filter=U'), 'Unmerged paths remain')
    require(git('diff', '--cached', '--name-only').decode().splitlines() == [target], 'Another path is staged')
    before = git('show', previous + ':' + target)
    after = (repo / target).read_bytes()
    require(before.count(old) == 1 and before.replace(old, new, 1) == after, 'Not the reviewed one-line replacement')
    def methods(raw):
        return [n.name for n in ast.walk(ast.parse(raw.decode())) if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]
    require(methods(before) == methods(after), 'Method names changed')
    report.update(exactSingleReplacement=True, testMethodsUnchanged=True, testMethodCount=len(methods(after)),
                  onlyRetainedPath=target, beforeTestSha256=hashlib.sha256(before).hexdigest(), afterTestSha256=hashlib.sha256(after).hexdigest())
    git('diff', '--cached', '--check')
    git('diff', '--cached', '--', target)
    git('commit', '-m', 'Repair the inherited stagger control anchor', '-m',
        '(cherry picked from commit ' + original + ')\nOnly ' + target + ' is retained; incoming issue 318 evidence is excluded.')
    head = git('rev-parse', 'HEAD').decode().strip()
    report['sourceHead'] = head
    require(git('diff-tree', '--no-commit-id', '--name-only', '-r', head).decode().splitlines() == [target], 'Unexpected committed path')
    require(not git('status', '--porcelain=v1', '--untracked-files=all'), 'Own checkout not clean')
    git('push', 'origin', 'HEAD:refs/heads/' + branch)
    remote = git('ls-remote', '--heads', 'origin', 'refs/heads/' + branch).decode().splitlines()
    require(len(remote) == 1, 'No unique remote head')
    report['remoteHead'] = remote[0].split('\t', 1)[0]
    require(report['remoteHead'] == head, 'Remote head differs')
    code = 0
except BaseException as error:
    report['errors'].append(type(error).__name__ + ': ' + str(error))
finally:
    report['maintenanceExit'] = code
    report['endedUtc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    receipt = out / 'receipt.json'
    receipt.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'receipt': str(receipt), 'sourceHead': report['sourceHead'], 'remoteHead': report['remoteHead'],
                      'maintenanceExit': code, 'errors': report['errors']}, ensure_ascii=False))
raise SystemExit(code)
