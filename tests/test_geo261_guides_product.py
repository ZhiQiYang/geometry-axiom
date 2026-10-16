"""Real H guide transactions consume the independently compiled K guide store."""
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native
from tests.test_geo261_native_datums import SCENE as DATUM_SCENE

SCENE=DATUM_SCENE+'guide 2 1 v 1/2*spec:h\n'

class GuideProduct(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=native();source=build.work/'guides-product-client.c'
        shutil.copy2(ROOT/'tests/geo261_guides_harness.c',source)
        cls.client=build.compile(source,'guides-product-client')
        cls.exe=build.link('guides-product-client',[cls.client,build.guides_object,
            build.datums_object,build.linear_object,build.exact_object,build.geometry_object])

    def case(self,exe):
        result=subprocess.run([str(exe),'local-values'],capture_output=True,text=True,timeout=10)
        self.assertIn(result.returncode,(0,1),'native crash is not a guide verdict: '+result.stderr)
        return result.returncode

    def load(self,session,text=SCENE):
        path=native().work/'guides-product.scene';path.write_text(text,encoding='utf-8')
        result=session.command('loadfile '+str(path));self.assertTrue(result['ok'],result)

    def guide(self,session,identifier=2):
        response=session.command('references');self.assertTrue(response['ok'],response)
        return next(item for item in response['guides'] if item['id']==identifier)

    def test_actual_local_text_and_cache_preview_cancel_confirm_undo_and_reload(self):
        with _bridge.BridgeSession(native().bridge()) as session:
            self.load(session);before=session.command('dump')['text']
            self.assertIn('guide 2 1 v 1/2*spec:h\n',before)
            self.assertEqual((1,'1/2*spec:h'),(self.guide(session)['off'],self.guide(session)['expression']))
            for cancel in (True,False):
                preview=session.command('line preview move 2 spec:h')
                self.assertTrue(preview['ok'],preview);self.assertTrue(preview['preview']['valid'],preview)
                self.assertEqual(before,session.command('dump')['text'])
                self.assertEqual(1,self.guide(session)['off'])
                if cancel:
                    self.assertTrue(session.command('line cancel-preview')['ok'])
                    self.assertEqual(before,session.command('dump')['text'])
                else:
                    confirmed=session.command('line confirm '+str(preview['preview']['token']))
                    self.assertTrue(confirmed['ok'],confirmed)
            after=session.command('dump')['text']
            self.assertIn('guide 2 1 v spec:h\n',after)
            self.assertEqual((3,'spec:h'),(self.guide(session)['off'],self.guide(session)['expression']))
            self.assertTrue(session.command('line undo')['ok']);self.assertEqual(before,session.command('dump')['text'])
            self.assertEqual(1,self.guide(session)['off'])
            self.load(session,after);self.assertEqual(after,session.command('dump')['text'])
            self.assertEqual((3,'spec:h'),(self.guide(session)['off'],self.guide(session)['expression']))
            self.assertEqual((7,''),(self.guide(session,1)['off'],self.guide(session,1)['expression']))

    def test_local_offset_mutation_changes_the_independent_client_and_real_product(self):
        build=native();self.assertEqual(0,self.case(self.exe))
        with _bridge.BridgeSession(build.bridge()) as session:
            self.load(session);self.assertEqual(1,self.guide(session)['off'])
        client,bridge=build.mutant('guides','guide->offset = result.linear.value.num;',
            'guide->offset = result.linear.value.num + 1;',self.client)
        self.assertEqual(1,self.case(client))
        with _bridge.BridgeSession(bridge) as session:
            self.load(session);self.assertEqual(2,self.guide(session)['off'])
        self.assertEqual(0,self.case(self.exe))
        with _bridge.BridgeSession(build.bridge()) as session:
            self.load(session);self.assertEqual(1,self.guide(session)['off'])

if __name__=='__main__':unittest.main(verbosity=2)
