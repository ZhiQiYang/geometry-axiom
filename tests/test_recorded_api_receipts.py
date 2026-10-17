"""#240 S9 / P-151: T1 receipt contracts without importing or starting the server."""
import ast
import json
from pathlib import Path
import re
import threading
from types import SimpleNamespace
import unittest
import uuid
from unittest.mock import Mock, call


SOURCE = Path(__file__).resolve().parents[1] / 'geometry-web' / 'serve.py'


def load_receipt_functions():
    """Compile the real functions/constants; importing serve.py would start a bridge."""
    names = {'recorded_api', 'err_json', 'MAX_RECEIPTS', 'BRIDGE_TIMEOUT'}
    selected, found = [], set()
    for node in ast.parse(SOURCE.read_text(encoding='utf-8'), filename=str(SOURCE)).body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            selected.append(node)
            found.add(node.name)
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in names:
                selected.append(node)
                found.add(target.id)
    if found != names or len(selected) != len(names):
        raise AssertionError('serve.py receipt functions/constants missing or duplicated: %r' % found)
    namespace = {'json': json, 're': re}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(SOURCE), 'exec'), namespace)
    return namespace


class RecordedApiReceipts(unittest.TestCase):
    def setUp(self):
        self.api = load_receipt_functions()
        self.native = self.new_context()
        self.result = {'ok': True, 'transaction_id': 17, 'revision': 9}
        self.bridge = Mock(return_value=self.encode(self.result))
        self.api.update(current_native_context=lambda: self.native, ask_bridge=self.bridge)

    @staticmethod
    def new_context():
        return SimpleNamespace(session=uuid.uuid4().hex, api_receipts={}, receipt_lock=threading.Lock())

    @staticmethod
    def encode(value):
        return json.dumps(value, ensure_ascii=False).encode('utf-8')

    def send(self, **fields):
        return json.loads(self.api['recorded_api']({'session': self.native.session, **fields}))

    def assert_bridge_calls(self, *commands):
        self.assertEqual([call(command) for command in commands], self.bridge.call_args_list,
                         msg='T1_BRIDGE_CALLS: exact command sequence and count')

    def test_lost_response_lookup_and_same_command_replay_call_bridge_once(self):
        # Same-id replay tests the defensive guard; clients should recover by lookup.
        for result in (self.result, {'ok': False, 'error': 'controlled operation rejection'}):
            with self.subTest(operation_ok=result['ok']):
                self.native.api_receipts.clear()
                self.bridge.reset_mock()
                self.bridge.return_value = self.encode(result)
                request_id = str(uuid.uuid4())
                self.assertEqual(result, self.send(requestId=request_id, cmd='engineering-confirm 17'), msg='T1_LOST_RESPONSE')
                self.assert_bridge_calls('engineering-confirm 17')
                self.assertEqual({'ok': True, 'result': result}, self.send(receipt=request_id), msg='T1_LOST_RESPONSE')
                self.assert_bridge_calls('engineering-confirm 17')
                self.assertEqual(result, self.send(requestId=request_id, cmd='engineering-confirm 17'), msg='T1_LOST_RESPONSE')
                self.assert_bridge_calls('engineering-confirm 17')

    def test_lookup_before_command_seals_id_and_late_command_never_runs(self):
        request_id = str(uuid.uuid4())
        response = self.send(receipt=request_id)
        self.assertTrue(response['ok'], msg='T1_EARLY_LOOKUP')
        self.assertFalse(response['result']['ok'], msg='T1_EARLY_LOOKUP')
        self.assertIn('操作未送達', response['result']['error'], msg='T1_EARLY_LOOKUP')
        self.assert_bridge_calls()
        self.assertEqual(response['result'], self.send(requestId=request_id, cmd='engineering-confirm 17'), msg='T1_EARLY_LOOKUP')
        self.assertEqual(response, self.send(receipt=request_id), msg='T1_EARLY_LOOKUP')
        self.assert_bridge_calls()

    def test_same_id_different_command_is_rejected_without_another_bridge_call(self):
        request_id = str(uuid.uuid4())
        self.assertEqual(self.result, self.send(requestId=request_id, cmd='engineering-confirm 17'), msg='T1_COMMAND_BINDING')
        rejected = self.send(requestId=request_id, cmd='engineering-confirm 18')
        self.assertFalse(rejected['ok'], msg='T1_COMMAND_BINDING')
        self.assertIn('同一操作識別不得用於不同指令', rejected['error'], msg='T1_COMMAND_BINDING')
        self.assertEqual({'ok': True, 'result': self.result}, self.send(receipt=request_id), msg='T1_COMMAND_BINDING')
        self.assert_bridge_calls('engineering-confirm 17')

    def test_context_session_change_rejects_old_session_and_cannot_recover_old_result(self):
        request_id = str(uuid.uuid4())
        old_session = self.native.session
        self.assertEqual(self.result, self.send(requestId=request_id, cmd='engineering-confirm 17'), msg='T1_SESSION')
        # A controlled new context, not an actual service restart.
        self.native = self.new_context()
        rejected = self.send(session=old_session, receipt=request_id)
        self.assertFalse(rejected['ok'], msg='T1_SESSION')
        self.assertIn('服務已重啟或請求識別不合法', rejected['error'], msg='T1_SESSION')
        rejected_command = self.send(session=old_session, requestId=str(uuid.uuid4()), cmd='dump')
        self.assertFalse(rejected_command['ok'], msg='T1_SESSION')
        self.assertIn('服務已重啟或請求識別不合法', rejected_command['error'], msg='T1_SESSION')
        self.assertEqual({}, self.native.api_receipts, msg='T1_SESSION')
        missing = self.send(receipt=request_id)
        self.assertTrue(missing['ok'], msg='T1_SESSION')
        self.assertFalse(missing['result']['ok'], msg='T1_SESSION')
        self.assertIn('操作未送達', missing['result']['error'], msg='T1_SESSION')
        self.assert_bridge_calls('engineering-confirm 17')

    def test_capacity_256_rejects_new_id_before_bridge_but_allows_existing_lookup(self):
        self.assertEqual(256, self.api['MAX_RECEIPTS'], msg='T1_CAPACITY')
        for count in (255, 256):
            with self.subTest(unacknowledged=count):
                self.native = self.new_context()
                self.bridge.reset_mock()
                ids = [str(uuid.UUID(int=i + 1)) for i in range(count)]
                self.native.api_receipts.update((key, ('engineering-confirm 17', self.encode(self.result)))
                                                for key in ids)
                before = self.native.api_receipts.copy()
                request_id = str(uuid.uuid4())
                response = self.send(requestId=request_id, cmd='engineering-confirm 18')
                if count == 255:
                    self.assertEqual(self.result, response, msg='T1_CAPACITY')
                    self.assertEqual(256, len(self.native.api_receipts), msg='T1_CAPACITY')
                    self.assert_bridge_calls('engineering-confirm 18')
                else:
                    self.assertFalse(response['ok'], msg='T1_CAPACITY')
                    self.assertIn('未確認的操作結果過多', response['error'], msg='T1_CAPACITY')
                    self.assertEqual(before, self.native.api_receipts, msg='T1_CAPACITY')
                    self.assert_bridge_calls()
                self.assertEqual({'ok': True, 'result': self.result}, self.send(receipt=ids[0]), msg='T1_CAPACITY')
                self.assertEqual(int(count == 255), self.bridge.call_count, msg='T1_CAPACITY')

    def test_full_table_ack_in_same_request_frees_capacity_and_runs_new_command_once(self):
        ids = [str(uuid.UUID(int=i + 1)) for i in range(256)]
        old_result = self.encode({'ok': True, 'transaction_id': 16, 'revision': 8})
        self.native.api_receipts.update((key, ('engineering-confirm 16', old_result)) for key in ids)
        self.assertEqual(256, len(self.native.api_receipts), msg='T1_ACK_CAPACITY')
        self.assert_bridge_calls()
        expected = self.native.api_receipts.copy()
        del expected[ids[0]]
        request_id = str(uuid.UUID(int=257))
        response = self.send(requestId=request_id, cmd='engineering-confirm 17', ack=[ids[0]])
        self.assertEqual(self.result, response,
                         msg='T1_ACK_CAPACITY: clear this request ack before checking new-id capacity')
        self.assert_bridge_calls('engineering-confirm 17')
        expected[request_id] = ('engineering-confirm 17', self.encode(self.result))
        self.assertEqual(expected, self.native.api_receipts,
                         msg='T1_ACK_CAPACITY: replace only the acknowledged receipt with the new result')
        self.assertEqual({'ok': True, 'result': self.result}, self.send(receipt=request_id),
                         msg='T1_ACK_CAPACITY: new result remains recoverable without another bridge call')
        self.assert_bridge_calls('engineering-confirm 17')

    def test_ack_clears_old_result_and_later_lookup_does_not_restore_history(self):
        request_id, ack_id = str(uuid.uuid4()), str(uuid.uuid4())
        self.assertEqual(self.result, self.send(requestId=request_id, cmd='engineering-confirm 17'), msg='T1_ACK_HISTORY')
        self.assert_bridge_calls('engineering-confirm 17')
        self.assertEqual(self.result, self.send(requestId=ack_id, cmd='dump', ack=[request_id]), msg='T1_ACK_HISTORY')
        self.assertNotIn(request_id, self.native.api_receipts, msg='T1_ACK_HISTORY')
        expected_calls = [call('engineering-confirm 17'), call('dump')]
        self.assertEqual(expected_calls, self.bridge.call_args_list, msg='T1_ACK_HISTORY')
        missing = self.send(receipt=request_id)
        self.assertTrue(missing['ok'], msg='T1_ACK_HISTORY')
        self.assertFalse(missing['result']['ok'], msg='T1_ACK_HISTORY')
        self.assertIn('操作未送達', missing['result']['error'], msg='T1_ACK_HISTORY')
        self.assertEqual(missing['result'], self.send(requestId=request_id, cmd='engineering-confirm 17'), msg='T1_ACK_HISTORY')
        # Ack must not remove a sealed cancellation and permit its late command.
        self.send(requestId=ack_id, cmd='dump', ack=[request_id])
        self.assertIn(request_id, self.native.api_receipts, msg='T1_ACK_HISTORY')
        self.assertEqual(expected_calls, self.bridge.call_args_list, msg='T1_ACK_HISTORY')

    def test_acknowledged_id_direct_replay_runs_again_so_client_must_not_reuse_id(self):
        request_id, ack_id = str(uuid.uuid4()), str(uuid.uuid4())
        self.assertEqual(self.result, self.send(requestId=request_id, cmd='engineering-confirm 17'), msg='T1_ACK_REPLAY')
        self.assert_bridge_calls('engineering-confirm 17')
        self.assertEqual(self.result, self.send(requestId=ack_id, cmd='dump', ack=[request_id]), msg='T1_ACK_REPLAY')
        self.assert_bridge_calls('engineering-confirm 17', 'dump')
        self.assertNotIn(request_id, self.native.api_receipts, msg='T1_ACK_REPLAY')
        # No receipt lookup between ack and replay: a lookup would seal this id.
        self.assertEqual(self.result, self.send(requestId=request_id, cmd='engineering-confirm 17'), msg='T1_ACK_REPLAY')
        self.assert_bridge_calls('engineering-confirm 17', 'dump', 'engineering-confirm 17')

    def test_early_lookup_cancellations_fill_session_and_ack_cannot_free_capacity(self):
        for i in range(256):
            request_id = str(uuid.UUID(int=i + 1))
            response = self.send(receipt=request_id, ack=list(self.native.api_receipts))
            self.assertTrue(response['ok'], msg='T1_SEALED_CAPACITY')
            self.assertFalse(response['result']['ok'], msg='T1_SEALED_CAPACITY')
            self.assertIn('操作未送達', response['result']['error'], msg='T1_SEALED_CAPACITY')
        self.assertEqual(256, len(self.native.api_receipts), msg='T1_SEALED_CAPACITY')
        self.assert_bridge_calls()
        request_id = str(uuid.uuid4())
        for request in ({'requestId': request_id, 'cmd': 'dump'}, {'receipt': request_id}):
            with self.subTest(request=request):
                rejected = self.send(**request, ack=list(self.native.api_receipts))
                self.assertFalse(rejected['ok'], msg='T1_SEALED_CAPACITY')
                self.assertIn('未確認的操作結果過多', rejected['error'], msg='T1_SEALED_CAPACITY')
                self.assertEqual(256, len(self.native.api_receipts), msg='T1_SEALED_CAPACITY')
                self.assert_bridge_calls()
        self.native = self.new_context()
        self.assertEqual(self.result, self.send(requestId=request_id, cmd='dump'), msg='T1_SEALED_CAPACITY')
        self.assert_bridge_calls('dump')

    def test_full_table_rejects_lookup_of_new_id_without_sealing_or_calling_bridge(self):
        self.native.api_receipts.update((str(uuid.UUID(int=i + 1)), ('dump', self.encode(self.result)))
                                        for i in range(256))
        before = self.native.api_receipts.copy()
        rejected = self.send(receipt=str(uuid.uuid4()))
        self.assertFalse(rejected['ok'], msg='T1_FULL_LOOKUP')
        self.assertIn('未確認的操作結果過多', rejected['error'], msg='T1_FULL_LOOKUP')
        self.assertEqual(before, self.native.api_receipts, msg='T1_FULL_LOOKUP')
        self.assert_bridge_calls()

    def test_ack_list_only_processes_first_256_entries(self):
        request_id = str(uuid.uuid4())
        self.assertEqual(self.result, self.send(requestId=request_id, cmd='dump'), msg='T1_ACK_LIMIT')
        unused_ids = [str(uuid.UUID(int=i + 1)) for i in range(256)]
        # First 255 no-op acknowledgements plus this id: position 256 is processed.
        self.send(requestId=str(uuid.uuid4()), cmd='newid', ack=unused_ids[:255] + [request_id])
        self.assertNotIn(request_id, self.native.api_receipts, msg='T1_ACK_LIMIT')
        # Position 257 is ignored, even when the earlier ids do not exist.
        self.assertEqual(self.result, self.send(requestId=request_id, cmd='dump'), msg='T1_ACK_LIMIT')
        self.send(requestId=str(uuid.uuid4()), cmd='newid', ack=unused_ids + [request_id])
        self.assertIn(request_id, self.native.api_receipts, msg='T1_ACK_LIMIT')
        self.assert_bridge_calls('dump', 'newid', 'dump', 'newid')

    def test_receipt_lock_is_held_during_bridge_and_busy_wait_uses_30_second_limit(self):
        self.assertEqual(30.0, self.api['BRIDGE_TIMEOUT'], msg='T1_LOCK')

        def while_locked(command):
            acquired = self.native.receipt_lock.acquire(blocking=False)
            if acquired:
                self.native.receipt_lock.release()
            self.assertFalse(acquired, msg='T1_LOCK_HELD: bridge runs under the receipt lock')
            return self.encode(self.result)

        self.bridge.side_effect = while_locked
        self.assertEqual(self.result, self.send(requestId=str(uuid.uuid4()), cmd='dump'), msg='T1_LOCK')
        self.assertFalse(self.native.receipt_lock.locked(), msg='T1_LOCK')
        self.assert_bridge_calls('dump')
        busy_lock = Mock()
        busy_lock.acquire.return_value = False
        self.native.receipt_lock = busy_lock
        rejected = self.send(receipt=str(uuid.uuid4()))
        self.assertFalse(rejected['ok'], msg='T1_LOCK')
        self.assertIn('操作結果仍在處理', rejected['error'], msg='T1_LOCK')
        self.assertEqual([call(timeout=30.0)], busy_lock.acquire.call_args_list, msg='T1_LOCK')
        self.assertEqual(0, busy_lock.release.call_count, msg='T1_LOCK')
        self.assert_bridge_calls('dump')


if __name__ == '__main__':
    unittest.main()
