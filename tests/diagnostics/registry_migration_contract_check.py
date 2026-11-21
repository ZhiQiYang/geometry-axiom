#!/usr/bin/env python3
"""R386 migration contract; explicit CI guard, not an unmeasured native suite."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / 'tests/registry_migrate.py'


def load_tool():
    assert TARGET.is_file(), 'R386_REGISTRY_MIGRATOR_MISSING'
    spec = importlib.util.spec_from_file_location('registry_migration_under_test', TARGET)
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    return tool


class MigrationContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = load_tool()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='registry-contract-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_canonical_lf_and_order(self):
        self.assertEqual(self.tool.canonical({'乙': 2, 'a': 1}),
                         self.tool.canonical({'a': 1, '乙': 2}))
        self.assertNotIn(b'\r', self.tool.canonical({'value': 'line\nbreak'}))
        self.assertTrue(self.tool.canonical({'a': 1}).endswith(b'\n'))

    def test_duplicate_json_key_is_not_last_writer_wins(self):
        path = self.root / 'duplicate.json'
        path.write_bytes(b'{"count": 12, "count": 1}\n')
        with self.assertRaisesRegex(ValueError, 'R386_DUPLICATE_JSON_KEY'):
            self.tool.read_json(path)

    def test_unsafe_and_symlink_paths(self):
        for relative in ('../outside', '/absolute', 'a/../b', 'a//b', 'a\\b'):
            with self.subTest(relative=relative):
                with self.assertRaisesRegex(ValueError, 'R386_UNSAFE_PATH'):
                    self.tool.safe_path(self.root, relative)
        outside = self.root / 'outside'
        outside.mkdir()
        (self.root / 'link').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'R386_SYMLINK_NOT_ALLOWED'):
            self.tool.safe_path(self.root, 'link/new.json')

    def test_manifest_carries_real_git_blob_identity(self):
        raw = b'{"count":13}\n'
        actual = subprocess.run(['git', 'hash-object', '--stdin'], input=raw,
                                capture_output=True, check=True).stdout.decode().strip()
        self.assertEqual(self.tool.digest(raw)['blob'], actual)
        self.assertEqual(self.tool.digest(raw)['bytes'], len(raw))

    def test_immutable_receipt_v1_cannot_be_silently_relabelled(self):
        path = self.root / '.github/scripts/evidence_architecture.py'
        path.parent.mkdir(parents=True)
        raw = b'GENERATOR_LF_SHA256 = "old-reviewed-generator"\n'
        path.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, 'R386_IMMUTABLE_ARCHITECTURE_ADAPTER_REQUIRED'):
            self.tool.immutable_architecture_boundary(self.root)
        self.assertEqual(path.read_bytes(), raw)

    def test_existing_canvas_layout_cannot_regenerate_a_missing_archive(self):
        # Returning old aggregate files must not turn a broken migrated tree
        # into a fresh migration. Exercise the real canvas guard through CLI.
        for relative in ('geometry-web/canvas_shards.json', 'geometry-web/cdp_sections.golden.json'):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'{}\n')
        for relative in (self.tool.MARKER, 'geometry-web/canvas-registry',
                         'geometry-web/cdp_sections.d', 'geometry-web/canvas_sections'):
            with self.subTest(marker=relative):
                path = self.root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.suffix == '.json':
                    path.write_bytes(self.tool.canonical(self.tool.LAYOUT))
                else:
                    path.mkdir()
                try:
                    with mock.patch.object(self.tool, 'git_head', return_value='a' * 40):
                        with self.assertRaisesRegex(ValueError, 'R386_CHILD_FAILED: .*canvas_registry.js check'):
                            self.tool.make_plan(self.root, 'a' * 40)
                finally:
                    if path.is_dir():
                        path.rmdir()
                    else:
                        path.unlink()
        self.assertEqual((self.root / 'geometry-web/canvas_shards.json').read_bytes(), b'{}\n')
        self.assertFalse((self.root / 'geometry-web/canvas-registry/legacy.json').exists())

    def test_ci_trust_requires_real_test_merge_second_parent(self):
        env = {'GITHUB_ACTIONS': 'true', 'EVENT_NAME': 'pull_request',
               'GITHUB_SHA': 'a' * 40, 'PR_HEAD': 'b' * 40}
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(self.tool, 'git_head', return_value='a' * 40), \
                mock.patch.object(self.tool, 'run', return_value='c' * 40 + '\n'):
            with self.assertRaisesRegex(ValueError, 'R386_CI_TEST_MERGE_SECOND_PARENT'):
                self.tool.trusted_base(self.root)

    def test_ci_trust_uses_first_parent_after_identity_check(self):
        env = {'GITHUB_ACTIONS': 'true', 'EVENT_NAME': 'pull_request',
               'GITHUB_SHA': 'a' * 40, 'PR_HEAD': 'b' * 40}
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(self.tool, 'git_head', return_value='a' * 40), \
                mock.patch.object(self.tool, 'run', side_effect=['b' * 40 + '\n', 'c' * 40 + '\n']):
            self.assertEqual(self.tool.trusted_base(self.root),
                             {'sha': 'c' * 40, 'source': 'verified-test-merge-first-parent'})

    def test_manual_capture_has_no_implicit_trust_anchor(self):
        env = {'GITHUB_ACTIONS': 'true', 'EVENT_NAME': 'workflow_dispatch',
               'GITHUB_SHA': 'a' * 40, 'GITHUB_REF': 'refs/heads/main'}
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(self.tool, 'git_head', return_value='a' * 40):
            self.assertIsNone(self.tool.trusted_base(self.root)['sha'])

    def transaction(self):
        original = self.root / 'geometry-web/canvas_shards.json'
        original.parent.mkdir(parents=True)
        original.write_bytes(b'{"old":true}\n')
        rel = 'tests/suites.d/py__a.json'
        payloads = {rel: b'{"count":1}\n', self.tool.MARKER: self.tool.canonical(self.tool.LAYOUT)}
        report = {'schema': self.tool.SCHEMA, 'base_sha': 'a' * 40,
                  'inputs': self.tool.source_paths(self.root), 'files': [
                      {'path': rel, 'before': None, 'after': self.tool.digest(payloads[rel])},
                      {'path': self.tool.MARKER, 'before': None,
                       'after': self.tool.digest(payloads[self.tool.MARKER])},
                      {'path': original.relative_to(self.root).as_posix(),
                       'before': self.tool.digest(original.read_bytes()), 'after': None},
                  ]}
        return payloads, [original.relative_to(self.root).as_posix()], report

    def test_atomic_validation_precedes_any_source_write(self):
        payloads, retired, report = self.transaction()
        with mock.patch.object(self.tool, 'git_head', return_value='a' * 40), \
                mock.patch.object(self.tool, 'validate_overlay', side_effect=ValueError('invalid canvas count')):
            with self.assertRaisesRegex(ValueError, 'invalid canvas count'):
                self.tool.apply_plan(self.root, payloads, retired, report)
        self.assertEqual((self.root / retired[0]).read_bytes(), b'{"old":true}\n')
        self.assertFalse((self.root / self.tool.MARKER).exists())
        self.assertFalse((self.root / self.tool.PENDING).exists())

    def test_overlay_keeps_inventoried_source_inside_nested_evidence(self):
        relative = 'geometry-core/domain-decoupling/evidence/native-p1-20261016/extract_evidence.py'
        script = self.root / relative
        script.parent.mkdir(parents=True)
        script.write_bytes(b'# inventoried executable source\n')
        archive = self.root / 'evidence/large-historical-log'
        archive.parent.mkdir()
        archive.write_bytes(b'not required by this source overlay')

        def command(argv, *, cwd, **kwargs):
            if argv[0] == 'git':
                return str(self.root / '.git') + '\n'
            self.assertEqual((Path(cwd) / relative).read_bytes(), script.read_bytes())
            self.assertFalse((Path(cwd) / 'evidence').exists())
            return '{}\n'

        with mock.patch.object(self.tool, 'run', side_effect=command):
            self.tool.validate_overlay(self.root, {}, [])

    def test_mid_write_failure_restores_sources(self):
        payloads, retired, report = self.transaction()
        replace = self.tool._replace

        def fail_marker(path, raw):
            if path == self.root / self.tool.MARKER:
                raise OSError('injected failed final marker write')
            return replace(path, raw)

        with mock.patch.object(self.tool, 'git_head', return_value='a' * 40), \
                mock.patch.object(self.tool, '_replace', side_effect=fail_marker):
            with self.assertRaisesRegex(OSError, 'injected failed final marker'):
                self.tool.apply_plan(self.root, payloads, retired, report, validate=False)
        self.assertEqual((self.root / retired[0]).read_bytes(), b'{"old":true}\n')
        self.assertFalse((self.root / 'tests/suites.d').exists())
        self.assertFalse((self.root / self.tool.PENDING).exists())

    def test_changes_during_overlay_validation_are_not_overwritten(self):
        payloads, retired, report = self.transaction()

        def changed_during_validation(*args, **kwargs):
            (self.root / retired[0]).write_bytes(b'{"later":"edit during validation"}\n')

        with mock.patch.object(self.tool, 'git_head', return_value='a' * 40), \
                mock.patch.object(self.tool, 'validate_overlay', side_effect=changed_during_validation):
            with self.assertRaisesRegex(ValueError, 'R386_SOURCE_CHANGED_BEFORE_APPLY'):
                self.tool.apply_plan(self.root, payloads, retired, report)
        self.assertEqual((self.root / retired[0]).read_bytes(), b'{"later":"edit during validation"}\n')
        self.assertFalse((self.root / self.tool.PENDING).exists())

    def test_killed_preparation_has_a_safe_recovery_path(self):
        payloads, retired, report = self.transaction()
        journal = self.root / self.tool.PENDING
        journal.mkdir(parents=True)
        self.tool.recover(self.root)  # killed immediately after mkdir
        journal.mkdir()
        (journal / '.registry-write-interrupted').write_bytes(b'partial prepare write')
        (journal / 'prepare.json').write_bytes(self.tool.canonical({
            'schema': self.tool.SCHEMA, 'state': 'preparing'}))
        backup = journal / 'before' / retired[0]
        backup.parent.mkdir(parents=True)
        backup.write_bytes(b'incomplete backup')
        self.tool.recover(self.root)
        self.assertEqual((self.root / retired[0]).read_bytes(), b'{"old":true}\n')
        self.assertFalse(journal.exists())

    def test_recovery_removes_only_reserved_interrupted_write_files(self):
        payloads, retired, report = self.transaction()
        journal = self.root / self.tool.PENDING
        journal.mkdir(parents=True)
        (journal / 'journal.json').write_bytes(self.tool.canonical({
            'schema': self.tool.SCHEMA, 'files': report['files']}))
        for row in report['files']:
            if row['before'] is not None:
                backup = journal / 'before' / row['path']
                backup.parent.mkdir(parents=True)
                backup.write_bytes((self.root / row['path']).read_bytes())
        target = self.root / 'tests/suites.d'
        target.mkdir(parents=True)
        (target / '.registry-write-interrupted').write_bytes(b'partial output')
        untouched = self.root / 'keep-user-file'
        untouched.write_bytes(b'keep')
        self.tool.recover(self.root)
        self.assertFalse(target.exists())
        self.assertEqual(untouched.read_bytes(), b'keep')

    def test_changed_source_between_plan_and_apply_refused(self):
        payloads, retired, report = self.transaction()
        (self.root / retired[0]).write_bytes(b'{"old":"changed"}\n')
        with self.assertRaisesRegex(ValueError, 'R386_SOURCE_CHANGED_BEFORE_APPLY'):
            self.tool.apply_plan(self.root, payloads, retired, report, validate=False)
        self.assertFalse((self.root / 'tests/suites.d').exists())

    def test_recover_refuses_to_destroy_subsequent_edits(self):
        payloads, retired, report = self.transaction()
        journal = self.root / self.tool.PENDING
        journal.mkdir(parents=True)
        (journal / 'journal.json').write_bytes(self.tool.canonical({
            'schema': self.tool.SCHEMA, 'files': report['files']}))
        for row in report['files']:
            if row['before'] is not None:
                backup = journal / 'before' / row['path']
                backup.parent.mkdir(parents=True)
                backup.write_bytes((self.root / row['path']).read_bytes())
        changed = self.root / 'tests/suites.d/py__a.json'
        changed.parent.mkdir(parents=True)
        changed.write_bytes(b'{"later":"user edit"}\n')
        with self.assertRaisesRegex(ValueError, 'R386_RECOVERY_REFUSES_LATER_EDIT'):
            self.tool.recover(self.root)
        self.assertEqual(changed.read_bytes(), b'{"later":"user edit"}\n')

    def test_no_timestamp_or_absolute_directory_in_export(self):
        payloads = {'tests/suites.d/py__a.json': self.tool.canonical({'count': 3})}
        report = {'schema': self.tool.SCHEMA, 'base_sha': 'b' * 40,
                  'files': [{'path': next(iter(payloads)), 'after': self.tool.digest(next(iter(payloads.values())))}]}
        for name in ('one', 'different-root'):
            self.tool.export_plan(payloads, report, self.root / name)
        a = self.root / 'one'
        b = self.root / 'different-root'
        for path in a.rglob('*'):
            if path.is_file():
                self.assertEqual(path.read_bytes(), (b / path.relative_to(a)).read_bytes())
        self.assertNotIn(str(self.root).encode(), (a / 'manifest.json').read_bytes())

    def test_two_branches_add_different_fragments_merge_in_both_orders(self):
        def git(*argv):
            return subprocess.run(['git', '-C', str(self.root), *argv], check=True,
                                  capture_output=True, text=True).stdout.strip()

        git('init', '-q', '-b', 'base')
        git('config', 'user.name', 'R386 contract')
        git('config', 'user.email', 'registry-contract@example.invalid')
        (self.root / 'baseline').write_text('unchanged\n')
        git('add', 'baseline')
        git('commit', '-qm', 'base')
        base = git('rev-parse', 'HEAD')
        for name in ('a', 'b'):
            git('checkout', '-qb', name, base)
            path = self.root / f'tests/suites.d/py__{name}.json'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(self.tool.canonical({'name': name, 'count': 7}))
            git('add', str(path.relative_to(self.root)))
            git('commit', '-qm', 'add ' + name)
        trees = []
        for left, right in (('a', 'b'), ('b', 'a')):
            git('checkout', '--detach', left)
            git('merge', '--no-ff', '--no-commit', right)
            self.assertEqual(sorted(p.name for p in (self.root / 'tests/suites.d').glob('*.json')),
                             ['py__a.json', 'py__b.json'])
            trees.append(git('write-tree'))
            git('merge', '--abort')
        self.assertEqual(trees[0], trees[1])


if __name__ == '__main__':
    # Before P, report a normal missing-feature assertion, not an import crash.
    if not TARGET.is_file():
        class MissingFeature(unittest.TestCase):
            def test_migrator_available(self):
                self.assertTrue(TARGET.is_file(), 'R386_REGISTRY_MIGRATOR_MISSING')
        unittest.main(defaultTest='MissingFeature', verbosity=2)
    unittest.main(verbosity=2)
