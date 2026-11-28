"""PF6 App HTTP protocol. Real handler/receipts; native geometry is separate.

The last test starts an owned HTTP service and the actual bridge. Mocked handler
tests are labelled protocol tests, never browser or native geometry evidence.
"""
import base64
from contextlib import contextmanager
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import signal
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'geometry-web'))
import test_serve as existing
import runtime_version
from tests import test_panel_fill_builder as native
from tests import test_panel_fill_layout as pf2
from tests import pf6_app_oracle as oracle


def suggest(revision='7'):
    return {'schema': 'panel-fill-builder-suggest/1', 'expectedRevision': revision,
            'input': native.builder_input(), 'pre': [], 'post': []}


def select(revision='7'):
    return {'schema': 'panel-fill-builder-select/1', 'expectedRevision': revision,
            'setKey': 'a' * 64, 'generation': '1', 'selected': []}


class PF6HTTPProtocol(unittest.TestCase):
    tearDown = existing.BridgeServerTests.tearDown

    def setUp(self):
        # Protocol-only fixture: avoid racing source edits during a unit test.
        # PF6HTTPNative below independently asserts the real runtime is fresh.
        runtime = SimpleNamespace(version='pf6-protocol-fixture', fresh=lambda: True, static={})
        with patch.object(runtime_version, 'RuntimeSnapshot', return_value=runtime):
            existing.BridgeServerTests.setUp(self)

    def dispatch(self, mode='suggest', value=None, *, headers=None, raw=None,
                 request_id=None, defaults=True, route=None):
        body = raw if raw is not None else json.dumps(value if value is not None else suggest()).encode()
        h = object.__new__(self.server_module.Handler)
        h.path = route or '/panel-fill/builder/' + mode
        h.headers = {'Content-Length': str(len(body))}
        if defaults:
            h.headers.update({'X-Geometry-Version': self.server_module.RUNTIME.version,
                              'X-Geometry-Session': self.server_module.root_context.session,
                              'X-Geometry-Request-Id': request_id or str(uuid.uuid4())})
        h.headers.update(headers or {})
        h.rfile = io.BytesIO(body)
        h._local_only = lambda: False
        h._send = Mock()
        h.send_error = Mock()
        calls, paths = [], []

        def ask(command):
            calls.append(command)
            if h.path.startswith('/panel-fill/builder/') and command.startswith(('pf6-suggest ', 'pf6-select ')):
                path = Path(command.split(' ', 1)[1])
                paths.append(path)
                payload = path.read_bytes()
                self.assertEqual(payload, body, 'PF6_HTTP_PRIVATE_EXACT_BYTES')
            return b'{"ok":true,"protocolFixture":true}'

        with patch.object(self.server_module.RUNTIME, 'fresh', return_value=True), \
                patch.object(self.server_module, 'ask_bridge', side_effect=ask):
            h.do_POST()
        self.assertTrue(h._send.called, 'PF6_HTTP_ENTRY: controlled endpoint must return JSON, not 404')
        result = json.loads(h._send.call_args.args[0])
        self.assertTrue(all(not p.exists() for p in paths), 'PF6_HTTP_PRIVATE_FILES_REMOVED')
        return result, calls, h

    def test_exact_protocol_has_server_owned_files_and_receipt(self):
        for mode, body in [('suggest', suggest()), ('select', select())]:
            with self.subTest(mode=mode):
                rid = str(uuid.uuid4())
                result, calls, _ = self.dispatch(mode, body, request_id=rid)
                self.assertTrue(result['ok'], 'PF6_HTTP_ENTRY')
                self.assertEqual(len(calls), 1)
                cached = self.server_module.root_context.api_receipts[rid]
                raw = json.dumps(body).encode()
                self.assertEqual(cached[0], 'pf6-' + mode + ':' + hashlib.sha256(raw).hexdigest())

    def test_all_three_headers_are_required_before_native(self):
        all_headers = {'X-Geometry-Version': self.server_module.RUNTIME.version,
                       'X-Geometry-Session': self.server_module.root_context.session,
                       'X-Geometry-Request-Id': str(uuid.uuid4())}
        for mode, value in [('suggest', suggest()), ('select', select())]:
            for key in all_headers:
                with self.subTest(mode=mode, missing=key):
                    result, calls, _ = self.dispatch(mode, value,
                        headers={k: v for k, v in all_headers.items() if k != key}, defaults=False)
                    self.assertFalse(result['ok'], 'PF6_HTTP_REQUIRED_HEADERS')
                    self.assertEqual(calls, [], 'PF6_HTTP_REQUIRED_HEADERS')

    def test_replay_binds_raw_body_and_never_executes_twice(self):
        rid = str(uuid.uuid4())
        first, calls, _ = self.dispatch(request_id=rid)
        replay, repeated, _ = self.dispatch(request_id=rid)
        self.assertEqual(first, replay)
        self.assertEqual(len(calls), 1)
        self.assertEqual(repeated, [], 'PF6_HTTP_EXACT_REPLAY')
        changed = suggest(); changed['input']['A']['value'] = 28
        conflict, calls, _ = self.dispatch(value=changed, request_id=rid)
        self.assertFalse(conflict['ok'], 'PF6_HTTP_BODY_BOUND_ID')
        self.assertEqual(calls, [])

    def test_early_receipt_seals_id_and_ack_cannot_unseal_it(self):
        rid = str(uuid.uuid4())
        lookup = {'receipt': rid, 'session': self.server_module.root_context.session}
        sealed = json.loads(self.server_module.recorded_api(lookup))
        self.assertTrue(sealed['ok']); self.assertFalse(sealed['result']['ok'])
        late, calls, _ = self.dispatch(request_id=rid)
        self.assertFalse(late['ok']); self.assertEqual(calls, [], 'PF6_HTTP_LATE_SEALED_NEVER_EXECUTES')
        self.dispatch(headers={'X-Geometry-Ack': json.dumps([rid])})
        self.assertIn(rid, self.server_module.root_context.api_sealed, 'PF6_HTTP_ACK_CANNOT_UNSEAL')

    def test_ack_is_bounded_unique_and_excludes_current_request(self):
        rid = str(uuid.uuid4())
        invalid = ['[', '{}', json.dumps([rid]), json.dumps(['not-a-uuid']),
                   json.dumps(['1' * 36]), json.dumps([str(uuid.uuid4())] * 2),
                   json.dumps([str(uuid.uuid4()) for _ in range(257)])]
        for raw in invalid:
            with self.subTest(raw=raw[:50]):
                result, calls, _ = self.dispatch(request_id=rid, headers={'X-Geometry-Ack': raw})
                self.assertFalse(result['ok'], 'PF6_HTTP_ACK_EXACT')
                self.assertEqual(calls, [], 'PF6_HTTP_ACK_EXACT')
        done = str(uuid.uuid4()); self.dispatch(request_id=done)
        self.dispatch(headers={'X-Geometry-Ack': json.dumps([done])})
        self.assertNotIn(done, self.server_module.root_context.api_receipts, 'PF6_HTTP_ACK_RELEASES_COMPLETED')

    def test_invalid_schema_and_outer_dsl_are_rejected_before_file_execution(self):
        requests = []
        for change in [{'pre': [{'op': 'create-timber'}]}, {'post': [{}]},
                       {'expectedRevision': 7}, {'expectedRevision': '07'},
                       {'expectedRevision': '18446744073709551616'}, {'extra': True}]:
            requests.append({**suggest(), **change})
        for value in requests:
            with self.subTest(value=value):
                result, calls, _ = self.dispatch(value=value)
                self.assertFalse(result['ok'], 'PF6_HTTP_CLOSED_APP_SCHEMA')
                self.assertEqual(calls, [])
        for body in [b'{"schema":"x","schema":"y"}', b'{"a":NaN}', b'\xff']:
            result, calls, _ = self.dispatch(raw=body)
            self.assertFalse(result['ok'], 'PF6_HTTP_STRICT_JSON'); self.assertEqual(calls, [])

    def test_exact_uint64_text_and_empty_selection_are_preserved(self):
        for mode, value in [('suggest', suggest('18446744073709551615')),
                            ('select', select('18446744073709551615'))]:
            result, calls, _ = self.dispatch(mode, value)
            self.assertTrue(result['ok'], 'PF6_HTTP_EXACT_UINT64')
            self.assertEqual(len(calls), 1)

    def test_parameter_zero_ids_reach_native_without_changing_the_source(self):
        value = suggest()
        value['input']['A'] = {'kind': 'parameter', 'parameterId': 0, 'fieldId': 0}
        result, calls, _ = self.dispatch(value=value)
        self.assertTrue(result['ok'], 'PF6_HTTP_PARAMETER_ZERO_IS_VALID')
        self.assertEqual(len(calls), 1, 'PF6_HTTP_PARAMETER_ZERO_IS_VALID')
        for field in ['parameterId', 'fieldId']:
            for bad in [-1, 4294967296, True, '0']:
                with self.subTest(field=field, bad=bad):
                    invalid = copy.deepcopy(value); invalid['input']['A'][field] = bad
                    result, calls, _ = self.dispatch(value=invalid)
                    self.assertFalse(result['ok'], 'PF6_HTTP_PARAMETER_STAYS_UINT32')
                    self.assertEqual(calls, [])

    def test_file_commands_are_not_a_public_api_backdoor(self):
        for cmd in ['pf6-suggest /tmp/client.json', 'pf6-select /tmp/client.json']:
            result, calls, _ = self.dispatch(value={'cmd': cmd}, route='/api')
            self.assertFalse(result['ok'], 'PF6_HTTP_NO_CLIENT_PATH')
            self.assertEqual(calls, [], 'PF6_HTTP_NO_CLIENT_PATH')

    def test_terminals_require_exact_receipted_positive_uint32(self):
        for verb in ['confirm', 'cancel']:
            for token in ['0', '-1', '4294967296', '01', '+1', '1.0', '', ' 1', '1 ']:
                value = {'cmd': 'pf6-' + verb + ' ' + token, 'requestId': str(uuid.uuid4()),
                         'session': self.server_module.root_context.session}
                with self.subTest(verb=verb, invalidToken=token):
                    result, calls, _ = self.dispatch(value=value, route='/api')
                    self.assertFalse(result['ok'], 'PF6_HTTP_TOKEN_POSITIVE_UINT32')
                    self.assertEqual(calls, [], 'PF6_HTTP_TOKEN_POSITIVE_UINT32')
            for token in ['1', '4294967295']:
                value = {'cmd': 'pf6-' + verb + ' ' + token, 'requestId': str(uuid.uuid4()),
                         'session': self.server_module.root_context.session}
                result, calls, _ = self.dispatch(value=value, route='/api')
                self.assertTrue(result['ok'], 'PF6_HTTP_POSITIVE_TOKEN_ENDPOINTS')
                self.assertEqual(calls, [value['cmd']], 'PF6_HTTP_POSITIVE_TOKEN_ENDPOINTS')

    def test_terminals_require_version_session_and_request_id_before_native(self):
        for verb in ['confirm', 'cancel']:
            body = {'cmd': 'pf6-' + verb + ' 1', 'requestId': str(uuid.uuid4()),
                    'session': self.server_module.root_context.session}
            for missing in ['version', 'session', 'requestId']:
                with self.subTest(verb=verb, missing=missing):
                    value = {key: item for key, item in body.items() if key != missing}
                    headers = {} if missing == 'version' else {'X-Geometry-Version': self.server_module.RUNTIME.version}
                    result, calls, _ = self.dispatch(value=value, headers=headers, defaults=False, route='/api')
                    self.assertFalse(result['ok'], 'PF6_HTTP_TERMINAL_RECEIPT_REQUIRED')
                    self.assertEqual(calls, [], 'PF6_HTTP_TERMINAL_RECEIPT_REQUIRED')

    def check_windows_file_command(self, verb, marker):
        # Exercise the real ask_bridge writer, not a copied conversion function.
        # The native process is a protocol fixture; this is not Windows execution.
        for wsl, filename, expected in [
                (True, r'C:\Users\builder\角材 candidate.json', '/mnt/c/Users/builder/角材 candidate.json'),
                (True, 'D:/work/selected.json', '/mnt/d/work/selected.json'),
                (True, '/tmp/pf6.json', '/tmp/pf6.json'),
                (False, r'C:\work\pf6.json', r'C:\work\pf6.json')]:
            with self.subTest(verb=verb, wsl=wsl, filename=filename):
                self.server_module.BRIDGE_WSL = wsl
                self.process.stdin.seek(0); self.process.stdin.truncate()
                self.responses.put(b'{"ok":true,"pathFixture":true}\n')
                reply = self.server_module.ask_bridge(verb + ' ' + filename)
                self.assertEqual(json.loads(reply), {'ok': True, 'pathFixture': True}, marker)
                self.assertEqual(self.process.stdin.getvalue(), (verb + ' ' + expected + '\n').encode(), marker)

    def test_suggest_windows_wsl_path_reaches_bridge_as_posix(self):
        self.check_windows_file_command('pf6-suggest', 'PF6_HTTP_WSL_SUGGEST_PATH')

    def test_select_windows_wsl_path_reaches_bridge_as_posix(self):
        self.check_windows_file_command('pf6-select', 'PF6_HTTP_WSL_SELECT_PATH')

    def test_byte_limit_is_not_larger_than_existing_bounded_transport(self):
        for route in ['/panel-fill/builder/suggest', '/panel-fill/builder/select']:
            self.assertEqual(self.server_module.POST_MAX_BYTES.get(route), 1024 * 1024,
                             'PF6_HTTP_1MIB_LIMIT')
        self.assertEqual(self.server_module.MAX_RECEIPTS, 256)
        self.assertEqual(self.server_module.BRIDGE_TIMEOUT, .1)  # Existing fixture's bound.


