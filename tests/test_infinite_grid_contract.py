"""D29/D30/I37/R32 acceptance: infinite lattice identities, not finite samples.

Run with GEOMETRY_TEST_BRIDGE pointing at the current native bridge. The old
test_grid_system_contract.py remains the independent legacy-finite regression.
Expected coordinates below are hand-calculated; no application evaluator is an
oracle. Query views, previews and failed operations must never alter definitions.
Refusals use the shared reject(command, why=...) from test_grid_system_contract.py: `why` pins the
reason (substring, or tuple of substrings) the bridge reports, see that module's docstring.
"""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:  # `python tests/x.py` puts tests/ first, not the repo root
    sys.path.insert(0, str(ROOT))
from tests import test_grid_system_contract as _legacy  # noqa: E402

native_path = _legacy.native_path
finite_system = _legacy.system


def infinite(identifier=0, name="無限 格網 A", u="repeat 0 600", v="repeat 0 400", main="none"):
    return f"grid-system {identifier} name-hex {name.encode('utf-8').hex()} main-along {main} u {u} v {v}"


class InfiniteGridContract(unittest.TestCase):
    # Share only bridge transport/transaction helpers, never legacy test cases or
    # expected geometry. This suite is separately runnable and separately counted.
    @classmethod
    def setUpClass(cls):
        _legacy.GridSystemContract.setUpClass.__func__(cls)

    setUp = _legacy.GridSystemContract.setUp
    command = _legacy.GridSystemContract.command
    line = _legacy.GridSystemContract.line
    commit = _legacy.GridSystemContract.commit
    dump = _legacy.GridSystemContract.dump
    refs = _legacy.GridSystemContract.refs
    objects = _legacy.GridSystemContract.objects
    grids = _legacy.GridSystemContract.grids
    snapshot = _legacy.GridSystemContract.snapshot
    preview = _legacy.GridSystemContract.preview
    reject = _legacy.GridSystemContract.reject
    roundtrip = _legacy.GridSystemContract.roundtrip

    RECT = [(100, 200), (1300, 200), (1300, 1000), (100, 1000)]

    def boundary(self, identifier=1, outer=None, holes=()):
        points = lambda values: " ".join(f"{u},{v}" for u, v in values)
        self.commit(f"boundary {identifier} outline " + points(outer or self.RECT)
                    + "".join(" hole " + points(hole) for hole in holes))

    def geometry(self, identifier=1):
        value = self.command(f"boundary {identifier}")
        self.assertTrue(value["ok"], value)
        return value

    def fingerprint(self, identifier=1):
        value = self.geometry(identifier)["geometryFingerprint"]
        self.assertRegex(value, r"^[a-f0-9]{64}$")
        return value

    def binding_command(self, identifier=0, boundary=1, source=0, cell=(-2, 1),
                        anchor=(0, 1, 0, 1), vertex="outer 0", key=None, fingerprint=None):
        reference = (f"vertex-key {key}" if key is not None else
                     f"vertex {vertex} geometry-hash {fingerprint or self.fingerprint(boundary)}")
        return (f"grid-binding {identifier} on-boundary {boundary} from-system {source} {reference} "
                f"cell {cell[0]} {cell[1]} anchor {' '.join(map(str, anchor))}")

    def binding(self, identifier=0, **kwargs):
        self.commit(self.binding_command(identifier=identifier, **kwargs))
        return self.bindings()[identifier]

    def bindings(self):
        return {row["id"]: row for row in self.objects()["gridBindings"]}

    def keymap(self, identifier=1):
        rows = [line for line in self.dump().splitlines()
                if line.startswith(f"boundary-vertex-keys {identifier} ")]
        self.assertEqual(1, len(rows), rows)
        loops = []
        for token in rows[0].split()[2:]:
            if token == "next-key":
                break
            if token in ("outer", "hole"):
                loops.append([])
            else:
                loops[-1].append(int(token))
        self.assertEqual(len(sum(loops, [])), len(set(sum(loops, []))))
        self.assertTrue(all(key > 0 for loop in loops for key in loop))
        return loops

    def keyed_command(self, identifier, loops, keys=None, fingerprint=None):
        keys = keys or self.keymap(identifier)
        self.assertEqual(len(keys), len(loops))
        chunks = []
        for i, (coordinates, identities) in enumerate(zip(loops, keys)):
            self.assertEqual(len(coordinates), len(identities))
            chunks.append(("outline" if i == 0 else "hole") + " " + " ".join(
                f"{key}:{u},{v}" for key, (u, v) in zip(identities, coordinates)))
        return f"boundary-keyed {identifier} geometry-hash {fingerprint or self.fingerprint(identifier)} " + " ".join(chunks)

    def fixture(self, second=False):
        self.boundary()
        self.commit(infinite())
        self.binding()
        if second:
            self.boundary(2)
            self.binding(1, boundary=2, anchor=(1, 2, 1, 2))

    def query(self, kind="system", identifier=0, rect=(-1200, -800, 1200, 800), mode="exact", limit=64):
        before = self.dump()
        result = self.command(f"grid-query {kind} {identifier} rect {' '.join(map(str, rect))} mode {mode} limit {limit}")
        self.assertEqual(before, self.dump(), "queries must not become stored sources")
        return result

    def axis(self, result, axis):
        self.assertTrue(result["ok"], result)
        return result["axes"][axis]

    def coordinates(self, result, axis):
        data = self.axis(result, axis)
        for row in data["lines"]:
            self.assertIsInstance(row["index"], str, "lattice indices cannot travel through JSON doubles")
        return {int(row["index"]): row["coordinate"] for row in data["lines"]}

    def test_infinite_sources_cross_zero_and_queries_never_define_an_extent(self):
        self.commit(infinite())
        objects = self.objects()
        self.assertEqual([], objects["faces"])
        self.assertEqual([], objects["gridBindings"])
        self.assertEqual([], self.refs()["grids"])
        source = objects["gridSystems"][0]
        self.assertEqual("infinite", source["mode"])
        self.assertNotIn("count", source["uDefinition"])
        result = self.query()
        self.assertTrue(result["exact"], result)
        self.assertEqual({-2: -1200, -1: -600, 0: 0, 1: 600, 2: 1200}, self.coordinates(result, "u"))
        self.assertEqual({-2: -800, -1: -400, 0: 0, 1: 400, 2: 800}, self.coordinates(result, "v"))
        shifted = self.query(rect=(-2400, -1600, -600, -400))
        self.assertEqual({-4: -2400, -3: -1800, -2: -1200, -1: -600}, self.coordinates(shifted, "u"))
        self.assertEqual(-1200, self.coordinates(shifted, "u")[-2])
        self.assertNotIn("count", self.dump())
        self.roundtrip()

    def test_repeat_panel_extends_both_directions_and_uses_negative_floor_correctly(self):
        self.commit(infinite(u="repeat-panel 400 gap 5 from -100", v="repeat -3 7"))
        result = self.query(rect=(-1000, -18, 1200, 18))
        # panel pitch=405, phase=-100+400+floor(5/2)=302.
        self.assertEqual({-3: -913, -2: -508, -1: -103, 0: 302, 1: 707, 2: 1112}, self.coordinates(result, "u"))
        self.assertEqual({-2: -17, -1: -10, 0: -3, 1: 4, 2: 11, 3: 18}, self.coordinates(result, "v"))
        self.assertEqual(-3, int(self.axis(result, "u")["firstIndex"]))
        self.assertEqual(2, int(self.axis(result, "u")["lastIndex"]))

    def test_infinite_lines_are_clipped_by_concavity_and_holes_without_renumbering(self):
        self.commit(infinite())
        self.boundary(outer=[(0, 0), (1800, 0), (1800, 800), (1200, 800),
                             (1200, 1600), (0, 1600)],
                      holes=[[(200, 200), (200, 600), (1000, 600), (1000, 200)]])
        self.binding(cell=(0, 0))
        result = self.query("binding", rect=(-600, -400, 2400, 2000))
        rows = lambda axis: {int(row["index"]): row for row in self.axis(result, axis)["lines"]}
        u, v = rows("u"), rows("v")
        segments = lambda row: {tuple(sorted((tuple(s["a"]), tuple(s["b"])))) for s in row["segments"]}
        self.assertEqual({((600, 0), (600, 200)), ((600, 600), (600, 1600))}, segments(u[1]))
        self.assertEqual({((0, 400), (200, 400)), ((1000, 400), (1800, 400))}, segments(v[1]))
        self.assertEqual({((0, 1200), (1200, 1200))}, segments(v[3]))
        self.assertEqual(-600, u[-1]["coordinate"])
        self.assertEqual([], u[-1]["segments"])
        self.assertEqual([], u[4]["segments"])
        self.roundtrip()

    def test_unplaced_boundaries_bind_by_key_and_fraction_not_cached_translation(self):
        self.fixture(second=True)
        objects = self.objects()
        self.assertEqual(2, len(objects["faces"]))
        self.assertTrue(all(not face["placed"] for face in objects["faces"]))
        self.assertEqual([], self.command("surfaces")["surfaces"])
        self.assertEqual([], self.refs()["timbers"])
        bindings = self.bindings()
        self.assertEqual([1300, -200], bindings[0]["translation"])
        self.assertEqual([1000, -400], bindings[1]["translation"])
        for identifier, boundary in ((0, 1), (1, 2)):
            self.assertEqual(["-2", "1"], bindings[identifier]["cell"])
            self.assertEqual(self.keymap(boundary)[0][0], bindings[identifier]["vertexKey"])
        self.assertEqual({-2: 100, -1: 700, 0: 1300}, self.coordinates(self.query("binding", rect=(100, 200, 1300, 1000)), "u"))
        self.assertEqual({-1: 400, 0: 1000}, self.coordinates(self.query("binding", 1, rect=(100, 200, 1300, 1000)), "u"))
        scene = self.dump()
        self.assertIn("vertex-key", scene)
        self.assertNotIn("geometry-hash", scene)
        self.assertNotIn("translation", scene)
        self.assertNotIn("vertex outer", scene)
        self.roundtrip()

    def test_pitch_changes_preserve_both_anchors_and_preview_cancel_history(self):
        self.fixture(second=True)
        self.commit("canvas-pos grid-binding 0 240 -80")
        before = self.snapshot()
        command = infinite(u="repeat 0 800", v="repeat 0 500")
        preview = self.preview(command)
        self.assertTrue(preview["valid"], preview)
        self.assertIn("gridBindings", preview)
        self.assertEqual({0, 1}, {row["id"] for row in preview["gridBindings"]})
        self.commit("cancel-preview")
        self.assertEqual(before, self.snapshot())
        preview = self.preview(command)
        self.commit("confirm " + str(preview["token"]))
        after = self.snapshot()
        self.assertEqual([1700, -300], self.bindings()[0]["translation"])
        self.assertEqual([1300, -550], self.bindings()[1]["translation"])
        self.assertEqual({-2: 100, -1: 900}, self.coordinates(self.query("binding", rect=(100, 200, 1300, 1000)), "u"))
        self.assertEqual({-1: 500, 0: 1300}, self.coordinates(self.query("binding", 1, rect=(100, 200, 1300, 1000)), "u"))
        for boundary in (1, 2):
            self.assertEqual([100, 200], self.geometry(boundary)["loops"][0]["verts"][0])
        self.commit("undo")
        self.assertEqual(before, self.snapshot())
        self.commit("redo")
        self.assertEqual(after, self.snapshot())
        self.roundtrip()

    def test_first_binding_keys_are_atomic_and_odd_centers_are_not_rounded(self):
        self.boundary()
        geometry_hash = self.fingerprint()
        self.commit(infinite(u="repeat 0 601"))
        before = self.snapshot()
        self.reject(self.binding_command(anchor=(1, 2, 1, 2)), ("D1/I37", "integer-millimetre"))
        self.assertEqual(before, self.snapshot())
        self.assertNotIn("boundary-vertex-keys", self.dump())
        preview = self.preview(self.binding_command())
        self.assertTrue(preview["valid"], preview)
        self.assertNotIn("boundary-vertex-keys", self.dump())
        self.commit("cancel-preview")
        self.assertEqual(before, self.snapshot())
        self.binding(anchor=(0, 2, 0, 6))
        self.assertIn("anchor 0 1 0 1", self.dump())
        self.assertEqual(geometry_hash, self.fingerprint(), "keys do not alter the boundary geometry fingerprint")
        self.commit("undo")
        self.assertEqual(before, self.snapshot(), "key initialization and binding creation are one transaction")

    def test_fraction_reduction_invalid_fractions_and_one_axis_cannot_make_cell(self):
        self.boundary()
        self.commit(infinite())
        self.binding(anchor=(2, 4, 3, 6))
        self.assertIn("anchor 1 2 1 2", self.dump())
        bad_fraction = ("D30/I37", "rational anchor declaration")   # weak: one line for every malformed fraction
        for anchor, why in (((-1, 2, 0, 1), bad_fraction), ((3, 2, 0, 1), bad_fraction), ((0, 0, 0, 1), bad_fraction),
                            ((0, -1, 0, 1), bad_fraction), ((1, 7, 0, 1), ("D1/I37", "integer-millimetre"))):
            with self.subTest(anchor=anchor):
                self.reject(self.binding_command(1, anchor=anchor), why)
        self.commit(infinite(1, v="none"))
        self.reject(self.binding_command(1, source=1), ("D30/I37", "two infinite axes"))
        # weak: the same D29/I37 definition-guard line for every malformed grid-system
        self.reject(infinite(2, u="repeat 0 600", v="series 0 400 3"), "D29/I37")
        self.reject(infinite(2, u="repeat 0 0"), "D29/I37")
        self.reject(infinite(2, u="repeat 0 -1"), "D29/I37")

    def test_geometry_hash_rejects_stale_initial_pick_and_keyed_edit(self):
        self.boundary()
        self.commit(infinite())
        old_hash = self.fingerprint()
        self.commit("canvas-pos boundary 1 999 -200")
        self.assertEqual(old_hash, self.fingerprint(), "canvas movement is not boundary geometry")
        reordered = self.RECT[1:] + self.RECT[:1]
        self.boundary(outer=reordered)
        self.assertNotEqual(old_hash, self.fingerprint())
        self.reject(self.binding_command(fingerprint=old_hash), ("D30", "STALE_GEOMETRY"))
        self.assertNotIn("boundary-vertex-keys", self.dump())
        self.binding(vertex="outer 3")
        old_hash = self.fingerprint()
        self.commit(self.keyed_command(1, [self.RECT], [self.keymap()[0][-1:] + self.keymap()[0][:-1]]))
        self.reject(self.keyed_command(1, [[(100, 200), (1900, 200), (1900, 1000), (100, 1000)]], fingerprint=old_hash),
                    ("D30", "geometry-hash is stale"))

    def test_expand_four_sides_keeps_hole_anchor_and_absolute_line_identities(self):
        outer = [(-1100, -1000), (1900, -1000), (1900, 1800), (-1100, 1800)]
        hole = [(100, 200), (700, 200), (700, 600), (100, 600)]
        self.boundary(outer=outer, holes=[hole])
        self.commit(infinite())
        self.binding(vertex="hole 0 0")
        key = self.bindings()[0]["vertexKey"]
        self.assertEqual(self.keymap()[1][0], key)
        previous = self.coordinates(self.query("binding", rect=(-1100, -1000, 1900, 1800)), "u")
        for rect in [(-2300, -1000, 1900, 1800), (-2300, -1000, 3100, 1800),
                     (-2300, -1800, 3100, 1800), (-2300, -1800, 3100, 2600)]:
            lo_u, lo_v, hi_u, hi_v = rect
            expanded = [(lo_u, lo_v), (hi_u, lo_v), (hi_u, hi_v), (lo_u, hi_v)]
            self.commit(self.keyed_command(1, [expanded, hole]))
            result = self.query("binding", rect=rect)
            actual = self.coordinates(result, "u")
            self.assertTrue(set(previous).issubset(actual))
            self.assertEqual(previous, {k: actual[k] for k in previous})
            self.assertEqual([1300, -200], self.bindings()[0]["translation"])
            self.assertEqual(key, self.bindings()[0]["vertexKey"])
            previous = actual
        self.roundtrip()

    def test_keyed_vertex_move_tracks_anchor_and_ambiguous_identity_is_rejected(self):
        self.fixture()
        keys = self.keymap()
        moved = [(200, 300), (1400, 300), (1400, 1100), (200, 1100)]
        # Weak pin: an unkeyed `boundary` redeclaration is refused by the world-revalidation path, whose wording
        # does not name D30/I37; this shows the refusal is the revalidation, not which rule.
        self.reject("boundary 1 outline " + " ".join(f"{u},{v}" for u, v in moved), "重宣告後有物件失效")
        self.commit(self.keyed_command(1, [moved]))
        self.assertEqual([1400, -100], self.bindings()[0]["translation"])
        self.assertEqual(keys, self.keymap())
        bad_keys = [keys[0][:]]
        bad_keys[0][0] = 999
        self.reject(self.keyed_command(1, [moved], bad_keys), ("D30/I37", "references a missing boundary vertex key"))
        duplicated = [keys[0][:]]
        duplicated[0][1] = duplicated[0][0]
        self.reject(self.keyed_command(1, [moved], duplicated), ("D30", "duplicate, missing, or inconsistent vertex keys"))
        self.reject("boundary-vertex-keys 1 outer 91 92 93 94 next-key 95",
                    ("D30", "cannot rebind an existing identity table"))
        # Ordinary reordered geometry keeps keys by coordinates, not old array indices.
        rotated = moved[1:] + moved[:1]
        self.boundary(outer=rotated)
        self.assertEqual(keys[0][0], self.keymap()[0][-1])
        self.assertEqual([1400, -100], self.bindings()[0]["translation"])

    def test_deleted_highest_vertex_key_is_never_reused_after_reload(self):
        with_extra = self.RECT + [(100, 600)]
        self.boundary(outer=with_extra)
        self.commit(infinite())
        self.binding()
        keys = self.keymap()[0]
        retired = keys[-1]
        self.assertEqual(max(keys), retired)
        self.commit(self.keyed_command(1, [self.RECT], [keys[:-1]]))
        self.assertIn(f"next-key {retired + 1}", self.dump())
        self.roundtrip()
        self.reject(self.keyed_command(1, [with_extra], [keys]), ("D30", "cannot reuse a retired vertex key"))
        self.commit(self.keyed_command(1, [with_extra], [keys[:-1] + [retired + 1]]))
        self.assertEqual(retired + 1, self.keymap()[0][-1])
        self.assertIn(f"next-key {retired + 2}", self.dump())

    def test_exhausted_vertex_key_space_remains_exhausted_after_high_key_removal(self):
        with_extra = self.RECT + [(100, 600)]
        self.boundary(outer=with_extra)
        self.commit("boundary-vertex-keys 1 outer 1 2 3 4 4294967295 next-key 0")
        self.commit(infinite())
        self.binding(key=1)
        self.commit(self.keyed_command(1, [self.RECT], [[1, 2, 3, 4]]))
        self.assertIn("next-key 0", self.dump())
        self.roundtrip()
        self.reject(self.keyed_command(1, [with_extra], [[1, 2, 3, 4, 5]]), ("D30", "cannot reuse a retired vertex key"))

    def test_dense_definitions_remain_valid_exact_rejects_and_sample_is_honest(self):
        self.boundary(outer=[(-1000, -1000), (1000, -1000), (1000, 1000), (-1000, 1000)])
        self.commit(infinite(u="repeat 0 1", v="repeat 0 1"))
        self.binding(cell=(0, 0))
        before = self.snapshot()
        rejected = self.query(rect=(-1000, -1000, 1000, 1000))
        self.assertFalse(rejected["ok"], rejected)
        self.assertIn("2001", json.dumps(rejected), "capacity rejection reports required counts")
        sample = self.query(rect=(-1000, -1000, 1000, 1000), mode="sample", limit=12)
        self.assertFalse(sample["exact"], sample)
        for axis in ("u", "v"):
            data = self.axis(sample, axis)
            self.assertEqual(2001, int(data["total"]))
            stride = int(data["stride"])
            self.assertGreater(stride, 1)
            self.assertLessEqual(len(data["lines"]), 12)
            # R32 fixes the phase, not the implementation's choice of stride.
            # Compare the complete declared sample so empty/partial arrays cannot
            # pass a vacuous per-row check. In particular k=0 must survive.
            expected = {k: k for k in range(-1000, 1001) if k % stride == 0}
            self.assertIn(0, expected)
            self.assertEqual(expected, self.coordinates(sample, axis))
            self.assertEqual(len(expected), len(data["lines"]), "no duplicate indices")
            self.assertEqual(-1000, int(data["firstIndex"]))
            self.assertEqual(1000, int(data["lastIndex"]))
        zoomed = self.query(rect=(-2, -2, 2, 2), limit=12)
        self.assertTrue(zoomed["exact"])
        self.assertEqual({-2: -2, -1: -1, 0: 0, 1: 1, 2: 2}, self.coordinates(zoomed, "u"))
        self.assertEqual(before, self.snapshot())
        self.roundtrip()

    def test_extreme_cell_binding_uses_exact_cancellation_not_overflowed_translation(self):
        self.boundary()
        self.commit(infinite())
        high = 9223372036854775790
        low = -9223372036854775790
        self.binding(cell=(high, low))
        binding = self.bindings()[0]
        self.assertEqual([str(high), str(low)], binding["cell"])
        self.assertIsNone(binding["translation"])
        self.assertIsNone(binding["translationExact"])
        self.assertFalse(binding["translationRepresentable"])
        result = self.query("binding", rect=(100, 200, 1300, 1000))
        self.assertEqual({high: 100, high + 1: 700, high + 2: 1300}, self.coordinates(result, "u"))
        self.assertEqual({low: 200, low + 1: 600, low + 2: 1000}, self.coordinates(result, "v"))
        self.commit("placement 1 on boundary 1 origin 0 0 0 u +x v +y")
        self.commit("grid 10 on 1 from-binding 0")
        self.commit(f"guide 1 1 v grid:10:u:{high + 1}")
        self.assertEqual(700, self.refs()["guides"][0]["off"])
        self.assertIn(f"grid:10:u:{high + 1}", self.dump())
        self.roundtrip()
        self.commit("delete guide 1")
        self.commit("delete grid 10")
        self.binding(cell=(9223372036854775806, 0), key=binding["vertexKey"])
        before = self.snapshot()
        result = self.query("binding", rect=(100, 200, 1300, 1000))
        self.assertFalse(result["ok"], result)
        self.assertEqual(before, self.snapshot())
        # The multiplication alone overflows int64, but cancellation makes the
        # derived translation representable. Rejecting its intermediate is wrong.
        self.commit(infinite(1, u="repeat 0 2", v="repeat 0 2"))
        self.binding(identifier=1, source=1, cell=(4611686018427387904, 0), key=binding["vertexKey"])
        recovered = self.bindings()[1]
        self.assertTrue(recovered["translationRepresentable"])
        self.assertEqual([-9223372036854775708, 200], recovered["translation"])
        self.assertEqual(["-9223372036854775708", "200"], recovered["translationExact"])
        self.assertEqual({4611686018427387904: 100, 4611686018427387905: 102},
                         self.coordinates(self.query("binding", 1, rect=(100, 200, 102, 202)), "u"))

    def test_query_input_limits_and_signed_overflow_never_mutate_world(self):
        self.fixture()
        before = self.snapshot()
        for rect, limit in [((0, 0, 1, 1), 0), ((0, 0, 1, 1), 65),
                            ((10, 0, 0, 1), 64), ((0, 10, 1, 0), 64),
                            ((-100000001, 0, 100, 100), 64), ((0, 0, 100000001, 100), 64)]:
            with self.subTest(rect=rect, limit=limit):
                self.assertFalse(self.query(rect=rect, limit=limit)["ok"])
                self.assertEqual(before, self.snapshot())
        # INT64_MAX parses but its upper line index overflows; 2^63 and -2^63-1 are refused at declaration (weak pin).
        for cell, why in (((9223372036854775807, 0), ("D29/R32", "exceeds signed int64")),
                          ((9223372036854775808, 0), ("D30/I37", "signed cell")),
                          ((-9223372036854775809, 0), ("D30/I37", "signed cell"))):
            self.reject(self.binding_command(identifier=1, cell=cell), why)
        edge = self.query(rect=(-100000000, -100000000, -99999000, -99999000))
        self.assertTrue(edge["ok"], edge)

    def test_lattice_guides_timbers_and_subgrid_keep_signed_identity_when_boundary_grows(self):
        self.fixture()
        self.commit("placement 1 on boundary 1 origin 0 0 0 u +x v +y")
        self.commit("grid 10 on 1 from-binding 0")
        grid = self.grids()[10]
        self.assertEqual("lattice", grid["indexSpace"])
        self.assertEqual(0, grid["bindingId"])
        self.assertTrue(all(isinstance(row["index"], str) for row in grid["lines"]))
        for command in [
            "guide 1 1 v grid:10:u:-1", "guide 2 1 v grid:10:u:-10",
            "spec signed_offset 20", "guide 3 1 v grid:10:u:-3+spec:signed_offset",
            "timber 90 20 33 role boundary", "place 90 on 1 at-face e0 +u +n",
            "timber 91 20 33 role boundary", "place 91 on 1 at-face e2 +u +n",
            "timber 1 27 33 role primary", "place 1 on 1 at-line grid 10 u -1 +v +n",
            "subgrid 11 parent 10 lattice-cell -2 1 divisions u 2 v 2",
        ]:
            self.commit(command)
        refs = self.refs()
        guides = {row["id"]: row for row in refs["guides"]}
        self.assertEqual(700, guides[1]["off"])
        self.assertEqual(-4700, guides[2]["off"])
        self.assertEqual(-480, guides[3]["off"])
        self.assertEqual([], guides[2]["segments"])
        timber = next(row for row in refs["timbers"] if row["id"] == 1)
        self.assertEqual(700, timber["geometry"]["centerline"])
        self.assertEqual("at-line grid 10 u -1", timber["definition"]["anchor"])
        self.assertEqual([400], self.grids()[11]["u"])
        self.assertEqual([400], self.grids()[11]["v"])
        self.commit("timber 2 27 33 role primary")
        self.reject("place 2 on 1 at-line grid 10 u -10 +v +n", "中線上沒有任何合法跨距")
        # Remove the unplaced fixture before testing save/reload completeness.
        self.commit("delete timber 2")
        expanded = [(100, 200), (2500, 200), (2500, 1800), (100, 1800)]
        self.commit(self.keyed_command(1, [expanded]))
        self.assertEqual([400], self.grids()[11]["u"])
        self.assertEqual([400], self.grids()[11]["v"])
        self.assertEqual(-4700, next(g for g in self.refs()["guides"] if g["id"] == 2)["off"])
        self.assertEqual({-2: 100, -1: 700, 0: 1300, 1: 1900, 2: 2500},
                         self.coordinates(self.query("grid", 10, rect=(100, 200, 2500, 1800)), "u"))
        for command, why in [("delete grid-binding 0", ("I37", "grid-binding is still referenced by a grid")),
                             ("delete grid-system 0", ("I37", "grid-system is still referenced by a grid-binding")),
                             ("grid 10 on 1 u 500 1000", ("D29", "direct axis edits are not allowed")),
                             ("grid 10 on 1 main-along u", ("D29", "direct axis edits are not allowed")),
                             ("grid 10 on 1 from-system 0 origin 0 0", ("I37", "existing grid identity")),
                              # I25: an infinite parent requires signed lattice-cell references.
                              ("subgrid 12 parent 10 cell u line:0 line:1 v min line:0 divisions u 2 v 2",
                               ("D19/I25", "子格 12", "父格 10", "lattice-cell"))]:
            self.reject(command, why)
        self.roundtrip()

    def test_wrong_placement_boundary_and_binding_capacity_are_atomic(self):
        self.fixture()
        self.boundary(2)
        self.commit("placement 2 on boundary 2 origin 0 0 0 u +x v +y")
        self.reject("grid 10 on 2 from-binding 0", ("D30/I37", "invalid grid-binding identity, capacity or application"))
        self.reject("delete boundary 1", ("I37", "boundary is still referenced by a grid-binding"))
        key = self.bindings()[0]["vertexKey"]
        for identifier in range(1, 31):
            self.binding(identifier, key=key)
        self.binding(4294967295, key=key)
        self.assertEqual(32, len(self.bindings()))
        self.reject(self.binding_command(identifier=31, key=key), ("I37", "grid-binding capacity is 32"))

    def test_source_or_vertex_failure_rolls_back_every_binding_and_dependent_geometry(self):
        self.fixture(second=True)
        self.commit("placement 1 on boundary 1 origin 0 0 0 u +x v +y")
        self.commit("grid 10 on 1 from-binding 0")
        self.commit("subgrid 11 parent 10 lattice-cell -2 1 divisions u 2 v 2")
        before = self.snapshot()
        # The left-top binding could accept 601, but the second center binding
        # cannot. Neither the source nor the already-valid first candidate commits.
        preview = self.preview(infinite(u="repeat 0 601"))
        self.assertFalse(preview["valid"], preview)
        self.assertFalse(self.line("confirm " + str(preview["token"]))["ok"])
        self.assertEqual(before, self.snapshot())
        preview = self.preview(infinite(u="repeat 0 800", v="repeat 0 500"))
        self.assertTrue(preview["valid"], preview)
        self.commit("spec changed_after_review 10")
        stale = self.snapshot()
        self.assertFalse(self.line("confirm " + str(preview["token"]))["ok"])
        self.assertEqual(stale, self.snapshot())
        bad_path = Path(self.directory.name) / "bad-infinite.scene"
        bad_path.write_text(self.dump().replace("from-binding 0", "from-binding 99"), encoding="utf-8")
        self.assertFalse(self.command("loadfile " + native_path(bad_path))["ok"])
        self.assertEqual(stale, self.snapshot())

    def test_legacy_finite_replay_keeps_ordinal_indices_and_cannot_silently_convert(self):
        self.commit("surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000")
        self.commit(finite_system())
        self.commit("grid 10 on 1 from-system 0 origin 0 0")
        before = self.snapshot()
        self.assertEqual("legacy-finite", self.objects()["gridSystems"][0]["mode"])
        self.assertEqual("ordinal", self.grids()[10]["indexSpace"])
        self.assertEqual([100, 300, 500], self.grids()[10]["u"])
        self.reject(infinite(), ("D29/I37", "cannot be converted implicitly"))
        self.assertEqual(before, self.snapshot())
        self.roundtrip()
        self.assertEqual(before, self.snapshot())
        self.commit(infinite(1))
        self.binding(1, source=1)
        self.reject("grid 10 on 1 from-binding 1", ("D30/I37", "requires an available lattice grid identity"))

    def band_segments(self, result, axis):
        rows = []
        for line in self.axis(result, axis)["lines"]:
            self.assertIsInstance(line["index"], str)
            for segment in line["segments"]:
                self.assertIsInstance(segment["band"], str)
                rows.append((int(line["index"]), int(segment["band"]), segment["a"], segment["b"]))
        return rows

    def test_alternating_stagger_segments_match_the_hand_oracle(self):
        self.commit(infinite(u="repeat 0 2000", v="repeat 0 1830 stagger 400"))
        result = self.query(rect=(-2000, 0, 4000, 5000))
        expected = []
        for index, base in ((0, 0), (1, 1830), (2, 3660)):
            for band, u0, u1 in ((-1, -2000, 0), (0, 0, 2000), (1, 2000, 4000)):
                coord = base + (400 if band & 1 else 0)
                expected.append((index, band, [u0, coord], [u1, coord]))
        self.assertEqual(expected, self.band_segments(result, "v"))
        self.assertEqual({0: 0, 1: 1830, 2: 3660}, self.coordinates(result, "v"))
        for line in self.axis(result, "u")["lines"]:
            for segment in line["segments"]:
                self.assertNotIn("band", segment)
        text = self.dump()
        self.assertIn("v repeat 0 1830 stagger 400", text)
        self.assertNotIn("u repeat 0 2000 stagger", text)
        self.roundtrip()
        narrow = self.query(rect=(2000, 300, 4000, 500))
        self.assertEqual([(0, 1, [2000, 400], [4000, 400])], self.band_segments(narrow, "v"))

    def test_unstaggered_scenes_do_not_gain_stagger_or_band(self):
        self.commit(infinite())
        self.assertNotIn("stagger", self.dump())
        result = self.query()
        for axis in ("u", "v"):
            for line in self.axis(result, axis)["lines"]:
                for segment in line["segments"]:
                    self.assertEqual(["a", "b"], sorted(segment))

    def test_stagger_rejects_zero_multiples_finite_axes_and_subgrids(self):
        self.reject(infinite(v="repeat 0 1830 stagger 0"), "相位差為 0")
        self.reject(infinite(v="repeat 0 1830 stagger 1830"), "整數倍")
        self.reject(infinite(v="repeat 0 1830 stagger -3660"), "整數倍")
        self.reject(infinite(u="repeat 0 2000", v="series 0 1830 3 stagger 400"), "只接受無限軸")
        self.reject(infinite(u="none", v="repeat 0 1830 stagger 400"), "兩軸都存在")
        self.commit(infinite(u="repeat 0 2000", v="repeat 0 1830 stagger 400"))
        self.boundary(outer=[(0, 0), (4000, 0), (4000, 4000), (0, 4000)])
        self.binding(cell=(0, 0), anchor=(0, 1, 0, 1))
        self.commit("placement 1 on boundary 1 origin 0 0 0 u +x v +y")
        self.commit("grid 10 on 1 from-binding 0")
        self.reject("subgrid 11 parent 10 lattice-cell 0 0 divisions u 2 v 2", "不能建立子網格")
        self.commit("timber 90 20 33 role boundary")
        self.commit("place 90 on 1 at-face e3 +v +n")
        self.commit("timber 91 20 33 role boundary")
        self.commit("place 91 on 1 at-face e1 +v +n")
        self.commit("timber 1 27 33 role primary")
        self.reject("place 1 on 1 at-line grid 10 v 0 +u +n", "必須寫 band")
        self.reject("place 1 on 1 at-line grid 10 u 0 band 0 +v +n", "不能寫 band")
        self.reject("place 1 on 1 at-line grid 10 v 1 band 0 +u +n", "沿線範圍超出該格子")
        self.commit("boundary-keyed 1 geometry-hash " + self.fingerprint(1) + " outline "
                    + " ".join(f"{key}:{u},{v}" for key, (u, v) in zip(self.keymap(1)[0], [(0, 0), (2000, 0), (2000, 4000), (0, 4000)])))
        self.commit("place 1 on 1 at-line grid 10 v 1 band 0 +u +n")
        timber = next(row for row in self.refs()["timbers"] if row["id"] == 1)
        self.assertEqual("at-line grid 10 v 1 band 0", timber["definition"]["anchor"])
        self.assertIn("band 0", self.dump())
        self.roundtrip()

    def test_adding_stagger_to_a_parent_with_a_subgrid_rolls_back(self):
        self.fixture()
        self.commit("placement 1 on boundary 1 origin 0 0 0 u +x v +y")
        self.commit("grid 10 on 1 from-binding 0")
        self.commit("subgrid 11 parent 10 lattice-cell -2 1 divisions u 2 v 2")
        self.reject(infinite(v="repeat 0 400 stagger 100"), "不能建立子網格")
        self.assertNotIn("stagger", self.dump())

    def test_parameter_stagger_survives_dump_and_zero_is_rejected_after_evaluation(self):
        revision = self.command("engineering-read")
        self.assertTrue(revision["ok"], revision)
        path = Path(self.directory.name) / "parameter.json"
        path.write_text(json.dumps({
            "schema": "engineering-transaction/1",
            "expectedRevision": revision["revision"],
            "operations": [{"op": "put-parameter", "value": {"id": 1, "name": "相位", "fields": [
                {"id": 1, "name": "差", "type": "dimension", "input": "400"},
                {"id": 2, "name": "零", "type": "dimension", "input": "0"},
                {"id": 3, "name": "倍", "type": "dimension", "input": "1830"},
            ]}}],
        }, ensure_ascii=False), encoding="utf-8")
        preview = self.command("engineering-preview " + native_path(path))
        self.assertTrue(preview["ok"] and preview["preview"]["valid"], preview)
        self.assertTrue(self.command("engineering-confirm " + str(preview["preview"]["token"]))["ok"])
        self.commit(infinite(u="repeat 0 2000", v="repeat 0 1830 stagger param:1:1"))
        self.assertEqual(400, self.objects()["gridSystems"][0]["vDefinition"]["stagger"])
        self.assertIn("stagger param:1:1", self.dump())
        self.roundtrip()
        self.reject(infinite(u="repeat 0 2000", v="repeat 0 1830 stagger param:1:2"), "相位差為 0")
        self.reject(infinite(u="repeat 0 2000", v="repeat 0 1830 stagger param:1:3"), "整數倍")

    def test_exact_stagger_query_reports_capacity_when_bands_exceed_the_segment_limit(self):
        self.commit(infinite(u="repeat 0 100", v="repeat 0 1830 stagger 400"))
        exact = self.query(rect=(0, 0, 4000, 2000))
        self.assertFalse(exact["ok"], exact)
        self.assertEqual("QUERY_CAPACITY", exact["code"])
        sample = self.query(rect=(0, 0, 4000, 2000), mode="sample")
        self.assertTrue(sample["ok"], sample)
        self.assertFalse(sample["exact"], "R22: thinning bands must disclose incompleteness")
        self.assertGreater(int(self.axis(sample, "v")["stride"]), 1)
        for axis, last, total, pitch in (("u", 40, 41, 100), ("v", 1, 2, 1830)):
            data = self.axis(sample, axis)
            self.assertEqual((0, last, total), tuple(int(data[key]) for key in
                             ("firstIndex", "lastIndex", "total")))
            coordinates = self.coordinates(sample, axis)
            self.assertIn(0, coordinates, "the global origin is retained in this view")
            self.assertLessEqual(len(data["lines"]), 64)
            self.assertEqual(len(coordinates), len(data["lines"]))
            for index, coordinate in coordinates.items():
                self.assertTrue(0 <= index <= last)
                self.assertEqual(index * pitch, coordinate)
            for line in data["lines"]:
                self.assertTrue(line["segments"], "visible sampled lines must have geometry")
        # R22 determines each returned segment independently of the chosen
        # thinning policy; do not require a particular stride or band subset.
        for index, band, a, b in self.band_segments(sample, "v"):
            self.assertTrue(0 <= band < 40)
            coordinate = index * 1830 + (400 if band & 1 else 0)
            self.assertTrue(0 <= coordinate <= 2000)
            self.assertEqual([band * 100, coordinate], a)
            self.assertEqual([(band + 1) * 100, coordinate], b)


if __name__ == "__main__":
    unittest.main(verbosity=2)
