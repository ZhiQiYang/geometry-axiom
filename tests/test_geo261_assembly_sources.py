"""Candidate-local assembly definitions, dimensions, generation and I42 graph.

Portable checks never build. Native cases and negative controls belong to the
serialized validation lane; compiler errors or crashes cannot count as kills.
"""
from copy import deepcopy
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import native
from tests.test_geo261_wood_assembly import rule, binding, source, canonical, digest

MODULE = ROOT / "geometry-templates/woodworking/native"


def fixture():
    selected = binding()
    selected["slots"][0]["A"] = {"kind": "parameter", "parameterId": 90, "fieldId": 2}
    selected["slots"][0]["B"] = {"kind": "spec", "name": "depth"}
    for field in ("A", "B"):
        selected["slots"][1][field] = {"kind": "material", "id": "wood", "version": 1, "field": field}
    incomplete = deepcopy(selected)
    incomplete["id"] = 10
    incomplete["name"] = "unfinished"
    for slot in incomplete["slots"]:
        for field in ("A", "B", "contactFace", "orientation"):
            slot[field] = None
    unused = rule()
    unused.update(id=80, name="unused rule")
    return {"material": {"id": "wood", "version": 1, "kind": "timber", "name": "wood", "A": 27, "B": 33},
            "rule": rule(), "unusedRule": unused, "binding": selected, "incomplete": incomplete,
            "create": {"op": "create-instance", "expectedBindingFingerprint": digest(selected), "value": source()}}


class AssemblySourceBoundary(unittest.TestCase):
    def test_public_ownership_registration_and_borrowed_lifetime(self):
        for name in ("assembly.h", "assembly.c", "assembly_sources.h", "assembly_sources.c"):
            text = (MODULE / name).read_text(encoding="utf-8")
            code = re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S)
            self.assertNotRegex(code, r"\b(?:World|ReferenceEval|TimberAnchor|PlacementSurface|ParameterSet)\b")
            self.assertNotIn("internal/", text)
            self.assertNotIn("geometry-app", text)
        source_text = (MODULE / "assembly_sources.c").read_text(encoding="utf-8")
        create = source_text[source_text.index("WoodAssemblySources *wood_assembly_sources_create"):source_text.index("bool wood_assembly_sources_bind")]
        self.assertIn("geo_eval_register(", create)
        self.assertNotIn("geo_eval_source(", create)
        self.assertNotIn("geo_eval_describe(", create)
        self.assertNotIn("geo_eval_", source_text[source_text.index("void wood_assembly_sources_destroy"):])
        describe = source_text[source_text.index("static bool wood_assembly_describe"):source_text.index("static bool wood_assembly_evaluate")]
        self.assertNotIn("wood_eng_material(", describe)
        self.assertNotIn("json_parse(", describe)

    def test_original_policy_hooks_and_generation_check_stay_separate(self):
        policy = (MODULE / "assembly.c").read_text(encoding="utf-8")
        provider = (MODULE / "assembly_sources.c").read_text(encoding="utf-8")
        for name in ("wood_assembly_binding_rebuild_direct", "wood_assembly_slot_dimension_direct", "wood_assembly_member_definition_direct", "wood_assembly_generated_dimension_direct", "wood_assembly_instance_check_direct"):
            self.assertIn(name + "(", policy)
            self.assertIn(name + "(", provider)
        self.assertIn("EngTarget target={1,0,0,axis}", policy)
        self.assertIn("UINT32_MAX,0", policy)
        self.assertIn("if(geo_json_is_null(j,value)){b->complete=false;continue;}", policy)
        dimensions = provider[provider.index("bool wood_assembly_sources_owned_dimensions"):provider.index("bool wood_assembly_sources_definitions")]
        self.assertNotIn("footprint(", dimensions)
        self.assertNotIn("instance_check", dimensions)
        self.assertIn("*out=value.as.quantity.num", provider)


