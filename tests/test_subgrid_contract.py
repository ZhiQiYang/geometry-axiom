"""Black-box acceptance for approved D19 / I25 / R23 (GEO-204).

Run against a freshly compiled bridge:
    GEOMETRY_TEST_BRIDGE=/path/to/bridge python tests/test_subgrid_contract.py

All rejection checks compare the complete dump. The tests intentionally use the
public bridge protocol, not internal structs.
Every reject(command, why=...) also pins the *reason*: `why` is a substring (or a tuple
of substrings, all required) of the clause code / wording the bridge reports, so a
mistyped command that is refused for the wrong reason (usage text, unknown command)
cannot pass as "the rule rejected it". A gated edit answers ok=false with the generic
"I8a: impact preview required" and keeps the real reason in preview.violations[].actual;
rejection_reason() reads that, not the generic line. Each rejection below supplies
its expected reason; malformed division tokens and boundary revalidation name their specific cause (GEO-246).
S14/S15 (visibility, hit testing, keyboard and responsive UI) live in cdp_test.js.
"""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:  # `python tests/x.py` puts tests/ first, not the repo root
    sys.path.insert(0, str(ROOT))
from tests import _bridge  # noqa: E402

# R6(b)/I13: direct at-line use of a subgrid line needs a fully supported span inside cell C.
NO_LOCAL_SPAN = ('I13/R6', '沒有兩端獲得支撐的完整跨距')
NO_BETWEEN_SPAN = 'between 指名的兩端之間沒有合法跨距'


def rejection_reason(result):
    """Why a refused command was refused.

    A preview-gated edit (ok=false + preview.valid=false) carries the generic
    "I8a: impact preview required" in `error`; its real reason is in
    preview.violations[].actual. Other refusals put the reason in `error`."""
    violations = (result.get('preview') or {}).get('violations') or []
    actual = [str(v['actual']) for v in violations if v.get('actual')]
    return '\n'.join(actual) if actual else str(result.get('error', ''))


