#!/usr/bin/env python3
"""Use the original unittest loader and retain compiler evidence before cleanup."""
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys
import unittest

source, out, recipe_path = map(Path, sys.argv[1:])
recipe = json.loads(recipe_path.read_text(encoding='utf-8'))
sys.path.insert(0, str(source))
modules = [importlib.import_module(name) for name in recipe['modules']]
module_suites = [unittest.defaultTestLoader.loadTestsFromModule(module) for module in modules]
discovered_counts = {module.__name__: suite.countTestCases() for module, suite in zip(modules, module_suites)}
def test_ids(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from test_ids(item)
        else:
            yield item.id()
planned = list(test_ids(unittest.TestSuite(module_suites)))
(out / 'test-discovery.json').write_text(json.dumps({'modules': discovered_counts, 'tests': planned}, indent=2) + '\n', encoding='utf-8')
if len(planned) != recipe['expected_tests'] or len(set(planned)) != len(planned):
    raise RuntimeError('Original discovery differs from the predeclared count or duplicates a test')
if recipe.get('module_counts') is not None and recipe['module_counts'] != discovered_counts:
    raise RuntimeError('Original per-module discovery differs from the predeclared counts')
class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subtests_by_test = {}
    def addSubTest(self, test, subtest, error):
        counts = self.subtests_by_test.setdefault(test.id(), {'passed': 0, 'failed': 0})
        counts['passed' if error is None else 'failed'] += 1
        super().addSubTest(test, subtest, error)
suite = unittest.TestSuite(module_suites)
result = unittest.TextTestRunner(verbosity=2, resultclass=RecordedResult).run(suite)
build = importlib.import_module('tests.test_geo261_native_kernel')._BUILD
artifacts = {}
if build is not None:
    for path in sorted(build.work.rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(build.work)
        artifacts[str(relative)] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size}
        if path.suffix in ('.json', '.c', '.h', '.cmd', '.scene'):
            target = out / 'native-build-inputs' / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    (out / 'native-build-artifacts.json').write_text(json.dumps(artifacts, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
summary = {'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
           'failed_tests': [test.id() for test, _ in result.failures], 'error_tests': [test.id() for test, _ in result.errors],
           'skipped': result.skipped, 'expected_failures': len(result.expectedFailures),
           'unexpected_successes': len(result.unexpectedSuccesses), 'successful': result.wasSuccessful(),
           'discovered_modules': discovered_counts, 'subtests_by_test': result.subtests_by_test,
           'compiler_commands': len(build.logs) if build is not None else 0, 'build_artifact_count': len(artifacts)}
(out / 'test-result.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
strict_pass = (result.wasSuccessful() and result.testsRun == recipe['expected_tests'] and not result.skipped
               and not result.expectedFailures and not result.unexpectedSuccesses)
sys.exit(0 if strict_pass else 1)
