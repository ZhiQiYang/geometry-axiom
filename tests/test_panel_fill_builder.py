"""PF-6N: real native R45 suggestions and one outer candidate transaction.

Oracles come from D45/R45 and the issue #128 composable-builder contract.
These tests deliberately do not claim the subsequent App/L4 workflow.
"""
import base64
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests import test_panel_fill_layout as pf2
from tests._bridge import BridgeSession


def builder_input(**changes):
    value = {"fillId": 1, "A": {"kind": "literal", "value": 27},
             "B": {"kind": "literal", "value": 30},
             "roles": {"u": "secondary", "v": "primary"}}
    value.update(changes)
    return value


def outer_member(key, anchor, *, role="boundary", direction="+v", on="r45-host",
                 selector="", width=27, depth=30):
    return {"op": "create-timber", "tempKey": key,
            "A": {"kind": "literal", "value": width},
            "B": {"kind": "literal", "value": depth}, "role": role,
            "placement": {"on": on, "anchor": anchor, "selector": selector,
                          "direction": direction, "side": "+n"}}


def edge_anchor(edge):
    source = json.dumps([[edge, 0, 1]], separators=(",", ":")).encode().hex()
    return "at-face key-hex:" + source


class PanelFillBuilder(unittest.TestCase):
    setUpClass = pf2.PanelFillLayout.__dict__["setUpClass"]
    setUp = pf2.PanelFillLayout.setUp
    command = pf2.PanelFillLayout.command
    load_text = pf2.PanelFillLayout.load_text
    read = pf2.PanelFillLayout.read
    preview = pf2.PanelFillLayout.preview
    apply = pf2.PanelFillLayout.apply
    seed = pf2.PanelFillLayout.seed

    def require_builder(self):
        reply = self.read()
        self.assertIn("panel-fill-builder-native/1", reply["native_capabilities"],
                      "PF6_NATIVE_BUILDER_CAPABILITY: R45 has an actual native builder")
        self.assertFalse(reply["complete"], "PF6_NO_FULL_PRODUCT_CLAIM")

    def fixture(self, *, host=False, side=1, outline="0,0 300,0 300,300 0,300",
                extra="", obstacles=None, **fill_changes):
        self.seed(outline=outline, extra=extra, obstacles=obstacles)
        if side != 1:
            self.apply([pf2.put(pf2.surface(boundary=8, origin=(0, 0, 0),
                                           side=side, obstacles=obstacles or []))])
        operations = [pf2.fill(**fill_changes)]
        if host is not False:
            operations.append({"op": "put-derived-placement", "value": {
                "id": 10 if host is True else host, "fillId": 1, "h": 30}})
        self.apply(operations)

    def formal_snapshot(self):
        return {"dump": self.command("dump")["text"],
                "revision": self.read()["revision"],
                "identity": self.command("identity-read"),
                "nextIds": self.command("newid")}

    def request(self, command, value, name="pf6.json"):
        self.require_builder()
        path = self.directory / name
        path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")),
                        encoding="utf-8", newline="\n")
        return self.command(command + " " + str(path))

    def commit_line(self, line):
        result = self.command("line " + line)
        self.assertTrue(result["ok"], "PF6_FIXTURE: " + json.dumps(result, ensure_ascii=False))
        return result

    def suggest_request(self, value=None, pre=None, post=None):
        return {"schema": "panel-fill-builder-suggest/1",
                "expectedRevision": str(self.read()["revision"]),
                "input": builder_input() if value is None else copy.deepcopy(value),
                "pre": [] if pre is None else copy.deepcopy(pre),
                "post": [] if post is None else copy.deepcopy(post)}

    def suggest(self, value=None, pre=None, post=None):
        reply = self.request("pf6-suggest", self.suggest_request(value, pre, post))
        self.assertTrue(reply["ok"], "PF6_SUGGEST_NATIVE: " + json.dumps(reply, ensure_ascii=False))
        self.assertEqual("panel-fill-builder-suggestions/1", reply["schema"])
        self.assertEqual(str(self.read()["revision"]), reply["revision"])
        self.assertRegex(reply["setKey"], r"^[0-9a-f]{64}$", "PF6_SEALED_SET_KEY")
        self.assertIsInstance(reply["generation"], str)
        self.assertFalse(reply["confirmable"], "PF6_SUGGEST_NOT_CONFIRMABLE")
        self.assertIsNone(reply["token"], "PF6_SUGGEST_HAS_NO_CONFIRM_TOKEN")
        self.assertIsInstance(reply["entries"], list)
        keys = [row["key"] for row in reply["entries"]]
        self.assertEqual(len(keys), len(set(keys)), "PF6_CANDIDATE_KEYS_UNIQUE")
        for row in reply["entries"]:
            self.assertIsInstance(row["valid"], bool)
            self.assertIsInstance(row["phase"], str)
        return reply

    def select_request(self, suggestion, selected):
        return {"schema": "panel-fill-builder-select/1",
                "expectedRevision": suggestion["revision"],
                "setKey": suggestion["setKey"], "generation": suggestion["generation"],
                "selected": list(selected)}

    def select(self, suggestion, selected):
        reply = self.request("pf6-select", self.select_request(suggestion, selected))
        self.assertTrue(reply["ok"], "PF6_SELECT_NATIVE: " + json.dumps(reply, ensure_ascii=False))
        self.assertIn("preview", reply, "PF6_SELECTED_PREVIEW_REQUIRED")
        return reply["preview"]

    def all_keys(self, suggestion):
        self.assertTrue(suggestion["entries"], "PF6_RECTANGLE_HAS_SUGGESTIONS")
        self.assertTrue(all(row["valid"] for row in suggestion["entries"]),
                        "PF6_RECTANGLE_ALL_LEGAL: " + json.dumps(suggestion, ensure_ascii=False))
        return [row["key"] for row in suggestion["entries"]]

    def confirm(self, preview):
        self.assertTrue(preview["valid"], "PF6_CONFIRM_REQUIRES_VALID_PREVIEW: " + str(preview))
        reply = self.command("pf6-confirm " + str(preview["token"]))
        self.assertTrue(reply["ok"], "PF6_CONFIRM_NATIVE: " + str(reply))
        return reply

    def outer_fixture(self):
        self.fixture(host=True)
        self.commit_line("spec postline 50")
        self.commit_line("guide 1 10 v spec:postline")
        before = [outer_member("left-edge", edge_anchor("e3"))]
        after = [outer_member("after-secondary", "at-line guide 1", role="secondary",
                              direction="+v", selector="through 153")]
        return before, after

    def test_PF6_native_builder_is_a_declared_partial_capability(self):
        self.require_builder()

    def test_PF6_suggest_is_readonly_and_has_no_confirmable_token(self):
        self.fixture()
        before = self.formal_snapshot()
        suggestion = self.suggest()
        self.all_keys(suggestion)
        self.assertEqual(before, self.formal_snapshot(), "PF6_SUGGEST_ZERO_WRITE")
        self.assertFalse(self.command("pf6-confirm 0")["ok"], "PF6_SUGGEST_CANNOT_CONFIRM")
        self.assertEqual(before, self.formal_snapshot(), "PF6_SUGGEST_CONFIRM_ZERO_WRITE")

    def test_PF6_empty_explicit_selection_creates_nothing(self):
        self.fixture()
        self.assertTrue(self.command("identity-epoch " + "01" * 16)["ok"])
        before = self.formal_snapshot()
        suggestion = self.suggest()
        selected = self.select(suggestion, [])
        self.assertTrue(selected["valid"], "PF6_EMPTY_SELECTION_IS_NOOP")
        self.assertEqual("NO_OP", selected["phase"], "PF6_UNSELECTED_CREATES")
        self.assertIsNone(selected["token"], "PF6_EMPTY_SELECTION_NO_TOKEN")
        self.assertEqual(selected["beforeScene"], selected["afterScene"], "PF6_UNSELECTED_CREATES")
        self.assertEqual(before, self.formal_snapshot(), "PF6_UNSELECTED_CREATES")
        self.assertEqual([], self.read()["state"]["derivedPlacements"], "PF6_EMPTY_NO_IMPLICIT_HOST")
        self.assertEqual([], self.command("references")["grids"], "PF6_EMPTY_NO_IMPLICIT_GRID")

    def test_PF6_missing_duplicate_and_unknown_selection_are_rejected(self):
        self.fixture()
        for kind in ("unknown", "duplicate", "missing"):
            with self.subTest(kind=kind):
                suggestion = self.suggest()
                key = self.all_keys(suggestion)[0]
                selected = ["not-a-candidate"] if kind == "unknown" else [key, key]
                before = self.formal_snapshot()
                value = self.select_request(suggestion, selected)
                if kind == "missing":
                    del value["selected"]
                reply = self.request("pf6-select", value)
                self.assertFalse(reply["ok"], "PF6_EXPLICIT_SELECTION_REQUIRED")
                self.assertEqual(before, self.formal_snapshot(), "PF6_BAD_SELECTION_ZERO_WRITE")

    def test_PF6_preview_cancel_and_single_undo_redo_keep_whole_batch(self):
        self.fixture()
        self.assertTrue(self.command("identity-epoch " + "02" * 16)["ok"])
        before = self.formal_snapshot()
        suggestion = self.suggest()
        keys = self.all_keys(suggestion)
        preview = self.select(suggestion, keys)
        self.assertTrue(preview["valid"], "PF6_RECTANGLE_SELECTED_VALID")
        self.assertEqual("SELECTED", preview["phase"])
        self.assertEqual(before, self.formal_snapshot(), "PF6_SELECT_ZERO_WRITE")
        self.assertTrue(self.command("pf6-cancel " + str(preview["token"]))["ok"])
        self.assertEqual(before, self.formal_snapshot(), "PF6_CANCEL_ZERO_WRITE")
        suggestion = self.suggest()
        preview = self.select(suggestion, self.all_keys(suggestion))
        done = self.command("pf6-confirm " + str(preview["token"]))
        self.assertTrue(done["ok"], done)
        self.assertTrue(done["history_changed"], "PF6_ONE_HISTORY_STEP")
        self.assertEqual(before["revision"] + 1, self.read()["revision"], "PF6_ONE_REVISION")
        after = self.command("dump")["text"]
        self.assertNotEqual(before["dump"], after, "PF6_ALL_SELECTED_FORMAL_DEFINITIONS")
        self.assertEqual(12, len(self.command("references")["timbers"]), "PF6_EXACT_SELECTED_UNIQUE_COUNT")
        self.commit_line("undo")
        self.assertEqual(before["dump"], self.command("dump")["text"], "PF6_ONE_UNDO_WHOLE_BATCH")
        self.commit_line("redo")
        self.assertEqual(after, self.command("dump")["text"], "PF6_ONE_REDO_WHOLE_BATCH")

    def test_PF6_stale_selection_and_confirm_never_rebase_silently(self):
        self.fixture()
        first = self.suggest()
        self.commit_line("spec unrelated 7")
        before = self.formal_snapshot()
        reply = self.request("pf6-select", self.select_request(first, self.all_keys(first)))
        self.assertFalse(reply["ok"], "PF6_STALE_SUGGESTION")
        self.assertEqual(before, self.formal_snapshot(), "PF6_STALE_SELECTION_ZERO_WRITE")
        fresh = self.suggest()
        preview = self.select(fresh, self.all_keys(fresh))
        self.assertTrue(preview["valid"])
        self.commit_line("spec unrelated 8")
        changed = self.formal_snapshot()
        self.assertFalse(self.command("pf6-confirm " + str(preview["token"]))["ok"], "PF6_STALE_CONFIRM")
        self.assertEqual(changed, self.formal_snapshot(), "PF6_STALE_CONFIRM_ZERO_WRITE")
        for kind in ("unknown", "duplicate"):
            suggestion = self.suggest()
            keys = self.all_keys(suggestion)
            old = self.select(suggestion, keys)
            self.assertTrue(old["valid"])
            before = self.formal_snapshot()
            bad = ["not-a-candidate"] if kind == "unknown" else [keys[0], keys[0]]
            self.assertFalse(self.request("pf6-select", self.select_request(suggestion, bad))["ok"])
            self.assertFalse(self.command("pf6-confirm " + str(old["token"]))["ok"],
                             "PF6_RESELECT_REVOKES_OLDER_SELECTION: " + kind)
            self.assertEqual(before, self.formal_snapshot(), "PF6_REJECTED_RESELECT_ZERO_WRITE")

    def test_PF6_rectangle_order_geometry_and_source_intent_are_exact(self):
        self.fixture()
        suggestion = self.suggest()
        self.all_keys(suggestion)
        rows = suggestion["entries"]
        self.assertEqual(["boundary"] * 2 + ["edge-primary"] * 2 +
                         ["seam-primary"] * 6 + ["seam-secondary"] * 6,
                         [row["phase"] for row in rows], "PF6_R45_ORDER")
        self.assertEqual([], suggestion["omissions"], "PF6_ALL_FOUR_EDGES_FIXED")
        self.assertEqual(["e1", "e3", "e0", "e2"],
                         [json.loads(row["source"]["edgeKey"])[0][0] for row in rows[:4]],
                         "PF6_CANONICAL_EDGE_ORDER")
        self.assertEqual(["0"] * 3 + ["1"] * 3 + ["0"] * 3 + ["1"] * 3,
                         [row["source"]["k"] for row in rows[4:]],
                         "PF6_INTEGER_SEAM_INDICES")
        self.assertEqual(["v"] * 6 + ["u"] * 6, [row["source"]["lineAxis"] for row in rows[4:]],
                         "PF6_ROLE_IS_SEAM_COORDINATE_AXIS")
        self.assertEqual(["273", "0", "300", "300"], rows[0]["geometry"]["rect"],
                         "PF6_RIGHT_BOUNDARY_BARE_EDGE_GEOMETRY")
        self.assertEqual(["0", "0", "27", "300"], rows[1]["geometry"]["rect"],
                         "PF6_LEFT_BOUNDARY_BARE_EDGE_GEOMETRY")
        self.assertEqual([["27", "88", "273", "115"]] * 3 + [["27", "191", "273", "218"]] * 3,
                         [row["geometry"]["rect"] for row in rows[4:10]], "PF6_ODD_WIDTH_FLOOR_CEIL")
        self.assertEqual([["88", "27", "115", "88"], ["88", "115", "115", "191"],
                          ["88", "218", "115", "273"], ["191", "27", "218", "88"],
                          ["191", "115", "218", "191"], ["191", "218", "218", "273"]],
                         [row["geometry"]["rect"] for row in rows[10:]], "PF6_R6_PRIMARY_INNER_FACES")
        self.assertEqual(["61", "76", "55"] * 2, [row["geometry"]["length"] for row in rows[10:]],
                         "PF6_R6_SEAM_LENGTH")
        self.assertEqual(["150"] * 4 + ["50", "153", "253"] * 4,
                         [row["source"]["through"] for row in rows], "PF6_EACH_EFFECTIVE_RANGE_MIDPOINT")
        self.assertEqual([None, rows[4]["key"], rows[4]["key"], None, rows[7]["key"], rows[7]["key"]],
                         [row["duplicateOf"] for row in rows[4:10]], "PF6_EQUAL_R6_SPAN_ALIASES")

    def test_PF6_subset_rebuilds_longer_legal_span_without_unselected_support(self):
        self.fixture()
        suggestion = self.suggest()
        keys = self.all_keys(suggestion)
        omitted = {row["key"] for row in suggestion["entries"]
                   if row["phase"] == "seam-primary" and row["source"]["k"] == "0"}
        self.assertEqual(3, len(omitted), "PF6_ALL_SAME_PRIMARY_SOURCE_ALIASES_OMITTED")
        preview = self.select(suggestion, [key for key in keys if key not in omitted])
        self.assertTrue(preview["valid"], "PF6_FRESH_SUBSET_CAN_CHANGE_R6_SPAN: " + str(preview))
        selected = [row for row in preview["entries"] if row["selected"]]
        self.assertFalse(omitted & {row["key"] for row in selected}, "PF6_ONLY_EXPLICIT_SELECTION")
        secondary = [row for row in selected if row["phase"] == "seam-secondary"]
        self.assertEqual(["164", "164", "55"] * 2, [row["geometry"]["length"] for row in secondary],
                         "PF6_SELECTED_PREFIX_RECOMPUTES_SPAN")
        self.assertEqual([["88", "27", "115", "191"]] * 2 + [["88", "218", "115", "273"]] +
                         [["191", "27", "218", "191"]] * 2 + [["191", "218", "218", "273"]],
                         [row["geometry"]["rect"] for row in secondary], "PF6_NO_STALE_SUGGEST_GEOMETRY")
        self.confirm(preview)
        self.assertEqual(9, len(self.command("references")["timbers"]), "PF6_NO_UNSELECTED_D7_AND_FRESH_ALIASES")

    def test_PF6_each_effective_segment_retains_its_own_rejected_midpoint(self):
        self.fixture(outline="0,0 250,0 250,250 0,250")
        before = self.formal_snapshot()
        suggestion = self.suggest()
        rejected = [row for row in suggestion["entries"] if not row["valid"]]
        self.assertEqual(4, len(rejected), "PF6_SMALL_REMAINDER_HAS_FOUR_ILLEGAL_THROUGH_SEEDS")
        self.assertEqual(["seam-primary"] * 2 + ["seam-secondary"] * 2,
                         [row["phase"] for row in rejected], "PF6_ALL_REJECTIONS_DISCLOSED")
        self.assertTrue(all(row["source"]["range"] == ["206", "250"] and
                            row["source"]["through"] == "228" for row in rejected),
                        "PF6_NO_WHOLE_LINE_MIDPOINT_SUBSTITUTION")
        self.assertTrue(all(row["diagnostics"] for row in rejected), "PF6_EACH_REJECTED_SEED_HAS_REASON")
        self.assertEqual(before, self.formal_snapshot(), "PF6_REJECTED_SUGGESTION_ZERO_WRITE")
        reply = self.request("pf6-select", self.select_request(suggestion, [rejected[-1]["key"]]))
        self.assertFalse(reply["ok"], "PF6_DIAGNOSED_REJECTED_SEED_CANNOT_BE_CONFIRMED")
        keys = [row["key"] for row in suggestion["entries"] if row["valid"]]
        preview = self.select(suggestion, keys)
        self.assertTrue(preview["valid"], "PF6_LEGAL_EXPLICIT_SUBSET_REMAINS_AVAILABLE")
        self.confirm(preview)
        self.assertEqual(10, len(self.command("references")["timbers"]), "PF6_SELECTED_GOOD_SEEDS_WITH_ALIASES")

    def test_PF6_subset_without_required_support_rejects_entire_candidate(self):
        self.fixture()
        before = self.formal_snapshot()
        suggestion = self.suggest()
        self.all_keys(suggestion)
        key = next(row["key"] for row in suggestion["entries"] if row["phase"] == "seam-secondary")
        preview = self.select(suggestion, [key])
        self.assertFalse(preview["valid"], "PF6_UNSELECTED_SUPPORT_MUST_NOT_LEAK")
        self.assertTrue(preview["violations"], "PF6_REJECTION_EXPLAINS_MISSING_SUPPORT")
        self.assertFalse(self.command("pf6-confirm " + str(preview["token"]))["ok"])
        self.assertEqual(before, self.formal_snapshot(), "PF6_REJECTED_SUBSET_ZERO_WRITE")

    def test_PF6_pre_r45_post_share_one_candidate_receipt_and_history(self):
        pre, post = self.outer_fixture()
        self.assertTrue(self.command("identity-epoch " + "03" * 16)["ok"])
        before = self.formal_snapshot()
        suggestion = self.suggest(pre=pre, post=post)
        keys = self.all_keys(suggestion)
        self.assertEqual(15, len(keys), "PF6_PRE_MEMBER_SUPPRESSES_COVERED_EDGE")
        self.assertEqual(["covered-edge"], [row["phase"] for row in suggestion["omissions"]],
                         "PF6_PRE_MEMBER_IS_SAME_CANDIDATE_EVIDENCE")
        preview = self.select(suggestion, keys)
        self.assertTrue(preview["valid"], "PF6_COMPOSABLE_PRE_R45_POST: " + str(preview))
        self.assertEqual(before, self.formal_snapshot(), "PF6_OUTER_PREVIEW_ZERO_WRITE")
        self.assertEqual(before["dump"], preview["beforeScene"], "PF6_DISCLOSED_BEFORE_IS_COMPLETE")
        self.assertTrue(preview["candidateIdsAreTemporary"])
        self.assertIsNone(preview["idMap"], "PF6_ID_MAP_ONLY_AFTER_CONFIRM")
        handles = {row["tempKey"] for row in preview["createdDefinitions"]}
        self.assertIn("pre:left-edge", handles, "PF6_PRE_HANDLE")
        self.assertIn("post:after-secondary", handles, "PF6_POST_HANDLE")
        self.assertTrue(all("candidateId" in row and "id" not in row
                            for row in preview["createdDefinitions"]), "PF6_PREVIEW_IDS_TEMPORARY")
        receipt = self.confirm(preview)
        self.assertEqual(handles, {row["tempKey"] for row in receipt["actionReceipt"]["idMap"]},
                         "PF6_ALL_HANDLES_RESOLVED_AT_ONE_PUBLICATION")
        self.assertTrue(all("id" in row and "candidateId" not in row
                            for row in receipt["actionReceipt"]["idMap"]), "PF6_CONFIRMED_IDS_FORMAL")
        self.assertEqual(13, len(self.command("references")["timbers"]), "PF6_THREE_PHASE_EXACT_COUNT")
        self.assertEqual(before["revision"] + 1, self.read()["revision"], "PF6_OUTER_ONE_REVISION")
        after = self.command("dump")["text"]
        self.commit_line("undo")
        self.assertEqual(before["dump"], self.command("dump")["text"], "PF6_OUTER_ONE_UNDO")
        self.commit_line("redo")
        self.assertEqual(after, self.command("dump")["text"], "PF6_OUTER_ONE_REDO")
        self.fixture(host=True)
        self.commit_line("timber 4294967295 27 30 role boundary")
        self.commit_line("place 4294967295 on 10 " + edge_anchor("e1") + " +v +n")
        suggestion = self.suggest(pre=[outer_member("wrap-edge", edge_anchor("e3"))])
        preview = self.select(suggestion, [])
        self.assertTrue(preview["valid"], "PF6_MAX_ID_DOES_NOT_HIDE_NEW_HANDLE")
        receipt = self.confirm(preview)
        rows = receipt["actionReceipt"]["idMap"]
        self.assertEqual(["pre:wrap-edge"], [row["tempKey"] for row in rows], "PF6_MAX_ID_HANDLE_RECEIPT_COMPLETE")
        self.assertNotIn(rows[0]["id"], (0, 4294967295), "PF6_NEW_ID_HAS_EXPLICIT_PRESENCE")
        self.assertEqual({4294967295, rows[0]["id"]},
                         {row["id"] for row in self.command("references")["timbers"]}, "PF6_MAX_ID_ACTUAL_PUBLICATION")

    def test_PF6_last_outer_failure_never_publishes_successful_prefix(self):
        pre, post = self.outer_fixture()
        last = outer_member("invalid-last-side", "at-line guide 1", role="secondary",
                            direction="+v", selector="through 153")
        last["placement"]["side"] = "-n"
        post.append(last)
        self.assertTrue(self.command("identity-epoch " + "04" * 16)["ok"])
        before = self.formal_snapshot()
        suggestion = self.suggest(pre=pre, post=post)
        keys = self.all_keys(suggestion)
        self.assertEqual(15, len(keys), "PF6_PARTIAL_PREFIX_FIXTURE_IS_LEGAL")
        preview = self.select(suggestion, keys)
        self.assertFalse(preview["valid"], "PF6_PARTIAL_SUCCESS_WRITES: rejected last step rejects all phases")
        self.assertTrue(preview["violations"], "PF6_OUTER_FAILURE_REPORTED")
        self.assertFalse(self.command("pf6-confirm " + str(preview["token"]))["ok"],
                         "PF6_PARTIAL_SUCCESS_WRITES: invalid package cannot confirm")
        self.assertEqual(before, self.formal_snapshot(), "PF6_PARTIAL_SUCCESS_WRITES: zero formal state change")

    def test_PF6_post_edit_revalidates_existing_dependent_timber(self):
        self.fixture(host=True)
        self.commit_line("timber 91 27 30 role boundary")
        self.commit_line("place 91 on 10 " + edge_anchor("e3") + " +v +n")
        self.assertTrue(self.command("identity-epoch " + "05" * 16)["ok"])
        before = self.formal_snapshot()
        post = [{"op": "set-timber-fields", "id": 91,
                 "fields": {"B": {"kind": "literal", "value": 31}}}]
        suggestion = self.suggest(post=post)
        keys = self.all_keys(suggestion)
        self.assertEqual(15, len(keys), "PF6_DEPENDENCY_FIXTURE_IS_LEGAL_BEFORE_POST")
        preview = self.select(suggestion, keys)
        self.assertFalse(preview["valid"], "PF6_OMIT_DEPENDENT_REVALIDATION: existing timber B must still equal host h")
        self.assertIn("V_DERIVED_TIMBER", json.dumps(preview["violations"], ensure_ascii=False),
                      "PF6_EXISTING_DEPENDENCY_DIAGNOSIS")
        self.assertFalse(self.command("pf6-confirm " + str(preview["token"]))["ok"])
        self.assertEqual(before, self.formal_snapshot(), "PF6_INVALID_DEPENDENCY_ZERO_WRITE")

    def test_PF6_post_change_reports_final_rebuilt_geometry_before_confirmation(self):
        self.fixture(host=True)
        self.commit_line("timber 91 27 30 role boundary")
        self.commit_line("place 91 on 10 " + edge_anchor("e3") + " +v +n")
        post = [{"op": "set-timber-fields", "id": 91,
                 "fields": {"A": {"kind": "literal", "value": 30}}}]
        suggestion = self.suggest(post=post)
        keys = self.all_keys(suggestion)
        original_primary = [row for row in suggestion["entries"] if row["role"] == "primary"]
        self.assertEqual(["246"] * 8, [row["geometry"]["length"] for row in original_primary],
                         "PF6_POST_SOURCE_FIXTURE_INITIAL_SPAN")
        preview = self.select(suggestion, keys)
        self.assertTrue(preview["valid"], "PF6_LEGAL_POST_REBUILDS_DEPENDENCIES: " + str(preview))
        final_primary = [row for row in preview["entries"] if row["selected"] and row["role"] == "primary"]
        self.assertEqual(["243"] * 8, [row["geometry"]["length"] for row in final_primary],
                         "PF6_PLAN_MUST_SHOW_FINAL_POST_GEOMETRY")
        handles = {row["tempKey"]: row["candidateId"] for row in preview["createdDefinitions"]}
        dependencies = {row["id"]: row["after"] for row in preview["dependencies"]["timbers"]}
        for row in preview["entries"]:
            if not row["selected"]:
                continue
            geometry = dependencies[handles["r45:" + row["key"]]]
            self.assertEqual(int(row["geometry"]["length"]), geometry["length"],
                             "PF6_PLAN_AND_COMPLETE_DEPENDENCIES_AGREE")
        self.confirm(preview)
        refs = {row["id"]: row["geometry"] for row in self.command("references")["timbers"]}
        self.assertEqual(dependencies, refs, "PF6_PREVIEW_GEOMETRY_IS_ACTUAL_COMMIT")

    def test_PF6_outer_numeric_targets_cannot_guess_generated_ids(self):
        self.fixture()
        before = self.formal_snapshot()
        cases = [
            ([outer_member("guessed-host", edge_anchor("e3"), on=1)], []),
            ([outer_member("generated-member", edge_anchor("e3"))],
             [{"op": "set-timber-fields", "id": 1,
               "fields": {"A": {"kind": "literal", "value": 30}}}]),
        ]
        for pre, post in cases:
            with self.subTest(pre=pre, post=post):
                reply = self.request("pf6-suggest", self.suggest_request(pre=pre, post=post))
                self.assertFalse(reply["ok"], "PF6_NO_GUESSED_CANDIDATE_ID_AUTHORITY")
                self.assertEqual(before, self.formal_snapshot(), "PF6_GUESSED_ID_ZERO_WRITE")
        suggestion = self.suggest(pre=[outer_member("explicit-handle", edge_anchor("e3"))])
        preview = self.select(suggestion, self.all_keys(suggestion))
        self.assertTrue(preview["valid"], "PF6_R45_HOST_IS_EXPLICIT_GENERATED_HOST_HANDLE")
        self.assertEqual(before, self.formal_snapshot())

    def test_PF6_existing_zero_id_host_is_an_explicit_valid_source(self):
        self.fixture(host=0)
        pre = [outer_member("zero-host-edge", edge_anchor("e3"))]
        suggestion = self.suggest(pre=pre)
        preview = self.select(suggestion, self.all_keys(suggestion))
        self.assertTrue(preview["valid"], "PF6_ZERO_HOST_NOT_MISSING: " + str(preview))
        self.confirm(preview)
        hosts = self.read()["state"]["derivedPlacements"]
        self.assertEqual([0], [row["definition"]["id"] for row in hosts], "PF6_ZERO_HOST_REUSED")
        self.assertTrue(all(row["geometry"]["surface"] == 0
                            for row in self.command("references")["timbers"]), "PF6_ZERO_HOST_D7_SOURCES")

    def test_PF6_outer_anchor_cannot_guess_a_new_r45_grid_id(self):
        self.fixture()
        self.assertEqual([], self.command("references")["grids"])
        before = self.formal_snapshot()
        post = [outer_member("guessed-grid", "at-line grid 1 u 0", role="secondary",
                             direction="+v", selector="through 153")]
        suggestion = self.suggest(post=post)
        self.all_keys(suggestion)
        keys = [row["key"] for row in suggestion["entries"] if row["phase"] in ("boundary", "edge-primary")]
        self.assertEqual(4, len(keys), "PF6_GUESSED_GRID_FIXTURE_HAS_LEGAL_SUPPORTS")
        preview = self.select(suggestion, keys)
        self.assertFalse(preview["valid"], "PF6_NEW_GRID_ID_IS_NOT_AN_AUTHORED_REFERENCE")
        self.assertFalse(self.command("pf6-confirm " + str(preview["token"]))["ok"])
        self.assertEqual(before, self.formal_snapshot(), "PF6_GUESSED_GRID_ZERO_WRITE")

    def test_PF6_empty_r45_selection_can_commit_explicit_outer_members_only(self):
        self.fixture(host=True)
        pre = [outer_member("explicit-only", edge_anchor("e3"))]
        before = self.formal_snapshot()
        suggestion = self.suggest(pre=pre)
        preview = self.select(suggestion, [])
        self.assertTrue(preview["valid"], "PF6_EXPLICIT_OUTER_CAN_STAND_ALONE: " + str(preview))
        self.assertEqual("SELECTED", preview["phase"])
        self.assertEqual([], [row for row in preview["entries"] if row["selected"]])
        self.confirm(preview)
        self.assertEqual(1, len(self.command("references")["timbers"]), "PF6_ONLY_ONE_EXPLICIT_OUTER_D7")
        self.assertEqual([], self.command("references")["grids"], "PF6_EMPTY_R45_NO_IMPLICIT_GRID")
        self.assertEqual(before["revision"] + 1, self.read()["revision"])

    def test_PF6_save_and_fresh_process_reopen_ordinary_live_sources(self):
        self.fixture()
        self.commit_line("spec r45width 27")
        self.commit_line("spec r45depth 30")
        value = builder_input(A={"kind": "spec", "name": "r45width"},
                              B={"kind": "spec", "name": "r45depth"})
        suggestion = self.suggest(value)
        preview = self.select(suggestion, self.all_keys(suggestion))
        self.confirm(preview)
        saved = self.command("dump")["text"]
        before_state = self.read()["uiContract"]["state"]
        before_refs = self.command("references")
        self.assertIn("requires panel-fill/1", saved)
        timber_records = [json.loads(base64.b64decode(line.split()[2])) for line in saved.splitlines()
                          if line.startswith("engineering timber ")]
        self.assertEqual(12, len(timber_records),
                         "PF6_SAVE_ORDINARY_D7")
        self.assertEqual(12, sum(line.startswith("place ") for line in saved.splitlines()),
                         "PF6_SAVE_COMPLETE_D7_ANCHORS")
        self.assertEqual(1, sum(line.startswith("grid ") and "from-fill 1" in line
                                for line in saved.splitlines()), "PF6_SAVE_FROM_FILL_GRID")
        self.assertTrue(all(row["A"]["source"] == value["A"] for row in timber_records), "PF6_SAVE_LIVE_A_SOURCE")
        self.assertTrue(all(row["B"]["source"] == value["B"] for row in timber_records), "PF6_SAVE_LIVE_B_SOURCE")
        for forbidden in ("pf6-suggest", "panel-fill-builder-suggestions", "setKey", "candidateId", "duplicateOf"):
            self.assertNotIn(forbidden, saved, "PF6_SAVE_HAS_NO_TRANSIENT_PLAN")
        path = self.directory / "pf6-cold.scene"
        path.write_text(saved, encoding="utf-8", newline="\n")
        with BridgeSession(self.binary, cwd=self.directory) as cold:
            self.assertTrue(cold.command("loadfile " + str(path))["ok"], "PF6_COLD_LOAD")
            self.assertEqual(saved, cold.command("dump")["text"], "PF6_COLD_DEFINITION_BYTES")
            self.assertEqual(before_state, cold.command("panel-fill-read")["uiContract"]["state"],
                             "PF6_COLD_DERIVED_CLOSURE")
            refs = cold.command("references")
            for name in ("grids", "guides", "timbers", "timberSupports"):
                self.assertEqual(before_refs[name], refs[name], "PF6_COLD_" + name)
            self.assertFalse(cold.command("pf6-confirm " + str(preview["token"]))["ok"],
                             "PF6_TOKEN_IS_NOT_SAVED_AUTHORITY")
        before = self.formal_snapshot()
        for prefix in ("panel-fill 1 ", "derived-placement ", "requires panel-fill/1", "grid "):
            path.write_text("\n".join(line for line in saved.splitlines()
                                      if not line.startswith(prefix)) + "\n", encoding="utf-8", newline="\n")
            self.assertFalse(self.command("loadfile " + str(path))["ok"], "PF6_COLD_REQUIRES_COMPLETE_SOURCE: " + prefix)
            self.assertEqual(before, self.formal_snapshot(), "PF6_CORRUPT_REOPEN_ZERO_WRITE")

    def test_PF6_explicit_input_and_fresh_owner_generation_are_required(self):
        self.fixture()
        missing_a = builder_input()
        del missing_a["A"]
        invalid = [builder_input(roles={"u": "primary", "v": "primary"}),
                   builder_input(roles={"u": "secondary"}), missing_a,
                   builder_input(B={"kind": "literal", "value": 0})]
        for value in invalid:
            before = self.formal_snapshot()
            reply = self.request("pf6-suggest", self.suggest_request(value))
            self.assertFalse(reply.get("valid", reply["ok"]), "PF6_NO_INFERRED_OR_INVALID_DIMENSIONS")
            self.assertEqual(before, self.formal_snapshot(), "PF6_BAD_INPUT_ZERO_WRITE")
        first = self.suggest()
        first_keys = self.all_keys(first)
        second = self.suggest()
        self.assertNotEqual(first["setKey"], second["setKey"], "PF6_FRESH_OWNER_KEY")
        self.assertNotEqual(first["generation"], second["generation"], "PF6_FRESH_GENERATION")
        before = self.formal_snapshot()
        for field in ("setKey", "generation"):
            value = self.select_request(second, self.all_keys(second))
            value[field] = first[field]
            reply = self.request("pf6-select", value)
            self.assertFalse(reply["ok"], "PF6_OLD_OWNER_OR_GENERATION_REJECTED")
            self.assertEqual(before, self.formal_snapshot())
        reply = self.request("pf6-select", self.select_request(first, first_keys))
        self.assertFalse(reply["ok"], "PF6_PREVIOUS_SUGGESTION_INVALIDATED")

    def test_PF6_explicit_integer_dimensions_equal_typed_literal_sources(self):
        self.fixture()
        typed = self.suggest()
        bare = self.suggest(builder_input(A=27, B=30))
        self.assertEqual(typed["entries"], bare["entries"], "PF6_EXPLICIT_LITERAL_SOURCE_COMPATIBILITY")
        self.assertEqual(typed["omissions"], bare["omissions"])

    def test_PF6_foreign_confirmation_owners_cannot_publish_the_selected_batch(self):
        self.fixture()
        for owner in ("line confirm", "engineering-confirm", "panel-fill-confirm",
                      "definition-import-confirm", "timber-edit-confirm", "assembly-confirm",
                      "section-profile-confirm", "boundary-pair-confirm", "load-confirm"):
            with self.subTest(owner=owner):
                suggestion = self.suggest()
                preview = self.select(suggestion, self.all_keys(suggestion))
                self.assertTrue(preview["valid"])
                before = self.formal_snapshot()
                reply = self.command(owner + " " + str(preview["token"]))
                self.assertFalse(reply["ok"], "PF6_FOREIGN_OWNER_CANNOT_CONFIRM: " + owner)
                self.assertEqual(before, self.formal_snapshot(), "PF6_FOREIGN_OWNER_ZERO_WRITE")
                self.command("pf6-cancel " + str(preview["token"]))

    def test_PF6_free_and_hole_edges_are_explained_without_edge_material(self):
        self.fixture(outline="0,0 300,0 300,300 0,300 fixity F F X F")
        before = self.formal_snapshot()
        suggestion = self.suggest()
        free = [row for row in suggestion["omissions"] if row["phase"] == "free-edge"]
        self.assertEqual(1, len(free), "PF6_FREE_EDGE_OMITTED_EXACTLY_ONCE")
        self.assertEqual([["e2", 0, 1]], json.loads(free[0]["source"]["edgeKey"]), "PF6_FREE_EDGE_SOURCE_KEY")
        self.assertFalse(free[0]["selectable"])
        self.assertTrue(free[0]["diagnostics"])
        self.assertNotIn(free[0]["source"]["edgeKey"],
                         [row["source"]["edgeKey"] for row in suggestion["entries"]], "PF6_FREE_NO_EDGE_D7")
        self.assertEqual(before, self.formal_snapshot())
        self.fixture(extra="beam 20 along x from 140 to 160 at 150 width 20 depth 30 top 39\n",
                     obstacles=["b20"])
        before = self.formal_snapshot()
        suggestion = self.suggest()
        holes = [row for row in suggestion["omissions"] if row["phase"] == "hole-edge"]
        self.assertEqual(4, len(holes), "PF6_HOLE_HAS_FOUR_REPORTED_NONBUILDABLE_EDGES")
        self.assertTrue(all(not row["selectable"] and row["diagnostics"] for row in holes))
        self.assertTrue(all(row["source"]["edgeKey"] not in {edge["source"]["edgeKey"] for edge in holes}
                            for row in suggestion["entries"]), "PF6_HOLE_NEVER_RECEIVES_EDGE_MATERIAL")
        self.assertEqual(before, self.formal_snapshot(), "PF6_HOLE_ANALYSIS_ZERO_WRITE")

    def test_PF6_source_edge_order_uses_numeric_keys_past_single_digits(self):
        self.fixture(outline="0,0 300,0 300,50 250,50 250,100 300,100 "
                             "300,300 200,300 200,250 100,250 100,300 0,300")
        before = self.formal_snapshot()
        suggestion = self.suggest()
        for phase, expected in (("boundary", [1, 3, 5, 7, 9, 11]),
                                ("edge-primary", [0, 2, 4, 6, 8, 10])):
            keys = [json.loads(row["source"]["edgeKey"]) for row in suggestion["entries"]
                    if row["phase"] == phase]
            self.assertEqual([[["e" + str(index), 0, 1]] for index in expected], keys,
                             "PF6_R41_SOURCE_KEY_NUMERIC_ORDER: " + phase)
        self.assertEqual(before, self.formal_snapshot(), "PF6_CONCAVE_ANALYSIS_ZERO_WRITE")

    def test_PF6_negative_structure_side_maps_source_midpoints_once(self):
        self.fixture(side=-1)
        suggestion = self.suggest()
        self.all_keys(suggestion)
        primary = [row for row in suggestion["entries"] if row["phase"] == "seam-primary"]
        self.assertEqual([["27", "-114", "273", "-87"]] * 3 +
                         [["27", "-217", "273", "-190"]] * 3,
                         [row["geometry"]["rect"] for row in primary],
                         "PF6_REFLECT_SOURCE_CENTER_THEN_APPLY_AT_LINE_FLOOR")
        secondary = [row for row in suggestion["entries"] if row["phase"] == "seam-secondary"]
        self.assertEqual(["-253", "-153", "-50"] * 2,
                         [row["source"]["through"] for row in secondary], "PF6_SIGNED_MIDPOINT_FLOOR")
        preview = self.select(suggestion, self.all_keys(suggestion))
        self.assertTrue(preview["valid"], "PF6_NEGATIVE_SIDE_REAL_NATIVE_SELECTION")
        self.confirm(preview)
        self.assertTrue(all(row["geometry"]["axes"][2] == [0, 0, -1]
                            for row in self.command("references")["timbers"]), "PF6_DEPTH_ALWAYS_HOST_POSITIVE_N")

    def test_PF6_staggered_axis_is_secondary_and_band_sources_are_retained(self):
        self.fixture(pattern="stagger", stagger={"axis": "u", "value": 20})
        before = self.formal_snapshot()
        wrong = self.suggest(builder_input(roles={"u": "primary", "v": "secondary"}))
        self.assertFalse(wrong["valid"], "PF6_STAGGER_PRIMARY_REJECTED")
        self.assertEqual(before, self.formal_snapshot())
        suggestion = self.suggest()
        secondary = [row for row in suggestion["entries"] if row["phase"] == "seam-secondary"]
        self.assertTrue(secondary, "PF6_STAGGER_RETAINS_ACTUAL_SECONDARY_SEEDS")
        self.assertTrue(all(row["source"]["band"] is not None for row in secondary), "PF6_BAND_SOURCE_REQUIRED")
        self.assertGreater(len({row["source"]["band"] for row in secondary}), 1, "PF6_BANDS_NOT_COLLAPSED")
        keys = [row["key"] for row in suggestion["entries"] if row["valid"]]
        self.assertTrue(any(row["phase"] == "seam-secondary" and row["valid"] for row in suggestion["entries"]))
        preview = self.select(suggestion, keys)
        self.assertTrue(preview["valid"], "PF6_STAGGER_SELECTED_SOURCES_REBUILD: " + str(preview))
        self.confirm(preview)
        placed = [row for row in self.command("dump")["text"].splitlines()
                  if row.startswith("place ") and "at-line grid" in row and " u " in row]
        self.assertTrue(placed, "PF6_STAGGER_ORDINARY_D7_PERSISTED")
        self.assertTrue(all(" band " in row for row in placed), "PF6_SAVE_BAND_INTENT_NOT_EXPANDED_POSITION")


if __name__ == "__main__":
    unittest.main(verbosity=2)
