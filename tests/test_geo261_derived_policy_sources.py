"""Derived keys/fixities are typed candidate-local sources with real consumers.

Only DerivedPolicyBoundary is portable. Native compilation/execution belongs to
the serialized runner; a compiler error, setup failure or crash is not a kill.
"""
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

MODULE = ROOT / "geometry-templates/woodworking/native"
RETURN_ANCHOR = "return status==GEO_SOURCE_OK;"
RETURN_CONTROL = (
    "extern void geo261_policy_source_control(WoodFinishSourceKind,uint32_t,GeoSourceValue *);\n"
    "    if(status==GEO_SOURCE_OK)geo261_policy_source_control(kind,id,out);return status==GEO_SOURCE_OK;"
)
RELATION_ANCHOR = (
    "wood_finish_get(s,WOOD_FINISH_SOURCE_DERIVED_POLICY,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&policy)"
    "&&wood_finish_policy_walk"
)
RETURN_CASES = (
    ("returned-region", "actual-returned-region-coordinate"),
    ("returned-fixity", "actual-returned-policy-fixity"),
    ("returned-key", "actual-returned-policy-key-bytes"),
    ("returned-boundary", "actual-returned-boundary-policy-fixity"),
)


class DerivedPolicyBoundary(unittest.TestCase):
    def test_policy_api_is_W_owned_and_reconstruction_uses_direct_key_validation(self):
        header = (MODULE / "finish_sources.h").read_text(encoding="utf-8")
        for name in ("DERIVED_POLICY", "BOUNDARY_POLICY", "wood_finish_sources_edge_key", "wood_finish_sources_edge_resolve", "wood_finish_sources_definitions"):
            self.assertIn(name, header)
        source = (MODULE / "derived_placement.c").read_text(encoding="utf-8")
        direct = source[source.index("bool wood_dp_value_direct("):source.index("bool wood_dp_rebuild(")]
        self.assertIn("wood_dp_edge_key_direct(", direct)
        self.assertNotIn("wood_dp_edge_key(", direct)
        code = re.sub(r"/\*.*?\*/|//[^\n]*", "", header, flags=re.S)
        self.assertNotRegex(code, r"\b(?:World|PlacementSurface|ReferenceEval)\b")

    def test_return_controls_and_definition_edge_control_have_unique_live_anchors(self):
        source = (MODULE / "finish_sources.c").read_text(encoding="utf-8")
        self.assertEqual(1, source.count(RETURN_ANCHOR))
        self.assertEqual(1, source.count(RELATION_ANCHOR))
        self.assertEqual(1, source.count("if(!wood_finish_policy_utf8(r.data+r.at,length))return false;"))
        reader = source[source.index("bool wood_finish_sources_read_derived("):source.index("static bool wood_finish_derived_hook(")]
        self.assertIn("wood_finish_derived_geometry(", reader)
        self.assertIn("wood_finish_policy_walk(", reader)
        self.assertNotIn("s->derived[", reader)


