"""Q38 model producer: native sources, independent meshes, identity and replay.

No reference geometry helper supplies the expected bounds, volume or topology.
The native adapter is real; only the incomplete-adapter protocol test mocks it.
"""
import base64
from collections import Counter
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "geometry-core"))
import modeling
from modeling import ModelError, ModelWorld, build_package, verify_package
from modeling.base import load_base
from modeling.common import digest
from modeling_cli import obj_bytes
from tests import binaries, _bridge

OUTLINE = [[0, 0], [400, 0], [400, 60], [60, 60], [60, 250], [0, 250]]


def literal(value):
    return {"kind": "literal", "value": value}


def profile(identifier=1, outline=None):
    return {"id": identifier, "name": "L / 原始斷面", "outline": deepcopy(OUTLINE if outline is None else outline)}


def member(identifier=1, **values):
    return {"id": identifier, "profileId": 1, "kind": "timber", "A": literal(27), "B": literal(33),
            "orientation": "A-u", "u0": 0, "v0": 0, **values}


def run(identifier=1, **values):
    return {"id": identifier, "profileId": 1, "length": literal(2400), "placement": None, **values}


def record(kind, value):
    encoded = base64.b64encode(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).decode()
    return f"section-profile {kind} {encoded}\n"


def scene(*, profiles=None, members=None, runs=None, prefix=""):
    records = [("profile", v) for v in ([profile()] if profiles is None else profiles)]
    records += [("member", v) for v in ([member(), member(2, u0=373), member(3, v0=223, orientation="A-v")] if members is None else members)]
    records += [("run", v) for v in ([run()] if runs is None else runs)]
    return prefix + "requires section-profile/1\n" + "".join(record(k, v) for k, v in records)


def request(*ids, **values):
    return {"roots": [{"kind": "profile-run", "id": i} for i in (ids or (1,))],
            "role": "geometry", "target": "solid-set", "allow_partial": False, **values}


def signed_volume6(obj):
    vertices = obj["vertices_mm"]
    total = 0
    for triangle in obj["triangles"]:
        a, b, c = [vertices[i] for i in triangle]
        total += (a[0] * (b[1] * c[2] - b[2] * c[1]) + a[1] * (b[2] * c[0] - b[0] * c[2]) +
                  a[2] * (b[0] * c[1] - b[1] * c[0]))
    return total