class SubgridContract(unittest.TestCase):
    def setUp(self):
        self.s = _bridge.BridgeSession()
        self.addCleanup(self.s.close)
        self.ok('reset')

    def line(self, command):
        return self.s.send('line ' + command)

    def ok(self, command):
        result = self.line(command)
        self.assertTrue(result['ok'], (command, result))
        self.assertNotIn('preview', result, (command, result))
        return result

    def dump(self):
        return self.s.send('dump')['text']

    def refs(self):
        return self.s.send('references')

    def grid(self, gid=2):
        return next(g for g in self.refs()['grids'] if g['id'] == gid)

    def guide(self, gid):
        return next(g for g in self.refs()['guides'] if g['id'] == gid)

    def timber(self, tid):
        return next(t for t in self.refs()['timbers'] if t['id'] == tid)

    def reject(self, command, why=None):
        """`why`: substring, or tuple of substrings (all required), of rejection_reason(); None = reason not pinned."""
        before = self.dump()
        result = self.line(command)
        self.assertFalse(result['ok'], (command, result))
        if 'preview' in result:
            self.assertFalse(result['preview']['valid'], (command, result))
            confirmation = self.line('confirm ' + str(result['preview']['token']))
            self.assertFalse(confirmation['ok'], confirmation)
        self.assertEqual(before, self.dump(), command)
        self.assertTrue(result.get('error'), result)
        if why is not None:
            reason = rejection_reason(result)
            for needle in ((why,) if isinstance(why, str) else why):
                self.assertIn(needle, reason, f'{command!r} was refused for a different reason: {reason!r}')
        return result

    def preview(self, command, valid=True):
        before = self.dump()
        result = self.line(command)
        self.assertIn('preview', result, (command, result))
        self.assertEqual(valid, result['preview']['valid'], (command, result))
        self.assertEqual(before, self.dump(), 'I8a preview must leave World untouched')
        return result['preview']

    def confirm(self, preview):
        self.ok('confirm ' + str(preview['token']))

    def apply(self, command):
        """Commit routine setup changes whether or not their impact needs approval."""
        result = self.line(command)
        if 'preview' in result:
            self.assertTrue(result['preview']['valid'], (command, result))
            self.confirm(result['preview'])
        else:
            self.assertTrue(result['ok'], (command, result))
        return result

    def surface(self, outline='0,0 4000,0 4000,3000 0,3000'):
        self.ok('surface 1 origin 0 0 2500 u +x v +y outline ' + outline)

    @staticmethod
    def child(gid=2, parent=1, u=('line:0', 'line:1'),
              v=('line:0', 'line:1'), divisions=(2, 2)):
        return (f'subgrid {gid} parent {parent} cell u {u[0]} {u[1]} '
                f'v {v[0]} {v[1]} divisions u {divisions[0]} v {divisions[1]}')

    def basic(self):
        self.surface()
        self.ok('grid 1 on 1 main-along v u 1000 3000 v 1000 2000')
        self.ok(self.child())

    def supported(self, v='1000 2000', child=True):
        self.surface()
        self.ok('timber 80 20 20 role boundary')
        self.ok('place 80 on 1 at-face e0 +u +n')
        self.ok('timber 81 20 20 role boundary')
        self.ok('place 81 on 1 at-face e2 +u +n')
        self.ok('grid 1 on 1 main-along v u 1000 3000 v ' + v)
        self.ok('timber 1 20 20 role primary')
        self.ok('place 1 on 1 at-line grid 1 u 0 +v +n')
        self.ok('timber 2 20 20 role primary')
        self.ok('place 2 on 1 at-line grid 1 u 1 +v +n')
        if child:
            self.ok(self.child())

    def roundtrip(self):
        before, refs = self.dump(), self.refs()
        with tempfile.TemporaryDirectory(prefix='subgrid-contract-') as tmp:
            path = Path(tmp) / 'roundtrip.scene'
            path.write_text(before, encoding='utf-8')
            result = self.s.send('loadfile ' + str(path))
            self.assertTrue(result['ok'], result)
        self.assertEqual(before, self.dump())
        self.assertEqual(refs, self.refs())

    def test_s01_explicit_series_and_odd_panel_use_actual_cell_spacing(self):
        cases = [
            ('u 1500 2500 v 300 600', (2, 2), [2000], [450]),
            ('u series 500 1000 3 v series 300 300 4', (2, 2), [1000], [450]),
            ('u panel 400 gap 5 from 0 v 300 600', (3, 2), [537, 672], [450]),
        ]
        for source, divisions, expected_u, expected_v in cases:
            with self.subTest(source=source):
                self.ok('reset')
                self.surface()
                self.ok('grid 1 on 1 ' + source)
                self.ok(self.child(divisions=divisions))
                grid = self.grid()
                self.assertEqual(grid['u'], expected_u)
                self.assertEqual(grid['v'], expected_v)
                self.assertEqual(grid['kind'], 'subgrid')
                self.assertEqual(grid['parentId'], 1)
                self.roundtrip()

    def test_s02_edge_cells_and_undefined_or_zero_line_axis(self):
        for source in ('u 1000 3000', 'u 1000 3000 v panel 4000 gap 5'):
            with self.subTest(source=source):
                self.ok('reset')
                self.surface()
                self.ok('grid 1 on 1 ' + source)
                self.ok(self.child(u=('min', 'line:0'), v=('min', 'max')))
                grid = self.grid()
                self.assertEqual(grid['bounds'], {'u': [0, 1000], 'v': [0, 3000]})
                self.assertEqual(grid['cell'], {'u': ['min', 'line:0'], 'v': ['min', 'max']})
                self.assertEqual((grid['u'], grid['v']), ([500], [1500]))

    def test_s02_canonical_edge_refs_adjacency_and_positive_area(self):
        self.surface('0,0 4000,0 4000,1000 1000,1000 1000,3000 0,3000')
        self.ok('grid 1 on 1 u 0 1000 3000 4000 v 1000 2000')
        self.ok(self.child(u=('min', 'line:1'), v=('min', 'line:0')))
        not_adjacent = ('I25', '彼此相鄰')
        invalid = [
            (self.child(3, u=('line:0', 'line:1'), v=('min', 'line:0')), not_adjacent),
            (self.child(3, u=('line:2', 'line:3'), v=('min', 'line:0')), not_adjacent),
            (self.child(3, u=('min', 'line:2'), v=('min', 'line:0')), not_adjacent),
            (self.child(3, u=('line:1', 'line:1'), v=('min', 'line:0')), not_adjacent),
            (self.child(3, u=('line:1', 'line:2')), ('I25', '沒有正面積交集')),
        ]
        for command, why in invalid:
            with self.subTest(command=command):
                self.reject(command, why)

    def test_s03_exact_divisions_one_axis_empty_and_64_line_limit(self):
        self.surface('0,0 260,0 260,260 0,260')
        self.ok('grid 1 on 1 u 130 v 130')
        command = self.child(u=('min', 'line:0'), v=('min', 'line:0'), divisions=(65, 1))
        self.ok(command)
        self.assertEqual(self.grid()['u'], list(range(2, 130, 2)))
        self.assertEqual(self.grid()['v'], [])
        self.assertEqual(len(self.grid()['lines']), 64)
        # Invalid tokens fail parsing before geometric divisibility checks.
        for divisions, why in [((1, 1), ('I25', '至少一軸須大於 1 等分')),
                               ((0, 2), ('I25', '無法精確分成 0 等分')),
                               ((-1, 2), ('D19/I25', 'divisions u=-1 must be a uint32 integer', 'subgrid 2 parent 1')),
                               (('2.5', 2), ('D19/I25', 'divisions u=2.5 must be a uint32 integer', 'subgrid 2 parent 1')),
                               ((66, 1), ('I25', '無法精確分成 66 等分')),
                               ((3, 1), ('I25', '無法精確分成 3 等分'))]:
            with self.subTest(divisions=divisions):
                self.reject(self.child(u=('min', 'line:0'), v=('min', 'line:0'), divisions=divisions), why)

    def test_s03_read_only_preview_matches_committed_subgrid(self):
        self.surface()
        self.ok('grid 1 on 1 u 1500 2500 v 300 600')
        command = self.child()
        before = self.dump()
        draft = self.s.send('grid-preview ' + command)
        self.assertTrue(draft['ok'], draft)
        self.assertEqual(before, self.dump())
        for _ in range(3):
            repeated = self.s.send('grid-preview ' + command)
            self.assertEqual(repeated, draft)
            self.assertEqual(before, self.dump())
        self.ok('undo')
        self.assertEqual(self.refs()['grids'], [])
        self.ok('redo')
        self.assertEqual(before, self.dump())
        self.ok(command)
        self.assertEqual(draft['grid'], self.grid())
        before = self.dump()
        invalid = self.s.send('grid-preview ' + self.child(divisions=(3, 2)))
        self.assertFalse(invalid['ok'], invalid)
        self.assertEqual(before, self.dump())

    def test_s04_hole_clipping_retains_invisible_line_and_guide_scope(self):
        self.surface('0,0 4000,0 4000,3000 0,3000 hole 1200,900 2800,900 2800,2100 1200,2100')
        self.ok('grid 1 on 1 u 1000 3000 v 1000 2000')
        self.ok(self.child())
        lines = {line['axis']: line for line in self.grid()['lines']}
        self.assertEqual(lines['u']['coordinate'], 2000)
        self.assertEqual(lines['u']['segments'], [])
        self.assertEqual(lines['v']['segments'], [[[1000, 1500], [1200, 1500]],
                                                 [[2800, 1500], [3000, 1500]]])
        self.ok('guide 1 1 v grid:2:u:0')
        self.assertEqual(self.guide(1)['off'], 2000)
        self.assertEqual(self.guide(1)['segments'], [[[2000, 0], [2000, 900]],
                                                   [[2000, 2100], [2000, 3000]]])
        self.ok('timber 1 20 20 role primary')
        self.reject('place 1 on 1 at-line grid 2 u 0 through 500 +v +n', NO_LOCAL_SPAN)

    def test_s04_concave_face_segments_are_clipped_to_cell_intersection(self):
        self.surface('0,0 4000,0 4000,1000 1000,1000 1000,3000 0,3000')
        self.ok('grid 1 on 1 u 2000 v 2000')
        self.ok(self.child(u=('min', 'line:0'), v=('min', 'line:0'), divisions=(4, 4)))
        lines = {(line['axis'], line['index']): line['segments'] for line in self.grid()['lines']}
        self.assertEqual(lines['u', 2], [[[1500, 0], [1500, 1000]]])
        self.assertEqual(lines['v', 2], [[[0, 1500], [1000, 1500]]])

    def test_s05_duplicate_cells_parent_kind_id_type_and_one_main_grid_are_rejected(self):
        self.basic()
        self.ok(self.child(3, u=('min', 'line:0')))
        parent_not_main = ('D19/I25', '父格必須是主網格')
        invalid = [(self.child(4), ('I25', '已有子格')),
                   (self.child(4, parent=2), parent_not_main),
                   (self.child(4, parent=99), parent_not_main),
                   (self.child(1), ('D19/I25', '類型與父格編號不能更換')),
                   ('grid 2 on 1 u 1000', ('D19', '不能將既有子網格改成主網格')),
                   # I10 permits children, but only one main grid per surface.
                   ('grid 4 on 1 u 1000', '一面一格')]
        for command, why in invalid:
            with self.subTest(command=command):
                self.reject(command, why)
        self.surface_on_two()
        self.ok('grid 8 on 2 u 1000 3000 v 1000 2000')
        self.reject(self.child(parent=8), ('D19/I25', '類型與父格編號不能更換'))

    def surface_on_two(self):
        self.ok('surface 2 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000')

    def test_s05_global_capacity_is_16_main_and_child_grids_together(self):
        self.surface()
        self.ok('grid 1 on 1 u series 100 100 16')
        for gid in range(2, 17):
            index = gid - 2
            lower = 'min' if index == 0 else f'line:{index - 1}'
            self.ok(self.child(gid, u=(lower, f'line:{index}'), v=('min', 'max'), divisions=(2, 1)))
        self.assertEqual(len(self.refs()['grids']), 16)
        self.reject(self.child(17, u=('line:14', 'line:15'), v=('min', 'max'), divisions=(2, 1)),
                    ('I10', '合計不能超過 16 組'))

    def test_s06_both_child_axes_default_secondary_and_direction_rules_still_apply(self):
        self.basic()
        self.assertIsNone(self.grid()['mainAlong'])
        self.assertEqual([(x['axis'], x['role'], x['priority']) for x in self.grid()['lines']],
                         [('u', 'secondary', 3), ('v', 'secondary', 3)])
        self.ok('timber 1 20 20 role secondary')
        # R6(b): this local cell has no supported complete span.
        self.reject('place 1 on 1 at-line grid 2 v 0 +u +n', NO_LOCAL_SPAN)
        self.ok('reset')
        self.supported()
        self.ok('timber 3 20 20 role secondary')
        self.ok('place 3 on 1 at-line grid 2 v 0 between t1 t2 +u +n')
        self.ok('timber 4 20 20 role secondary')
        self.reject('place 4 on 1 at-line grid 2 u 0 +v +n', NO_LOCAL_SPAN)
        before = self.timber(3)
        self.ok('grid 1 on 1 main-along u')
        self.assertEqual(self.timber(3), before)
        self.assertTrue(all(x['role'] == 'secondary' for x in self.grid()['lines']))

        # D17/I21: full-height child cell and real boundary supports remove the
        # earlier R6(b) failure. A secondary parallel to the primary axis must fail.
        self.ok('reset')
        self.supported(v='panel 4000 gap 5', child=False)
        self.ok(self.child(v=('min', 'max')))
        self.ok('timber 4 20 20 role secondary')
        self.reject('place 4 on 1 at-line grid 2 u 0 +v +n', 'V_PRIMARY_AXIS')
        self.ok('timber 4 20 20 role primary')
        self.ok('place 4 on 1 at-line grid 2 u 0 +v +n')
        self.assertEqual(self.timber(4)['geometry']['length'], 2960)

    def test_s06_explicit_primary_override_can_use_a_fully_supported_child_line(self):
        self.supported(child=False)
        self.ok(self.child(u=('min', 'line:0'), v=('min', 'line:0'), divisions=(2, 1)))
        # This cell ends at v=1000, so it cannot support a full primary span.
        self.ok('timber 3 20 20 role primary')
        self.reject('place 3 on 1 at-line grid 2 u 0 +v +n', NO_LOCAL_SPAN)
        self.apply('delete grid 2')
        self.ok('grid 1 on 1 v panel 4000 gap 5')
        self.ok(self.child(u=('min', 'line:0'), v=('min', 'max'), divisions=(2, 1)))
        self.ok('place 3 on 1 at-line grid 2 u 0 +v +n')
        self.assertEqual(self.timber(3)['role'], 'primary')
        self.assertEqual(self.timber(3)['geometry']['length'], 2960)

    def test_s07_real_supports_succeed_but_long_span_and_wide_band_do_not(self):
        self.supported()
        self.ok('timber 3 20 20 role secondary')
        self.ok('place 3 on 1 at-line grid 2 v 0 +u +n')
        self.assertEqual(self.timber(3)['geometry']['length'], 1980)
        self.ok('timber 4 20 20 role primary')
        self.reject('place 4 on 1 at-line grid 2 u 0 +v +n', NO_LOCAL_SPAN)
        self.reject('place 4 on 1 at-line grid 2 u 0 through 1500 +v +n', NO_LOCAL_SPAN)
        self.reject('place 4 on 1 at-line grid 2 u 0 between t80 t81 +v +n', NO_BETWEEN_SPAN)
        self.ok('reset')
        self.supported(v='1000 1010')
        self.ok('timber 3 20 20 role secondary')
        self.reject('place 3 on 1 at-line grid 2 v 0 between t1 t2 +u +n', ('I13', '完整寬度超出子格範圍'))

    def test_s07_independent_guide_from_child_coordinate_does_not_inherit_scope(self):
        self.supported()
        self.ok('guide 1 1 v grid:2:u:0')
        self.ok('timber 3 20 20 role primary')
        self.reject('place 3 on 1 at-line grid 2 u 0 +v +n', NO_LOCAL_SPAN)
        self.ok('place 3 on 1 at-line guide 1 +v +n')
        self.assertEqual(self.timber(3)['geometry']['centerline'], 2000)
        self.assertEqual(self.timber(3)['geometry']['length'], 2960)
        self.roundtrip()

    def test_s08_hole_divides_spans_and_scope_filters_before_through(self):
        self.surface('0,0 4000,0 4000,3000 0,3000 hole 1800,1200 2200,1200 2200,1800 1800,1800')
        self.ok('timber 80 20 20 role boundary')
        self.ok('place 80 on 1 at-face e0 +u +n')
        self.ok('timber 81 20 20 role boundary')
        self.ok('place 81 on 1 at-face e2 +u +n')
        self.ok('grid 1 on 1 u 1000 3000 v 1200 1800')
        self.ok(self.child(v=('min', 'line:0'), divisions=(2, 1)))
        self.ok('timber 1 20 20 role primary')
        self.reject('place 1 on 1 at-line grid 2 u 0 through 2400 +v +n', 'through 座標不在任何合法跨距內')
        self.ok('place 1 on 1 at-line grid 2 u 0 through 600 +v +n')
        self.assertEqual(self.timber(1)['geometry']['length'], 1180)
        self.ok('undo')
        self.ok('place 1 on 1 at-line grid 2 u 0 between t80 h0e0 +v +n')
        self.assertEqual(self.timber(1)['geometry']['length'], 1180)

    def test_s08_multiple_in_scope_spans_require_through_or_named_stops(self):
        self.surface('0,0 4000,0 4000,3000 0,3000 hole 1800,1200 2200,1200 2200,1800 1800,1800')
        for tid, edge in [(80, 'e0'), (81, 'e2')]:
            self.ok(f'timber {tid} 20 20 role boundary')
            self.ok(f'place {tid} on 1 at-face {edge} +u +n')
        self.ok('grid 1 on 1 u 1000 3000')
        self.ok(self.child(v=('min', 'max'), divisions=(2, 1)))
        self.ok('timber 1 20 20 role primary')
        self.reject('place 1 on 1 at-line grid 2 u 0 +v +n', '跨距歧義')
        self.reject('place 1 on 1 at-line grid 2 u 0 between t80 t81 +v +n', NO_BETWEEN_SPAN)
        self.ok('place 1 on 1 at-line grid 2 u 0 between t80 h0e0 +v +n')
        self.assertEqual(self.timber(1)['geometry']['length'], 1180)

    def test_s09_parent_same_count_move_previews_child_without_timber(self):
        self.basic()
        self.ok('guide 1 1 v grid:2:u:0')
        before = self.dump()
        preview = self.preview('grid 1 on 1 u 1100 3100')
        row = next(g for g in preview['grids'] if g['id'] == 2)
        self.assertEqual(row['before']['bounds']['u'], [1000, 3000])
        self.assertEqual(row['after']['bounds']['u'], [1100, 3100])
        self.assertEqual((row['before']['u'], row['after']['u']), ([2000], [2100]))
        guide = next(g for g in preview['guides'] if g['id'] == 1)
        self.assertEqual((guide['before']['off'], guide['after']['off']), (2000, 2100))
        self.confirm(preview)
        self.assertEqual(self.guide(1)['off'], 2100)
        self.ok('undo')
        self.assertEqual(before, self.dump())
        self.ok('redo')
        self.assertEqual(self.grid()['u'], [2100])
        self.roundtrip()

    def test_s09_visible_segment_change_previews_unreferenced_child(self):
        self.basic()
        before = self.dump()
        preview = self.preview('boundary 1 outline 0,0 4000,0 4000,3000 0,3000 '
                               'hole 1500,1200 2500,1200 2500,1800 1500,1800')
        row = next(g for g in preview['grids'] if g['id'] == 2)
        self.assertEqual(row['before']['bounds'], row['after']['bounds'])
        self.assertEqual(row['before']['u'], row['after']['u'])
        self.assertEqual(row['before']['v'], row['after']['v'])
        self.assertNotEqual(row['before']['lines'], row['after']['lines'])
        self.confirm(preview)
        self.assertEqual(sum(len(line['segments']) for line in self.grid()['lines']), 4)
        self.ok('undo')
        self.assertEqual(before, self.dump())

    def test_s09_dependency_closure_updates_child_guide_and_timber_in_one_confirmation(self):
        self.supported()
        self.ok('guide 1 1 u grid:2:v:0')
        self.ok('timber 3 20 20 role secondary')
        self.ok('place 3 on 1 at-line guide 1 between t1 t2 +u +n')
        before = self.dump()
        preview = self.preview('grid 1 on 1 u 1100 3100 v 1100 2100')
        child = next(g for g in preview['grids'] if g['id'] == 2)
        self.assertEqual(child['after']['v'], [1600])
        guide = next(g for g in preview['guides'] if g['id'] == 1)
        self.assertEqual((guide['before']['off'], guide['after']['off']), (1500, 1600))
        timber = next(t for t in preview['timbers'] if t['id'] == 3)
        self.assertEqual((timber['before']['centerline'], timber['after']['centerline']), (1500, 1600))
        self.confirm(preview)
        self.assertEqual(self.timber(3)['geometry']['centerline'], 1600)
        self.assertEqual(self.timber(3)['geometry']['length'], 1980)
        self.ok('undo')
        self.assertEqual(before, self.dump())
        self.ok('redo')
        self.roundtrip()

    def test_s09_parent_line_count_and_child_canonical_edges_are_preserved(self):
        self.basic()
        for command in ['grid 1 on 1 u 500 1000 3000', 'grid 1 on 1 u 1000',
                        'grid 1 on 1 v panel 4000 gap 5', 'grid 1 on 1 v 500 1000 2000']:
            with self.subTest(command=command):
                self.reject(command, ('I23', '線數不可從'))
        self.ok('reset')
        self.surface()
        self.ok('grid 1 on 1 u 1000 3000')
        self.ok(self.child(u=('min', 'line:0'), v=('min', 'max')))
        # D19/I25: line:0 coincides with min, invalidating the child's canonical edge.
        self.reject('grid 1 on 1 u 0 3000', ('I25', '相鄰'))

    def test_s09_boundary_growth_cannot_change_panel_count_behind_children(self):
        self.surface()
        self.ok('grid 1 on 1 u panel 400 gap 5 from 0')
        self.ok(self.child(v=('min', 'max'), divisions=(3, 1)))
        self.reject('boundary 1 outline 0,0 4100,0 4100,3000 0,3000',
                    ('重宣告後有物件失效', 'u 軸線數不可從 9 改成 10', 'I23', '父網格 1', 'boundary 1'))

    def test_s09_retarget_divisions_and_referenced_index_contract(self):
        self.basic()
        preview = self.preview(self.child(u=('min', 'line:0')))
        self.confirm(preview)
        self.assertEqual(self.grid()['u'], [500])
        preview = self.preview(self.child(u=('min', 'line:0'), divisions=(4, 2)))
        self.confirm(preview)
        self.ok('guide 1 1 v grid:2:u:2')
        self.reject(self.child(u=('min', 'line:0'), divisions=(2, 2)), ('guide 1', 'grid:2:u:2'))
        self.apply('delete guide 1')
        self.ok('guide 1 1 v grid:2:u:0')
        preview = self.preview(self.child(u=('min', 'line:0'), divisions=(2, 2)))
        self.confirm(preview)
        self.assertEqual(self.guide(1)['off'], 500)
        self.assertEqual(self.grid()['u'], [500])

    def test_s10_cancel_stale_and_invalid_previews_preserve_source_world(self):
        self.basic()
        before = self.dump()
        preview = self.preview('grid 1 on 1 u 1100 3100')
        self.ok('cancel-preview')
        self.reject('confirm ' + str(preview['token']), ('I8a', 'preview token'))
        self.assertEqual(before, self.dump())
        preview = self.preview('grid 1 on 1 u 1100 3100')
        self.ok('spec unrelated 20')
        self.reject('confirm ' + str(preview['token']), ('I8a', 'stale'))
        self.assertEqual(self.grid()['u'], [2000])
        preview = self.preview('grid 1 on 1 u 1001 3000', valid=False)
        self.reject('confirm ' + str(preview['token']), ('I8a', 'preview token'))
        self.assertEqual(self.grid()['u'], [2000])

    def test_s10_invalid_preview_shows_requested_parent_and_unresolvable_child(self):
        self.surface('-4000,0 0,0 0,3000 -4000,3000')
        self.ok('grid 1 on 1 u -3000 -1000 v 1000 2000')
        self.ok(self.child())
        self.ok('guide 1 1 v grid:2:u:0')
        before = self.dump()
        preview = self.preview('grid 1 on 1 u -3500 -3000 -1000', valid=False)
        parent = next(g for g in preview['grids'] if g['id'] == 1)
        self.assertEqual(parent['before']['u'], [-3000, -1000])
        self.assertEqual(parent['after']['u'], [-3500, -3000, -1000])
        child = next(g for g in preview['grids'] if g['id'] == 2)
        self.assertEqual(child['before']['bounds']['u'], [-3000, -1000])
        self.assertEqual(child['after']['bounds']['u'], [-3500, -3000])
        self.assertEqual(child['after']['u'], [-3250])
        # The early I23 rejection cannot present an untested guide as valid new geometry.
        guide = next(g for g in preview['guides'] if g['id'] == 1)
        self.assertIsNone(guide['after'])
        self.reject('confirm ' + str(preview['token']), ('I8a', 'preview token'))
        self.assertEqual(before, self.dump())
        preview = self.preview(self.child(divisions=(3, 2)), valid=False)
        child = next(g for g in preview['grids'] if g['id'] == 2)
        self.assertEqual(child['before']['divisions']['u'], 2)
        self.assertEqual(child['after']['divisions']['u'], 3)
        self.assertEqual(child['after']['bounds']['u'], [-3000, -1000])
        self.assertEqual(child['after']['u'], [])
        self.assertFalse(any(line['axis'] == 'u' for line in child['after']['lines']))
        self.assertIsNone(next(g for g in preview['guides'] if g['id'] == 1)['after'])
        self.reject('confirm ' + str(preview['token']), ('I8a', 'preview token'))
        self.assertEqual(before, self.dump())

    def test_s11_parent_guide_and_timber_dependencies_block_deletion(self):
        self.supported()
        self.ok('guide 1 1 v grid:2:u:0')
        self.ok('timber 3 20 20 role secondary')
        self.ok('place 3 on 1 at-line grid 2 v 0 +u +n')
        self.assertEqual(self.grid(1)['dependencies']['children'], [2])
        self.assertIn(1, self.grid()['dependencies']['guides'])
        self.assertIn(3, self.grid()['dependencies']['timbers'])
        self.reject('delete grid 1', ('I23', '仍有子格'))
        self.reject('delete grid 2', ('I23', '仍被參考線'))
        self.apply('delete guide 1')
        self.reject('delete grid 2', 'V_GRID_LOCKED')
        preview = self.preview('delete timber 3')
        self.confirm(preview)
        before = self.dump()
        self.apply('delete grid 2')
        self.assertEqual([g['id'] for g in self.refs()['grids']], [1])
        self.ok('undo')
        self.assertEqual(before, self.dump())

    def test_s11_dependency_ids_are_exact_and_scaled_expressions_are_tracked(self):
        self.basic()
        self.ok(self.child(20, u=('min', 'line:0')))
        self.ok('guide 21 1 v 1/2*grid:20:u:0')
        self.ok('guide 22 1 v 1/2*grid:2:u:0+1/2*grid:20:u:0')
        self.assertEqual(self.grid(2)['dependencies']['guides'], [22])
        self.assertEqual(self.grid(20)['dependencies']['guides'], [21, 22])
        self.reject('delete grid 20', ('I23', '仍被參考線'))
        self.ok('reset')
        self.surface()
        self.ok('grid 0 on 1 u 1000 3000 v 1000 2000')
        self.ok('timber 0 20 20 role boundary')
        self.ok('place 0 on 1 at-face e0 +u +n')
        self.assertEqual(self.grid(0)['dependencies']['timbers'], [])
        self.ok(self.child(parent=0))
        self.ok('guide 0 1 v grid:2:u:0')
        self.assertEqual(self.grid(2)['dependencies']['guides'], [0])
        self.reject('delete grid 2', ('I23', '仍被參考線'))

    def room_for_split(self):
        for line in (ROOT / '_ax_r13_anchor_follows.scene').read_text(encoding='utf-8').splitlines():
            if line.startswith(('surface ', 'space ')):
                self.ok(line)
        self.ok('beam 1 in 1 along y from 0 to 3000 at 2800 width 300 depth 500')

    def test_s12_split_moves_parent_children_and_guides_as_one_family(self):
        self.room_for_split()
        self.ok('grid 1 on 1 u 3300 3800')
        self.ok(self.child(v=('min', 'max')))
        self.ok('guide 1 1 v grid:2:u:0')
        before = self.dump()
        preview = self.preview('apply-proj 1 b1 cut-strip')
        self.confirm(preview)
        parent, child = self.grid(1), self.grid()
        self.assertNotEqual(parent['surface'], 1)
        self.assertEqual(parent['surface'], child['surface'])
        self.assertEqual(child['surface'], self.guide(1)['surface'])
        self.assertEqual(child['u'], [3550])
        self.assertEqual(child['v'], [1500])
        self.roundtrip()
        # Load is a separate history operation; verify split undo on a fresh repeat.
        self.ok('reset')
        self.room_for_split()
        self.ok('grid 1 on 1 u 3300 3800')
        self.ok(self.child(v=('min', 'max')))
        self.ok('guide 1 1 v grid:2:u:0')
        self.confirm(self.preview('apply-proj 1 b1 cut-strip'))
        self.ok('undo')
        self.assertEqual(before, self.dump())

    def test_s12_split_with_no_valid_common_fragment_is_atomic(self):
        self.room_for_split()
        self.ok('grid 1 on 1 u 1000 3500')
        self.ok(self.child(v=('min', 'max')))
        self.reject('apply-proj 1 b1 cut-strip', '拆分後參考線/網格/角材失去承載面')

    def test_s12_split_assigns_guide_from_recomputed_child_not_stale_coordinate(self):
        self.room_for_split()
        self.ok('grid 1 on 1 v 1000')
        self.ok(self.child(u=('min', 'max'), v=('min', 'line:0'), divisions=(2, 1)))
        self.ok('guide 1 1 v 3/2*grid:2:u:0')
        self.ok('guide 2 1 v guide:1')
        self.assertEqual(self.guide(1)['off'], 3000)
        before = self.dump()
        preview = self.preview('apply-proj 1 b1 cut-strip')
        child_row = next(g for g in preview['grids'] if g['id'] == 2)
        self.assertEqual(child_row['after']['surface'], 1)
        self.assertEqual(child_row['after']['bounds']['u'], [0, 2650])
        self.assertEqual(child_row['after']['u'], [1325])
        guide_row = next(g for g in preview['guides'] if g['id'] == 1)
        self.assertEqual(guide_row['before']['off'], 3000)
        self.assertEqual(guide_row['after']['off'], 1987)
        self.assertEqual(guide_row['after']['surface'], 1)
        dependent = next(g for g in preview['guides'] if g['id'] == 2)
        self.assertEqual(dependent['after']['off'], 1987)
        self.assertEqual(dependent['after']['surface'], 1)
        self.confirm(preview)
        self.assertEqual(self.grid(1)['surface'], self.grid(2)['surface'])
        self.assertEqual(self.grid(2)['surface'], self.guide(1)['surface'])
        self.assertEqual(self.guide(1)['surface'], self.guide(2)['surface'])
        self.assertEqual(self.guide(1)['segments'], [[[1987, 0], [1987, 3000]]])
        after = self.dump()
        self.ok('undo')
        self.assertEqual(before, self.dump())
        self.ok('redo')
        self.assertEqual(after, self.dump())
        self.roundtrip()

    def test_s13_scene_roundtrip_orders_parent_before_child_before_reference(self):
        fixture = ROOT / 'subgrid-local.scene'
        result = self.s.send('loadfile ' + str(fixture))
        self.assertTrue(result['ok'], result)
        self.assertEqual([t['geometry']['length'] for t in self.refs()['timbers']],
                         [4000, 4000, 2960, 2960, 1980])
        self.ok('guide 1 1 v grid:2:u:0')
        dump = self.dump()
        self.assertLess(dump.index('grid 1 on '), dump.index('subgrid 2 parent '))
        self.assertLess(dump.index('subgrid 2 parent '), dump.index('guide 1 '))
        self.assertIn('cell u line:0 line:1 v line:0 line:1 divisions u 2 v 2', dump)
        self.roundtrip()

    def test_s13_legacy_main_grid_scene_still_loads_with_no_children(self):
        result = self.s.send('loadfile ' + str(ROOT / '_test_grid_series.scene'))
        self.assertTrue(result['ok'], result)
        self.assertTrue(self.refs()['grids'])
        self.assertTrue(all(g['kind'] == 'main' and g['parentId'] is None
                            for g in self.refs()['grids']))
        self.roundtrip()

    def test_s13_history_group_restores_whole_parent_child_guide_chain(self):
        self.surface()
        before = self.dump()
        self.ok('history-begin')
        self.ok('grid 1 on 1 u 1000 3000 v 1000 2000')
        self.ok(self.child())
        self.ok('guide 1 1 v grid:2:u:0')
        self.ok('history-end')
        after = self.dump()
        self.ok('undo')
        self.assertEqual(before, self.dump())
        self.ok('redo')
        self.assertEqual(after, self.dump())
        self.roundtrip()


if __name__ == '__main__':
    unittest.main(verbosity=2)
