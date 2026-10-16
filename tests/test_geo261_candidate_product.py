"""Real preview/import paths retain and publish the validated candidate exactly once."""
import subprocess
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native
from tests.test_geo261_wood_product import SCENE

class CandidateProduct(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        b=native();cls.scene=b.work/'candidate-product.scene';cls.scene.write_text(SCENE,encoding='utf-8')
        cls.client=b.compile(ROOT/'tests/geo261_candidate_product_harness.c','candidate-product-client',
            ['GEOMETRY_KERNEL_EXTERNAL=1','GEOMETRY_WOODWORKING_EXTERNAL=1','GEOMETRY_HOST_HISTORY_EXTERNAL=1','GEOMETRY_HOST_CANDIDATE_EXTERNAL=1'])
        cls.exe=b.link('candidate-product-client',[cls.client,*b.product_objects()])

    def case(self,name,exe=None):
        r=subprocess.run([str(exe or self.exe),name,str(self.scene)],capture_output=True,text=True,timeout=30)
        self.assertIn(r.returncode,(0,1),'Crash/setup failure is not a candidate verdict: '+r.stderr)
        if r.returncode:self.assertIn('ASSERT:',r.stderr)
        return r

    def test_preview_retains_same_resolver_through_confirm_and_one_history_step(self):
        r=self.case('lifecycle');self.assertEqual(0,r.returncode,r.stderr)
    def test_sealed_template_bytes_cannot_be_replaced(self):
        r=self.case('wood-tamper');self.assertEqual(0,r.returncode,r.stderr)
    def test_sealed_presentation_bytes_cannot_be_replaced(self):
        r=self.case('host-tamper');self.assertEqual(0,r.returncode,r.stderr)
    def test_sealed_before_template_bytes_cannot_be_replaced(self):
        r=self.case('before-tamper');self.assertEqual(0,r.returncode,r.stderr)
    def test_kernel_revision_rejects_even_if_legacy_token_revision_is_altered(self):
        r=self.case('revision');self.assertEqual(0,r.returncode,r.stderr)
    def test_cancel_discards_candidate_and_cannot_publish(self):
        r=self.case('cancel');self.assertEqual(0,r.returncode,r.stderr)
    def test_import_and_readonly_validation_preserve_unrelated_live_preview(self):
        r=self.case('imports');self.assertEqual(0,r.returncode,r.stderr)

    def mutation(self,module,attribute,before,after,case,label):
        b=native();directory=b.host if attribute.startswith('host_') else b.kernel
        text=(directory/(module+'.c')).read_text(encoding='utf-8');self.assertEqual(1,text.count(before))
        path=directory/(module+'-product-mutant.c');path.write_text(text.replace(before,after),encoding='utf-8')
        changed=b.compile(path,module+'-product-mutant');original=getattr(b,attribute)
        objects=b.product_objects();self.assertEqual(1,objects.count(original))
        exe=b.link(module+'-product-mutant',[self.client,*[changed if obj==original else obj for obj in objects]])
        r=self.case(case);self.assertEqual(0,r.returncode,r.stderr)
        r=self.case(case,exe);self.assertEqual(1,r.returncode,r.stderr);self.assertIn('ASSERT:'+label,r.stderr)
        r=self.case(case);self.assertEqual(0,r.returncode,r.stderr)

    def test_actual_host_hash_object_is_required_by_real_confirm(self):
        self.mutation('app_candidate','host_candidate_object','return !strcmp(actual,expected);','return true;',
            'wood-tamper','full-snapshot-tamper-rejected')
    def test_actual_kernel_revision_object_is_required_by_real_confirm(self):
        self.mutation('candidate','candidate_object','if(live_revision!=candidate->base_revision)return GEO_CANDIDATE_REVISION_CHANGED;',
            '/* negative control: omit actual K revision check */','revision','kernel-revision-gate')

    def test_real_bridge_import_confirm_uses_prepared_bytes_after_source_file_changes(self):
        b=native();path=b.work/'candidate-import.scene';path.write_text(SCENE,encoding='utf-8')
        with _bridge.BridgeSession(b.bridge()) as session:
            loaded=session.command('loadfile '+str(path));self.assertTrue(loaded['ok'],loaded)
            before=session.command('dump')['text']
            path.write_text(SCENE.replace('spec x 500','spec x 700'),encoding='utf-8')
            preview=session.command('load-prepare '+str(path));self.assertTrue(preview['ok'],preview)
            self.assertEqual(before,session.command('dump')['text'])
            path.write_text('this source has changed\n',encoding='utf-8')
            confirm=session.command('load-confirm '+str(preview['token']));self.assertTrue(confirm['ok'],confirm)
            self.assertIn('spec x 700\n',session.command('dump')['text'])
            self.assertTrue(session.line('undo')['ok']);self.assertEqual(before,session.command('dump')['text'])

if __name__=='__main__':unittest.main(verbosity=2)
