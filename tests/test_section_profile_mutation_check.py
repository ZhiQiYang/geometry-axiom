#!/usr/bin/env python3
"""Selection guards and adversarial exception-evidence checks for the section-profile mutation gate.

No native binary or compile: CLI selection cases stop at argument validation; runner fixtures use Python only.

Why it is pinned: a selection that picks no case never builds a baseline, no mutant is judged, and ``all([])`` is True,
so a mistyped ``--only`` id used to exit 0 without testing anything (PR #182 review).  Unknown ids and an empty
selection must exit 2 and say why; legal selections must still pass validation.  What a legal subset does once it
reaches the baseline (compile, run, judge) is the gate's own Linux/WSL job and is not repeated here.
"""
from __future__ import annotations

from pathlib import Path
from copy import deepcopy
import inspect
import os
import json
import tempfile
import subprocess
import sys
import unittest

try:
    from tests import section_profile_mutation_check as gate
except ModuleNotFoundError:
    import section_profile_mutation_check as gate

SCRIPT = Path(gate.__file__).resolve()
BOTH = ['native', 'model']
SILENT_SUCCESS = ('exit 0 means the mistyped selection was taken as a success: no case was selected, so no baseline '
                  'ran and all([]) reported success')


def run(*args):
    return subprocess.run([sys.executable, '-I', str(SCRIPT), *args], capture_output=True, text=True,
                          encoding='utf-8', errors='replace', timeout=120)


def why(result):
    head = SILENT_SUCCESS if result.returncode == 0 else 'unexpected exit %d' % result.returncode
    return '%s; stdout=%r stderr=%r' % (head, result.stdout[-300:], result.stderr[-300:])


def ids(cases):
    return [case['id'] for case in cases]


class SelectionGuardCli(unittest.TestCase):
    def test_mistyped_id_exits_2_and_lists_the_valid_ids(self):
        for typo in ('SPM3', 'spm03', 'SPM99', 'SPM003', ''):
            with self.subTest(only=typo):
                result = run('--only', typo)
                self.assertEqual(result.returncode, 2, why(result))
                self.assertIn('unknown --only case id', result.stderr, why(result))
                self.assertIn(repr(typo), result.stderr)
                self.assertIn('SPM01', result.stderr)   # the valid ids are listed
                self.assertIn('SPM42', result.stderr)
                self.assertNotIn('baseline', result.stdout)

    def test_one_mistyped_id_among_legal_ones_rejects_the_whole_run(self):
        # --list stops right after the selection, so even a broken guard cannot start a real compile-and-mutate run here
        result = run('--list', '--only', 'SPM03', '--only', 'SPM3x', '--group', 'native')
        self.assertEqual(result.returncode, 2, why(result))
        self.assertIn("'SPM3x'", result.stderr)
        self.assertNotIn("'SPM03'", result.stderr)      # the legal id is not blamed
        self.assertEqual(result.stdout, '')             # and no partial list or run was produced

    def test_selection_outside_the_chosen_group_is_empty_and_rejected(self):
        for only, group, owner in (('SPM36', 'native', 'model'), ('SPM01', 'model', 'native')):
            with self.subTest(only=only, group=group):
                result = run('--only', only, '--group', group)
                self.assertEqual(result.returncode, 2, why(result))
                self.assertIn('no case selected', result.stderr, why(result))
                self.assertIn('%s is in group %s' % (only, owner), result.stderr)
                self.assertNotIn('baseline', result.stdout)

    def test_the_guard_also_applies_to_list(self):
        result = run('--list', '--only', 'SPM3')
        self.assertEqual(result.returncode, 2, 'a mistyped id must not be ignored just because --list was given: ' + why(result))
        self.assertIn("'SPM3'", result.stderr)

    def test_legal_ids_still_pass_validation(self):
        result = run('--list', '--only', 'SPM03', '--only', 'SPM41')
        self.assertEqual(result.returncode, 0, result.stderr[-300:])
        self.assertIn('SPM03', result.stdout)
        self.assertIn('SPM41', result.stdout)


