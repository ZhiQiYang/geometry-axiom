"""R03 live guide-source regression over the actual native World.

No template/oracle generator is used to compute expected movement. Increasing
the gap from 2 to 4 moves the selected seam by exactly one millimetre towards
the start direction; ordinary guide references and their members must follow.
The same IDs, full history and a new-process cold replay are checked as well.
"""
from copy import deepcopy
import json
import unittest

from test_framing_template import FramingTemplateHarness, POLICY_A
from test_timber_edit import Session


class R03MutationCoverage(FramingTemplateHarness):
    template_version = 1

    def request(self, *args, **kwargs):
        value = super().request(*args, **kwargs)
        if self.template_version == 2:
            value['template'] = {'id': 'flat-ceiling', 'version': 2,
                                 'policyFingerprint': POLICY_A}
        return value

    def test_mark_guides_follow_live_fill_sources_axes_starts_versions_and_cold_replay(self):
        for version in (1, 2):
            for along in ('u', 'v'):
                for start in ('min', 'max'):
                    with self.subTest(version=version, along=along, start=start):
                        self.template_version = version
                        self.surface(*( (2000, 3740) if along == 'u' else (3740, 2000) ))
                        corner = (start + '-min') if along == 'u' else ('min-' + start)
                        pending = self.accepted(along=along, corner=corner, marker='R03_MAIN_CONTINUOUS')
                        mains = [row for row in pending['preview']['members'] if row['kind'] == 'main']
                        self.assertEqual(4, len(mains), 'R03_MAIN_CONTINUOUS')
                        axis = 0 if along == 'u' else 1
                        self.assertTrue(all(row['rect'][axis] == 27 and row['rect'][axis+2] == 1973
                                            and row['length'] == 1946 for row in mains),
                                        'R03_MAIN_CONTINUOUS')
                        self.assertTrue(self.terminal(pending).get('ok'), 'R03_MARK_INITIAL_CONFIRM')
                        before_scene = self.ok('dump')['text']
                        before = self.ok('references')
                        guides = {row['id']: row for row in before['guides']}
                        self.assertEqual(4, len(guides), 'R03_MARK_FOUR_GUIDES')
                        for row in guides.values():
                            self.assertIn('grid:', row['expression'], 'R03_MARK_GUIDE_LIVE_SOURCE')
                        members = {row['id']: row for row in before['timbers']}
                        secondary = {key: row for key, row in members.items()
                                     if 'at-line guide ' in row['definition'].get('anchor', '')}
                        self.assertTrue(secondary, 'R03_MARK_SECONDARY_JUDGES_PRESENT')
                        invocations = self.read()['generatorInvocations']
                        definition = json.loads(bytes.fromhex(next(line.split()[3]
                            for line in before_scene.splitlines() if line.startswith('panel-fill '))))
                        self.assertEqual(2, definition['gap'], 'R03_MARK_INITIAL_GAP')
                        definition = deepcopy(definition)
                        definition['gap'] = 4
                        preview = self.packet('panel-fill-preview', {
                            'schema': 'panel-fill-transaction/1',
                            'expectedRevision': self.ok('panel-fill-read')['revision'],
                            'operations': [{'op': 'put-panel-fill', 'value': definition}]})
                        self.assertTrue(preview.get('ok') and preview['preview']['valid'],
                                        'R03_MARK_GAP_EDIT_VALID: ' + repr(preview))
                        self.assertEqual(before_scene, self.ok('dump')['text'], 'R03_MARK_PREVIEW_ZERO_WRITE')
                        self.ok('panel-fill-confirm ' + str(preview['preview']['token']))
                        after_scene = self.ok('dump')['text']
                        after = self.ok('references')
                        after_guides = {row['id']: row for row in after['guides']}
                        after_members = {row['id']: row for row in after['timbers']}
                        self.assertEqual(set(guides), set(after_guides), 'R03_MARK_GUIDE_IDS')
                        self.assertEqual(set(members), set(after_members), 'R03_MARK_MEMBER_IDS')
                        delta = 1 if start == 'min' else -1
                        for identifier, old in guides.items():
                            self.assertEqual(old['off'] + delta, after_guides[identifier]['off'],
                                             'R03_MARK_GUIDE_LIVE_SOURCE')
                            self.assertEqual(old['expression'], after_guides[identifier]['expression'],
                                             'R03_MARK_REFERENCE_IDENTITY')
                        for identifier, old in secondary.items():
                            self.assertEqual(old['geometry']['centerline'] + delta,
                                             after_members[identifier]['geometry']['centerline'],
                                             'R03_MARK_SECONDARY_FOLLOWS_GUIDE')
                        self.assertEqual(invocations, self.read()['generatorInvocations'],
                                         'R03_MARK_EDIT_NO_GENERATOR')
                        self.ok('line undo')
                        self.assertEqual(before_scene, self.ok('dump')['text'], 'R03_MARK_ONE_HISTORY_UNDO')
                        self.assertEqual(before, self.ok('references'), 'R03_MARK_UNDO_ALL_GEOMETRY')
                        self.ok('line redo')
                        self.assertEqual(after_scene, self.ok('dump')['text'], 'R03_MARK_REDO_SAME_DEFINITIONS')
                        self.assertEqual(after, self.ok('references'), 'R03_MARK_REDO_ALL_GEOMETRY')
                        file = self.directory / 'o467-live-guides.scene'
                        file.write_text(after_scene, encoding='utf-8')
                        cold = Session(self.executable)
                        try:
                            self.assertTrue(cold.command('loadfile ' + str(file)).get('ok'),
                                            'R03_MARK_COLD_REPLAY_VALID')
                            self.assertEqual(after_scene, cold.command('dump')['text'], 'R03_MARK_COLD_DEFINITIONS')
                            self.assertEqual(after, cold.command('references'), 'R03_MARK_COLD_ALL_GEOMETRY')
                            read = self.packet('framing-template-read',
                                {'schema': 'framing-template-read/1', 'boundaryId': 1}, cold)
                            self.assertEqual(0, read['generatorInvocations'], 'R03_MARK_COLD_NO_GENERATOR')
                        finally:
                            cold.stop()


if __name__ == '__main__':
    unittest.main()
