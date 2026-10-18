"""Real preview/import paths retain and publish the validated candidate exactly once."""
import json
import subprocess
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native
from tests.test_geo261_wood_product import SCENE

# Same support/primary dependency as the existing room_a scene. The primary
# member really moves with guide 1; an unused guide is not an implicit I8a edit.
REPLAY_IMPACT_SCENE="""surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000
timber 90 20 20 role boundary
place 90 on 1 at-face e0 +u +n
timber 91 20 20 role boundary
place 91 on 1 at-face e2 +u +n
spec x 500
guide 1 1 v spec:x
timber 1 27 33 role primary
place 1 on 1 at-line guide 1 +v +n
"""

class CandidateProduct(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        b=native();cls.scene=b.work/'candidate-product.scene';cls.scene.write_text(SCENE,encoding='utf-8')
        cls.client=b.compile(ROOT/'tests/geo261_candidate_product_harness.c','candidate-product-client',
            ['GEOMETRY_KERNEL_EXTERNAL=1','GEOMETRY_WOODWORKING_EXTERNAL=1','GEOMETRY_HOST_HISTORY_EXTERNAL=1','GEOMETRY_HOST_CANDIDATE_EXTERNAL=1'])
        cls.exe=b.link('candidate-product-client',[cls.client,*b.product_objects()])

    def case(self,name,exe=None,path=None):
        r=subprocess.run([str(exe or self.exe),name,str(path or self.scene)],capture_output=True,text=True,timeout=30)
        self.assertIn(r.returncode,(0,1),'Crash/setup failure is not a candidate verdict: '+r.stderr)
        if r.returncode:self.assertIn('ASSERT:',r.stderr)
        return r

    def test_preview_revalidates_same_candidate_through_confirm_and_one_history_step(self):
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

    def test_reset_and_default_replace_complete_world_and_keep_old_history_policy(self):
        with _bridge.BridgeSession(native().bridge()) as session:
            initial=session.command('dump')['text']
            self.assertIn('boundary 1 outline ',initial)
            self.assertIn('placement 1 on boundary 1 ',initial)
            self.assertTrue(session.command('reset')['ok'])
            empty=session.command('dump')['text']
            self.assertFalse(any(row.startswith(('boundary ','placement ','timber ')) for row in empty.splitlines()))
            self.assertFalse(session.line('undo')['ok'])
            self.assertTrue(session.command('default')['ok'])
            self.assertEqual(initial,session.command('dump')['text'])
            self.assertFalse(session.line('undo')['ok'])

    def replay_result(self,name,tail="",scene=SCENE):
        path=native().work/'candidate-file-replay.scene';path.write_text(scene+tail,encoding='utf-8')
        result=self.case(name,path=path)
        print('FILE_REPLAY_JSON:'+json.dumps({'case':name,'exit_code':result.returncode,
              'stdout':result.stdout,'stderr':result.stderr},ensure_ascii=False))
        self.assertEqual(0,result.returncode,result.stderr)
        return result

    def test_owned_file_replay_avoids_inner_candidates_and_retains_final_graph(self):
        self.replay_result('replay-cost')

    def test_unscoped_parse_inside_outer_still_creates_each_inner_candidate(self):
        self.replay_result('replay-unscoped')

    def test_standalone_model_style_parse_keeps_five_lines_and_final_candidate(self):
        self.replay_result('replay-standalone')

    def test_optional_file_scratch_oom_falls_back_to_original_candidates(self):
        self.replay_result('replay-scratch-oom')

    def test_owned_file_replay_keeps_valid_and_invalid_i8a_original_refusal(self):
        for case,tail,preview in [('replay-i8a-valid','spec x 700\n','valid; confirm token to apply'),
                                  ('replay-i8a-invalid','spec x 100000001\n','invalid; cannot apply')]:
            with self.subTest(case=case):
                result=self.replay_result(case,tail,REPLAY_IMPACT_SCENE)
                self.assertIn('I8a preview 1: '+preview,result.stderr)

    def test_owned_file_replay_restores_all_bytes_after_real_partial_datum_failure(self):
        self.replay_result('replay-rollback')

    def test_owned_file_replay_releases_each_graph_across_real_preview_fallback(self):
        self.replay_result('replay-lifetime')

    def test_owned_file_replay_does_not_leak_keyed_operation_or_padding(self):
        self.replay_result('replay-operation')

    def test_line_readiness_uses_real_describe_failure_and_active_source_verdict(self):
        self.replay_result('replay-source-guards')

    def default_result(self,name):
        result=self.case(name)
        print('DEFAULT_REPLAY_JSON:'+json.dumps({'case':name,'argv':result.args,'exit_code':result.returncode,
              'stdout':result.stdout,'stderr':result.stderr},ensure_ascii=False))
        self.assertEqual(0,result.returncode,result.stderr)
        return result

    def test_owned_default_replay_keeps_only_spec_guide_inner_candidates_and_final_graph(self):
        self.default_result('default-cost')

    def test_default_optional_scratch_oom_keeps_original_nine_line_revisions(self):
        self.default_result('default-scratch-oom')

    def test_default_standalone_call_preserves_original_nine_candidates(self):
        self.default_result('default-standalone')

    def test_default_and_reset_preserve_revision_history_and_preview_policies(self):
        self.default_result('default-policy')

    def test_default_required_owner_failures_preserve_user_state_and_recover(self):
        for name in ('default-inner-oom','default-outer-oom'):
            with self.subTest(case=name):
                self.default_result(name)

    def test_default_replay_rejects_changed_or_truncated_builtin_program(self):
        self.default_result('default-program-guard')

if __name__=='__main__':unittest.main(verbosity=2)
