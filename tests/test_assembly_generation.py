"""AR06 generation uses real C candidates, ownership and fresh scene replay."""
from copy import deepcopy
import base64
import json
from pathlib import Path
import tempfile
import unittest
from tests._bridge import BridgeSession,find_bridge
from tests.test_assembly_rules import rule,binding

class Generation(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='assembly-generation-');self.addCleanup(self.temp.cleanup)
        self.directory=Path(self.temp.name);self.bridge=BridgeSession(find_bridge(),cwd=self.directory);self.addCleanup(self.bridge.stop)
        self.command('reset')
        for line in ['surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000','spec position1 500','spec position2 2500','spec position3 1500','guide 1 1 v spec:position1','guide 2 1 v spec:position2','guide 3 1 u spec:position3','timber 90 20 20 role boundary','place 90 on 1 at-face e0 +u +n','timber 91 20 20 role boundary','place 91 on 1 at-face e2 +u +n']:
            self.line(line)
        value=binding()
        for slot in value['slots']:slot['orientation']='A'
        self.apply([{'op':'publish-rule','value':rule()},{'op':'create-binding','value':value}],False)
    def command(self,c):return self.bridge.command(c)
    def line(self,c):
        result=self.command('line '+c)
        if result.get('preview',{}).get('valid'):result=self.command('line confirm '+str(result['preview']['token']))
        self.assertTrue(result.get('ok'),result);return result
    def read(self):return self.command('assembly-read')
    def dump(self):return self.command('dump')['text']
    def request(self,operations,generation=True):
        p=self.directory/'transaction.json';p.write_text(json.dumps({'schema':'assembly-generation-transaction/1' if generation else 'assembly-transaction/1','expectedRevision':self.read()['revision'],'operations':operations}))
        return self.command(('assembly-generation-preview ' if generation else 'assembly-preview ')+str(p))
    def apply(self,operations,generation=True):
        r=self.request(operations,generation);self.assertTrue(r.get('ok'),r);self.assertTrue(r['preview']['valid'],r)
        done=self.command('assembly-confirm '+str(r['preview']['token']));self.assertTrue(done.get('ok'),done);return done
    def source(self,id=1):
        r=self.read()['state']['rules'][0]
        return {'id':id,'name':'two primary and cross','bindingId':1,'rule':{'id':1,'version':1,'fingerprint':r['fingerprint']},'surfaceId':1,'members':[{'memberId':i,'role':'primary' if i<3 else 'secondary','guideId':i,'dir':'+v' if i<3 else '+u','depthSide':'+n','ends':{'start':{'kind':'timber','id':90},'finish':{'kind':'timber','id':91}} if i<3 else {'start':{'kind':'member','memberId':1},'finish':{'kind':'member','memberId':2}}} for i in [1,2,3]]}
    def create(self,value=None):return {'op':'create-instance','value':value or self.source(),'expectedBindingFingerprint':self.read()['state']['bindings'][0]['fingerprint']}
    def instance(self):return self.read()['state']['instances'][0]
    def edit(self,value=None):
        a=self.instance();return {'op':'edit-instance','id':a['value']['source']['id'],'value':value or a['value']['source'],'expectedFingerprint':a['fingerprint'],'expectedBindingFingerprint':self.read()['state']['bindings'][0]['fingerprint']}
    def reject(self,ops,message,generation=True):
        before=self.dump();r=self.request(ops,generation);self.assertTrue(r.get('ok'),r);self.assertFalse(r['preview']['valid'],r);self.assertIn(message,'\n'.join(v.get('message','') for v in r['preview']['violations']));self.assertEqual(before,self.dump());self.assertFalse(self.command('assembly-confirm '+str(r['preview']['token']))['ok'])
    def test_preview_then_create_exact_three_native_timbers(self):
        before=self.dump();r=self.request([self.create()]);self.assertTrue(r['preview']['valid'],r);self.assertEqual(before,self.dump());self.assertEqual([],r['preview']['before']['instances'])
        self.assertEqual([2960,2960,1973],[m['geometry']['length'] for m in r['preview']['after']['instances'][0]['members']]);self.assertTrue(self.command('assembly-confirm '+str(r['preview']['token']))['ok'])
        a=self.instance();self.assertEqual(3,len(set(m['timberId'] for m in a['members'])));self.assertEqual(5,len(self.command('references')['timbers']));self.assertIn('owned 1 3 place',self.dump())
        self.assertEqual([0,0,1],a['members'][0]['geometry']['axes'][2])
    def test_cancel_stale_confirm_and_current_revision_stale_instance(self):
        self.apply([self.create()]);before=self.dump();op=self.edit(dict(self.instance()['value']['source'],name='trial'));r=self.request([op]);self.command('assembly-cancel '+str(r['preview']['token']));self.assertEqual(before,self.dump())
        r=self.request([op]);self.line('spec unrelated 2');self.assertFalse(self.command('assembly-confirm '+str(r['preview']['token']))['ok']);self.assertEqual('two primary and cross',self.instance()['value']['source']['name'])
        self.apply([op]);self.reject([op],'STALE')
    def test_two_section_and_position_configurations_recompute_all_members(self):
        self.apply([self.create()]);mapping=self.instance()['value']['mapping'];b=self.read()['state']['bindings'][0];value=deepcopy(b['value'])
        for slot in value['slots']:slot['A']['value']=40;slot['B']['value']=50
        self.apply([{'op':'edit-binding','id':1,'expectedFingerprint':b['fingerprint'],'value':value}],False);self.line('spec position2 2800')
        a=self.instance();self.assertEqual(mapping,a['value']['mapping']);self.assertEqual([2960,2960,2260],[m['geometry']['length'] for m in a['members']]);self.assertTrue(all(m['geometry']['A']==40 and m['geometry']['B']==50 and m['geometry']['side']=='+n' for m in a['members']))
    def test_reorder_rename_keeps_member_to_timber_mapping(self):
        self.apply([self.create()]);before={m['memberId']:m['timberId'] for m in self.instance()['members']};v=deepcopy(self.instance()['value']['source']);v['members'].reverse();v['name']='renamed';self.apply([self.edit(v)]);self.assertEqual(before,{m['memberId']:m['timberId'] for m in self.instance()['members']})
    def test_primary_support_selectors_follow_unordered_r21_not_physical_end_labels(self):
        self.apply([self.create()])
        before=deepcopy(self.instance())
        value=deepcopy(before['value']['source'])
        for member in value['members'][:2]:
            member['ends']['start'],member['ends']['finish']=member['ends']['finish'],member['ends']['start']
        self.apply([self.edit(value)])
        after=self.instance()
        self.assertEqual(before['value']['mapping'],after['value']['mapping'])
        self.assertEqual([m['geometry'] for m in before['members']],[m['geometry'] for m in after['members']])
        self.assertEqual(91,after['value']['source']['members'][0]['ends']['start']['id'])
        self.assertEqual(20,after['members'][0]['geometry']['origin'][1])
    def test_missing_wrong_sources_and_inward_joint_geometry_are_atomic(self):
        for change,diagnostic in [('guide','I42'),('surface','I42'),('support','I42'),('side','I42')]:
            v=self.source()
            if change=='guide':v['members'][0]['guideId']=999
            elif change=='surface':v['surfaceId']=999
            elif change=='support':v['members'][0]['ends']['start']['id']=999
            else:v['members'][0]['guideId']=2;v['members'][1]['guideId']=1
            self.reject([self.create(v)],diagnostic)
    def test_unsupported_section_orientation_and_joint_topology(self):
        b=self.read()['state']['bindings'][0];v=deepcopy(b['value']);v['slots'][0]['orientation']='B';self.apply([{'op':'edit-binding','id':1,'expectedFingerprint':b['fingerprint'],'value':v}],False);self.reject([self.create()],'UNSUPPORTED')
        v=self.source();v['members'][0]['dir']='-v';self.reject([self.create(v)],'UNSUPPORTED')
    def test_unselected_sources_report_i42_and_preserve_world_on_create_and_edit(self):
        for edit in [False,True]:
            if edit:self.apply([self.create()])
            for field in ['surface','primary-guide','secondary-guide','start-support','finish-support']:
                with self.subTest(edit=edit,field=field):
                    value=deepcopy(self.instance()['value']['source']) if edit else self.source()
                    if field=='surface':value['surfaceId']=0
                    elif field.endswith('guide'):value['members'][2 if field=='secondary-guide' else 0]['guideId']=0
                    else:value['members'][0]['ends'][field.split('-')[0]]['id']=0
                    self.reject([self.edit(value) if edit else self.create(value)],'I42:')
    def test_owned_members_refuse_native_place_delete_dimensions_and_record_ingress(self):
        self.apply([self.create()]);tid=self.instance()['members'][0]['timberId'];before=self.dump()
        for c in [f'timber {tid} 40 50 role primary',f'place {tid} on 1 at-line guide 1 +v +n',f'delete timber {tid}',f'owned 1 1 timber {tid} 40 50 role primary']:
            self.assertFalse(self.command('line '+c)['ok'],c);self.assertEqual(before,self.dump())
        self.reject([{'op':'set-source','target':{'kind':'timber','id':tid,'field':'A'},'source':{'kind':'literal','value':40}}],'I42',False)
    def test_roundtrip_preserves_sources_mapping_and_geometry_in_fresh_process(self):
        self.apply([self.create()]);scene=self.dump();p=self.directory/'saved.scene';p.write_text(scene)
        with BridgeSession(find_bridge(),cwd=self.directory) as fresh:
            r=fresh.command('loadfile '+str(p));self.assertTrue(r['ok'],r);self.assertEqual(scene,fresh.command('dump')['text']);self.assertEqual(self.read()['state'],fresh.command('assembly-read')['state'])
    def test_scene_stripped_capability_or_owned_source_changes_refuse_repair(self):
        self.apply([self.create()]);scene=self.dump()
        for altered in [scene.replace('requires assembly-timber-generation/1\n',''),scene.replace('owned 1 1 timber 1 27 33','owned 1 1 timber 1 40 33'),scene.replace('owned 1 1 timber','owned 1 99 timber')]:
            p=self.directory/'bad.scene';p.write_text(altered);r=self.command('loadfile '+str(p));self.assertFalse(r['ok'],r);self.assertEqual(scene,self.dump())
    def test_delete_external_consumer_guard_and_native_undo_redo(self):
        self.apply([self.create()]);tid=self.instance()['members'][0]['timberId'];self.line(f'guide 4 1 v timber:{tid}:u:lo');a=self.instance();op={'op':'delete-instance','id':1,'expectedFingerprint':a['fingerprint']};self.reject([op],'I9')
        self.line('delete guide 4');before=self.dump();self.apply([op]);self.assertEqual([],self.read()['state']['instances']);self.assertEqual(2,len(self.command('references')['timbers']));self.command('line undo');self.assertEqual(before,self.dump());self.command('line redo');self.assertEqual([],self.read()['state']['instances'])
    def test_binding_revision_and_guarded_create_reject_duplicates_and_wrong_hash(self):
        v=self.create();v['expectedBindingFingerprint']='0'*64;self.reject([v],'STALE');self.apply([self.create()]);self.reject([self.create()],'already exists');op=self.edit();op['expectedFingerprint']='g'*64;self.reject([op],'I42')
    def test_parameter_source_update_recomputes_without_reallocating(self):
        self.apply([{'op':'put-parameter','value':{'id':1,'name':'section','fields':[{'id':1,'name':'width','type':'dimension','input':'27'}]}}],False)
        b=self.read()['state']['bindings'][0];v=deepcopy(b['value'])
        for slot in v['slots']:slot['A']={'kind':'parameter','parameterId':1,'fieldId':1}
        self.apply([{'op':'edit-binding','id':1,'expectedFingerprint':b['fingerprint'],'value':v}],False);self.apply([self.create()]);mapping=self.instance()['value']['mapping']
        self.apply([{'op':'put-parameter','value':{'id':1,'name':'section','fields':[{'id':1,'name':'width','type':'dimension','input':'40'}]}}],False)
        self.assertEqual(mapping,self.instance()['value']['mapping']);self.assertEqual(1960,self.instance()['members'][2]['geometry']['length'])
    def test_explicit_version_upgrade_retains_members_and_does_not_auto_upgrade(self):
        self.apply([self.create()]);mapping=self.instance()['value']['mapping'];newer=rule();newer['version']=2;newer['name']='version two';self.apply([{'op':'publish-rule','value':newer}],False)
        self.assertEqual(1,self.instance()['value']['source']['rule']['version'])
        b=deepcopy(self.read()['state']['bindings'][0]['value']);b['id']=2;b['rule']['version']=2;self.apply([{'op':'create-binding','value':b}],False)
        value=deepcopy(self.instance()['value']['source']);r=self.read()['state']['rules'][1];value['bindingId']=2;value['rule']={'id':1,'version':2,'fingerprint':r['fingerprint']};op=self.edit(value);op['expectedBindingFingerprint']=self.read()['state']['bindings'][1]['fingerprint'];self.apply([op])
        self.assertEqual(mapping,self.instance()['value']['mapping']);self.assertEqual(2,self.instance()['value']['source']['rule']['version'])
    def test_member_identity_role_and_self_dependency_changes_reject(self):
        self.apply([self.create()])
        for change in ['member','role','self']:
            value=deepcopy(self.instance()['value']['source'])
            if change=='member':value['members'][0]['memberId']=99
            elif change=='role':value['members'][0]['role']='secondary'
            else:value['members'][2]['ends']['start']['memberId']=3
            self.reject([self.edit(value)],'UNSUPPORTED')
    def test_capacity_is_checked_before_any_partial_creation(self):
        self.reject([self.create(self.source(i)) for i in range(1,18)],'CAPACITY');self.assertEqual([],self.read()['state']['instances'])
    def test_source_change_collision_rejects_entire_world(self):
        self.apply([self.create()]);before=self.dump();r=self.command('line spec position2 500');self.assertFalse(r.get('ok') and not r.get('preview'),r)
        if r.get('preview'):self.assertFalse(r['preview']['valid']);self.assertFalse(self.command('line confirm '+str(r['preview']['token']))['ok'])
        self.assertEqual(before,self.dump())

if __name__=='__main__':unittest.main()
