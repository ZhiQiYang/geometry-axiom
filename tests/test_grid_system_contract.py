"""Independent D29/I37/R32 acceptance against the actual native bridge.

GEOMETRY_TEST_BRIDGE points to a fresh executable (or a WSL launcher).
GEOMETRY_TEST_SERVER_PATH_STYLE=wsl translates temporary load/request paths.
No coordinate oracle calls the implementation's grid evaluator.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def system(identifier=0, name="天花 網格 A", u="series 100 200 3", v="explicit 200 600", main="none"):
    return f"grid-system {identifier} name-hex {name.encode('utf-8').hex()} main-along {main} u {u} v {v}"


def native_path(path):
    value = str(path)
    if os.environ.get("GEOMETRY_TEST_SERVER_PATH_STYLE") == "wsl" and len(value) > 2 and value[1] == ":":
        return "/mnt/" + value[0].lower() + "/" + value[3:].replace("\\", "/")
    return value


class GridSystemContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        override = os.environ.get("GEOMETRY_TEST_BRIDGE")
        if override:
            cls.bridge = override
            return
        cc = shutil.which("cc")
        if not cc:
            raise unittest.SkipTest("set GEOMETRY_TEST_BRIDGE to a freshly built bridge")
        cls.build = tempfile.TemporaryDirectory(prefix="geometry-grid-build-")
        cls.addClassCleanup(cls.build.cleanup)
        cls.bridge = str(Path(cls.build.name) / "bridge")
        subprocess.run([cc, "-std=c11", "-O0", str(ROOT / "geometry-web/web_bridge.c"), "-lm", "-o", cls.bridge], check=True, capture_output=True)

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="geometry-grid-contract-")
        self.addCleanup(self.directory.cleanup)
        self.stderr = tempfile.TemporaryFile()
        self.addCleanup(self.stderr.close)
        self.proc = subprocess.Popen([self.bridge], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=self.stderr, text=True, encoding="utf-8")
        self.addCleanup(self.stop)
        self.assertTrue(self.command("reset")["ok"])

    def stop(self):
        self.proc.stdin.close()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
        self.proc.stdout.close()
        self.stderr.close()

    def command(self, command):
        self.proc.stdin.write(command + "\n")
        self.proc.stdin.flush()
        answer = self.proc.stdout.readline()
        if not answer:
            self.stderr.seek(0)
            self.fail("Bridge exited: " + self.stderr.read().decode("utf-8", errors="replace"))
        return json.loads(answer)

    def line(self, command):
        return self.command("line " + command)

    def commit(self, command):
        result = self.line(command)
        if "preview" in result:
            self.assertTrue(result["preview"]["valid"], result)
            result = self.line("confirm " + str(result["preview"]["token"]))
        self.assertTrue(result["ok"], (command, result))
        return result

    def dump(self):
        result = self.command("dump")
        self.assertTrue(result["ok"], result)
        return result["text"]

    def refs(self):
        return self.command("references")

    def objects(self):
        return self.command("objects")

    def grids(self):
        return {row["id"]: row for row in self.refs()["grids"]}

    def snapshot(self):
        # Definition bytes and resolved geometry must both survive a rejected edit.
        return self.dump(), self.refs(), self.objects()

    def surface(self, identifier, outline="0,0 4000,0 4000,3000 0,3000"):
        self.commit(f"surface {identifier} origin 0 0 0 u +x v +y outline {outline}")

    def pair(self, command=None):
        self.surface(1)
        self.surface(2)
        self.commit(command or system())
        self.commit("grid 10 on 1 from-system 0 origin 0 0")
        self.commit("grid 20 on 2 from-system 0 origin 100 200")

    def preview(self, command):
        before = self.snapshot()
        response = self.line("preview " + command)
        self.assertIn("preview", response, response)
        self.assertEqual(before, self.snapshot(), "a preview must not mutate any live definition or geometry")
        return response["preview"]

    def reject(self, command):
        before = self.snapshot()
        response = self.line(command)
        self.assertFalse(response.get("ok") and response.get("preview", {}).get("valid", True), response)
        if "preview" in response:
            self.assertFalse(self.line("confirm " + str(response["preview"]["token"]))["ok"])
        self.assertEqual(before, self.snapshot(), command)

    def roundtrip(self):
        before = self.snapshot()
        path = Path(self.directory.name) / "grid system.scene"
        path.write_text(before[0], encoding="utf-8")
        self.assertTrue(self.command("reset")["ok"])
        self.assertEqual([], self.objects()["gridSystems"])
        self.assertEqual([], self.refs()["grids"])
        loaded = self.command("loadfile " + native_path(path))
        self.assertTrue(loaded["ok"], loaded)
        self.assertEqual(before, self.snapshot())

    def test_three_independent_layouts_names_zero_id_and_no_hidden_surface(self):
        cases = [
            (0, "中文 名稱 甲", "explicit -200 0 300", "none", "v"),
            (7, "有限 等差", "series -100 200 4", "explicit 900", "u"),
            (4294967295, "面材 ＆ 接縫", "panel 400 gap 5 from -100", "panel 900 gap 3 from 50", "none"),
        ]
        for identifier, name, u, v, main in cases:
            self.commit(system(identifier, name, u, v, main))
        objects = self.objects()
        self.assertEqual([], objects["faces"])
        self.assertNotIn("boundary ", self.dump())
        self.assertNotIn("placement ", self.dump())
        self.assertEqual([], self.refs()["grids"])
        records = {row["id"]: row for row in objects["gridSystems"]}
        self.assertEqual({0, 7, 4294967295}, set(records))
        self.assertEqual({identifier: name for identifier, name, *_ in cases}, {i: r["name"] for i, r in records.items()})
        self.assertEqual({"source": "series", "start": -100, "step": 200, "count": 4}, records[7]["uDefinition"])
        self.assertEqual({"source": "panel", "panel": 400, "gap": 5, "anchor": -100, "anchorExplicit": True}, records[4294967295]["uDefinition"])
        self.assertTrue(all(row["kind"] == "grid-system" and row["applications"] == [] for row in records.values()))
        self.assertNotIn(self.command("newid")["gridSystem"], records)
        self.commit("canvas-pos grid-system 0 -80 240")
        positioned = next(x for x in self.objects()["gridSystems"] if x["id"] == 0)
        self.assertEqual((-80, 240, True), (positioned["cx"], positioned["cy"], positioned["hasPos"]))
        self.roundtrip()

    def test_invalid_definitions_limits_and_missing_sources_are_atomic(self):
        invalid_axes = ["explicit 1 1", "explicit 2 1", "series 0 0 2", "series 0 -1 2",
                        "series 0 1 0", "series 0 1 65", "series 99999999 2 2",
                        "series 0 9223372036854775807 2", "panel 0 gap 0 from 0",
                        "panel 10 gap -1 from 0", "panel 10 gap 0", "explicit 100000001",
                        "explicit " + " ".join(str(i) for i in range(65))]
        for axis in invalid_axes:
            with self.subTest(axis=axis):
                self.reject(system(u=axis, v="none"))
        for command in [system(u="none", v="none"), system(u="explicit 100", v="none", main="u"),
                        system(name=""), system(name="界" * 33), system().replace("name-hex " + "天花 網格 A".encode().hex(), "name-hex ff"),
                        system().replace("name-hex " + "天花 網格 A".encode().hex(), "name-hex 610a62"),
                        system().replace("name-hex " + "天花 網格 A".encode().hex(), "name-hex 610062"),
                        system().replace("grid-system 0", "grid-system 4294967296"),
                        "grid 1 on 1 from-system 0 origin 0 0"]:
            with self.subTest(command=command):
                self.reject(command)
        self.commit(system(name="界" * 32))
        self.reject("grid 1 on 1 from-system 0 origin 0 0")
        self.surface(1)
        self.reject("grid 1 on 1 from-system 99 origin 0 0")
        self.reject("grid 1 on 1 from-system 0 origin 100000000 0")
        for identifier in range(1, 16):
            self.commit(system(identifier=identifier))
        self.reject(system(identifier=16))
        self.assertEqual(16, len(self.objects()["gridSystems"]))

    def test_line_limit_applies_when_panel_system_gets_a_surface(self):
        self.surface(1)
        self.commit(system(u="series 0 1 64", v="none"))
        self.commit("grid 10 on 1 from-system 0 origin 0 0")
        self.assertEqual(list(range(64)), self.grids()[10]["u"])
        self.commit(system(1, u="panel 1 gap 0 from 0", v="none"))
        self.surface(2)
        self.reject("grid 20 on 2 from-system 1 origin 0 0")
        self.assertEqual([], next(x for x in self.objects()["gridSystems"] if x["id"] == 1)["applications"])

    def test_failed_reload_preserves_live_source_and_all_applications(self):
        self.pair()
        before = self.snapshot()
        path = Path(self.directory.name) / "invalid-source.scene"
        path.write_text(before[0].replace("from-system 0 origin 100 200", "from-system 99 origin 100 200"), encoding="utf-8")
        self.assertFalse(self.command("loadfile " + native_path(path))["ok"])
        self.assertEqual(before, self.snapshot())

    def test_two_applications_origins_reference_identity_and_serialization(self):
        self.pair()
        grids = self.grids()
        for identifier, origin, u, v in [(10, [0, 0], [100, 300, 500], [200, 600]),
                                         (20, [100, 200], [200, 400, 600], [400, 800])]:
            self.assertEqual((0, origin, u, v), (grids[identifier]["sourceSystem"], grids[identifier]["origin"], grids[identifier]["u"], grids[identifier]["v"]))
        self.assertEqual([{"grid": 10, "surface": 1}, {"grid": 20, "surface": 2}], self.objects()["gridSystems"][0]["applications"])
        scene = self.dump()
        self.assertLess(scene.index("grid-system 0 "), scene.index("grid 10 on 1 from-system"))
        self.assertIn("grid 10 on 1 from-system 0 origin 0 0", scene)
        self.assertIn("grid 20 on 2 from-system 0 origin 100 200", scene)
        self.assertNotIn("grid 10 on 1 u ", scene, "derived coordinates cannot become persisted sources")
        self.reject("grid 11 on 1 from-system 0 origin 0 0")
        self.roundtrip()

    def test_panel_anchor_and_true_l_shape_hole_segments(self):
        self.surface(1, "0,0 4000,0 4000,1000 2000,1000 2000,3000 0,3000")
        self.surface(2, "0,0 4000,0 4000,3000 0,3000 hole 1000,1000 2000,1000 2000,2000 1000,2000")
        self.commit(system(u="explicit 1500 2500", v="explicit 500 1500 2500"))
        self.commit("grid 10 on 1 from-system 0 origin 0 0")
        self.commit("grid 20 on 2 from-system 0 origin 0 0")
        segments = lambda g, axis, index: next(line["segments"] for line in g["lines"] if line["axis"] == axis and line["index"] == index)
        grids = self.grids()
        self.assertEqual([[[2500, 0], [2500, 1000]]], segments(grids[10], "u", 1))
        self.assertEqual([[[0, 1500], [2000, 1500]]], segments(grids[10], "v", 1))
        self.assertEqual([[[1500, 0], [1500, 1000]], [[1500, 2000], [1500, 3000]]], segments(grids[20], "u", 0))
        self.assertEqual([[[0, 1500], [1000, 1500]], [[2000, 1500], [4000, 1500]]], segments(grids[20], "v", 1))
        self.surface(3)
        self.commit(system(1, u="panel 400 gap 5 from -100", v="none"))
        self.commit("grid 30 on 3 from-system 1 origin 200 0")
        panel = self.grids()[30]
        self.assertEqual([502, 907, 1312, 1717, 2122, 2527, 2932, 3337, 3742], panel["u"])
        self.assertEqual(100, panel["uDefinition"]["anchor"])
        self.roundtrip()

    def test_source_preview_cancel_stale_atomic_update_and_history(self):
        self.pair()
        before = self.snapshot()
        command = system(u="series 150 250 3", v="explicit 300 700")
        preview = self.preview(command)
        self.assertTrue(preview["valid"], preview)
        rows = {row["id"]: row for row in preview["grids"]}
        self.assertEqual({10, 20}, set(rows))
        self.assertEqual(([100, 300, 500], [150, 400, 650]), (rows[10]["before"]["u"], rows[10]["after"]["u"]))
        self.assertEqual(([200, 400, 600], [250, 500, 750]), (rows[20]["before"]["u"], rows[20]["after"]["u"]))
        self.commit("cancel-preview")
        self.assertFalse(self.line("confirm " + str(preview["token"]))["ok"])
        self.assertEqual(before, self.snapshot())
        preview = self.preview(command)
        self.commit("spec unrelated 10")
        stale = self.snapshot()
        self.assertFalse(self.line("confirm " + str(preview["token"]))["ok"])
        self.assertEqual(stale, self.snapshot())
        preview = self.preview(command)
        self.commit("confirm " + str(preview["token"]))
        after = self.snapshot()
        self.assertEqual([150, 400, 650], self.grids()[10]["u"])
        self.assertEqual([250, 500, 750], self.grids()[20]["u"])
        self.commit("undo")
        self.assertEqual(stale, self.snapshot())
        self.commit("redo")
        self.assertEqual(after, self.snapshot())
        self.roundtrip()

    def test_display_move_preserves_pending_geometry_preview_and_new_position(self):
        self.pair()
        preview = self.preview(system(u="series 150 250 3"))
        self.commit("canvas-pos grid-system 0 120 220")
        self.commit("confirm " + str(preview["token"]))
        source = self.objects()["gridSystems"][0]
        self.assertEqual((120, 220, True), (source["cx"], source["cy"], source["hasPos"]))
        self.assertEqual([150, 400, 650], self.grids()[10]["u"])
        self.assertEqual([250, 500, 750], self.grids()[20]["u"])

    def test_read_only_rebinding_preview_respects_subgrid_topology_lock(self):
        self.surface(1)
        self.commit(system(0, u="explicit 500 1000 1500", v="explicit 1000 2000"))
        self.commit(system(1, u="explicit 500 1000 1500 2000", v="explicit 1000 2000"))
        self.commit("grid 10 on 1 from-system 0 origin 0 0")
        self.commit("subgrid 11 parent 10 cell u line:0 line:1 v min line:0 divisions u 2 v 1")
        before = self.snapshot()
        response = self.command("grid-preview grid 10 on 1 from-system 1 origin 0 0")
        self.assertFalse(response["ok"], response)
        self.assertEqual(before, self.snapshot())
        preview = self.preview("grid 10 on 1 from-system 1 origin 0 0")
        self.assertFalse(preview["valid"], preview)
        self.assertEqual(before, self.snapshot())

    def test_dependent_subgrid_guide_timber_recompute_or_roll_back_together(self):
        self.pair(system(u="explicit 1000 2000", v="explicit 1000"))
        for line in ["subgrid 11 parent 10 cell u line:0 line:1 v min line:0 divisions u 2 v 1",
                     "guide 1 1 v grid:10:u:0", "timber 90 20 33 role boundary", "place 90 on 1 at-face e0 +u +n",
                     "timber 91 20 33 role boundary", "place 91 on 1 at-face e2 +u +n",
                     "timber 1 27 33 role primary", "place 1 on 1 at-line guide 1 +v +n"]:
            self.commit(line)
        preview = self.preview(system(u="explicit 1200 2400", v="explicit 1000"))
        self.assertTrue(preview["valid"], preview)
        self.commit("confirm " + str(preview["token"]))
        self.assertEqual([1800], self.grids()[11]["u"])
        self.assertEqual(1200, self.refs()["guides"][0]["off"])
        self.assertEqual(1200, next(row for row in self.refs()["timbers"] if row["id"] == 1)["geometry"]["centerline"])
        for u in ["explicit 1200 2401", "explicit 1200", "explicit 0 1200", "explicit 3900 4000"]:
            before = self.snapshot()
            preview = self.preview(system(u=u, v="explicit 1000"))
            self.assertFalse(preview["valid"], (u, preview))
            self.assertFalse(self.line("confirm " + str(preview["token"]))["ok"])
            self.assertEqual(before, self.snapshot(), "one invalid child/support/second surface must roll back every application")
        self.roundtrip()

    def test_protected_source_deletion_and_ordinary_grid_edits(self):
        self.pair()
        self.reject("delete grid-system 0")
        self.reject("grid 10 on 1 u 500 1000")
        self.reject("grid 10 on 1 main-along u")
        self.reject("grid 10 on 1 u panel 1000 gap 0 from 0")
        self.commit("delete grid 10")
        self.reject("delete grid-system 0")
        self.commit("delete grid 20")
        before = self.snapshot()
        self.commit("delete grid-system 0")
        self.assertEqual([], self.objects()["gridSystems"])
        self.commit("undo")
        self.assertEqual(before, self.snapshot())
        self.commit("redo")
        self.assertEqual([], self.objects()["gridSystems"])

    def test_engineering_binding_cannot_replace_source(self):
        self.pair(system(u="panel 400 gap 5 from 0", v="panel 900 gap 3 from 0"))
        before = self.snapshot()
        engineering = self.command("engineering-read")
        data = {"schema": "engineering-transaction/1", "expectedRevision": engineering["revision"],
                "operations": [{"op": "set-source", "target": {"kind": "grid", "id": 10, "axis": "u", "field": "panel"},
                                "source": {"kind": "literal", "value": 600}}]}
        path = Path(self.directory.name) / "engineering.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        response = self.command("engineering-preview " + native_path(path))
        self.assertFalse(response.get("ok") and response.get("preview", {}).get("valid", True), response)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(engineering["state"], self.command("engineering-read")["state"])
        # Publishing a valid material/method/application in the candidate must not
        # make bind-grid a back door that flattens a grid-system reference.
        data["operations"] = [
            {"op": "publish-material", "value": {"id": "panel-a", "version": 1, "kind": "panel", "name": "面材", "width": 400, "length": 900, "thickness": "6", "notes": None}},
            {"op": "publish-method", "value": {"id": "method-a", "version": 1, "name": "做法", "panel": {"id": "panel-a", "version": 1}, "gap": 5, "longAxis": "v", "mainAlong": "u"}},
            {"op": "put-application", "value": {"id": "application-a", "placement_id": 1, "method": {"id": "method-a", "version": 1}, "overrides": {}, "anchorOptions": {"u": {"kind": "coordinate", "value": 0}, "v": {"kind": "coordinate", "value": 0}}}},
            {"op": "bind-grid", "id": 10, "application": "application-a"},
        ]
        path.write_text(json.dumps(data), encoding="utf-8")
        response = self.command("engineering-preview " + native_path(path))
        self.assertFalse(response.get("ok") and response.get("preview", {}).get("valid", True), response)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(engineering["state"], self.command("engineering-read")["state"])

    def test_engineering_bound_grid_cannot_be_implicitly_converted(self):
        self.surface(1)
        self.commit(system())
        self.commit("grid 10 on 1 u panel 400 gap 5 from 0 v panel 900 gap 3 from 0")
        data = {"schema": "engineering-transaction/1", "expectedRevision": self.command("engineering-read")["revision"],
                "operations": [{"op": "set-source", "target": {"kind": "grid", "id": 10, "axis": "u", "field": "panel"},
                                "source": {"kind": "literal", "value": 600}}]}
        path = Path(self.directory.name) / "engineering.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        response = self.command("engineering-preview " + native_path(path))
        self.assertTrue(response["preview"]["valid"], response)
        self.assertTrue(self.command("engineering-confirm " + str(response["preview"]["token"]))["ok"])
        binding = self.command("engineering-read")["state"]
        self.reject("grid 10 on 1 from-system 0 origin 0 0")
        self.assertEqual(binding, self.command("engineering-read")["state"])
        self.assertIsNone(self.grids()[10]["sourceSystem"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
