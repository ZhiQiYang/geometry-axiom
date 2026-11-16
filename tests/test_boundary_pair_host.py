"""R17 literal host: real native candidates, scope, receipts and cold replay.

No geometry is emulated here. GEOMETRY_TEST_BRIDGE selects the registry-built
binary; named assertions distinguish missing entry from semantic refusals.
"""
from copy import deepcopy
import base64
import importlib.util
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.error import URLError
from urllib.request import Request, urlopen
import uuid

from test_timber_edit import Session

ROOT = Path(__file__).resolve().parents[1]
SURFACE = 'surface 1 origin 0 0 2500 u +x v +y outline 0,0 500,0 500,13 1000,13 1000,1000 0,1000'


def member(edge, a=27, b=20, direction='+u', side='+n'):
    return {'A': a, 'B': b, 'edge': edge, 'direction': direction, 'side': side}


def operation():
    return {'op': 'create', 'on': 1, 'members': [member('e0'), member('e2')]}


class BoundaryPairHostNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.executable = os.environ.get('GEOMETRY_TEST_BRIDGE')
        if not cls.executable:
            raise unittest.SkipTest('GEOMETRY_TEST_BRIDGE is required for actual native execution')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='r17-host-')
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.session = Session(self.executable)
        self.addCleanup(self.finish)
        self.ok('reset')
        self.ok('line ' + SURFACE)

    def finish(self):
        target = os.environ.get('GEOMETRY_BOUNDARY_PAIR_RECEIPTS')
        if target:
            directory = Path(target)
            directory.mkdir(parents=True, exist_ok=True)
            (directory / (self._testMethodName + '.json')).write_text(json.dumps(
                {'case': self.id(), 'receipts': self.session.receipts}, ensure_ascii=False, indent=2), encoding='utf-8')
        self.session.stop()

    def cmd(self, command):
        return self.session.command(command)

    def ok(self, command):
        result = self.cmd(command)
        self.assertTrue(result.get('ok'), result)
        return result

    def packet(self, command, data, session=None):
        path = self.directory / 'request.json'
        path.write_bytes(data if isinstance(data, bytes) else json.dumps(data).encode('utf-8'))
        target = session or self.session
        result = target.command(command + ' ' + str(path))
        target.receipts[-1]['request'] = data.decode('utf-8', errors='replace') if isinstance(data, bytes) else deepcopy(data)
        return result

    def read(self, boundary=1):
        result = self.packet('boundary-pair-read', {'schema': 'boundary-pair-read/1', 'boundaryId': boundary})
        self.assertTrue(result.get('ok'), 'R17_HOST_ENTRY_AVAILABLE: ' + repr(result))
        return result

    def preview(self, op=None, read=None, boundary=1):
        read = read or self.read(boundary)
        return self.packet('boundary-pair-preview', {'schema': 'boundary-pair-transaction/1',
            'boundaryId': boundary, 'contextKey': read['contextKey'], 'expectedRevision': read['revision'],
            'operation': op or operation()})

    def accepted(self, op=None):
        result = self.preview(op)
        self.assertTrue(result.get('ok'), result)
        self.assertTrue(result['preview']['valid'], result)
        self.assertEqual('boundary-pair', result['preview']['type'])
        return result

    def token(self, preview, cancel=False, owner=None, token=None):
        return self.cmd('boundary-pair-' + ('cancel' if cancel else 'confirm') + ' ' +
                        str(preview['preview']['token'] if token is None else token) + ' ' +
                        (preview['ownerKey'] if owner is None else owner))

    def confirm(self, preview):
        result = self.token(preview)
        self.assertTrue(result.get('ok'), result)
        return result

    def snapshot(self):
        return self.ok('dump')['text'], self.ok('engineering-read')['revision']

    def create(self):
        pending = self.accepted()
        self.confirm(pending)
        return self.read()['groups'][0]

    def test_H01_create_is_readonly_until_one_history_commit(self):
        before = self.snapshot()
        next_id = self.ok('newid')['timber']
        read = self.read()
        self.assertEqual([], read['groups'])
        self.assertFalse(read['complete'])
        self.assertEqual(['literal'], read['memberDimensionSources'])
        pending = self.accepted()
        self.assertRegex(pending['ownerKey'], r'^[0-9a-f]{64}$')
        pair = pending['preview']['boundaryPairs'][0]
        self.assertEqual([next_id, next_id + 1], [pair['first'], pair['second']])
        self.assertEqual('create', pending['preview']['kind'])
        self.assertFalse(pending['preview']['noOp'])
        self.assertEqual([[0, 500], [500, 1000]], [m['interval'] for m in pair['after']['members']])
        self.assertEqual([13, 27], pair['after']['contacts'][0]['contact'])
        self.assertEqual(before, self.snapshot(), 'R17_HOST_PREVIEW_ZERO_WRITE')
        self.assertEqual(next_id, self.ok('newid')['timber'])
        result = self.confirm(pending)
        self.assertTrue(result['history_changed'], 'R17_HOST_ONE_PUBLICATION')
        self.assertEqual(str(before[1] + 1), result['revision'])
        after = self.snapshot()[0]
        self.assertFalse(self.token(pending)['ok'])
        self.ok('line undo')
        self.assertEqual(before[0], self.snapshot()[0], 'R17_HOST_ONE_UNDO')
        self.ok('line redo')
        self.assertEqual(after, self.snapshot()[0])

    def test_H02_owner_and_exact_token_guard_preserve_candidate(self):
        pending = self.accepted()
        before = self.snapshot()
        for cancel in (False, True):
            self.assertEqual('TOKEN', self.token(pending, cancel=cancel, owner='0' * 64).get('code'),
                             'R17_HOST_OWNER_TOKEN_ISOLATION')
            self.assertEqual('TOKEN', self.token(pending, cancel=cancel, token=pending['preview']['token'] + 1).get('code'),
                             'R17_HOST_OWNER_TOKEN_ISOLATION')
        self.assertFalse(self.cmd('line confirm ' + str(pending['preview']['token']))['ok'])
        self.assertFalse(self.cmd('line cancel-preview')['ok'])
        self.assertEqual(before, self.snapshot(), 'R17_HOST_FOREIGN_TOKEN_ZERO_WRITE')
        self.confirm(pending)

    def test_H03_cancel_expires_owned_token_without_world_or_identity_write(self):
        before = self.snapshot()
        pending = self.accepted()
        cancelled = self.token(pending, cancel=True)
        self.assertTrue(cancelled['ok'])
        self.assertTrue(cancelled['cancelled'])
        self.assertFalse(cancelled['history_changed'])
        self.assertFalse(self.token(pending)['ok'])
        self.assertEqual(before, self.snapshot(), 'R17_HOST_CANCEL_ZERO_WRITE')
        self.confirm(self.accepted())

    def test_H04_redeclare_same_geometry_new_source_and_reverse_ids(self):
        self.ok('line placement 2 on boundary 1 origin 0 0 2500 u +x v +y')
        group = self.create()
        old = self.snapshot()[0]
        op = {'op': 'redeclare', 'on': 2, 'ids': list(reversed(group['ids'])),
              'members': [member('e2'), member('e0')]}
        pending = self.accepted(op)
        pair = pending['preview']['boundaryPairs'][0]
        self.assertEqual('redeclared', pair['change'])
        self.assertEqual([1, 1], [m['source']['surface'] for m in pair['before']['members']])
        self.assertEqual([2, 2], [m['source']['surface'] for m in pair['after']['members']])
        self.assertEqual(old, self.snapshot()[0])
        self.assertTrue(self.confirm(pending)['history_changed'])
        current = self.read()['groups'][0]
        self.assertEqual(group['ids'], current['ids'])
        self.assertEqual(2, current['on'])
        self.assertEqual([m['order'] for m in group['members']], [m['order'] for m in current['members']])

    def test_H05_group_delete_rejects_live_downstream_then_undo_restores_group(self):
        group = self.create()
        self.ok('line guide 9 1 v timber:%s:A' % group['first'])
        before = self.snapshot()
        rejected = self.preview({'op': 'delete', 'ids': group['ids']})
        self.assertFalse(rejected['ok'])
        self.assertEqual('BOUNDARY_PAIR_INVALID', rejected['code'])
        self.assertEqual(before, self.snapshot(), 'R17_HOST_DELETE_DOES_NOT_DELETE_DOWNSTREAM')
        self.ok('line delete guide 9')
        before = self.snapshot()[0]
        pending = self.accepted({'op': 'delete', 'ids': group['ids']})
        self.assertEqual('removed', pending['preview']['boundaryPairs'][0]['change'])
        self.confirm(pending)
        self.assertEqual([], self.read()['groups'])
        self.ok('line undo')
        self.assertEqual(before, self.snapshot()[0])

    def seed_ordinary(self):
        self.ok('line surface 3 origin 0 0 5000 u +x v +y outline 0,0 1000,0 1000,1000 0,1000')
        self.ok('line timber 0 27 20 role boundary')
        self.ok('line place 0 on 3 at-face e0 +u +n')

    def ordinary_preview(self):
        return self.packet('timber-edit-preview', {'schema': 'timber-edit-transaction/1',
            'boundaryId': 3, 'expectedRevision': str(self.ok('engineering-read')['revision']),
            'operations': [{'op': 'update-timber-fields', 'id': 0, 'fields': {'B': {'mode': 'direct', 'value': 25}}}]})

    def test_H06_foreign_timber_pending_survives_pair_read_preview_confirm_cancel(self):
        self.seed_ordinary()
        foreign = self.ordinary_preview()
        self.assertTrue(foreign['ok'], foreign)
        token = foreign['preview']['token']
        self.assertTrue(foreign['preview']['valid'])
        before = self.snapshot()
        self.read()
        self.assertEqual('PENDING', self.preview()['code'])
        for action in ('confirm', 'cancel'):
            self.assertEqual('TOKEN', self.cmd('boundary-pair-%s %s %s' % (action, token, '0' * 64))['code'])
        self.assertEqual(before, self.snapshot(), 'R17_HOST_FOREIGN_PENDING_PRESERVED')
        self.ok('timber-edit-confirm ' + str(token))

    def test_H07_pair_pending_survives_timber_preview_and_cancel(self):
        self.seed_ordinary()
        pending = self.accepted()
        self.assertEqual('PENDING', self.ordinary_preview()['code'])
        cancelled = self.ok('timber-edit-cancel ' + str(pending['preview']['token']))
        self.assertFalse(cancelled['cancelled'])
        self.confirm(pending)

    def test_H08_stale_preview_and_foreign_context_refused(self):
        read = self.read()
        self.ok('line spec unused 1')
        self.assertEqual('STALE', self.preview(read=read)['code'])
        foreign = dict(self.read(), contextKey='0' * 64)
        self.assertEqual('CONTEXT', self.preview(read=foreign)['code'])
        pending = self.accepted()
        self.ok('line spec unused 2')
        before = self.snapshot()
        rejected = self.token(pending)
        self.assertFalse(rejected['ok'], 'R17_HOST_STALE_NEVER_PUBLISHES')
        self.assertEqual(before, self.snapshot())
        self.assertFalse(self.token(pending)['ok'])
        pending = self.accepted()
        self.ok('line history-begin')
        before = self.snapshot()
        self.assertEqual('HISTORY_GROUP', self.token(pending)['code'])
        self.assertEqual(before, self.snapshot(), 'R17_HOST_CONFIRM_NOT_ABSORBED_IN_OTHER_HISTORY_GROUP')
        self.assertFalse(self.token(pending)['ok'])
        self.ok('line history-end')

    def test_H09_scope_and_literal_only_refusals_do_not_stage_candidate(self):
        self.ok('line surface 3 origin 0 0 5000 u +x v +y outline 0,0 1000,0 1000,1000 0,1000')
        before = self.snapshot()
        outside = operation()
        outside['on'] = 3
        self.assertEqual('BOUNDARY_PAIR_SCOPE', self.preview(outside)['code'])
        for mutation in ('source', 'role', 'priority', 'through', 'client-id'):
            op = operation()
            if mutation == 'source':
                op['members'][0]['A'] = {'kind': 'literal', 'value': 27}
            elif mutation == 'client-id':
                op['ids'] = [123, 456]
            else:
                op['members'][0][mutation] = 'boundary' if mutation == 'role' else 1
            self.assertFalse(self.preview(op)['ok'], mutation)
        op = operation()
        op['members'][1]['edge'] = 'e0'
        self.assertEqual('BOUNDARY_PAIR_INVALID', self.preview(op)['code'])
        self.assertEqual(before, self.snapshot())
        self.confirm(self.accepted())

    def test_H10_downstream_preview_uses_native_intervals_sources_contacts(self):
        group = self.create()
        self.ok('line timber 3 27 20 role boundary')
        self.ok('line place 3 on 1 at-face e4 +u +n')
        self.ok('line guide 9 1 v timber:%s:A' % group['first'])
        self.ok('line timber 4 27 20 role primary')
        self.ok('line place 4 on 1 at-line guide 9 +v +n')
        pending = self.accepted({'op': 'redeclare', 'on': 1, 'ids': group['ids'],
                                 'members': [member('e0', a=30), member('e2')]})
        impacts = {row['id']: row for row in pending['preview']['timberImpacts']}
        row = impacts[4]
        for side, interval, cross, length in [('before', [27, 973], [14, 41], 946),
                                               ('after', [30, 973], [17, 44], 943)]:
            facts = row[side]
            self.assertEqual(interval, facts['interval'], 'R17_HOST_I8A_DOWNSTREAM_INTERVAL')
            self.assertEqual(cross, facts['cross'], 'R17_HOST_I8A_DOWNSTREAM_CROSS')
            self.assertEqual(length, facts['geometry']['length'])
            self.assertEqual('primary', facts['role'])
            self.assertEqual('at-line guide 9', facts['source']['anchor'])
            self.assertEqual({'surface': 1, 'dir': '+v', 'side': '+n',
                              'dimensions': {'A': {'mode': 'direct', 'value': 27},
                                             'B': {'mode': 'direct', 'value': 20}}},
                             {key: facts['source'].get(key) for key in ('surface', 'dir', 'side', 'dimensions')},
                             'R17_HOST_I8A_LITERAL_DEFINITION_SOURCE')
            self.assertEqual({group['first'], 3}, {c['timber'] for c in facts['contacts']})
        self.confirm(pending)

    def test_H11_noop_redeclare_and_identity_marks_are_preserved(self):
        self.ok('identity-epoch ' + secrets.token_hex(16))
        self.ok('line identity-ledger activate')
        before = self.snapshot()
        pending = self.accepted()
        self.assertEqual(before, self.snapshot())
        self.confirm(pending)
        after = self.snapshot()
        group = self.read()['groups'][0]
        identity_lines = [line for line in after[0].splitlines() if line.startswith('identity timber ')]
        self.assertEqual(2, len(identity_lines), 'R17_HOST_TWO_EXISTENCE_MARKS_ONLY')
        pending = self.accepted({'op': 'redeclare', 'on': 1, 'ids': group['ids'], 'members': operation()['members']})
        self.assertTrue(pending['preview']['noOp'])
        impacts = {row['id']: row for row in pending['preview']['timberImpacts']}
        for identifier in group['ids']:
            self.assertEqual('unchanged', impacts[identifier]['change'])
            for side in ('before', 'after'):
                self.assertEqual({'START', 'END'}, {c['end'] for c in impacts[identifier][side]['contacts']},
                                 'R17_HOST_UNCHANGED_MEMBER_ALL_END_CONTACTS')
        self.assertFalse(self.confirm(pending)['history_changed'])
        self.assertEqual(after, self.snapshot(), 'R17_HOST_NOOP_NO_HISTORY_OR_SERIAL')

    def test_H12_allocator_wraps_without_client_ids_or_preview_reservation(self):
        self.ok('line timber 4294967295 27 20 role boundary')
        self.ok('line timber 0 27 20 role boundary')
        pending = self.accepted()
        pair = pending['preview']['boundaryPairs'][0]
        self.assertEqual([1, 2], [pair['first'], pair['second']])
        self.assertEqual(1, self.ok('newid')['timber'])
        self.confirm(pending)

    def test_H13_grouped_members_are_not_falsely_reported_as_ordinary_reuse(self):
        group = self.create()
        response = self.packet('timber-edit-read', {'schema': 'timber-edit-read/1', 'boundaryId': 1,
                                                    'timberIds': [group['first']]})
        self.assertTrue(response['ok'], response)
        self.assertFalse(response['eligible'], 'R17_HOST_REAL_GROUP_ELIGIBILITY')
        self.assertEqual([{'kind': 'boundary-pair', 'first': group['first'], 'second': group['second']}],
                         response['timbers'][0]['groups'])
        self.assertIsNone(response['recipeKey'])

    def test_H14_dump_cold_replay_requires_capability_and_keeps_downstream_order(self):
        group = self.create()
        self.ok('line guide 9 1 v timber:%s:A' % group['first'])
        original = self.snapshot()[0]
        self.assertIn('requires boundary-pair/1\n', original)
        self.assertLess(original.index('boundary-pair end'), original.index('guide 9'))
        cold = Session(self.executable)
        self.addCleanup(cold.stop)
        path = self.directory / 'cold.scene'
        path.write_text(original, encoding='utf-8')
        self.assertTrue(cold.command('loadfile ' + str(path))['ok'])
        self.assertEqual(original, cold.command('dump')['text'], 'R17_HOST_COLD_GROUP_ROUNDTRIP')
        for broken in [original.replace('requires boundary-pair/1\n', ''), original.replace('boundary-pair/1', 'boundary-pair/2')]:
            path.write_text(broken, encoding='utf-8')
            self.assertFalse(cold.command('loadfile ' + str(path))['ok'])
            self.assertEqual(original, cold.command('dump')['text'], 'R17_HOST_CAPABILITY_REFUSAL_ZERO_REPLACE')
        state = self.ok('engineering-read')['state']
        self.assertIn('boundary-pair/1', state['required_capabilities'])
        self.assertNotIn('boundary-pair/1', state['capabilities'])
        self.assertFalse(state['boundary_pair_native']['complete'])
        self.assertIn('host-app-literal-entry', state['boundary_pair_native']['supported'])

    def test_H18_failed_candidate_reports_native_i8a_then_discards_token(self):
        self.ok('line surface 1 origin 0 0 2500 u +x v +y outline 0,0 1000,0 1000,1000 0,1000')
        self.ok('identity-epoch ' + secrets.token_hex(16))
        self.ok('line identity-ledger activate')
        before = self.snapshot()
        result = self.preview()
        self.assertFalse(result['ok'])
        self.assertEqual('BOUNDARY_PAIR_INVALID', result['code'])
        self.assertNotIn('ownerKey', result)
        self.assertNotIn('preview', result)
        self.assertIn('diagnostics', result, 'R17_HOST_I8A_NATIVE_FAILURE_REPORT')
        report = result['diagnostics']
        self.assertEqual('boundary-pair', report['type'])
        self.assertFalse(report['valid'])
        self.assertIsNone(report['token'], 'R17_HOST_INVALID_REPORT_NO_CONFIRMABLE_TOKEN')
        self.assertTrue(report['command'].startswith('boundary-pair begin '))
        self.assertTrue(report['command'].endswith('boundary-pair end'))
        members = report['boundaryPairs'][0]['after']['members']
        self.assertEqual(['boundary', 'boundary'], [m['role'] for m in members])
        self.assertEqual(['e0', 'e2'], [m['source']['edge'] for m in members])
        self.assertEqual([[0, 1000], [0, 1000]], [m['interval'] for m in members])
        self.assertEqual(2, len(report['timberImpacts']))
        self.assertTrue(report['violations'], 'R17_HOST_I8A_NATIVE_FAILURE_VIOLATIONS')
        for violation in report['violations']:
            self.assertTrue(violation['clause'])
            self.assertTrue(violation['expected'])
            self.assertTrue(violation['actual'])
        self.assertTrue(any('P1-A' in v['actual'] for v in report['violations']))
        self.assertEqual(before, self.snapshot(), 'R17_HOST_FAILED_REPORT_WORLD_AND_LEDGER_ZERO_WRITE')
        self.assertFalse(self.cmd('line boundary-pair confirm 1')['ok'])
        self.ok('line boundary-pair begin 100 101')
        self.ok('line boundary-pair cancel')
        self.assertEqual(before, self.snapshot(), 'R17_HOST_FAILURE_SINGLE_JSON_AND_NO_PENDING_INPUT')

    def test_H19_downstream_typed_sources_survive_invalid_geometry_and_equal_value_rebinding(self):
        group = self.create()
        self.ok('line timber 3 27 20 role boundary')
        self.ok('line place 3 on 1 at-face e4 +u +n')
        self.ok('line guide 9 1 v timber:%s:A' % group['first'])
        self.ok('line timber 4 27 20 role primary')
        self.ok('line place 4 on 1 at-line guide 9 +v +n')
        parameter = {'id': 10, 'name': 'same-valued dimensions', 'nextFieldId': 14, 'fields': [
            {'id': 5, 'name': 'first', 'type': 'dimension', 'input': '27'},
            {'id': 13, 'name': 'second', 'type': 'dimension', 'input': '27'}]}
        source_a = {'kind': 'parameter', 'parameterId': 10, 'fieldId': 5}
        source_b = {'kind': 'material', 'id': 'pine', 'version': 1, 'field': 'B'}
        operations = [
            {'op': 'put-parameter', 'value': parameter},
            {'op': 'publish-material', 'value': {'id': 'pine', 'version': 1, 'kind': 'timber',
                                                'name': 'pine', 'A': 27, 'B': 20}},
            {'op': 'set-source', 'target': {'kind': 'timber', 'id': 4, 'field': 'A'}, 'source': source_a},
            {'op': 'set-source', 'target': {'kind': 'timber', 'id': 4, 'field': 'B'}, 'source': source_b},
            {'op': 'set-override', 'target': {'kind': 'timber', 'id': 4, 'field': 'B'},
             'value': {'kind': 'literal', 'value': 20}},
        ]
        seed = self.packet('engineering-preview', {'schema': 'engineering-transaction/1',
            'expectedRevision': self.ok('engineering-read')['revision'], 'operations': operations})
        self.assertTrue(seed.get('ok') and seed['preview']['valid'], seed)
        self.ok('engineering-confirm ' + str(seed['preview']['token']))
        before = self.snapshot()
        expected_dimensions = {'A': {'mode': 'source', 'source': source_a, 'override': None},
                               'B': {'mode': 'source', 'source': source_b,
                                     'override': {'kind': 'literal', 'value': 20}}}
        pending = self.accepted({'op': 'redeclare', 'on': 1, 'ids': group['ids'],
                                 'members': [member('e0', a=30), member('e2')]})
        row = next(item for item in pending['preview']['timberImpacts'] if item['id'] == 4)
        for side in ('before', 'after'):
            self.assertEqual(expected_dimensions, row[side]['source'].get('dimensions'),
                             'R17_HOST_I8A_TYPED_DIMENSION_SOURCES')
            self.assertEqual((1, '+v', '+n'), tuple(row[side]['source'].get(key)
                                                  for key in ('surface', 'dir', 'side')))
        self.assertTrue(self.token(pending, cancel=True)['ok'])
        self.assertEqual(before, self.snapshot())

        # The native engineering route already treats a same-value source rebind
        # as a definition edit. Its common I8a report must retain that distinction.
        rebind = {'op': 'set-source', 'target': {'kind': 'timber', 'id': 4, 'field': 'A'},
                  'source': dict(source_a, fieldId=13)}
        encoded = base64.b64encode(json.dumps(rebind).encode('utf-8')).decode('ascii')
        changed = self.ok('line preview engineering archive ' + encoded)['preview']
        self.assertTrue(changed['valid'], changed)
        impacts = {item['id']: item for item in changed['timberImpacts']}
        self.assertIn(4, impacts, 'R17_HOST_I8A_EQUAL_VALUE_SOURCE_REBIND_LISTED')
        row = impacts[4]
        self.assertEqual('changed', row['change'])
        self.assertEqual(row['before']['geometry'], row['after']['geometry'])
        self.assertEqual(expected_dimensions, row['before']['source']['dimensions'])
        rebound = deepcopy(expected_dimensions)
        rebound['A']['source']['fieldId'] = 13
        self.assertEqual(rebound, row['after']['source']['dimensions'])
        self.ok('line cancel-preview')
        self.assertEqual(before, self.snapshot())

        failed = self.ok('line preview guide 9 1 v 2000')['preview']
        self.assertFalse(failed['valid'])
        row = next(item for item in failed['timberImpacts'] if item['id'] == 4)
        self.assertIsNone(row['after']['geometry'], 'R17_HOST_I8A_INVALID_GEOMETRY_FIXTURE')
        self.assertEqual({'anchor': 'at-line guide 9', 'selector': '', 'priority': 2,
                          'surface': 1, 'dir': '+v', 'side': '+n', 'dimensions': expected_dimensions},
                         row['after']['source'], 'R17_HOST_I8A_INVALID_GEOMETRY_KEEP_RAW_SOURCE')
        self.assertTrue(failed['violations'])
        self.ok('line cancel-preview')
        self.assertEqual(before, self.snapshot(), 'R17_HOST_I8A_SOURCE_REPORT_ZERO_WRITE')


