#!/usr/bin/env python3
"""Same-source registry originals and existing PF-3 mutation driver, unmodified."""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE.parent
recipe = json.loads((HERE / 'recipe.json').read_bytes())
native = json.loads((EVIDENCE / 'native-closure-a3aeef41-v1/summary.json').read_bytes())
root = Path(native['source_root'])
out = EVIDENCE / recipe['label']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest():
    return {str(path.relative_to(root)): sha(path) for path in sorted(root.rglob('*')) if path.is_file()}


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


held, lock = os.fstat(7), Path('/run/lock/ga-wsl-v3.lock').stat()
if (held.st_dev, held.st_ino) != (lock.st_dev, lock.st_ino):
    raise RuntimeError('Original shared lock is not inherited')
if native['source'] != recipe['source'] or not native['source_unchanged']:
    raise RuntimeError('Native prerequisite source identity differs')
if any(row['classification'] in ('native-compile-or-link-failure', 'process-timeout', 'process-or-filesystem-error', 'native-process-failure') for row in native['test_result'].get('failure_details', [])):
    raise RuntimeError('Native prerequisite has infrastructure failure; do not duplicate failing builds')
before = manifest()
expected = json.loads((EVIDENCE / 'native-closure-a3aeef41-v1/source-after.json').read_bytes())
if before != expected:
    raise RuntimeError('Fixed native archive changed before PF-3 run')
for path, expected_sha in recipe['original_source_sha256'].items():
    if sha(root / path) != expected_sha:
        raise RuntimeError('Original referee bytes differ: ' + path)
out.mkdir(exist_ok=False)
save(out / 'source-before.json', before)
runner_before = {name: sha(HERE / name) for name in ('run.py', 'namespace.sh', 'recipe.json')}
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
env = os.environ.copy()
for key in tuple(env):
    if key.startswith(('GEOMETRY_TEST_', 'GEOMETRY_ENGINEERING_')) or key in ('GEOMETRY_MODEL_BASE', 'GEOMETRY_BRIDGE'):
        env.pop(key)
env['PYTHONDONTWRITEBYTECODE'] = '1'
env['GEOMETRY_TEST_BRIDGE'] = '/tmp/geometry-tests/bridge'
env['GEOMETRY_TEST_PF3_ALGORITHM'] = '/tmp/geometry-tests/pf3-algorithm'
commands, exits = {}, {}


def execute(name, arguments, timeout=1800):
    commands[name] = arguments
    with (out / (name + '.log')).open('xb') as stream:
        try:
            actual = subprocess.run(arguments, cwd=root, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
            exits[name] = actual.returncode
        except subprocess.TimeoutExpired:
            exits[name] = 'timeout'
    return exits[name]


execute('build', ['python3', '-u', 'tests/binaries.py', 'build', 'bridge', 'pf3-algorithm'])
execute('status-before', ['python3', '-u', 'tests/binaries.py', 'status', 'bridge', 'pf3-algorithm'])
original_ok = False
mutation_ok = False
mutation_summary = None
if exits['build'] == exits['status-before'] == 0:
    execute('original-layout-host', ['python3', '-u', '-m', 'unittest', '-v', *recipe['modules']])
    log = (out / 'original-layout-host.log').read_text(encoding='utf-8', errors='replace')
    original_ok = exits['original-layout-host'] == 0 and re.search(r'^Ran ' + str(recipe['expected_tests']) + r' tests in ', log, re.M) is not None and re.search(r'^OK$', log, re.M) is not None and 'skipped=' not in log
    execute('pf3-mutations', ['python3', '-u', recipe['mutation_driver'], '--out', str(out / 'mutations'), '--jobs', '1'], timeout=7200)
    summary_path = out / 'mutations/summary.json'
    if summary_path.exists():
        mutation_summary = json.loads(summary_path.read_bytes())
        if isinstance(mutation_summary, dict):
            rows = mutation_summary.get('mutations', [])
            positives = [mutation_summary.get(name, {}) for name in ('baseline', 'restored')]
            mutation_ok = (exits['pf3-mutations'] == 0 and len(rows) == recipe['mutation_cases']
                           and len({row['id'] for row in rows}) == recipe['mutation_cases']
                           and {row['id'] for row in rows} == {row['id'] for row in recipe['mutation_targets']}
                           and all(row.get('verdict') == 'killed' and row.get('counts') == {'run': 1, 'failures': 1, 'errors': 0, 'skipped': 0} for row in rows)
                           and all(row.get('verdict') == 'pass' and row.get('counts') == {'run': 20, 'failures': 0, 'errors': 0, 'skipped': 0} for row in positives)
                           and mutation_summary.get('originalSourcesUnchanged') is True)
execute('status-after', ['python3', '-u', 'tests/binaries.py', 'status', 'bridge', 'pf3-algorithm'])
artifacts = {}
for name in ('bridge', 'pf3-algorithm'):
    binary = Path('/tmp/geometry-tests') / name
    sidecar = Path(str(binary) + '.fingerprint.json')
    if binary.is_file() and sidecar.is_file():
        artifacts[name] = {'sha256': sha(binary), 'bytes': binary.stat().st_size, 'sidecarSha256': sha(sidecar)}
        (out / sidecar.name).write_bytes(sidecar.read_bytes())
after = manifest()
save(out / 'source-after.json', after)
runner_after = {name: sha(HERE / name) for name in runner_before}
summary = {'kind': 'original-pf2-host-regressions-and-pf3-referee', 'source': recipe['source'], 'source_root': str(root),
           'started_utc': started, 'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'recipe': recipe, 'commands': commands, 'exit_codes': exits,
           'original_layout_host_pass': original_ok, 'original_expected_tests': recipe['expected_tests'],
           'mutation_referee_pass': mutation_ok, 'mutation_summary': mutation_summary,
           'source_files': len(before), 'source_unchanged': before == after,
           'source_before_sha256': sha(out / 'source-before.json'), 'source_after_sha256': sha(out / 'source-after.json'),
           'runner_sha256_before': runner_before, 'runner_sha256_after': runner_after, 'runners_unchanged': runner_before == runner_after,
           'registry_binary_artifacts': artifacts, 'log_sha256': {path.name: sha(path) for path in out.glob('*.log')},
           'shared_lock_holder': Path('/run/lock/ga-wsl-v3.holder').read_text(), 'full_suite_executed': False, 'browser_executed': False,
           'exit': 0 if original_ok and mutation_ok and exits['status-after'] == 0 and before == after and runner_before == runner_after else 1}
save(out / 'summary.json', summary)
(out / 'exit.txt').write_text(str(summary['exit']) + '\n', encoding='ascii')
print(json.dumps(summary, ensure_ascii=False, indent=2))
sys.exit(summary['exit'])
