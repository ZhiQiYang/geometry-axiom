import importlib.util
import json
import os
import pathlib
import tempfile
import threading
import time
import unittest
import subprocess
import sys
from unittest.mock import patch


class WaitTraceTests(unittest.TestCase):
    def test_http_header_errors_are_recorded_without_replacing_exception(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        script = '''
import sys, pathlib, json
from unittest.mock import Mock
sys.path.insert(0, str(pathlib.Path.cwd() / 'tests'))
from test_serve import BridgeServerTests
t=BridgeServerTests(); t.setUp(); m=t.server_module
try:
    for action in ('_send', 'send_error'):
        handler=object.__new__(m.Handler)
        failure=BrokenPipeError('original header failure')
        handler.send_response=Mock(side_effect=failure)
        handler.wfile=Mock()
        m.wait_trace.begin('/api'); m.wait_trace.command(action)
        try:
            getattr(handler, action)(b'body' if action == '_send' else 400)
            raise AssertionError('HTTP_ERROR_NOT_PROPAGATED')
        except BrokenPipeError as exc:
            assert exc is failure
        finally:
            m.wait_trace.end()
        handler.wfile.write.assert_not_called()
finally:
    t.tearDown()
'''
        with tempfile.TemporaryDirectory() as directory:
            env = dict(os.environ, GEOMETRY_WAIT_TRACE='1', GEOMETRY_FEEDBACK_DIR=directory)
            run = subprocess.run([sys.executable, '-c', script], cwd=root, env=env,
                                 capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stderr)
            rows = [json.loads(line) for line in (pathlib.Path(directory) / 'wait-trace.jsonl').read_text().splitlines()]
            writes = [r for r in rows if r['stage'] == 'http_write']
            self.assertEqual({r['command'] for r in writes}, {'_send', 'send_error'}, 'WAIT_TRACE_HTTP_HEADERS_MISSING')
            self.assertTrue(all(r['error'] == 'BrokenPipeError' for r in writes))

    def test_measurements_exclude_diagnostic_sink_time(self):
        with tempfile.TemporaryDirectory() as directory:
            m = self.load(directory, '1')
            clock, rows = [0.0], []
            def emit(stage, **fields):
                rows.append((stage, fields))
                clock[0] += 100
            def operation():
                clock[0] += 2
                return 7
            with patch.object(m, 'emit', side_effect=emit), patch.object(m.time, 'monotonic', side_effect=lambda: clock[0]):
                self.assertEqual(m.call('write', operation), 7)
                lock = m.wrap_lock(threading.Lock(), 'lock')
                with lock:
                    pass
            durations = {stage: fields['seconds'] for stage, fields in rows if 'seconds' in fields}
            self.assertEqual(durations, {'write': 2, 'lock': 0}, 'WAIT_TRACE_DIAGNOSTIC_IO_IN_WAIT')

    def test_workflow_enables_only_wsl_canvas_before_server(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        workflow = (root / '.github/workflows/integration-tests.yml').read_text()
        self.assertIn('# WSL canvas wait trace', workflow, 'WAIT_TRACE_RUNNER_GATE_MISSING')
        gate = workflow.split('# WSL canvas wait trace', 1)[1].split('python3 -u geometry-web/start_local.py', 1)[0]
        for kernel in ('6.18-linux', '6.6-microsoft-standard-WSL2'):
            for suite in ('canvas', 'grid', 'space'):
                env = dict(os.environ, GEOMETRY_BROWSER_SUITE=suite, GEOMETRY_WAIT_TRACE='1')
                script = 'uname() { printf "%s\\n" "$TEST_KERNEL"; };\n' + gate + '\nprintf "%s" "${GEOMETRY_WAIT_TRACE-unset}"'
                env['TEST_KERNEL'] = kernel
                with tempfile.TemporaryDirectory() as directory:
                    env['GITHUB_ENV'] = str(pathlib.Path(directory) / 'environment')
                    result = subprocess.run(['bash', '-c', script], env=env, capture_output=True, text=True, timeout=5)
                    exported = pathlib.Path(env['GITHUB_ENV']).read_text()
                    self.assertEqual(exported, 'GEOMETRY_WAIT_TRACE=1\n' if suite == 'canvas' and 'microsoft' in kernel else 'GEOMETRY_WAIT_TRACE=\n', 'WAIT_TRACE_ARCHIVE_EFFECTIVE_ENV')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, '1' if suite == 'canvas' and 'microsoft' in kernel else 'unset', 'WAIT_TRACE_RUNNER_SCOPE')

    def test_real_http_identical_response_and_all_stages(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        script = '''
import sys, pathlib, importlib.util, json, http.client, threading
sys.path.insert(0, str(pathlib.Path.cwd() / 'tests'))
from test_serve import BridgeServerTests
t = BridgeServerTests()
t.setUp()
m = t.server_module
server = m.PreviewHTTPServer(('127.0.0.1', 0), m.Handler)
thread = threading.Thread(target=server.serve_forever)
thread.start()
try:
    t.responses.put(b'{"ok":true,"text":"native-result"}\\n')
    data = {'cmd':'newid 1','requestId':'12345678-1234-1234-1234-123456789012','session':m.root_context.session}
    connection = http.client.HTTPConnection('127.0.0.1', server.server_port)
    connection.request('POST', '/api', json.dumps(data), {'Host':'localhost'})
    response = connection.getresponse()
    body = response.read()
    connection.close()
    receipt_data = {'receipt':data['requestId'],'requestId':'87654321-4321-4321-4321-210987654321','cmd':'ignored','session':m.root_context.session}
    connection = http.client.HTTPConnection('127.0.0.1', server.server_port)
    connection.request('POST', '/api', json.dumps(receipt_data), {'Host':'localhost'})
    receipt_response = connection.getresponse()
    receipt = json.loads(receipt_response.read())
    connection.close()
    print(json.dumps({'status':response.status,'body':body.decode(),'receipt':receipt,'stdin':m.root_context.bridge.stdin.getvalue().decode()}))
finally:
    server.shutdown(); server.server_close(); thread.join(); t.tearDown()
'''
        outputs = []
        with tempfile.TemporaryDirectory() as directory:
            for enabled in (None, '1'):
                env = dict(os.environ, GEOMETRY_FEEDBACK_DIR=directory)
                env.pop('GEOMETRY_WAIT_TRACE', None)
                if enabled:
                    env['GEOMETRY_WAIT_TRACE'] = enabled
                run = subprocess.run([sys.executable, '-c', script], cwd=root, env=env,
                                     capture_output=True, text=True, timeout=30)
                self.assertEqual(run.returncode, 0, run.stderr)
                outputs.append(json.loads(run.stdout))
                if enabled is None:
                    self.assertEqual(list(pathlib.Path(directory).iterdir()), [], 'WAIT_TRACE_DEFAULT_OFF_HTTP')
            self.assertEqual(outputs[0], outputs[1], 'WAIT_TRACE_RESPONSE_UNCHANGED')
            self.assertEqual(outputs[1]['body'], '{"ok":true,"text":"native-result"}\n')
            self.assertEqual(outputs[1]['receipt'], {'ok':True,'result':{'ok':True,'text':'native-result'}})
            self.assertEqual(outputs[1]['stdin'], 'newid 1\n', 'WAIT_TRACE_RECEIPT_MUST_NOT_REEXECUTE')
            rows = [json.loads(line) for line in (pathlib.Path(directory) / 'wait-trace.jsonl').read_text().splitlines()]
            stages = {r['stage'] for r in rows}
            self.assertTrue({'source_lock','receipt_lock','bridge_lock','stdin_write','stdin_flush','response_queue','http_write','request_end'} <= stages, stages)
            commands = [r for r in rows if r['stage'] != 'request_begin']
            self.assertEqual({r['command'] for r in commands}, {'newid 1','receipt'}, 'WAIT_TRACE_RECEIPT_COMMAND')
            self.assertTrue(all(r['businessRequestId'] == '12345678-1234-1234-1234-123456789012' for r in commands), 'WAIT_TRACE_RECEIPT_ID_PRECEDENCE')
            self.assertEqual(len({r['traceRequestId'] for r in rows}), 2)

    def load(self, directory, enabled):
        path = pathlib.Path(__file__).resolve().parents[1] / 'geometry-web/wait_trace.py'
        spec = importlib.util.spec_from_file_location('trace_test', path)
        module = importlib.util.module_from_spec(spec)
        env = {'GEOMETRY_FEEDBACK_DIR': directory}
        if enabled is not None:
            env['GEOMETRY_WAIT_TRACE'] = enabled
        with patch.dict(os.environ, env, clear=True):
            spec.loader.exec_module(module)
        return module

    def test_default_off_preserves_lock_and_output(self):
        with tempfile.TemporaryDirectory() as directory:
            for enabled in (None, '0', 'true'):
                m = self.load(directory, enabled)
                lock = threading.RLock()
                self.assertIs(m.wrap_lock(lock, 'bridge'), lock, 'WAIT_TRACE_DEFAULT_OFF')
                m.begin('/api')
                m.command('dump')
                self.assertEqual(m.call('write', lambda: b'unchanged'), b'unchanged')
                m.end()
                self.assertEqual(list(pathlib.Path(directory).iterdir()), [], 'WAIT_TRACE_DEFAULT_OFF')

    def test_enabled_records_wait_holder_reentrancy_and_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            m = self.load(directory, '1')
            lock = m.wrap_lock(threading.RLock(), 'bridge')
            held, release = threading.Event(), threading.Event()
            def holder():
                m.begin('/api')
                m.command('holder-command')
                with lock:
                    with lock:
                        held.set()
                        release.wait(2)
                m.end()
            thread = threading.Thread(target=holder)
            thread.start()
            self.assertTrue(held.wait(2))
            m.begin('/api')
            m.command('waiting-command', 'business-id')
            self.assertFalse(lock.acquire(timeout=.02))
            release.set()
            thread.join(2)
            self.assertFalse(thread.is_alive())
            with lock:
                self.assertEqual(m.call('stdin_write', lambda: 3), 3)
                with self.assertRaisesRegex(ValueError, 'original'):
                    m.call('response_queue', lambda: (_ for _ in ()).throw(ValueError('original')))
            m.end()
            rows = [json.loads(line) for line in (pathlib.Path(directory) / 'wait-trace.jsonl').read_text().splitlines()]
            wait = next(r for r in rows if r['stage'] == 'bridge' and r.get('acquired') is False)
            self.assertEqual(wait['holder']['command'], 'holder-command')
            self.assertGreaterEqual(wait['holder']['heldSeconds'], 0)
            self.assertGreaterEqual(wait['seconds'], .015)
            self.assertEqual(wait['businessRequestId'], 'business-id')
            self.assertTrue(any(r['stage'] == 'response_queue' and r['error'] == 'ValueError' for r in rows))
            self.assertTrue(any(r['stage'] == 'stdin_write' for r in rows))

    def test_outer_release_records_each_holder_before_unlock(self):
        with tempfile.TemporaryDirectory() as directory:
            m = self.load(directory, '1')
            lock = m.wrap_lock(threading.RLock(), 'bridge')
            held, waiting = threading.Event(), threading.Event()
            release_observations = []
            original_emit = m.emit
            def observe(stage, **fields):
                if stage == 'bridge_release':
                    release_observations.append((lock.owner is not None, lock.depth))
                if stage == 'bridge_begin' and fields.get('holder') and fields['holder']['command'] == 'first':
                    waiting.set()
                original_emit(stage, **fields)
            m.emit = observe
            def first():
                m.begin('/api'); m.command('first')
                with lock:
                    with lock:
                        held.set()
                        self.assertTrue(waiting.wait(2))
                m.end()
            worker = threading.Thread(target=first)
            worker.start()
            self.assertTrue(held.wait(2))
            m.begin('/api'); m.command('second')
            with lock:
                pass
            m.end()
            worker.join(2)
            self.assertFalse(worker.is_alive())
            rows = [json.loads(line) for line in (pathlib.Path(directory) / 'wait-trace.jsonl').read_text().splitlines()]
            releases = [r for r in rows if r['stage'] == 'bridge_release']
            self.assertEqual(release_observations, [(True, 1), (True, 1)], 'WAIT_TRACE_RELEASE_BEFORE_UNLOCK')
            self.assertEqual([r['holder']['command'] for r in releases], ['first', 'second'], 'WAIT_TRACE_OUTER_RELEASE')
            for row in releases:
                self.assertGreaterEqual(row['heldSeconds'], 0)
                self.assertEqual(row['holder']['traceRequestId'], row['traceRequestId'])
            self.assertIsNone(lock.owner)
            self.assertEqual(lock.depth, 0)

    def test_runner_archive_keeps_raw_trace_and_effective_environment(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            base = pathlib.Path(directory)
            feedback, output = base / 'feedback', base / 'artifact'
            feedback.mkdir()
            raw = b'{"stage":"bridge_release","heldSeconds":1}\n'
            (feedback / 'wait-trace.jsonl').write_bytes(raw)
            env = dict(os.environ, GEOMETRY_WAIT_TRACE='1', GEOMETRY_FEEDBACK_DIR=str(feedback), GEOMETRY_BROWSER_SUITE='canvas')
            run = subprocess.run([sys.executable, str(root / 'geometry-web/archive_wait_trace.py'), str(output)], env=env, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual((output / 'wait-trace.jsonl').read_bytes(), raw, 'WAIT_TRACE_ARCHIVE_RAW')
            receipt = json.loads((output / 'receipt.json').read_text())
            self.assertEqual(receipt['effectiveEnvironment']['GEOMETRY_WAIT_TRACE'], '1')
            self.assertEqual(receipt['status'], 'archived')
            self.assertEqual(receipt['records'], 1)
            (feedback / 'wait-trace.jsonl').unlink()
            run = subprocess.run([sys.executable, str(root / 'geometry-web/archive_wait_trace.py'), str(output)], env=env, capture_output=True, text=True)
            self.assertEqual(run.returncode, 1, 'WAIT_TRACE_ARCHIVE_MISSING_MUST_FAIL')
            self.assertFalse((output / 'wait-trace.jsonl').exists(), 'WAIT_TRACE_ARCHIVE_NO_STALE_FILE')
            self.assertEqual(json.loads((output / 'receipt.json').read_text())['status'], 'missing-enabled-trace')

    def test_archive_workflow_runs_even_on_failure(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        workflow = (root / '.github/workflows/integration-tests.yml').read_text()
        archive = workflow.split('      - name: Collect canvas wait trace')[1]
        collect, upload = archive.split('      - name: Preserve canvas wait trace', 1)
        self.assertIn("if: always() && matrix.suite == 'canvas'", collect, 'WAIT_TRACE_ARCHIVE_ALWAYS')
        self.assertIn('archive_wait_trace.py', collect)
        self.assertIn("if: always() && matrix.suite == 'canvas'", upload)
        self.assertIn('if-no-files-found: error', upload)

    def test_unwritable_sink_does_not_change_result(self):
        with tempfile.TemporaryDirectory() as directory:
            target = pathlib.Path(directory) / 'file'
            target.write_text('occupied')
            m = self.load(str(target), '1')
            m.begin('/api')
            self.assertEqual(m.call('http_write', lambda: 7), 7)
            m.end()


if __name__ == '__main__':
    unittest.main()
