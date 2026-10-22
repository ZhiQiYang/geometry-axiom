"""I24 submission policy through real native candidates and legacy scene replay.

The legacy fixtures are frozen by an unmodified bridge.  This suite never creates
its legacy two-axis baseline with an interactive submission or a policy bypass.
Every refusal pins its clause/reason, checks the preview itself, rejects its
confirmation token, and preserves definition bytes, objects, and revision.
"""
import base64
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import _bridge
from tests.test_grid_system_contract import system
from tests.test_parameters_core import card, field
from tests.test_grid_card_reference import grid as card_grid, parameter, source, swap, unbind

M1 = "同一份網格只能有一軸錯開"
M2 = "先在同一筆編輯裡移除一軸"
DIRECT_U = "repeat 0 2000 stagger 400"
DIRECT_V = "repeat 0 1830 stagger 300"
PLAIN_U = "repeat 0 2000"
PLAIN_V = "repeat 0 1830"
PARAM_U = "repeat 0 2000 stagger param:901:1"
PARAM_V = "repeat 0 1830 stagger param:901:2"


def grid(identifier=0, u=DIRECT_U, v=DIRECT_V, name="G"):
    return {"op": "put-grid-system", "value": {
        "id": identifier, "name": name, "mainAlong": "none", "u": u, "v": v}}


def offsets(u="400", v="300", identifier=901):
    return card(identifier, "offset", [field(1, u), field(2, v)])


def archive(operation):
    encoded = base64.b64encode(json.dumps(operation, ensure_ascii=False,
        separators=(",", ":")).encode("utf-8")).decode("ascii")
    return "engineering archive " + encoded