class DerivedPolicySources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        for name in ("finish_sources.h", "finish_sources.c", "derived_placement.h", "derived_placement.c"):
            shutil.copy2(MODULE / name, build.woodworking / name)
        shutil.copy2(ROOT / "tests/geo261_finish_sources_harness.c", build.woodworking / "geo261_finish_sources_harness.c")
        client = build.woodworking / "derived-policy-sources-client.c"
        shutil.copy2(ROOT / "tests/geo261_derived_policy_sources_harness.c", client)
        cls.client = build.compile(client, "derived-policy-sources-client")
        cls.provider = build.compile(build.woodworking / "finish_sources.c", "derived-policy-sources-provider")
        cls.derived = build.compile(build.woodworking / "derived_placement.c", "derived-policy-sources-derived")
        cls.exe = build.link("derived-policy-sources-client", cls.objects(build))
        cls.return_exe = None

    @classmethod
    def objects(cls, build, changed=None):
        return [cls.client, changed or cls.provider, build.wood_finish_object, cls.derived,
                build.wood_engineering_object, build.wood_engineering_sources_object,
                build.wood_section_profile_object, build.wood_panel_layout_object, *build.kernel_objects()]

    def case(self, name, executable=None):
        result = subprocess.run([str(executable or self.exe), name], capture_output=True, text=True, timeout=30)
        self.assertIn(result.returncode, (0, 1), "Native crash/setup failure is not a policy verdict: " + result.stderr)
        return result

    def assert_case(self, name, executable=None):
        result = self.case(name, executable)
        self.assertEqual(0, result.returncode, result.stderr)

    def control_executable(self, name, before, after):
        build = native()
        original = build.woodworking / "finish_sources.c"
        snapshot = original.read_bytes()
        source = snapshot.decode("utf-8")
        self.assertEqual(1, source.count(before), "Control must match exactly once: " + name)
        path = build.woodworking / ("derived-policy-control-" + name + ".c")
        path.write_text(source.replace(before, after), encoding="utf-8")
        changed = build.compile(path, "derived-policy-control-" + name)
        executable = build.link("derived-policy-control-" + name, self.objects(build, changed))
        self.assertEqual(snapshot, original.read_bytes(), "Baseline provider source is unchanged")
        return executable

    def returned_executable(self):
        cls = type(self)
        if cls.return_exe is None:
            cls.return_exe = self.control_executable("returned-value", RETURN_ANCHOR, RETURN_CONTROL)
        return cls.return_exe

    def test_policy_describe_and_definition_only_queries_do_not_read_candidate_facts(self):
        self.assert_case("metadata")

    def test_canonical_policy_bytes_and_exact_real_consumer_dependencies(self):
        self.assert_case("graph")

    def test_policy_first_and_region_first_have_identical_results_without_cycle(self):
        self.assert_case("order")

    def test_candidate_isolation_borrowed_lifetime_sealed_reads_and_both_teardown_orders(self):
        self.assert_case("lifetime")

    def test_all_edges_key_buffer_contents_and_diagnostics_match_direct_policy(self):
        self.assert_case("keys")

    def test_unique_zero_match_component_addresses_and_public_W_resolve_hook(self):
        self.assert_case("resolve")

    def test_actual_returned_region_fixity_key_and_boundary_controls_fail_named_assertions(self):
        for case, marker in RETURN_CASES:
            with self.subTest(control=case):
                self.assert_case(case)
                result = self.case(case, self.returned_executable())
                self.assertEqual(1, result.returncode, result.stderr)
                self.assertIn("ASSERT:" + marker + ":", result.stderr)
                self.assert_case(case)

    def test_policy_definition_required_edge_control_fails_named_graph_assertion(self):
        self.assert_case("graph")
        changed = self.control_executable("definition-relation", RELATION_ANCHOR,
                                          RELATION_ANCHOR.replace("GEO_DEPENDENCY_DEFINITION_REQUIRED", "GEO_DEPENDENCY_VALUE_REQUIRED"))
        result = self.case("graph", changed)
        self.assertEqual(1, result.returncode, result.stderr)
        self.assertIn("ASSERT:derived-policy-definition-required-edge:", result.stderr)
        self.assert_case("graph")

    def test_cloned_returned_policy_ambiguity_and_later_failure_keep_partial_outputs(self):
        self.assert_case("resolve")
        self.assert_case("controlled-resolve", self.returned_executable())
        self.assert_case("resolve")

    def test_malformed_returned_policy_schema_counts_lengths_and_content_are_rejected(self):
        self.assert_case("order")
        self.assert_case("malformed", self.returned_executable())
        self.assert_case("order")

    def test_malformed_returned_boundary_policy_propagates_without_uninitialized_traversal(self):
        self.assert_case("order")
        self.assert_case("malformed-boundary", self.returned_executable())
        self.assert_case("order")

    def test_returned_policy_utf8_scalar_validation_and_bypass_control(self):
        self.assert_case("malformed-utf8", self.returned_executable())
        anchor = "if(!wood_finish_policy_utf8(r.data+r.at,length))return false;"
        build = native()
        original = build.woodworking / "finish_sources.c"
        snapshot = original.read_bytes()
        source = snapshot.decode("utf-8")
        self.assertEqual(1, source.count(anchor))
        path = build.woodworking / "derived-policy-control-utf8-bypass.c"
        path.write_text(source.replace(RETURN_ANCHOR, RETURN_CONTROL).replace(anchor, "if(false)return false;"), encoding="utf-8")
        obj = build.compile(path, "derived-policy-control-utf8-bypass")
        changed = build.link("derived-policy-control-utf8-bypass", self.objects(build, obj))
        result = self.case("malformed-utf8", changed)
        self.assertEqual(1, result.returncode, result.stderr)
        self.assertIn("ASSERT:malformed-utf8-policy-rejected-with-output-unchanged:", result.stderr)
        self.assertEqual(snapshot, original.read_bytes())
        self.assert_case("malformed-utf8", self.returned_executable())


if __name__ == "__main__":
    unittest.main(verbosity=2)
