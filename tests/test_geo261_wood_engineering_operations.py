"""Ordered D28 editing and I36 member replay use the real product W object."""
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


class EngineeringOperationsBoundary(unittest.TestCase):
    def test_public_policy_uses_explicit_candidate_facts_and_writes(self):
        source = (ROOT / "geometry-templates/woodworking/native/engineering_operations.c").read_text(encoding="utf-8")
        source = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
        self.assertNotRegex(source, r"\b(?:World|world_find_timber|reference_timber_index|g_engineering_error|scene_error)\b")
        header = (ROOT / "geometry-templates/woodworking/native/engineering_operations.h").read_text(encoding="utf-8")
        for entry in ("wood_engineering_operation", "wood_engineering_restore_member"):
            self.assertRegex(header, r"\bbool\s+" + entry + r"\(")
            self.assertRegex(source, r"\bbool\s+" + entry + r"\(")


class WoodEngineeringOperations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        source = build.woodworking / "engineering-operations-client.c"
        shutil.copy2(ROOT / "tests/geo261_engineering_operations_harness.c", source)
        cls.client = build.compile(source, "engineering-operations-client")
        cls.exe = build.link("engineering-operations-client", [cls.client, *build.product_objects()])

    def case(self, name, exe=None, marker=None):
        result = subprocess.run([str(exe or self.exe), name], capture_output=True, text=True, timeout=10)
        self.assertIn(result.returncode, (0, 1), "Native crash/setup failure is not an engineering verdict: " + result.stderr)
        self.assertEqual(1 if marker else 0, result.returncode, name + ": " + result.stderr)
        self.assertEqual("ASSERT:" + marker + "\n" if marker else "", result.stderr, "Only the exact intended assertion kills a guard")

    def test_unplaced_source_override_rejection_and_typed_identity_removal(self):
        self.case("sources")

    def test_unbind_rebuild_effective_cache_write_then_binding_compaction(self):
        self.case("unbind-order")

    def test_unbind_parameter_and_effective_failures_preserve_binding_and_cache(self):
        self.case("unbind-failures")

    def test_bind_timber_requires_selected_face_placement_and_matching_role(self):
        self.case("roles")

    def test_publication_wrapper_fingerprint_fields_and_application_dispatch(self):
        self.case("publication")

    def test_member_restore_priority_identity_capacity_and_unplaced_sources(self):
        self.case("restore-members")

    def test_grid_dispatch_preserves_operation_shape_and_application_targets(self):
        self.case("grid-dispatch")

    def test_candidate_callbacks_and_late_failure_leave_original_unchanged(self):
        self.case("candidate")

    def mutant(self, name, before, after, bridge=False):
        build = native()
        source = (build.woodworking / "engineering_operations.c").read_text(encoding="utf-8")
        self.assertEqual(1, source.count(before), "Negative control must change exactly one production guard")
        path = build.woodworking / ("engineering-operations-" + name + ".c")
        path.write_text(source.replace(before, after), encoding="utf-8")
        obj = build.compile(path, "engineering-operations-" + name)
        self.assertEqual(1, build.product_objects().count(build.wood_engineering_operations_object))
        objects = [obj if old == build.wood_engineering_operations_object else old for old in build.product_objects()]
        client = build.link("engineering-operations-" + name, [self.client, *objects])
        if not bridge:
            return client
        build.bridge()
        product = build.link("engineering-operations-" + name + "-bridge", [build.bridge_object, *objects])
        return client, product

    def test_removed_rebuild_failure_guard_fails_named_assertion(self):
        self.case("unbind-failures")
        before = "if(!operations->rebuild_parameters(operations->user,error,sizeof error))return wood_eng_fail(w,error);"
        exe = self.mutant("unbind-rebuild", before, "(void)operations->rebuild_parameters(operations->user,error,sizeof error);")
        self.case("unbind-failures", exe, "engineering-operations-unbind-rebuild-failure")
        self.case("unbind-failures")

    def test_removed_role_guard_fails_named_assertion(self):
        self.case("roles")
        exe = self.mutant("matching-role", " || fact.role!=r)", ")")
        self.case("roles", exe, "engineering-operations-role-lock")
        self.case("roles")

    def test_removed_publication_extra_field_guard_fails_named_assertion(self):
        self.case("publication")
        before = 'if (!geo_json_keys(j,t,"op,value","fingerprint")) return wood_eng_fail(w,"I35: unexpected publication operation fields");'
        exe = self.mutant("publication-fields", before, "if (false) return false;")
        self.case("publication", exe, "engineering-operations-publication-fields")
        self.case("publication")

    def test_removed_noncustom_priority_guard_fails_named_assertion(self):
        self.case("restore-members")
        before = 'else if(pt>=0)return wood_eng_fail(w,"I36: non-custom role cannot set priority");'
        exe = self.mutant("restore-priority", before, "")
        self.case("restore-members", exe, "engineering-operations-restore-priority")
        self.case("restore-members")

    def test_removed_restore_identity_guard_fails_named_assertion(self):
        self.case("restore-members")
        exe = self.mutant("restore-identity", "w->target(w->user,&lookup,&fact) || ", "")
        self.case("restore-members", exe, "engineering-operations-restore-identity")
        self.case("restore-members")

    def unplaced_source_bridge(self, exe):
        with tempfile.TemporaryDirectory(prefix="geometry-eng-operations-") as directory, _bridge.BridgeSession(exe) as session:
            self.assertTrue(session.command("reset")["ok"])
            declared = session.command("line timber 1 27 33 role primary")
            if "preview" in declared:
                self.assertTrue(declared["preview"]["valid"], declared)
                declared = session.command("line confirm " + str(declared["preview"]["token"]))
            self.assertTrue(declared["ok"], declared)
            read = session.command("engineering-read")
            self.assertTrue(read["ok"], read)
            payload = {"schema": "engineering-transaction/1", "expectedRevision": read["revision"], "operations": [
                {"op": "set-source", "target": {"kind": "timber", "id": 1, "field": "A"}, "source": {"kind": "literal", "value": 55}},
            ]}
            request = Path(directory) / "request.json"
            request.write_text(json.dumps(payload), encoding="utf-8")
            original = session.command("dump")["text"]
            response = session.command("engineering-preview " + str(request))
            self.assertEqual(original, session.command("dump")["text"])
            accepted = bool(response.get("preview", {}).get("valid", False))
            if accepted:
                confirmed = session.command("engineering-confirm " + str(response["preview"]["token"]))
                self.assertTrue(confirmed["ok"], confirmed)
                sources = session.command("engineering-read")["state"]["sources"]
                self.assertEqual(1, len(sources))
                self.assertEqual({"kind": "timber", "id": 1, "field": "A"}, sources[0]["target"])
                self.assertEqual({"kind": "literal", "value": 55}, sources[0]["source"])
                self.assertEqual(55, sources[0]["effective"])
                self.assertIsNone(sources[0]["override"])
            return accepted, response

    def test_removed_unplaced_guard_fails_named_client_and_actual_bridge(self):
        build = native()
        self.case("sources")
        accepted, response = self.unplaced_source_bridge(build.bridge())
        self.assertFalse(accepted, response)
        self.assertIn("bind only an already placed timber", json.dumps(response))
        before = 'if (!fact.placed) return wood_eng_fail(w,"D28: bind only an already placed timber");'
        exe, bridge = self.mutant("unplaced-source", before, "if (false) return false;", bridge=True)
        self.case("sources", exe, "engineering-operations-unplaced-source")
        accepted, response = self.unplaced_source_bridge(bridge)
        self.assertTrue(accepted, response)
        self.case("sources")
        accepted, response = self.unplaced_source_bridge(build.bridge())
        self.assertFalse(accepted, response)
        self.assertIn("bind only an already placed timber", json.dumps(response))


if __name__ == "__main__":
    unittest.main(verbosity=2)