class BoundaryPairHostTransport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('boundary_pair_transport', ROOT/'geometry-web/boundary_pair_transport.py')
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def test_H15_transport_owns_files_and_preserves_exact_request(self):
        packet = {'schema': 'boundary-pair-read/1', 'boundaryId': 1}
        paths = []
        def ask(command):
            kind, path = command.split(' ', 1)
            self.assertEqual('boundary-pair-read', kind)
            paths.append(Path(path))
            self.assertEqual(packet, json.loads(Path(path).read_bytes()))
            return b'{"ok":true}'
        self.assertEqual(b'{"ok":true}', self.module.request(json.dumps(packet).encode(), ask, mode='read'))
        self.assertFalse(paths[0].exists())
        for body in [json.dumps(dict(packet, path='/tmp/other')).encode(), b'{}{}',
                     b'{"schema":"boundary-pair-read/1","boundaryId":1,"boundaryId":1}',
                     json.dumps(dict(packet, boundaryId=True)).encode(), b'x'*(self.module.MAX_BYTES+1)]:
            result = self.module.request(body, lambda _: self.fail('invalid request reached native'), mode='read')
            self.assertFalse(json.loads(result)['ok'])

    def test_H16_transport_checks_schema_and_maps_owned_token_without_paths(self):
        calls = []
        token = {'schema': 'boundary-pair-token/1', 'token': 7, 'ownerKey': 'a' * 64}
        for mode in ('confirm', 'cancel'):
            self.module.request(json.dumps(token).encode(), lambda cmd: calls.append(cmd) or b'{"ok":true}', mode=mode)
            self.assertEqual('boundary-pair-%s 7 %s' % (mode, 'a' * 64), calls[-1])
        packet = {'schema': 'boundary-pair-transaction/1', 'boundaryId': 1,
                  'contextKey': 'a' * 64, 'expectedRevision': '7', 'operation': operation()}
        bad = []
        for key, value in [('contextKey', 'x'*64), ('expectedRevision', 7), ('expectedRevision', '01')]:
            bad.append(dict(packet, **{key: value}))
        for key, value in [('A', {'kind': 'literal', 'value': 27}), ('edge', 'e0\nreset'), ('role', 'boundary')]:
            altered = deepcopy(packet)
            altered['operation']['members'][0][key] = value
            bad.append(altered)
        for item in bad:
            result = self.module.request(json.dumps(item).encode(), lambda _: self.fail('invalid request reached native'), mode='preview')
            self.assertFalse(json.loads(result)['ok'])


