"""Formal scope boundaries; all fixture data is repo-authored."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'geometry-web'))
from rule_case_host import RuleCaseHost, prepare_data, PROTOCOL
from rule_case_workbench_adapter import AdapterError, DATA_SCHEMA
from rule_cases.catalog import cases


class Native:
    session = 'selected-native-session'
    editor_sequence = 71
    revision = 4
    closed = False


class RuleCaseHostTests(unittest.TestCase):
    def setUp(self):
        self.native = Native()
        self.fresh = True
        self.host = RuleCaseHost(self.native, read_native=lambda: {'ok': True, 'revision': self.native.revision},
                                 version='original-runtime', fresh=lambda: self.fresh)
        self.data = dict(protocol=PROTOCOL, action='create', requestId='a'*32, sequence=1,
                         session=self.native.session, runtime='original-runtime', revision=4,
                         context={'projectId':'logical-original', 'generation':1, 'contextToken':'original-frame'})

    def tearDown(self):
        self.host.close()

    def bind(self, data=None):
        return self.host.bind(json.dumps(data or self.data).encode())

    def dispatch(self, action, **fields):
        return self.host.dispatch(json.dumps(dict(protocol='rule-case-workbench/1', action=action, **fields)).encode())

    def test_pending_cancel_tombstones_original_without_consuming_editor_sequence(self):
        self.bind({**self.data, 'action':'cancel'})
        with self.assertRaises(AdapterError): self.bind()
        self.assertEqual(self.host.next_sequence()['sequence'], 2)
        self.assertEqual(self.native.editor_sequence, 71)

    def test_binding_is_immutable_and_duplicate_creation_is_idempotent(self):
        self.bind(); owner = self.host.binding
        self.bind(); self.assertIs(self.host.binding, owner)
        for field, value in [('revision',5),('sequence',2),('context',{**self.data['context'],'contextToken':'replacement'})]:
            with self.subTest(field=field), self.assertRaises(AdapterError): self.bind({**self.data, field:value})

    def test_cancelled_old_binding_cannot_close_the_new_one(self):
        self.bind()
        new = {**self.data,'requestId':'b'*32,'sequence':2,'context':{**self.data['context'],'generation':2}}
        self.bind(new); owner = self.host.binding
        self.bind({**self.data,'action':'cancel'})
        self.assertIs(self.host.binding, owner)
        self.assertEqual(self.dispatch('open')[0], 200)

    def test_unknown_lower_sequence_is_permanently_rejected_after_finite_eviction(self):
        for index in range(1,70): self.bind({**self.data,'action':'cancel','requestId':f'{index:032x}','sequence':index,'context':{**self.data['context'],'generation':index}})
        self.assertEqual(len(self.host.requests),64)
        with self.assertRaises(AdapterError): self.bind({**self.data,'requestId':f'{1:032x}'})

    def test_native_change_retires_session_and_never_rebinds_it(self):
        self.bind(); opened=self.dispatch('open')[1]
        self.native.revision += 1
        self.assertEqual(self.dispatch('validate',sessionId=opened['sessionId'],definition=cases()[0])[0],409)
        self.native.revision -= 1
        self.assertEqual(self.dispatch('open')[0],409)

    def test_selected_session_runtime_and_revision_are_exact_guards(self):
        for field,value in [('session','root-fallback'),('runtime','replacement'),('revision',3)]:
            with self.subTest(field=field),self.assertRaises(AdapterError): self.bind({**self.data,field:value})

    def test_close_only_retires_cases_and_not_the_selected_native(self):
        self.bind(); self.host.close()
        self.assertFalse(self.native.closed)
        self.assertEqual(self.native.editor_sequence,71)
        self.assertEqual(self.dispatch('open')[0],409)

    def test_expiry_and_runtime_retirement_never_yield_current_results(self):
        self.bind(); self.host.binding['started'] -= 301
        self.assertEqual(self.dispatch('open')[0],409)
        self.bind({**self.data,'requestId':'b'*32,'sequence':2,'context':{**self.data['context'],'generation':2}}); self.fresh=False
        self.assertEqual(self.dispatch('open')[0],409)

    def test_detached_prepare_preserves_data_and_never_creates_binding(self):
        data={'schema':DATA_SCHEMA,'definitions':cases(),'receipts':[]}; original=deepcopy(data)
        result=prepare_data(json.dumps(data).encode())
        self.assertEqual(result['data'],original);self.assertEqual(result['trust'],'historical-unverified')
        self.assertIsNone(self.host.binding)
        bad=deepcopy(data);bad['definitions'][1]['input']['setup']=[]
        with self.assertRaises((ValueError,AdapterError)):prepare_data(json.dumps(bad).encode())

    def test_true_native_receipt_prepares_as_history_without_current_trust(self):
        from tests._bridge import find_bridge
        from rule_cases.request import run_case_request
        definition=cases()[0]
        receipt=run_case_request(json.dumps(definition).encode(),project_id='original',generation=7,binary=find_bridge())
        self.assertEqual(receipt['status'],'passed')
        data={'schema':DATA_SCHEMA,'definitions':cases(),'receipts':[{'definition':definition,'receipt':receipt}]}
        result=prepare_data(json.dumps(data).encode(),find_bridge())
        self.assertEqual(result['data'],data);self.assertEqual(result['trust'],'historical-unverified')

    def test_closed_shapes_and_bool_identifiers_fail_before_allocation(self):
        for change in [{'sequence':True},{'revision':True},{'program':'echo arbitrary'}]:
            with self.subTest(change=change),self.assertRaises(AdapterError):self.bind({**self.data,**change})
        self.assertEqual(self.host.sequence,0)

    def test_generation_is_the_controlled_sequence_before_any_allocation(self):
        for generation in [0,999,True]:
            data=deepcopy(self.data);data['context']['generation']=generation
            with self.subTest(generation=generation),self.assertRaises(AdapterError):self.bind(data)
            self.assertEqual(self.host.sequence,0);self.assertEqual(self.host.requests,{})
            self.assertIsNone(self.host.binding);self.assertEqual(self.host.adapters,set())

    def test_finite_cache_cannot_evict_a_still_active_binding_request(self):
        self.bind();owner=self.host.binding
        for index in range(2,70):self.bind({**self.data,'action':'cancel','requestId':f'{index:032x}','sequence':index,'context':{**self.data['context'],'generation':index}})
        self.assertLessEqual(len(self.host.requests),64);self.assertIs(self.host.binding,owner)
        self.bind({**self.data,'action':'close'});self.assertIsNone(self.host.binding)
        self.assertEqual(self.host.dispatch(json.dumps({'protocol':'rule-case-workbench/1','action':'open'}).encode())[0],409)


if __name__=='__main__': unittest.main()
