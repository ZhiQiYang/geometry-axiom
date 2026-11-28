#!/usr/bin/env python3
"""One bounded checker self-test, run in a fresh process per mutation phase."""
import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys

import check
import fixtures


def run(candidate, corruption, proposed):
    data = fixtures.named('same-source-explicit')
    try:
        process = subprocess.run(['node', str(candidate), 'batch'], input=json.dumps([data]),
                                 text=True, encoding='utf-8', capture_output=True, timeout=10)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError('U476_PROBE_CANDIDATE_TIMEOUT') from error
    if process.returncode != 0:
        raise RuntimeError('U476_PROBE_CANDIDATE_EXIT:' + str(process.returncode) + ':' + process.stderr)
    outputs = json.loads(process.stdout)
    if not isinstance(outputs, list) or len(outputs) != 1:
        raise RuntimeError('U476_PROBE_CANDIDATE_BATCH')
    good = outputs[0]
    check.inspect(data, good)
    bad = copy.deepcopy(good)
    if corruption == 'count':
        bad['itemCount'] += 1
        expected = 'U476_CHECK_COUNT'
    elif corruption == 'physical-total':
        bad['accounting']['physicalItemLengthMm'] += 1
        expected = 'U476_CHECK_PHYSICAL_LENGTH'
    elif corruption == 'native-length':
        bad['items'][0]['L'] += 1
        expected = 'U476_CHECK_NATIVE_MEASUREMENT:L'
    else:
        raise RuntimeError('U476_PROBE_UNKNOWN_CORRUPTION')
    proposed.write_text(json.dumps({'input': data, 'valid': good, 'corrupted': bad},
                                   sort_keys=True, indent=2) + '\n', encoding='utf-8')
    try:
        check.inspect(data, bad)
    except check.Rejected as error:
        if str(error) != expected:
            raise AssertionError('U476_CHECKER_SELFTEST_WRONG_REJECTION:' + str(error)) from error
    else:
        raise AssertionError('U476_CHECKER_SELFTEST_REJECTS_BAD_OUTPUT:' + corruption)
    print(json.dumps({'corruption': corruption, 'validAccepted': True,
                      'badRejected': expected}, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--corruption', required=True,
                        choices=('count', 'physical-total', 'native-length'))
    parser.add_argument('--proposed', required=True, type=Path)
    args = parser.parse_args()
    try:
        run(args.candidate.resolve(), args.corruption, args.proposed.resolve())
    except AssertionError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
    except Exception as error:
        print('U476_PROBE_INFRASTRUCTURE:' + type(error).__name__ + ':' + str(error), file=sys.stderr)
        raise SystemExit(2)
