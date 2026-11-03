"""Native scene gate for room-candidate-drafts/1.

The draft is a project attachment. The scene must reject that capability, and
preview/cancel must not invent a room boundary. Requires GEOMETRY_TEST_BRIDGE
when the local bridge fingerprint is not already fresh.
"""
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import _bridge  # noqa: E402


class ZeroRoomNativeTests(unittest.TestCase):
    def bridge(self, commands):
        _bridge.find_bridge()
        completed = _bridge.run_once("\n".join(commands) + "\n")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        rows = [json.loads(line) for line in completed.stdout.splitlines() if line.strip()]
        self.assertEqual(len(rows), len(commands), completed.stdout)
        return rows

    def test_capability_cancel_and_confirm(self):
        first = self.bridge([
            "line reset",
            "line boundary 1 outline 0,0 3000,0 3000,2000 0,2000",
            "dump",
            "line requires room-candidate-drafts/1",
            "line preview boundary 2 outline 4000,0 5000,0 5000,1000 4000,1000",
            "line cancel-preview",
            "dump",
        ])
        self.assertTrue(first[0]["ok"] and first[1]["ok"] and first[2]["ok"])
        self.assertFalse(first[3]["ok"])
        self.assertNotIn("room-candidate", first[2]["text"])
        self.assertTrue(first[4]["ok"] and first[5]["ok"] and first[6]["ok"])
        self.assertEqual(first[6]["text"], first[2]["text"])
        second = self.bridge([
            "line reset",
            "line boundary 1 outline 0,0 3000,0 3000,2000 0,2000",
            "line history-begin",
            "line preview boundary 2 outline 4000,0 5000,0 5000,1000 4000,1000",
            "line confirm 1",
            "line history-end",
            "dump",
        ])
        self.assertTrue(all(row["ok"] for row in second[:6]), second)
        self.assertIn("boundary 2", second[6]["text"])
        self.assertNotIn("room-candidate", second[6]["text"])


if __name__ == "__main__":
    unittest.main()
