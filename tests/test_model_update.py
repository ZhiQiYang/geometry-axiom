"""#44 F1b producer acceptance with actual native replay and typed graphs."""
from copy import deepcopy
import base64
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "geometry-web"))
import model_update as update
import space_modeling
from modeling import ModelError, canonical_bytes, verify_package
from modeling.base import load_base
from modeling.common import digest
from tests import _bridge
from tests import binaries


def scene(*, a=27, placement=1, boundary=1, timber=0, width=4000):
    return (f"boundary {boundary} outline 0,0 {width},0 {width},3000 0,3000 kind room_plan\n"
            f"placement {placement} on boundary {boundary} origin 0 0 2500 u +x v +y\n"
            f"timber {timber} {a} 33 role boundary\n"
            f"place {timber} on {placement} at-face e0 +u +n\n")


class ModelUpdate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _bridge.find_bridge()
        info = binaries.inspect_one(binaries.BY_NAME["model-base"], path=os.environ.get("GEOMETRY_MODEL_BASE"))
        if info.state != "fresh":
            raise unittest.SkipTest("Set GEOMETRY_MODEL_BASE to freshly built adapter: " + info.reason)
        cls.base = str(info.path)
        cls.native = {"base_executable": cls.base, "bridge_executable": cls.bridge}
        cls.old = cls.record(scene())

    @classmethod
    def record(cls, source, *, timbers=True, edges=None, projection=None):
        base = load_base(source, executable=cls.base)
        placement = base["placements"][0]
        inputs = {"mode": "plan", "base_scene": base["base_scene"], "placement_id": placement["id"], "obstacles": [],
                  "settings": {"bottom": 0, "height": 3000, "edges": edges or [0, 1, 2, 3], "floor": "boundary",
                               "ceiling": "boundary", "holes": "none", "wall_thickness": 100}}
        if timbers:
            inputs["timbers"] = [{"kind": "timber", "id": solid["id"]} for solid in base["solids"] if solid["kind"] == "timber"]
        result = space_modeling.preview(inputs, base_executable=cls.base)
        metadata = {"kind": "scene", "placement_id": placement["id"], "boundary_id": placement["boundary_id"], "scene_hash": result["source_sha256"]}
        if projection is not None:
            metadata["projection"] = deepcopy(projection)
        return {"id": "model-original", "name": "舊完整模型", "created_at": "2026-10-04T03:00:00.000Z", "source": metadata,
                "input": inputs, "result": result}

    def request(self, current=None, *, record=None, placement=1, boundary=1, timber=0):
        return {"record": deepcopy(record or self.old), "current_scene": current or scene(a=29),
                "selection": {"placement_id": placement, "boundary_id": boundary, "edges": [0, 1, 2, 3],
                              "obstacles": [], "timbers": [{"kind": "timber", "id": timber}], "projection": None}}

    def prepare(self, data, **options):
        return update.prepare_update(data, **{**self.native, **options})

    def failure(self, data, code=None, *, status=None, **options):
        before = canonical_bytes(data)
        with self.assertRaises(ModelError) as caught:
            self.prepare(data, **options)
        self.assertEqual(before, canonical_bytes(data))
        if code:
            self.assertEqual(code, caught.exception.code)
        if status:
            self.assertEqual(status, caught.exception.status)
        return caught.exception

    def test_real_27_to_29_full_replacement_typed_diff_and_actual_runtime_pins(self):
        data = self.request()
        before = canonical_bytes(data)
        candidate = self.prepare(data)
        self.assertEqual(before, canonical_bytes(data))
        self.assertEqual(set(candidate), {"ok", "schema", "identity", "old_record_sha256", "current_scene_sha256", "selection", "record", "diff", "runtime"})
        self.assertTrue(candidate["ok"])
        self.assertEqual(candidate["schema"], "geometry-model-update-candidate/1")
        self.assertEqual(candidate["identity"], "unknown")
        self.assertEqual(candidate["selection"], data["selection"])
        self.assertEqual(candidate["old_record_sha256"], digest(data["record"]))
        self.assertEqual(candidate["current_scene_sha256"], hashlib.sha256(data["current_scene"].encode()).hexdigest())
        record = candidate["record"]
        for name in ("id", "name", "created_at"):
            self.assertEqual(record[name], self.old[name])
        self.assertEqual(record["input"]["settings"], self.old["input"]["settings"])
        self.assertEqual(record["result"]["summary"]["timber_volume_mm3"], str(4000 * 29 * 33))
        self.assertEqual(self.old["result"]["summary"]["timber_volume_mm3"], str(4000 * 27 * 33))
        for kind in update.PACKAGES:
            package = record["result"].get(kind)
            if package is not None:
                self.assertEqual(verify_package(package, base_executable=self.base), package)
        diff = candidate["diff"]
        self.assertEqual(set(diff), {"source", "input", "settings", "summary", "packages"})
        self.assertEqual(diff["summary"], {"before": self.old["result"]["summary"], "after": record["result"]["summary"]})
        self.assertEqual([row["kind"] for row in diff["packages"]], list(update.PACKAGES))
        for row in diff["packages"]:
            for side, target in (("before", self.old), ("after", record)):
                package = target["result"].get(row["kind"])
                self.assertEqual(row[side], digest(package["manifest"]) if package else None)
        self.assertNotEqual(diff["packages"][-1]["before"], diff["packages"][-1]["after"])
        runtime = candidate["runtime"]
        self.assertEqual(runtime["base_binary_sha256"], hashlib.sha256(Path(self.base).read_bytes()).hexdigest())
        self.assertEqual(runtime["bridge_binary_sha256"], hashlib.sha256(Path(self.bridge).read_bytes()).hexdigest())
        self.assertEqual(runtime["axiom_sha256"], hashlib.sha256((ROOT / "公理層.md").read_bytes().replace(b"\r\n", b"\n")).hexdigest())
        self.assertRegex(runtime["producer_sha256"], r"^[a-f0-9]{64}$")

    def test_explicit_different_and_same_ids_never_claim_identity_continuity(self):
        for ids in ((1, 1, 0), (0, 2, 7), (8, 9, 10)):
            placement, boundary, timber = ids
            data = self.request(scene(a=29, placement=placement, boundary=boundary, timber=timber),
                                placement=placement, boundary=boundary, timber=timber)
            candidate = self.prepare(data)
            self.assertEqual(candidate["identity"], "unknown")
            self.assertEqual(candidate["record"]["source"]["placement_id"], placement)
            self.assertEqual(candidate["record"]["source"]["boundary_id"], boundary)
            self.assertEqual(candidate["record"]["input"]["timbers"], [{"kind": "timber", "id": timber}])
        same = self.prepare(self.request(self.old["input"]["base_scene"]))
        self.assertEqual(same["identity"], "unknown")
        self.assertEqual(same["record"], self.old)

    def test_no_selection_field_is_inferred_from_old_record(self):
        for field in ("placement_id", "boundary_id", "edges", "obstacles", "timbers", "projection"):
            data = self.request()
            del data["selection"][field]
            self.failure(data, "UPDATE_SHAPE")
        for bad in (None, {}, {"kind": "placement", "id": 1}):
            data = self.request(); data["selection"] = bad
            self.failure(data, "UPDATE_SHAPE")

    def test_empty_current_material_and_obstacles_are_explicit_removal_not_old_fallback(self):
        data = self.request(); data["selection"]["timbers"] = []
        replacement = self.prepare(data)["record"]
        self.assertNotIn("timbers", replacement["input"])
        self.assertNotIn("timbers", replacement["result"])
        self.assertEqual(replacement["result"]["schema"], "geometry-space-preview/1")
        self.assertEqual(replacement["input"]["obstacles"], [])
        self.assertNotIn("timber_count", replacement["result"]["summary"])

    def test_edges_reselected_and_original_other_settings_preserved(self):
        data = self.request(scene(a=29, width=5000)); data["selection"]["edges"] = [0, 2]
        result = self.prepare(data)
        settings = result["record"]["input"]["settings"]
        self.assertEqual(settings["edges"], [0, 2])
        for key in set(settings) - {"edges"}:
            self.assertEqual(settings[key], self.old["input"]["settings"][key])
        self.assertFalse(result["record"]["result"]["summary"]["closed"])
        self.assertIsNone(result["record"]["result"]["volume"])

    def test_source_missing_wrong_boundary_wrong_kind_and_bad_edges_fail(self):
        for field, value, code in (("placement_id", 77, "UPDATE_SOURCE"), ("boundary_id", 99, "UPDATE_SOURCE"),
                                   ("edges", [], "UPDATE_EDGES"), ("edges", [0, 0], "UPDATE_EDGES"),
                                   ("edges", [True], "UPDATE_EDGES"), ("edges", [99], "SPACE_EDGES"),
                                   ("timbers", [{"kind": "beam", "id": 0}], "UPDATE_SELECTION"),
                                   ("timbers", [{"kind": "timber", "id": 90}], "UPDATE_GRAPH_UNCHECKED"),
                                   ("obstacles", [{"kind": "timber", "id": 0}], "UPDATE_SELECTION")):
            data = self.request(); data["selection"][field] = value
            self.failure(data, code)

    def test_projection_is_explicit_retained_removed_and_validated(self):
        projection = {"kind": "space-boundary-plan", "view": "top", "region": "interior", "wallSide": "outside"}
        old = self.record(scene(), projection=projection)
        data = self.request(record=old)
        self.assertNotIn("projection", self.prepare(data)["record"]["source"])
        data["selection"]["projection"] = deepcopy(projection)
        data["selection"]["projection"]["view"] = "bottom"
        self.assertEqual(self.prepare(data)["record"]["source"]["projection"], data["selection"]["projection"])
        data["selection"]["projection"]["wallSide"] = "inside"
        self.failure(data, "UPDATE_PROJECTION")

    def test_old_full_result_summary_package_input_and_metadata_must_replay_exactly(self):
        changes = (
            lambda r: r["result"]["summary"].update(timber_volume_mm3="1"),
            lambda r: r["result"]["timbers"]["derived"]["objects"][0]["vertices_mm"][0].__setitem__(0, 101),
            lambda r: r["input"]["settings"].update(height=3200),
            lambda r: r["source"].update(scene_hash="a" * 64),
            lambda r: r["result"].pop("ok"),
            lambda r: r["result"].update(extra="unrecognized"),
        )
        for change in changes:
            data = self.request(); change(data["record"])
            self.failure(data, "UPDATE_OLD_REPLAY")
        for field, value in (("id", "bad id"), ("name", " "), ("created_at", "invalid")):
            data = self.request(); data["record"][field] = value
            self.failure(data, "UPDATE_RECORD")
        data = self.request(); data["record"]["source"]["boundary_id"] = 88
        self.failure(data, "UPDATE_SOURCE")

    def test_ordinary_inline_rect_boundary_null_remains_supported_with_explicit_zero(self):
        source = "surface 0 origin 0 0 2500 u +x v +y rect 0 0 4000 3000\ntimber 0 27 33 role boundary\nplace 0 on 0 at-face e0 +u +n\n"
        old = self.record(source)
        self.assertIsNone(old["source"]["boundary_id"])
        data = self.request(source.replace("27 33", "29 33"), record=old, placement=0, boundary=0)
        candidate = self.prepare(data)
        self.assertEqual(candidate["record"]["source"]["boundary_id"], 0)
        self.assertEqual(candidate["identity"], "unknown")

    def test_faces_assembly_owned_unknown_capability_and_unplaced_sources_reject(self):
        data = self.request(); data["record"]["input"]["mode"] = "faces"
        self.failure(data, "UPDATE_SCOPE", status="UNSUPPORTED")
        for header in ("requires assembly-rule-authoring/1\n", "requires assembly-timber-generation/1\n", "requires unknown/1\n"):
            data = self.request(header + scene(a=29))
            self.failure(data, status="UNSUPPORTED")
        data = self.request(scene(a=29) + "timber 77 29 33 role primary\n")
        self.failure(data)

    def test_capacity_native_timeout_exit_protocol_and_missing_binary_are_never_green(self):
        data = self.request()
        self.failure(data, "UPDATE_EXECUTABLE", bridge_executable="/tmp/missing-update-bridge", status="UNSUPPORTED")
        self.failure(data, "UPDATE_EXECUTABLE", base_executable="/tmp/missing-update-base", status="UNSUPPORTED")
        for budget in (0, True):
            self.failure(data, "UPDATE_CAPACITY", max_cells=budget, status="UNSUPPORTED")
        self.failure(data, max_cells=1)
        too_big = self.request("#" + "x" * (update.MAX_SCENE_BYTES + 1))
        self.failure(too_big, "UPDATE_CAPACITY", status="UNSUPPORTED")
        with mock.patch.object(update, "BRIDGE_TIMEOUT", 0.000001):
            self.failure(data, "UPDATE_GRAPH_TIMEOUT", status="UNSUPPORTED")
        # Actual child processes fail; no mocked native success is accepted.
        with tempfile.TemporaryDirectory(prefix="update-bad-program-") as directory:
            executable = Path(directory) / "bad-bridge"
            for script, code in (("#!/bin/sh\nexit 3\n", "UPDATE_GRAPH_EXIT"),
                                 ('#!/bin/sh\nprintf \'{"ok":true,"schema":"source-inspector/1","complete":false}\'\n', "UPDATE_GRAPH_UNCHECKED")):
                executable.write_text(script, encoding="utf-8"); executable.chmod(0o700)
                self.failure(data, code, bridge_executable=executable, status="UNSUPPORTED")

    def test_isolated_native_children_leave_live_world_revision_pending_preview_and_ids_unchanged(self):
        with tempfile.TemporaryDirectory(prefix="update-live-proof-") as directory:
            live = _bridge.BridgeSession(self.bridge, cwd=directory)
            self.addCleanup(live.stop)
            self.assertTrue(live.command("reset")["ok"])
            self.assertTrue(live.line("surface 17 origin 0 0 2500 u +x v +y rect 0 0 2000 2000")["ok"])
            self.assertTrue(live.line("spec unrelated 77")["ok"])
            before = {command: live.command(command) for command in ("dump", "source-inspect", "newid 2")}
            request = {"schema": "engineering-transaction/1", "expectedRevision": live.command("engineering-read")["revision"],
                       "operations": [{"op": "put-parameter", "value": {"id": 0, "name": "pending", "fields": [{"id": 0, "name": "A", "type": "dimension", "input": "27"}]}}]}
            path = Path(directory) / "pending.json"; path.write_text(json.dumps(request), encoding="utf-8")
            preview = live.command("engineering-preview " + str(path))
            self.assertTrue(preview["ok"]); self.assertTrue(preview["preview"]["valid"])
            self.prepare(self.request())
            for command, expected in before.items():
                self.assertEqual(live.command(command), expected)
            self.assertTrue(live.command("engineering-confirm " + str(preview["preview"]["token"]))["ok"])

    def test_isolated_producer_preserves_live_pending_assembly_preview(self):
        from tests.test_assembly_rules import rule
        with tempfile.TemporaryDirectory(prefix="update-live-assembly-proof-") as directory:
            with _bridge.BridgeSession(self.bridge, cwd=directory) as live:
                self.assertTrue(live.command("reset")["ok"])
                before = live.command("dump")
                revision = live.command("assembly-read")["revision"]
                path = Path(directory) / "pending.json"
                path.write_text(json.dumps({"schema": "assembly-transaction/1", "expectedRevision": revision,
                                            "operations": [{"op": "publish-rule", "value": rule()}]}), encoding="utf-8")
                preview = live.command("assembly-preview " + str(path))
                self.assertTrue(preview["ok"]); self.assertTrue(preview["preview"]["valid"])
                token = preview["preview"]["token"]
                self.prepare(self.request())
                self.assertEqual(live.command("dump"), before)
                self.assertEqual(live.command("assembly-read")["revision"], revision)
                self.assertTrue(live.command("assembly-confirm " + str(token))["ok"])

    def engineering_scenes(self):
        with tempfile.TemporaryDirectory(prefix="update-fixed-proof-") as directory:
            with _bridge.BridgeSession(self.bridge, cwd=directory) as session:
                for command in ("reset", *["line " + line for line in scene().splitlines()]):
                    self.assertTrue(session.command(command)["ok"])
                def apply(operations):
                    request = {"schema": "engineering-transaction/1", "expectedRevision": session.command("engineering-read")["revision"], "operations": operations}
                    path = Path(directory) / "request.json"; path.write_text(json.dumps(request), encoding="utf-8")
                    result = session.command("engineering-preview " + str(path))
                    self.assertTrue(result["ok"], result); self.assertTrue(result["preview"]["valid"], result)
                    self.assertTrue(session.command("engineering-confirm " + str(result["preview"]["token"]))["ok"])
                material = {"id": "wood", "version": 1, "kind": "timber", "name": "Fixed", "A": 27, "B": 33}
                method = {"id": "frame", "version": 1, "name": "Fixed", "roles": {"boundary": {"id": "wood", "version": 1}}}
                apply([{"op": "publish-material", "value": material}, {"op": "publish-method", "value": method},
                       {"op": "put-application", "value": {"id": "applied", "placement_id": 1, "method": {"id": "frame", "version": 1}}},
                       {"op": "bind-timber", "id": 0, "application": "applied", "slot": "boundary"}])
                old = session.command("dump")["text"]
                apply([{"op": "publish-material", "value": {**material, "version": 2}},
                       {"op": "publish-method", "value": {**method, "version": 2, "roles": {"boundary": {"id": "wood", "version": 2}}}}])
                catalogue = session.command("dump")["text"]
                apply([{"op": "put-application", "value": {"id": "applied", "placement_id": 1, "method": {"id": "frame", "version": 2}}}])
                changed = session.command("dump")["text"]
                return old, catalogue, changed

    def test_fixed_material_method_upgrade_same_geometry_is_rejected_but_unused_catalogue_versions_are_allowed(self):
        old, catalogue, changed = self.engineering_scenes()
        record = self.record(old)
        retained = self.prepare(self.request(catalogue, record=record))
        self.assertEqual(retained["record"]["result"]["summary"]["timber_volume_mm3"], str(4000 * 27 * 33))
        error = self.failure(self.request(changed, record=record), "UPDATE_FIXED_VERSION")
        delta = error.diagnostics[0]["missing"]
        self.assertEqual({(row["kind"], row["id"], row["version"]) for row in delta["before_only"]}, {("material", "wood", 1), ("method", "frame", 1)})
        self.assertEqual({(row["kind"], row["id"], row["version"]) for row in delta["after_only"]}, {("material", "wood", 2), ("method", "frame", 2)})

    def fixed_field_scenes(self, *, override=False, swap_roots=False):
        with tempfile.TemporaryDirectory(prefix="update-fixed-fields-") as directory:
            with _bridge.BridgeSession(self.bridge, cwd=directory) as session:
                for command in ("reset", *["line " + line for line in scene().splitlines()], "line timber 2 27 33 role boundary", "line place 2 on 1 at-face e2 +u +n"):
                    self.assertTrue(session.command(command)["ok"])
                def apply(operations):
                    path = Path(directory) / "request.json"
                    path.write_text(json.dumps({"schema": "engineering-transaction/1", "expectedRevision": session.command("engineering-read")["revision"], "operations": operations}), encoding="utf-8")
                    result = session.command("engineering-preview " + str(path))
                    self.assertTrue(result["ok"], result); self.assertTrue(result["preview"]["valid"], result)
                    self.assertTrue(session.command("engineering-confirm " + str(result["preview"]["token"]))["ok"])
                def binding(identifier, field, version):
                    return {"op": "set-source", "target": {"kind": "timber", "id": identifier, "field": field},
                            "source": {"kind": "material", "id": "wood", "version": version, "field": field}}
                operations = [{"op": "publish-material", "value": {"id": "wood", "version": version, "kind": "timber", "name": "Fixed", "A": 27, "B": 33}} for version in (1, 2)]
                operations.extend([binding(0, "A", 1), binding(0, "B", 2)])
                if swap_roots:
                    operations.extend([binding(2, "A", 2), binding(2, "B", 1)])
                if override:
                    operations.append({"op": "set-override", "target": {"kind": "timber", "id": 0, "field": "A"}, "value": {"kind": "literal", "value": 27}})
                apply(operations)
                old = session.command("dump")["text"]
                operations = [binding(0, "A", 2), binding(0, "B", 1)]
                if swap_roots:
                    operations.extend([binding(2, "A", 1), binding(2, "B", 2)])
                apply(operations)
                return old, session.command("dump")["text"]

    def test_same_value_fixed_A_B_version_swap_rejects_per_field_including_inactive_override_sources(self):
        for override in (False, True):
            old, changed = self.fixed_field_scenes(override=override)
            record = self.record(old)
            self.assertEqual(self.record(changed)["result"]["summary"]["timber_volume_mm3"], record["result"]["summary"]["timber_volume_mm3"])
            failure = self.failure(self.request(changed, record=record), "UPDATE_FIXED_VERSION")
            self.assertEqual(failure.diagnostics[0]["missing"]["selected_root"], "timber:0")

    def test_same_value_fixed_versions_swapped_between_two_explicit_timber_roots_reject(self):
        old, changed = self.fixed_field_scenes(swap_roots=True)
        record = self.record(old)
        data = self.request(changed, record=record); data["selection"]["timbers"] = [{"kind": "timber", "id": value} for value in (0, 2)]
        self.failure(data, "UPDATE_FIXED_VERSION")

    def test_unselected_I9_candidate_fixed_versions_do_not_block_selected_literal_timber(self):
        old, changed = self.fixed_field_scenes()
        record = self.record(old)
        record["input"]["timbers"] = [{"kind": "timber", "id": 2}]
        record["result"] = space_modeling.preview(record["input"], base_executable=self.base)
        data = self.request(changed, record=record, timber=2)
        self.assertEqual(self.prepare(data)["record"]["result"]["summary"]["timber_volume_mm3"], str(4000 * 27 * 33))

    def test_unselected_actual_native_support_fixed_material_upgrade_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="update-real-support-") as directory:
            with _bridge.BridgeSession(self.bridge, cwd=directory) as session:
                source = scene() + ("timber 1 27 33 role boundary\nplace 1 on 1 at-face e2 +u +n\n"
                                    "spec middle 2000\nguide 1 1 v spec:middle\n"
                                    "timber 2 27 33 role primary\nplace 2 on 1 at-line guide 1 +v +n\n")
                for command in ("reset", *["line " + line for line in source.splitlines()]):
                    self.assertTrue(session.command(command)["ok"])
                def apply(operations):
                    path = Path(directory) / "request.json"
                    path.write_text(json.dumps({"schema": "engineering-transaction/1", "expectedRevision": session.command("engineering-read")["revision"], "operations": operations}), encoding="utf-8")
                    preview = session.command("engineering-preview " + str(path))
                    self.assertTrue(preview["ok"], preview); self.assertTrue(preview["preview"]["valid"], preview)
                    self.assertTrue(session.command("engineering-confirm " + str(preview["preview"]["token"]))["ok"])
                def binding(version):
                    return {"op": "set-source", "target": {"kind": "timber", "id": 0, "field": "A"},
                            "source": {"kind": "material", "id": "support-wood", "version": version, "field": "A"}}
                apply([{"op": "publish-material", "value": {"id": "support-wood", "version": version, "kind": "timber", "name": "Support", "A": 27, "B": 33}} for version in (1, 2)] + [binding(1)])
                old = session.command("dump")["text"]
                support = next(entry for entry in session.command("source-inspect")["timberSupports"]["entries"] if entry["id"] == 2)
                self.assertEqual({support[end]["relation"]["source"]["id"] for end in ("start", "finish")}, {0, 1})
                self.assertEqual({support[end]["status"] for end in ("start", "finish")}, {"exact"})
                apply([binding(2)])
                changed = session.command("dump")["text"]
        record = self.record(old)
        record["input"]["timbers"] = [{"kind": "timber", "id": 2}]
        record["result"] = space_modeling.preview(record["input"], base_executable=self.base)
        self.failure(self.request(changed, record=record, timber=2), "UPDATE_FIXED_VERSION")

    def test_different_protected_root_keys_require_explicit_correspondence(self):
        old, catalogue, _ = self.engineering_scenes()
        record = self.record(old)
        # All source definitions remain real; only the explicitly chosen root is
        # renamed. We do not infer that equal versions mean the same object.
        lines = catalogue.splitlines()
        for index, line in enumerate(lines):
            if line.startswith("engineering timber "):
                value = json.loads(base64.b64decode(line.split()[2])); value["id"] = 7
                lines[index] = "engineering timber " + base64.b64encode(canonical_bytes(value)).decode("ascii")
        changed = ("\n".join(lines) + "\n").replace("place 0 on", "place 7 on")
        data = self.request(changed, record=record, timber=7)
        self.failure(data, "UPDATE_FIXED_ASSOCIATION", status="UNSUPPORTED")

    def test_runtime_changes_during_candidate_are_rejected(self):
        original = update._runtime
        calls = []
        def changed(*args):
            result = original(*args); calls.append(result)
            if len(calls) > 1:
                result["producer_sha256"] = "0" * 64
            return result
        with mock.patch.object(update, "_runtime", side_effect=changed):
            self.failure(self.request(), "UPDATE_RUNTIME_CHANGED", status="UNSUPPORTED")


if __name__ == "__main__":
    unittest.main()
