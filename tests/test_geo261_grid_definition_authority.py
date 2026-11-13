"""Actual grid definition/value returns control W computation and policy.

Boundary checks are portable. Compilation/execution belongs to the P1 lane.
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

WOOD = ROOT / 'geometry-templates/woodworking/native'
HARNESS = ROOT / 'tests/geo261_grid_definition_authority_harness.c'
LINE_CASES = ('system-definition', 'binding-definition', 'system-value',
              'binding-value', 'application-value', 'parameter-value')
CONTROLS = tuple((case, 'grid-authority-line-return') for case in LINE_CASES) + (
    ('application-definition', 'grid-authority-application-definition-return'),
    ('rule-definition', 'grid-authority-rule-definition-return'),
    ('world-policy', 'grid-authority-world-policy-definition'),
    ('rule-policy', 'grid-authority-rule-policy-definition'),
    ('panel-value', 'grid-authority-preserves-unbound-returned-quantities'),
    ('gap-value', 'grid-authority-preserves-unbound-returned-quantities'),
)


class GridDefinitionAuthorityBoundary(unittest.TestCase):
    def test_shadow_definitions_and_policy_hooks_are_owned_by_the_provider(self):
        source = (WOOD / 'grid_sources.c').read_text(encoding='utf-8')
        for text in ('s->context.state=&s->evaluated', 's->context.sources=s->evaluated_sources',
                     'wood_grid_decode_system(', 'wood_grid_decode_application(',
                     'wood_grid_decode_binding(', 'wood_grid_decode_rule(',
                     'wood_grid_decode_system_value(', 'wood_grid_decode_application_value(',
                     'wood_grid_world_valid_direct(&evaluated', 'wood_grid_rules_world_valid_direct(&evaluated'):
            self.assertIn(text, source)
        self.assertNotIn('checked!=value.as.quantity.num', source)
        create = source[source.index('WoodGridSources *wood_grid_sources_create'):source.index('bool wood_grid_sources_bind')]
        self.assertNotIn('geo_eval_source(', create)
        self.assertIn('geo_grid_store_clone(', create)

    def test_controls_only_interpose_the_return_value_and_target_named_oracles(self):
        text = HARNESS.read_text(encoding='utf-8')
        self.assertIn('GeoSourceStatus status=geo_eval_source(graph,ref,relation,out)', text)
        self.assertIn('out->as.definition.content=bytes', text)
        self.assertIn('GEO261_GRID_AUTHORITY_CONTROL', text)
        self.assertEqual(12, len(CONTROLS))
        self.assertEqual(12, len({case for case, _ in CONTROLS}))
        for case, marker in CONTROLS:
            self.assertIn('"' + case + '"', text)
            self.assertEqual(1, text.count('"' + marker + '"'))
        self.assertNotRegex(text, r'\b(?:World|ReferenceEval)\b|internal/|current_geometry')


class GridDefinitionAuthority(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = native()
        build = cls.build
        for name in ('geo261_grid_sources_harness.c', 'geo261_grid_definition_authority_harness.c'):
            shutil.copy2(ROOT / 'tests' / name, build.woodworking / name)
        cls.source = build.woodworking / 'geo261_grid_definition_authority_harness.c'
        cls.provider = build.compile(build.woodworking / 'grid_sources.c', 'grid-authority-provider',
                                     ['geo_eval_source=geo261_grid_authority_source'])
        cls.client = build.compile(cls.source, 'grid-authority-client')
        cls.exe = build.link('grid-authority-client', cls.objects(cls.client))

    @classmethod
    def objects(cls, client):
        b = cls.build
        return [client, cls.provider, b.wood_grid_application_object, b.wood_grid_cells_object,
                b.wood_grid_rules_object, b.wood_grid_definition_codec_object,
                b.wood_engineering_object, b.wood_engineering_sources_object, *b.kernel_objects()]

    def case(self, name, executable=None):
        return subprocess.run([str(executable or self.exe), name], capture_output=True, text=True, timeout=30)

    def assert_case(self, name):
        result = self.case(name)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_system_binding_application_and_parameter_returns_feed_real_lines(self):
        for name in LINE_CASES:
            with self.subTest(case=name):
                self.assert_case(name)

    def test_direct_application_definition_preserves_authoring_and_updates_only_bound_cache(self):
        self.assert_case('application-definition')

    def test_rule_definition_controls_the_actual_subdivision_coordinate(self):
        self.assert_case('rule-definition')

    def test_world_validation_reads_the_application_definition(self):
        self.assert_case('world-policy')

    def test_rule_conflict_policy_reads_definitions_without_evaluating_geometry(self):
        self.assert_case('rule-policy')

    def test_noncanonical_return_is_rejected_without_changing_output_or_raw_candidate(self):
        self.assert_case('invalid-definition')

    def test_multiple_bound_dimensions_survive_nested_resolution_and_sealed_memoization(self):
        self.assert_case('multiple-and-memo')

    def test_unbound_panel_and_gap_quantities_survive_later_dimension_reads(self):
        self.assert_case('panel-value')
        self.assert_case('gap-value')

    def test_memoized_rule_policy_survives_system_reinstallation_and_rejects_a_new_line_index(self):
        self.assert_case('rule-stability')

    def test_borrowed_rule_pointer_control_fails_after_system_reinstallation(self):
        build = self.build
        path = build.woodworking / 'grid_sources.c'
        snapshot = path.read_bytes()
        source = snapshot.decode('utf-8')
        before = 'r->target.rule=&r->target_rule;'
        self.assertEqual(1, source.count(before))
        self.assert_case('rule-stability')
        changed = build.woodworking / 'grid-authority-borrowed-rule-control.c'
        changed.write_text(source.replace(before, ''), encoding='utf-8')
        obj = build.compile(changed, 'grid-authority-borrowed-rule-control', ['geo_eval_source=geo261_grid_authority_source'])
        exe = build.link('grid-authority-borrowed-rule-control', [obj if item == self.provider else item for item in self.objects(self.client)])
        result = self.case('rule-stability', exe)
        self.assertEqual(1, result.returncode, 'Crash/setup is not a verdict: ' + result.stdout + result.stderr)
        self.assertRegex(result.stderr, r'^ASSERT:grid-authority-memoized-rule-keeps-returned-policy:\d+\n$')
        self.assertEqual(snapshot, path.read_bytes())
        self.assert_case('rule-stability')

    def test_twelve_return_substitutions_fail_exact_named_assertions_between_passing_baselines(self):
        build = self.build
        snapshot = (build.woodworking / 'grid_sources.c').read_bytes()
        client = build.compile(self.source, 'grid-authority-control', ['GEO261_GRID_AUTHORITY_CONTROL=1'])
        executable = build.link('grid-authority-control', self.objects(client))
        for name, marker in CONTROLS:
            with self.subTest(control=name):
                self.assert_case(name)
                result = self.case(name, executable)
                self.assertEqual(1, result.returncode, 'Crash/setup is not a verdict: ' + result.stdout + result.stderr)
                self.assertRegex(result.stderr, r'^ASSERT:' + re.escape(marker) + r':\d+\n$')
                self.assertEqual(snapshot, (build.woodworking / 'grid_sources.c').read_bytes())
                self.assert_case(name)


if __name__ == '__main__':
    unittest.main(verbosity=2)
