"""P-065/B5: an overwritten dependency must retain its last valid candidate value."""
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests import test_parameters_upstream_unbind as upstream
from tests.test_parameters_core import card,field


class CandidateValueHistory(unittest.TestCase):
    Base=upstream.UpstreamDeletedUnbind
    setUpClass=classmethod(Base.setUpClass.__func__)
    setUp=Base.setUp
    command=Base.command
    read=Base.read
    request=Base.request
    apply=Base.apply
    apply_line=Base.apply_line
    TARGET=Base.TARGET
    unbind=Base.unbind
    delete=Base.delete
    source=Base.source
    seed=Base.seed
    accept=Base.accept
    reject=Base.reject
    change_dependency=Base.change_dependency
    reject_live_path=Base.reject_live_path

    def broken_dependency(self):return self.change_dependency('=@5:1')

    def both_orders(self,*,value=27,bad=None,prefix=(),cleanup=None):
        before=self.command('dump')['text']
        bad=self.broken_dependency() if bad is None else bad
        cleanup=[self.delete(4),self.delete(3)] if cleanup is None else cleanup
        first_ops=[*prefix,self.unbind(),bad,*cleanup]
        second_ops=[*prefix,bad,*cleanup,self.unbind()]
        first=self.accept(first_ops,value=value)
        self.apply_line('undo');self.assertEqual(before,self.command('dump')['text'])
        second=self.accept(second_ops,value=value)
        self.assertEqual(first.encode('utf-8'),second.encode('utf-8'),
                         'B5 overwrite/delete order changed the complete accepted dump')
        trace=os.environ.get('GEOMETRY_B5_TRACE_DIR')
        if trace:
            directory=Path(trace);directory.mkdir(parents=True,exist_ok=True)
            name=self._testMethodName
            raw_first=first.encode('utf-8');raw_second=second.encode('utf-8')
            (directory/(name+'-legal.dump')).write_bytes(raw_first)
            (directory/(name+'-overwrite-first.dump')).write_bytes(raw_second)
            result={'name':name,'expected_mm':value,'operations':[first_ops,second_ops],
                    'dumps_utf8':[first,second],'dump_sha256':[hashlib.sha256(b).hexdigest() for b in (raw_first,raw_second)],
                    'pairwise_dump_byte_identity':raw_first==raw_second,'completed':True}
            (directory/(name+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')

    def test_unbind_first_before_missing_overwrite_control(self):
        self.seed(dependency=True)
        self.accept([self.unbind(),self.broken_dependency(),self.delete(4),self.delete(3)])

    def test_missing_overwrite_first_keeps_baseline_and_identical_dump(self):
        self.seed(dependency=True);self.both_orders()

    def test_unbind_first_after_valid_change_control(self):
        self.seed(dependency=True)
        self.accept([self.change_dependency(29),self.unbind(),self.broken_dependency(),
                     self.delete(4),self.delete(3)],value=29)

    def test_missing_overwrite_first_refreshes_changed_value_and_identical_dump(self):
        self.seed(dependency=True)
        self.both_orders(value=29,prefix=[self.change_dependency(29)])

    def test_cycle_overwrite_keeps_last_valid_closure(self):
        self.seed(dependency=True);self.both_orders(bad=self.change_dependency('=@3:1'))

    def test_upstream_field_removal_keeps_the_deleted_source_value(self):
        self.seed(dependency=True)
        self.both_orders(bad=card(4,'selected dependency',[field(2,'41')]))

    def test_source_field_removal_keeps_its_deleted_field_value(self):
        self.seed(dependency=True)
        self.both_orders(bad=card(3,'selected source',[field(2,'41')]))

    def test_cancelled_overwrite_candidate_cannot_leak_refreshed_value(self):
        self.seed(dependency=True);before=self.command('dump');revision=self.read()['revision']
        pending=self.request([self.change_dependency(29),self.broken_dependency(),self.delete(4),
                              self.delete(3),self.unbind()])
        self.assertTrue(pending['ok'],pending)
        self.assertTrue(pending['preview']['valid'],'B5 canceled candidate needs the valid29 snapshot: '+json.dumps(pending))
        self.assertEqual(before,self.command('dump'));self.assertEqual(revision,self.read()['revision'])
        self.assertTrue(self.command('engineering-cancel '+str(pending['preview']['token']))['cancelled'])
        self.assertEqual(before,self.command('dump'));self.assertEqual(revision,self.read()['revision'])
        self.accept([self.broken_dependency(),self.delete(4),self.delete(3),self.unbind()],value=27)

    def test_failed_overwrite_candidate_cannot_leak_refreshed_value(self):
        self.seed(dependency=True)
        self.reject_live_path([self.change_dependency(29),self.broken_dependency(),self.delete(4),self.unbind()],3,4)
        self.accept([self.broken_dependency(),self.delete(4),self.delete(3),self.unbind()],value=27)

    def test_surviving_source_still_requires_current_dependencies_control(self):
        self.seed(dependency=True)
        self.reject_live_path([self.broken_dependency(),self.delete(4),self.unbind()],3,4)

    def test_surviving_override_still_requires_current_dependencies_control(self):
        self.seed()
        self.apply([card(4,'override',[field(1,'=@5:1')]),card(5,'override dependency',[field(1,'29')]),
                    {'op':'set-override','target':self.TARGET,'value':{'kind':'parameter','parameterId':4,'fieldId':1}}])
        self.reject_live_path([card(5,'override dependency',[field(1,'=@9:1')]),self.delete(5),
                               self.delete(3),self.unbind()],4,5)

    def test_unrelated_invalid_definition_does_not_block_capture_controlled_closure(self):
        self.seed(dependency=True)
        self.both_orders(prefix=[card(8,'unrelated temporary cycle',[field(1,'=@8:1')])],
                         cleanup=[self.delete(4),self.delete(3),self.delete(8)])


if __name__=='__main__':unittest.main(verbosity=2)
