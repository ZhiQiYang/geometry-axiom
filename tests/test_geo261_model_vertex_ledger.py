"""Placement transport consumes actual ledger bytes while preserving D30 absence."""
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import native
from tests import test_geo261_model_sources as model_sources

FLAGS = ['GEOMETRY_KERNEL_EXTERNAL=1', 'GEOMETRY_WOODWORKING_EXTERNAL=1',
         'GEOMETRY_HOST_HISTORY_EXTERNAL=1', 'GEOMETRY_HOST_CANDIDATE_EXTERNAL=1']
SOURCE = ROOT / 'geometry-app/native/model_sources.inc'
CONTROLS = (
    ('raw-ledger', '*item->owned_vertex_keys=decoded;',
     '*item->owned_vertex_keys=*geo_region_keys_find(&state->reference.world->geo.region_data,region_id);',
     'actual', 'ledger-actual-return-controls-attached-keys'),
    ('edge-kind', 'GEO_DEPENDENCY_DEFINITION_REQUIRED,&ledger)', 'GEO_DEPENDENCY_VALUE_REQUIRED,&ledger)',
     'actual', 'ledger-root-has-definition-edge'),
    ('schema', 'strcmp(ledger.as.definition.schema,"geometry.region-key-ledger/1")', 'false',
     'malformed', 'ledger-malformed-return-rejects-root'),
    ('shape', '!geo_region_keys_valid(&shape,&decoded)', 'false',
     'malformed', 'ledger-malformed-return-rejects-root'),
    ('placement-definition', 'if(!geo_placement_sources_definition(state->reference.placement_sources,item->id,&placement))return false;',
     'placement=*geo_placements_find(&state->reference.world->geo.placement_data,item->id);',
     'selection', 'ledger-selection-actual-definition-controls-attachment'),
)
SCENE = ('boundary 7 outline 0,0 1000,0 1000,1000 0,1000 hole 100,100 200,100 200,200 100,200\n'
         'placement 9 on boundary 7 origin 0 0 30 u +x v +y\n'
         'placement 10 on boundary 7 origin 0 0 40 u +x v +y\n'
         'boundary-vertex-keys 7 outer 1 2 3 4 hole 5 6 7 8 next-key 9\n')
# D4: a region-set range belongs only to the derived (panel-fill/1) placement,
# derived by R41. This is the product bridge's own dump of that fixture
# (test_panel_fill_host second-component case) with boundary 7, placement 9
# and boundary 7's key ledger; beam 20 splits the range into two components.
COMPONENTS_SCENE = (
    'requires parameters/1\nparameters begin\n'
    'parameters card eyJpZCI6OTAsIm5hbWUiOiLploDmqrsiLCJuZXh0RmllbGRJZCI6Mn0=\n'
    'parameters field eyJwYXJhbWV0ZXJJZCI6OTAsImlkIjoxLCJuYW1lIjoiWCIsInR5cGUiOjAsImV4cHJlc3Npb24iOnsiZGVuIjoiMSIsIm51bSI6IjgiLCJvcCI6ImxpdGVyYWwiLCJ1bml0IjoibW0ifX0=\n'
    'parameters end\nrequires engineering-spec/1\n'
    'engineering material eyJmaW5nZXJwcmludCI6ImQ4YjY3OGMxNzM2ZmNhYTBiNTQxOGY0NDdkMThlYzI4Yjg3ZDRhNjQ1MTFhNmRiNDgwYTVlYjdhMmU5MDVhYTciLCJ2YWx1ZSI6eyJpZCI6InBmLWJvYXJkIiwia2luZCI6InBhbmVsIiwibGVuZ3RoIjoxODMwLCJuYW1lIjoi5p2/IiwidGhpY2tuZXNzIjoiOSIsInZlcnNpb24iOjEsIndpZHRoIjo5MTV9fQ==\n'
    'boundary 7 outline 0,0 100,0 100,100 0,100 kind room_plan\n'
    'beam 20 along x from 40 to 60 at 50 width 120 depth 30 top 39\n'
    'boundary-vertex-keys 7 outer 1 2 3 4 next-key 5\n'
    'requires panel-fill/1\n'
    'finish-surface 1 on boundary 7 origin 0 0 0 u +x v +y n +z side +n obstacles b20 name-hex e5a4a9e88ab1e5ae8ce68890e99da2\n'
    'panel-fill 1 definition-hex ' + json.dumps({'finishSurfaceId': 1, 'gap': 0, 'id': 1, 'lengthAlong': 'v', 'origin': [0, 0],
        'panel': {'id': 'pf-board', 'version': 1}, 'pattern': 'straight', 'threshold': {'fieldId': 1, 'parameterId': 90}},
        sort_keys=True, separators=(',', ':')).encode().hex() + '\n'
    'derived-placement 9 definition-hex ' + json.dumps({'fillId': 1, 'h': 30, 'id': 9},
        sort_keys=True, separators=(',', ':')).encode().hex() + '\n')


