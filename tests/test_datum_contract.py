"""D6c/I7a end-to-end core contract through the same public bridge as the UI."""
import itertools
import json
import tempfile
from pathlib import Path
import unittest
from test_reference_contract import Session


class DatumContract(unittest.TestCase):
    def setUp(self):
        self.s = Session()
        self.addCleanup(self.s.close)
        self.assertTrue(self.s.send('reset')['ok'])

    def line(self, command):
        return self.s.send('line ' + command)

    def ok(self, command):
        r = self.line(command)
        self.assertTrue(r['ok'], (command, r))
        return r

    def refs(self):
        return self.s.send('references')

    def dump(self):
        return self.s.send('dump')['text']

    def reject_unchanged(self, command):
        old = self.dump()
        r = self.line(command)
        self.assertFalse(r['ok'], (command, r))
        self.assertEqual(old, self.dump())
        return r

    def preview(self, command):
        old = self.dump()
        r = self.line('preview ' + command)
        self.assertTrue(r['ok'], r)
        self.assertEqual(old, self.dump())
        return r['preview']

    def walls(self, timbers=False):
        self.ok('spec height 500')
        self.ok('datum 1 z spec:height')
        for sid, axis, base in [(1, '+x', 0), (2, '+y', 10)]:
            self.ok(f'surface {sid} origin 0 0 0 u {axis} v +z rect 0 0 4000 3000')
            self.ok(f'guide {base+1} {sid} datum 1')
            self.ok(f'guide {base+2} {sid} u guide:{base+1}')
            if timbers:
                for tid, edge in [(base+1, 'e1'), (base+2, 'e3')]:
                    self.ok(f'timber {tid} 27 33 role boundary')
                    self.ok(f'place {tid} on {sid} at-face {edge} +v +n')
                self.ok(f'timber {base+3} 27 33 role primary')
                self.ok(f'place {base+3} on {sid} at-line guide {base+2} +u +n')

    def test_all_orthogonal_frames_and_three_shared_axes(self):
        # Check world-plane membership rather than reproducing the uv formula.
        vectors = {'+x': (1,0,0), '-x': (-1,0,0), '+y': (0,1,0), '-y': (0,-1,0), '+z': (0,0,1), '-z': (0,0,-1)}
        self.ok('spec offset 37')
        for world_axis, axis in enumerate('xyz'):
            self.ok(f'datum 1 {axis} spec:offset')
            for u, v in itertools.permutations(vectors, 2):
                if u[1] == v[1]:
                    continue
                with self.subTest(axis=axis, u=u, v=v):
                    self.ok(f'surface 1 origin 101 -211 307 u {u} v {v} rect -1000 -1000 1000 1000')
                    r = self.line('guide 1 1 datum 1')
                    intersects = vectors[u][world_axis] or vectors[v][world_axis]
                    self.assertEqual(bool(intersects), r['ok'], r)
                    if intersects:
                        g = self.refs()['guides'][0]
                        self.assertEqual(g['worldPoint'][world_axis], 37)
                        self.assertEqual(g['worldDirection'][world_axis], 0)
                        self.assertEqual(len(g['segments']), 1)
                        self.ok('delete guide 1')
                    self.ok('delete placement 1')
        # The test traversed every signed orthogonal frame and all three axes.

    def test_floor_precedes_negative_axis_transform(self):
        self.ok('spec h 3')
        self.ok('datum 1 x -1/2*spec:h')
        self.ok('surface 1 origin 5 0 0 u -x v +z rect 0 0 100 100')
        self.ok('guide 1 1 datum 1')
        r = self.refs()
        self.assertEqual(r['datums'][0]['position'], -2)
        self.assertEqual(r['guides'][0]['off'], 7)
        self.assertEqual(r['guides'][0]['worldPoint'], [-2,0,0])

    def test_unique_line_and_invalid_sources_are_atomic(self):
        self.ok('spec h 500')
        self.ok('datum 1 z spec:h')
        self.ok('surface 1 origin 0 0 0 u +x v +y rect 0 0 4000 3000')
        self.assertIn('parallel', str(self.reject_unchanged('guide 1 1 datum 1')))
        self.ok('surface 1 origin 0 0 500 u +x v +y rect 0 0 4000 3000')
        self.assertIn('coincident', str(self.reject_unchanged('guide 1 1 datum 1')))
        for expr in ['500', 'spec:missing', 'guide:1', '1/0*spec:h', '100000000*spec:h']:
            self.reject_unchanged('datum 2 z ' + expr)
        self.reject_unchanged('datum 2 q spec:h')
        self.reject_unchanged('guide 2 1 datum 99')
        self.ok('datum 0 x spec:h')
        self.ok('datum 4294967295 x spec:h')
        self.assertNotIn(self.s.send('newid')['datum'], (0,1,4294967295))

    def test_hidden_and_hole_split_are_one_reference_and_no_material_exemption(self):
        self.ok('spec h 1500')
        self.ok('spec outside 9999')
        self.ok('datum 1 z spec:h')
        self.ok('surface 1 origin 0 0 0 u +x v +z outline 0,0 4000,0 4000,3000 0,3000 hole 1000,1000 2000,1000 2000,2000 1000,2000')
        self.ok('guide 1 1 datum 1')
        self.ok('guide 2 1 u spec:outside')
        self.ok('guide 3 1 u guide:2-spec:outside+spec:h')
        guides = self.refs()['guides']
        self.assertEqual([len(g['segments']) for g in guides], [2,0,2])
        self.assertEqual(guides[0]['segments'], [[[0,1500],[1000,1500]],[[2000,1500],[4000,1500]]])
        self.ok('timber 10 27 33 role primary')
        self.reject_unchanged('place 10 on 1 at-line guide 2 +u +n')
        # A self-contained rectangular placement must clip too.
        self.ok('surface 2 origin 0 0 0 u +y v +z rect 0 0 500 500')
        self.ok('guide 4 2 datum 1')
        self.assertEqual(self.refs()['guides'][-1]['segments'], [])
        self.reject_unchanged('guide 5 2 u guide:1')
        self.reject_unchanged('guide 5 1 v guide:1')
        self.reject_unchanged('move 1 spec:outside')
        self.reject_unchanged('delete datum 1')

    def test_cross_face_preview_confirm_cancel_stale_and_undo(self):
        self.walls(timbers=True)
        original = self.dump()
        p = self.preview('spec height 900')
        self.assertTrue(p['valid'], p)
        changed = [t for t in p['timbers'] if t['before'] != t['after']]
        self.assertEqual({t['id'] for t in changed}, {3,13})
        self.assertEqual({t['after']['surface'] for t in changed}, {1,2})
        self.assertTrue(all(t['after']['centerline'] == 900 for t in changed))
        self.assertEqual({g['id'] for g in p['guides'] if g['before'] != g['after']}, {1,2,11,12})
        self.ok('cancel-preview')
        self.assertEqual(original, self.dump())
        p = self.preview('datum 1 z 2*spec:height')
        self.ok('confirm ' + str(p['token']))
        changed_dump = self.dump()
        self.assertEqual({t['geometry']['centerline'] for t in self.refs()['timbers'] if t['id'] in (3,13)}, {1000})
        self.ok('undo'); self.assertEqual(original, self.dump())
        self.ok('redo'); self.assertEqual(changed_dump, self.dump())
        p = self.preview('spec height 650')
        self.ok('spec unrelated 1')
        self.reject_unchanged('confirm ' + str(p['token']))
        p = self.preview('spec height 650')
        self.ok('canvas-pos placement 1 800 900')
        self.ok('confirm ' + str(p['token']))
        self.assertIn('canvas-pos placement 1 800 900', self.dump())

    def test_frame_world_pose_and_derived_axis_recompute(self):
        self.walls(timbers=True)
        p = self.preview('surface 1 origin 100 0 0 u -x v +z rect 0 0 4000 3000')
        self.assertTrue(p['valid'], p)
        row = next(t for t in p['timbers'] if t['id'] == 3)
        self.assertEqual(row['before']['centerline'], row['after']['centerline'])
        self.assertNotEqual(row['before']['origin'], row['after']['origin'])
        self.assertNotEqual(row['before']['axes'], row['after']['axes'])
        self.ok('confirm ' + str(p['token']))
        old = self.dump()
        bad = self.preview('surface 1 origin 0 0 0 u +x v +y rect 0 0 4000 3000')
        self.assertFalse(bad['valid'])
        self.reject_unchanged('confirm ' + str(bad['token']))
        self.assertEqual(old, self.dump())
        self.assertTrue(any(v['clause']=='I7a' for v in bad['violations']))

    def test_invalid_one_face_rejects_all_and_round_trip(self):
        self.walls(timbers=True)
        self.ok('surface 3 origin 0 0 0 u +x v +z rect 0 0 4000 600')
        self.ok('guide 21 3 datum 1')
        for tid, edge in [(21,'e1'),(22,'e3')]:
            self.ok(f'timber {tid} 27 33 role boundary')
            self.ok(f'place {tid} on 3 at-face {edge} +v +n')
        self.ok('timber 23 27 33 role primary')
        self.ok('place 23 on 3 at-line guide 21 +u +n')
        old = self.dump()
        p = self.preview('spec height 900')
        self.assertFalse(p['valid'])
        self.assertTrue(any(v['timber']==23 for v in p['violations']))
        self.reject_unchanged('confirm ' + str(p['token']))
        self.assertEqual(old,self.dump())
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'shared.scene';path.write_text(old,encoding='utf-8')
            self.assertTrue(self.s.send('loadfile '+str(path))['ok'])
        self.assertEqual(old,self.dump())
        self.assertEqual(self.refs()['datums'][0]['guides'], [1,11,21])

    def test_hidden_guide_split_rejects_and_datum_identity_follows_piece(self):
        fixture = Path(__file__).resolve().parents[1] / '_ax_r13_anchor_follows.scene'
        for command in fixture.read_text().splitlines():
            if command and not command.startswith('#') and not command.startswith('apply-proj'):
                self.ok(command)
        self.ok('datum 1 y spec:掛線位置')
        self.ok('guide 1 5 datum 1')
        self.ok('spec hidden 9999')
        self.ok('guide 2 5 u spec:hidden')
        self.reject_unchanged('apply-proj 5 c1')
        self.ok('delete guide 2')
        self.ok('spec 掛線位置 2500')
        self.ok('apply-proj 5 c1')
        g = self.refs()['guides'][0]
        self.assertNotEqual(g['surface'],5)
        self.assertEqual((g['datum'],g['source'],g['worldPoint'][1]),(1,'datum',2500))

    def test_axis_exchange_resolves_dependencies_before_comparing_cache(self):
        self.walls()
        self.ok('delete guide 2')
        # A local V-direction guide uses a datum that currently runs along U.
        # Change both definitions within one transaction, then swap frame.
        self.ok('delete guide 1')
        self.ok('surface 1 origin 0 0 0 u +z v +x rect 0 0 4000 3000')
        self.ok('guide 1 1 datum 1')
        self.ok('guide 2 1 v guide:1')
        self.assertEqual(self.refs()['guides'][-1]['off'],500)
        # Changing frame back makes the LOCAL fixed-axis reference illegal.
        self.reject_unchanged('surface 1 origin 0 0 0 u +x v +z rect 0 0 4000 3000')


if __name__ == '__main__':
    unittest.main(verbosity=2)
