"""Canonical profile authority and real I45 returned-region consumption.

The public get shim first evaluates the real K source, then changes only the
returned value. Independent linked W controls remove a dependency or bypass
that value. Every baseline and control must reach an exact named assertion;
compile errors and abnormal process exits never count as successful controls.
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
PREFIX = '''#include "section_profile_sources.h"
extern GeoSourceStatus geo261_sp_get(GeoEvalContext *,GeoSourceRef,GeoDependencyKind,GeoSourceValue *);
#define geo_eval_source geo261_sp_get
'''
PAIR_READ = "GeoSourceValue a,b;bool a_ok=wood_sp_source_pair_region(s,first,&a),b_ok=wood_sp_source_pair_region(s,second,&b);"
RECT_READ = "GeoRect2 ar,br;if(!wood_sp_source_rectangle(&a,&ar)||!wood_sp_source_rectangle(&b,&br))return false;"
GET_DEFINITION = "wood_sp_source_get(s,kind,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition)"
CONTROLS = (
    ("member-definition-bypass", "if(!wood_sp_source_load_definition(s,WOOD_SP_SOURCE_MEMBER_DEFINITION,id)){", "if(false){", "member", "member-definition-controls-geometry"),
    ("run-definition-bypass", "if(!wood_sp_source_load_definition(s,WOOD_SP_SOURCE_RUN_DEFINITION,id)){", "if(false){", "run", "run-definition-controls-length-placement"),
    ("profile-definition-bypass", "if(!wood_sp_source_load_definition(s,WOOD_SP_SOURCE_PROFILE_DEFINITION,id))return false;", "(void)id;", "profile", "profile-definition-controls-containment"),
    ("returned-frame-bypass", "r->frame=value.as.frame;r->placement_resolved=true;return true;", "r->placement_resolved=true;return true;", "frame", "run-frame-return-controls-range"),
    ("returned-host-region-bypass", "if(f.kind!=GEO_SOURCE_FRAME||!geo_frame_is_valid(&f.as.frame)||!wood_sp_source_region_copy(&r,region))return false;", "if(f.kind!=GEO_SOURCE_FRAME||!geo_frame_is_valid(&f.as.frame))return false;*region=host->region;", "host-region", "host-region-return-controls-placement"),
    ("pair-first-value-bypass", RECT_READ, "GeoRect2 ar=wood_sp_member(&s->context,first)->rect,br;if(!wood_sp_source_rectangle(&b,&br))return false;", "pair-first", "pair-first-return-controls-overlap"),
    ("pair-second-value-bypass", RECT_READ, "GeoRect2 ar,br=wood_sp_member(&s->context,second)->rect;if(!wood_sp_source_rectangle(&a,&ar))return false;", "pair-second", "pair-second-return-controls-overlap"),
    ("pair-hook-removal", "wood_sp_source_live_host,wood_sp_source_pair_root};", "wood_sp_source_live_host,NULL};", "pair", "pair-check-node"),
    ("pair-first-edge-removal", PAIR_READ, "GeoSourceValue a,b;a.kind=GEO_SOURCE_REGION_SET;a.as.regions=(GeoRegionSetView){&s->member_regions[wood_sp_source_member(s,first)],1};bool a_ok=true,b_ok=wood_sp_source_pair_region(s,second,&b);", "pair", "pair-first-member-edge"),
    ("pair-second-edge-removal", PAIR_READ, "GeoSourceValue a,b;b.kind=GEO_SOURCE_REGION_SET;b.as.regions=(GeoRegionSetView){&s->member_regions[wood_sp_source_member(s,second)],1};bool a_ok=wood_sp_source_pair_region(s,first,&a),b_ok=true;", "pair", "pair-second-member-edge"),
    ("unused-definition-removal", "for(size_t i=0;i<s->authored->profile_count;++i)if(!wood_sp_source_load_definition(s,WOOD_SP_SOURCE_PROFILE_DEFINITION,s->authored->profiles[i].id))return false;", "(void)s;", "complete", "unused-definition-complete"),
    ("definition-status-ignored", "if(" + GET_DEFINITION + "!=GEO_SOURCE_OK){", "if((" + GET_DEFINITION + ",false)){", "status-member", "definition-status-refused"),
    ("definition-schema-ignored", "definition.kind!=GEO_SOURCE_DEFINITION||!definition.as.definition.schema||strcmp(definition.as.definition.schema,wood_sp_source_schema(kind))||", "definition.kind!=GEO_SOURCE_DEFINITION||", "schema-member", "definition-bytes-refused"),
)


class SectionProfileAuthorityBoundary(unittest.TestCase):
    def test_public_keys_hooks_and_completion_keep_candidate_boundary(self):
        for name in ("section_profile.h", "section_profile.c", "section_profile_sources.h", "section_profile_sources.c"):
            source = (MODULE / name).read_text(encoding="utf-8")
            code = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
            self.assertNotRegex(code, r"\b(?:World|ReferenceEval|PlacementSurface|g_engineering_error)\b")
            self.assertNotIn("internal/", source)
        header = (MODULE / "section_profile_sources.h").read_text(encoding="utf-8")
        self.assertIn("unsigned char bytes[9]", header)
        self.assertLess(header.index("WOOD_SP_SOURCE_HOST_REGION"), header.index("WOOD_SP_SOURCE_MEMBER_PAIR_CHECK"))
        source = (MODULE / "section_profile_sources.c").read_text(encoding="utf-8")
        complete = source[source.index("bool wood_sp_sources_complete("):source.index("void wood_sp_sources_destroy(")]
        self.assertNotIn("WOOD_SP_SOURCE_RUN_FRAME", complete)
        self.assertIn("e->source_version_field==a->source_version_field", source)
        self.assertNotIn("geo_eval_", source[source.index("void wood_sp_sources_destroy("):])

    def test_each_negative_control_changes_one_live_site_and_has_exact_oracle(self):
        source = (MODULE / "section_profile_sources.c").read_text(encoding="utf-8")
        harness = (ROOT / "tests/geo261_section_profile_authority_harness.c").read_text(encoding="utf-8")
        self.assertEqual(13, len(CONTROLS))
        for name, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                self.assertEqual(1, source.count(before), name)
                self.assertNotEqual(before, after)
                self.assertIn('"' + marker + '"', harness)
                self.assertTrue(case)


class SectionProfileAuthority(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        for name in ("geo261_section_profile_sources_harness.c", "geo261_section_profile_authority_harness.c"):
            shutil.copy2(ROOT / "tests" / name, build.woodworking / name)
        cls.client = build.compile(build.woodworking / "geo261_section_profile_authority_harness.c", "section-profile-authority-client")
        cls.source = (build.woodworking / "section_profile_sources.c").read_text(encoding="utf-8")
        provider = build.woodworking / "section-profile-authority-provider.c"
        provider.write_text(PREFIX + cls.source, encoding="utf-8")
        cls.provider = build.compile(provider, "section-profile-authority-provider")
        cls.exe = build.link("section-profile-authority-client", cls.objects(build, cls.provider))

    @classmethod
    def objects(cls, build, provider):
        return [cls.client, provider, build.wood_section_profile_object, build.wood_engineering_object, *build.kernel_objects()]

    def case(self, case, executable=None):
        result = subprocess.run([str(executable or self.exe), case], capture_output=True, text=True, timeout=25)
        self.assertIn(result.returncode, (0, 1), "Crash/setup failure is not a control verdict: " + result.stderr)
        self.assertEqual("", result.stdout)
        if result.returncode:
            self.assertRegex(result.stderr, r"ASSERT:[a-z0-9-]+")
        else:
            self.assertEqual("", result.stderr)
        return result

    def test_returned_member_definition_controls_dimensions_orientation_and_coordinates(self):
        self.assertEqual(0, self.case("member").returncode)

    def test_returned_run_definition_controls_length_and_placement_without_raw_mutation(self):
        self.assertEqual(0, self.case("run").returncode)

    def test_returned_profile_controls_containment_and_published_run_region(self):
        self.assertEqual(0, self.case("profile").returncode)

    def test_returned_run_frame_controls_generated_vertex_range(self):
        for case in ("frame", "frame-status"):
            self.assertEqual(0, self.case(case).returncode)

    def test_returned_live_host_region_controls_closed_range(self):
        for case in ("host-region", "host-status"):
            self.assertEqual(0, self.case(case).returncode)

    def test_pair_node_consumes_both_member_regions_and_keeps_exact_pair_identity(self):
        for case in ("pair", "pair-first", "pair-second"):
            with self.subTest(case=case):
                self.assertEqual(0, self.case(case).returncode)

    def test_malformed_returned_definitions_refuse_each_derived_root_or_completion(self):
        for kind in ("profile", "member", "run", "unused"):
            with self.subTest(kind=kind):
                self.assertEqual(0, self.case("malformed-" + kind).returncode)

    def test_non_ok_definition_status_is_propagated_for_all_authored_record_kinds(self):
        for kind in ("profile", "member", "run", "unused"):
            with self.subTest(kind=kind):
                self.assertEqual(0, self.case("status-" + kind).returncode)

    def test_wrong_schema_and_identity_are_not_accepted_as_equivalent_definitions(self):
        for failure in ("schema", "identity"):
            for kind in ("profile", "member", "run", "unused"):
                with self.subTest(failure=failure, kind=kind):
                    self.assertEqual(0, self.case(failure + "-" + kind).returncode)

    def test_unused_profile_canonical_bytes_seal_without_evaluating_unplaced_frame(self):
        self.assertEqual(0, self.case("complete").returncode)

    def test_copied_host_definition_owns_frame_region_and_description_without_live_edge(self):
        self.assertEqual(0, self.case("copied").returncode)

    def test_existing_success_failure_order_partial_writes_and_diagnostics_remain_exact(self):
        self.assertEqual(0, self.case("parity").returncode)

    def test_thirteen_dependency_removal_and_actual_value_bypasses_fail_named_assertions(self):
        build = native()
        for name, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                self.assertEqual(0, self.case(case).returncode)
                self.assertEqual(1, self.source.count(before), "Control must change exactly one site: " + name)
                changed = build.woodworking / ("profile-authority-" + name + ".c")
                changed.write_text(PREFIX + self.source.replace(before, after), encoding="utf-8")
                obj = build.compile(changed, "profile-authority-" + name)
                exe = build.link("profile-authority-mutant-" + name, self.objects(build, obj))
                result = self.case(case, exe)
                self.assertEqual(1, result.returncode, "Control survived: " + name)
                self.assertEqual("ASSERT:" + marker + "\n", result.stderr)
                self.assertEqual(0, self.case(case).returncode)


if __name__ == "__main__":
    unittest.main(verbosity=2)