CONTROLS = (
    ("binding-rule-relation", "assembly_sources", "GEO_DEPENDENCY_DEFINITION_REQUIRED)==GEO_SOURCE_OK;}", "GEO_DEPENDENCY_VALUE_REQUIRED)==GEO_SOURCE_OK;}", "graph", "binding-rule-definition-identity-edge"),
    ("generated-dimension-hook", "assembly", "w->evaluation&&w->evaluation->generated_dimension?", "false?", "graph", "generated-slot-actual-quantity-edges"),
    ("quantity-actual-value", "assembly_sources", "*out=value.as.quantity.num;", "*out=value.as.quantity.num+1;", "graph", "generated-dimensions-and-direct-policy-parity"),
    ("null-slot-quantity", "assembly", "if(geo_json_is_null(j,value)){b->complete=false;continue;}", "if(geo_json_is_null(j,value)){b->complete=false;if(!resolve)continue;}", "definitions", "incomplete-binding-remains-legal"),
    ("I42-check-hook", "assembly", "if(w->evaluation&&w->evaluation->instance_check){", "if(false){", "graph", "I42-actual-pose-value-edge"),
    ("failed-retry", "assembly_sources", ".retry_failure=true", ".retry_failure=false", "diagnostics", "failed-binding-retries-original-diagnostic"),
)


class AssemblySources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        for name in ("assembly_sources.h", "assembly_sources.c"):
            shutil.copy2(MODULE / name, build.woodworking / name)
        source_path = build.woodworking / "assembly-sources-client.c"
        shutil.copy2(ROOT / "tests/geo261_assembly_sources_harness.c", source_path)
        cls.client = build.compile(source_path, "assembly-sources-client")
        cls.provider = build.compile(build.woodworking / "assembly_sources.c", "assembly-sources-provider-client")
        cls.fixture_path = build.work / "assembly-sources-fixture.json"
        cls.fixture_path.write_text(canonical(fixture()), encoding="utf-8")
        cls.exe = build.link("assembly-sources-client", cls.objects(build))

    @classmethod
    def objects(cls, build, module=None, changed=None):
        return [cls.client, changed if module == "assembly_sources" else cls.provider,
                changed if module == "assembly" else build.wood_assembly_object,
                build.wood_engineering_object, build.wood_engineering_sources_object,
                build.wood_members_object, *build.kernel_objects()]

    def case(self, name, executable=None):
        result = subprocess.run([str(executable or self.exe), name, str(self.fixture_path)], capture_output=True, text=True, timeout=30)
        self.assertIn(result.returncode, (0, 1), "Native crash/setup failure is not an assembly verdict: " + result.stderr)
        return result

    def test_actual_generation_quantities_pose_and_final_contact_edges(self):
        result = self.case("graph")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_unused_canonical_definitions_nullable_slots_and_no_eager_geometry(self):
        result = self.case("definitions")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_original_anonymous_target_error_order_and_retry(self):
        result = self.case("diagnostics")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_partial_primary_writes_and_real_one_unit_contact_rejection(self):
        result = self.case("partial")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_candidate_identity_stable_keys_and_both_teardown_orders(self):
        result = self.case("lifetime")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_six_controls_fail_the_named_independent_assertions(self):
        build = native()
        for name, module, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                baseline = self.case(case)
                self.assertEqual(0, baseline.returncode, baseline.stderr)
                original = build.woodworking / (module + ".c")
                original_bytes = original.read_bytes()
                source_text = original_bytes.decode("utf-8")
                self.assertEqual(1, source_text.count(before), "Control must match exactly once: " + name)
                path = build.woodworking / ("assembly-source-control-" + name + ".c")
                path.write_text(source_text.replace(before, after), encoding="utf-8")
                changed = build.compile(path, "assembly-source-control-" + name)
                executable = build.link("assembly-source-control-" + name, self.objects(build, module, changed))
                result = self.case(case, executable)
                self.assertEqual(1, result.returncode, result.stderr)
                self.assertIn("ASSERT:" + marker + ":", result.stderr)
                self.assertEqual(original_bytes, original.read_bytes())
                restored = self.case(case)
                self.assertEqual(0, restored.returncode, restored.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
