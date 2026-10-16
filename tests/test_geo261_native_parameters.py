"""K-owned parameter state: standalone API, snapshots and product witness."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native


class NativeParameters(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=native();source=build.work/'parameters-client.c'
        shutil.copy2(ROOT/'tests/geo261_parameters_harness.c',source)
        cls.client=build.compile(source,'parameters-client')
        cls.exe=build.link('parameters-client',[cls.client,build.parameters_object,build.exact_object,build.codec_object,build.geometry_object])

    def case(self,name,exe=None):
        run=subprocess.run([str(exe or self.exe),name],capture_output=True,text=True,timeout=10)
        self.assertIn(run.returncode,(0,1),'native crash is not a parameter verdict: '+run.stderr)
        return run

    def check(self,name):
        run=self.case(name);self.assertEqual(0,run.returncode,run.stderr)

    def test_exact_dependencies_and_coordinate_constraint(self):self.check('exact')
    def test_dimension_count_ratio_remain_distinct(self):self.check('types')
    def test_field_high_water_and_exhaustion_survive_deletion(self):self.check('identity')
    def test_cloned_candidates_own_every_definition_and_cache(self):self.check('clone')
    def test_missing_and_cyclic_sources_keep_full_identity_trace(self):self.check('references')
    def test_atomic_input_staging_owns_no_host_loading_state(self):self.check('staging')

    def product_count(self,exe):
        with _bridge.BridgeSession(exe) as session:
            self.assertTrue(session.command('reset')['ok'])
            current=session.command('engineering-read');self.assertTrue(current['ok'],current)
            request={'schema':'engineering-transaction/1','expectedRevision':current['revision'],
                     'operations':[{'op':'put-parameter','value':{'id':1,'name':'counts','fields':[{'id':1,'name':'count','type':'count','input':'-1'}]}}]}
            path=native().work/'negative-count.json';path.write_text(json.dumps(request),encoding='utf-8')
            response=session.command('engineering-preview '+str(path));self.assertTrue(response['ok'],response)
            return response

    def test_count_guard_negative_control_changes_kernel_and_product(self):
        build=native();self.check('types')
        response=self.product_count(build.bridge());self.assertFalse(response['preview']['valid'],response)
        self.assertIn('I38 COUNT',json.dumps(response))
        client,bridge=build.mutant('parameters','if(ok&&f->type==1&&(value.num<0||value.den!=1))','if(0)',self.client)
        self.assertEqual(1,self.case('types',client).returncode)
        response=self.product_count(bridge);self.assertTrue(response['preview']['valid'],response)
        self.check('types');self.assertFalse(self.product_count(build.bridge())['preview']['valid'])


if __name__=='__main__':unittest.main(verbosity=2)
