"""The parts of tests/assembly_mutation_check.py that need no compiler.

The tool compiles one bridge per phase and runs only on Linux/WSL, outside run_all. What can be checked anywhere is
checked here: every killer tag of the test file is listed once and no unlisted one exists; every case and control is
bound to a live, unique assertion and an anchor that still occurs once; the baseline asks for all the listed tags, not
only the cases'; the verdict rules reject every outcome that is not "exactly the tagged assertion of the killer test
failed" and name an unchanged binary; the result recorder keeps tags, errors, skips and bridge deaths apart; what is
left of a timed-out process group is looked up and judged. The real fault builds, including the negative controls,
are the tool's own run (receipt in geometry-web/docs/ASSEMBLY-RULES-VALIDATION.md).
"""
import importlib.util
import io
import os
from pathlib import Path
import sys
import tempfile
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
        self.assertEqual({'wrong-assertion', 'bridge-closed', 'error', 'timeout', 'survived', 'identical-binary'},
                         {control[3] for control in self.tool.CONTROLS})
        self.assertEqual(8, len(self.tool.TAGS))
        self.assertLessEqual({case[3] for case in self.tool.CASES}, set(self.tool.TAGS))

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

    def test_a_tag_that_no_case_is_bound_to_cannot_be_deleted_repeated_moved_or_added_unnoticed(self):
        tool, text = self.tool, self.text
        unbound = sorted(set(tool.TAGS) - {case[3] for case in tool.CASES})
        self.assertEqual(['conflict:end', 'missing-source:application', 'missing-source:literal-negative',
                          'missing-source:material', 'missing-source:parameter'], unbound)
        for tag in unbound:
            with self.subTest(tag=tag):
                gone = tool.binding_problems(text.replace('"%s"' % tag, '"gone"'))
                self.assertTrue(any(p.startswith(tag + ':') and 'exactly once' in p and 'found 0' in p for p in gone), gone)
                twice = tool.binding_problems(text + '\nSTRAY = "%s"\n' % tag)
                self.assertTrue(any(p.startswith(tag + ':') and 'exactly once' in p and 'found 2' in p for p in twice), twice)
        # moved into another test: the literal exists once, in the wrong method
        moved = text.replace('"conflict:end"', '"gone"').replace('"missing-source:application"', '"conflict:end"')
        problems = tool.binding_problems(moved)
        self.assertTrue(any(p.startswith('conflict:end:') and 'is not inside' in p for p in problems), problems)
        self.assertTrue(any(p.startswith('missing-source:application:') and 'found 0' in p for p in problems), problems)
        # a new tag nobody listed, and a killer() call whose argument cannot be listed
        problems = tool.binding_problems(text + '\nNEW = "conflict:brand-new"\n')
        self.assertTrue(any(p.startswith('conflict:brand-new:') and 'not listed in TAGS' in p for p in problems), problems)
        for call in ('killer("no colon")', 'killer(name)', 'killer(f"conflict:{1}")', 'killer()'):
            problems = tool.binding_problems(text + '\nPROBE = %s\n' % call)
            self.assertTrue(any('killer() needs a family:name tag literal' in p for p in problems), (call, problems))
        # a case may only be bound to a listed tag, and to the method that holds it
        stray = [(name, patches, test, 'conflict:unlisted') for name, patches, test, tag in tool.CASES[:1]]
        self.assertTrue(any('not listed in TAGS' in p for p in tool.binding_problems(text, stray, [])))
        other = [(name, patches, tool.CANCEL_TEST, tag) for name, patches, test, tag in tool.CASES[:1]]
        self.assertTrue(any('TAGS puts tag conflict:scope in' in p for p in tool.binding_problems(text, other, [])))

    def test_the_baseline_has_to_reach_every_listed_tag_and_nothing_else(self):
        tool = self.tool
        killers, tags = tool.baseline_selection()
        self.assertEqual(set(tool.TAGS), set(tags))
        self.assertGreater(len(tags), len(tool.CASES))
        self.assertEqual({tool.TEST_PREFIX + test for test in tool.TAGS.values()}, set(killers))
        self.assertLessEqual({tool.TEST_PREFIX + case[2] for case in tool.CASES}, set(killers))

        def green(reached):
            return dict(exit=0, timeout=False, result=dict(run=len(killers), failures=[], errors=[], skipped=[],
                                                            expectedFailures=[], unexpectedSuccesses=[], reached=reached))
        self.assertEqual(('pass', 'green'), tool.judge_pass(green(sorted(tags)), killers, tags))
        only_cases = sorted(case[3] for case in tool.CASES)
        self.assertEqual(('fail', 'killer-not-reached'), tool.judge_pass(green(only_cases), killers, tags))
        for tag in tags:
            with self.subTest(missing=tag):
                self.assertEqual(('fail', 'killer-not-reached'),
                                 tool.judge_pass(green(sorted(set(tags) - {tag})), killers, tags))
        self.assertEqual(('fail', 'unlisted-tag-reached'), tool.judge_pass(green(sorted(tags) + ['x:y']), killers, tags))

    def test_a_comment_only_control_is_judged_identical_binary_and_changes_nothing_else(self):
        tool, text = self.tool, self.text
        control = next(c for c in tool.CONTROLS if c[3] == 'identical-binary')
        name, patches, target, reason = control[:4]
        self.assertEqual('conflict', target)
        # the patch is a comment on the anchor's own line: strip comments and the file is the one it was, line for line
        for relative, before, after in patches:
            original = tool.read_lf(ROOT, relative)
            patched = original.replace(before, after, 1)
            self.assertNotEqual(original, patched)
            self.assertEqual(original.count('\n'), patched.count('\n'))
            self.assertEqual(tool.COMMENT.sub('', original), tool.COMMENT.sub('', patched))
        # a patch that does more, or moves a line, is refused as an identical-binary control
        relative, before, after = patches[0]
        for bad in ('if(false)', after + ';', after + '\n', before + '/* a\nb */'):
            with self.subTest(after=bad):
                problems = tool.binding_problems(text, controls=[(name, [(relative, before, bad)], target, reason)])
                self.assertTrue(any('may only add a /* */ comment' in p for p in problems), problems)
        # the verdict does not depend on what the test did, only on the digests
        same = dict(exit=0, timeout=False, result=None, binary='abc', baselineBinary='abc')
        self.assertEqual(('not-killed', 'identical-binary'), tool.judge_mutant(same, ['t'], 't', 'a:b'))
        self.assertEqual(('not-killed', 'child-crash'), tool.judge_mutant(dict(same, binary='abd'), ['t'], 't', 'a:b'))

    def test_what_is_left_of_a_killed_process_group_is_looked_up_and_a_leftover_is_a_problem(self):
        tool = self.tool
        self.assertEqual(dict(pid=42, comm='a b) (c', state='Z', pgrp=7, session=8),
                         tool.parse_proc_stat('42 (a b) (c) Z 1 7 8 0 -1 4194560 0 0\n'))
        for bad in ('', 'garbage', '42 name S 1 7 8', '42 (x) S 1', 'x (x) S 1 7 8 0', '42 (x) S 1 q 8 0'):
            self.assertIsNone(tool.parse_proc_stat(bad), bad)
        with tempfile.TemporaryDirectory() as directory:
            proc = Path(directory)

            def add(pid, comm, state, pgrp, session, cmdline=b''):
                (proc / str(pid)).mkdir()
                (proc / str(pid) / 'stat').write_text('%d (%s) %s 1 %d %d 0 -1 0\n' % (pid, comm, state, pgrp, session))
                (proc / str(pid) / 'cmdline').write_bytes(cmdline)
            add(100, 'python3', 'S', 100, 100, b'python3\0-B\0')
            add(101, 'bridge', 'R', 100, 100)
            add(102, 'moved off', 'S', 102, 100)       # left the group, still in the session
            add(103, 'zombie', 'Z', 100, 100)
            add(200, 'other', 'S', 200, 200)
            (proc / '300').mkdir()                      # no stat: it exited while we looked
            (proc / 'self').mkdir()
            found = tool.group_members(100, proc)
            self.assertEqual([100, 101, 102, 103], [item['pid'] for item in found])
            self.assertEqual('python3 -B', found[0]['cmdline'])
            self.assertEqual('Z', found[3]['state'])
            self.assertEqual([], tool.group_members(999, proc))
            self.assertIsNone(tool.group_members(100, proc / 'missing'))

        clock = [0.0]

        def sleep(seconds):
            clock[0] += seconds
        answers = iter([[dict(pid=1)], [dict(pid=1)], []])
        remaining, waited = tool.wait_group_gone(5, timeout=1.0, interval=0.25, members=lambda pgid: next(answers),
                                                 sleep=sleep, clock=lambda: clock[0])
        self.assertEqual(([], 0.5), (remaining, waited))
        clock[0] = 0.0
        remaining, waited = tool.wait_group_gone(5, timeout=1.0, interval=0.25, members=lambda pgid: [dict(pid=1)],
                                                 sleep=sleep, clock=lambda: clock[0])
        self.assertEqual(([dict(pid=1)], 1.0), (remaining, waited))
        self.assertEqual((None, 0.0), tool.wait_group_gone(5, members=lambda pgid: None, sleep=sleep, clock=lambda: 0.0))

        clean = dict(pgid=5, checked=True, beforeKill=[dict(pid=5)], afterKill=[], secondsUntilGone=0.0)
        self.assertEqual([], tool.group_problems(dict(id='baseline')))
        self.assertEqual([], tool.group_problems(dict(id='control-hang', processGroup=clean)))
        left = dict(clean, afterKill=[dict(pid=9, comm='bridge', state='R')])
        problems = tool.group_problems(dict(id='control-hang', processGroup=left))
        self.assertEqual(1, len(problems), problems)
        self.assertIn('still running after the timeout kill', problems[0])
        self.assertIn('9[bridge R]', problems[0])
        self.assertTrue(tool.group_problems(dict(id='control-hang', processGroup=dict(clean, checked=False))))
        self.assertTrue(tool.group_problems(dict(id='x', buildProcessGroup=left)))

    def test_run_logged_kills_the_whole_group_and_records_that_nothing_is_left(self):
        if os.name != 'posix' or not Path('/proc/self/stat').is_file():
            # Needs POSIX process groups and /proc; the tool itself refuses to run elsewhere.  A bare `return` here
            # would report a pass for a test that checked nothing, so the skip is explicit and named in
            # tests/run_all.py ALLOWED_SKIPS (Windows only: any other platform that lands here stays a visible skip).
            self.skipTest('requires POSIX process groups and /proc (Linux/WSL/CI run it)')
        tool = self.tool
        with tempfile.TemporaryDirectory() as directory:
            where = Path(directory)
            code, timed_out, group = tool.run_logged(['sh', '-c', 'sleep 30 & sleep 30; wait'], where / 'hang', where,
                                                     dict(os.environ), 2)
            self.assertEqual((None, True), (code, timed_out))
            self.assertTrue(group['checked'])
            self.assertGreaterEqual(len(group['beforeKill']), 2, group)     # the shell and a child of it
            self.assertEqual([], group['afterKill'])
            self.assertEqual([], tool.group_members(group['pgid']))
            self.assertEqual([], tool.group_problems(dict(id='probe', processGroup=group)))
            written = tool.json.loads((where / 'hang' / 'execution.json').read_text(encoding='utf-8'))
            self.assertEqual(group, written['processGroup'])
            code, timed_out, group = tool.run_logged(['sh', '-c', 'exit 3'], where / 'quick', where, dict(os.environ), 30)
            self.assertEqual((3, False, None), (code, timed_out, group))


if __name__ == '__main__':
    unittest.main()
