"""H consumes actual typed pose/frame/threshold and authored policy values."""
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import native
from tests import _bridge, test_panel_fill_host as host

FLAGS = ['GEOMETRY_KERNEL_EXTERNAL=1', 'GEOMETRY_WOODWORKING_EXTERNAL=1',
         'GEOMETRY_HOST_HISTORY_EXTERNAL=1', 'GEOMETRY_HOST_CANDIDATE_EXTERNAL=1']
FOOTPRINT_ANCHOR = 'if(ctx->use_current_values)return true;\n    uint32_t id=world->wood.timbers[index].id;'
THRESHOLD_ANCHOR = '*out=value.as.quantity;return true;'
GUIDE_ANCHOR = 'if(ctx->use_current_values)return true;\n    int index=reference_source_guide_index(ctx->world,id);'
DATUM_CONTEXT_ANCHOR = 'if(!ctx->use_current_values){descriptor->context_from_value=true;descriptor->context.axis=-1;return true;}'
GUIDE_CONTEXT_ANCHOR = 'if(!ctx->use_current_values){descriptor->context.axis=-1;descriptor->context_from_value=true;return true;}'
GUIDE_PLACEMENT_ANCHOR = 'if(!ctx->use_current_values){if(!geo_linear_definition_sources_guide(ctx->linear_definition_sources,id,&definition))return false;q=&definition;}'


class HostAuthorityBoundary(unittest.TestCase):
    def test_harness_and_consumers_have_actual_value_paths_and_unique_controls(self):
        source = (ROOT / 'geometry-app/native/reference_sources.inc').read_text(encoding='utf-8')
        support = (ROOT / 'geometry-core/panel_fill_support.inc').read_text(encoding='utf-8')
        self.assertEqual(1, source.count(FOOTPRINT_ANCHOR))
        self.assertEqual(1, support.count(THRESHOLD_ANCHOR))
        self.assertEqual(1, source.count(GUIDE_ANCHOR))
        self.assertEqual(1, source.count(DATUM_CONTEXT_ANCHOR))
        self.assertEqual(1, source.count(GUIDE_CONTEXT_ANCHOR))
        references = (ROOT / 'geometry-core/references.inc').read_text(encoding='utf-8')
        self.assertEqual(1, references.count(GUIDE_PLACEMENT_ANCHOR))
        self.assertIn('wood_grid_sources_definition(ctx->grid_sources,id,out)', source)
        self.assertIn('wood_definition_sources_member(ctx->definition_sources,target->id,&member)', source)
        self.assertIn('wood_finish_sources_fill_definition', support)
        self.assertIn('wood_finish_sources_surface_definition', support)
        self.assertIn('wood_finish_sources_derived_definition', support)


