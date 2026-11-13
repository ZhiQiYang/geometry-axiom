"""Same-candidate enclosure consumption and unchanged partial-space semantics."""
import base64
from pathlib import Path
import struct
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests.test_geo261_native_kernel import native
from tests import test_geo261_model_sources as model_sources

SCENE=('boundary 7 outline 0,0 100,0 100,200 0,200\n'
       'placement 9 on boundary 7 origin 10 20 330 u +x v +y\n'
       'space 5 boundary 7\n')


class EnclosureProductBoundary(unittest.TestCase):
    def test_h_keeps_raw_parser_probe_and_shared_source_rebuild_distinct(self):
        adapter=(ROOT/'geometry-app/native/enclosure_sources.inc').read_text(encoding='utf-8')
        main=(ROOT/'current_geometry.c').read_bytes().replace(b'\r\n',b'\n').decode('utf-8')
        self.assertIn('stored->member_count==count',adapter)
        self.assertIn('geo_enclosure_sources_value(ctx->enclosure_sources,id,out,fault)',adapter)
        self.assertIn('return handled?ok:geo_enclosure_evaluate(',main)
        self.assertIn('app_enclosure_sources_complete(&state->reference)',
                      (ROOT/'geometry-app/native/model_sources.inc').read_text(encoding='utf-8'))


class EnclosureProduct(unittest.TestCase):
    execute=model_sources.ModelSources.execute
    ref=staticmethod(model_sources.ModelSources.ref)
    nodes=model_sources.ModelSources.nodes

    @staticmethod
    def source(kind,identifier,axis=-1,slot=-1):
        return 'core.enclosure',bytes([kind])+struct.pack('>I',identifier)+bytes([axis+1,slot+1])

    def test_partial_and_unused_empty_definitions_have_exact_result_values(self):
        envelope=self.execute(SCENE+'space 6\n')
        nodes=self.nodes(envelope)
        for identifier,members,bounds in ((5,[7],[10,20,0,110,220,330]),(6,[],[0]*6)):
            definition=nodes[self.source(1,identifier)]
            result=nodes[self.source(2,identifier)]
            prefix=struct.pack('>II',identifier,len(members))+b''.join(struct.pack('>I',x) for x in members)
            self.assertEqual('scalar',definition['descriptor']['unit'])
            self.assertEqual('geo.enclosure.members/1',definition['value']['schema'])
            self.assertEqual(prefix,base64.b64decode(definition['value']['contentBase64'],validate=True))
            self.assertEqual('geo.enclosure.result/1',result['value']['schema'])
            self.assertEqual(prefix+struct.pack('>6qB',*bounds,0),
                             base64.b64decode(result['value']['contentBase64'],validate=True))
        self.assertTrue(all(root['kind']!='space' for root in envelope['neutralSources']['roots']))

    def test_actual_slot_and_result_depend_on_member_region_and_placement_frame(self):
        envelope=self.execute(SCENE);nodes=self.nodes(envelope)
        slots={ref:node for ref,node in nodes.items() if ref[0]=='core.enclosure' and ref[1][0]==3}
        self.assertEqual({self.source(3,5,2,1)},set(slots))
        self.assertEqual(330,slots[self.source(3,5,2,1)]['value']['coordinate'])
        edges={(self.ref(edge['consumer']),self.ref(edge['source']),edge['kind'])
               for edge in envelope['neutralSources']['edges']}
        result=self.source(2,5)
        self.assertIn((result,self.source(1,5),'definition-required'),edges)
        self.assertIn((result,('core.region',struct.pack('>I',7)),'value-required'),edges)
        frame=('core.placement',bytes([1])+struct.pack('>I',9))
        self.assertIn((result,frame,'value-required'),edges)
        self.assertIn((self.source(3,5,2,1),frame,'value-required'),edges)

    def build_client(self):
        build=native()
        client=build.compile(ROOT/'tests/geo261_enclosure_product_harness.c','enclosure-product',
            ['GEOMETRY_KERNEL_EXTERNAL=1','GEOMETRY_WOODWORKING_EXTERNAL=1',
             'GEOMETRY_HOST_HISTORY_EXTERNAL=1','GEOMETRY_HOST_CANDIDATE_EXTERNAL=1'])
        path=build.work/'enclosure-product.scene';path.write_text(SCENE,encoding='utf-8')
        return build,client,path

    def run_client(self,executable,path,marker=None):
        result=subprocess.run([str(executable),str(path)],capture_output=True,text=True,encoding='utf-8',timeout=30)
        self.assertEqual(1 if marker else 0,result.returncode,result.stdout+'\n'+result.stderr)
        expected='I8a preview 1: valid; confirm token to apply\n'
        if marker:expected+='ASSERT:'+marker+'\n'
        self.assertEqual(expected,result.stderr)

    def test_real_preview_rebuild_confirm_and_undo_retain_enclosure_graph(self):
        build,client,path=self.build_client()
        executable=build.link('enclosure-product',[client,*build.product_objects()])
        self.run_client(executable,path)

    def test_changed_kernel_result_is_observed_by_actual_space_cache(self):
        build,client,path=self.build_client()
        executable=build.link('enclosure-product-control-baseline',[client,*build.product_objects()])
        self.run_client(executable,path)
        source=(build.kernel/'enclosure_sources.c').read_text(encoding='utf-8')
        before='return value.kind==GEO_SOURCE_DEFINITION&&\n        geo_enclosure_source_decode_definition(GEO_ENCLOSURE_SOURCE_RESULT,&value.as.definition,id,out);'
        self.assertEqual(1,source.count(before),'Control must target the actual K result accessor')
        changed=build.kernel/'enclosure-result-product-control.c'
        changed.write_text(source.replace(before,
            'if(value.kind!=GEO_SOURCE_DEFINITION||!geo_enclosure_source_decode_definition(GEO_ENCLOSURE_SOURCE_RESULT,&value.as.definition,id,out))return false;if(out->id==5&&out->max[2]==340)++out->max[2];return true;'),encoding='utf-8')
        obj=build.compile(changed,'enclosure-result-product-control')
        self.assertEqual(1,build.product_objects().count(build.enclosure_sources_object))
        mutant=build.link('enclosure-result-product-control',[client,
            *[obj if x==build.enclosure_sources_object else x for x in build.product_objects()]])
        self.run_client(mutant,path,'space-result-applied')
        self.run_client(executable,path)


if __name__=='__main__':unittest.main(verbosity=2)
