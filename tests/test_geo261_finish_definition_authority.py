"""Returned finish definitions control W geometry and policy, not raw records.

Only FinishDefinitionBoundary is portable. All native compile/run work belongs
to the serialized validator. A crash or compiler error never counts as a kill.
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
PREFIX = '''#include "finish_sources.h"
extern GeoSourceStatus geo261_finish_get(GeoEvalContext *,GeoSourceRef,GeoDependencyKind,GeoSourceValue *);
#define geo_eval_source geo261_finish_get
'''
GET_DEFINITION = "wood_finish_get(s,kind,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value)"
SCHEMA_CHECK = "value.kind!=GEO_SOURCE_DEFINITION||!value.as.definition.schema||strcmp(value.as.definition.schema,schema)||"
CONTROLS = (
    ("surface-definition-bypass", "finish_sources", "s->decoded.items[index]=f;return true;", "(void)f;return true;", "surface", "surface-definition-controls-side-frame-obstacles"),
    ("fill-definition-bypass", "finish_sources", "s->decoded.fills[index]=fill;", "s->decoded.fills[index]=s->base.finish.state->fills[index];", "fill", "fill-definition-controls-fields-and-axis"),
    ("derived-definition-bypass", "finish_sources", "s->decoded.hosts[index]=derived;", "s->decoded.hosts[index]=s->base.finish.state->hosts[index];", "derived", "derived-definition-controls-fill-height-and-policy"),
    ("fill-origin-bypass", "finish", "input.origin[0]=d->fill->origin[0];input.origin[1]=d->fill->origin[1];", "input.origin[0]=p->origin[0];input.origin[1]=p->origin[1];", "fill", "fill-definition-controls-origin-and-stagger-axis"),
    ("fill-stagger-axis-bypass", "finish", "input.stagger_axis=d->fill->stagger_axis;", "input.stagger_axis=p->stagger_axis;", "fill", "fill-definition-controls-origin-and-stagger-axis"),
    ("finish-definition-hook-bypass", "finish_sources", "*out=wood_fs_find(&s->context.finish,id);return *out!=NULL;", "*out=wood_fs_find(&s->base.finish,id);return *out!=NULL;", "surface", "surface-definition-controls-side-frame-obstacles"),
    ("returned-gap-bypass", "finish_sources", "if(field!=WOOD_PF_THRESHOLD&&(value.as.quantity.den!=1||!geo_coord_in_range(value.as.quantity.num)))return false;\n    *out=value.as.quantity;", "if(field!=WOOD_PF_THRESHOLD&&(value.as.quantity.den!=1||!geo_coord_in_range(value.as.quantity.num)))return false;\n    *out=checked;", "gap", "returned-gap-controls-layout"),
    ("threshold-policy-bypass", "finish", "if(x.num<=0)return wood_fs_error(w,\"D44: panel-fill threshold must be a positive dimension\");", "if(false)return wood_fs_error(w,\"D44: panel-fill threshold must be a positive dimension\");", "threshold", "returned-threshold-controls-policy"),
    ("definition-status-ignored", "finish_sources", "if(!" + GET_DEFINITION + ")return false;", "(void)" + GET_DEFINITION + ";", "status-fill", "invalid-definition-return-refused-with-output-unchanged"),
    ("definition-schema-ignored", "finish_sources", SCHEMA_CHECK, "value.kind!=GEO_SOURCE_DEFINITION||", "schema-fill", "invalid-definition-return-refused-with-output-unchanged"),
    ("dormant-fill-definition-omitted", "finish_sources", "for(size_t i=0;i<state->fill_count;++i)if(!wood_finish_load_definition(s,WOOD_FINISH_SOURCE_FILL_DEFINITION,state->fills[i].id))return false;", "(void)state;", "complete", "dormant-definitions-completed"),
    ("definition-value-edge", "finish_sources", GET_DEFINITION, GET_DEFINITION.replace("GEO_DEPENDENCY_DEFINITION_REQUIRED", "GEO_DEPENDENCY_VALUE_REQUIRED"), "fill", "fill-definition-required-edge"),
    ("panel-kind-policy-bypass", "finish_sources", "if(material.kind!=0)return wood_fs_error", "if(false)return wood_fs_error", "panel-policy", "returned-panel-definition-controls-material-policy"),
    ("panel-definition-schema-bypass", "finish_sources", "definition.kind!=GEO_SOURCE_DEFINITION||!definition.as.definition.schema||strcmp(definition.as.definition.schema,\"woodworking.material-version/1\")||", "definition.kind!=GEO_SOURCE_DEFINITION||", "panel-schema", "returned-panel-definition-controls-material-policy"),
    ("selected-k-field-value-bypass", "finish_sources", "*out=(GeoQuantity){actual,1,GEO_UNIT_LENGTH};return true;", "*out=checked;return true;", "version-thickness", "returned-k-field-controls-finish-quantity"),
    ("selected-k-field-edge-bypass", "finish_sources", "if(!engineering->source_version_field(engineering->sources,0,&p->panel,selected,&actual)){", "actual=checked.num;if(false){", "version-edges", "finish-selected-k-field-edge"),
    ("shared-version-definition-bypass", "finish_sources", "wood_eng_read_version(e,0,p->panel.id,p->panel.version,&version,fields)", "wood_eng_version_view(e,0,p->panel.id,p->panel.version,&version)", "shared-version", "panel-definition-consumes-actual-shared-version-definition"),
)


class FinishDefinitionBoundary(unittest.TestCase):
    def test_definition_readers_use_decoded_candidate_owned_inputs_without_host_dependencies(self):
        header = (MODULE / "finish_sources.h").read_text(encoding="utf-8")
        source = (MODULE / "finish_sources.c").read_text(encoding="utf-8")
        for name in ("surface", "fill", "derived"):
            self.assertIn("wood_finish_sources_" + name + "_definition(", header)
            self.assertIn("wood_finish_sources_" + name + "_definition(", source)
        for name in ("finish_sources.h", "finish_sources.c", "finish.h", "finish.c"):
            content = (MODULE / name).read_text(encoding="utf-8")
            code = re.sub(r"/\*.*?\*/|//[^\n]*", "", content, flags=re.S)
            self.assertNotRegex(code, r"\b(?:World|ReferenceEval|PlacementSurface|ParameterSet)\b")
            self.assertNotIn("internal/", content)
            self.assertNotIn("geometry-app", content)
        self.assertIn("s->context.finish.state=&s->decoded", source)
        self.assertNotIn("placement_write(", source)
        for name in ("source_version_field", "source_version_definition", "source_application"):
            self.assertIn("e->" + name + "!=a->" + name, source)

    def test_every_negative_control_has_one_live_site_and_an_exact_assertion(self):
        harness = (ROOT / "tests/geo261_finish_definition_authority_harness.c").read_text(encoding="utf-8")
        self.assertEqual(17, len(CONTROLS))
        for name, module, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                self.assertEqual(1, (MODULE / (module + ".c")).read_text(encoding="utf-8").count(before), name)
                self.assertNotEqual(before, after)
                self.assertIn('"' + marker + '"', harness)
                self.assertTrue(case)


class FinishDefinitionAuthority(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        for name in ("geo261_finish_sources_harness.c", "geo261_finish_definition_authority_harness.c"):
            shutil.copy2(ROOT / "tests" / name, build.woodworking / name)
        cls.client = build.compile(build.woodworking / "geo261_finish_definition_authority_harness.c", "finish-definition-authority-client")
        cls.provider_source = (build.woodworking / "finish_sources.c").read_text(encoding="utf-8")
        path = build.woodworking / "finish-definition-authority-provider.c"
        path.write_text(PREFIX + cls.provider_source, encoding="utf-8")
        cls.provider = build.compile(path, "finish-definition-authority-provider")
        engineering = build.woodworking / "finish-definition-authority-engineering.c"
        engineering.write_text(PREFIX + (build.woodworking / "engineering_sources.c").read_text(encoding="utf-8"), encoding="utf-8")
        cls.engineering = build.compile(engineering, "finish-definition-authority-engineering")
        cls.exe = build.link("finish-definition-authority", cls.objects(build))

    @classmethod
    def objects(cls, build, module=None, changed=None):
        return [cls.client, changed if module == "finish_sources" else cls.provider,
                changed if module == "finish" else build.wood_finish_object,
                build.wood_derived_placement_object, build.wood_engineering_object, cls.engineering,
                build.wood_section_profile_object, build.wood_panel_layout_object, *build.kernel_objects()]

    def case(self, name, executable=None):
        result = subprocess.run([str(executable or self.exe), name], capture_output=True, text=True, timeout=30)
        self.assertIn(result.returncode, (0, 1), "Crash/setup failure is not a source verdict: " + result.stderr)
        self.assertEqual("", result.stdout)
        if not result.returncode:
            self.assertEqual("", result.stderr)
        return result

    def test_actual_surface_definition_controls_side_frame_obstacles_and_boundary_policy(self):
        for case in ("surface", "surface-boundary"):
            self.assertEqual(0, self.case(case).returncode)

    def test_actual_fill_definition_controls_material_axes_origin_and_stagger_policy(self):
        for case in ("fill", "fill-policy"):
            self.assertEqual(0, self.case(case).returncode)

    def test_actual_derived_definition_controls_fill_height_and_explicit_successful_writes(self):
        self.assertEqual(0, self.case("derived").returncode)

    def test_actual_parameter_quantity_controls_gap_and_threshold_without_mutating_cached_value(self):
        for case in ("gap", "threshold"):
            self.assertEqual(0, self.case(case).returncode)

    def test_actual_panel_definition_controls_material_kind_and_schema_policy(self):
        for case in ("panel-policy", "panel-schema"):
            self.assertEqual(0, self.case(case).returncode)

    def test_actual_shared_version_definition_reaches_panel_definition_without_raw_lookup(self):
        self.assertEqual(0, self.case("shared-version").returncode)

    def test_actual_width_length_thickness_quantities_use_shared_k_field_nodes(self):
        for case in ("version-width", "version-length", "version-thickness", "version-edges"):
            with self.subTest(case=case):
                self.assertEqual(0, self.case(case).returncode)

    def test_actual_field_unit_integer_range_and_status_reject_after_legacy_thickness_gate(self):
        for case in ("version-zero", "version-fraction", "version-unit", "version-status", "legacy-thickness"):
            with self.subTest(case=case):
                self.assertEqual(0, self.case(case).returncode)

    def test_definition_only_completion_includes_dormant_records_and_preserves_sealed_bytes(self):
        for case in ("complete", "dormant-malformed"):
            self.assertEqual(0, self.case(case).returncode)

    def test_all_definition_kinds_reject_failed_status_wrong_kind_schema_malformed_bytes_and_identity(self):
        for failure in ("status", "kind", "schema", "malformed", "identity"):
            for kind in ("surface", "fill", "derived"):
                with self.subTest(failure=failure, kind=kind):
                    self.assertEqual(0, self.case(failure + "-" + kind).returncode)

    def test_original_policy_order_diagnostics_partial_writes_lifetime_and_memoization(self):
        self.assertEqual(0, self.case("parity").returncode)

    def test_seventeen_actual_value_or_dependency_bypasses_fail_exact_named_assertions(self):
        build = native()
        for name, module, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                self.assertEqual(0, self.case(case).returncode)
                original = build.woodworking / (module + ".c")
                snapshot = original.read_bytes()
                source = snapshot.decode("utf-8")
                self.assertEqual(1, source.count(before), name)
                path = build.woodworking / ("finish-authority-control-" + name + ".c")
                path.write_text((PREFIX if module == "finish_sources" else "") + source.replace(before, after), encoding="utf-8")
                obj = build.compile(path, "finish-authority-control-" + name)
                exe = build.link("finish-authority-control-" + name, self.objects(build, module, obj))
                result = self.case(case, exe)
                self.assertEqual(1, result.returncode, name)
                self.assertEqual("ASSERT:" + marker + "\n", result.stderr)
                self.assertEqual(snapshot, original.read_bytes())
                self.assertEqual(0, self.case(case).returncode)


if __name__ == "__main__":
    unittest.main(verbosity=2)
