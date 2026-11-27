#!/usr/bin/env python3
"""Record the real 128-input v2/v3 rectangle matrix and read/source sensitivity.

The ordinary native suite owns the assertions. This diagnostic retains their
real requests/responses and optional source-withdrawal 0/1/0 executions. It
does not fix v2, change an acceptance expectation from observed output, alter
compiler flags/timeouts, or create official CI evidence. All withdrawn sources
live in a separate copied native include closure.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests'))
import binaries
from test_framing_template_notch import (native_outcome, rectangle_cases,
                                        rectangle_expected_acceptance)

SOURCE = Path('geometry-web/framing_template_bridge.inc')
SUITE = ROOT / 'tests/test_framing_template_notch.py'
B03 = 'FramingTemplateNotch.test_B03_rectangle_degeneracy_preserves_v2_exact_rows'
B14 = 'FramingTemplateNotch.test_B14_rectangle_acceptance_matrix_and_common_exact_values'
B15 = 'FramingTemplateNotch.test_B15_reordered_rectangle_known_difference_has_true_output'
B16 = 'FramingTemplateNotch.test_B16_real_native_scope_reads_reach_app_specific_reason'
FAULTS = (
    {'id': 'R03B_RECTANGLE_SOURCE_V3_FIRST_LENGTH_PLUS_ONE',
     'before': '(long long)w->wood.timbers[i].length,(long long)w->wood.timbers[i].size_a',
     'after': '((long long)w->wood.timbers[i].length+(c->version==3&&k==0)),(long long)w->wood.timbers[i].size_a',
     'judges': ((B03, 'R03B_ZERO_NOTCH_EQUALS_V2'),
                (B15, 'R03B_RECTANGLE_TRUE_OUTPUT_EVERY_MEMBER'))},
    {'id': 'R03B_RECTANGLE_SOURCE_V3_REUSE_INPUT_EDGE_INDEX',
     'before': 'if(match<0||!framing_template_edge_key(w,host,match,key))return false;',
     'after': 'if(boundary->outline.count==4)match=edge;\n    if(match<0||!framing_template_edge_key(w,host,match,key))return false;',
     'judges': ((B14, 'R03B_RECTANGLE_ACCEPTANCE_SET_EXACT'),)},
    {'id': 'R03B_READ_SURFACE_LIFETIME',
     'before': 'surface=app_boundary_read(&g_world,boundary,&read_surface)',
     'after': 'surface=world_find_boundary(&g_world,boundary)',
     'judges': ((B16, 'R03B_REAL_READ_HOLE_COUNT'),)},
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def run(args, directory, *, env=None):
    directory.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    # The enclosing native workflow and the original build/Session supervisors
    # retain their existing limits. No extra timeout or retry is introduced.
    try:
        process = subprocess.run([str(arg) for arg in args], cwd=ROOT, env=env, capture_output=True)
        stdout, stderr, code = process.stdout, process.stderr, process.returncode
    except OSError as exc:
        stdout, stderr, code = b'', str(exc).encode(), None
    (directory / 'stdout.txt').write_bytes(stdout)
    (directory / 'stderr.txt').write_bytes(stderr)
    result = {'command': [str(arg) for arg in args], 'cwd': str(ROOT), 'exit': code,
              'seconds': time.monotonic() - start,
              'stdout': {'path': 'stdout.txt', 'bytes': len(stdout), 'sha256': sha(stdout)},
              'stderr': {'path': 'stderr.txt', 'bytes': len(stderr), 'sha256': sha(stderr)}}
    write_json(directory / 'execution.json', result)
    return result, stdout, stderr


def run_test(binary, method, directory):
    env = dict(os.environ, GEOMETRY_TEST_BRIDGE=str(binary),
               GEOMETRY_FRAMING_RECEIPTS=str(directory / 'native'))
    result, _, stderr = run([sys.executable, '-B', SUITE, '-v', method], directory, env=env)
    result['binary_sha256'] = sha(binary.read_bytes())
    result['assertion_failure_only'] = bool(re.search(rb'^FAILED \(failures=[1-9][0-9]*\)$', stderr, re.M))
    write_json(directory / 'execution.json', result)
    return result, stderr.decode('utf-8', errors='replace')


def require(condition, name):
    if not condition:
        raise AssertionError(name)


def require_fresh(binary):
    inspected = binaries.inspect_one(binaries.BY_NAME['bridge'], path=binary)
    require(inspected.state == 'fresh', 'R03B_RECTANGLE_REAL_BINARY_FRESH: ' + inspected.reason)


def scan(binary, directory):
    require_fresh(binary)
    execution, _ = run_test(binary, B14, directory / 'judge')
    require(execution['exit'] == 0, 'R03B_RECTANGLE_MATRIX_NATIVE_JUDGE')
    receipt_path = directory / 'judge/native' / (B14.split('.')[-1] + '.json')
    native = json.loads(receipt_path.read_bytes())
    previews, points = [], None
    for event in native['receipts']:
        command = event['command']
        if command.startswith('line surface 1 '):
            points = [[int(value) for value in item.split(',')]
                      for item in command.split(' outline ', 1)[1].split()]
        elif command.startswith('framing-template-preview '):
            previews.append({'points': points, 'request': event['request'], 'reply': event['reply']})
    cases = list(rectangle_cases())
    require(len(cases) == 128 and len(previews) == 256, 'R03B_RECTANGLE_MATRIX_ALL_RAW_CALLS')
    records = []
    for index, case in enumerate(cases):
        actual = {}
        for offset, version in enumerate((2, 3)):
            event = previews[2 * index + offset]
            request = event['request']
            require(event['points'] == case['points'] and request['template']['version'] == version
                    and request['parameters']['gap'] == case['gap']
                    and request['layout'] == {'corner': case['corner'], 'lengthAlong': case['along']},
                    'R03B_RECTANGLE_MATRIX_REQUEST_IDENTITY')
            actual[f'v{version}'] = event
        observed = {version: native_outcome(event['reply']) for version, event in actual.items()}
        expected = rectangle_expected_acceptance(case)
        require(expected == observed, 'R03B_RECTANGLE_ACCEPTANCE_SET_EXACT')
        records.append({'input': case, 'expected': expected, 'observed': observed, 'native': actual})
    raw_path = directory / 'rectangle-matrix.jsonl'
    raw_path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in records), encoding='utf-8')
    counts = Counter((row['observed']['v2'], row['observed']['v3']) for row in records)
    summary = {'schema': 'r03b-rectangle-native-matrix/1', 'official_workflow': False,
               'inputs': 128, 'native_preview_calls': 256, 'common_accepted': counts[('accepted', 'accepted')],
               'v2_native_invalid_v3_accepted': counts[('NATIVE_INVALID', 'accepted')],
               'v2_accepted_keys': [r['input']['id'] for r in records if r['observed']['v2'] == 'accepted'],
               'v3_accepted_keys': [r['input']['id'] for r in records if r['observed']['v3'] == 'accepted'],
               'raw': {'path': raw_path.name, 'bytes': raw_path.stat().st_size, 'sha256': sha(raw_path.read_bytes())},
               'judge': execution, 'suite_sha256': sha(SUITE.read_bytes()),
               'diagnostic_sha256': sha(Path(__file__).read_bytes())}
    write_json(directory / 'receipt.json', summary)
    print(json.dumps({k: summary[k] for k in ('schema', 'inputs', 'native_preview_calls',
                                            'common_accepted', 'v2_native_invalid_v3_accepted')}, ensure_ascii=False), flush=True)
    return summary


def withdrawals(binary, directory):
    require_fresh(binary)
    original = (ROOT / SOURCE).read_bytes()
    fingerprint, closure, command = binaries.compute_fingerprint(binaries.BY_NAME['bridge'])
    isolated = directory / 'source'
    for relative in closure:
        path = isolated / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, path)
    (isolated / 'tests').mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / 'tests/binaries.py', isolated / 'tests/binaries.py')
    original_bin = directory / 'bin/original'
    original_bin.mkdir(parents=True, exist_ok=True)
    executable_name = binaries.BY_NAME['bridge'].exe
    shutil.copy2(binary, original_bin / executable_name)
    shutil.copy2(Path(str(binary) + binaries.SIDECAR_SUFFIX), original_bin / (executable_name + binaries.SIDECAR_SUFFIX))
    manifest = {'source_fingerprint': fingerprint, 'source_closure': closure, 'command': command,
                'builder_sha256': sha((ROOT / 'tests/binaries.py').read_bytes()),
                'suite_sha256': sha(SUITE.read_bytes()), 'diagnostic_sha256': sha(Path(__file__).read_bytes())}
    write_json(directory / 'inputs.json', manifest)
    records = []
    for fault in FAULTS:
        old, new = fault['before'].encode(), fault['after'].encode()
        require(original.count(old) == 1, 'R03B_RECTANGLE_SOURCE_ANCHOR_EXACT: ' + fault['id'])
        mutant = original.replace(old, new, 1)
        phases = []
        for label, source in (('baseline', original), ('withdrawn', mutant), ('restored', original)):
            phase_dir = directory / fault['id'] / label
            phase_dir.mkdir(parents=True, exist_ok=True)
            (isolated / SOURCE).write_bytes(source)
            (phase_dir / SOURCE.name).write_bytes(source)
            bin_dir = directory / 'bin' / fault['id'] if label == 'withdrawn' else original_bin
            build, _, _ = run([sys.executable, '-B', Path(__file__).resolve(), '--build-root', isolated,
                               '--build-out', bin_dir], phase_dir / 'build')
            phase = {'source_sha256': sha(source), 'source_path': SOURCE.name,
                     'build': build, 'judges': []}
            if build['exit'] == 0:
                built = bin_dir / binaries.BY_NAME['bridge'].exe
                phase['binary_sha256'] = sha(built.read_bytes())
                for method, marker in fault['judges']:
                    result, stderr = run_test(built, method, phase_dir / method.split('.')[-1])
                    result['expected_assertion'] = marker
                    result['named_assertion_observed'] = marker in stderr
                    phase['judges'].append(result)
            phases.append(phase)
            write_json(phase_dir / 'phase.json', phase)
            print(json.dumps({'fault': fault['id'], 'phase': label, 'build_exit': build['exit'],
                              'judge_exits': [row['exit'] for row in phase['judges']]}, ensure_ascii=False), flush=True)
        outcomes = []
        for index, (method, marker) in enumerate(fault['judges']):
            valid = all(len(phase['judges']) == len(fault['judges']) for phase in phases)
            exits = [phase['judges'][index]['exit'] for phase in phases] if valid else []
            killed = (exits == [0, 1, 0] and phases[1]['judges'][index]['assertion_failure_only']
                      and phases[1]['judges'][index]['named_assertion_observed']) if valid else False
            status = ('blocked' if not valid else 'killed' if killed else 'survived' if exits == [0, 0, 0]
                      else 'invalid' if exits[0] != 0 or exits[2] != 0 else 'blocked')
            outcomes.append({'method': method, 'expected_assertion': marker, 'exits': exits, 'status': status})
        restored = (isolated / SOURCE).read_bytes() == original == (ROOT / SOURCE).read_bytes()
        unchanged = all(binaries._normalized_sha(ROOT / path) == digest for path, digest in closure.items())
        status = ('blocked' if not restored or not unchanged or any(r['status'] == 'blocked' for r in outcomes)
                  else 'invalid' if any(r['status'] == 'invalid' for r in outcomes)
                  else 'survived' if any(r['status'] == 'survived' for r in outcomes) else 'killed')
        record = {'id': fault['id'], 'status': status, 'judges': outcomes, 'source_restored_exact': restored,
                  'worktree_closure_unchanged': unchanged,
                  'baseline_restored_source_sha256': sha(original), 'mutant_sha256': sha(mutant)}
        records.append(record)
    result = {'schema': 'r03b-rectangle-native-source-withdrawals/1', 'official_workflow': False,
              'records': records, 'killed': sum(row['status'] == 'killed' for row in records),
              'blocked': sum(row['status'] == 'blocked' for row in records),
              'survived': sum(row['status'] == 'survived' for row in records),
              'invalid': sum(row['status'] == 'invalid' for row in records)}
    write_json(directory / 'receipt.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bridge', type=Path, default=os.environ.get('GEOMETRY_TEST_BRIDGE'))
    parser.add_argument('--out', type=Path)
    parser.add_argument('--withdrawals', action='store_true')
    parser.add_argument('--build-root', type=Path, help=argparse.SUPPRESS)
    parser.add_argument('--build-out', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.build_root:
        require(args.build_out is not None, 'R03B_RECTANGLE_BUILD_OUTPUT_REQUIRED')
        binaries.ROOT, binaries.OUT_DIR = args.build_root.resolve(), args.build_out.resolve()
        return binaries.main(['build', 'bridge'])
    if args.bridge is None or args.out is None:
        parser.error('--bridge (or GEOMETRY_TEST_BRIDGE) and --out are required')
    binary, directory = args.bridge.resolve(), args.out.resolve()
    scan(binary, directory / 'matrix')
    if args.withdrawals:
        result = withdrawals(binary, directory / 'withdrawals')
        return 0 if result['killed'] == len(FAULTS) else 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
