#!/usr/bin/env python3
"""R2 PF-6 HTTP/WSL functional withdrawals in isolated Python source copies.

Linux protocol fixtures exercise the real handler and bridge writer. These are
not Windows, native geometry, Chrome, or official mutation ledger receipts.
Tests are copied unchanged; only the named product guard is withdrawn. A named
assertion and exact 0/1/0 are required; syntax/import/setup errors do not count.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BASE = 'b3c4b981bb96b118c1c05b7a1bd98062d710c8b2'
TRANSPORT = 'geometry-web/panel_fill_builder_transport.py'
SERVE = 'geometry-web/serve.py'
TEST = 'tests.test_panel_fill_builder_transport.PF6HTTPProtocol.'
SOURCES = [
    TRANSPORT, SERVE, 'geometry-web/feedback_store.py',
    'geometry-web/wait_trace.py', 'geometry-web/native_context.py',
    'geometry-web/runtime_version.py', 'tests/__init__.py',
    'tests/test_panel_fill_builder_transport.py', 'tests/test_serve.py',
    'tests/test_panel_fill_builder.py', 'tests/test_panel_fill_layout.py',
    'tests/test_panel_fill_finish_surface.py', 'tests/_bridge.py',
    'tests/binaries.py', 'tests/pf6_app_oracle.py',
]
ROWS = [
    ('PF6_HTTP_ACCEPT_ZERO_TOKEN', TRANSPORT, 'PF6_HTTP_TOKEN_POSITIVE_UINT32',
     'test_terminals_require_exact_receipted_positive_uint32',
     "r'pf6-(confirm|cancel) ([1-9][0-9]{0,9})'",
     "r'pf6-(confirm|cancel) (0|[1-9][0-9]{0,9})'"),
    ('PF6_HTTP_DROP_WSL_SUGGEST', SERVE, 'PF6_HTTP_WSL_SUGGEST_PATH',
     'test_suggest_windows_wsl_path_reaches_bridge_as_posix',
     ', "pf6-suggest "', ''),
    ('PF6_HTTP_DROP_WSL_SELECT', SERVE, 'PF6_HTTP_WSL_SELECT_PATH',
     'test_select_windows_wsl_path_reaches_bridge_as_posix',
     ', "pf6-select "', ''),
    ('PF6_HTTP_DROP_VERSION_GUARD', TRANSPORT, 'PF6_HTTP_REQUIRED_HEADERS',
     'test_all_three_headers_are_required_before_native',
     "headers.get('X-Geometry-Version') != version", 'False'),
    ('PF6_HTTP_DROP_SESSION_GUARD', TRANSPORT, 'PF6_HTTP_REQUIRED_HEADERS',
     'test_all_three_headers_are_required_before_native',
     "headers.get('X-Geometry-Session') != session", 'False'),
    ('PF6_HTTP_DROP_REQUEST_ID_GUARD', TRANSPORT, 'PF6_HTTP_REQUIRED_HEADERS',
     'test_all_three_headers_are_required_before_native',
     'not _uuid(request_id)', 'False'),
    ('PF6_HTTP_ACCEPT_SUGGEST_CLIENT_PATH', SERVE, 'PF6_HTTP_NO_CLIENT_PATH',
     'test_file_commands_are_not_a_public_api_backdoor',
     ', "pf6-suggest"', ''),
    ('PF6_HTTP_ACCEPT_SELECT_CLIENT_PATH', SERVE, 'PF6_HTTP_NO_CLIENT_PATH',
     'test_file_commands_are_not_a_public_api_backdoor',
     ', "pf6-select"', ''),
    ('PF6_HTTP_DROP_RECEIPT_REPLAY_CACHE', SERVE, 'PF6_HTTP_EXACT_REPLAY',
     'test_replay_binds_raw_body_and_never_executes_twice',
     'cached = native.api_receipts.get(request_id)', 'cached = None'),
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    options = parser.parse_args()
    output = options.out.resolve()
    if output.exists() or output == ROOT or ROOT in output.parents:
        parser.error('--out must be a new directory outside the repository')
    originals = {relative: (ROOT / relative).read_bytes() for relative in SOURCES}
    output.mkdir(parents=True)
    records = []
    with tempfile.TemporaryDirectory(prefix='pf6-r2-transport-withdraw-') as temporary:
        work = Path(temporary)
        for relative, raw in originals.items():
            path = work / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        for name, relative, assertion, test, before, after in ROWS:
            original = originals[relative]
            if b'\r' in original or original.count(before.encode()) != 1:
                raise AssertionError(name + ': exact LF product anchor must occur once')
            mutant = original.replace(before.encode(), after.encode(), 1)
            compile(mutant, relative, 'exec')
            command = [sys.executable, '-B', '-m', 'unittest', '-v', TEST + test]
            runs, failure = [], ''
            target = work / relative
            try:
                for phase, raw in [('baseline', original), ('withdrawn', mutant), ('restored', original)]:
                    target.write_bytes(raw)
                    env = dict(os.environ)
                    env.pop('GEOMETRY_WAIT_TRACE', None)
                    result = subprocess.run(command, cwd=work, env=env, capture_output=True, timeout=60)
                    logs = {}
                    for suffix, content in [('stdout', result.stdout), ('stderr', result.stderr)]:
                        path = output / (name + '-' + phase + '.' + suffix)
                        path.write_bytes(content)
                        logs[suffix] = {'file': path.name, 'bytes': len(content), 'sha256': sha(content)}
                    runs.append({'phase': phase, 'exit': result.returncode, **logs})
                    if phase == 'withdrawn':
                        failure = (result.stdout + result.stderr).decode('utf-8', 'replace')
            finally:
                target.write_bytes(original)
            codes = [run['exit'] for run in runs]
            named = (assertion in failure and 'AssertionError:' in failure and 'FAIL: ' + test in failure
                     and 'ERROR:' not in failure and 'SyntaxError' not in failure and 'ImportError' not in failure)
            record = {'name': name, 'source': relative, 'test': TEST + test, 'assertion': assertion,
                      'command': command, 'cwd': str(work), 'sourceSha256': sha(original),
                      'withdrawnSha256': sha(mutant), 'exitCodes': codes, 'runs': runs,
                      'sourceRestoredExactly': target.read_bytes() == original,
                      'status': 'killed' if codes == [0, 1, 0] and named else 'blocked'}
            records.append(record)
            if record['status'] != 'killed':
                break
    for relative, original in originals.items():
        if (ROOT / relative).read_bytes() != original:
            raise AssertionError('PF6_HTTP_WITHDRAW_INPUT_CHANGED: ' + relative)
    report = {'schema': 'pf6-r2-transport-withdrawals/1', 'base': BASE,
              'windowsExecuted': False, 'browserExecuted': False, 'officialMutationEvidence': False,
              'inputs': [{'path': path, 'bytes': len(raw), 'sha256': sha(raw)} for path, raw in sorted(originals.items())],
              'records': records,
              'status': 'passed' if len(records) == len(ROWS) and all(row['status'] == 'killed' for row in records) else 'blocked'}
    (output / 'receipt.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'status': report['status'], 'records': [
        {'name': row['name'], 'exitCodes': row['exitCodes'], 'status': row['status']} for row in records]}, indent=2))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
