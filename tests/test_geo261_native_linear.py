"""K-owned named values and typed linear expressions, with product controls."""
from fractions import Fraction
import random
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native

class NativeLinear(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=native();source=build.work/'linear-client.c';shutil.copy2(ROOT/'tests/geo261_linear_harness.c',source)
        cls.client=build.compile(source,'linear-client')
        cls.exe=build.link('linear-client',[cls.client,build.linear_object,build.named_values_object,build.exact_object,build.geometry_object])

    def call(self,*args,exe=None):
        run=subprocess.run([str(exe or self.exe),*map(str,args)],capture_output=True,text=True,timeout=10)
        self.assertIn(run.returncode,(0,1),'crash is not a semantic verdict: '+run.stderr)
        return run

    def test_named_values_own_identity_capacity_order_and_clones(self):self.assertEqual(0,self.call('named').returncode)
    def test_modes_failures_and_invalid_suffix_keep_source_order(self):self.assertEqual(0,self.call('statuses').returncode)

    def test_floor_final_matches_independent_fraction_oracle(self):
        rng=random.Random(2612)
        for _ in range(90):
            terms=[(rng.randint(-10000,10000),rng.randint(-100,100),rng.randint(1,30)) for _ in range(rng.randint(1,8))]
            expected=sum((Fraction(v*n,d) for v,n,d in terms),Fraction())
            result=self.call(0,*(x for term in terms for x in term));self.assertEqual(0,result.returncode,result.stderr)
            status,num,den,calls=map(int,result.stdout.split())
            self.assertEqual((0,expected.numerator//expected.denominator,1,len(terms)),(status,num,den,calls))

    def test_exact_final_preserves_integer_constraint_and_cross_cancellation(self):
        for terms,expected in [([(-3,1,2),(5,1,2)],(0,1,1,2)),([(-3,1,2)],(4,-3,2,1)),([(2**63-1,1,2**63-1)],(0,1,1,1))]:
            run=self.call(1,*(x for term in terms for x in term));self.assertEqual(expected,tuple(map(int,run.stdout.split())))

    def product(self,exe,text):
        path=native().work/'linear.scene';path.write_text(text,encoding='utf-8')
        with _bridge.BridgeSession(exe) as session:
            response=session.command('loadfile '+str(path));self.assertTrue(response['ok'],response)
            result=session.command('references');self.assertTrue(result['ok'],result);return result

    def test_floor_negative_control_changes_kernel_and_real_datum(self):
        build=native();text='spec width 1\ndatum 7 z -1/2*spec:width\n'
        self.assertEqual(-1,self.product(build.bridge(),text)['datums'][0]['position'])
        client,bridge=build.mutant('linear','sum/den-(sum<0&&sum%den!=0)','sum/den',self.client)
        self.assertEqual(1,self.call('statuses',exe=client).returncode)
        self.assertEqual(0,self.product(bridge,text)['datums'][0]['position'])
        self.assertEqual(-1,self.product(build.bridge(),text)['datums'][0]['position'])

    def test_named_store_negative_control_changes_kernel_and_real_spec(self):
        build=native();text='spec width 91\n'
        self.assertEqual(91,self.product(build.bridge(),text)['specs'][0]['value'])
        client,bridge=build.mutant('named_values','next.value=value;','next.value=value+1;',self.client)
        self.assertEqual(1,self.call('named',exe=client).returncode)
        self.assertEqual(92,self.product(bridge,text)['specs'][0]['value'])
        self.assertEqual(91,self.product(build.bridge(),text)['specs'][0]['value'])

if __name__=='__main__':unittest.main(verbosity=2)
