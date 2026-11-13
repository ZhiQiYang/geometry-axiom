"""Actual H datum/guide/member consumers use returned definitions and values.

Only LinearDefinitionProductBoundary is portable. Native work belongs to P1.
"""
from pathlib import Path
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import native
from tests import test_geo261_model_sources as sources

SCENE = ('spec h 3\ndatum 1 x spec:h\n'
         'surface 1 origin 0 0 0 u +x v +y rect 0 0 100 100\n'
         'guide 1 1 datum 1\nguide 2 1 v guide:1\n')
DEFINITION_RETURN = ('return geo_eval_source(s->graph,geo_linear_definition_source_ref(s->token,kind,id,&key),'
                     'GEO_DEPENDENCY_DEFINITION_REQUIRED,out)==GEO_SOURCE_OK;')


class LinearDefinitionProductBoundary(unittest.TestCase):
    def test_h_composition_binds_and_completes_definition_providers(self):
        source = (ROOT / 'geometry-app/native/reference_sources.inc').read_text(encoding='utf-8')
        complete = (ROOT / 'geometry-app/native/model_sources.inc').read_text(encoding='utf-8')
        self.assertIn('geo_linear_definition_sources_register(', source)
        self.assertIn('geo_parameter_sources_register_with_definitions(', source)
        self.assertIn('geo_linear_definition_sources_complete(', complete)
        self.assertIn('geo_parameter_sources_definitions(', complete)
        self.assertIn('wood_sp_sources_complete(', complete)
        provider = (ROOT / 'geometry-core/kernel/linear_definition_sources.c').read_text(encoding='utf-8')
        self.assertEqual(1, provider.count(DEFINITION_RETURN))


class LinearDefinitionGraphProduct(unittest.TestCase):
    execute = sources.ModelSources.execute
    ref = staticmethod(sources.ModelSources.ref)
    nodes = sources.ModelSources.nodes

    @classmethod
    def setUpClass(cls):
        build = native()
        cls.scene = build.work / 'linear-definition-h.scene'
        cls.scene.write_text(SCENE, encoding='utf-8')
        cls.build = build
        cls.defines = ['GEOMETRY_KERNEL_EXTERNAL=1', 'GEOMETRY_WOODWORKING_EXTERNAL=1',
                       'GEOMETRY_HOST_HISTORY_EXTERNAL=1', 'GEOMETRY_HOST_CANDIDATE_EXTERNAL=1']
        cls.client = build.compile(ROOT / 'tests/geo261_linear_definition_product_harness.c',
                                   'linear-definition-h-client', cls.defines)
        cls.exe = build.link('linear-definition-h-client', [cls.client, *build.product_objects()])

    def case(self, name, executable=None):
        return subprocess.run([str(executable or self.exe), str(self.scene), name],
                              capture_output=True, text=True, timeout=30)

    def assert_case(self, name):
        result = self.case(name)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_datum_guide_and_guide_reference_publish_real_definition_edges(self):
        envelope = self.execute(SCENE)
        nodes = self.nodes(envelope)
        edges = {(self.ref(edge['consumer']), self.ref(edge['source']), edge['kind'])
                 for edge in envelope['neutralSources']['edges']}
        datum = ('core.datum.position', struct.pack('=I', 1))
        guide = ('app.guide', struct.pack('=I', 1))
        datum_definition = ('core.linear-definition', bytes([1]) + struct.pack('>I', 1))
        guide_definition = ('core.linear-definition', bytes([2]) + struct.pack('>I', 1))
        self.assertIn((datum, datum_definition, 'definition-required'), edges)
        self.assertIn((guide, guide_definition, 'definition-required'), edges)
        self.assertIn((guide, datum, 'value-required'), edges)
        self.assertEqual(3, nodes[datum]['value']['coordinate'])
        self.assertEqual(3, nodes[guide]['value']['coordinate'])
        self.assertTrue(any(a[0] == 'app.legacy-reference' and b == guide and kind == 'value-required'
                            for a, b, kind in edges))
        self.assertTrue(nodes[datum_definition]['value']['contentBase64'])
        self.assertTrue(nodes[guide_definition]['value']['contentBase64'])

    def test_datum_return_overrides_a_deliberately_stale_position_cache(self):
        self.assert_case('datum')

    def test_guide_reference_overrides_a_deliberately_stale_offset_cache(self):
        self.assert_case('guide')

    def test_member_guide_fact_consumes_the_evaluated_returned_position(self):
        self.assert_case('member')

    def test_snapshot_keeps_its_caches_and_ignores_an_ambient_candidate(self):
        self.assert_case('snapshot')

    def test_value_and_axis_substitution_controls_hit_exact_h_assertions(self):
        build = self.build
        client = build.compile(ROOT / 'tests/geo261_linear_definition_product_harness.c',
                               'linear-definition-h-control', self.defines + ['GEO261_LINEAR_RETURN_CONTROL=1'])
        changed = build.link('linear-definition-h-control', [client, *build.product_objects()])
        for name, label in (('datum', 'datum'), ('guide', 'guide'), ('member', 'member'), ('guide-axis', 'guide')):
            with self.subTest(control=name):
                self.assert_case(name)
                result = self.case(name, changed)
                self.assertEqual(1, result.returncode, 'Crash/setup is not a verdict: ' + result.stdout + result.stderr)
                self.assertEqual('ASSERT:linear-product-' + label + '-return-is-authoritative\n', result.stderr)
                self.assert_case(name)

    def test_actual_returned_definition_controls_reach_datum_and_local_guide_evaluation(self):
        build = self.build
        original = build.kernel / 'linear_definition_sources.c'
        snapshot = original.read_bytes()
        source = snapshot.decode('utf-8')
        self.assertEqual(1, source.count(DEFINITION_RETURN))
        changed_return = (
            'GeoSourceStatus status=geo_eval_source(s->graph,geo_linear_definition_source_ref(s->token,kind,id,&key),'
            'GEO_DEPENDENCY_DEFINITION_REQUIRED,out);'
            'extern void geo261_linear_definition_product_control(GeoLinearDefinitionKind,uint32_t,GeoSourceValue *);'
            'if(status==GEO_SOURCE_OK)geo261_linear_definition_product_control(kind,id,out);return status==GEO_SOURCE_OK;')
        path = build.kernel / 'linear-definition-h-definition-control.c'
        path.write_text(source.replace(DEFINITION_RETURN, changed_return), encoding='utf-8')
        obj = build.compile(path, 'linear-definition-h-definition-control')
        changed = build.link('linear-definition-h-definition-control', [self.client,
            *[obj if item == build.linear_definition_sources_object else item for item in build.product_objects()]])
        for name in ('datum-definition', 'guide-definition'):
            with self.subTest(control=name):
                self.assert_case(name)
                result = self.case(name, changed)
                self.assertEqual(1, result.returncode, 'Crash/setup is not a verdict: ' + result.stdout + result.stderr)
                self.assertEqual('ASSERT:linear-product-' + name + '-is-authoritative\n', result.stderr)
                self.assertEqual(snapshot, original.read_bytes())
                self.assert_case(name)


if __name__ == '__main__':
    unittest.main(verbosity=2)
