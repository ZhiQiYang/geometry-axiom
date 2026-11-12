"""在CI用真覆蓋／預算測試反證：各具名撤回必須正常AssertionError紅，恢復綠。"""
import argparse
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
if mode == 'drop-one-suite':
    original = run_all.partition_suites
    def mutated(suites, count, weights=None):
        parts = original(suites, count, weights)
        removed.append(parts[0].pop(0).name)
        return parts
    run_all.partition_suites = mutated
if mode in ('measured-baseline', 'R348_REVERT_MEASURED_PROFILE', 'R348_REMOVE_SCENARIO_SWAP'):
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
suite = unittest.defaultTestLoader.loadTestsFromName(target)
result = unittest.TextTestRunner(verbosity=2).run(suite)
row = dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
           skips=len(result.skipped), failure_ids=[case.id() for case,_ in result.failures],
           assertion_failure=all('AssertionError' in text for _,text in result.failures), removed=removed,
           budget_failure=all('R348_MEASURED_RECEIPT_BUDGET' in text for _,text in result.failures))
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
    for mutation in ['R348_REVERT_MEASURED_PROFILE', 'R348_REMOVE_SCENARIO_SWAP']:
        proof = []
        for label, mode, expected in [('baseline', 'measured-baseline', 0),
                                      ('withdrawn', mutation, 1), ('restored', 'measured-baseline', 0)]:
            stem = mutation + '-' + label
            report, log = args.output/(stem+'.json'), args.output/(stem+'.log')
            with log.open('wb') as stream:
                result = subprocess.run([sys.executable, '-B', '-c', PROGRAM, mode, str(report.resolve())],
                                        env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=60)
            row = json.loads(report.read_text(encoding='utf-8'))
            assert result.returncode == expected and row['tests'] == 1 and row['errors'] == row['skips'] == 0, row
            assert bool(row['failures']) == bool(expected), row
            if expected:
                assert row['assertion_failure'] and row['budget_failure'], row
                assert all(name.startswith('test_unittest_runner.NativeShardCoverage.test_profile_balances_measured_work')
                           for name in row['failure_ids']), row
            proof.append(dict(label=label, exit=result.returncode, **row))
        timing_proofs[mutation] = dict(baseline_mutant_restored_exit=[r['exit'] for r in proof], rows=proof)
    receipt = dict(passed=True, baseline_mutant_restored_exit=[r['exit'] for r in rows], rows=rows,
                   timing_proofs=timing_proofs)
    (args.output/'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
