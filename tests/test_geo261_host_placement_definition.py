"""H engineering host admission reads K definitions before any geometry work."""
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
FLAGS = ['GEOMETRY_KERNEL_EXTERNAL=1', 'GEOMETRY_WOODWORKING_EXTERNAL=1',
         'GEOMETRY_HOST_HISTORY_EXTERNAL=1', 'GEOMETRY_HOST_CANDIDATE_EXTERNAL=1']
CONTROLS = (
    ('domain', 'if(derived)*derived=definition.domain==GEO_PLACEMENT_REGION_SET;',
     'if(derived)*derived=direct_derived;', 'actual', 'host-placement-actual-definition-controls-derived'),
    ('derived-geometry', 'if(ctx->use_current_values||kind==GEO_PLACEMENT_SOURCE_DEFINITION)return false;',
     'if(ctx->use_current_values)return false;', 'derived', 'host-placement-definition-avoids-derived-geometry'),
)


class HostPlacementDefinitionBoundary(unittest.TestCase):
    def test_host_callback_consumes_actual_definition_and_keeps_legacy_gates(self):
        text = SOURCE.read_text(encoding='utf-8')
        start = text.index('static bool reference_eng_placement(')
        end = text.index('static bool reference_grid_definition(', start)
        callback = text[start:end]
        self.assertIn('geo_placement_sources_definition(ctx->placement_sources,id,&definition)', callback)
        self.assertLess(callback.index('app_eng_placement'), callback.index('geo_placement_sources_definition'))
        self.assertLess(callback.index('ctx->use_current_values'), callback.index('geo_placement_sources_definition'))
        self.assertNotIn('reference_placement_frame', callback)

    def test_controls_have_unique_anchors_and_exact_oracles(self):
        text = SOURCE.read_text(encoding='utf-8')
        harness = (ROOT / 'tests/geo261_host_placement_definition_harness.c').read_text(encoding='utf-8')
        for name, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                self.assertEqual(1, text.count(before))
                self.assertNotEqual(before, after)
                self.assertIn('"' + marker + '"', harness)


class HostPlacementDefinition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        cls.client = build.compile(ROOT / 'tests/geo261_host_placement_definition_harness.c', 'host-placement-definition', FLAGS)
        cls.exe = build.link('host-placement-definition', [cls.client, *build.product_objects()])

    def case(self, name, exe=None, marker=None):
        run = subprocess.run([str(exe or self.exe), name], capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(1 if marker else 0, run.returncode, 'Crash/setup is not an authority verdict: ' + run.stdout + run.stderr)
        self.assertEqual('ASSERT:' + marker + '\n' if marker else '', run.stderr)
        self.assertEqual('', run.stdout)

    def test_actual_definition_controls_both_domain_directions_and_dependency(self): self.case('actual')
    def test_missing_and_snapshot_gates_remain_direct(self): self.case('gates')
    def test_malformed_definition_keeps_output_and_authored_world_unchanged(self): self.case('malformed')
    def test_derived_host_definition_does_not_evaluate_derived_geometry(self): self.case('derived')

    def test_two_isolated_controls_fail_precise_h_authority_oracles(self):
        build = native()
        originals = [ROOT / 'current_geometry.c', ROOT / 'geometry-core/references.inc', SOURCE,
                     ROOT / 'tests/geo261_host_placement_definition_harness.c']
        saved = {p: p.read_bytes() for p in originals}
        for name, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                texts = {p: data.replace(b'\r\n', b'\n').decode('utf-8') for p, data in saved.items()}
                self.assertEqual(1, texts[SOURCE].count(before))
                texts[SOURCE] = texts[SOURCE].replace(before, after)
                paths = {p.resolve(): build.work / ('host-placement-' + name + '-' + p.name) for p in originals}
                for p in originals:
                    def include(match):
                        path = (p.parent / match.group(1)).resolve()
                        return '#include "' + str(paths.get(path, path)).replace('\\', '/') + '"'
                    paths[p.resolve()].write_text(re.sub(r'^#include "([^"]+)"', include, texts[p], flags=re.MULTILINE), encoding='utf-8')
                client = build.compile(paths[originals[-1].resolve()], 'host-placement-control-' + name, FLAGS)
                exe = build.link('host-placement-control-' + name, [client, *build.product_objects()])
                self.case(case)
                self.case(case, exe, marker)
                self.case(case)
                for p, data in saved.items():
                    self.assertEqual(data, p.read_bytes())


if __name__ == '__main__':
    unittest.main(verbosity=2)
