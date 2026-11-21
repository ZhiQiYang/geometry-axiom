"""R06 native baseline keeps every test and its original per-child deadline."""
import ast
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))
import bay_repeat_mutation_check as runner


class NativeBaselinePartition(unittest.TestCase):
    def setUp(self):
        self.manifest = runner.load_manifest()
        tree = ast.parse((runner.ROOT / runner.NATIVE_FILE).read_text(encoding='utf-8'))
        native = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'BayRepeat')
        self.names = [runner.PREFIX + node.name for node in native.body
                      if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')]

    def receipt(self, names):
        tags = [tag for tag, name in self.manifest['nativeTags'].items() if runner.PREFIX + name in names]
        return dict(exit=0, timeout=False, processGroup=dict(pid=123, pgid=123),
                    result=dict(selected=list(names), executed=list(names), run=len(names), failures=[], errors=[],
                                skipped=[], expectedFailures=[], unexpectedSuccesses=[], reached=tags,
                                python=sys.version.split()[0]))

    def run_native(self, change=None, selected=None):
        calls = []
        def observe(directory, argv, root, env, timeout):
            directory.mkdir(parents=True, exist_ok=True)
            names = argv[6:]
            calls.append(dict(directory=directory, argv=argv, root=root, env=env, timeout=timeout, names=names))
            value = self.receipt(names)
            if change is not None:
                change(value, len(calls) - 1)
            return value
        with tempfile.TemporaryDirectory(prefix='r06-native-partitions-') as directory, \
                patch.object(runner, 'observation', side_effect=observe):
            value = runner.run_oracle('native', runner.ROOT, Path(directory), {}, self.manifest,
                                      selected=selected, timeout=120, binary='control-bridge')
        return value, calls

    def assert_full_plan(self, calls):
        self.assertEqual([37, 11, 7], [len(call['names']) for call in calls])
        self.assertEqual(self.names, [name for call in calls for name in call['names']])
        self.assertEqual(55, len(set(name for call in calls for name in call['names'])))
        self.assertEqual([False, True, False],
                         [all(name.rsplit('.', 1)[1].startswith('test_br11_') for name in call['names']) for call in calls])
        self.assertEqual([120] * 3, [call['timeout'] for call in calls])
        self.assertEqual(3, len({call['directory'] for call in calls}))
        self.assertEqual(3, len({call['argv'][5] for call in calls}))

    def test_native_baseline_keeps_all_55_in_source_order_with_three_original_deadlines(self):
        value, calls = self.run_native()
        self.assert_full_plan(calls)
        untagged = set(self.names) - {runner.PREFIX + name for name in self.manifest['nativeTags'].values()}
        self.assertEqual(5, len(untagged))
        self.assertTrue(untagged <= set(value['result']['selected']))
        self.assertEqual(self.names, value['result']['selected'])
        self.assertEqual(self.names, value['result']['executed'])
        self.assertEqual(55, value['result']['run'])
        self.assertEqual(('pass', 'green'), runner.oracle.judge_pass(value, self.names, list(self.manifest['nativeTags'])))

    def test_explicit_single_native_selection_stays_one_child(self):
        for name in (self.names[0], self.names[37]):
            with self.subTest(name=name):
                value, calls = self.run_native(selected=[name])
                self.assertEqual(1, len(calls))
                self.assertEqual([name], calls[0]['names'])
                self.assertEqual(120, calls[0]['timeout'])
                self.assertEqual([name], value['result']['executed'])

    def test_selected_mutant_preserves_its_exact_red_assertion(self):
        case = next(case for case in self.manifest['cases'] if case['kind'] == 'native')
        def fail(value, index):
            value['exit'] = 1
            value['result']['failures'] = [dict(test=case['test'], tags=[case['assertion']], bridgeClosed=False)]
        value, calls = self.run_native(fail, selected=[case['test']])
        self.assertEqual(1, len(calls))
        self.assertEqual(('killed', 'exact-assertion'),
                         runner.oracle.judge_mutant(value, [case['test']], case['test'], case['assertion']))

    def test_empty_explicit_native_selection_cannot_expand_to_the_full_baseline(self):
        def observe_child(directory, argv, root, env, timeout):
            directory.mkdir(parents=True, exist_ok=True)
            return self.receipt(argv[6:])
        with tempfile.TemporaryDirectory(prefix='r06-native-empty-') as directory, \
                patch.object(runner, 'observation', side_effect=observe_child) as observe:
            with self.assertRaises(ValueError):
                runner.run_oracle('native', runner.ROOT, Path(directory), {}, self.manifest,
                                  selected=[], timeout=120, binary='control-bridge')
            observe.assert_not_called()

    def test_each_native_child_must_report_exact_selected_and_executed_identities(self):
        changes = {
            'missing': lambda result, field: result.pop(field),
            'omitted-test': lambda result, field: result[field].pop(),
            'duplicate-test': lambda result, field: result[field].__setitem__(-1, result[field][0]),
            'wrong-test': lambda result, field: result[field].__setitem__(0, runner.PREFIX + 'test_not_selected'),
            'wrong-order': lambda result, field: result[field].reverse(),
        }
        for field in ('selected', 'executed'):
            for name, change in changes.items():
                for child in range(3):
                    with self.subTest(field=field, change=name, child=child):
                        def corrupt(value, index):
                            if index == child:
                                change(value['result'], field)
                        value, _ = self.run_native(corrupt)
                        self.assertNotEqual('pass', runner.oracle.judge_pass(value, self.names, list(self.manifest['nativeTags']))[0])

    def test_native_child_failure_error_skip_or_timeout_cannot_be_hidden_by_other_children(self):
        for field in ('failures', 'errors', 'skipped', 'expectedFailures', 'unexpectedSuccesses', 'timeout'):
            for child in range(3):
                with self.subTest(field=field, child=child):
                    def corrupt(value, index):
                        if index == child:
                            if field == 'timeout':
                                value['timeout'] = True
                            else:
                                value['result'][field] = [dict(test=value['result']['selected'][0])]
                    value, _ = self.run_native(corrupt)
                    self.assertNotEqual('pass', runner.oracle.judge_pass(value, self.names, list(self.manifest['nativeTags']))[0])

    def test_native_receipt_requires_integer_counts_exit_and_literal_false_timeout(self):
        changes = [('exit', False), ('exit', 0.0), ('exit', '0'), ('exit', 1),
                   ('timeout', 0), ('run', True), ('run', 1.0), ('run', '1'), ('run', -1)]
        for field, replacement in changes:
            for child in range(3):
                with self.subTest(field=field, replacement=replacement, child=child):
                    def corrupt(value, index):
                        if index == child:
                            target = value['result'] if field == 'run' else value
                            target[field] = float(target[field]) if field == 'run' and replacement == 1.0 and type(replacement) is float else replacement
                    value, _ = self.run_native(corrupt)
                    self.assertNotEqual('pass', runner.oracle.judge_pass(value, self.names, list(self.manifest['nativeTags']))[0])

    def test_native_outcome_and_reached_fields_keep_their_strict_list_shape(self):
        changes = [(field, replacement) for field in ('failures', 'errors', 'skipped', 'expectedFailures', 'unexpectedSuccesses')
                   for replacement in ({}, None)]
        changes += [('reached', 'not-a-tag-list'), ('reached', [None])]
        for field, replacement in changes:
            with self.subTest(field=field, replacement=replacement):
                def corrupt(value, index):
                    if index == 0:
                        value['result'][field] = replacement
                value, _ = self.run_native(corrupt)
                self.assertNotEqual('pass', runner.oracle.judge_pass(value, self.names, list(self.manifest['nativeTags']))[0])
        def duplicate_tag(value, index):
            if index == 0:
                value['result']['reached'].append(value['result']['reached'][0])
        value, _ = self.run_native(duplicate_tag)
        self.assertNotEqual('pass', runner.oracle.judge_pass(value, self.names, list(self.manifest['nativeTags']))[0])

    def test_native_tag_cannot_be_borrowed_from_another_partition(self):
        for child in range(3):
            with self.subTest(missing_tag_in_child=child):
                def drop_tag(value, index):
                    if index == child:
                        value['result']['reached'].pop()
                value, _ = self.run_native(drop_tag)
                self.assertNotEqual('pass', runner.oracle.judge_pass(value, self.names, list(self.manifest['nativeTags']))[0])
        def add_unlisted_tag(value, index):
            if index == 0:
                value['result']['reached'].append('control:unlisted-tag')
        value, _ = self.run_native(add_unlisted_tag)
        self.assertNotEqual('pass', runner.oracle.judge_pass(value, self.names, list(self.manifest['nativeTags']))[0])
        tag = next(tag for tag, name in self.manifest['nativeTags'].items() if runner.PREFIX + name == self.names[37])
        def move_tag(value, index):
            if index == 0:
                value['result']['reached'].append(tag)
            elif index == 1:
                value['result']['reached'].remove(tag)
        value, _ = self.run_native(move_tag)
        self.assertNotEqual('pass', runner.oracle.judge_pass(value, self.names, list(self.manifest['nativeTags']))[0])

    def test_one_mutation_case_still_runs_full_baseline_and_full_restored_plan(self):
        case = next(case for case in self.manifest['cases'] if case['kind'] == 'native')
        calls = []
        def observe(directory, argv, root, env, timeout):
            directory.mkdir(parents=True, exist_ok=True)
            names = argv[6:]
            calls.append(dict(directory=directory, argv=argv, names=names, timeout=timeout))
            value = self.receipt(names)
            if argv[4] == 'mutant-bridge':
                value['exit'] = 1
                value['result']['failures'] = [dict(test=case['test'], tags=[case['assertion']], bridgeClosed=False)]
            return value
        def compile_control(root, directory, env, registry=False):
            kind = 'mutant' if 'cases' in directory.parts else 'baseline'
            return dict(path=kind + '-bridge', sha256=kind)
        with tempfile.TemporaryDirectory(prefix='r06-native-lifecycle-') as directory, \
                patch.object(runner, 'observation', side_effect=observe), \
                patch.object(runner, 'compile_native', side_effect=compile_control), \
                patch.object(runner, 'apply_patches', return_value={}), \
                patch.object(runner.oracle, 'tree_hashes', return_value={}):
            phase = runner.run_kind('native', [case], runner.ROOT, Path(directory) / 'phase', {}, self.manifest, 120)
        self.assertTrue(phase['ok'], phase)
        self.assertEqual(7, len(calls))
        self.assert_full_plan(calls[:3])
        self.assertEqual([case['test']], calls[3]['names'])
        self.assertEqual(120, calls[3]['timeout'])
        self.assert_full_plan(calls[4:])

    def test_native_child_records_the_tests_that_actually_started(self):
        requested = runner.PREFIX + 'test_control_requested'
        started = runner.PREFIX + 'test_control_actually_started'
        module = SimpleNamespace(find_bridge=lambda: None, REACHED=set())
        class Control(unittest.TestCase):
            def id(self):
                return started
            def runTest(self):
                module.REACHED.add('control:started')
                self.assertEqual(1, 1)
        with tempfile.TemporaryDirectory(prefix='r06-native-started-') as directory, \
                patch.object(runner.importlib, 'import_module', return_value=module), \
                patch.object(runner.unittest.defaultTestLoader, 'loadTestsFromNames', return_value=unittest.TestSuite([Control()])):
            destination = Path(directory) / 'result.json'
            code = runner.native_child(['unused-control-bridge', str(destination), requested])
            result = json.loads(destination.read_text(encoding='utf-8'))
        self.assertEqual(0, code)
        self.assertEqual([started], result.get('executed'))
        self.assertEqual([requested], result['selected'])
        self.assertEqual(['control:started'], result['reached'])


if __name__ == '__main__':
    unittest.main()
