#!/usr/bin/env python3
"""R433 test-only closure/receipt regressions. No Chrome, native build or ME."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def load(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FragmentedRunners(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = load('tests/canvas_touch_regression.py', 'r433_fragment_original')

    def test_exact_module_scope_rejects_retired_or_wrong_selection(self):
        result = {'scope': {'mode': 'partial', 'filters': ['GEOMETRY_CANVAS_MODULE_ONLY'],
                           'module': 'P1162', 'modifiers': [], 'acceptance': False}}
        self.assertTrue(self.original.module_scope(result))
        for field, value in (('mode', 'full'), ('filters', ['GEOMETRY_CANVAS_TOUCH_ONLY']),
                             ('module', 'P999'), ('modifiers', ['anything']), ('acceptance', True)):
            with self.subTest(field=field):
                wrong = copy.deepcopy(result)
                wrong['scope'][field] = value
                self.assertFalse(self.original.module_scope(wrong))

    def test_registry_cannot_smuggle_a_product_into_test_overlay(self):
        forged = subprocess.CompletedProcess([], 0, stdout=json.dumps(
            {'extensions': ['P1162'], 'files': ['geometry-web/app.js']}).encode(), stderr=b'')
        with patch.object(self.original.subprocess, 'run', return_value=forged):
            with self.assertRaisesRegex(RuntimeError, 'unreviewed or product file'):
                self.original.test_overlay(ROOT)

    def test_historical_product_plus_real_fragment_closure_is_loadable(self):
        with tempfile.TemporaryDirectory(prefix='r433-overlay-test-') as directory:
            source = Path(directory) / 'source'
            manifest = self.original.baseline(source, self.original.BASE)
            self.assertTrue(manifest['productOutsideOverlayUnchanged'])
            self.assertEqual(manifest['historicalProductBase'], self.original.BASE)
            self.assertEqual(set(manifest['files']), set(self.original.test_overlay(ROOT)))
            for relative in ('geometry-web/app.js', 'geometry-web/start_local.py', '公理層.md'):
                wanted = subprocess.check_output(['git', 'show', self.original.BASE + ':' + relative], cwd=ROOT)
                self.assertEqual((source / relative).read_bytes(), wanted, relative)
            for relative in self.original.test_overlay(ROOT):
                self.assertEqual((source / relative).read_bytes(), (ROOT / relative).read_bytes(), relative)
            # This calls the actual #434 loader and strict transitive JS parser
            # against the historical snapshot, not a fabricated closure list.
            self.assertEqual(self.original.test_overlay(source), self.original.test_overlay(ROOT))
            (source / 'geometry-web/cdp_navigation.js').unlink()
            with self.assertRaises(subprocess.CalledProcessError):
                self.original.test_overlay(source)

    def test_historical_diagnostic_executes_pinned_old_authority(self):
        historical = load('tests/diagnostics/r433_original_release.py', 'r433_fragment_historical')
        sources = historical.historical_sources()
        authority = historical.load_runner(sources)
        self.assertEqual(authority.TEST_OVERLAY, ('geometry-web/cdp_test.js', 'geometry-web/canvas_touch_test.js'))
        self.assertTrue(authority.run.__code__.co_filename.endswith('@' + historical.OLD))
        self.assertNotEqual((ROOT / historical.DRIVER).read_bytes(), sources[historical.DRIVER])

    def test_own_scroll_predicates_keep_registration_red_invalid(self):
        own = load('tests/diagnostics/r433_sheet_own_scroll.py', 'r433_fragment_own_scroll')
        self.assertNotEqual(own.NAME, self.original.MUTANT)
        self.assertEqual(own.self_test(self.original), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
