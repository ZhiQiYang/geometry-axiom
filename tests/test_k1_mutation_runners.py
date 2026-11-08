"""R354-03：突變必須命中唯一位置並由指定測試的斷言偵測。"""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tests' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MutationRunners(unittest.TestCase):
    def test_native_anchors_are_unique_in_current_owner(self):
        runner = load('mutate_k1_terminal')
        for name, filename, before, after, method in runner.CASES:
            with self.subTest(case=name):
                self.assertEqual((ROOT / filename).read_bytes().count(before.encode()), 1)
                self.assertNotEqual(before, after)
                self.assertTrue(method.startswith('test_'))

    def test_frontend_anchors_are_unique_in_current_owner(self):
        runner = load('mutate_k1_frontend')
        for name, filename, before, after, pattern in runner.CASES:
            with self.subTest(case=name):
                self.assertEqual((ROOT / 'geometry-web' / filename).read_text().count(before), 1)
                self.assertNotEqual(before, after)
                self.assertTrue(pattern)

    def test_native_requires_named_assertion_not_compiler_error_or_crash(self):
        judge = load('mutate_k1_terminal').killed_by_named_assertion
        good = 'FAIL: test_leaf (tests.Terminal.test_leaf)\nAssertionError: wrong leaf\nFAILED (failures=1)'
        self.assertTrue(judge(1, good, 'test_leaf'))
        for code, log in [(0, good), (-11, good), (1, good.replace('test_leaf', 'test_other')),
                          (1, good + '\nerrors=1'), (1, good + '\nskipped=1'),
                          (1, good + '\nAddressSanitizer'), (1, good + '\nruntime error:'),
                          (1, good + '\nBridgeClosed'), (1, good + '\nSegmentation fault'),
                          (1, 'collect2: error: ld returned 1 exit status')]:
            with self.subTest(code=code, log=log):
                self.assertFalse(judge(code, log, 'test_leaf'))

    def test_frontend_requires_matching_named_assertion_not_runtime_failure(self):
        judge = load('mutate_k1_frontend').classify_failure
        good = 'not ok 1 - T17 archive roundtrip\n name: AssertionError\n'
        self.assertEqual(judge(1, good, 'T17 archive'), 'assertion')
        for code, log in [(0, good), (-11, good), (1, good.replace('T17 archive', 'other test')),
                          (1, 'not ok 1 - T17 archive\nError: unknown'),
                          *[(1, good + token) for token in ('SyntaxError', 'MODULE_NOT_FOUND', 'ReferenceError', 'TypeError', 'uncaughtException', 'unhandledRejection')]]:
            with self.subTest(code=code, log=log):
                self.assertIsNone(judge(code, log, 'T17 archive'))


if __name__ == '__main__':
    unittest.main()
