#!/usr/bin/env python3
"""Run unchanged native unittest modules from one fixed Git archive."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

BASELINE = Path('/var/tmp/geo261-baseline-a898ad6e')
EVIDENCE = Path('/mnt/d/geometry-axiom-work/geo261-evidence/p1')
RUNNERS = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def manifest(root):
    return {str(path.relative_to(root)): sha(path) for path in sorted(root.rglob('*')) if path.is_file()}

def main():
    recipe_path = Path(sys.argv[1]).resolve()
    recipe = json.loads(recipe_path.read_text(encoding='utf-8'))
    source, label = recipe['source'], recipe['label']
    if len(source) != 40 or any(c not in '0123456789abcdef' for c in source):
        raise RuntimeError('source must be a complete immutable commit SHA')
    if any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in label):
        raise RuntimeError('label is not a safe local directory name')
    modules = recipe['modules']
    if not modules or any(not name.startswith('tests.test_geo261_') for name in modules):
        raise RuntimeError('recipe is not an original GEO-261 native test suite')
    root = BASELINE / '.git/geo261-candidates' / label
    out = EVIDENCE / label
    out.mkdir(exist_ok=False)
    root.mkdir(parents=True, exist_ok=False)
    runner_files = (Path(__file__), RUNNERS / 'exercise-native-receipt.py', RUNNERS / 'native-receipt-namespace.sh', recipe_path)
    runners_before = {str(path): sha(path) for path in runner_files}
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    archive = root.parent / (label + '.tar')
    subprocess.run(['git', '-C', str(BASELINE), 'archive', '--format=tar', '--output=' + str(archive), source], check=True)
    with tarfile.open(archive) as content:
        content.extractall(root, filter='data')
    before = manifest(root)
    (out / 'source-before.json').write_text(json.dumps(before, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    private_tmp = BASELINE / '.git' / (label + '-tmp')
    private_tmp.mkdir(exist_ok=False)
    env = os.environ.copy()
    env['TMPDIR'] = str(private_tmp)
    env['PYTHONDONTWRITEBYTECODE']= '1'
    cleared = {}
    for key in tuple(env):
        if key.startswith(('GEOMETRY_TEST_', 'GEOMETRY_ENGINEERING_')) or key in ('GEOMETRY_MODEL_BASE', 'GEOMETRY_BRIDGE'):
            cleared[key] = env.pop(key)
    command = ['python3', '-u', str(RUNNERS / 'exercise-native-receipt.py'), str(root), str(out), str(recipe_path)]
    with (out / 'unittest.log').open('xb') as log:
        run = subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
    after = manifest(root)
    (out / 'source-after.json').write_text(json.dumps(after, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    runners_after = {str(path): sha(path) for path in runner_files}
    test = json.loads((out / 'test-result.json').read_text()) if (out / 'test-result.json').exists() else {}
    summary = {'kind': 'fixed-commit-original-native-modules', 'source': source, 'source_root': str(root),
               'recipe': recipe, 'archive_sha256': sha(archive), 'command': command, 'started_utc': start,
               'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'private_tmp': str(private_tmp),
               'shared_lock_holder': Path('/run/lock/ga-wsl-v3.holder').read_text(), 'test_exit': run.returncode,
               'test_result': test, 'source_unchanged': before == after, 'source_files': len(before),
               'source_before_sha256': sha(out / 'source-before.json'), 'source_after_sha256': sha(out / 'source-after.json'),
               'runner_sha256_before': runners_before, 'runner_sha256_after': runners_after,
               'runners_unchanged': runners_before == runners_after, 'cleared_override_names': sorted(cleared),
               'log_sha256': sha(out / 'unittest.log'), 'full_suite_executed': False, 'browser_executed': False,
               'exit': 0 if run.returncode == 0 and before == after and runners_before == runners_after else 1}
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out / 'exit.txt').write_text(str(summary['exit']) + '\n', encoding='ascii')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary['exit']

if __name__ == '__main__':
    sys.exit(main())
