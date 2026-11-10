"""R362: real producer replay for saved identity records and ordered faces."""
from copy import deepcopy
import json, os
from pathlib import Path
import unittest
from tests import test_model_update as original
from tests.test_model_update import scene, update, space_modeling, load_base, canonical_bytes, ModelError

ROOT=Path(__file__).resolve().parents[1]

class ModelIdentityFaces(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original.ModelUpdate.setUpClass()
        cls.native=original.ModelUpdate.native; cls.base=original.ModelUpdate.base
        cls.old=deepcopy(original.ModelUpdate.old)
        fixture=json.loads((ROOT/'geometry-core/modeling-cases.json').read_text())
        data=next(x for x in fixture['cases'] if x['id']=='l_room_eight_faces')['definitions']
        cls.faceScene=load_base(data['base_scene'],executable=cls.base)['base_scene']
        cls.uses=deepcopy(next(x for x in data['extensions'] if x['kind']=='shell')['uses'])
        cls.uses[-1]['purpose']='calculation-cap'
        inputs={'mode':'faces','base_scene':cls.faceScene,'uses':cls.uses,'obstacles':[]}
        result=space_modeling.preview(inputs,base_executable=cls.base)
        cls.faces={'id':'faces-original','name':'八面模型','created_at':'2026-11-03T01:00:00.000Z',
            'source':{'kind':'scene','placement_id':None,'boundary_id':None,'scene_hash':result['source_sha256']},'input':inputs,'result':result}

    def prepare(self,record,selection,current=None):
        data={'record':deepcopy(record),'selection':deepcopy(selection),'current_scene':current or record['input']['base_scene']}
        before=canonical_bytes(data)
        candidate=update.prepare_update(data,**self.native)
        self.assertEqual(canonical_bytes(data),before,'R362_PRODUCER_NO_INPUT_WRITE')
        return candidate

    def selection(self):
        return {'mode':'faces','uses':[{'placement_id':u['placement_id']} for u in self.uses],'obstacles':[]}

    def test_identified_plan_record_reaches_real_native_replay(self):
        old=deepcopy(self.old)
        old['sourceIdentity']={'schema':'model-source-identity/1','roots':[
            {'role':'placement','kind':'placement','id':1,'fieldId':0,'incarnation':'1'*32+':1'},
            {'role':'boundary','kind':'boundary','id':1,'incarnation':'1'*32+':2'},
            {'role':'timber','kind':'timber','id':0,'incarnation':'1'*32+':3'}]}
        request=original.ModelUpdate().request(record=old)
        try: candidate=self.prepare(old,request['selection'],request['current_scene'])
        except ModelError as error: self.fail('R362_SOURCE_IDENTITY_REPLAY: '+error.code)
        self.assertEqual(candidate['record']['id'],old['id'])
        self.assertEqual(candidate['record']['result']['summary']['timber_volume_mm3'],str(4000*29*33))
        self.assertNotIn('sourceIdentity',candidate['record'],'producer cannot invent current ledger pins')

    def test_faces_full_replay_keeps_order_orientation_purpose_and_model_id(self):
        try: candidate=self.prepare(self.faces,self.selection())
        except ModelError as error: self.fail('R362_FACES_REPLAY: '+error.code)
        self.assertEqual(candidate['record']['id'],self.faces['id'])
        self.assertEqual(candidate['record']['input']['uses'],self.uses)
        self.assertEqual(candidate['record']['result'],self.faces['result'])
        self.assertEqual(candidate['record']['result']['summary']['volume_mm3'],'68040000000')
        self.assertEqual(candidate['selection'],self.selection())

    def test_faces_changed_source_recomputes_complete_packages(self):
        current=self.faceScene.replace('2800','3000')
        self.assertNotEqual(current,self.faceScene)
        try: candidate=self.prepare(self.faces,self.selection(),current)
        except ModelError as error: self.fail('R362_FACES_CHANGED_REPLAY: '+error.code)
        changed=candidate['record']
        self.assertNotEqual(changed['result']['source_sha256'],self.faces['result']['source_sha256'])
        self.assertEqual(changed['input']['uses'],self.uses)
        self.assertEqual(changed['result'],space_modeling.preview(changed['input'],base_executable=self.base))
        self.assertNotEqual(changed['result']['summary']['volume_mm3'],self.faces['result']['summary']['volume_mm3'])

    def test_faces_invalid_count_duplicates_and_injected_orientation_are_rejected(self):
        try:update._selection({'mode':'faces','uses':[{'placement_id':i} for i in range(17)],'obstacles':[]})
        except ModelError as error:self.fail('R362_FACE_CAPACITY_CONTRACT: '+error.code)
        variants=[]
        missing=self.selection();missing['uses'].pop();variants.append(missing)
        duplicate=self.selection();duplicate['uses'][1]=deepcopy(duplicate['uses'][0]);variants.append(duplicate)
        orientation=self.selection();orientation['uses'][0]['orientation']=-self.uses[0]['orientation'];variants.append(orientation)
        for selection in variants:
            with self.subTest(selection=selection),self.assertRaises(ModelError): self.prepare(self.faces,selection)

    def test_faces_cannot_sneak_timbers_into_the_selection(self):
        selection=self.selection();selection['timbers']=[]
        with self.assertRaises(ModelError):self.prepare(self.faces,selection)

    def test_source_identity_schema_is_validated_before_any_replay(self):
        old=deepcopy(self.old);old['sourceIdentity']={'schema':'model-source-identity/1','roots':[]}
        request=original.ModelUpdate().request(record=old)
        with self.assertRaises(ModelError):self.prepare(old,request['selection'],request['current_scene'])

    def test_faces_saved_identity_accepts_exact_roots_and_rejects_overflow_or_wrong_key(self):
        old=deepcopy(self.faces)
        old['sourceIdentity']={'schema':'model-source-identity/1','roots':[
            {'role':'use','kind':'placement','id':u['placement_id'],'incarnation':'a'*32+':'+str(i+1)}
            for i,u in enumerate(old['input']['uses'])]}
        try:candidate=self.prepare(old,self.selection())
        except ModelError as error:self.fail('R362_FACES_IDENTIFIED_REPLAY: '+error.code)
        self.assertEqual(candidate['record']['result'],old['result'])
        for changes in [{'incarnation':'a'*32+':18446744073709551616'},{'id':99},{'fieldId':1},{'role':[]},{'incarnation':None}]:
            invalid=deepcopy(old);invalid['sourceIdentity']['roots'][0].update(changes)
            with self.subTest(changes=changes),self.assertRaises(ModelError):self.prepare(invalid,self.selection())

if __name__=='__main__': unittest.main()
