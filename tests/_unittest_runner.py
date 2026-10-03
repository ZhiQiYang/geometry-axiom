#!/usr/bin/env python3
"""Run one tests/test_*.py file in this process and report *test-level* numbers as JSON.

    python tests/_unittest_runner.py tests/test_x.py --json-out result.json [--log run.log]

Why not ``python -m unittest``: a class-level ``SkipTest`` (setUpClass / setUpModule) shows up as
"skipped=1" although it blocked N tests.  Here ``total`` = ``countTestCases()`` and

    skipped = explicit skips (skipTest/skipUnless on a test that really started)
              + tests that never ran because setUpClass/setUpModule raised SkipTest
              + (anything else that never ran: total - run - the two groups above - blocked_by_error)

A module that raises SkipTest while being imported blocks all of its tests: they are counted by reading the file's
AST (``skip_count_basis`` = ``ast``, or ``at-least-1`` when that is impossible).  A file with 0 tests is a failure
(``no_tests``), never a pass.  ``skip_items`` lists every skip with its exact test id, so run_all can match the
platform-inherent ones against a named allowlist instead of a reason regex.

A setUpClass/setUpModule *error* is not a skip: those tests are reported in ``blocked_by_error``
and counted as failed.  The module is loaded by file path with both the repo root and tests/ on
sys.path, so ``from tests import x``, ``import test_reference_contract`` and ``from run_tests import``
all resolve no matter how the file is normally started.  ``unittest.main()`` blocks are not executed.
"""
from __future__ import annotations

import ast
import collections
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import sys
import time
import traceback
import unittest
from unittest import util as unittest_util

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def _first_line(text: str) -> str:
    lines = [line for line in str(text).strip().splitlines() if line.strip()]
    return lines[-1].strip()[:300] if lines else ''


def _class_key(test) -> str:
    return unittest_util.strclass(test.__class__)


