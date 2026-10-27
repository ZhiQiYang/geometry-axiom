"""K1-a / D49, I59(d): typed leaves from the native D28 resolver (N1-N5)."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests import _bridge, test_engineering_core as eng, test_assembly_rules as asm


def without_terminal(value):
    if isinstance(value, dict):
        return {key: without_terminal(item) for key, item in value.items() if key != "terminal"}
    if isinstance(value, list):
        return [without_terminal(item) for item in value]
    return value


class EngineeringTerminal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exe = os.environ.get("GEOMETRY_TERMINAL_HARNESS") or _bridge.find_bridge()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="geometry-terminal-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.session = _bridge.BridgeSession(self.exe)
        self.addCleanup(self.session.stop)
        self.assertTrue(self.command("reset")["ok"])
        self.assertTrue(self.command("line surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000")["ok"])

    command = eng.EngineeringCore.command
    read = eng.EngineeringCore.read
    request = eng.EngineeringCore.request
    apply = eng.EngineeringCore.apply
    seed = eng.EngineeringCore.seed

    def source(self, sources, field="panel"):
        return next(s for s in sources if s["target"] == {"kind": "grid", "id": 1, "axis": "u", "field": field})

    def check_terminal(self, source, expected):
        self.assertIn("terminal", source, "N1-N5: native serializer omitted the typed terminal field")
        self.assertEqual(expected, source["terminal"], "D49: terminal must be the resolved leaf, including its exact material fingerprint")

    def test_n1_literal_spec_parameter_and_material_leaves(self):
        self.apply(self.seed())
        self.assertTrue(self.command("line spec panelWidth 915")["ok"])
        parameter = {"id": 1, "name": "尺寸", "fields": [{"id": 1, "name": "寬", "type": "dimension", "input": "915"}]}
        self.apply([{"op": "put-parameter", "value": parameter}])
        fp = self.read()["state"]["materials"][0]["fingerprint"]
        cases = [({"kind": "literal", "value": 915}, {"kind": "literal"}),
                 ({"kind": "spec", "name": "panelWidth"}, {"kind": "spec"}),
                 ({"kind": "parameter", "parameterId": 1, "fieldId": 1}, {"kind": "parameter"}),
                 ({"kind": "material", "id": "panel-a", "version": 1, "field": "width"},
                  {"kind": "material", "id": "panel-a", "version": 1, "fingerprint": fp})]
        target = {"kind": "grid", "id": 1, "axis": "u", "field": "panel"}
        for definition, expected in cases:
            with self.subTest(leaf=definition["kind"]):
                self.apply([{"op": "set-source", "target": target, "source": definition}])
                source = self.source(self.command("references")["engineeringSources"])
                self.check_terminal(source, expected)
                self.assertEqual(915, source["effective"])

    def test_n2_application_material_and_gap_literal(self):
        preview, _ = self.apply(self.seed())
        fp = self.read()["state"]["materials"][0]["fingerprint"]
        expected = {"kind": "material", "id": "panel-a", "version": 1, "fingerprint": fp}
        self.check_terminal(self.source(self.command("references")["engineeringSources"]), expected)
        self.check_terminal(self.source(preview["preview"]["after"]["sources"]), expected)
        self.check_terminal(self.source(self.read()["state"]["sources"], "gap"), {"kind": "literal"})

    def test_n3_face_and_object_overrides_replace_the_terminal(self):
        ops = self.seed()
        ops[2]["value"]["overrides"] = {"gap": {"kind": "literal", "value": 3}}
        self.apply(ops)
        self.check_terminal(self.source(self.read()["state"]["sources"], "gap"), {"kind": "literal"})
        target = {"kind": "grid", "id": 1, "axis": "u", "field": "panel"}
        self.apply([{"op": "set-override", "target": target, "value": {"kind": "literal", "value": 915}}])
        self.check_terminal(self.source(self.command("references")["engineeringSources"]), {"kind": "literal"})
        self.apply([{"op": "set-override", "target": target, "value": None}])
        self.assertEqual("material", self.source(self.read()["state"]["sources"])["terminal"]["kind"])

    def test_n3_timber_application_face_override(self):
        self.assertTrue(self.command("default")["ok"])
        ops = [{"op": "publish-material", "value": {"id": "wood-a", "version": 1, "kind": "timber", "name": "角材", "A": 27, "B": 33}},
               {"op": "publish-method", "value": {"id": "framing", "version": 1, "name": "骨架", "roles": {"boundary": {"id": "wood-a", "version": 1}}}},
               {"op": "put-application", "value": {"id": "frame-face", "placement_id": 1, "method": {"id": "framing", "version": 1}, "overrides": {"boundary.A": {"kind": "literal", "value": 27}}}},
               {"op": "bind-timber", "id": 1, "application": "frame-face", "slot": "boundary"}]
        self.apply(ops)
        sources = self.command("references")["engineeringSources"]
        source = next(s for s in sources if s["target"] == {"kind": "timber", "id": 1, "field": "A"})
        self.check_terminal(source, {"kind": "literal"})
        source = next(s for s in sources if s["target"] == {"kind": "timber", "id": 1, "field": "B"})
        self.assertEqual("material", source["terminal"]["kind"], "N3: face override must not replace the other axis")

    def test_n4_owned_slot_effective_material_leaf(self):
        material = {"id": "cedar", "version": 1, "kind": "timber", "name": "杉木", "A": 27, "B": 33}
        binding = asm.binding()
        for slot in binding["slots"]:
            for axis in ("A", "B"):
                slot[axis] = {"kind": "material", "id": "cedar", "version": 1, "field": axis}
        operations = [{"op": "publish-material", "value": material},
                      {"op": "publish-rule", "value": asm.rule()}, {"op": "put-binding", "value": binding}]
        path = self.directory / "owned.json"
        path.write_text(json.dumps({"schema": "assembly-transaction/1", "expectedRevision": self.read()["revision"],
                                    "operations": operations}, ensure_ascii=False), encoding="utf-8")
        preview = self.command("assembly-preview " + str(path))["preview"]
        self.assertTrue(preview["valid"], preview)
        done = self.command("assembly-confirm " + str(preview["token"]))
        self.assertTrue(done["ok"], done)
        fp = self.read()["state"]["materials"][0]["fingerprint"]
        expected = {"kind": "material", "id": "cedar", "version": 1, "fingerprint": fp}
        for result in (self.command("assembly-read")["state"], self.read()["state"]["assembly"], self.command("references")["assembly"]):
            for slot in result["bindings"][0]["effective"]:
                for axis in ("A", "B"):
                    self.check_terminal(slot[axis], expected)
        self.assertEqual(done["revision"], self.read()["revision"], "N4: reading terminals must not advance history")

    def test_n5_invalid_preview_returns_null_without_mutating_world(self):
        self.apply(self.seed())
        before = self.command("dump"), self.read()["revision"]
        target = {"kind": "grid", "id": 1, "axis": "u", "field": "panel"}
        result = self.request([{"op": "set-source", "target": target, "source": {"kind": "spec", "name": "missing"}}])
        self.assertFalse(result["preview"]["valid"])
        source = self.source(result["preview"]["after"]["sources"])
        self.check_terminal(source, None)
        self.assertIsNone(source["effective"])
        self.assertEqual(before, (self.command("dump"), self.read()["revision"]))

    def test_readonly_and_external_baseline_replies(self):
        self.apply(self.seed())
        before = self.command("dump"), self.read()["revision"]
        replies = {cmd: self.command(cmd) for cmd in ("references", "engineering-read", "assembly-read")}
        self.assertEqual(replies["references"]["engineeringSources"], replies["engineering-read"]["state"]["sources"])
        self.assertEqual(before, (self.command("dump"), self.read()["revision"]))
        baseline = Path(os.environ.get("GEOMETRY_TERMINAL_BASELINE", ROOT / "tests/fixtures/k1_terminal_legacy_replies.json"))
        original = json.loads(baseline.read_text(encoding="utf-8"))
        self.assertEqual(json.dumps(original, ensure_ascii=False, separators=(",", ":")),
                         json.dumps(without_terminal(replies), ensure_ascii=False, separators=(",", ":")),
                         "K1-a: non-terminal fields/order changed relative to the independently built baseline")


if __name__ == "__main__":
    unittest.main(verbosity=2)