class HostAuthority(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        cls.client = build.compile(ROOT / 'tests/geo261_host_authority_harness.c', 'host-authority-client', FLAGS)
        cls.exe = build.link('host-authority-client', [cls.client, *build.product_objects()])
        with _bridge.BridgeSession(build.bridge()) as bridge:
            fixture = host.PanelFillHost()
            fixture.bridge, fixture.directory = bridge, build.work
            fixture.host()
            fixture.timbers()
            cls.scene = build.work / 'host-authority.scene'
            cls.scene.write_text(bridge.command('dump')['text'], encoding='utf-8')

    def case(self, name, *, exe=None, failure=None):
        command = [str(exe or self.exe), name]
        if name.startswith('pf-'):
            command.append(str(self.scene))
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(1 if failure else 0, result.returncode,
                         'Crash/setup is not an authority verdict: ' + result.stdout + result.stderr)
        self.assertEqual('ASSERT:' + failure + '\n' if failure else '', result.stderr)
        self.assertEqual('', result.stdout)

    def test_typed_pose_origin_and_rotation_control_actual_footprint(self):
        self.case('origin')
        self.case('rotated')

    def test_actual_returned_placement_frame_controls_projection(self):
        self.case('frame')

    def test_reference_quantity_consumes_actual_box_frame_and_value_edges(self):
        self.case('quantity')

    def test_member_callback_consumes_actual_box_not_anchor_cache(self):
        self.case('member')

    def test_snapshot_keeps_its_direct_geometry_without_evaluating_sources(self):
        self.case('snapshot')

    def test_engineering_target_consumes_actual_member_and_anchor_definitions(self):
        self.case('target')

    def test_ownership_replay_snapshot_and_source_failure_keep_exact_admission_behavior(self):
        self.case('owned-replay')
        self.case('owned-snapshot')
        self.case('owned-failure')

    def test_assembly_eligibility_consumes_actual_guide_axis_and_member_policy(self):
        self.case('assembly-guide')
        self.case('assembly-member')

    def test_actual_datum_and_guide_definitions_resolve_metadata_after_evaluation(self):
        self.case('context-datum')
        self.case('context-guide')

    def test_actual_rotated_frame_controls_datum_guide_axis_without_metadata_evaluation(self):
        self.case('context-frame')

    def test_panel_support_consumes_returned_threshold_quantity(self):
        self.case('pf-threshold')

    def test_panel_support_projects_actual_member_boxes_without_authoring_changes(self):
        self.case('pf-footprints')

    @staticmethod
    def remap_includes(text, original, replacements):
        def replace(match):
            path = (original.parent / match.group(1)).resolve()
            return '#include "' + str(replacements.get(path, path)).replace('\\', '/') + '"'
        return re.sub(r'^#include "([^"]+)"', replace, text, flags=re.MULTILINE)

    def h_control(self, path, before, after, name, marker):
        build = native()
        originals = [ROOT / 'current_geometry.c', ROOT / 'geometry-core/references.inc',
                     ROOT / 'geometry-app/native/reference_sources.inc', ROOT / 'geometry-core/panel_fill_support.inc',
                     ROOT / 'tests/geo261_host_authority_harness.c']
        saved = {p: p.read_bytes() for p in originals}
        text = {p: data.replace(b'\r\n', b'\n').decode('utf-8') for p, data in saved.items()}
        target = ROOT / path
        self.assertEqual(1, text[target].count(before), 'Control must hit once: ' + marker)
        text[target] = text[target].replace(before, after)
        replacements = {p.resolve(): build.work / ('host-control-' + name + '-' + p.name) for p in originals}
        for original in originals:
            replacements[original.resolve()].write_text(self.remap_includes(text[original], original, replacements), encoding='utf-8')
        client = build.compile(replacements[originals[-1].resolve()], 'host-control-' + name, FLAGS)
        exe = build.link('host-control-' + name, [client, *build.product_objects()])
        self.case(name)
        self.case(name, exe=exe, failure=marker)
        self.case(name)
        for original, data in saved.items():
            self.assertEqual(data, original.read_bytes())

    def test_footprint_raw_anchor_bypass_fails_precise_actual_value_oracle(self):
        self.h_control('geometry-app/native/reference_sources.inc', FOOTPRINT_ANCHOR,
                       FOOTPRINT_ANCHOR.replace('if(ctx->use_current_values)', 'if(true)'),
                       'origin', 'host-footprint-actual-box-and-frame')

    def test_threshold_return_discard_fails_precise_actual_value_oracle(self):
        self.h_control('geometry-core/panel_fill_support.inc', THRESHOLD_ANCHOR, 'return true;',
                       'pf-threshold', 'host-pf-actual-threshold')

    def test_assembly_guide_raw_direction_bypass_fails_actual_axis_oracle(self):
        self.h_control('geometry-app/native/reference_sources.inc', GUIDE_ANCHOR,
                       GUIDE_ANCHOR.replace('if(ctx->use_current_values)', 'if(true)'),
                       'assembly-guide', 'host-assembly-guide-actual-axis')

    def test_context_flags_and_definition_preflight_controls_fail_actual_context_oracles(self):
        for anchor, case, marker in ((DATUM_CONTEXT_ANCHOR, 'context-datum', 'host-context-actual-datum-axis'),
                                     (GUIDE_CONTEXT_ANCHOR, 'context-frame', 'host-context-actual-guide-context')):
            self.h_control('geometry-app/native/reference_sources.inc', anchor,
                           anchor.replace('descriptor->context_from_value=true;', ''), case, marker)
        self.h_control('geometry-core/references.inc', GUIDE_PLACEMENT_ANCHOR, '',
                       'context-guide', 'host-context-reference-actual-guide-placement')

    def test_actual_w_definition_mutation_changes_h_engineering_target(self):
        build = native()
        original = build.woodworking / 'definition_sources.c'
        saved = original.read_bytes()
        source = saved.decode('utf-8')
        before = 'wd_write(w,(uint32_t)m->role,4);'
        self.assertEqual(1, source.count(before))
        path = build.woodworking / 'host-target-definition-control.c'
        path.write_text(source.replace(before, 'wd_write(w,(uint32_t)m->role+1,4);'), encoding='utf-8')
        changed = build.compile(path, 'host-target-definition-control')
        exe = build.link('host-target-definition-control', [self.client,
            *[changed if obj == build.wood_definition_sources_object else obj for obj in build.product_objects()]])
        for case, marker in (('target', 'host-target-actual-member-definition'),
                             ('assembly-member', 'host-assembly-member-actual-policy')):
            self.case(case)
            self.case(case, exe=exe, failure=marker)
            self.case(case)
        self.assertEqual(saved, original.read_bytes())


if __name__ == '__main__':
    unittest.main(verbosity=2)
