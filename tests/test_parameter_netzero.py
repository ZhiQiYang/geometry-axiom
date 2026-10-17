"""Net-zero candidates preserve native history, redo and cold/warm behavior."""
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests import _bridge, test_parameters_core as harness
from tests.test_parameters_core import card, field


class ParameterNetZero(unittest.TestCase):
    setUpClass=classmethod(harness.ParametersCore.setUpClass.__func__)
    command=harness.ParametersCore.command
    read=harness.ParametersCore.read
    request=harness.ParametersCore.request
    apply=harness.ParametersCore.apply
    apply_line=harness.ParametersCore.apply_line
    archive_line=harness.ParametersCore.archive_line

    def setUp(self):
        harness.ParametersCore.setUp(self)
        self.assertTrue(self.command('reset')['ok'])

    def confirm_net_zero(self,identities):
        before=self.command('dump')['text']
        revision=self.read()['revision']
        operations=[card(i,'temporary '+str(i),[field(1,str(i+10))]) for i in identities]
        operations.extend({'op':'delete-parameter','id':i} for i in identities)
        pending=self.request(operations)
        self.assertTrue(pending['ok'],pending)
        self.assertTrue(pending['preview']['valid'],pending)
        self.assertEqual(before,self.command('dump')['text'],'net-zero preview changed live definitions')
        self.assertEqual(revision,self.read()['revision'],'net-zero preview changed revision')
        confirmed=self.command('engineering-confirm '+str(pending['preview']['token']))
        self.assertTrue(confirmed['ok'],confirmed)
        after=self.command('dump')['text']
        revision_after=self.read()['revision']
        self.assertEqual(before,after,'net-zero confirmation changed definitions')
        # Do not fail on history_changed yet: callers must exercise native redo
        # or a fresh bridge first, so the corresponding regressions actually run.
        return {'before':before,'after':after,'revision_before':revision,
                'revision_after':revision_after,'confirmed':confirmed}

    def assert_no_history_change(self,result,label):
        self.assertFalse(result['confirmed']['history_changed'],label+': net-zero candidate recorded history: '+repr(result))
        self.assertEqual(result['revision_before'],result['revision_after'],label+': net-zero candidate incremented revision')

    def test_empty_world_net_zero_does_not_add_history_or_revision(self):
        observed=self.confirm_net_zero((1,))
        self.assert_no_history_change(observed,'empty world')
        self.assertFalse(self.command('line undo')['ok'],'net-zero candidate created an undo entry')
        self.assertFalse(self.command('line redo')['ok'],'net-zero candidate created a redo entry')
        self.assertEqual(observed['before'],self.command('dump')['text'])

    def test_multiple_retired_identities_do_not_destroy_redo(self):
        empty=self.command('dump')['text']
        self.apply([card(9,'stable',[field(1,'10')])])
        stable=self.command('dump')['text']
        self.apply([card(8,'redo marker',[field(1,'20')])])
        redo_world=self.command('dump')['text']
        self.apply_line('undo')
        observed=self.confirm_net_zero((1,2,3))
        self.assertEqual(stable,observed['before'])
        # This is an actual native redo attempt even on the broken version.
        redo=self.command('line redo')
        after_redo=self.command('dump')['text']
        self.assertTrue(redo['ok'],'net-zero candidate discarded existing redo: '+repr({'redo':redo,'candidate':observed}))
        self.assertEqual(redo_world,after_redo,'redo restored the wrong saved world')
        self.assert_no_history_change(observed,'multiple identities')
        self.apply_line('undo')
        self.assertEqual(stable,self.command('dump')['text'])
        self.apply_line('undo')
        self.assertEqual(empty,self.command('dump')['text'],'net-zero candidate inserted an extra undo entry')

    def test_archive_retirement_cannot_change_a_later_net_zero_candidate(self):
        self.apply_line(self.archive_line(card(7,'archive temporary',[field(1,'10')])))
        with_card=self.command('dump')['text']
        self.apply_line(self.archive_line({'op':'delete-parameter','id':7}))
        empty=self.command('dump')['text']
        observed=self.confirm_net_zero((1,2))
        # Observe the history target before checking the response's history flag.
        self.apply_line('undo')
        self.assertEqual(with_card,self.command('dump')['text'],'archive retirement left a hidden net-zero history entry')
        self.assert_no_history_change(observed,'archive retirement')
        self.apply_line('redo')
        self.assertEqual(empty,self.command('dump')['text'])

    def test_saved_definitions_have_identical_cold_and_warm_history_behavior(self):
        self.apply([card(9,'stable saved definition',[field(1,'10')])])
        saved=self.command('dump')['text']
        # Warm up the same transient id before observing the second transaction.
        # No expectation is made about this setup transaction's history flag.
        self.apply([card(1,'warm-up transient',[field(1,'11')]),{'op':'delete-parameter','id':1}])
        self.assertEqual(saved,self.command('dump')['text'])
        warm=self.confirm_net_zero((1,))
        saved_path=self.directory/'cold-warm.scene'
        saved_path.write_text(saved,encoding='utf-8')
        warm_session=self.session
        cold_session=_bridge.BridgeSession(self.exe)
        try:
            self.session=cold_session
            self.assertTrue(self.command('loadfile '+str(saved_path))['ok'])
            self.assertEqual(saved,self.command('dump')['text'],'cold reload changed saved definitions')
            cold=self.confirm_net_zero((1,))
        finally:
            self.session=warm_session
            cold_session.stop()
        self.assertEqual(warm['before'],cold['before'])
        self.assertEqual(warm['after'],cold['after'])
        self.assertEqual((False,False),
            (warm['confirmed']['history_changed'],cold['confirmed']['history_changed']),
            'cold/warm net-zero candidates changed history: '+repr({'warm':warm,'cold':cold}))
        self.assert_no_history_change(warm,'warm saved definition')
        self.assert_no_history_change(cold,'cold saved definition')


if __name__=='__main__':unittest.main()
