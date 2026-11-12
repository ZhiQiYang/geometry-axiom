"""在CI用真覆蓋／預算測試反證：各具名撤回必須正常AssertionError紅，恢復綠。"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys

PROGRAM = r'''
import json, pathlib, sys, unittest
sys.path.insert(0, str(pathlib.Path('tests').resolve()))
import run_all
import native_shards
mode, output = sys.argv[1:]
removed = []
target = 'test_unittest_runner.NativeShardCoverage.test_partition_covers_actual_suite_registry_once'
if mode in ('drop-one-suite', 'R348_FOUR_SHARD_DROP_ONE_SUITE', 'R378_SIX_SHARD_DROP_ONE_SUITE'):
    original = run_all.partition_suites
    only = {'R348_FOUR_SHARD_DROP_ONE_SUITE': 4, 'R378_SIX_SHARD_DROP_ONE_SUITE': 6}.get(mode)
    def mutated(suites, count, weights=None):
        parts = original(suites, count, weights)
        if mode == 'drop-one-suite' or count == only:
            removed.append(parts[0].pop(0).name)
        return parts
    run_all.partition_suites = mutated
# R378: anchors follow the current six-shard workflow. The R348 names keep
# their original meaning (revert to three shards, drop the fourth entry, ...);
# R378 adds the revert-to-four and fifth/sixth-entry withdrawals.
workflow_replacements = {
    'R348_REVERT_TO_THREE_NATIVE_SHARDS': [
        ('matrix.shard }}/6', 'matrix.shard }}/3'),
        ('max-parallel: 6', 'max-parallel: 3'),
        ('shard: [1, 2, 3, 4, 5, 6]', 'shard: [1, 2, 3]'),
        ('--parts 6', '--parts 3')],
    'R348_REVERT_NATIVE_JOB_NAME': [('name: native (${{ matrix.shard }}/6)',
                                    'name: native (${{ matrix.shard }}/3)')],
    'R348_REVERT_NATIVE_RUNNER_DENOMINATOR': [("--shard '${{ matrix.shard }}/6'",
                                             "--shard '${{ matrix.shard }}/3'")],
    'R348_DROP_FOURTH_MATRIX_ENTRY': [('shard: [1, 2, 3, 4, 5, 6]', 'shard: [1, 2, 3, 5, 6]')],
    'R348_REVERT_COVERAGE_PARTS': [('--parts 6', '--parts 3')],
    'R348_RELAX_NATIVE_JOB_TIMEOUT': [('timeout-minutes: 35', 'timeout-minutes: 36')],
    'R378_REVERT_TO_FOUR_NATIVE_SHARDS': [
        ('matrix.shard }}/6', 'matrix.shard }}/4'),
        ('max-parallel: 6', 'max-parallel: 4'),
        ('shard: [1, 2, 3, 4, 5, 6]', 'shard: [1, 2, 3, 4]'),
        ('--parts 6', '--parts 4')],
    'R378_REVERT_NATIVE_JOB_NAME_TO_FOUR': [('name: native (${{ matrix.shard }}/6)',
                                            'name: native (${{ matrix.shard }}/4)')],
    'R378_REVERT_RUNNER_DENOMINATOR_TO_FOUR': [("--shard '${{ matrix.shard }}/6'",
                                              "--shard '${{ matrix.shard }}/4'")],
    'R378_REVERT_MAX_PARALLEL_TO_FOUR': [('max-parallel: 6', 'max-parallel: 4')],
    'R378_DROP_FIFTH_MATRIX_ENTRY': [('shard: [1, 2, 3, 4, 5, 6]', 'shard: [1, 2, 3, 4, 6]')],
    'R378_DROP_SIXTH_MATRIX_ENTRY': [('shard: [1, 2, 3, 4, 5, 6]', 'shard: [1, 2, 3, 4, 5]')],
    'R378_REVERT_COVERAGE_PARTS_TO_FOUR': [('--parts 6', '--parts 4')],
}
evidence_modes = ('R348_DROP_LATEST_MEASURED_RUN', 'R348_REWRITE_RETAINED_MEASUREMENT',
                  'R348_LOWER_LATEST_MEASUREMENT', 'R378_DROP_ADDED_SCENARIO',
                  'R378_LOWER_ADDED_SCENARIO', 'R378_RELABEL_ADDED_SCENARIO_AS_MAIN')
if (mode in ('measured-baseline', 'R348_REVERT_MEASURED_PROFILE', 'R348_REMOVE_SCENARIO_SWAP',
             'R380_REVERT_SINGLE_PAIR_SWEEP', 'R380_DROP_ADDED_SUITE_EVIDENCE',
             'R380_REMOVE_MULTISTART_SCREENING')
        or mode in workflow_replacements or mode in evidence_modes):
    target = 'test_unittest_runner.NativeShardCoverage.test_profile_balances_measured_work'
if mode == 'R348_REVERT_MEASURED_PROFILE':
    original = native_shards.partition_suites
    def legacy(suites, count, weights=None):
        if weights is None:
            weights = native_shards.timing_weights()
            profile = json.loads(native_shards.TIMINGS.read_text(encoding='utf-8'))
            weights.update({name: row['planning_weight_ms']
                            for name, row in profile['supplemental'].items()})
        return original(suites, count, weights)
    native_shards.partition_suites = legacy
elif mode == 'R348_REMOVE_SCENARIO_SWAP':
    native_shards._improve_scenarios = lambda parts, loads, costs: None
elif mode == 'R380_REVERT_SINGLE_PAIR_SWEEP':
    native_shards._improve_scenarios = native_shards._swap_scenarios
elif mode == 'R380_REMOVE_MULTISTART_SCREENING':
    def single_start(parts, loads, costs):
        for _ in range(2):
            native_shards._swap_scenarios(parts, loads, costs)
        for _ in range(4):
            native_shards._exchange_scenarios(parts, loads, costs)
            native_shards._swap_scenarios(parts, loads, costs)
    native_shards._improve_scenarios = single_start
elif mode == 'R380_DROP_ADDED_SUITE_EVIDENCE':
    native_shards.added_suite_costs = lambda: {}
if mode in workflow_replacements or mode in evidence_modes:
    # Mutate only this child's in-memory file read; never rewrite the checkout.
    original_read = pathlib.Path.read_text
    workflow_path = pathlib.Path('.github/workflows/integration-tests.yml').resolve()
    timings_path = native_shards.TIMINGS.resolve()
    def mutated_read(path, *args, **kwargs):
        value = original_read(path, *args, **kwargs)
        if mode in workflow_replacements and path.resolve() == workflow_path:
            for before, after in workflow_replacements[mode]:
                if before not in value:
                    raise RuntimeError('mutation anchor missing: ' + before)
                value = value.replace(before, after)
        elif mode in evidence_modes and path.resolve() == timings_path:
            profile = json.loads(value)
            if mode == 'R348_DROP_LATEST_MEASURED_RUN':
                # Original meaning: drop the d7515daf run (index 2).
                profile['measured_runs'].pop(2)
            elif mode == 'R378_DROP_ADDED_SCENARIO':
                profile['measured_runs'].pop(3)
            elif mode == 'R378_LOWER_ADDED_SCENARIO':
                profile['measured_runs'][3]['shards'][1]['timings_ms']['py:test_model_update'] = 1
            elif mode == 'R378_RELABEL_ADDED_SCENARIO_AS_MAIN':
                profile['measured_runs'][3]['source_checkout'] = 'f3ee80cf07a548089bfe705e50c93fc7632d8720'
            elif mode == 'R348_LOWER_LATEST_MEASUREMENT':
                profile['measured_runs'][2]['shards'][0]['timings_ms']['py:test_geo261_timber_capacity_host'] = 1
            else:
                profile['measured_runs'][0]['source_checkout'] = '0' * 40
            value = json.dumps(profile)
        return value
    pathlib.Path.read_text = mutated_read
suite = unittest.defaultTestLoader.loadTestsFromName(target)
result = unittest.TextTestRunner(verbosity=2).run(suite)
markers = ('R348_MEASURED_RECEIPT_BUDGET', 'R378_SIX_NATIVE_WORKFLOW',
           'R348_RETAINED_MEASURED_EVIDENCE', 'R348_FOUR_SHARDS_COVER_FULL_REGISTRY',
           'R378_SIX_SHARDS_COVER_FULL_REGISTRY',
           'R380_NEW_SUITES_HAVE_INDEPENDENT_CI_RECEIPTS')
row = dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
           skips=len(result.skipped), failure_ids=[case.id() for case,_ in result.failures],
           assertion_failure=all('AssertionError' in text for _,text in result.failures), removed=removed,
           budget_failure=all('R348_MEASURED_RECEIPT_BUDGET' in text for _,text in result.failures),
           failure_markers=[marker for marker in markers
                            if result.failures and all(marker in text for _, text in result.failures)])
pathlib.Path(output).write_text(json.dumps(row, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
raise SystemExit(0 if result.wasSuccessful() else 1)
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    rows = []
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8')
    for label, mode, expected in [('baseline','baseline',0), ('removed','drop-one-suite',1), ('restored','baseline',0)]:
        report, log = args.output/(label+'.json'), args.output/(label+'.log')
        with log.open('wb') as stream:
            result = subprocess.run([sys.executable, '-B', '-c', PROGRAM, mode, str(report.resolve())],
                                    env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=60)
        row = json.loads(report.read_text(encoding='utf-8'))
        assert result.returncode == expected and row['tests'] == 1 and row['errors'] == row['skips'] == 0, row
        assert row['failures'] == expected, row
        if expected:
            assert len(row['removed']) == 1 and row['assertion_failure']
            assert row['failure_ids'] == ['test_unittest_runner.NativeShardCoverage.test_partition_covers_actual_suite_registry_once']
        rows.append(dict(label=label, exit=result.returncode, **row))
    timing_proofs = {}
    mutations = {
        'R348_REVERT_MEASURED_PROFILE': ('measured-baseline', 'R348_MEASURED_RECEIPT_BUDGET'),
        'R348_REMOVE_SCENARIO_SWAP': ('measured-baseline', 'R348_MEASURED_RECEIPT_BUDGET'),
        'R380_REVERT_SINGLE_PAIR_SWEEP': ('measured-baseline', 'R348_MEASURED_RECEIPT_BUDGET'),
        'R380_REMOVE_MULTISTART_SCREENING': ('measured-baseline', 'R348_MEASURED_RECEIPT_BUDGET'),
        'R380_DROP_ADDED_SUITE_EVIDENCE': ('measured-baseline', 'R380_NEW_SUITES_HAVE_INDEPENDENT_CI_RECEIPTS'),
        'R348_REVERT_TO_THREE_NATIVE_SHARDS': ('measured-baseline', 'R348_MEASURED_RECEIPT_BUDGET'),
        'R348_REVERT_NATIVE_JOB_NAME': ('measured-baseline', 'R378_SIX_NATIVE_WORKFLOW'),
        'R348_REVERT_NATIVE_RUNNER_DENOMINATOR': ('measured-baseline', 'R378_SIX_NATIVE_WORKFLOW'),
        'R348_DROP_FOURTH_MATRIX_ENTRY': ('measured-baseline', 'R378_SIX_NATIVE_WORKFLOW'),
        'R348_REVERT_COVERAGE_PARTS': ('measured-baseline', 'R378_SIX_NATIVE_WORKFLOW'),
        'R348_RELAX_NATIVE_JOB_TIMEOUT': ('measured-baseline', 'R378_SIX_NATIVE_WORKFLOW'),
        'R348_DROP_LATEST_MEASURED_RUN': ('measured-baseline', 'R348_RETAINED_MEASURED_EVIDENCE'),
        'R348_REWRITE_RETAINED_MEASUREMENT': ('measured-baseline', 'R348_RETAINED_MEASURED_EVIDENCE'),
        'R348_LOWER_LATEST_MEASUREMENT': ('measured-baseline', 'R348_RETAINED_MEASURED_EVIDENCE'),
        'R348_FOUR_SHARD_DROP_ONE_SUITE': ('baseline', 'R348_FOUR_SHARDS_COVER_FULL_REGISTRY'),
        'R378_REVERT_TO_FOUR_NATIVE_SHARDS': ('measured-baseline', 'R348_MEASURED_RECEIPT_BUDGET'),
        'R378_REVERT_NATIVE_JOB_NAME_TO_FOUR': ('measured-baseline', 'R378_SIX_NATIVE_WORKFLOW'),
        'R378_REVERT_RUNNER_DENOMINATOR_TO_FOUR': ('measured-baseline', 'R378_SIX_NATIVE_WORKFLOW'),
        'R378_REVERT_MAX_PARALLEL_TO_FOUR': ('measured-baseline', 'R378_SIX_NATIVE_WORKFLOW'),
        'R378_DROP_FIFTH_MATRIX_ENTRY': ('measured-baseline', 'R378_SIX_NATIVE_WORKFLOW'),
        'R378_DROP_SIXTH_MATRIX_ENTRY': ('measured-baseline', 'R378_SIX_NATIVE_WORKFLOW'),
        'R378_REVERT_COVERAGE_PARTS_TO_FOUR': ('measured-baseline', 'R378_SIX_NATIVE_WORKFLOW'),
        'R378_DROP_ADDED_SCENARIO': ('measured-baseline', 'R348_RETAINED_MEASURED_EVIDENCE'),
        'R378_LOWER_ADDED_SCENARIO': ('measured-baseline', 'R348_RETAINED_MEASURED_EVIDENCE'),
        'R378_RELABEL_ADDED_SCENARIO_AS_MAIN': ('measured-baseline', 'R348_RETAINED_MEASURED_EVIDENCE'),
        'R378_SIX_SHARD_DROP_ONE_SUITE': ('baseline', 'R378_SIX_SHARDS_COVER_FULL_REGISTRY'),
    }
    def prove(mutation, baseline, marker):
        # Each named proof stays strictly sequential: baseline, withdrawn, restored.
        proof = []
        for label, mode, expected in [('baseline', baseline, 0),
                                      ('withdrawn', mutation, 1), ('restored', baseline, 0)]:
            stem = mutation + '-' + label
            report, log = args.output/(stem+'.json'), args.output/(stem+'.log')
            with log.open('wb') as stream:
                result = subprocess.run([sys.executable, '-B', '-c', PROGRAM, mode, str(report.resolve())],
                                        env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=60)
            row = json.loads(report.read_text(encoding='utf-8'))
            assert result.returncode == expected and row['tests'] == 1 and row['errors'] == row['skips'] == 0, row
            assert bool(row['failures']) == bool(expected), row
            if expected:
                assert row['assertion_failure'] and marker in row['failure_markers'], row
                method = ('test_partition_covers_actual_suite_registry_once' if baseline == 'baseline'
                          else 'test_profile_balances_measured_work')
                assert all(name.startswith('test_unittest_runner.NativeShardCoverage.' + method)
                           for name in row['failure_ids']), row
            proof.append(dict(label=label, exit=result.returncode, **row))
        return dict(baseline_mutant_restored_exit=[r['exit'] for r in proof], rows=proof)

    # R378: independent named proofs run on up to four worker processes so the
    # unchanged 5-minute coverage job still fits; every child keeps its own
    # 60 s limit, its own log/report, and the receipt keeps the declared order.
    with ThreadPoolExecutor(max_workers=max(1, min(4, os.cpu_count() or 1))) as pool:
        futures = {mutation: pool.submit(prove, mutation, baseline, marker)
                   for mutation, (baseline, marker) in mutations.items()}
        for mutation in mutations:
            timing_proofs[mutation] = futures[mutation].result()
    receipt = dict(passed=True, baseline_mutant_restored_exit=[r['exit'] for r in rows], rows=rows,
                   timing_proofs=timing_proofs)
    (args.output/'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