class SectionProfileModeling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        info = binaries.inspect_one(binaries.BY_NAME["model-base"], path=os.environ.get("GEOMETRY_MODEL_BASE"))
        if info.state != "fresh":
            raise unittest.SkipTest("Set GEOMETRY_MODEL_BASE to a freshly built adapter: " + info.reason)
        cls.base = str(info.path)

    def build(self, source=None, req=None, **options):
        return build_package({"base_scene": scene() if source is None else source, "extensions": []},
                             request() if req is None else req, base_executable=self.base, **options)

    def mesh(self, obj, volume, bounds=None):
        self.assertEqual(obj["status"], "COMPLETE")
        self.assertEqual(obj["closure"], "closed")
        self.assertEqual(obj["volume_mm3"], str(volume))
        self.assertEqual(signed_volume6(obj), 6 * volume)
        self.assertEqual(len(obj["boundary_shells"]), 1)
        self.assertEqual(obj["boundary_shells"][0]["role"], "outer")
        edges = Counter()
        for tri in obj["triangles"]:
            self.assertEqual(len(set(tri)), 3)
            for a, b in zip(tri, tri[1:] + tri[:1]):
                edges[a, b] += 1
        self.assertTrue(edges)
        self.assertTrue(all(count == 1 and edges[b, a] == 1 for (a, b), count in edges.items()))
        self.assertEqual(len(obj["vertices_mm"]) - len(edges) // 2 + len(obj["triangles"]), 2)
        if bounds is not None:
            actual = [[min(p[i] for p in obj["vertices_mm"]) for i in range(3)],
                      [max(p[i] for p in obj["vertices_mm"]) for i in range(3)]]
            self.assertEqual(actual, bounds)
            self.assertEqual(obj["section_profile"]["bounds_mm"], bounds)

    def test_three_timber_members_and_actual_concave_reference_envelope(self):
        package = self.build()
        self.assertIn("section-profile/1", package["manifest"]["capabilities"])
        objects = package["derived"]["objects"]
        self.assertEqual(len(objects), 4)
        expected = {1: [[0, 0, 0], [27, 33, 2400]], 2: [[373, 0, 0], [400, 33, 2400]],
                    3: [[0, 223, 0], [33, 250, 2400]]}
        for obj in objects:
            details = obj["section_profile"]
            self.assertEqual(details["run_id"], 1)
            self.assertEqual(details["profile_id"], 1)
            self.assertEqual(details["coordinate_space"], "local")
            identifier = details["member_id"]
            if identifier is None:
                self.mesh(obj, 84960000, [[0, 0, 0], [400, 250, 2400]])
                self.assertEqual((obj["role"], obj["member_path"], details["kind"], details["material_volume_mm3"]),
                                 ("reference", [], "envelope", "0"))
                self.assertIsNone(details["dimensions_mm"])
                self.assertTrue(all(not (v[0] > 60 and v[1] > 60) for v in obj["vertices_mm"]))
            else:
                self.mesh(obj, 2138400, expected[identifier])
                self.assertEqual((obj["role"], obj["member_path"], details["kind"]), ("geometry", [identifier], "timber"))
                self.assertEqual(details["dimensions_mm"], [27, 33, 2400])
                self.assertEqual(details["orientation"], "A-v" if identifier == 3 else "A-u")
            for sources in obj["face_sources"]:
                self.assertTrue(sources)
                for source in sources:
                    self.assertEqual(source["origin"], {"kind": "profile-run", "id": 1})
                    self.assertEqual(source["operation_path"], ["profile", "1"] if identifier is None else ["members", str(identifier)])
                    self.assertIsNone(source["placement_id"])
                    self.assertIsNone(source["boundary_id"])
        self.assertEqual(sum(int(o["section_profile"]["material_volume_mm3"]) for o in objects), 6415200)
        self.assertEqual(verify_package(package, base_executable=self.base), package)

    def test_long_panel_is_one_exact_solid_in_both_orientations(self):
        value = {"id": 44, "profileId": 1, "kind": "panel", "panelSpec": "calcium-silicate-6",
                 "width": 914, "orientation": "thickness-v", "u0": 0, "v0": 0}
        for orientation, bounds in (("thickness-v", [[0, 0, 0], [914, 6, 2000]]),
                                    ("thickness-u", [[0, 0, 0], [6, 914, 2000]])):
            package = self.build(scene(profiles=[profile(outline=[[0, 0], [1000, 0], [1000, 1000], [0, 1000]])],
                                       members=[{**value, "orientation": orientation}], runs=[run(length=literal(2000))]))
            materials = [o for o in package["derived"]["objects"] if o["role"] == "geometry"]
            self.assertEqual(len(materials), 1)
            self.mesh(materials[0], 10968000, bounds)
            self.assertEqual(materials[0]["section_profile"]["dimensions_mm"], [6, 914, 2000])
            self.assertEqual(materials[0]["member_path"], [44])

    def test_advanced_native_frame_controls_world_axes_and_bounds(self):
        package = self.build(scene(members=[member()], runs=[run(placement={"kind": "advanced", "origin": [1000, 2000, 2700], "N": "+Y", "V": "-Z"})]))
        obj = next(o for o in package["derived"]["objects"] if o["role"] == "geometry")
        self.mesh(obj, 2138400, [[1000, 2000, 2667], [1027, 4400, 2700]])
        self.assertEqual(obj["section_profile"]["coordinate_space"], "world")
        self.assertEqual(obj["section_profile"]["dimensions_mm"], [27, 33, 2400])

    def test_zero_members_and_unused_profiles_are_preserved(self):
        source = scene(profiles=[profile(), profile(2)], members=[], runs=[run()])
        package = self.build(source)
        self.assertEqual(len(package["derived"]["objects"]), 1)
        self.assertEqual(package["derived"]["status"], "COMPLETE")
        self.mesh(package["derived"]["objects"][0], 84960000)
        self.assertEqual(package["derived"]["objects"][0]["section_profile"]["material_volume_mm3"], "0")
        self.assertEqual(package["definitions"]["base_scene"].count("section-profile profile "), 2)
        self.assertEqual(verify_package(package, base_executable=self.base), package)

    def test_local_runs_do_not_cut_other_local_or_world_mesh_grids(self):
        world_run = run(2, placement={"kind": "advanced", "origin": [1001, 2003, 2707], "N": "+Y", "V": "-Z"})
        other = run(3, profileId=2, length=literal(321))
        source = scene(profiles=[profile(), profile(2, [[1, 2], [49, 2], [49, 51], [1, 51]])],
                       runs=[run(), world_run, other])
        mixed = self.build(source, request(1, 2, 3))
        for identifier in (1, 2, 3):
            selected = self.build(source, request(identifier))
            self.assertEqual([o for o in mixed["derived"]["objects"] if o["root"]["id"] == identifier], selected["derived"]["objects"])
        self.assertEqual(len({(o["root"]["id"], tuple(o["member_path"])) for o in mixed["derived"]["objects"]}), 9)

    def test_uint32_zero_ids_keep_typed_run_member_identity(self):
        package = self.build(scene(profiles=[profile(0)], members=[member(0, profileId=0)], runs=[run(0, profileId=0)]), request(0))
        self.assertEqual([o["member_path"] for o in package["derived"]["objects"]], [[], [0]])
        self.assertTrue(all(o["root"] == {"kind": "profile-run", "id": 0} for o in package["derived"]["objects"]))

    def test_spec_update_preview_cancel_confirm_and_invalid_update_preserve_source(self):
        def source(a):
            return scene(members=[member(A={"kind": "spec", "name": "A"})], runs=[run(length={"kind": "spec", "name": "L"})],
                         prefix=f"spec A {a}\nspec L 2400\n")
        world = ModelWorld({"base_scene": source(27), "extensions": []}, request(), base_executable=self.base)
        before = world.package
        pending = world.preview({"base_scene": source(29), "extensions": []})
        self.assertEqual(world.package, before)
        changed = next(o for o in pending["package"]["derived"]["objects"] if o["role"] == "geometry")
        self.mesh(changed, 2296800, [[0, 0, 0], [29, 33, 2400]])
        world.cancel(pending["token"])
        self.assertEqual(world.package, before)
        pending = world.preview({"base_scene": source(29), "extensions": []})
        world.confirm(pending["token"])
        accepted = world.package
        self.assertIn("spec A 29", accepted["definitions"]["base_scene"])
        with self.assertRaises(ModelError):
            world.preview({"base_scene": source(500), "extensions": []})
        self.assertEqual(world.package, accepted)
        with self.assertRaises(ModelError):
            world.confirm(pending["token"])

    def test_parameter_and_fixed_material_sources_survive_native_dump_and_package(self):
        binary = _bridge.find_bridge()
        with tempfile.TemporaryDirectory(prefix="q38-model-sources-") as directory:
            bridge = _bridge.BridgeSession(binary, cwd=Path(directory))
            self.addCleanup(bridge.stop)
            self.assertTrue(bridge.command("reset")["ok"])
            parameter = {"id": 0, "name": "live", "fields": [{"id": 0, "name": "A", "type": "dimension", "input": "27"},
                          {"id": 1, "name": "L", "type": "dimension", "input": "2400"}]}
            material = {"id": "q38-fixed", "version": 1, "kind": "timber", "name": "fixed", "A": 99, "B": 33}
            operations = [{"op": "put-parameter", "value": parameter}, {"op": "publish-material", "value": material},
                          {"op": "put-profile", "value": profile()},
                          {"op": "put-member", "value": member(A={"kind": "parameter", "parameterId": 0, "fieldId": 0},
                           B={"kind": "material", "id": "q38-fixed", "version": 1, "field": "B"})},
                          {"op": "put-run", "value": run(length={"kind": "parameter", "parameterId": 0, "fieldId": 1})}]
            path = Path(directory) / "transaction.json"
            path.write_text(json.dumps({"schema": "section-profile-transaction/1", "expectedRevision": bridge.command("section-profile-read")["revision"],
                                       "operations": operations}), encoding="utf-8")
            preview = bridge.command("section-profile-preview " + str(path))
            self.assertTrue(preview["ok"], preview)
            self.assertTrue(preview["preview"]["valid"], preview)
            self.assertTrue(bridge.command("section-profile-confirm " + str(preview["preview"]["token"]))["ok"])
            source = bridge.command("dump")["text"]
        package = self.build(source)
        self.assertTrue({"section-profile/1", "parameters/1", "engineering-spec/1"} <= set(package["manifest"]["capabilities"]))
        self.assertEqual(package["definitions"]["base_scene"], source)
        obj = next(o for o in package["derived"]["objects"] if o["role"] == "geometry")
        self.mesh(obj, 2138400)
        self.assertEqual(verify_package(package, base_executable=self.base), package)

    def test_invalid_native_sources_never_produce_partial_meshes(self):
        cases = [scene(members=[member(), member(2, u0=26)]), scene(members=[member(A=literal(500))]),
                 scene(runs=[run(length={"kind": "spec", "name": "absent"})]),
                 scene().replace("requires section-profile/1\n", "")]
        for source in cases:
            with self.subTest(source=source), self.assertRaises(ModelError) as caught:
                self.build(source, request(allow_partial=True))
            self.assertEqual(caught.exception.status, "INVALID")

    def test_capacity_failures_are_explicit_unsupported_even_with_partial(self):
        with self.assertRaises(ModelError) as caught:
            self.build(req=request(allow_partial=True), max_cells=1)
        self.assertEqual(caught.exception.status, "UNSUPPORTED")
        with self.assertRaises(ModelError) as caught:
            self.build(scene(profiles=[profile(i) for i in range(17)], members=[], runs=[run(profileId=0)]))
        self.assertEqual(caught.exception.status, "UNSUPPORTED")
        self.assertEqual(caught.exception.code, "BASE_CAPACITY")

    def test_capability_reduction_unknown_capability_and_old_axioms_reject(self):
        with self.assertRaises(ModelError) as caught:
            self.build(capabilities=[c for c in modeling.CAPABILITIES if c != "section-profile/1"])
        self.assertEqual(caught.exception.code, "CAPABILITY")
        with self.assertRaises(ModelError) as caught:
            self.build(capabilities=[*modeling.CAPABILITIES, "future-profile/1"])
        self.assertEqual(caught.exception.code, "CAPABILITY")
        package = self.build()
        package["manifest"]["axiom_revision"], package["manifest"]["axiom_sha256"] = next(iter(modeling.PRE_SECTION_PROFILE_AXIOM_VERSIONS))
        with self.assertRaises(ModelError) as caught:
            verify_package(package, base_executable=self.base)
        self.assertEqual(caught.exception.code, "AXIOM_VERSION")

    def test_tampered_identity_bounds_volume_or_vertices_fail_reconstruction(self):
        original = self.build()
        for field, value in (("member_id", 77), ("bounds_mm", [[0, 0, 0], [1, 1, 1]]), ("material_volume_mm3", "0"),
                             ("coordinate_space", "world"), ("dimensions_mm", [33, 27, 2400])):
            package = deepcopy(original)
            package["derived"]["objects"][1]["section_profile"][field] = value
            package["manifest"]["geometry_sha256"] = digest(package["derived"])
            with self.subTest(field=field), self.assertRaises(ModelError) as caught:
                verify_package(package, base_executable=self.base)
            self.assertEqual(caught.exception.code, "SNAPSHOT_MISMATCH")

    def test_roots_reject_wrong_roles_targets_and_composition_coercion(self):
        for values in ({"role": "clearance"}, {"role": "enclosure"}, {"target": "surface-set"}):
            with self.subTest(values=values), self.assertRaises(ModelError):
                self.build(req=request(**values))
        definitions = {"base_scene": scene(), "extensions": [{"kind": "composition", "id": 3, "op": "KEEP", "inputs": [{"kind": "profile-run", "id": 1}]}]}
        with self.assertRaises(ModelError):
            build_package(definitions, request(roots=[{"kind": "composition", "id": 3}]), base_executable=self.base)

    def test_legacy_meshes_unchanged_and_unselected_q38_sources_are_not_dropped(self):
        legacy = "column 1 at 0 0 size 20 30 z 0 40\n"
        req = request(roots=[{"kind": "column", "id": 1}])
        old = self.build(legacy, req)
        combined = self.build(scene(prefix=legacy), req)
        self.assertEqual(combined["derived"], old["derived"])
        self.assertNotIn("section-profile/1", old["manifest"]["capabilities"])
        self.assertIn("section-profile/1", combined["manifest"]["capabilities"])
        self.assertEqual(combined["definitions"]["base_scene"].count("section-profile member "), 3)
        old["manifest"]["axiom_revision"], old["manifest"]["axiom_sha256"] = next(iter(modeling.PRE_SECTION_PROFILE_AXIOM_VERSIONS))
        self.assertEqual(verify_package(old, base_executable=self.base)["derived"], old["derived"])

    def test_incomplete_native_adapter_cannot_flatten_new_sources(self):
        snapshot = load_base(scene(), executable=self.base)
        del snapshot["profile_runs"]
        result = subprocess.CompletedProcess([], 0, json.dumps(snapshot).encode(), b"")
        with mock.patch("modeling.base.subprocess.run", return_value=result), self.assertRaises(ModelError) as caught:
            load_base(scene(), executable=self.base)
        self.assertEqual((caught.exception.status, caught.exception.code), ("UNSUPPORTED", "BASE_PROTOCOL"))

    def test_obj_labels_local_reference_material_and_rejects_mixed_frames(self):
        local = obj_bytes(self.build()).decode()
        self.assertIn("coordinates: local (u,v,n) of profile-run 1", local)
        self.assertIn("kind envelope; material-volume-mm3 0", local)
        self.assertNotIn("coordinates: world", local)
        source = scene(runs=[run(), run(2, placement={"kind": "advanced", "origin": [1000, 2000, 2700], "N": "+Y", "V": "-Z"})])
        with self.assertRaises(ModelError) as caught:
            obj_bytes(self.build(source, request(1, 2)))
        self.assertEqual(caught.exception.code, "OBJ_COORDINATE_SPACE")
        self.assertIn("coordinates: world XYZ", obj_bytes(self.build(source, request(2))).decode())


if __name__ == "__main__":
    unittest.main(verbosity=2)
