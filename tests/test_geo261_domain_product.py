"""Actual H composition preserves K domain storage, metadata and transactions.

The negative controls replace a K object in both the real host witness and the
real bridge. Compile failures and process crashes never count as detections.
"""
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native

SCENE = """boundary 11 outline 0,0 100,0 100,100 0,100 fixity F X F X kind room_plan hole 20,20 20,40 40,40 40,20 fixity X F X F
boundary 22 outline 200,0 500,0 500,200 200,200 fixity X F X F kind wall_elevation
placement 101 on boundary 11 origin 10 20 30 u +x v +y
placement 102 on boundary 22 origin 40 50 60 u +x v +z
placement 103 origin -10 -20 70 u +x v +y rect 0 0 90 80
"""


class DomainStoreProduct(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        cls.client = build.compile(ROOT / "tests/geo261_domain_product_harness.c", "domain-host-product",
            ["GEOMETRY_KERNEL_EXTERNAL=1", "GEOMETRY_WOODWORKING_EXTERNAL=1", "GEOMETRY_HOST_HISTORY_EXTERNAL=1",
             "GEOMETRY_HOST_CANDIDATE_EXTERNAL=1"])
        cls.exe = build.link("domain-host-product", [cls.client, *build.product_objects()])

    def case(self, name, exe=None):
        result = subprocess.run([str(exe or self.exe), name], capture_output=True, text=True, timeout=20)
        self.assertIn(result.returncode, (0, 1), "Native crash/setup failure is not a domain verdict: " + result.stderr)
        if result.returncode:
            self.assertIn("ASSERT:", result.stderr, "Only an explicit host assertion counts as a detection")
        return result.returncode

    def load(self, session, scene=SCENE):
        path = native().work / "domain-product.scene"
        path.write_text(scene, encoding="utf-8")
        result = session.command("loadfile " + str(path))
        self.assertTrue(result["ok"], result)

    def commit(self, session, command):
        result = session.command("line " + command)
        if "preview" in result:
            self.assertTrue(result["preview"]["valid"], result)
            result = session.command("line confirm " + str(result["preview"]["token"]))
        self.assertTrue(result["ok"], (command, result))

    def test_boundary_geometry_and_distinct_kind_fixity_are_owned_and_compact_together(self):
        self.assertEqual(0, self.case("boundaries"))

    def test_all_placement_variants_keep_geometry_in_kernel_and_policy_aligned(self):
        self.assertEqual(0, self.case("placements"))

    def test_copied_world_candidate_has_independent_geometry_and_metadata(self):
        self.assertEqual(0, self.case("snapshot"))

    def test_rejected_real_command_preserves_every_world_byte(self):
        self.assertEqual(0, self.case("rollback"))

    def test_reference_placement_keeps_inactive_wire_rect_outside_kernel_geometry(self):
        self.assertEqual(0, self.case("inactive-rect"))

    def test_real_bridge_dump_replay_delete_compaction_and_undo_are_exact(self):
        with _bridge.BridgeSession(native().bridge()) as session:
            self.load(session)
            before = session.command("dump")["text"]
            first, second = session.command("boundary 11"), session.command("boundary 22")
            self.assertEqual("room_plan", first["kind"])
            self.assertEqual("wall_elevation", second["kind"])
            self.assertEqual([1, 0, 1, 0], first["loops"][0]["fixity"])
            self.assertEqual([0, 1, 0, 1], first["loops"][1]["fixity"])
            self.assertEqual([0, 1, 0, 1], second["loops"][0]["fixity"])
            surfaces = session.command("surfaces")["surfaces"]
            self.assertEqual([101, 102, 103], [row["id"] for row in surfaces])
            self.commit(session, "delete placement 101")
            self.commit(session, "delete boundary 11")
            self.assertEqual(second, session.command("boundary 22"))
            self.assertEqual(surfaces[1:], session.command("surfaces")["surfaces"])
            self.commit(session, "undo")
            self.commit(session, "undo")
            self.assertEqual(before, session.command("dump")["text"])
            self.assertEqual(first, session.command("boundary 11"))
            self.load(session, before)
            self.assertEqual(before, session.command("dump")["text"])
            self.assertEqual(first, session.command("boundary 11"))
            self.assertEqual(second, session.command("boundary 22"))
            self.assertEqual(surfaces, session.command("surfaces")["surfaces"])

    def test_failed_candidate_and_failed_import_preserve_bridge_dump_and_queries(self):
        with _bridge.BridgeSession(native().bridge()) as session:
            self.load(session)
            before = session.command("dump")["text"]
            boundary = session.command("boundary 11")
            surfaces = session.command("surfaces")
            result = session.command("line preview placement 101 on boundary 999 origin 0 0 0 u +x v +y")
            self.assertTrue(result["ok"], result)
            self.assertFalse(result["preview"]["valid"], result)
            self.assertEqual(before, session.command("dump")["text"])
            self.assertEqual(boundary, session.command("boundary 11"))
            self.assertEqual(surfaces, session.command("surfaces"))
            path = native().work / "domain-product-invalid.scene"
            path.write_text("boundary 77 outline 0,0 60,0 60,60 0,60\n"
                "placement 88 on boundary 999 origin 0 0 0 u +x v +y\n", encoding="utf-8")
            self.assertFalse(session.command("loadfile " + str(path))["ok"])
            self.assertEqual(before, session.command("dump")["text"])
            self.assertEqual(boundary, session.command("boundary 11"))
            self.assertEqual(surfaces, session.command("surfaces"))

    def mutant(self, module, name, before, after):
        build = native()
        source = (build.kernel / (module + ".c")).read_text(encoding="utf-8")
        self.assertEqual(1, source.count(before), "Negative control must replace exactly one K expression")
        path = build.work / ("domain-" + name + ".c")
        path.write_text(source.replace(before, after), encoding="utf-8")
        changed = build.compile(path, "domain-" + name)
        original = getattr(build, module + "_object")
        objects = build.product_objects()
        self.assertEqual(1, objects.count(original))
        substituted = [changed if obj == original else obj for obj in objects]
        client = build.link("domain-" + name + "-host", [self.client, *substituted])
        build.bridge()
        bridge = build.link("domain-" + name + "-bridge", [build.bridge_object, *substituted])
        return client, bridge

    def boundary_geometry(self, exe):
        with _bridge.BridgeSession(exe) as session:
            self.load(session, "boundary 1 outline 0,0 100,0 100,80 0,80\n")
            return (session.command("boundary 1")["loops"][0]["verts"],
                    session.command("bhit 1 0 0 0"), session.command("bhit 1 7 0 0"))

    def test_region_store_geometry_negative_control_changes_real_host_and_hit_query(self):
        build = native()
        hit = {"ok": True, "kind": "vertex", "loop": -1, "index": 0}
        expected = ([[0, 0], [100, 0], [100, 80], [0, 80]], hit, {"ok": True, "kind": "edge", "loop": -1, "index": 0})
        self.assertEqual(0, self.case("boundaries"))
        self.assertEqual(expected, self.boundary_geometry(build.bridge()))
        before = "memcpy(next.outline.v, region->outline.v, next.outline.count * sizeof next.outline.v[0]);"
        client, bridge = self.mutant("regions", "region-left", before,
            before + "\n    next.outline.v[0].u=next.outline.v[3].u=7;")
        self.assertEqual(1, self.case("boundaries", client))
        self.assertEqual(([[7, 0], [100, 0], [100, 80], [7, 80]], {"ok": False}, hit), self.boundary_geometry(bridge))
        self.assertEqual(0, self.case("boundaries"))
        self.assertEqual(expected, self.boundary_geometry(build.bridge()))

    def placement_geometry(self, exe):
        with _bridge.BridgeSession(exe) as session:
            self.load(session, "placement 9 origin 0 0 30 u +x v +y rect 0 0 100 80\ngrid 3 on 9 u 50\n")
            face = next(row for row in session.command("objects")["faces"] if row["kind"] == "placement" and row["id"] == 9)
            grid = next(row for row in session.command("references")["grids"] if row["id"] == 3)
            return face["bbox"], grid["bounds"]

    def test_placement_store_geometry_negative_control_changes_real_host_and_grid_bounds(self):
        build = native()
        expected = ([0, 0, 100, 80], {"u": [0, 100], "v": [0, 80]})
        self.assertEqual(0, self.case("placements"))
        self.assertEqual(expected, self.placement_geometry(build.bridge()))
        before = "next.rect=definition->rect;"
        client, bridge = self.mutant("placements", "placement-right", before, before + "\n        next.rect.max_u=93;")
        self.assertEqual(1, self.case("placements", client))
        self.assertEqual(([0, 0, 93, 80], {"u": [0, 93], "v": [0, 80]}), self.placement_geometry(bridge))
        self.assertEqual(0, self.case("placements"))
        self.assertEqual(expected, self.placement_geometry(build.bridge()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
