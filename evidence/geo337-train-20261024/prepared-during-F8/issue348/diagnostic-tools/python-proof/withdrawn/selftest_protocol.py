"""Pure Python synthetic protocol/negative controls. No child product or C."""
import argparse, copy, json, os, subprocess, tempfile
from pathlib import Path
import sidecar
import launch_diagnostic as launcher

PAYLOAD = b'loadfile /synthetic/scene512.scene\ndump\nobjects\nreferences\n'

def sequence():
    events = []
    def event(kind, command, rc=0, length=0, eof=0, error=0):
        events.append(dict(seq=len(events)+1, kind=kind, command=command,
                           monotonic_ns=1000+len(events)*100, rc=rc,
                           length=length, feof=eof, ferror=error))
    for i, line in enumerate(PAYLOAD.splitlines(keepends=True), 1):
        event('stdin_line_returned', i, 1, len(line))
        event('stdout_flush_enter', i)
        event('stdout_flush_return', i)
    event('stdin_eof', 4, eof=16)
    return events

def packet(events, **overrides):
    values = dict(magic=sidecar.MAGIC, version=1, attached=1, attempts=len(events),
                  successes=len(events), faults=0, reserved0=0, reserved1=0)
    values.update(overrides)
    return (b''.join(json.dumps(e).encode()+b'\n' for e in events), sidecar.STATUS.pack(*values.values()))

