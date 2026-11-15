#!/usr/bin/env python3
"""Canvas flake regression: R116 C09_DOUBLE_CONFIRM_ONE_HISTORY and P90 save wait.

Both flakes were test-contract gaps, not product races: the harness moved on
after a native request's fetch() had returned, while the application was
still finishing that same native operation.

R116 (geometry-web/timber_reuse_test.js)
  settled() only counted the probe's fetch() wrapper.  apiRequest still reads
  the reply and calls ReferenceWorkspace.observe() (the history step) after
  that.  Fix: settled() also requires getEvidenceState().blocked===false,
  which stays true until apiRequest releases its native operation.
  Injection GEOMETRY_R116_LATE_REPLY_BODY=1: the actual confirm reply's bytes
  are held after its headers until settled() has evaluated its configured
  predicate while they were still held.  Named withdrawal
  GEOMETRY_R116_REVERT=R116_REVERT_NATIVE_SETTLE restores the old predicate.

P90 (geometry-web/room_candidate_browser_test.js)
  After #roomConfirm the test waited only for !RoomCollectionWorkspace.hasWork;
  commitRoomDraft then still runs renderObjects(), which writes
  `line canvas-pos` for the new card.  Save refuses while that native write is
  pending (「原生操作結果尚未取得…」) and the test waited 20 s for a file.
  Fix: wait for commitRoomDraft's final status line, and click Save only when
  the app reports no pending native operation.
  Injection GEOMETRY_P90_LATE_CANVAS_POS=1: the actual reply of that
  canvas-pos write is held until the test has evaluated its configured wait
  while the write was still pending.  Named withdrawal
  GEOMETRY_P90_REVERT=P90_REVERT_SAVE_READY restores the old waits.

Determinism (review F3): no timer decides any outcome.  Each held reply is
released by event order: the test first reaches the defect window (reply held,
native operation provably unfinished, the old predicate already true), then
asks its configured predicate once.  The reverted predicate accepts there, so
the history oracle / Save run before the reply, every time; the fixed predicate
refuses there, so the reply is released and the run proceeds as usual.  A slow
or fast runner only changes how long each step takes, not their order.

Usage (an isolated service must already be running):
  GEOMETRY_TEST_URL=http://127.0.0.1:18839/ GEOMETRY_FEEDBACK_DIR=/tmp/fb \\
    python3 tests/canvas_flake_r116_p90_regression.py

Four real browser runs.  Exit 0 only when both fixed runs are green with the
injection proven applied, and both withdrawals fail in the specified way.
Another failing assertion, a crash or a missing proof line never counts.
"""
import json
import os
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
R116_ASSERTION = 'C09_DOUBLE_CONFIRM_ONE_HISTORY'
P90_WAIT = "UI condition timed out at === P90. 零房起步與房間候選跨次保存 ===: typeof window.__roomSave==='string' && !ReferenceWorkspace.busy"
P90_REFUSAL = '原生操作結果尚未取得'


def tagged(lines, tag):
    rows = []
    for line in lines:
        if line.startswith(tag + ' '):
            try:
                rows.append(json.loads(line.split(' ', 1)[1]))
            except ValueError:
                rows.append({'unparsed': line})
    return rows


def run(label, extra, port):
    env = {k: v for k, v in os.environ.items()
           if not (k.startswith('GEOMETRY_') and (k.endswith('_ONLY') or k.endswith('_CASE') or k.endswith('_REVERT')
                                                  or k in ('GEOMETRY_CDP_SHARD', 'GEOMETRY_CDP_FROM_P31',
                                                           'GEOMETRY_R116_LATE_REPLY_BODY', 'GEOMETRY_P90_LATE_CANVAS_POS')))}
    env.update(extra, GEOMETRY_CDP_PORT=str(port))
    start = time.monotonic()
    proc = subprocess.run(['node', 'geometry-web/cdp_test.js'], cwd=ROOT, env=env,
                          capture_output=True, text=True, timeout=300)
    lines = proc.stdout.splitlines()
    result = {'label': label, 'exit': proc.returncode, 'seconds': round(time.monotonic() - start, 1),
              'failed': [line for line in lines if '✗' in line],
              'fatal': [line[len('FATAL: '):] for line in lines if line.startswith('FATAL: ')],
              'cases': tagged(lines, 'R116_CASE_RESULT'), 'diag': tagged(lines, 'R116_DIAG'),
              'late_body': tagged(lines, 'R116_LATE_REPLY_BODY'), 'late_canvas_pos': tagged(lines, 'P90_LATE_CANVAS_POS'),
              'save_traces': tagged(lines, 'P90_SAVE_TRACE'),
              'p90_complete': any(line.startswith('P90 這段沒有新的未捕捉例外 ✓') for line in lines),
              'result': (tagged(lines, 'CDP_RESULT') or [{}])[-1]}
    summary = {k: result[k] for k in ('label', 'exit', 'seconds', 'failed', 'fatal', 'diag', 'late_body', 'late_canvas_pos')}
    summary['passedAssertions'] = result['result'].get('passedAssertions')
    summary['p90Complete'] = result['p90_complete']
    print('CANVAS_FLAKE_RUN ' + json.dumps(summary, ensure_ascii=False), flush=True)
    return result


