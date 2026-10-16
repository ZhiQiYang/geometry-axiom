"""Actual product placement and role fields consume the independently linked W."""
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native
from tests.test_geo261_wood_product import SCENE
from tests.test_geo261_wood_supports import frozen_translation_unit

class WoodSupportsProduct(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=native();source=build.woodworking/'support-product-client.c'
        shutil.copy2(ROOT/'tests/geo261_supports_harness.c',source)
        frozen=build.woodworking/'support-product-frozen.c';frozen.write_text(frozen_translation_unit(),encoding='utf-8')
        cls.client=build.compile(source,'support-product-client');cls.frozen=build.compile(frozen,'support-product-frozen')
        cls.exe=build.link('support-product-client',[cls.client,cls.frozen,build.wood_supports_object])

    def case(self,case,exe=None):
        run=subprocess.run([str(exe or self.exe),case],capture_output=True,text=True,timeout=10)
        self.assertIn(run.returncode,(0,1),'crash is not a support verdict: '+run.stderr)
        if run.returncode:self.assertIn('ASSERT:',run.stderr)
        return run.returncode

    def mutant(self,name,before,after):
        build=native();source=(build.woodworking/'supports.c').read_text(encoding='utf-8');self.assertEqual(1,source.count(before))
        path=build.woodworking/('supports-product-'+name+'.c');path.write_text(source.replace(before,after),encoding='utf-8')
        changed=build.compile(path,'supports-product-'+name);build.bridge()
        client=build.link('supports-product-'+name+'-client',[self.client,self.frozen,changed])
        bridge=build.link('supports-product-'+name+'-bridge',[build.bridge_object,*build.kernel_objects(),build.wood_members_object,changed])
        return client,bridge

    def load(self,exe,text):
        path=native().work/'supports-product.scene';path.write_text(text,encoding='utf-8')
        with _bridge.BridgeSession(exe) as bridge:
            before=bridge.command('dump')['text'];loaded=bridge.command('loadfile '+str(path))
            objects=bridge.command('objects');objects['_references']=bridge.command('references');after=bridge.command('dump')['text']
            if not loaded['ok']:self.assertEqual(before,after)
            return loaded,objects

    def test_boundary_derivation_guard_changes_kernel_client_and_object_fields(self):
        self.assertEqual(0,self.case('boundary'));loaded,objects=self.load(native().bridge(),SCENE);self.assertTrue(loaded['ok'],loaded)
        self.assertTrue(objects['timbers'][0]['onBoundary']);self.assertEqual(0,objects['timbers'][0]['boundaryEdge'])
        client,bridge=self.mutant('boundary','*out_on_boundary = true;','*out_on_boundary = false;')
        self.assertEqual(1,self.case('boundary',client));loaded,objects=self.load(bridge,SCENE)
        self.assertTrue(not loaded['ok'] or not objects['timbers'][0]['onBoundary'])
        self.assertEqual(0,self.case('boundary'));self.assertTrue(self.load(native().bridge(),SCENE)[1]['timbers'][0]['onBoundary'])

    def test_stop_identity_guard_changes_kernel_client_and_real_between_placement(self):
        scene=(ROOT/'_test_between.scene').read_text(encoding='utf-8')
        self.assertEqual(0,self.case('references'));loaded,objects=self.load(native().bridge(),scene);self.assertTrue(loaded['ok'],loaded)
        self.assertEqual(1960,next(timber for timber in objects['_references']['timbers'] if timber['id']==2)['geometry']['length'])
        client,bridge=self.mutant('identity','f->timber_id == r->timber','f->timber_id != r->timber')
        self.assertEqual(1,self.case('references',client));loaded,_=self.load(bridge,scene);self.assertFalse(loaded['ok'],loaded)
        self.assertTrue(self.load(native().bridge(),scene)[0]['ok'])

if __name__=='__main__':unittest.main(verbosity=2)
