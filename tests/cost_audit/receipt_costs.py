#!/usr/bin/env python3
"""Read existing aggregate/browser receipts; never import or run repository tests."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys

ROW = re.compile(r'^(?P<suite>(?:py|node|c|core|mutation):\S+)\s+'
                 r'(?P<total>\d+|-)\s+(?P<passed>\d+|ok|-)\s+(?P<failed>\d+|FAIL|-)\s+'
                 r'(?P<skipped>\d+|-)\s+(?P<seconds>\d+(?:\.\d+)?|-)\s*(?P<note>.*)$')
SUM = re.compile(r'^合計[^\n]*?\s(\d+(?:\.\d+)?)\s*$', re.M)
RAN = re.compile(r'^Ran (\d+) tests? in (\d+(?:\.\d+)?)s$', re.M)


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'),
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite: ' + value)))


def seconds(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError('invalid elapsed seconds: ' + repr(value))
    return value


def file_record(path):
    data = path.read_bytes()
    return dict(path=str(path.resolve()), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def parse_aggregate(text):
    rows = []
    seen = set()
    for line_no, line in enumerate(text.splitlines(), 1):
        match = ROW.fullmatch(line)
        if not match:
            if re.match(r'^(?:py|node|c|core|mutation):\S+\s', line):
                raise ValueError('unrecognized suite result at line %d: %s' % (line_no, line))
            continue
        row = match.groupdict()
        if row['suite'] in seen:
            raise ValueError('multiple result rows for ' + row['suite'])
        seen.add(row['suite'])
        for key in ('total', 'passed', 'failed', 'skipped'):
            value = row[key]
            row[key] = int(value) if value.isdigit() else value
        duration = row.pop('seconds')
        row['suite_process_seconds_rounded'] = None if duration == '-' else seconds(float(duration))
        row['status'] = ('not-run' if duration == '-' else
                         'failed' if row['failed'] == 'FAIL' or isinstance(row['failed'], int) and row['failed'] > 0 else
                         'skipped' if isinstance(row['skipped'], int) and row['skipped'] > 0 else 'reported-no-fail')
        row['line'] = line_no
        row['phases_seconds'] = dict(sleep=None, poll=None, native_execution=None,
                                    compilation=None, fingerprint=None, reader_rebuild=None)
        rows.append(row)
    if not rows:
        raise ValueError('no aggregate result table rows')
    sums = SUM.findall(text)
    if len(sums) != 1:
        raise ValueError('expected one aggregate suite sum')
    return rows, seconds(float(sums[0]))


def source_census(repo):
    # AST only: binary lookup/build/import side effects are never invoked.
    registry = ast.parse((repo / 'tests/run_all.py').read_text(encoding='utf-8'))
    needs = next(ast.literal_eval(node.value) for node in registry.body
                 if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'PY_NEEDS'
                                                        for t in node.targets))
    tree = ast.parse((repo / 'tests/binaries.py').read_text(encoding='utf-8'))
    entries = next(node.value for node in tree.body if isinstance(node, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'REGISTRY' for t in node.targets))
    posix = {}
    for entry in entries.elts:
        win_only = any(item.arg == 'win_only' and ast.literal_eval(item.value) for item in entry.keywords)
        if not win_only:
            posix[ast.literal_eval(entry.args[0])] = ast.literal_eval(entry.args[6])
    checks = sum(len(envs) for envs in posix.values())
    return dict(registered_python_suites=len(needs), posix_native_overrides=posix,
                all_fresh_preflight_checks_per_suite=checks,
                all_fresh_preflight_checks_static=len(needs) * checks,
                bridge_alias_rechecks_static=len(needs) * max(0, len(posix['bridge']) - 1),
                declared_needs_only_checks_counterfactual=sum(len(posix.get(name, []))
                                                             for names in needs.values() for name in names),
                counterfactual_validated=False,
                assumptions=['Every applicable native override is fresh and exported to each Python suite.',
                             'Declared-needs-only is an unvalidated dependency proposal, not an executed policy.'])


def parse_browser(text):
    found = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for marker in ('CDP_RESULT ', 'SPACE_RESULT '):
            if line.startswith(marker):
                data = json.loads(line[len(marker):])
                scope = data.get('scope') or {}
                found.append(dict(line=line_no, marker=marker.strip(), schema=data.get('schema'),
                                  mode=scope.get('mode'), filters=scope.get('filters'),
                                  completed=data.get('completed'),
                                  passed=data.get('passedAssertions', data.get('passed')),
                                  failed=data.get('failedAssertions', data.get('failed')),
                                  golden_compare=data.get('goldenCompare'),
                                  browser_exception_count=data.get('uncaughtBrowserExceptions',
                                                                  len(data.get('exceptions', []))),
                                  scope_omissions=scope.get('omitted'),
                                  sections=data.get('sections'), groups=data.get('groups')))
    exits = re.findall(r'^EXIT=(-?\d+)\s+SECONDS=(\d+(?:\.\d+)?)\s*$', text, re.M)
    return dict(results=found, shell_exit=int(exits[0][0]) if len(exits) == 1 else None,
                shell_seconds=seconds(float(exits[0][1])) if len(exits) == 1 else None,
                status='has-terminal-receipt' if len(exits) == 1 else 'unknown-terminal',
                acceptance_claim=False)


def build_report(args):
    evidence = []
    aggregate = args.aggregate_log.read_text(encoding='utf-8')
    rows, suite_sum = parse_aggregate(aggregate)
    evidence.append(file_record(args.aggregate_log))
    command = read_json(args.aggregate_receipt)
    evidence.append(file_record(args.aggregate_receipt))
    process_seconds = seconds(command['seconds'])
    for row in rows:
        stem = row['suite'].replace(':', '_')
        reporter = args.suite_dir / (stem + '.json')
        log = args.suite_dir / (stem + '.unittest.log')
        if row['suite'].startswith('py:'):
            row['reporter_inclusive_seconds'] = None
            row['unittest_run_seconds_including_fixtures'] = None
            if row['status'] == 'not-run':
                row['timing_status'] = 'not-run; existing per-suite files ignored'
                continue
            if reporter.exists():
                data = read_json(reporter)
                row['reporter_inclusive_seconds'] = seconds(data['seconds'])
                row['reporter_counts'] = {key: data[key] for key in ('total', 'run', 'passed', 'failed', 'skipped')}
                evidence.append(file_record(reporter))
            if log.exists():
                timings = RAN.findall(log.read_text(encoding='utf-8'))
                if len(timings) == 1:
                    row['unittest_run_seconds_including_fixtures'] = seconds(float(timings[0][1]))
                    row['unittest_run_count'] = int(timings[0][0])
                row['unittest_timing_status'] = 'one-summary' if len(timings) == 1 else 'unknown-or-ambiguous'
                evidence.append(file_record(log))
    browsers = []
    for path in args.browser_log:
        browsers.append(dict(file=file_record(path), declared_baseline_source_sha=args.browser_baseline_sha,
                             source_identity_verified=False,
                             source_limit='Baseline label only; patch/native-byte identity is not verified by this ledger.',
                             **parse_browser(path.read_text(encoding='utf-8'))))
    source_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=args.source_repo, text=True).strip()
    return dict(schema='geometry-test-cost-ledger/1', source_sha=source_sha, aggregate_evidence_sha=args.evidence_sha,
                command=command, aggregate_process_seconds=process_seconds,
                suite_process_sum_seconds_rounded=suite_sum,
                outside_suite_gap_seconds_approximate=round(process_seconds - suite_sum, 6),
                outside_suite_gap_attribution=None,
                suites=rows, largest_suites=sorted([r for r in rows if r['suite_process_seconds_rounded'] is not None],
                                                  key=lambda r: r['suite_process_seconds_rounded'], reverse=True)[:6],
                browser_receipts=browsers, static_source_census=source_census(args.source_repo),
                evidence_files=evidence,
                limits=['Historical timing is not a run of source_sha.',
                        'Unittest timing includes setUp/tearDown/cleanup and any native execution inside the suite.',
                        'Unknown phase costs stay null. Sleeps/timeouts in source are not observed elapsed time.',
                        'Rounded console, reporter and unittest durations have distinct boundaries.',
                        'Node file concurrency and inclusive parent/subtest times prevent summing node item durations.',
                        'Browser partial, failed and completed receipts remain distinct; exit0 does not upgrade scope.',
                        'No test/build/native executable/browser/service was invoked by this ledger.'])


def self_check():
    fixture = ('py:test_x 2 1 1 0 1.2 failure\nnode:script - ok - - 0.0 exit only\n'
               'node:failed_script - - FAIL - 0.1 exit failure\npy:unrun - - - - - missing binary\n'
               '合計(已執行、有計數者) 2 1 1 0 1.3\n')
    rows, elapsed = parse_aggregate(fixture)
    assert len(rows) == 4 and elapsed == 1.3 and rows[0]['failed'] == 1 and rows[1]['passed'] == 'ok'
    assert rows[2]['failed'] == 'FAIL' and rows[2]['status'] == 'failed'
    assert rows[3]['status'] == 'not-run' and rows[3]['suite_process_seconds_rounded'] is None
    for bad in ('garbage', fixture + 'py:test_x 2 1 1 0 1.2\n', fixture + 'py:malformed bogus row\n'):
        try:
            parse_aggregate(bad)
        except ValueError:
            pass
        else:
            raise AssertionError('malformed/duplicate table accepted')
    partial = parse_browser('CDP_RESULT {"scope":{"mode":"partial"},"completed":true,"passedAssertions":7,"failedAssertions":0,"goldenCompare":"not compared (partial mode)"}\nEXIT=0 SECONDS=9\n')
    assert partial['results'][0]['mode'] == 'partial' and partial['acceptance_claim'] is False
    incomplete = parse_browser('SPACE_RESULT {"scope":{"mode":"partial"},"completed":false,"passed":2,"failed":1}\nEXIT=1 SECONDS=10\n')
    assert incomplete['shell_exit'] == 1 and incomplete['results'][0]['completed'] is False
    assert parse_browser('PASS something')['shell_seconds'] is None
    for value in (-1, float('nan'), float('inf'), True):
        try:
            seconds(value)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid duration accepted')
    print('self-check: table/exit-only-failure/unrun/duplicate/malformed/partial/incomplete/missing/nonfinite PASS')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-check', action='store_true')
    parser.add_argument('--source-repo', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--evidence-sha')
    parser.add_argument('--aggregate-log', type=Path)
    parser.add_argument('--aggregate-receipt', type=Path)
    parser.add_argument('--suite-dir', type=Path)
    parser.add_argument('--browser-log', type=Path, action='append', default=[])
    parser.add_argument('--browser-baseline-sha', help='declared baseline only; does not verify patched source/native identity')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.self_check:
        self_check()
        return 0
    if not all((args.aggregate_log, args.aggregate_receipt, args.suite_dir, args.evidence_sha, args.out)):
        parser.error('provide aggregate log/receipt, suite dir, evidence SHA and new output path')
    if not re.fullmatch(r'[0-9a-f]{40}', args.evidence_sha):
        parser.error('evidence-sha must be a complete commit SHA')
    if args.browser_log and not re.fullmatch(r'[0-9a-f]{40}', args.browser_baseline_sha or ''):
        parser.error('browser logs require a complete browser-baseline-sha label')
    if args.out.exists():
        parser.error('refusing to overwrite existing evidence output')
    report = build_report(args)
    with args.out.open('x', encoding='utf-8') as output:
        json.dump(report, output, ensure_ascii=False, indent=2)
        output.write('\n')
    print(json.dumps(dict(output=str(args.out), suites=len(report['suites']),
                          aggregate_process_seconds=report['aggregate_process_seconds'],
                          outside_suite_gap_unattributed=report['outside_suite_gap_seconds_approximate'],
                          static_source_census=report['static_source_census']), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
