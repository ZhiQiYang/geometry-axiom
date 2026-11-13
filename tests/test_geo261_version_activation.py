"""Real product K version ownership, serialization and full-precision use sites.

Native execution belongs to P1. This module supplies hard-coded product
witnesses, not a replacement implementation or a portability-only claim.
"""
from pathlib import Path
import json
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native


def panel(identifier="p", thickness="9", version=1):
    return {"id": identifier, "version": version, "name": "Panel", "kind": "panel",
            "width": 100, "length": 100, "thickness": thickness}


class VersionActivation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        b = native()
        cls.request = b.work / "version-product-valid.json"
        cls.bad_request = b.work / "version-product-invalid.json"
        request = {"schema": "engineering-transaction/1", "expectedRevision": 0,
                   "operations": [{"op": "publish-material", "value": panel()}]}
        cls.request.write_text(json.dumps(request), encoding="utf-8")
        request["operations"].append({"op": "not-an-operation"})
        cls.bad_request.write_text(json.dumps(request), encoding="utf-8")
        cls.client = b.compile(ROOT / "tests/geo261_version_product_harness.c", "version-product-client",
            ["GEOMETRY_KERNEL_EXTERNAL=1", "GEOMETRY_WOODWORKING_EXTERNAL=1",
             "GEOMETRY_HOST_HISTORY_EXTERNAL=1", "GEOMETRY_HOST_CANDIDATE_EXTERNAL=1"])
        cls.exe = b.link("version-product-client", [cls.client, *b.product_objects()])

    def succeeds(self, case):
        request = self.bad_request if case == "rollback" else self.request
        result = subprocess.run([str(self.exe), case, str(request)], capture_output=True,
                                text=True, encoding="utf-8", timeout=30)
        self.assertEqual(0, result.returncode, "Native failure is not a policy verdict: " + result.stderr)

    def test_real_candidate_owns_and_publishes_k_versions_with_one_undo(self):
        self.succeeds("lifecycle")

    def test_real_k_binding_seals_before_version_bytes(self):
        self.succeeds("before-tamper")

    def test_real_k_binding_seals_after_typed_version_bytes(self):
        self.succeeds("after-tamper")

    def test_late_batch_failure_keeps_new_versions_out_of_live_world_and_history(self):
        self.succeeds("rollback")

    def test_real_lookup_uses_k_definition_and_replaces_stale_template_cache(self):
        self.succeeds("authority")

    def preview(self, bridge, operations, kind="engineering"):
        revision = bridge.command("engineering-read")["revision"]
        path = native().work / ("version-activation-" + kind + ".json")
        path.write_text(json.dumps({"schema": kind + "-transaction/1", "expectedRevision": revision,
                                    "operations": operations}), encoding="utf-8")
        before = bridge.command("dump")["text"]
        result = bridge.command(kind + "-preview " + str(path))
        self.assertTrue(result["ok"], result)
        self.assertEqual(before, bridge.command("dump")["text"])
        self.assertEqual(revision, bridge.command("engineering-read")["revision"])
        return result["preview"]

    def apply(self, bridge, operations, kind="engineering"):
        preview = self.preview(bridge, operations, kind)
        self.assertTrue(preview["valid"], preview)
        result = bridge.command(kind + "-confirm " + str(preview["token"]))
        self.assertTrue(result["ok"], result)
        return result

    def test_material_method_namespace_archive_republish_and_scene_roundtrip(self):
        b = native()
        with _bridge.BridgeSession(b.bridge()) as bridge:
            self.assertTrue(bridge.command("reset")["ok"])
            value = panel(thickness="0" * 126 + "9")
            method = {"id": "p", "version": 1, "name": "Method", "panel": {"id": "p", "version": 1}, "gap": 0, "longAxis": "v"}
            self.apply(bridge, [{"op": "publish-material", "value": value}, {"op": "publish-method", "value": method}])
            read = bridge.command("engineering-read")
            self.assertEqual("p", read["state"]["materials"][0]["id"])
            self.assertEqual("p", read["state"]["methods"][0]["id"])
            fingerprint = read["state"]["materials"][0]["fingerprint"]
            self.apply(bridge, [{"op": "archive", "kind": "material", "id": "p", "version": 1, "value": True}])
            archived = bridge.command("engineering-read")
            self.assertTrue(archived["state"]["materials"][0]["archived"])
            self.assertEqual(fingerprint, archived["state"]["materials"][0]["fingerprint"])
            repeated = self.apply(bridge, [{"op": "publish-material", "value": value}])
            self.assertFalse(repeated["history_changed"])
            self.assertEqual(archived["revision"], repeated["revision"])
            saved = bridge.command("dump")["text"]
            path = b.work / "version-activation-roundtrip.scene"
            path.write_text(saved, encoding="utf-8")
            self.assertTrue(bridge.command("reset")["ok"])
            self.assertTrue(bridge.command("loadfile " + str(path))["ok"])
            self.assertEqual(saved, bridge.command("dump")["text"])
            restored = bridge.command("engineering-read")["state"]
            self.assertEqual(value["thickness"], restored["materials"][0]["thickness"])
            self.assertEqual(fingerprint, restored["materials"][0]["fingerprint"])
            self.assertTrue(restored["materials"][0]["archived"])
            self.assertEqual(method["panel"], restored["methods"][0]["panel"])
            self.apply(bridge, [{"op": "archive", "kind": "material", "id": "p", "version": 1, "value": False}])
            self.assertTrue(bridge.line("undo")["ok"])
            self.assertEqual(saved, bridge.command("dump")["text"])

    def test_d26_full_127_character_thickness_remains_publishable(self):
        with _bridge.BridgeSession(native().bridge()) as bridge:
            self.assertTrue(bridge.command("reset")["ok"])
            values = ["9" * 127, "0." + "0" * 124 + "1", "0" * 126 + "9"]
            for index, thickness in enumerate(values):
                self.apply(bridge, [{"op": "publish-material", "value": panel("p" + str(index), thickness)}])
            read = bridge.command("engineering-read")
            self.assertEqual(values, [value["thickness"] for value in read["state"]["materials"]])
            before = bridge.command("dump")["text"]
            bad = self.preview(bridge, [{"op": "publish-material", "value": panel("long", "9" * 128)}])
            self.assertFalse(bad["valid"])
            self.assertFalse(bridge.command("engineering-confirm " + str(bad["token"]))["ok"])
            self.assertEqual(before, bridge.command("dump")["text"])

    def test_same_k_fingerprint_guard_controls_real_publication_preview(self):
        b = native()
        source = (b.kernel / "versions.c").read_text(encoding="utf-8")
        guard = "if(memcmp(next.fingerprint,definition->fingerprint,GEO_VERSION_FINGERPRINT_BYTES))"
        self.assertEqual(1, source.count(guard))
        path = b.kernel / "versions-product-fingerprint.c"
        path.write_text(source.replace(guard, "if(false)"), encoding="utf-8")
        changed = b.compile(path, "versions-product-fingerprint")
        objects = b.product_objects()
        self.assertEqual(1, objects.count(b.versions_object))
        mutant = b.link("versions-product-fingerprint-bridge", [b.bridge_object,
            *[changed if obj == b.versions_object else obj for obj in objects]])
        for exe, expected in ((b.bridge(), False), (mutant, True), (b.bridge(), False)):
            with _bridge.BridgeSession(exe) as bridge:
                self.assertTrue(bridge.command("reset")["ok"])
                preview = self.preview(bridge, [{"op": "publish-material", "value": panel(), "fingerprint": "0" * 64}])
                self.assertEqual(expected, preview["valid"], preview)

    def fill_with_thickness(self, thickness):
        b = native()
        with _bridge.BridgeSession(b.bridge()) as bridge:
            path = b.work / "version-fill.scene"
            path.write_text("boundary 8 outline 0,0 250,0 250,250 0,250 kind room_plan\n", encoding="utf-8")
            self.assertTrue(bridge.command("loadfile " + str(path))["ok"])
            threshold = {"id": 90, "name": "threshold", "fields": [{"id": 1, "name": "X", "type": "dimension", "input": "8"}]}
            self.apply(bridge, [{"op": "publish-material", "value": panel(thickness=thickness)}, {"op": "put-parameter", "value": threshold}])
            finish = {"id": 1, "name": "finish", "boundaryId": 8,
                      "frame": {"origin": [0, 0, 0], "U": "+X", "V": "+Y", "N": "+Z"}, "structureSide": 1, "obstacles": []}
            self.apply(bridge, [{"op": "put-finish-surface", "value": finish}], "panel-fill")
            fill = {"id": 1, "finishSurfaceId": 1, "panel": {"id": "p", "version": 1}, "lengthAlong": "v", "origin": [0, 0],
                    "gap": 3, "pattern": "straight", "threshold": {"parameterId": 90, "fieldId": 1}}
            preview = self.preview(bridge, [{"op": "put-panel-fill", "value": fill}], "panel-fill")
            if preview["valid"]:
                self.assertTrue(bridge.command("panel-fill-confirm " + str(preview["token"]))["ok"])
                derived = bridge.command("panel-fill-read")["state"]["panelFills"][0]["derived"]
                self.assertEqual(9, derived["thickness"])
                self.assertEqual(9, derived["tileCount"])
            else:
                self.assertIn("no rounding", json.dumps(preview["violations"]))
                self.assertFalse(bridge.command("panel-fill-confirm " + str(preview["token"]))["ok"])
            return preview["valid"]

    def test_long_leading_zero_thickness_works_at_actual_integer_use_site(self):
        self.assertTrue(self.fill_with_thickness("0" * 126 + "9"))

    def test_tiny_and_huge_legal_sources_are_rejected_only_when_used_as_integer_thickness(self):
        self.assertFalse(self.fill_with_thickness("0." + "0" * 124 + "1"))
        self.assertFalse(self.fill_with_thickness("9" * 127))


if __name__ == "__main__":
    unittest.main(verbosity=2)