class BoundaryPairHostHTTP(unittest.TestCase):
    def test_H17_real_host_receipt_recovers_confirm_without_second_history(self):
        executable = os.environ.get('GEOMETRY_TEST_BRIDGE')
        if not executable:
            self.skipTest('GEOMETRY_TEST_BRIDGE is required for real host execution')
        if os.name != 'nt':
            import resource
            soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
            resource.setrlimit(resource.RLIMIT_STACK, (max(soft, 16 * 1024 * 1024), hard))
        with tempfile.TemporaryDirectory(prefix='r17-http-') as directory:
            with socket.socket() as reserved:
                reserved.bind(('127.0.0.1', 0))
                port = reserved.getsockname()[1]
            env = dict(os.environ, GEOMETRY_BRIDGE_EXECUTABLE=executable,
                       GEOMETRY_FEEDBACK_DIR=str(Path(directory)/'feedback'))
            with open(Path(directory)/'serve.log', 'wb') as log:
                process = subprocess.Popen([sys.executable, str(ROOT/'geometry-web/serve.py'), str(port)],
                                           env=env, stdout=log, stderr=log)
                http_receipts = []
                try:
                    base = 'http://127.0.0.1:%d' % port
                    deadline = time.monotonic() + 15
                    while True:
                        try:
                            with urlopen(base + '/runtime', timeout=1) as response:
                                runtime = json.load(response)
                            break
                        except (URLError, OSError):
                            if process.poll() is not None or time.monotonic() > deadline:
                                self.fail('host did not start: ' + (Path(directory)/'serve.log').read_text())
                            time.sleep(.05)
                    self.assertTrue(runtime['fresh'])
                    def post(route, data, headers=None):
                        request = Request(base + route, json.dumps(data).encode(),
                                          {'Content-Type': 'application/json', **(headers or {})})
                        with urlopen(request, timeout=15) as response:
                            result = json.load(response)
                        http_receipts.append({'route': route, 'request': data, 'headers': headers or {}, 'reply': result})
                        return result
                    def command(text, **fields):
                        return post('/api', dict(cmd=text, **fields))
                    reset = command('reset')
                    self.assertTrue(reset['ok'], reset)
                    seeded = command('line ' + SURFACE)
                    self.assertTrue(seeded['ok'], seeded)
                    before = command('dump')['text']
                    read = post('/boundary-pair/read', {'schema': 'boundary-pair-read/1', 'boundaryId': 1})
                    self.assertTrue(read['ok'], 'R17_HOST_HTTP_ENTRY: ' + repr(read))
                    body = {'schema': 'boundary-pair-transaction/1', 'boundaryId': 1,
                            'contextKey': read['contextKey'], 'expectedRevision': read['revision'], 'operation': operation()}
                    sealed_id = str(uuid.uuid4())
                    early = post('/api', {'receipt': sealed_id, 'session': runtime['session']})
                    self.assertFalse(early['result']['ok'])
                    sealed_headers = {'X-Geometry-Request-Id': sealed_id, 'X-Geometry-Session': runtime['session']}
                    self.assertFalse(post('/boundary-pair/preview', body, sealed_headers)['ok'])
                    self.assertEqual(before, command('dump')['text'], 'R17_HOST_EARLY_PREVIEW_ZERO_WRITE')
                    preview_id = str(uuid.uuid4())
                    headers = {'X-Geometry-Request-Id': preview_id, 'X-Geometry-Session': runtime['session']}
                    pending = post('/boundary-pair/preview', body, headers)
                    self.assertTrue(pending['ok'], pending)
                    preview_receipt = post('/api', {'receipt': preview_id, 'session': runtime['session']})
                    self.assertEqual(pending, preview_receipt['result'], 'R17_HOST_PREVIEW_RECEIPT_SAME_OWNER_TOKEN')
                    self.assertEqual(pending, post('/boundary-pair/preview', body, headers))
                    changed = deepcopy(body)
                    changed['operation']['members'][0]['A'] = 30
                    self.assertFalse(post('/boundary-pair/preview', changed, headers)['ok'],
                                     'R17_HOST_PREVIEW_ID_BINDS_EXACT_BODY')
                    request_id = str(uuid.uuid4())
                    text = 'boundary-pair-confirm %s %s' % (pending['preview']['token'], pending['ownerKey'])
                    first = command(text, requestId=request_id, session=runtime['session'])
                    self.assertTrue(first['ok'], first)
                    self.assertTrue(first['history_changed'])
                    recovered = post('/api', {'receipt': request_id, 'session': runtime['session']})
                    self.assertEqual(first, recovered['result'], 'R17_HOST_RECEIPT_EXACT_RESULT')
                    self.assertEqual(first, command(text, requestId=request_id, session=runtime['session']))
                    after = command('dump')['text']
                    self.assertTrue(command('line undo')['ok'])
                    self.assertEqual(before, command('dump')['text'], 'R17_HOST_RECEIPT_ONE_HISTORY')
                    self.assertTrue(command('line redo')['ok'])
                    self.assertEqual(after, command('dump')['text'])
                finally:
                    process.terminate()
                    process.wait(timeout=10)
                    target = os.environ.get('GEOMETRY_BOUNDARY_PAIR_RECEIPTS')
                    if target:
                        output = Path(target)
                        output.mkdir(parents=True, exist_ok=True)
                        (output / (self._testMethodName + '.json')).write_text(json.dumps(
                            {'case': self.id(), 'receipts': http_receipts}, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    unittest.main(verbosity=2)
