"""Actual same-process model envelope, exact roots and explicit partial coverage."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests.test_geo261_native_kernel import native
from tests.test_geo261_wood_product import SCENE

def encoded(value):
    return base64.b64encode(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).decode()

def parameter_scene():
    rows=['requires parameters/1','parameters begin','parameters card '+encoded({'id':8,'name':'typed','nextFieldId':4})]
    for identifier,kind,num,den in [(1,0,'7','2'),(2,1,'3','1'),(3,2,'1','3')]:
        rows.append('parameters field '+encoded({'parameterId':8,'id':identifier,'name':str(identifier),'type':kind,
            'expression':{'op':'literal','num':num,'den':den,'unit':'mm' if kind==0 else '1'}}))
    return '\n'.join(rows+['parameters end'])+'\n'

def profile_scene():
    values=[('profile',{'id':1,'name':'L','outline':[[0,0],[400,0],[400,60],[60,60],[60,250],[0,250]]}),
        ('member',{'id':4,'profileId':1,'kind':'timber','A':{'kind':'literal','value':27},'B':{'kind':'literal','value':33},'orientation':'A-u','u0':0,'v0':0}),
        ('run',{'id':1,'profileId':1,'length':{'kind':'literal','value':2400},'placement':None}),
        ('run',{'id':2,'profileId':1,'length':{'kind':'literal','value':2400},'placement':None})]
    return 'requires section-profile/1\n'+''.join('section-profile '+kind+' '+encoded(value)+'\n' for kind,value in values)

class ModelSources(unittest.TestCase):
    def execute(self,text,neutral=True,exe=None):
        build=native();path=build.work/'model-neutral.scene';path.write_text(text,encoding='utf-8')
        command=[str(exe or build.model_base())]+(['--neutral-sources'] if neutral else [])+[str(path)]
        run=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',timeout=30)
        self.assertEqual(0,run.returncode,run.stderr+'\n'+run.stdout)
        data=json.loads(run.stdout);self.assertTrue(data['ok'],data);return data

    @staticmethod
    def ref(ref):return ref['namespace'],base64.b64decode(ref['keyBase64'],validate=True)

    def nodes(self,envelope):
        nodes=envelope['neutralSources']['nodes'];result={self.ref(node['ref']):node for node in nodes}
        self.assertEqual(len(nodes),len(result));return result

    def test_legacy_payload_and_full_definition_identity_share_one_candidate(self):
        old=self.execute(SCENE,False);envelope=self.execute(SCENE)
        self.assertEqual('geometry-neutral-source-envelope/1',envelope['schema'])
        self.assertEqual(old,envelope['legacySnapshot'])
        candidate={'id':hashlib.sha256(old['base_scene'].encode()).hexdigest(),'baseRevision':0}
        self.assertEqual(candidate,envelope['candidate']);self.assertEqual(candidate,envelope['neutralSources']['candidate'])
        source_hash=hashlib.sha256(SCENE.replace('\n','\r\n').encode() if sys.platform=='win32' else SCENE.encode()).hexdigest()
        self.assertEqual({'sha256Before':source_hash,'sha256After':source_hash},envelope['source'])

    def test_source_graph_owns_exact_keys_and_exports_actual_guide_edges(self):
        envelope=self.execute(SCENE);bundle=envelope['neutralSources'];nodes=self.nodes(envelope)
        guide=[node for node in nodes.values() if node['ref']['namespace']=='app.guide']
        self.assertEqual(1,len(guide));self.assertEqual(500,guide[0]['value']['coordinate'])
        self.assertIn(b'\0',base64.b64decode(guide[0]['ref']['keyBase64']))
        self.assertTrue(any(edge['consumer']['namespace']=='app.guide' and edge['source']['namespace']=='app.legacy-reference' for edge in bundle['edges']))
        for edge in bundle['edges']:
            self.assertIn(self.ref(edge['consumer']),nodes);self.assertIn(self.ref(edge['source']),nodes)
        for root in bundle['roots']:self.assertEqual('ok',nodes[self.ref(root['ref'])]['status'])
        self.assertFalse(bundle['coverage']['complete']);self.assertTrue(bundle['coverage']['rootsComplete'])
        self.assertIn('grid-fields-and-bindings',bundle['coverage']['missingGroups'])

    def test_box_roots_keep_native_face_provenance_and_exact_extent(self):
        envelope=self.execute(SCENE);nodes=self.nodes(envelope)
        root=next(root for root in envelope['neutralSources']['roots'] if root['kind']=='timber')
        box=nodes[self.ref(root['ref'])]['value']
        self.assertEqual([0,0,0],box['lo']);self.assertEqual([1000,40,50],box['hi'])
        self.assertEqual(['A0','A1','B0','B1','START','END'],[face['legacyFeature'] for face in root['faces']])
        self.assertEqual([(2,0),(2,1),(1,0),(1,1),(0,0),(0,1)],[(face['axis'],face['side']) for face in root['faces']])
        self.assertEqual(6,len({base64.b64decode(face['featureKeyBase64']) for face in root['faces']}))
        self.assertEqual([face['feature'] for face in envelope['legacySnapshot']['solids'][0]['faces']],[face['legacyFeature'] for face in root['faces']])

    def test_region_roots_keep_holes_and_authored_vertex_identities(self):
        scene=('boundary 7 outline 0,0 1000,0 1000,1000 0,1000 hole 100,100 200,100 200,200 100,200\n'
               'placement 9 on boundary 7 origin 0 0 30 u +x v +y\n'
               'boundary-vertex-keys 7 outer 1 2 3 4 hole 5 6 7 8 next-key 9\n')
        envelope=self.execute(scene);nodes=self.nodes(envelope)
        root=next(root for root in envelope['neutralSources']['roots'] if root['slot']=='placement.region')
        components=nodes[self.ref(root['ref'])]['value']['components'];self.assertEqual(1,len(components))
        self.assertEqual([[1,2,3,4],[5,6,7,8]],components[0]['vertexKeys'])
        self.assertEqual([[[100,100],[200,100],[200,200],[100,200]]],components[0]['holes'])

    def test_parameter_quantities_retain_exact_fractions_and_field_types(self):
        envelope=self.execute(parameter_scene());nodes=self.nodes(envelope)
        fields={root['memberId']:nodes[self.ref(root['ref'])]['value'] for root in envelope['neutralSources']['roots'] if root['kind']=='parameter'}
        self.assertEqual({1:('dimension','7','2','length'),2:('count','3','1','scalar'),3:('ratio','1','3','scalar')},
            {key:(value['quantityType'],value['num'],value['den'],value['unit']) for key,value in fields.items()})

    def test_profile_envelope_and_members_keep_distinct_local_domains(self):
        envelope=self.execute(profile_scene());nodes=self.nodes(envelope)
        roots=envelope['neutralSources']['roots'];self.assertEqual(12,len(roots))
        frames={root['id']:nodes[self.ref(root['ref'])]['value'] for root in roots if root['slot']=='profile.frame' and root['memberId'] is None}
        self.assertEqual('local',frames[1]['coordinateDomain']);self.assertNotEqual(frames[1]['owner'],frames[2]['owner'])
        outline=next(nodes[self.ref(root['ref'])]['value']['components'][0]['outer'] for root in roots if root['slot']=='profile.region' and root['memberId'] is None)
        self.assertEqual([[0,0],[400,0],[400,60],[60,60],[60,250],[0,250]],outline)
        for root in roots:
            if root['slot']=='profile.length':self.assertEqual('2400',nodes[self.ref(root['ref'])]['value']['num'])

    def test_candidate_identity_changes_with_definitions_but_ignores_canvas_positions(self):
        original=self.execute(SCENE);moved=self.execute(SCENE+'canvas-pos placement 1 31 29\n')
        self.assertEqual(original['candidate'],moved['candidate'])
        changed=self.execute(SCENE.replace('spec x 500','spec x 501'))
        self.assertNotEqual(original['candidate'],changed['candidate'])

    def test_shared_kernel_cache_negative_control_changes_actual_model_transport(self):
        build=native();baseline=self.execute(parameter_scene());source=(build.kernel/'source.c').read_text(encoding='utf-8')
        before='node->value=value;node->state=GEO_NODE_VALID;node->status=GEO_SOURCE_OK;'
        self.assertEqual(1,source.count(before))
        after=before+'if(node->value.kind==GEO_SOURCE_QUANTITY&&node->value.as.quantity.unit==GEO_UNIT_SCALAR)++node->value.as.quantity.num;'
        path=build.work/'source-model-mutant.c';path.write_text(source.replace(before,after),encoding='utf-8')
        changed=build.compile(path,'source-model-mutant')
        product=build.link('model-base-source-mutant',[build.model_base_object,*[changed if obj==build.source_object else obj for obj in build.product_objects()]])
        mutated=self.execute(parameter_scene(),exe=product)
        self.assertEqual(baseline['legacySnapshot'],mutated['legacySnapshot'])
        def quantities(envelope):
            nodes=self.nodes(envelope)
            return {root['memberId']:nodes[self.ref(root['ref'])]['value']['num'] for root in envelope['neutralSources']['roots'] if root['kind']=='parameter'}
        self.assertEqual({1:'7',2:'3',3:'1'},quantities(baseline))
        self.assertEqual({1:'7',2:'4',3:'2'},quantities(mutated))
        self.assertEqual(quantities(baseline),quantities(self.execute(parameter_scene())))

if __name__=='__main__':unittest.main(verbosity=2)
