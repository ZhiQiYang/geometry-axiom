"""Actual product graph and H consumers use derived policy source values."""
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
from tests import _bridge, test_geo261_model_sources as sources, test_panel_fill_host as host


class DerivedPolicyGraphProduct(unittest.TestCase):
    execute = sources.ModelSources.execute
    ref = staticmethod(sources.ModelSources.ref)
    nodes = sources.ModelSources.nodes

    @staticmethod
    def finish(kind, identifier):
        return 'wood.finish', bytes([kind]) + struct.pack('>I', identifier)

    def scene(self, guide=False):
        build = native()
        with _bridge.BridgeSession(build.bridge()) as bridge:
            fixture = host.PanelFillHost()
            fixture.bridge, fixture.directory = bridge, build.work
            self.assertTrue(bridge.command('reset')['ok'])
            fixture.region()
            if guide:
                key = host.PanelFillHost.key([['e1', 0, 1]]).split(':')[1]
                self.assertTrue(bridge.command('line guide 1 10 v edge-key:' + key + ':u')['ok'])
            return bridge.command('dump')['text']

    def test_guide_key_and_derived_region_share_the_actual_policy_dependencies(self):
        envelope = self.execute(self.scene(guide=True))
        nodes = self.nodes(envelope)
        edges = {(self.ref(edge['consumer']), self.ref(edge['source']), edge['kind'])
                 for edge in envelope['neutralSources']['edges']}
        policy = self.finish(21, 10)
        self.assertEqual('wood.finish.derived-policy/1', nodes[policy]['value']['schema'])
        for kind in (18, 19, 20):
            self.assertIn((policy, self.finish(kind, 10), 'value-required'), edges)
        self.assertIn((policy, self.finish(22, 8), 'definition-required'), edges)
        self.assertTrue(any(a[0] == 'app.legacy-reference' and b == policy and relation == 'definition-required'
                            for a, b, relation in edges))
        self.assertIn((self.finish(22, 8), self.finish(5, 8), 'value-required'), edges)
        content = base64.b64decode(nodes[policy]['value']['contentBase64'], validate=True)
        self.assertEqual(bytes([1]) + struct.pack('>I', 10) + bytes([0]) + struct.pack('>III', 1, 0, 4), content[:18])
        self.assertEqual(1, content[18])
        self.assertEqual(b'[["e0",0,1]]', content[21:21 + int.from_bytes(content[19:21], 'big')])
        guide = nodes['app.guide', struct.pack('=I', 1)]['value']
        self.assertEqual(100, guide['coordinate'])

    def test_h_reads_typed_geometry_despite_a_deliberately_stale_world_cache(self):
        build, executable, scene = self.harness()
        result = subprocess.run([str(executable), str(scene), 'geometry'], capture_output=True, text=True, timeout=30)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_current_snapshot_uses_its_geometry_even_with_an_ambient_candidate(self):
        build, executable, scene = self.harness()
        result = subprocess.run([str(executable), str(scene), 'snapshot'], capture_output=True, text=True, timeout=30)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def harness(self):
        build = native()
        scene = build.work / 'derived-policy-h.scene'
        scene.write_text(self.scene(), encoding='utf-8')
        client = build.compile(ROOT / 'tests/geo261_derived_policy_product_harness.c', 'derived-policy-h-client',
            ['GEOMETRY_KERNEL_EXTERNAL=1', 'GEOMETRY_WOODWORKING_EXTERNAL=1',
             'GEOMETRY_HOST_HISTORY_EXTERNAL=1', 'GEOMETRY_HOST_CANDIDATE_EXTERNAL=1'])
        self.client = client
        return build, build.link('derived-policy-h-client', [client, *build.product_objects()]), scene

    def test_three_value_substitution_controls_reach_real_h_fixity_and_key_consumers(self):
        build, baseline, scene = self.harness()
        original = build.woodworking / 'finish_sources.c'
        original_bytes = original.read_bytes()
        source = original_bytes.decode('utf-8')
        before = 'return status==GEO_SOURCE_OK;'
        after = ('extern void geo261_policy_source_control(WoodFinishSourceKind,uint32_t,GeoSourceValue *);\n'
                 '    if(status==GEO_SOURCE_OK)geo261_policy_source_control(kind,id,out);return status==GEO_SOURCE_OK;')
        self.assertEqual(1, source.count(before))
        path = build.woodworking / 'derived-policy-h-control.c'
        path.write_text(source.replace(before, after), encoding='utf-8')
        changed = build.compile(path, 'derived-policy-h-control')
        product = build.link('derived-policy-h-control', [self.client,
            *[changed if obj == build.wood_finish_sources_object else obj for obj in build.product_objects()]])
        for name in ('fixity', 'guide-key', 'member-key'):
            with self.subTest(control=name):
                normal = subprocess.run([str(baseline), str(scene), name], capture_output=True, text=True, timeout=30)
                self.assertEqual(0, normal.returncode, normal.stdout + normal.stderr)
                result = subprocess.run([str(product), str(scene), name], capture_output=True, text=True, timeout=30)
                self.assertEqual(1, result.returncode, 'Crash/setup is not a control verdict: ' + result.stdout + result.stderr)
                self.assertEqual('ASSERT:derived-product-' + name + '-is-returned-value\n', result.stderr)
                self.assertEqual(original_bytes, original.read_bytes())
                restored = subprocess.run([str(baseline), str(scene), name], capture_output=True, text=True, timeout=30)
                self.assertEqual(0, restored.returncode, restored.stdout + restored.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