def _iter_tests(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _iter_tests(item)
        else:
            yield item


def _count_test_methods_ast(path: Path):
    """Best-effort count of the test methods a file *would* have defined, for a module that raised SkipTest at import.

    Returns (count, exact).  Top-level classes count when one of their bases is named ``*TestCase`` or is another such
    class of the same file; inherited ``test*`` methods are counted for each subclass (as unittest does).  Classes that
    inherit from something imported cannot be resolved: when nothing countable is found the answer is (1, False),
    i.e. "at least 1"."""
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'))
    except (OSError, SyntaxError, ValueError):
        return 1, False
    classes = {}

    def collect(body):
        for node in body:
            if isinstance(node, ast.ClassDef):
                classes[node.name] = node
            elif isinstance(node, (ast.If, ast.Try, ast.With)):
                for sub in (getattr(node, 'body', []), getattr(node, 'orelse', []), getattr(node, 'finalbody', [])):
                    collect(sub)
                for handler in getattr(node, 'handlers', []):
                    collect(handler.body)
    collect(tree.body)

    def base_name(expr):
        if isinstance(expr, ast.Name):
            return expr.id
        if isinstance(expr, ast.Attribute):
            return expr.attr
        return ''

    cache = {}

    def effective(name, stack=()):
        """(is_test_case, set of test method names) of a class of this file."""
        if name in cache:
            return cache[name]
        if name in stack or name not in classes:
            return False, set()
        node = classes[name]
        is_test = False
        methods = {n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith('test')}
        for base in node.bases:
            bname = base_name(base)
            if bname.endswith('TestCase'):
                is_test = True
            elif bname in classes:
                sub_is_test, sub_methods = effective(bname, stack + (name,))
                if sub_is_test:
                    is_test = True
                    methods |= sub_methods
        cache[name] = (is_test, methods if is_test else set())
        return cache[name]

    total = sum(len(effective(name)[1]) for name in classes)
    return (total, True) if total else (1, False)


def _holder_info(test):
    """(kind, class-or-module string) for unittest's _ErrorHolder, else None."""
    if type(test).__name__ != '_ErrorHolder':
        return None
    description = getattr(test, 'description', '') or str(test)
    match = re.match(r'(\w+)\s*\((.*)\)\s*$', description)
    return (match.group(1), match.group(2)) if match else (description, '')


def main(argv) -> int:
    args = list(argv)
    json_out = log_path = None
    if '--json-out' in args:
        i = args.index('--json-out')
        json_out = args[i + 1]
        del args[i:i + 2]
    if '--log' in args:
        i = args.index('--log')
        log_path = args[i + 1]
        del args[i:i + 2]
    if len(args) != 1:
        print(__doc__)
        return 64
    target = Path(args[0]).resolve()
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(HERE))
    started = time.time()
    try:
        shown = str(target.relative_to(ROOT)).replace('\\', '/')
    except ValueError:  # a test file outside the repo (e.g. a demo in %TEMP%)
        shown = str(target)
    report = {'file': shown, 'total': 0, 'run': 0, 'passed': 0, 'failed': 0,
              'skipped': 0, 'explicit_skipped': 0, 'unrun_skipped': 0, 'blocked_by_error': 0,
              'failures': [], 'skip_reasons': {}, 'skip_items': [], 'import_error': None}

    def emit(code):
        report['seconds'] = round(time.time() - started, 2)
        if json_out:
            Path(json_out).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
        return code

    stem = target.stem
    spec = importlib.util.spec_from_file_location(stem, target)
    module = importlib.util.module_from_spec(spec)
    sys.modules[stem] = module
    try:
        # Test-only boundary: model-base's product API still accepts a caller's
        # trusted program. Aggregate evidence must verify every native override.
        import binaries
        for binary in binaries.REGISTRY:
            if binary.applicable():
                for var in binary.envs:
                    if os.environ.get(var):
                        binaries.require_fresh(binary.name, os.environ[var])
        spec.loader.exec_module(module)
    except unittest.SkipTest as exc:
        # A SkipTest at import time blocks every test of the file: count them (AST), never just "1".
        count, exact = _count_test_methods_ast(target)
        reason = str(exc)
        report.update(total=count, skipped=count, unrun_skipped=count, skip_reasons={reason: count},
                      skip_items=[{'test': stem, 'reason': reason, 'scope': 'module-import', 'count': count}],
                      skip_count_basis='ast' if exact else 'at-least-1')
        return emit(0)
    except BaseException:  # noqa: BLE001 - an import failure is a failed suite, not a crash of the runner
        report.update(total=1, failed=1, import_error=traceback.format_exc()[-1500:])
        report['failures'].append({'test': stem, 'kind': 'import', 'message': _first_line(report['import_error'])})
        return emit(1)

    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    tests = list(_iter_tests(suite))
    total = suite.countTestCases()
    if total == 0:
        # "0 tests" must never be a pass (empty module, empty TestCase, a load_tests() that returns nothing...)
        report['failures'].append({'test': stem, 'kind': 'no-tests', 'message': '0 tests discovered in this file'})
        report.update(total=0, failed=1, no_tests=True)
        return emit(1)
    per_class = collections.Counter(_class_key(t) for t in tests)
    per_module = total

    log = open(log_path, 'w', encoding='utf-8') if log_path else io.StringIO()
    runner = unittest.TextTestRunner(stream=log, verbosity=1)
    result = runner.run(suite)
    if log_path:
        log.close()

    explicit_skips = collections.Counter()
    skip_items = []   # one entry per skip: the exact test id (scope 'test') or the class/module that blocked N tests
    unrun_skips = 0
    for test, reason in result.skipped:
        holder = _holder_info(test)
        if holder is None:
            explicit_skips[reason] += 1
            skip_items.append({'test': test.id(), 'reason': reason, 'scope': 'test', 'count': 1})
        else:
            kind, where = holder
            n = per_module if kind == 'setUpModule' else per_class.get(where, 0)
            unrun_skips += n
            explicit_skips[reason] += n
            skip_items.append({'test': where or kind, 'reason': reason, 'scope': kind, 'count': n})

    test_level_failed = 0
    blocked = 0
    extra_errors = 0
    failures = []
    for kind, rows in (('failure', result.failures), ('error', result.errors)):
        for test, trace in rows:
            holder = _holder_info(test)
            entry = {'test': test.id() if holder is None else test.description, 'kind': kind, 'message': _first_line(trace)}
            failures.append(entry)
            if holder is None:
                test_level_failed += 1
            elif holder[0] in ('setUpClass', 'setUpModule'):
                blocked += per_module if holder[0] == 'setUpModule' else per_class.get(holder[1], 0)
                entry['blocked_tests'] = per_module if holder[0] == 'setUpModule' else per_class.get(holder[1], 0)
            else:
                extra_errors += 1  # tearDownClass etc.: every test ran, but the suite is not clean
    unexpected = len(result.unexpectedSuccesses)
    test_level_failed += unexpected
    for test in result.unexpectedSuccesses:
        failures.append({'test': test.id(), 'kind': 'unexpected-success', 'message': 'expected failure passed'})

    explicit_only = sum(1 for test, _ in result.skipped if _holder_info(test) is None)
    residue = max(0, total - result.testsRun - unrun_skips - blocked)
    skipped = explicit_only + unrun_skips + residue
    failed = test_level_failed + blocked + extra_errors
    passed = max(0, total - skipped - test_level_failed - blocked)
    if residue:
        explicit_skips['(never started; not attributed to a setUpClass/setUpModule skip)'] += residue
        skip_items.append({'test': stem, 'reason': '(never started; not attributed to a setUpClass/setUpModule skip)',
                           'scope': 'never-started', 'count': residue})
    report.update(total=total, run=result.testsRun, passed=passed, failed=failed, skipped=skipped,
                  explicit_skipped=explicit_only, unrun_skipped=unrun_skips + residue, blocked_by_error=blocked,
                  extra_errors=extra_errors, failures=failures[:40],
                  skip_reasons=dict(explicit_skips.most_common(30)), skip_items=skip_items[:200])
    return emit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
