"""R09a/R01 integration: definition imports settle the real process serials.

The source is authored through the native assembly transaction, then exported
deidentified. All assertions drive the fresh registered native bridge; no JS
allocator or manually supplied identity marks participate in the oracle.
"""
import hashlib
import json
import os
from pathlib import Path
import secrets
import tempfile
import unittest

from tests import _bridge
from tests.test_definition_import import face, literal, rule


class IdentityDefinitionImportMerge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.name != 'nt':
            import resource
            soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
            if soft != resource.RLIM_INFINITY and soft < 16 * 1024 * 1024:
                resource.setrlimit(resource.RLIMIT_STACK, (16 * 1024 * 1024, hard))
        cls.binary = _bridge.find_bridge()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='r360-definition-import-')
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.bridge = _bridge.BridgeSession(self.binary, cwd=self.directory)
        self.addCleanup(self.bridge.stop)
        self.counter = 0
        self.ok('reset')
        operations = [
            {'op': 'publish-rule', 'value': rule(1)},
            {'op': 'put-parameter', 'value': {
                'id': 21, 'name': 'source width', 'fields': [
                    {'id': 0, 'name': 'width', 'type': 'dimension', 'input': '31'}]}},
            {'op': 'put-binding', 'value': {
                'id': 1, 'name': 'source binding', 'rule': {'id': 1, 'version': 1},
                'slots': [face({'kind': 'parameter', 'parameterId': 21, 'fieldId': 0}, literal(43)),
                          face(literal(31), literal(43), 2)]}},
        ]
        revision = self.ok('assembly-read')['revision']
        request = self.directory / 'source-transaction.json'
        request.write_text(json.dumps({'schema': 'assembly-transaction/1', 'expectedRevision': revision,
                                       'operations': operations}), encoding='utf-8')
        preview = self.ok('assembly-preview ' + str(request))['preview']
        self.assertTrue(preview['valid'], preview)
        self.ok('assembly-confirm ' + str(preview['token']))
        self.source = self.ok('dump-deidentified')['text']
        self.assertNotIn('requires identity-ledger/1', self.source)
        self.ok('reset')
        # Epochs are fresh for every bridge/test. Reset must not be used to
        # recycle an epoch previously present in a project.
        self.epoch = secrets.token_hex(16)

    def command(self, text):
        return self.bridge.command(text)

    def ok(self, text, marker='R360_DI_NATIVE_SETUP'):
        result = self.command(text)
        self.assertTrue(result.get('ok'), marker + ': ' + str(result))
        return result

    def enable(self):
        self.ok('identity-epoch ' + self.epoch)
        self.ok('line identity-ledger activate')
        self.assertEqual(self.marks(), {})

    def dump(self):
        return self.ok('dump')['text']

    def marks(self):
        ledger = self.ok('identity-read')
        return {(mark['kind'], mark['id'], mark.get('fieldId', 0)): mark['mark']
                for mark in ledger['marks']}

    def preview_import(self):
        directory = self.directory / ('import-' + str(self.counter))
        self.counter += 1
        directory.mkdir()
        raw = self.source.encode('utf-8')
        (directory / 'source.scene').write_bytes(raw)
        (directory / 'request.json').write_text(json.dumps({
            'schema': 'definition-import/1',
            'expectedRevision': self.ok('engineering-read')['revision'],
            'sourceSceneSha256': hashlib.sha256(raw).hexdigest(),
            'roots': {'rules': [], 'bindings': [1]}, 'names': {}}), encoding='utf-8')
        result = self.ok('definition-import-preview ' + str(directory))
        self.assertTrue(result['preview']['valid'], result)
        return result['preview']

    def confirm(self, preview):
        return self.ok('definition-import-confirm ' + str(preview['token']))

    def boundary(self, identifier, marker):
        return self.ok('line boundary %d outline 0,0 4000,0 4000,3000 0,3000' % identifier, marker)

    def test_successful_import_commits_serials_before_the_next_covered_key(self):
        self.enable()
        before = self.dump()
        preview = self.preview_import()
        self.assertEqual(before, self.dump(), 'R360_DI_PREVIEW_DOES_NOT_PUBLISH')
        self.assertEqual(self.marks(), {})
        self.assertTrue(self.confirm(preview)['history_changed'])
        imported = self.marks()
        self.assertEqual(len(imported), 2)
        self.assertEqual(set(imported.values()), {self.epoch + ':1', self.epoch + ':2'})
        self.boundary(88, 'R360_DI_SUCCESS_BURNS_ISSUED_SERIALS')
        after = self.marks()
        self.assertEqual(after[('boundary', 88, 0)], self.epoch + ':3',
                         'R360_DI_NEXT_SERIAL_FOLLOWS_IMPORTED_KEYS')
        self.assertEqual(len(set(after.values())), len(after), 'R360_DI_MARKS_REMAIN_UNIQUE')
        self.assertTrue(all(after[key] == value for key, value in imported.items()))

    def test_undo_of_import_does_not_reuse_its_serials_on_a_new_branch(self):
        self.enable()
        before = self.dump()
        self.confirm(self.preview_import())
        imported = self.marks()
        self.ok('line undo')
        self.assertEqual(before, self.dump(), 'R360_DI_ONE_UNDO_RESTORES_WORLD')
        self.boundary(89, 'R360_DI_BRANCH_BOUNDARY_CREATED')
        mark = self.marks()[('boundary', 89, 0)]
        self.assertNotIn(mark, imported.values(), 'R360_DI_UNDO_MUST_NOT_RECYCLE_IMPORTED_MARKS')
        self.assertEqual(mark, self.epoch + ':3', 'R360_DI_UNDO_PRESERVES_PROCESS_HIGH_WATER')

    def test_wrong_token_cancel_and_stale_import_do_not_advance_serials(self):
        self.enable()
        before = self.dump()
        preview = self.preview_import()
        self.assertFalse(self.command('definition-import-confirm ' + str(preview['token'] + 1))['ok'])
        self.assertTrue(self.ok('definition-import-cancel ' + str(preview['token']))['cancelled'])
        self.assertEqual(before, self.dump())
        stale = self.preview_import()
        self.boundary(90, 'R360_DI_FIRST_SUCCESS_AFTER_CANCEL')
        self.assertEqual(self.marks()[('boundary', 90, 0)], self.epoch + ':1',
                         'R360_DI_CANCEL_MUST_NOT_BURN_SERIALS')
        current = self.dump()
        self.assertFalse(self.command('definition-import-confirm ' + str(stale['token']))['ok'])
        self.assertEqual(current, self.dump(), 'R360_DI_STALE_MUST_NOT_PUBLISH')
        self.boundary(91, 'R360_DI_SUCCESS_AFTER_STALE')
        self.assertEqual(self.marks()[('boundary', 91, 0)], self.epoch + ':2',
                         'R360_DI_STALE_MUST_NOT_BURN_SERIALS')

    def test_failed_settlement_without_epoch_keeps_world_and_counter_unchanged(self):
        self.enable()
        scene = self.directory / 'active-empty.scene'
        scene.write_text(self.dump(), encoding='utf-8')
        self.ok('loadfile ' + str(scene))
        self.assertTrue(self.ok('identity-read')['active'])
        before = self.dump()
        preview = self.preview_import()
        rejected = self.command('definition-import-confirm ' + str(preview['token']))
        self.assertFalse(rejected['ok'], 'R360_DI_MISSING_EPOCH_REJECTS')
        self.assertEqual(before, self.dump(), 'R360_DI_FAILED_SETTLEMENT_IS_ATOMIC')
        # A loaded World clears the epoch; use a different cryptographic value.
        new_epoch = secrets.token_hex(16)
        self.ok('identity-epoch ' + new_epoch)
        self.boundary(92, 'R360_DI_SUCCESS_AFTER_FAILED_SETTLEMENT')
        self.assertEqual(self.marks()[('boundary', 92, 0)], new_epoch + ':1',
                         'R360_DI_FAILED_SETTLEMENT_MUST_NOT_BURN_SERIALS')

    def test_inactive_import_assigns_no_marks_until_explicit_activation(self):
        self.confirm(self.preview_import())
        self.assertFalse(self.ok('identity-read')['active'])
        self.assertEqual(self.marks(), {}, 'R360_DI_INACTIVE_IMPORT_HAS_NO_MARKS')
        self.ok('identity-epoch ' + self.epoch)
        self.ok('line identity-ledger activate')
        self.assertEqual(set(self.marks().values()), {self.epoch + ':1', self.epoch + ':2'})
        self.boundary(93, 'R360_DI_SUCCESS_AFTER_EXPLICIT_ACTIVATION')
        self.assertEqual(self.marks()[('boundary', 93, 0)], self.epoch + ':3')


if __name__ == '__main__':
    unittest.main()
