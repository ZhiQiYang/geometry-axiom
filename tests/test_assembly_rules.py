#!/usr/bin/env python3
"""Core-facing assembly rule checks. Bridge cases run when GEOMETRY_BRIDGE is set."""
import json, os, subprocess, tempfile, unittest

class Contract(unittest.TestCase):
    def test_authoring_is_not_generation(self):
        with open(os.path.join(os.path.dirname(__file__), "..", "geometry-core", "ASSEMBLY-RULES-CONTRACT.md"), encoding="utf-8") as f:
            text = f.read()
        self.assertIn("assembly-rule-authoring/1", text)
        self.assertIn("#25", text)

    def test_bridge_roundtrip(self):
        bridge = os.environ.get("GEOMETRY_BRIDGE")
        if not bridge:
            self.skipTest("GEOMETRY_BRIDGE not set; core binary not built in this environment")
        tx = {"schema": "assembly-transaction/1", "expectedRevision": 0, "operations": [{"op": "publish-rule", "rule": {
            "id": 1, "version": 1, "name": "角材",
            "slots": [{"id": 1, "name": "主支"}, {"id": 2, "name": "副支"}],
            "members": [{"id": 1, "slotId": 1}, {"id": 2, "slotId": 1}, {"id": 3, "slotId": 2}],
            "joints": [{"id": 1, "kind": "end-to-side", "terminatedMember": 3, "targetMember": 1, "end": "start", "side": "+u", "dir": "u"}]}}]}
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            json.dump(tx, f); path = f.name
        proc = subprocess.run([bridge], input=f"reset\nassembly-preview {path}\n", text=True, capture_output=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("assembly-rule-authoring/1", proc.stdout)

if __name__ == "__main__":
    unittest.main()
