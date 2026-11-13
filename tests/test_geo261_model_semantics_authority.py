"""Finite H metadata authority: actual FIELDDEF and SP definition-node results.

D9/I29/I46 witnesses exercise the real model adapter and linked K/W product.
Native execution is deliberately separate from the two portable boundary
checks; importing this module never instantiates NativeBuild.
"""
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import test_geo261_native_kernel as kernel_tests

SOURCE = ROOT / 'geometry-app/native/model_sources.inc'
HARNESS = ROOT / 'tests/geo261_model_semantics_authority_harness.c'
FLAGS = ['GEOMETRY_KERNEL_EXTERNAL=1', 'GEOMETRY_WOODWORKING_EXTERNAL=1',
         'GEOMETRY_HOST_HISTORY_EXTERNAL=1', 'GEOMETRY_HOST_CANDIDATE_EXTERNAL=1']
# K closes registration at the first source request (source.h), so priming
# FIELDDEF must follow the adapter's own provider registration.
INSTALL_HOOK = 'if(!geo_eval_register(state->reference.sources,&provider))return false;'
ALIAS_HOOK = 'for(size_t i=0;i<state->count;++i){ModelSourceItem *item=state->items[i];GeoSourceValue value;'
TYPE_ASSIGNMENT = 'item->quantity_type=field.type==GEO_PARAMETER_COUNT?"count":field.type==GEO_PARAMETER_RATIO?"ratio":"dimension";'
RAW_FIELD = ('geo_parameters_fields(&state->reference.world->geo.parameters)'
             '[geo_parameters_field_index(&state->reference.world->geo.parameters,item->id,item->member_id)]')
RAW_CORE_FIELD = ('geo_parameters_fields(&state->reference.world->geo.parameters)'
                  '[geo_parameters_field_index(&state->reference.world->geo.parameters,ids[0],ids[1])]')

# Each replacement hits one exact production statement in an isolated copy.
# Every control is bracketed by the unchanged executable and must reach its
# declared first semantic ASSERT with normal exit 1, empty stdout, no crash.
CONTROLS = (
    ('raw-parameter-type', TYPE_ASSIGNMENT,
     'field.type=' + RAW_FIELD + '.type;' + TYPE_ASSIGNMENT,
     'parameter-ratio', 'sem-parameter-actual-type-controls-alias'),
    ('raw-parameter-name', 'memcpy(item->owned_name,field.name,sizeof item->owned_name);',
     'memcpy(item->owned_name,' + RAW_FIELD + '.name,sizeof item->owned_name);',
     'parameter-ratio', 'sem-parameter-actual-name-controls-root'),
    ('raw-core-parameter-type', 'root->member_id==ids[1])return root->quantity_type;',
     'root->member_id==ids[1])return ' + RAW_CORE_FIELD + '.type==GEO_PARAMETER_COUNT?"count":' + RAW_CORE_FIELD + '.type==GEO_PARAMETER_RATIO?"ratio":"dimension";',
     'parameter-ratio', 'sem-parameter-actual-type-controls-core-export'),
    ('parameter-schema', 'strcmp(definition.as.definition.schema,"geometry.parameter-field/1")',
     'false', 'parameter-bad', 'sem-parameter-invalid-definition-refuses-alias'),
    ('parameter-identity', 'field.parameter_id!=item->id||field.id!=item->member_id||',
     'field.parameter_id!=item->id||', 'parameter-bad', 'sem-parameter-invalid-definition-refuses-alias'),
    ('parameter-edge', 'item->id,item->member_id,&key),GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition)',
     'item->id,item->member_id,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&definition)',
     'parameter-ratio', 'sem-parameter-alias-definition-required'),
    ('raw-run-roots', 'const ProfileRun *run=&state->profile_runs[i];SectionProfile actual_profile;',
     'const ProfileRun *run=&profiles->runs[i];SectionProfile actual_profile;',
     'to-placed', 'sem-sp-actual-placement-controls-domain'),
    ('raw-member-roots', 'const ProfileMember *member=m?&state->profile_members[m-1]:NULL;',
     'const ProfileMember *member=m?&profiles->members[m-1]:NULL;',
     'member-map', 'sem-sp-actual-mapping-controls-root-membership'),
    ('raw-run-owner', 'profile=state->profile_runs[i].profile_id;break;',
     'profile=state->reference.world->wood.section_profiles.runs[i].profile_id;break;',
     'run-map', 'sem-sp-actual-run-owner'),
    ('raw-member-owner', 'profile=state->profile_members[i].profile_id;break;',
     'profile=state->reference.world->wood.section_profiles.members[i].profile_id;break;',
     'member-map', 'sem-sp-actual-member-owner'),
)


