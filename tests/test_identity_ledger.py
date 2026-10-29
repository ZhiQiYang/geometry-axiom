"""Identity ledger over a fresh bridge. SkipTest means this machine did not run it."""
import tempfile
import unittest
from pathlib import Path

from tests import _bridge

EPOCH = "0123456789abcdef0123456789abcdef"
OTHER = "fedcba9876543210fedcba9876543210"
BOUNDARY = "boundary 1 outline 0,0 2000,0 2000,1000 0,1000"


class IdentityLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _bridge.find_bridge()

    def setUp(self):
        self.session = _bridge.BridgeSession(self.bridge)
        self.session.__enter__()
        reset = self.session.command("reset")
        self.assertTrue(reset.get("ok"), reset)
        epoch = self.session.command("identity-epoch " + EPOCH)
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
        self.assertTrue(issued["marks"][0]["mark"].startswith(EPOCH + ":"))
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
        rejected = self.session.line("identity boundary 1 %s:1" % EPOCH)
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
        again = self.session.command("identity-epoch " + EPOCH)
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
        rejected = self.session.command("identity-epoch " + EPOCH)
        self.assertFalse(rejected.get("ok"), rejected)
        self.assertIn("配號區段已出現在目前記號", rejected.get("error", ""))
        accepted = self.session.command("identity-epoch " + OTHER)
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


if __name__ == "__main__":
    unittest.main()
