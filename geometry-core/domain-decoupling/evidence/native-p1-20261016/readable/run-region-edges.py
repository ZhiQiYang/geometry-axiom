#!/usr/bin/env python3
"""Separate frozen-old red and fixed-new green geometry evidence."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

OLD = '51e9045b43078a77383afdaf5db379117ffc8871'
NEW = 'be9ed3e7886f951918a8e02e678e0284f0d34079'
BASELINE = Path('/var/tmp/geo261-baseline-a898ad6e')
EVIDENCE = Path('/mnt/d/geometry-axiom-work/geo261-evidence/p1')
OVERLAYS = ('tests/test_geo261_region_edges.py', 'tests/geo261_region_edges_harness.c',
            'tests/fixtures/geo261_region_crossing.scene', 'tests/fixtures/geo261_region_unit_hole.scene')
EXPECTED_FAILURES = {'test_crossing_holes_have_positive_overlap_without_contained_vertices',
                     'test_unit_rectangles_exclude_hole_interiors_at_coordinate_limits',
                     'test_unit_strips_keep_two_maximal_intervals_and_capacity_failure',
                     'test_product_crossing_holes_rejected_without_mutation',
                     'test_product_unit_hole_placement_rejected_without_mutation'}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def manifest(root):
    return {str(path.relative_to(root)): sha(path) for path in sorted(root.rglob('*')) if path.is_file()}

def run_case(mode, source):
    label = 'region-edges-' + mode + '-' + source[:8] + '-v1'
    out = EVIDENCE / label
    root = BASELINE / '.git/geo261-candidates' / label
    out.mkdir(exist_ok=False)
    root.mkdir(parents=True, exist_ok=False)
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    archive = root.parent / (label + '.tar')
    subprocess.run(['git', '-C', str(BASELINE), 'archive', '--format=tar', '--output=' + str(archive), source], check=True)
    with tarfile.open(archive) as content:
        content.extractall(root, filter='data')
    original = manifest(root)
    overlay_receipt = {}
    if mode == 'old':
        for name in OVERLAYS:
            data = subprocess.check_output(['git', '-C', str(BASELINE), 'show', NEW + ':' + name])
            target = root / name
            if target.exists():
                raise RuntimeError('old-source overlay would overwrite an existing tracked file: ' + name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            overlay_receipt[name] = sha(target)
    before = manifest(root)
    expected_overlay_only = all(before[name] == value for name, value in original.items()) and set(before) - set(original) == set(overlay_receipt)
    if not expected_overlay_only:
        raise RuntimeError('archive product changed during judge-only overlay')
    (out / 'archive-source.json').write_text(json.dumps(original, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out / 'source-before.json').write_text(json.dumps(before, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    private_tmp = BASELINE / '.git' / (label + '-tmp')
    private_tmp.mkdir(exist_ok=True)
    env = os.environ.copy()
    env['TMPDIR'] = str(private_tmp)
    for key in ('GEOMETRY_MODEL_BASE', 'GEOMETRY_TEST_BRIDGE', 'GEOMETRY_ENGINEERING_BRIDGE', 'GEOMETRY_TEST_ENGINEERING_JSON', 'GEOMETRY_TEST_CORE'):
        env.pop(key, None)
    command = ['python3', '-u', str(EVIDENCE / 'exercise-region-edges.py'), str(root), str(out), mode]
    with (out / 'unittest.log').open('xb') as log:
        run = subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
    after = manifest(root)
    (out / 'source-after.json').write_text(json.dumps(after, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    test = json.loads((out / 'test-result.json').read_text()) if (out / 'test-result.json').exists() else {}
    failed = {name.rsplit('.', 1)[-1] for name in test.get('failed_tests', [])}
    no_infrastructure_failure = test.get('errors') == 0 and test.get('skipped') == [] and test.get('expected_failures') == 0 and test.get('unexpected_successes') == 0
    expected_outcome = (run.returncode == 1 and test.get('tests_run') == 6 and failed == EXPECTED_FAILURES and test.get('failures') == 5) if mode == 'old' else (run.returncode == 0 and test.get('tests_run') == 8 and test.get('successful') is True)
    summary = {'kind': 'frozen-old-expected-red' if mode == 'old' else 'fixed-new-regression-and-removal-controls',
               'product_source': source, 'judge_source': NEW, 'source_root': str(root), 'archive_sha256': sha(archive),
               'original_product_preserved': expected_overlay_only, 'judge_only_added_files': overlay_receipt,
               'started_utc': start, 'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'command': command, 'raw_test_exit': run.returncode, 'test_result': test,
               'expected_outcome_observed': expected_outcome and no_infrastructure_failure,
               'expected_red_test_names': sorted(EXPECTED_FAILURES) if mode == 'old' else [],
               'source_unchanged_after_tests': before == after, 'source_files': len(before),
               'source_before_sha256': sha(out / 'source-before.json'), 'source_after_sha256': sha(out / 'source-after.json'),
               'log_sha256': sha(out / 'unittest.log'), 'shared_lock_holder': Path('/run/lock/ga-wsl-v3.holder').read_text(),
               'runner_sha256': {name: sha(EVIDENCE / name) for name in ('run-region-edges.py', 'exercise-region-edges.py')},
               'full_suite_executed': False, 'browser_executed': False,
               'exit': 0 if expected_outcome and no_infrastructure_failure and before == after else 1}
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out / 'exit.txt').write_text(str(summary['exit']) + '\n', encoding='ascii')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary['exit']

codes = [run_case('old', OLD), run_case('new', NEW)]
sys.exit(0 if codes == [0, 0] else 1)
