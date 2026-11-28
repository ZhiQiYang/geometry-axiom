"""Physical CSS/markup withdrawals; Node contracts and Chromium stay separate.

Source: python3 -B tests/diagnostics/r03_preview_length_withdrawals.py --out /tmp/r03-length-source
Browser: GEOMETRY_CHROME=/path/to/chrome \
  python3 -B tests/diagnostics/r03_preview_length_withdrawals.py --browser --out /tmp/r03-length-chrome

Browser mode starts a separate owned service after each source mutation;
GEOMETRY_TEST_URL is never used. Each service proves its PID, current checkout,
fresh native bridge and new session before cdp_test can reset that service.
Every cdp_test invocation owns its own browser process. It restores the exact CSS bytes in
finally, and saves stdout/stderr for each actual baseline/withdrawal/restore.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import sys
import threading
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
CSS = ROOT / "geometry-web/framing-template-workspace.css"
MARKUP = ROOT / "geometry-web/framing-template-workspace.js"
RULE = (b".ft-workspace .ft-results [data-ft-length]"
        b"{white-space:nowrap;overflow-wrap:normal;word-break:normal}\n")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def run_browser(command, env, stem, sessions):
    """Never connect a destructive fixture to a caller-supplied service."""
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    feedback = stem.with_suffix(stem.suffix + '.feedback')
    feedback.mkdir()
    owned_env = dict(env, GEOMETRY_TEST_URL='http://127.0.0.1:' + str(port) + '/',
                     GEOMETRY_ISOLATED_SERVICE='1', GEOMETRY_FEEDBACK_DIR=str(feedback))
    ready = threading.Event()
    process = None
    with stem.with_suffix(stem.suffix + '.server.stdout.log').open('wb') as stdout, \
            stem.with_suffix(stem.suffix + '.server.stderr.log').open('wb') as stderr:
        try:
            process = subprocess.Popen([sys.executable, '-u', '-B', 'geometry-web/serve.py', str(port)],
                                       cwd=ROOT, env=owned_env, stdout=subprocess.PIPE, stderr=stderr,
                                       start_new_session=(os.name != 'nt'))
            def collect():
                for line in process.stdout:
                    stdout.write(line)
                    stdout.flush()
                    if line.startswith(('http://localhost:' + str(port) + ' ').encode()):
                        ready.set()
            reader = threading.Thread(target=collect, daemon=True)
            reader.start()
            # Event signalled by the server's post-bind readiness line: no sleep.
            if not ready.wait(30) or process.poll() is not None:
                raise AssertionError('R03_LENGTH_OWNED_SERVICE_START')
            with urlopen(owned_env['GEOMETRY_TEST_URL'] + 'runtime', timeout=3) as response:
                runtime = json.load(response)
            assert (runtime.get('pid') == process.pid and runtime.get('fresh') is True and
                    Path(runtime.get('root', '')).resolve() == ROOT and runtime.get('session') and
                    runtime['session'] not in sessions), 'R03_LENGTH_OWNED_SERVICE_IDENTITY'
            sessions.add(runtime['session'])
            stem.with_suffix(stem.suffix + '.runtime.json').write_text(json.dumps(runtime, indent=2) + '\n')
            result = subprocess.run(command, cwd=ROOT, env=owned_env, capture_output=True, timeout=2100)
            return result, runtime
        finally:
            if process is not None and process.poll() is None:
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True, check=True)
                else:
                    os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    if os.name == 'nt':
                        process.kill()
                    else:
                        os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
            if process is not None:
                reader.join(timeout=5)
                assert not reader.is_alive(), 'R03_LENGTH_OWNED_SERVICE_DRAIN'


def judge_node(completed, phase, name):
    marker = 'R03_LENGTH_NODE_RESULT'
    try:
        events = [json.loads(line) for line in completed.stdout.decode('utf-8').splitlines()]
    except (ValueError, UnicodeError) as error:
        raise AssertionError(marker + ': malformed event stream') from error
    summaries = [row['data'] for row in events if row.get('type') == 'test:summary']
    results = [row for row in events if row.get('type') in ('test:pass', 'test:fail')]
    planned = re.findall(r"^test\('([^']+)'", (ROOT/'tests/test_r03_preview_length.js').read_text(), re.M)
    assert len(summaries) == 1 and len(planned) == 18 and len(set(planned)) == 18, marker + ': complete census'
    assert len(results) == 18 and {row['name'] for row in results} == set(planned), marker + ': exact test identity'
    assert all(row['nesting'] == 0 and not row['skip'] and not row['todo'] for row in results), marker + ': skip/todo/nesting'
    expected = {}
    if phase == 'withdrawn':
        projection_cases = {
            'R2054_WITHDRAW_COUNT_GUARD': ('R2054_CANVAS_PROJECTION rejects a consistent-sum count drift', 'R2054_CANVAS_COUNT_GUARD_REQUIRED'),
            'R2054_WITHDRAW_OWNER_GUARD': ('R2054_CANVAS_PROJECTION rejects duplicate ownership even when shard 2 neighbors remain exact', 'R2054_CANVAS_OWNER_GUARD_REQUIRED'),
            'R2054_WITHDRAW_ORDER_GUARD': ('R2054_CANVAS_PROJECTION rejects changed neighbors while preserving the unique owner', 'R2054_CANVAS_ORDER_GUARD_REQUIRED'),
        }
        if name in projection_cases:
            test_name, assertion = projection_cases[name]
            expected = {test_name: 'Missing expected exception: ' + assertion}
        elif name == 'R03_LENGTH_DROP_CELL_MARKER':
            expected = {
                'R2054_LENGTH_SEMANTIC_CELL follows the actual numeric value in every rendered row': 'R2054_LENGTH_SEMANTIC_CELL',
                'R2054_LENGTH_SEMANTIC_CELL survives column reordering without relabeling another value': 'R2054_LENGTH_REORDERED_SEMANTICS',
            }
        else:
            expected = {'R2054_LENGTH_POLICY overrides shared anywhere only in the semantic R03 length cells': 'R03_PREVIEW_LENGTH_POLICY'}
    failures = {row['name']: row.get('error') for row in results if row['type'] == 'test:fail'}
    assert set(failures) == set(expected), marker + ': wrong failing subtest'
    for test_name, assertion in expected.items():
        error = failures[test_name]
        assert error and error['name'] == 'AssertionError' and error['code'] == 'ERR_ASSERTION' and error['failureType'] == 'testCodeFailure', marker + ': not a normal assertion'
        first = error['message'].splitlines()[0]
        assert first == assertion or first.startswith(assertion + ':'), marker + ': wrong assertion message'
    counts = summaries[0]['counts']
    assert all(counts.get(key) == value for key, value in {'tests':18,'passed':18-len(expected),'failed':len(expected),'cancelled':0,'skipped':0,'todo':0}.items()), marker + ': incomplete result'
    assert summaries[0]['success'] is (not expected) and completed.returncode == int(bool(expected)), marker + ': exit/summary mismatch'
    assert not completed.stderr, marker + ': unexpected stderr'
    return summaries[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError("output directory must be new")
    args.out.mkdir(parents=True)
    original = {CSS: CSS.read_bytes(), MARKUP: MARKUP.read_bytes()}
    if original[CSS].count(RULE) != 1:
        raise AssertionError("R03_LENGTH_WITHDRAWAL_ANCHOR: expected exactly one reviewed CSS rule")
    cell = b'<td data-ft-length>${m.length}</td>'
    if original[MARKUP].count(cell) != 1:
        raise AssertionError("R03_LENGTH_MARKUP_ANCHOR: expected exactly one reviewed numeric cell")
    variants = {
        "R03_LENGTH_REMOVE_NUMERIC_RULE": ({**original, CSS: original[CSS].replace(RULE, b"")}, "R03_PREVIEW_LENGTH_POLICY"),
        "R03_LENGTH_STYLE_WRONG_FIELD": ({**original, CSS: original[CSS].replace(RULE, RULE.replace(b"data-ft-length", b"data-ft-width"))}, "R03_PREVIEW_LENGTH_POLICY"),
        "R03_LENGTH_DROP_CELL_MARKER": ({**original, MARKUP: original[MARKUP].replace(cell, b'<td>${m.length}</td>')}, "R2054_LENGTH_SEMANTIC_CELL"),
    }
    env = os.environ.copy()
    if args.browser:
        env["GEOMETRY_CANVAS_MODULE_ONLY"] = "1"
        env["GEOMETRY_CANVAS_MODULE"] = "P2054"
        command = ["node", "geometry-web/cdp_test.js"]
    else:
        command = ["node", "--test", "--test-reporter=./tests/diagnostics/r03_preview_length_reporter.cjs", "tests/test_r03_preview_length.js"]
    records = []
    sessions = set()
    try:
        for name, (withdrawn, marker) in variants.items():
            phases = []
            for phase, sources in (("baseline", original), ("withdrawn", withdrawn), ("restored", original)):
                for target, raw in sources.items():
                    target.write_bytes(raw)
                    if target.read_bytes() != raw:
                        raise AssertionError("R03_LENGTH_SOURCE_WRITE")
                stem = args.out / (name + "." + phase)
                if args.browser:
                    completed, runtime = run_browser(command, env, stem, sessions)
                else:
                    completed = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=60)
                stem.with_suffix(stem.suffix + ".stdout.log").write_bytes(completed.stdout)
                stem.with_suffix(stem.suffix + ".stderr.log").write_bytes(completed.stderr)
                output = completed.stdout.decode("utf-8", "replace")
                errors = completed.stderr.decode("utf-8", "replace")
                row = {"phase": phase, "exit": completed.returncode, "sources_sha256": {str(k.relative_to(ROOT)): sha(v) for k,v in sources.items()},
                       "stdout_sha256": sha(completed.stdout), "stderr_sha256": sha(completed.stderr)}
                if args.browser:
                    row['ownedRuntime'] = runtime
                    lines = [line[11:] for line in output.splitlines() if line.startswith("CDP_RESULT ")]
                    if len(lines) != 1:
                        raise AssertionError(name + " " + phase + " lacks one complete CDP_RESULT")
                    result = json.loads(lines[0])
                    if not (result["completed"] is True and result["sectionOrder"] == ["P2054"] and
                            result["unexpectedBrowserExceptions"] == 0 and result["uncaughtBrowserExceptions"] == 0):
                        raise AssertionError(name + " " + phase + " is not a clean P2054 execution")
                    if phase == "withdrawn":
                        if "P2054 R03_PREVIEW_LENGTH_SINGLE_LINE v2 1400 ✗" not in output:
                            raise AssertionError(name + " wrong browser failure; a crash is not a kill")
                    elif result["sections"] != {"P2054": 15} or result["failedAssertions"] != 0:
                        raise AssertionError(name + " " + phase + " is not all 15 planned assertions")
                    row["cdp_result"] = result
                else:
                    row['node_result'] = judge_node(completed, phase, name)
                phases.append(row)
            if [row["exit"] for row in phases] != [0, 1, 0]:
                raise AssertionError(name + " expected 0/1/0, got " + repr([row["exit"] for row in phases]))
            records.append({"name": name, "phases": phases})
    finally:
        for target, raw in original.items():
            target.write_bytes(raw)
            if target.read_bytes() != raw:
                raise AssertionError("R03_LENGTH_RESTORE_EXACT_BYTES")
    report = {"schema": "r03-preview-length-withdrawals/3", "mode": "chromium-layout" if args.browser else "node-markup-and-source-policy",
              "base": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "command": command, "sources_restored_sha256": {str(k.relative_to(ROOT)): sha(k.read_bytes()) for k in original}, "withdrawals": records,
              "browserExecuted": args.browser}
    (args.out / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
