"""在CI跑原覆蓋測試：基準綠、拿掉某片一個suite為正常AssertionError紅、恢復綠。"""
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
mode, output = sys.argv[1:]
removed = []
if mode == 'drop-one-suite':
    original = run_all.partition_suites
    def mutated(suites, count, weights=None):
        parts = original(suites, count, weights)
        removed.append(parts[0].pop(0).name)
        return parts
    run_all.partition_suites = mutated
suite = unittest.defaultTestLoader.loadTestsFromName('test_unittest_runner.NativeShardCoverage.test_partition_covers_actual_suite_registry_once')
result = unittest.TextTestRunner(verbosity=2).run(suite)
row = dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
           skips=len(result.skipped), failure_ids=[case.id() for case,_ in result.failures],
           assertion_failure=all('AssertionError' in text for _,text in result.failures), removed=removed)
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
    receipt = dict(passed=True, baseline_mutant_restored_exit=[r['exit'] for r in rows], rows=rows)
    (args.output/'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
