"""Identity ledger over a fresh bridge. SkipTest means this machine did not run it."""
import json
import secrets
import tempfile
import unittest
from pathlib import Path

from tests import _bridge

BOUNDARY = "boundary 1 outline 0,0 2000,0 2000,1000 0,1000"


class IdentityLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _bridge.find_bridge()

    def setUp(self):
        self.epoch = secrets.token_hex(16)
        self.other_epoch = secrets.token_hex(16)
        while self.other_epoch == self.epoch:
            self.other_epoch = secrets.token_hex(16)
        self.session = _bridge.BridgeSession(self.bridge)
        self.session.__enter__()
        reset = self.session.command("reset")
        self.assertTrue(reset.get("ok"), reset)
        epoch = self.session.command("identity-epoch " + self.epoch)
        self.assertTrue(epoch.get("ok"), epoch)

    def tearDown(self):
        self.session.__exit__(None, None, None)

    def read(self):
        data = self.session.command("identity-read")
        self.assertTrue(data.get("ok"), data)
        return data

    def test_inactive_dump_has_no_identity_lines(self):
        text = self.session.command("dump")["text"]
        self.assertNotIn("identity ", text)
        self.assertNotIn("identity-ledger", text)
        self.assertFalse(self.read()["active"])

    def test_activate_issues_mark_and_second_activate_is_rejected(self):
        self.assertTrue(self.session.line(BOUNDARY)["ok"])
        first = self.session.line("identity-ledger activate")
        self.assertTrue(first.get("ok"), first)
        issued = self.read()
        self.assertTrue(issued["active"])
        self.assertEqual(len(issued["marks"]), 1)
        self.assertEqual(issued["marks"][0]["kind"], "boundary")
        self.assertEqual(issued["marks"][0]["id"], 1)
        self.assertTrue(issued["marks"][0]["mark"].startswith(self.epoch + ":"))
        second = self.session.line("identity-ledger activate")
        self.assertFalse(second.get("ok"), second)
        self.assertIn("身分帳已啟用", second.get("error", ""))

    def test_deidentified_dump_matches_pre_activation_text(self):
        self.assertTrue(self.session.line(BOUNDARY)["ok"])
        before = self.session.command("dump")["text"]
        self.assertTrue(self.session.line("identity-ledger activate")["ok"])
        full = self.session.command("dump")["text"]
        bare = self.session.command("dump-deidentified")["text"]
        self.assertIn("requires identity-ledger/1", full)
        self.assertIn("identity boundary 1 ", full)
        self.assertEqual(bare, before)
        self.assertNotIn("identity ", bare)

    def test_same_key_rebuild_gets_a_new_mark(self):
        self.assertTrue(self.session.line(BOUNDARY)["ok"])
        self.assertTrue(self.session.line("identity-ledger activate")["ok"])
        first = self.read()["marks"][0]["mark"]
        self.assertTrue(self.session.line("delete boundary 1")["ok"])
        self.assertEqual(self.read()["marks"], [])
        self.assertTrue(self.session.line(BOUNDARY)["ok"])
        second = self.read()["marks"][0]["mark"]
        self.assertNotEqual(first, second)

    def test_preview_and_cancel_do_not_issue_until_confirm(self):
        self.assertTrue(self.session.line("identity-ledger activate")["ok"])
        before = self.read()["nextSerial"]
        preview = self.session.line("preview " + BOUNDARY)
        self.assertTrue(preview.get("ok"), preview)
        self.assertTrue(preview["preview"]["valid"], preview)
        self.assertEqual(self.read()["marks"], [])
        self.assertEqual(self.read()["nextSerial"], before)
        self.assertTrue(self.session.line("cancel-preview")["ok"])
        self.assertEqual(self.read()["nextSerial"], before)
        again = self.session.line("preview " + BOUNDARY)
        token = again["preview"]["token"]
        confirmed = self.session.line("confirm %s" % token)
        self.assertTrue(confirmed.get("ok"), confirmed)
        issued = self.read()
        self.assertEqual(len(issued["marks"]), 1)
        self.assertGreater(issued["nextSerial"], before)

    def test_interactive_identity_line_is_rejected(self):
        rejected = self.session.line("identity boundary 1 %s:1" % self.epoch)
        self.assertFalse(rejected.get("ok"), rejected)
        self.assertIn("互動輸入不得宣告 identity", rejected.get("error", ""))

    def test_scene_roundtrip_restores_marks_without_advancing_serial(self):
        self.assertTrue(self.session.line(BOUNDARY)["ok"])
        self.assertTrue(self.session.line("identity-ledger activate")["ok"])
        text = self.session.command("dump")["text"]
        before = self.read()
        path = Path(tempfile.mkdtemp()) / "identity.scene"
        path.write_bytes(text.encode("utf-8"))
        try:
            loaded = self.session.command("loadfile " + str(path))
            self.assertTrue(loaded.get("ok"), loaded)
            after = self.read()
            self.assertEqual(after["marks"], before["marks"])
            self.assertEqual(after["nextSerial"], before["nextSerial"])
            self.assertEqual(self.session.command("dump")["text"], text)
        finally:
            path.unlink(missing_ok=True)

    def test_requires_without_identity_lines_rejects_the_file(self):
        self.assertTrue(self.session.line(BOUNDARY)["ok"])
        intact = self.session.command("dump")["text"]
        broken = intact + "requires identity-ledger/1\n"
        path = Path(tempfile.mkdtemp()) / "missing-mark.scene"
        path.write_bytes(broken.encode("utf-8"))
        try:
            loaded = self.session.command("loadfile " + str(path))
            self.assertFalse(loaded.get("ok"), loaded)
            self.assertEqual(self.session.command("dump")["text"], intact)
        finally:
            path.unlink(missing_ok=True)

    def test_line_reset_keeps_ledger_active_and_clears_marks(self):
        self.assertTrue(self.session.line(BOUNDARY)["ok"])
        self.assertTrue(self.session.line("identity-ledger activate")["ok"])
        serial = self.read()["nextSerial"]
        self.assertTrue(self.session.line("reset")["ok"])
        data = self.read()
        self.assertTrue(data["active"])
        self.assertEqual(data["marks"], [])
        self.assertGreaterEqual(data["nextSerial"], serial)
        again = self.session.command("identity-epoch " + self.other_epoch)
        self.assertTrue(again.get("ok"), again)

    def test_bridge_reset_is_replacement_and_does_not_rewind_serial(self):
        self.assertTrue(self.session.line(BOUNDARY)["ok"])
        self.assertTrue(self.session.line("identity-ledger activate")["ok"])
        serial = self.read()["nextSerial"]
        replaced = self.session.command("reset")
        self.assertTrue(replaced.get("ok"), replaced)
        data = self.read()
        self.assertFalse(data["active"])
        self.assertEqual(data["marks"], [])
        self.assertEqual(data["nextSerial"], serial)

    def test_epoch_already_in_marks_is_rejected_and_another_epoch_succeeds(self):
        self.assertTrue(self.session.line(BOUNDARY)["ok"])
        self.assertTrue(self.session.line("identity-ledger activate")["ok"])
        rejected = self.session.command("identity-epoch " + self.epoch)
        self.assertFalse(rejected.get("ok"), rejected)
        self.assertIn("配號區段已出現在目前記號", rejected.get("error", ""))
        accepted = self.session.command("identity-epoch " + self.other_epoch)
        self.assertTrue(accepted.get("ok"), accepted)

    def test_undo_activate_restores_inactive_dump_text(self):
        self.assertTrue(self.session.line(BOUNDARY)["ok"])
        before = self.session.command("dump")["text"]
        self.assertTrue(self.session.line("identity-ledger activate")["ok"])
        serial = self.read()["nextSerial"]
        self.assertTrue(self.session.line("undo")["ok"])
        self.assertEqual(self.session.command("dump")["text"], before)
        data = self.read()
        self.assertFalse(data["active"])
        self.assertEqual(data["nextSerial"], serial)

    def test_activation_without_epoch_keeps_original_diagnostic_and_state(self):
        # The ordinary fixture sets an epoch; this independent process must not.
        with _bridge.BridgeSession(self.bridge) as fresh:
            self.assertTrue(fresh.command("reset")["ok"])
            self.assertTrue(fresh.line(BOUNDARY)["ok"])
            before = fresh.command("identity-read")
            self.assertTrue(before["ok"], before)
            self.assertFalse(before["active"])
            self.assertFalse(before["epochSet"])
            world = fresh.command("dump")["text"]
            self.assertIn(BOUNDARY, world)
            rejected = fresh.line("identity-ledger activate")
            self.assertFalse(rejected.get("ok"), rejected)
            self.assertIn("未設定配號區段", rejected.get("error", ""))
            self.assertEqual(fresh.command("identity-read"), before)
            self.assertEqual(fresh.command("dump")["text"], world)

    def test_active_same_boundary_noop_keeps_marks_serial_and_history(self):
        self.assertTrue(self.session.line(BOUNDARY)["ok"])
        inactive = self.session.command("dump")["text"]
        self.assertTrue(self.session.line("identity-ledger activate")["ok"])
        before = self.read()
        world = self.session.command("dump")["text"]
        unchanged = self.session.line(BOUNDARY)
        self.assertTrue(unchanged.get("ok"), unchanged)
        self.assertEqual(self.read(), before)
        self.assertEqual(self.session.command("dump")["text"], world)
        # A no-op history entry would consume this undo and leave activation on.
        self.assertTrue(self.session.line("undo")["ok"])
        self.assertEqual(self.session.command("dump")["text"], inactive)
        after = self.read()
        self.assertFalse(after["active"])
        self.assertEqual(after["marks"], [])
        self.assertEqual(after["nextSerial"], before["nextSerial"])

    def test_active_stale_preview_cannot_publish_or_consume_serial(self):
        self.assertTrue(self.session.line("identity-ledger activate")["ok"])
        before = self.read()
        preview = self.session.line("preview " + BOUNDARY)
        self.assertTrue(preview.get("ok"), preview)
        self.assertTrue(preview["preview"]["valid"], preview)
        self.assertEqual(self.read(), before)
        token = preview["preview"]["token"]
        edited = self.session.line("spec identity_unrelated 7")
        self.assertTrue(edited.get("ok"), edited)
        world = self.session.command("dump")["text"]
        self.assertIn("spec identity_unrelated 7", world)
        before_confirm = self.read()
        self.assertEqual(before_confirm, before)
        rejected = self.session.line("confirm %s" % token)
        self.assertFalse(rejected.get("ok"), rejected)
        self.assertIn("stale", rejected.get("error", "").lower())
        self.assertEqual(self.session.command("dump")["text"], world)
        self.assertEqual(self.read(), before_confirm)

    def test_active_engineering_batch_allocates_once_only_on_confirm(self):
        self.assertTrue(self.session.line("identity-ledger activate")["ok"])
        before = self.read()
        world = self.session.command("dump")["text"]
        # Two independently declared cards each add one card and one field key.
        operations = [{"op": "put-parameter", "value": {
            "id": card, "name": "card-%s" % card, "fields": [
                {"id": 1, "name": "width", "type": "dimension", "input": value}
            ]}} for card, value in ((7, "20"), (8, "30"))]
        with tempfile.TemporaryDirectory(prefix="identity-engineering-") as directory:
            path = Path(directory) / "request.json"

            def preview():
                engineering = self.session.command("engineering-read")
                self.assertTrue(engineering.get("ok"), engineering)
                request = {"schema": "engineering-transaction/1",
                           "expectedRevision": engineering["revision"], "operations": operations}
                path.write_bytes(json.dumps(request, ensure_ascii=False).encode("utf-8"))
                result = self.session.command("engineering-preview " + str(path))
                self.assertTrue(result.get("ok"), result)
                self.assertTrue(result["preview"]["valid"], result)
                return result["preview"]["token"]

            cancelled_token = preview()
            self.assertEqual(self.read(), before)
            self.assertEqual(self.session.command("dump")["text"], world)
            cancelled = self.session.command("engineering-cancel %s" % cancelled_token)
            self.assertTrue(cancelled.get("cancelled"), cancelled)
            self.assertFalse(self.session.command("engineering-confirm %s" % cancelled_token)["ok"])
            self.assertEqual(self.read(), before)
            self.assertEqual(self.session.command("dump")["text"], world)
            token = preview()
            self.assertEqual(self.read(), before)
            self.assertEqual(self.session.command("dump")["text"], world)
            confirmed = self.session.command("engineering-confirm %s" % token)
            self.assertTrue(confirmed.get("ok"), confirmed)
            self.assertTrue(confirmed["history_changed"], confirmed)
            after = self.read()
            self.assertEqual(after["nextSerial"], before["nextSerial"] + 4)
            self.assertEqual([(mark["kind"], mark["id"], mark.get("fieldId")) for mark in after["marks"]],
                             [("parameter", 7, None), ("parameter", 8, None),
                              ("parameter-field", 7, 1), ("parameter-field", 8, 1)])
            self.assertEqual([mark["mark"] for mark in after["marks"]],
                             [self.epoch + ":%s" % serial for serial in range(before["nextSerial"], after["nextSerial"])])
            committed = self.session.command("dump")["text"]
            self.assertNotEqual(committed, world)
            self.assertFalse(self.session.command("engineering-confirm %s" % token)["ok"])
            self.assertEqual(self.session.command("dump")["text"], committed)
            self.assertEqual(self.read(), after)
            self.assertTrue(self.session.line("undo")["ok"])
            self.assertEqual(self.session.command("dump")["text"], world)
            undone = self.read()
            self.assertTrue(undone["active"])
            self.assertEqual(undone["marks"], before["marks"])
            self.assertEqual(undone["nextSerial"], after["nextSerial"])
            self.assertTrue(self.session.line("redo")["ok"])
            self.assertEqual(self.session.command("dump")["text"], committed)
            self.assertEqual(self.read(), after)


if __name__ == "__main__":
    unittest.main()
