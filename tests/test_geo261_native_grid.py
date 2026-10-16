"""N1c exact sequence/clip oracles and actual product shared-code witness."""
from pathlib import Path
import random
import shutil
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native


class NativeGrid(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=native();source=build.work/'grid-client.c'
        shutil.copy2(ROOT/'tests/geo261_grid_harness.c',source)
        cls.client=build.compile(source,'grid-client')
        cls.exe=build.link('grid-client',[cls.client,build.grid_object,build.geometry_object])

    def call(self,*args,exe=None):
        result=subprocess.run([str(exe or self.exe),*map(str,args)],capture_output=True,text=True,timeout=10)
        self.assertEqual(0,result.returncode,result.stderr)
        return list(map(int,result.stdout.split()))

    def test_finite_body_gap_stop_and_floor_match_integer_oracle(self):
        rng=random.Random(26103)
        for _ in range(50):
            lo=rng.randint(-100,100);anchor=lo+rng.randint(0,20)
            body=rng.randint(1,100);gap=rng.randint(0,11);hi=anchor+rng.randint(1,1500)
            expected=[];k=0
            while anchor+(k+1)*(body+gap)<hi:
                expected.append(anchor+k*(body+gap)+body+gap//2);k+=1
            actual=self.call('finite',anchor,body,gap,lo,hi,64)
            self.assertEqual([0,len(expected),*expected] if len(expected)<=64 else [3,0],actual)
        self.assertEqual([0,0],self.call('finite',0,10,3,0,13,64))
        self.assertEqual([0,1,11],self.call('finite',0,10,3,0,14,64))

    def test_signed_lattice_window_sampling_keeps_global_indices(self):
        rng=random.Random(26104)
        for _ in range(50):
            base=rng.randint(-100,100);pitch=rng.randint(1,100);origin=rng.randint(-50,50)
            lo=rng.randint(-500,0);hi=rng.randint(0,500);limit=rng.randint(1,64)
            first=origin-((base-lo)//pitch);last=origin+(hi-base)//pitch
            total=max(0,last-first+1);stride=max(1,(total+limit-1)//limit)
            expected=[(i,base+(i-origin)*pitch) for i in range(first,last+1) if i%stride==0]
            actual=self.call('window',base,pitch,origin,lo,hi,limit,1)
            wanted=[0,1,first,last,total,stride,len(expected),*[v for pair in expected for v in pair]] if total else [0,1,0,0,0,1,0]
            self.assertEqual(wanted,actual)
        self.assertEqual([3,1,-100,100,201,1,0],self.call('window',0,1,0,-100,100,64,0))
        self.assertEqual([0,0,0,0,0,1,0],self.call('window',0,0,0,-100,100,64,0))

    def test_full_signed_index_and_derived_phase_outside_coordinate_domain(self):
        for index in (-(2**63),2**63-1):
            self.assertEqual([1,0],self.call('coordinate',0,7,index,index))
        self.assertEqual([0,197],self.call('coordinate',0,7,-(2**63),2**63-1))
        self.assertEqual([2,1,0,0,0,1,0],self.call('window',0,1,2**63-1,1,2,64,0))
        self.assertEqual([1,50000000],self.call('coordinate',250000000,200000000,0,-1))
        self.assertEqual([1,0],self.call('coordinate',-400000000,200000000,0,2))
        self.assertEqual([1,-1],self.call('coordinate',-(2**63),2**63-1,0,1))
        self.assertEqual([1,0],self.call('coordinate',2**63-1,2**63-1,0,-1))
        self.assertEqual([0,1,1,1,1,1,1,1,-1],self.call('window',-(2**63),2**63-1,0,-5,5,64,0))
        self.assertEqual([0,1,0,0,0,1,0],self.call('window',0,100,2**63-1,1,2,64,0))

    def test_negative_odd_bands_and_explicit_omission(self):
        for band in range(-7,8):
            self.assertEqual([37 if band%2 else 0],self.call('shift',1,37,band))
            self.assertEqual([0],self.call('shift',0,37,band))
        for k in (-3,-1,0,1,3):self.assertEqual([100+k*405+402],self.call('center',100,400,5,k))

    def test_subdivision_is_exact_and_capacity_is_not_truncation(self):
        self.assertEqual([0,0],self.call('subdivide',-10,20,1,64))
        self.assertEqual([0,2,0,10],self.call('subdivide',-10,20,3,64))
        self.assertEqual([9,0],self.call('subdivide',0,10,3,64))
        self.assertEqual([3,0],self.call('subdivide',0,100,5,3))

    def test_clipped_area_matches_disjoint_rectangle_oracle(self):
        rng=random.Random(26105)
        def overlap(a,b):return max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
        for _ in range(60):
            x,y=rng.randint(-5,15),rng.randint(-5,15)
            r=(x,y,x+rng.randint(1,10),y+rng.randint(1,10))
            expected=2*(overlap(r,(0,0,10,4))+overlap(r,(0,4,4,10)))
            self.assertEqual([0,expected],self.call('area',*r))
        self.assertEqual([0,1,0,1,1],self.call('regions'))

    def product_centers(self,exe):
        with _bridge.BridgeSession(exe) as session:
            self.assertTrue(session.command('reset')['ok'])
            cmd='line grid-system 0 name-hex 74657374 main-along none u repeat-panel 400 gap 5 from -100 v repeat 0 100'
            result=session.command(cmd)
            if 'preview' in result:
                self.assertTrue(result['preview']['valid'],result)
                result=session.command('line confirm '+str(result['preview']['token']))
            self.assertTrue(result['ok'],result)
            result=session.command('grid-query system 0 rect -1000 0 1200 100 mode exact limit 64')
            self.assertTrue(result['ok'],result)
            return [(int(line['index']),line['coordinate']) for line in result['axes']['u']['lines']]

    def test_floor_negative_control_changes_kernel_and_actual_product(self):
        build=native();expected=[(-3,-913),(-2,-508),(-1,-103),(0,302),(1,707),(2,1112)]
        self.assertEqual([302],self.call('center',-100,400,5,0))
        self.assertEqual(expected,self.product_centers(build.bridge()))
        client,bridge=build.mutant('grid','+body+gap/2;','+body+(gap+1)/2;',self.client)
        self.assertEqual([303],self.call('center',-100,400,5,0,exe=client))
        self.assertEqual([(i,c+1) for i,c in expected],self.product_centers(bridge))
        self.assertEqual([302],self.call('center',-100,400,5,0))
        self.assertEqual(expected,self.product_centers(build.bridge()))

    def test_large_staggered_binding_base_still_has_valid_signed_lines(self):
        with _bridge.BridgeSession(native().bridge()) as session:
            def commit(command):
                result=session.command('line '+command)
                if 'preview' in result:
                    self.assertTrue(result['preview']['valid'],result)
                    result=session.command('line confirm '+str(result['preview']['token']))
                self.assertTrue(result['ok'],result)
            self.assertTrue(session.command('reset')['ok'])
            commit('boundary 1 outline -100000000,0 0,0 0,100 -100000000,100')
            commit('grid-system 0 name-hex 73746167676572 main-along none u repeat-panel 100000000 gap 100000000 from 0 stagger 100000000 v repeat 0 100')
            fingerprint=session.command('boundary 1')['geometryFingerprint']
            commit('grid-binding 0 on-boundary 1 from-system 0 vertex outer 0 geometry-hash '+fingerprint+' cell 0 1 anchor 1 1 0 1')
            result=session.command('grid-query binding 0 rect -5 0 5 100 mode exact limit 64')
            self.assertTrue(result['ok'],result)
            self.assertEqual([(2,0)],[(int(line['index']),line['coordinate']) for line in result['axes']['u']['lines']])


if __name__=='__main__':unittest.main(verbosity=2)
