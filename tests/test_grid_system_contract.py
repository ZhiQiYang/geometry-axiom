"""Independent D29/I37/R32 acceptance against the actual native bridge.

GEOMETRY_TEST_BRIDGE points to a fresh executable (or a WSL launcher).
GEOMETRY_TEST_SERVER_PATH_STYLE=wsl translates temporary load/request paths.
No coordinate oracle calls the implementation's grid evaluator.

reject(command, why=...) pins the *reason* as well as "refused and World unchanged": `why` is a
substring (or a tuple of substrings, all required) of rejection_reason(response), so a command that
is refused only because it was mistyped (unknown command) cannot pass as a rule rejection.
test_infinite_grid_contract.py shares this reject().  A gated edit answers ok=false with the generic
"I8a: impact preview required" and puts the real reason in preview.violations[].actual; the
definition refusals name the specific field and violated clause (GEO-246).
"""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:  # `python tests/x.py` puts tests/ first, not the repo root
    sys.path.insert(0, str(ROOT))
from tests import _bridge  # noqa: E402


def system(identifier=0, name="天花 網格 A", u="series 100 200 3", v="explicit 200 600", main="none"):
    return f"grid-system {identifier} name-hex {name.encode('utf-8').hex()} main-along {main} u {u} v {v}"


def native_path(path):
    value = str(path)
    if os.environ.get("GEOMETRY_TEST_SERVER_PATH_STYLE") == "wsl" and len(value) > 2 and value[1] == ":":
        return "/mnt/" + value[0].lower() + "/" + value[3:].replace("\\", "/")
    return value


def rejection_reason(response):
    """Why a refused command was refused: preview.violations[].actual when the refusal is a
    preview-gated one (its top-level `error` is then the generic "I8a: impact preview required"),
    else the top-level `error`."""
    violations = (response.get("preview") or {}).get("violations") or []
    actual = [str(v["actual"]) for v in violations if v.get("actual")]
    return "\n".join(actual) if actual else str(response.get("error", ""))


class GridSystemContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _bridge.find_bridge()

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="geometry-grid-contract-")
        self.addCleanup(self.directory.cleanup)
        self.session = _bridge.BridgeSession(self.bridge)
        self.addCleanup(self.session.stop)
        self.assertTrue(self.command("reset")["ok"])

    def command(self, command):
        return self.session.command(command)

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

    def reject(self, command, why=None):
        """`why`: substring, or tuple of substrings (all required), of rejection_reason(); None = reason not pinned."""
        before = self.snapshot()
        response = self.line(command)
        self.assertFalse(response.get("ok") and response.get("preview", {}).get("valid", True), response)
        if "preview" in response:
            self.assertFalse(self.line("confirm " + str(response["preview"]["token"]))["ok"])
        self.assertEqual(before, self.snapshot(), command)
        if why is not None:
            reason = rejection_reason(response)
            for needle in ((why,) if isinstance(why, str) else why):
                self.assertIn(needle, reason, f"{command!r} was refused for a different reason: {reason!r}")

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
        reasons = [
            "u explicit coordinate[1]=1 must be greater than coordinate[0]=1",
            "u explicit coordinate[1]=1 must be greater than coordinate[0]=2",
            "u step=0 must be positive", "u step=-1 must be positive",
            "u count=0 must be in 1..64", "u count=65 must be in 1..64",
            "u series last coordinate exceeds D1 range", "超出支援範圍",
            "u panel=0 must be positive", "u gap=-1 must be non-negative",
            "u anchor requires explicit from", "超出支援範圍", "u explicit count exceeds 64 lines",
        ]
        out_of_d1_range = {"series 0 9223372036854775807 2", "explicit 100000001"}
        for axis, reason in zip(invalid_axes, reasons, strict=True):
            with self.subTest(axis=axis):
                self.reject(system(u=axis, v="none"), reason if axis in out_of_d1_range else ("D29/I37", reason))
        needs_surface = "前面要先有 placement 或 surface"
        for command, why in [(system(u="none", v="none"), ("D29/I37", "u/v sources cannot both be none")),
                             (system(u="explicit 100", v="none", main="u"), ("D29/I37", "main-along=u requires v source")),
                             (system(name=""), ("D29/I37", "name-hex must be non-empty")),
                             (system(name="界" * 33), ("D29/I37", "name-hex exceeds 96 bytes")),
                             (system().replace("name-hex " + "天花 網格 A".encode().hex(), "name-hex ff"), ("D29/I37", "name-hex requires valid UTF-8")),
                             (system().replace("name-hex " + "天花 網格 A".encode().hex(), "name-hex 610a62"), ("D29/I37", "name-hex contains control byte 0x0a")),
                             (system().replace("name-hex " + "天花 網格 A".encode().hex(), "name-hex 610062"), ("D29/I37", "name-hex contains control byte 0x00")),
                             (system().replace("grid-system 0", "grid-system 4294967296"), ("D29/I37", "id must be uint32 (0..4294967295)")),
                             ("grid 1 on 1 from-system 0 origin 0 0", needs_surface)]:
            with self.subTest(command=command):
                self.reject(command, why)
        self.commit(system(name="界" * 32))
        self.reject("grid 1 on 1 from-system 0 origin 0 0", needs_surface)
        self.surface(1)
        self.reject("grid 1 on 1 from-system 99 origin 0 0", ("I37", "existing surface and grid-system"))
        self.reject("grid 1 on 1 from-system 0 origin 100000000 0", ("I37", "exceed D1 range"))
        for identifier in range(1, 16):
            self.commit(system(identifier=identifier))
        self.reject(system(identifier=16), ("I37", "capacity is 16"))
        self.assertEqual(16, len(self.objects()["gridSystems"]))

    def test_line_limit_applies_when_panel_system_gets_a_surface(self):
        # GEO-246 / dot P2: grammar failures name the actual field; a present
        # `from` must never turn a misspelled `gap` into an anchor diagnosis.
        for axis, why in [
            ("panel 10 gaps 0 from 0", "u gap keyword must be gap (got gaps)"),
            ("repeat-panel 10 gaps 0 from 0", "u gap keyword must be gap (got gaps)"),
            ("panel 10 gap 0 origin 0", "u anchor requires explicit from"),
            ("panel ten gap 0 from 0", "u panel length requires an integer in D1 range"),
            ("panel 10 gap none from 0", "u gap requires an integer in D1 range"),
            ("panel 10 gap 0 from none", "u anchor requires an integer in D1 range"),
            ("panel 10", "u panel definition requires length, gap and from anchor"),
        ]:
            with self.subTest(panel_grammar=axis):
                self.reject(system(u=axis, v="none"), ("D29/I37", why))
        self.surface(1)
        self.commit(system(u="series 0 1 64", v="none"))
        self.commit("grid 10 on 1 from-system 0 origin 0 0")
        self.assertEqual(list(range(64)), self.grids()[10]["u"])
        self.commit(system(1, u="panel 1 gap 0 from 0", v="none"))
        self.surface(2)
        self.reject("grid 20 on 2 from-system 1 origin 0 0", ("I10", "來源或主支方向不合法"))
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
        self.reject("grid 11 on 1 from-system 0 origin 0 0", ("I10", "already has a main grid"))
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
        self.reject("delete grid-system 0", ("I37", "still referenced by grid"))
        self.reject("grid 10 on 1 u 500 1000", ("D29", "direct axis edits are not allowed"))
        self.reject("grid 10 on 1 main-along u", ("D29", "direct axis edits are not allowed"))
        self.reject("grid 10 on 1 u panel 1000 gap 0 from 0", ("D29", "direct axis edits are not allowed"))
        self.commit("delete grid 10")
        self.reject("delete grid-system 0", ("I37", "still referenced by grid"))
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
        self.reject("grid 10 on 1 from-system 0 origin 0 0", ("D28", "engineering sources"))
        self.assertEqual(binding, self.command("engineering-read")["state"])
        self.assertIsNone(self.grids()[10]["sourceSystem"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
