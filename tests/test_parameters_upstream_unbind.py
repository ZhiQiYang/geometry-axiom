"""P-065: only explicitly unbound deleted sources may use pre-upstream-deletion values."""
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests import test_parameters_deleted_unbind as deleted
from tests.test_parameters_core import card,field


class UpstreamDeletedUnbind(unittest.TestCase):
    Base=deleted.DeletedSourceUnbind
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

    def change_dependency(self,value):
        return card(4,'selected dependency',[field(1,str(value))])

    def both_orders(self,value):
        self.seed(dependency=True)
        before=self.command('dump')['text']
        prefix=[] if value==27 else [self.change_dependency(value)]
        legal=self.accept(prefix+[self.unbind(),self.delete(4),self.delete(3)],value=value)
        self.apply_line('undo');self.assertEqual(before,self.command('dump')['text'])
        upstream=self.accept(prefix+[self.delete(4),self.delete(3),self.unbind()],value=value)
        self.assertEqual(legal.encode('utf-8'),upstream.encode('utf-8'),
                         'P-065 upstream deletion changed the complete accepted dump')

    def reject_live_path(self,operations,source,dependency):
        before=self.command('dump');self.assertTrue(before['ok'])
        revision=self.read()['revision'];pending=self.request(operations)
        self.assertTrue(pending['ok'],pending);self.assertFalse(pending['preview']['valid'],pending)
        text=json.dumps(pending)
        left='[%d:1 '%source;right='parameter %d field 1'%dependency
        self.assertIn(left,text,pending);self.assertIn(right,text,pending)
        self.assertLess(text.index(left),text.index(right),'diagnostic must identify surviving source to missing dependency')
        self.assertIn(' -> ',text[text.index(left):text.index(right)],pending)
        self.assertFalse(self.command('engineering-confirm '+str(pending['preview']['token']))['ok'])
        self.assertEqual(before,self.command('dump'));self.assertEqual(revision,self.read()['revision'])

    def test_unbind_first_unchanged_control(self):
        self.seed(dependency=True)
        self.accept([self.unbind(),self.delete(4),self.delete(3)])

    def test_upstream_first_unchanged_matches_legal_order(self):
        self.both_orders(27)

    def test_unbind_first_modified_control(self):
        self.seed(dependency=True)
        self.accept([self.change_dependency(29),self.unbind(),self.delete(4),self.delete(3)],value=29)

    def test_upstream_first_modified_matches_legal_order(self):
        self.both_orders(29)

    def test_surviving_source_cannot_use_its_upstream_deletion_snapshot(self):
        self.seed(dependency=True)
        self.reject_live_path([self.delete(4),self.unbind()],3,4)

    def test_unrelated_invalid_definition_does_not_block_the_deleted_closure(self):
        self.seed(dependency=True)
        self.accept([card(8,'temporary unrelated cycle',[field(1,'=@8:1')]),
                     self.delete(4),self.delete(3),self.unbind(),self.delete(8)])

    def test_transitive_upstream_deletion_keeps_the_source_last_valid_value(self):
        self.seed(dependency=True)
        self.apply([card(5,'transitive upstream',[field(1,'27')]),self.change_dependency('=@5:1')])
        self.accept([self.delete(5),self.delete(4),self.delete(3),self.unbind()])

    def test_deleted_source_and_override_each_keep_their_last_valid_values(self):
        self.seed(dependency=True)
        self.apply([card(5,'override',[field(1,'=@6:1')]),card(6,'override upstream',[field(1,'29')]),
                    {'op':'set-override','target':self.TARGET,'value':{'kind':'parameter','parameterId':5,'fieldId':1}}])
        self.accept([self.delete(4),self.delete(6),self.delete(3),self.delete(5),self.unbind()],value=29)

    def test_surviving_override_cannot_use_its_upstream_deletion_snapshot(self):
        self.seed()
        self.apply([card(4,'override',[field(1,'=@5:1')]),card(5,'override upstream',[field(1,'29')]),
                    {'op':'set-override','target':self.TARGET,'value':{'kind':'parameter','parameterId':4,'fieldId':1}}])
        self.reject_live_path([self.delete(5),self.delete(3),self.unbind()],4,5)

    def test_recovered_source_replaces_its_earlier_candidate_snapshot(self):
        self.seed(dependency=True)
        self.apply([card(5,'replacement upstream',[field(1,'31')])])
        self.accept([self.delete(4),card(3,'selected source',[field(1,'=@5:1')]),
                     self.delete(5),self.delete(3),self.unbind()],value=31)

    def test_rejected_candidate_cannot_leak_an_upstream_snapshot(self):
        self.seed(dependency=True)
        self.reject_live_path([self.change_dependency(29),self.delete(4),self.unbind()],3,4)
        self.accept([self.delete(4),self.delete(3),self.unbind()],value=27)

    def test_zero_card_and_field_id_remain_valid_upstream_references(self):
        self.seed()
        self.apply([card(0,'zero upstream',[field(0,'27')]),
                    card(3,'selected source',[field(1,'=@0:0')])])
        self.accept([self.delete(0),self.delete(3),self.unbind()])


if __name__=='__main__':unittest.main(verbosity=2)
