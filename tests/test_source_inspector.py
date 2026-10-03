"""F1a against the actual native bridge; no mocked reference extraction."""
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from tests._bridge import BridgeSession, find_bridge
from tests.test_assembly_rules import rule, binding


class SourceInspector(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='source-inspector-')
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.session = BridgeSession(find_bridge(), cwd=self.path)
        self.addCleanup(self.session.stop)
        self.command('reset')

    def command(self, command):
        return self.session.command(command)

    def line(self, line):
        result = self.command('line ' + line)
        if result.get('preview', {}).get('valid'):
            result = self.command('line confirm ' + str(result['preview']['token']))
        self.assertTrue(result['ok'], result)
        return result

    def apply(self, operations, assembly=False, confirm=True):
        request = {'schema': 'assembly-transaction/1' if assembly else 'engineering-transaction/1',
                   'expectedRevision': self.command('engineering-read')['revision'], 'operations': operations}
        path = self.path / 'request.json'
        path.write_text(json.dumps(request), encoding='utf-8')
        result = self.command(('assembly-preview ' if assembly else 'engineering-preview ') + str(path))
        self.assertTrue(result['ok'], result)
        self.assertTrue(result['preview']['valid'], result)
        if confirm:
            self.assertTrue(self.command(('assembly-confirm ' if assembly else 'engineering-confirm ') + str(result['preview']['token']))['ok'])
        return result['preview']['token']

    def graph(self):
        graph = self.command('source-inspect')
        self.assertTrue(graph['ok'], graph)
        self.assertTrue(graph['complete'], graph)
        self.assertEqual(len(graph['nodes']), len({n['key'] for n in graph['nodes']}))
        return graph

    def nodes(self):
        return {n['key']: n for n in self.graph()['nodes']}

    def snapshot(self, scene):
        path = self.path / 'snapshot.scene'
        path.write_text(scene, encoding='utf-8')
        return self.command('source-inspect-file ' + str(path))

    def card(self, value='600', name='Spacing'):
        return {'id': 0, 'name': name, 'fields': [{'id': 0, 'name': 'pitch', 'type': 'dimension', 'input': value}]}

    def generated(self):
        self.line('surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000')
        for line in ['timber 90 20 20 role boundary','place 90 on 1 at-face e0 +u +n','timber 91 20 20 role boundary','place 91 on 1 at-face e2 +u +n',
                     'spec pos1 500','guide 1 1 v spec:pos1','spec pos2 2500','guide 2 1 v spec:pos2','spec pos3 1500','guide 3 1 u spec:pos3']:
            self.line(line)
        value=binding()
        for slot in value['slots']:slot['orientation']='A'
        self.apply([{'op':'publish-rule','value':rule()},{'op':'create-binding','value':value}],assembly=True)
        state=self.command('assembly-read')['state']
        source={'id':1,'name':'native support source','bindingId':1,'rule':{'id':1,'version':1,'fingerprint':state['rules'][0]['fingerprint']},'surfaceId':1,
                'members':[{'memberId':m,'role':'primary' if m<3 else 'secondary','guideId':m,'dir':'+v' if m<3 else '+u','depthSide':'+n',
                            'ends':{'start':{'kind':'timber','id':91},'finish':{'kind':'timber','id':90}} if m<3 else {'start':{'kind':'member','memberId':1},'finish':{'kind':'member','memberId':2}}} for m in [1,2,3]]}
        request={'schema':'assembly-generation-transaction/1','expectedRevision':self.command('assembly-read')['revision'],
                 'operations':[{'op':'create-instance','value':source,'expectedBindingFingerprint':state['bindings'][0]['fingerprint']}]}
        path=self.path/'generation.json';path.write_text(json.dumps(request))
        result=self.command('assembly-generation-preview '+str(path));self.assertTrue(result['ok'],result);self.assertTrue(result['preview']['valid'],result)
        self.assertTrue(self.command('assembly-confirm '+str(result['preview']['token']))['ok'])

    def test_support_projection_is_atomic_with_independent_placed_zero_id_node_facts(self):
        self.line('surface 0 origin 0 0 2500 u +x v +y rect 0 0 4000 3000')
        self.line('timber 0 27 33 role boundary');self.line('place 0 on 0 at-face e0 +u +n');self.line('timber 55 27 33 role primary')
        graph=self.graph();refs=self.command('references');nodes={n['key']:n for n in graph['nodes']}
        self.assertEqual(refs['sourceFingerprint'],graph['sourceFingerprint']);self.assertEqual(refs['timberSupports'],graph['timberSupports'])
        self.assertEqual({'placed':True,'surface':0,'lengthAxis':'u','nativeOwner':None},{k:nodes['timber:0'][k] for k in ['placed','surface','lengthAxis','nativeOwner']})
        self.assertFalse(nodes['timber:55']['placed']);self.assertEqual([0],[e['id'] for e in graph['timberSupports']['entries']])
        entry=graph['timberSupports']['entries'][0]
        for end in ['start','finish']:
            self.assertEqual('exact',entry[end]['status']);self.assertEqual({'kind':'placement','id':0},entry[end]['relation']['source'])
        self.assertEqual('unknown',graph['supportStatus']);self.assertEqual('unknown',graph['identityContinuity'])

    def test_saved_world_support_hash_and_projection_do_not_borrow_live_world(self):
        self.line('surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000')
        self.line('timber 0 27 33 role boundary');self.line('place 0 on 1 at-face e0 +u +n')
        scene=self.command('dump')['text'];old=self.graph();self.line('spec unrelated 77');live=self.graph()
        saved=self.snapshot(scene);self.assertTrue(saved['ok'],saved);self.assertFalse(saved['live'])
        self.assertNotEqual(live['sourceFingerprint'],saved['sourceFingerprint']);self.assertEqual(old['sourceFingerprint'],saved['sourceFingerprint'])
        self.assertEqual(old['timberSupports'],saved['timberSupports']);self.assertEqual(live,self.graph())

    def test_owned_native_B0_B1_sources_pass_production_JS_and_reject_corrupt_provenance(self):
        self.generated();graph=self.graph();refs=self.command('references');nodes={n['key']:n for n in graph['nodes']}
        self.assertEqual(refs['timberSupports'],graph['timberSupports'])
        entries={e['id']:e for e in graph['timberSupports']['entries']}
        secondary=next(e for e in entries.values() if e['owner'] and e['owner']['memberId']==3)
        for end,face,member in [('start','B0',1),('finish','B1',2)]:
            relation=secondary[end]['relation'];self.assertEqual(face,relation['localFace']);self.assertEqual(member,relation['owner']['memberId'])
            self.assertEqual(nodes['timber:'+str(relation['source']['id'])]['nativeOwner'],relation['owner'])
        self.assertEqual(nodes['timber:'+str(secondary['id'])]['nativeOwner'],secondary['owner'])
        proof=os.environ.get('GEOMETRY_SOURCE_INSPECTOR_PROOF_DIR')
        if proof:
            output=Path(proof);output.mkdir(parents=True,exist_ok=True);(output/'native-owned-index.json').write_text(json.dumps(graph),encoding='utf-8')
        script=r"""
          const assert=require('node:assert/strict'),fs=require('node:fs');
          const S=require('./geometry-web/source-inspector.js'),data=JSON.parse(fs.readFileSync(0,'utf8'));
          const entry=data.timberSupports.entries.find(e=>e.owner?.memberId===3),key='timber:'+entry.id;
          const g=S.index(data);assert.equal(g.supportEntries.get(key).start.relation.localFace,'B0');assert.equal(g.supportEntries.get(key).finish.relation.localFace,'B1');
          assert.equal(g.supportEntries.get(key).start.relation.owner.memberId,1);assert(g.nodes.has('timber:90'));
          let rejected=0;
          for(const target of ['row','support'])for(const field of ['instanceId','memberId','bindingId','ruleId','ruleVersion','ruleFingerprint','instanceFingerprint','bindingFingerprint']){
            const bad=structuredClone(data),e=bad.timberSupports.entries.find(e=>e.id===entry.id),owner=target==='row'?e.owner:e.start.relation.owner;
            owner[field]=typeof owner[field]==='number'?999:'a'.repeat(64);assert.throws(()=>S.index(bad));rejected++;
          }
          for(const mutate of [e=>e.start.relation.source.id=999,e=>e.surface=0,e=>e.start.relation.localFace='min_u',e=>e.start.relation.stop.axis='v']){
            const bad=structuredClone(data);mutate(bad.timberSupports.entries.find(e=>e.id===entry.id));assert.throws(()=>S.index(bad));rejected++;
          }
          assert.equal(rejected,20);console.log('actual-native-shaped negative cases='+rejected);
        """
        result=subprocess.run(['node','-e',script],input=json.dumps(graph),cwd=Path(__file__).parents[1],text=True,capture_output=True)
        self.assertEqual(0,result.returncode,result.stderr)
        self.assertIn('negative cases=20',result.stdout)

    def test_legal_zero_card_field_placement_and_timber_namespaces(self):
        self.apply([{'op': 'put-parameter', 'value': self.card()}])
        self.line('surface 0 origin 0 0 2500 u +x v +y rect 0 0 4000 3000')
        self.line('guide 0 0 v param:0:0')
        self.line('timber 0 27 33 role boundary')
        self.line('place 0 on 0 at-face e0 +u +n')
        nodes = self.nodes()
        for key in ['parameter:0', 'parameter-field:0:f0', 'placement:0', 'guide:0', 'timber:0']:
            self.assertIn(key, nodes)
        edges = {(e['from'], e['to'], e['relation']) for e in self.graph()['edges']}
        self.assertIn(('guide:0', 'parameter-field:0:f0', 'dimension'), edges)
        self.assertIn(('timber:0', 'placement:0', 'position'), edges)

    def test_ast_refs_exact_ids_and_signed_grid_index_are_typed(self):
        self.apply([{'op':'put-parameter','value':self.card()}, {'op':'put-parameter','value':{'id':10,'name':'Spacing','fields':[{'id':0,'name':'derived','type':'dimension','input':'=@0:0 + 10 mm'}]}}])
        nodes = self.nodes()
        edges = self.graph()['edges']
        self.assertTrue(any(e['from']=='parameter-field:10:f0' and e['to']=='parameter-field:0:f0' for e in edges))
        self.assertNotEqual(nodes['parameter:0']['key'], nodes['parameter:10']['key'])
        self.line('surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000')
        self.line('grid-system 1 name-hex 67726964 main-along u u repeat 0 600 v repeat 0 500')
        fingerprint=self.command('boundary 1')['geometryFingerprint']
        self.line(f'grid-binding 1 on-boundary 1 from-system 1 vertex outer 0 geometry-hash {fingerprint} cell 0 0 anchor 0 1 0 1')
        self.line('grid 1 on 1 from-binding 1')
        self.line('guide 1 1 v grid:1:u:-1')
        self.assertTrue(any(e['from']=='guide:1' and e['to']=='grid:1' for e in self.graph()['edges']))

    def test_reads_and_snapshot_validation_preserve_world_revision_preview_and_history(self):
        self.apply([{'op':'put-parameter','value':self.card()}])
        before = self.command('dump')['text']
        revision = self.command('engineering-read')['revision']
        token = self.apply([{'op':'put-parameter','value':self.card('700')}], confirm=False)
        for _ in range(2):
            self.graph()
            self.assertTrue(self.snapshot(before)['ok'])
            self.assertFalse(self.snapshot('not-a-definition')['ok'])
        self.assertEqual(before, self.command('dump')['text'])
        self.assertEqual(revision, self.command('engineering-read')['revision'])
        # A read must leave the original pending candidate usable.
        self.assertTrue(self.command('engineering-confirm ' + str(token))['ok'])
        self.command('line undo')
        self.assertEqual(before, self.command('dump')['text'])

    def test_rename_move_unrelated_definition_do_not_change_relevant_fingerprints(self):
        self.apply([{'op':'put-parameter','value':self.card()}])
        initial = self.nodes()['parameter-field:0:f0']
        self.apply([{'op':'put-parameter','value':self.card(name='Renamed')}])
        self.line('canvas-pos parameter 0 22 33')
        self.line('spec unrelated 900')
        renamed = self.nodes()['parameter-field:0:f0']
        self.assertNotEqual(initial['label'], renamed['label'])
        self.assertEqual(initial['definitionFingerprint'], renamed['definitionFingerprint'])
        self.assertEqual(initial['valueFingerprint'], renamed['valueFingerprint'])
        self.apply([{'op':'put-parameter','value':self.card('700')}])
        changed = self.nodes()['parameter-field:0:f0']
        self.assertNotEqual(initial['valueFingerprint'], changed['valueFingerprint'])

    def test_fixed_material_and_rule_versions_and_binding_sources_survive_replay(self):
        self.apply([{'op':'publish-material','value':{'id':'wood','version':v,'name':'Same','kind':'timber','A':27,'B':33}} for v in [1,2]])
        b = binding();b['slots'][0]['A']={'kind':'material','id':'wood','version':1,'field':'A'}
        self.apply([{'op':'publish-rule','value':rule()},{'op':'create-binding','value':b}], assembly=True)
        edges = self.graph()['edges']
        self.assertTrue(any(e['from']=='assembly-binding:1' and e['to']=='assembly-rule:1:v1' for e in edges))
        self.assertTrue(any(e['from']=='assembly-binding:1' and e['to']=='material:wood:v1' for e in edges))
        self.assertFalse(any(e['from']=='assembly-binding:1' and e['to']=='material:wood:v2' for e in edges))
        self.assertTrue(any(e['from']=='assembly-rule:1:v1' and e['relation']=='joint-definition' for e in edges))
        self.assertTrue(any(e['from']=='assembly-rule:1:v1' and e['to'].startswith('assembly-member:1:v1') for e in edges))
        old = self.graph();saved=self.snapshot(self.command('dump')['text'])
        self.assertEqual(old['nodes'], saved['nodes'])
        self.assertEqual(old['edges'], saved['edges'])
        self.assertEqual('unknown', saved['identityContinuity'])

    def test_application_field_tracks_exact_resolution_without_unrelated_overrides(self):
        self.line('surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000')
        self.line('spec size 27')
        app={'id':'frame','placement_id':1,'method':{'id':'method','version':1},'overrides':{'boundary.A':{'kind':'spec','name':'size'}}}
        self.apply([
            {'op':'publish-material','value':{'id':'wood','version':1,'name':'Wood','kind':'timber','A':27,'B':33}},
            {'op':'publish-method','value':{'id':'method','version':1,'name':'Frame','roles':{'boundary':{'id':'wood','version':1}}}},
            {'op':'put-application','value':app}])
        self.line('timber 0 27 33 role boundary');self.line('place 0 on 1 at-face e0 +u +n')
        self.apply([{'op':'bind-timber','id':0,'application':'frame','slot':'boundary'}])
        graph=self.graph();old={n['key']:n for n in graph['nodes']}
        self.assertTrue(any(e['from']=='timber:0' and e['to']=='application-field:frame:f8' for e in graph['edges']))
        self.assertTrue(any(e['from']=='application-field:frame:f8' and e['to']=='spec:size' for e in graph['edges']))
        changed=deepcopy(app);changed['overrides']['primary.A']={'kind':'literal','value':29}
        self.apply([{'op':'put-application','value':changed}])
        self.assertEqual(old['application-field:frame:f8'],self.nodes()['application-field:frame:f8'])
        before=self.nodes()['timber:0']
        self.line('spec size 28')
        after=self.nodes()['timber:0']
        self.assertEqual(before['definitionFingerprint'],after['definitionFingerprint'])
        self.assertNotEqual(before['valueFingerprint'],after['valueFingerprint'])

    def test_snapshot_transport_bounds_encoding_and_cleans_its_owned_file(self):
        spec=importlib.util.spec_from_file_location('source_inspector_transport',Path(__file__).parents[1]/'geometry-web/source_inspector_transport.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        before=self.command('dump')['text'];paths=[]
        def bridge(command):
            path=Path(command.split(' ',1)[1]);paths.append(path)
            self.assertTrue(path.is_file())
            return json.dumps(self.command(command)).encode()
        self.assertTrue(json.loads(module.snapshot_request(before.encode(),bridge))['ok'])
        self.assertFalse(paths[0].exists())
        for body,code in [(b'\xff','ENCODING'),(b'\0','ENCODING'),(b'x'*(module.MAX_BYTES+1),'CAPACITY')]:
            self.assertEqual(code,json.loads(module.snapshot_request(body,bridge))['code'])
        self.assertEqual(1,len(paths));self.assertEqual(before,self.command('dump')['text'])

    def test_grid_parameter_value_changes_do_not_invent_a_new_definition(self):
        self.apply([{'op':'put-parameter','value':self.card()}])
        self.line('surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000')
        self.line('grid-system 0 name-hex 47726964 main-along none u repeat 0 param:0:0 v repeat 0 500')
        fingerprint=self.command('boundary 1')['geometryFingerprint']
        self.line(f'grid-binding 0 on-boundary 1 from-system 0 vertex outer 0 geometry-hash {fingerprint} cell 0 0 anchor 0 1 0 1')
        self.line('grid 0 on 1 from-binding 0')
        before=self.nodes()
        self.apply([{'op':'put-parameter','value':self.card('700')}])
        after=self.nodes()
        for key in ['grid-system:0','grid:0']:
            self.assertEqual(before[key]['definitionFingerprint'],after[key]['definitionFingerprint'])
            self.assertNotEqual(before[key]['valueFingerprint'],after[key]['valueFingerprint'])

    def test_same_value_source_change_override_and_delete_are_not_guessed(self):
        self.apply([{'op':'put-parameter','value':self.card('27')}])
        self.line('surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000')
        self.line('timber 0 27 33 role boundary');self.line('place 0 on 1 at-face e0 +u +n')
        old=self.nodes()['timber:0']
        self.apply([{'op':'set-source','target':{'kind':'timber','id':0,'field':'A'},'source':{'kind':'parameter','parameterId':0,'fieldId':0}}])
        new=self.nodes()['timber:0']
        self.assertNotEqual(old['definitionFingerprint'],new['definitionFingerprint'])
        self.assertEqual(old['valueFingerprint'],new['valueFingerprint'])
        self.apply([{'op':'set-override','target':{'kind':'timber','id':0,'field':'A'},'value':{'kind':'literal','value':27}}])
        edge=next(e for e in self.graph()['edges'] if e['from']=='timber:0' and e['to']=='parameter-field:0:f0')
        self.assertFalse(edge['active'])
        self.line('delete timber 0')
        self.assertNotIn('timber:0',self.nodes())
        self.line('timber 0 27 33 role boundary');self.line('place 0 on 1 at-face e0 +u +n')
        self.assertFalse(any(e['from']=='timber:0' and e['to']=='parameter-field:0:f0' for e in self.graph()['edges']))

    def test_candidate_timber_is_not_reported_as_confirmed_support(self):
        self.line('surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000')
        for identifier,edge in [(0,'e0'),(1,'e2')]:
            self.line(f'timber {identifier} 27 33 role boundary');self.line(f'place {identifier} on 1 at-face {edge} +u +n')
        graph=self.graph()
        self.assertEqual('unknown',graph['supportStatus'])
        self.assertTrue(any(e['from']=='timber:1' and e['to']=='timber:0' and e['relation']=='span-candidate' for e in graph['edges']))


if __name__ == '__main__':
    unittest.main()
