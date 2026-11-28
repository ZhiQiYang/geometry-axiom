#!/usr/bin/env python3
"""Three real checker-source withdrawals; these are local research evidence.

Each phase uses a new Python/Node process and exact stderr classification.
Import, setup, timeout, child crashes, and unrelated assertions never count as
a killed mutation. No shared candidate or repository source is edited.
"""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent


def cases():
    return [
        {'name': 'M_U476_CHECKER_COUNT_GUARD', 'corruption': 'count',
         'old': "    require(answer['itemCount'] == len(declarations), 'U476_CHECK_COUNT')\n",
         'new': "    require(True, 'U476_CHECK_COUNT')\n"},
        {'name': 'M_U476_CHECKER_PHYSICAL_TOTAL_GUARD', 'corruption': 'physical-total',
         'old': "    require(book['physicalItemLengthMm'] == physical, 'U476_CHECK_PHYSICAL_LENGTH')\n",
         'new': "    require(True, 'U476_CHECK_PHYSICAL_LENGTH')\n"},
        {'name': 'M_U476_CHECKER_NATIVE_LENGTH_GUARD', 'corruption': 'native-length',
         'old': "            require(_same_json(row[field], source['native']['content'][field]), 'U476_CHECK_NATIVE_MEASUREMENT:' + field)\n",
         'new': "            require(True, 'U476_CHECK_NATIVE_MEASUREMENT:' + field)\n"},
    ]


def pin(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def run(candidate, destination):
    destination.mkdir(parents=True, exist_ok=True)
    candidate_bytes = candidate.read_bytes()
    original = (ROOT / 'check.py').read_bytes()
    reports = []
    for mutation in cases():
        old, replacement = mutation['old'].encode(), mutation['new'].encode()
        assert original.count(old) == 1, mutation['name'] + ':NON_UNIQUE_TARGET'
        withdrawn = original.replace(old, replacement)
        assert withdrawn != original and b'\r' not in withdrawn, mutation['name'] + ':INVALID_PATCH'
        output = destination / mutation['name']
        output.mkdir(exist_ok=True)
        expected = 'U476_CHECKER_SELFTEST_REJECTS_BAD_OUTPUT:' + mutation['corruption']
        phases = []
        with tempfile.TemporaryDirectory(prefix='u476-checker-') as temporary:
            work = Path(temporary)
            for filename in ('fixtures.py', 'probe.py'):
                shutil.copyfile(ROOT / filename, work / filename)
            (work / 'candidate.cjs').write_bytes(candidate_bytes)
            target = work / 'check.py'
            try:
                for label, source in (('baseline', original), ('withdrawn', withdrawn), ('restored', original)):
                    target.write_bytes(source)
                    (output / (label + '.check.py')).write_bytes(source)
                    proposed = output / (label + '.proposed.json')
                    command = [sys.executable, '-B', 'probe.py', '--candidate', str(work / 'candidate.cjs'),
                               '--corruption', mutation['corruption'], '--proposed', str(proposed)]
                    try:
                        process = subprocess.run(command, cwd=work, text=True, encoding='utf-8',
                                                 capture_output=True, timeout=15,
                                                 env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
                    except subprocess.TimeoutExpired as error:
                        raise RuntimeError(mutation['name'] + ':INFRASTRUCTURE_TIMEOUT') from error
                    (output / (label + '.stdout.txt')).write_text(process.stdout, encoding='utf-8')
                    (output / (label + '.stderr.txt')).write_text(process.stderr, encoding='utf-8')
                    phases.append({'phase': label, 'command': command, 'exit': process.returncode,
                                   'source': pin(target.read_bytes()),
                                   'proposed': pin(proposed.read_bytes()) if proposed.exists() else None,
                                   'stdout': process.stdout, 'stderr': process.stderr})
            finally:
                target.write_bytes(original)
            restored = target.read_bytes() == original
        patch = ''.join(difflib.unified_diff(original.decode().splitlines(True), withdrawn.decode().splitlines(True),
                                            'a/geometry-core/timber-takeoff/research/check.py',
                                            'b/geometry-core/timber-takeoff/research/check.py'))
        (output / 'withdrawal.patch').write_text(patch, encoding='utf-8', newline='\n')
        passed = ([phase['exit'] for phase in phases] == [0, 1, 0]
                  and phases[1]['stderr'].strip() == expected and restored)
        report = {'name': mutation['name'], 'target': 'check.py', 'corruption': mutation['corruption'],
                  'expectedAssertion': expected, 'original': pin(original), 'withdrawn': pin(withdrawn),
                  'candidate': pin(candidate_bytes), 'phases': phases,
                  'restoredBytesIdentical': restored, 'passed': passed}
        reports.append(report)
        if not passed:
            (destination / 'failed-report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
            raise AssertionError(mutation['name'] + ':NOT_A_NAMED_0_1_0')
    summary = {'studySchema': 'U476-checker-withdrawals/1', 'researchOnly': True,
               'checkerWithdrawals': len(reports), 'allExitCodes': '0/1/0',
               'namedAssertionsOnly': True, 'allRestoredBytesIdentical': True,
               'crashed': 0, 'survived': 0, 'records': reports}
    (destination / 'mutation-summary.json').write_text(json.dumps(summary, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in summary.items() if key != 'records'}, sort_keys=True))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--bounded', required=True, action='store_true')
    args = parser.parse_args()
    try:
        run(args.candidate.resolve(), args.out.resolve())
    except (AssertionError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
