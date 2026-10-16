"""Typed demand graph governs the actual product's guide/member evaluation."""
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native

SCENE='spec h 100\nsurface 1 origin 0 0 0 u +x v +y rect 0 0 1000 1000\nguide 1 1 v spec:h\n'
class NativeSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=native();source=build.work/'sources-client.c';shutil.copy2(ROOT/'tests/geo261_sources_harness.c',source)
        cls.client=build.compile(source,'sources-client');cls.exe=build.link('sources-client',[cls.client,build.source_object])
    def case(self,name,exe=None):
        run=subprocess.run([str(exe or self.exe),name],capture_output=True,text=True,timeout=10)
        self.assertIn(run.returncode,(0,1),'native crash is not a source verdict: '+run.stderr);return run.returncode
    def test_exact_keys_provider_metadata_and_candidate_isolation(self):self.assertEqual(0,self.case('ownership'))
    def test_cycle_rejection_and_failed_value_memoization(self):self.assertEqual(0,self.case('cycles'))
    def test_soft_ordering_and_definition_edges_do_not_add_hard_requirements(self):self.assertEqual(0,self.case('relations'))
    def test_failure_retry_preserves_diagnostics_without_bypassing_descriptor_validation(self):self.assertEqual(0,self.case('failures'))
    def test_units_and_global_or_placed_axes_are_checked(self):self.assertEqual(0,self.case('types'))
    def test_recursive_node_growth_keeps_provider_and_node_lifetimes(self):self.assertEqual(0,self.case('growth'))
    def test_product_member_cycle_retains_all_ordered_diagnostics_and_soft_edges(self):
        build=native();client=build.compile(ROOT/'tests/geo261_source_product_harness.c','sources-product-client',['GEOMETRY_KERNEL_EXTERNAL=1','GEOMETRY_WOODWORKING_EXTERNAL=1','GEOMETRY_HOST_HISTORY_EXTERNAL=1','GEOMETRY_HOST_CANDIDATE_EXTERNAL=1'])
        exe=build.link('sources-product-client',[client,*build.product_objects()])
        run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
        self.assertEqual(0,run.returncode,'product source graph failure: '+run.stderr)
    def load(self,session,text=SCENE):
        path=native().work/'sources.scene';path.write_text(text,encoding='utf-8');result=session.command('loadfile '+str(path));self.assertTrue(result['ok'],result)
    def test_real_host_keeps_unplaced_dimensions_and_ordered_cycle_diagnostics(self):
        with _bridge.BridgeSession(native().bridge()) as session:
            self.load(session)
            for command in ('timber 1 40 50 role primary','guide 2 1 v timber:1:A','guide 3 1 v guide:2'):
                result=session.command('line '+command);self.assertTrue(result['ok'],result)
            refs=session.command('references');self.assertEqual([100,40,40],[x['off'] for x in refs['guides']]);before=session.command('dump')['text']
            result=session.command('line preview move 2 guide:3');self.assertTrue(result['ok'],result);self.assertFalse(result['preview']['valid'],result)
            violations=result['preview']['violations']
            self.assertEqual([0,0],[x['timber'] for x in violations])
            self.assertEqual(['D6a/I7/I9','D6a/I7/I9'],[x['clause'] for x in violations])
            self.assertTrue(violations[0]['actual'].startswith('guide 3: '),violations)
            self.assertTrue(violations[1]['actual'].startswith('guide 2: '),violations)
            self.assertEqual(before,session.command('dump')['text'])
    def test_cached_value_negative_control_changes_kernel_and_real_product(self):
        build=native();self.assertEqual(0,self.case('position'))
        # An edge coordinate is a typed axis-position input consumed by the
        # guide expression. The guide's own published output is observational;
        # publishing it must not write back into the K-owned guide cache.
        scene='surface 1 origin 0 0 0 u +x v +y outline 0,0 1000,0 1000,1000 0,1000\nguide 1 1 v edge:e1:u\n'
        with _bridge.BridgeSession(build.bridge()) as session:self.load(session,scene);self.assertEqual(1000,session.command('references')['guides'][0]['off'])
        before='node->value=value;node->state=GEO_NODE_VALID;node->status=GEO_SOURCE_OK;'
        after=before+'if(node->value.kind==GEO_SOURCE_AXIS_POSITION)++node->value.as.position.coordinate;'
        client,bridge=build.mutant('source',before,after,self.client)
        self.assertEqual(1,self.case('position',client))
        with _bridge.BridgeSession(bridge) as session:self.load(session,scene);self.assertEqual(1001,session.command('references')['guides'][0]['off'])
        self.assertEqual(0,self.case('position'))
if __name__=='__main__':unittest.main(verbosity=2)
