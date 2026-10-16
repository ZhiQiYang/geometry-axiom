"""K-owned datum definitions/caches and real host text/transaction behavior."""
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native

SCENE='spec h 3\ndatum 1 x -1/2*spec:h\nsurface 1 origin 5 0 0 u -x v +z rect 0 0 100 100\nguide 1 1 datum 1\n'
class NativeDatums(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=native();source=build.work/'datums-client.c';shutil.copy2(ROOT/'tests/geo261_datums_harness.c',source)
        cls.client=build.compile(source,'datums-client')
        cls.exe=build.link('datums-client',[cls.client,build.datums_object,build.linear_object,build.exact_object,build.geometry_object])

    def case(self,name,exe=None):
        run=subprocess.run([str(exe or self.exe),name],capture_output=True,text=True,timeout=10)
        self.assertIn(run.returncode,(0,1),'native crash is not a datum verdict: '+run.stderr);return run.returncode

    def test_typed_definitions_and_caches_have_independent_ownership(self):self.assertEqual(0,self.case('ownership'))
    def test_capacity_replacement_deletion_and_uint32_identity(self):self.assertEqual(0,self.case('capacity'))
    def test_failed_values_keep_the_existing_cache_policy(self):self.assertEqual(0,self.case('failures'))
    def test_all_signed_orthogonal_frames_use_world_plane_membership(self):self.assertEqual(0,self.case('frames'))

    def load(self,session,text=SCENE):
        path=native().work/'datums.scene';path.write_text(text,encoding='utf-8')
        result=session.command('loadfile '+str(path));self.assertTrue(result['ok'],result)

    def test_real_host_roundtrip_preview_cancel_confirm_and_undo(self):
        with _bridge.BridgeSession(native().bridge()) as session:
            self.load(session);before=session.command('dump')['text']
            refs=session.command('references');self.assertEqual(-2,refs['datums'][0]['position']);self.assertEqual(7,refs['guides'][0]['off'])
            self.assertIn('datum 1 x -1/2*spec:h\n',before)
            preview=session.command('line preview spec h 5');self.assertTrue(preview['ok'],preview)
            self.assertEqual(before,session.command('dump')['text'])
            self.assertTrue(session.command('line cancel-preview')['ok'])
            self.assertEqual(before,session.command('dump')['text'])
            preview=session.command('line preview spec h 5');self.assertTrue(preview['ok'],preview)
            token=preview['preview']['token'];self.assertTrue(session.command('line confirm '+str(token))['ok'])
            self.assertEqual(-3,session.command('references')['datums'][0]['position'])
            self.assertTrue(session.command('line undo')['ok']);self.assertEqual(before,session.command('dump')['text'])
            self.load(session,before);self.assertEqual(before,session.command('dump')['text'])

    def test_malformed_suffix_keeps_earlier_missing_parameter_diagnostic(self):
        with _bridge.BridgeSession(native().bridge()) as session:
            self.load(session);before=session.command('dump')['text']
            for expression in ('param:99:1+1/0*spec:h','param:99:1+param:bad'):
                result=session.command('line preview datum 9 x '+expression)
                self.assertTrue(result['ok'],result);self.assertFalse(result['preview']['valid'],result)
                self.assertIn({'timber':0,'clause':'D6c/I7a',
                               'expected':'axis X/Y/Z and exact spec-only expression within D1',
                               'actual':'datum 9: I38 MISSING: parameter 99'},result['preview']['violations'])
                self.assertEqual(before,session.command('dump')['text'])

    def test_intersection_negative_control_changes_kernel_and_product(self):
        build=native()
        with _bridge.BridgeSession(build.bridge()) as session:
            self.load(session);self.assertEqual(7,session.command('references')['guides'][0]['off'])
        client,bridge=build.mutant('datums','(datum->position-origin)','datum->position',self.client)
        self.assertEqual(1,self.case('frames',client))
        with _bridge.BridgeSession(bridge) as session:
            self.load(session);self.assertEqual(2,session.command('references')['guides'][0]['off'])
        self.assertEqual(0,self.case('frames'))

if __name__=='__main__':unittest.main(verbosity=2)