def run_tests():
    checks = []
    def check(name, predicate):
        try:
            okay = bool(predicate())
            checks.append(dict(name=name, passed=okay))
        except BaseException as exc:
            checks.append(dict(name=name, passed=False, exception=repr(exc)))
    def observed(events, completed=False, **overrides):
        return sidecar.inspect_events(*packet(events, **overrides), PAYLOAD, completed=completed)
    valid = sequence()
    check('four-original-commands-observable-without-product-verdict', lambda: observed(valid, True)['valid'] and observed(valid, True)['product_gate_verdict'] is None)
    check('timeout-with-handler-open-is-prefix-only', lambda: observed(valid[:4])['valid'] and observed(valid[:4])['last_boundary']['command'] == 2)
    check('timeout-during-flush-is-distinct-boundary', lambda: observed(valid[:2])['valid'] and observed(valid[:2])['last_boundary']['kind'] == 'stdout_flush_enter')
    wrong = copy.deepcopy(valid); wrong[0]['length'] += 1
    check('reject-wrong-command-line-length', lambda: not observed(wrong, True)['valid'])
    wrong = copy.deepcopy(valid); wrong[3]['command'] = 4
    check('reject-command-identity-drift', lambda: not observed(wrong, True)['valid'])
    wrong = copy.deepcopy(valid); wrong[1]['seq'] += 1
    check('reject-event-sequence-gap', lambda: not observed(wrong, True)['valid'])
    wrong = copy.deepcopy(valid); wrong[1]['monotonic_ns'] = 1
    check('reject-clock-regression', lambda: not observed(wrong, True)['valid'])
    check('reject-missing-flush-return', lambda: not observed([valid[0], valid[3]], True)['valid'])
    wrong = copy.deepcopy(valid); wrong[-1]['ferror'] = 32
    check('reject-read-error-mislabeled-eof', lambda: not observed(wrong, True)['valid'])
    wrong[-1]['kind'] = 'stdin_error'
    check('read-error-recorded-without-relabeling-it-eof', lambda: observed(wrong, True)['valid'] and observed(wrong, True)['last_boundary']['kind'] == 'stdin_error')
    check('reject-unattached-wrapper', lambda: not observed([], attached=0)['valid'])
    check('reject-observer-io-fault', lambda: not observed(valid, True, faults=1)['valid'])
    check('reject-dropped-event-count', lambda: not observed(valid, True, attempts=14, successes=14)['valid'])
    check('reject-incomplete-write', lambda: not observed(valid, True, attempts=14)['valid'])
    raw, status = packet(valid)
    check('reject-truncated-json-event', lambda: not sidecar.inspect_events(raw[:-1], status, PAYLOAD)['valid'])
    check('reject-partial-normal-terminal', lambda: not observed(valid[:4], True)['valid'])
    check('reject-four-separate-budget-payload', lambda: not sidecar.inspect_events(raw, status, b'loadfile /synthetic/scene512.scene\n')['valid'])

    with tempfile.TemporaryDirectory(prefix='geo348-python-only-') as tmp:
        root = Path(tmp)
        def emit(kwargs, events):
            body, header = packet(events)
            os.write(int(kwargs['env']['GEO348_DIAG_EVENT_FD']), body)
            os.pwrite(int(kwargs['env']['GEO348_DIAG_STATUS_FD']), header, 0)
        argv = ['synthetic-never-launched']
        completed = subprocess.CompletedProcess(argv, 0, b'{"ok":true}\n'*4, b'diagnostic-stderr-original\x00')
        calls = []
        def original(*args, **kwargs):
            calls.append((args, kwargs))
            emit(kwargs, valid)
            return completed
        got = launcher.capture(argv, PAYLOAD, root/'completed', env={}, source_sha='synthetic',
                               bindings={}, runner=original, synthetic=True)
        row = json.loads((root/'completed/RESULT.json').read_bytes())
        check('original-completedprocess-object-identity', lambda: got is completed)
        check('single-original600-call-with-unchanged-argv-and-stdin', lambda: len(calls)==1 and calls[0][0][0] is argv and calls[0][1]['input'] is PAYLOAD and calls[0][1]['timeout']==600 and calls[0][1]['capture_output'] is True)
        check('full-stdout-and-stderr-original-bytes', lambda: (root/'completed/stdout.bin').read_bytes()==completed.stdout and (root/'completed/stderr.bin').read_bytes()==completed.stderr)
        check('completed-receipt-keeps-gate-null', lambda: row['diagnostic_observation_valid'] and row['product_gate_verdict'] is None and row['synthetic'] is True)
        expired = subprocess.TimeoutExpired(argv, 600, output=b'{"ok":true}\n{"partial":', stderr=b'original-timeout-error')
        def timeout(*args, **kwargs):
            emit(kwargs, valid[:4])
            raise expired
        caught = None
        try:
            launcher.capture(argv, PAYLOAD, root/'timeout', env={}, source_sha='synthetic',
                             bindings={}, runner=timeout, synthetic=True)
        except subprocess.TimeoutExpired as exc:
            caught = exc
        row = json.loads((root/'timeout/RESULT.json').read_bytes())
        check('original-timeoutexpired-object-identity', lambda: caught is expired)
        check('timeout-is-not-completed-or-exit-zero', lambda: row['completed_process_returned'] is False and row['returncode'] is None and row['exception']['type']=='TimeoutExpired')
        check('timeout-full-partial-bytes-preserved', lambda: (root/'timeout/stdout.bin').read_bytes()==expired.stdout and (root/'timeout/stderr.bin').read_bytes()==expired.stderr)
        check('timeout-boundary-not-root-cause', lambda: row['sidecar']['last_boundary']['command']==2 and row['root_cause'] is None)
        empty = subprocess.TimeoutExpired(argv, 600)
        def no_stream(*args, **kwargs):
            emit(kwargs, valid[:1]); raise empty
        try:
            launcher.capture(argv, PAYLOAD, root/'absent', env={}, source_sha='synthetic',
                             bindings={}, runner=no_stream, synthetic=True)
        except subprocess.TimeoutExpired:
            pass
        row = json.loads((root/'absent/RESULT.json').read_bytes())
        check('absent-partial-is-not-fabricated-empty-file', lambda: row['stdout']=={'captured':False} and row['stderr']=={'captured':False} and not (root/'absent/stdout.bin').exists())
        original_writer = launcher.write_json
        def broken_writer(path, value):
            if path.name == 'RESULT.json': raise OSError('synthetic-observer-write-failure')
            return original_writer(path, value)
        launcher.write_json = broken_writer; caught = None
        try:
            launcher.capture(argv, PAYLOAD, root/'writer-error', env={}, source_sha='synthetic',
                             bindings={}, runner=timeout, synthetic=True)
        except subprocess.TimeoutExpired as exc:
            caught = exc
        finally:
            launcher.write_json = original_writer
        check('observer-failure-cannot-replace-original-timeout', lambda: caught is expired and (root/'writer-error/OBSERVER_ERROR.json').exists() and not (root/'writer-error/RESULT.json').exists())
    return checks

if __name__ == '__main__':
    parser = argparse.ArgumentParser();parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args();checks = run_tests()
    result = {'schema':'geo348-python-synthetic-protocol-test/1', 'product_executed':False,
              'wrapper_compiled':False, 'synthetic':True, 'checks':checks,
              'exit':int(any(not x['passed'] for x in checks))}
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'tests':len(checks), 'exit':result['exit'], 'failed':[x['name'] for x in checks if not x['passed']]}))
    raise SystemExit(result['exit'])
