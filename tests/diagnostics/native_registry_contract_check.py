#!/usr/bin/env python3
"""R386 infrastructure gate; fixture costs are never published as CI evidence."""
from __future__ import annotations

import argparse
import copy
import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
import urllib.request
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests'))
try:
    import native_registry as registry
except ModuleNotFoundError as error:
    if error.name != 'native_registry':
        raise
    registry = None
import native_shards
import run_all

WITHDRAWALS = ('R386_NATIVE_DROP_FRAGMENT', 'R386_NATIVE_COUNT_MISMATCH',
               'R386_NATIVE_TWO_SHARDS_OVERLAP', 'R386_NATIVE_COST_WITHOUT_RECEIPT',
               'R386_NATIVE_STALE_SUITE_SOURCE',
               # Review 7056059753 E5/E4 and three similar empty-run rewrites:
               # data-only edits that must not silently weaken a legacy suite.
               'R386_NATIVE_E5_UNITTEST_TO_EMPTY_SCRIPT', 'R386_NATIVE_E4_NODE_SCRIPT_EMPTY_CMD',
               'R386_NATIVE_NODE_TEST_TO_EXIT_ONLY', 'R386_NATIVE_SCRIPT_EXTRA_ARGS',
               'R386_NATIVE_LEGACY_ORDER_ESCAPE', 'R386_NATIVE_SEALED_CATALOG_REWRITE',
               'R386_NATIVE_AMENDMENT_LEGALIZES_EMPTY_RUN')
# A named withdrawal is only "red" when it fails at its designated assertion;
# a different failure exits 3 so 0/1/0 cannot be produced by an unrelated error.
WITHDRAWAL_MARKERS = {
    'R386_NATIVE_E5_UNITTEST_TO_EMPTY_SCRIPT': 'R386_NATIVE_LEGACY_EXECUTION_PIN',
    'R386_NATIVE_E4_NODE_SCRIPT_EMPTY_CMD': 'R386_NATIVE_LEGACY_EXECUTION_PIN',
    'R386_NATIVE_NODE_TEST_TO_EXIT_ONLY': 'R386_NATIVE_LEGACY_EXECUTION_PIN',
    'R386_NATIVE_SCRIPT_EXTRA_ARGS': 'R386_NATIVE_LEGACY_EXECUTION_PIN',
    'R386_NATIVE_LEGACY_ORDER_ESCAPE': 'R386_NATIVE_LEGACY_EXECUTION_PIN',
    # Rewriting the sealed catalog together with the fragment only fails
    # against the trusted base's original run_all.py tables.
    'R386_NATIVE_SEALED_CATALOG_REWRITE': 'R386_NATIVE_LEGACY_EXECUTION_NOT_IN_TRUSTED_BASE',
    # The amendment door must not reopen the hole it replaces.
    'R386_NATIVE_AMENDMENT_LEGALIZES_EMPTY_RUN': 'R386_NATIVE_AMENDMENT_FIELD',
}


def amend(root, name, reason='fixture: reviewed legitimate change of an existing suite'):
    return registry.amend_suite(root, name=name, reason=reason)


def make_fixture(root, destination):
    inventory = registry.migrate(root, destination)
    paths = set()
    for path in (destination / registry.SUITES).glob('*.json'):
        paths.update(json.loads(path.read_bytes())['files'])
    paths.update(run_all.NODE_EXCLUDED)
    paths.update(run_all.REQUIRED_OWNER_GATES)
    paths.update(run_all.REQUIRED_BROWSER_GATES)
    paths.update('tests/' + stem + '.py' for stem in run_all.PY_BROWSER_GATES)
    # main #438: the R03 workspace source's original stdout/receipt/child files
    # stay at their tests/ paths and are re-validated on every registry read.
    paths.update(path.relative_to(root).as_posix()
                 for path in (root / 'tests/native_shard_evidence').rglob('*') if path.is_file())
    for rel in sorted(paths):
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / rel, target)
    (destination / registry.MARKER).write_bytes(registry.canonical_bytes({'schema': 'geometry-test-registries/1'}))
    gitdir = subprocess.check_output(['git', '-C', str(root), 'rev-parse', '--absolute-git-dir'], text=True).strip()
    (destination / '.git').write_text('gitdir: ' + gitdir + '\n')
    return inventory


def validate_fixture(root, observed):
    records = registry.load_registry(root)
    registry.timing_profile(root)
    with mock.patch.object(run_all, 'ROOT', root), mock.patch.object(run_all, 'HERE', root / 'tests'):
        problems = run_all.check_registry()
        if problems:
            raise ValueError('R386_NATIVE_DISK_CENSUS: ' + '; '.join(problems))
        suites = run_all.build_suites()
        rows = []
        for suite in suites:
            row = run_all.Row(suite.name, suite.counted)
            row.ran = True
            row.total = observed[suite.name].get('count', 0)
            row.passed = row.total
            rows.append(row)
        problems = run_all.compare_expected(rows, suites, registry.expected(root), '', True)
        if problems:
            raise ValueError('R386_NATIVE_COUNT_MISMATCH: ' + repr(problems))
    return records


