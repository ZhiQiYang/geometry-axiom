#!/usr/bin/env python3
"""Check reporter semantics with synthetic fixtures; never builds or runs product suites."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import time
from unittest.mock import patch

PREFIX = 'import unittest\n\n'


def case(body, total, run, passed=0, failed=0, skipped=0, code=0, **extra):
    return (PREFIX + textwrap.dedent(body),
            dict(total=total, run=run, passed=passed, failed=failed, skipped=skipped, **extra), code)


CASES = {
    'normal': case('''
        class Fixture(unittest.TestCase):
            def test_ok(self): self.assertEqual(2 + 3, 5)
    ''', 1, 1, passed=1),
    'two_failing_subtests': case('''
        class Fixture(unittest.TestCase):
            def test_values(self):
                for value in (1, 2):
                    with self.subTest(value=value): self.assertEqual(value, 0)
    ''', 1, 1, failed=1, code=1, failure_items=2),
    'subtest_failure_and_error': case('''
        class Fixture(unittest.TestCase):
            def test_values(self):
                with self.subTest(kind='failure'): self.fail('subtest assertion')
                with self.subTest(kind='error'): raise RuntimeError('subtest error')
    ''', 1, 1, failed=1, code=1, failure_items=2),
    'failure_then_skip': case('''
        class Fixture(unittest.TestCase):
            def test_values(self):
                with self.subTest(kind='failure'): self.fail('broken')
                with self.subTest(kind='skip'): self.skipTest('unsupported subcase')
    ''', 1, 1, failed=1, code=1, skip_event_counts=[0]),
    'skip_then_failure': case('''
        class Fixture(unittest.TestCase):
            def test_values(self):
                with self.subTest(kind='skip'): self.skipTest('unsupported subcase')
                with self.subTest(kind='failure'): self.fail('broken')
    ''', 1, 1, failed=1, code=1, skip_event_counts=[0]),
    'two_skipped_subtests': case('''
        class Fixture(unittest.TestCase):
            def test_values(self):
                for value in (1, 2):
                    with self.subTest(value=value): self.skipTest('unsupported subcase')
    ''', 1, 1, skipped=1, skip_event_counts=[1, 0]),
    'skip_then_passed_subtest': case('''
        class Fixture(unittest.TestCase):
            def test_values(self):
                with self.subTest(kind='skip'): self.skipTest('unsupported subcase')
                with self.subTest(kind='pass'): self.assertTrue(True)
    ''', 1, 1, skipped=1),
    'expected_failure': case('''
        class Fixture(unittest.TestCase):
            @unittest.expectedFailure
            def test_known_bug(self): self.fail('known bug')
    ''', 1, 1, skipped=1, expected_failed=1, expected_failure_items=1),
    'expected_subtest_failure': case('''
        class Fixture(unittest.TestCase):
            @unittest.expectedFailure
            def test_known_bug(self):
                with self.subTest(value=1): self.fail('known bug')
    ''', 1, 1, skipped=1, expected_failed=1, expected_failure_items=1),
    'unexpected_success': case('''
        class Fixture(unittest.TestCase):
            @unittest.expectedFailure
            def test_known_bug(self): self.assertTrue(True)
    ''', 1, 1, failed=1, code=1, failure_items=1),
    'ordinary_skip': case('''
        class Fixture(unittest.TestCase):
            def test_skip(self): self.skipTest('fixture skip')
    ''', 1, 1, skipped=1),
    'ordinary_error': case('''
        class Fixture(unittest.TestCase):
            def test_error(self): raise RuntimeError('fixture error')
    ''', 1, 1, failed=1, code=1, failure_items=1),
    'failure_and_teardown_error': case('''
        class Fixture(unittest.TestCase):
            def test_failure(self): self.fail('body failure')
            def tearDown(self): raise RuntimeError('teardown error')
    ''', 1, 1, failed=1, code=1, failure_items=2),
    'skip_and_teardown_error': case('''
        class Fixture(unittest.TestCase):
            def test_skip(self): self.skipTest('body skip')
            def tearDown(self): raise RuntimeError('teardown error')
    ''', 1, 1, failed=1, code=1, skip_event_counts=[0]),
    'class_skip': case('''
        class Fixture(unittest.TestCase):
            @classmethod
            def setUpClass(cls): raise unittest.SkipTest('class unavailable')
            def test_one(self): pass
            def test_two(self): pass
    ''', 2, 0, skipped=2, unrun_skipped=2),
    'module_skip': case('''
        def setUpModule(): raise unittest.SkipTest('module unavailable')
        class Fixture(unittest.TestCase):
            def test_one(self): pass
            def test_two(self): pass
    ''', 2, 0, skipped=2, unrun_skipped=2),
    'import_skip': case('''
        class Fixture(unittest.TestCase):
            def test_one(self): pass
            def test_two(self): pass
        raise unittest.SkipTest('import unavailable')
    ''', 2, 0, skipped=2, unrun_skipped=2),
    'class_error': case('''
        class Fixture(unittest.TestCase):
            @classmethod
            def setUpClass(cls): raise RuntimeError('class broken')
            def test_one(self): pass
            def test_two(self): pass
    ''', 2, 0, failed=2, code=1, blocked_by_error=2),
    'module_error': case('''
        def setUpModule(): raise RuntimeError('module broken')
        class Fixture(unittest.TestCase):
            def test_one(self): pass
            def test_two(self): pass
    ''', 2, 0, failed=2, code=1, blocked_by_error=2),
    'teardown_class_error': case('''
        class Fixture(unittest.TestCase):
            def test_one(self): pass
            def test_two(self): pass
            @classmethod
            def tearDownClass(cls): raise RuntimeError('class teardown broken')
    ''', 2, 2, passed=2, failed=1, code=1, extra_errors=1),
    'teardown_module_error': case('''
        def tearDownModule(): raise RuntimeError('module teardown broken')
        class Fixture(unittest.TestCase):
            def test_one(self): pass
            def test_two(self): pass
    ''', 2, 2, passed=2, failed=1, code=1, extra_errors=1),
    'duplicate_test_id': case('''
        class Fixture(unittest.TestCase):
            calls = 0
            def test_repeated(self):
                type(self).calls += 1
                if self.calls == 1: self.fail('first occurrence')
        def load_tests(loader, tests, pattern):
            return unittest.TestSuite([Fixture('test_repeated'), Fixture('test_repeated')])
    ''', 2, 2, passed=1, failed=1, code=1),
    'same_instance_repeated': case('''
        class Fixture(unittest.TestCase):
            calls = 0
            def test_repeated(self):
                type(self).calls += 1
                if self.calls == 1: self.fail('first occurrence')
        def load_tests(loader, tests, pattern):
            test = Fixture('test_repeated')
            return unittest.TestSuite([test, test])
    ''', 2, 2, passed=1, failed=1, code=1),
    'many_subtest_details': case('''
        class Fixture(unittest.TestCase):
            def test_values(self):
                for value in range(45):
                    with self.subTest(value=value): self.fail('individual subtest')
    ''', 1, 1, failed=1, code=1, failure_items=45),
    'many_subtest_skip_details': case('''
        class Fixture(unittest.TestCase):
            def test_values(self):
                for value in range(205):
                    with self.subTest(value=value): self.skipTest('individual subtest')
    ''', 1, 1, skipped=1, skip_event_counts=[1] + [0] * 204),
    'class_error_and_cleanup_error': case('''
        class Fixture(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                cls.addClassCleanup(cls.broken_cleanup)
                raise RuntimeError('class setup broken')
            @classmethod
            def broken_cleanup(cls): raise RuntimeError('class cleanup broken')
            def test_one(self): pass
            def test_two(self): pass
    ''', 2, 0, failed=2, code=1, blocked_by_error=2, failure_items=2),
    'class_skip_and_cleanup_error': case('''
        class Fixture(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                cls.addClassCleanup(cls.broken_cleanup)
                raise unittest.SkipTest('class unavailable')
            @classmethod
            def broken_cleanup(cls): raise RuntimeError('class cleanup broken')
            def test_one(self): pass
            def test_two(self): pass
    ''', 2, 0, failed=2, code=1, blocked_by_error=2, skip_event_counts=[0]),
    'expected_failure_with_cleanup_error': case('''
        class Fixture(unittest.TestCase):
            def broken_cleanup(self): raise RuntimeError('cleanup broken')
            @unittest.expectedFailure
            def test_known_bug(self):
                self.addCleanup(self.broken_cleanup)
                self.fail('known bug')
    ''', 1, 1, failed=1, code=1, expected_failed=0, failure_items=1),
    'zero_tests': case('pass', 0, 0, failed=1, code=1, no_tests=True),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_consumer(runner, out, env):
    """Exercise the real parser against one synthetic suite, using isolated logs."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import run_all

    consumer_logs = out / 'consumer'
    suite = run_all.Suite('py:synthetic_expected_failure', 'unittest',
                          [sys.executable, str(runner), str((out / 'test_expected_failure.py').resolve())],
                          needs=[], timeout=15)
    with patch.object(run_all, 'LOG_DIR', consumer_logs):
        row = run_all.run_suite(suite, env, {})
    expected = dict(total=1, passed=0, failed=0, skipped=1, allowed_skips=0, crashed=False)
    differences = {key: {'want': value, 'got': getattr(row, key)} for key, value in expected.items()
                   if getattr(row, key) != value}
    allowlist_checks = []
    for name, want in [('ordinary_skip', 1), ('failure_then_skip', 0), ('expected_failure', 0)]:
        data = json.loads((out / (name + '.json')).read_text(encoding='utf-8'))
        item = data['skip_items'][0] if data.get('skip_items') else {'test': '', 'reason': ''}
        entry = dict(suite='synthetic', test=item['test'], reason=item['reason'], platforms=(os.name,))
        with patch.object(run_all, 'ALLOWED_SKIPS', [entry]):
            got = run_all.classify_skips('synthetic', data)
        allowlist_checks.append(dict(case=name, want=want, got=got))
        if got != want:
            differences['allowlist:' + name] = dict(want=want, got=got)
    return dict(row=vars(row), expected=expected, allowlist_checks=allowlist_checks, differences=differences)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runner', type=Path, default=Path(__file__).resolve().parents[1] / '_unittest_runner.py')
    parser.add_argument('--out', type=Path, required=True, help='new directory; existing evidence is never overwritten')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    runner = args.runner.resolve()
    env = {k: v for k, v in os.environ.items() if not k.startswith('GEOMETRY_')}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    records = []
    for name, (source, expected, code) in CASES.items():
        fixture = args.out / ('test_' + name + '.py')
        receipt = args.out / (name + '.json')
        log = args.out / (name + '.log')
        fixture.write_text(source, encoding='utf-8')
        command = [sys.executable, str(runner), str(fixture.resolve()), '--json-out', str(receipt.resolve()),
                   '--log', str(log.resolve())]
        started = time.perf_counter()
        proc = subprocess.run(command, env=env, capture_output=True, text=True, timeout=15)
        elapsed = time.perf_counter() - started
        data = json.loads(receipt.read_text(encoding='utf-8')) if receipt.exists() else {}
        observed = dict(data)
        observed.update(failure_items=len(data.get('failures', [])),
                        expected_failure_items=len(data.get('expected_failures', [])),
                        skip_event_counts=[item['count'] for item in data.get('skip_items', [])])
        differences = {key: {'want': value, 'got': observed.get(key)} for key, value in expected.items()
                       if observed.get(key) != value}
        if proc.returncode != code:
            differences['exit'] = {'want': code, 'got': proc.returncode}
        records.append(dict(case=name, command=command, exit=proc.returncode, expected_exit=code,
                            seconds=round(elapsed, 6), expected=expected, differences=differences,
                            stdout=proc.stdout, stderr=proc.stderr,
                            fixture_sha256=sha(fixture), receipt_sha256=sha(receipt) if receipt.exists() else None,
                            log_sha256=sha(log) if log.exists() else None))
        print(('%s: ' % name) + ('PASS' if not differences else json.dumps(differences, sort_keys=True)))
    consumer = check_consumer(runner, args.out, env)
    failed = sum(bool(record['differences']) for record in records)
    summary = dict(runner=str(runner), runner_sha256=sha(runner), verifier_sha256=sha(Path(__file__)),
                   python=sys.version, cases=len(records), matched=len(records) - failed,
                   mismatched=failed, records=records, consumer=consumer)
    (args.out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('%d/%d fixture classifications matched; mismatched=%d' % (len(records) - failed, len(records), failed))
    print('existing aggregate parser / allowlist: ' + ('PASS' if not consumer['differences']
                                                     else json.dumps(consumer['differences'], sort_keys=True)))
    return int(bool(failed or consumer['differences']))


if __name__ == '__main__':
    sys.exit(main())
