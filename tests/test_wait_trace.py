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
import io
import ast
import queue
from unittest.mock import patch


class WaitTraceTests(unittest.TestCase):
    def test_close_drains_a_row_admitted_after_empty_observation(self):
        with tempfile.TemporaryDirectory() as directory:
            m = self.load(directory, '1')
            empty, resume = threading.Event(), threading.Event()
            get = m._writer.pending.get
            def paused_empty(*args, **kwargs):
                try: return get(*args, **kwargs)
                except queue.Empty:
                    empty.set(); resume.wait(2); raise
            m._writer.pending.get = paused_empty
            try:
                self.assertTrue(empty.wait(2))
                self.assertTrue(m._writer.submit(dict(stage='must-keep',monotonic=time.monotonic())))
                m.close(timeout=.01)
            finally:
                resume.set(); m._writer.thread.join(2)
            self.assertFalse(m._writer.thread.is_alive())
            rows = [json.loads(line) for line in (pathlib.Path(directory)/'wait-trace.jsonl').read_text().splitlines()]
            self.assertTrue(any(row['stage']=='must-keep' for row in rows), 'WAIT_TRACE_CLOSE_MUST_NOT_DISCARD_ACCEPTED_ROW')
            self.assertEqual(rows[-1]['acceptedEvents']+1, rows[-1]['writtenEvents'])

    def test_holder_age_is_sampled_after_metadata_wait(self):
        with tempfile.TemporaryDirectory() as directory:
            m = self.load(directory, '1'); lock = m.wrap_lock(threading.Lock(), 'bridge')
            clock, rows = [0.0], []
            class Metadata:
                def __enter__(self):
                    clock[0] = 2
                    lock.owner = dict(thread=-1,since=1,command='new-holder')
                def __exit__(self, *args): pass
            lock.metadata = Metadata(); lock.lock.acquire()
            m.emit = lambda stage, **fields: rows.append((stage, fields))
            try:
                with patch.object(m.time, 'monotonic', side_effect=lambda: clock[0]):
                    self.assertFalse(lock.acquire(blocking=False))
                begin = next(fields for stage,fields in rows if stage=='bridge_begin')
                self.assertEqual(begin['holder']['heldSeconds'], 1, 'WAIT_TRACE_HOLDER_AGE_MUST_USE_SNAPSHOT_TIME')
            finally:
                lock.lock.release(); m.close()

    def test_trace_sigterm_does_not_enter_business_lock_cleanup(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        source = (root / 'geometry-web/serve.py').read_text()
        function = next(node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.FunctionDef) and node.name == 'stop_traced_service')
        code = ast.get_source_segment(source, function)
        script = 'import os,signal,time,types\nwait_trace=types.SimpleNamespace(close=lambda:True)\n' + code + '\nsignal.signal(signal.SIGTERM,stop_traced_service)\nprint("READY",flush=True)\ntry:\n while True: time.sleep(1)\nfinally:\n time.sleep(2)\n'
        child = subprocess.Popen([sys.executable, '-c', script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            self.assertEqual(child.stdout.readline().strip(), 'READY')
            child.terminate()
            try:
                child.wait(timeout=.5)
                bounded = True
            except subprocess.TimeoutExpired:
                bounded = False
            self.assertTrue(bounded, 'WAIT_TRACE_SIGTERM_MUST_NOT_WAIT_FOR_BUSINESS_CLEANUP')
            self.assertEqual(child.returncode, 0)
        finally:
            if child.poll() is None: child.kill(); child.wait()
            child.stdout.close(); child.stderr.close()

    def test_slow_sink_does_not_extend_nested_business_locks(self):
        for stage in ('bridge', 'stdin_write_begin', 'receipt_release'):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as directory:
                m = self.load(directory, '1')
                receipt = m.wrap_lock(threading.Lock(), 'receipt')
                bridge = m.wrap_lock(threading.Lock(), 'bridge')
                entered, release, done = threading.Event(), threading.Event(), threading.Event()
                calls = []
                class Sink(io.StringIO):
                    def write(self, value):
                        if json.loads(value).get('stage') == stage:
                            entered.set(); release.wait(3)
                        return len(value)
                def holder():
                    m.begin('/api'); m.command('holder')
                    with receipt:
                        with bridge:
                            m.call('stdin_write', lambda: calls.append('one-command'))
                    m.end(); done.set()
                with patch.object(m.Path, 'open', side_effect=lambda *args, **kwargs: Sink()):
                    thread = threading.Thread(target=holder); thread.start()
                    try:
                        self.assertTrue(entered.wait(2))
                        self.assertTrue(done.wait(.5), 'WAIT_TRACE_SINK_MUST_NOT_EXTEND_BUSINESS_LOCKS')
                        self.assertTrue(receipt.acquire(timeout=.02))
                        receipt.release()
                        self.assertEqual(calls, ['one-command'])
                    finally:
                        release.set(); thread.join(3)
                        if hasattr(m, 'close'): m.close()

    def test_slow_sink_is_outside_acquire_timeout(self):
        with tempfile.TemporaryDirectory() as directory:
            m = self.load(directory, '1')
            lock = m.wrap_lock(threading.Lock(), 'bridge')
            sink_entered, sink_release, business_release, waiter_done = [threading.Event() for _ in range(4)]
            results = []
            class Sink(io.StringIO):
                def write(self, value):
                    if json.loads(value).get('stage') == 'bridge' and json.loads(value).get('command') == 'holder':
                        sink_entered.set(); sink_release.wait(3)
                    return len(value)
            def holder():
                m.begin('/api'); m.command('holder')
                with lock: business_release.wait(3)
                m.end()
            def waiter():
                m._local.request = dict(traceRequestId='waiter',route='/api',command='waiter',businessRequestId=None)
                acquired = lock.acquire(timeout=.02)
                results.append(acquired)
                if acquired: lock.release()
                waiter_done.set()
            with patch.object(m.Path, 'open', side_effect=lambda *args, **kwargs: Sink()):
                first = threading.Thread(target=holder); first.start()
                second = None
                try:
                    self.assertTrue(sink_entered.wait(2))
                    second = threading.Thread(target=waiter); second.start()
                    self.assertTrue(waiter_done.wait(.5), 'WAIT_TRACE_TIMEOUT_MUST_NOT_WAIT_FOR_SINK')
                    self.assertEqual(results, [False])
                finally:
                    sink_release.set(); business_release.set(); first.join(3)
                    if second: second.join(3)
                    if hasattr(m, 'close'): m.close()

    def test_release_snapshot_uses_actual_unlock_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            m = self.load(directory, '1'); lock = m.wrap_lock(threading.Lock(), 'bridge')
            clock, rows = [0.0], []
            def emit(stage, **fields):
                if stage == 'bridge_release':
                    self.assertFalse(lock.lock.locked(), 'WAIT_TRACE_RELEASE_IO_AFTER_UNLOCK')
                    self.assertFalse(lock.metadata.locked(), 'WAIT_TRACE_RELEASE_IO_AFTER_METADATA')
                    rows.append(fields); clock[0] += 100
            m.emit = emit; m.begin('/api'); m.command('holder')
            with patch.object(m.time, 'monotonic', side_effect=lambda: clock[0]):
                lock.acquire(); clock[0] = 2; lock.release()
            self.assertEqual(rows[0]['heldSeconds'], 2)
            self.assertEqual(rows[0]['releasedMonotonic'], 2)
            if hasattr(m, 'close'): m.close()

    def test_bounded_writer_reports_loss_without_replaying_operation(self):
        with tempfile.TemporaryDirectory() as directory:
            m = self.load(directory, '1')
            self.assertTrue(hasattr(m, 'Writer'), 'WAIT_TRACE_MISSING_BOUNDED_WRITER')
            m.close()
            (pathlib.Path(directory) / 'wait-trace.jsonl').unlink(missing_ok=True)
            m._writer = m.Writer(directory, capacity=1, run_id='bounded-test')
            entered, release = threading.Event(), threading.Event()
            write = m._writer.write
            def slow(row):
                if row.get('stage') == 'block': entered.set(); release.wait(3)
                return write(row)
            m._writer.write = slow
            m._local.request = dict(traceRequestId='one',route='/api',command='one',businessRequestId=None)
            m.emit('block'); self.assertTrue(entered.wait(2))
            try:
                m.emit('queued'); m.emit('dropped')
                calls=[]; value=object()
                self.assertIs(m.call('operation',lambda: calls.append('one') or value),value)
                failure=ValueError('original')
                with self.assertRaises(ValueError) as caught:
                    m.call('failure',lambda: (_ for _ in ()).throw(failure))
                self.assertIs(caught.exception,failure)
                self.assertEqual(calls,['one'])
            finally:
                release.set(); m.close()
            rows=[json.loads(line) for line in (pathlib.Path(directory)/'wait-trace.jsonl').read_text().splitlines()]
            complete=next(row for row in rows if row['stage']=='trace_complete')
            self.assertTrue(complete['incomplete'], 'WAIT_TRACE_LOSS_MUST_BE_EXPLICIT')
            self.assertGreater(complete['droppedEvents'],0)

    def test_two_runs_remove_only_old_trace_and_archive_current_run(self):
        root=pathlib.Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            feedback=pathlib.Path(directory)/'feedback'; feedback.mkdir()
            (feedback/'keep-user-report.txt').write_text('preserve')
            (feedback/'wait-trace.jsonl').write_text('{"stage":"trace_start","traceRunId":"old-run"}\n{"stage":"trace_complete","traceRunId":"old-run","incomplete":false}\n')
            env=dict(os.environ,GEOMETRY_FEEDBACK_DIR=str(feedback),GEOMETRY_WAIT_TRACE='1',GEOMETRY_BROWSER_SUITE='canvas')
            runs=[]
            for index in range(2):
                preparation=subprocess.run([sys.executable,'geometry-web/prepare_wait_trace.py'],cwd=root,env=env,capture_output=True,text=True)
                self.assertEqual(preparation.returncode,0,'WAIT_TRACE_MISSING_RUN_PREPARATION')
                self.assertFalse((feedback/'wait-trace.jsonl').exists(), 'WAIT_TRACE_STALE_SOURCE_MUST_BE_REMOVED_BEFORE_SERVICE')
                run_id=preparation.stdout.strip(); runs.append(run_id)
                env['GEOMETRY_WAIT_TRACE_RUN_ID']=run_id
                script='import sys; sys.path.insert(0,"geometry-web"); import wait_trace as m; m.begin("/api"); m.command("one"); m.end(); assert m.close()'
                result=subprocess.run([sys.executable,'-c',script],cwd=root,env=env,capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)
                output=pathlib.Path(directory)/('artifact'+str(index))
                archived=subprocess.run([sys.executable,'geometry-web/archive_wait_trace.py',str(output)],cwd=root,env=env,capture_output=True,text=True)
                self.assertEqual(archived.returncode,0,archived.stdout+archived.stderr)
                rows=[json.loads(line) for line in (output/'wait-trace.jsonl').read_text().splitlines()]
                self.assertTrue(all(row.get('traceRunId')==run_id for row in rows),'WAIT_TRACE_ARCHIVE_MUST_NOT_MIX_RUNS')
                self.assertEqual((feedback/'keep-user-report.txt').read_text(),'preserve')
            self.assertNotEqual(runs[0],runs[1])

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
    m.wait_trace.close(); t.tearDown()
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
            self.assertTrue(m.close())

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
                    env['GEOMETRY_FEEDBACK_DIR'] = str(pathlib.Path(directory) / 'feedback')
                    result = subprocess.run(['bash', '-c', script], cwd=root, env=env, capture_output=True, text=True, timeout=5)
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
    server.shutdown(); server.server_close(); thread.join(); m.wait_trace.close(); t.tearDown()
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
            commands = [r for r in rows if 'traceRequestId' in r and r['stage'] != 'request_begin']
            self.assertEqual({r['command'] for r in commands}, {'newid 1','receipt'}, 'WAIT_TRACE_RECEIPT_COMMAND')
            self.assertTrue(all(r['businessRequestId'] == '12345678-1234-1234-1234-123456789012' for r in commands), 'WAIT_TRACE_RECEIPT_ID_PRECEDENCE')
            self.assertEqual(len({r['traceRequestId'] for r in rows if 'traceRequestId' in r}), 2)

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
                with patch.object(m.time, 'monotonic', side_effect=AssertionError('OFF_CLOCK')), patch.object(m.uuid, 'uuid4', side_effect=AssertionError('OFF_UUID')), patch.object(m.Path, 'mkdir', side_effect=AssertionError('OFF_PATH')):
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
            self.assertTrue(m.close())
            rows = [json.loads(line) for line in (pathlib.Path(directory) / 'wait-trace.jsonl').read_text().splitlines()]
            wait = next(r for r in rows if r['stage'] == 'bridge' and r.get('acquired') is False)
            self.assertEqual(wait['holder']['command'], 'holder-command')
            self.assertGreaterEqual(wait['holder']['heldSeconds'], 0)
            self.assertGreaterEqual(wait['seconds'], .015)
            self.assertEqual(wait['businessRequestId'], 'business-id')
            self.assertTrue(any(r['stage'] == 'response_queue' and r['error'] == 'ValueError' for r in rows))
            self.assertTrue(any(r['stage'] == 'stdin_write' for r in rows))

    def test_outer_release_records_snapshot_after_both_unlocks(self):
        with tempfile.TemporaryDirectory() as directory:
            m = self.load(directory, '1')
            lock = m.wrap_lock(threading.RLock(), 'bridge')
            held, waiting = threading.Event(), threading.Event()
            release_observations = []
            original_emit = m.emit
            def observe(stage, **fields):
                if stage == 'bridge_release':
                    release_observations.append(fields['holder']['command'])
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
            self.assertTrue(m.close())
            rows = [json.loads(line) for line in (pathlib.Path(directory) / 'wait-trace.jsonl').read_text().splitlines()]
            releases = sorted([r for r in rows if r['stage'] == 'bridge_release'], key=lambda r:r['releasedMonotonic'])
            self.assertCountEqual(release_observations, ['first','second'], 'WAIT_TRACE_RELEASE_SNAPSHOTS_PRESERVED')
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
            raw = b'{"stage":"trace_start","traceRunId":"fixture"}\n{"stage":"trace_complete","traceRunId":"fixture","incomplete":false}\n'
            (feedback / 'wait-trace.jsonl').write_bytes(raw)
            env = dict(os.environ, GEOMETRY_WAIT_TRACE='1', GEOMETRY_FEEDBACK_DIR=str(feedback), GEOMETRY_BROWSER_SUITE='canvas', GEOMETRY_WAIT_TRACE_RUN_ID='fixture')
            run = subprocess.run([sys.executable, str(root / 'geometry-web/archive_wait_trace.py'), str(output)], env=env, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual((output / 'wait-trace.jsonl').read_bytes(), raw, 'WAIT_TRACE_ARCHIVE_RAW')
            receipt = json.loads((output / 'receipt.json').read_text())
            self.assertEqual(receipt['effectiveEnvironment']['GEOMETRY_WAIT_TRACE'], '1')
            self.assertEqual(receipt['status'], 'archived')
            self.assertEqual(receipt['records'], 2)
            for bad in (raw.replace(b'fixture', b'older', 1), raw.replace(b'false', b'true'), raw.splitlines()[0]+b'\n'):
                (feedback / 'wait-trace.jsonl').write_bytes(bad)
                rejected = subprocess.run([sys.executable, str(root / 'geometry-web/archive_wait_trace.py'), str(output)], env=env, capture_output=True, text=True)
                self.assertEqual(rejected.returncode, 1, 'WAIT_TRACE_MIXED_OR_INCOMPLETE_MUST_FAIL')
                self.assertEqual(json.loads((output / 'receipt.json').read_text())['status'], 'incomplete-or-mixed-trace')
                self.assertEqual((output / 'wait-trace.jsonl').read_bytes(), bad)
            (feedback / 'wait-trace.jsonl').unlink()
            run = subprocess.run([sys.executable, str(root / 'geometry-web/archive_wait_trace.py'), str(output)], env=env, capture_output=True, text=True)
            self.assertEqual(run.returncode, 1, 'WAIT_TRACE_ARCHIVE_MISSING_MUST_FAIL')
            self.assertFalse((output / 'wait-trace.jsonl').exists(), 'WAIT_TRACE_ARCHIVE_NO_STALE_FILE')
            self.assertEqual(json.loads((output / 'receipt.json').read_text())['status'], 'missing-enabled-trace')

    def test_archive_cleanup_preserves_failed_job_status(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        workflow = (root / '.github/workflows/integration-tests.yml').read_text()
        cleanup = 'cleanup() {' + workflow.split('cleanup() {', 1)[1].split('          for attempt', 1)[0]
        with tempfile.TemporaryDirectory() as directory:
            output = pathlib.Path(directory) / 'artifact'
            script = 'set -e\nkill() { :; }; server=unused\n' + cleanup.replace('/tmp/geometry-wait-trace-artifact', str(output)) + '\nexit 7\n'
            env = dict(os.environ, GEOMETRY_BROWSER_SUITE='canvas', GEOMETRY_WAIT_TRACE='1', GEOMETRY_FEEDBACK_DIR=directory)
            run = subprocess.run(['bash', '-c', script], cwd=root, env=env, capture_output=True, text=True)
            self.assertEqual(run.returncode, 7, 'WAIT_TRACE_ARCHIVE_MUST_KEEP_ORIGINAL_FAILURE')
            self.assertEqual(json.loads((output / 'receipt.json').read_text())['status'], 'missing-enabled-trace')

    def test_archive_workflow_runs_even_on_failure(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        workflow = (root / '.github/workflows/integration-tests.yml').read_text()
        collect, upload = workflow.split('      - name: Preserve canvas wait trace', 1)
        self.assertIn('trap cleanup EXIT', collect, 'WAIT_TRACE_ARCHIVE_ALWAYS')
        self.assertIn('python3 geometry-web/archive_wait_trace.py /tmp/geometry-wait-trace-artifact', collect)
        self.assertIn('exit "$original_status"', collect)
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
            self.assertFalse(m.close(), 'WAIT_TRACE_SINK_FAILURE_MUST_BE_RECORDED')


if __name__ == '__main__':
    unittest.main()
