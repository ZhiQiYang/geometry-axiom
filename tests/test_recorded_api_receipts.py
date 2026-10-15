"""T1 receipt contract (#240 S9): real functions, controlled native/bridge only.

Select definitions from serve.py's AST instead of importing its process-starting
module. No HTTP server, native process or copied receipt implementation is used.
These tests do not prove T2 native commits or T3 project attachment atomicity.
"""
import ast
import json
from pathlib import Path
import re
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[1]


def load_recorded_api(native, bridge):
    path = ROOT / "geometry-web" / "serve.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names = {"err_json", "recorded_api"}
    constants = {"MAX_RECEIPTS", "BRIDGE_TIMEOUT"}
    selected = []
    found = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            selected.append(node)
            found.add(node.name)
        elif isinstance(node, ast.Assign):
            targets = {t.id for t in node.targets if isinstance(t, ast.Name)}
            if targets & constants:
                if not targets <= constants:
                    raise AssertionError("T1 extraction: unexpected shared assignment")
                selected.append(node)
                found.update(targets)
    if found != names | constants:
        raise AssertionError("T1 extraction: production definitions missing: %r" % (names | constants - found))
    namespace = {"json": json, "re": re, "ask_bridge": bridge,
                 "current_native_context": lambda: native}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), "exec"), namespace)
    return namespace["recorded_api"], namespace["MAX_RECEIPTS"]


def request_id(index):
    return "%08x-0000-0000-0000-%012x" % (index, index)


class RecordedApiReceipts(unittest.TestCase):
    def setUp(self):
        self.native = SimpleNamespace(session="test-session", api_receipts={},
                                      receipt_lock=threading.Lock())
        self.bridge = Mock(return_value=b'{"ok":true,"revision":7,"transaction_id":19}')
        self.recorded, self.capacity = load_recorded_api(self.native, self.bridge)
        self.q = request_id(1)

    def tearDown(self):
        self.assertFalse(self.native.receipt_lock.locked(), "T1_LOCK_RELEASED")

    def call(self, **data):
        return json.loads(self.recorded({"session": self.native.session, **data}))

    def test_lost_response_lookup_and_same_command_do_not_reexecute(self):
        first = self.call(requestId=self.q, cmd="engineering-confirm 19")
        self.assertEqual({"ok": True, "revision": 7, "transaction_id": 19}, first)
        recovered = self.call(receipt=self.q)
        self.assertEqual({"ok": True, "result": first}, recovered, "T1_LOST_RESPONSE_RECOVERED")
        self.assertEqual(first, self.call(requestId=self.q, cmd="engineering-confirm 19"))
        self.assertEqual(1, self.bridge.call_count, "T1_NO_REEXECUTION: lookup/repeat must use cached result")
        self.bridge.assert_called_once_with("engineering-confirm 19")

    def test_lookup_before_command_seals_id_even_when_acknowledged(self):
        early = self.call(receipt=self.q)
        self.assertTrue(early["ok"], "T1_OUTER_OK_MEANS_RESULT_AVAILABLE")
        self.assertFalse(early["result"]["ok"])
        self.assertIn("操作未送達", early["result"]["error"])
        late = self.call(requestId=self.q, cmd="engineering-confirm 19", ack=[self.q])
        self.assertEqual(early["result"], late, "T1_EARLY_LOOKUP_SEALS_ID")
        self.assertEqual(early, self.call(receipt=self.q))
        self.assertEqual(0, self.bridge.call_count, "T1_CANCELLED_ID_NEVER_EXECUTES")

    def test_same_id_with_different_command_is_rejected(self):
        first = self.call(requestId=self.q, cmd="engineering-confirm 19")
        rejected = self.call(requestId=self.q, cmd="engineering-confirm 20")
        self.assertFalse(rejected["ok"], "T1_COMMAND_BINDING")
        self.assertIn("不同指令", rejected["error"])
        self.assertEqual(first, self.call(receipt=self.q)["result"])
        self.assertEqual(1, self.bridge.call_count, "T1_CHANGED_COMMAND_NOT_EXECUTED")

    def test_changed_session_rejects_old_lookup_and_command(self):
        self.call(requestId=self.q, cmd="engineering-confirm 19")
        old_session = self.native.session
        self.native.session = "replacement-session"
        self.native.api_receipts.clear()  # Model context replacement, not a real restart.
        for operation in ({"receipt": self.q},
                          {"requestId": self.q, "cmd": "engineering-confirm 19"}):
            with self.subTest(operation=operation):
                result = self.call(**operation, session=old_session)
                self.assertFalse(result["ok"], "T1_SESSION_INVALIDATION")
                self.assertIn("服務已重啟或請求識別不合法", result["error"])
        self.assertEqual({}, self.native.api_receipts)
        self.assertEqual(1, self.bridge.call_count, "T1_OLD_SESSION_NOT_EXECUTED")

    def test_256_unacknowledged_results_block_new_command(self):
        self.assertEqual(256, self.capacity, "T1_CAPACITY_256")
        encoded = b'{"ok":true}'
        self.native.api_receipts.update({request_id(i): ("old command", encoded)
                                         for i in range(1, 257)})
        before = dict(self.native.api_receipts)
        result = self.call(requestId=request_id(257), cmd="engineering-confirm 19")
        self.assertFalse(result["ok"], "T1_CAPACITY_REJECTS_BEFORE_BRIDGE")
        self.assertIn("未確認的操作結果過多", result["error"])
        self.assertEqual(before, self.native.api_receipts)
        self.assertEqual(0, self.bridge.call_count, "T1_FULL_CACHE_NOT_EXECUTED")
        self.assertEqual({"ok": True, "result": {"ok": True}}, self.call(receipt=self.q))
        self.assertEqual(0, self.bridge.call_count)

    def test_ack_clears_result_and_later_lookup_is_not_durable_history(self):
        original = self.call(requestId=self.q, cmd="engineering-confirm 19")
        self.bridge.return_value = b'{"ok":true,"revision":8,"transaction_id":20}'
        second = self.call(requestId=request_id(2), cmd="engineering-confirm 20", ack=[self.q])
        self.assertEqual(8, second["revision"])
        self.assertNotIn(self.q, self.native.api_receipts, "T1_ACK_REMOVES_RESULT")
        late = self.call(receipt=self.q)
        self.assertTrue(late["ok"])
        self.assertFalse(late["result"]["ok"], "T1_ACK_IS_NOT_DURABLE_HISTORY")
        self.assertIn("操作未送達", late["result"]["error"])
        self.assertNotEqual(original, late["result"])
        self.assertEqual(2, self.bridge.call_count, "T1_LOOKUP_AFTER_ACK_NOT_EXECUTED")
        self.assertEqual(["engineering-confirm 19", "engineering-confirm 20"],
                         [c.args[0] for c in self.bridge.call_args_list])


if __name__ == "__main__":
    unittest.main()
