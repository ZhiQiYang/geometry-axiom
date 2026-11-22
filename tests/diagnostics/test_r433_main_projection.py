#!/usr/bin/env python3
"""R433 source gate regression after the exact R13 main merge; never Chrome.

Exercise execute() through its real source guard with memory-only candidate
fingerprints. Stop at native_inputs, before any native build or browser run.
The Chromium identity and snapshot copies are synthetic; no result is browser
acceptance and no source, golden, receipt or cost file is written to the repo.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
OLD = '82b7b76526ab9e926ac2d6eb4e3f3de1163155b5'
MAIN = '883e68688f6480a5f1de6e86e6a056cc20339cb9'
STOP = 'R433_STOP_AFTER_SOURCE_GUARD_BEFORE_NATIVE_OR_CHROME'
EXPECTED_MAIN_PATHS = (
    'geometry-core/card-reference/run_axiom_mutations.py',
    'geometry-core/domain-decoupling/product-architecture.d/exclusions/geometry-core/card-reference/run_axiom_mutations.py.json',
    'geometry-core/modeling/__init__.py',
    'geometry-guide/公理層-白話.md',
    'geometry-guide/公理層-閱讀器.html',
    'tests/fixtures/q38j-b-native-model.json',
    'tests/fixtures/r13-approved-delta.json',
    'tests/fixtures/r13-main-3ef07683/card.json',
    'tests/fixtures/r13-main-3ef07683/profile.json',
    'tests/fixtures/r13-main-3ef07683/provenance.json',
    'tests/fixtures/r13-main-3ef07683/stagger.json',
    'tests/make_r13_approved_delta.py',
    'tests/mutation_r14_repeat_panel.py',
    'tests/test_domain_decoupling_adoption.py',
    'tests/test_engineering_model_compatibility.py',
    '公理層.md',
)


def load_runner():
    spec = importlib.util.spec_from_file_location('r433_main_projection_runner',
        ROOT / 'tests/diagnostics/r433_sheet_own_scroll.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReviewedMainProjection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = load_runner()
        cls.original, cls.pins = cls.runner.pinned_runner(ROOT)
        actual = cls.original.fingerprint(ROOT)
        # The regression itself is not part of the already-published candidate
        # being replayed. Its addition must not be the reason for T's red.
        cls.control = {name: row for name, row in actual.items()
            if name != 'tests/diagnostics/test_r433_main_projection.py'
                and cls.original.wanted(name) and (name.split('/')[0] in cls.original.DIRECTORIES
                or name in cls.original.ROOT_FILES or '/' not in name and Path(name).suffix in {'.h', '.inc'})}

    def probe(self, control):
        runner, original = self.runner, self.original
        product = (ROOT / runner.PRODUCT).read_bytes()
        with tempfile.TemporaryDirectory(prefix='r433-main-gate-') as temp:
            out = Path(temp) / 'proof'

            def candidate(destination):
                target = destination / runner.PRODUCT
                target.parent.mkdir(parents=True)
                target.write_bytes(product)

            def fingerprint(source):
                result = copy.deepcopy(control)
                if source != ROOT:
                    result[runner.PRODUCT] = runner.identity((source / runner.PRODUCT).read_bytes())
                return result

            args = argparse.Namespace(root=ROOT, out=out, binary_dir=None)
            with patch.object(original, 'candidate', side_effect=candidate), \
                    patch.object(original, 'fingerprint', side_effect=fingerprint), \
                    patch.object(runner, 'chrome_identity', return_value={'synthetic': True}), \
                    patch.object(runner, 'native_inputs', side_effect=RuntimeError(STOP)) as native:
                code = runner.execute(args, original, self.pins)
                report = json.loads((out / 'summary.json').read_text())
            self.assertEqual(code, 2, 'This synthetic stop must never claim Chrome acceptance')
            self.assertEqual(report['runs'], [], 'No native or Chrome phase may execute')
            self.assertTrue(report['checkoutUnchanged'])
            return native.called, report

    def test_exact_main_merge_reaches_source_gate_exit_before_chrome(self):
        reached, report = self.probe(self.control)
        self.assertTrue(reached, 'R433_MAIN_MERGE_REPLAYABLE_BEFORE_CHROME: ' + repr(report['problems']))
        self.assertEqual(report['problems'], [STOP])
        self.assertEqual(report['fixedBase'], OLD, 'R433_ORIGINAL_BASE_AUTHORITY_RETAINED')
        self.assertEqual(report['mainProjection']['main'], MAIN)
        self.assertEqual(tuple(report['mainProjection']['paths']), EXPECTED_MAIN_PATHS,
                         'R433_MAIN_PROJECTION_EXACT_16_PATHS')
        for name, row in report['mainProjection']['paths'].items():
            self.assertEqual(row['after'], self.control[name]['blob'], name)

    def test_one_extra_byte_in_adopted_main_source_is_rejected(self):
        changed = copy.deepcopy(self.control)
        name = 'geometry-core/modeling/__init__.py'
        changed[name] = self.runner.identity((ROOT / name).read_bytes() + b'\n')
        reached, report = self.probe(changed)
        self.assertFalse(reached, 'R433_MAIN_ADOPTION_BYTES_MUST_MATCH')
        self.assertTrue(any(name in problem for problem in report['problems']))

    def test_missing_adopted_main_source_is_rejected(self):
        changed = copy.deepcopy(self.control)
        name = 'tests/fixtures/r13-approved-delta.json'
        del changed[name]
        reached, report = self.probe(changed)
        self.assertFalse(reached, 'R433_MAIN_ADOPTION_FILE_REQUIRED')
        self.assertTrue(any(name in problem for problem in report['problems']))

    def test_unlisted_new_product_path_is_rejected(self):
        changed = copy.deepcopy(self.control)
        name = 'geometry-web/r433-unreviewed-product.js'
        changed[name] = self.runner.identity(b'// unreviewed source\n')
        reached, report = self.probe(changed)
        self.assertFalse(reached, 'R433_UNLISTED_SOURCE_MUST_STILL_BE_REJECTED')
        self.assertTrue(any('Runtime source differs outside the reviewed fragment conversion' in problem
                            and name in problem for problem in report['problems']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
