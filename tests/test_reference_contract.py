"""Acceptance tests for the 2026-09-18 axioms (never mutate 公理層.md).

GEOMETRY_TEST_BRIDGE=/path/to/fresh/bridge python tests/test_reference_contract.py
"""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:  # `python tests/x.py` puts tests/ first, not the repo root
    sys.path.insert(0, str(ROOT))
from tests import _bridge  # noqa: E402


class ReferenceContract(unittest.TestCase):
    def projection_fixture(self, outline, column):
        self.ok('reset')
        self.ok('surface 1 origin 0 0 0 u +x v +y outline ' + outline)
        self.ok('column 1 at ' + column + ' z 0 100')

    def notch_projection_fixture(self):
        self.ok('reset')
        self.ok('surface 1 origin 0 0 100 u +x v +y outline '
                '0,0 100,0 100,100 60,100 60,40 40,40 40,100 0,100')

    def test_rect_outline_rectangle_plus_isolated_line_transaction(self):
        self.notch_projection_fixture()
        self.ok('column 1 at 45 0 size 10 40 z 0 100')
        self.ok('column 2 at 30 50 size 30 30 z 0 100')
        before = self.dump()
        query = self.s.send('obstacles 1')
        with self.subTest(phase='query'):
            self.assertFalse(query['ok'], 'R7 must retain the isolated x=60 contact line')
            self.assertIn('R7', query['error'])
        result = self.line('apply-proj 1 c1 c2')
        with self.subTest(phase='apply'):
            self.assertFalse(result['ok'], 'c2 must not lose contact with the right split piece')
        self.assertEqual(before, self.dump(), 'R8 must roll back the earlier c1 split too')

    def test_rect_outline_strip_plus_isolated_line(self):
        for prior_split in (False, True):
            with self.subTest(prior_split=prior_split):
                self.notch_projection_fixture()
                self.ok('column 1 at 45 0 size 10 40 z 0 100')
                self.ok('beam 2 along x from 30 to 60 at 65 width 30 depth 10 top 100')
                before = self.dump()
                command = 'apply-proj 1 ' + ('c1 ' if prior_split else '') + 'b2 cut-strip'
                result = self.line(command)
                self.assertFalse(result['ok'], 'STRIP must retain the isolated contact line')
                self.assertIn('R7', result['error'])
                self.assertEqual(before, self.dump(), 'all earlier cuts must roll back')

    def test_rect_outline_rectangle_plus_isolated_point(self):
        self.projection_fixture('0,0 100,0 100,100 60,100 60,80 80,80 '
                                '80,40 40,40 40,100 0,100', '30 50 size 30 30')
        before = self.dump()
        result = self.line('apply-proj 1 c1')
        self.assertFalse(result['ok'], 'rectangle plus the isolated point (60,80) is degenerate')
        self.assertIn('R7', result['error'])
        self.assertEqual(before, self.dump())

    def test_rect_outline_uncut_complex_strip_is_noop(self):
        self.notch_projection_fixture()
        self.ok('beam 1 along x from 30 to 70 at 65 width 30 depth 10 top 100')
        self.assertEqual('strip', self.s.send('obstacles 1')['items'][0]['cls'])
        before = self.dump()
        self.ok('apply-proj 1 b1')
        self.assertEqual(before, self.dump(), 'R12 uncut strip does not alter geometry')

    def test_rect_outline_uncut_strip_continues_with_later_valid_item(self):
        self.notch_projection_fixture()
        self.ok('beam 1 along x from 30 to 70 at 65 width 30 depth 10 top 100')
        self.ok('column 2 at 10 10 size 10 10 z 0 100')
        self.ok('apply-proj 1 b1 c2')
        self.assertIn('hole ', self.dump(), 'an uncut strip must not return before applying c2')

    def test_rect_outline_uncut_strip_still_validates_later_missing_id(self):
        self.notch_projection_fixture()
        self.ok('beam 1 along x from 30 to 70 at 65 width 30 depth 10 top 100')
        before = self.dump()
        result = self.line('apply-proj 1 b1 c99')
        self.assertFalse(result['ok'])
        self.assertIn('不存在', result['error'], 'R15 must validate the item after an uncut strip')
        self.assertEqual(before, self.dump())

    def test_rect_outline_uncut_strip_still_requires_unique_piece(self):
        self.notch_projection_fixture()
        self.ok('column 1 at 45 0 size 10 40 z 0 100')
        self.ok('beam 1 along x from 30 to 70 at 65 width 30 depth 10 top 100')
        before = self.dump()
        result = self.line('apply-proj 1 c1 b1')
        self.assertFalse(result['ok'])
        self.assertIn('橫跨拆分線', result['error'], 'R14 applies even without cut-strip')
        self.assertEqual(before, self.dump())

    def test_rect_outline_uncut_strip_still_requires_contact(self):
        self.notch_projection_fixture()
        self.ok('beam 1 along x from 110 to 120 at 65 width 10 depth 10 top 100')
        before = self.dump()
        result = self.line('apply-proj 1 b1')
        self.assertFalse(result['ok'])
        self.assertIn('不與任何面片接觸', result['error'])
        self.assertEqual(before, self.dump())

    def test_rect_outline_counterexample_A_rejects_disconnected_contact(self):
        self.projection_fixture('0,0 100,0 100,100 60,100 60,40 40,40 40,100 0,100',
                                '30 50 size 40 30')
        before = self.dump()
        result = self.s.send('obstacles 1')
        self.assertFalse(result['ok'], 'counterexample A must not invent a hole across the notch')
        self.assertIn('R7', result['error'])
        self.assertIn('單一矩形', result['error'])
        result = self.line('apply-proj 1 c1')
        self.assertFalse(result['ok'])
        self.assertIn('R7', result['error'])
        self.assertEqual(before, self.dump(), 'counterexample A must roll back completely')

    def test_rect_outline_counterexample_B_clips_ridge_and_applies_split(self):
        self.projection_fixture('0,0 100,0 100,50 60,50 60,90 40,90 40,50 0,50',
                                '20 70 size 60 10')
        items = self.s.send('obstacles 1')['items']
        self.assertEqual([{'id':1, 'type':'column', 'cls':'split', 'rect':[40,70,60,80]}],
                         items, 'counterexample B must retain the positive-area ridge intersection')
        self.ok('apply-proj 1 c1')
        dump = self.dump()
        self.assertIn('boundary 2', dump)
        self.assertNotIn('hole ', dump)

    def test_rect_outline_three_residual_components_rejects_and_rolls_back(self):
        outline = ('0,10 10,10 10,0 20,0 20,10 30,10 30,0 '
                   '40,0 40,20 20,20 20,30 10,30 10,20 0,20')
        for strip in (False, True):
            for prior_hole in (False, True):
                with self.subTest(strip=strip, prior_hole=prior_hole):
                    self.ok('reset')
                    self.ok('surface 1 origin 0 0 0 u +x v +y outline ' + outline)
                    if strip:
                        self.ok('beam 1 along x from -10 to 50 at 15 width 10 depth 10 top 0')
                    else:
                        self.ok('column 1 at -10 10 size 60 10 z 0 100')
                    if prior_hole:
                        self.ok('column 2 at 12 2 size 4 4 z 0 100')
                    before, refs = self.dump(), self.refs()
                    command = 'apply-proj 1 ' + ('c2 ' if prior_hole else '')
                    command += 'b1 cut-strip' if strip else 'c1'
                    result = self.line(command)
                    self.assertFalse(result['ok'], 'R3/R4: three residual components cannot become two rings')
                    self.assertIn('拆分退化', result['error'])
                    self.assertEqual(before, self.dump(), 'R8 must also roll back an earlier valid hole')
                    self.assertEqual(refs, self.refs())
                    self.ok('undo')
                    self.ok('redo')
                    self.assertEqual(before, self.dump(), 'failed apply must not leave a redo transaction')
                    self.roundtrip()

    def test_rect_outline_two_piece_difference_is_complete_after_redo_and_reopen(self):
        fixtures = [
            ('0,10 10,10 10,0 20,0 20,10 30,10 30,20 20,20 20,30 10,30 10,20 0,20',
             '-10 10 size 60 10', (0,10,30,20), 200),
            ('0,0 100,0 100,50 60,50 60,90 40,90 40,50 0,50',
             '20 70 size 60 10', (40,70,60,80), 5600),
        ]
        def cells(verts):
            l, b = min(x for x,y in verts), min(y for x,y in verts)
            r, t = max(x for x,y in verts), max(y for x,y in verts)
            def inside(x,y):
                return sum(a[0] == e[0] and 2*min(a[1],e[1]) < 2*y+1 < 2*max(a[1],e[1])
                           and 2*a[0] > 2*x+1 for a,e in zip(verts,verts[1:]+verts[:1])) % 2 == 1
            return {(x,y) for x in range(l,r) for y in range(b,t) if inside(x,y)}
        for outline, column, rect, area in fixtures:
            with self.subTest(outline=outline):
                self.projection_fixture(outline, column)
                before = self.dump()
                original = [list(map(int,p.split(','))) for p in outline.split()]
                u0,v0,u1,v1 = rect
                expected = cells(original) - {(x,y) for x in range(u0,u1) for y in range(v0,v1)}
                self.assertEqual(area, len(expected))
                def assert_difference():
                    loops = [self.s.send('boundary '+str(i))['loops'][0]['verts'] for i in (1,2)]
                    pieces = [cells(v) for v in loops]
                    self.assertFalse(pieces[0] & pieces[1], 'split pieces must have disjoint interiors')
                    self.assertEqual(expected, pieces[0] | pieces[1], 'full saved union must equal the exact difference')
                    signed = [abs(sum(a[0]*e[1]-a[1]*e[0] for a,e in zip(v,v[1:]+v[:1]))) for v in loops]
                    self.assertEqual(2*area, sum(signed), 'saved polygon area must equal the exact remainder')
                    self.assertFalse(any(u0 <= x < u1 and v0 <= y < v1 for x,y in pieces[0] | pieces[1]))
                self.ok('apply-proj 1 c1')
                assert_difference()
                after = self.dump()
                self.ok('undo')
                self.assertEqual(before, self.dump())
                self.ok('redo')
                self.assertEqual(after, self.dump())
                assert_difference()
                self.roundtrip()
                assert_difference()

    def test_rect_outline_unselected_complex_column_does_not_block_valid_item(self):
        self.projection_fixture('0,0 100,0 100,100 60,100 60,40 40,40 40,100 0,100',
                                '30 50 size 40 30')
        self.ok('column 2 at 10 10 size 10 10 z 0 100')
        self.ok('apply-proj 1 c2')
        self.assertIn('hole ', self.dump())

    def test_rect_outline_strip_reclassification_uses_exact_contact(self):
        self.ok('reset')
        self.ok('surface 1 origin 0 0 100 u +x v +y outline '
                '0,0 100,0 100,50 60,50 60,90 40,90 40,50 0,50')
        self.ok('beam 1 along x from 20 to 80 at 75 width 10 depth 10 top 100')
        self.assertEqual('strip', self.s.send('obstacles 1')['items'][0]['cls'])
        self.ok('apply-proj 1 b1 cut-strip')
        self.assertIn('boundary 2', self.dump())

    def test_rect_outline_real_hole_no_contact_and_notch_controls(self):
        for column, expected in [('10 10 size 10 10', ('hole',[10,10,20,20])),
                                 ('110 110 size 10 10', None),
                                 ('-10 10 size 30 10', ('notch',[0,10,20,20]))]:
            with self.subTest(column=column):
                self.projection_fixture('0,0 100,0 100,100 0,100', column)
                items = self.s.send('obstacles 1')['items']
                if expected is None:
                    self.assertEqual([], items)
                else:
                    self.assertEqual(expected, (items[0]['cls'], items[0]['rect']))
                    self.ok('apply-proj 1 c1')

    def setUp(self):
        self.s = _bridge.BridgeSession()
        self.addCleanup(self.s.close)

    def line(self, text):
        return self.s.send('line ' + text)

    def ok(self, text):
        r = self.line(text)
        self.assertTrue(r['ok'], r)
        return r

    def dump(self):
        return self.s.send('dump')['text']

    def refs(self):
        return self.s.send('references')

    def test_schedule_fingerprint_is_native_read_only_and_tracks_definitions(self):
        before = self.dump()
        refs = self.refs()
        fingerprint = refs['sourceFingerprint']
        self.assertRegex(fingerprint, r'^[a-f0-9]{64}$')
        self.assertEqual(before, self.dump())
        self.assertEqual(fingerprint, self.refs()['sourceFingerprint'])
        self.ok('canvas-pos boundary 1 100 200')
        self.assertEqual(fingerprint, self.refs()['sourceFingerprint'])
        self.ok('spec schedule_revision 99')
        changed = self.refs()['sourceFingerprint']
        self.assertNotEqual(fingerprint, changed)
        self.ok('undo')
        self.assertEqual(fingerprint, self.refs()['sourceFingerprint'])
        self.ok('redo')
        self.assertEqual(changed, self.refs()['sourceFingerprint'])

    def test_schedule_reference_preserves_legal_zero_placement_and_timber_identity(self):
        self.ok('reset')
        self.ok('boundary 1 outline 0,0 4000,0 4000,3000 0,3000')
        self.ok('placement 0 on boundary 1 origin 0 0 2500 u +x v +y')
        self.ok('timber 0 27 33 role boundary')
        self.ok('place 0 on 0 at-face e0 +u +n')
        before=self.dump()
        refs=self.refs()
        self.assertEqual(0,refs['timbers'][0]['id'])
        self.assertEqual(0,refs['timbers'][0]['geometry']['surface'])
        self.assertEqual(4000,refs['timbers'][0]['geometry']['length'])
        self.assertEqual(before,self.dump())

    def geom(self, tid):
        return next(t['geometry'] for t in self.refs()['timbers'] if t['id'] == tid)

    def preview(self, command):
        before = self.dump()
        r = self.line(command)
        self.assertIn('preview', r, r)
        self.assertEqual(before, self.dump(), 'I8a preview must leave World unchanged')
        return r['preview']

    def confirm(self, p):
        return self.ok('confirm ' + str(p['token']))

    def test_grid_source_metadata_and_read_only_draft(self):
        self.ok('reset')
        self.ok('surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000')
        original = self.dump()
        command = 'grid 1 on 1 u series 100 200 3 v panel 400 gap 5 from 0'
        preview = self.s.send('grid-preview ' + command)
        self.assertTrue(preview['ok'], preview)
        self.assertEqual(original, self.dump())
        self.assertEqual(preview['grid']['u'], [100, 300, 500])
        self.assertEqual(preview['grid']['v'][:2], [402, 807])
        self.ok(command)
        grid = self.refs()['grids'][0]
        self.assertEqual(grid, preview['grid'])
        self.assertEqual(grid['uDefinition'], {'source': 'series', 'start': 100, 'step': 200, 'count': 3})
        self.assertEqual(grid['vDefinition'], {'source': 'panel', 'panel': 400, 'gap': 5,
                                                'anchor': 0, 'anchorExplicit': True})
        failed = self.s.send('grid-preview grid 1 on 1 u series 3900 200 3')
        self.assertFalse(failed['ok'], failed)
        self.assertEqual(grid, self.refs()['grids'][0])

    def test_grid_line_roles_follow_main_length_axis(self):
        self.ok('reset')
        self.ok('surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000')
        self.ok('grid 1 on 1 main-along u u 500 1500 v 300 900')
        grid = self.refs()['grids'][0]
        self.assertEqual(grid['mainAlong'], 'u')
        self.assertEqual([(x['axis'], x['role'], x['priority']) for x in grid['lines']],
                         [('u', 'secondary', 3), ('u', 'secondary', 3),
                          ('v', 'primary', 2), ('v', 'primary', 2)])
        self.assertIn('grid 1 on 1 main-along u v 300 900', self.dump())
        self.roundtrip()
        before = self.dump()
        self.assertFalse(self.line('grid 1 on 1 main-along z')['ok'])
        self.assertFalse(self.line('grid 1 on 1 main-along u u 500 1500 v 900 300')['ok'])
        self.assertEqual(before, self.dump())
        self.ok('grid 1 on 1 main-along v')
        self.assertEqual([(x['axis'], x['priority']) for x in self.refs()['grids'][0]['lines']],
                         [('u', 2), ('u', 2), ('v', 3), ('v', 3)])
        self.roundtrip()

    def test_grid_role_legacy_and_source_validation(self):
        self.ok('reset')
        self.ok('surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000')
        self.ok('grid 1 on 1 u 500')
        self.assertIsNone(self.refs()['grids'][0]['mainAlong'])
        self.assertIsNone(self.refs()['grids'][0]['lines'][0]['role'])
        before = self.dump()
        self.assertFalse(self.line('grid 1 on 1 main-along u')['ok'])
        self.assertEqual(before, self.dump())
        self.ok('grid 1 on 1 main-along v')
        self.assertEqual(self.refs()['grids'][0]['lines'][0]['priority'], 2)
        self.ok('grid 1 on 1 main-along none')
        self.assertIsNone(self.refs()['grids'][0]['lines'][0]['priority'])
        self.assertEqual(before, self.dump())
        self.roundtrip()

    def test_grid_main_direction_never_rewrites_existing_timber(self):
        original = self.geom(3)
        role = next(t['role'] for t in self.refs()['timbers'] if t['id'] == 3)
        self.ok('grid 7 on 1 main-along u u 1000 v 500')
        self.assertEqual(self.refs()['grids'][0]['lines'][0]['role'], 'secondary')
        self.ok('timber 4 27 33 role primary')
        self.ok('place 4 on 1 at-line grid 7 u 0 +v +n')
        grid_timber = self.geom(4)
        self.ok('grid 7 on 1 main-along v')
        self.assertEqual(self.geom(3), original)
        self.assertEqual(self.geom(4), grid_timber)
        self.assertEqual(next(t['role'] for t in self.refs()['timbers'] if t['id'] == 3), role)
        self.assertEqual(next(t['role'] for t in self.refs()['timbers'] if t['id'] == 4), 'primary')
        self.ok('undo')
        self.assertEqual(self.refs()['grids'][0]['mainAlong'], 'u')
        self.ok('redo')
        self.assertEqual(self.refs()['grids'][0]['mainAlong'], 'v')
        self.roundtrip()

    def test_default_is_supported_reference_world(self):
        self.assertEqual(self.geom(3)['length'], 2946)
        self.assertEqual(self.geom(3)['centerline'], 500)
        d = self.dump()
        self.assertIn('at-line guide 1', d)
        self.assertNotIn(' at ', d)
        self.assertNotIn('span-auto', d)
        self.assertNotIn('grid-ref', d)

    def test_old_syntax_and_naked_mm_are_rejected_atomically(self):
        for cmd in ['guide 2 1 u 500', 'move 1 900', 'timber 9 500 20 20 role primary',
                    'span-auto 3', 'place 3 on 1 at 10 20 +v +n',
                    'place 3 on 1 at-guides 1 2 +v +n',
                    'place 3 on 1 at-grid 1 u 0 +v +n']:
            with self.subTest(command=cmd):
                before = self.dump()
                self.assertFalse(self.line(cmd)['ok'])
                self.assertEqual(before, self.dump())

    def test_spec_capacity_reports_resource_and_preserves_world(self):
        self.ok('reset')
        for index in range(64):
            self.ok(f'spec capacity_{index} {index}')
        before = self.dump()
        rejected = self.line('spec capacity_overflow 100')
        self.assertFalse(rejected['ok'], rejected)
        self.assertRegex(rejected['error'], r'spec.*capacity')
        self.assertEqual(before, self.dump(), 'Capacity rejection must leave World unchanged')
        self.ok('spec capacity_0 100')
        self.assertIn('spec capacity_0 100', self.dump())

    def test_guide_capacity_reports_resource_and_preserves_world(self):
        self.ok('reset')
        self.ok('surface 1 origin 0 0 0 u +x v +y rect 0 0 4000 3000')
        self.ok('spec offset 100')
        for guide_id in range(1, 17):
            self.ok(f'guide {guide_id} 1 v spec:offset')
        before = self.dump()
        rejected = self.line('guide 17 1 v spec:offset')
        self.assertFalse(rejected['ok'], rejected)
        self.assertRegex(rejected['error'], r'guide.*capacity')
        self.assertEqual(before, self.dump(), 'Capacity rejection must leave World unchanged')
        self.ok('guide 1 1 v 2*spec:offset')
        self.assertEqual(len(self.refs()['guides']), 16)
        self.assertEqual(next(g['off'] for g in self.refs()['guides'] if g['id'] == 1), 200)

    def test_spec_redeclare_requires_preview_then_moves_timber(self):
        p = self.preview('spec 主支中線 900')
        self.assertTrue(p['valid'], p)
        row = next(t for t in p['timbers'] if t['id'] == 3)
        self.assertEqual((row['before']['centerline'], row['after']['centerline']), (500, 900))
        self.confirm(p)
        self.assertEqual(self.geom(3)['centerline'], 900)
        self.ok('undo')
        self.assertEqual(self.geom(3)['centerline'], 500)
        self.ok('redo')
        self.assertEqual(self.geom(3)['centerline'], 900)

    def test_guide_move_keeps_expression_and_preview(self):
        p = self.preview('move 1 1/2*edge:e1:u')
        self.assertTrue(p['valid'], p)
        self.confirm(p)
        self.assertEqual(self.geom(3)['centerline'], 2000)
        self.assertIn('1/2*edge:e1:u', self.dump())

    def test_floor_is_after_exact_sum_including_negative(self):
        self.s.send('reset')
        self.ok('surface 1 origin 0 0 0 u +x v +y rect -100 -100 100 100')
        self.ok('spec odd 3')
        for gid, expr, want in [(1, '-1/2*spec:odd', -2), (2, '1/2*spec:odd+1/2*spec:odd', 3),
                                (3, '1/3*spec:odd+1/6*spec:odd', 1)]:
            self.ok(f'guide {gid} 1 u {expr}')
            self.assertEqual(next(g['off'] for g in self.refs()['guides'] if g['id'] == gid), want)

    def test_reference_families_and_wrong_axis(self):
        self.ok('grid 1 on 1 u panel 400 gap 5')
        cases = [('edge:e1:u', 4000), ('vertex:v2:u', 4000), ('grid:1:u:1', 807),
                 ('panel:1:u+gap:1:u', 405), ('timber:3:u:lo', 487), ('timber:3:A', 27),
                 ('guide:1', 500)]
        for i, (expr, want) in enumerate(cases, 2):
            self.ok(f'guide {i} 1 v {expr}')
            self.assertEqual(next(g['off'] for g in self.refs()['guides'] if g['id'] == i), want)
        self.assertFalse(self.line('guide 15 1 v edge:e0:v')['ok'])
        self.assertFalse(self.line('guide 15 1 v spec:undeclared')['ok'])

    def test_guide_cycle_and_cross_face_rejected(self):
        self.ok('guide 2 1 v guide:1')
        before = self.dump()
        self.assertFalse(self.line('move 1 guide:2')['ok'])
        self.assertEqual(before, self.dump())
        self.ok('surface 2 origin 0 0 0 u +x v +y rect 0 0 4000 3000')
        self.assertFalse(self.line('guide 3 2 v guide:1')['ok'])

    def test_invalid_preview_has_item_clause_expected_actual(self):
        p = self.preview('spec 主支中線 0')
        self.assertFalse(p['valid'])
        self.assertTrue(p['violations'])
        self.assertTrue(all(v['clause'] and v['expected'] and v['actual'] for v in p['violations']))
        self.assertTrue(any(v['timber'] == 3 for v in p['violations']))
        before = self.dump()
        self.assertFalse(self.line('confirm ' + str(p['token']))['ok'])
        self.assertEqual(before, self.dump())

    def test_preview_can_be_cancelled_and_stale_token_cannot_apply(self):
        p = self.preview('spec 主支中線 900')
        self.ok('cancel-preview')
        self.assertFalse(self.line('confirm ' + str(p['token']))['ok'])
        p = self.preview('spec 主支中線 900')
        self.ok('spec unrelated 10')
        self.assertFalse(self.line('confirm ' + str(p['token']))['ok'])
        self.assertEqual(self.geom(3)['centerline'], 500)

    def test_boundary_change_recomputes_lengths_with_preview(self):
        p = self.preview('boundary 1 outline 0,0 4000,0 4000,3500 0,3500')
        self.assertTrue(p['valid'], p)
        self.assertEqual(next(t['after']['length'] for t in p['timbers'] if t['id'] == 3), 3446)
        self.confirm(p)
        self.assertEqual(self.geom(3)['length'], 3446)

    def test_frame_rebind_changes_world_pose_without_losing_references(self):
        p = self.preview('placement 1 on boundary 1 origin 100 200 3000 u +y v -x')
        self.assertTrue(p['valid'], p)
        self.confirm(p)
        self.assertEqual(self.geom(3)['origin'], [73, 714, 3000])

    def test_grid_move_and_disappearing_index(self):
        self.ok('grid 1 on 1 u 1500 2500')
        self.ok('timber 4 27 33 role primary')
        self.ok('place 4 on 1 at-line grid 1 u 1 +v +n')
        p = self.preview('grid 1 on 1 u 1600 2600')
        self.assertTrue(p['valid'], p)
        self.confirm(p)
        self.assertEqual(self.geom(4)['centerline'], 2600)
        p = self.preview('grid 1 on 1 u 1600')
        self.assertFalse(p['valid'])

    def test_dependency_closure_moves_secondary_stop_and_length(self):
        self.ok('grid 1 on 1 u 2500 v 1000')
        self.ok('timber 4 27 33 role primary')
        self.ok('place 4 on 1 at-line grid 1 u 0 +v +n')
        self.ok('timber 5 27 33 role secondary')
        self.ok('place 5 on 1 at-line grid 1 v 0 between t3 t4 +u +n')
        self.assertEqual(self.geom(5)['length'], 1973)
        p = self.preview('spec 主支中線 900')
        self.assertTrue(p['valid'], p)
        self.assertEqual(next(t['after']['length'] for t in p['timbers'] if t['id'] == 5), 1573)
        self.confirm(p)
        self.assertEqual(self.geom(5)['length'], 1573)
        self.roundtrip()

    def test_at_face_timber_ambiguous_then_unique_near_wall(self):
        self.ok('timber 4 27 33 role primary')
        r = self.line('place 4 on 1 at-face t3 +v +n')
        self.assertFalse(r['ok'], r)
        self.assertIn('ambiguous', r['error'])
        self.ok('delete timber 4')
        p = self.preview('move 1 1/2*timber:3:A')
        self.assertTrue(p['valid'], p)
        self.confirm(p)
        self.ok('timber 4 27 33 role primary')
        self.ok('place 4 on 1 at-face t3 +v +n')
        self.assertEqual(self.geom(4)['centerline'], 40)

    def test_timber_redeclare_recomputes_cross_section_and_dependents(self):
        p = self.preview('timber 1 40 33 role boundary')
        self.assertTrue(p['valid'], p)
        self.confirm(p)
        self.assertEqual(self.geom(3)['length'], 2933)

    def test_delete_referenced_guide_or_support_cannot_commit(self):
        for command in ['delete guide 1', 'delete timber 1']:
            p = self.preview(command)
            self.assertFalse(p['valid'], p)
            self.assertFalse(self.line('confirm ' + str(p['token']))['ok'])

    def test_drag_snap_writes_reference_or_refuses(self):
        self.ok('spec target 900')
        r = self.s.send('snap 1 v 1 903 8')
        self.assertTrue(r['ok'], r)
        self.assertEqual(r['expression'], 'spec:target')
        self.assertFalse(self.s.send('snap 1 v 1 1200 8')['ok'])

    def test_odd_panel_gap_and_anchor_freezing(self):
        self.ok('grid 1 on 1 u panel 400 gap 5 from 100')
        self.ok('guide 2 1 v grid:1:u:0')
        self.assertEqual(next(g['off'] for g in self.refs()['guides'] if g['id'] == 2), 502)
        self.roundtrip()

    def test_failed_group_after_preview_rolls_back(self):
        self.preview('spec 主支中線 900')
        before=self.dump()
        self.ok('history-begin')
        self.ok('boundary 8 outline 0,0 50,0 50,50 0,50')
        self.assertFalse(self.line('boundary 8 bogus')['ok'])
        self.assertEqual(self.dump(),before)
        self.assertFalse(self.line('history-end')['ok'])
        self.assertFalse(self.line('undo')['ok'])

    def test_multiple_affected_timbers_are_reported(self):
        self.ok('guide 2 1 v spec:主支中線+timber:3:A')
        self.ok('timber 4 27 33 role primary')
        self.ok('place 4 on 1 at-line guide 2 +v +n')
        p=self.preview('spec 主支中線 -100')
        self.assertFalse(p['valid'])
        self.assertTrue({3,4}.issubset({e['timber'] for e in p['violations']}),p)
        self.assertFalse(self.line('confirm '+str(p['token']))['ok'])

    def test_projection_split_rebinds_referenced_timber_with_preview(self):
        self.s.send('reset')
        for line in (ROOT/'_ax_r13_anchor_follows.scene').read_text(encoding='utf-8').splitlines():
            if line.startswith(('surface ', 'space ')):
                self.ok(line)
        self.ok('boundary 1 outline 0,0 4000,0 4000,3000 0,3000 hole 3300,500 3800,500 3800,800 3300,800 hole 3300,2200 3800,2200 3800,2500 3300,2500')
        self.ok('beam 1 in 1 along y from 0 to 3000 at 2800 width 300 depth 500')
        self.ok('spec 分片主支 3500')
        self.ok('guide 1 1 v spec:分片主支')
        self.ok('timber 1 27 33 role primary')
        self.ok('place 1 on 1 at-line guide 1 between h0e2 h1e0 +v +n')
        before=self.geom(1)
        p=self.preview('apply-proj 1 b1 cut-strip')
        self.assertTrue(p['valid'],p)
        self.confirm(p)
        after=self.geom(1)
        self.assertNotEqual(before['surface'],after['surface'])
        self.assertEqual(before['origin'],after['origin'])
        self.assertEqual(after['length'],1400)
        self.roundtrip()

    def test_timber_zero_id_is_a_real_reference(self):
        self.s.send('reset')
        for line in ['surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
                     'timber 90 20 20 role boundary','place 90 on 1 at-face e0 +u +n',
                     'timber 91 20 20 role boundary','place 91 on 1 at-face e2 +u +n',
                     'spec 貼近左牆 13','guide 1 1 v spec:貼近左牆',
                     'timber 0 27 33 role primary','place 0 on 1 at-line guide 1 +v +n',
                     'timber 1 27 33 role primary','place 1 on 1 at-face t0 +v +n']:
            self.ok(line)
        self.assertEqual(self.geom(1)['centerline'],40)
        self.assertIn('at-face t0',self.dump())
        self.assertEqual(next(t['definition'] for t in self.refs()['timbers'] if t['id'] == 1),
                         {'anchor': 'at-face t0', 'selector': '', 'priority': 2})
        self.roundtrip()

    def test_timber_definition_preserves_anchor_selector_priority_and_zero_ids(self):
        surface = 'surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000'
        supports = ['timber 90 20 33 role boundary', 'place 90 on 1 at-face e0 +u +n',
                    'timber 91 20 33 role boundary', 'place 91 on 1 at-face e2 +u +n']
        cases = [
            ([], 'timber 0 27 33 role boundary', 'at-face e0', '', '+u', 1),
            ([*supports, 'spec center_x 1000', 'guide 0 1 v spec:center_x'],
             'timber 0 27 33 role custom priority 7', 'at-line guide 0', 'through 600', '+v', 7),
            ([*supports, 'grid 0 on 1 main-along v u 1000'],
             'timber 0 27 33 role custom priority 9', 'at-line grid 0 u 0', 'through 700', '+v', 9),
            (['timber 90 20 33 role boundary', 'place 90 on 1 at-face e0 +u +n',
              'timber 91 20 33 role boundary', 'place 91 on 1 at-face e2 +u +n',
              'spec center_x 1000', 'guide 0 1 v spec:center_x'],
             'timber 0 27 33 role primary', 'at-line guide 0', 'between t90 t91', '+v', 2),
        ]
        for setup, declaration, anchor, selector, direction, priority in cases:
            with self.subTest(anchor=anchor, selector=selector):
                self.ok('reset')
                for line in [surface, *setup, declaration,
                             f'place 0 on 1 {anchor} {selector} {direction} +n']:
                    self.ok(line)
                timber = next(t for t in self.refs()['timbers'] if t['id'] == 0)
                self.assertEqual(timber['definition'], {'anchor': anchor, 'selector': selector, 'priority': priority})
                before = self.dump()
                self.roundtrip()
                self.assertEqual(before, self.dump())
                self.assertEqual(next(t['definition'] for t in self.refs()['timbers'] if t['id'] == 0), timber['definition'])

    def test_timber_definition_keeps_hole_edge_references(self):
        self.ok('reset')
        for line in [
            'surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000 hole 3300,500 3800,500 3800,800 3300,800 hole 3300,2200 3800,2200 3800,2500 3300,2500',
            'spec center_x 3500', 'guide 0 1 v spec:center_x',
            'timber 0 27 33 role primary', 'place 0 on 1 at-line guide 0 between h0e2 h1e0 +v +n',
        ]:
            self.ok(line)
        self.assertEqual(self.refs()['timbers'][0]['definition'],
                         {'anchor': 'at-line guide 0', 'selector': 'between h0e2 h1e0', 'priority': 2})
        self.roundtrip()

    def test_collinear_extra_vertex_is_valid(self):
        self.s.send('reset')
        self.ok('boundary 1 outline 0,0 2000,0 4000,0 4000,3000 0,3000')
        self.assertEqual(len(self.s.send('boundary 1')['loops'][0]['verts']),5)

    def roundtrip(self):
        before, refs = self.dump(), self.refs()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'references.scene'
            path.write_text(before, encoding='utf-8')
            # Loading over an identical live World lets a no-op loader pass.
            # Remove that oracle shortcut: replay must reconstruct definitions
            # and geometry from the saved bytes into an empty World.
            self.ok('reset')
            self.assertNotEqual(before, self.dump())
            r = self.s.send('loadfile ' + str(path))
            self.assertTrue(r['ok'], r)
        self.assertEqual(before, self.dump())
        self.assertEqual(refs, self.refs())

    def test_dump_orders_guides_after_referenced_timber(self):
        self.ok('guide 2 1 v timber:3:u:hi+timber:3:A')
        self.ok('timber 4 27 33 role primary')
        self.ok('place 4 on 1 at-line guide 2 +v +n')
        self.roundtrip()

    def test_boundary_role_priority_and_orphan_file_rejection(self):
        self.s.send('reset')
        self.ok('surface 1 origin 0 0 0 u +x v +y rect 0 0 4000 3000')
        before, refs = self.dump(), self.refs()
        self.assertFalse(self.line('timber 1 27 33')['ok'])
        self.assertFalse(self.line('timber 1 27 33 role custom')['ok'])
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'orphan.scene'
            p.write_text('boundary 1 outline 0,0 10,0 10,10 0,10\ntimber 1 2 2 role primary\n',encoding='utf-8')
            self.assertFalse(self.s.send('loadfile '+str(p))['ok'])
        self.assertEqual(before, self.dump(), 'I9 rejected replay must preserve the current World')
        self.assertEqual(refs, self.refs())


if __name__ == '__main__':
    unittest.main(verbosity=2)
