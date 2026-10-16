#!/usr/bin/env python3
"""N1c fixed archive, original 28 tests, source and build evidence."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

SOURCE = '49f03842cca4f70e0e38a82d120c06edd1b16189'
BASELINE = Path('/var/tmp/geo261-baseline-a898ad6e')
EVIDENCE = Path('/mnt/d/geometry-axiom-work/geo261-evidence/p1')
OUT = EVIDENCE / 'native-grid-49f03842-v1'
ROOT = BASELINE / '.git/geo261-candidates/native-grid-49f03842'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def manifest():
    return {str(path.relative_to(ROOT)): sha(path) for path in sorted(ROOT.rglob('*')) if path.is_file()}

def main():
    OUT.mkdir(exist_ok=False)
    ROOT.mkdir(parents=True, exist_ok=False)
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    archive = ROOT.parent / 'native-grid-49f03842.tar'
    subprocess.run(['git', '-C', str(BASELINE), 'archive', '--format=tar', '--output=' + str(archive), SOURCE], check=True)
    with tarfile.open(archive) as source:
        source.extractall(ROOT, filter='data')
    before = manifest()
    (OUT / 'source-before.json').write_text(json.dumps(before, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    private_tmp = BASELINE / '.git/geo261-native-grid-tmp'
    private_tmp.mkdir(exist_ok=True)
    env = os.environ.copy()
    env['TMPDIR'] = str(private_tmp)
    for key in ('GEOMETRY_MODEL_BASE', 'GEOMETRY_TEST_BRIDGE', 'GEOMETRY_ENGINEERING_BRIDGE', 'GEOMETRY_TEST_ENGINEERING_JSON', 'GEOMETRY_TEST_CORE'):
        env.pop(key, None)
    command = ['python3', '-u', str(EVIDENCE / 'exercise-native-grid49.py'), str(ROOT), str(OUT)]
    with (OUT / 'unittest.log').open('xb') as log:
        run = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    after = manifest()
    (OUT / 'source-after.json').write_text(json.dumps(after, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    summary = {'kind': 'fixed-commit-targeted-native-grid', 'source': SOURCE, 'source_root': str(ROOT),
               'archive_sha256': sha(archive), 'command': command, 'started_utc': start,
               'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'private_tmp': str(private_tmp), 'shared_lock_holder': Path('/run/lock/ga-wsl-v3.holder').read_text(),
               'test_exit': run.returncode, 'source_unchanged': before == after, 'source_files': len(before),
               'source_before_sha256': sha(OUT / 'source-before.json'), 'source_after_sha256': sha(OUT / 'source-after.json'),
               'log_sha256': sha(OUT / 'unittest.log'), 'full_suite_executed': False, 'browser_executed': False,
               'runner_sha256': {name: sha(EVIDENCE / name) for name in ('run-native-grid49.py', 'exercise-native-grid49.py')},
               'exit': 0 if run.returncode == 0 and before == after else 1}
    if (OUT / 'test-result.json').exists():
        summary['test_result'] = json.loads((OUT / 'test-result.json').read_text())
    (OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'exit.txt').write_text(str(summary['exit']) + '\n', encoding='ascii')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary['exit']

if __name__ == '__main__':
    sys.exit(main())
