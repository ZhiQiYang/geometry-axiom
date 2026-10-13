"""Unittest child runner: preserve terminal exception data separately from printed tracebacks."""
from __future__ import annotations

import argparse
from contextlib import nullcontext
import importlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


class ExceptionResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.executed = []
        self.passed = []
        self.events = []

    def startTest(self, test):
        self.executed.append(test.id())
        super().startTest(test)

    def addSuccess(self, test):
        self.passed.append(test.id())
        super().addSuccess(test)

    def exception(self, test, err, kind, subtest=None):
        self.events.append(dict(test_id=test.id(), subtest_id=subtest.id() if subtest is not None else None,
                                kind=kind, exception_type=err[0].__module__+'.'+err[0].__qualname__,
                                message=str(err[1])))

    def addFailure(self, test, err):
        self.exception(test, err, 'failure')
        super().addFailure(test, err)

    def addError(self, test, err):
        self.exception(test, err, 'error')
        super().addError(test, err)

    def addSubTest(self, test, subtest, err):
        if err is not None:
            kind = 'failure' if issubclass(err[0], test.failureException) else 'error'
            self.exception(test, err, kind, subtest)
        super().addSubTest(test, subtest, err)


def run_tests(names, receipt):
    suite = unittest.defaultTestLoader.loadTestsFromNames(names)
    result = unittest.TextTestRunner(verbosity=2, resultclass=ExceptionResult).run(suite)
    value = dict(schema='section-profile-exceptions/1', requested=list(names), executed=result.executed,
                 passed=result.passed, tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                 skipped=len(result.skipped), expected_failures=len(result.expectedFailures),
                 unexpected_successes=len(result.unexpectedSuccesses), events=result.events)
    Path(receipt).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if result.wasSuccessful() else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', required=True)
    parser.add_argument('--bridge')
    parser.add_argument('names', nargs='+')
    args = parser.parse_args(argv)
    # Model faults run in a disposable copy; import its tests and producer, not the checkout's modules.
    sys.path.insert(0, str(Path.cwd()))
    context = nullcontext()
    if args.bridge:
        module = importlib.import_module('tests.test_section_profile_native')
        context = patch.object(module, 'find_bridge', return_value=args.bridge)
    with context:
        return run_tests(args.names, args.receipt)


if __name__ == '__main__':
    sys.exit(main())
