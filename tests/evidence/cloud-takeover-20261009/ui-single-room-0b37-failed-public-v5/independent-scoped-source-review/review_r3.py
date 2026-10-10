"""Pure binding fixtures and reviewer-self read-only capture; no product run."""
import ast
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path

out = Path('<workspace-path>')
source = Path('<workspace-path>')
raw = source.read_bytes()
digest = hashlib.sha256(raw).hexdigest()
assert digest == '573f192f8f71108ded270f7a9aecb40af93cad30c37cdfa682d3a7df2659c8b4'
tree = ast.parse(raw)
expressions = {name: next(n.value for n in ast.walk(tree) if isinstance(n, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == name for t in n.targets))
               for name in ['probe_python', 'driver_node', 'main_chrome']}
probe = ['/virtual/python', '/scratch/probe.py', '--out', '/scratch/new-case']
fixture = [
    {'pid': 101, 'parent': 100, 'startTicks': '1001', 'parentStartTicks': '1000', 'exe': '/virtual/python', 'argv': ['/virtual/python', '/scratch/run_gate.py', '--', *probe]},
    {'pid': 102, 'parent': 101, 'startTicks': '1002', 'parentStartTicks': '1001', 'exe': '/virtual/python', 'argv': probe},
    {'pid': 103, 'parent': 102, 'startTicks': '1003', 'parentStartTicks': '1002', 'exe': '/node', 'argv': ['node', '/playwright/cli.js']},
    {'pid': 104, 'parent': 103, 'startTicks': '1004', 'parentStartTicks': '1003', 'exe': '/chromium', 'argv': ['chromium', '--remote-debugging-pipe']},
]
def bindings(values, execution_pid=102):
    env = {'Path': Path, 'probe': probe, 'probe_pid': execution_pid,
           'observed': {i: v for i, v in enumerate(values)}}
    for name in ['probe_python', 'driver_node', 'main_chrome']:
        env[name] = eval(compile(ast.Expression(expressions[name]), '<binding-only>', 'eval'), env)
    return {name: [v['pid'] for v in env[name]] for name in ['probe_python', 'driver_node', 'main_chrome']}
checks = []
def check(name, ok, observed=None):
    checks.append({'check': name, 'ok': bool(ok), **({'bindingResult': observed} if observed is not None else {})})
result = bindings(fixture)
check('valid-exact-probe-node-chrome-chain-accepted', result == {'probe_python': [102], 'driver_node': [103], 'main_chrome': [104]}, result)
result = bindings([fixture[0]])
check('original-forwarded-gate-argv-counterexample-rejected', not any(result.values()), result)
bad = copy.deepcopy(fixture); bad[1]['argv'] = [*probe, '--different']
result = bindings(bad)
check('exact-probe-argv-required', not any(result.values()), result)
bad = copy.deepcopy(fixture); bad[2]['parent'] = 101
result = bindings(bad)
check('node-requires-exact-probe-parent', result['probe_python'] == [102] and not result['driver_node'] and not result['main_chrome'], result)
bad = copy.deepcopy(fixture); bad[2]['parentStartTicks'] = 'old-python-start'
result = bindings(bad)
check('node-rejects-reused-python-parent-pid', not result['driver_node'] and not result['main_chrome'], result)
bad = copy.deepcopy(fixture); bad[3]['parent'] = 102
result = bindings(bad)
check('chrome-requires-exact-driver-parent', result['driver_node'] == [103] and not result['main_chrome'], result)
bad = copy.deepcopy(fixture); bad[3]['parentStartTicks'] = 'old-node-start'
result = bindings(bad)
check('chrome-rejects-reused-node-parent-pid', not result['main_chrome'], result)
bad = copy.deepcopy(fixture); bad[3]['argv'].append('--type=renderer')
result = bindings(bad)
check('renderer-does-not-count-as-main-chrome', not result['main_chrome'], result)
result = bindings(fixture, execution_pid=999)
check('actual-inner-execution-pid-required', not any(result.values()), result)
live_node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'live')
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
env = {'Path': Path, 'os': os, 'hashlib': hashlib, 'now': now}
exec(compile(ast.Module(body=[live_node], type_ignores=[]), '<live-only>', 'exec'), env)
cache = {}
first = env['live'](os.getpid(), cache)
second = env['live'](os.getpid(), cache)
fd_hash = hashlib.sha256(Path('/proc/self/exe').read_bytes()).hexdigest()
stat = os.stat('/proc/self/exe')
check('reviewer-self-fd-byte-capture-sanity', first['sha256'] == second['sha256'] == fd_hash and first['executableFileIdentity']['device'] == stat.st_dev and first['executableFileIdentity']['inode'] == stat.st_ino and first['startTicks'] == second['startTicks'] and len(cache) == 1)
check('metadata-relocation-review-remains-pass', json.loads((out / 'source-metadata-relocation-independent-review.json').read_text())['verdict'] == 'pass')
report = {
    'actor': '/root/race_review/hole_order_oracle_review', 'at': now(),
    'source': {'path': str(source), 'sha256': digest},
    'verdict': 'accepted-for-six-direct-Python-probes' if all(c['ok'] for c in checks) else 'fail',
    'scope': 'Source review, pure AST binding fixtures and read-only live capture of this reviewer Python process only. No observer main, original gate, browser, product or service run.',
    'checks': checks,
    'reviewerSelfCapture': first,
    'resolvedOriginalFindings': ['Exact inner execution PID, complete original argv and interpreter path required for actual probe Python.', 'Node and main Chrome bind direct parent PID plus process startTicks to the same probe interpreter chain.', 'Historical exec states retained by PID/startTicks/exe/argv rather than first PID sample only.', 'Executable fd hash is cached by device/inode/size/mtime/ctime and process/exe/argv rechecked.', 'Native stable comparison includes startTicks.', 'Observer/snapshot failures produce fatal exit-2 receipts and preserve existing inner original gate evidence.'],
    'remainingRecoverableLimitations': [
        {'severity': 'medium', 'finding': 'disk-vs-opened-fd inode mismatch uses assert, while polling catches only OSError/ValueError. A concurrent exec may therefore produce a recorded fatal observer failure rather than retrying that sample.', 'next': 'Use ValueError for this transient identity mismatch; no change to probe or acceptance conditions.'},
        {'severity': 'medium', 'finding': 'Timeout cleanup uses TERM and bounded wait, with no final KILL or inventory of survivors. A client ignoring TERM may remain alive; cleanup error is recorded and result is exit 2, so it cannot yield green evidence.', 'next': 'Bounded cleanup of verified owned PID/startTicks, with survivor identity inventory. Keep failure evidence; never stop service or unrelated processes.'}
    ],
    'acceptanceBoundary': 'Original six commands must directly run their browser probe Python scripts, as parent confirmed. This direct-child rule does not cover run_*.py launch wrappers or Node Resume. New real runs still must pass original census and all live-role/source checks; static review is not product acceptance.',
    'notVerified': ['Real observer execution or any of the six product probe results.', 'Actual probe Python/driver Node/Chrome from a live product run.', 'Windows originals or golden comparison.'],
}
p = out / 'observer-r3-independent-review.json'
p.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'verdict': report['verdict'], 'checksPassed': sum(c['ok'] for c in checks), 'checksFailed': sum(not c['ok'] for c in checks), 'report': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}, ensure_ascii=False))
assert all(c['ok'] for c in checks)
