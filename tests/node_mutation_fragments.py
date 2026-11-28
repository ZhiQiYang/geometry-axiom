"""O467 Node-only semantic withdrawals, separate from native Mutation evidence.

Each definition executes its complete file: no name filter, skipped tests or
arbitrary nonzero exit can kill. Node events must match the declared complete
case census and exact semantic failure-message set. Source is overridden
only in a temporary copy. Receipts are diagnostics, never official native ME.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

from mutation_fragments import _object, _safe

ROOT = Path(__file__).resolve().parents[1]
FIELDS = {'id', 'file', 'old', 'new', 'test', 'environment', 'expected_assertion',
          'expected_tests', 'expected_cases', 'expected_failures', 'reason'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def definitions(root):
    root = Path(root).resolve()
    directory = root / 'tests/node-mutants.d'
    _safe(root, directory)
    if not directory.is_dir():
        raise ValueError('O467_NODE_FRAGMENTS_REQUIRED')
    rows, seen = [], set()
    for path in sorted(directory.iterdir()):
        _safe(root, path)
        if not path.is_file() or path.suffix != '.json':
            raise ValueError('O467_NODE_FRAGMENT_PATH')
        row = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=_object)
        if (type(row) is not dict or set(row) != FIELDS
                or any(type(row[k]) is not str or not row[k].strip()
                       for k in FIELDS - {'expected_tests', 'expected_cases', 'expected_failures'})
                or type(row['expected_tests']) is not int or row['expected_tests'] <= 0
                or not re.fullmatch(r'[A-Z][A-Z0-9_]+', row['id'])
                or row['id'].casefold() in seen or path.name != row['id'] + '.json'
                or not re.fullmatch(r'[A-Z][A-Z0-9_]+', row['environment'])
                or row['old'] == row['new']):
            raise ValueError('O467_NODE_FRAGMENT_SHAPE: ' + path.name)
        cases, failures = row['expected_cases'], row['expected_failures']
        if (type(cases) is not list or len(cases) != row['expected_tests']
                or any(type(case) is not str or not case for case in cases)
                or len(cases) != len(set(cases)) or type(failures) is not dict or not failures
                or not set(failures) <= set(cases)
                or any(type(message) is not str or not message or '\n' in message
                       for message in failures.values())
                or not any(message == row['expected_assertion'] or
                           message.startswith(row['expected_assertion'] + ' ')
                           for message in failures.values())):
            raise ValueError('O467_NODE_SEMANTIC_CENSUS: ' + path.name)
        seen.add(row['id'].casefold())
        for key in ('file', 'test'):
            rel = row[key]
            if ('\\' in rel or ':' in rel or rel.startswith('/')
                    or any(part in ('', '.', '..') for part in rel.split('/'))):
                raise ValueError('O467_NODE_SOURCE_PATH')
            source = root / rel
            _safe(root, source)
            if not source.is_file() or source.suffix not in ('.js', '.cjs'):
                raise ValueError('O467_NODE_SOURCE_PATH')
        if (root / row['file']).read_text(encoding='utf-8').count(row['old']) != 1:
            raise ValueError('O467_NODE_UNIQUE_ANCHOR: ' + row['id'])
        rows.append(row)
    return rows


def classify(run, expected_tests, marker):
    """Judge actual Node error records, exact cases and exact failure messages."""
    if run.get('timed_out') or run.get('exit') not in (0, 1):
        return 'blocked'
    try:
        events = [json.loads(line) for line in run['stdout'].splitlines()]
        if any(type(event) is not dict or event.get('type') not in
               ('test:pass', 'test:fail', 'test:summary') for event in events):
            return 'blocked'
        rows = [event for event in events if event['type'] != 'test:summary']
        summaries = [event['data'] for event in events if event['type'] == 'test:summary']
        cases, declared = run['expected_cases'], run['expected_failures']
        if (type(cases) is not list or len(cases) != expected_tests
                or any(type(case) is not str or not case for case in cases)
                or len(cases) != len(set(cases)) or type(declared) is not dict
                or not set(declared) <= set(cases) or len(rows) != expected_tests
                or len(summaries) != 1 or events[-1]['type'] != 'test:summary'
                or [row['name'] for row in rows] != cases
                or any(type(row['testNumber']) is not int or type(row['nesting']) is not int for row in rows)
                or [row['testNumber'] for row in rows] != list(range(1, expected_tests + 1))
                or any(row['nesting'] != 0 or row['skip'] is not False or row['todo'] is not False
                       for row in rows)):
            return 'blocked'
        failed = {row['name']: row['error'] for row in rows if row['type'] == 'test:fail'}
        if any(row['error'] is not None for row in rows if row['type'] == 'test:pass'):
            return 'blocked'
        summary = summaries[0]
        expected_counts = dict(tests=expected_tests, suites=0, passed=expected_tests - len(failed),
                               failed=len(failed), cancelled=0, skipped=0, todo=0)
        if (any(type(summary['counts'].get(key)) is not int or summary['counts'][key] != value
                for key, value in expected_counts.items())
                or summary['success'] is not (not failed) or run['exit'] != int(bool(failed))
                or run.get('stderr')):
            return 'blocked'
        if not failed:
            return 'passed'
        if set(failed) != set(declared):
            return 'blocked'
        messages = []
        for name, error in failed.items():
            if (type(error) is not dict or error.get('name') != 'AssertionError'
                    or error.get('code') != 'ERR_ASSERTION'
                    or error.get('failureType') != 'testCodeFailure'
                    or type(error.get('message')) is not str or not error['message']):
                return 'blocked'
            first = error['message'].splitlines()[0]
            if first != declared[name]:
                return 'blocked'
            messages.append(first)
        return 'killed' if any(message == marker or message.startswith(marker + ' ')
                               for message in messages) else 'blocked'
    except (KeyError, TypeError, ValueError, IndexError):
        return 'blocked'


def run(command, env=None):
    start = time.monotonic()
    try:
        call = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                              text=True, timeout=30)
        return {'command': command, 'exit': call.returncode,
                'seconds': time.monotonic() - start, 'stdout': call.stdout,
                'stderr': call.stderr, 'timed_out': False}
    except subprocess.TimeoutExpired as error:
        return {'command': command, 'exit': None, 'seconds': time.monotonic() - start,
                'stdout': str(error.stdout or ''), 'stderr': str(error.stderr or ''),
                'timed_out': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--only', action='append')
    options = parser.parse_args()
    options.out.mkdir(parents=True, exist_ok=False)
    rows = definitions(ROOT)
    if options.only:
        if set(options.only) - {row['id'] for row in rows}:
            parser.error('unknown mutation ID')
        rows = [row for row in rows if row['id'] in options.only]
    report = {'schema': 'geometry-node-mutation/1', 'browserExecuted': False,
              'sourceHead': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'driverSha256': sha(Path(__file__).read_bytes()), 'records': []}
    reporter = ROOT / 'tests/diagnostics/o467_node_reporter.cjs'
    report['reporterSha256'] = sha(reporter.read_bytes())
    for row in rows:
        original = (ROOT / row['file']).read_bytes()
        changed = original.replace(row['old'].encode(), row['new'].encode(), 1)
        record = dict(id=row['id'], expected_assertion=row['expected_assertion'],
                      source=row['file'], sourceSha256=sha(original), mutantSha256=sha(changed),
                      judge=row['test'], judgeSha256=sha((ROOT / row['test']).read_bytes()),
                      definitionSha256=sha((ROOT / 'tests/node-mutants.d' / (row['id'] + '.json')).read_bytes()),
                      expected_cases=row['expected_cases'], expected_failures=row['expected_failures'],
                      status='blocked', phases=[])
        with tempfile.TemporaryDirectory(prefix='o467-node-') as temporary:
            directory = Path(temporary)
            target = directory / Path(row['file']).name
            # The real framing session imports this sibling on its Node path.
            shutil.copy2(ROOT / 'geometry-web/framing-recipes.js', directory / 'framing-recipes.js')
            for phase, raw in [('baseline', original), ('withdrawn', changed), ('restored', original)]:
                target.write_bytes(raw)
                syntax = run(['node', '--check', str(target)])
                if syntax['exit'] != 0:
                    record['phases'].append({'phase': phase, 'syntax': syntax, 'status': 'blocked'})
                    break
                env = dict(os.environ, **{row['environment']: str(target)})
                result = run(['node', '--test', '--test-reporter=' + str(reporter), str(ROOT / row['test'])], env)
                result.update(expected_cases=row['expected_cases'], expected_failures=row['expected_failures'])
                result['status'] = classify(result, row['expected_tests'], row['expected_assertion'])
                record['phases'].append({'phase': phase, 'sourceSha256': sha(raw), 'run': result})
                (options.out / (row['id'] + '-' + phase + '.events.jsonl')).write_text(result['stdout'], encoding='utf-8')
                (options.out / (row['id'] + '-' + phase + '.stderr')).write_text(result['stderr'], encoding='utf-8')
            target.write_bytes(original)
            record['restoredSha256'] = sha(target.read_bytes())
        phases = record['phases']
        if len(phases) == 3 and all('run' in phase for phase in phases):
            record['exits'] = [phase['run']['exit'] for phase in phases]
            statuses = [phase['run']['status'] for phase in phases]
            if statuses == ['passed', 'killed', 'passed'] and record['exits'] == [0, 1, 0]:
                record['status'] = 'killed'
            elif statuses == ['passed', 'passed', 'passed']:
                record['status'] = 'survived'
        if (ROOT / row['file']).read_bytes() != original:
            raise RuntimeError('working source changed during proof')
        report['records'].append(record)
        (options.out / 'receipt.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(row['id'] + ': ' + record['status'], flush=True)
    return 0 if all(row['status'] == 'killed' for row in report['records']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
