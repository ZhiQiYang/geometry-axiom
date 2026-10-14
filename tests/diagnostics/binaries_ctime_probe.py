#!/usr/bin/env python3
"""Collect #212 evidence without replacing or changing its unittest body.

Linux example (this probe does not compile or execute native binaries):
  ulimit -s 16384
  python3 tests/diagnostics/binaries_ctime_probe.py --output /tmp/ctime-evidence

Runs 200 original cases without instrumentation, then 200 with three stat
observations around the existing utime calls. Additional stat calls can suppress
a timing failure. Neither a clean observed run nor a minimum positive timestamp
delta proves the absence of a race or the filesystem's universal resolution.
Exit 0: all requested cases passed and telemetry is complete; 1: test failure;
2: incomplete/invalid evidence, skipped cases, or an infrastructure error.
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import csv
import datetime
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time
import traceback
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
TARGET_FILE = ROOT / 'tests' / 'test_binaries.py'
TARGET_CLASS = 'BinaryFreshnessTests'
TARGET_METHOD = 'test_same_size_rewrite_restoring_mtime_is_not_published'
# LF-normalized, indented AST method text, including its final newline.
EXPECTED_METHOD_SHA256 = '47c7a13a67ab63f4fe4321a36b502f5fa5154af7bbf373e0f9f4c526d8f08e8f'
# These fixture assumptions are coupled to EXPECTED_METHOD_SHA256 above.
EXPECTED_PAYLOAD = b'0123456789abcdef'
STAT_FIELDS = ('st_dev', 'st_ino', 'st_size', 'st_atime_ns', 'st_mtime_ns',
               'st_ctime_ns', 'st_birthtime_ns')
STAGES = ('before', 'after_rewrite', 'after_restore')
LIMIT = 100_000


def sha(data):
    return hashlib.sha256(data).hexdigest()


def target_source_metadata():
    raw = TARGET_FILE.read_bytes()
    normalized = raw.replace(b'\r\n', b'\n')
    source = normalized.decode('utf-8')
    cls = next(node for node in ast.parse(source).body
               if isinstance(node, ast.ClassDef) and node.name == TARGET_CLASS)
    method = next(node for node in cls.body
                  if isinstance(node, ast.FunctionDef) and node.name == TARGET_METHOD)
    text = ''.join(source.splitlines(keepends=True)[method.lineno - 1:method.end_lineno])
    return {'method_sha256': sha(text.encode('utf-8')),
            'expected_method_sha256': EXPECTED_METHOD_SHA256,
            'method_lines': [method.lineno, method.end_lineno],
            'file_raw_sha256': sha(raw), 'file_lf_sha256': sha(normalized)}


def load_target():
    spec = importlib.util.spec_from_file_location('ctime_probe_target', TARGET_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, TARGET_CLASS), module


def source_hashes():
    hashes = {}
    for path in (TARGET_FILE, ROOT / 'tests' / 'binaries.py', Path(__file__).resolve()):
        raw = path.read_bytes()
        hashes[str(path.relative_to(ROOT))] = {
            'raw_sha256': sha(raw), 'lf_sha256': sha(raw.replace(b'\r\n', b'\n'))}
    return hashes


def stat_dict(value):
    return {name: getattr(value, name, None) for name in STAT_FIELDS}


class UtimesObserver:
    """Only wrap utime for this case's neutral.bin; never intercept stat/read.

    Keep stat_result objects until the case ends. No JSON, logging, content
    hashing, extra file opens, sleeps, or descriptor observers in the race window.
    fstat is intentionally not instrumented: that would also change the control
    flow inside the product's hash operation.
    """

    def __init__(self, case):
        self.case = case
        self.original = os.utime
        self.calls = 0
        self.samples = []
        self.errors = []
        self.payload = None

    def readback(self, path):
        """Run after the test body, before its temporary directory is removed."""
        try:
            # Use builtin open: Path.open is replaced by the target's Rewriter
            # during the test. Never trigger a second rewrite for observation.
            with open(path, 'rb') as stream:
                payload = stream.read()
            rewritten = bytes([EXPECTED_PAYLOAD[0] ^ 0xff]) + EXPECTED_PAYLOAD[1:]
            self.payload = {'expected_original_hex': EXPECTED_PAYLOAD.hex(),
                            'expected_original_sha256': sha(EXPECTED_PAYLOAD),
                            'actual_hex': payload.hex(), 'actual_sha256': sha(payload),
                            'byte_count': len(payload),
                            'changed_vs_expected_original': payload != EXPECTED_PAYLOAD,
                            'matches_expected_rewrite': payload == rewritten,
                            'error': None}
        except OSError as exc:
            self.payload = {'error': repr(exc)}

    def capture(self, stage, path):
        try:
            self.samples.append((stage, os.stat(path)))
        except OSError as exc:
            # Observation failure must not replace the original test outcome.
            self.errors.append((stage, repr(exc)))

    def __call__(self, path, *args, **kwargs):
        target = getattr(self.case, 'root', None)
        if target is None or isinstance(path, int) or Path(path) != target / 'neutral.bin':
            return self.original(path, *args, **kwargs)
        self.calls += 1
        if self.calls == 1:
            # Register before the initial utime, so this bookkeeping precedes
            # the entire measured before/rewrite/restore interval.
            self.case.addCleanup(self.readback, Path(path))
        if self.calls == 2:
            self.capture('after_rewrite', path)
        result = self.original(path, *args, **kwargs)
        if self.calls == 1:
            self.capture('before', path)
        elif self.calls == 2:
            self.capture('after_restore', path)
        return result

    def report(self):
        stages = [stage for stage, _ in self.samples]
        return {'utime_calls': self.calls,
                'complete': (self.calls == 2 and stages == list(STAGES) and not self.errors
                             and self.payload is not None and self.payload.get('error') is None),
                'errors': self.errors,
                'payload_readback': self.payload,
                'snapshots': {stage: stat_dict(value) for stage, value in self.samples}}


def result_summary(result):
    failures = [{'test': str(case), 'traceback': detail} for case, detail in result.failures]
    errors = [{'test': str(case), 'traceback': detail} for case, detail in result.errors]
    skips = [{'test': str(case), 'reason': detail} for case, detail in result.skipped]
    expected = [{'test': str(case), 'traceback': detail}
                for case, detail in result.expectedFailures]
    unexpected = [str(case) for case in result.unexpectedSuccesses]
    if errors:
        status = 'error'
    elif failures or unexpected:
        status = 'failure'
    elif skips:
        status = 'skip'
    elif expected:
        status = 'expected_failure'
    elif result.testsRun == 1 and result.wasSuccessful():
        status = 'pass'
    else:
        status = 'incomplete'
    return {'status': status, 'tests_run': result.testsRun, 'failures': failures,
            'errors': errors, 'skips': skips, 'expected_failures': expected,
            'unexpected_successes': unexpected,
            'oserror_not_raised': any('AssertionError: OSError not raised' in row['traceback']
                                     for row in failures)}


def run_case(case, observed):
    output = io.StringIO()
    observer = UtimesObserver(case) if observed else None
    started = time.perf_counter_ns()
    # Context-managed patches survive the test's patch.stopall cleanup, but are
    # restored after each case. Do not use patch.start() around the whole loop.
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        with patch.object(os, 'utime', observer) if observed else contextlib.nullcontext():
            result = unittest.TextTestRunner(stream=output, verbosity=2).run(
                unittest.TestSuite([case]))
    record = result_summary(result)
    record['elapsed_ns'] = time.perf_counter_ns() - started
    record['unittest_output'] = output.getvalue()
    record['telemetry'] = observer.report() if observer else None
    record['fixture_root'] = str(getattr(case, 'root', ''))
    return record


def delta_summary(deltas):
    positive = [value for value in deltas if value > 0]
    return {'count': len(deltas), 'zero': sum(value == 0 for value in deltas),
            'negative': sum(value < 0 for value in deltas), 'positive': len(positive),
            'min_positive_delta_ns_observed': min(positive) if positive else None,
            'max_positive_delta_ns_observed': max(positive) if positive else None}


def measure_ctime(temp_base, samples):
    readings = []
    with tempfile.TemporaryDirectory(prefix='ctime-resolution-', dir=temp_base) as directory:
        path = Path(directory) / 'clock.bin'
        path.write_bytes(b'ctime probe')
        before = path.stat()
        readings.append(stat_dict(before))
        for _ in range(samples):
            os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
            before = path.stat()
            readings.append(stat_dict(before))
        measured_path = str(path)
    deltas = [right['st_ctime_ns'] - left['st_ctime_ns']
              for left, right in zip(readings, readings[1:])]
    return {'path': measured_path, 'operation': 'utime(preserved atime/mtime ns), then stat',
            'samples_requested': samples, 'readings': readings, 'deltas_ns': deltas,
            'summary': delta_summary(deltas),
            'interpretation': 'Minimum observed positive delta only; not a universal kernel or filesystem resolution guarantee.'}


def command_metadata(args):
    try:
        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=10)
        return {'argv': args, 'exit_code': result.returncode,
                'stdout': result.stdout, 'stderr': result.stderr}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'argv': args, 'exit_code': None, 'error': repr(exc)}


def environment_metadata(temp_base):
    info = {'platform': platform.platform(), 'uname': platform.uname()._asdict(),
            'os_name': os.name, 'sys_platform': sys.platform, 'python': sys.version,
            'python_executable': sys.executable, 'temp_base': str(temp_base),
            'argv': sys.argv, 'git_head': command_metadata(['git', 'rev-parse', 'HEAD']),
            'git_dirty': command_metadata(['git', 'status', '--porcelain=v1']),
            'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    if sys.platform == 'linux':
        import resource
        info['stack_limit_bytes_soft_hard'] = list(resource.getrlimit(resource.RLIMIT_STACK))
        info['gcc'] = command_metadata(['gcc', '--version'])
        info['findmnt'] = command_metadata(['findmnt', '--json', '--target', str(temp_base)])
        info['stat_filesystem'] = command_metadata(['stat', '-f', str(temp_base)])
        try:
            info['proc_mountinfo'] = Path('/proc/self/mountinfo').read_text()
        except OSError as exc:
            info['proc_mountinfo_error'] = repr(exc)
    return info


def summarize(records, requested):
    summary = {}
    for mode in ('control', 'observed'):
        rows = [row for row in records if row['mode'] == mode]
        counts = {name: sum(row['status'] == name for row in rows)
                  for name in ('pass', 'failure', 'error', 'skip', 'expected_failure', 'incomplete')}
        counts.update({'requested': requested, 'completed': len(rows),
                       'failure_rate': counts['failure'] / len(rows) if rows else None,
                       'oserror_not_raised': sum(row['oserror_not_raised'] for row in rows),
                       'elapsed_seconds': sum(row['elapsed_ns'] for row in rows) / 1e9})
        if mode == 'observed':
            counts['incomplete_telemetry'] = sum(not row['telemetry']['complete'] for row in rows)
            valid = [row['telemetry']['snapshots'] for row in rows if row['telemetry']['complete']]
            counts['ctime_unchanged_all_three'] = sum(
                len({stages[name]['st_ctime_ns'] for name in STAGES}) == 1 for stages in valid)
            counts['ctime_before_equals_restore'] = sum(
                stages['before']['st_ctime_ns'] == stages['after_restore']['st_ctime_ns']
                for stages in valid)
        summary[mode] = counts
    return summary


def evidence_exit_code(report):
    if report.get('infrastructure_errors'):
        return 2
    for value in report['summary'].values():
        if (value['completed'] != value['requested'] or value['skip']
                or value['expected_failure'] or value['incomplete']
                or value.get('incomplete_telemetry')):
            return 2
    return 1 if any(value['failure'] or value['error']
                    for value in report['summary'].values()) else 0


def save_evidence(directory, report):
    fields = ['mode', 'iteration', 'status', 'elapsed_ns', 'telemetry_complete']
    fields += [stage + '_' + name for stage in STAGES for name in STAT_FIELDS]
    with (directory / 'iterations.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for record in report['iterations']:
            row = {key: record[key] for key in ('mode', 'iteration', 'status', 'elapsed_ns')}
            if record['telemetry']:
                row['telemetry_complete'] = record['telemetry']['complete']
                for stage, snapshot in record['telemetry']['snapshots'].items():
                    row.update({stage + '_' + key: value for key, value in snapshot.items()})
            writer.writerow(row)
    with (directory / 'unittest.log').open('w', encoding='utf-8') as stream:
        for record in report['iterations']:
            stream.write('\n=== %s iteration %d ===\n' % (record['mode'], record['iteration']))
            stream.write(record['unittest_output'])
        stream.write('\nprobe_exit_code=%d\n' % report['exit_code'])
    resolution = report.get('ctime_measurement')
    if resolution:
        with (directory / 'ctime-readings.csv').open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=['sample', 'delta_ns', *STAT_FIELDS])
            writer.writeheader()
            for index, reading in enumerate(resolution['readings']):
                writer.writerow({'sample': index,
                                 'delta_ns': resolution['deltas_ns'][index - 1] if index else '',
                                 **reading})
    # Write the report after its supporting artifacts, so an earlier output
    # failure cannot leave an apparently successful final report behind.
    (directory / 'report.json').write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def bounded_positive(value):
    number = int(value)
    if not 1 <= number <= LIMIT:
        raise argparse.ArgumentTypeError('must be between 1 and %d' % LIMIT)
    return number


def bounded_samples(value):
    number = bounded_positive(value)
    if number < 2:
        raise argparse.ArgumentTypeError('samples must be at least 2')
    return number


def warn_incomplete(message):
    try:
        print('Evidence incomplete: ' + message, file=sys.stderr, flush=True)
    except OSError:
        # A broken stderr must not turn an infrastructure error into exit 1.
        pass


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--iterations', type=bounded_positive, default=200)
    parser.add_argument('--samples', type=bounded_samples, default=10_000)
    parser.add_argument('--output', type=Path, required=True, help='new or empty evidence directory')
    parser.add_argument('--temp-root', type=Path, help='existing base directory, used by both unittest and timestamp probe')
    parser.add_argument('--allow-non-linux', action='store_true', help='plumbing only; results are not Linux evidence')
    args = parser.parse_args(argv)
    if sys.platform != 'linux' and not args.allow_non_linux:
        parser.error('Linux is required. --allow-non-linux is for plumbing only, not #212 inference.')
    temp_base = (args.temp_root or Path(tempfile.gettempdir())).resolve()
    if not temp_base.is_dir():
        parser.error('--temp-root must be an existing directory')
    output = args.output.resolve()
    try:
        if output.exists() and (not output.is_dir() or any(output.iterdir())):
            parser.error('--output must be a new or empty directory; evidence is never overwritten')
        output.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        warn_incomplete('cannot prepare output directory %s: %r' % (output, exc))
        return 2
    report = {'schema': 'geometry-binaries-ctime-probe/1', 'iterations': [],
              'infrastructure_errors': [], 'linux_evidence': sys.platform == 'linux',
              'limitations': [
                  'Observed stat calls can suppress the race; control cases have no utime/stat wrapper.',
                  'No instrumented fstat: snapshots are pathname stat values near the two original utime calls.',
                  'Observed payload readback uses builtin open during unittest cleanup, after the test body and before tempfile deletion; it is not a returned-identity digest capture.',
                  'The control block runs before the observed block; their failure rates may also vary over time.',
                  'Zero failures does not disprove timestamp collisions; no automatic verdict is produced.']}
    previous_tempdir = tempfile.tempdir
    try:
        report['environment'] = environment_metadata(temp_base)
        report['source'] = target_source_metadata()
        report['source_files_before'] = source_hashes()
        if report['source']['method_sha256'] != EXPECTED_METHOD_SHA256:
            raise RuntimeError('Target method changed; review observer assumptions before updating its source hash guard.')
        target, module = load_target()
        report['imported_modules'] = {'target': str(Path(module.__file__).resolve()),
                                      'binaries': str(Path(module.binaries.__file__).resolve())}
        if Path(module.binaries.__file__).resolve() != ROOT / 'tests' / 'binaries.py':
            raise RuntimeError('Imported binaries module does not match this checkout.')
        tempfile.tempdir = str(temp_base)
        for mode in ('control', 'observed'):
            for iteration in range(1, args.iterations + 1):
                record = run_case(target(TARGET_METHOD), observed=mode == 'observed')
                report['iterations'].append({'mode': mode, 'iteration': iteration, **record})
        report['ctime_measurement'] = measure_ctime(temp_base, args.samples)
        report['source_files_after'] = source_hashes()
        if report['source_files_before'] != report['source_files_after']:
            raise RuntimeError('Experiment source changed during the run.')
    except (Exception, KeyboardInterrupt):
        report['infrastructure_errors'].append(traceback.format_exc())
    finally:
        tempfile.tempdir = previous_tempdir
    report['summary'] = summarize(report['iterations'], args.iterations)
    report['exit_code'] = evidence_exit_code(report)
    report['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        save_evidence(output, report)
    except OSError as exc:
        warn_incomplete('cannot finish writing %s; partial artifacts are preserved: %r' % (output, exc))
        return 2
    try:
        print(json.dumps({'output': str(output), 'linux_evidence': report['linux_evidence'],
                          'summary': report['summary'], 'exit_code': report['exit_code']}, indent=2),
              flush=True)
    except OSError as exc:
        report['infrastructure_errors'].append('Final stdout summary failed: %r' % exc)
        report['exit_code'] = 2
        # Best effort: align saved status with the command's exit code. Keep
        # partial files if this second write also fails; never report success.
        try:
            save_evidence(output, report)
        except OSError:
            pass
        warn_incomplete('final stdout summary failed; inspect potentially partial artifacts at %s: %r'
                        % (output, exc))
    return report['exit_code']


if __name__ == '__main__':
    sys.exit(main())
