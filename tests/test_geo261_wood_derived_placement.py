"""D4/R41 W policy oracles using public K geometry and actual bridge controls.

Portable boundary checks do not compile. P1 owns serialized native execution;
compile/link errors and process failures never count as successful controls.
"""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native
from tests.test_panel_fill_finish_surface import surface, put as finish_put
from tests.test_panel_fill_layout import fill

MODULE = ROOT / "geometry-templates/woodworking/native"


def put(identifier=10, fill_id=1, h=30):
    return {"kind": "operation", "value": {"op": "put-derived-placement", "value": {"id": identifier, "fillId": fill_id, "h": h}}}


def box(identifier=20, lo=(20, 20, 9), hi=(40, 40, 39), kind=1):
    return {"kind": "obstacle", "id": identifier, "lo": list(lo), "hi": list(hi), "type": kind}


REBUILD = {"kind": "rebuild"}
RECT = [[0, 0], [100, 0], [100, 100], [0, 100]]
BREAK = {"kind": "boundary", "points": [[0, 0], [40, 0], [100, 0], [100, 100], [0, 100]], "fixity": [0, 1, 1, 1, 1]}
CONTROLS = (
    ("depth-open", "d->obstacles[i].q[0]<d->t+p->derived_h", "d->obstacles[i].q[0]<=d->t+p->derived_h"),
    ("immutable", "i<s->host_count&&s->hosts[i].fill_id!=d.fill_id", "false"),
    ("one-host", "k!=i&&s->hosts[k].fill_id==d.fill_id", "false"),
    ("fixity", "fix[prev]==fix[i]&&", "true&&"),
    ("one-match", "matches==1||wood_fs_error", "matches>0||wood_fs_error"),
)


class DerivedPlacementBoundary(unittest.TestCase):
    def test_w_owns_policy_and_only_uses_public_k_geometry(self):
        for name in ("derived_placement.h", "derived_placement.c"):
            text = (MODULE / name).read_text(encoding="utf-8")
            code = re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S)
            self.assertNotRegex(code, r"\b(?:World|PlacementSurface|SpaceBoundarySurface|g_engineering_error|world_find_placement|scene_error)\b")
            self.assertNotIn("internal/", text)
            self.assertNotIn("geometry-app", text)
        text = (MODULE / "derived_placement.c").read_text(encoding="utf-8")
        for call in ("geo_collinear_segment_overlap", "geo_region_is_valid", "geo_loop_bbox"):
            self.assertIn(call + "(", text)
        self.assertNotIn("static bool wood_dp_overlap", text)

    def test_host_entries_delegate_and_scene_dump_remains_definition_only(self):
        text = (ROOT / "geometry-core/derived_placements.inc").read_text(encoding="utf-8")
        for name in ("find", "operation", "rebuild", "edge_key", "edge_resolve"):
            match = re.search(r"static [^\n]+\bdp_" + name + r"\([^\n]+\)\s*\{([^{}]*)\}", text)
            self.assertIsNotNone(match, name)
            self.assertIn("wood_dp_" + name + "(&c", match[1])
        self.assertIn("wood_dp_load(&c", text)
        self.assertIn("definition-hex", text)
        self.assertNotIn("dp_overlap", text)
        self.assertNotIn("one derived placement per panel fill", text)