class ModelSemanticsAuthorityBoundary(unittest.TestCase):
    def test_actual_definition_hooks_and_public_copy_boundary_are_present(self):
        source = SOURCE.read_text(encoding='utf-8')
        harness = HARNESS.read_text(encoding='utf-8')
        header = (ROOT / 'geometry-templates/woodworking/native/section_profile_sources.h').read_text(encoding='utf-8')
        self.assertEqual(1, source.count(INSTALL_HOOK))
        self.assertEqual(1, source.count(ALIAS_HOOK))
        self.assertIn('geo_parameter_field_definition_decode(definition.as.definition.content', source)
        self.assertIn('GEO_PARAMETER_DEFINITION_FIELD', source)
        for kind in ('profile', 'member', 'run'):
            self.assertIn('wood_sp_sources_' + kind + '_definition(', source)
            self.assertIn('wood_sp_sources_' + kind + '_definition(', header)
        self.assertIn('sem_prime_parameter_definition(reference)', harness)
        self.assertIn('geo_eval_source(reference->sources,definition,GEO_DEPENDENCY_DEFINITION_REQUIRED,&returned)', harness)
        self.assertIn('actual->as.definition.content=sem_field_bytes;actual->as.definition.content_size=sem_field_size;', harness)
        self.assertNotIn('sem_parameter_provider', harness)
        self.assertIn('if(provider->token==APP_SOURCE_PARAMETER_DEFINITION)parameter=true;', harness)
        self.assertIn('provider->evaluate=sem_sp_provider', harness)
        self.assertIn('GeoSourceValue *actual=(GeoSourceValue *)node.value;', harness)
        self.assertIn('offsetof(ProfileMember,a)', harness)
        self.assertIn('offsetof(ProfileRun,length)', harness)
        self.assertIn('sem-parameter-authored-fields-unchanged', harness)
        self.assertIn('sem-sp-unplaced-world-frame-is-new', harness)
        self.assertNotIn('#define geo_eval_source', harness)

    def test_all_controls_have_unique_production_anchors_and_exact_failure_oracles(self):
        source = SOURCE.read_text(encoding='utf-8')
        harness = HARNESS.read_text(encoding='utf-8')
        self.assertEqual(10, len(CONTROLS))
        self.assertEqual(len(CONTROLS), len({control[0] for control in CONTROLS}))
        for name, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                self.assertEqual(1, source.count(before))
                self.assertNotEqual(before, after)
                self.assertIn('"' + case + '"', harness)
                self.assertIn('CHECK("' + marker + '"', harness)