class ExceptionEvidence(unittest.TestCase):
    def setUp(self):
        self.case = deepcopy(next(c for c in gate.CASES if c['id'] == 'SPM08'))
        self.name = gate.NATIVE_MODULE + '.' + gate.NATIVE_CLASS + '.' + gate.PANEL
        self.cause = self.case['cause'][0]

    def event(self, message, kind='failure', exception_type='builtins.AssertionError', name=None, subtest=None):
        return dict(test_id=name or self.name, subtest_id=subtest, kind=kind,
                    exception_type=exception_type, message=message)

    def receipt(self, events):
        names = list(dict.fromkeys(e['test_id'] for e in events)) or [self.name]
        return dict(schema='section-profile-exceptions/1', requested=names, executed=names,
                    passed=[] if events else names, tests_run=len(names),
                    failures=sum(e['kind']=='failure' for e in events), errors=sum(e['kind']=='error' for e in events),
                    skipped=0, expected_failures=0, unexpected_successes=0, events=events)

    def judge(self, events, log=None, code=1, receipt=None):
        evidence = self.receipt(events) if receipt is None else receipt
        if log is None:
            log = ''.join('%s: %s (fixture)\n%s\n' %
                          ('FAIL' if e['kind']=='failure' else 'ERROR', e['test_id'].split('.')[-1], e['message'])
                          for e in events)
        # Also run these counterexamples against the historical three-argument matcher in fault-injection probes.
        if 'evidence' in inspect.signature(gate.verdict).parameters:
            return gate.verdict(self.case, code, log, evidence)
        return gate.verdict(self.case, code, log)

    def test_keyerror_cannot_borrow_cause_from_traceback_source(self):
        event = self.event("'rect'", 'error', 'builtins.KeyError')
        log = 'ERROR: %s (fixture)\n  self.assertEqual(p["rect"], "%s")\nKeyError: \'rect\'\n' % (gate.PANEL, self.cause)
        self.assertNotEqual(self.judge([event], log)['verdict'], 'killed')

    def test_stdout_cannot_supply_missing_exception_cause(self):
        event = self.event('unrelated assertion')
        log = '%s\nFAIL: %s (fixture)\nAssertionError: unrelated assertion\n' % (self.cause, gate.PANEL)
        self.assertNotEqual(self.judge([event], log)['verdict'], 'killed')

    def test_other_method_cannot_supply_cause_to_expected_method(self):
        events = [self.event('unrelated assertion'), self.event(self.cause, name=self.name.replace(gate.PANEL, gate.GEOM))]
        self.assertNotEqual(self.judge(events)['verdict'], 'killed')

    def test_causes_must_all_belong_to_one_exception_including_subtests(self):
        self.case = deepcopy(next(c for c in gate.CASES if c['id']=='SPM03'))
        self.name = gate.NATIVE_MODULE+'.'+gate.NATIVE_CLASS+'.'+gate.TOUCH
        events = [self.event(text, subtest=self.name+' (part=%d)' % i) for i,text in enumerate(self.case['cause'])]
        self.assertNotEqual(self.judge(events)['verdict'], 'killed')

    def test_error_type_requires_explicit_case_allowlist(self):
        self.assertNotEqual(self.judge([self.event(self.cause, 'error', 'builtins.ValueError')])['verdict'], 'killed')

    def test_missing_evidence_is_blocked(self):
        log = 'FAIL: %s (fixture)\nAssertionError: %s\n' % (gate.PANEL, self.cause)
        self.assertNotEqual(gate.verdict(self.case, 1, log)['verdict'], 'killed')

    def test_duplicate_terminal_records_are_blocked(self):
        e = self.event(self.cause)
        self.assertNotEqual(self.judge([e, deepcopy(e)])['verdict'], 'killed')

    def test_malformed_record_is_blocked(self):
        e = self.event(self.cause); e['message'] = [self.cause]
        self.assertNotEqual(self.judge([e], log='FAIL: %s (fixture)\n%s\n' % (gate.PANEL,self.cause))['verdict'], 'killed')

    def test_exit_and_exception_counts_must_agree(self):
        e = self.event(self.cause)
        self.assertNotEqual(self.judge([e], code=0)['verdict'], 'killed')
        evidence = self.receipt([e]); evidence['errors']=1
        self.assertNotEqual(self.judge([e], receipt=evidence)['verdict'], 'killed')

    def test_missing_or_duplicate_executed_method_is_blocked(self):
        e = self.event(self.cause)
        for names in ([], [self.name,self.name]):
            with self.subTest(names=names):
                evidence=self.receipt([e]); evidence['executed']=names
                self.assertNotEqual(self.judge([e], receipt=evidence)['verdict'], 'killed')

    def test_multiline_assertion_keeps_cause_after_three_hundred_characters(self):
        message = 'difference\n'+'x'*350+'\n'+self.cause
        self.assertEqual(self.judge([self.event(message)])['verdict'], 'killed')

    def test_case_declared_modelerror_is_detection(self):
        self.case = deepcopy(next(c for c in gate.CASES if c['id']=='SPM38'))
        self.name = gate.MODEL_MODULE+'.'+gate.MODEL_CLASS+'.'+gate.MLONG
        self.assertEqual(self.judge([self.event(self.case['cause'][0], 'error', 'modeling.common.ModelError')])['verdict'], 'killed')

    def test_wrong_method_with_cause_is_not_the_killer(self):
        self.assertNotEqual(self.judge([self.event(self.cause, name=self.name.replace(gate.PANEL, gate.GEOM))])['verdict'], 'killed')

    def test_same_method_name_from_another_module_is_not_the_killer(self):
        self.assertNotEqual(self.judge([self.event(self.cause, name='other.Fixture.'+gate.PANEL)])['verdict'], 'killed')

    def test_spm41_named_assertion_still_detects(self):
        self.case = deepcopy(next(c for c in gate.CASES if c['id']=='SPM41'))
        self.name = gate.NATIVE_MODULE+'.'+gate.NATIVE_CLASS+'.'+gate.CONCAVE
        self.assertEqual(self.judge([self.event(self.case['cause'][0])])['verdict'], 'killed')

    def test_skips_cannot_be_detection(self):
        e=self.event(self.cause); evidence=self.receipt([e]); evidence['skipped']=1
        self.assertNotEqual(self.judge([e], receipt=evidence)['verdict'], 'killed')


