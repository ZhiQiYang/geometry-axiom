"""O467 fragment contract: original definitions, real registration and closure.

Missing implementation fails at a named assertion, never at import time.
These tests do not manufacture mutation execution receipts.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import sys
from types import SimpleNamespace
import unittest
from unittest import mock

import mutate
import mutation_bridge

ROOT = Path(__file__).resolve().parents[1]
LEGACY_SHA = '6b425d427e0cf20b2cc48114d8cb2d93e39c1db3c094f93bc7d74441d2a63725'
RESTORED_SHA = '4318545a163731c5bebb83d2ee352224a01174260b2392c20f37efa71ed6c5e4'
IDS = {
    'R03_MAIN_CONTINUOUS', 'R03_NOT_CENTERED', 'R03_ONLY_OPPOSITE_WALL_TRIM',
    'R03_CEIL_MARKS', 'R03_CANCEL_ZERO_WRITE', 'R03A_FIXED_JIG',
    'R03A_LAST_TWO_STEPS_SPLIT', 'R03A_REJECT_WRITES',
    'R03A_CONFIRM_DIFFERENT_CANDIDATE', 'R03_MARK_GUIDE_FREEZES_GRID_SOURCE',
    'PF6_O_FINAL_POST_GEOMETRY', 'PF6_O_LIVE_DIMENSION_BINDING',
    'PF6_O_NUMERIC_EDGE_ORDER', 'PF6_O_RECEIPT_FINAL_HASH',
    'PF6_O_REUSED_ID', 'PF6_O_SELECTED_SET_ONLY',
}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':')).encode()


class MutationFragments(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='o467-fragments-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'tests/mutants.d').mkdir(parents=True)
        (self.root / 'product.c').write_text('int guard = 1;\n', encoding='utf-8')
        self.row = dict(id='O467_EXAMPLE', desc='Executable assertion control',
                        binary='bridge', file='product.c', old='int guard = 1;',
                        new='int guard = 0;',
                        tests=['tests.test_example.Example.test_guard'],
                        expected_assertion='O467_GUARD', reason='Guard rejection is observable.')

    def write(self, row=None, name=None):
        row = deepcopy(self.row if row is None else row)
        path = self.root / 'tests/mutants.d' / ((name or row['id']) + '.json')
        path.write_bytes(canonical(row) + b'\n')
        return path

    @property
    def loader(self):
        path = ROOT / 'tests/mutation_fragments.py'
        self.assertTrue(path.is_file(), 'O467_FRAGMENT_LOADER_AVAILABLE')
        spec = importlib.util.spec_from_file_location('o467_fragment_test', path)
        loader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(loader)
        return loader

    def load(self, legacy=()):
        return self.loader.load_fragments(self.root, legacy)

    def test_original_152_and_new_16_form_exact_complete_union(self):
        self.assertEqual((168, 74, 94), (len(mutate.MUTANTS),
            sum(row.get('binary') != 'bridge' for row in mutate.MUTANTS),
            sum(row.get('binary') == 'bridge' for row in mutate.MUTANTS)), 'O467_NATIVE_COUNTS')
        legacy = list(getattr(mutate, 'LEGACY_MUTANTS', ()))
        self.assertEqual(152, len(legacy), 'O467_LEGACY_152_PRESERVED')
        self.assertEqual(LEGACY_SHA, hashlib.sha256(canonical(legacy)).hexdigest(),
                         'O467_LEGACY_DEFINITIONS_AND_ORDER_UNCHANGED')
        fragments = self.loader.load_fragments(ROOT, legacy)
        self.assertEqual(IDS, {row['id'] for row in fragments}, 'O467_NATIVE_16_EXACT')
        self.assertEqual([*legacy, *fragments], mutate.MUTANTS, 'O467_NATIVE_APPEND_WIRED')

    def test_restored_preserves_original_methods_and_includes_every_new_judge(self):
        old = list(getattr(mutation_bridge, 'LEGACY_RESTORED', mutation_bridge.RESTORED))
        self.assertEqual(67, len(old), 'O467_RESTORED_67_PRESERVED')
        self.assertEqual(RESTORED_SHA, hashlib.sha256(json.dumps(old, separators=(',', ':')).encode()).hexdigest())
        self.assertIn('tests.test_r03_mutation_coverage.R03MutationCoverage.'
            'test_mark_guides_follow_live_fill_sources_axes_starts_versions_and_cold_replay',
            mutation_bridge.RESTORED, 'O467_RESTORED_ALL_FRAGMENT_JUDGES')
        expected = list(dict.fromkeys([*old, *(method for row in
            self.loader.load_fragments(ROOT, mutate.LEGACY_MUTANTS) for method in row['tests'])]))
        self.assertEqual(expected, mutation_bridge.RESTORED, 'O467_RESTORED_ALL_FRAGMENT_JUDGES')
        self.assertEqual(len(expected), len(set(expected)), 'O467_RESTORED_NO_DUPLICATE')

    def test_valid_fragments_keep_full_metadata_and_stable_filename_order(self):
        self.write(dict(self.row, id='O467_Z'))
        self.write(dict(self.row, id='O467_A'))
        self.assertEqual([dict(self.row, id='O467_A'), dict(self.row, id='O467_Z')], self.load())

    def test_duplicate_and_casefold_ids_fail_closed(self):
        self.write()
        for identifier in ('O467_EXAMPLE', 'o467_example'):
            with self.subTest(identifier=identifier), self.assertRaisesRegex(ValueError, 'O467_DUPLICATE_ID',
                    msg='O467_DUPLICATE_ID_MUST_REJECT'):
                self.load([{'id': identifier}])

    def test_duplicate_json_keys_and_unknown_fields_are_rejected(self):
        path = self.write()
        path.write_text(path.read_text().replace('"id":', '"id":"DUPLICATE","id":'), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'O467_DUPLICATE_JSON_KEY'):
            self.load()
        self.write(dict(self.row, equivalent='unsupported exemption'))
        with self.assertRaisesRegex(ValueError, 'O467_FRAGMENT_SHAPE'):
            self.load()

    def test_exact_filename_and_non_json_inventory_are_required(self):
        path = self.write(name='O467_WRONG')
        with self.assertRaisesRegex(ValueError, 'O467_FILENAME'):
            self.load()
        path.unlink()
        (self.root / 'tests/mutants.d/unreviewed.txt').write_text('ignored?', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'O467_FRAGMENT_PATH'):
            self.load()

    def test_unsafe_target_paths_and_symlinks_are_rejected(self):
        for name in ('../outside.c', '/tmp/outside.c', 'C:/outside.c', 'a\\b.c', 'a/../product.c'):
            self.write(dict(self.row, file=name))
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'O467_SOURCE_PATH'):
                self.load()
        path = self.write()
        path.unlink()
        external = self.root / 'outside.json'
        external.write_bytes(canonical(self.row))
        path.symlink_to(external)
        with self.assertRaisesRegex(ValueError, 'O467_SYMLINK'):
            self.load()
        path.unlink(); self.write()
        (self.root / 'product.c').unlink()
        (self.root / 'outside.c').write_text('int guard = 1;', encoding='utf-8')
        (self.root / 'product.c').symlink_to(self.root / 'outside.c')
        with self.assertRaisesRegex(ValueError, 'O467_SYMLINK'):
            self.load()

    def test_directory_symlink_and_missing_registry_are_rejected(self):
        directory = self.root / 'tests/mutants.d'
        directory.rmdir()
        with self.assertRaisesRegex(ValueError, 'O467_DIRECTORY_REQUIRED'):
            self.load()
        (self.root / 'outside').mkdir()
        directory.symlink_to(self.root / 'outside', target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'O467_SYMLINK'):
            self.load()

    def test_empty_duplicate_or_malformed_judges_and_blank_metadata_are_rejected(self):
        variants = [dict(self.row, tests=[]), dict(self.row, tests=self.row['tests'] * 2),
                    dict(self.row, tests=['os.system']), dict(self.row, tests=['tests.x.X.helper']),
                    dict(self.row, expected_assertion=''), dict(self.row, reason=''),
                    dict(self.row, binary='core'), dict(self.row, old=''),
                    dict(self.row, new=self.row['old'])]
        for row in variants:
            self.write(row)
            with self.subTest(row=row), self.assertRaises(ValueError):
                self.load()

    def test_tool_hash_includes_loader_and_every_fragment_byte(self):
        directory = self.root / 'tests'
        for name in ('mutate.py', 'mutation_bridge.py', 'mutation_fragments.py'):
            original = ROOT / 'tests' / name
            (directory / name).write_bytes(original.read_bytes() if original.is_file() else
                                          b'# loader fixture before implementation\n')
        path = self.write()
        with mock.patch.object(mutate, 'HERE', directory):
            original = mutate.tool_hash()
            for target in (path, directory / 'mutation_fragments.py'):
                raw = target.read_bytes(); target.write_bytes(raw + b' ')
                self.assertNotEqual(original, mutate.tool_hash(), 'O467_TOOL_CLOSURE_BINDS_' + target.name)
                target.write_bytes(raw)
            self.assertEqual(original, mutate.tool_hash())
        spec = importlib.util.spec_from_file_location('o467_evidence_reader',
            ROOT / '.github/scripts/evidence_records.py')
        reader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(reader)
        with mock.patch.dict(sys.modules, {'mutation_fragments':
                SimpleNamespace(__file__=str(self.root / 'foreign/mutation_fragments.py'))}):
            with self.assertRaisesRegex(ValueError, 'judge dependency imported from another checkout: mutation_fragments'):
                reader.OriginalJudge(ROOT)

    def test_bridge_oracle_hash_includes_fragment_bytes_without_dropping_old_sources(self):
        path = self.write()
        fixture = self.root / 'tests/old_judge.py'
        fixture.write_text('# old oracle\n', encoding='utf-8')
        original = mutation_bridge.oracle_hash(self.row, self.root)
        for target in (path, fixture):
            raw = target.read_bytes(); target.write_bytes(raw + b' ')
            self.assertNotEqual(original, mutation_bridge.oracle_hash(self.row, self.root),
                                'O467_ORACLE_CLOSURE_BINDS_' + target.name)
            target.write_bytes(raw)

    def test_all_registered_fragments_have_one_real_anchor_and_real_baseline_judge(self):
        fragments = self.loader.load_fragments(ROOT, mutate.LEGACY_MUTANTS)
        sources = mutate.Sources(ROOT)
        with mock.patch.object(mutate, 'run_cmd', side_effect=AssertionError('native command forbidden')):
            for row in fragments:
                with self.subTest(mid=row['id']):
                    self.assertEqual(1, sources.texts[row['file']].count(row['old']), 'O467_EXACT_SOURCE_ANCHOR')
                    self.assertEqual('run', mutate.definition_kind(row, sources)[0], 'O467_EXECUTABLE_NATIVE_DEFINITION')

    def test_node_verdict_requires_own_named_assertion_and_complete_zero_skip_run(self):
        path = ROOT / 'tests/node_mutation_fragments.py'
        self.assertTrue(path.is_file(), 'O467_NODE_RUNNER_AVAILABLE')
        spec = importlib.util.spec_from_file_location('o467_node_runner_test', path)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        error = dict(name='AssertionError', code='ERR_ASSERTION', failureType='testCodeFailure',
                     message='O467_NAMED assertion', stack='neutral', expected='neutral', actual='neutral')
        events = [dict(type='test:fail', name='case-one', testNumber=1, nesting=0,
                       skip=False, todo=False, error=error),
                  dict(type='test:summary', data=dict(success=False, counts=dict(
                       tests=1, suites=0, passed=0, failed=1, cancelled=0, skipped=0, todo=0)))]
        def outcome(rows, cases=('case-one',), failed=('case-one',), **kwargs):
            return dict(exit=1, stdout=''.join(json.dumps(row) + '\n' for row in rows),
                        stderr='', timed_out=False, expected_cases=list(cases),
                        expected_failures={name: 'O467_NAMED assertion' for name in failed}, **kwargs)
        run = outcome(events)
        self.assertEqual('killed', runner.classify(run, 1, 'O467_NAMED'),
                         'O467_NODE_STRUCTURED_ASSERTION_ACCEPTED')
        bad = []
        for field in ('stack', 'expected', 'actual'):
            copy = deepcopy(events)
            copy[0]['error']['message'] = 'UNRELATED_ASSERTION'
            copy[0]['error'][field] = 'O467_NAMED assertion'
            bad.append((field + '-only', copy, ('case-one',), ('case-one',)))
        for message in ('UNRELATED_ASSERTION\n+ actual: O467_NAMED',
                        'UNRELATED_O467_NAMED', 'O467_NAMED_WRONG'):
            copy = deepcopy(events); copy[0]['error']['message'] = message
            bad.append(('wrong-message-first-line', copy, ('case-one',), ('case-one',)))
        for field, wrong in (('name', 'TypeError'), ('code', 'ERR_TEST_FAILURE'),
                             ('failureType', 'cancelledByParent')):
            copy = deepcopy(events); copy[0]['error'][field] = wrong
            copy[0]['error']['actual'] = {field: error[field]}
            bad.append(('nested-' + field + '-cannot-borrow', copy, ('case-one',), ('case-one',)))
        copy = deepcopy(events); copy[0]['name'] = 'O467_NAMED passing name'
        copy[0]['error']['message'] = 'UNRELATED_ASSERTION'
        bad.append(('test-name-only', copy, ('O467_NAMED passing name',), ('O467_NAMED passing name',)))
        two = deepcopy(events)
        extra = deepcopy(two[0]); extra.update(name='case-two', testNumber=2)
        extra['error']['message'] = 'UNRELATED_ASSERTION'
        two.insert(1, extra); two[-1]['data']['counts'].update(tests=2, failed=2)
        bad.append(('unrelated-extra-failure', two, ('case-one', 'case-two'), ('case-one',)))
        valid_two = deepcopy(two); valid_two[1]['error']['message'] = 'O467_NAMED assertion'
        self.assertEqual('killed', runner.classify(outcome(valid_two, ('case-one', 'case-two'),
            ('case-one', 'case-two')), 2, 'O467_NAMED'), 'O467_NODE_DECLARED_MULTI_FAILURE_ACCEPTED')
        duplicate = deepcopy(valid_two); duplicate[1]['testNumber'] = 1
        bad.append(('duplicate-ordinal', duplicate, ('case-one', 'case-two'), ('case-one', 'case-two')))
        absent = deepcopy(events)
        bad.append(('missing-declared-failure', absent, ('case-one',), ('case-one', 'case-two')))
        for key, value in (('skipped', 1), ('tests', 2), ('failed', 0)):
            copy = deepcopy(events); copy[-1]['data']['counts'][key] = value
            bad.append(('wrong-count-' + key, copy, ('case-one',), ('case-one',)))
        skipped = deepcopy(events); skipped[0]['skip'] = True
        bad.append(('skipped-event', skipped, ('case-one',), ('case-one',)))
        for label, rows, cases, failed in bad:
            with self.subTest(control=label):
                self.assertEqual('blocked', runner.classify(outcome(rows, cases, failed), len(cases), 'O467_NAMED'),
                                 'O467_NODE_UNRELATED_FAILURE_CANNOT_KILL: ' + label)
        self.assertEqual('blocked', runner.classify(dict(run, timed_out=True), 1, 'O467_NAMED'))
        self.assertEqual('blocked', runner.classify(dict(run, exit=2), 1, 'O467_NAMED'))


if __name__ == '__main__':
    unittest.main()
