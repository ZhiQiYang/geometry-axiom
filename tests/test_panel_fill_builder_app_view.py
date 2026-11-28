"""PF-6 App: native same-candidate human-readable projection (not L4).

The old CLI owner tests retain their own assertions and test counts.
This new suite intentionally fails with PF6_APP_VIEW_REQUIRED on pre-App main.
"""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests import test_panel_fill_builder as native
from tests import test_panel_fill_layout as pf2
from tests import pf6_app_oracle as oracle
from tests import test_builder_token_owners as owners
from tests import test_framing_template as framing


class PanelFillBuilderAppView(unittest.TestCase):
    setUpClass = native.PanelFillBuilder.__dict__["setUpClass"]
    setUp = native.PanelFillBuilder.setUp
    command = native.PanelFillBuilder.command
    load_text = native.PanelFillBuilder.load_text
    read = native.PanelFillBuilder.read
    preview = native.PanelFillBuilder.preview
    apply = native.PanelFillBuilder.apply
    seed = native.PanelFillBuilder.seed
    fixture = native.PanelFillBuilder.fixture
    require_builder = native.PanelFillBuilder.require_builder
    request = native.PanelFillBuilder.request
    commit_line = native.PanelFillBuilder.commit_line
    suggest_request = native.PanelFillBuilder.suggest_request
    suggest = native.PanelFillBuilder.suggest
    select_request = native.PanelFillBuilder.select_request
    select = native.PanelFillBuilder.select
    all_keys = native.PanelFillBuilder.all_keys
    formal_snapshot = native.PanelFillBuilder.formal_snapshot
    packet = owners.BuilderTokenOwners.packet
    seed_framing = owners.BuilderTokenOwners.seed_framing
    framing_pending = owners.BuilderTokenOwners.framing_pending

    def app_view(self, value, suggestion, phase, selected):
        self.assertIn("appView", value, "PF6_APP_VIEW_REQUIRED")
        view = value["appView"]
        self.assertEqual("panel-fill-builder-workspace/1", view["schema"], "PF6_APP_VIEW_SCHEMA")
        for key in ("revision", "setKey", "generation"):
            self.assertIsInstance(view[key], str, "PF6_APP_EXACT_WIRE")
            self.assertEqual(suggestion[key], view[key], "PF6_APP_SAME_SET_BINDING")
        self.assertEqual(phase, view["phase"], "PF6_APP_PHASE")
        self.assertEqual(selected, view["selected"], "PF6_APP_EXPLICIT_SET")
        self.assertEqual(suggestion["revision"], view["uiContract"]["revision"], "PF6_APP_SAME_WORLD_REVISION")
        return view

    def test_suggestion_projection_is_bound_and_zero_write(self):
        self.fixture()
        before = self.formal_snapshot()
        suggestion = self.suggest()
        view = self.app_view(suggestion, suggestion, "ANALYSIS", [])
        self.assertTrue(view["completeForScope"], "PF6_APP_COMPLETE_VIEW")
        self.assertTrue(view["uiContract"]["completeForScope"], "PF6_APP_COMPLETE_R43")
        self.assertEqual("u", view["input"]["primaryAlong"])
        self.assertEqual("27", view["input"]["A"]["effective"], "PF6_APP_EXACT_DIMENSION")
        self.assertEqual("30", view["input"]["B"]["effective"])
        self.assertEqual("mm", view["input"]["A"]["unit"])
        self.assertTrue(view["host"]["created"])
        self.assertTrue(view["grid"]["created"])
        self.assertEqual([], view["timbers"], "PF6_APP_ANALYSIS_NOT_SELECTED_WORLD")
        self.assertEqual(oracle.support_parts([]), oracle.disclosed_support(view["uiContract"]["after"]),
                         "PF6_APP_SUGGEST_HAS_NO_HIDDEN_SELECTION")
        self.assertEqual(before, self.formal_snapshot(), "PF6_APP_VIEW_ZERO_WRITE")

    def test_selected_projection_matches_independent_geometry_and_r43_scan(self):
        for width in (25, 27, 31):
            for side in (1, -1):
                with self.subTest(width=width, side=side):
                    self.fixture(side=side)
                    suggestion = self.suggest(native.builder_input(A={"kind": "literal", "value": width}))
                    keys = self.all_keys(suggestion)
                    preview = self.select(suggestion, keys)
                    self.assertTrue(preview["valid"], "PF6_APP_VALID_SCAN")
                    view = self.app_view(preview, suggestion, "SELECTED", keys)
                    self.assertTrue(view["completeForScope"], "PF6_APP_COMPLETE_VIEW")
                    rectangles = oracle.construct_rectangles(width, side=side)
                    expected = sorted(oracle.host_rectangle(r, side) for r in rectangles)
                    actual = sorted({tuple(map(int, row["geometry"]["rect"])) for row in preview["entries"]
                                     if row["selected"] and row["valid"]})
                    self.assertEqual(expected, actual, "PF6_APP_RECTANGLE_INDEPENDENT_ORACLE")
                    self.assertEqual(oracle.support_parts(rectangles),
                                     oracle.disclosed_support(view["uiContract"]["after"]),
                                     "PF6_APP_SELECTED_R43_SAME_WORLD")
                    self.assertEqual(oracle.support_parts([]),
                                     oracle.disclosed_support(view["uiContract"]["before"]),
                                     "PF6_APP_BEFORE_R43_UNCHANGED")
                    self.assertEqual(len(rectangles), len(view["timbers"]), "PF6_APP_ALL_MEMBERS_DISCLOSED")
                    self.assertEqual(sorted(max(r[2]-r[0], r[3]-r[1]) for r in rectangles),
                                     sorted(int(t["after"]["geometry"]["length"]) for t in view["timbers"]),
                                     "PF6_APP_FINAL_MEMBER_LENGTH")
                    for timber in view["timbers"]:
                        self.assertIsNone(timber["before"])
                        after = timber["after"]
                        self.assertEqual(str(width), after["A"]["effective"], "PF6_APP_MEMBER_EXACT_A")
                        self.assertEqual("30", after["B"]["effective"], "PF6_APP_MEMBER_EXACT_B")
                        for key in ("centerline", "length", "u", "v", "A", "B"):
                            self.assertRegex(after["geometry"][key], r"^-?(0|[1-9][0-9]*)$", "PF6_APP_EXACT_MEMBER_GEOMETRY")
                        self.assertEqual(["0", "0", str(side)], after["geometry"]["axes"][2], "PF6_APP_STRUCTURE_SIDE")
                    self.assertTrue(self.command("pf6-cancel " + str(preview["token"]))["cancelled"])

    def test_subset_is_fresh_geometry_and_keeps_insufficient_support_visible(self):
        self.fixture()
        suggestion = self.suggest()
        keys = [row["key"] for row in suggestion["entries"]
                if not (row["phase"] == "seam-primary" and row["source"]["k"] == "0")]
        preview = self.select(suggestion, keys)
        self.assertTrue(preview["valid"], "PF6_APP_SUBSET_LEGAL")
        view = self.app_view(preview, suggestion, "SELECTED", keys)
        self.assertTrue(view["completeForScope"], "PF6_APP_INSUFFICIENT_IS_NOT_INVALID")
        rectangles = oracle.construct_rectangles(27, omit_first_primary=True)
        self.assertEqual(sorted(rectangles), sorted({tuple(map(int, row["geometry"]["rect"]))
                         for row in preview["entries"] if row["selected"] and row["valid"]}),
                         "PF6_APP_SELECTED_REBUILD")
        self.assertEqual(oracle.support_parts(rectangles), oracle.disclosed_support(view["uiContract"]["after"]),
                         "PF6_APP_SUBSET_R43")
        support = view["uiContract"]["after"]["panelFills"][0]["derived"]["support"]
        self.assertTrue(any(not p["supported"] for p in support), "PF6_APP_INSUFFICIENT_VISIBLE")

    def publish_sources(self):
        self.commit_line("spec chosen_width 27")
        value = {"schema": "engineering-transaction/1", "expectedRevision": self.read()["revision"],
                 "operations": [
                     {"op": "publish-material", "value": {"id": "chosen-timber", "version": 1,
                      "kind": "timber", "name": "明選松木", "A": 27, "B": 30}},
                     {"op": "put-parameter", "value": {"id": 91, "name": "貼板尺寸",
                      "fields": [{"id": 1, "name": "角材寬", "type": "dimension", "input": "27"},
                                 {"id": 2, "name": "貼板厚", "type": "dimension", "input": "30"}]}}]}
        result = self.request("engineering-preview", value)
        self.assertTrue(result["ok"] and result["preview"]["valid"], result)
        self.assertTrue(self.command("engineering-confirm " + str(result["preview"]["token"]))["ok"])

    def test_all_four_source_kinds_have_native_names_and_exact_values(self):
        self.fixture()
        self.publish_sources()
        sources = [({"kind": "literal", "value": 27}, "直接值"),
                   ({"kind": "spec", "name": "chosen_width"}, "chosen_width"),
                   ({"kind": "material", "id": "chosen-timber", "version": 1, "field": "A"}, "明選松木"),
                   ({"kind": "parameter", "parameterId": 91, "fieldId": 1}, "貼板尺寸／角材寬")]
        for source, name in sources:
            with self.subTest(source=source):
                suggestion = self.suggest(native.builder_input(A=source))
                self.assertTrue(suggestion["valid"], "PF6_APP_SOURCE_VALID")
                view = self.app_view(suggestion, suggestion, "ANALYSIS", [])
                self.assertTrue(view["completeForScope"], "PF6_APP_SOURCE_PROJECTION_COMPLETE")
                dimension = view["input"]["A"]
                self.assertEqual(source, dimension["source"], "PF6_APP_TYPED_SOURCE_IDENTITY")
                self.assertEqual(name, dimension["name"], "PF6_APP_NATIVE_SOURCE_NAME")
                self.assertEqual("27", dimension["effective"], "PF6_APP_SOURCE_EXACT_VALUE")
                self.assertTrue(dimension["path"])

    def test_zero_parameter_card_and_field_ids_are_preserved(self):
        self.fixture()
        value = {"schema": "engineering-transaction/1", "expectedRevision": self.read()["revision"],
                 "operations": [
                     {"op": "put-parameter", "value": {"id": 0, "name": "零號寬度卡",
                      "fields": [{"id": 0, "name": "零號寬欄", "type": "dimension", "input": "27"}]}},
                     {"op": "put-parameter", "value": {"id": 1, "name": "厚度卡",
                      "fields": [{"id": 0, "name": "零號厚欄", "type": "dimension", "input": "30"}]}}]}
        result = self.request("engineering-preview", value)
        self.assertTrue(result["ok"] and result["preview"]["valid"], "PF6_APP_ZERO_IDS_NATIVE_FIXTURE")
        self.assertTrue(self.command("engineering-confirm " + str(result["preview"]["token"]))["ok"])
        sources = {"A": {"kind": "parameter", "parameterId": 0, "fieldId": 0},
                   "B": {"kind": "parameter", "parameterId": 1, "fieldId": 0}}
        names = {"A": ("零號寬度卡", "零號寬欄", "27"), "B": ("厚度卡", "零號厚欄", "30")}
        before = self.formal_snapshot()
        suggestion = self.suggest(native.builder_input(**sources))
        self.assertTrue(suggestion["valid"], "PF6_APP_ZERO_IDS_NATIVE_VALID")
        analysis = self.app_view(suggestion, suggestion, "ANALYSIS", [])
        keys = self.all_keys(suggestion)
        preview = self.select(suggestion, keys)
        self.assertTrue(preview["valid"], "PF6_APP_ZERO_IDS_SELECTED_VALID")
        selected = self.app_view(preview, suggestion, "SELECTED", keys)
        for view in (analysis, selected):
            self.assertTrue(view["completeForScope"], "PF6_APP_ZERO_IDS_COMPLETE")
            dimensions = [view["input"]] + [row["after"] for row in view["timbers"]]
            for dimensions_by_field in dimensions:
                for field, source in sources.items():
                    dimension = dimensions_by_field[field]
                    card_name, field_name, effective = names[field]
                    self.assertEqual(source, dimension["source"], "PF6_APP_ZERO_IDS_EXACT_SOURCE")
                    self.assertEqual(card_name, dimension["cardName"], "PF6_APP_ZERO_IDS_CARD_NAME")
                    self.assertEqual(field_name, dimension["fieldName"], "PF6_APP_ZERO_IDS_FIELD_NAME")
                    self.assertEqual(card_name + "／" + field_name, dimension["name"], "PF6_APP_ZERO_IDS_NAME")
                    self.assertEqual(effective, dimension["effective"], "PF6_APP_ZERO_IDS_EXACT_VALUE")
            self.assertEqual(sources["B"], view["host"]["h"]["source"], "PF6_APP_ZERO_IDS_HOST_SOURCE")
        self.assertEqual(12, len(selected["timbers"]), "PF6_APP_ZERO_IDS_ALL_MEMBERS")
        self.assertEqual(before, self.formal_snapshot(), "PF6_APP_ZERO_IDS_ZERO_WRITE")
        self.assertTrue(self.command("pf6-cancel " + str(preview["token"]))["cancelled"])
        self.assertEqual(before, self.formal_snapshot(), "PF6_APP_ZERO_IDS_CANCEL_ZERO_WRITE")

    def test_existing_equal_height_source_and_grid_preference_are_preserved(self):
        self.fixture()
        self.publish_sources()
        self.apply([{"op": "put-derived-placement", "value": {"id": 10, "fillId": 1,
                     "h": {"kind": "parameter", "parameterId": 91, "fieldId": 2}}}])
        self.commit_line("grid 9 on 10 from-fill 1 main-along v")
        suggestion = self.suggest()
        keys = self.all_keys(suggestion)
        view = self.app_view(self.select(suggestion, keys), suggestion, "SELECTED", keys)
        self.assertFalse(view["host"]["created"])
        self.assertFalse(view["grid"]["created"])
        self.assertEqual(10, view["host"]["id"])
        self.assertEqual("貼板尺寸／貼板厚", view["host"]["h"]["name"], "PF6_APP_PRESERVE_HOST_H_NAME")
        self.assertEqual({"kind": "parameter", "parameterId": 91, "fieldId": 2},
                         view["host"]["h"]["source"], "PF6_APP_EQUAL_VALUE_IS_NOT_EQUAL_SOURCE")
        self.assertEqual({"kind": "literal", "value": 30}, view["input"]["B"]["source"])
        self.assertEqual("v", view["grid"]["mainAlong"], "PF6_APP_PRESERVE_EXISTING_GRID_PREFERENCE")

    def test_noop_and_invalid_never_claim_selected_completeness(self):
        self.fixture()
        before = self.formal_snapshot()
        suggestion = self.suggest()
        noop = self.select(suggestion, [])
        view = self.app_view(noop, suggestion, "NO_OP", [])
        self.assertTrue(view["completeForScope"], "PF6_APP_NOOP_COMPLETE")
        self.assertIsNone(view["host"]["id"], "PF6_APP_NOOP_NO_HOST")
        self.assertIsNone(view["grid"]["id"], "PF6_APP_NOOP_NO_GRID")
        self.assertEqual(before, self.formal_snapshot(), "PF6_APP_NOOP_ZERO_WRITE")
        # A selected secondary lacks its necessary new supports. Reject whole set.
        key = next(row["key"] for row in suggestion["entries"] if row["phase"] == "seam-secondary")
        invalid = self.select(suggestion, [key])
        self.assertFalse(invalid["valid"], "PF6_APP_SUBSET_INVALID")
        view = self.app_view(invalid, suggestion, "SELECTED", [key])
        self.assertFalse(view["completeForScope"], "PF6_APP_INVALID_NOT_CONFIRMABLE")
        self.assertFalse(view["uiContract"]["completeForScope"])
        self.assertEqual(before, self.formal_snapshot(), "PF6_APP_INVALID_ZERO_WRITE")

    def test_native_tokens_and_temporary_definition_map_are_exact(self):
        self.fixture()
        before = self.formal_snapshot()
        suggestion = self.suggest()
        self.assertIsNone(suggestion["token"], "PF6_NATIVE_ANALYSIS_HAS_NO_TOKEN")
        self.assertIs(suggestion["confirmable"], False, "PF6_NATIVE_ANALYSIS_NOT_CONFIRMABLE")
        self.assertTrue(all(row["selected"] is False for row in suggestion["entries"]),
                        "PF6_NATIVE_ANALYSIS_EXPLICIT_EMPTY_SET")
        noop = self.select(suggestion, [])
        self.assertEqual("NO_OP", noop["phase"], "PF6_NATIVE_NOOP_PHASE")
        self.assertIsNone(noop["token"], "PF6_NATIVE_NOOP_HAS_NO_TOKEN")
        self.assertIsNone(noop["idMap"], "PF6_NATIVE_NOOP_HAS_NO_FORMAL_MAP")
        preview = self.select(suggestion, self.all_keys(suggestion))
        self.assertIs(type(preview["token"]), int, "PF6_NATIVE_TOKEN_IS_INTEGER")
        self.assertTrue(1 <= preview["token"] <= 4294967295, "PF6_NATIVE_POSITIVE_TOKEN")
        self.assertIs(preview["candidateIdsAreTemporary"], True, "PF6_NATIVE_CANDIDATE_IDS_TEMPORARY")
        self.assertIsNone(preview["idMap"], "PF6_NATIVE_PREVIEW_HAS_NO_FORMAL_MAP")
        self.assertTrue(preview["createdDefinitions"], "PF6_NATIVE_CREATED_DEFINITIONS_DISCLOSED")
        for item in preview["createdDefinitions"]:
            self.assertEqual({"kind", "tempKey", "candidateId"}, set(item),
                             "PF6_NATIVE_TEMPORARY_MAP_EXACT_FIELDS")
        self.assertEqual(before, self.formal_snapshot(), "PF6_NATIVE_CANDIDATE_NO_ALLOCATION")
        result = self.command("pf6-confirm " + str(preview["token"]))
        self.assertTrue(result["ok"], "PF6_NATIVE_CONFIRM_SUCCEEDS")
        self.assertTrue(result["actionReceipt"]["idMap"], "PF6_NATIVE_ONLY_RECEIPT_HAS_FORMAL_MAP")

    def test_ui13_original_six_mutations_keep_unique_anchors(self):
        from tests import panel_fill_ui_mutations
        try:
            variants = panel_fill_ui_mutations.variants(ROOT)
        except ValueError as error:
            self.fail("PF6_UI13_SIX_ORIGINAL_ANCHORS: " + str(error))
        self.assertEqual([
            ("entry-handler", "UI13_ENTRY_HANDLER"),
            ("preview-http", "UI13_PREVIEW_HTTP"),
            ("confirm-receipt", "UI13_CONFIRM_RECEIPT"),
            ("preview-focus", "UI12_PREVIEW_FOCUS"),
            ("downstream-impact", "UI04_NATIVE_DOWNSTREAM_IMPACT"),
            ("confirm-scene-sync", "UI05_HOST_SCENE_SYNC"),
        ], [(row[0], row[1]) for row in variants], "PF6_UI13_SIX_ORIGINAL_MUTATIONS_RETAINED")
        for identifier, _, _, original, changed in variants:
            self.assertNotEqual(original, changed, "PF6_UI13_REAL_WITHDRAWAL_" + identifier)
        # This is anchor preflight only; real UI13 kill evidence still needs CDP.

    def test_capability_migration_rejects_every_weakened_declaration(self):
        from tests.pf6_app_contract import assert_supported_actions, PF6_ACTIONS
        assert_supported_actions(self, PF6_ACTIONS)
        wrong_order = PF6_ACTIONS.copy()
        wrong_order[0], wrong_order[1] = wrong_order[1], wrong_order[0]
        negatives = {"missing-old": PF6_ACTIONS[1:], "missing-new": PF6_ACTIONS[:5],
                     "unknown": PF6_ACTIONS + ["export-grid-snapshot"],
                     "duplicate": PF6_ACTIONS + ["suggest-timbers"], "wrong-order": wrong_order}
        for name, value in negatives.items():
            with self.subTest(declaration=name):
                with self.assertRaisesRegex(AssertionError, "PF6_UI_WIRE_ACTIONS_EXACT",
                                            msg="PF6_CAPABILITY_NEGATIVE_CONTROL_" + name):
                    assert_supported_actions(self, value)

    def r03_request(self):
        read = self.packet("framing-template-read", {"schema": "framing-template-read/1", "boundaryId": 1})
        self.assertTrue(read["ok"], "PF6_R03_READ_FOR_CURRENT_WORLD")
        return {"schema": "framing-template-generate/1", "expectedRevision": read["revision"],
                "contextKey": read["contextKey"], "definitionFingerprint": read["definitionFingerprint"],
                "boundaryId": 1, "on": 1,
                "template": {"id": "flat-ceiling", "version": 1, "policyFingerprint": framing.POLICY},
                "parameters": copy.deepcopy(framing.PARAMETERS),
                "sources": {"panel": {"id": "r03-board", "version": 1},
                            "threshold": {"parameterId": 90, "fieldId": 1}},
                "layout": {"corner": "min-min", "lengthAlong": "v"},
                "material": {"boundary": "rc", "timber": "literal"}}

    def test_existing_finish_always_rejects_r03_and_cancel_clears_pending(self):
        self.seed_framing()
        self.apply([pf2.put(pf2.surface(boundary=1, origin=(0, 0, 2500), obstacles=[])),
                    pf2.fill(panel={"id": "r03-board", "version": 1}, gap=2)])
        before = self.formal_snapshot()
        refused = self.packet("framing-template-preview", self.r03_request())
        self.assertEqual("UNSUPPORTED_SCOPE", refused.get("code"), "PF6_R03_EXISTING_FINISH_MUST_REJECT")
        self.assertEqual(before, self.formal_snapshot(), "PF6_R03_EXISTING_FINISH_ZERO_WRITE")
        suggestion = self.suggest(native.builder_input(B={"kind": "literal", "value": 33}))
        secondary = next(row["key"] for row in suggestion["entries"]
                         if row["phase"] == "seam-secondary" and row["valid"] and row["selectable"])
        candidate = self.select(suggestion, [secondary])
        self.assertIs(candidate["valid"], False, "PF6_R03_INVALID_CANDIDATE_FIXTURE")
        self.assertGreater(candidate["token"], 0, "PF6_R03_INVALID_HAS_POSITIVE_TOKEN")
        blocked = self.packet("framing-template-preview", self.r03_request())
        self.assertEqual("PENDING", blocked.get("code"), "PF6_R03_INVALID_OCCUPIES_OWNER")
        self.assertTrue(self.command("pf6-cancel " + str(candidate["token"]))["cancelled"],
                        "PF6_R03_CANCEL_INVALID_EXACT_TOKEN")
        released = self.packet("framing-template-preview", self.r03_request())
        self.assertEqual("UNSUPPORTED_SCOPE", released.get("code"),
                         "PF6_R03_CANCEL_REMOVES_PENDING_BUT_NOT_SCOPE_RULE")
        self.assertEqual(before, self.formal_snapshot(), "PF6_R03_CANCEL_AND_SCOPE_REJECT_ZERO_WRITE")
        candidate = self.select(suggestion, self.all_keys(suggestion))
        self.assertTrue(candidate["valid"], "PF6_R03_ALL_SELECTED_VALID")
        self.assertTrue(self.command("pf6-confirm " + str(candidate["token"]))["ok"])
        committed = self.formal_snapshot()
        refused = self.packet("framing-template-preview", self.r03_request())
        self.assertEqual("UNSUPPORTED_SCOPE", refused.get("code"), "PF6_THEN_R03_SAME_BOUNDARY_MUST_REJECT")
        self.assertEqual(committed, self.formal_snapshot(), "PF6_THEN_R03_ZERO_WRITE")

    def test_r03_then_pf6_reuses_its_formal_fill_host_and_grid(self):
        self.seed_framing()
        pending = self.framing_pending()
        done = self.command("framing-template-confirm " + str(pending["token"]) + " " + pending["ownerKey"])
        self.assertTrue(done["ok"], "PF6_R03_FORMAL_FIXTURE")
        state = self.read()["state"]
        fill_id = state["panelFills"][0]["definition"]["id"]
        grid = state["fillGrids"][0]["definition"]
        along = grid["mainAlong"]
        roles = {"u": "secondary", "v": "primary"} if along == "u" else {"u": "primary", "v": "secondary"}
        before = self.formal_snapshot()
        suggestion = self.suggest(native.builder_input(fillId=fill_id, B={"kind": "literal", "value": 33}, roles=roles))
        self.assertTrue(suggestion["valid"], "PF6_AFTER_R03_ANALYSIS_ALLOWED")
        view = self.app_view(suggestion, suggestion, "ANALYSIS", [])
        self.assertFalse(view["host"]["created"], "PF6_AFTER_R03_REUSES_HOST")
        self.assertFalse(view["grid"]["created"], "PF6_AFTER_R03_REUSES_GRID")
        self.assertEqual(grid["hostId"], view["host"]["id"], "PF6_AFTER_R03_SAME_HOST_ID")
        self.assertEqual(grid["id"], view["grid"]["id"], "PF6_AFTER_R03_SAME_GRID_ID")
        self.assertEqual(along, view["grid"]["mainAlong"], "PF6_AFTER_R03_SAME_AXIS")
        self.assertTrue(suggestion["omissions"], "PF6_AFTER_R03_COVERED_OUTER_EDGE_OMITTED")
        self.assertTrue(any(not row["valid"] for row in suggestion["entries"]),
                        "PF6_AFTER_R03_COINCIDENT_SEAM_NOT_AUTO_REUSED")
        self.assertEqual(before, self.formal_snapshot(), "PF6_AFTER_R03_ANALYSIS_ZERO_WRITE")
        mismatch = self.suggest(native.builder_input(fillId=fill_id, B={"kind": "literal", "value": 30}, roles=roles))
        self.assertIs(mismatch["valid"], False, "PF6_AFTER_R03_HEIGHT_MISMATCH_WHOLE_ANALYSIS_INVALID")
        self.assertTrue(mismatch["error"], "PF6_AFTER_R03_HEIGHT_MISMATCH_DIAGNOSTIC")
        self.assertEqual(before, self.formal_snapshot(), "PF6_AFTER_R03_HEIGHT_REJECT_ZERO_WRITE")

    def test_projection_does_not_add_history_and_survives_native_cold_replay(self):
        self.fixture()
        before = self.formal_snapshot()
        suggestion = self.suggest()
        keys = self.all_keys(suggestion)
        selected = self.select(suggestion, keys)
        view = self.app_view(selected, suggestion, "SELECTED", keys)
        self.assertEqual(before, self.formal_snapshot(), "PF6_APP_PREVIEW_ZERO_WRITE")
        self.assertTrue(self.command("pf6-cancel " + str(selected["token"]))["cancelled"])
        self.assertEqual(before, self.formal_snapshot(), "PF6_APP_CANCEL_ZERO_WRITE")
        selected = self.select(suggestion, keys)
        done = self.command("pf6-confirm " + str(selected["token"]))
        self.assertTrue(done["ok"] and done["history_changed"], "PF6_APP_CONFIRM_ONE_HISTORY")
        after = self.command("dump")["text"]
        formal = self.read()["uiContract"]["state"]
        self.assertEqual(view["uiContract"]["after"], formal, "PF6_APP_COMMIT_SAME_DISPLAYED_WORLD")
        self.commit_line("undo")
        self.assertEqual(before["dump"], self.command("dump")["text"], "PF6_APP_ONE_UNDO")
        self.commit_line("redo")
        self.assertEqual(after, self.command("dump")["text"], "PF6_APP_ONE_REDO")
        self.assertTrue(self.command("reset")["ok"])
        self.load_text(after)
        self.assertEqual(after, self.command("dump")["text"], "PF6_APP_DEFINITION_COLD_REPLAY")
        self.assertEqual(formal, self.read()["uiContract"]["state"], "PF6_APP_R43_COLD_REPLAY")
        self.assertFalse(self.command("pf6-confirm " + str(selected["token"]))["ok"], "PF6_APP_COLD_NO_TOKEN")


if __name__ == "__main__":
    unittest.main(verbosity=2)
