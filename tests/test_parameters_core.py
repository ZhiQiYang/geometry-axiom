"""Parameters are evaluated by the real native bridge, never by a test evaluator."""
import base64
import json
import os
from pathlib import Path
import sys
import unittest

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:  # `python tests/x.py` puts tests/ first, not the repo root
    sys.path.insert(0, str(_ROOT))
from tests import test_engineering_core as harness  # noqa: E402


def card(id=1, name="板材", fields=None):
    return {"op": "put-parameter", "value": {"id": id, "name": name, "fields": fields or [
        {"id": 1, "name": "寬", "type": "dimension", "input": "915"},
        {"id": 2, "name": "長", "type": "dimension", "input": "1830"},
    ]}}


def field(id, text, type="dimension", name=None):
    return {"id": id, "name": name or str(id), "type": type, "input": text}


class ParametersCore(unittest.TestCase):
    setUpClass = classmethod(harness.EngineeringCore.setUpClass.__func__)
    setUp = harness.EngineeringCore.setUp
    command = harness.EngineeringCore.command
    read = harness.EngineeringCore.read
    request = harness.EngineeringCore.request
    apply = harness.EngineeringCore.apply
    apply_line = harness.EngineeringCore.apply_line

    def values(self):
        return {(c["id"], f["id"]): f["value"] for c in self.read()["state"]["parameters"] for f in c["fields"]}

    def rejected(self, operations, message):
        before = self.command("dump")["text"]
        r = self.request(operations)
        self.assertTrue(r["ok"], r)
        self.assertFalse(r["preview"]["valid"], r)
        self.assertIn(message, json.dumps(r), r)
        self.assertFalse(self.command(f'engineering-confirm {r["preview"]["token"]}')["ok"])
        self.assertEqual(before, self.command("dump")["text"])

    def test_exact_units_cross_card_and_native_roundtrip(self):
        self.apply([card(), card(2, "排格", [field(1, "2"), field(2, "=@1:1 + @2:1"), field(3, "=(@1:1 / 2)"), field(4, "=1/3*3", "ratio"), field(5, "=-2 * (3 + 1)", "ratio")])])
        self.assertEqual({"num": "917", "den": "1", "unit": "mm"}, self.values()[2, 2])
        self.assertEqual({"num": "915", "den": "2", "unit": "mm"}, self.values()[2, 3])
        self.assertEqual("1", self.values()[2, 4]["num"])
        self.assertEqual("-8", self.values()[2, 5]["num"])
        self.apply_line("canvas-pos parameter 1 33 -9")
        before = self.command("dump")["text"]
        self.assertIn("requires parameters/1", before)
        path = self.directory / "parameters.scene"
        path.write_text(before, encoding="utf-8")
        self.assertTrue(self.command("loadfile " + str(path))["ok"])
        self.assertEqual(before, self.command("dump")["text"])

    def test_rejections_are_atomic(self):
        self.apply([card()])
        for text, type, message in [("=@1:9", "dimension", "MISSING"), ("=2 mm+1", "dimension", "UNIT"), ("=2 mm*1 mm", "dimension", "UNIT"), ("=1/2 mm", "ratio", "UNIT"), ("=1 mm/0", "dimension", "DIV_ZERO"), ("-1", "count", "COUNT"), (".5", "count", "COUNT"), ("=9223372036854775807+1", "ratio", "PRECISION")]:
            with self.subTest(text=text): self.rejected([card(2, "錯誤", [field(1, text, type)])], message)
        self.rejected([card(2, "環", [field(1, "=@2:2"), field(2, "=@2:1")])], "CYCLE")
        self.rejected([card(2, "同名", [field(1, "1", name="A"), field(2, "2", name="A")])], "DUPLICATE")

    def test_unicode_precision_capacity_and_deleted_identity(self):
        self.apply([card(fields=[field(1, "＝(1÷3)×3", "ratio"), field(2, "＝−2 mm＋1 mm".replace("＋", "+")), field(3, "0.1", "ratio")])])
        self.assertEqual("1", self.values()[1, 1]["num"])
        self.assertEqual("-1", self.values()[1, 2]["num"])
        self.assertEqual({"num":"1", "den":"10", "unit":"1"}, self.values()[1, 3])
        self.apply([card(fields=[field(1, "1", "ratio")])])
        self.rejected([card(fields=[field(1, "1", "ratio"), field(2, "2")])], "cannot be reused")
        self.rejected([card(2, fields=[field(n, "1") for n in range(17)])], "CAPACITY")
        self.rejected([card(2, fields=[field(1, "="+"("*34+"1 mm"+")"*34)])], "CAPACITY")
        self.rejected([card(2, fields=[field(1, "9223372036854775808")])], "PRECISION")

    def seed_native_block_world(self):
        """Shared scene for the two tests below: two cards, a timber whose width is sourced from a card."""
        self.apply([card(), card(2, "未使用分數", [field(1, "457.5")])])
        self.apply_line("timber 10 27 33 role boundary")
        self.apply_line("place 10 on 1 at-face e0 +u +n")
        self.apply([{"op":"set-source","target":{"kind":"timber","id":10,"field":"A"},"source":{"kind":"parameter","parameterId":1,"fieldId":1}}])
        return self.command("dump")["text"]

    def test_native_block_is_atomic_and_model_source_retains_parameters(self):
        before=self.seed_native_block_world()
        for malformed in [before.replace("parameters end\n", ""), before.replace("parameters end", "spec forbidden 2\nparameters end")]:
            path=self.directory / "broken.scene";path.write_text(malformed,encoding="utf-8")
            self.assertFalse(self.command("loadfile "+str(path))["ok"])
            self.assertEqual(before,self.command("dump")["text"])
        self.assertFalse(self.command("line parameters begin")["ok"])

    # Second half of the test above, split out so a missing model adapter shows up as a
    # visible skip instead of the assertions silently not running (it used to `return`).
    @unittest.skipUnless(os.environ.get("GEOMETRY_MODEL_BASE"), "set GEOMETRY_MODEL_BASE to a freshly built model adapter")
    def test_model_package_retains_parameters_and_verifies_hashes(self):
        from copy import deepcopy
        import sys
        sys.path.insert(0, str(harness.ROOT / "geometry-core"))
        from modeling import build_package, verify_package, ModelError, INFINITE_GRID_AXIOM_VERSIONS
        before=self.seed_native_block_world()
        package=build_package({"base_scene":before,"extensions":[]},{"roots":[{"kind":"timber","id":10}],"role":"geometry","target":"solid-set","allow_partial":False})
        self.assertIn("parameters/1",package["manifest"]["capabilities"])
        self.assertEqual(2,package["definitions"]["base_scene"].count("parameters card "))
        self.assertEqual(str(4000*915*33),package["derived"]["objects"][0]["volume_mm3"])
        self.assertEqual(package["derived"],verify_package(package)["derived"])
        previous=deepcopy(package)
        previous["manifest"]["axiom_revision"]="802f9bda1b1b8ab046f059e115dbf05a44da10df"
        previous["manifest"]["axiom_sha256"]="b19009682ba5b3e7150341ae1b5190629cb03985d500d382aa918438fb548c0b"
        self.assertEqual(package["derived"],verify_package(previous)["derived"])
        invalid=deepcopy(package);invalid["manifest"]["capabilities"].remove("parameters/1")
        with self.assertRaises(ModelError):verify_package(invalid)
        invalid=deepcopy(package);invalid["manifest"]["axiom_revision"],invalid["manifest"]["axiom_sha256"]=next(iter(INFINITE_GRID_AXIOM_VERSIONS))
        with self.assertRaises(ModelError):verify_package(invalid)

    def test_fractional_geometry_and_legacy_floor(self):
        self.apply([card(fields=[field(1, "457.5"), field(2, "=@1:1*2")])])
        self.assertFalse(self.command("line grid-system 1 name-hex 47726964 main-along none u repeat 0 param:1:1 v none")["ok"])
        self.apply_line("grid-system 1 name-hex 47726964 main-along none u repeat 0 param:1:2 v none")
        self.apply_line("datum 1 x 2*param:1:1")
        self.assertFalse(self.command("line datum 2 x param:1:1")["ok"])
        self.apply_line("spec odd 915")
        self.apply_line("datum 2 x 1/2*spec:odd")
        objects = self.command("objects")
        self.assertEqual(915, objects["gridSystems"][0]["uDefinition"]["step"])

    def test_every_infinite_axis_field_keeps_its_reference(self):
        self.apply([card(fields=[field(1,"915"),field(2,"2"),field(3,"-2")])])
        self.apply_line("grid-system 1 name-hex 47726964 main-along none u repeat-panel param:1:1 gap param:1:2 from param:1:3 v repeat param:1:3 param:1:1")
        d=self.command("objects")["gridSystems"][0]
        self.assertEqual([915,2,-2],[d["uDefinition"][k] for k in ["panel","gap","anchor"]])
        self.assertEqual({"panel","gap","anchor"},set(d["uDefinition"]["parameterRefs"]))
        self.assertEqual({"phase","step"},set(d["vDefinition"]["parameterRefs"]))
        self.rejected([{"op":"delete-parameter","id":1}],"MISSING")
        self.apply([card(fields=[field(1,"920"),field(2,"3"),field(3,"-3")])])
        d=self.command("objects")["gridSystems"][0]
        self.assertEqual([920,3,-3],[d["uDefinition"][k] for k in ["panel","gap","anchor"]])

    def test_capacity_and_package_cycle_leave_no_partial_import(self):
        self.apply([card(i,"卡"+str(i),[field(1,"1")]) for i in range(64)])
        self.rejected([card(64)],"CAPACITY")
        package={"schema":"geometry-parameters/1","cards":[{"id":100,"name":"外部","fields":[{"id":1,"name":"值","type":"dimension","expression":{"op":"literal","num":"1","den":"1","unit":"mm"}}]}]}
        self.rejected([{"op":"import-parameters","value":package}],"CAPACITY")
        self.apply([{"op":"delete-parameter","id":0}])
        package['cards'][0]['fields'][0]['expression']={"op":"ref","parameterId":100,"fieldId":1}
        self.rejected([{"op":"import-parameters","value":package}],"CYCLE")

    def test_dependencies_stale_confirm_undo_and_move(self):
        self.apply([card()])
        self.apply_line("grid-system 1 name-hex 47726964 main-along none u repeat 0 param:1:1 v repeat 0 param:1:2")
        baseline = self.command("dump")["text"]
        changed = card(fields=[field(1, "920"), field(2, "1830")])
        r = self.request([changed])["preview"]
        self.assertEqual(920, r["after"]["geometry"]["gridSystems"][0]["uDefinition"]["step"])
        self.apply_line("canvas-pos parameter 1 300 400")
        self.assertTrue(self.command(f'engineering-confirm {r["token"]}')["ok"])
        self.assertTrue(self.command("line undo")["ok"])
        self.assertEqual("915", self.values()[1, 1]["num"])
        self.assertTrue(self.command("line redo")["ok"])
        r = self.request([card()])["preview"]
        self.apply_line("spec different 3")
        self.assertEqual("STALE", self.command(f'engineering-confirm {r["token"]}')["code"])
        self.rejected([{"op": "delete-parameter", "id": 1}], "MISSING")
        self.rejected([card(fields=[field(1, "-5"), field(2, "1830")])], "invalid")

    def test_field_level_graph_and_stable_identity(self):
        self.apply([card(1, "同名", [field(1, "=@2:1"), field(2, "20")]), card(2, "同名", [field(1, "10"), field(2, "=@1:2")])])
        self.apply([card(1, "改名", [field(2, "30", name="new"), field(1, "=@2:1", name="old")])])
        self.assertEqual("30", self.values()[2, 2]["num"])
        self.rejected([card(1, "改名", [field(1, "10")])], "MISSING")

    def test_package_import_is_independent_complete_and_atomic(self):
        self.apply([card(), card(2, "排格", [field(1, "=@1:1+2 mm")])])
        cards = self.read()["state"]["parameters"]
        for c in cards:
            for f in c["fields"]: f.pop("value")
        package = {"schema": "geometry-parameters/1", "cards": cards}
        self.apply([{"op": "import-parameters", "value": package}])
        result = self.read()["state"]["parameters"]
        self.assertEqual([1, 2, 0, 3], [c["id"] for c in result])
        self.assertEqual(0, result[-1]["fields"][0]["expression"]["left"]["parameterId"])
        self.apply([card(fields=[field(1, "800"), field(2, "1600")])])
        self.assertEqual("917", self.values()[3, 1]["num"])
        self.assertEqual("802", self.values()[2, 1]["num"])
        self.apply([{"op": "import-parameters", "value": package}])
        self.assertEqual(6, len(self.read()["state"]["parameters"]))
        self.rejected([{"op": "import-parameters", "value": {**package, "cards": [cards[1]]}}], "missing dependency")

    def test_finite_grid_timber_and_unbind_roundtrip(self):
        self.apply([card(), card(2, "截面", [field(1, "27"), field(2, "33")])])
        self.apply_line("grid 1 on 1 u panel 915 gap 2 from 0 v panel 1830 gap 2 from 0")
        self.apply_line("timber 1 27 33 role boundary")
        self.apply_line("place 1 on 1 at-face e3 +v +n")
        targets = [{"kind": "grid", "id": 1, "axis": "u", "field": "panel"}, {"kind": "timber", "id": 1, "field": "A"}]
        self.apply([{"op": "set-source", "target": t, "source": {"kind": "parameter", "parameterId": i + 1, "fieldId": 1}} for i, t in enumerate(targets)])
        self.rejected([card(2, "截面", [field(1, "27.5"), field(2, "33")])], "integer mm")
        self.apply([{"op": "unbind-source", "target": targets[1]}, {"op": "delete-parameter", "id": 2}])
        self.assertEqual(1, len(self.read()["state"]["sources"]))
        self.assertIn("timber 1 27 33", self.command("dump")["text"])

    def test_position_bind_and_unbind_require_preview_without_dependents(self):
        self.apply([card()])
        baseline=self.command("dump")["text"]
        for line in ["guide 1 1 u param:1:1", "datum 1 x param:1:1", "grid-system 1 name-hex 47726964 main-along none u repeat 0 param:1:1 v none"]:
            pending=self.command("line "+line)
            self.assertIn("preview",pending)
            self.assertTrue(pending["preview"]["valid"],pending)
            self.assertEqual(baseline,self.command("dump")["text"])
            if line.startswith("datum"):
                self.assertEqual(915,pending["preview"]["datums"][0]["after"]["position"])
            self.assertTrue(self.command("line cancel-preview")["ok"])
            self.assertEqual(baseline,self.command("dump")["text"])
        self.apply_line("guide 1 1 u param:1:1")
        self.apply_line("datum 1 x param:1:1")
        self.apply_line("spec detached 915")
        for line in ["move 1 spec:detached", "datum 1 x spec:detached", "delete guide 1", "delete datum 1"]:
            pending=self.command("line "+line)
            self.assertIn("preview",pending)
            self.assertTrue(pending["preview"]["valid"],pending)
            self.assertTrue(self.command("line cancel-preview")["ok"])
        self.apply_line("move 1 spec:detached")
        self.apply_line("datum 1 x spec:detached")
        self.apply([{"op":"delete-parameter","id":1}])
        self.assertEqual(915,self.command("references")["datums"][0]["position"])

    def test_delete_refuses_a_referenced_card_and_names_every_kind_of_referrer(self):
        # GEO-258 / I38:被其他定義引用的卡片不得刪除。拒絕發生在 delete 那一步(看候選當下狀態),訊息指名引用者。
        self.apply([card(1, "被卡引用", [field(1, "915")]), card(2, "被綁定引用", [field(1, "27"), field(2, "33")]),
                    card(3, "被導線引用", [field(1, "500")]), card(4, "被格網引用", [field(1, "915")]),
                    card(5, "被基準面引用", [field(1, "700")]), card(6, "引用者", [field(1, "=@1:1 + 1 mm")])])
        self.apply_line("timber 1 27 33 role boundary")
        self.apply_line("place 1 on 1 at-face e3 +v +n")
        target = {"kind": "timber", "id": 1, "field": "A"}
        self.apply([{"op": "set-source", "target": target, "source": {"kind": "parameter", "parameterId": 2, "fieldId": 1}}])
        self.apply_line("guide 1 1 u param:3:1")
        self.apply_line("grid-system 1 name-hex 47726964 main-along none u repeat 0 param:4:1 v none")
        self.apply_line("datum 1 x param:5:1")
        for card_id, referrer in [(1, "parameter 6 field 1"), (2, "timber 1 A"), (3, "guide 1"),
                                  (4, "grid-system 1 u step"), (5, "datum 1")]:
            with self.subTest(card=card_id):
                self.rejected([{"op": "delete-parameter", "id": card_id}], "I38 MISSING: parameter %d is still referenced by %s" % (card_id, referrer))
        # 順序有意義:先解除(或改綁)再刪,同一交易內通過;先刪再解除仍拒絕。
        self.apply([card(6, "引用者", [field(1, "10")]), {"op": "delete-parameter", "id": 1}])
        self.apply([{"op": "unbind-source", "target": target}, {"op": "delete-parameter", "id": 2}])
        self.apply_line("spec detached 500")
        self.apply_line("move 1 spec:detached")
        self.apply([{"op": "delete-parameter", "id": 3}])
        self.assertEqual([4, 5, 6], [c["id"] for c in self.read()["state"]["parameters"]])
        # 多個引用者:只列前幾個,數量精確。
        self.apply([card(7, "多引用", [field(1, "1")]), card(8, "甲", [field(1, "=@7:1")]), card(9, "乙", [field(1, "=@7:1")]),
                    card(10, "丙", [field(1, "=@7:1")]), card(11, "丁", [field(1, "=@7:1")])])
        self.rejected([{"op": "delete-parameter", "id": 7}],
                      "parameter 8 field 1; parameter 9 field 1; parameter 10 field 1 and 1 more; unbind or repoint them")

    def test_delete_then_import_or_redeclare_cannot_rebind_references(self):
        # BACKLOG GEO-258 兩個反例:[delete 0, import P]、[delete 2, put-parameter{id:2}],World 內有引用指向被刪的卡。
        self.apply([card(0, "來源", [field(1, "915")]), card(1, "引用者", [field(1, "=@0:1 + 1 mm")])])
        package = {"schema": "geometry-parameters/1", "cards": [{"id": 7, "name": "外來", "fields": [
            {"id": 1, "name": "寬", "type": "dimension", "expression": {"op": "literal", "num": "1", "den": "1", "unit": "mm"}}]}]}
        before = self.values()
        self.rejected([{"op": "delete-parameter", "id": 0}, {"op": "import-parameters", "value": package}],
                      "parameter 0 is still referenced by parameter 1 field 1")
        # P-060: identity reuse is rejected before the complete-candidate reference check.
        self.rejected([{"op": "delete-parameter", "id": 0}, card(0, "換人", [field(1, "1")])],
                      "parameter 0 was deleted earlier in this transaction")
        self.assertEqual(before, self.values())
        # 沒有任何引用時刪除本身合法;但同一交易內不得把剛刪的身分再宣告,匯入也必須拿到新身分。
        self.apply([card(2, "獨立", [field(1, "5")])])
        self.rejected([{"op": "delete-parameter", "id": 2}, card(2, "換人", [field(1, "1")])],
                      "parameter 2 was deleted earlier in this transaction")
        self.apply([{"op": "delete-parameter", "id": 2}, {"op": "import-parameters", "value": package}])
        ids = [c["id"] for c in self.read()["state"]["parameters"]]
        self.assertEqual([0, 1, 3], ids)  # 2 已退役,不得被匯入重用
        # 「退役」只在那一筆候選內:之後另一筆交易可以重新宣告同一身分(沒有任何引用能指到它)。
        self.apply([{"op": "delete-parameter", "id": 3}])
        self.apply([card(3, "再宣告", [field(1, "1")])])
        self.assertEqual([0, 1, 3], [c["id"] for c in self.read()["state"]["parameters"]])

    def archive_line(self, operation):
        """The DSL entry that dispatches an arbitrary engineering operation without engineering-preview."""
        return "engineering archive " + base64.b64encode(json.dumps(operation, ensure_ascii=False).encode("utf-8")).decode("ascii")

    def test_retired_identity_never_leaks_out_of_its_candidate(self):
        # PR #193 審查:退役清單只屬於「那一筆候選」。取消、失敗的預覽,以及 DSL 入口(engineering archive)都不得殘留。
        self.apply([card(0, "獨立", [field(1, "5")])])
        preview = self.request([{"op": "delete-parameter", "id": 0}])["preview"]
        self.assertTrue(preview["valid"], preview)
        self.assertTrue(self.command("engineering-cancel %d" % preview["token"])["cancelled"])
        self.apply_line(self.archive_line(card(0, "取消後以 DSL 修改", [field(1, "6")])))
        self.assertEqual("6", self.values()[0, 1]["num"])
        self.rejected([{"op": "delete-parameter", "id": 0}, card(5, "壞", [field(1, "=@9:9")])], "MISSING")
        self.apply_line(self.archive_line(card(0, "失敗後以 DSL 修改", [field(1, "7")])))
        self.apply([card(0, "失敗後以批次修改", [field(1, "8")])])
        self.assertEqual("8", self.values()[0, 1]["num"])
        # 成功的 DSL 刪除不會替下一行 DSL／下一筆批次留下退役;批次成功刪除也一樣。
        self.apply_line(self.archive_line({"op": "delete-parameter", "id": 0}))
        self.apply_line(self.archive_line(card(0, "DSL 刪後再宣告", [field(1, "9")])))
        self.apply([{"op": "delete-parameter", "id": 0}])
        self.apply([card(0, "批次刪後再宣告", [field(1, "10")])])
        self.assertEqual([0], [c["id"] for c in self.read()["state"]["parameters"]])
        # 同一筆候選內仍然禁止(範圍是候選,不是放寬)。
        self.rejected([{"op": "delete-parameter", "id": 0}, card(0, "同候選再宣告", [field(1, "11")])],
                      "parameter 0 was deleted earlier in this transaction")

    def test_archive_parameter_update_rebuilds_values_and_dependencies_before_confirm(self):
        self.apply([card(0, "source", [field(1, "10")]),
                    card(1, "dependent", [field(1, "=@0:1 + 1 mm")])])
        self.apply_line("datum 1 x param:1:1")
        before = self.command("dump")["text"]
        preview = self.command("line preview " + self.archive_line(card(0, "source", [field(1, "20")])))
        self.assertTrue(preview["ok"], preview)
        self.assertTrue(preview["preview"]["valid"], preview)
        self.assertEqual([21], [row["after"]["position"] for row in preview["preview"]["datums"]],
                         "archive preview did not rebuild the parameter-dependent datum")
        self.assertEqual(before, self.command("dump")["text"], "archive preview changed the live World")
        self.assertEqual("10", self.values()[0, 1]["num"])
        self.assertTrue(self.command("line confirm " + str(preview["preview"]["token"]))["ok"])
        self.assertEqual("20", self.values()[0, 1]["num"], "archive confirm committed an unevaluated parameter")
        self.assertEqual("21", self.values()[1, 1]["num"])
        self.assertEqual(21, self.command("references")["datums"][0]["position"])
        after = self.command("dump")["text"]
        self.assertTrue(self.command("line undo")["ok"])
        self.assertEqual(before, self.command("dump")["text"])
        self.assertTrue(self.command("line redo")["ok"])
        self.assertEqual(after, self.command("dump")["text"])
        self.assertEqual("20", self.values()[0, 1]["num"])

    def test_archive_parameter_invalid_candidates_are_rejected_without_changing_world(self):
        self.apply([card(0, "source", [field(1, "10")])])
        self.apply_line("datum 1 x param:0:1")
        before = self.command("dump")["text"]
        revision = self.read()["revision"]
        for value, diagnostic in (("=@9:9", "MISSING"), ("=1 mm/0", "DIV_ZERO"), ("0.5", "I38 GEOMETRY")):
            with self.subTest(value=value):
                result = self.command("line preview " + self.archive_line(card(0, "invalid", [field(1, value)])))
                self.assertTrue(result["ok"], result)
                self.assertFalse(result["preview"]["valid"],
                                 "archive candidate bypassed parameter or dependent geometry validation")
                self.assertIn(diagnostic, json.dumps(result), "archive revalidation lost its precise diagnostic")
                self.assertFalse(self.command("line confirm " + str(result["preview"]["token"]))["ok"])
                self.assertEqual(before, self.command("dump")["text"])
                self.assertEqual(revision, self.read()["revision"])
                self.assertEqual("10", self.values()[0, 1]["num"])

    # ---- 驗收矩陣補列：對應 PARAMETERS-PROPOSAL.md「驗收矩陣」，逐列索引見 PARAMETERS-VALIDATION.md「驗收矩陣對應」 ----
    split_room = harness.EngineeringCore.split_room

    def sources(self):
        return [(s["target"], s["source"]["kind"], s["override"], s["effective"]) for s in self.read()["state"]["sources"]]

    def load_scene(self, text, name="matrix.scene"):
        path = self.directory / name
        path.write_text(text, encoding="utf-8")
        return self.command("loadfile " + str(path))

    def test_matrix_finite_series_explicit_keep_meaning_and_panel_layout_uses_engineering_source(self):
        self.apply([card()])
        self.apply_line("surface 2 origin 0 0 5000 u +x v +y outline 0,0 4000,0 4000,3000 0,3000")
        self.apply_line("grid 1 on 1 u series 100 200 3 v 500 1000")
        self.apply_line("grid 2 on 2 u panel 915 gap 2 from 0 v 700")
        series = self.command("references")["grids"][0]
        self.assertEqual(([100, 300, 500], [500, 1000]), (series["u"], series["v"]))
        baseline = self.command("dump")["text"]
        for line in ["grid 1 on 1 u series param:1:1 200 3", "grid 1 on 1 u series 100 param:1:1 3", "grid 1 on 1 u series 100 200 param:1:1",
                     "grid 1 on 1 u param:1:1 1000", "grid 2 on 2 u panel param:1:1 gap 2 from 0", "grid 2 on 2 u panel 915 gap param:1:1 from 0",
                     "grid 2 on 2 u panel 915 gap 2 from param:1:1"]:
            with self.subTest(line=line):
                self.assertFalse(self.command("line " + line)["ok"])
                self.assertEqual(baseline, self.command("dump")["text"])
        ref = {"kind": "parameter", "parameterId": 1, "fieldId": 1}
        for target in [{"kind": "grid", "id": 1, "axis": "u", "field": "start"}, {"kind": "grid", "id": 1, "axis": "u", "field": "step"},
                       {"kind": "grid", "id": 1, "axis": "v", "field": "panel"}, {"kind": "grid", "id": 2, "axis": "v", "field": "panel"},
                       {"kind": "grid", "id": 2, "axis": "u", "field": "anchor"}]:
            with self.subTest(target=target):
                r = self.request([{"op": "set-source", "target": target, "source": ref}])
                self.assertFalse(r["preview"]["valid"], r)
        self.assertEqual(baseline, self.command("dump")["text"])
        self.apply([{"op": "set-source", "target": {"kind": "grid", "id": 2, "axis": "u", "field": "panel"}, "source": ref}])
        self.apply([card(fields=[field(1, "920"), field(2, "1830")])])
        grids = {g["id"]: g for g in self.command("references")["grids"]}
        self.assertEqual([921, 1843, 2765, 3687], grids[2]["u"])
        self.assertEqual(([100, 300, 500], [500, 1000]), (grids[1]["u"], grids[1]["v"]))
        saved = self.command("dump")["text"]
        self.assertTrue(self.command("reset")["ok"])
        self.assertTrue(self.load_scene(saved)["ok"])
        self.assertEqual(saved, self.command("dump")["text"])
        self.assertEqual(["parameter"], [kind for _, kind, _, _ in self.sources()])

    def capacity(self, operations, accepted, message=None):
        r = self.request(operations)
        self.assertTrue(r["ok"], r)
        self.assertEqual(accepted, r["preview"]["valid"], r)
        if message:
            self.assertIn(message, json.dumps(r, ensure_ascii=False), r)

    def test_matrix_capacity_limits_accept_the_bound_and_reject_one_beyond(self):
        cap = "UNSUPPORTED/CAPACITY"
        many = lambda cards, fields: [card(i, "c%d" % i, [field(j, "1") for j in range(1, fields + 1)]) for i in range(1, cards + 1)]
        self.capacity(many(64, 1), True)
        self.capacity(many(65, 1), False, cap)
        self.capacity(many(16, 16), True)
        self.capacity(many(16, 16) + [card(17, "c17", [field(1, "1")])], False, cap)
        self.capacity(many(1, 16), True)
        self.capacity(many(1, 17), False, cap)
        self.capacity([{"op": "put-parameter", "value": {"id": 1, "name": "空", "fields": []}}], False, cap)
        # 名稱以 UTF-8 位元組計：96 合法，97 與 33 個漢字（99 bytes）不合法。注意訊息是 I38 NAME（非 UNSUPPORTED）。
        for name, accepted in [("a" * 96, True), ("字" * 32, True), ("a" * 97, False), ("字" * 33, False), ("", False)]:
            self.capacity([card(1, name)], accepted, None if accepted else "I38 NAME")
        for length, accepted in [(2047, True), (2048, False)]:
            self.capacity([card(1, "x", [field(1, "=1 mm" + " " * (length - 5))])], accepted, None if accepted else "exceeds 2047 bytes")
        self.capacity([card(1, "x", [field(1, "=" + "+".join(["1"] * 20), "ratio")])], True)
        self.capacity([card(1, "x", [field(1, "=" + "+".join(["1"] * 65), "ratio")])], False, "exceeds 128 nodes")
        for depth, accepted in [(31, True), (32, False)]:
            self.capacity([card(1, "x", [field(1, "=" + "(" * depth + "1" + ")" * depth, "ratio")])], accepted, None if accepted else "nesting exceeds 32")
        # 依賴深度（GEO-223 契約：最多 64 層）：判定必須與儲存順序、求值順序、快取命中無關。
        # 邏輯鏈 0→1→…→n-1（0 是最深端、n-1 是葉）；leaf_first 決定儲存順序：False＝深端排最前，True＝葉排最前（快取由淺往深填）。
        # 以前只有求值堆疊真的走到第 65 層才拒絕：葉排前面時 65/120/256 層全被接受。extra 另掛一個只依賴「已快取的鏈頂」的欄位。
        def chain(n, leaf_first, extra=False):
            pos = (lambda i: n - 1 - i) if leaf_first else (lambda i: i)
            slots = [None] * n
            for i in range(n):
                slots[pos(i)] = "1" if i == n - 1 else "=@%d:%d+1" % (pos(i + 1) // 16 + 1, pos(i + 1) % 16 + 1)
            if extra:  # 依賴邏輯鏈頂（鏈頂深度 n），自己是第 n+1 層；排在最後，此時鏈頂早已被快取
                slots.append("=@%d:%d+1" % (pos(0) // 16 + 1, pos(0) % 16 + 1))
            cards = []
            for c in range(0, len(slots), 16):
                cards.append(card(c // 16 + 1, "c%d" % (c // 16), [field(j + 1, t, "ratio") for j, t in enumerate(slots[c:c + 16])]))
            return cards
        for leaf_first in (False, True):
            for n, accepted in [(1, True), (63, True), (64, True), (65, False), (120, False), (256, False)]:
                with self.subTest(depth=n, leaf_first=leaf_first):
                    self.capacity(chain(n, leaf_first), accepted, None if accepted else "UNSUPPORTED/CAPACITY: dependency depth exceeds 64")
        # 快取命中也要帶出深度：64 層鏈（葉在前、全部已快取）＋一個依賴鏈頂的欄位＝65 層，必須拒絕；63 層鏈＋同款欄位＝64 層，合法。
        with self.subTest(cached_top="65"):
            self.capacity(chain(64, True, extra=True), False, "UNSUPPORTED/CAPACITY: dependency depth exceeds 64")
        with self.subTest(cached_top="64"):
            self.capacity(chain(63, True, extra=True), True)
        # 扇入（菱形）：深度是「所引用欄位深度的最大值 +1」，不是累加。一個欄位同時引用 63 層鏈頂（深度 63）與葉（深度 1）：
        # 取最大＝64 合法；若誤寫成累加＝65 會被拒。引用 64 層鏈頂＋葉＝65 必須拒絕，兩種引用順序都要（防止進出遞迴時 maxref 沒還原）。
        def fanin(n, top_first):
            cards = chain(n, True)
            top = "@%d:%d" % ((n - 1) // 16 + 1, (n - 1) % 16 + 1)
            leaf = "@1:1"
            text = "=" + (top + "+" + leaf if top_first else leaf + "+" + top)
            if len(cards[-1]["value"]["fields"]) < 16:
                cards[-1]["value"]["fields"].append(field(len(cards[-1]["value"]["fields"]) + 1, text, "ratio"))
            else:
                cards.append(card(len(cards) + 1, "fan", [field(1, text, "ratio")]))
            return cards
        for top_first in (True, False):
            with self.subTest(fanin="63+leaf", top_first=top_first):
                self.capacity(fanin(63, top_first), True)
            with self.subTest(fanin="64+leaf", top_first=top_first):
                self.capacity(fanin(64, top_first), False, "UNSUPPORTED/CAPACITY: dependency depth exceeds 64")
        self.assertEqual([], self.read()["state"]["parameters"])

    def test_matrix_scene_block_integrity_and_canvas_position_survive_reopen(self):
        self.apply([card(), card(2, "排格", [field(1, "=@1:1+2 mm")])])
        self.apply_line("canvas-pos parameter 1 33 -9")
        self.apply_line("canvas-pos parameter 2 -70 88")
        text = self.command("dump")["text"]
        lines = text.splitlines(True)
        self.assertEqual(1, sum(l.startswith("parameters begin") for l in lines))
        self.assertEqual(1, sum(l.startswith("parameters end") for l in lines))
        self.assertLess(next(i for i, l in enumerate(lines) if l.startswith("parameters begin")), next(i for i, l in enumerate(lines) if l.startswith("parameters end")))
        first_card = next(i for i, l in enumerate(lines) if l.startswith("parameters card"))
        first_field = next(i for i, l in enumerate(lines) if l.startswith("parameters field"))
        end = next(i for i, l in enumerate(lines) if l.startswith("parameters end"))
        parts = lines[first_card].split()

        def edited(change):
            copy = lines[:]
            change(copy)
            return "".join(copy)
        broken = {
            "缺 end": text.replace("parameters end\n", ""),
            "缺 begin": text.replace("parameters begin\n", ""),
            "重複 begin": text.replace("parameters begin\n", "parameters begin\nparameters begin\n"),
            "base64 被截斷": edited(lambda c: c.__setitem__(first_card, " ".join(parts[:2] + [parts[2][:-6]]) + "\n")),
            "base64 非法字元": edited(lambda c: c.__setitem__(first_card, " ".join(parts[:2] + ["!!!" + parts[2]]) + "\n")),
            "end 之後又有紀錄": edited(lambda c: c.insert(end + 1, lines[first_card])),
            "卡片紀錄被刪": edited(lambda c: c.pop(first_card)),
            "欄位紀錄被刪": edited(lambda c: c.pop(first_field)),
            "區塊內夾帶其他指令": text.replace("parameters end", "spec forbidden 2\nparameters end"),
            "canvas-pos 指向不存在的卡": text.replace("canvas-pos parameter 1 33 -9", "canvas-pos parameter 9 33 -9"),
        }
        before = self.command("dump")["text"]
        for label, scene in broken.items():
            with self.subTest(label):
                self.assertFalse(self.load_scene(scene, "broken.scene")["ok"])
                self.assertEqual(before, self.command("dump")["text"])
        self.assertTrue(self.command("reset")["ok"])
        self.assertEqual([], self.read()["state"]["parameters"])
        self.assertTrue(self.load_scene(text)["ok"])
        reopened = self.command("dump")["text"]
        self.assertEqual(text, reopened)
        self.assertEqual(["canvas-pos parameter 1 33 -9", "canvas-pos parameter 2 -70 88"], [l for l in reopened.splitlines() if l.startswith("canvas-pos parameter")])
        self.assertEqual({(1, 1): "915", (1, 2): "1830", (2, 1): "917"}, {k: v["num"] for k, v in self.values().items()})

    def test_matrix_parameter_edit_keeps_object_override_and_legacy_entries_cannot_flatten(self):
        self.split_room()
        self.apply([card(), card(2, "截面", [field(1, "27"), field(2, "33")])])
        self.apply_line("grid 1 on 1 u panel 915 gap 2 from 3300 v panel 1830 gap 2 from 0")
        self.apply_line("timber 10 27 33 role boundary")
        self.apply_line("place 10 on 1 at-face e0 +u +n")
        grid_target = {"kind": "grid", "id": 1, "axis": "u", "field": "panel"}
        timber_target = {"kind": "timber", "id": 10, "field": "A"}
        self.apply([{"op": "set-source", "target": grid_target, "source": {"kind": "parameter", "parameterId": 1, "fieldId": 1}},
                    {"op": "set-source", "target": timber_target, "source": {"kind": "parameter", "parameterId": 2, "fieldId": 1}}])
        self.apply([{"op": "set-override", "target": timber_target, "value": {"kind": "literal", "value": 30}}])
        width = lambda: next(t for t in self.command("references")["timbers"] if t["id"] == 10)["geometry"]["A"]
        self.apply([card(2, "截面", [field(1, "28"), field(2, "33")])])
        override = {"kind": "literal", "value": 30}
        self.assertIn((timber_target, "parameter", override, 30), self.sources())
        self.assertEqual(30, width())
        # 舊入口不能把有來源的物件展平成直接尺寸
        before = self.command("dump")["text"]
        for line in ["grid 1 on 1 u panel 1000 gap 2 from 3300 v panel 1830 gap 2 from 0", "timber 10 40 33 role boundary"]:
            with self.subTest(line=line):
                r = self.command("line " + line)
                self.assertFalse(r["ok"], r)
                self.assertIn("engineering source", r["error"])
                self.assertEqual(before, self.command("dump")["text"])
        # 拆面：格線隨材料片搬到新面，來源仍是參數，之後改參數仍連動，一次復原回到拆面前
        pending = self.command("line apply-proj 1 b1 cut-strip")
        self.assertTrue(pending["preview"]["valid"], pending)
        self.assertTrue(self.command("line confirm %d" % pending["preview"]["token"])["ok"])
        grid = self.command("references")["grids"][0]
        self.assertNotEqual(1, grid["surface"])
        self.assertEqual(915, grid["uDefinition"]["panel"])
        self.assertIn((grid_target, "parameter", None, 915), self.sources())
        self.apply([card(fields=[field(1, "920"), field(2, "1830")])])
        self.assertEqual(920, self.command("references")["grids"][0]["uDefinition"]["panel"])
        self.assertIn((grid_target, "parameter", None, 920), self.sources())
        self.apply_line("undo")
        self.apply_line("undo")
        self.assertEqual(before, self.command("dump")["text"])
        self.assertEqual(915, self.command("references")["grids"][0]["uDefinition"]["panel"])
        # 清除覆寫後參數重新生效；刪除角材只清自己的來源，格線的參數來源與卡片保留
        self.apply([{"op": "set-override", "target": timber_target, "value": None}])
        self.assertEqual(28, width())
        pending = self.command("line delete timber 10")
        self.assertTrue(pending["preview"]["valid"], pending)
        self.assertTrue(self.command("line confirm %d" % pending["preview"]["token"])["ok"])
        self.assertEqual([(grid_target, "parameter", None, 915)], self.sources())
        self.assertEqual(2, len(self.read()["state"]["parameters"]))

    def test_matrix_explicit_unbind_then_delete_is_one_transaction(self):
        self.apply([card(), card(2, "截面", [field(1, "27"), field(2, "33")])])
        self.apply_line("timber 1 27 33 role boundary")
        self.apply_line("place 1 on 1 at-face e3 +v +n")
        target = {"kind": "timber", "id": 1, "field": "A"}
        self.apply([{"op": "set-source", "target": target, "source": {"kind": "parameter", "parameterId": 2, "fieldId": 1}}])
        self.rejected([{"op": "delete-parameter", "id": 2}], "MISSING")
        before = self.command("dump")["text"]
        # P-062 adopts both orders; deletion-time values are candidate-only and require explicit unbind.
        revision = self.read()["revision"]
        r = self.request([{"op": "delete-parameter", "id": 2}, {"op": "unbind-source", "target": target}])
        self.assertTrue(r["preview"]["valid"], r)
        self.assertEqual(before, self.command("dump")["text"])
        self.assertEqual(revision, self.read()["revision"])
        self.assertTrue(self.command("engineering-cancel " + str(r["preview"]["token"]))["cancelled"])
        self.assertEqual(before, self.command("dump")["text"])
        self.assertEqual(revision, self.read()["revision"])
        self.apply([{"op": "unbind-source", "target": target}, {"op": "delete-parameter", "id": 2}])
        self.assertEqual(revision + 1, self.read()["revision"])
        after = self.command("dump")["text"]
        self.assertEqual([1], [c["id"] for c in self.read()["state"]["parameters"]])
        self.assertEqual([], self.read()["state"]["sources"])
        self.assertIn("timber 1 27 33", after)
        self.apply_line("undo")
        self.assertEqual(before, self.command("dump")["text"])
        self.assertEqual([(target, "parameter", None, 27)], self.sources())
        self.apply_line("redo")
        self.assertEqual(after, self.command("dump")["text"])

        self.apply_line("undo")
        self.assertEqual(before, self.command("dump")["text"])
        revision = self.read()["revision"]
        self.apply([{"op": "delete-parameter", "id": 2}, {"op": "unbind-source", "target": target}])
        self.assertEqual(revision + 1, self.read()["revision"])
        self.assertEqual(after.encode("utf-8"), self.command("dump")["text"].encode("utf-8"))
        self.apply_line("undo")
        self.assertEqual(before, self.command("dump")["text"])
        self.apply_line("redo")
        self.assertEqual(after, self.command("dump")["text"])

    def test_matrix_unknown_scene_versions_are_rejected_and_capability_is_rederived_never_dropped(self):
        self.apply([card()])
        text = self.command("dump")["text"]
        self.assertTrue(self.command("reset")["ok"])
        before = self.command("dump")["text"]
        for label, scene in {"parameters/2": text.replace("requires parameters/1", "requires parameters/2"),
                             "parameters/0": text.replace("requires parameters/1", "requires parameters/0"),
                             "1 與 2 並存": text.replace("requires parameters/1", "requires parameters/1\nrequires parameters/2")}.items():
            with self.subTest(label):
                r = self.load_scene(scene)
                self.assertFalse(r["ok"], r)
                self.assertIn("unsupported required scene capability", r["error"])
                self.assertEqual(before, self.command("dump")["text"])
        # 拿掉 requires 行不會降級成沒有參數的世界：區塊照常完整載入，重新輸出時補回宣告
        self.assertTrue(self.load_scene(text.replace("requires parameters/1\n", ""))["ok"])
        self.assertEqual(text, self.command("dump")["text"])
        self.assertEqual({(1, 1): "915", (1, 2): "1830"}, {k: v["num"] for k, v in self.values().items()})

    def test_matrix_impact_list_carries_guide_direction_coordinates_visible_segments_and_subgrid(self):
        self.apply([card(), card(2, "截面", [field(1, "27"), field(2, "33")])])
        self.apply_line("grid 1 on 1 u panel 915 gap 2 from 0 v panel 1830 gap 2 from 0")
        self.apply([{"op": "set-source", "target": {"kind": "grid", "id": 1, "axis": "u", "field": "panel"}, "source": {"kind": "parameter", "parameterId": 1, "fieldId": 1}}])
        self.apply_line("guide 1 1 v grid:1:u:1")
        self.apply_line("guide 2 1 u param:1:1")
        self.apply_line("subgrid 5 parent 1 cell u min line:0 v min line:0 divisions u 2 v 1")
        pv = self.request([card(fields=[field(1, "925"), field(2, "1830")])])["preview"]
        self.assertTrue(pv["valid"], pv)
        guides = lambda side: {g["id"]: g for g in pv[side]["geometry"]["guides"]}
        grids = lambda side: {g["id"]: g for g in pv[side]["geometry"]["grids"]}
        old, new = guides("before"), guides("after")
        for gid, axis, direction, old_point, new_point in [(1, "v", [0, 1, 0], [1833, 0, 2500], [1853, 0, 2500]), (2, "u", [1, 0, 0], [0, 915, 2500], [0, 925, 2500])]:
            for guide, point in ((old[gid], old_point), (new[gid], new_point)):
                self.assertEqual((axis, direction, point), (guide["axis"], guide["worldDirection"], guide["worldPoint"]))
            self.assertEqual([[[1833, 0], [1833, 3000]]], old[1]["segments"])
        self.assertEqual([[[1853, 0], [1853, 3000]]], new[1]["segments"])
        self.assertEqual([[[0, 915], [4000, 915]]], old[2]["segments"])
        self.assertEqual([[[0, 925], [4000, 925]]], new[2]["segments"])
        self.assertEqual({1, 5}, set(grids("after")))
        self.assertEqual(([458], [463]), (grids("before")[5]["u"], grids("after")[5]["u"]))
        self.assertEqual({"u": [0, 916], "v": [0, 1831]}, grids("before")[5]["bounds"])
        self.assertEqual({"u": [0, 926], "v": [0, 1831]}, grids("after")[5]["bounds"])
        self.assertEqual(([5], [1]), (grids("after")[1]["dependencies"]["children"], grids("after")[1]["dependencies"]["guides"]))


if __name__ == "__main__":
    unittest.main()
