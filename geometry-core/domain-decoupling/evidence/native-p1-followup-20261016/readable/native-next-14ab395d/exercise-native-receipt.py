#!/usr/bin/env python3
"""Run original tests once; retain separate groups and actual failure details."""
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import traceback
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
if len(planned) != recipe['expected_tests'] or len(set(planned)) != len(planned):
    raise RuntimeError('Original discovery differs from the predeclared count or duplicates a test')
if recipe['module_counts'] != discovered_counts:
    raise RuntimeError('Original per-module discovery differs from the predeclared counts')
group_modules = [module for group in recipe['groups'].values() for module in group]
if len(group_modules) != len(set(group_modules)) or set(group_modules) != set(discovered_counts):
    raise RuntimeError('Declared group coverage overlaps or omits original modules')
if {name: sum(discovered_counts[module] for module in modules) for name, modules in recipe['groups'].items()} != recipe['group_counts']:
    raise RuntimeError('Declared group totals differ from actual discovery')
(out / 'test-discovery.json').write_text(json.dumps({'modules': discovered_counts, 'tests': planned, 'groups': recipe['groups']}, indent=2) + '\n', encoding='utf-8')


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subtests_by_test = {}
        self.outcomes = {name: 'not-started' for name in planned}
        self.failure_details = []

    def startTest(self, test):
        self.outcomes[test.id()] = 'started'
        super().startTest(test)

    def addSuccess(self, test):
        self.outcomes[test.id()] = 'passed'
        super().addSuccess(test)

    def record_failure(self, test, error, classification, subtest=None):
        message = str(error[1])
        if message.startswith('Native compile/link failed (not a valid negative control):'):
            classification = 'native-compile-or-link-failure'
        elif isinstance(error[1], subprocess.TimeoutExpired):
            classification = 'process-timeout'
        elif isinstance(error[1], OSError):
            classification = 'process-or-filesystem-error'
        elif message.startswith('K process failed, not a numerical rejection:'):
            classification = 'native-process-failure'
        self.failure_details.append({'test': test.id(), 'subtest': subtest, 'classification': classification,
                                     'exceptionType': error[0].__name__, 'message': message,
                                     'traceback': ''.join(traceback.format_exception(*error))})

    def addFailure(self, test, error):
        self.outcomes[test.id()] = 'failed'
        self.record_failure(test, error, 'test-assertion-failure')
        super().addFailure(test, error)

    def addError(self, test, error):
        self.outcomes[test.id()] = 'error'
        self.record_failure(test, error, 'setup-or-test-exception')
        super().addError(test, error)

    def addSkip(self, test, reason):
        self.outcomes[test.id()] = 'skipped'
        super().addSkip(test, reason)

    def addExpectedFailure(self, test, error):
        self.outcomes[test.id()] = 'expected-failure'
        super().addExpectedFailure(test, error)

    def addUnexpectedSuccess(self, test):
        self.outcomes[test.id()] = 'unexpected-success'
        super().addUnexpectedSuccess(test)

    def addSubTest(self, test, subtest, error):
        counts = self.subtests_by_test.setdefault(test.id(), {'passed': 0, 'failed': 0})
        counts['passed' if error is None else 'failed'] += 1
        if error is not None:
            self.outcomes[test.id()] = 'failed'
            self.record_failure(test, error, 'subtest-assertion-or-exception', str(subtest))
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
groups = {}
for name, member_modules in recipe['groups'].items():
    selected = {test: status for test, status in result.outcomes.items()
                if any(test.startswith(module + '.') or module + '.' in test for module in member_modules)}
    groups[name] = {'expected': recipe['group_counts'][name], 'discovered': sum(discovered_counts[module] for module in member_modules),
                    'outcomes': selected,
                    'counts': {status: sum(value == status for value in selected.values()) for status in sorted(set(selected.values()))},
                    'failureDetails': [row for row in result.failure_details if row['test'] in selected]}
summary = {'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
           'failed_tests': [test.id() for test, _ in result.failures], 'error_tests': [test.id() for test, _ in result.errors],
           'skipped': result.skipped, 'expected_failures': len(result.expectedFailures),
           'unexpected_successes': len(result.unexpectedSuccesses), 'successful': result.wasSuccessful(),
           'discovered_modules': discovered_counts, 'groups': groups, 'outcomes': result.outcomes,
           'failure_details': result.failure_details, 'subtests_by_test': result.subtests_by_test,
           'compiler_commands': len(build.logs) if build is not None else 0, 'build_artifact_count': len(artifacts)}
(out / 'test-result.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
strict_pass = (result.wasSuccessful() and result.testsRun == recipe['expected_tests'] and not result.skipped
               and not result.expectedFailures and not result.unexpectedSuccesses
               and all(value == 'passed' for value in result.outcomes.values()))
sys.exit(0 if strict_pass else 1)
