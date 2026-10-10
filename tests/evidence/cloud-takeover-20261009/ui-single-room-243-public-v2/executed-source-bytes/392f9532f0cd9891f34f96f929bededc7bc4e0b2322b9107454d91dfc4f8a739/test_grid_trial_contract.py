"""Read-only unsaved-source trials use exact native lattice segments."""
import unittest
import json
from pathlib import Path
from tests import test_infinite_grid_contract as contract
infinite = contract.infinite


class GridTrialContract(unittest.TestCase):
    setUpClass = classmethod(contract.InfiniteGridContract.setUpClass.__func__)
    setUp = contract.InfiniteGridContract.setUp
    command = contract.InfiniteGridContract.command
    line = contract.InfiniteGridContract.line
    commit = contract.InfiniteGridContract.commit
    dump = contract.InfiniteGridContract.dump
    objects = contract.InfiniteGridContract.objects
    refs = contract.InfiniteGridContract.refs
    snapshot = contract.InfiniteGridContract.snapshot

    def trial(self, rect='-100 -100 700 500', u='repeat 0 600', v='repeat 0 400'):
        return self.command(f'grid-trial-query rect {rect} ' + infinite(u=u, v=v))

    def test_exact_unsaved_query_has_no_world_or_undo_mutation(self):
        before = self.snapshot()
        result = self.trial()
        self.assertTrue(result['ok'], result)
        self.assertTrue(result['exact'])
        self.assertEqual([l['coordinate'] for l in result['axes']['u']['lines']], [0, 600])
        self.assertEqual(result['axes']['v']['lines'][0]['segments'], [{'a': [-100, 0], 'b': [700, 0]}])
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.command('undo')['ok'])

    def test_negative_stagger_bands_are_core_clipped(self):
        result = self.trial('-700 -500 700 500', 'repeat 0 600 stagger 100')
        self.assertTrue(result['ok'], result)
        line = next(l for l in result['axes']['u']['lines'] if l['index'] == '-1')
        self.assertEqual(line['segments'], [
            {'a': [-600, -500], 'b': [-600, -400], 'band': '-2'},
            {'a': [-500, -400], 'b': [-500, 0], 'band': '-1'},
            {'a': [-600, 0], 'b': [-600, 400], 'band': '0'},
            {'a': [-500, 400], 'b': [-500, 500], 'band': '1'}])

    def test_invalid_zero_and_capacity_refuse_without_mutation(self):
        before = self.snapshot()
        for u in ('repeat 0 0', 'repeat 0 600 stagger 0', 'repeat 0 600 stagger 600'):
            self.assertFalse(self.trial(u=u)['ok'], u)
        result = self.trial('0 0 1000 1000', 'repeat 0 1')
        self.assertFalse(result['ok']); self.assertEqual(result['code'], 'QUERY_CAPACITY')
        self.assertFalse(self.trial('0 0 0 100')['ok'])
        self.assertEqual(self.snapshot(), before)

    def test_pending_confirmation_survives_trial(self):
        staged = self.line('preview ' + infinite(4))
        self.assertTrue(staged['preview']['valid'], staged)
        token = staged['preview']['token']
        before = self.dump()
        self.assertTrue(self.trial()['ok'])
        self.assertEqual(self.dump(), before)
        result = self.line('confirm ' + str(token))
        self.assertTrue(result['ok'], result)
        self.assertEqual([s['id'] for s in self.objects()['gridSystems']], [4])

    def test_parameter_reference_is_resolved_without_saving_source(self):
        revision = self.command('engineering-read')['revision']
        path = Path(self.directory.name) / 'trial-parameters.json'
        path.write_text(json.dumps({'schema': 'engineering-transaction/1', 'expectedRevision': revision,
            'operations': [{'op': 'put-parameter', 'value': {'id': 1, 'name': 'trial dimensions', 'fields': [
                {'id': 1, 'name': 'step', 'type': 'dimension', 'input': '200'},
                {'id': 2, 'name': 'phase', 'type': 'dimension', 'input': '-30'},
                {'id': 3, 'name': 'stagger', 'type': 'dimension', 'input': '50'},
                {'id': 4, 'name': 'fraction', 'type': 'dimension', 'input': '457.5'},
                {'id': 5, 'name': 'count', 'type': 'count', 'input': '200'},
            ]}}]}), encoding='utf-8')
        preview = self.command('engineering-preview ' + contract.native_path(path))
        self.assertTrue(preview['ok'], preview)
        self.assertTrue(self.command('engineering-confirm ' + str(preview['preview']['token']))['ok'])
        before = self.snapshot()
        r = self.trial('0 0 650 350', 'repeat param:1:2 param:1:1 stagger param:1:3')
        self.assertTrue(r['ok'], r)
        self.assertEqual([l['coordinate'] for l in r['axes']['u']['lines'] if l['segments']], [170, 370, 570])
        self.assertEqual(r['axes']['u']['lines'][0]['segments'], [])
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.trial(u='repeat 0 param:1:99')['ok'])
        self.assertFalse(self.trial(u='repeat 0 param:1:4')['ok'])
        self.assertFalse(self.trial(u='repeat 0 param:1:5')['ok'])
        self.assertEqual(self.snapshot(), before)


if __name__ == '__main__':
    unittest.main()
