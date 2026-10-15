"""#240 S9: six T1 receipt contracts, without importing or starting the server."""
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

    def test_lost_response_lookup_and_same_command_replay_call_bridge_once(self):
        # Same-id replay tests the defensive guard; clients should recover by lookup.
        for result in (self.result, {'ok': False, 'error': 'controlled operation rejection'}):
            with self.subTest(operation_ok=result['ok']):
                self.native.api_receipts.clear()
                self.bridge.reset_mock()
                self.bridge.return_value = self.encode(result)
                request_id = str(uuid.uuid4())
                self.assertEqual(result, self.send(requestId=request_id, cmd='engineering-confirm 17'))
                self.bridge.assert_called_once_with('engineering-confirm 17')
                self.assertEqual({'ok': True, 'result': result}, self.send(receipt=request_id))
                self.bridge.assert_called_once_with('engineering-confirm 17')
                self.assertEqual(result, self.send(requestId=request_id, cmd='engineering-confirm 17'))
                self.bridge.assert_called_once_with('engineering-confirm 17')

    def test_lookup_before_command_seals_id_and_late_command_never_runs(self):
        request_id = str(uuid.uuid4())
        response = self.send(receipt=request_id)
        self.assertTrue(response['ok'])
        self.assertFalse(response['result']['ok'])
        self.assertIn('操作未送達', response['result']['error'])
        self.bridge.assert_not_called()
        self.assertEqual(response['result'], self.send(requestId=request_id, cmd='engineering-confirm 17'))
        self.assertEqual(response, self.send(receipt=request_id))
        self.bridge.assert_not_called()

    def test_same_id_different_command_is_rejected_without_another_bridge_call(self):
        request_id = str(uuid.uuid4())
        self.assertEqual(self.result, self.send(requestId=request_id, cmd='engineering-confirm 17'))
        rejected = self.send(requestId=request_id, cmd='engineering-confirm 18')
        self.assertFalse(rejected['ok'])
        self.assertIn('同一操作識別不得用於不同指令', rejected['error'])
        self.assertEqual({'ok': True, 'result': self.result}, self.send(receipt=request_id))
        self.bridge.assert_called_once_with('engineering-confirm 17')

    def test_context_session_change_rejects_old_session_and_cannot_recover_old_result(self):
        request_id = str(uuid.uuid4())
        old_session = self.native.session
        self.assertEqual(self.result, self.send(requestId=request_id, cmd='engineering-confirm 17'))
        # A controlled new context, not an actual service restart.
        self.native = self.new_context()
        rejected = self.send(session=old_session, receipt=request_id)
        self.assertFalse(rejected['ok'])
        self.assertIn('服務已重啟或請求識別不合法', rejected['error'])
        self.assertEqual({}, self.native.api_receipts)
        missing = self.send(receipt=request_id)
        self.assertTrue(missing['ok'])
        self.assertFalse(missing['result']['ok'])
        self.assertIn('操作未送達', missing['result']['error'])
        self.bridge.assert_called_once_with('engineering-confirm 17')

    def test_capacity_256_rejects_new_id_before_bridge_but_allows_existing_lookup(self):
        self.assertEqual(256, self.api['MAX_RECEIPTS'])
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
                    self.assertEqual(self.result, response)
                    self.assertEqual(256, len(self.native.api_receipts))
                    self.bridge.assert_called_once_with('engineering-confirm 18')
                else:
                    self.assertFalse(response['ok'])
                    self.assertIn('未確認的操作結果過多', response['error'])
                    self.assertEqual(before, self.native.api_receipts)
                    self.bridge.assert_not_called()
                self.assertEqual({'ok': True, 'result': self.result}, self.send(receipt=ids[0]))
                self.assertEqual(int(count == 255), self.bridge.call_count)

    def test_ack_clears_old_result_and_later_lookup_does_not_restore_history(self):
        request_id, ack_id = str(uuid.uuid4()), str(uuid.uuid4())
        self.assertEqual(self.result, self.send(requestId=request_id, cmd='engineering-confirm 17'))
        self.bridge.assert_called_once_with('engineering-confirm 17')
        self.assertEqual(self.result, self.send(requestId=ack_id, cmd='dump', ack=[request_id]))
        self.assertNotIn(request_id, self.native.api_receipts)
        expected_calls = [call('engineering-confirm 17'), call('dump')]
        self.assertEqual(expected_calls, self.bridge.call_args_list)
        missing = self.send(receipt=request_id)
        self.assertTrue(missing['ok'])
        self.assertFalse(missing['result']['ok'])
        self.assertIn('操作未送達', missing['result']['error'])
        self.assertEqual(missing['result'], self.send(requestId=request_id, cmd='engineering-confirm 17'))
        # Ack must not remove a sealed cancellation and permit its late command.
        self.send(requestId=ack_id, cmd='dump', ack=[request_id])
        self.assertIn(request_id, self.native.api_receipts)
        self.assertEqual(expected_calls, self.bridge.call_args_list)


if __name__ == '__main__':
    unittest.main()
