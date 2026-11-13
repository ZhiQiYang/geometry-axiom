"""The real transaction path uses K-owned vertex identities and reconciliation."""
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native

SCENE='boundary 1 outline 0,0 100,0 100,100 0,100\nboundary-vertex-keys 1 outer 1 2 3 4 next-key 5\n'
INSERT='boundary 1 outline 0,0 50,0 100,0 100,100 0,100'

class RegionProduct(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=native();path=build.work/'regions-product-client.c';shutil.copy2(ROOT/'tests/geo261_regions_harness.c',path)
        cls.client=build.compile(path,'regions-product-client')
        cls.exe=build.link('regions-product-client',[cls.client,build.regions_object,build.geometry_object])

    def case(self,exe):
        result=subprocess.run([str(exe),'ordinary'],capture_output=True,text=True,timeout=10)
        self.assertIn(result.returncode,(0,1),'process failure is not an identity verdict: '+result.stderr)
        return result.returncode

    def load(self,bridge):
        path=native().work/'regions-product.scene';path.write_text(SCENE,encoding='utf-8')
        result=bridge.command('loadfile '+str(path));self.assertTrue(result['ok'],result)

    def test_identity_allocator_preview_cancel_confirm_and_undo_share_whole_snapshot(self):
        with _bridge.BridgeSession(native().bridge()) as bridge:
            self.load(bridge);before=bridge.command('dump')['text']
            result=bridge.command('line preview '+INSERT);self.assertTrue(result['ok'],result);self.assertTrue(result['preview']['valid'],result)
            self.assertEqual(before,bridge.command('dump')['text'])
            self.assertTrue(bridge.command('line cancel-preview')['ok']);self.assertEqual(before,bridge.command('dump')['text'])
            result=bridge.command('line preview '+INSERT)
            self.assertTrue(bridge.command('line confirm '+str(result['preview']['token']))['ok'])
            self.assertIn('boundary-vertex-keys 1 outer 1 5 2 3 4 next-key 6\n',bridge.command('dump')['text'])
            self.assertTrue(bridge.command('line undo')['ok']);self.assertEqual(before,bridge.command('dump')['text'])

    def test_coordinate_match_guard_controls_independent_client_and_actual_preview(self):
        build=native();self.assertEqual(0,self.case(self.exe))
        with _bridge.BridgeSession(build.bridge()) as bridge:
            self.load(bridge);self.assertTrue(bridge.command('line preview '+INSERT)['preview']['valid'])
        client,changed=build.mutant('regions','loop->v[i].u == p.u && loop->v[i].v == p.v','loop->v[i].u == p.u || loop->v[i].v == p.v',self.client)
        self.assertEqual(1,self.case(client))
        with _bridge.BridgeSession(changed) as bridge:
            self.load(bridge);before=bridge.command('dump')['text'];result=bridge.command('line preview '+INSERT)
            self.assertTrue(result['ok'],result);self.assertFalse(result['preview']['valid'],result)
            self.assertEqual(before,bridge.command('dump')['text'])
        self.assertEqual(0,self.case(self.exe))

if __name__=='__main__':unittest.main(verbosity=2)