class PF6HTTPNative(unittest.TestCase):
    @contextmanager
    def service(self, directory, label, receipts, lifecycle):
        """An owned service process and native child, never a reset of the old one."""
        executable = os.environ.get('GEOMETRY_TEST_BRIDGE')
        if not executable:
            self.skipTest('actual native bridge required; use --needs bridge')
        if os.name != 'nt':
            import resource
            soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
            resource.setrlimit(resource.RLIMIT_STACK, (max(soft, 16 * 1024 * 1024), hard))
        with socket.socket() as reserve:
            reserve.bind(('127.0.0.1', 0)); port = reserve.getsockname()[1]
        env = dict(os.environ, GEOMETRY_BRIDGE_EXECUTABLE=executable,
                   GEOMETRY_FEEDBACK_DIR=str(directory / (label + '-feedback')))
        stdout_path, stderr_path = directory / (label + '.stdout'), directory / (label + '.stderr')
        with stdout_path.open('wb') as stdout, stderr_path.open('wb') as stderr:
            process = subprocess.Popen([sys.executable, str(ROOT / 'geometry-web/serve.py'), str(port)],
                                       env=env, stdout=stdout, stderr=stderr, start_new_session=os.name != 'nt')
            runtime = None
            try:
                url = f'http://127.0.0.1:{port}'
                deadline = time.monotonic() + 15
                while True:
                    try:
                        with urlopen(url + '/runtime', timeout=1) as reply:
                            runtime = json.load(reply)
                        break
                    except (OSError, URLError):
                        if process.poll() is not None or time.monotonic() >= deadline:
                            self.fail('PF6_HTTP_COLD_START: ' + stderr_path.read_text())
                        time.sleep(.05)
                self.assertEqual(process.pid, runtime['pid'], 'PF6_HTTP_COLD_OWNED_SERVICE')
                self.assertTrue(runtime['fresh'], 'PF6_HTTP_COLD_FRESH_SOURCE')

                def post(route, value=None, *, headers=None, raw=None, with_version=True):
                    body = raw if raw is not None else json.dumps(value, ensure_ascii=False).encode()
                    sent_headers = {'Content-Type': 'application/json'}
                    if with_version:
                        sent_headers['X-Geometry-Version'] = runtime['version']
                    sent_headers.update(headers or {})
                    request = Request(url + route, body, sent_headers)
                    try:
                        with urlopen(request, timeout=15) as reply:
                            status, returned_headers, received = reply.status, dict(reply.headers), reply.read()
                    except HTTPError as error:
                        status, returned_headers, received = error.code, dict(error.headers), error.read()
                    receipts.append({'service': label, 'pid': process.pid, 'session': runtime['session'],
                                     'route': route, 'headers': sent_headers, 'requestRawUtf8': body.decode(),
                                     'status': status, 'responseHeaders': returned_headers,
                                     'replyRawUtf8': received.decode()})
                    self.assertIn(status, (200, 409), 'PF6_HTTP_COLD_CONTROLLED_ROUTE')
                    self.assertEqual(runtime['session'], returned_headers.get('X-Geometry-Session'),
                                     'PF6_HTTP_COLD_RESPONSE_SESSION')
                    return json.loads(received)

                def command(cmd, **fields):
                    return post('/api', {'cmd': cmd, **fields})

                def packet(mode, value, request_id=None):
                    return post('/panel-fill/builder/' + mode, value,
                                headers={'X-Geometry-Session': runtime['session'],
                                         'X-Geometry-Request-Id': request_id or str(uuid.uuid4())})

                yield SimpleNamespace(runtime=runtime, process=process, post=post,
                                      command=command, packet=packet)
            finally:
                children = []
                children_path = Path('/proc') / str(process.pid) / 'task' / str(process.pid) / 'children'
                if children_path.is_file():
                    children = [int(pid) for pid in children_path.read_text().split()]
                if process.poll() is None:
                    process.send_signal(signal.SIGINT) if os.name != 'nt' else process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    if os.name != 'nt':
                        os.killpg(process.pid, signal.SIGKILL)
                    else:
                        process.kill()
                    process.wait(timeout=2)
                    self.fail('PF6_HTTP_COLD_STOP: owned service did not stop within the existing bound')
                group_stopped = None
                if os.name != 'nt':
                    try:
                        os.killpg(process.pid, 0)
                        group_stopped = False
                    except ProcessLookupError:
                        group_stopped = True
                lifecycle.append({'service': label, 'pid': process.pid, 'runtime': runtime,
                                  'returncode': process.returncode, 'nativeChildPids': children,
                                  'nativeChildrenStopped': all(not (Path('/proc') / str(pid)).exists() for pid in children) if children else None,
                                  'ownedProcessGroupStopped': group_stopped})
                if children:
                    self.assertTrue(lifecycle[-1]['nativeChildrenStopped'], 'PF6_HTTP_COLD_NATIVE_STOPPED')
                if group_stopped is not None:
                    if not group_stopped:
                        os.killpg(process.pid, signal.SIGKILL)
                    self.assertTrue(group_stopped, 'PF6_HTTP_COLD_OWNED_GROUP_STOPPED')

    def test_real_http_native_cancel_confirm_undo_redo_and_receipts(self):
        executable = os.environ.get('GEOMETRY_TEST_BRIDGE')
        if not executable:
            self.skipTest('actual native bridge required; use --needs bridge')
        if os.name != 'nt':
            import resource
            soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
            resource.setrlimit(resource.RLIMIT_STACK, (max(soft, 16 * 1024 * 1024), hard))
        with tempfile.TemporaryDirectory(prefix='pf6-app-http-') as directory:
            directory = Path(directory)
            with socket.socket() as reserve:
                reserve.bind(('127.0.0.1', 0)); port = reserve.getsockname()[1]
            env = dict(os.environ, GEOMETRY_BRIDGE_EXECUTABLE=executable,
                       GEOMETRY_FEEDBACK_DIR=str(directory / 'feedback'))
            receipts, log_path = [], directory / 'serve.log'
            with log_path.open('wb') as log:
                proc = subprocess.Popen([sys.executable, str(ROOT / 'geometry-web/serve.py'), str(port)],
                                        env=env, stdout=log, stderr=log)
                try:
                    url = f'http://127.0.0.1:{port}'
                    deadline = time.monotonic() + 15
                    while True:
                        try:
                            with urlopen(url + '/runtime', timeout=1) as reply: runtime = json.load(reply)
                            break
                        except (OSError, URLError):
                            if proc.poll() is not None or time.monotonic() >= deadline:
                                self.fail('PF6_HTTP_START: ' + log_path.read_text())
                            time.sleep(.05)
                    self.assertTrue(runtime['fresh'], 'PF6_HTTP_FRESH_BINARY')

                    def post(route, value, headers=None):
                        req = Request(url + route, json.dumps(value).encode(),
                                      {'Content-Type': 'application/json', 'X-Geometry-Version': runtime['version'], **(headers or {})})
                        try:
                            with urlopen(req, timeout=15) as reply: result = json.load(reply)
                        except HTTPError as error:
                            self.fail('PF6_HTTP_ENTRY: HTTP ' + str(error.code) + ' at ' + route)
                        receipts.append({'route': route, 'request': value, 'headers': headers or {}, 'reply': result})
                        return result

                    def command(cmd, **fields): return post('/api', {'cmd': cmd, **fields})
                    def terminal(cmd): return command(cmd, requestId=str(uuid.uuid4()), session=runtime['session'])
                    def packet(mode, body, rid=None):
                        return post('/panel-fill/builder/' + mode, body,
                                    {'X-Geometry-Session': runtime['session'], 'X-Geometry-Request-Id': rid or str(uuid.uuid4())})
                    self.assertTrue(command('reset')['ok'])
                    self.assertTrue(command('line boundary 8 outline 0,0 300,0 300,300 0,300 kind room_plan')['ok'])
                    e = command('engineering-read')
                    preview = post('/engineering/preview', {'schema': 'engineering-transaction/1', 'expectedRevision': e['revision'],
                        'operations': [{'op': 'publish-material', 'value': {'id': 'pf-board', 'version': 1, 'name': '板', 'kind': 'panel', 'width': 100, 'length': 100, 'thickness': '9'}},
                                       {'op': 'put-parameter', 'value': {'id': 90, 'name': '門檻', 'fields': [{'id': 1, 'name': 'X', 'type': 'dimension', 'input': '8'}]}}]})
                    self.assertTrue(preview['ok'] and preview['preview']['valid'], preview)
                    self.assertTrue(command('engineering-confirm ' + str(preview['preview']['token']))['ok'])
                    r = command('panel-fill-read')
                    preview = post('/panel-fill/preview', {'schema': 'panel-fill-transaction/1', 'expectedRevision': r['revision'],
                        'operations': [pf2.put(pf2.surface(boundary=8, origin=(0, 0, 0), obstacles=[])), pf2.fill()]})
                    self.assertTrue(preview['ok'] and preview['preview']['valid'], preview)
                    self.assertTrue(command('panel-fill-confirm ' + str(preview['preview']['token']))['ok'])
                    before, identity = command('dump')['text'], command('identity-read')
                    request = suggest(str(command('panel-fill-read')['revision']))
                    rid = str(uuid.uuid4()); proposal = packet('suggest', request, rid)
                    self.assertTrue(proposal.get('ok') and proposal.get('valid'), 'PF6_HTTP_NATIVE_SUGGEST')
                    self.assertEqual(proposal, packet('suggest', request, rid), 'PF6_HTTP_NATIVE_REPLAY')
                    self.assertEqual(proposal, command('', receipt=rid, session=runtime['session'])['result'])
                    body = {'schema': 'panel-fill-builder-select/1', 'expectedRevision': proposal['revision'],
                            'generation': proposal['generation'], 'setKey': proposal['setKey'],
                            'selected': [r['key'] for r in proposal['entries'] if r['selectable'] and r['valid']]}
                    selected = packet('select', body)['preview']
                    self.assertTrue(selected['valid'], selected)
                    self.assertEqual(before, command('dump')['text'], 'PF6_HTTP_PREVIEW_ZERO_WRITE')
                    self.assertTrue(terminal('pf6-cancel ' + str(selected['token']))['ok'])
                    self.assertEqual(before, command('dump')['text'], 'PF6_HTTP_CANCEL_ZERO_WRITE')
                    self.assertEqual(identity, command('identity-read'), 'PF6_HTTP_CANCEL_IDENTITY_UNCHANGED')
                    selected = packet('select', body)['preview']
                    commit_id, commit_cmd = str(uuid.uuid4()), 'pf6-confirm ' + str(selected['token'])
                    result = command(commit_cmd, requestId=commit_id, session=runtime['session'])
                    self.assertTrue(result['ok'] and result['history_changed'], result)
                    self.assertEqual(result, command(commit_cmd, requestId=commit_id, session=runtime['session']))
                    after = command('dump')['text']
                    self.assertEqual(sum(line.startswith('timber ') for line in after.splitlines()), 12)
                    self.assertTrue(command('line undo')['ok'])
                    self.assertEqual(before, command('dump')['text'], 'PF6_HTTP_ONE_HISTORY')
                    self.assertTrue(command('line redo')['ok'])
                    self.assertEqual(after, command('dump')['text'], 'PF6_HTTP_REDO_WHOLE_GROUP')
                finally:
                    proc.terminate(); proc.wait(timeout=10)
                    output = os.environ.get('GEOMETRY_PF6_HTTP_RECEIPTS')
                    if output:
                        target = Path(output); target.mkdir(parents=True, exist_ok=True)
                        (target / 'HTTP-receipts.json').write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
                        (target / 'HTTP-serve.log').write_bytes(log_path.read_bytes())

    def test_real_http_new_service_reloads_sources_keys_and_r43_exactly(self):
        receipts, lifecycle, snapshots = [], [], {}
        with tempfile.TemporaryDirectory(prefix='pf6-app-http-cold-') as temporary:
            directory = Path(temporary)
            try:
                sources = {'A': {'kind': 'parameter', 'parameterId': 0, 'fieldId': 0},
                           'B': {'kind': 'spec', 'name': 'pf6_depth'}}

                def snapshot(service):
                    return {'dump': service.command('dump')['text'],
                            'state': service.command('panel-fill-read')['uiContract']['state'],
                            'references': service.command('references')}

                def reject_client_paths(service):
                    before = service.command('dump')['text']
                    for verb in ['pf6-suggest', 'pf6-select']:
                        denied = service.command(verb + ' C:\\client-owned\\request.json')
                        self.assertFalse(denied['ok'], 'PF6_HTTP_COLD_NO_CLIENT_PATH')
                    self.assertEqual(before, service.command('dump')['text'], 'PF6_HTTP_COLD_REJECT_ZERO_WRITE')

                with self.service(directory, 'first', receipts, lifecycle) as first:
                    command, post, packet = first.command, first.post, first.packet
                    self.assertTrue(command('reset')['ok'])
                    self.assertTrue(command('line boundary 8 outline 0,0 300,0 300,300 0,300 kind room_plan')['ok'])
                    self.assertTrue(command('line spec pf6_depth 30')['ok'])
                    engineering = command('engineering-read')
                    preview = post('/engineering/preview', {
                        'schema': 'engineering-transaction/1', 'expectedRevision': engineering['revision'],
                        'operations': [
                            {'op': 'publish-material', 'value': {'id': 'pf-board', 'version': 1, 'name': '板',
                             'kind': 'panel', 'width': 100, 'length': 100, 'thickness': '9'}},
                            {'op': 'put-parameter', 'value': {'id': 90, 'name': '門檻', 'fields': [
                             {'id': 1, 'name': 'X', 'type': 'dimension', 'input': '8'}]}},
                            {'op': 'put-parameter', 'value': {'id': 0, 'name': '零號寬度卡', 'fields': [
                             {'id': 0, 'name': '零號寬欄', 'type': 'dimension', 'input': '27'}]}}]})
                    self.assertTrue(preview['ok'] and preview['preview']['valid'], preview)
                    self.assertTrue(command('engineering-confirm ' + str(preview['preview']['token']))['ok'])
                    preview = post('/panel-fill/preview', {'schema': 'panel-fill-transaction/1',
                        'expectedRevision': command('panel-fill-read')['revision'],
                        'operations': [pf2.put(pf2.surface(boundary=8, origin=(0, 0, 0), obstacles=[])), pf2.fill()]})
                    self.assertTrue(preview['ok'] and preview['preview']['valid'], preview)
                    self.assertTrue(command('panel-fill-confirm ' + str(preview['preview']['token']))['ok'])
                    reject_client_paths(first)
                    before = snapshot(first)
                    request = suggest(str(command('panel-fill-read')['revision']))
                    request['input'].update(sources)
                    all_headers = {'X-Geometry-Session': first.runtime['session'],
                                   'X-Geometry-Request-Id': str(uuid.uuid4())}
                    for missing in ['version', 'X-Geometry-Session', 'X-Geometry-Request-Id']:
                        denied = post('/panel-fill/builder/suggest', request,
                                      headers={key: value for key, value in all_headers.items() if key != missing},
                                      with_version=missing != 'version')
                        self.assertFalse(denied['ok'], 'PF6_HTTP_COLD_REQUIRED_HEADERS')
                    self.assertEqual(before, snapshot(first), 'PF6_HTTP_COLD_HEADER_ZERO_WRITE')
                    proposal_id = str(uuid.uuid4())
                    proposal = packet('suggest', request, proposal_id)
                    self.assertTrue(proposal['ok'] and proposal['valid'], 'PF6_HTTP_COLD_SUGGEST')
                    self.assertIsNone(proposal['token'], 'PF6_HTTP_COLD_SUGGEST_TOKEN_NULL')
                    self.assertEqual(proposal, command('', receipt=proposal_id, session=first.runtime['session'])['result'],
                                     'PF6_HTTP_COLD_ORIGINAL_RECEIPT')
                    body = {'schema': 'panel-fill-builder-select/1', 'expectedRevision': proposal['revision'],
                            'generation': proposal['generation'], 'setKey': proposal['setKey'], 'selected': []}
                    empty = packet('select', body)['preview']
                    self.assertEqual('NO_OP', empty['phase'], 'PF6_HTTP_COLD_EMPTY_NO_OP')
                    self.assertIsNone(empty['token'], 'PF6_HTTP_COLD_EMPTY_TOKEN_NULL')
                    self.assertEqual(before, snapshot(first), 'PF6_HTTP_COLD_EMPTY_ZERO_WRITE')
                    body['selected'] = [row['key'] for row in proposal['entries'] if row['selectable'] and row['valid']]
                    selected = packet('select', body)['preview']
                    self.assertTrue(selected['valid'], 'PF6_HTTP_COLD_SELECTED_VALID')
                    self.assertIs(type(selected['token']), int, 'PF6_HTTP_COLD_POSITIVE_TOKEN')
                    self.assertTrue(1 <= selected['token'] <= 4294967295, 'PF6_HTTP_COLD_POSITIVE_TOKEN')
                    self.assertEqual(before, snapshot(first), 'PF6_HTTP_COLD_PREVIEW_ZERO_WRITE')
                    for field in ['A', 'B']:
                        self.assertEqual(sources[field], selected['appView']['input'][field]['source'],
                                         'PF6_HTTP_COLD_PREVIEW_TYPED_SOURCE')
                    commit_id = str(uuid.uuid4())
                    commit_cmd = 'pf6-confirm ' + str(selected['token'])
                    committed = command(commit_cmd, requestId=commit_id, session=first.runtime['session'])
                    self.assertTrue(committed['ok'] and committed['history_changed'], 'PF6_HTTP_COLD_CONFIRM')
                    self.assertEqual(committed, command('', receipt=commit_id, session=first.runtime['session'])['result'],
                                     'PF6_HTTP_COLD_CONFIRM_RECEIPT')
                    saved = snapshot(first)
                    self.assertEqual(selected['appView']['uiContract']['after'], saved['state'],
                                     'PF6_HTTP_COLD_SAME_CANDIDATE_WORLD')
                    timber_records = [json.loads(base64.b64decode(line.split()[2])) for line in saved['dump'].splitlines()
                                      if line.startswith('engineering timber ')]
                    self.assertEqual(12, len(timber_records), 'PF6_HTTP_COLD_ORDINARY_D7_COUNT')
                    for record in timber_records:
                        for field in ['A', 'B']:
                            self.assertEqual(sources[field], record[field]['source'], 'PF6_HTTP_COLD_SAVED_TYPED_SOURCE')
                    for forbidden in ['pf6-suggest', 'panel-fill-builder-suggestions', 'setKey', 'candidateId', 'duplicateOf']:
                        self.assertNotIn(forbidden, saved['dump'], 'PF6_HTTP_COLD_DEFINITIONS_ONLY')
                    keys = [edge['key'] for host in saved['state']['derivedPlacements']
                            for component in host['derived']['components'] for edge in component['edges']]
                    self.assertEqual(4, len(keys), 'PF6_HTTP_COLD_DERIVED_KEYS_PRESENT')
                    support = oracle.disclosed_support(saved['state'])
                    self.assertEqual(oracle.support_parts(oracle.construct_rectangles()), support,
                                     'PF6_HTTP_COLD_R43_INDEPENDENT_ORACLE')
                    self.assertTrue(command('line undo')['ok'])
                    self.assertEqual(before, snapshot(first), 'PF6_HTTP_COLD_ONE_UNDO')
                    self.assertTrue(command('line redo')['ok'])
                    self.assertEqual(saved, snapshot(first), 'PF6_HTTP_COLD_ONE_REDO')
                    (directory / 'saved.scene').write_bytes(saved['dump'].encode())
                    snapshots['saved'] = saved

                self.assertIsNotNone(first.process.poll(), 'PF6_HTTP_COLD_FIRST_STOPPED_BEFORE_NEW')
                with self.service(directory, 'second', receipts, lifecycle) as second:
                    self.assertNotEqual(first.runtime['pid'], second.runtime['pid'], 'PF6_HTTP_COLD_NEW_PROCESS')
                    self.assertNotEqual(first.runtime['session'], second.runtime['session'], 'PF6_HTTP_COLD_NEW_SESSION')
                    self.assertEqual(first.runtime['version'], second.runtime['version'], 'PF6_HTTP_COLD_SAME_SOURCE_VERSION')
                    self.assertNotEqual(saved['dump'], second.command('dump')['text'], 'PF6_HTTP_COLD_NO_OLD_WORLD')
                    prepared = second.post('/upload/prepare', raw=(directory / 'saved.scene').read_bytes())
                    self.assertTrue(prepared['ok'], 'PF6_HTTP_COLD_REOPEN_PREPARE')
                    loaded = second.post('/upload/confirm', prepared['token'])
                    self.assertTrue(loaded['ok'] and loaded['state'] == 'committed', 'PF6_HTTP_COLD_REOPEN_COMMIT')
                    reopened = snapshot(second)
                    self.assertEqual(saved['dump'].encode(), reopened['dump'].encode(), 'PF6_HTTP_COLD_DEFINITION_BYTES')
                    for key in ['state', 'references']:
                        self.assertEqual(json.dumps(saved[key], ensure_ascii=False, separators=(',', ':')).encode(),
                                         json.dumps(reopened[key], ensure_ascii=False, separators=(',', ':')).encode(),
                                         'PF6_HTTP_COLD_TYPED_GEOMETRY_KEYS_R43_BYTES')
                    self.assertEqual(support, oracle.disclosed_support(reopened['state']), 'PF6_HTTP_COLD_R43_BYTES')
                    self.assertFalse(second.command('', receipt=commit_id, session=first.runtime['session'])['ok'],
                                     'PF6_HTTP_COLD_OLD_RECEIPT_NOT_REBOUND')
                    reject_client_paths(second)
                    self.assertEqual(reopened, snapshot(second), 'PF6_HTTP_COLD_RECEIPT_ZERO_WRITE')
                    snapshots['reopened'] = reopened
            finally:
                output = os.environ.get('GEOMETRY_PF6_HTTP_RECEIPTS')
                if output:
                    target = Path(output); target.mkdir(parents=True, exist_ok=True)
                    for name, value in [('HTTP-cold-receipts.json', receipts), ('HTTP-cold-lifecycle.json', lifecycle),
                                        ('HTTP-cold-snapshots.json', snapshots)]:
                        (target / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
                    for path in directory.iterdir():
                        if path.is_file():
                            (target / ('HTTP-cold-' + path.name)).write_bytes(path.read_bytes())


if __name__ == '__main__':
    unittest.main()
