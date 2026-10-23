"""Product end-contact policy and the public W client share one linked object."""
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native
from tests.test_geo261_wood_contacts import frozen_translation_unit

class WoodContactsProduct(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=native();source=build.woodworking/'contacts-product-client.c';shutil.copy2(ROOT/'tests/geo261_contacts_harness.c',source)
        judge=build.woodworking/'contacts-product-frozen.c';judge.write_text(frozen_translation_unit(),encoding='utf-8')
        cls.client=build.compile(source,'contacts-product-client');cls.judge=build.compile(judge,'contacts-product-frozen')
        cls.exe=build.link('contacts-product-client',[cls.client,cls.judge,build.wood_contacts_object])

    def case(self,exe):
        result=subprocess.run([str(exe),'priorities'],capture_output=True,text=True,timeout=10)
        self.assertIn(result.returncode,(0,1),'process failure is not a contact-policy verdict: '+result.stderr)
        if result.returncode:self.assertIn('ASSERT:',result.stderr)
        return result.returncode

    def load(self,exe):
        with _bridge.BridgeSession(exe) as bridge:
            before=bridge.command('dump')['text'];result=bridge.command('loadfile '+str(ROOT/'_role_priority_ext_custom.scene'))
            if not result['ok']:self.assertEqual(before,bridge.command('dump')['text'])
            return result

    def test_extension_priority_controls_independent_client_and_actual_placement(self):
        build=native();self.assertEqual(0,self.case(self.exe));self.assertTrue(self.load(build.bridge())['ok'])
        source=(build.woodworking/'contacts.c').read_text(encoding='utf-8');before='owner_prio = 2;';self.assertEqual(1,source.count(before))
        path=build.woodworking/'contacts-product-mutant.c';path.write_text(source.replace(before,'owner_prio = 3;'),encoding='utf-8')
        changed=build.compile(path,'contacts-product-mutant')
        client=build.link('contacts-product-mutant-client',[self.client,self.judge,changed])
        bridge=build.link('contacts-product-mutant-bridge',[build.bridge_object,*[changed if obj==build.wood_contacts_object else obj for obj in build.product_objects()]])
        self.assertEqual(1,self.case(client));self.assertFalse(self.load(bridge)['ok'])
        self.assertEqual(0,self.case(self.exe));self.assertTrue(self.load(build.bridge())['ok'])

if __name__=='__main__':unittest.main(verbosity=2)