def withdraw(root, name):
    if name == 'R386_NATIVE_DROP_FRAGMENT':
        (root / registry.SUITES / 'py__test_unittest_runner.json').unlink()
    elif name == 'R386_NATIVE_COUNT_MISMATCH':
        path = root / registry.SUITES / 'py__test_unittest_runner.json'
        row = json.loads(path.read_bytes())
        row['expected']['count'] += 1
        path.write_bytes(registry.canonical_bytes(row))
        # Even a reviewed amendment of the count is still checked against the
        # real run by the original runner guard; it is not a way to set counts.
        amend(root, 'py:test_unittest_runner')
    elif name == 'R386_NATIVE_COST_WITHOUT_RECEIPT':
        path = root / registry.COSTS / 'py__test_unittest_runner.json'
        row = json.loads(path.read_bytes())
        row['source_sha256'] = '0' * 64
        path.write_bytes(registry.canonical_bytes(row))
    elif name == 'R386_NATIVE_STALE_SUITE_SOURCE':
        path = root / 'tests/test_r386_ci_fixture.py'
        path.write_bytes(path.read_bytes() + b'# changed after real named observation\n')
    elif name in ('R386_NATIVE_E5_UNITTEST_TO_EMPTY_SCRIPT', 'R386_NATIVE_LEGACY_ORDER_ESCAPE',
                  'R386_NATIVE_AMENDMENT_LEGALIZES_EMPTY_RUN'):
        # Review E5 verbatim: 53 real tests become `python -c pass`.
        path = root / registry.SUITES / 'py__test_serve.json'
        row = json.loads(path.read_bytes())
        row['execution']['kind'] = 'python-script'
        row['execution']['cmd'] = ['{python}', '-c', 'pass']
        row['expected'] = {'mode': 'exit-code-only'}
        if name == 'R386_NATIVE_LEGACY_ORDER_ESCAPE':
            # Same empty run, relabelled as a "new" suite to dodge a legacy-only pin.
            row['order'] = 'new/py__test_serve'
        path.write_bytes(registry.canonical_bytes(row))
        if name == 'R386_NATIVE_AMENDMENT_LEGALIZES_EMPTY_RUN':
            sealed = json.loads((root / registry.EXECUTION_CATALOG).read_bytes())['suites']['py:test_serve']
            folder = root / registry.AMENDMENTS
            folder.mkdir(parents=True, exist_ok=True)
            (folder / 'py__test_serve.json').write_bytes(registry.canonical_bytes({
                'schema': registry.AMENDMENT_SCHEMA, 'name': 'py:test_serve',
                'before_sha256': registry.declaration_sha256(sealed),
                'after': registry.declaration(row), 'reason': 'hand-written amendment hiding an empty run'}))
    elif name == 'R386_NATIVE_E4_NODE_SCRIPT_EMPTY_CMD':
        # Review E4 verbatim: the node script no longer runs its file.
        path = root / registry.SUITES / 'node__document_format.json'
        row = json.loads(path.read_bytes())
        row['execution']['cmd'] = ['-e', '0']
        path.write_bytes(registry.canonical_bytes(row))
    elif name in ('R386_NATIVE_NODE_TEST_TO_EXIT_ONLY', 'R386_NATIVE_SEALED_CATALOG_REWRITE'):
        # Still runs the real file, but its 14-test count is no longer verified.
        # Structurally valid for a node-script, so only the seal can catch it.
        path = root / registry.SUITES / 'node__anchor_band_clip.json'
        row = json.loads(path.read_bytes())
        row['execution']['kind'] = 'node-script'
        row['execution']['cmd'] = list(row['files'])
        row['expected'] = {'mode': 'exit-code-only'}
        path.write_bytes(registry.canonical_bytes(row))
        if name == 'R386_NATIVE_SEALED_CATALOG_REWRITE':
            # ...and rewrite the sealed catalog consistently with it.
            catalog_path = root / registry.EXECUTION_CATALOG
            catalog = json.loads(catalog_path.read_bytes())
            catalog['suites'][row['name']] = registry.declaration(row)
            catalog_path.write_bytes(registry.canonical_bytes(catalog))
    elif name == 'R386_NATIVE_SCRIPT_EXTRA_ARGS':
        # The right script, given an argument that only prints usage.
        path = root / registry.SUITES / 'oracle__framing-selftest.json'
        row = json.loads(path.read_bytes())
        row['execution']['cmd'].append('--help')
        path.write_bytes(registry.canonical_bytes(row))
    elif name != 'R386_NATIVE_TWO_SHARDS_OVERLAP':
        raise ValueError(name)


class NativeRegistryContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='r386-native-contract-')
        cls.base = Path(cls.temporary.name)
        cls.template = cls.base / 'template'
        cls.inventory = make_fixture(ROOT, cls.template)
        cls.observed = copy.deepcopy(registry.expected(cls.template)['suites'])

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.root = self.base / self._testMethodName
        shutil.copytree(self.template, self.root)

    def path(self, name='py:test_unittest_runner'):
        return self.root / registry.SUITES / (registry.key(name) + '.json')

    def write(self, path, value):
        path.write_bytes(registry.canonical_bytes(value))

    def verify_ci(self, responses, *, trusted_ref=None):
        trusted_ref = trusted_ref or registry._legacy_catalog(self.root)['base_sha']
        return registry.verify_ci_sources(self.root, fetch=responses.__getitem__, trusted_ref=trusted_ref)

    def test_migration_is_lossless_and_idempotent(self):
        records = validate_fixture(self.root, self.observed)
        with mock.patch.object(run_all, 'ROOT', self.root), mock.patch.object(run_all, 'HERE', self.root / 'tests'):
            migrated = run_all.build_suites()
        current = run_all.build_suites()
        self.assertEqual([s.name for s in current], [s.name for s in migrated])
        for before, after in zip(current, migrated):
            self.assertEqual(before.kind, after.kind)
            self.assertEqual(before.timeout, after.timeout)
            self.assertEqual(before.needs, after.needs)
            self.assertEqual(before.needs_node, after.needs_node)
            self.assertEqual(before.extra_env, after.extra_env)
            self.assertEqual(before.label, after.label)
            self.assertEqual(before.cmd and [c.replace(str(ROOT), '{root}') for c in before.cmd],
                             after.cmd and [c.replace(str(self.root), '{root}') for c in after.cmd])
        second = self.base / 'second'
        inventory = registry.migrate(self.root, second)
        self.assertEqual(self.inventory, inventory)
        self.assertEqual(len(records), len(self.observed))
        # The 783-test historical aggregate is transported intact; migration
        # never guesses a per-file census that was not measured.
        aggregate = next(r for r in records if r['name'] == 'node:tests-js')
        original = next(s for s in current if s.name == 'node:tests-js')
        self.assertEqual(aggregate['expected'], self.observed['node:tests-js'])
        self.assertEqual(aggregate['execution']['cmd'], original.cmd)

    def test_migration_preserves_every_actual_timing_scenario(self):
        profile = registry.timing_profile(self.root)
        self.assertEqual(native_shards.measured_profiles(), profile['profiles'])
        self.assertEqual(native_shards.timing_weights(), profile['weights'])
        self.assertEqual(native_shards.added_suite_costs(), profile['added'])
        names = set(self.observed)
        for scenario in profile['profiles']:
            self.assertEqual(names, set(scenario))

    def test_missing_fragment_and_missing_disk_suite_are_rejected(self):
        self.path().unlink()
        with self.assertRaisesRegex(ValueError, 'COVERAGE'):
            validate_fixture(self.root, self.observed)

    def test_marker_forbids_legacy_fallback_even_when_all_fragments_disappear(self):
        shutil.rmtree(self.root / registry.SUITES)
        self.assertTrue(registry.active(self.root))
        with self.assertRaisesRegex(ValueError, 'DIRECTORY_REQUIRED'):
            registry.load_registry(self.root)

    def test_expected_count_mismatch_still_uses_existing_runner_guard(self):
        withdraw(self.root, 'R386_NATIVE_COUNT_MISMATCH')
        with self.assertRaisesRegex(ValueError, 'COUNT_MISMATCH'):
            validate_fixture(self.root, self.observed)

    def test_partial_update_cannot_rewrite_counts(self):
        before = self.path().read_bytes()
        with self.assertRaisesRegex(ValueError, 'CENSUS_MUST_BE_COMPLETE'):
            registry.update_expected(self.root, {'py:test_unittest_runner': self.observed['py:test_unittest_runner']})
        self.assertEqual(before, self.path().read_bytes())

    def test_cost_missing_or_without_original_receipt_is_rejected(self):
        path = self.root / registry.COSTS / 'py__test_unittest_runner.json'
        raw = path.read_bytes()
        path.unlink()
        with self.assertRaisesRegex(ValueError, 'EXACT_COST_COVERAGE'):
            registry.timing_profile(self.root)
        path.write_bytes(raw)
        withdraw(self.root, 'R386_NATIVE_COST_WITHOUT_RECEIPT')
        with self.assertRaisesRegex(ValueError, 'RECEIPT_REQUIRED'):
            registry.timing_profile(self.root)
        path.write_bytes(raw)
        catalog = registry._legacy_catalog(self.root)
        legacy = next(source for source in catalog['sources'] if source['kind'] == 'historical-added')
        invented = copy.deepcopy(registry._source(self.root, legacy['sha256']))
        invented['observations'] = [dict(invented['observations'][0], name='py:test_r386_no_ci')]
        source_bytes = registry.canonical_bytes(invented)
        source_hash = hashlib.sha256(source_bytes).hexdigest()
        (self.root / registry.SOURCES / (source_hash + '.json')).write_bytes(source_bytes)
        with self.assertRaisesRegex(ValueError, 'NEW_SOURCE_CANNOT_CLAIM_LEGACY'):
            registry.timing_profile(self.root)
        catalog['sources'].append({'path': 'tests/native_shard_added_evidence_forged.json',
            'sha256': source_hash, 'kind': 'historical-added', 'suites': ['py:test_r386_no_ci']})
        self.write(self.root / registry.LEGACY, catalog)
        with self.assertRaisesRegex(ValueError, 'LEGACY_NOT_IN_TRUSTED_BASE'):
            registry.verify_ci_sources(self.root, trusted_ref=catalog['base_sha'])
        with mock.patch.object(registry, '_git_bytes', return_value=b'{"different":"old catalog"}\n'):
            with self.assertRaisesRegex(ValueError, 'LEGACY_CATALOG_IS_IMMUTABLE'):
                registry._verify_legacy_catalog(self.root, catalog['base_sha'])

    def test_original_receipt_bytes_are_content_addressed(self):
        path = next((self.root / registry.SOURCES).glob('*.json'))
        path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'SOURCE_BYTES'):
            registry.timing_profile(self.root)

    def test_duplicate_json_keys_duplicate_order_and_boolean_counts_are_rejected(self):
        path = self.path()
        original = path.read_bytes()
        path.write_bytes(original.replace(b'{', b'{"name":"duplicate",', 1))
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_JSON_KEY'):
            registry.load_registry(self.root)
        row = json.loads(original)
        row['order'] = 'legacy/000000'
        self.write(path, row)
        with self.assertRaisesRegex(ValueError, 'STABLE_ORDER'):
            registry.load_registry(self.root)
        row = json.loads(original)
        row['expected']['count'] = True
        self.write(path, row)
        with self.assertRaisesRegex(ValueError, 'EXACT_EXPECTED'):
            registry.load_registry(self.root)

    def test_crlf_unknown_extension_and_nested_directory_are_rejected(self):
        path = self.path()
        raw = path.read_bytes()
        path.write_bytes(raw.replace(b'\n', b'\r\n'))
        with self.assertRaisesRegex(ValueError, 'PURE_LF'):
            registry.load_registry(self.root)
        path.write_bytes(raw)
        extra = self.root / registry.SUITES / 'ignored.txt'
        extra.write_text('must not disappear from the census')
        with self.assertRaisesRegex(ValueError, 'UNEXPECTED_FRAGMENT_PATH'):
            registry.load_registry(self.root)
        extra.unlink()
        extra.mkdir()
        with self.assertRaisesRegex(ValueError, 'UNEXPECTED_FRAGMENT_PATH'):
            registry.load_registry(self.root)

    def test_symlink_file_and_parent_directory_are_rejected(self):
        path = self.path()
        raw = path.read_bytes()
        original = self.root / 'outside.json'
        original.write_bytes(raw)
        path.unlink()
        path.symlink_to(original)
        with self.assertRaisesRegex(ValueError, 'SYMLINK'):
            registry.load_registry(self.root)
        path.unlink()
        path.write_bytes(raw)
        folder = self.root / registry.SUITES
        moved = self.root / 'outside-dir'
        folder.rename(moved)
        folder.symlink_to(moved, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'SYMLINK'):
            registry.load_registry(self.root)

    def test_plan_rejects_missing_cost_and_overlap(self):
        suites = [SimpleNamespace(name='unmeasured-new-suite')]
        with self.assertRaisesRegex(ValueError, 'NO_UNMEASURED_COST'):
            native_shards.partition_suites(suites, 1)
        suites = [SimpleNamespace(name='a'), SimpleNamespace(name='b')]
        with self.assertRaisesRegex(ValueError, '分片聯集'):
            native_shards.validate_partition(suites, [[suites[0]], suites])

    def test_source_digest_binds_execution_expected_and_original_cost_bytes(self):
        first = registry.source_digest(self.root)
        row = json.loads(self.path().read_bytes())
        row['execution']['label'] += ' fixture'
        self.write(self.path(), row)
        with self.assertRaisesRegex(ValueError, 'LEGACY_EXECUTION_PIN'):
            registry.source_digest(self.root)
        amend(self.root, 'py:test_unittest_runner')
        second = registry.source_digest(self.root)
        self.assertNotEqual(first, second)
        row['expected']['count'] += 1
        self.write(self.path(), row)
        amend(self.root, 'py:test_unittest_runner')
        self.assertNotEqual(second, registry.source_digest(self.root))

    def test_two_new_suites_touch_distinct_files_and_require_independent_costs(self):
        before = {p.relative_to(self.root): p.read_bytes()
                  for p in (self.root / registry.SUITES).glob('*.json')}
        for suffix in ('a', 'b'):
            row = json.loads(self.path().read_bytes())
            row['name'] = 'py:test_r386_fixture_' + suffix
            row['order'] = 'new/' + registry.key(row['name'])
            file = 'tests/test_r386_fixture_' + suffix + '.py'
            row['files'] = [file]
            row['execution']['cmd'][-1] = '{root}/' + file
            row['execution']['label'] = file
            row['expected'] = {'mode': 'count', 'count': 1, 'unit': 'test'}
            (self.root / file).write_text('import unittest\nclass Example(unittest.TestCase):\n def test_real(self): self.assertEqual(1,1)\n')
            self.write(self.path(row['name']), row)
        records = registry.load_registry(self.root)
        self.assertEqual(len(records), len(self.observed) + 2)
        self.assertTrue(all((self.root / rel).read_bytes() == raw for rel, raw in before.items()))
        with self.assertRaisesRegex(ValueError, 'EXACT_COST_COVERAGE'):
            registry.timing_profile(self.root)
        # Actually execute the two independent unittest fixtures. Their results
        # are deliberately not imported as production cost receipts.
        result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s',
                                 str(self.root / 'tests'), '-p', 'test_r386_fixture_*.py'],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Ran 2 tests', result.stderr)

    def test_existing_suite_execution_is_sealed_against_trusted_base(self):
        """Review 7056059753 problem A: data-only edits cannot weaken a legacy suite."""
        base = registry._execution_catalog(self.root)['base_sha']
        self.assertEqual(registry.verify_legacy_execution(self.root, base)['source'], 'trusted-base-original-run_all')
        for withdrawal in ('R386_NATIVE_E5_UNITTEST_TO_EMPTY_SCRIPT', 'R386_NATIVE_E4_NODE_SCRIPT_EMPTY_CMD',
                           'R386_NATIVE_NODE_TEST_TO_EXIT_ONLY', 'R386_NATIVE_SCRIPT_EXTRA_ARGS',
                           'R386_NATIVE_LEGACY_ORDER_ESCAPE'):
            root = self.base / (self._testMethodName + withdrawal)
            shutil.copytree(self.template, root)
            withdraw(root, withdrawal)
            with self.assertRaisesRegex(ValueError, 'R386_NATIVE_LEGACY_EXECUTION_PIN'):
                registry.load_registry(root)
        withdraw(self.root, 'R386_NATIVE_SEALED_CATALOG_REWRITE')
        registry.load_registry(self.root)  # self-consistent data passes offline ...
        with self.assertRaisesRegex(ValueError, 'LEGACY_EXECUTION_NOT_IN_TRUSTED_BASE'):
            registry.verify_legacy_execution(self.root, base)  # ... but not against the trusted base
        with mock.patch.object(registry, '_git_bytes', return_value=b'{"sealed":"elsewhere"}\n'):
            with self.assertRaisesRegex(ValueError, 'LEGACY_EXECUTION_CATALOG_IS_IMMUTABLE'):
                registry.verify_legacy_execution(self.root, base)
        with self.assertRaisesRegex(ValueError, 'LEGACY_REQUIRES_EXPLICIT_TRUSTED_BASE'):
            registry.verify_legacy_execution(self.root, None)
        (self.root / registry.EXECUTION_CATALOG).unlink()
        with self.assertRaisesRegex(ValueError, 'LEGACY_EXECUTION_CATALOG_REQUIRED'):
            registry.load_registry(self.root)

    def test_legitimate_count_and_needs_change_goes_through_named_amendment(self):
        """#437-style change: py:test_gdi_contract count 5->10 and needs gdi->+core,bridge,model-base."""
        name = 'py:test_gdi_contract'
        path = self.path(name)
        row = json.loads(path.read_bytes())
        row['expected']['count'] += 5
        row['execution']['needs'] = sorted(set(row['execution']['needs']) | {'core', 'bridge', 'model-base'})
        self.write(path, row)
        with self.assertRaisesRegex(ValueError, 'LEGACY_EXECUTION_PIN'):
            registry.load_registry(self.root)
        with self.assertRaisesRegex(ValueError, 'AMEND_EXISTING_SUITE_ONLY'):
            registry.amend_suite(self.root, name='py:test_not_sealed', reason='only existing suites')
        result = amend(self.root, name)
        self.assertIs(result['acceptance'], False)
        records = {r['name']: r for r in registry.load_registry(self.root)}
        self.assertEqual(records[name]['expected']['count'], row['expected']['count'])
        registry.verify_legacy_execution(self.root, registry._execution_catalog(self.root)['base_sha'])
        # Amendments may only add needs and may never touch what is executed.
        for field, value in (('needs', []), ('kind', 'python-script'), ('cmd', ['{python}', '-c', 'pass']),
                             ('extra_env', {'GEOMETRY_SKIP': '1'})):
            changed = copy.deepcopy(row)
            changed['execution'][field] = value
            self.write(path, changed)
            with self.assertRaisesRegex(ValueError, 'AMENDMENT_FIELD'):
                amend(self.root, name)
        changed = copy.deepcopy(row)
        changed['expected'] = {'mode': 'exit-code-only'}
        self.write(path, changed)
        with self.assertRaisesRegex(ValueError, 'AMENDMENT_FIELD'):
            amend(self.root, name)
        self.write(path, row)
        registry.load_registry(self.root)
        amendment = self.root / registry.AMENDMENTS / (registry.key(name) + '.json')
        forged = json.loads(amendment.read_bytes())
        forged['before_sha256'] = '0' * 64
        self.write(amendment, forged)
        with self.assertRaisesRegex(ValueError, 'AMENDMENT_BEFORE_MUST_BE_SEALED'):
            registry.load_registry(self.root)

    def test_new_script_suites_are_bound_to_their_own_file(self):
        for kind, name, file, cmd in (
                ('python-script', 'script:r386_fixture', 'tests/r386_fixture_script.py',
                 ['{python}', '{root}/tests/r386_fixture_script.py']),
                ('node-script', 'node:r386_fixture_script', 'tests/r386_fixture_script.js',
                 ['tests/r386_fixture_script.js'])):
            (self.root / file).write_text('// fixture\n' if file.endswith('.js') else '# fixture\n')
            registry.init_suite(self.root, name=name, file=file, kind=kind)
            row = json.loads(self.path(name).read_bytes())
            self.assertEqual(row['execution']['cmd'], cmd)
            self.assertEqual(row['expected'], {'mode': 'exit-code-only'})
            self.assertEqual(row['order'], 'new/' + registry.key(name))
            registry.load_registry(self.root)
            for bad in (['{python}', '-c', 'pass'] if kind == 'python-script' else ['-e', '0'],):
                row['execution']['cmd'] = bad
                self.write(self.path(name), row)
                with self.assertRaisesRegex(ValueError, 'EXECUTION_FILE_BINDING'):
                    registry.load_registry(self.root)
            row['execution']['cmd'] = cmd
            self.write(self.path(name), row)
        (self.root / 'tests/r386_other_script.py').write_text('# fixture\n')
        with self.assertRaisesRegex(ValueError, 'INIT_SCRIPT_IDENTITY'):
            registry.init_suite(self.root, name='py:test_r386_script', file='tests/r386_other_script.py',
                                kind='python-script')
        with self.assertRaisesRegex(ValueError, 'INIT_NEW_COUNTED_SUITE_ONLY'):
            registry.init_suite(self.root, name='py:test_serve', file='tests/test_serve.py', kind='unittest')
        # Still not runnable formally: a new suite needs its own CI cost receipt.
        with self.assertRaisesRegex(ValueError, 'EXACT_COST_COVERAGE'):
            registry.timing_profile(self.root)

    def test_fragments_check_out_as_lf_on_every_platform(self):
        """Review 7056059753 problem B: readers reject CR, so autocrlf must not apply."""
        lf = ('tests/suites.d/py__test_serve.json', 'tests/native-costs.d/py__test_serve.json',
              'tests/registry-layout.json', registry.LEGACY.as_posix(), registry.EXECUTION_CATALOG.as_posix(),
              (registry.AMENDMENTS / 'py__example.json').as_posix(), 'geometry-web/cdp_sections.d/P50.json',
              'geometry-web/canvas_sections/P999.js',
              'geometry-core/domain-decoupling/product-architecture.d/example.json')
        raw = ((registry.SOURCES / 'example.json').as_posix(), 'geometry-web/canvas-registry/legacy.json')
        output = subprocess.run(['git', '-C', str(ROOT), 'check-attr', 'text', 'eol', '--', *lf, *raw],
                                capture_output=True, text=True, check=True).stdout
        attributes = {}
        for line in output.splitlines():
            path, name, value = line.rsplit(': ', 2)
            attributes.setdefault(path, {})[name] = value
        for path in lf:
            self.assertEqual(attributes[path], {'text': 'set', 'eol': 'lf'}, path)
        for path in raw:
            self.assertEqual(attributes[path]['text'], 'unset', path)

    def ci_fixture(self, *, pending=False, ordinal=1):
        """Synthetic API/archive fixture, never a claim about a real CI run."""
        name = 'py:test_r386_ci_fixture'
        declaration = json.loads(self.path().read_bytes())
        declaration.update(name=name, order='new/' + registry.key(name),
                           files=['tests/test_r386_ci_fixture.py'],
                           expected={'mode': 'count', 'count': 1, 'unit': 'test'})
        declaration['execution']['cmd'][-1] = '{root}/tests/test_r386_ci_fixture.py'
        (self.root / declaration['files'][0]).write_text('# synthetic contract fixture revision %d\n' % ordinal)
        if pending:
            registry.init_suite(self.root, name=name, file=declaration['files'][0], kind='unittest')
        else:
            self.write(self.path(name), declaration)
        head, checkout = 'a' * 40, 'b' * 40
        run_id, job_id, artifact_id = 1000 + ordinal, 2000 + ordinal, 3000 + ordinal
        run = {'id': run_id, 'head_sha': head, 'run_attempt': 1, 'status': 'completed',
               'html_url': registry.RUN_URL + str(run_id)}
        job = {'id': job_id, 'run_id': run_id, 'head_sha': head, 'status': 'completed', 'run_attempt': 1,
               'html_url': registry.RUN_URL + str(run_id) + '/job/' + str(job_id)}
        commit = {'sha': checkout, 'parents': [{'sha': head}]}
        row = run_all.report_row(run_all.Row(name))
        row.update(ran=True, total=1, passed=1, seconds=0.2, process_exit_code=0)
        report = {'schema': 'geometry-native-measurement/1', 'acceptance': False,
                  'commit_sha': checkout, 'selected': [name], 'rows': [row],
                  'ci_run_id': str(run_id), 'ci_run_attempt': '1', 'census_pending': pending,
                  'expected_candidate': declaration['expected'] if pending else None,
                  'suite_binding': registry.measurement_binding(self.root, json.loads(self.path(name).read_bytes())),
                  'source_stable': True}
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            archive.writestr(zipfile.ZipInfo('measurement.json', (2000, 1, 1, 0, 0, 0)),
                             registry.canonical_bytes(report))
        raw_zip = stream.getvalue()
        artifact = {'id': artifact_id, 'name': 'native-measurement-fixture',
                    'workflow_run': {'id': run_id, 'head_sha': head},
                    'size_in_bytes': len(raw_zip), 'digest': 'sha256:' + hashlib.sha256(raw_zip).hexdigest()}
        responses = {'/actions/runs/%d' % run_id: registry.canonical_bytes(run),
                     '/actions/runs/%d/attempts/1' % run_id: registry.canonical_bytes(run),
                     '/actions/jobs/%d' % job_id: registry.canonical_bytes(job),
                     '/actions/artifacts/%d' % artifact_id: registry.canonical_bytes(artifact),
                     '/actions/artifacts/%d/zip' % artifact_id: raw_zip,
                     '/git/commits/' + checkout: registry.canonical_bytes(commit)}
        arguments = dict(name=name, run_id=run_id, job_id=job_id, artifact_id=artifact_id,
                         member='measurement.json', planning_upper_ms=1000)
        return responses, arguments

    def test_cost_import_requires_original_archive_and_run_job_identity(self):
        responses, arguments = self.ci_fixture()
        bad = dict(responses)
        job = json.loads(bad['/actions/jobs/2001'])
        job['run_id'] = 9999
        bad['/actions/jobs/2001'] = registry.canonical_bytes(job)
        with self.assertRaisesRegex(ValueError, 'RUN_JOB_CHECKOUT_BINDING'):
            registry.import_ci_cost(self.root, self.root, **arguments, fetch=bad.__getitem__)
        bad = dict(responses)
        bad['/actions/artifacts/3001/zip'] += b'tampered original'
        with self.assertRaisesRegex(ValueError, 'ORIGINAL_CI_ARTIFACT_REQUIRED'):
            registry.import_ci_cost(self.root, self.root, **arguments, fetch=bad.__getitem__)
        inventory = registry.import_ci_cost(self.root, self.root, **arguments, fetch=responses.__getitem__)
        self.assertEqual(len(inventory), 2)
        self.assertEqual(registry.timing_profile(self.root)['added'][arguments['name']], 1000)
        file = self.root / 'tests/test_r386_ci_fixture.py'
        original = file.read_bytes()
        withdraw(self.root, 'R386_NATIVE_STALE_SUITE_SOURCE')
        with self.assertRaisesRegex(ValueError, 'STALE_SUITE_SOURCE_OR_EXECUTION'):
            registry.timing_profile(self.root)
        # A fresh measured revision changes the active pointer, while every
        # original remains immutable history and is still authenticated.
        old_sources = {p.name: p.read_bytes() for p in (self.root / registry.SOURCES).glob('*.json')}
        newer, newer_arguments = self.ci_fixture(ordinal=2)
        stage = self.root / 'refresh-stage'
        refreshed = registry.import_ci_cost(self.root, stage, **newer_arguments, fetch=newer.__getitem__)
        for item in refreshed:
            shutil.copyfile(stage / item['path'], self.root / item['path'])
        self.assertEqual(registry.timing_profile(self.root)['added'][arguments['name']], 1000)
        self.assertTrue(all((self.root / registry.SOURCES / path).read_bytes() == raw
                            for path, raw in old_sources.items()))
        self.assertEqual(self.verify_ci({**responses, **newer})['verified_online'], 2)
        declaration = json.loads(self.path(arguments['name']).read_bytes())
        declaration['execution']['timeout'] -= 1
        self.write(self.path(arguments['name']), declaration)
        with self.assertRaisesRegex(ValueError, 'STALE_SUITE_SOURCE_OR_EXECUTION'):
            registry.timing_profile(self.root)

    def test_live_authentication_rejects_self_filled_or_changed_receipt_bytes(self):
        responses, arguments = self.ci_fixture()
        registry.import_ci_cost(self.root, self.root, **arguments, fetch=responses.__getitem__)
        verified = self.verify_ci(responses)
        self.assertEqual(verified['verified_online'], 1)
        self.assertEqual(verified['inherited_from_base'], 0)
        self.assertEqual(verified['legacy_inherited'], len(registry._legacy_catalog(self.root)['sources']))
        self.assertEqual(verified['status'], 'verified')
        with self.assertRaisesRegex(ValueError, 'LEGACY_REQUIRES_EXPLICIT_TRUSTED_BASE'):
            registry.verify_ci_sources(self.root, fetch=responses.__getitem__)
        changed = dict(responses)
        changed['/actions/artifacts/3001/zip'] += b'changed authoritative bytes'
        with self.assertRaisesRegex(ValueError, 'LIVE_CI_BYTES'):
            self.verify_ci(changed)
        changed = dict(responses)
        run = json.loads(changed['/actions/runs/1001/attempts/1'])
        run['head_sha'] = 'c' * 40
        changed['/actions/runs/1001/attempts/1'] = registry.canonical_bytes(run)
        with self.assertRaisesRegex(ValueError, 'LIVE_CI_IDENTITY'):
            self.verify_ci(changed)
        cost = json.loads((self.root / registry.COSTS / (registry.key(arguments['name']) + '.json')).read_bytes())
        relative = registry.SOURCES / (cost['source_sha256'] + '.json')
        trusted = 'd' * 40
        with mock.patch.object(registry.subprocess, 'run', return_value=SimpleNamespace(
                returncode=0, stdout=(self.root / relative).read_bytes())) as git, \
                mock.patch.object(registry, '_verify_legacy_catalog', return_value={'source': 'unit-test-only', 'sha': trusted}), \
                mock.patch.object(registry, '_github_bytes', side_effect=AssertionError('trusted originals need no live artifact')):
            verified = registry.verify_ci_sources(self.root, trusted_ref=trusted)
            self.assertEqual(verified['verified_online'], 0)
            self.assertEqual(verified['inherited_from_base'], 1)
            self.assertEqual(verified['legacy_inherited'], len(registry._legacy_catalog(self.root)['sources']))
            self.assertEqual(git.call_args.args[0][-1], trusted + ':' + relative.as_posix())
        with mock.patch.object(registry.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout=b'forged base bytes')), \
                mock.patch.object(registry, '_verify_legacy_catalog', return_value={'source': 'unit-test-only', 'sha': trusted}):
            self.assertEqual(registry.verify_ci_sources(self.root, fetch=responses.__getitem__, trusted_ref=trusted)['verified_online'], 1)
        request = urllib.request.Request('https://api.github.com/example', headers={'Authorization': 'Bearer fixture-token'})
        redirect = registry._GitHubRedirect()
        external = redirect.redirect_request(request, None, 302, 'Found', {}, 'https://storage.example.invalid/archive')
        self.assertFalse(external.has_header('Authorization'))
        internal = redirect.redirect_request(request, None, 302, 'Found', {}, 'https://api.github.com/next')
        self.assertEqual(internal.get_header('Authorization'), 'Bearer fixture-token')
        with self.assertRaisesRegex(ValueError, 'REDIRECT_REQUIRES_HTTPS'):
            redirect.redirect_request(request, None, 302, 'Found', {}, 'http://storage.example.invalid/archive')

    def test_new_suite_measurement_discovers_count_without_changing_existing_baselines(self):
        before = {p.name: p.read_bytes() for p in (self.root / registry.SUITES).glob('*.json')}
        name, relative = 'py:test_r386_pending', 'tests/test_r386_pending.py'
        (self.root / relative).write_text('import unittest\nclass Example(unittest.TestCase):\n'
            ' def test_first(self): self.assertEqual(1,1)\n def test_second(self): self.assertEqual(2,2)\n')
        result = registry.init_suite(self.root, name=name, file=relative, kind='unittest')
        self.assertIs(result['acceptance'], False)
        with self.assertRaisesRegex(ValueError, 'EXACT_EXPECTED'):
            registry.load_registry(self.root)
        shutil.copyfile(ROOT / 'tests/_unittest_runner.py', self.root / 'tests/_unittest_runner.py')
        shutil.copyfile(ROOT / 'tests/binaries.py', self.root / 'tests/binaries.py')
        report_path = self.root / 'measurement.json'
        output = io.StringIO()
        with mock.patch.object(run_all, 'ROOT', self.root), \
                mock.patch.object(run_all, 'HERE', self.root / 'tests'), \
                mock.patch.object(run_all, 'EXPECTED_FILE', self.root / 'tests/run_all.expected.json'), \
                mock.patch.object(run_all, 'LOG_DIR', self.root / 'logs'), \
                mock.patch.object(run_all.binaries, 'OUT_DIR', self.root / 'out'), \
                mock.patch.object(run_all.binaries, 'inspect_all', return_value={}), \
                mock.patch.object(run_all.subprocess, 'check_output', return_value='f' * 40), \
                contextlib.redirect_stdout(output):
            code = run_all.main(['--measure-suite', name, '--report', str(report_path)])
        self.assertEqual(code, 0, output.getvalue())
        report = json.loads(report_path.read_bytes())
        self.assertIs(report['acceptance'], False)
        self.assertIs(report['census_pending'], True)
        self.assertIs(report['source_stable'], True)
        self.assertEqual(report['schema'], 'geometry-native-measurement/1')
        self.assertEqual(report['expected_candidate'], {'mode': 'count', 'count': 2, 'unit': 'test'})
        self.assertEqual(report['rows'][0]['process_exit_code'], 0)
        self.assertEqual(report['rows'][0]['passed'], 2)
        self.assertGreater(report['rows'][0]['seconds'], 0)
        self.assertEqual(json.loads(self.path(name).read_bytes())['expected'], {'mode': 'pending-ci-census'})
        pending_record = json.loads(self.path(name).read_bytes())
        self.assertEqual(report['suite_binding'], registry.measurement_binding(self.root, pending_record))
        self.assertTrue(all((self.root / registry.SUITES / file).read_bytes() == raw for file, raw in before.items()))

    def test_pending_import_updates_only_the_new_suite_from_original_census(self):
        before = {p.name: p.read_bytes() for p in (self.root / registry.SUITES).glob('*.json')}
        responses, arguments = self.ci_fixture(pending=True)
        with self.assertRaisesRegex(ValueError, 'EXACT_EXPECTED'):
            registry.timing_profile(self.root)
        imported = registry.import_ci_cost(self.root, self.root, **arguments, fetch=responses.__getitem__)
        self.assertEqual(len(imported), 3)
        self.assertEqual(registry.expected(self.root)['suites'][arguments['name']],
                         {'mode': 'count', 'count': 1, 'unit': 'test'})
        self.assertTrue(all((self.root / registry.SUITES / file).read_bytes() == raw for file, raw in before.items()))
        self.assertEqual(registry.timing_profile(self.root)['added'][arguments['name']], 1000)


