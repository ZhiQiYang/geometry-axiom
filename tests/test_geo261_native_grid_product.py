"""Actual bridge and H adapters consume the owned K grid source/binding store."""
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native
from tests.test_grid_system_contract import rejection_reason


def source(identifier=5, main="u", u="repeat 7 120 stagger 13", v="repeat -11 80 stagger -7"):
    return f"grid-system {identifier} name-hex 677269642073746f7265 main-along {main} u {u} v {v}"


class GridStoreProduct(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=native();path=build.work/'grid-store-product-client.c'
        shutil.copy2(ROOT/'tests/geo261_grid_store_harness.c',path)
        cls.client=build.compile(path,'grid-store-product-client')
        cls.exe=build.link('grid-store-product-client',[cls.client,build.grid_store_object,
            build.grid_object,build.geometry_object,build.codec_object])

    def case(self,name,exe=None):
        run=subprocess.run([str(exe or self.exe),name],capture_output=True,text=True,timeout=10)
        self.assertIn(run.returncode,(0,1),'native crash/setup failure is not a grid verdict: '+run.stderr)
        return run.returncode

    def commit(self,session,command):
        result=session.command('line '+command)
        if 'preview' in result:
            self.assertTrue(result['preview']['valid'],result)
            result=session.command('line confirm '+str(result['preview']['token']))
        self.assertTrue(result['ok'],(command,result));return result

    def setup_binding(self,session):
        self.assertTrue(session.command('reset')['ok'])
        self.commit(session,'boundary 71 outline 400,500 1600,500 1600,1300 400,1300')
        self.commit(session,source())
        fingerprint=session.command('boundary 71')['geometryFingerprint']
        self.commit(session,'grid-binding 1 on-boundary 71 from-system 5 vertex outer 0 geometry-hash '+fingerprint+
            ' cell -2 -3 anchor 2 4 2 8')

    def binding_translation(self,exe):
        with _bridge.BridgeSession(exe) as session:
            self.setup_binding(session)
            binding=session.command('objects')['gridBindings'][0]
            self.assertEqual([{'num':1,'den':2},{'num':1,'den':4}],binding['anchor'])
            return binding['translation']

    def mutant(self,name,before,after):
        build=native();text=(build.kernel/'grid_store.c').read_text(encoding='utf-8')
        self.assertEqual(1,text.count(before),'negative control must change exactly one expression')
        path=build.work/('grid-store-product-'+name+'.c');path.write_text(text.replace(before,after),encoding='utf-8')
        changed=build.compile(path,'grid-store-product-'+name);build.bridge()
        client=build.link('grid-store-product-'+name+'-client',[self.client,changed,build.grid_object,build.geometry_object,build.codec_object])
        objects=build.product_objects();self.assertEqual(1,objects.count(build.grid_store_object))
        bridge=build.link('grid-store-product-'+name+'-bridge',[build.bridge_object,
            *[changed if obj==build.grid_store_object else obj for obj in objects]])
        return client,bridge

    def test_actual_host_keeps_role_sidecar_order_binding_bytes_and_undo_roundtrip(self):
        with _bridge.BridgeSession(native().bridge()) as session:
            self.setup_binding(session)
            self.commit(session,source(6,'v','repeat 0 100','repeat 0 100'))
            before=session.command('dump')['text'];objects=session.command('objects')
            self.assertEqual([5,6],[item['id'] for item in objects['gridSystems']])
            self.assertEqual(['u','v'],[item['mainAlong'] for item in objects['gridSystems']])
            self.assertEqual([560,731],objects['gridBindings'][0]['translation'])
            self.commit(session,'delete grid-binding 1');self.commit(session,'delete grid-system 5')
            self.assertEqual([(6,'v')],[(item['id'],item['mainAlong']) for item in session.command('objects')['gridSystems']])
            self.commit(session,'undo');self.commit(session,'undo')
            self.assertEqual(before,session.command('dump')['text'])
            restored=session.command('objects')
            self.assertEqual(objects['gridSystems'],restored['gridSystems'])
            self.assertEqual(objects['gridBindings'],restored['gridBindings'])
            path=native().work/'grid-store-product-roundtrip.scene';path.write_text(before,encoding='utf-8')
            self.assertTrue(session.command('loadfile '+str(path))['ok'])
            self.assertEqual(before,session.command('dump')['text'])
            self.assertEqual(objects['gridSystems'],session.command('objects')['gridSystems'])

    def test_redeclaration_and_rule_edits_keep_source_identity_and_undo_highwater(self):
        with _bridge.BridgeSession(native().bridge()) as session:
            self.assertTrue(session.command('reset')['ok'])
            self.commit(session,source(5,'u','repeat 7 120','repeat -11 80'))
            rule='grid-source-rule 5 create name-hex 72756c65 selector cell -2 -3 divide 3 2'
            self.commit(session,rule)
            initial=session.command('objects')['gridSystems'][0]
            self.assertEqual(2,initial['nextRuleKey']);self.assertEqual(1,initial['rules'][0]['ruleKey'])
            self.commit(session,source(5,'v','repeat 17 120','repeat -21 80'))
            changed=session.command('objects')['gridSystems'][0]
            self.assertEqual('v',changed['mainAlong']);self.assertEqual(initial['rules'],changed['rules'])
            self.assertEqual(2,changed['nextRuleKey'])
            self.commit(session,rule.replace('-2 -3','-1 -3'))
            self.assertEqual(3,session.command('objects')['gridSystems'][0]['nextRuleKey'])
            self.commit(session,'undo')
            self.assertEqual(changed,session.command('objects')['gridSystems'][0])
            self.commit(session,rule.replace('-2 -3','0 -3'))
            self.assertEqual([1,2],[row['ruleKey'] for row in session.command('objects')['gridSystems'][0]['rules']])

    def test_host_first_error_order_and_rejected_partial_cache_use_real_kernel(self):
        build=native();obj=build.compile(ROOT/'tests/geo261_grid_product_harness.c','grid-host-product',
            ['GEOMETRY_KERNEL_EXTERNAL=1','GEOMETRY_WOODWORKING_EXTERNAL=1','GEOMETRY_HOST_HISTORY_EXTERNAL=1','GEOMETRY_HOST_CANDIDATE_EXTERNAL=1'])
        exe=build.link('grid-host-product',[obj,*build.product_objects()])
        run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
        self.assertEqual(0,run.returncode,run.stderr)

    def test_parity_negative_control_changes_standalone_witness_and_actual_binding(self):
        build=native();self.assertEqual(0,self.case('binding-geometry'))
        self.assertEqual([560,731],self.binding_translation(build.bridge()))
        client,bridge=self.mutant('parity','binding->cell[1 - a] & 1','binding->cell[a] & 1')
        self.assertEqual(1,self.case('binding-geometry',client))
        self.assertEqual([573,738],self.binding_translation(bridge))
        self.assertEqual(0,self.case('binding-geometry'))
        self.assertEqual([560,731],self.binding_translation(build.bridge()))

    def zero_stagger(self,exe):
        with _bridge.BridgeSession(exe) as session:
            self.assertTrue(session.command('reset')['ok']);current=session.command('engineering-read')
            self.assertTrue(current['ok'],current)
            request={'schema':'engineering-transaction/1','expectedRevision':current['revision'],
                'operations':[{'op':'put-parameter','value':{'id':1,'name':'offset','fields':[
                    {'id':1,'name':'zero','type':'dimension','input':'0'}]}}]}
            path=native().work/'grid-store-zero-stagger.json';path.write_text(json.dumps(request),encoding='utf-8')
            preview=session.command('engineering-preview '+str(path))
            self.assertTrue(preview['ok'] and preview['preview']['valid'],preview)
            self.assertTrue(session.command('engineering-confirm '+str(preview['preview']['token']))['ok'])
            before=session.command('dump')['text']
            response=session.command('line '+source(5,'u','repeat 7 120 stagger param:1:1','repeat -11 80'))
            if 'preview' in response:
                # Implicit I8a previews use ok:false to say nothing was yet
                # committed. A valid preview still needs the real confirm path.
                self.assertEqual(before,session.command('dump')['text'])
                accepted=bool(response['preview']['valid'])
                if accepted:
                    confirmed=session.command('line confirm '+str(response['preview']['token']))
                    self.assertTrue(confirmed['ok'],confirmed)
            else:accepted=bool(response.get('ok'))
            if not accepted:self.assertEqual(before,session.command('dump')['text'])
            return accepted,response,session.command('objects')['gridSystems']

    def test_zero_stagger_negative_control_reaches_real_parameter_rebuild(self):
        build=native();self.assertEqual(0,self.case('stagger'))
        accepted,response,_=self.zero_stagger(build.bridge());self.assertFalse(accepted,response)
        self.assertIn('相位差為 0',rejection_reason(response))
        client,bridge=self.mutant('zero','if (a->stagger == 0) return geo_grid_error(error, GEO_GRID_STORE_STAGGER_ZERO);',
            'if (a->stagger == 0) return true;')
        self.assertEqual(1,self.case('stagger',client))
        accepted,response,systems=self.zero_stagger(bridge);self.assertTrue(accepted,response)
        self.assertEqual(0,systems[0]['uDefinition']['stagger'])
        self.assertEqual(0,self.case('stagger'))
        self.assertFalse(self.zero_stagger(build.bridge())[0])


if __name__=='__main__':unittest.main(verbosity=2)
