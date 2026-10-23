"""The product uses canonical authored W facts in the same geometry graph."""
import base64
from pathlib import Path
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import native
from tests import test_geo261_model_sources as model_sources
from tests.test_geo261_wood_product import SCENE


class DefinitionGraphProduct(unittest.TestCase):
    execute = model_sources.ModelSources.execute
    ref = staticmethod(model_sources.ModelSources.ref)
    nodes = model_sources.ModelSources.nodes

    @staticmethod
    def source(kind, identifier):
        return 'wood.definition', bytes([kind]) + struct.pack('>I', identifier)

    def edges(self, envelope):
        return {(self.ref(e['consumer']), self.ref(e['source']), e['kind'])
                for e in envelope['neutralSources']['edges']}

    def test_member_pose_uses_authored_anchor_role_and_typed_literal_dimensions(self):
        envelope = self.execute(SCENE)
        nodes, edges = self.nodes(envelope), self.edges(envelope)
        pose = 'woodworking.member.pose', struct.pack('=I', 1)
        for kind in (1, 2):
            self.assertIn((pose, self.source(kind, 1), 'definition-required'), edges)
        for kind, value in ((3, '40'), (4, '50')):
            self.assertIn((pose, self.source(kind, 1), 'value-required'), edges)
            self.assertIn((self.source(kind, 1), self.source(1, 1), 'definition-required'), edges)
            self.assertEqual(value, nodes[self.source(kind, 1)]['value']['num'])
        declaration = base64.b64decode(nodes[self.source(1, 1)]['value']['contentBase64'], validate=True)
        self.assertEqual(struct.pack('>IBIqBqBq', 1, 1, 0, 1, 1, 40, 1, 50), declaration)
        self.assertTrue(all(root['kind'] != 'wood.definition' for root in envelope['neutralSources']['roots']))
        # I9 rejects unplaced members at scene EOF. Check the unused authored
        # identity in an unfinished H candidate, without asserting illegal load.
        build = native()
        client = build.compile(ROOT / 'tests/geo261_definition_product_harness.c', 'definition-unplaced-client',
                               ['GEOMETRY_KERNEL_EXTERNAL=1', 'GEOMETRY_WOODWORKING_EXTERNAL=1',
                                'GEOMETRY_HOST_HISTORY_EXTERNAL=1', 'GEOMETRY_HOST_CANDIDATE_EXTERNAL=1'])
        executable = build.link('definition-unplaced-client', [client, *build.product_objects()])
        result = subprocess.run([str(executable), 'unplaced'], capture_output=True, text=True, timeout=20)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_ordered_contact_features_include_the_actual_boundary_policy(self):
        envelope = self.execute(SCENE)
        nodes, edges = self.nodes(envelope), self.edges(envelope)
        policy = self.source(7, 1)
        self.assertEqual('wood.boundary-policy/1', nodes[policy]['value']['schema'])
        self.assertEqual(struct.pack('>IIII4I', 1, 0, 1, 4, 1, 1, 1, 1),
                         base64.b64decode(nodes[policy]['value']['contentBase64'], validate=True))
        self.assertIn((policy, ('core.region', struct.pack('>I', 1)), 'value-required'), edges)
        self.assertTrue(any(a[0] == 'wood.contact' and b == policy and relation == 'definition-required'
                            for a, b, relation in edges))

    def test_rc_box_keeps_frozen_geometry_and_explicit_room_association(self):
        scene = ('surface 7 origin 0 0 300 u +x v +y outline 0,0 1000,0 1000,800 0,800\n'
                 'space 5 boundary 7\n'
                 'column 29 in 5 at 100 100 size 30 40 z 0 300\n'
                 'beam 31 along x from 100 to 300 at 115 width 30 depth 50 top 300\n')
        envelope = self.execute(scene)
        nodes, edges = self.nodes(envelope), self.edges(envelope)
        column, beam = self.source(5, 29), self.source(6, 31)
        room = 'core.enclosure', bytes([1]) + struct.pack('>I', 5) + bytes([0, 0])
        self.assertEqual(struct.pack('>II6q', 29, 5, 100, 130, 100, 140, 0, 300),
                         base64.b64decode(nodes[column]['value']['contentBase64'], validate=True))
        self.assertEqual(struct.pack('>III6q', 31, 0, 0, 100, 300, 100, 130, 250, 300),
                         base64.b64decode(nodes[beam]['value']['contentBase64'], validate=True))
        self.assertIn((column, room, 'definition-required'), edges)
        self.assertFalse(any(a in (column, beam) and b[0] == 'core.enclosure' and b[1][0] != 1
                             for a, b, _ in edges))
        for ref in (column, beam):
            self.assertTrue(any(a[0] == 'wood.finish' and b == ref and relation == 'definition-required'
                                for a, b, relation in edges))

    def test_source_quantity_mutation_changes_actual_product_pose(self):
        build = native()
        baseline = self.execute(SCENE)
        source = (build.woodworking / 'definition_sources.c').read_text(encoding='utf-8')
        before = '.as.quantity={m.dimension[axis],1,GEO_UNIT_LENGTH}'
        self.assertEqual(1, source.count(before))
        path = build.woodworking / 'definition-product-control.c'
        path.write_text(source.replace(before, '.as.quantity={m.dimension[axis]+1,1,GEO_UNIT_LENGTH}'), encoding='utf-8')
        changed = build.compile(path, 'definition-product-control')
        build.model_base()
        product = build.link('definition-product-control', [build.model_base_object,
            *[changed if obj == build.wood_definition_sources_object else obj for obj in build.product_objects()]])
        mutated = self.execute(SCENE, exe=product)
        old, new = self.nodes(baseline), self.nodes(mutated)
        pose = 'woodworking.member.pose', struct.pack('=I', 1)
        self.assertGreater(new[pose]['value']['hi'][1], old[pose]['value']['hi'][1])
        for axis in (0, 1):
            self.assertEqual(int(new[self.source(3 + axis, 1)]['value']['num']), new[pose]['value']['hi'][1 + axis])
        self.assertEqual(baseline['legacySnapshot'], self.execute(SCENE)['legacySnapshot'])

    def test_four_controls_prove_actual_h_callbacks_consume_definition_values(self):
        build = native()
        client = build.compile(ROOT / 'tests/geo261_definition_product_harness.c', 'definition-h-client',
                               ['GEOMETRY_KERNEL_EXTERNAL=1', 'GEOMETRY_WOODWORKING_EXTERNAL=1',
                                'GEOMETRY_HOST_HISTORY_EXTERNAL=1', 'GEOMETRY_HOST_CANDIDATE_EXTERNAL=1'])
        baseline = build.link('definition-h-client', [client, *build.product_objects()])
        original = build.woodworking / 'definition_sources.c'
        original_bytes = original.read_bytes()
        source = original_bytes.decode('utf-8')
        controls = (
            ('role', 'wd_write(w,(uint32_t)m->role,4);', 'wd_write(w,(uint32_t)m->role+1,4);', 'role'),
            ('anchor', 'wd_write(w,a->order,8);', 'wd_write(w,a->order+1,8);', 'anchor'),
            ('fixity', 'wd_write(&w,(uint32_t)b->fixity[l][i],4);', 'wd_write(&w,(uint32_t)b->fixity[l][i]+1,4);', 'fixity'),
            ('rc', 'GeoCoord fields[]={xl,xh,yl,yh,zl,zh};', 'GeoCoord fields[]={xl+1,xh,yl,yh,zl,zh};', 'RC'),
        )
        for name, before, after, marker in controls:
            with self.subTest(control=name):
                normal = subprocess.run([str(baseline), name], capture_output=True, text=True, timeout=30)
                self.assertEqual(0, normal.returncode, normal.stdout + normal.stderr)
                self.assertEqual(1, source.count(before))
                path = build.woodworking / ('definition-h-control-' + name + '.c')
                path.write_text(source.replace(before, after), encoding='utf-8')
                changed = build.compile(path, 'definition-h-control-' + name)
                product = build.link('definition-h-control-' + name, [client,
                    *[changed if obj == build.wood_definition_sources_object else obj for obj in build.product_objects()]])
                result = subprocess.run([str(product), name], capture_output=True, text=True, timeout=30)
                self.assertEqual(1, result.returncode, 'Crash/setup is not a control verdict: ' + result.stdout + result.stderr)
                self.assertEqual('ASSERT:definition-product-' + marker + '-is-returned-value\n', result.stderr)
                self.assertEqual(original_bytes, original.read_bytes())
                restored = subprocess.run([str(baseline), name], capture_output=True, text=True, timeout=30)
                self.assertEqual(0, restored.returncode, restored.stdout + restored.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
