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


# Keep the independent 405f8c5e fixture byte-for-byte. The exact additive
# contracts below come from R06 F4 (7a876ed6: assembly_bridge.inc,
# engineering_bridge.inc and test_assembly_bay_repeat.LIMITS) and R08 #359.
# Do not derive expected fields, values, or ordering from the bridge under test.
R06_CAPABILITY = "assembly-bay-repeat/1"
R06_LIMITS = {
    "instances": 16, "ownedTimbers": 48, "worldTimbers": 64,
    "instanceRecordBytes": 8191, "bayPrimaries": 12,
    "baySecondaryLines": 24, "bayOmit": 24,
}
LATER_ENGINEERING_CAPABILITIES = (
    "definition-import/1",  # R08 #359: definition import across projects
)


def with_later_capabilities(original):
    expected = json.loads(json.dumps(original))
    capabilities = expected["engineering-read"]["state"]["capabilities"]
    capabilities.insert(capabilities.index("assembly-timber-generation/1") + 1,
                        R06_CAPABILITY)
    capabilities.extend(LATER_ENGINEERING_CAPABILITIES)
    for parent, key in ((expected["references"], "assembly"),
                        (expected["engineering-read"]["state"], "assembly"),
                        (expected["assembly-read"], "state")):
        assembly = parent[key]
        expanded = {}
        for field, value in assembly.items():
            expanded[field] = value
            if field == "capabilities":
                value.append(R06_CAPABILITY)
                expanded["limits"] = dict(R06_LIMITS)
        parent[key] = expanded
    return expected


def project_identity_capability(case, value):
    """I72 declares one new capability; preserve the external K1 baseline.

    Extract only this reviewed extension at its fixed position. The caller
    still compares every remaining field, value and JSON key order exactly.
    """
    projected = json.loads(json.dumps(value))
    capabilities = projected["engineering-read"]["state"]["capabilities"]
    case.assertEqual(1, capabilities.count("identity-ledger/1"),
                     "K1_R09A_CAPABILITY_EXACTLY_ONCE")
    at = capabilities.index("identity-ledger/1")
    case.assertEqual(len(capabilities) - len(LATER_ENGINEERING_CAPABILITIES) - 1, at,
                     "K1_R09A_CAPABILITY_BEFORE_NAMED_LATER_EXTENSIONS")
    case.assertEqual(list(LATER_ENGINEERING_CAPABILITIES), capabilities[at + 1:],
                     "K1_R09A_LATER_EXTENSION_ORDER")
    del capabilities[at]
    return projected


def project_panel_fill_reader(case, value):
    """Check the scoped R02 reader before comparing the independent K1 reply.

    UI-1 adds this definition-reader descriptor, not the full panel-fill/1
    product capability. Its four fields, values and insertion point are fixed
    by the reviewed UI-1 wire contract; no value is taken from the reply being
    tested. Every other field and its order still reaches the original check.
    """
    projected = json.loads(json.dumps(value))
    state = projected["engineering-read"]["state"]
    expected_reader = {
        "schema": "panel-fill-definition-reader/1",
        "capability": "panel-fill/1",
        "supportedRecords": ["finish-surface", "panel-fill", "derived-placement"],
        "complete": False,
    }
    case.assertIn("panel_fill_reader", state, "K1_PF_READER_PRESENT")
    case.assertEqual(json.dumps(expected_reader, ensure_ascii=False, separators=(",", ":")),
                     json.dumps(state["panel_fill_reader"], ensure_ascii=False, separators=(",", ":")),
                     "K1_PF_READER_EXACT_CONTRACT")
    keys = list(state)
    at = keys.index("panel_fill_reader")
    case.assertEqual(["native_capabilities", "panel_fill_reader", "specs"], keys[at - 1:at + 2],
                     "K1_PF_READER_INSERTION_ORDER")
    del state["panel_fill_reader"]
    return projected


