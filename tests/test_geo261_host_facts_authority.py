"""Real returned K/W definitions govern H host facts and final validators.

The harness wraps registered production evaluators after their normal return;
canonical replacement bytes become the same graph's actual cached values.
Negative controls mutate isolated copies of H only, require an exact normal
assertion exit, and repeat the baseline before/after without changing sources.
"""
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import native

SOURCE = ROOT / 'geometry-app/native/reference_sources.inc'
VALIDATION = ROOT / 'geometry-app/native/world_validation.inc'
HARNESS = ROOT / 'tests/geo261_host_facts_authority_harness.c'
REFERENCES = ROOT / 'geometry-core/references.inc'
FLAGS = ['GEOMETRY_KERNEL_EXTERNAL=1', 'GEOMETRY_WOODWORKING_EXTERNAL=1',
         'GEOMETRY_HOST_HISTORY_EXTERNAL=1', 'GEOMETRY_HOST_CANDIDATE_EXTERNAL=1']
CONTROLS = (
    ('region-policy', 'actual->boundary_id=definition.region_id;region->id=definition.region_id;',
     'actual->boundary_id=world_find_placement(ctx->world,id)->boundary_id;region->id=actual->boundary_id;',
     'ref-policy', 'facts-ref-policy-follows-actual-region'),
    ('rect-ref', '}else if(definition.domain==GEO_PLACEMENT_REGION_REF){',
     '}else if(definition.domain==GEO_PLACEMENT_REGION_REF&&world_find_placement(ctx->world,id)->boundary_id){',
     'rect-ref', 'facts-rect-to-ref-preserves-hole'),
    ('clear-boundary', 'actual->boundary_id=0;actual->derived_fill_id=0;actual->derived_h=0;actual->component_count=0;',
     'actual->derived_fill_id=0;actual->derived_h=0;actual->component_count=0;',
     'ref-rect', 'facts-ref-to-rect-clears-boundary'),
    ('sp-domain', 'if(definition.domain==GEO_PLACEMENT_REGION_SET){*derived=true;return true;}',
     'if(world_find_placement(ctx->world,id)->derived_fill_id){*derived=true;return true;}',
     'sp-derived', 'facts-sp-actual-domain-controls-admission'),
    ('raw-footprint', 'if(ctx->use_current_values)return timber_a0_footprint_uv(&placement,&world->wood.timbers[index],&world->wood.anchors[index],out);',
     'if(!timber_a0_footprint_uv(&placement,&world->wood.timbers[index],&world->wood.anchors[index],out))return false;\n'
     '    if(ctx->use_current_values)return true;',
     'moved', 'facts-moved-actual-anchor-footprint'),
    ('raw-contact', 'if(ctx->use_current_values&&!fact->footprint_valid)continue;',
     'if(!fact->footprint_valid)continue;',
     'moved', 'facts-moved-contact-admits-actual-footprint'),
    ('final-anchor', 'if(!ctx||ctx->use_current_values){*out=world->wood.anchors[i];return true;}',
     'if(true){*out=world->wood.anchors[i];return true;}',
     'final', 'facts-final-validator-actual-anchor'),
    ('rc-column', 'if(ctx&&!ctx->use_current_values){if(!reference_sources_ensure(ctx)||!wood_definition_sources_column(ctx->definition_sources,box->id,&actual))return false;box=&actual;}',
     'if(false){if(!reference_sources_ensure(ctx)||!wood_definition_sources_column(ctx->definition_sources,box->id,&actual))return false;box=&actual;}',
     'rc', 'facts-rc-column-actual-definition'),
    ('rc-room', '        space=&actual;', '        /* isolated control discards the actual enclosure result */',
     'rc', 'facts-rc-room-actual-result'),
    ('probe-box', 'member->origin=value.as.box.frame.origin;member->axis_length=value.as.box.frame.axis_u;',
     'return true; /* isolated control discards actual local probe geometry */',
     'end-facts', 'facts-probe-consumes-actual-box'),
    ('end-refresh', 'context->target->members=context->facts.members;context->target->member_count=context->facts.member_count;',
     '/* isolated control keeps stale owner-extension facts */',
     'end-facts', 'facts-delayed-refresh-controls-owner-extension'),
    ('end-eager', '    return wood_contact_end_faces_with_sources(&facts.world,member,along_v,span_lo,span_hi,cross_lo,cross_hi,',
     '    WoodContactSourceRequest early={placement->id,along_v,member};\n'
     '    if(!reference_contact_facts(ctx,ctx->sources,&early,&source.facts))return false;\n'
     '    return wood_contact_end_faces_with_sources(&facts.world,member,along_v,span_lo,span_hi,cross_lo,cross_hi,',
     'end-facts', 'facts-span-error-precedes-source-failure'),
    ('probe-projection', '    if(from_source)uv=geo_frame_project_uv(&domain.p->frame,member->origin);',
     '    /* isolated control preserves stale cached UV */',
     'end-facts', 'facts-probe-projects-actual-origin'),
)
# D6a(a) hole-vertex grammar: the hole index must parse. Accepting a non-digit
# index as hole 0 keeps every pre-existing oracle green; only the grammar
# checks, placed after all of them in the rect-ref case, can reach this marker.
HOLE_VERTEX_CONTROL = ('hole-index-digits',
    "*v='\\0'; if (!parse_u32(q+1,&hi) || hi>=POLY_MAX_HOLES) return false;",
    "*v='\\0'; (void)parse_u32(q+1,&hi); if (hi>=POLY_MAX_HOLES) return false;",
    'rect-ref', 'facts-hole-vertex-grammar-rejects-malformed')
