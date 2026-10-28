"""UI-1 native/wire contract; this is not a receipt for the real App UI flow.

Legacy views stay numeric. The versioned view transports int64 quantities as
decimal strings and reports the scope it actually computed, including failures.
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests import test_panel_fill_layout as pf2


class PanelFillUiContract(unittest.TestCase):
    setUpClass = pf2.PanelFillLayout.__dict__["setUpClass"]
    setUp = pf2.PanelFillLayout.setUp
    command = pf2.PanelFillLayout.command
    load_text = pf2.PanelFillLayout.load_text
    read = pf2.PanelFillLayout.read
    snapshot = pf2.PanelFillLayout.snapshot
    preview = pf2.PanelFillLayout.preview
    apply = pf2.PanelFillLayout.apply
    seed = pf2.PanelFillLayout.seed

    def contract(self, response, complete=True):
        ui = response["uiContract"]
        self.assertEqual("panel-fill-workspace/1", ui["schema"], "UI_WIRE_SCHEMA")
        self.assertEqual(["read", "edit-definitions", "read-layout", "read-support"],
                         ui["supportedActions"], "UI_WIRE_ACTIONS: no PF-4/5/6 promises")
        self.assertEqual(str(response["revision"]), ui["revision"], "UI_WIRE_REVISION_EXACT")
        self.assertIs(ui["completeForScope"], complete, "UI_WIRE_COMPLETENESS")
        if complete:
            self.assertEqual([], ui["errors"], "UI_WIRE_NO_HIDDEN_ERROR")
        return ui

    def test_read_scoped_delivery_does_not_claim_full_product(self):
        self.seed()
        self.apply([pf2.fill()])
        before = self.snapshot()
        read = self.read()
        ui = self.contract(read)
        self.assertIs(read["complete"], False, "UI_WIRE_GLOBAL_INCOMPLETE")
        self.assertEqual({"finishSurfaceIds": [1], "fillIds": [1]}, ui["scope"])
        self.assertEqual("pending", read["layerJudgement"]["status"])
        self.assertEqual([], ui["state"]["derivedPlacements"])
        self.assertEqual(before, self.snapshot(), "UI_WIRE_READ_IS_READONLY")
        old = read["state"]["panelFills"][0]
        exact = ui["state"]["panelFills"][0]
        self.assertEqual(old["definition"], exact["definition"], "UI_WIRE_SOURCE_TYPES_UNCHANGED")
        self.assertIsInstance(old["derived"]["thickness"], int)
        self.assertEqual("9", exact["derived"]["thickness"])
        self.assertEqual(9, exact["derived"]["tileCount"])
        self.assertEqual([1, "0", "0"], exact["derived"]["tiles"][0]["key"])
        self.assertEqual([0, 0, 0], read["state"]["finishSurfaces"][0]["frame"]["origin"])
        self.assertEqual(["0", "0", "0"], ui["state"]["finishSurfaces"][0]["frame"]["origin"])
        for seam in exact["derived"]["seamLines"]:
            self.assertIsInstance(seam["coordinate"], str)
            self.assertIsInstance(seam["k"], str)
        for part in exact["derived"]["support"]:
            self.assertIsInstance(part["left"], str)
            self.assertIsInstance(part["right"], str)
            self.assertTrue(all(isinstance(v, str) for v in part["range"]))
        self.assertEqual({"num": "8", "den": "1"}, exact["derived"]["threshold"])
        self.assertNotIn("threshold", old["derived"], "UI_WIRE_LEGACY_FIELDS_UNCHANGED")

    def test_preview_scope_includes_deleted_and_created_records(self):
        self.seed()
        self.apply([pf2.fill()])
        before = self.snapshot()
        preview = self.preview([
            {"op": "delete-panel-fill", "id": 1},
            {"op": "delete-finish-surface", "id": 1},
            pf2.put(pf2.surface(identifier=2, boundary=8, origin=(0, 0, 0), obstacles=[])),
            pf2.fill(id=2, finishSurfaceId=2),
        ])
        self.assertIs(preview["valid"], True)
        ui = self.contract(preview)
        self.assertEqual({"finishSurfaceIds": [1, 2], "fillIds": [1, 2]}, ui["scope"],
                         "UI_WIRE_SCOPE_UNION: deletion is part of this candidate")
        self.assertEqual([1], [x["id"] for x in ui["before"]["finishSurfaces"]])
        self.assertEqual([2], [x["id"] for x in ui["after"]["finishSurfaces"]])
        self.assertEqual(before, self.snapshot())
        self.assertTrue(self.command("panel-fill-cancel %d" % preview["token"])["ok"])
        self.assertEqual(before, self.snapshot(), "UI_WIRE_CANCEL_NO_MUTATION")

    def test_invalid_candidate_is_incomplete_with_typed_error(self):
        self.seed()
        before = self.snapshot()
        preview = self.preview([pf2.put(pf2.surface(boundary=8, origin=(0, 0, 0), side=0, obstacles=[]))])
        self.assertIs(preview["valid"], False)
        ui = self.contract(preview, complete=False)
        error = next(e for e in ui["errors"] if e["recordType"] == "transaction")
        self.assertIsNone(error["id"])
        self.assertEqual("after", error["stage"])
        self.assertEqual("PANEL_FILL_INVALID", error["code"])
        self.assertTrue(error["clause"])
        self.assertTrue(error["expected"])
        self.assertEqual(preview["violations"][0]["message"], error["actual"],
                         "UI_WIRE_ORIGINAL_DIAGNOSTIC")
        self.assertEqual(["PANEL_FILL_INVALID"], error["missing"])
        self.assertFalse(self.command("panel-fill-confirm %d" % preview["token"])["ok"])
        self.assertEqual(before, self.snapshot())

    def test_exact_large_area_survives_native_json_and_javascript(self):
        # D1-valid rectangle. Odd area is above 2**53 and cannot be represented
        # by a JavaScript Number; a decimal spelling inferred later is too late.
        self.seed(width=100000000, length=100000000,
                  outline="0,0 99999999,0 99999999,99999997 0,99999997")
        self.apply([pf2.fill(gap=0)])
        read = self.read()
        ui = self.contract(read)
        old = read["state"]["panelFills"][0]["derived"]["tiles"][0]["fragments"][0]
        exact = ui["state"]["panelFills"][0]["derived"]["tiles"][0]["fragments"][0]
        self.assertEqual(9999999600000003, old["area"], "UI_WIRE_LEGACY_NUMBER_UNCHANGED")
        self.assertEqual("9999999600000003", exact["area"], "UI_WIRE_INT64_EXACT")
        self.assertTrue(all(isinstance(v, str) for xy in exact["outer"] for v in xy))
        node = shutil.which("node")
        self.assertIsNotNone(node, "UI_WIRE_JS: Node is required for the cross-language exactness assertion")
        result = subprocess.run([node, "-e", """
