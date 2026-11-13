"""K-only deferred geometric context, retaining strict default descriptors."""
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import native

CONTROLS = (
    ('axis-only', '(!d->context_from_value||d->kind==GEO_SOURCE_AXIS_POSITION)', 'true', 'kind', 'context-flag-is-axis-only'),
    ('axis-range', 'v->as.position.context.axis>=0&&v->as.position.context.axis<=2', 'true', 'rejection', 'context-rejects-invalid-derived-axis'),
    ('strict-context', 'geo_source_context_equal(d->context,v->as.position.context)', 'true', 'strict', 'context-strict-provider-still-rejects-mismatch'),
    ('publish-context', 'node->descriptor.context=value.as.position.context;', '', 'metadata', 'context-finalizes-exact-returned-context'),
    ('publish-flag', 'node->descriptor.context_from_value=false;', '', 'metadata', 'context-clears-unresolved-flag'),
    ('provider-failure', 'if(!ok)return node->status;', 'if(false)return node->status;', 'failed', 'context-failed-provider-does-not-publish'),
)


class SourceContextBoundary(unittest.TestCase):
    def test_context_is_explicit_opt_in_and_only_finalizes_after_validation(self):
        header = (ROOT / 'geometry-core/kernel/source.h').read_text(encoding='utf-8')
        source = (ROOT / 'geometry-core/kernel/source.c').read_text(encoding='utf-8')
        self.assertIn('bool context_from_value;', header)
        begin = source.index('GeoSourceStatus geo_eval_describe(')
        end = source.index('GeoSourceStatus geo_eval_depend(', begin)
        self.assertNotIn('->evaluate(', source[begin:end])
        self.assertLess(source.index('if(!geo_source_value_matches('), source.index('node->descriptor.context=value.as.position.context;'))
        harness = (ROOT / 'tests/geo261_source_context_harness.c').read_text(encoding='utf-8')
        self.assertNotRegex(harness, r'wood_|World|geometry-app|internal/')

    def test_each_control_matches_one_expression_and_one_exact_assertion(self):
        source = (ROOT / 'geometry-core/kernel/source.c').read_text(encoding='utf-8')
        harness = (ROOT / 'tests/geo261_source_context_harness.c').read_text(encoding='utf-8')
        for name, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                self.assertEqual(1, source.count(before))
                self.assertNotEqual(before, after)
                self.assertEqual(1, harness.count('"' + marker + '"'))
                self.assertIn('"' + case + '"', harness)


class SourceContext(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = native()
        cls.client = cls.build.compile(ROOT / 'tests/geo261_source_context_harness.c', 'source-context-client')
        cls.exe = cls.build.link('source-context-client', [cls.client, cls.build.source_object])

    def case(self, name, executable=None):
        return subprocess.run([str(executable or self.exe), name], capture_output=True, text=True, timeout=20)

    def assert_case(self, name):
        result = self.case(name)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_metadata_stays_lazy_and_finalizes_atomically_with_a_sealed_value(self):
        self.assert_case('metadata')

    def test_invalid_axes_leave_outputs_and_metadata_unchanged_until_valid_retry(self):
        self.assert_case('rejection')

    def test_existing_strict_context_validation_is_unchanged(self):
        self.assert_case('strict')

    def test_opt_in_is_rejected_for_other_kinds_and_never_weakens_typed_kind(self):
        self.assert_case('kind')

    def test_provider_failure_and_context_reset_preserve_the_existing_lifecycle(self):
        self.assert_case('failed')

    def test_six_controls_fail_exact_assertions_between_passing_baselines(self):
        build = self.build
        path = build.kernel / 'source.c'
        snapshot = path.read_bytes()
        source = snapshot.decode('utf-8')
        for name, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                self.assert_case(case)
                self.assertEqual(1, source.count(before))
                changed = build.kernel / ('source-context-control-' + name + '.c')
                changed.write_text(source.replace(before, after), encoding='utf-8')
                obj = build.compile(changed, 'source-context-control-' + name)
                exe = build.link('source-context-control-' + name, [self.client, obj])
                result = self.case(case, exe)
                self.assertEqual(1, result.returncode, 'Crash/setup is not a verdict: ' + result.stdout + result.stderr)
                self.assertEqual('ASSERT:' + marker + '\n', result.stderr)
                self.assertEqual(snapshot, path.read_bytes())
                self.assert_case(case)


if __name__ == '__main__':
    unittest.main(verbosity=2)
