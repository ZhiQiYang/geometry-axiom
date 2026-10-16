#!/usr/bin/env python3
"""Frozen rename regression and negative controls in a private Git checkout."""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

SOURCE = '73aca666e779527bd096e7f09a9bc12cdc38d051'
BASELINE = Path('/var/tmp/geo261-baseline-a898ad6e')
OUT = Path('/mnt/d/geometry-axiom-work/geo261-evidence/p1/grid-rename-native-v3')
ROOT = BASELINE / '.git/geo261-candidates/grid-rename-73aca666'
EXPECTED = {
    # Git blob has LF; worker Windows checkout SHA d116ef4... has CRLF.
    # Independently verified CRLF -> LF makes the bytes identical before run.
    'geometry-web/grid-inspector.js': '79bb990ae980c8f0a68b4a7b85e91f7dcb9080fa85e62c7fd6dbd181c7d07624',
    'tests/fixtures/grid_inspector_command.cjs': 'd1491dd13456221fb34ce7877bd21e4e133307eca64334eaba2772120bc53509',
    'tests/test_grid_inspector_contract.py': '752685eb5b95191c5958bbfaec765484926fcc34a985c28346d0b9a4213769c7',
    'tests/diagnostics/grid_inspector_mutation_probe.py': '83c16e948e705347336d26d1fab2bd993550852c4b17988ba211684f6fe97abc',
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])

def manifest():
    return {name: sha(ROOT / name) for name in sorted(git('ls-files', '-z').decode().strip('\0').split('\0'))}

def main():
    OUT.mkdir(exist_ok=False)
    ROOT.mkdir(parents=True, exist_ok=False)
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    subprocess.run(['git', '-C', str(ROOT), 'init', '--quiet'], check=True)
    subprocess.run(['git', '-C', str(ROOT), 'config', 'core.autocrlf', 'false'], check=True)
    (ROOT / '.git/objects/info/alternates').write_text('/mnt/d/geometry-axiom/.git/objects\n')
    subprocess.run(['git', '-C', str(ROOT), 'checkout', '--quiet', '--detach', SOURCE], check=True)
    if git('rev-parse', 'HEAD').decode().strip() != SOURCE or git('status', '--porcelain'):
        raise RuntimeError('private checkout is not the clean requested commit')
    before = manifest()
    if {name: before[name] for name in EXPECTED} != EXPECTED:
        raise RuntimeError('frozen source hashes do not match worker receipt')
    (OUT / 'source-before.json').write_text(json.dumps(before, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    spec = importlib.util.spec_from_file_location('rename_v2_binaries', ROOT / 'tests/binaries.py')
    registry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(registry)
    fresh = registry.inspect_one(registry.BY_NAME['bridge'], '/tmp/geometry-tests/bridge')
    if fresh.state != 'fresh':
        raise RuntimeError('main bridge is not fresh for frozen rename sources: ' + fresh.reason)
    command = ['python3', '-u', '-m', 'unittest', '-v', 'tests.test_grid_inspector_contract', 'tests.test_infinite_grid_contract']
    with (OUT / 'unittest.log').open('xb') as log:
        run = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    output = (OUT / 'unittest.log').read_text(encoding='utf-8')
    proper_count = bool(re.search(r'Ran 28 tests in', output)) and 'skipped=' not in output
    mutation_exit = None
    mutation_command = ['python3', '-u', 'tests/diagnostics/grid_inspector_mutation_probe.py', '--native', '--out', str(OUT / 'mutations')]
    if run.returncode == 0 and proper_count:
        with (OUT / 'mutations.log').open('xb') as log:
            mutation_run = subprocess.run(mutation_command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        mutation_exit = mutation_run.returncode
    after = manifest()
    (OUT / 'source-after.json').write_text(json.dumps(after, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    fresh_after = registry.inspect_one(registry.BY_NAME['bridge'], '/tmp/geometry-tests/bridge')
    clean_after = not git('status', '--porcelain') and git('rev-parse', 'HEAD').decode().strip() == SOURCE
    summary = {'kind': 'fixed-commit-rename-regression-and-controls', 'source': SOURCE, 'source_root': str(ROOT),
               'started_utc': started, 'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'command': command, 'test_exit': run.returncode, 'exact_28_tests_without_skip': proper_count,
               'mutation_command': mutation_command, 'mutation_exit': mutation_exit,
               'source_unchanged': before == after, 'checkout_clean_after': clean_after, 'source_files': len(before),
               'worker_product_crlf_sha256': 'd116ef4fbc575f95d371cd280cd5783c9a4e45a2e435d8cfba92602d6e441db9',
               'git_product_lf_sha256': before['geometry-web/grid-inspector.js'],
               'source_before_sha256': sha(OUT / 'source-before.json'), 'source_after_sha256': sha(OUT / 'source-after.json'),
               'bridge_sha256': sha(fresh.path), 'bridge_fresh_before': fresh.state, 'bridge_fresh_after': fresh_after.state,
               'shared_lock_holder': Path('/run/lock/ga-wsl-v3.holder').read_text(),
               'log_sha256': sha(OUT / 'unittest.log'), 'runner_sha256': sha(Path(__file__)),
               'full_suite_executed': False, 'browser_executed': False,
               'exit': 0 if run.returncode == 0 and proper_count and mutation_exit == 0 and before == after and clean_after and fresh_after.state == 'fresh' else 1}
    (OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'exit.txt').write_text(str(summary['exit']) + '\n', encoding='ascii')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary['exit']

if __name__ == '__main__':
    sys.exit(main())