def named_probe(name, control_for=None):
    with tempfile.TemporaryDirectory(prefix='r386-native-withdrawal-') as directory:
        root = Path(directory)
        make_fixture(ROOT, root)
        if (name or control_for) == 'R386_NATIVE_STALE_SUITE_SOURCE':
            fixture = NativeRegistryContract('test_cost_import_requires_original_archive_and_run_job_identity')
            fixture.root = root
            responses, arguments = fixture.ci_fixture()
            registry.import_ci_cost(root, root, **arguments, fetch=responses.__getitem__)
        observed = registry.expected(root)['suites']
        if name:
            withdraw(root, name)
        try:
            validate_fixture(root, observed)
            # The fixture shares the real Git objects; its sealed catalog must
            # still be re-derivable from the migration base's original tables.
            registry.verify_legacy_execution(root, registry._execution_catalog(root)['base_sha'])
            if (name or control_for) == 'R386_NATIVE_TWO_SHARDS_OVERLAP':
                suites = [SimpleNamespace(name='a'), SimpleNamespace(name='b')]
                parts = [[suites[0]], suites if name else [suites[1]]]
                native_shards.validate_partition(suites, parts)
        except ValueError as exc:
            raise AssertionError((name or 'baseline') + ': ' + str(exc)) from exc


def main():
    assert registry is not None, 'R386_NATIVE_FRAGMENT_CONTRACT: deterministic registry loader is absent'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe', action='store_true')
    parser.add_argument('--withdraw', choices=WITHDRAWALS)
    parser.add_argument('--probe-for', choices=WITHDRAWALS)
    args = parser.parse_args()
    if args.probe or args.withdraw or args.probe_for:
        marker = WITHDRAWAL_MARKERS.get(args.withdraw)
        try:
            named_probe(args.withdraw, args.probe_for)
        except AssertionError as exc:
            if marker and marker not in str(exc):
                print('R386_NATIVE_WITHDRAWAL_WRONG_ASSERTION: expected %s, got %s' % (marker, exc))
                return 3
            raise
        print('R386 native registry named control passed')
        return 0
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeRegistryContract)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun != 22 or result.skipped:
        raise AssertionError('R386_NATIVE_CONTRACT_EXACT_22_NO_SKIP')
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
