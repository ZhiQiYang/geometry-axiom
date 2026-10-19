"""#240 S9 / P-151: T1 receipt contracts without importing or starting the server."""
import ast
import importlib.util
import json
from pathlib import Path
import re
import threading
from types import SimpleNamespace
import unittest
import uuid
from unittest.mock import Mock, call, patch


SOURCE = Path(__file__).resolve().parents[1] / 'geometry-web' / 'serve.py'
NATIVE_SOURCE = SOURCE.with_name('native_context.py')


def load_native_context_class():
    """The real NativeContext (it imports nothing from the server); only Popen is replaced per use."""
    spec = importlib.util.spec_from_file_location('receipts_native_context_under_test', NATIVE_SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.NativeContext


def load_receipt_functions():
    """Compile the real functions/constants; importing serve.py would start a bridge."""
    names = {'recorded_api', 'err_json', 'MAX_RECEIPTS', 'BRIDGE_TIMEOUT'}
    # #264: the sealed-id bound is optional at load time so a source without it
    # fails its own named tests instead of making every test error while loading.
    optional = {'MAX_SEALED_RECEIPTS'}
    selected, found = [], []
    for node in ast.parse(SOURCE.read_text(encoding='utf-8'), filename=str(SOURCE)).body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            selected.append(node)
            found.append(node.name)
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in names | optional:
                selected.append(node)
                found.append(target.id)
    if not names <= set(found) or len(found) != len(set(found)):
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
        return SimpleNamespace(session=uuid.uuid4().hex, api_receipts={}, api_sealed=set(),
                               receipt_lock=threading.Lock())

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
        # (#264: the seal now lives in api_sealed, never in the result table.)
        self.send(requestId=ack_id, cmd='dump', ack=[request_id])
        self.assertIn(request_id, self.native.api_sealed, msg='T1_ACK_HISTORY')
        self.assertNotIn(request_id, self.native.api_receipts, msg='T1_ACK_HISTORY')
        self.assertEqual(expected_calls, self.bridge.call_args_list, msg='T1_ACK_HISTORY')
        self.assertEqual(missing['result'], self.send(requestId=request_id, cmd='engineering-confirm 17'), msg='T1_ACK_HISTORY')
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

    # --- #264: sealed (early-lookup) ids are counted apart from unacknowledged results ---

    def seal_by_early_lookup(self, count, *, ack_previous=False):
        """Early-lookup `count` distinct ids through the real function; return the ids."""
        ids = []
        for i in range(count):
            request_id = str(uuid.UUID(int=i + 1))
            response = self.send(receipt=request_id, ack=list(ids) if ack_previous else [])
            self.assertTrue(response['ok'], msg='T1_SEALED_SETUP')
            self.assertFalse(response['result']['ok'], msg='T1_SEALED_SETUP')
            self.assertIn('操作未送達', response['result']['error'], msg='T1_SEALED_SETUP')
            ids.append(request_id)
        return ids

    def assert_sealed_unchanged(self, before):
        # Compare sizes of the differences, not the sets: a 4096-id diff is unreadable.
        now = self.native.api_sealed
        self.assertEqual((0, 0), (len(before - now), len(now - before)),
                         msg='T1_SEALED_FULL: 封存項數量變動 (少了, 多了) - 不得新增也不得淘汰封存項')

    def test_256_early_lookups_do_not_consume_command_capacity_and_new_command_runs_once(self):
        sealed = self.seal_by_early_lookup(256, ack_previous=True)
        self.assert_bridge_calls()
        request_id = str(uuid.uuid4())
        # Even carrying an ack of every sealed id, the new command must not be refused.
        response = self.send(requestId=request_id, cmd='dump', ack=sealed)
        self.assertEqual(self.result, response,
                         msg='T1_SEALED_CAPACITY: 容量被封存項佔滿 - 256 次早查詢後新命令被拒、bridge 未被呼叫；'
                             '封存項不得計入待 ack 結果的容量')
        self.assert_bridge_calls('dump')
        self.assertEqual({'ok': True, 'result': self.result}, self.send(receipt=request_id), msg='T1_SEALED_CAPACITY')
        self.assert_bridge_calls('dump')
        # The result capacity is still the full 256: sealed ids take none of it.
        for i in range(255):
            self.assertEqual(self.result, self.send(requestId=str(uuid.UUID(int=1000 + i)), cmd='dump'),
                             msg='T1_SEALED_CAPACITY: 封存項不得縮減待 ack 結果的 256 筆容量')
        self.assertEqual(256, len(self.native.api_receipts), msg='T1_SEALED_CAPACITY')
        self.assertEqual(256, self.bridge.call_count, msg='T1_SEALED_CAPACITY')
        rejected = self.send(requestId=str(uuid.uuid4()), cmd='dump')
        self.assertFalse(rejected['ok'], msg='T1_SEALED_CAPACITY')
        self.assertIn('未確認的操作結果過多', rejected['error'], msg='T1_SEALED_CAPACITY')
        self.assertEqual(256, self.bridge.call_count, msg='T1_SEALED_CAPACITY')

    def test_late_command_for_an_early_looked_up_id_never_runs(self):
        first, middle, last = (str(uuid.uuid4()) for _ in range(3))
        for request_id in (first, middle):
            self.assertFalse(self.send(receipt=request_id)['result']['ok'], msg='T1_SEALED_LATE')
        # Ordinary traffic in between neither unseals nor is blocked by the seals.
        self.assertEqual(self.result, self.send(requestId=str(uuid.uuid4()), cmd='dump'), msg='T1_SEALED_LATE')
        self.assertFalse(self.send(receipt=last)['result']['ok'], msg='T1_SEALED_LATE')
        self.assert_bridge_calls('dump')
        unsent = json.loads(self.api['err_json']('操作未送達，場景未變更；請重新操作。'))
        for request_id in (first, middle, last):
            for command in ('engineering-confirm 17', 'engineering-confirm 18'):
                with self.subTest(request_id=request_id, cmd=command):
                    self.assertEqual(unsent, self.send(requestId=request_id, cmd=command),
                                     msg='T1_SEALED_LATE: late command of a sealed id must answer 未送達 and not run')
                    self.assertEqual({'ok': True, 'result': unsent}, self.send(receipt=request_id),
                                     msg='T1_SEALED_LATE')
        self.assert_bridge_calls('dump')

    def test_ack_never_clears_a_sealed_id_so_its_late_command_still_does_not_run(self):
        def sealed_then(late_ack, *, carrier):
            self.native = self.new_context()
            self.bridge.reset_mock()
            sealed_id, carrier_id = str(uuid.uuid4()), str(uuid.uuid4())
            self.assertFalse(self.send(receipt=sealed_id)['result']['ok'], msg='T1_ACK_SEALED')
            calls = []
            if carrier == 'command':
                self.assertEqual(self.result, self.send(requestId=carrier_id, cmd='dump', ack=[sealed_id]), msg='T1_ACK_SEALED')
                calls.append('dump')
            elif carrier == 'lookup':
                self.assertTrue(self.send(receipt=carrier_id, ack=[sealed_id])['ok'], msg='T1_ACK_SEALED')
            elif carrier == 'bulk':
                # The sealed id sits at position 256 of an ack list that is processed in full.
                filler = [str(uuid.UUID(int=i + 1)) for i in range(255)]
                self.assertEqual(self.result, self.send(requestId=carrier_id, cmd='dump', ack=filler + [sealed_id]), msg='T1_ACK_SEALED')
                calls.append('dump')
            late = self.send(requestId=sealed_id, cmd='engineering-confirm 17', ack=[sealed_id] if late_ack else [])
            self.assertFalse(late['ok'], msg='T1_ACK_SEALED: ack 清掉封存項 - 晚到命令被執行 (I67)')
            self.assertIn('操作未送達', late['error'], msg='T1_ACK_SEALED: ack 清掉封存項 - 晚到命令被執行 (I67)')
            self.assert_bridge_calls(*calls)
            looked_up = self.send(receipt=sealed_id)
            self.assertTrue(looked_up['ok'], msg='T1_ACK_SEALED')
            self.assertEqual(late, looked_up['result'], msg='T1_ACK_SEALED')
            self.assert_bridge_calls(*calls)

        for carrier in ('command', 'lookup', 'bulk'):
            for late_ack in (False, True):
                with self.subTest(carrier=carrier, ack_on_the_late_command_itself=late_ack):
                    sealed_then(late_ack, carrier=carrier)

    def test_sealed_set_full_refuses_new_early_lookup_explicitly_and_never_evicts(self):
        limit = self.api.get('MAX_SEALED_RECEIPTS')
        self.assertIsNotNone(limit, msg='T1_SEALED_FULL: serve.py 沒有封存項上限常數 MAX_SEALED_RECEIPTS')
        self.assertGreater(limit, self.api['MAX_RECEIPTS'], msg='T1_SEALED_FULL: id-only 封存項的上限應比結果容量寬鬆')
        sealed = self.seal_by_early_lookup(limit)
        self.assertEqual(limit, len(self.native.api_sealed), msg='T1_SEALED_FULL')
        self.assertEqual({}, self.native.api_receipts, msg='T1_SEALED_FULL')
        before = set(self.native.api_sealed)
        refused_id = str(uuid.uuid4())
        for ack in ([], sealed[:256]):
            with self.subTest(ack_count=len(ack)):
                refused = self.send(receipt=refused_id, ack=ack)
                self.assertFalse(refused['ok'], msg='T1_SEALED_FULL: 封存項已滿時新早查詢必須被明確拒絕')
                self.assertIn('早查詢封存項已達上限', refused['error'], msg='T1_SEALED_FULL')
                self.assertIn('未被受理', refused['error'], msg='T1_SEALED_FULL: 要講明這次查詢不是「未送達」')
                self.assertNotIn('操作未送達', refused['error'], msg='T1_SEALED_FULL')
                self.assert_sealed_unchanged(before)
                self.assert_bridge_calls()
        # No eviction: the oldest and the newest seal still hold, and their late commands do not run.
        unsent = json.loads(self.api['err_json']('操作未送達，場景未變更；請重新操作。'))
        for request_id in (sealed[0], sealed[-1]):
            self.assertEqual({'ok': True, 'result': unsent}, self.send(receipt=request_id), msg='T1_SEALED_FULL')
            self.assertEqual(unsent, self.send(requestId=request_id, cmd='engineering-confirm 17'), msg='T1_SEALED_FULL')
        self.assert_bridge_calls()
        # A full sealed set does not touch command capacity.
        self.assertEqual(self.result, self.send(requestId=str(uuid.uuid4()), cmd='dump'), msg='T1_SEALED_FULL')
        self.assert_bridge_calls('dump')
        self.assert_sealed_unchanged(before)

    def test_sealed_id_still_answers_unsent_and_late_command_does_not_run_when_result_table_is_full(self):
        sealed_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        for request_id in sealed_ids:
            self.assertFalse(self.send(receipt=request_id)['result']['ok'], msg='T1_SEALED_TABLE_FULL')
        # 256 bound, unacknowledged results: the result table is at its limit.
        self.native.api_receipts.update((str(uuid.UUID(int=i + 1)), ('dump', self.encode(self.result)))
                                        for i in range(256))
        results_before, sealed_before = self.native.api_receipts.copy(), set(self.native.api_sealed)
        unsent = json.loads(self.api['err_json']('操作未送達，場景未變更；請重新操作。'))
        why = ('T1_SEALED_TABLE_FULL: 待 ack 表已滿時，已封存 id 的查詢與晚到命令必須仍回「操作未送達」，'
               '不得被「未確認的操作結果過多」取代，更不得執行')
        for request_id in sealed_ids:
            with self.subTest(request_id=request_id):
                self.assertEqual({'ok': True, 'result': unsent}, self.send(receipt=request_id), msg=why)
                self.assertEqual(unsent, self.send(requestId=request_id, cmd='engineering-confirm 17'), msg=why)
                self.assertEqual(unsent, self.send(requestId=request_id, cmd='engineering-confirm 18'), msg=why)
        # The table stayed full throughout; no seal changed and nothing ran.
        self.assertEqual(results_before, self.native.api_receipts, msg='T1_SEALED_TABLE_FULL')
        self.assertEqual(sealed_before, self.native.api_sealed, msg='T1_SEALED_TABLE_FULL')
        self.assert_bridge_calls()

    def test_new_session_has_an_empty_sealed_set_and_old_session_keeps_its_own(self):
        context_class = load_native_context_class()  # one class: a class-level set would be shared

        def real_context():
            process = Mock()
            process.stdout.readline.return_value = b''  # the reader thread ends at once
            with patch('subprocess.Popen', return_value=process):
                native = context_class(['unused-bridge'])
            native.reader.join(timeout=2)
            self.assertFalse(native.reader.is_alive(), msg='T1_SESSION_SEALED')
            return native

        old, new = real_context(), real_context()
        self.assertNotEqual(old.session, new.session, msg='T1_SESSION_SEALED')
        self.assertIsNot(old.api_sealed, new.api_sealed, msg='T1_SESSION_SEALED: 封存集合是每個 context 自己的，不得共用')
        request_id = str(uuid.uuid4())
        unsent = json.loads(self.api['err_json']('操作未送達，場景未變更；請重新操作。'))
        self.native = old
        self.assertEqual({'ok': True, 'result': unsent}, self.send(receipt=request_id), msg='T1_SESSION_SEALED')
        self.assertEqual({request_id}, old.api_sealed, msg='T1_SESSION_SEALED')
        self.native = new
        self.assertEqual(set(), new.api_sealed, msg='T1_SESSION_SEALED: 新 session 的封存集合必須是空的')
        rejected = self.send(session=old.session, requestId=request_id, cmd='engineering-confirm 17')
        self.assertFalse(rejected['ok'], msg='T1_SESSION_SEALED')
        self.assertIn('服務已重啟或請求識別不合法', rejected['error'], msg='T1_SESSION_SEALED')
        self.assert_bridge_calls()
        self.assertEqual(self.result, self.send(requestId=request_id, cmd='engineering-confirm 17'),
                         msg='T1_SESSION_SEALED: 舊 session 的封存不得擋住新 session 的同 id 命令')
        self.assert_bridge_calls('engineering-confirm 17')
        self.assertEqual(set(), new.api_sealed, msg='T1_SESSION_SEALED')
        self.assertIn(request_id, new.api_receipts, msg='T1_SESSION_SEALED')
        # Back on the old session: its seal is untouched and its late command still does not run.
        self.native = old
        self.assertEqual({request_id}, old.api_sealed, msg='T1_SESSION_SEALED')
        self.assertEqual({}, old.api_receipts, msg='T1_SESSION_SEALED')
        self.assertEqual(unsent, self.send(requestId=request_id, cmd='engineering-confirm 17'), msg='T1_SESSION_SEALED')
        self.assertEqual({'ok': True, 'result': unsent}, self.send(receipt=request_id), msg='T1_SESSION_SEALED')
        self.assert_bridge_calls('engineering-confirm 17')

    def test_full_table_rejects_lookup_of_new_id_without_sealing_or_calling_bridge(self):
        self.native.api_receipts.update((str(uuid.UUID(int=i + 1)), ('dump', self.encode(self.result)))
                                        for i in range(256))
        before = self.native.api_receipts.copy()
        rejected = self.send(receipt=str(uuid.uuid4()))
        self.assertFalse(rejected['ok'], msg='T1_FULL_LOOKUP')
        self.assertIn('未確認的操作結果過多', rejected['error'], msg='T1_FULL_LOOKUP')
        self.assertEqual(before, self.native.api_receipts, msg='T1_FULL_LOOKUP')
        self.assertEqual(set(), self.native.api_sealed, msg='T1_FULL_LOOKUP')
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
