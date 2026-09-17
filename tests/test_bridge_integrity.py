"""Semantic persistence and malformed-input regression tests.

GEOMETRY_TEST_BRIDGE=/absolute/path/to/bridge python tests/test_bridge_integrity.py
The bridge runs only against temporary worlds; no running server is used.
"""
import json
import os
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
BRIDGE = os.environ.get("GEOMETRY_TEST_BRIDGE", str(ROOT / "geometry-web/web_bridge.exe"))


class IntegrityTests(unittest.TestCase):
    def bridge(self, commands):
        p = subprocess.run([BRIDGE], input="\n".join(commands) + "\n",
                           capture_output=True, text=True, encoding="utf-8", timeout=20)
        self.assertEqual(p.returncode, 0, p.stderr)
        rows = [json.loads(line) for line in p.stdout.splitlines()]
        self.assertEqual(len(rows), len(commands), p.stdout)
        return rows

    def test_truncated_beam_preserves_world_and_connection(self):
        seeds = ["beam 1 in 1 along x from 0 to 1000 at 500 width 100 depth 100 top 2000",
                 "beam 1 along y from 0 to 1000 at 500 width 100 depth 100 top 2000"]
        for seed in seeds:
            words = seed.split()
            for n in range(1, len(words)):
                command = " ".join(words[:n])
                with self.subTest(command=command):
                    r = self.bridge(["default", "dump", "line " + command, "dump", "objects"])
                    self.assertFalse(r[2]["ok"])
                    self.assertEqual(r[1], r[3])
                    self.assertTrue(r[4]["ok"])

    def test_removed_frozen_metadata_is_rejected_atomically(self):
        for cmd in ['span-auto 3', 'place 3 on 1 at 514 27 +v +n grid-ref 1 u 0',
                    'timber 9 1000 27 33 role primary']:
            r = self.bridge(['default', 'dump', 'line ' + cmd, 'dump'])
            self.assertFalse(r[2]['ok'])
            self.assertEqual(r[1], r[3])

    def test_auto_support_and_reference_roundtrip(self):
        before = self.bridge(['loadfile ' + str(ROOT / '_role_ext_stop_primary.scene'), 'dump',
                              'line delete timber 3', 'dump'])
        self.assertTrue(before[0]['ok'], before[0])
        self.assertFalse(before[2]['ok'])
        self.assertIn('preview', before[2])
        self.assertEqual(before[1], before[3])
        self.assertIn('at-face', before[1]['text'])
        self.assertNotIn('span-auto', before[1]['text'])
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / 'edge.scene'
            path.write_text(before[1]['text'], encoding='utf-8')
            after = self.bridge(['loadfile ' + str(path), 'dump', 'line delete timber 3', 'dump'])
        self.assertTrue(after[0]['ok'], after[0])
        self.assertEqual(before[1], after[1])
        self.assertFalse(after[2]['ok'])
        self.assertEqual(after[1], after[3])

    def test_beam_centers_survive_repeated_reload(self):
        lines = []
        for axis in ['x', 'y']:
            for center in [-100, -1, 0, 100]:
                for width in [1, 2, 300, 301]:
                    lines.append(f'line beam {len(lines)+1} along {axis} from -1000 to 1000 at {center} width {width} depth 100 top 2500')
        before = self.bridge(['reset'] + lines + ['objects', 'dump', 'render'])
        self.assertTrue(all(r['ok'] for r in before))
        expected = before[-3:]
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / 'beams.scene'
            for _ in range(3):
                path.write_text(before[-2]['text'], encoding='utf-8')
                before = self.bridge(['loadfile ' + str(path), 'objects', 'dump', 'render'])
                self.assertTrue(before[0]['ok'], before[0])
                self.assertEqual(expected, before[-3:])

    def test_boundary_kind_survives_reload(self):
        for kind in ['room_plan', 'wall_elevation', 'unspecified']:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                r = self.bridge(['reset', f'line boundary 1 outline 0,0 4000,0 4000,3000 0,3000 kind {kind}', 'dump'])
                self.assertTrue(r[1]['ok'])
                if kind != 'unspecified':
                    self.assertIn('kind ' + kind, r[-1]['text'])
                path = pathlib.Path(tmp) / 'kind.scene'
                path.write_text(r[-1]['text'], encoding='utf-8')
                after = self.bridge(['loadfile ' + str(path), 'dump'])
                self.assertTrue(after[0]['ok'])
                self.assertEqual(r[-1], after[-1])

    def test_failed_auto_place_restores_draft_and_redo(self):
        lines = [l for l in (ROOT / '_role_priority_primary_rc.scene').read_text(encoding='utf-8').splitlines()
                 if l.strip() and not l.startswith('#')]
        setup = ['reset'] + ['line ' + l for l in lines[:-1]]
        r = self.bridge(setup + ['line guide 90 1 u 1/2*edge:e2:v', 'line undo', 'dump',
                                 'line ' + lines[-1], 'dump', 'line redo', 'dump'])
        self.assertFalse(r[-4]['ok'])
        self.assertIn('V_CUT_PRIORITY', r[-4]['error'])
        self.assertEqual(r[-5], r[-3], 'a rejected placement must leave the draft unchanged')
        self.assertTrue(r[-2]['ok'], 'rejection must preserve redo history')
        self.assertIn('guide 90 1 u 1/2*edge:e2:v', r[-1]['text'])

    def test_drag_history_group_and_cancel(self):
        # View 2 maps ceiling u,v directly to x,y.
        setup = ['reset', 'line surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
                 'line spec start 300', 'line spec middle 600', 'line spec end 900', 'line spec cancel 1200', 'line guide 1 1 u spec:start']
        r = self.bridge(setup + ['dump', 'line history-begin', 'drag 0 2 2500 600',
                                'drag 0 2 2500 900', 'line history-end', 'dump',
                                'line undo', 'dump', 'line redo', 'dump',
                                'line history-begin', 'drag 0 2 2500 1200',
                                'line history-abort', 'dump'])
        self.assertTrue(all(x['ok'] for x in r), r)
        self.assertIn('guide 1 1 u spec:end', r[-9]['text'])
        self.assertEqual(r[len(setup)], r[-7], 'one undo must restore the entire gesture')
        self.assertEqual(r[-9], r[-5])
        self.assertEqual(r[-5], r[-1], 'cancel must restore the gesture start')

    def test_large_coordinates_rejected_without_mutation(self):
        commands = [
            'line boundary 8 outline 0,0 4000000000,0 4000000000,4000000000 0,4000000000',
            'line boundary 8 outline 0,0 9223372036854775807,0 9223372036854775807,3000 0,3000',
            'line placement 1 on boundary 1 origin -9223372036854775808 0 0 u +x v +y',
            'line guide 8 1 u 100000001', 'line timber 8 100000001 27 33 role primary',
            'line column 8 at 100000001 0 size 100 100 z 0 2500',
            'line beam 8 along x from 0 to 1000 at 0 width 100000001 depth 100 top 2500',
            'line grid 8 on 1 u series 0 9223372036854775807 2',
            'pick 2 9223372036854775807 0 10', 'drag 0 2 0 -9223372036854775808',
            'uv 2 4000000000 0 1', 'proj 2 4000000000 0 1', 'bhit 1 0 0 4000000000']
        for command in commands:
            with self.subTest(command=command):
                r = self.bridge(['default', 'dump', command, 'dump', 'render'])
                self.assertFalse(r[2]['ok'], command)
                self.assertEqual(r[1], r[3])
                self.assertTrue(r[4]['ok'])
        # The maximum supported definitions and full uint32 IDs remain accepted.
        r = self.bridge(['reset', 'line boundary 4294967295 outline -100000000,-100000000 100000000,-100000000 100000000,100000000 -100000000,100000000',
                         'line placement 1 on boundary 4294967295 origin 100000000 100000000 100000000 u +x v +y',
                         'render', 'dump', 'proj 2 100000000 100000000 1',
                         'uv 2 200000000 200000000 1', 'pick 2 200000000 200000000 10'])
        self.assertTrue(all(x['ok'] for x in r), r)
        self.assertEqual((r[-2]['u'], r[-2]['v']), (100000000, 100000000))

    def test_all_accepted_scenes_keep_geometry_and_canonical_dump(self):
        # Use the repository's accepted fixtures, including role/grid/projection combinations.
        from run_tests import TESTS
        for spec in TESTS:
            if spec["expect"] != "accept":
                continue
            with self.subTest(scene=spec["scene"]), tempfile.TemporaryDirectory() as tmp:
                before = self.bridge(["loadfile " + str(ROOT / spec["scene"]), "dump", "render"])
                self.assertTrue(before[0]["ok"], before[0])
                path = pathlib.Path(tmp) / "saved.scene"
                path.write_text(before[1]["text"], encoding="utf-8")
                after = self.bridge(["loadfile " + str(path), "dump", "render"])
                self.assertTrue(after[0]["ok"], after[0])
                self.assertEqual(before[1:], after[1:])


if __name__ == "__main__":
    unittest.main()