class WoodDerivedPlacement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        path = build.woodworking / "derived-placement-client.c"
        shutil.copy2(ROOT / "tests/geo261_derived_placement_harness.c", path)
        cls.client = build.compile(path, "derived-placement-client")
        cls.exe = build.link("derived-placement-client", cls.objects(build, build.wood_derived_placement_object))

    @classmethod
    def objects(cls, build, changed):
        return [cls.client, changed, build.wood_finish_object, build.wood_engineering_object,
                build.wood_section_profile_object, build.wood_panel_layout_object, *build.kernel_objects()]

    def call(self, actions, exe=None):
        path = native().work / "derived-placement-client.json"
        path.write_text(json.dumps(actions), encoding="utf-8")
        run = subprocess.run([str(exe or self.exe), str(path)], capture_output=True, text=True, timeout=30)
        self.assertEqual(0, run.returncode, "Process crash/error is not a domain verdict: " + run.stderr)
        rows = [json.loads(line) for line in run.stdout.splitlines()]
        self.assertEqual(len(actions), len(rows))
        return rows

    @staticmethod
    def host(row):
        return next(p for p in row["placements"] if p["id"] == 10)

    def test_typed_height_sources_and_definition_only_identity(self):
        for source, expected in ((30, 30), ({"kind": "spec", "name": "depth"}, 30), ({"kind": "parameter", "parameterId": 90, "fieldId": 2}, 31),
                                 ({"kind": "material", "id": "timber", "version": 1, "field": "B"}, 32)):
            with self.subTest(source=source):
                row = self.call([put(h=source), REBUILD])[-1]
                self.assertTrue(row["ok"], row)
                self.assertEqual(expected, self.host(row)["h"])
                self.assertEqual([{"id": 10, "fillId": 1, "h": source}], row["definitions"])
        bad = {"kind": "material", "id": "timber", "version": 1, "field": "A"}
        row = self.call([put(h=bad)])[0]
        self.assertFalse(row["ok"])
        self.assertEqual("D4: h material source must be timber B", row["error"])
        row = self.call([put(h={"kind": "application", "id": "a", "field": "primary.B"})])[0]
        self.assertFalse(row["ok"])
        self.assertIn("application", row["error"])

    def test_admission_order_variant_immutable_unique_capacity_and_delete(self):
        scenarios = (([{"kind": "normal"}, put()], "D4: placement variant cannot change"),
                     ([put(), put(fill_id=2)], "D4: source fill is immutable"),
                     ([put(), put(identifier=11)], "D4: one derived placement per panel fill"),
                     ([{"kind": "capacity"}, put()], "I33 CAPACITY: derived placement limit reached"))
        for actions, expected in scenarios:
            with self.subTest(error=expected):
                row = self.call(actions)[-1]
                self.assertFalse(row["ok"]);self.assertEqual(expected, row["error"])
        row = self.call([put(), REBUILD, {"kind": "operation", "remove": 1, "value": {"op": "delete-derived-placement", "id": 10}}])[-1]
        self.assertTrue(row["ok"]);self.assertEqual((0, 0, 1), (row["hostCount"], row["placementCount"], row["drops"]))

    def test_scene_admission_preserves_error_kind_and_rebuilds_sources(self):
        definition = {"id": 10, "fillId": 1, "h": 30}
        row = self.call([{"kind": "load", "value": definition}])[-1]
        self.assertTrue(row["ok"], row);self.assertEqual([0, 0, 9], self.host(row)["origin"])
        row = self.call([{"kind": "diagnostic", "value": 1}, {"kind": "load", "id": 12, "value": definition}])[-1]
        self.assertFalse(row["ok"]);self.assertEqual(1, row["diagnostic"])
        self.assertEqual("D4/I56: derived placement id mismatch, duplicate or variant collision", row["sceneMessage"])
        self.assertEqual("", row["error"])
        for setup, other, expected in (([put()], dict(definition), "D4/I56: derived placement id mismatch, duplicate or variant collision"),
                                       ([put()], dict(definition, id=11), "D4: one derived placement per fill"),
                                       ([{"kind": "capacity"}], definition, "I33 CAPACITY: derived placement limit reached")):
            with self.subTest(scene_error=expected):
                row = self.call(setup + [{"kind": "load", "id": other["id"], "value": other}])[-1]
                self.assertFalse(row["ok"]);self.assertEqual(expected, row["sceneMessage"])

    def test_open_depth_endpoints_exact_hole_geometry_and_touch_only(self):
        for low, high, holes in ((0, 9, []), (9, 39, [[[20, 20], [20, 40], [40, 40], [40, 20]]]),
                                 (39, 49, []), (8, 10, [[[20, 20], [20, 40], [40, 40], [40, 20]]])):
            with self.subTest(depth=(low, high)):
                row = self.call([box(lo=(20, 20, low), hi=(40, 40, high)), put(), REBUILD])[-1]
                self.assertTrue(row["ok"], row)
                self.assertEqual(RECT, self.host(row)["components"][0]["outline"])
                self.assertEqual(holes, self.host(row)["components"][0]["holes"])
        row = self.call([box(lo=(100, 20, 9), hi=(120, 80, 39)), put(), REBUILD])[-1]
        self.assertEqual([], self.host(row)["components"][0]["holes"])

    def test_negative_side_mapping_and_vertical_normal_depth(self):
        row = self.call([{"kind": "side", "side": -1}, put(), REBUILD])[-1]
        host = self.host(row);self.assertTrue(row["ok"], row)
        self.assertEqual(([0, 0, -9], [0, -1, 0], [0, 0, -1]), (host["origin"], host["V"], host["N"]))
        self.assertEqual([[0, -100], [100, -100], [100, 0], [0, 0]], host["components"][0]["outline"])
        row = self.call([{"kind": "vertical"}, box(lo=(1010, 20, 20), hi=(1020, 40, 40)), put(), REBUILD])[-1]
        self.assertTrue(row["ok"], row);self.assertEqual([1009, 0, 0], self.host(row)["origin"])
        self.assertEqual([[[20, 20], [20, 40], [40, 40], [40, 20]]], self.host(row)["components"][0]["holes"])

    def test_components_point_contact_and_empty_difference_have_no_fallback(self):
        row = self.call([box(lo=(40, -10, 9), hi=(60, 110, 39)), put(), REBUILD])[-1]
        self.assertTrue(row["ok"], row)
        self.assertEqual([[[0, 0], [40, 0], [40, 100], [0, 100]], [[60, 0], [100, 0], [100, 100], [60, 100]]], [c["outline"] for c in self.host(row)["components"]])
        row = self.call([box(lo=(0, 50, 9), hi=(50, 100, 39)), box(21, (50, 0, 9), (100, 50, 39)), put(), REBUILD])[-1]
        self.assertTrue(row["ok"], row);self.assertEqual(2, len(self.host(row)["components"]))
        row = self.call([box(lo=(-10, -10, 9), hi=(110, 110, 39)), put(), REBUILD])[-1]
        self.assertTrue(row["ok"], row);self.assertEqual([], self.host(row)["components"])

    def test_fixity_breaks_and_merged_provenance_use_source_order(self):
        row = self.call([BREAK, put(), REBUILD])[-1]
        self.assertTrue(row["ok"], row);self.assertEqual(BREAK["points"], self.host(row)["components"][0]["outline"])
        self.assertEqual([0, 1, 1, 1, 1], self.host(row)["components"][0]["fixity"])
        merged = dict(BREAK, fixity=[1] * 5)
        row = self.call([merged, put(), REBUILD, {"kind": "key"}])[-1]
        self.assertTrue(row["ok"], row);self.assertEqual([["e0", 0, 1], ["e1", 0, 1]], json.loads(row["key"]))
        row = self.call([box(21), box(20), put(), REBUILD, {"kind": "key", "hole": 0}])[-1]
        self.assertTrue(row["ok"], row);self.assertEqual([["b20:u-", 0, 1], ["b21:u-", 0, 1]], json.loads(row["key"]))

    def test_remote_split_changes_total_and_stale_key_never_rebinds(self):
        actions = [box(lo=(30, -10, 9), hi=(40, 60, 39)), put(), REBUILD, {"kind": "key"}]
        row = self.call(actions)[-1];self.assertEqual([["e0", 0, 2]], json.loads(row["key"]))
        actions += [box(21, (70, -10, 9), (80, 60, 39)), REBUILD, {"kind": "key"}, {"kind": "resolve", "key": [["e0", 0, 2]]}]
        rows = self.call(actions)
        self.assertEqual([["e0", 0, 3]], json.loads(rows[-2]["key"]))
        self.assertFalse(rows[-1]["ok"]);self.assertIn("matches 0 derived edges", rows[-1]["error"])

    def test_resolver_requires_exactly_one_match_and_preserves_component_address(self):
        row = self.call([box(lo=(40, -10, 9), hi=(60, 110, 39)), put(), REBUILD, {"kind": "resolve", "key": [["e0", 1, 2]]}])[-1]
        self.assertTrue(row["ok"], row);self.assertEqual([-1, 32], row["resolved"])
        row = self.call([put(), REBUILD, {"kind": "duplicate-component"}, {"kind": "resolve", "key": [["e0", 0, 1]]}])[-1]
        self.assertFalse(row["ok"]);self.assertIn("matches 2 derived edges", row["error"])

    def test_touching_holes_and_component_or_key_capacity_reject(self):
        row = self.call([box(), box(21, (40, 40, 9), (60, 60, 39)), put(), REBUILD])[-1]
        self.assertFalse(row["ok"]);self.assertIn("non-simple or touching", row["error"])
        row = self.call([box(i + 1, (10 * i + 5, -10, 9), (10 * i + 7, 110, 39)) for i in range(8)] + [put(), REBUILD])[-1]
        self.assertFalse(row["ok"]);self.assertEqual(1, row["diagnostic"]);self.assertEqual("I33 CAPACITY: R41 component limit is 8", row["error"])
        row = self.call([box(70000 + i) for i in range(32)] + [put(), REBUILD])[-1]
        self.assertFalse(row["ok"]);self.assertEqual(1, row["diagnostic"]);self.assertEqual("I33 CAPACITY: R41 key exceeds supported size", row["error"])

    def mutant(self, control):
        name, before, after = control;build = native()
        text = (build.woodworking / "derived_placement.c").read_text(encoding="utf-8")
        self.assertEqual(1, text.count(before), name)
        path = build.woodworking / ("derived-placement-" + name + ".c")
        path.write_text(text.replace(before, after), encoding="utf-8")
        changed = build.compile(path, "derived-placement-" + name)
        return changed, build.link("derived-placement-mutant-" + name, self.objects(build, changed))

    def test_five_guard_removals_expose_the_named_policy_failure(self):
        actions = ([box(lo=(20, 20, 39), hi=(40, 40, 49)), put(), REBUILD],
                   [put(), put(fill_id=2)], [put(), put(identifier=11)], [BREAK, put(), REBUILD],
                   [put(), REBUILD, {"kind": "duplicate-component"}, {"kind": "resolve", "key": [["e0", 0, 1]]}])
        selectors = (lambda r: len(self.host(r)["components"][0]["holes"]), lambda r: r["ok"], lambda r: r["ok"],
                     lambda r: len(self.host(r)["components"][0]["outline"]), lambda r: r["ok"])
        for control, case, select, expected, exposed in zip(CONTROLS, actions, selectors, (0, False, False, 5, False), (1, True, True, 4, True)):
            with self.subTest(control=control[0]):
                self.assertEqual(expected, select(self.call(case)[-1]))
                _, mutant = self.mutant(control)
                self.assertEqual(exposed, select(self.call(case, mutant)[-1]))
                self.assertEqual(expected, select(self.call(case)[-1]))

    def product_immutable_preview(self, executable, suffix):
        build = native()
        with _bridge.BridgeSession(executable) as bridge:
            scene = build.work / ("dp-" + suffix + ".scene")
            scene.write_text("boundary 8 outline 0,0 100,0 100,100 0,100 kind room_plan\n", encoding="utf-8")
            self.assertTrue(bridge.command("loadfile " + str(scene))["ok"])
            def preview(kind, operations, apply=False):
                path = build.work / ("dp-transaction-" + suffix + ".json")
                read = bridge.command("panel-fill-read");self.assertTrue(read["ok"], read)
                path.write_text(json.dumps({"schema": kind + "-transaction/1", "expectedRevision": read["revision"], "operations": operations}), encoding="utf-8")
                response = bridge.command(kind + "-preview " + str(path));self.assertTrue(response["ok"], response)
                if apply:
                    self.assertTrue(response["preview"]["valid"], response)
                    self.assertTrue(bridge.command(kind + "-confirm " + str(response["preview"]["token"]))["ok"])
                return response["preview"]
            preview("engineering", [{"op": "publish-material", "value": {"id": "pf-board", "version": 1, "name": "board", "kind": "panel", "width": 100, "length": 100, "thickness": "9"}},
                                    {"op": "put-parameter", "value": {"id": 90, "name": "threshold", "fields": [{"id": 1, "name": "X", "type": "dimension", "input": "8"}]}}], True)
            preview("panel-fill", [finish_put(surface(boundary=8, origin=(0, 0, 0), obstacles=[])), fill(gap=0), fill(id=2, gap=0), put()["value"]], True)
            before = bridge.command("dump")["text"]
            result = preview("panel-fill", [put(fill_id=2)["value"]])
            self.assertEqual(before, bridge.command("dump")["text"])
            return result

    def test_actual_bridge_consumes_the_same_immutable_source_guard(self):
        build = native();baseline = build.bridge()
        self.assertFalse(self.product_immutable_preview(baseline, "baseline")["valid"])
        changed, _ = self.mutant(CONTROLS[1]);objects = build.product_objects()
        self.assertEqual(1, objects.count(build.wood_derived_placement_object))
        mutant = build.link("derived-placement-mutant-bridge", [build.bridge_object, *[changed if obj == build.wood_derived_placement_object else obj for obj in objects]])
        self.assertTrue(self.product_immutable_preview(mutant, "removed")["valid"])
        self.assertFalse(self.product_immutable_preview(baseline, "restored")["valid"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
