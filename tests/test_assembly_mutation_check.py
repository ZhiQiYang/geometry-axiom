"""The parts of tests/assembly_mutation_check.py that need no compiler.

The tool compiles one bridge per phase and runs only on Linux/WSL, outside run_all. What can be checked anywhere is
checked here: every case and control is bound to a live, unique assertion and an anchor that still occurs once; the
verdict rules reject every outcome that is not "exactly the tagged assertion of the killer test failed"; the result
recorder keeps tags, errors, skips and bridge deaths apart. The real fault builds, including the negative controls,
are the tool's own run (receipt in geometry-web/docs/ASSEMBLY-RULES-VALIDATION.md).
"""
import importlib.util
import io
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_tool():
    spec = importlib.util.spec_from_file_location('assembly_mutation_check_under_test', ROOT / 'tests/assembly_mutation_check.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BridgeDied(AssertionError):
    """Shaped like tests/_bridge.py::BridgeClosed, which is an AssertionError carrying these two attributes."""
    bridge_closed = True
    returncode = -6


class AssemblyMutationCheck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = load_tool()
        cls.text = cls.tool.read_lf(ROOT, cls.tool.TEST_FILE)

    def test_cases_and_controls_are_bound_to_live_assertions_and_anchors(self):
        self.assertEqual([], self.tool.static_problems())
        self.assertEqual({'conflict', 'missing-source', 'cancelled-preview'}, {case[0] for case in self.tool.CASES})
        self.assertEqual({'wrong-assertion', 'bridge-closed', 'error', 'timeout', 'survived'},
                         {control[3] for control in self.tool.CONTROLS})

    def test_verdict_rules_reject_everything_but_the_exact_assertion(self):
        self.assertEqual([], self.tool.selftest())

    def test_the_legacy_criterion_called_a_different_assertion_killed_and_the_judge_does_not(self):
        tool = self.tool
        log = ('FAIL: test_cancel_and_protocol_tokens_do_not_commit\nTraceback (most recent call last):\n'
               '    self.assertTrue(self.command(f"assembly-cancel {token}")["cancelled"])\n'
               'AssertionError: False is not true\n\nFAILED (failures=1)\n')
        test = tool.TEST_PREFIX + 'test_cancel_and_protocol_tokens_do_not_commit'
        other = dict(test=test, tags=[], exception='builtins.AssertionError', bridgeClosed=False, frames=[])
        obs = dict(exit=1, timeout=False, result=dict(run=1, failures=[other], errors=[], skipped=[], expectedFailures=[],
                                                      unexpectedSuccesses=[], reached=[]))
        self.assertTrue(tool.legacy_killed(1, log))
        self.assertEqual(('not-killed', 'wrong-assertion'),
                         tool.judge_mutant(obs, [test], test, 'cancelled-preview:confirm-after-cancel'))
        exact = dict(other, tags=['cancelled-preview:confirm-after-cancel'])
        obs['result']['failures'] = [exact]
        self.assertEqual(('killed', 'exact-assertion'),
                         tool.judge_mutant(obs, [test], test, 'cancelled-preview:confirm-after-cancel'))

    def test_binding_problems_name_a_missing_moved_or_duplicated_tag_or_test(self):
        tool = self.tool
        text = self.text
        self.assertEqual([], tool.binding_problems(text))
        renamed = text.replace('"conflict:scope"', '"conflict:renamed"')
        self.assertTrue(any('conflict:scope' in p and 'exactly once' in p for p in tool.binding_problems(renamed)))
        duplicated = text + '\nSTRAY = "conflict:scope"\n'
        self.assertTrue(any('conflict:scope' in p and 'exactly once' in p for p in tool.binding_problems(duplicated)))
        moved = text.replace('("scope", "conflict:scope")', '("scope", "conflict:other")').replace(
            'killer("cancelled-preview:confirm-after-cancel")', 'killer("conflict:scope")')
        problems = tool.binding_problems(moved)
        self.assertTrue(any(p.startswith('conflict:') and 'is not inside' in p for p in problems), problems)
        missing = [(name, patches, 'test_does_not_exist', tag) for name, patches, _, tag in tool.CASES]
        self.assertTrue(all(any('not defined exactly once' in p and name in p for p in tool.binding_problems(text, missing))
                            for name, *_ in tool.CASES))
        clash = [tool.CASES[0], (tool.CASES[1][0], tool.CASES[1][1], tool.CASES[1][2], tool.CASES[0][3])]
        self.assertTrue(any('claimed by more than one case' in p for p in tool.binding_problems(text, clash, [])))
        self.assertTrue(any('unknown reason' in p for p in tool.binding_problems(
            text, controls=[('c', [('f', 'a', 'b')], 'conflict', 'not-a-reason')])))

    def test_anchor_problems_report_an_anchor_that_moved(self):
        tool = self.tool
        moved = [(name, [(f, before + '\x00', after) for f, before, after in patches], test, tag)
                 for name, patches, test, tag in tool.CASES]
        problems = tool.anchor_problems(ROOT, moved, [])
        self.assertEqual({case[0] for case in tool.CASES}, {p.split(':')[0] for p in problems})
        self.assertTrue(all('occurs 0 times' in p for p in problems))

    def test_recorder_keeps_tags_errors_skips_bridge_deaths_and_subtests_apart(self):
        class Sample(unittest.TestCase):
            def test_tagged(self):
                self.assertFalse(True, 'KILLER[t:a] {"ok": true}')

            def test_plain_failure(self):
                self.assertTrue(False)

            def test_error(self):
                raise ValueError('boom')

            def test_skip(self):
                self.skipTest('no bridge')

            def test_bridge_died(self):
                raise BridgeDied('bridge closed: exit status -6')

            def test_subtest(self):
                with self.subTest('x'):
                    self.assertEqual(1, 2, 'KILLER[t:b]')

            def test_passes(self):
                pass

        stream = io.StringIO()
        result = unittest.TextTestRunner(stream=stream, resultclass=self.tool.recording_result_class()).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Sample))
        records = result.records
        by_test = lambda key: {item['test'].rsplit('.', 1)[1]: item for item in records[key]}
        failures = by_test('failures')
        self.assertEqual({'test_tagged', 'test_plain_failure', 'test_bridge_died', 'test_subtest'}, set(failures))
        self.assertEqual(['t:a'], failures['test_tagged']['tags'])
        self.assertEqual([], failures['test_plain_failure']['tags'])
        self.assertEqual(['t:b'], failures['test_subtest']['tags'])
        self.assertTrue(failures['test_subtest']['subtest'].endswith('[x]'), failures['test_subtest']['subtest'])
        self.assertTrue(failures['test_bridge_died']['bridgeClosed'])
        self.assertEqual(-6, failures['test_bridge_died']['returncode'])
        self.assertFalse(failures['test_tagged']['bridgeClosed'])
        self.assertEqual('test_tagged', failures['test_tagged']['frames'][-1]['function'])
        self.assertEqual(['test_error'], list(by_test('errors')))
        self.assertEqual('builtins.ValueError', by_test('errors')['test_error']['exception'])
        self.assertEqual(['test_skip'], list(by_test('skipped')))
        self.assertEqual(7, result.testsRun)

    def test_killer_message_records_the_tag_even_when_the_assertion_passes(self):
        sys.path.insert(0, str(ROOT))
        from tests import test_assembly_rules as module
        module.REACHED.discard('probe:tag')
        self.assertEqual('KILLER[probe:tag] detail', module.killer('probe:tag', 'detail'))
        self.assertEqual('KILLER[probe:tag]', module.killer('probe:tag'))
        self.assertIn('probe:tag', module.REACHED)
        self.assertEqual(['probe:tag'], self.tool.TAG.findall(module.killer('probe:tag', {'ok': False})))
        module.REACHED.discard('probe:tag')


if __name__ == '__main__':
    unittest.main()
