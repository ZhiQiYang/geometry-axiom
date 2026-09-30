"""Parameters are evaluated by the real native bridge, never by a test evaluator."""
import json
import unittest
from tests import test_engineering_core as harness


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
    stop = harness.EngineeringCore.stop
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

    def test_native_block_is_atomic_and_model_source_retains_parameters(self):
        from copy import deepcopy
        import sys
        sys.path.insert(0, str(harness.ROOT / "geometry-core"))
        from modeling import build_package, verify_package, ModelError, INFINITE_GRID_AXIOM_VERSIONS
        self.apply([card(), card(2, "未使用分數", [field(1, "457.5")])])
        self.apply_line("timber 10 27 33 role boundary")
        self.apply_line("place 10 on 1 at-face e0 +u +n")
        self.apply([{"op":"set-source","target":{"kind":"timber","id":10,"field":"A"},"source":{"kind":"parameter","parameterId":1,"fieldId":1}}])
        before=self.command("dump")["text"]
        for malformed in [before.replace("parameters end\n", ""), before.replace("parameters end", "spec forbidden 2\nparameters end")]:
            path=self.directory / "broken.scene";path.write_text(malformed,encoding="utf-8")
            self.assertFalse(self.command("loadfile "+str(path))["ok"])
            self.assertEqual(before,self.command("dump")["text"])
        self.assertFalse(self.command("line parameters begin")["ok"])
        if not __import__('os').environ.get('GEOMETRY_MODEL_BASE'):
            return
        package=build_package({"base_scene":before,"extensions":[]},{"roots":[{"kind":"timber","id":10}],"role":"geometry","target":"solid-set","allow_partial":False})
        self.assertIn("parameters/1",package["manifest"]["capabilities"])
        self.assertEqual(2,package["definitions"]["base_scene"].count("parameters card "))
        self.assertEqual(str(4000*915*33),package["derived"]["objects"][0]["volume_mm3"])
        self.assertEqual(package["derived"],verify_package(package)["derived"])
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


if __name__ == "__main__":
    unittest.main()