def project_r14_native_capability(case, value):
    """Project exactly the approved native-only addition; keep the old oracle."""
    projected = json.loads(json.dumps(value))
    capabilities = projected["engineering-read"]["state"]["native_capabilities"]
    case.assertEqual(1, capabilities.count("grid-subdivision-native/2"),
                     "K1_R14_NATIVE_CAPABILITY_EXACTLY_ONCE")
    at = capabilities.index("grid-subdivision-native/2")
    case.assertEqual(len(capabilities) - 1, at, "K1_R14_NATIVE_CAPABILITY_FIXED_LAST")
    del capabilities[at]
    return projected


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
        original = with_later_capabilities(json.loads(baseline.read_text(encoding="utf-8")))
        expected_json = json.dumps(original, ensure_ascii=False, separators=(",", ":"))

        def compare(value):
            projected = project_panel_fill_reader(self, value)
            projected = project_identity_capability(self, without_terminal(projected))
            projected = project_r14_native_capability(self, projected)
            self.assertEqual(expected_json,
                             json.dumps(projected, ensure_ascii=False, separators=(",", ":")),
                             "K1-a: non-terminal fields/order changed relative to the independently built baseline")

        unchanged = json.dumps(replies, ensure_ascii=False, separators=(",", ":"))
        compare(replies)
        self.assertEqual(unchanged, json.dumps(replies, ensure_ascii=False, separators=(",", ":")),
                         "K1_R09A_PROJECTION_IS_READONLY")
        # The extension must not hide a missing, extra, moved capability, an
        # unrelated field change, or the original baseline's JSON key order.
        for fault in ("missing", "duplicate", "moved", "unknown", "legacy-order", "material", "reply-order"):
            with self.subTest(identity_projection_negative=fault):
                probe = json.loads(json.dumps(replies))
                state = probe["engineering-read"]["state"]
                caps = state["capabilities"]
                at = caps.index("identity-ledger/1")
                if fault == "missing":
                    del caps[at]
                elif fault == "duplicate":
                    caps.insert(at, "identity-ledger/1")
                elif fault == "moved":
                    caps[0], caps[at] = caps[at], caps[0]
                elif fault == "unknown":
                    caps.append("unreviewed-capability/1")
                elif fault == "legacy-order":
                    caps[0], caps[1] = caps[1], caps[0]
                elif fault == "material":
                    state["materials"][0]["name"] += "-changed"
                else:
                    first = next(iter(probe["references"]))
                    probe["references"][first] = probe["references"].pop(first)
                with self.assertRaises(AssertionError, msg="K1_R09A_NEGATIVE_" + fault):
                    compare(probe)

        # The additive reader cannot conceal a wrong schema, an unsupported
        # record, a full-product claim, or an unrelated legacy/order change.
        for fault in ("missing", "schema", "capability", "records", "complete", "complete-type",
                      "extra-field", "terminal-extra", "reader-key-order", "moved", "full-capability"):
            with self.subTest(panel_fill_reader_negative=fault):
                probe = json.loads(json.dumps(replies))
                state = probe["engineering-read"]["state"]
                reader = state["panel_fill_reader"]
                if fault == "missing":
                    del state["panel_fill_reader"]
                elif fault == "schema":
                    reader["schema"] = "panel-fill-definition-reader/2"
                elif fault == "capability":
                    reader["capability"] = "panel-fill/2"
                elif fault == "records":
                    reader["supportedRecords"].append("unsupported-record")
                elif fault == "complete":
                    reader["complete"] = True
                elif fault == "complete-type":
                    reader["complete"] = 0
                elif fault == "extra-field":
                    reader["extra"] = True
                elif fault == "terminal-extra":
                    reader["terminal"] = {"kind": "literal"}
                elif fault == "reader-key-order":
                    reader["schema"] = reader.pop("schema")
                elif fault == "moved":
                    state["panel_fill_reader"] = state.pop("panel_fill_reader")
                else:
                    state["capabilities"].append("panel-fill/1")
                with self.assertRaises(AssertionError, msg="K1_PF_READER_NEGATIVE_" + fault):
                    compare(probe)

        for fault in ("missing", "duplicate", "moved", "unknown"):
            with self.subTest(r14_native_projection_negative=fault):
                probe = json.loads(json.dumps(replies))
                caps = probe["engineering-read"]["state"]["native_capabilities"]
                at = caps.index("grid-subdivision-native/2")
                if fault == "missing":
                    del caps[at]
                elif fault == "duplicate":
                    caps.append("grid-subdivision-native/2")
                elif fault == "moved":
                    caps[0], caps[at] = caps[at], caps[0]
                else:
                    caps.insert(at, "unreviewed-native-capability/1")
                with self.assertRaises(AssertionError, msg="K1_R14_NATIVE_NEGATIVE_" + fault):
                    compare(probe)


if __name__ == "__main__":
    unittest.main(verbosity=2)
