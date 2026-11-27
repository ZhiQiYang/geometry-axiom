"""R03R: actual native R-butt identity, geometry and sealed transaction proof.

Only this new identity enables the bounded policy. The old v1/v2 contracts are
not relaxed. All bridge replies and shutdowns have deadlines; an execution
error or timeout is not an assertion kill in the companion mutation proof.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

import binaries
from test_framing_template import FramingTemplateHarness, PARAMETERS, POLICY

ROOT = Path(__file__).resolve().parents[1]
RBUTT_POLICY = '2e4d5dc2507d00558dfd5a02389391101210c999bed8265bbee0a2656e2b9de7'
POLICY_A = '3641dec4060cfcf062e2f1d55f341ecb5ae5023da4a4d8a3aba2c3c4110b6d58'
TEMPLATE = {'id': 'flat-ceiling-rbutt', 'version': 1,
            'policyFingerprint': RBUTT_POLICY}
OLD_TWO = {'id': 'flat-ceiling', 'version': 2, 'policyFingerprint': POLICY_A}
CORNERS = ('min-min', 'max-min', 'min-max', 'max-max')


def retreat_oracle():
    """Independent test-only source; no product header or generated golden."""
    path = ROOT / 'tests/diagnostics/r03_retreat_oracle.py'
    spec = importlib.util.spec_from_file_location('r03r_test_only_oracle', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BoundedSession:
    """Real native process with a per-reply deadline and bounded teardown."""
    REPLY_SECONDS = 15
    STOP_SECONDS = 2

    def __init__(self, executable):
        if os.name != 'nt':
            import resource
            soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
            wanted = 16 * 1024 * 1024
            if soft != resource.RLIM_INFINITY and soft < wanted:
                resource.setrlimit(resource.RLIMIT_STACK,
                                   (wanted if hard == resource.RLIM_INFINITY else min(wanted, hard), hard))
        self.stderr = tempfile.TemporaryFile(mode='w+b')
        self.process = subprocess.Popen([str(executable)], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=self.stderr,
                                        bufsize=0)
        self.receipts = []
        self.replies = queue.Queue()
        self.closed = False
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        pending = b''
        try:
            while True:
                chunk = os.read(self.process.stdout.fileno(), 65536)
                if not chunk:
                    self.replies.put(('eof', pending))
                    return
                pending += chunk
                while b'\n' in pending:
                    line, pending = pending.split(b'\n', 1)
                    self.replies.put(('line', line))
        except (OSError, ValueError) as error:
            self.replies.put(('error', str(error).encode()))

    def command(self, command):
        if self.closed:
            raise RuntimeError('R03R_BRIDGE_CLOSED')
        self.process.stdin.write((command + '\n').encode('utf-8'))
        self.process.stdin.flush()
        try:
            kind, data = self.replies.get(timeout=self.REPLY_SECONDS)
        except queue.Empty as error:
            self.stop()
            raise RuntimeError('R03R_BRIDGE_REPLY_TIMEOUT: ' + command) from error
        if kind != 'line':
            self.stderr.seek(0)
            diagnostic = self.stderr.read(1024 * 1024).decode('utf-8', errors='replace')
            raise RuntimeError('R03R_BRIDGE_EXECUTION_ERROR: ' + kind + ': ' +
                               data.decode('utf-8', errors='replace') + ': ' + diagnostic)
        result = json.loads(data.decode('utf-8'))
        self.receipts.append({'command': command, 'reply': result})
        return result

    def stop(self):
        if self.closed:
            return
        self.closed = True
        try:
            self.process.stdin.close()
        except (BrokenPipeError, OSError):
            pass
        try:
            self.process.wait(timeout=self.STOP_SECONDS)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                self.process.wait(timeout=self.STOP_SECONDS)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=self.STOP_SECONDS)
        self.reader.join(timeout=self.STOP_SECONDS)
        self.process.stdout.close()
        self.stderr.close()


class FramingTemplateRbutt(FramingTemplateHarness):
    """Inherit helpers only: FramingTemplateHarness has no test methods."""

    @classmethod
    def setUpClass(cls):
        cls.executable = os.environ.get('GEOMETRY_TEST_BRIDGE')
        if not cls.executable:
            raise RuntimeError('GEOMETRY_TEST_BRIDGE is required; this proof does not skip native execution')
        if not Path(cls.executable).is_file():
            raise RuntimeError('GEOMETRY_TEST_BRIDGE does not name an existing executable')
        cls.executable = binaries.require_fresh('bridge', cls.executable)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='r03r-native-')
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.session = BoundedSession(self.executable)
        self.addCleanup(self.finish)
        self.active_parameters = deepcopy(PARAMETERS)
        self.active_threshold = '8'
        self.surface(3709, 2000)

    def seed_sources(self, threshold=None):
        p = self.active_parameters
        revision = self.ok('engineering-read')['revision']
        operations = [
            {'op': 'publish-material', 'value': {
                'id': 'r03-board', 'version': 1, 'kind': 'panel', 'name': '明選試驗板材',
                'width': p['panelWidth'], 'length': p['panelLength'], 'thickness': '6'}},
            {'op': 'put-parameter', 'value': {'id': 90, 'name': '承接', 'fields': [
                {'id': 1, 'name': 'X', 'type': 'dimension',
                 'input': self.active_threshold if threshold is None else threshold}]}}]
        pending = self.packet('engineering-preview', {
            'schema': 'engineering-transaction/1', 'expectedRevision': revision,
            'operations': operations})
        self.assertTrue(pending.get('ok') and pending.get('preview', {}).get('valid'), pending)
        self.ok('engineering-confirm ' + str(pending['preview']['token']))

    def read(self):
        result = self.packet('framing-template-read', {
            'schema': 'framing-template-read/2', 'boundaryId': 1,
            'template': deepcopy(TEMPLATE)})
        self.assertTrue(result.get('ok'), 'R03R_NATIVE_ENTRY_AVAILABLE: ' + repr(result))
        return result

    def request(self, **kwargs):
        value = super().request(**kwargs)
        value['template'] = deepcopy(TEMPLATE)
        return value

    @staticmethod
    def case(A=3709, B=2000, *, corner='min-min', along='v', origin=(0, 0),
             gap=2, threshold=(8, 1), parameters=None):
        width, height = (A, B) if along == 'v' else (B, A)
        return {'bounds': [origin[0], origin[1], origin[0] + width, origin[1] + height],
                'parameters': dict(parameters or PARAMETERS, gap=gap),
                'layout': {'corner': corner, 'lengthAlong': along},
                'seam_retreat': 'none', 'r_butt': True,
                'threshold': {'num': threshold[0], 'den': threshold[1]}}

    def configure(self, case):
        self.active_parameters = deepcopy(case['parameters'])
        x = case['threshold']
        self.active_threshold = str(x['num']) if x['den'] == 1 else f"{x['num']}/{x['den']}"
        x0, y0, x1, y1 = case['bounds']
        self.surface(x1 - x0, y1 - y0, x0, y0)

    def request_case(self, case):
        return self.request(corner=case['layout']['corner'], along=case['layout']['lengthAlong'],
                            parameters=case['parameters'])

    def assert_geometry(self, rows, case):
        p = case['parameters']
        for row in rows:
            geometry = row['geometry']
            role = ('boundary' if row['kind'] == 'boundary' else
                    'secondary' if row['kind'].startswith('secondary:') else 'primary')
            self.assertEqual(role, row['role'], 'R03R_NATIVE_ROLE')
            self.assertEqual((p['timberWidth'], p['timberDepth'], '+n'),
                             (geometry['A'], geometry['B'], geometry['side']),
                             'R03R_NATIVE_SECTION')
            self.assertEqual(row['length'], geometry['length'], 'R03R_NATIVE_LENGTH')
            self.assertEqual([0, 0, 1], geometry['axes'][2], 'R03R_NATIVE_DEPTH_AXIS')
            vertices = [[geometry['origin'][d] + i * geometry['length'] * geometry['axes'][0][d]
                         + j * p['timberWidth'] * geometry['axes'][1][d]
                         + k * p['timberDepth'] * geometry['axes'][2][d]
                         for d in range(3)]
                        for i in (0, 1) for j in (0, 1) for k in (0, 1)]
            bounds = [min(v[d] for v in vertices) for d in range(3)] + [max(v[d] for v in vertices) for d in range(3)]
            self.assertEqual([row['rect'][0], row['rect'][1], 2506,
                              row['rect'][2], row['rect'][3], 2506 + p['timberDepth']],
                             bounds, 'R03R_NATIVE_EIGHT_VERTICES')

    def assert_panels(self, panel_layout, expected, case):
        """Check every physical fragment, original key and uncut source body."""
        wanted = {(row['i'], row['j']): row['rect'] for row in expected['panels']}
        tiles = panel_layout['tiles']
        self.assertEqual(len(wanted), len(tiles), 'R03R_EVERY_PANEL')
        self.assertEqual(len(wanted), panel_layout['tileCount'], 'R03R_EVERY_PANEL')
        self.assertEqual(len(wanted), panel_layout['fragmentCount'], 'R03R_EVERY_PANEL')
        self.assertEqual(6, panel_layout['thickness'], 'R03R_PANEL_FIXED_MATERIAL')
        self.assertEqual(set(wanted), {(tile['i'], tile['j']) for tile in tiles}, 'R03R_PANEL_SIGNED_KEYS')
        b = 'uv'.index(case['layout']['lengthAlong'])
        p = case['parameters']
        sizes = [p['panelWidth'], p['panelWidth']]
        sizes[b] = p['panelLength']
        whole_count = 0
        for tile in tiles:
            indices = (tile['i'], tile['j'])
            rect = wanted[indices]
            body_low = [expected['origin'][axis] + indices[axis] * (sizes[axis] + p['gap'])
                        for axis in (0, 1)]
            self.assertEqual(body_low + [body_low[0] + sizes[0], body_low[1] + sizes[1]],
                             tile['body'], 'R03R_PANEL_BODY_STAYS_PERIODIC')
            self.assertEqual([tile['i'], tile['j']], tile['key'][1:], 'R03R_PANEL_SIGNED_KEYS')
            self.assertEqual(1, len(tile['fragments']), 'R03R_EVERY_PANEL_FRAGMENT')
            fragment = tile['fragments'][0]
            self.assertEqual([], fragment['holes'], 'R03R_EVERY_PANEL_FRAGMENT')
            self.assertEqual(4, len(fragment['outer']), 'R03R_EVERY_PANEL_FRAGMENT')
            corners = {(rect[0], rect[1]), (rect[2], rect[1]),
                       (rect[2], rect[3]), (rect[0], rect[3])}
            self.assertEqual(corners, {tuple(point) for point in fragment['outer']},
                             'R03R_EVERY_PANEL_FRAGMENT')
            area = (rect[2] - rect[0]) * (rect[3] - rect[1])
            self.assertEqual(area, fragment['area'], 'R03R_EVERY_PANEL_FRAGMENT')
            whole = area == sizes[0] * sizes[1]
            self.assertEqual(whole, tile['whole'], 'R03R_PANEL_CUT_CLASSIFICATION')
            whole_count += whole
        self.assertEqual(whole_count, panel_layout['wholeCount'], 'R03R_PANEL_CUT_CLASSIFICATION')
        self.assertEqual(len(wanted) - whole_count, panel_layout['cutCount'],
                         'R03R_PANEL_CUT_CLASSIFICATION')

    def assert_case(self, case, *, arrange=True, marker='R03R_EVERY_MEMBER'):
        if arrange:
            self.configure(case)
        oracle = retreat_oracle()
        expected = oracle.build(case)
        self.assertEqual([], oracle.check(case, expected), 'R03R_INDEPENDENT_ORACLE_PRECONDITION')
        pending = self.packet('framing-template-preview', self.request_case(case))
        self.assertTrue(pending.get('ok') and pending.get('preview', {}).get('valid'),
                        marker + ': ' + repr(pending))
        actual = pending['preview']
        self.assertEqual(TEMPLATE, actual.get('template'), 'R03R_PREVIEW_SELECTED_IDENTITY')
        self.assertRegex(actual.get('definitionFingerprint', ''), r'^[a-f0-9]{64}$')
        wanted_members = [(row['kind'], row['rect'], row['length']) for row in expected['members']]
        self.assertEqual(wanted_members, [(row['kind'], row['rect'], row['length']) for row in actual['members']],
                         marker)
        self.assertEqual(expected['seams'], actual['seams'], 'R03R_SEAMS_DO_NOT_MOVE')
        self.assertEqual(expected['marks'], actual['marks'], 'R03R_FIXED_JIG_UNCHANGED')
        self.assert_geometry(actual['members'], case)
        self.assert_panels(actual['panelLayout'], expected, case)
        axis = 'u' if case['layout']['lengthAlong'] == 'v' else 'v'
        sources = {(row['axis'], row['k']): row['center'] for row in expected['seam_rows']}
        wanted_shifts = [(axis, row['seam_key'], sources[(axis, row['seam_key'])], row['shift'])
                         for row in expected['members'] if row['kind'] == 'main' and row['shift']]
        shifts = actual['rbuttShifts']
        for row in shifts:
            self.assertEqual({'axis', 'k', 'seamCenter', 'shift', 'guideId'}, set(row),
                             'R03R_SHIFT_SOURCE_RECORD')
            self.assertIs(type(row['guideId']), int, 'R03R_SHIFT_SOURCE_RECORD')
            self.assertTrue(0 <= row['guideId'] <= 4294967295, 'R03R_SHIFT_SOURCE_RECORD')
            self.assertNotEqual(0, row['shift'], 'R03R_SHIFT_SOURCE_RECORD')
        self.assertEqual(len(shifts), len({row['guideId'] for row in shifts}), 'R03R_UNIQUE_SHIFT_GUIDES')
        self.assertEqual(wanted_shifts,
                         [(row['axis'], int(row['k']), row['seamCenter'], row['shift']) for row in shifts],
                         'R03R_SHIFT_SOURCE_RECORD')
        self.assertTrue(actual['supportComplete'], 'R03R_COMPLETE_NATIVE_SUPPORT')
        self.assertTrue(actual['support'], 'R03R_COMPLETE_NATIVE_SUPPORT')
        num, den = case['threshold']['num'], case['threshold']['den']
        self.assertTrue(all(row['supported'] and min(row['left'], row['right']) * den >= num
                            for row in actual['support']), 'R03R_EXACT_R43_EACH_SIDE')
        self.session.receipts[-1]['oracle_input'] = deepcopy(case)
        self.session.receipts[-1]['oracle_expected'] = expected
        return pending

    def test_R01_native_entry_available(self):
        before = self.snapshot()
        read = self.read()
        self.assertEqual('framing-template-read-result/2', read.get('schema'),
                         'R03R_NATIVE_ENTRY_AVAILABLE')
        self.assertEqual(TEMPLATE, {key: read['generator'][key] for key in TEMPLATE},
                         'R03R_NATIVE_ENTRY_AVAILABLE')
        self.assertEqual(PARAMETERS, read['generator']['defaults'])
        self.assertEqual(before, self.snapshot(), 'R03R_READ_ZERO_WRITE')

    def test_R02_four_corners_both_axes_every_member_and_panel(self):
        for along in ('u', 'v'):
            for corner in CORNERS:
                with self.subTest(along=along, corner=corner):
                    pending = self.assert_case(self.case(along=along, corner=corner))
                    self.assertEqual(1, len(pending['preview']['rbuttShifts']), 'R03R_NONZERO_SHIFT_EXERCISED')
                    self.assertTrue(self.terminal(pending, cancel=True).get('cancelled'))

    def test_R03_translated_and_odd_gap_source_floor(self):
        for case in (self.case(origin=(-123, 456)),
                     self.case(along='u', corner='max-max', origin=(-2000, -4000)),
                     *(self.case(3713, gap=3, along=along, corner=corner)
                       for along in ('u', 'v') for corner in CORNERS)):
            with self.subTest(case=case):
                pending = self.assert_case(case, marker='R03R_ODD_GAP_SOURCE_FLOOR')
                self.assertTrue(self.terminal(pending, cancel=True).get('cancelled'))

    def test_R04_exact_rational_threshold_and_full_r43(self):
        for along in ('u', 'v'):
            for corner in CORNERS:
                with self.subTest(along=along, corner=corner):
                    case = self.case(3713, gap=3, along=along, corner=corner, threshold=(40, 4))
                    pending = self.assert_case(case, marker='R03R_EXACT_THRESHOLD')
                    self.assertEqual(1, len(pending['preview']['rbuttShifts']), 'R03R_EXACT_THRESHOLD')
                    self.assertTrue(self.terminal(pending, cancel=True).get('cancelled'))
        case = self.case(3713, gap=3, threshold=(41, 4))
        self.configure(case)
        oracle = retreat_oracle()
        expected = oracle.build(case)
        self.assertTrue(any(row.startswith('R43_SUPPORT:') for row in oracle.check(case, expected)),
                        'R03R_R43_COUNTEREXAMPLE_PRECONDITION')
        before = self.snapshot()
        refused = self.packet('framing-template-preview', self.request_case(case))
        self.assertFalse(refused.get('ok'), 'R03R_EXACT_THRESHOLD')
        self.assertEqual('NATIVE_INVALID', refused.get('code'), 'R03R_COMPLETE_R43_REQUIRED')
        self.assertIn('R43', refused.get('error', ''), 'R03R_COMPLETE_R43_REQUIRED')
        self.assertEqual(before, self.snapshot(), 'R03R_REJECT_ZERO_WRITE')

    def test_R05_existing_contact_and_nearest_tie_negative(self):
        pending = self.assert_case(self.case(3708), marker='R03R_EXISTING_CONTACT')
        self.assertEqual([], pending['preview']['rbuttShifts'], 'R03R_EXISTING_CONTACT')
        self.assertTrue(self.terminal(pending, cancel=True).get('cancelled'))
        case = self.case(83, 1000, parameters=dict(PARAMETERS, panelWidth=40))
        pending = self.assert_case(case, marker='R03R_NEAREST_TIE_NEGATIVE')
        self.assertEqual([-1], [row['shift'] for row in pending['preview']['rbuttShifts']],
                         'R03R_NEAREST_TIE_NEGATIVE')
        self.assertTrue(self.terminal(pending, cancel=True).get('cancelled'))

    def test_R06_ft02_and_native_gap_remain_real_rejections(self):
        for width, code, detail in ((3700, 'POLICY_RULE_CONFLICT', None),
                                    (3720, 'NATIVE_INVALID', 'R43')):
            case = self.case(width)
            self.configure(case)
            before = self.snapshot()
            refused = self.packet('framing-template-preview', self.request_case(case))
            self.assertFalse(refused.get('ok'),
                             'R03R_COMPLETE_R43_REQUIRED' if detail else 'R03R_NO_UNSUPPORTED_APPROVAL')
            self.assertEqual(code, refused.get('code'), 'R03R_NO_UNSUPPORTED_APPROVAL')
            if detail:
                self.assertIn(detail, refused.get('error', ''), 'R03R_COMPLETE_R43_REQUIRED')
            self.assertNotIn('preview', refused, 'R03R_REJECT_ZERO_WRITE')
            self.assertEqual(before, self.snapshot(), 'R03R_REJECT_ZERO_WRITE')

    def test_R07_immutable_v1_v2_and_zero_action_equivalence(self):
        old_one_request = {'schema': 'framing-template-read/1', 'boundaryId': 1}
        old_two_request = {'schema': 'framing-template-read/2', 'boundaryId': 1, 'template': OLD_TWO}
        old_one = self.packet('framing-template-read', old_one_request)
        old_two = self.packet('framing-template-read', old_two_request)
        self.read()
        self.assertEqual(old_one, self.packet('framing-template-read', old_one_request), 'R03R_OLD_READ_UNCHANGED')
        self.assertEqual(old_two, self.packet('framing-template-read', old_two_request), 'R03R_OLD_READ_UNCHANGED')
        self.assertEqual(('flat-ceiling', 1, POLICY),
                         tuple(old_one['generator'][key] for key in ('id', 'version', 'policyFingerprint')))
        request = self.request(read=old_two)
        request['template'] = deepcopy(OLD_TWO)
        before = self.snapshot()
        rejected = self.packet('framing-template-preview', request)
        self.assertEqual('POLICY_RULE_CONFLICT', rejected.get('code'), 'R03R_V2_STILL_REJECTS_BUTT')
        self.assertEqual(before, self.snapshot(), 'R03R_REJECT_ZERO_WRITE')
        for along in ('u', 'v'):
            for corner in CORNERS:
                case = self.case(3740, 3301, along=along, corner=corner)
                pending = self.assert_case(case)
                self.assertEqual([], pending['preview']['rbuttShifts'], 'R03R_ZERO_ACTION')
                self.assertTrue(self.terminal(pending, cancel=True).get('cancelled'))
                read = self.packet('framing-template-read', old_two_request)
                request = self.request(read=read, along=along, corner=corner)
                request['template'] = deepcopy(OLD_TWO)
                old = self.packet('framing-template-preview', request)
                self.assertTrue(old.get('ok') and old.get('preview', {}).get('valid'), old)
                for key in ('members', 'seams', 'marks', 'sources', 'definitionChain', 'supportComplete', 'support'):
                    self.assertEqual(old['preview'][key], pending['preview'][key], 'R03R_ZERO_ACTION_OLD_V2_EQUIVALENCE')
                self.assertNotIn('panelLayout', old['preview'], 'R03R_OLD_PREVIEW_UNCHANGED')
                self.assertNotIn('rbuttShifts', old['preview'], 'R03R_OLD_PREVIEW_UNCHANGED')
                self.assertTrue(self.terminal(old, cancel=True).get('cancelled'))

    def test_R08_explicit_identity_source_schema_and_context(self):
        read = self.read()
        before = self.snapshot()
        for template in (dict(TEMPLATE, policyFingerprint='0' * 64),
                         dict(TEMPLATE, version=2), dict(TEMPLATE, id='flat-ceiling'),
                         dict(OLD_TWO, version=1)):
            refused = self.packet('framing-template-read', {
                'schema': 'framing-template-read/2', 'boundaryId': 1, 'template': template})
            self.assertFalse(refused.get('ok'), 'R03R_EXACT_IMMUTABLE_IDENTITY')
        original = self.request(read=read)
        variants = []
        for field in ('on', 'material', 'definitionFingerprint', 'sources'):
            value = deepcopy(original)
            del value[field]
            variants.append(value)
        for extra in ('seam_retreat', 'r_butt'):
            value = deepcopy(original)
            value[extra] = False
            variants.append(value)
        value = deepcopy(original); value['template']['policyFingerprint'] = POLICY_A; variants.append(value)
        value = deepcopy(original); value['parameters']['gap'] = True; variants.append(value)
        value = deepcopy(original); value['sources']['panel']['version'] = 2; variants.append(value)
        value = deepcopy(original); value['sources']['threshold']['fieldId'] = 999; variants.append(value)
        for value in variants:
            self.assertFalse(self.packet('framing-template-preview', value).get('ok'), 'R03R_STRICT_SOURCE_SCHEMA')
            self.assertEqual(before, self.snapshot(), 'R03R_REJECT_ZERO_WRITE')
        for field, code in (('contextKey', 'CONTEXT'), ('definitionFingerprint', 'STALE')):
            value = deepcopy(original)
            value[field] = '0' * 64
            refused = self.packet('framing-template-preview', value)
            self.assertEqual(code, refused.get('code'), 'R03R_CONTEXT_SOURCE_SEAL')
            self.assertEqual(before, self.snapshot(), 'R03R_REJECT_ZERO_WRITE')

    def test_R09_cancel_confirm_one_history_and_cold_load(self):
        case = self.case()
        self.configure(case)
        before = self.snapshot()
        pending = self.assert_case(case, arrange=False)
        self.assertEqual(before, self.snapshot(), 'R03R_PREVIEW_ZERO_WRITE')
        self.assertTrue(self.terminal(pending, cancel=True).get('cancelled'))
        self.assertEqual(before, self.snapshot(), 'R03R_CANCEL_ZERO_WRITE')
        self.assertFalse(self.terminal(pending).get('ok'), 'R03R_CANCELLED_TOKEN')
        pending = self.assert_case(case, arrange=False)
        committed = self.terminal(pending)
        self.assertTrue(committed.get('ok') and committed.get('history_changed'),
                        'R03R_CONFIRM_EXACT_CANDIDATE: ' + repr(committed))
        rows = self.ok('references')['timbers']
        self.assertEqual([row['geometry'] for row in pending['preview']['members']],
                         [row['geometry'] for row in rows], 'R03R_CONFIRM_EXACT_CANDIDATE')
        self.assertEqual(pending['preview']['definitionFingerprint'],
                         self.ok('engineering-read')['definition_sha256'], 'R03R_CONFIRM_EXACT_CANDIDATE')
        layout = self.ok('panel-fill-read')['state']['panelFills'][0]['derived']
        self.assertEqual(pending['preview']['panelLayout'], layout, 'R03R_CONFIRM_EVERY_PANEL')
        after = self.ok('dump')['text']
        self.assertNotIn('framing-template', after, 'R03R_ORDINARY_WORLD_ONLY')
        self.assertNotIn('flat-ceiling', after, 'R03R_ORDINARY_WORLD_ONLY')
        self.assertFalse(self.terminal(pending).get('ok'), 'R03R_CONFIRM_EXACTLY_ONCE')
        self.ok('line undo')
        self.assertEqual(before[0], self.ok('dump')['text'], 'R03R_ONE_HISTORY')
        self.ok('line redo')
        self.assertEqual(after, self.ok('dump')['text'], 'R03R_ONE_HISTORY')
        path = self.directory / 'rbutt-confirmed.scene'
        path.write_text(after, encoding='utf-8')
        cold = BoundedSession(self.executable)
        try:
            self.assertTrue(cold.command('loadfile ' + str(path)).get('ok'), 'R03R_COLD_LOAD')
            self.assertEqual(after, cold.command('dump')['text'], 'R03R_COLD_ORDINARY_BYTES')
            self.assertEqual(rows, cold.command('references')['timbers'], 'R03R_COLD_EVERY_MEMBER')
            self.assertEqual(layout, cold.command('panel-fill-read')['state']['panelFills'][0]['derived'],
                             'R03R_COLD_EVERY_PANEL')
            read = self.packet('framing-template-read', {
                'schema': 'framing-template-read/2', 'boundaryId': 1, 'template': TEMPLATE}, cold)
            self.assertTrue(read.get('ok'), 'R03R_COLD_READ_IDENTITY')
            self.assertEqual(0, read['generatorInvocations'], 'R03R_COLD_NO_GENERATOR')
        finally:
            self.session.receipts.append({'separate_session': 'cold', 'receipts': cold.receipts})
            cold.stop()

    def test_R10_live_original_seam_guide_and_named_offset(self):
        pending = self.assert_case(self.case(), marker='R03R_LIVE_SEAM_GUIDE')
        self.assertTrue(self.terminal(pending).get('ok'))
        scene = self.ok('dump')['text']
        fill_record = next(line for line in scene.splitlines() if line.startswith('panel-fill '))
        definition = json.loads(bytes.fromhex(fill_record.split()[3]))
        self.assertEqual({'id', 'finishSurfaceId', 'panel', 'lengthAlong', 'origin', 'gap', 'pattern', 'threshold'},
                         set(definition), 'R03R_NO_FAKE_FT02_DEFINITION')
        self.assertEqual({'parameterId': 90, 'fieldId': 1}, definition['threshold'], 'R03R_X_PARAMETER_REF')
        shifts = pending['preview']['rbuttShifts']
        rows = self.ok('references')['timbers']
        for shift in shifts:
            identifier = shift['guideId']
            guide = next(line for line in scene.splitlines() if line.startswith(f'guide {identifier} '))
            self.assertRegex(guide, rf'grid:\d+:{shift["axis"]}:{int(shift["k"])}(?:\+|-)spec:',
                             'R03R_LIVE_ORIGINAL_GRID_K')
            source = re.search(r'spec:([A-Za-z0-9_]+)', guide).group(1)
            self.assertIn(f'spec {source} {shift["shift"]}', scene.splitlines(), 'R03R_NAMED_SHIFT_VALUE')
            native = [row for row in rows if row['definition']['anchor'] == f'at-line guide {identifier}']
            self.assertEqual(1, len(native), 'R03R_SHIFT_GUIDE_ACTUALLY_ANCHORS_MAIN')
            self.assertEqual('primary', native[0]['role'], 'R03R_SHIFT_GUIDE_ACTUALLY_ANCHORS_MAIN')
            self.assertEqual(shift['seamCenter'] + shift['shift'], native[0]['geometry']['centerline'],
                             'R03R_LIVE_ORIGINAL_GRID_K')
            calls = self.read()['generatorInvocations']
            edit = self.cmd(f'line spec {source} 0')
            self.assertTrue(edit.get('preview', {}).get('valid'),
                            'R03R_SOURCE_EDIT_IMPACT_PREVIEW: ' + repr(edit))
            self.assertEqual(scene, self.ok('dump')['text'], 'R03R_SOURCE_EDIT_PREVIEW_ZERO_WRITE')
            self.ok('line confirm ' + str(edit['preview']['token']))
            changed = next(row for row in self.ok('references')['timbers'] if row['id'] == native[0]['id'])
            self.assertEqual(shift['seamCenter'], changed['geometry']['centerline'], 'R03R_GUIDE_LIVE_RECALCULATION')
            self.assertEqual(calls, self.read()['generatorInvocations'], 'R03R_EDIT_NO_REGENERATION')
            support = self.ok('panel-fill-read')['state']['panelFills'][0]['derived']['support']
            self.assertTrue(any(not row['supported'] for row in support),
                            'R03R_ORDINARY_EDIT_RETAINS_VISIBLE_R43_INSUFFICIENCY')
            self.ok('line undo')
            self.assertEqual(scene, self.ok('dump')['text'], 'R03R_GUIDE_EDIT_UNDO')

    def test_R11_owner_stale_and_whole_scope(self):
        pending = self.assert_case(self.case())
        before = self.snapshot()
        self.assertFalse(self.terminal(pending, owner='0' * 64).get('ok'), 'R03R_OWNER_REQUIRED')
        self.assertFalse(self.cmd('engineering-confirm ' + str(pending['preview']['token'])).get('ok'),
                         'R03R_FOREIGN_CONFIRM_REQUIRED')
        self.assertEqual(before, self.snapshot(), 'R03R_FOREIGN_ZERO_WRITE')
        self.ok('line spec r03r_unrelated 123')
        before = self.snapshot()
        self.assertFalse(self.terminal(pending).get('ok'), 'R03R_STALE_CONFIRM_REQUIRED')
        self.assertEqual(before, self.snapshot(), 'R03R_STALE_ZERO_WRITE')
        for shape in ('hole', 'column'):
            self.configure(self.case())
            if shape == 'hole':
                self.ok('line surface 1 origin 0 0 2500 u +x v +y outline 0,0 3709,0 3709,2000 0,2000 hole 1000,500 1200,500 1200,700 1000,700')
            else:
                self.ok('line column 1 at 900 900 size 100 100 z 0 3000')
            before = self.snapshot()
            refused = self.preview()
            self.assertEqual('UNSUPPORTED_SCOPE', refused.get('code'), 'R03R_COMPLETE_SCOPE_REQUIRED')
            self.assertEqual(before, self.snapshot(), 'R03R_REJECT_ZERO_WRITE')

    def test_R12_capacity_counts_shift_guides_without_raising_limits(self):
        self.ok('line spec r03r_existing_guide 100')
        for identifier in range(12):
            self.ok(f'line guide {identifier} 1 v spec:r03r_existing_guide')
        before = self.snapshot()
        refused = self.preview()
        self.assertFalse(refused.get('ok'), 'R03R_SHIFT_GUIDE_CAPACITY')
        self.assertIn('CAPACITY', refused.get('error', ''), 'R03R_SHIFT_GUIDE_CAPACITY')
        self.assertEqual(before, self.snapshot(), 'R03R_CAPACITY_ZERO_WRITE')
        self.configure(self.case(60000))
        before = self.snapshot()
        refused = self.preview()
        self.assertEqual('CAPACITY', refused.get('code'), 'R03R_W_CAPACITY_NO_TRUNCATION')
        self.assertEqual(before, self.snapshot(), 'R03R_CAPACITY_ZERO_WRITE')

    def test_R13_transport_named_identity_and_strict_private_payload(self):
        path = ROOT / 'geometry-web/framing_template_transport.py'
        spec = importlib.util.spec_from_file_location('r03r_exact_transport', path)
        transport = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(transport)
        seen, paths = [], []

        def ask(command):
            private = Path(command.split(' ', 1)[1])
            paths.append(private)
            seen.append(private.read_bytes())
            return json.dumps(self.cmd(command)).encode('utf-8')

        value = {'schema': 'framing-template-read/2', 'boundaryId': 1, 'template': TEMPLATE}
        raw = json.dumps(value, separators=(',', ':')).encode('utf-8')
        result = json.loads(transport.request(raw, ask, mode='read'))
        self.assertTrue(result.get('ok'), 'R03R_TRANSPORT_NEW_IDENTITY')
        self.assertEqual(raw, seen[-1], 'R03R_TRANSPORT_EXACT_BYTES')
        before = len(seen)
        for template in ({}, dict(TEMPLATE, version=True), dict(TEMPLATE, version=2),
                         dict(TEMPLATE, extra=0), dict(OLD_TWO, version=1)):
            bad = dict(value, template=template)
            self.assertFalse(json.loads(transport.request(json.dumps(bad).encode(), ask, mode='read')).get('ok'),
                             'R03R_TRANSPORT_STRICT_SHAPE')
        self.assertFalse(json.loads(transport.request(raw.replace(b'"boundaryId":1', b'"boundaryId":1,"boundaryId":1'),
                                                      ask, mode='read')).get('ok'), 'R03R_TRANSPORT_DUPLICATE_KEY')
        self.assertEqual(before, len(seen), 'R03R_TRANSPORT_BAD_INPUT_ZERO_NATIVE_CALLS')
        bad = dict(value, template=dict(TEMPLATE, policyFingerprint='0' * 64))
        self.assertFalse(json.loads(transport.request(json.dumps(bad).encode(), ask, mode='read')).get('ok'),
                         'R03R_NATIVE_POLICY_GATE')
        self.assertEqual(before + 1, len(seen), 'R03R_NATIVE_POLICY_GATE')
        self.assertTrue(all(not path.exists() for path in paths), 'R03R_PRIVATE_TRANSPORT_FILES_REMOVED')

    def test_R14_minimum_piece_equality_and_no_short_infill(self):
        for along in ('u', 'v'):
            reverse = 'min-max' if along == 'u' else 'max-min'
            for extent, corner in ((3735, 'min-min'), (3734, reverse)):
                with self.subTest(along=along, extent=extent, corner=corner):
                    pending = self.assert_case(self.case(extent, along=along, corner=corner),
                                               marker='R03R_MIN_PIECE_EQUALITY')
                    short = [row for row in pending['preview']['members'] if row['length'] == 27]
                    self.assertEqual(5, len(short), 'R03R_MIN_PIECE_EQUALITY')
                    self.assertEqual({'secondary:mark', 'secondary:seam'},
                                     {row['kind'] for row in short}, 'R03R_MIN_PIECE_EQUALITY')
                    self.assertTrue(self.terminal(pending, cancel=True).get('cancelled'))
            for extent, corner in ((3734, 'min-min'), (3733, reverse)):
                with self.subTest(along=along, extent=extent, corner=corner):
                    case = self.case(extent, along=along, corner=corner)
                    self.configure(case)
                    oracle = retreat_oracle()
                    expected = oracle.build(case)
                    self.assertFalse(any(row['length'] < 27 for row in expected['members']),
                                     'R03R_SHORT_PIECE_ORACLE_PRECONDITION')
                    self.assertTrue(any(row.startswith('R43_SUPPORT:') for row in oracle.check(case, expected)),
                                    'R03R_SHORT_PIECE_ORACLE_PRECONDITION')
                    before = self.snapshot()
                    refused = self.packet('framing-template-preview', self.request_case(case))
                    self.assertFalse(refused.get('ok'), 'R03R_SHORT_PIECE_NOT_FABRICATED')
                    self.assertEqual('NATIVE_INVALID', refused.get('code'), 'R03R_SHORT_PIECE_NOT_FABRICATED')
                    self.assertIn('R43', refused.get('error', ''), 'R03R_SHORT_PIECE_NOT_FABRICATED')
                    self.assertEqual(before, self.snapshot(), 'R03R_REJECT_ZERO_WRITE')

    def test_R15_real_footprint_union_and_independent_ft02_checker(self):
        # A centered width-28 main has 13/12 mm alone. Its + side already
        # touches the parallel wall member, whose real material raises that
        # side's contiguous union to 40 mm. R43 does not impose another
        # isolated-main threshold on this otherwise legal zero-action case.
        case = self.case(143, 200, gap=3, threshold=(13, 1),
                         parameters=dict(PARAMETERS, panelWidth=100, timberWidth=28))
        pending = self.assert_case(case, marker='R03R_REAL_FOOTPRINT_UNION')
        self.assertEqual([], pending['preview']['rbuttShifts'], 'R03R_EXISTING_CONTACT')
        self.assertEqual([[87, 28, 115, 172]],
                         [row['rect'] for row in pending['preview']['members'] if row['kind'] == 'main'],
                         'R03R_REAL_FOOTPRINT_UNION')
        self.assertTrue(any(row['left'] == 13 and row['right'] == 40
                            for row in pending['preview']['support']), 'R03R_REAL_FOOTPRINT_UNION')
        oracle = retreat_oracle()
        enabled = oracle.build(case)
        zero_action = deepcopy(case)
        zero_action['r_butt'] = False
        unchanged = oracle.build(zero_action)
        self.assertEqual([], oracle.check(zero_action, unchanged), 'R03R_ZERO_ACTION_UNION')
        self.assertEqual(enabled['members'], unchanged['members'], 'R03R_ZERO_ACTION_UNION')
        self.assertEqual(enabled['panels'], unchanged['panels'], 'R03R_ZERO_ACTION_UNION')
        self.assertTrue(self.terminal(pending, cancel=True).get('cancelled'))
        old_read = self.packet('framing-template-read', {
            'schema': 'framing-template-read/2', 'boundaryId': 1, 'template': OLD_TWO})
        self.assertTrue(old_read.get('ok'), 'R03R_V2_EXISTING_CONTACT')
        request = self.request(read=old_read, parameters=case['parameters'])
        request['template'] = deepcopy(OLD_TWO)
        old = self.packet('framing-template-preview', request)
        self.assertTrue(old.get('ok') and old.get('preview', {}).get('valid'),
                        'R03R_V2_EXISTING_CONTACT: ' + repr(old))
        self.assertEqual(pending['preview']['members'], old['preview']['members'], 'R03R_ZERO_ACTION_UNION')
        self.assertEqual(pending['preview']['definitionFingerprint'], old['preview']['definitionFingerprint'],
                         'R03R_ZERO_ACTION_ORDINARY_DEFINITIONS')
        self.assertTrue(self.terminal(old).get('ok'))
        self.assertEqual(pending['preview']['panelLayout'],
                         self.ok('panel-fill-read')['state']['panelFills'][0]['derived'],
                         'R03R_V2_EVERY_PANEL_UNION')

        # FT02 remains a later native slice. This is a test of the independent
        # diagnostic predicate: after construction it must not call build.
        ft02 = self.case(3700)
        ft02['seam_retreat'] = 'ft02'
        result = oracle.build(ft02)
        with patch.object(oracle, 'build', side_effect=RuntimeError('checker called construction')):
            self.assertEqual([], oracle.check(ft02, result), 'R03R_CHECKER_INDEPENDENT_OF_BUILD')
        self.assertEqual([0, 1, 2, 3],
                         [row['k'] for row in result['seam_rows'] if row['axis'] == 'u'],
                         'R03R_FT02_ORIGINAL_SIGNED_KEYS')
        self.assertEqual([907, 40],
                         [row['rect'][2] - row['rect'][0] for row in result['panels']
                          if row['j'] == 0 and row['i'] in (3, 4)], 'R03R_FT02_REAL_PANEL_CUTS')

        # A union may be wider than the panel being supported. Only actual
        # material beneath that particular adjacent panel body counts: the
        # retreated middle panel here is 28 mm wide and cannot bear X=30.
        narrow = self.case(112, 200, gap=0, threshold=(30, 1),
                           parameters=dict(PARAMETERS, panelWidth=42, timberWidth=28))
        narrow['seam_retreat'] = 'ft02'
        narrow_result = oracle.build(narrow)
        self.assertEqual([42, 70], narrow_result['seams']['u'], 'R03R_R43_PANEL_BODY_LIMIT')
        middle = [row for row in narrow_result['panels'] if row['i'] == 1 and row['j'] == 0]
        self.assertEqual(1, len(middle), 'R03R_R43_PANEL_BODY_LIMIT')
        self.assertEqual(28, middle[0]['rect'][2] - middle[0]['rect'][0], 'R03R_R43_PANEL_BODY_LIMIT')
        errors = oracle.check(narrow, narrow_result)
        self.assertEqual({'R43_SUPPORT'}, {row.split(':', 1)[0] for row in errors},
                         'R03R_R43_PANEL_BODY_LIMIT: ' + repr(errors))
        self.assertTrue(any(re.search(r'has (?:28/\d+|\d+/28) mm, X=30/1', row) for row in errors),
                        'R03R_R43_PANEL_BODY_LIMIT: ' + repr(errors))

        # D1 also constrains the resulting formal origin and automatic length,
        # even when every input scalar separately fits its coordinate limit.
        outside_origin = self.case(100, 100, corner='max-min', origin=(-100000000, 0))
        oversized = self.case(200000000, 100, gap=0, origin=(-100000000, 0),
                              parameters=dict(PARAMETERS, panelWidth=100000000))
        for label, vector in (('formal-origin', outside_origin), ('automatic-length', oversized)):
            with self.subTest(derived_limit=label):
                problems = oracle.check(vector, oracle.build(vector))
                self.assertTrue(any(row.startswith('D1_DERIVED:') for row in problems),
                                'R03R_D1_DERIVED_LIMIT: ' + repr(problems))


if __name__ == '__main__':
    unittest.main()
