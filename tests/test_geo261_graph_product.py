"""Actual product geometry consumes the shared candidate source graph."""
import base64
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native
from tests import test_geo261_model_sources as model_sources
from tests.test_geo261_wood_product import SCENE


class GraphProduct(unittest.TestCase):
    execute = model_sources.ModelSources.execute
    ref = staticmethod(model_sources.ModelSources.ref)
    nodes = model_sources.ModelSources.nodes

    def edges(self, envelope):
        return {(self.ref(edge['consumer']), self.ref(edge['source']), edge['kind'])
                for edge in envelope['neutralSources']['edges']}

    def test_placement_roots_consume_owned_region_values(self):
        scene = ('boundary 7 outline 10,20 410,20 410,320 10,320 hole 100,100 150,100 150,150 100,150\n'
                 'placement 9 on boundary 7 origin 3 4 5 u +x v +y\n')
        envelope = self.execute(scene)
        nodes = self.nodes(envelope)
        placement = ('core.placement', bytes([2]) + (9).to_bytes(4, 'big'))
        region = ('core.region', (7).to_bytes(4, 'big'))
        self.assertIn((placement, region, 'value-required'), self.edges(envelope))
        self.assertEqual([[10, 20], [410, 20], [410, 320], [10, 320]],
                         nodes[placement]['value']['components'][0]['outer'])
        self.assertEqual(nodes[placement]['value'], nodes[region]['value'])
        root = next(root for root in envelope['neutralSources']['roots']
                    if root['slot'] == 'placement.region')
        self.assertIn((self.ref(root['ref']), placement, 'value-required'), self.edges(envelope))

    def test_ordered_features_drive_actual_member_placement(self):
        envelope = self.execute(SCENE)
        nodes = self.nodes(envelope)
        features = {ref: node for ref, node in nodes.items()
                    if ref[0] == 'wood.contact' and node['descriptor']['valueType'] == 'feature'}
        self.assertTrue(features)
        self.assertEqual({((0, 0, 0), (0, 1000, 0)), ((1000, 0, 0), (1000, 1000, 0))},
                         {tuple(tuple(point) for point in node['value']['segment'])
                          for node in features.values()})
        edges = self.edges(envelope)
        self.assertTrue(any(a[0] == 'woodworking.member.pose' and b in features
                            for a, b, relation in edges if relation == 'value-required'))
        for ref, node in features.items():
            self.assertEqual({'placementId': 1, 'axis': None, 'owner': None},
                             node['descriptor']['context'])
            self.assertEqual(24, len(base64.b64decode(node['value']['keyBase64'], validate=True)))
            self.assertTrue(any(a == ref and b[0] == 'wood.contact' and b[1][0] == 1
                                for a, b, relation in edges if relation == 'value-required'))
        self.assertTrue(any(a[0] == 'wood.contact' and a[1][0] == 1 and b[0] == 'core.placement'
                            for a, b, relation in edges if relation == 'value-required'))

    def test_grid_rule_values_feed_member_geometry_and_owned_binding_sources(self):
        fixture = ROOT / 'tests/release-evidence/20261008-cloud-closeout/contracts/grid-final/grid-rule-timber.scene'
        envelope = self.execute(fixture.read_text(encoding='utf-8'))
        nodes = self.nodes(envelope)
        grid_nodes = {ref: node for ref, node in nodes.items() if ref[0] == 'wood.grid'}
        self.assertTrue(grid_nodes)
        kinds = {ref[1][0] for ref in grid_nodes}
        self.assertTrue({1, 2, 3, 4, 5, 6, 11, 12}.issubset(kinds), kinds)
        rule_lines = [(ref, node) for ref, node in grid_nodes.items() if ref[1][0] == 11]
        self.assertTrue(rule_lines)
        edges = self.edges(envelope)
        for ref, node in rule_lines:
            self.assertEqual('axis-position', node['descriptor']['valueType'])
            self.assertEqual(500, node['value']['coordinate'])
            self.assertTrue(any(a == ref and b[0] == 'wood.grid' and b[1][0] == 12
                                for a, b, relation in edges if relation == 'value-required'))
        # The binding consumes the region through its typed vertex-key coordinates
        # (72d6835c); each coordinate consumes the owned core.region value.
        binding = ('wood.grid', bytes([4]) + struct.pack('>I', 0) + bytes(59))
        region = ('core.region', struct.pack('>I', 1))
        for axis, value in enumerate((100, 200)):
            coordinate = ('core.region-key', struct.pack('>4I', 2, 1, 1, axis))
            self.assertEqual(str(value), nodes[coordinate]['value']['num'])
            self.assertIn((binding, coordinate, 'value-required'), edges)
            self.assertIn((coordinate, region, 'value-required'), edges)
        self.assertTrue(any(a[0] == 'woodworking.member.pose' and b[0] == 'wood.grid'
                            for a, b, relation in edges if relation == 'value-required'))

    def test_profile_local_regions_keep_definition_identity(self):
        envelope = self.execute(model_sources.profile_scene())
        nodes = self.nodes(envelope)
        local = [node for ref, node in nodes.items()
                 if ref[0] == 'wood.section-profile' and node['descriptor']['valueType'] == 'region-set']
        self.assertTrue(local)
        for node in local:
            owner = node['descriptor']['context']['owner']
            self.assertEqual('wood.section-profile', owner['namespace'])
            self.assertEqual(bytes([1]) + (1).to_bytes(4, 'big'),
                             base64.b64decode(owner['keyBase64'], validate=True))
        self.assertTrue(any(a[0] == 'wood.section-profile' and b[0] == 'wood.section-profile'
                            and relation == 'definition-required' for a, b, relation in self.edges(envelope)))

    def test_feature_coordinate_mutation_is_rejected_by_the_real_bridge(self):
        build = native()
        scene = build.work / 'contact-source-product.scene'
        scene.write_text(SCENE, encoding='utf-8')

        def load(exe):
            with _bridge.BridgeSession(exe) as session:
                self.assertTrue(session.command('reset')['ok'])
                return session.command('loadfile ' + str(scene))

        self.assertTrue(load(build.bridge())['ok'])
        source = (build.woodworking / 'contact_sources.c').read_text(encoding='utf-8')
        before = 'out->kind=GEO_SOURCE_FEATURE;out->as.feature=(GeoFeatureValue){record,WOOD_CONTACT_SOURCE_METADATA_SIZE,segment};return true;'
        self.assertEqual(1, source.count(before))
        path = build.woodworking / 'contact-source-product-mutant.c'
        path.write_text(source.replace(before, '++segment.start.x;++segment.end.x;' + before), encoding='utf-8')
        changed = build.compile(path, 'contact-source-product-mutant')
        product = build.link('contact-source-product-mutant', [build.bridge_object,
            *[changed if obj == build.wood_contact_sources_object else obj for obj in build.product_objects()]])
        rejected = load(product)
        self.assertFalse(rejected['ok'], rejected)
        self.assertTrue(load(build.bridge())['ok'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
