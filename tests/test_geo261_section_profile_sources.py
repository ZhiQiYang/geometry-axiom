"""Actual profile rebuild nodes, demand edges and diagnostic equivalence.

The standalone client links the public W evaluators and actual K graph. Its
leaf callbacks check ACTIVE nodes while computing values, so post-cache graph
decoration cannot satisfy the gate. Compilation/crash is never a control kill.
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


class SectionProfileSourceBoundary(unittest.TestCase):
    def test_optional_hooks_and_provider_use_public_candidate_facts_only(self):
        for name in ("section_profile.h", "section_profile.c", "section_profile_sources.h", "section_profile_sources.c"):
            source = (MODULE / name).read_text(encoding="utf-8")
            code = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
            self.assertNotRegex(code, r"\b(?:World|PlacementSurface|SpaceBoundarySurface|ReferenceEval|ParameterSet|g_engineering_error)\b")
            self.assertNotIn("internal/", source)
            self.assertNotIn("geometry-app", source)
        header = (MODULE / "section_profile.h").read_text(encoding="utf-8")
        self.assertLess(header.index("bool (*live_host)"), header.index("const WoodSectionProfileEvaluation *evaluation;"))
        source = (MODULE / "section_profile_sources.c").read_text(encoding="utf-8")
        create = source[source.index("WoodSectionProfileSources *wood_sp_sources_create"):source.index("bool wood_sp_sources_bind")]
        self.assertIn("geo_eval_register(", create)
        self.assertNotIn("geo_eval_source(", create)
        self.assertNotIn("geo_eval_describe(", create)
        destroy = source[source.index("void wood_sp_sources_destroy"):]
        self.assertNotIn("geo_eval_", destroy)

    def test_actual_rebuild_dispatches_direct_policy_in_original_error_phase_order(self):
        source = (MODULE / "section_profile.c").read_text(encoding="utf-8")
        rebuild = source[source.index("bool wood_sp_rebuild("):source.index("const char *wood_sp_axis_name(")]
        self.assertLess(rebuild.index("evaluation->member("), rebuild.index("wood_sp_intersection("))
        self.assertLess(rebuild.index("wood_sp_intersection("), rebuild.index("evaluation->run("))
        self.assertIn("else wood_sp_evaluate_member_direct(", rebuild)
        self.assertIn("else wood_sp_evaluate_run_direct(", rebuild)
        provider = (MODULE / "section_profile_sources.c").read_text(encoding="utf-8")
        for target in ("wood_sp_evaluate_member_direct", "wood_sp_evaluate_run_direct", "wood_sp_member_dimension_direct", "wood_sp_run_length_direct", "wood_sp_resolve_placement"):
            self.assertIn(target + "(", provider)
        self.assertIn("geo_eval_depend(", provider)
        self.assertIn("geo_eval_describe(", provider)
        self.assertIn("GEO_SOURCE_DEFINITION", provider)


CONTROLS = (
    ("dimension-outside-node", "section_profile", "?w->evaluation->member_dimension(w->evaluation->user,w,i,f,f?&m->b:&m->a)", "?wood_sp_member_dimension_direct(w,i,f,f?&m->b:&m->a)", "graph", "callbacks-inside-active-values"),
    ("frame-outside-node", "section_profile", "?w->evaluation->run_placement(w->evaluation->user,w,i)", "?wood_sp_resolve_placement(w,r)", "graph", "run-inputs-drive-region"),
    ("definition-relation", "section_profile_sources", "wood_sp_source_get(s,WOOD_SP_SOURCE_MEMBER_DEFINITION,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition)", "wood_sp_source_get(s,WOOD_SP_SOURCE_MEMBER_DEFINITION,id,GEO_DEPENDENCY_VALUE_REQUIRED,&definition)", "graph", "member-definition-edge"),
    ("profile-dependency", "section_profile_sources", "(void)wood_sp_source_get(s,WOOD_SP_SOURCE_PROFILE_DEFINITION,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value);", "(void)id;", "graph", "member-profile-edge"),
    ("unplaced-frame-value", "section_profile_sources", "if(!r->placed){", "if(false){", "inactive", "unplaced-rebuild-without-frame-value"),
    ("outside-region-value", "section_profile_sources", "if(!m->resolved||m->missing_profile||m->outside||m->range_error)return false;", "if(!m->resolved||m->missing_profile||m->range_error)return false;", "regions", "outside-source-refused"),
    ("range-run-value", "section_profile_sources", "if(!r->resolved)return false;SectionProfile *p=", "if(!r->resolved&&!r->range_error)return false;SectionProfile *p=", "regions", "range-source-refused"),
    ("host-region-dependency", "section_profile_sources", "if(status!=GEO_SOURCE_OK||wood_sp_source_get(s,WOOD_SP_SOURCE_HOST_REGION,id,GEO_DEPENDENCY_VALUE_REQUIRED,&r)!=GEO_SOURCE_OK)return false;", "if(status!=GEO_SOURCE_OK)return false;", "graph", "live-host-value-edges"),
    ("candidate-binding", "section_profile_sources", "if(!s||!w||w->state!=s->context.state||w->user!=s->context.user||w->error!=s->context.error||w->error_capacity!=s->context.error_capacity||w->resolve_dimension!=s->context.resolve_dimension||w->live_host!=s->context.live_host)return false;", "if(!s||!w)return false;", "lifetime", "bind-rejects-other-candidate"),
    ("diagnostic-retry", "section_profile_sources", ".retry_failure=true", ".retry_failure=false", "diagnostics", "diagnostic-retry-preserves-first"),
    ("definition-content", "section_profile_sources", "out->as.definition=(GeoDefinitionValue){schema,content,strlen(content)};", "out->as.definition=(GeoDefinitionValue){schema,content,strlen(content)-1};", "graph", "definition-canonical-content"),
    ("geometry-units", "section_profile_sources", "if(d.kind!=GEO_SOURCE_DEFINITION)d.unit=GEO_UNIT_LENGTH;", "(void)d;", "graph", "geometry-descriptor-length-units"),
    ("member-failed-cache-write", "section_profile_sources", "GeoCoord *value=field?&m->b:&m->a;", "GeoCoord local;GeoCoord *value=&local;", "diagnostics", "failed-member-dimension-cache-write"),
    ("run-failed-cache-write", "section_profile_sources", "GeoCoord *value=&r->length;", "GeoCoord local;GeoCoord *value=&local;", "diagnostics", "failed-run-length-cache-write"),
)


class SectionProfileSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        path = build.woodworking / "section-profile-sources-client.c"
        shutil.copy2(ROOT / "tests/geo261_section_profile_sources_harness.c", path)
        cls.client = build.compile(path, "section-profile-sources-client")
        cls.exe = build.link("section-profile-sources-client", cls.objects(build))

    @classmethod
    def objects(cls, build, changed=None, module=None):
        return [cls.client, changed if module == "section_profile_sources" else build.wood_section_profile_sources_object,
                changed if module == "section_profile" else build.wood_section_profile_object,
                build.wood_engineering_object, *build.kernel_objects()]

    def case(self, name, executable=None):
        result = subprocess.run([str(executable or self.exe), name], capture_output=True, text=True, timeout=20)
        self.assertIn(result.returncode, (0, 1), "Native crash/setup failure is not a graph verdict: " + result.stderr)
        if result.returncode:
            self.assertRegex(result.stderr, r"ASSERT:[a-z0-9-]+")
        return result

    def test_actual_active_nodes_numeric_values_definition_content_and_parameter_closure(self):
        self.assertEqual(0, self.case("graph").returncode)

    def test_unplaced_frame_and_unused_definition_stay_new_with_metadata_and_sealed_reads(self):
        self.assertEqual(0, self.case("inactive").returncode)

    def test_old_diagnostic_order_all_failures_cache_equivalence_retry_and_full_error_length(self):
        self.assertEqual(0, self.case("diagnostics").returncode)

    def test_actual_outside_overlap_and_generated_vertex_range_reject_source_values(self):
        self.assertEqual(0, self.case("regions").returncode)

    def test_live_derived_closed_range_and_copied_host_dependency_distinction(self):
        self.assertEqual(0, self.case("hosts").returncode)

    def test_candidate_isolation_stable_borrowed_views_exact_keys_and_both_teardown_orders(self):
        self.assertEqual(0, self.case("lifetime").returncode)

    def test_fourteen_actual_execution_and_publication_controls_fail_named_assertions(self):
        build = native()
        for name, module, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                self.assertEqual(0, self.case(case).returncode)
                source = (build.woodworking / (module + ".c")).read_text(encoding="utf-8")
                self.assertEqual(1, source.count(before), "Control must change one actual site: " + name)
                path = build.woodworking / ("profile-sources-" + name + ".c")
                path.write_text(source.replace(before, after), encoding="utf-8")
                changed = build.compile(path, "profile-sources-" + name)
                executable = build.link("profile-sources-mutant-" + name, self.objects(build, changed, module))
                result = self.case(case, executable)
                self.assertEqual(1, result.returncode, "Control survived: " + name)
                self.assertIn("ASSERT:" + marker, result.stderr)
                self.assertEqual(0, self.case(case).returncode)


if __name__ == "__main__":
    unittest.main(verbosity=2)
