"""D28/I35/I36 grid engineering policy, direct clients and actual bridge mutants.

The W entry points mutate caller-owned candidates. The harness checks original
isolation, not a new local rollback guarantee. Native cases use the same W
object as product_objects(); no separate test implementation of the policy.
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native


class GridEngineeringBoundary(unittest.TestCase):
    def test_public_policy_accepts_candidate_context_without_host_world(self):
        source = (ROOT / "geometry-templates/woodworking/native/grid_application.c").read_text(encoding="utf-8")
        source = source[source.index("bool wood_grid_bind_engineering("):]
        source = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
        self.assertNotRegex(source, r"\b(?:World|world_find_grid|world_find_placement|scene_error|g_engineering_error)\b")
        header = (ROOT / "geometry-templates/woodworking/native/grid_application.h").read_text(encoding="utf-8")
        for entry in ("wood_grid_bind_engineering", "wood_grid_restore_engineering", "wood_grid_dimension_read"):
            self.assertRegex(header, r"\bbool\s+" + entry + r"\(")
            self.assertRegex(source, r"\bbool\s+" + entry + r"\(")


class WoodGridEngineering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        source = build.woodworking / "grid-engineering-client.c"
        shutil.copy2(ROOT / "tests/geo261_grid_engineering_harness.c", source)
        cls.client = build.compile(source, "grid-engineering-client")
        cls.exe = build.link("grid-engineering-client", [cls.client, *build.product_objects()])

    def case(self, name, exe=None, marker=None):
        result = subprocess.run([str(exe or self.exe), name], capture_output=True, text=True, timeout=10)
        self.assertIn(result.returncode, (0, 1), "Native crash/setup failure is not a policy verdict: " + result.stderr)
        self.assertEqual(1 if marker else 0, result.returncode, name + ": " + result.stderr)
        if marker:
            self.assertEqual("ASSERT:" + marker + "\n", result.stderr, "Only the exact intended assertion kills a guard")
        else:
            self.assertEqual("", result.stderr)

    def test_admission_preserves_first_error_and_missing_source_create_locks(self):
        self.case("admission")

    def test_create_update_preserve_direction_binding_and_override_identity(self):
        self.case("create-update")

    def test_anchor_inheritance_explicit_update_edges_and_bounds(self):
        self.case("anchors")

    def test_direct_gap_body_limits_and_typed_source_override_identity(self):
        self.case("dimensions")

    def test_binding_capacity_counts_unique_targets_and_allows_existing_updates(self):
        self.case("binding-capacity")

    def test_restore_panel_series_explicit_and_absent_axes(self):
        self.case("restore-axes")

    def test_restore_duplicate_capacity_shape_and_first_error(self):
        self.case("restore-errors")

    def test_candidate_host_errors_and_partial_failure_do_not_touch_original(self):
        self.case("candidate")

    def mutant(self, name, before, after, bridge=False):
        build = native()
        source = (build.woodworking / "grid_application.c").read_text(encoding="utf-8")
        self.assertEqual(1, source.count(before), "Negative control must change exactly one production guard")
        path = build.woodworking / ("grid-engineering-" + name + ".c")
        path.write_text(source.replace(before, after), encoding="utf-8")
        obj = build.compile(path, "grid-engineering-" + name)
        self.assertEqual(1, build.product_objects().count(build.wood_grid_application_object))
        objects = [obj if old == build.wood_grid_application_object else old for old in build.product_objects()]
        client = build.link("grid-engineering-" + name, [self.client, *objects])
        if not bridge:
            return client
        build.bridge()
        product = build.link("grid-engineering-" + name + "-bridge", [build.bridge_object, *objects])
        return client, product

    def test_removed_source_lock_changes_exact_first_error(self):
        self.case("admission")
        before = 'if (g && (g->from_system || g->from_binding)) return wood_eng_fail(&c->engineering,"D29: grid-system applications cannot have engineering bindings");'
        exe = self.mutant("source-lock", before, "if (false) return false;")
        self.case("admission", exe, "grid-engineering-source-first")
        self.case("admission")

    def test_removed_anchor_inheritance_guard_fails_exact_assertion(self):
        self.case("anchors")
        exe = self.mutant("anchor-inheritance", "else if (g->axis[axis].source!=GEO_GRID_SOURCE_BODY_GAP)", "else if (true)")
        self.case("anchors", exe, "grid-engineering-anchor-inheritance")
        self.case("anchors")

    def test_removed_dimension_lower_bound_fails_exact_assertion(self):
        self.case("dimensions")
        exe = self.mutant("panel-positive", "*cache<((!target->kind&&target->field)?0:1) || ", "")
        self.case("dimensions", exe, "grid-engineering-panel-positive")
        self.case("dimensions")

    def test_removed_restore_identity_guard_fails_exact_assertion(self):
        self.case("restore-errors")
        before = 'if (wood_grid_find(c->state,id)) return wood_eng_fail(&c->engineering,"I36: repeated engineering grid declaration");'
        exe = self.mutant("restore-identity", before, "if (false) return false;")
        self.case("restore-errors", exe, "grid-engineering-restore-identity")
        self.case("restore-errors")

    def commit_line(self, session, text):
        result = session.command("line " + text)
        if "preview" in result:
            self.assertTrue(result["preview"]["valid"], result)
            result = session.command("line confirm " + str(result["preview"]["token"]))
        self.assertTrue(result["ok"], result)

    def create_existing_bridge(self, exe):
        with tempfile.TemporaryDirectory(prefix="geometry-grid-eng-") as directory, _bridge.BridgeSession(exe) as session:
            self.assertTrue(session.command("reset")["ok"])
            self.commit_line(session, "surface 10 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000")
            self.commit_line(session, "grid 1 on 10 main-along u u 100 200 v 100 200")
            read = session.command("engineering-read")
            self.assertTrue(read["ok"], read)
            payload = {"schema": "engineering-transaction/1", "expectedRevision": read["revision"], "operations": [
                {"op": "publish-material", "value": {"id": "panel-a", "version": 1, "kind": "panel", "name": "Panel", "width": 915, "length": 1830}},
                {"op": "publish-method", "value": {"id": "method-a", "version": 1, "name": "Method", "panel": {"id": "panel-a", "version": 1}, "gap": 3, "longAxis": "v", "mainAlong": "u"}},
                {"op": "put-application", "value": {"id": "application-a", "placement_id": 10, "method": {"id": "method-a", "version": 1}, "anchorOptions": {"u": {"kind": "coordinate", "value": 0}, "v": {"kind": "coordinate", "value": 0}}}},
                {"op": "bind-grid", "id": 1, "application": "application-a", "create": True},
            ]}
            request = Path(directory) / "request.json"
            request.write_text(json.dumps(payload), encoding="utf-8")
            original = session.command("dump")["text"]
            response = session.command("engineering-preview " + str(request))
            self.assertEqual(original, session.command("dump")["text"], "Preview must not commit either baseline or mutant")
            accepted = bool(response.get("preview", {}).get("valid", False))
            if accepted:
                confirmed = session.command("engineering-confirm " + str(response["preview"]["token"]))
                self.assertTrue(confirmed["ok"], confirmed)
                sources = session.command("engineering-read")["state"]["sources"]
                self.assertEqual(4, len(sources))
                self.assertEqual({("grid", 1, axis, field) for axis in ("u", "v") for field in ("panel", "gap")},
                                 {(item["target"]["kind"], item["target"]["id"], item["target"]["axis"], item["target"]["field"]) for item in sources})
                for item in sources:
                    target = item["target"]
                    self.assertEqual({"kind": "application", "id": "application-a", "field": target["axis"] + "." + target["field"]}, item["source"])
                    self.assertIsNone(item["override"])
            return accepted, response

    def test_removed_create_lock_fails_exact_client_and_actual_bridge(self):
        build = native()
        self.case("create-update")
        accepted, response = self.create_existing_bridge(build.bridge())
        self.assertFalse(accepted, response)
        self.assertIn("create grid ID already exists; select update instead", json.dumps(response))
        before = '} else if (create) return wood_eng_fail(&c->engineering,"D28: create grid ID already exists; select update instead");'
        exe, bridge = self.mutant("create-existing", before, "}", bridge=True)
        self.case("create-update", exe, "grid-engineering-create-existing")
        accepted, response = self.create_existing_bridge(bridge)
        self.assertTrue(accepted, response)
        self.case("create-update")
        accepted, response = self.create_existing_bridge(build.bridge())
        self.assertFalse(accepted, response)
        self.assertIn("create grid ID already exists; select update instead", json.dumps(response))


if __name__ == "__main__":
    unittest.main(verbosity=2)
