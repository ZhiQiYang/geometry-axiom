"""I8/I8a candidate retirement never leaks into another command or reader."""
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import test_parameters_core as harness
from tests.test_parameters_core import card, field


class ParameterRetirementScope(unittest.TestCase):
    setUpClass = classmethod(harness.ParametersCore.setUpClass.__func__)
    setUp = harness.ParametersCore.setUp
    command = harness.ParametersCore.command
    read = harness.ParametersCore.read
    request = harness.ParametersCore.request
    apply = harness.ParametersCore.apply
    apply_line = harness.ParametersCore.apply_line
    archive_line = harness.ParametersCore.archive_line

    def seed(self, extra=()):
        self.apply([card(0, 'Unreferenced live card', [field(1, '10')]), *extra])
        return self.command('dump')['text']

    def assert_archive_can_edit_live_card(self, before):
        self.assertEqual(before, self.command('dump')['text'], 'failed or read-only work changed live World')
        pending = self.command('line preview ' + self.archive_line(card(0, 'Changed by a later command', [field(1, '20')])))
        self.assertTrue(pending['ok'], pending)
        self.assertTrue(pending['preview']['valid'], 'candidate retirement leaked into the next DSL preview: ' + repr(pending))
        self.assertEqual(before, self.command('dump')['text'], 'the new preview itself changed live World')
        self.assertTrue(self.command('line cancel-preview')['ok'])
        self.assertEqual(before, self.command('dump')['text'])

    def test_cancelled_batch_does_not_retire_a_live_card(self):
        before = self.seed()
        pending = self.request([{'op': 'delete-parameter', 'id': 0}])['preview']
        self.assertTrue(pending['valid'], pending)
        self.assertTrue(self.command('engineering-cancel ' + str(pending['token']))['cancelled'])
        self.assert_archive_can_edit_live_card(before)

    def test_operation_failure_does_not_retire_a_live_card(self):
        before = self.seed()
        pending = self.request([{'op': 'delete-parameter', 'id': 0}, {'op': 'not-a-real-operation'}])['preview']
        self.assertFalse(pending['valid'], pending)
        self.assert_archive_can_edit_live_card(before)

    def test_geometry_revalidation_failure_does_not_retire_a_live_card(self):
        self.seed([card(1, 'Datum coordinate', [field(1, '10')])])
        self.apply_line('datum 1 x param:1:1')
        before = self.command('dump')['text']
        pending = self.request([{'op': 'delete-parameter', 'id': 0}, card(1, 'Fractional coordinate', [field(1, '0.5')])])['preview']
        self.assertFalse(pending['valid'], 'a fractional datum coordinate must fail geometry revalidation: ' + repr(pending))
        self.assert_archive_can_edit_live_card(before)

    def test_confirm_then_undo_does_not_retire_the_restored_card(self):
        before = self.seed()
        self.apply([{'op': 'delete-parameter', 'id': 0}])
        self.assertTrue(self.command('line undo')['ok'])
        self.assert_archive_can_edit_live_card(before)

    def test_readonly_validate_does_not_retire_a_live_card(self):
        before = self.seed()
        scene = self.directory/'readonly-archive.scene'
        scene.write_text(before + self.archive_line(card(0, 'Private scene card', [field(1, '11')])) + '\n'
                         + self.archive_line({'op': 'delete-parameter', 'id': 0}) + '\n', encoding='utf-8')
        revision = self.read()['revision']
        result = self.command('engineering-validate ' + str(scene))
        self.assertTrue(result['ok'], result)
        self.assertEqual(revision, self.read()['revision'], 'read-only validation changed live revision')
        self.assert_archive_can_edit_live_card(before)

    def test_failed_scene_load_does_not_retire_a_live_card(self):
        before = self.seed()
        scene = self.directory/'failed-archive.scene'
        scene.write_text(before + self.archive_line(card(0, 'Private scene card', [field(1, '11')])) + '\n'
                         + self.archive_line({'op': 'delete-parameter', 'id': 0}) + '\nnot-a-scene-command\n', encoding='utf-8')
        self.assertFalse(self.command('loadfile ' + str(scene))['ok'])
        self.assert_archive_can_edit_live_card(before)


if __name__ == '__main__':
    unittest.main()