class ModelVertexLedgerBoundary(unittest.TestCase):
    def test_root_reads_actual_ledger_and_owns_its_decoded_storage(self):
        text = SOURCE.read_text(encoding='utf-8')
        self.assertIn('GEO_REGION_KEY_SOURCE_LEDGER,region_id', text)
        self.assertIn('geo_region_key_ledger_decode(ledger.as.definition.content,ledger.as.definition.content_size,&decoded)', text)
        self.assertIn('free(state->items[i]->owned_vertex_keys)', text)
        self.assertNotIn('world_find_vertex_keys', text)
        self.assertIn('placement.domain!=GEO_PLACEMENT_REGION_REF||!geo_region_keys_find', text)
        self.assertNotIn('geo_placement_domain_view(', text)

    def test_controls_are_unique_and_hit_declared_behavioral_oracles(self):
        text = SOURCE.read_text(encoding='utf-8')
        harness = (ROOT / 'tests/geo261_model_vertex_ledger_harness.c').read_text(encoding='utf-8')
        for name, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                self.assertEqual(1, text.count(before))
                self.assertNotEqual(before, after)
                self.assertIn('"' + marker + '"', harness)


class ModelVertexLedger(unittest.TestCase):
    execute = model_sources.ModelSources.execute
    ref = staticmethod(model_sources.ModelSources.ref)
    nodes = model_sources.ModelSources.nodes

    @staticmethod
    def remap(text, original, replacements):
        def include(match):
            path = (original.parent / match.group(1)).resolve()
            return '#include "' + str(replacements.get(path, path)).replace('\\', '/') + '"'
        return re.sub(r'^#include "([^"]+)"', include, text, flags=re.MULTILINE)

    @classmethod
    def harness(cls, name, replacement=None):
        build = native()
        originals = [ROOT / 'geometry-core/model_base.c', SOURCE, ROOT / 'tests/geo261_model_vertex_ledger_harness.c']
        saved = {p: p.read_bytes() for p in originals}
        texts = {p: b.replace(b'\r\n', b'\n').decode('utf-8') for p, b in saved.items()}
        main = 'int main(int argc, char **argv)'
        if texts[originals[0]].count(main) != 1:
            raise AssertionError('Actual model adapter main must be renamed exactly once')
        texts[originals[0]] = texts[originals[0]].replace(main, 'int ledger_model_command_main(int argc, char **argv)')
        if replacement:
            before, after = replacement
            if texts[SOURCE].count(before) != 1:
                raise AssertionError('Control must hit exactly once')
            texts[SOURCE] = texts[SOURCE].replace(before, after)
        paths = {p.resolve(): build.work / ('vertex-ledger-' + name + '-' + p.name) for p in originals}
        for p in originals:
            paths[p.resolve()].write_text(cls.remap(texts[p], p, paths), encoding='utf-8')
        client = build.compile(paths[originals[-1].resolve()], 'vertex-ledger-' + name, FLAGS)
        exe = build.link('vertex-ledger-' + name, [client, *build.product_objects()])
        for p, data in saved.items():
            if p.read_bytes() != data:
                raise AssertionError('Control edited production source')
        return exe

    @classmethod
    def setUpClass(cls):
        cls.exe = cls.harness('baseline')
        cls.components_scene = native().work / 'vertex-ledger-components.scene'
        cls.components_scene.write_text(COMPONENTS_SCENE, encoding='utf-8')

    def case(self, name, exe=None, marker=None):
        scene = [str(self.components_scene)] if name == 'components' else []
        run = subprocess.run([str(exe or self.exe), name, *scene], capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(1 if marker else 0, run.returncode, 'Crash/setup is not an authority verdict: ' + run.stdout + run.stderr)
        self.assertEqual('ASSERT:' + marker + '\n' if marker else '', run.stderr)
        self.assertEqual('', run.stdout)

    def test_actual_ledger_controls_roots_and_shared_ledger_edges(self):
        self.case('actual')
        self.case('shared')
        self.case('selection')

    def test_absent_rectangle_and_region_set_ledgers_remain_null(self):
        for case in ('absent', 'rectangle', 'components'):
            self.case(case)

    def test_malformed_returned_ledgers_reject_atomically(self):
        self.case('malformed')

    def test_isolated_controls_fail_exact_actual_value_edge_and_validation_oracles(self):
        for name, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                self.case(case)
                self.case(case, self.harness(name, (before, after)), marker)
                self.case(case)

    def test_actual_k_provider_substitution_changes_serialized_roots_not_legacy_snapshot(self):
        build = native()
        baseline = self.execute(SCENE)
        original = build.kernel / 'region_key_sources.c'
        saved = original.read_bytes()
        text = saved.decode('utf-8')
        anchor = 'out->kind=GEO_SOURCE_DEFINITION;out->as.definition=(GeoDefinitionValue){"geometry.region-key-ledger/1",d->content,d->size};return true;'
        self.assertEqual(1, text.count(anchor))
        path = build.kernel / 'vertex-ledger-provider-control.c'
        path.write_text(text.replace(anchor,
            'unsigned char saved_key[4];memcpy(saved_key,d->content+16,4);memcpy(d->content+16,d->content+20,4);memcpy(d->content+20,saved_key,4);' + anchor), encoding='utf-8')
        changed = build.compile(path, 'vertex-ledger-provider-control')
        build.model_base()
        exe = build.link('vertex-ledger-provider-control', [build.model_base_object,
            *[changed if obj == build.kernel_region_key_sources_object else obj for obj in build.product_objects()]])
        mutated = self.execute(SCENE, exe=exe)
        self.assertEqual(baseline['legacySnapshot'], mutated['legacySnapshot'])
        key_ref = ('core.region-key', struct.pack('>IIII', 1, 7, 0, 0))
        for envelope, expected in ((baseline, [1, 2, 3, 4]), (mutated, [2, 1, 3, 4])):
            nodes = self.nodes(envelope)
            edges = {(self.ref(e['consumer']), self.ref(e['source']), e['kind']) for e in envelope['neutralSources']['edges']}
            roots = [r for r in envelope['neutralSources']['roots'] if r['slot'] == 'placement.region']
            self.assertEqual(2, len(roots))
            for root in roots:
                ref = self.ref(root['ref'])
                self.assertEqual([expected, [5, 6, 7, 8]], nodes[ref]['value']['components'][0]['vertexKeys'])
                self.assertIn((ref, key_ref, 'definition-required'), edges)
        self.assertEqual(saved, original.read_bytes())
        self.assertEqual(baseline['legacySnapshot'], self.execute(SCENE)['legacySnapshot'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
