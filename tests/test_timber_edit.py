"""R11 A: actual native H-116-TIMBER/1 acceptance, with named mutation oracles.

GEOMETRY_TEST_BRIDGE must identify a compiled bridge. No JS/native emulation.
The companion mutation runner compiles each changed include closure separately.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
REACHED = set()


def killer(name):
    REACHED.add(name)
    return 'KILLER[' + name + ']'


class Session:
    def __init__(self, executable):
        if os.name != 'nt':
            import resource
            soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
            resource.setrlimit(resource.RLIMIT_STACK, (max(soft, 16 * 1024 * 1024), hard))
        self.stderr = tempfile.TemporaryFile(mode='w+')
        self.process = subprocess.Popen([str(executable)], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=self.stderr,
                                        text=True, encoding='utf-8')
        self.receipts = []

    def command(self, command):
        self.process.stdin.write(command + '\n')
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        if not line:
            self.stderr.seek(0)
            raise RuntimeError(f'Bridge stopped ({self.process.poll()}): {self.stderr.read()}')
        result = json.loads(line)
        self.receipts.append({'command': command, 'reply': result})
        return result

    def stop(self):
        self.process.stdin.close()
        self.process.wait(timeout=15)
        self.process.stdout.close()
        self.stderr.close()


def direct(value):
    return {'mode': 'direct', 'value': value}


def sourced(source, override=None):
    return {'mode': 'source', 'source': source, 'override': override}


def patch(identifier, **fields):
    return {'op': 'update-timber-fields', 'id': identifier, 'fields': fields}


class TimberEditNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.executable = os.environ.get('GEOMETRY_TEST_BRIDGE')
        if not cls.executable:
            raise unittest.SkipTest('GEOMETRY_TEST_BRIDGE is required for real native execution')
        if not Path(cls.executable).is_file():
            raise RuntimeError('GEOMETRY_TEST_BRIDGE does not exist')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='r11-timber-')
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.session = Session(self.executable)
        self.addCleanup(self.finish)
        self.assertTrue(self.command('reset')['ok'])
        self.line('boundary 1 outline 0,0 4000,0 4000,3000 0,3000')
        self.line('placement 0 on boundary 1 origin 0 0 2500 u +x v +y')
        self.line('timber 0 27 33 role boundary')
        self.line('place 0 on 0 at-face e0 +u +n')

    def finish(self):
        output = os.environ.get('GEOMETRY_TIMBER_RECEIPTS')
        if output:
            path = Path(output)
            path.mkdir(parents=True, exist_ok=True)
            (path / (self._testMethodName + '.json')).write_text(json.dumps({
                'case': self.id(), 'binary_sha256': hashlib.sha256(Path(self.executable).read_bytes()).hexdigest(),
                'receipts': self.session.receipts}, ensure_ascii=False, indent=2), encoding='utf-8')
        self.session.stop()

    def command(self, value):
        return self.session.command(value)

    def line(self, value):
        result = self.command('line ' + value)
        if 'preview' in result:
            self.assertTrue(result['preview']['valid'], result)
            result = self.command('line confirm ' + str(result['preview']['token']))
        self.assertTrue(result['ok'], result)
        return result

    def packet(self, command, value, session=None):
        path = self.directory / 'request.json'
        path.write_bytes(value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False).encode())
        return (session or self.session).command(command + ' ' + str(path))

    def read(self, identifiers=(0,), boundary=1, session=None):
        return self.packet('timber-edit-read', {'schema': 'timber-edit-read/1',
                           'boundaryId': boundary, 'timberIds': list(identifiers)}, session)

    def snapshot(self):
        return self.command('dump')['text'], self.command('engineering-read')['revision']

    def preview(self, operations, revision=None, boundary=1):
        if revision is None:
            revision = str(self.command('engineering-read')['revision'])
        return self.packet('timber-edit-preview', {'schema': 'timber-edit-transaction/1',
                           'expectedRevision': revision, 'boundaryId': boundary, 'operations': operations})

    def confirm(self, result):
        self.assertTrue(result.get('ok'), result)
        self.assertTrue(result['preview']['valid'], result)
        done = self.command('timber-edit-confirm ' + str(result['preview']['token']))
        self.assertTrue(done.get('ok'), done)
        return done

    def batch(self, operations, family='engineering'):
        schema = 'assembly-generation' if family == 'assembly-generation' else family
        result = self.packet(family + '-preview', {'schema': schema + '-transaction/1',
                             'expectedRevision': self.command('engineering-read')['revision'],
                             'operations': operations})
        self.assertTrue(result.get('ok'), result)
        self.assertTrue(result['preview']['valid'], result)
        result = self.command(('assembly' if family == 'assembly-generation' else family) +
                              '-confirm ' + str(result['preview']['token']))
        self.assertTrue(result.get('ok'), result)
        return result

    def create(self, recipe=None, anchor='at-face e2', on=0, **placement):
        return {'op': 'create-from-recipe', 'recipeKey': recipe or self.read()['recipeKey'],
                'placement': dict(on=on, anchor=anchor, selector='', direction='+u', side='+n', **placement)}

    def seed_sources(self):
        card = {'id': 10, 'name': 'section', 'nextFieldId': 14, 'fields': [
            {'id': 5, 'name': 'same one', 'type': 'dimension', 'input': '27'},
            {'id': 13, 'name': 'same two', 'type': 'dimension', 'input': '27'}]}
        material = {'id': 'pine', 'version': 1, 'kind': 'timber', 'name': 'pine', 'A': 27, 'B': 33}
        self.batch([{'op': 'put-parameter', 'value': card},
                    {'op': 'publish-material', 'value': material},
                    {'op': 'publish-material', 'value': dict(material, version=2)},
                    {'op': 'set-source', 'target': {'kind': 'timber', 'id': 0, 'field': 'A'},
                     'source': {'kind': 'parameter', 'parameterId': 10, 'fieldId': 5}},
                    {'op': 'set-source', 'target': {'kind': 'timber', 'id': 0, 'field': 'B'},
                     'source': {'kind': 'material', 'id': 'pine', 'version': 1, 'field': 'B'}},
                    {'op': 'set-override', 'target': {'kind': 'timber', 'id': 0, 'field': 'A'},
                     'value': {'kind': 'literal', 'value': 27}}])
        return sourced({'kind': 'parameter', 'parameterId': 10, 'fieldId': 5}, {'kind': 'literal', 'value': 27}), sourced({'kind': 'material', 'id': 'pine', 'version': 1, 'field': 'B'})

    def seed_atomic_pair(self):
        self.line('spec position1 500')
        self.line('spec position2 550')
        self.line('guide 1 0 v spec:position1')
        self.line('guide 2 0 v spec:position2')
        self.line('timber 90 20 20 role boundary')
        self.line('place 90 on 0 at-face e2 +u +n')
        self.line('timber 1 20 33 role primary')
        self.line('place 1 on 0 at-line guide 1 +v +n')
        self.line('timber 2 80 33 role primary')
        self.line('place 2 on 0 at-line guide 2 +v +n')

    def seed_owned(self):
        # The existing assembly-generation schema requires a positive surface id.
        # Its guard fixture is separate from ordinary timber/placement id-zero.
        self.assertTrue(self.command('reset')['ok'])
        self.line('surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000')
        self.line('timber 89 20 20 role boundary')
        self.line('place 89 on 1 at-face e0 +u +n')
        self.line('spec left 500')
        self.line('spec right 2500')
        self.line('spec middle 1500')
        for number, axis, name in [(1, 'v', 'left'), (2, 'v', 'right'), (3, 'u', 'middle')]:
            self.line(f'guide {number} 1 {axis} spec:{name}')
        self.line('timber 90 20 20 role boundary')
        self.line('place 90 on 1 at-face e2 +u +n')
        rule = {'id': 1, 'version': 1, 'name': 'R11 owner guard',
                'slots': [{'id': 1, 'name': 'main'}, {'id': 2, 'name': 'cross'}],
                'members': [{'id': 1, 'slotId': 1}, {'id': 2, 'slotId': 1}, {'id': 3, 'slotId': 2}],
                'joints': [dict(id=1, kind='end-to-side', scope='left', terminatedMember=3,
                               targetMember=1, end='start', side='+u', dir='u'),
                           dict(id=2, kind='end-to-side', scope='right', terminatedMember=3,
                                targetMember=2, end='finish', side='-u', dir='u')]}
        binding = {'id': 1, 'name': 'R11 owner binding', 'rule': {'id': 1, 'version': 1},
                   'slots': [{'slotId': identifier, 'A': {'kind': 'literal', 'value': 27},
                              'B': {'kind': 'literal', 'value': 33}, 'contactFace': 'A',
                              'orientation': 'A'} for identifier in (1, 2)]}
        self.batch([{'op': 'publish-rule', 'value': rule}, {'op': 'create-binding', 'value': binding}], 'assembly')
        state = self.command('assembly-read')['state']
        source = {'id': 1, 'name': 'owned', 'bindingId': 1,
                  'rule': {'id': 1, 'version': 1, 'fingerprint': state['rules'][0]['fingerprint']},
                  'surfaceId': 1, 'members': []}
        for identifier in (1, 2, 3):
            source['members'].append({'memberId': identifier, 'role': 'primary' if identifier < 3 else 'secondary',
                                      'guideId': identifier, 'dir': '+v' if identifier < 3 else '+u', 'depthSide': '+n',
                                      'ends': {'start': {'kind': 'timber', 'id': 89}, 'finish': {'kind': 'timber', 'id': 90}}
                                      if identifier < 3 else {'start': {'kind': 'member', 'memberId': 1},
                                                              'finish': {'kind': 'member', 'memberId': 2}}})
        self.batch([{'op': 'create-instance', 'value': source,
                     'expectedBindingFingerprint': state['bindings'][0]['fingerprint']}], 'assembly-generation')
        return self.command('assembly-read')['state']['instances'][0]['members'][0]['timberId']

    def test_C01_id_zero_read_private_preview_and_single_publish(self):
        before = self.snapshot()
        read = self.read()
        self.assertTrue(read.get('ok'), read)
        self.assertTrue(read['eligible'])
        self.assertEqual('0', str(read['timbers'][0]['id']))
        self.assertEqual(0, read['timbers'][0]['definition']['placement']['on'])
        self.assertIsInstance(read['revision'], str)
        self.assertRegex(read['contextKey'], r'^[a-f0-9]{64}$')
        self.assertRegex(read['recipeKey'], r'^[a-f0-9]{64}$')
        self.assertEqual(before, self.snapshot())
        next_id = self.command('newid')['timber']
        result = self.preview([self.create(read['recipeKey'])])
        self.assertTrue(result['preview']['valid'], result)
        row = result['preview']['after'][0]
        self.assertNotIn('id', row, killer('private-preview-id'))
        self.assertEqual('new:0', row['handle'])
        self.assertEqual(next_id, self.command('newid')['timber'])
        self.assertEqual(before, self.snapshot())
        done = self.confirm(result)
        self.assertEqual([{'handle': 'new:0', 'kind': 'timber', 'id': next_id}], done['created'])
        self.assertEqual(str(before[1] + 1), done['revision'])
        after = self.snapshot()[0]
        self.line('undo')
        self.assertEqual(before[0], self.snapshot()[0])
        self.line('redo')
        self.assertEqual(after, self.snapshot()[0])

    def test_C01_same_location_overlap_is_rejected_without_consuming_id(self):
        before = self.snapshot()
        next_id = self.command('newid')['timber']
        result = self.preview([self.create(anchor='at-face e0')])
        self.assertFalse(result['preview']['valid'], killer('global-validation'))
        self.assertFalse(self.command('timber-edit-confirm ' + str(result['preview']['token']))['ok'])
        self.assertEqual(before, self.snapshot())
        self.assertEqual(next_id, self.command('newid')['timber'])

    def test_C01_private_handle_covers_dependencies_geometry_and_diagnostics(self):
        next_id = self.command('newid')['timber']
        before_ids = {row['id'] for row in self.command('references')['timbers']}
        before = self.snapshot()
        for anchor in ('at-face e2', 'at-face e0'):
            result = self.preview([self.create(anchor=anchor)])['preview']
            self.assertEqual('new:0', result['after'][0]['handle'])
            self.assertNotIn('id', result['after'][0])
            self.assertNotIn('created', result)
            self.assertEqual([{'op': 'create-from-recipe', 'handle': 'new:0'}], result['changes'])
            self.assertEqual(before_ids, {row['id'] for row in result['dependencies']['timbers']})
            for row in result['after']:
                if row['geometry'] is not None:
                    self.assertNotIn('id', row['geometry'])
                    self.assertNotIn('timberId', row['geometry'])
            for violation in result['violations']:
                self.assertNotEqual(next_id, violation.get('timber'))
                self.assertNotRegex(violation['message'], r'(?:timber[: ]|角材[ （(])' + str(next_id) + r'(?![0-9])', killer('private-diagnostic-handle'))
            self.assertTrue(self.command('timber-edit-cancel ' + str(result['token']))['cancelled'])
            self.assertEqual(before, self.snapshot())
            self.assertEqual(next_id, self.command('newid')['timber'])

    def test_C01_uint32_wrap_skips_every_live_id_before_single_publish(self):
        self.seed_atomic_pair()
        for line in ('spec wrap3 1000', 'spec wrap4 1500', 'guide 3 0 v spec:wrap3',
                     'guide 4 0 v spec:wrap4', 'timber 4294967295 27 33 role primary',
                     'place 4294967295 on 0 at-line guide 3 +v +n'):
            self.line(line)
        before = self.snapshot()
        before_rows = self.read([0, 1, 2, 90, 4294967295])['timbers']
        self.assertEqual(3, self.command('newid')['timber'])
        operation = self.create(self.read([1])['recipeKey'], anchor='at-line guide 4')
        operation['placement']['direction'] = '+v'
        preview = self.preview([operation])
        self.assertTrue(preview['preview']['valid'], killer('private-id-wrap-safe'))
        self.assertEqual(before, self.snapshot())
        self.assertEqual(3, self.command('newid')['timber'])
        done = self.confirm(preview)
        self.assertEqual([{'handle': 'new:0', 'kind': 'timber', 'id': 3}], done['created'])
        after_rows = self.read([0, 1, 2, 90, 4294967295])['timbers']
        self.assertEqual(before_rows, after_rows)
        self.line('undo')
        self.assertEqual(before[0], self.snapshot()[0])

    def test_C02_recipe_preserves_parameter_fields_versions_and_override(self):
        expected_a, expected_b = self.seed_sources()
        before = self.snapshot()
        read = self.read()
        self.assertEqual(expected_a, read['timbers'][0]['definition']['A'], killer('typed-source-read'))
        self.assertEqual(expected_b, read['timbers'][0]['definition']['B'])
        result = self.preview([self.create(read['recipeKey'])])
        self.assertTrue(result['preview']['valid'], result)
        self.assertEqual(expected_a, result['preview']['after'][0]['definition']['A'], killer('recipe-source-preserved'))
        self.assertEqual(expected_b, result['preview']['after'][0]['definition']['B'])
        self.assertEqual(before, self.snapshot())
        new_id = self.confirm(result)['created'][0]['id']
        row = self.read([new_id])['timbers'][0]
        self.assertEqual((expected_a, expected_b), (row['definition']['A'], row['definition']['B']))
        scene = self.directory / 'saved.scene'
        scene.write_text(self.snapshot()[0], encoding='utf-8')
        fresh = Session(self.executable)
        try:
            self.assertTrue(fresh.command('loadfile ' + str(scene))['ok'])
            loaded = self.read([new_id], session=fresh)
            self.assertEqual((expected_a, expected_b), (loaded['timbers'][0]['definition']['A'], loaded['timbers'][0]['definition']['B']), killer('saved-source-roundtrip'))
            self.assertNotEqual(read['contextKey'], loaded['contextKey'])
            rejected = self.packet('timber-edit-preview', {'schema': 'timber-edit-transaction/1',
                'expectedRevision': loaded['revision'], 'boundaryId': 1, 'operations': [self.create(read['recipeKey'])]}, fresh)
            self.assertFalse(rejected['ok'])
        finally:
            fresh.stop()

    def test_C02_equal_effective_different_source_is_a_real_edit(self):
        original_a, original_b = self.seed_sources()
        before = self.snapshot()
        changed_a = sourced({'kind': 'parameter', 'parameterId': 10, 'fieldId': 13}, original_a['override'])
        changed_b = sourced({'kind': 'material', 'id': 'pine', 'version': 2, 'field': 'B'})
        result = self.preview([patch(0, A=changed_a, B=changed_b)])
        self.assertFalse(result['preview']['noOp'], killer('source-identity-is-definition'))
        self.confirm(result)
        row = self.read()['timbers'][0]
        self.assertEqual((changed_a, changed_b), (row['definition']['A'], row['definition']['B']))
        self.assertEqual({'A': 27, 'B': 33}, row['effective'])
        self.line('undo')
        self.assertEqual(before[0], self.snapshot()[0])
        row = self.read()['timbers'][0]
        self.assertEqual((original_a, original_b), (row['definition']['A'], row['definition']['B']))

    def test_C03_empty_and_identical_fields_are_noop_without_history(self):
        original = self.snapshot()[0]
        self.confirm(self.preview([patch(0, A=direct(29))]))
        before = self.snapshot()
        for fields in ({}, {'A': direct(29)}):
            result = self.preview([patch(0, **fields)])
            self.assertTrue(result['preview']['valid'], result)
            self.assertTrue(result['preview']['noOp'], killer('noop-without-token'))
            self.assertIsNone(result['preview']['token'])
            self.assertEqual(before, self.snapshot())
        self.line('undo')
        self.assertEqual(original, self.snapshot()[0])

    def test_C02_explicit_direct_removes_only_the_selected_source_binding(self):
        _expected_a, expected_b = self.seed_sources()
        before = self.snapshot()[0]
        result = self.preview([patch(0, A=direct(27))])
        self.assertEqual(direct(27), result['preview']['after'][0]['definition']['A'], killer('explicit-direct-unbind'))
        self.assertFalse(result['preview']['noOp'])
        self.confirm(result)
        row = self.read()['timbers'][0]
        self.assertEqual(direct(27), row['definition']['A'])
        self.assertEqual(expected_b, row['definition']['B'])
        self.line('undo')
        self.assertEqual(before, self.snapshot()[0])

    def test_C04_all_fields_precede_validation_and_one_undo_restores_all(self):
        self.seed_atomic_pair()
        before = self.snapshot()
        rows = self.read([1, 2])['timbers']
        rejected = self.preview([patch(1, A=direct(50))])
        self.assertFalse(rejected['preview']['valid'])
        result = self.preview([patch(1, A=direct(50)), patch(2, A=direct(50))])
        self.assertTrue(result['preview']['valid'], killer('all-fields-before-evaluation'))
        self.assertEqual(before, self.snapshot())
        self.confirm(result)
        changed = self.read([1, 2])['timbers']
        self.assertEqual([50, 50], [row['effective']['A'] for row in changed])
        self.assertEqual([row['placementOrder'] for row in rows], [row['placementOrder'] for row in changed], killer('in-place-order'))
        self.assertEqual([row['definition']['placement'] for row in rows], [row['definition']['placement'] for row in changed])
        after = self.snapshot()[0]
        self.line('undo')
        self.assertEqual(before[0], self.snapshot()[0])
        self.line('redo')
        self.assertEqual(after, self.snapshot()[0])

    def test_C04_invalid_third_target_rejects_the_entire_candidate(self):
        self.seed_atomic_pair()
        self.line('spec position3 1000')
        self.line('guide 3 0 v spec:position3')
        self.line('timber 3 27 33 role primary')
        self.line('place 3 on 0 at-line guide 3 +v +n')
        before = self.snapshot()
        result = self.preview([patch(1, A=direct(50)), patch(2, A=direct(50)), patch(3, A=direct(10000))])
        self.assertFalse(result['preview']['valid'], killer('invalid-final-is-atomic'))
        self.assertFalse(self.command('timber-edit-confirm ' + str(result['preview']['token']))['ok'])
        self.assertEqual(before, self.snapshot())

    def test_C05_native_owned_and_mixed_selection_are_blocked_whole(self):
        owned_id = self.seed_owned()
        before = self.snapshot()
        read = self.read([89, owned_id])
        self.assertFalse(read['eligible'], killer('native-owner-guard'))
        self.assertIsNotNone(read['timbers'][1]['owner'])
        self.assertIsNone(read['recipeKey'])
        result = self.preview([patch(89, B=direct(34)), patch(owned_id, B=direct(34))])
        self.assertFalse(result['ok'])
        self.assertEqual(before, self.snapshot())
        self.assertFalse(self.read([89, 4294967295])['eligible'])

    def test_C06_revision_and_recipe_expire_even_after_identical_dump_undo_redo(self):
        before = self.snapshot()
        recipe = self.read()['recipeKey']
        pending = self.preview([patch(0, A=direct(29))])
        self.line('spec temporary 1')
        self.line('undo')
        self.assertEqual(before[0], self.snapshot()[0])
        stale = self.preview([self.create(recipe)])
        self.assertFalse(stale['ok'], killer('recipe-revision-bound'))
        self.assertFalse(self.command('timber-edit-confirm ' + str(pending['preview']['token']))['ok'])
        self.assertEqual(before[0], self.snapshot()[0])
        self.assertNotEqual(before[1], self.snapshot()[1])
        self.assertFalse(self.preview([patch(0, A=direct(29))], revision=str(before[1]))['ok'])

    def test_C06_token_families_cancel_and_duplicate_confirm_are_isolated(self):
        before = self.snapshot()
        pending = self.preview([patch(0, A=direct(29))])
        token = pending['preview']['token']
        self.assertFalse(self.command(f'engineering-confirm {token}')['ok'], killer('token-family-confirm'))
        for family in ('engineering', 'assembly', 'section-profile', 'panel-fill'):
            self.assertFalse(self.command(f'{family}-cancel {token}')['cancelled'])
        self.assertFalse(self.command('line cancel-preview')['ok'])
        self.assertEqual(before, self.snapshot())
        self.assertTrue(self.command(f'timber-edit-cancel {token}')['cancelled'])
        self.assertFalse(self.command(f'timber-edit-confirm {token}')['ok'])
        result = self.preview([patch(0, A=direct(29))])
        self.confirm(result)
        after = self.snapshot()
        self.assertFalse(self.command('timber-edit-confirm ' + str(result['preview']['token']))['ok'])
        self.assertEqual(after, self.snapshot())
        ordinary = self.command('line preview spec pending_other 1')['preview']
        self.assertFalse(self.command('timber-edit-cancel ' + str(ordinary['token']))['cancelled'])
        self.assertFalse(self.command('timber-edit-confirm ' + str(ordinary['token']))['ok'])
        self.assertTrue(self.command('line confirm ' + str(ordinary['token']))['ok'])

    def test_C10_omitted_source_and_custom_priority_direction_are_preserved(self):
        expected_a, expected_b = self.seed_sources()
        self.line('spec inside 1000')
        self.line('guide 1 0 v spec:inside')
        self.line('timber 90 20 20 role boundary')
        self.line('place 90 on 0 at-face e2 +u +n')
        self.line('timber 1 27 33 role primary')
        self.line('place 1 on 0 at-line guide 1 +v +n')
        self.confirm(self.preview([patch(1, A=expected_a, B=expected_b)]))
        before = self.read([1])['timbers'][0]
        invalid = self.preview([patch(1, role='custom')])
        self.assertFalse(invalid.get('preview', {}).get('valid', False))
        result = self.preview([patch(1, role='custom', priority=7, direction='-v')])
        self.confirm(result)
        after = self.read([1])['timbers'][0]
        self.assertEqual((expected_a, expected_b), (after['definition']['A'], after['definition']['B']))
        self.assertEqual(before['placementOrder'], after['placementOrder'])
        self.assertEqual(7, after['definition']['priority'])
        self.assertEqual('-v', after['definition']['placement']['direction'])
        self.confirm(self.preview([patch(1, role='primary')]))
        self.assertEqual(2, self.read([1])['timbers'][0]['definition']['priority'])

    def test_C10_priority_is_positive_integer_not_a_dimension(self):
        self.seed_atomic_pair()
        before = self.read([1])['timbers'][0]
        result = self.preview([patch(1, role='custom', priority=100000001)])
        self.assertTrue(result.get('preview', {}).get('valid', False), killer('priority-is-not-dimension'))
        self.confirm(result)
        row = self.read([1])['timbers'][0]
        self.assertEqual(100000001, row['definition']['priority'])
        self.assertEqual(before['placementOrder'], row['placementOrder'])
        self.assertEqual(before['definition']['placement'], row['definition']['placement'])
        self.confirm(self.preview([patch(1, role='primary')]))
        self.assertEqual(2, self.read([1])['timbers'][0]['definition']['priority'])

    def test_C10_full_int64_priority_text_and_recipe_are_exact(self):
        self.seed_atomic_pair()
        self.line('spec exact_priority 1000')
        self.line('guide 3 0 v spec:exact_priority')
        for exact in ('9007199254740993', '9223372036854775807'):
            result = self.preview([patch(1, role='custom', priority=exact)])
            self.assertTrue(result.get('preview', {}).get('valid', False), result)
            self.assertEqual(exact, result['preview']['after'][0]['definition']['priorityText'], killer('exact-priority-text'))
            self.confirm(result)
            self.assertEqual(exact, self.read([1])['timbers'][0]['definition']['priorityText'])
        read = self.read([1])
        operation = self.create(read['recipeKey'], anchor='at-line guide 3')
        operation['placement']['direction'] = '+v'
        result = self.preview([operation])
        self.assertTrue(result['preview']['valid'], result)
        self.assertEqual('9223372036854775807', result['preview']['after'][0]['definition']['priorityText'])
        new_id = self.confirm(result)['created'][0]['id']
        self.assertEqual('9223372036854775807', self.read([new_id])['timbers'][0]['definition']['priorityText'])
        scene = self.directory/'priority.scene'
        scene.write_text(self.snapshot()[0], encoding='utf-8')
        fresh = Session(self.executable)
        try:
            self.assertTrue(fresh.command('loadfile ' + str(scene))['ok'])
            self.assertEqual('9223372036854775807', self.read([new_id], session=fresh)['timbers'][0]['definition']['priorityText'])
        finally:
            fresh.stop()
        before = self.snapshot()
        for invalid in (0, -1, '0', '01', '+1', '1e3', '9223372036854775808', True):
            self.assertFalse(self.preview([patch(1, role='custom', priority=invalid)])['ok'])
            self.assertEqual(before, self.snapshot())

    def test_C12_strict_schema_duplicate_target_controls_and_full_uint64(self):
        before = self.snapshot()
        valid = {'schema': 'timber-edit-read/1', 'boundaryId': 1, 'timberIds': [0]}
        for data in [dict(valid, timberIds=[0, 0]), dict(valid, callerPath='/tmp/ignored'),
                     dict(valid, timberIds=[True]), dict(valid, timberIds=[]), dict(valid, timberIds=[-1]),
                     b'{"schema":"timber-edit-read/1","boundaryId":1,"boundaryId":1,"timberIds":[0]}']:
            self.assertFalse(self.packet('timber-edit-read', data)['ok'])
        self.assertFalse(self.preview([patch(0, surprise=True)])['ok'], killer('strict-fields'))
        self.assertFalse(self.preview([patch(0), patch(0)])['ok'])
        for revision in [before[1], '-1', '01', '1.0', '18446744073709551616']:
            self.assertEqual('TIMBER_SCHEMA', self.preview([patch(0)], revision=revision)['code'])
        self.assertEqual('STALE', self.preview([patch(0)], revision='18446744073709551615')['code'], killer('full-uint64-revision'))
        for anchor in ['at-face e2 through 1', 'at-face e2 +u +n delete timber 0', 'at-face e2' + chr(10) + 'reset']:
            self.assertFalse(self.preview([self.create(anchor=anchor)])['ok'])
        self.assertEqual(before, self.snapshot())

    def test_C12_same_project_face_recipe_and_capacity_are_native_guards(self):
        recipe = self.read()['recipeKey']
        self.line('boundary 2 outline 0,0 4000,0 4000,3000 0,3000')
        self.line('placement 2 on boundary 2 origin 0 0 3000 u +x v +y')
        recipe = self.read()['recipeKey']
        before = self.snapshot()
        self.assertFalse(self.preview([self.create(recipe, on=2)])['ok'], killer('same-face-guard'))
        self.assertFalse(self.preview([self.create(recipe)], boundary=2)['ok'])
        self.assertFalse(self.read([0], boundary=2)['eligible'])
        self.assertFalse(self.preview([patch(i) for i in range(65)])['ok'])
        self.assertEqual(before, self.snapshot())


class TimberEditTransport(unittest.TestCase):
    def test_C12_transport_rejects_paths_duplicates_and_cleans_owned_file(self):
        spec = importlib.util.spec_from_file_location('timber_transport', ROOT/'geometry-web/timber_edit_transport.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        packet = {'schema': 'timber-edit-read/1', 'boundaryId': 1, 'timberIds': [0]}
        paths = []

        def ask(command):
            kind, path = command.split(' ', 1)
            self.assertEqual('timber-edit-read', kind)
            paths.append(Path(path))
            self.assertEqual(packet, json.loads(Path(path).read_text()))
            return b'{"ok":true}'

        self.assertEqual(b'{"ok":true}', module.file_request(json.dumps(packet).encode(), ask, read=True))
        self.assertFalse(paths[0].exists())
        for body in [json.dumps(dict(packet, path='/tmp/external')).encode(), b'{}', b'{}{}',
                     b'{"schema":"timber-edit-read/1","boundaryId":1,"boundaryId":1,"timberIds":[0]}',
                     json.dumps(dict(packet, timberIds=[0, 0])).encode(), b'x' * (module.MAX_BYTES+1)]:
            self.assertFalse(json.loads(module.file_request(body, lambda _c: self.fail('invalid data reached bridge'), read=True))['ok'])


if __name__ == '__main__':
    program = unittest.main(exit=False, verbosity=2)
    receipt = os.environ.get('GEOMETRY_TIMBER_ORACLES')
    if receipt:
        Path(receipt).write_text(json.dumps({'reached': sorted(REACHED), 'tests': program.result.testsRun,
            'failures': len(program.result.failures), 'errors': len(program.result.errors),
            'skipped': len(program.result.skipped)}, indent=2), encoding='utf-8')
    raise SystemExit(not program.result.wasSuccessful())
