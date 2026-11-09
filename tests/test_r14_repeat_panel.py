"""R14 native acceptance for the approved REPEAT_PANEL /2 clauses.

Written on 83d4ca22e3129d64bbb3b8dd024e950250992eee plus the approved P patch
(axiom blob c017aae31e925a166c91b2c5d2d13f9e96c38f5a); landed on main 6fd9e8b1, whose axiom is the approved
R17 text plus the same P (blob b3472f2d2b481f7c889945a092fb9b3e911dc027).
Approval: issue #57 comment 6688023475; native mutation specification:
comment 6677738068. These tests cover the native slice, not the later UI.

    python tests/test_r14_repeat_panel.py -v

All expected coordinates below are literal fixture values. Only the
repository's freshness-checked public bridge transport is shared.
The pre-implementation /1 baseline must fail before the /2 product is applied.
"""
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import _bridge  # noqa: E402

DATA = json.loads((ROOT / "tests/fixtures/r14_repeat_panel_candidate.json").read_text(encoding="utf-8"))
CASES = {case["id"]: case for case in DATA["vectors"]}


def reason(result):
    values = (result.get("preview") or {}).get("violations") or []
    return "\n".join(str(row.get("actual") or row.get("message") or "") for row in values) or str(result.get("error", ""))


class R14RepeatPanelNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.executable = _bridge.find_bridge()

    def setUp(self):
        self.session = _bridge.BridgeSession(self.executable)
        self.addCleanup(self.session.stop)
        directory = tempfile.TemporaryDirectory(prefix="r14-candidate-")
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.commit("reset")

    def command(self, value):
        return self.session.command(value)

    def commit(self, value):
        result = self.command("line " + value)
        if "preview" in result:
            self.assertTrue(result["preview"]["valid"], ("R14_CANDIDATE_ACCEPT", value, reason(result)))
            result = self.command("line confirm " + str(result["preview"]["token"]))
        self.assertTrue(result["ok"], ("R14_CANDIDATE_ACCEPT", value, reason(result)))
        return result

    @staticmethod
    def source(u="repeat-panel 915 gap 2 from 0", v="repeat 0 400", prefix=""):
        return f"grid-system 0 name-hex 523134 main-along none {prefix}u {u} v {v}"

    @staticmethod
    def rule(divisions=(7, 2), key=None, name="R14", selector="all-cells"):
        intent = "create" if key is None else f"key {key}"
        return (f"grid-source-rule 0 {intent} name-hex {name.encode().hex()} "
                f"selector {selector} divide {divisions[0]} {divisions[1]}")

    def dump(self):
        result = self.command("dump")
        self.assertTrue(result["ok"], result)
        return result["text"]

    def snapshot(self):
        return self.dump(), self.command("objects"), self.command("references")

    def owner(self):
        return next(row for row in self.command("objects")["gridSystems"] if row["id"] == 0)

    def capabilities(self):
        result = self.command("engineering-read")
        self.assertTrue(result["ok"], result)
        return result["state"]["required_capabilities"]

    def revision(self):
        result = self.command("engineering-read")
        self.assertTrue(result["ok"], result)
        return result["revision"]

    def reject(self, value, expected):
        before = self.snapshot()
        revision = self.revision()
        result = self.command("line " + value)
        self.assertFalse(result.get("ok") and result.get("preview", {}).get("valid", True),
                         ("R14_REJECTION_REQUIRED", value, reason(result)))
        if "preview" in result:
            self.assertFalse(result["preview"]["valid"], ("R14_REJECTION_REQUIRED", value, reason(result)))
            self.assertFalse(self.command("line confirm " + str(result["preview"]["token"]))["ok"])
        self.assertIn(expected.lower(), reason(result).lower(), ("R14_REJECTION_REASON", value, reason(result)))
        self.assertEqual(before, self.snapshot(), "R14_REJECT_IS_ATOMIC")
        self.assertEqual(revision, self.revision(), "R14_REJECT_REVISION_UNCHANGED")

    def load(self, lines):
        path = self.directory / "candidate.scene"
        path.write_text(lines if isinstance(lines, str) else "\n".join(lines) + "\n", encoding="utf-8")
        return self.command("loadfile " + str(path))

    def roundtrip(self):
        before = self.snapshot()
        result = self.load(before[0])
        self.assertTrue(result["ok"], result)
        self.assertEqual(before, self.snapshot(), "R14_SCENE_CLOSURE")

    def query(self, case, kind="system", identifier=0, placed=None):
        before = self.snapshot()
        revision = self.revision()
        result = self.command(f"grid-rule-query {kind} {identifier} rule 1 cell {' '.join(case['cell'])}")
        self.assertTrue(result["ok"], ("R14_NATIVE_QUERY", case["id"], result))
        self.assertEqual(before, self.snapshot(), "R14_QUERY_READONLY")
        self.assertEqual(revision, self.revision(), "R14_QUERY_REVISION_UNCHANGED")
        self.assertEqual((0, 1, case["cell"], case["bounds"]),
                         (result["systemId"], result["ruleKey"], result["cell"], result["bounds"]), case["id"])
        self.assertTrue(all(isinstance(value, str) for value in result["cell"]), "R14_SIGNED_STRING")
        self.assertEqual(sum(case["divisions"]) - 2, len(result["lines"]), "R14_NO_PARENT_EDGE_DUPLICATES")
        for axis in ("u", "v"):
            rows = sorted((row for row in result["lines"] if row["axis"] == axis), key=lambda row: row["innerIndex"])
            self.assertEqual(list(range(len(case["coordinates"][axis]))), [row["innerIndex"] for row in rows], "R14_INNER_INDEX")
            self.assertEqual(case["coordinates"][axis], [row["coordinate"] for row in rows], case["id"] + "/" + axis)
            for row in rows:
                if placed is None:
                    self.assertIsNone(row["ref"], "R14_UNPLACED_REF_NULL")
                else:
                    self.assertEqual({"kind": "grid-rule-line", "appliedGridId": placed, "systemId": 0,
                                      "ruleKey": 1, "cellI": case["cell"][0], "cellJ": case["cell"][1],
                                      "axis": axis, "innerIndex": row["innerIndex"]}, row["ref"], "R14_FULL_REF_TUPLE")
                expected = ([[row["coordinate"], case["bounds"][1]], [row["coordinate"], case["bounds"][3]]]
                            if axis == "u" else
                            [[case["bounds"][0], row["coordinate"]], [case["bounds"][2], row["coordinate"]]])
                self.assertEqual([sorted(expected)], [sorted(segment) for segment in row["segments"]], "R14_FULL_CELL_SEGMENT")
        return result

    def seed(self, case=None):
        case = case or CASES["panel917-negative"]
        self.commit(self.source(case["u"], case["v"]))
        self.commit(self.rule(case["divisions"]))

    def engineering(self, operations, valid=True):
        before = self.snapshot()
        read = self.command("engineering-read")
        self.assertTrue(read["ok"], read)
        path = self.directory / "request.json"
        path.write_text(json.dumps({"schema": "engineering-transaction/1", "expectedRevision": read["revision"],
                                    "operations": operations}), encoding="utf-8")
        result = self.command("engineering-preview " + str(path))
        self.assertTrue(result["ok"], result)
        self.assertEqual(valid, result["preview"]["valid"], ("R14_ENGINEERING_CANDIDATE", result))
        self.assertEqual(before, self.snapshot(), "R14_ENGINEERING_PREVIEW_READONLY")
        self.assertEqual(read["revision"], self.revision(), "R14_ENGINEERING_PREVIEW_REVISION")
        confirmation = self.command("engineering-confirm " + str(result["preview"]["token"]))
        self.assertEqual(valid, confirmation["ok"], confirmation)
        if not valid:
            self.assertEqual(before, self.snapshot(), "R14_UPSTREAM_REJECT_IS_ATOMIC")
            self.assertEqual(read["revision"], self.revision(), "R14_UPSTREAM_REJECT_REVISION")
        return result

    @staticmethod
    def parameter(panel="915", identifier=10):
        return {"op": "put-parameter", "value": {"id": identifier, "name": "R14 material", "fields": [
            {"id": 3, "name": "panel", "type": "dimension", "input": panel},
            {"id": 8, "name": "step", "type": "dimension", "input": "400"}]}}

    def test_01_literal_mixed_dual_panel_phase_anchor_and_inner_lines(self):
        for case in DATA["vectors"]:
            with self.subTest(case=case["id"]):
                self.commit("reset")
                self.seed(case)
                self.query(case)
                self.assertEqual([], self.command("references")["grids"], "R14_NO_EXPANDED_CHILD_GRIDS")

    def test_02_binding_and_placed_refs_keep_large_signed_cells(self):
        self.seed()
        self.commit("boundary 1 outline 100,200 2100,200 2100,1800 100,1800")
        boundary = self.command("boundary 1")
        self.assertTrue(boundary["ok"], boundary)
        self.commit("grid-binding 0 on-boundary 1 from-system 0 vertex outer 0 geometry-hash "
                    + boundary["geometryFingerprint"] + " cell 9007199254740993 -9007199254740995 anchor 0 1 0 1")
        for case in DATA["binding_vectors"]:
            self.query(case, "binding")
        self.commit("placement 1 on boundary 1 origin 0 0 0 u +x v +y")
        self.commit("grid 10 on 1 from-binding 0")
        for case in DATA["binding_vectors"]:
            self.query(case, "grid", 10, placed=10)
        self.commit("guide 9 1 v gridrule:10:0:1:9007199254740993:-9007199254740995:u:0")
        guide = next(row for row in self.command("references")["guides"] if row["id"] == 9)
        self.assertEqual(231, guide["off"])
        self.assertIn("gridrule:10:0:1:9007199254740993:-9007199254740995:u:0", self.dump())
        self.roundtrip()

    def test_03_unconfigured_upstream_edit_preserves_rule_or_rejects_whole_candidate(self):
        self.seed()
        self.assertEqual([], self.command("references")["grids"])
        before = self.owner()
        self.commit(self.source("repeat-panel 922 gap 2 from 0"))
        self.assertEqual(before["rules"], self.owner()["rules"])
        self.assertEqual(before["nextRuleKey"], self.owner()["nextRuleKey"])
        self.query(CASES["valid-panel922-edit"])
        self.reject(self.source("repeat-panel 922 gap 3 from 0"), "DIVISION_NOT_EXACT")
        self.assertEqual(before["rules"], self.owner()["rules"])

    def test_04_nonintegral_full_pitch_never_rounds_or_allocates_remainder(self):
        for case in DATA["nonintegral"]:
            with self.subTest(case=case["id"]):
                self.commit("reset")
                self.commit(self.source(case["u"], case["v"]))
                self.reject(self.rule(case["divisions"]), case["reason"])
                self.assertEqual([], self.owner()["rules"])
                self.assertEqual(1, self.owner()["nextRuleKey"])

    def test_05_missing_finite_and_d10b_sources_remain_rejected(self):
        for case in DATA["unsupported_sources"]:
            with self.subTest(case=case["id"]):
                self.commit("reset")
                self.commit(self.source(case["u"], case["v"]))
                self.reject(self.rule(case["divisions"]), "SOURCE_KIND")
                self.assertEqual([], self.owner()["rules"])

    def test_06_same_pitch_source_kind_switch_keeps_rules_highwater_and_identity(self):
        self.commit(self.source("repeat 916 917"))
        self.commit(self.rule())
        before = self.owner()
        self.commit(self.source())
        self.assertEqual(before["rules"], self.owner()["rules"], "R14_SOURCE_EDIT_PRESERVES_RULES")
        self.assertEqual(2, self.owner()["nextRuleKey"])
        self.assertIn("u repeat-panel 915 gap 2 from 0", self.dump())
        self.query(CASES["panel917-negative"])
        self.assertIn("grid-subdivision-rules/2", self.capabilities())
        self.commit(self.source("repeat 916 917"))
        self.assertEqual(before["rules"], self.owner()["rules"], "R14_SOURCE_EDIT_PRESERVES_RULES")
        self.assertEqual(2, self.owner()["nextRuleKey"])
        self.assertIn("grid-subdivision-rules/1", self.capabilities())
        self.assertNotIn("grid-subdivision-rules/2", self.capabilities())

    def test_07_v2_scene_roundtrip_missing_or_downgraded_marker_is_atomic(self):
        lines = DATA["scenes"]["panel-rule-v2"]
        result = self.load(lines)
        self.assertTrue(result["ok"], ("R14_LOAD_V2_POSITIVE_CONTROL", reason(result)))
        self.query(CASES["panel917-negative"])
        self.assertIn("requires grid-subdivision-rules/2", self.dump())
        self.assertNotIn("requires grid-subdivision-rules/1", self.dump())
        self.roundtrip()
        for changed in (lines[1:], ["requires grid-subdivision-rules/1"] + lines[1:]):
            before = self.snapshot()
            revision = self.revision()
            pending = self.command("line " + self.rule(key=1, name="pending capability guard"))
            self.assertTrue(pending["preview"]["valid"], pending)
            rejected = self.load(changed)
            self.assertFalse(rejected["ok"], "R14_CAPABILITY_STRIP_OR_DOWNGRADE")
            self.assertIn("capability", reason(rejected).lower(), rejected)
            self.assertEqual(before, self.snapshot(), "R14_LOAD_REFUSAL_PRESERVES_WORLD")
            self.assertEqual(revision, self.revision(), "R14_LOAD_REFUSAL_PRESERVES_REVISION")
            self.commit("confirm " + str(pending["preview"]["token"]))
            self.commit("undo")
            self.assertEqual(before, self.snapshot(), "R14_LOAD_REFUSAL_PRESERVES_PENDING_AND_HISTORY")

    def test_08_replay_encountered_panel_rule_requires_v2_after_source_delete(self):
        lines = DATA["scenes"]["panel-rule-v2"] + ["delete grid-system 0"]
        result = self.load(lines)
        self.assertTrue(result["ok"], ("R14_ENCOUNTERED_POSITIVE_CONTROL", reason(result)))
        self.assertEqual([], self.command("objects")["gridSystems"])
        self.commit(self.source("repeat 0 600"))
        before = self.snapshot()
        for changed in (lines[1:], ["requires grid-subdivision-rules/1"] + lines[1:]):
            revision = self.revision()
            rejected = self.load(changed)
            self.assertFalse(rejected["ok"], "R14_ENCOUNTERED_CAPABILITY_NOT_FINAL_STATE_ONLY")
            self.assertIn("capability", reason(rejected).lower(), rejected)
            self.assertEqual(before, self.snapshot())
            self.assertEqual(revision, self.revision(), "R14_ENCOUNTERED_REFUSAL_PRESERVES_REVISION")

    def test_09_panel_without_rule_or_with_only_highwater_does_not_require_v2(self):
        for name, highwater, required in (("panel-without-rule", 1, False), ("panel-highwater-only-v1", 8, True)):
            with self.subTest(scene=name):
                result = self.load(DATA["scenes"][name])
                self.assertTrue(result["ok"], result)
                self.assertEqual([], self.owner()["rules"])
                self.assertEqual(highwater, self.owner()["nextRuleKey"])
                self.assertNotIn("grid-subdivision-rules/2", self.capabilities())
                self.assertNotIn("requires grid-subdivision-rules/2", self.dump())
                self.assertEqual(required, "grid-subdivision-rules/1" in self.capabilities())
                self.roundtrip()

    def test_10_cancel_create_delete_and_recreate_preserve_allocator(self):
        self.commit(self.source())
        before = self.snapshot()
        revision = self.revision()
        pending = self.command("line " + self.rule())
        self.assertIn("preview", pending, ("R14_RULE_PREVIEW_PRESENT", pending))
        self.assertTrue(pending["preview"]["valid"], ("R14_RULE_PREVIEW_VALID", pending))
        self.assertEqual(before, self.snapshot(), "R14_RULE_PREVIEW_READONLY")
        self.assertEqual(revision, self.revision(), "R14_RULE_PREVIEW_REVISION")
        self.commit("cancel-preview")
        self.assertEqual(before, self.snapshot(), "R14_RULE_CANCEL_READONLY")
        self.assertEqual(revision, self.revision(), "R14_RULE_CANCEL_REVISION")
        self.assertFalse(self.command("line confirm " + str(pending["preview"]["token"]))["ok"])
        self.assertEqual(1, self.owner()["nextRuleKey"])
        self.commit(self.rule())
        self.assertEqual((1, 2), (self.owner()["rules"][0]["ruleKey"], self.owner()["nextRuleKey"]))
        committed = self.snapshot()
        self.commit("undo")
        self.assertEqual(before, self.snapshot(), "R14_UNDO_FULL_RULE_AND_HIGHWATER")
        self.commit("redo")
        self.assertEqual(committed, self.snapshot(), "R14_REDO_FULL_RULE_AND_HIGHWATER")
        self.commit("grid-source-rule 0 delete 1")
        self.assertEqual([], self.owner()["rules"])
        self.assertEqual(2, self.owner()["nextRuleKey"])
        self.assertIn("grid-subdivision-rules/1", self.capabilities())
        self.assertNotIn("grid-subdivision-rules/2", self.capabilities())
        self.roundtrip()
        self.commit(self.rule())
        self.assertEqual((2, 3), (self.owner()["rules"][0]["ruleKey"], self.owner()["nextRuleKey"]))
        self.assertIn("grid-subdivision-rules/2", self.capabilities())

    def test_11_repeat_only_original_geometry_and_minimum_capability_stay_unchanged(self):
        case = DATA["legacy_control"]
        self.seed(case)
        self.query(case)
        self.assertIn("grid-subdivision-rules/1", self.capabilities())
        self.assertNotIn("grid-subdivision-rules/2", self.capabilities())
        self.assertIn("requires grid-subdivision-rules/1", self.dump())
        self.assertNotIn("requires grid-subdivision-rules/2", self.dump())
        self.reject(self.rule((7, 2), key=1), "DIVISION_NOT_EXACT")
        self.reject(self.rule((1, 1), key=1), "DIVISION_RANGE")
        self.roundtrip()

    def test_12_parameter_and_card_sources_resolve_before_exactness_and_are_not_flattened(self):
        for mode in ("parameter", "card"):
            with self.subTest(mode=mode):
                self.commit("reset")
                self.engineering([self.parameter()])
                definition = (self.source("repeat-panel param:10:3 gap 2 from 0", "repeat 0 param:10:8")
                              if mode == "parameter" else
                              self.source("repeat-panel card gap 2 from 0", "repeat 0 card", "card-reference 10 3 8 "))
                self.commit(definition)
                self.commit(self.rule())
                self.assertIn(definition, self.dump(), "R14_SOURCE_DEFINITION_NOT_EFFECTIVE_VALUE")
                self.query(CASES["panel917-negative"])
                before = self.owner()
                rejected = self.engineering([self.parameter("916")], valid=False)
                self.assertIn("DIVISION_NOT_EXACT", reason(rejected))
                self.assertEqual(before, self.owner())
                self.engineering([self.parameter("922")])
                self.query(CASES["valid-panel922-edit"])
                self.assertIn(definition, self.dump(), "R14_SOURCE_DEFINITION_NOT_EFFECTIVE_VALUE")
                self.assertEqual(before["rules"], self.owner()["rules"])
                self.assertIn("parameters/1", self.capabilities())
                if mode == "card":
                    self.assertEqual({"parameterId": 10, "uFieldId": 3, "vFieldId": 8}, self.owner()["cardReference"])
                    self.assertIn("grid-card-reference/1", self.capabilities())
                self.roundtrip()
                self.engineering([self.parameter("922", identifier=11)])
                before_rebind = self.dump()
                if mode == "card":
                    self.engineering([{"op": "set-grid-card-reference", "id": 0,
                                       "value": {"parameterId": 11, "uFieldId": 3, "vFieldId": 8}}])
                    self.assertEqual({"parameterId": 11, "uFieldId": 3, "vFieldId": 8},
                                     self.owner()["cardReference"], "R14_EQUAL_VALUE_DIFFERENT_SOURCE")
                else:
                    self.commit(self.source("repeat-panel param:11:3 gap 2 from 0", "repeat 0 param:11:8"))
                    self.assertIn("u repeat-panel param:11:3 gap 2 from 0 v repeat 0 param:11:8", self.dump())
                self.assertNotEqual(before_rebind, self.dump(), "R14_EQUAL_VALUE_DIFFERENT_SOURCE")
                self.query(CASES["valid-panel922-edit"])
                self.assertEqual(before["rules"], self.owner()["rules"])
                self.roundtrip()

    def test_13_native_slice_capability_is_explicit_without_claiming_complete_host_support(self):
        state = self.command("engineering-read")["state"]
        self.assertEqual([
            "engineering-spec/1", "parameters/1", "assembly-rule-authoring/1",
            "assembly-timber-generation/1", "assembly-bay-repeat/1", "grid-subdivision-rules/1",
            "section-profile/1", "grid-card-reference/1", "identity-ledger/1", "definition-import/1",
        ], state["capabilities"], "R14_NATIVE_SLICE_PRESERVES_COMPLETE_HOST_CAPABILITIES")
        self.assertEqual(["section-profile-native/1", "panel-fill-native/1", "grid-subdivision-native/2"],
                         state["native_capabilities"], "R14_NATIVE_CAPABILITY_EXPLICIT_AND_ORDERED")
        self.seed()
        self.assertIn("grid-subdivision-rules/2", self.capabilities())
        dumped = self.command("dump")
        self.assertEqual(state["capabilities"], dumped["capabilities"])
        self.assertEqual(state["native_capabilities"], dumped["native_capabilities"])
        self.assertIn("requires grid-subdivision-rules/2", dumped["text"])
        self.roundtrip()


if __name__ == "__main__":
    program = unittest.main(verbosity=2, exit=False)
    if program.result.skipped:
        print("R14_BLOCKED: skipped checks are not a passing or killed-product receipt", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(0 if program.result.wasSuccessful() else 1)
