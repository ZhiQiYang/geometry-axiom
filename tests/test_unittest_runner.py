"""One parent test guards the reporter's synthetic outcome matrix (#118)."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import argparse
from collections import Counter
import contextlib
import io
import json
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
import run_all
from native_shards import parse_shard, partition_suites, timing_weights, validate_partition
from native_shard_receipts import validate_rows


class RunnerClassification(unittest.TestCase):
    def test_synthetic_parent_outcomes(self):
        verifier = Path(__file__).parent / 'runner_classification' / 'verify.py'
        env = {key: value for key, value in os.environ.items() if not key.startswith('GEOMETRY_')}
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        with tempfile.TemporaryDirectory(prefix='geometry-runner-classification-') as temp:
            result = subprocess.run([sys.executable, str(verifier), '--out', str(Path(temp) / 'receipts')],
                                    env=env, capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class NativeShardCoverage(unittest.TestCase):
    def test_partition_covers_actual_suite_registry_once(self):
        suites = run_all.build_suites()
        expected, error = run_all.load_expected()
        self.assertFalse(error)
        parts = run_all.partition_suites(suites, 3)
        actual = Counter(s.name for part in parts for s in part)
        self.assertEqual(actual, Counter({name:1 for name in expected['suites']}),
                         '分片必須完整涵蓋原套件清單，且每個suite恰好一次')
        self.assertEqual(sum(map(len, parts)), len(suites))

    def test_partition_is_deterministic(self):
        suites = run_all.build_suites()
        first = partition_suites(suites, 3)
        second = partition_suites(suites, 3)
        self.assertEqual([[s.name for s in p] for p in first], [[s.name for s in p] for p in second])
        reverse = partition_suites(list(reversed(suites)), 3)
        self.assertEqual([set(s.name for s in p) for p in first], [set(s.name for s in p) for p in reverse])

    def test_profile_balances_measured_work(self):
        suites = run_all.build_suites()
        weights = timing_weights()
        parts = partition_suites(suites, 3, weights)
        loads = [sum(weights.get(s.name, 1000) for s in part) for part in parts]
        self.assertLess(max(loads), 600000, '固定main實測配置應低於每片10分鐘，留建置與新套件餘量')
        self.assertLessEqual(max(loads)-min(loads), max(weights.values()))
        # Keep the historical 224-row and supplemental relative-weight checks.
        current_parts = partition_suites(suites, 3)
        owners = {s.name: i for i, part in enumerate(current_parts) for s in part}
        self.assertNotEqual(owners['py:test_geo261_timber_capacity_host'],
                            owners['py:test_axiom_reader'], 'R348_SHARD_H7_READER_SEPARATION')
        profile = json.loads((Path(__file__).parent / 'native_shard_timings.json').read_text(encoding='utf-8'))
        current_weights = dict(weights)
        current_weights.update({name: row['planning_weight_ms']
                                for name, row in profile.get('supplemental', {}).items()})
        historical_parts = partition_suites(suites, 3, current_weights)
        current_loads = [sum(current_weights.get(s.name, 1000) for s in p) for p in historical_parts]
        self.assertLess(max(current_loads), 650000, 'R348_SHARD_SUPPLEMENTAL_PROFILE_CEILING')
        # Replay both complete measurements independently against the production
        # plan. The raw maximum overhead is 92.195s: reserve 100s plus 30s margin.
        runs = profile['measured_runs']
        self.assertEqual([r['source_run'].rsplit('/', 1)[-1] for r in runs],
                         ['43162989157', '43150038015'])
        for run in runs:
            with self.subTest(source_run=run['source_run']):
                measured = {name: ms for shard in run['shards']
                            for name, ms in shard['timings_ms'].items()}
                self.assertEqual(sum(len(s['timings_ms']) for s in run['shards']), len(measured))
                self.assertEqual(len(measured), run['suite_count'])
                self.assertEqual(set(measured), {s.name for s in suites},
                                 'R348_MEASURED_PROFILE_COVERS_REGISTRY')
                replay = [sum(measured[s.name] for s in part) for part in current_parts]
                self.assertLess(max(replay) + 100000 + 30000, 1200000,
                                'R348_MEASURED_RECEIPT_BUDGET')

    def test_invalid_shards_are_rejected(self):
        for value in ['0/2', '1/0', '4/3', 'a/2', '1/2/3', '-1/3']:
            with self.subTest(value=value), self.assertRaises(argparse.ArgumentTypeError):
                parse_shard(value)
        self.assertEqual(parse_shard('2/3'), (2, 3))

    def test_shards_cannot_update_or_filter_expected(self):
        for extra in [['--only', 'bridge'], ['--extra-py', 'unused.py'],
                      ['--simulate-missing', 'GEOMETRY_MODEL_BASE'], ['--update-expected']]:
            with self.subTest(extra=extra), mock.patch.object(run_all, 'run') as child, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(run_all.main(['--shard', '1/3', *extra]), 2)
                child.assert_not_called()

    def test_partition_rejects_missing_duplicate_and_unknown(self):
        suites = [SimpleNamespace(name=n) for n in ['a', 'b', 'c']]
        for parts in [[suites[:1], suites[2:]], [suites, suites[:1]],
                      [suites, [SimpleNamespace(name='unknown')]]]:
            with self.subTest(parts=parts), self.assertRaisesRegex(ValueError, '分片聯集'):
                validate_partition(suites, parts)

    def test_orphan_expected_entry_is_rejected_for_shard(self):
        selected = [run_all.Suite('a', 'unittest', [])]
        universe = selected + [run_all.Suite('b', 'unittest', [])]
        expected = {'suites': {n:{'mode':'count', 'count':1} for n in ['a', 'b', 'orphan']}}
        row = run_all.Row('a'); row.ran = True; row.total = row.passed = 1
        problems = run_all.compare_expected([row], selected, expected, '', False, universe=universe)
        self.assertEqual([name for name, _ in problems], ['orphan'])

    def test_selected_count_mismatch_is_rejected(self):
        suites = [run_all.Suite('a', 'unittest', [])]
        row = run_all.Row('a'); row.ran = True; row.total = row.passed = 1
        problems = run_all.compare_expected([row], suites, {'suites':{'a':{'mode':'count','count':2}}},
                                            '', False, universe=suites)
        self.assertEqual([name for name, _ in problems], ['a'])
        self.assertTrue(row.expected_problem)

    def test_cross_shard_report_requires_all_rows(self):
        row = vars(run_all.Row('a')); row.update(ran=True, total=1, passed=1, process_exit_code=0)
        expected = {'a':{'mode':'count','count':1}, 'b':{'mode':'count','count':1}}
        with self.assertRaisesRegex(ValueError, '缺少或重複suite'):
            validate_rows(['a','b'], [row], expected)

    def test_cross_shard_report_rejects_inconsistent_counters(self):
        row = vars(run_all.Row('a')); row.update(ran=True, total=1, passed=0, process_exit_code=0)
        with self.assertRaisesRegex(ValueError, '計數不守恆'):
            validate_rows(['a'], [row], {'a':{'mode':'count','count':1}})

    def test_inventory_keeps_zero_assertions_and_requires_real_child_exit(self):
        suite = next(s for s in run_all.build_suites() if s.name == 'mutation:check')
        expected = {suite.name:{'mode':'exit-code-only'}}
        with tempfile.TemporaryDirectory(prefix='geometry-inventory-exit-') as temp:
            with mock.patch.object(run_all, 'LOG_DIR', Path(temp)):
                for code in [0, 1, 2, -11, None, False]:
                    with mock.patch.object(run_all, 'run_process',
                                           return_value=run_all.ProcResult(code, '', 0.0, False)):
                        observed = json.loads(json.dumps(run_all.report_row(run_all.run_suite(suite, {}, {}))))
                    self.assertEqual(observed['process_exit_code'], code)
                    self.assertIs(type(observed['process_exit_code']), type(code))
                    if type(code) is int and code == 0:
                        row = observed
                    else:
                        with self.assertRaisesRegex(ValueError, '子行程退出碼'):
                            validate_rows([suite.name], [observed], expected)
        self.assertEqual(row['process_exit_code'], 0)
        self.assertEqual([row[k] for k in ['total', 'passed', 'failed', 'skipped']], [0, 0, 0, 0])
        validate_rows([suite.name], [row], expected)
        for code in [1, 2, -11, None, False]:
            with self.subTest(code=code), self.assertRaisesRegex(ValueError, '子行程退出碼'):
                validate_rows([suite.name], [dict(row, process_exit_code=code)], expected)
        missing = dict(row); missing.pop('process_exit_code')
        with self.assertRaisesRegex(ValueError, '子行程退出碼'):
            validate_rows([suite.name], [missing], expected)
        with self.assertRaisesRegex(ValueError, '僅退出碼'):
            validate_rows([suite.name], [dict(row, passed=1)], expected)
        script = dict(row, name='oracle:framing-selftest')
        with self.assertRaisesRegex(ValueError, '僅退出碼'):
            validate_rows([script['name']], [script], {script['name']:{'mode':'exit-code-only'}})
        validate_rows([script['name']], [dict(script, passed=1)],
                      {script['name']:{'mode':'exit-code-only'}})


if __name__ == '__main__':
    unittest.main()
