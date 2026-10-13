"""I8a regression: assembly ownership does not bound native candidate impact.

Public synthetic scene. The expected integers below come from the two support
centrelines (500, 2500) and half sections, not from an assembly/member oracle.
"""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from tests._bridge import BridgeSession


class CandidateImpact(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix='assembly-impact-')
        self.addCleanup(tmp.cleanup)
        self.directory = Path(tmp.name)
        self.bridge = BridgeSession(cwd=self.directory)
        self.addCleanup(self.bridge.stop)
        fixture = Path(__file__).parent / 'fixtures/assembly-external-dependencies.scene'
        self.ok('loadfile ' + str(fixture.resolve()))

    def ok(self, command):
        r = self.bridge.command(command)
        self.assertTrue(r.get('ok'), r)
        return r

    def line(self, text):
        r = self.bridge.command('line ' + text)
        if 'preview' in r:
            self.assertTrue(r['preview']['valid'], r)
            r = self.ok('line confirm ' + str(r['preview']['token']))
        self.assertTrue(r.get('ok'), r)

    def dump(self):
        return self.ok('dump')['text']

    def request(self, operations, generation=False):
        read = self.ok('assembly-read')
        payload = {'schema': 'assembly-generation-transaction/1' if generation else 'assembly-transaction/1',
                   'expectedRevision': read['revision'], 'operations': operations}
        path = self.directory / 'edit.json'
        path.write_text(json.dumps(payload), encoding='utf-8')
        return self.ok(('assembly-generation-preview ' if generation else 'assembly-preview ') + str(path))['preview']

    def preview(self, width=40):
        read = self.ok('assembly-read')
        b = read['state']['bindings'][0]
        value = deepcopy(b['value'])
        value['slots'][0]['A']['value'] = width
        return self.request([{'op': 'edit-binding', 'id': 1,
                              'expectedFingerprint': b['fingerprint'], 'value': value}])

    def geometry(self):
        refs = self.ok('references')
        return {t['id']: t['geometry'] for t in refs['timbers']}

    def assert_complete_confirmation(self, p):
        self.assertEqual('candidate-geometry/1', p['impact']['schema'])
        old = self.geometry()
        self.assertEqual(old, {r['id']: r['before'] for r in p['impact']['timbers'] if r['before'] is not None})
        self.ok('assembly-confirm ' + str(p['token']))
        self.assertEqual(self.geometry(), {r['id']: r['after'] for r in p['impact']['timbers'] if r['after'] is not None})
        refs = self.ok('references')
        self.assertEqual({g['id']: g for g in refs['guides']},
                         {r['id']: r['after'] for r in p['impact']['guides']})

    def test_first_hop_external_and_unchanged_geometry_are_shown_before_confirm(self):
        before = self.dump()
        p = self.preview()
        self.assertTrue(p['valid'], p)
        rows = {r['id']: r for r in p['impact']['timbers']}
        self.assertEqual(1973, rows[92]['before']['length'])  # 2487 - 514
        self.assertEqual([514, 987, 2500], rows[92]['before']['origin'])
        self.assertEqual(1960, rows[92]['after']['length'])  # 2480 - 520
        self.assertEqual([520, 987, 2500], rows[92]['after']['origin'])
        for identifier in (90, 91):
            self.assertEqual(rows[identifier]['before'], rows[identifier]['after'])
        self.assertEqual(before, self.dump())
        self.assert_complete_confirmation(p)
        after = self.dump()
        self.line('undo'); self.assertEqual(before, self.dump())
        self.line('redo'); self.assertEqual(after, self.dump())

    def test_multi_hop_external_timber_guide_timber_closure_matches_candidate(self):
        # owned 2 -> ordinary 92 -> guide 5 -> ordinary 93 -> guide 6 -> 94.
        for line in ('spec gapOne 100', 'spec gapTwo 200',
                     'guide 5 1 v timber:92:u:hi+spec:gapOne', 'timber 93 27 33 role primary',
                     'place 93 on 1 at-line guide 5 between t90 t91 +v +n',
                     'guide 6 1 v timber:93:u:lo+spec:gapTwo', 'timber 94 27 33 role primary',
                     'place 94 on 1 at-line guide 6 between t90 t91 +v +n'):
            self.line(line)
        before = self.dump()
        p = self.preview()
        self.assertTrue(p['valid'], p)
        rows = {r['id']: r for r in p['impact']['timbers']}
        guides = {r['id']: r for r in p['impact']['guides']}
        # +v has its A axis toward -u: native origin is centre + ceil(27/2).
        for identifier, old, new in ((93, 2601, 2594), (94, 2788, 2781)):
            self.assertEqual([old, 20, 2500], rows[identifier]['before']['origin'])
            self.assertEqual([new, 20, 2500], rows[identifier]['after']['origin'])
            self.assertEqual(2960, rows[identifier]['after']['length'])
        for identifier, old, new in ((5, 2587, 2580), (6, 2774, 2767)):
            self.assertEqual(old, guides[identifier]['before']['off'])
            self.assertEqual(new, guides[identifier]['after']['off'])
        self.assertEqual(before, self.dump())
        self.assert_complete_confirmation(p)

    def test_cancel_stale_and_invalid_do_not_commit_candidate(self):
        before = self.dump()
        p = self.preview()
        self.ok('assembly-cancel ' + str(p['token']))
        self.assertFalse(self.bridge.command('assembly-confirm ' + str(p['token']))['ok'])
        self.assertEqual(before, self.dump())
        p = self.preview()
        self.line('spec unrelated 1')
        changed = self.dump()
        self.assertFalse(self.bridge.command('assembly-confirm ' + str(p['token']))['ok'])
        self.assertEqual(changed, self.dump())
        p = self.preview(3000)
        self.assertFalse(p['valid'], p)
        self.assertTrue(p['violations'])
        self.assertIn(92, {r['id'] for r in p['impact']['timbers']})
        self.assertFalse(self.bridge.command('assembly-confirm ' + str(p['token']))['ok'])
        self.assertEqual(changed, self.dump())

    def test_generation_creation_and_removal_have_explicit_null_geometry(self):
        self.line('delete timber 92')
        state = self.ok('assembly-read')['state']
        instance = state['instances'][0]
        source = instance['value']['source']
        p = self.request([{'op': 'delete-instance', 'id': 1,
                           'expectedFingerprint': instance['fingerprint']}], True)
        self.assertTrue(p['valid'], p)
        removed = [r for r in p['impact']['timbers'] if r['after'] is None]
        self.assertEqual({m['timberId'] for m in instance['members']}, {r['id'] for r in removed})
        self.assertTrue(all(r['before'] is not None for r in removed))
        self.assert_complete_confirmation(p)
        p = self.request([{'op': 'create-instance', 'value': source,
                           'expectedBindingFingerprint': state['bindings'][0]['fingerprint']}], True)
        self.assertTrue(p['valid'], p)
        created = [r for r in p['impact']['timbers'] if r['before'] is None]
        self.assertEqual([1973, 2960, 2960], sorted(r['after']['length'] for r in created))
        self.assert_complete_confirmation(p)


if __name__ == '__main__':
    unittest.main()
