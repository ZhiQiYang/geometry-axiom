"""The actual H bridge consumes the isolated W member implementation."""
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native

SCENE='surface 1 origin 0 0 0 u +x v +y outline 0,0 1000,0 1000,1000 0,1000\nspec x 500\nguide 1 1 v spec:x\ntimber 1 40 50 role boundary\nplace 1 on 1 at-face e0 +u +n\n'
class WoodProduct(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=native();source=build.woodworking/'wood-product-client.c';shutil.copy2(ROOT/'tests/geo261_wood_members_harness.c',source)
        cls.client=build.compile(source,'wood-product-client')
        cls.exe=build.link('wood-product-client',[cls.client,build.wood_members_object,build.geometry_object])
    def case(self,exe,name):
        run=subprocess.run([str(exe),name],capture_output=True,text=True,timeout=10)
        self.assertIn(run.returncode,(0,1),'crash is not a W verdict: '+run.stderr);return run.returncode
    def mutant(self,name,before,after):
        build=native();source=(build.woodworking/'members.c').read_text(encoding='utf-8');self.assertEqual(1,source.count(before))
        path=build.woodworking/('members-product-'+name+'.c');path.write_text(source.replace(before,after),encoding='utf-8')
        changed=build.compile(path,'members-product-'+name);build.bridge()
        client=build.link('members-product-'+name+'-client',[self.client,changed,build.geometry_object])
        bridge=build.link('members-product-'+name+'-bridge',[build.bridge_object,*build.kernel_objects(),changed])
        return client,bridge
    def result(self,exe):
        build=native();path=build.work/'wood-product.scene';path.write_text(SCENE,encoding='utf-8')
        with _bridge.BridgeSession(exe) as session:
            loaded=session.command('loadfile '+str(path));self.assertTrue(loaded['ok'],loaded)
            objects=session.command('objects');self.assertTrue(objects['ok'],objects)
            rendered=session.command('render');self.assertTrue(rendered['ok'],rendered)
            return objects,rendered
    def test_role_priority_mutation_changes_standalone_and_real_product(self):
        self.assertEqual(0,self.case(self.exe,'construction'));control,_=self.result(native().bridge())
        self.assertEqual(1,control['timbers'][0]['priority'])
        client,bridge=self.mutant('priority','(GeoCoord)role + 1','(GeoCoord)role + 2')
        self.assertEqual(1,self.case(client,'construction'));changed,_=self.result(bridge)
        self.assertEqual(2,changed['timbers'][0]['priority']);self.assertEqual(0,self.case(self.exe,'construction'))
    def test_contact_face_mutation_changes_standalone_and_real_render_geometry(self):
        self.assertEqual(0,self.case(self.exe,'faces'));_,control=self.result(native().bridge())
        client,bridge=self.mutant('contact-face','[WOOD_MEMBER_FACE_A0]    = { 2, 0 }','[WOOD_MEMBER_FACE_A0]    = { 1, 0 }')
        self.assertEqual(1,self.case(client,'faces'));_,changed=self.result(bridge)
        self.assertTrue(control['ops']);self.assertNotEqual(control['ops'],changed['ops'])
        self.assertEqual(0,self.case(self.exe,'faces'))
if __name__=='__main__':unittest.main(verbosity=2)
