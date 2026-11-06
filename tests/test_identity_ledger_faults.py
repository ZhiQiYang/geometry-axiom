"""L20/P-053 faults in the actual native World, validator and process counter."""
import os
from pathlib import Path
import secrets
import tempfile
import unittest

from tests import _bridge, _identity_fault_bridge

BOUNDARY = "boundary 1 outline 0,0 4000,0 4000,3000 0,3000"


class IdentityLedgerFaults(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory(prefix="r09a-fault-build-")
        cls.addClassCleanup(cls.directory.cleanup)
        cls.binary = os.environ.get("GEOMETRY_IDENTITY_FAULT_BRIDGE") or _identity_fault_bridge.build(cls.directory.name)

    def setUp(self):
        self.bridge = _bridge.BridgeSession(self.binary)
        self.addCleanup(self.bridge.stop)
        self.epoch = secrets.token_hex(16)
        for command in ("reset", "identity-epoch " + self.epoch, "line " + BOUNDARY, "line identity-ledger activate"):
            self.ok(command)

    def ok(self, command):
        result = self.bridge.command(command)
        self.assertTrue(result.get("ok"), (command, result))
        return result

    def state(self):
        return self.ok("dump")["text"], self.ok("identity-read")

    def test_L20_incomplete_world_refuses_full_dump_but_can_export_and_undo(self):
        before = self.state()
        self.ok("line timber 7 27 33 role primary")
        full = self.ok("dump")["text"]
        plain = self.ok("dump-deidentified")["text"]
        self.ok("__identity_drop_last")
        broken = self.bridge.command("dump")
        self.assertFalse(broken["ok"], "L20_FULL_DUMP_REJECTS_INCOMPLETE_LEDGER")
        self.assertIn("I70", broken["error"])
        exported = self.ok("dump-deidentified")
        self.assertEqual(exported["text"], plain)
        self.assertEqual(exported["diagnostic"], "身分帳不完整，此輸出不能還原記號")
        self.assertNotEqual(full, plain)
        self.ok("line undo")
        restored = self.state()
        self.assertEqual(restored[0], before[0], "L20_UNDO_RESTORES_COMPLETE_WORLD")
        self.assertEqual(restored[1]["marks"], before[1]["marks"])
        self.assertEqual(restored[1]["nextSerial"], 3)

    def test_P053_capacity_checks_whole_candidate_before_consuming_last_serial(self):
        maximum = 2**64 - 1
        self.ok("__identity_counter " + str(maximum))
        before = self.state()
        preview = self.ok("line preview surface 2 origin 0 0 0 u +x v +y outline 0,0 100,0 100,100 0,100")["preview"]
        self.assertTrue(preview["valid"], preview)
        result = self.bridge.command("line confirm " + str(preview["token"]))
        self.assertFalse(result["ok"], "P053_CAPACITY_REJECTS_WHOLE_CANDIDATE")
        self.assertIn("I33", result["error"])
        self.assertEqual(self.state(), before, "P053_FAILED_CAPACITY_CONSUMES_NOTHING")
        self.ok("line timber 7 27 33 role primary")
        ledger = self.ok("identity-read")
        self.assertEqual(ledger["marks"][-1]["mark"], self.epoch + ":" + str(maximum))
        self.assertEqual(ledger["nextSerial"], 0)
        exhausted = self.bridge.command("line timber 8 27 33 role primary")
        self.assertFalse(exhausted["ok"])
        self.assertIn("I33", exhausted["error"])
        self.assertEqual(self.ok("identity-read"), ledger)

    def test_P053_failed_settlement_after_temporary_allocation_consumes_nothing(self):
        self.ok("__identity_counter 41")
        before = self.state()
        self.ok("__identity_fail_settlement")
        result = self.bridge.command("line surface 2 origin 0 0 0 u +x v +y outline 0,0 100,0 100,100 0,100")
        self.assertFalse(result["ok"], "P053_SETTLEMENT_REJECTS")
        self.assertIn("I70", result["error"])
        self.assertEqual(self.state(), before, "P053_TEMPORARY_SERIALS_ARE_NOT_COMMITTED")
        self.ok("line timber 7 27 33 role primary")
        self.assertEqual(self.ok("identity-read")["marks"][-1]["mark"], self.epoch + ":41")

    def test_P053_group_failure_preserves_only_previously_committed_serials(self):
        self.ok("__identity_counter 41")
        before = self.state()
        self.ok("line history-begin")
        self.ok("line timber 7 27 33 role primary")
        self.assertEqual(self.ok("identity-read")["marks"][-1]["mark"], self.epoch + ":41")
        self.ok("__identity_fail_settlement")
        result = self.bridge.command("line timber 8 27 33 role primary")
        self.assertFalse(result["ok"], "P053_GROUP_SETTLEMENT_REJECTS")
        self.assertIn("I70", result["error"])
        after = self.state()
        self.assertEqual(after[0], before[0], "P053_GROUP_RESTORES_WORLD")
        self.assertEqual(after[1]["marks"], before[1]["marks"])
        self.assertEqual(after[1]["nextSerial"], 42, "P053_GROUP_KEEPS_ONLY_COMMITTED_HIGH_WATER")
        self.ok("line timber 9 27 33 role primary")
        self.assertEqual(self.ok("identity-read")["marks"][-1]["mark"], self.epoch + ":42")


if __name__ == "__main__":
    unittest.main()