class ModelSemanticsAuthority(unittest.TestCase):
    @staticmethod
    def remap(text, original, replacements):
        def include(match):
            path = (original.parent / match.group(1)).resolve()
            return '#include "' + str(replacements.get(path, path)).replace('\\', '/') + '"'
        return re.sub(r'^#include "([^"]+)"', include, text, flags=re.MULTILINE)

    @classmethod
    def harness(cls, name, replacement=None):
        build = kernel_tests.native()
        originals = [ROOT / 'geometry-core/model_base.c', SOURCE, HARNESS]
        # Exact current_geometry bytes are read for the audit, never rewritten
        # or text-scanned: its established CRLF is part of this source snapshot.
        audited = [*originals, ROOT / 'current_geometry.c',
                   ROOT / 'geometry-templates/woodworking/native/section_profile_sources.c',
                   ROOT / 'geometry-templates/woodworking/native/section_profile_sources.h']
        saved = {path: path.read_bytes() for path in audited}
        texts = {path: saved[path].replace(b'\r\n', b'\n').decode('utf-8') for path in originals}
        main = 'int main(int argc, char **argv)'
        if texts[originals[0]].count(main) != 1:
            raise AssertionError('Actual adapter command main must be renamed exactly once')
        texts[originals[0]] = texts[originals[0]].replace(main, 'int semantics_model_command_main(int argc, char **argv)')
        source = texts[SOURCE]
        if replacement:
            before, after = replacement
            if source.count(before) != 1:
                raise AssertionError('Negative control must hit exactly one production anchor')
            source = source.replace(before, after)
        hooks = (
            ('} ModelSources;', '} ModelSources;\nstatic bool semantics_install(ReferenceEval *);\nstatic bool semantics_before_aliases(ModelSources *);'),
            (INSTALL_HOOK, INSTALL_HOOK + '\n    if(!semantics_install(&state->reference))return false;'),
            (ALIAS_HOOK, 'if(!semantics_before_aliases(state))return false;\n    ' + ALIAS_HOOK),
        )
        for before, after in hooks:
            if source.count(before) != 1:
                raise AssertionError('Actual adapter observation hook must hit exactly once')
            source = source.replace(before, after)
        texts[SOURCE] = source
        paths = {path.resolve(): build.work / ('model-semantics-' + name + '-' + path.name) for path in originals}
        try:
            for path in originals:
                paths[path.resolve()].write_text(cls.remap(texts[path], path, paths), encoding='utf-8')
            client = build.compile(paths[HARNESS.resolve()], 'model-semantics-' + name, FLAGS)
            return build.link('model-semantics-' + name, [client, *build.product_objects()])
        finally:
            for path, data in saved.items():
                if path.read_bytes() != data:
                    raise AssertionError('Authority fixture or control edited production source: ' + str(path))

    @classmethod
    def setUpClass(cls):
        cls.exe = cls.harness('baseline')

    def case(self, name, exe=None, marker=None):
        run = subprocess.run([str(exe or self.exe), name], capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(1 if marker else 0, run.returncode, 'Crash/setup is not an authority verdict: ' + run.stdout + run.stderr)
        self.assertEqual('ASSERT:' + marker + '\n' if marker else '', run.stderr)
        self.assertEqual('', run.stdout)

    def test_count_to_actual_fractional_ratio_preserves_authored_count(self):
        self.case('parameter-ratio')

    def test_ratio_to_actual_integer_count_preserves_authored_ratio(self):
        self.case('parameter-count')

    def test_bad_actual_parameter_definition_fails_h_atomically_after_k_succeeds(self):
        self.case('parameter-bad')

    def test_actual_placed_run_controls_world_frame_and_domain(self):
        self.case('to-placed')

    def test_actual_unplaced_run_keeps_identity_frame_and_world_frame_new(self):
        self.case('to-local')
        self.case('baseline')

    def test_actual_run_profile_controls_roots_outline_and_local_owner(self):
        self.case('run-map')

    def test_actual_member_profile_controls_root_membership_and_owner_both_ways(self):
        self.case('member-map')
        self.case('member-back')

    def test_bad_actual_sp_definitions_reject_and_leave_copy_outputs_atomic(self):
        self.case('sp-bad')

    def test_real_definition_edges_and_definition_copies_survive_sealing(self):
        self.case('graph')

    def test_isolated_controls_fail_only_the_declared_semantic_assertion(self):
        for name, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                self.case(case)
                self.case(case, self.harness(name, (before, after)), marker)
                self.case(case)


if __name__ == '__main__':
    unittest.main(verbosity=2)
