#!/usr/bin/env python3
"""The --only / --group selection guard of tests/section_profile_mutation_check.py.

No native binary, no compile: every case here stops at argument validation, before the gate builds anything.

Why it is pinned: a selection that picks no case never builds a baseline, no mutant is judged, and ``all([])`` is True,
so a mistyped ``--only`` id used to exit 0 without testing anything (PR #182 review).  Unknown ids and an empty
selection must exit 2 and say why; legal selections must still pass validation.  What a legal subset does once it
reaches the baseline (compile, run, judge) is the gate's own Linux/WSL job and is not repeated here.
"""
from __future__ import annotations

from pathlib import Path
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
