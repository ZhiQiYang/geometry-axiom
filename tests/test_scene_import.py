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
        self.bridge = subprocess.Popen([os.environ['GEOMETRY_TEST_BRIDGE']], stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)

    def tearDown(self):
        self.bridge.stdin.close()
        self.bridge.wait(timeout=5)
        self.bridge.stdout.close()
        self.directory.cleanup()

    def ask(self, command):
        self.bridge.stdin.write(command + '\n')
        self.bridge.stdin.flush()
        return json.loads(self.bridge.stdout.readline())

    def prepare(self, scene):
        path = Path(self.directory.name) / 'candidate.scene'
        path.write_text(scene, encoding='utf-8')
        return self.ask('load-prepare ' + str(path))

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
                self.assertEqual(self.ask('dump'), before)
                self.assertTrue(self.ask(f"load-cancel {candidate['token']}")['cancelled'])
                self.assertFalse(self.ask(f"load-confirm {candidate['token']}")['ok'])
        self.assertFalse(self.prepare(boundary.replace('boundary 1', 'boundary 0'))['ok'])
        self.assertEqual(self.ask('dump'), before)

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
