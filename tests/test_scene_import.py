"""Fresh native final-object candidate, atomic confirmation and history oracle."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


@unittest.skipUnless(os.environ.get('GEOMETRY_TEST_BRIDGE'), 'GEOMETRY_TEST_BRIDGE required')
class SceneImportTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.stderr = tempfile.TemporaryFile()
        self.bridge = subprocess.Popen([os.environ['GEOMETRY_TEST_BRIDGE']], stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=self.stderr, text=True)

    def tearDown(self):
        self.bridge.stdin.close()
        exit_code = self.bridge.wait(timeout=5)
        self.bridge.stdout.close()
        self.stderr.seek(0)
        diagnostics = self.stderr.read().decode('utf-8', errors='replace')
        self.stderr.close()
        self.directory.cleanup()
        self.assertEqual(exit_code, 0, diagnostics)

    def ask(self, command):
        self.bridge.stdin.write(command + '\n')
        self.bridge.stdin.flush()
        return json.loads(self.bridge.stdout.readline())

    def prepare(self, scene):
        path = Path(self.directory.name) / 'candidate.scene'
        path.write_text(scene, encoding='utf-8')
        return self.ask('load-prepare ' + str(path))

    def assert_candidate_pins(self, candidate, scene):
        """A second actual native World is the oracle, never a JS hash/live lookup."""
        self.assertTrue(candidate['ok'], candidate)
        objects = candidate['final_objects']
        entries = objects['boundaryFingerprints']
        self.assertEqual([row['id'] for row in entries], objects['boundaries'])
        self.assertEqual(len({row['id'] for row in entries}), len(entries))
        for row in entries:
            self.assertEqual(set(row), {'id', 'geometryFingerprint'})
            self.assertRegex(row['geometryFingerprint'], r'^[0-9a-f]{64}$')
        path = Path(self.directory.name) / 'oracle.scene'
        path.write_text(scene, encoding='utf-8')
        commands = ['loadfile ' + str(path), *('boundary ' + str(row['id']) for row in entries)]
        oracle = subprocess.run([os.environ['GEOMETRY_TEST_BRIDGE']], input='\n'.join(commands) + '\n',
                                capture_output=True, text=True, timeout=10, check=True)
        responses = [json.loads(line) for line in oracle.stdout.splitlines()]
        self.assertTrue(responses[0]['ok'], responses)
        self.assertEqual(entries, [{'id': row['id'], 'geometryFingerprint': row['geometryFingerprint']}
                                   for row in responses[1:]])
        return entries

    def test_final_objects_trim_reset_delete_redeclare_and_zero(self):
        boundary = 'boundary 1 outline 0,0 800,0 800,700 0,700\n'
        cases = [(boundary, [1]), ('  ' + boundary, [1]), (boundary + 'reset\n', []),
                 (boundary + 'delete boundary 1\n', []),
                 (boundary + 'delete boundary 1\n' + boundary, [1]),
                 (boundary + 'placement 0 on boundary 1 origin 0 0 0 u +x v +y\n', [1])]
        before = self.ask('dump')
        for scene, expected in cases:
            with self.subTest(scene=scene):
                candidate = self.prepare(scene)
                self.assertTrue(candidate['ok'], candidate)
                self.assertEqual(candidate['final_objects']['boundaries'], expected)
                self.assert_candidate_pins(candidate, scene)
                self.assertEqual(self.ask('dump'), before)
                self.assertTrue(self.ask(f"load-cancel {candidate['token']}")['cancelled'])
                self.assertFalse(self.ask(f"load-confirm {candidate['token']}")['ok'])
        self.assertFalse(self.prepare(boundary.replace('boundary 1', 'boundary 0'))['ok'])
        self.assertEqual(self.ask('dump'), before)

    def test_default_and_empty_candidate_pins(self):
        before = self.ask('dump')
        for scene in [before['text'], '', '# empty\n', 'reset\n']:
            with self.subTest(scene=scene):
                candidate = self.prepare(scene)
                self.assert_candidate_pins(candidate, scene)
                self.assertEqual(self.ask('dump'), before)
                self.assertTrue(self.ask(f"load-cancel {candidate['token']}")['cancelled'])

    def test_detached_pins_differ_from_live_and_expired_tokens_cannot_replace_candidate(self):
        before = self.ask('dump')
        live = self.ask('boundary 1')['geometryFingerprint']
        scenes = ['boundary 1 outline 0,0 80,0 80,70 0,70\n',
                  'boundary 1 kind room_plan outline 1000,1000 7000,1000 7000,5000 1000,5000\n'
                  'boundary 2 kind wall_elevation outline 10000,0 14000,0 14000,3000 10000,3000\n']
        old = self.prepare(scenes[0])
        old_pin = self.assert_candidate_pins(old, scenes[0])[0]['geometryFingerprint']
        current = self.prepare(scenes[1])
        current_entries = self.assert_candidate_pins(current, scenes[1])
        self.assertEqual(current_entries, [
            {'id': 1, 'geometryFingerprint': '8fed27137c6e361ce8b20aa7e33885a4d4d3eccf26eec49aaf3555f7caa2e576'},
            {'id': 2, 'geometryFingerprint': '6f12c618020027d8e6181dd87d4d3aea3944b3e25a4b36913c68632750751f2c'}])
        current_pin = current_entries[0]['geometryFingerprint']
        self.assertEqual(len({live, old_pin, current_pin}), 3)
        self.assertFalse(self.ask('boundary 2')['ok'])
        for token in [0, old['token'], current['token'] + 1]:
            self.assertFalse(self.ask(f'load-cancel {token}')['cancelled'])
            self.assertEqual(self.ask(f'load-confirm {token}')['code'], 'TOKEN')
            self.assertEqual(self.ask('dump'), before)
            self.assertEqual(self.ask('boundary 1')['geometryFingerprint'], live)
        # The backing file can change; confirmation must publish the pinned World.
        (Path(self.directory.name) / 'candidate.scene').write_text(scenes[0])
        self.assertTrue(self.ask(f"load-confirm {current['token']}")['ok'])
        self.assertEqual(self.ask('boundary 1')['geometryFingerprint'], current_pin)
        self.assertEqual(self.ask('boundary 2')['geometryFingerprint'], current_entries[1]['geometryFingerprint'])
        self.assertEqual(self.ask('dump')['revision'], before['revision'] + 1)
        after = self.ask('dump')['text']
        self.assertTrue(self.ask('line undo')['ok'])
        self.assertEqual(self.ask('dump')['text'], before['text'])
        self.assertTrue(self.ask('line redo')['ok'])
        self.assertEqual(self.ask('dump')['text'], after)
        self.assertFalse(self.ask(f"load-confirm {current['token']}")['ok'])

    def test_pins_keep_native_kind_holes_fixity_and_ignore_presentation_and_id(self):
        outline = 'outline 0,0 800,0 800,700 0,700'
        definitions = [outline, outline + ' kind room_plan', outline + ' kind wall_elevation',
                       outline + ' fixity fixed free fixed fixed',
                       outline + ' hole 100,100 200,100 200,200 100,200',
                       outline + ' hole 100,100 200,100 200,200 100,200 fixity fixed free fixed fixed']
        before = self.ask('dump')
        hashes = []
        for definition in definitions:
            scene = 'boundary 1 ' + definition + '\n'
            candidate = self.prepare(scene)
            hashes.append(self.assert_candidate_pins(candidate, scene)[0]['geometryFingerprint'])
            self.assertTrue(self.ask(f"load-cancel {candidate['token']}")['cancelled'])
            self.assertEqual(self.ask('dump'), before)
        self.assertEqual(len(set(hashes)), len(hashes))
        for scene in ['boundary 4294967295 ' + outline + '\n',
                      'boundary 1 ' + outline + '\ncanvas-pos boundary 1 123 456\n',
                      'boundary 1 ' + outline + '\nplacement 0 on boundary 1 origin 0 0 9 u +x v +y\n']:
            candidate = self.prepare(scene)
            self.assertEqual(self.assert_candidate_pins(candidate, scene)[0]['geometryFingerprint'], hashes[0])
            self.assertTrue(self.ask(f"load-cancel {candidate['token']}")['cancelled'])
            self.assertEqual(self.ask('dump'), before)

    def test_bounded_full_capacity_and_failed_reference_preserve_pending_preview(self):
        # Default native timber 3 depends on guide 1. This owned preview must
        # remain confirmable after successful/failed imports and cancellations.
        pending = self.ask('line spec 主支中線 900')['preview']
        self.assertTrue(pending['valid'], pending)
        before = self.ask('dump')
        full = ''.join(f'boundary {i} outline 0,0 80,0 80,70 0,70\n' for i in range(1, 17))
        candidate = self.prepare(full)
        entries = self.assert_candidate_pins(candidate, full)
        self.assertEqual(len(entries), 16)
        self.assertLess(len(json.dumps(entries)), 1800)
        self.assertTrue(self.ask(f"load-cancel {candidate['token']}")['cancelled'])
        invalid = [full + 'boundary 17 outline 0,0 80,0 80,70 0,70\n',
                   'boundary 0 outline 0,0 80,0 80,70 0,70\n',
                   'placement 0 on boundary 7 origin 0 0 0 u +x v +y\n',
                   'boundary 7 outline 0,0 80,0 80,70 0,70\ndelete boundary 7\n'
                   'placement 0 on boundary 7 origin 0 0 0 u +x v +y\n']
        for scene in invalid:
            prior = self.prepare('boundary 7 outline 0,0 80,0 80,70 0,70\n')
            rejected = self.prepare(scene)
            self.assertFalse(rejected['ok'], rejected)
            self.assertNotIn('final_objects', rejected)
            self.assertEqual(self.ask('dump'), before)
            self.assertEqual(self.ask(f"load-confirm {prior['token']}")['code'], 'TOKEN')
        self.assertTrue(self.ask(f"line confirm {pending['token']}")['ok'])
        self.assertTrue(self.ask('line undo')['ok'])
        self.assertEqual(self.ask('dump')['text'], before['text'])

    def test_commits_exact_candidate_without_reparse_and_one_undo(self):
        before = self.ask('dump')['text']
        candidate = self.prepare('boundary 7 outline 0,0 80,0 80,70 0,70\n')
        (Path(self.directory.name) / 'candidate.scene').write_text('reset\n')
        self.assertTrue(self.ask(f"load-confirm {candidate['token']}")['ok'])
        after = self.ask('dump')['text']
        self.assertIn('boundary 7 ', after)
        self.assertTrue(self.ask('line undo')['ok'])
        self.assertEqual(self.ask('dump')['text'], before)
        self.assertTrue(self.ask('line redo')['ok'])
        self.assertEqual(self.ask('dump')['text'], after)

    def test_stale_candidate_rejects_geometry_canvas_and_aba_changes(self):
        for mutation in [['line spec X 27'], ['line canvas-pos boundary 1 60 60'],
                         ['line spec X 27', 'line undo']]:
            with self.subTest(mutation=mutation):
                candidate = self.prepare('boundary 7 outline 0,0 80,0 80,70 0,70\n')
                for command in mutation:
                    self.assertTrue(self.ask(command)['ok'])
                before = self.ask('dump')
                rejected = self.ask(f"load-confirm {candidate['token']}")
                self.assertFalse(rejected['ok'])
                self.assertEqual(self.ask('dump'), before)

    def test_saved_canvas_positions_replace_prior_positions_on_same_id(self):
        self.assertTrue(self.ask('line canvas-pos boundary 1 60 60')['ok'])
        candidate = self.prepare('boundary 1 outline 0,0 80,0 80,70 0,70\ncanvas-pos boundary 1 900 900\n')
        self.assertTrue(self.ask(f"load-confirm {candidate['token']}")['ok'])
        self.assertIn('canvas-pos boundary 1 900 900', self.ask('dump')['text'])
        candidate = self.prepare('boundary 1 outline 0,0 80,0 80,70 0,70\n')
        self.assertTrue(self.ask(f"load-confirm {candidate['token']}")['ok'])
        self.assertNotIn('canvas-pos boundary', self.ask('dump')['text'])

    def test_final_placement_zero_deleted_and_redeclared_targets(self):
        boundary = 'boundary 1 outline 0,0 80,0 80,70 0,70\n'
        placement = 'placement 0 on boundary 1 origin 0 0 0 u +x v +y\n'
        self.assertEqual(self.prepare(boundary + placement)['final_objects']['placements'],
                         [{'id': 0, 'bid': 1, 'horizontal': True}])
        self.assertEqual(self.prepare(boundary + placement + 'delete placement 0\n')['final_objects']['placements'], [])
        self.assertEqual(self.prepare(boundary + placement + placement.replace('v +y', 'v +z'))['final_objects']['placements'],
                         [{'id': 0, 'bid': 1, 'horizontal': False}])

    def test_failed_prepare_and_group_leave_world_history_and_prior_preview(self):
        self.assertTrue(self.ask('line spec X 27')['ok'])
        before = self.ask('dump')
        self.assertFalse(self.prepare('not-a-scene\n')['ok'])
        self.assertEqual(self.ask('dump'), before)
        self.assertTrue(self.ask('line undo')['ok'])
        self.assertNotIn('spec X ', self.ask('dump')['text'])
        self.assertTrue(self.ask('line history-begin')['ok'])
        self.assertFalse(self.prepare('reset\n')['ok'])
        self.assertTrue(self.ask('line history-abort')['ok'])


if __name__ == '__main__':
    unittest.main()
