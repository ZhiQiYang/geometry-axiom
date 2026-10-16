#!/usr/bin/env python3
"""Fixed source, registered partial 11-test template proof, retained raw commands."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

SOURCE = 'c65995221cf016cb02533a6cb0952f19c22bfeb9'
BASELINE = Path('/var/tmp/geo261-baseline-a898ad6e')
EVIDENCE = Path('/mnt/d/geometry-axiom-work/geo261-evidence/p1')
OUT = EVIDENCE / 'rectangular-template-c6599522-v1'
ROOT = BASELINE / '.git/geo261-candidates/rectangular-template-c6599522'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def manifest():
    return {str(path.relative_to(ROOT)): sha(path) for path in sorted(ROOT.rglob('*')) if path.is_file()}

OUT.mkdir(exist_ok=False)
ROOT.mkdir(parents=True, exist_ok=False)
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
archive = ROOT.parent / 'rectangular-template-c6599522.tar'
subprocess.run(['git', '-C', str(BASELINE), 'archive', '--format=tar', '--output=' + str(archive), SOURCE], check=True)
with tarfile.open(archive) as content:
    content.extractall(ROOT, filter='data')
before = manifest()
(OUT / 'source-before.json').write_text(json.dumps(before, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
private_tmp = BASELINE / '.git/geo261-rectangular-template-tmp'
private_tmp.mkdir(exist_ok=False)
env = {key: value for key, value in os.environ.items() if not key.upper().startswith('GEOMETRY_')}
command = ['unshare', '--mount', '--propagation', 'private', 'bash',
           str(EVIDENCE / 'rectangular-template-namespace.sh'), str(ROOT), str(OUT), str(private_tmp)]
with (OUT / 'aggregate.log').open('xb') as log:
    run = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, pass_fds=(7,))
after = manifest()
(OUT / 'source-after.json').write_text(json.dumps(after, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
report_file = OUT / 'run-all-logs/py_test_rectangular_template.json'
report = json.loads(report_file.read_text()) if report_file.exists() else {}
correct_counts = all(report.get(key) == value for key, value in {'total': 11, 'run': 11, 'passed': 11, 'failed': 0, 'skipped': 0}.items())
native_file = OUT / 'native-commands.json'
native = json.loads(native_file.read_text()) if native_file.exists() else {}
commands = native.get('commands', [])
mutation = [row for row in commands if row.get('case') == 'fractional-rollback' and row.get('exit') == 1 and 'FRACTIONAL_CELL_ACCEPTED' in row.get('stderr', '')]
missing_object = [row for row in commands if 'case' not in row and row.get('exit') != 0 and 'geo_interval_subdivide' in row.get('stdout', '') + row.get('stderr', '')]
compiler_failures = [row for row in commands if 'case' not in row and row.get('exit') != 0]
controls = len(mutation) == 1 and len(missing_object) == 1 and compiler_failures == missing_object
summary = {'kind': 'fixed-source-partial-registered-template-suite', 'source': SOURCE, 'source_root': str(ROOT),
           'started_utc': started, 'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'command': command, 'selected_test_command': ['python3', '-u', 'tests/run_all.py', '--only', 'rectangular_template'],
           'aggregate_exit': run.returncode, 'test_report': report, 'exact_11_tests_without_skip': correct_counts,
           'native_command_count': len(commands), 'real_mutation_and_missing_object_controls_recorded': controls,
           'source_unchanged': before == after, 'source_files': len(before), 'archive_sha256': sha(archive),
           'source_before_sha256': sha(OUT / 'source-before.json'), 'source_after_sha256': sha(OUT / 'source-after.json'),
           'native_commands_sha256': sha(native_file) if native_file.exists() else None,
           'log_sha256': sha(OUT / 'aggregate.log'), 'shared_lock_holder': Path('/run/lock/ga-wsl-v3.holder').read_text(),
           'runner_sha256': {name: sha(EVIDENCE / name) for name in ('run-rectangular-template.py', 'rectangular-template-namespace.sh')},
           'product_binary_executed': False, 'full_suite_executed': False, 'browser_executed': False,
           'exit': 0 if run.returncode == 0 and correct_counts and controls and before == after else 1}
(OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(OUT / 'exit.txt').write_text(str(summary['exit']) + '\n', encoding='ascii')
print(json.dumps(summary, ensure_ascii=False, indent=2))
sys.exit(summary['exit'])