class ExceptionCollector(unittest.TestCase):
    def run_fixture(self, name):
        fixture = '''import sys,unittest
sys.path.insert(0, %r)
from modeling.common import ModelError
class Fixture(unittest.TestCase):
    def test_multiline(self):
        self.fail('begin\\n'+'x'*350+'\\nterminal cause')
    def test_model_error(self):
        raise ModelError('INVALID','PROFILE_VOLUME','R37','terminal cause')
    def test_subtests(self):
        with self.subTest(part=1):self.fail('first cause')
        with self.subTest(part=2):raise KeyError('second cause')
''' % str(SCRIPT.parents[1]/'geometry-core')
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp,'fixture.py').write_text(fixture)
            code,log,evidence=gate.run_child(['fixture.Fixture.'+name],Path(tmp),dict(os.environ),timeout=10)
        self.assertEqual(code,1,log)
        self.assertIsNone(gate.evidence_problem(code,evidence))
        return evidence

    def test_collector_preserves_full_multiline_exception(self):
        evidence=self.run_fixture('test_multiline')
        e=evidence['events'][0]
        self.assertEqual(e['exception_type'],'builtins.AssertionError')
        self.assertEqual(e['message'],'begin\n'+'x'*350+'\nterminal cause')

    def test_collector_preserves_actual_module_qualified_modelerror(self):
        e=self.run_fixture('test_model_error')['events'][0]
        self.assertEqual(e['kind'],'error')
        self.assertEqual(e['exception_type'],'modeling.common.ModelError')
        self.assertIn('terminal cause',e['message'])

    def test_subtests_keep_separate_terminal_exception_identities(self):
        evidence=self.run_fixture('test_subtests')
        self.assertEqual((evidence['tests_run'],evidence['failures'],evidence['errors']),(1,1,1))
        self.assertEqual([e['kind'] for e in evidence['events']],['failure','error'])
        self.assertEqual(len({e['subtest_id'] for e in evidence['events']}),2)
        self.assertEqual({e['test_id'] for e in evidence['events']},{'fixture.Fixture.test_subtests'})

    def test_missing_receipt_and_duplicate_json_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp,'exceptions.json')
            self.assertIn('invalid_receipt',gate.read_evidence(path,['fixture.test']))
            path.write_text('{"requested":["fixture.test"],"schema":"a","schema":"b"}')
            evidence=gate.read_evidence(path,['fixture.test'])
            self.assertIn('duplicate JSON key',evidence['invalid_receipt'])
            self.assertIsNotNone(gate.evidence_problem(1,evidence))
            path.write_text(json.dumps({'requested':['other.test']}))
            self.assertIn('requested methods differ',gate.read_evidence(path,['fixture.test'])['invalid_receipt'])


class SelectCases(unittest.TestCase):
    def test_every_legal_id_selects_exactly_that_case(self):
        for case in gate.CASES:
            with self.subTest(id=case['id']):
                self.assertEqual(ids(gate.select_cases([case['id']], BOTH)), [case['id']])
                self.assertEqual(ids(gate.select_cases([case['id']], [case['group']])), [case['id']])

    def test_no_only_selects_all_cases_of_the_groups(self):
        self.assertEqual(gate.select_cases([], BOTH), gate.CASES)
        model = gate.select_cases([], ['model'])
        self.assertTrue(model)
        self.assertEqual(ids(model), [c['id'] for c in gate.CASES if c['group'] == 'model'])

    def test_a_legal_subset_keeps_declaration_order_and_drops_duplicates(self):
        self.assertEqual(ids(gate.select_cases(['SPM04', 'SPM03', 'SPM03'], ['native'])), ['SPM03', 'SPM04'])

    def test_unknown_id_and_empty_selection_raise(self):
        for only, groups, text in ((['SPM3'], BOTH, 'unknown --only case id'),
                                   (['SPM03', 'nope'], ['native'], 'unknown --only case id'),
                                   (['SPM36'], ['native'], 'no case selected')):
            with self.subTest(only=only, groups=groups):
                with self.assertRaises(ValueError) as caught:
                    gate.select_cases(only, groups)
                self.assertIn(text, str(caught.exception))


if __name__ == '__main__':
    unittest.main()