class StaggerCommit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exe = _bridge.find_bridge()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="geometry-314-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.session = _bridge.BridgeSession(self.exe)
        self.addCleanup(self.session.stop)
        self.assertTrue(self.command("reset")["ok"])

    def command(self, command):
        return self.session.command(command)

    def line(self, command):
        return self.command("line " + command)

    def dump(self):
        result = self.command("dump")
        self.assertTrue(result["ok"], result)
        return result["text"]

    def read(self):
        result = self.command("engineering-read")
        self.assertTrue(result["ok"], result)
        return result

    def state(self):
        return self.dump(), self.command("objects"), self.read()["revision"]

    def systems(self):
        return {row["id"]: row for row in self.command("objects")["gridSystems"]}

    def assert_staggers(self, identifier, u, v):
        row = self.systems()[identifier]
        for axis, expected in (("u", u), ("v", v)):
            definition = row[axis + "Definition"]
            if expected is None:
                self.assertNotIn("stagger", definition, (axis, row))
            else:
                self.assertEqual(expected, definition.get("stagger"), (axis, row))

    def commit(self, command):
        response = self.line(command)
        if "preview" in response:
            self.assertTrue(response["preview"]["valid"], (command, response))
            response = self.line("confirm " + str(response["preview"]["token"]))
        self.assertTrue(response["ok"], (command, response))
        return response

    def request(self, operations, kind="engineering", revision=None):
        payload = {"schema": kind + "-transaction/1", "expectedRevision":
            self.read()["revision"] if revision is None else revision,
            "operations": operations}
        path = self.directory / (kind + "-request.json")
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return self.command(kind + "-preview " + str(path))

    def apply(self, operations, kind="engineering"):
        before = self.state()
        response = self.request(operations, kind)
        self.assertTrue(response["ok"], response)
        self.assertTrue(response["preview"]["valid"], response)
        self.assertEqual(before, self.state(), "preview cannot mutate the live World")
        confirmed = self.command(kind + "-confirm " + str(response["preview"]["token"]))
        self.assertTrue(confirmed["ok"], confirmed)
        return response, confirmed

    @staticmethod
    def reason(response):
        violations = response.get("preview", {}).get("violations", [])
        return "\n".join([str(response.get("error", "")), *[
            str(value) for row in violations for key in ("actual", "message")
            if (value := row.get(key))]])

    def reject_line(self, command, reason, clause="I24"):
        before = self.state()
        response = self.line(command)
        self.assertFalse(response.get("ok") and response.get("preview", {}).get("valid", True), response)
        if "preview" in response:
            self.assertFalse(response["preview"]["valid"], "preview guard: " + repr(response))
        self.assertIn(clause, self.reason(response), response)
        self.assertIn(reason, self.reason(response), response)
        if "preview" in response:
            confirmed = self.line("confirm " + str(response["preview"]["token"]))
            self.assertFalse(confirmed["ok"], "invalid preview must never confirm: " + repr(confirmed))
        self.assertEqual(before, self.state(), "rejected line preserves bytes/objects/revision")
        return response

    def reject(self, operations, reason, kind="engineering", clause="I24"):
        before = self.state()
        response = self.request(operations, kind)
        self.assertTrue(response["ok"], response)
        self.assertFalse(response["preview"]["valid"], "preview guard: " + repr(response))
        self.assertIn(clause, self.reason(response), response)
        self.assertIn(reason, self.reason(response), response)
        confirmed = self.command(kind + "-confirm " + str(response["preview"]["token"]))
        self.assertFalse(confirmed["ok"], "invalid preview must never confirm: " + repr(confirmed))
        self.assertEqual(before, self.state(), "rejected batch preserves bytes/objects/revision")
        return response

    def fixture(self, kind):
        path = ROOT / "tests/fixtures" / ("legacy-two-axis-stagger-" + kind + ".scene")
        self.assertTrue(path.is_file(), "Missing frozen pre-policy fixture: " + str(path))
        return path

    def legacy(self, kind="direct"):
        path = self.fixture(kind)
        original = path.read_bytes()
        loaded = self.command("loadfile " + str(path))
        self.assertTrue(loaded["ok"], loaded)
        self.assertEqual(original, self.dump().encode("utf-8"), "legacy load/dump must be byte-identical")
        self.assertTrue(any("stagger" in row["uDefinition"] and "stagger" in row["vDefinition"]
            for row in self.systems().values()), "legacy replay retains both stagger axes")
        return original.decode("utf-8")

    def replace_legacy_system(self, identifier, replacement):
        """Make a file-replay variant; do not interactively create dual axes."""
        text = self.dump()
        rows = [line for line in text.splitlines() if line.startswith(f"grid-system {identifier} ")]
        self.assertEqual(1, len(rows), (identifier, text))
        path = self.directory / "legacy-variant.scene"
        path.write_text(text.replace(rows[0], replacement), encoding="utf-8")
        result = self.command("loadfile " + str(path))
        self.assertTrue(result["ok"], result)

    def test_C1_new_direct_and_repeat_panel_dual_axes_reject_M1(self):
        self.reject_line(system(0, "G", DIRECT_U, DIRECT_V), M1)
        self.reject_line(system(0, "G", "repeat-panel 400 gap 5 from -100 stagger 200",
            "repeat 0 600 stagger 100"), M1)

    def test_C1_new_parameter_dual_axes_reject_M1(self):
        self.apply([offsets()])
        self.reject_line(system(0, "G", PARAM_U, PARAM_V), M1)

    def test_C1_each_single_axis_is_a_legal_new_submission(self):
        self.commit(system(0, "U", DIRECT_U, PLAIN_V))
        self.commit(system(1, "V", PLAIN_U, DIRECT_V))
        self.assert_staggers(0, 400, None)
        self.assert_staggers(1, None, 300)

    def test_C2_existing_single_axis_cannot_add_the_other_axis(self):
        for u, v in ((DIRECT_U, PLAIN_V), (PLAIN_U, DIRECT_V)):
            self.assertTrue(self.command("reset")["ok"])
            self.commit(system(0, "G", u, v))
            self.reject_line(system(0, "G", DIRECT_U, DIRECT_V), M1)

    def test_C2_one_submission_can_switch_direction_edit_single_remove_and_rename(self):
        self.commit(system(0, "G", PLAIN_U, DIRECT_V))
        self.commit(system(0, "G", DIRECT_U, PLAIN_V))
        self.assert_staggers(0, 400, None)
        self.commit(system(0, "renamed", "repeat 0 2000 stagger 500", PLAIN_V))
        self.assertEqual("renamed", self.systems()[0]["name"])
        self.assert_staggers(0, 500, None)
        self.commit(system(0, "renamed", PLAIN_U, PLAIN_V))
        self.assert_staggers(0, None, None)

    def test_C3_archive_new_and_existing_second_axes_reject_M1(self):
        self.reject_line(archive(grid()), M1)
        self.commit(archive(grid(v=PLAIN_V)))
        self.reject_line(archive(grid()), M1)

    def test_C3_archive_single_axis_and_direction_switch_commit(self):
        self.commit(archive(grid(v=PLAIN_V)))
        self.commit(archive(grid(u=PLAIN_U)))
        self.assert_staggers(0, None, 300)

    def test_C4_batch_new_and_added_second_axes_reject_M1(self):
        self.reject([grid()], M1)
        self.apply([grid(v=PLAIN_V)])
        self.reject([grid()], M1)

    def test_C4_temporary_dual_axes_are_allowed_when_final_state_has_one(self):
        self.apply([grid(), grid(u=PLAIN_U)])
        self.assert_staggers(0, None, 300)

    def test_C4_remove_then_readd_changed_legacy_axis_still_rejects_M2(self):
        self.legacy()
        self.reject([grid(u=PLAIN_U), grid(u="repeat 0 2000 stagger 450")], M2)

    def test_C4_unrelated_parameter_put_import_delete_preserve_legacy_axes(self):
        self.legacy()
        self.apply([offsets(identifier=910)])
        package = {"schema": "geometry-parameters/1", "cards": [{
            "id": 911, "name": "unrelated", "fields": [{"id": 1, "name": "x",
                "type": "dimension", "expression": {"op": "literal", "num": "25", "den": "1", "unit": "mm"}}]}]}
        self.apply([{"op": "import-parameters", "value": package}])
        self.apply([{"op": "delete-parameter", "id": 910}])
        self.assert_staggers(0, 400, 300)

    def test_C4_other_batch_kinds_preserve_unchanged_legacy_axes(self):
        self.legacy()
        # All three commands use batch_preview/world_revalidate.  Each changes
        # its own registered domain and leaves the legacy grid definition alone.
        from tests.test_assembly_rules import rule
        from tests.test_section_profile_native import profile
        from tests.test_panel_fill_finish_surface import surface
        self.commit("boundary 70 outline 0,0 4000,0 4000,3000 0,3000 kind room_plan")
        operations = (("assembly", {"op": "publish-rule", "value": rule()}),
            ("section-profile", {"op": "put-profile", "value": profile()}),
            ("panel-fill", {"op": "put-finish-surface", "value": surface(
                boundary=70, obstacles=[])}))
        for kind, operation in operations:
            with self.subTest(kind=kind):
                self.apply([operation], kind)
                self.assert_staggers(0, 400, 300)

    def test_C5_new_and_added_card_second_axes_reject_M1(self):
        self.apply([parameter()])
        self.reject([card_grid(u="repeat -5 card stagger 6", v="repeat 7 card stagger 4")], M1)
        self.apply([card_grid(u="repeat -5 card stagger 6")])
        self.reject([card_grid(u="repeat -5 card stagger 6", v="repeat 7 card stagger 4")], M1)
        self.reject([{"op": "set-grid-card-reference", "id": 4, "value": source()},
            card_grid(u="repeat -5 card stagger 6", v="repeat 7 card stagger 4")], M1)

    def test_C5_single_card_swap_keeps_stagger_and_existing_pitch_guard(self):
        self.apply([parameter(), card_grid(u="repeat -5 card stagger 6")])
        self.apply([swap()])
        self.assert_staggers(4, 6, None)
        self.reject([parameter(a="12", b="6")], "整數倍")

    def test_C5_legacy_card_swap_repoint_and_both_unbind_modes_preserve_staggers(self):
        for operation in (swap(), {"op": "set-grid-card-reference", "id": 4,
                "value": source(u=8, v=3)}, unbind("direct"), unbind("parameter")):
            with self.subTest(operation=operation):
                self.legacy("card")
                self.apply([operation])
                self.assert_staggers(4, 6, 4)

    def test_C5_legacy_card_value_edit_rejects_and_remove_one_axis_allows(self):
        self.legacy("card")
        self.reject([card_grid(u="repeat -5 card stagger 8", v="repeat 7 card stagger 4")], M2)
        self.apply([card_grid(v="repeat 7 card stagger 4")])
        self.assert_staggers(4, None, 4)

    def test_C6_same_parameter_references_allow_one_and_both_card_values_to_change(self):
        self.legacy("param")
        self.apply([offsets("401")])
        self.assert_staggers(0, 401, 300)
        self.apply([offsets("402", "301")])
        self.assert_staggers(0, 402, 301)
        row = self.systems()[0]
        self.assertEqual({"kind": "parameter", "parameterId": 901, "fieldId": 1}, row["uDefinition"]["parameterRefs"]["stagger"])
        self.assertEqual({"kind": "parameter", "parameterId": 901, "fieldId": 2}, row["vDefinition"]["parameterRefs"]["stagger"])

    def test_C6_parameter_zero_still_fails_original_per_axis_guard(self):
        self.legacy("param")
        response = self.reject([offsets("0")], "相位差為 0")
        self.assertNotIn(M1, self.reason(response))
        self.assertNotIn(M2, self.reason(response))

    def test_C6_replacing_parameter_by_direct_requires_current_effective_value(self):
        self.legacy("param")
        self.apply([offsets("401")])
        self.reject([grid(u="repeat 0 2000 stagger 999", v=PARAM_V)], M2)
        self.apply([grid(u="repeat 0 2000 stagger 401", v=PARAM_V)])
        self.assert_staggers(0, 401, 300)
        self.assertNotIn("stagger", self.systems()[0]["uDefinition"].get("parameterRefs", {}))

    def test_C6_single_axis_parameter_card_values_remain_editable(self):
        self.apply([offsets(), grid(u=PARAM_U, v=PLAIN_V)])
        self.apply([offsets("500")])
        self.assert_staggers(0, 500, None)

    def ordered_legacy(self):
        self.legacy("param")
        self.replace_legacy_system(0, system(0, "G", PARAM_U, DIRECT_V))
        self.assert_staggers(0, 400, 300)

    def test_Q3_parameter_then_same_value_unbind_survives_preview_and_confirmation(self):
        self.ordered_legacy()
        before = self.state()
        response = self.request([offsets("500"), grid(u="repeat 0 2000 stagger 500")])
        self.assertTrue(response["ok"], response)
        preview = response["preview"]
        self.assertTrue(preview["valid"], preview)
        self.assertEqual(before, self.state())
        self.assertTrue(self.command("engineering-confirm " + str(preview["token"]))["ok"],
            "confirmation must retain the exact ordered source facts")
        self.assert_staggers(0, 500, 300)
        self.assertNotIn("stagger", self.systems()[0]["uDefinition"].get("parameterRefs", {}))
        self.assertIn("stagger 500", self.dump())

    def test_Q3_parameter_then_different_value_unbind_rejects_M2(self):
        self.ordered_legacy()
        self.reject([offsets("500"), grid(u="repeat 0 2000 stagger 450")], M2)

    def test_Q3_reverse_unbind_then_parameter_edit_cannot_borrow_future_value(self):
        self.ordered_legacy()
        self.reject([grid(u="repeat 0 2000 stagger 500"), offsets("500")], M2)

    def test_Q3_unrelated_parameter_edit_cannot_exempt_direct_value_change(self):
        self.legacy()
        self.reject([offsets("500", identifier=910), grid(u="repeat 0 2000 stagger 500")], M2)

    def test_Q3_source_repoint_checks_the_ordered_value_of_the_new_reference(self):
        self.ordered_legacy()
        self.apply([offsets("400", "300", identifier=902)])
        self.apply([grid(u="repeat 0 2000 stagger param:902:1")])
        self.assert_staggers(0, 400, 300)
        self.reject([offsets("450", identifier=901), grid(u=PARAM_U)], M2)

    def test_Q3_cancelled_and_stale_facts_do_not_leak_to_later_candidates(self):
        self.ordered_legacy()
        original = self.state()
        preview = self.request([offsets("500"), grid(u="repeat 0 2000 stagger 500")])["preview"]
        self.assertTrue(preview["valid"], preview)
        self.assertTrue(self.command("engineering-cancel " + str(preview["token"]))["cancelled"])
        self.assertFalse(self.command("engineering-confirm " + str(preview["token"]))["ok"])
        self.assertEqual(original, self.state())
        self.reject([grid(u="repeat 0 2000 stagger 500")], M2)
        preview = self.request([offsets("500"), grid(u="repeat 0 2000 stagger 500")])["preview"]
        self.assertTrue(preview["valid"], preview)
        self.commit("spec unrelated 17")
        after_change = self.state()
        self.assertFalse(self.command("engineering-confirm " + str(preview["token"]))["ok"])
        self.assertEqual(after_change, self.state())
        self.reject([grid(u="repeat 0 2000 stagger 500")], M2)

    def test_C7_unrelated_guides_move_and_delete_preserve_legacy_axes(self):
        self.legacy()
        self.commit("surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000")
        self.commit("spec start 300")
        self.commit("spec end 900")
        self.commit("guide 1 1 u spec:start")
        self.commit("move 1 spec:end")
        self.commit("delete guide 1")
        self.assert_staggers(0, 400, 300)

    def test_C7_binding_placement_and_grid_application_preserve_legacy_axes(self):
        self.legacy()
        self.commit("boundary 71 outline 0,0 4000,0 4000,3000 0,3000")
        boundary = self.command("boundary 71")
        self.assertTrue(boundary["ok"], boundary)
        self.commit("grid-binding 1 on-boundary 71 from-system 0 vertex outer 0 geometry-hash " +
            boundary["geometryFingerprint"] + " cell 0 0 anchor 0 1 0 1")
        self.commit("placement 1 on boundary 71 origin 0 0 2500 u +x v +y")
        self.commit("grid 1 on 1 from-binding 1")
        objects = self.command("objects")
        self.assertEqual([1], [row["id"] for row in objects["gridBindings"]])
        self.assert_staggers(0, 400, 300)

    def test_C8_history_lines_are_separate_submissions_and_undo_restores_legacy(self):
        original = self.legacy()
        self.commit("history-begin")
        self.commit(system(0, "G", PLAIN_U, DIRECT_V))
        self.commit(system(0, "G", PLAIN_U, "repeat 0 1830 stagger 350"))
        self.commit("history-end")
        changed = self.dump()
        self.assert_staggers(0, None, 350)
        self.commit("undo")
        self.assertEqual(original, self.dump())
        self.commit("redo")
        self.assertEqual(changed, self.dump())

    def test_C8_legacy_value_change_rolls_back_the_history_group(self):
        original = self.legacy()
        self.commit("history-begin")
        self.reject_line(system(0, "G", "repeat 0 2000 stagger 450", DIRECT_V), M2)
        self.assertFalse(self.line("history-end")["ok"])
        self.assertEqual(original, self.dump())

    def test_C8_remove_then_new_second_axis_is_M1_and_rolls_back_the_group(self):
        original = self.legacy()
        self.commit("history-begin")
        self.commit(system(0, "G", PLAIN_U, DIRECT_V))
        # A failed second line rolls back to the whole group's initial bytes;
        # this differs intentionally from reject_line's single-commit snapshot.
        response = self.line(system(0, "G", "repeat 0 2000 stagger 450", DIRECT_V))
        self.assertIn("preview", response, response)
        self.assertFalse(response["preview"]["valid"], response)
        self.assertIn("I24", self.reason(response))
        self.assertIn(M1, self.reason(response))
        self.assertFalse(self.line("confirm " + str(response["preview"]["token"]))["ok"])
        self.assertFalse(self.line("history-end")["ok"])
        self.assertEqual(original, self.dump())

    def test_C9_real_guide_drag_keeps_legacy_axes(self):
        self.legacy()
        self.commit("surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000")
        self.commit("spec start 300")
        self.commit("spec end 900")
        self.commit("guide 1 1 u spec:start")
        response = self.command("drag 0 2 2500 900")
        if "preview" in response:
            self.assertTrue(response["preview"]["valid"], response)
            response = self.line("confirm " + str(response["preview"]["token"]))
        self.assertTrue(response["ok"], response)
        self.assertIn("guide 1 1 u spec:end", self.dump())
        self.assert_staggers(0, 400, 300)

    def test_L1_all_frozen_legacy_modes_load_and_dump_byte_identically(self):
        for kind in ("direct", "param", "card", "panel", "bound"):
            with self.subTest(kind=kind):
                self.legacy(kind)

    def test_L2_bound_legacy_scene_roundtrips_in_an_independent_process(self):
        original = self.legacy("bound")
        self.assertEqual([560, 731], self.command("objects")["gridBindings"][0]["translation"])
        path = self.directory / "saved.scene"
        path.write_text(original, encoding="utf-8")
        with _bridge.BridgeSession(self.exe) as other:
            self.assertTrue(other.command("loadfile " + str(path))["ok"])
            self.assertEqual(original.encode("utf-8"), other.command("dump")["text"].encode("utf-8"))
            self.assertEqual([560, 731], other.command("objects")["gridBindings"][0]["translation"])

    def test_L3_load_prepare_confirm_preserve_the_legacy_final_scene(self):
        before = self.state()
        path = self.fixture("direct")
        response = self.command("load-prepare " + str(path))
        self.assertTrue(response["ok"], response)
        self.assertEqual(path.read_bytes(), response["final_scene"].encode("utf-8"))
        self.assertEqual(before, self.state(), "load preparation is isolated")
        self.assertTrue(self.command("load-confirm " + str(response["token"]))["ok"])
        self.assertEqual(path.read_bytes(), self.dump().encode("utf-8"))

    def test_L4_source_inspect_file_is_complete_and_read_only_for_legacy_modes(self):
        before = self.state()
        for kind in ("direct", "param", "card", "panel", "bound"):
            response = self.command("source-inspect-file " + str(self.fixture(kind)))
            self.assertTrue(response["ok"], response)
            self.assertTrue(response["complete"], response)
            self.assertEqual(before, self.state())

    def test_L5_default_replaces_legacy_and_interactive_reset_clears_it(self):
        self.legacy()
        self.assertTrue(self.command("default")["ok"])
        self.assertFalse(any("stagger" in row["uDefinition"] and "stagger" in row["vDefinition"]
            for row in self.systems().values()))
        self.legacy()
        self.commit("reset")
        self.assertEqual({}, self.systems())

    def test_L6_undo_and_redo_restore_two_axes_without_submission_comparison(self):
        original = self.legacy()
        self.commit(system(0, "G", "repeat 0 2000 stagger 450", PLAIN_V))
        changed = self.dump()
        self.commit("undo")
        self.assertEqual(original, self.dump())
        self.commit("redo")
        self.assertEqual(changed, self.dump())

    def test_L7_legacy_rename_spacing_and_source_preserving_changes_are_legal(self):
        self.legacy()
        self.commit(system(0, "renamed", DIRECT_U, DIRECT_V))
        self.commit(system(0, "renamed", "repeat 0 2100 stagger 400", "repeat 0 1900 stagger 300"))
        self.assert_staggers(0, 400, 300)
        self.assertEqual("renamed", self.systems()[0]["name"])

    def test_L8_legacy_u_and_v_value_edits_each_reject_M2(self):
        self.legacy()
        for u, v, axis, old, new in (("repeat 0 2000 stagger 450", DIRECT_V, "u", "400", "450"),
                (DIRECT_U, "repeat 0 1830 stagger 350", "v", "300", "350")):
            with self.subTest(axis=axis):
                response = self.reject_line(system(0, "G", u, v), M2)
                for part in (axis, old, new):
                    self.assertIn(part, self.reason(response))

    def test_L9_removing_one_axis_can_edit_the_other_but_cannot_readd_second(self):
        self.legacy()
        self.commit(system(0, "G", PLAIN_U, "repeat 0 1830 stagger 350"))
        self.assert_staggers(0, None, 350)
        self.reject_line(system(0, "G", DIRECT_U, "repeat 0 1830 stagger 350"), M1)

    def test_L10_engineering_archive_inside_legacy_file_is_replay(self):
        self.legacy("card")
        operation = card_grid(u="repeat -5 card stagger 6", v="repeat 7 card stagger 4")
        self.replace_legacy_system(4, archive(operation))
        self.assert_staggers(4, 6, 4)

    def test_L11_single_then_dual_file_records_do_not_become_submissions(self):
        text = self.dump() + system(1, "single", DIRECT_U, PLAIN_V) + "\n" + system(0, "dual", DIRECT_U, DIRECT_V) + "\n"
        path = self.directory / "single-then-dual.scene"
        path.write_text(text, encoding="utf-8")
        self.assertTrue(self.command("loadfile " + str(path))["ok"])
        self.assert_staggers(1, 400, None)
        self.assert_staggers(0, 400, 300)

    def test_L12_failed_load_cannot_leak_replay_flag_or_submission_baseline(self):
        self.legacy()
        before = self.state()
        path = self.directory / "malformed.scene"
        path.write_bytes(self.fixture("param").read_bytes() + b"not-a-scene-command\n")
        response = self.command("loadfile " + str(path))
        self.assertFalse(response["ok"], response)
        self.assertEqual(before, self.state())
        self.commit(system(1, "single", DIRECT_U, PLAIN_V))
        self.reject_line(system(2, "dual", DIRECT_U, DIRECT_V), M1)

    def test_Q4_actual_delete_ends_legacy_exception_and_redeclare_does_not(self):
        self.legacy()
        self.commit(system(0, "ordinary-redeclaration", DIRECT_U, DIRECT_V))
        self.commit("delete grid-system 0")
        self.assertNotIn(0, self.systems())
        self.reject_line(system(0, "recreated", DIRECT_U, DIRECT_V), M1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
