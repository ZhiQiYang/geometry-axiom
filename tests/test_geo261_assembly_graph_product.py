"""Actual owned-member consumers and final I42 use shared assembly source values."""
import base64
from copy import deepcopy
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import _bridge
from tests import test_assembly_generation as generation
from tests import test_geo261_model_sources as model_sources
from tests import test_geo261_wood_assembly as definitions
from tests.test_geo261_native_kernel import native


def parameter(width=40, depth=50):
    return {'id': 10, 'name': 'secondary section', 'nextFieldId': 18, 'fields': [
        {'id': 5, 'name': 'A', 'type': 'dimension', 'input': str(width)},
        {'id': 17, 'name': 'B', 'type': 'dimension', 'input': str(depth)}]}


class AssemblyGraphProduct(unittest.TestCase):
    execute = model_sources.ModelSources.execute
    ref = staticmethod(model_sources.ModelSources.ref)
    nodes = model_sources.ModelSources.nodes

    @staticmethod
    def assembly_ref(kind, identifier, version=0, sub=0):
        return 'wood.assembly', bytes([kind]) + struct.pack('>III', identifier, version, sub)

    def edges(self, envelope):
        return {(self.ref(edge['consumer']), self.ref(edge['source']), edge['kind'])
                for edge in envelope['neutralSources']['edges']}

    def scenes(self, update=False, unused=False):
        build = native()
        with _bridge.BridgeSession(build.bridge()) as bridge:
            fixture = generation.Generation()
            fixture.bridge = bridge
            fixture.directory = build.work
            self.assertTrue(bridge.command('reset')['ok'])
            for line in ('surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
                         'spec position1 500', 'spec position2 2500', 'spec position3 1500',
                         'guide 1 1 v spec:position1', 'guide 2 1 v spec:position2', 'guide 3 1 u spec:position3',
                         'timber 90 20 20 role boundary', 'place 90 on 1 at-face e0 +u +n',
                         'timber 91 20 20 role boundary', 'place 91 on 1 at-face e2 +u +n'):
                fixture.line(line)
            binding = definitions.binding()
            for slot in binding['slots']:
                if slot['slotId'] == 41:
                    slot['A'] = {'kind': 'parameter', 'parameterId': 10, 'fieldId': 5}
                    slot['B'] = {'kind': 'parameter', 'parameterId': 10, 'fieldId': 17}
            operations = [{'op': 'publish-rule', 'value': definitions.rule()},
                          {'op': 'put-parameter', 'value': parameter()},
                          {'op': 'create-binding', 'value': binding}]
            if unused:
                rule = definitions.rule()
                rule['id'] = 99
                nullable = deepcopy(binding)
                nullable['id'] = 12
                nullable['slots'][0]['A'] = None
                nullable['slots'][0]['orientation'] = None
                operations.extend([{'op': 'publish-rule', 'value': rule}, {'op': 'create-binding', 'value': nullable}])
            fixture.apply(operations, False)
            fixture.apply([{'op': 'create-instance', 'expectedBindingFingerprint': definitions.digest(binding),
                            'value': definitions.source()}])
            state = bridge.command('assembly-read')['state']['instances'][0]
            mapping = {item['memberId']: item['timberId'] for item in state['value']['mapping']}
            before = bridge.command('dump')['text']
            if update:
                fixture.apply([{'op': 'put-parameter', 'value': parameter(42, 61)}], False)
            after = bridge.command('dump')['text']
        return before, after, mapping

    def test_owned_boxes_consume_typed_dimensions_and_i42_depends_on_actual_poses(self):
        scene, _, mapping = self.scenes()
        envelope = self.execute(scene)
        nodes, edges = self.nodes(envelope), self.edges(envelope)
        for member, sizes in ((11, (27, 33)), (37, (27, 33)), (89, (40, 50))):
            pose = 'woodworking.member.pose', struct.pack('=I', mapping[member])
            for axis, dimension in enumerate(sizes):
                source = self.assembly_ref(10 + axis, 2, sub=member)
                self.assertEqual(str(dimension), nodes[source]['value']['num'])
                self.assertIn((pose, source, 'value-required'), edges)
            self.assertIn((self.assembly_ref(12, 2), pose, 'value-required'), edges)
        for axis, field in ((0, 5), (1, 17)):
            generated = self.assembly_ref(10 + axis, 2, sub=89)
            slot = self.assembly_ref(5 + axis, 9, sub=41)
            self.assertIn((generated, slot, 'value-required'), edges)
            parameter_ref = 'core.parameter.field', struct.pack('=II', 10, field)
            self.assertTrue(any(a == slot and b[0] == 'woodworking.dimension-source' and relation == 'value-required'
                                for a, b, relation in edges))
            self.assertTrue(any(b == parameter_ref and relation == 'value-required' for _, b, relation in edges))
        self.assertTrue(any(a == self.assembly_ref(12, 2) and b[0] == 'core.placement'
                            and relation == 'value-required' for a, b, relation in edges))

    def test_unused_nullable_authored_definitions_are_preserved_without_new_geometry_roots(self):
        scene, _, _ = self.scenes(unused=True)
        envelope = self.execute(scene)
        nodes = self.nodes(envelope)
        rule = definitions.rule()
        rule['id'] = 99
        node = nodes[self.assembly_ref(1, 99, 1)]
        self.assertEqual(rule, json.loads(base64.b64decode(node['value']['contentBase64'], validate=True)))
        binding = nodes[self.assembly_ref(2, 12)]
        value = json.loads(base64.b64decode(binding['value']['contentBase64'], validate=True))
        self.assertIsNone(value['slots'][0]['A'])
        self.assertIn(self.assembly_ref(4, 12, sub=41), nodes)
        self.assertNotIn(self.assembly_ref(5, 12, sub=41), nodes)
        self.assertTrue(all(root['kind'] != 'assembly' for root in envelope['neutralSources']['roots']))

    def test_parameter_change_recomputes_owned_box_and_keeps_mapping_in_fresh_graph(self):
        before, after, mapping = self.scenes(update=True)
        old, changed = self.execute(before), self.execute(after)
        old_nodes, new_nodes = self.nodes(old), self.nodes(changed)
        self.assertNotEqual(old['candidate']['id'], changed['candidate']['id'])
        for member in (11, 37):
            pose = 'woodworking.member.pose', struct.pack('=I', mapping[member])
            self.assertEqual(old_nodes[pose]['value'], new_nodes[pose]['value'])
        for axis, dimension in ((0, 42), (1, 61)):
            self.assertEqual(str(dimension), new_nodes[self.assembly_ref(10 + axis, 2, sub=89)]['value']['num'])
        pose = 'woodworking.member.pose', struct.pack('=I', mapping[89])
        self.assertEqual([1973, 42, 61], new_nodes[pose]['value']['hi'])
        self.assertEqual(old_nodes[self.assembly_ref(8, 2)]['value'], new_nodes[self.assembly_ref(8, 2)]['value'])

    def test_actual_h_footprint_uses_box_pose_and_i42_preserves_first_refusal(self):
        build = native()
        client = build.compile(ROOT / 'tests/geo261_assembly_pose_product_harness.c', 'assembly-pose-product',
                               ['GEOMETRY_KERNEL_EXTERNAL=1', 'GEOMETRY_WOODWORKING_EXTERNAL=1',
                                'GEOMETRY_HOST_HISTORY_EXTERNAL=1', 'GEOMETRY_HOST_CANDIDATE_EXTERNAL=1'])
        executable = build.link('assembly-pose-product', [client, *build.product_objects()])
        result = subprocess.run([str(executable), 'pose'], capture_output=True, text=True, timeout=30)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual('PASS pose\n', result.stdout)
        self.assertEqual('', result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
