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
