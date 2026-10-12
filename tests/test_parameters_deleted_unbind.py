"""P-062: explicit unbind may consume only its same-candidate deleted source value."""
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests import test_parameters_core as harness
from tests.test_parameters_core import card,field


class DeletedSourceUnbind(unittest.TestCase):
    setUpClass=classmethod(harness.ParametersCore.setUpClass.__func__)
    setUp=harness.ParametersCore.setUp
    command=harness.ParametersCore.command
    read=harness.ParametersCore.read
    request=harness.ParametersCore.request
    apply=harness.ParametersCore.apply
    apply_line=harness.ParametersCore.apply_line
    TARGET={'kind':'timber','id':1,'field':'A'}

    def unbind(self):return {'op':'unbind-source','target':self.TARGET}
    def delete(self,identity=3):return {'op':'delete-parameter','id':identity}
    def source(self,identity=3):
        return {'op':'set-source','target':self.TARGET,'source':{'kind':'parameter','parameterId':identity,'fieldId':1}}

    def seed(self,*,dependency=False,override=False):
        self.apply_line('timber 1 27 33 role boundary')
        self.apply_line('place 1 on 1 at-face e3 +v +n')
        operations=[card(3,'selected source',[field(1,'=@4:1' if dependency else '27')])]
        if dependency or override:operations.append(card(4,'selected dependency',[field(1,'29' if override else '27')]))
        operations.append(self.source())
        self.apply(operations)
        if override:self.apply([{'op':'set-override','target':self.TARGET,'value':{'kind':'parameter','parameterId':4,'fieldId':1}}])
        self.assertEqual(29 if override else 27,self.read()['state']['sources'][0]['effective'])

    def accept(self,operations,*,value=27,ids=()):
        before=self.command('dump')['text'];revision=self.read()['revision']
        pending=self.request(operations)
        self.assertTrue(pending['ok'],pending)
        self.assertTrue(pending['preview']['valid'],
                        'P-062 explicit unbind must preserve the deleted source value: '+json.dumps(pending))
        self.assertEqual(before,self.command('dump')['text'],'preview changed formal definitions')
        self.assertEqual(revision,self.read()['revision'])
        self.assertEqual([],pending['preview']['after']['sources'])
        self.assertTrue(self.command('engineering-cancel '+str(pending['preview']['token']))['cancelled'])
        self.assertEqual(before,self.command('dump')['text'],'cancel leaked candidate source values')
        self.assertEqual(revision,self.read()['revision'])
        pending=self.request(operations);self.assertTrue(pending['preview']['valid'],pending)
        done=self.command('engineering-confirm '+str(pending['preview']['token']))
        self.assertTrue(done['ok'],done);self.assertTrue(done['history_changed'],done)
        self.assertEqual(revision+1,self.read()['revision'],'mixed candidate is one history step')
        after=self.command('dump')['text']
        self.assertRegex(after,r'(?m)^timber 1 %d 33 role boundary$'%value,
                         'P-062 unbind used the wrong candidate source value')
        self.assertEqual([],self.read()['state']['sources'])
        self.assertEqual(list(ids),[c['id'] for c in self.read()['state']['parameters']])
        self.apply_line('undo');self.assertEqual(before,self.command('dump')['text'],'Undo was not a full transaction restore')
        self.apply_line('redo');self.assertEqual(after,self.command('dump')['text'],'Redo changed the accepted candidate')
        return after

    def reject(self,operations,diagnostic):
        before=self.command('dump')['text'];revision=self.read()['revision']
        pending=self.request(operations);self.assertTrue(pending['ok'],pending)
        self.assertFalse(pending['preview']['valid'],'final unresolved reference or invalid value was accepted')
        self.assertIn(diagnostic,json.dumps(pending),pending)
        self.assertFalse(self.command('engineering-confirm '+str(pending['preview']['token']))['ok'])
        self.assertEqual(before,self.command('dump')['text'],'failed candidate changed formal definitions')
        self.assertEqual(revision,self.read()['revision'])

    def test_unbind_then_delete_is_legal_order_control(self):
        self.seed();self.accept([self.unbind(),self.delete()])

    def test_delete_then_unbind_has_identical_dump_to_legal_order(self):
        self.seed();before=self.command('dump')['text']
        first=self.accept([self.unbind(),self.delete()])
        self.apply_line('undo');self.assertEqual(before,self.command('dump')['text'])
        second=self.accept([self.delete(),self.unbind()])
        self.assertEqual(first.encode('utf-8'),second.encode('utf-8'),'operation order changed resulting bytes')

    def test_modified_source_is_captured_before_deletion(self):
        self.seed()
        self.accept([card(3,'selected source',[field(1,'29')]),self.delete(),self.unbind()],value=29)

    def test_modified_transitive_dependency_is_recomputed_before_deletion(self):
        self.seed(dependency=True)
        self.accept([card(4,'selected dependency',[field(1,'29')]),self.delete(),self.unbind()],value=29,ids=(4,))

    def test_deleted_source_does_not_follow_later_dependency_changes(self):
        self.seed(dependency=True)
        self.accept([self.delete(),card(4,'selected dependency',[field(1,'31')]),self.unbind()],value=27,ids=(4,))

    def test_live_override_uses_current_value_after_base_source_deletion(self):
        self.seed(override=True)
        self.accept([self.delete(),card(4,'selected dependency',[field(1,'31')]),self.unbind()],value=31,ids=(4,))

    def test_deleted_override_keeps_value_while_live_source_is_recomputed(self):
        self.seed(override=True)
        self.accept([self.delete(4),card(3,'selected source',[field(1,'31')]),self.unbind()],value=29,ids=(3,))

    def test_both_deleted_source_and_override_are_explicitly_unbound(self):
        self.seed(override=True)
        self.accept([self.delete(),self.delete(4),self.unbind()],value=29)

    def test_reused_identity_in_next_candidate_cannot_read_previous_cache(self):
        self.seed();self.accept([self.delete(),self.unbind()])
        self.apply([card(3,'new identity in next transaction',[field(1,'31')]),self.source()])
        self.accept([self.delete(),self.unbind()],value=31)

    def test_no_explicit_unbind_still_names_and_rejects_remaining_target(self):
        self.seed();self.reject([self.delete()],'timber 1 A')

    def test_failed_candidate_does_not_leak_value_to_the_next_attempt(self):
        self.seed()
        self.reject([card(3,'selected source',[field(1,'29')]),self.delete(),self.unbind(),
                     card(8,'invalid survivor',[field(1,'=@8:1')])],'CYCLE')
        self.accept([self.delete(),self.unbind()],value=27)

    def test_deleted_fractional_source_does_not_fall_back_to_old_integer(self):
        self.seed()
        self.reject([card(3,'selected source',[field(1,'27.5')]),self.delete(),self.unbind()],'GEOMETRY')

    def test_surviving_override_missing_dependency_is_not_frozen(self):
        self.seed(override=True)
        self.reject([self.delete(),card(4,'selected dependency',[field(1,'=@99:1')]),self.unbind()],'parameter 99 field 1')

    def test_live_original_under_deleted_override_still_validates_current_dependencies(self):
        self.seed(override=True)
        self.reject([self.delete(4),card(3,'selected source',[field(1,'=@99:1')]),self.unbind()],'parameter 99 field 1')


if __name__=='__main__':unittest.main(verbosity=2)