def r116(port, problems):
    base = {'GEOMETRY_TIMBER_REUSE_ONLY': '1', 'GEOMETRY_TIMBER_REUSE_CASE': 'C09', 'GEOMETRY_R116_LATE_REPLY_BODY': '1'}
    fixed = run('R116 fixed', base, port)
    if fixed['exit'] != 0 or fixed['failed'] or fixed['fatal']:
        problems.append('R116 fixed run is not green')
    if not any(c.get('id') == 'C09' and c.get('status') == 'pass' for c in fixed['cases']):
        problems.append('R116 fixed run has no passing C09')
    if not any(x.get('releasedBy') == 'settle-predicate-false' and not x.get('acceptedWhileHeld') for x in fixed['late_body']):
        problems.append('R116 fixed run did not prove settled() refused while the reply body was held')

    withdrawn = run('R116 withdrawn R116_REVERT_NATIVE_SETTLE', {**base, 'GEOMETRY_R116_REVERT': 'R116_REVERT_NATIVE_SETTLE'}, port + 1)
    case = next((c for c in withdrawn['cases'] if c.get('id') == 'C09'), {})
    first = case.get('firstFailure') or case
    # The held reply is released right after the history verdict, so cleanup
    # drains normally and the only failure is the assertion itself.
    if withdrawn['exit'] != 1 or withdrawn['fatal']:
        problems.append('R116 withdrawal did not end as a normal failing run')
    if [line.split()[1] for line in withdrawn['failed']] != [R116_ASSERTION]:
        problems.append('R116 withdrawal must fail exactly ' + R116_ASSERTION)
    if first.get('kind') != 'assertion' or first.get('assertion') != R116_ASSERTION:
        problems.append('R116 withdrawal first failure is not ' + R116_ASSERTION)
    if not any(d.get('afterUndo') == d.get('beforeUndo') and d.get('newEntries') == [] and d.get('lenOk') is False
               and d.get('groupNull') is True and d.get('redoEmpty') is True and d.get('evidenceBlocked') is True
               for d in withdrawn['diag']):
        problems.append('R116 withdrawal diagnostic does not show the not-yet-observed history step')
    if not any(x.get('phase') == 'late' and x.get('acceptedWhileHeld') is True for x in withdrawn['late_body']):
        problems.append('R116 withdrawal did not check history while the reply body was still held')


def p90(port, problems):
    base = {'GEOMETRY_ROOM_CANDIDATE_ONLY': '1', 'GEOMETRY_P90_LATE_CANVAS_POS': '1'}
    fixed = run('P90 fixed', base, port)
    # GEOMETRY_ROOM_CANDIDATE_ONLY also runs P358/R358 after P90.  Those are
    # covered by the shard's own full sequence; this proof only judges P90, so
    # an unrelated later section cannot turn this script into another flake.
    if (any(line.startswith('P90 ') for line in fixed['failed']) or any('P90' in f for f in fixed['fatal'])
            or not fixed['p90_complete']):
        problems.append('P90 fixed run is not green')
    if not any(x.get('phase') == 'delivered' and x.get('acceptedWhileHeld') == [] and x.get('releasedBy') == 'room-confirmed'
               and str(x.get('command', '')).startswith('line canvas-pos boundary ') for x in fixed['late_canvas_pos']):
        problems.append('P90 fixed run did not prove its confirm wait refused while the canvas-pos reply was held')

    withdrawn = run('P90 withdrawn P90_REVERT_SAVE_READY', {**base, 'GEOMETRY_P90_REVERT': 'P90_REVERT_SAVE_READY'}, port + 1)
    if withdrawn['exit'] != 1 or withdrawn['failed']:
        problems.append('P90 withdrawal did not end as a failing run without other assertions')
    if withdrawn['fatal'] != [P90_WAIT]:
        problems.append('P90 withdrawal must stop exactly at the original save wait')
    if not any(x.get('saveClickedWhileHeld') is True and 'room-confirmed' in x.get('acceptedWhileHeld', [])
               for x in withdrawn['late_canvas_pos']):
        problems.append('P90 withdrawal did not click Save while the canvas-pos reply was held')
    refused = [e for trace in withdrawn['save_traces'] for e in trace.get('events', [])
               if e.get('phase') == 'toast' and any(P90_REFUSAL in m for m in e.get('messages', []))]
    if not refused:
        problems.append('P90 withdrawal trace does not show Save refusing a pending native write')


def main():
    if not os.environ.get('GEOMETRY_TEST_URL') or not os.environ.get('GEOMETRY_FEEDBACK_DIR'):
        sys.exit('GEOMETRY_TEST_URL and GEOMETRY_FEEDBACK_DIR are required (an isolated running service).')
    port = int(os.environ.get('CANVAS_FLAKE_CDP_PORT', '9368'))
    problems = []
    r116(port, problems)
    p90(port + 2, problems)
    verdict = {'schema': 'canvas-flake-r116-p90-regression/1', 'problems': problems,
               'withdrawals': ['R116_REVERT_NATIVE_SETTLE', 'P90_REVERT_SAVE_READY']}
    print('CANVAS_FLAKE_VERDICT ' + json.dumps(verdict, ensure_ascii=False))
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