CONTROL_SOURCES = {'probe-projection': VALIDATION, 'hole-index-digits': REFERENCES}
# 只撤掉一項語義，要求原正常斷言精確轉紅；不把效能退化當作功能突變。
COPY_CONTROLS = (
    ('copy-clear', 'if(clear_components)memset(actual->components,0,sizeof actual->components);',
     '(void)clear_components;', 'copy-clear', 'facts-copy-clears-all-original-components'),
    ('copy-atomic', 'if(!reference_host_scratch(ctx,id,&actual,&region,&selected))return false;',
     'if(!reference_host_scratch(ctx,id,&actual,&region,&selected)){*placement=actual;return false;}',
     'malformed', 'facts-malformed-actual-definition-is-atomic'),
    ('copy-view', '*view=selected?(actual.derived_fill_id?&placement->components[0]:boundary):NULL;',
     '*view=selected?boundary:NULL;', 'copy-snapshot', 'facts-copy-snapshot-view-owned-by-caller'),
    ('scratch-view', '*view=has_boundary?(actual->derived_fill_id?&actual->components[0]:region):NULL;',
     '*view=has_boundary?region:NULL;', 'scratch-owned', 'facts-scratch-view-owned-by-caller'),
)


class HostFactsAuthorityBoundary(unittest.TestCase):
    def test_real_provider_interception_and_shared_h_adapters_are_present(self):
        harness = HARNESS.read_text(encoding='utf-8')
        self.assertIn('#include "../current_geometry.c"', harness)
        self.assertIn('geo_eval_provider_at(f->ctx.sources,i)', harness)
        for provider in ('placement', 'wood', 'enclosure', 'pose'):
            self.assertIn('f->' + provider + '_evaluate(state,graph,ref,out)', harness)
        self.assertIn('facts-actual-definition-is-k-node', harness)
        self.assertIn('facts-real-typed-dependencies', harness)
        self.assertIn('facts-moved-raw-footprint-is-invalid', harness)
        self.assertNotIn('#define geo_eval_source', harness)
        source = SOURCE.read_text(encoding='utf-8')
        self.assertIn('actual->boundary_id=definition.region_id;region->id=definition.region_id;', source)
        self.assertIn('wood_finish_sources_read_derived(ctx->finish_sources,id,&derived)', source)
        validation = (ROOT / 'geometry-app/native/world_validation.inc').read_text(encoding='utf-8')
        for function in ('app_reference_host_read', 'app_reference_member_anchor',
                         'app_reference_member_footprint', 'app_reference_validation_room',
                         'app_reference_validation_obstacle'):
            self.assertIn(function, validation)

    def test_thirteen_controls_have_unique_source_anchors_and_exact_assertions(self):
        harness = HARNESS.read_text(encoding='utf-8')
        self.assertEqual(13, len(CONTROLS))
        self.assertEqual(13, len({row[0] for row in CONTROLS}))
        for name, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                source = CONTROL_SOURCES.get(name, SOURCE).read_text(encoding='utf-8')
                self.assertEqual(1, source.count(before))
                self.assertNotEqual(before, after)
                self.assertIn('"' + case + '"', harness)
                self.assertIn('"' + marker + '"', harness)

    def test_copy_controls_have_unique_source_anchors_and_exact_assertions(self):
        source = SOURCE.read_text(encoding='utf-8')
        harness = HARNESS.read_text(encoding='utf-8')
        self.assertEqual(4, len(COPY_CONTROLS))
        for name, before, after, case, marker in COPY_CONTROLS:
            with self.subTest(control=name):
                self.assertEqual(1, source.count(before))
                self.assertNotEqual(before, after)
                self.assertIn('"' + case + '"', harness)
                self.assertIn('"' + marker + '"', harness)