const fs = require('fs');
const r = JSON.parse(fs.readFileSync(0, 'utf8'));
const area = r.uiContract.state.panelFills[0].derived.tiles[0].fragments[0].area;
if (typeof area !== 'string' || area !== '9999999600000003') process.exit(1);
if (BigInt(area) !== 9999999600000003n) process.exit(2);
if (Number.isSafeInteger(r.state.panelFills[0].derived.tiles[0].fragments[0].area)) process.exit(3);
"""], input=json.dumps(read), text=True, capture_output=True, check=False)
        self.assertEqual(0, result.returncode, "UI_WIRE_JS_EXACT: " + result.stdout + result.stderr)

    def test_host_zero_id_and_exact_height_are_not_missing(self):
        self.seed()
        self.apply([pf2.fill(), {"op": "put-derived-placement", "value": {"id": 0, "fillId": 1, "h": 30}}])
        read = self.read()
        ui = self.contract(read)
        host = ui["state"]["derivedPlacements"][0]
        self.assertEqual(0, host["id"])
        self.assertEqual(0, ui["state"]["panelFills"][0]["derived"]["derivedPlacement"])
        self.assertEqual({"id": 0, "fillId": 1, "h": 30}, host["definition"])
        self.assertEqual("30", host["derived"]["h"])
        self.assertEqual(["0", "0", "9"], host["derived"]["frame"]["origin"])
        self.assertTrue(all(e["key"] is not None for c in host["derived"]["components"] for e in c["edges"]))

    def test_fractional_threshold_is_the_native_effective_value(self):
        self.seed()
        self.apply([pf2.fill()])
        request = self.directory / "threshold.json"
        request.write_text(json.dumps({"schema": "engineering-transaction/1", "expectedRevision": self.read()["revision"],
            "operations": [{"op": "put-parameter", "value": {"id": 90, "name": "門檻",
                "fields": [{"id": 1, "name": "X", "type": "dimension", "input": "17/2"}]}}]}), encoding="utf-8")
        reply = self.command("engineering-preview " + str(request))
        self.assertTrue(reply["ok"] and reply["preview"]["valid"], reply)
        self.assertTrue(self.command("engineering-confirm %d" % reply["preview"]["token"])["ok"])
        value = self.contract(self.read())["state"]["panelFills"][0]
        self.assertEqual({"parameterId": 90, "fieldId": 1}, value["definition"]["threshold"])
        self.assertEqual({"num": "17", "den": "2"}, value["derived"]["threshold"], "UI_WIRE_X_NOT_ROUNDED")
        candidate = self.preview([pf2.fill(origin=[1, 0])])
        ui = self.contract(candidate)
        for stage in ["before", "after"]:
            self.assertEqual({"num": "17", "den": "2"}, ui[stage]["panelFills"][0]["derived"]["threshold"])

    def test_native_allocators_skip_occupied_ids_and_wrap_without_zero(self):
        self.seed()
        self.apply([pf2.put(pf2.surface(identifier=4294967295, boundary=8, origin=(0, 0, 0), obstacles=[])),
                    pf2.fill(), pf2.fill(id=4294967295)])
        before = self.snapshot()
        ids = self.command("newid")
        self.assertTrue(ids["ok"])
        self.assertEqual(2, ids["finishSurface"], "UI_WIRE_FINISH_ID_WRAP")
        self.assertEqual(2, ids["panelFill"], "UI_WIRE_FILL_ID_WRAP")
        self.assertIsInstance(ids["placement"], int)
        self.assertEqual(before, self.snapshot(), "UI_WIRE_ALLOCATOR_IS_READONLY")

    def test_saved_definitions_recompute_the_same_exact_view(self):
        self.seed()
        self.apply([pf2.fill(), {"op": "put-derived-placement", "value": {"id": 10, "fillId": 1, "h": 30}}])
        expected = self.contract(self.read())["state"]
        text = self.command("dump")["text"]
        self.assertNotIn("uiContract", text)
        self.assertNotIn("completeForScope", text)
        self.assertTrue(self.command("reset")["ok"])
        self.load_text(text, "reopen.scene")
        self.assertEqual(expected, self.contract(self.read())["state"], "UI_WIRE_REOPEN_RECOMPUTES")

    def test_definition_reader_is_separate_from_full_product_capabilities(self):
        self.seed()
        self.apply([pf2.fill(), {"op": "put-derived-placement", "value": {"id": 10, "fillId": 1, "h": 30}}])
        before = self.snapshot()
        path = self.directory / "reader.scene"
        path.write_text(before[0], encoding="utf-8")
        candidate = self.command("load-prepare " + str(path))
        self.assertTrue(candidate["ok"], candidate)
        expected_reader = {
            "schema": "panel-fill-definition-reader/1", "capability": "panel-fill/1",
            "supportedRecords": ["finish-surface", "panel-fill", "derived-placement"], "complete": False,
        }
        original_capabilities = ["engineering-spec/1", "parameters/1", "assembly-rule-authoring/1",
                                 "assembly-timber-generation/1", "grid-subdivision-rules/1",
                                 "section-profile/1", "grid-card-reference/1"]
        for response in [self.read(), self.command("engineering-read")["state"], candidate]:
            self.assertEqual(original_capabilities, response["capabilities"], "UI_READER_NO_FULL_PF_CLAIM")
            self.assertEqual(expected_reader, response["panel_fill_reader"], "UI_READER_RECORD_CLOSURE")
            self.assertIn("panel-fill/1", response["required_capabilities"])
        self.assertEqual(before[0], candidate["final_scene"], "UI_READER_CANONICAL_DEFINITIONS")
        self.assertEqual(before, self.snapshot(), "UI_READER_DETACHED_CANDIDATE")
        self.assertTrue(self.command("load-cancel %d" % candidate["token"])["ok"])
        self.assertEqual(before, self.snapshot())


if __name__ == "__main__":
    unittest.main()
