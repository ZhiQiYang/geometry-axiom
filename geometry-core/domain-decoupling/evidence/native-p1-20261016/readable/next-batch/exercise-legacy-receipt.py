#!/usr/bin/env python3
"""Unchanged 20-test parameter regression with registry-verified adapters."""
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

RECIPE_PATH = Path(sys.argv[1]).resolve()
RECIPE = json.loads(RECIPE_PATH.read_text(encoding='utf-8'))
SOURCE = RECIPE['source']
EVIDENCE = Path('/mnt/d/geometry-axiom-work/geo261-evidence/p1')
RUNNERS = Path(__file__).resolve().parent
ROOT = Path('/var/tmp/geo261-baseline-a898ad6e/.git/geo261-candidates') / RECIPE['native_label']
OUT = EVIDENCE / RECIPE['label']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def manifest():
    return {str(path.relative_to(ROOT)): sha(path) for path in sorted(ROOT.rglob('*')) if path.is_file()}

def run(command, name):
    with (OUT / name).open('xb') as log:
        return subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT).returncode

OUT.mkdir(exist_ok=False)
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
native_receipt = json.loads((EVIDENCE / RECIPE['native_label'] / 'summary.json').read_text(encoding='utf-8'))
if native_receipt.get('source') != SOURCE or native_receipt.get('source_root') != str(ROOT) or native_receipt.get('source_unchanged') is not True:
    raise RuntimeError('The native archive receipt does not prove this exact source')
before = manifest()
frozen = json.loads((EVIDENCE / RECIPE['native_label'] / 'source-before.json').read_text())
if before != frozen:
    raise RuntimeError('N2 archive no longer equals its pre-test fixed-source manifest')
(OUT / 'source-before.json').write_text(json.dumps(before, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
commands = {
    'build': ['python3', '-u', 'tests/binaries.py', 'build', 'model-base', 'bridge'],
    'status': ['python3', '-u', 'tests/binaries.py', 'status', 'model-base', 'bridge'],
    'test': ['python3', '-u', '-m', 'unittest', '-v', 'tests.test_parameters_core'],
}
codes = {'build': run(commands['build'], 'build.log')}
codes['status'] = run(commands['status'], 'status.log')
codes['test'] = run(commands['test'], 'unittest.log') if codes['build'] == 0 and codes['status'] == 0 else None
output = (OUT / 'unittest.log').read_text(encoding='utf-8') if (OUT / 'unittest.log').exists() else ''
exact = bool(re.search(r'Ran 20 tests in', output)) and 'skipped=' not in output
artifacts = {}
for name in ('model-base', 'bridge'):
    path = Path('/tmp/geometry-tests') / name
    sidecar = path.with_name(name + '.fingerprint.json')
    if path.exists():
        artifacts[name] = {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}
    if sidecar.exists():
        shutil.copy2(sidecar, OUT / sidecar.name)
        artifacts[name]['sidecar_sha256'] = sha(sidecar)
after = manifest()
(OUT / 'source-after.json').write_text(json.dumps(after, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
codes['status_after'] = run(commands['status'], 'status-after.log')
summary = {'kind': 'fixed-source-registry-parameter-regression', 'source': SOURCE, 'source_root': str(ROOT),
           'started_utc': started, 'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'commands': commands, 'exit_codes': codes, 'exact_20_tests_without_skip': exact,
           'source_unchanged': before == after, 'source_files': len(before),
           'source_before_sha256': sha(OUT / 'source-before.json'), 'source_after_sha256': sha(OUT / 'source-after.json'),
           'adapter_artifacts': artifacts, 'adapter_build_kind': 'unchanged tests/binaries.py registry at same SHA',
           'shared_lock_holder': Path('/run/lock/ga-wsl-v3.holder').read_text(),
           'runner_sha256': {name: sha(RUNNERS / name) for name in ('run-legacy-receipt.py', 'legacy-receipt-namespace.sh', 'exercise-legacy-receipt.py')} | {'recipe': sha(RECIPE_PATH)},
           'log_sha256': {name: sha(OUT / name) for name in ('build.log', 'status.log', 'unittest.log', 'status-after.log') if (OUT / name).exists()},
           'full_suite_executed': False, 'browser_executed': False,
           'exit': 0 if all(code == 0 for code in codes.values()) and exact and before == after else 1}
(OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(OUT / 'exit.txt').write_text(str(summary['exit']) + '\n', encoding='ascii')
print(json.dumps(summary, ensure_ascii=False, indent=2))
sys.exit(summary['exit'])