class HostFactsAuthority(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        cls.client = build.compile(HARNESS, 'host-facts-authority', FLAGS)
        cls.exe = build.link('host-facts-authority', [cls.client, *build.product_objects()])

    def case(self, name, exe=None, marker=None):
        result = subprocess.run([str(exe or self.exe), name], capture_output=True,
                                text=True, encoding='utf-8', timeout=30)
        self.assertEqual(1 if marker else 0, result.returncode,
                         'Crash/setup is not an authority verdict: ' + result.stdout + result.stderr)
        self.assertEqual('ASSERT:' + marker + '\n' if marker else '', result.stderr)
        self.assertEqual('', result.stdout)

    def test_actual_ref_identity_selects_policy_and_typed_dependencies(self): self.case('ref-policy')
    def test_actual_rect_to_ref_preserves_holes_across_consumers(self): self.case('rect-ref')
    def test_actual_ref_to_rect_clears_raw_boundary(self): self.case('ref-rect')
    def test_raw_derived_host_becomes_actual_ordinary_sp_host(self): self.case('sp-ordinary')
    def test_actual_derived_sp_host_stays_lazy(self): self.case('sp-derived')
    def test_snapshot_and_no_context_keep_legacy_values(self): self.case('snapshot')
    def test_malformed_actual_definition_preserves_all_outputs_and_world(self): self.case('malformed')
    def test_actual_rectangle_clears_full_raw_component_storage(self): self.case('copy-clear')
    def test_snapshot_preserves_components_and_caller_owned_view(self): self.case('copy-snapshot')
    def test_private_scratch_view_points_into_its_caller_storage(self): self.case('scratch-owned')
    def test_moved_actual_anchor_overcomes_invalid_raw_footprint(self): self.case('moved')
    def test_final_world_validation_and_reference_check_share_actual_facts(self): self.case('final')
    def test_delayed_owner_refresh_and_span_first_error_consume_actual_facts(self): self.case('end-facts')
    def test_rc_actual_definitions_and_rebound_room_reach_final_validator(self): self.case('rc')
    def test_malformed_rc_or_room_rejects_atomically_and_fails_closed(self): self.case('rc-malformed')

    def control(self, control):
        name, before, after, case, marker = control
        build = native()
        originals = [ROOT / 'current_geometry.c', ROOT / 'geometry-core/references.inc', SOURCE, VALIDATION, HARNESS]
        saved = {path: path.read_bytes() for path in originals}
        texts = {path: data.replace(b'\r\n', b'\n').decode('utf-8') for path, data in saved.items()}
        target = CONTROL_SOURCES.get(name, SOURCE)
        self.assertEqual(1, texts[target].count(before), 'Control must hit exactly once: ' + name)
        texts[target] = texts[target].replace(before, after)
        copies = {path.resolve(): build.work / ('host-facts-' + name + '-' + path.name) for path in originals}
        for original in originals:
            def include(match):
                path = (original.parent / match.group(1)).resolve()
                return '#include "' + str(copies.get(path, path)).replace('\\', '/') + '"'
            copies[original.resolve()].write_text(
                re.sub(r'^#include "([^"]+)"', include, texts[original], flags=re.MULTILINE), encoding='utf-8')
        client = build.compile(copies[HARNESS.resolve()], 'host-facts-control-' + name, FLAGS)
        exe = build.link('host-facts-control-' + name, [client, *build.product_objects()])
        self.case(case)
        self.case(case, exe, marker)
        self.case(case)
        for original, data in saved.items():
            self.assertEqual(data, original.read_bytes(), 'Control changed repository bytes: ' + str(original))

    def test_five_host_domain_and_footprint_controls_fail_exact_oracles(self):
        for control in CONTROLS[:5]:
            with self.subTest(control=control[0]):
                self.control(control)

    def test_hole_vertex_snap_and_non_digit_hole_index_control(self):
        self.case('hole-snap')
        self.control(HOLE_VERTEX_CONTROL)

    def test_eight_contact_and_final_validator_controls_fail_exact_oracles(self):
        for control in CONTROLS[5:]:
            with self.subTest(control=control[0]):
                self.control(control)

    def test_four_copy_and_output_lifetime_controls_fail_exact_oracles(self):
        for control in COPY_CONTROLS:
            with self.subTest(control=control[0]):
                self.control(control)


if __name__ == '__main__':
    unittest.main(verbosity=2)
