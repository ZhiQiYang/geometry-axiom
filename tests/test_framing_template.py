"""R03 native product slice: independent oracle values and real candidate lifecycle.

The oracle is test-only. Product code must not import it, read its golden, or
store generated results/search traces in project recipes or native definitions.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
import re
import socket
import subprocess
from pathlib import Path
import sys
import tempfile
import time
import unittest
from urllib.error import URLError
from urllib.request import Request, urlopen
import uuid

from test_timber_edit import Session

ROOT = Path(__file__).resolve().parents[1]
POLICY = '21d364e9cbc1d98bf7d3663d0878829c00adc17f43957127d6cea748b3cebd83'
PARAMETERS = {'panelWidth': 915, 'panelLength': 1830, 'gap': 2,
              'timberWidth': 27, 'timberDepth': 33,
              'maxSecondarySpacing': 367}


def oracle_module():
    path = ROOT / 'geometry-core/framing-template/oracle/framing_oracle.py'
    spec = importlib.util.spec_from_file_location('r03_independent_oracle', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FramingTemplateNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.executable = os.environ.get('GEOMETRY_TEST_BRIDGE')
        if not cls.executable:
            raise unittest.SkipTest('GEOMETRY_TEST_BRIDGE required for actual native execution')
        cls.oracle = oracle_module()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='r03-native-')
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.session = Session(self.executable)
        self.addCleanup(self.finish)
        self.surface(3740, 2000)

    def finish(self):
        target = os.environ.get('GEOMETRY_FRAMING_RECEIPTS')
        if target:
            target = Path(target)
            target.mkdir(parents=True, exist_ok=True)
            (target / (self._testMethodName + '.json')).write_text(json.dumps({
                'case': self.id(),
                'binary_sha256': hashlib.sha256(Path(self.executable).read_bytes()).hexdigest(),
                'receipts': self.session.receipts}, ensure_ascii=False, indent=2), encoding='utf-8')
        self.session.stop()

    def cmd(self, command):
        return self.session.command(command)

    def ok(self, command):
        result = self.cmd(command)
        self.assertTrue(result.get('ok'), result)
        return result

    def surface(self, width, height, x0=0, y0=0):
        self.ok('reset')
        self.ok(f'line surface 1 origin 0 0 2500 u +x v +y outline {x0},{y0} {x0+width},{y0} {x0+width},{y0+height} {x0},{y0+height}')
        self.seed_sources()

    def seed_sources(self, threshold='8'):
        revision = self.ok('engineering-read')['revision']
        operations = [{'op': 'publish-material', 'value': {'id': 'r03-board', 'version': 1,
                       'kind': 'panel', 'name': '明選試驗板材', 'width': 915, 'length': 1830, 'thickness': '6'}},
                      {'op': 'put-parameter', 'value': {'id': 90, 'name': '承接', 'fields': [
                          {'id': 1, 'name': 'X', 'type': 'dimension', 'input': threshold}]}}]
        result = self.packet('engineering-preview', {'schema': 'engineering-transaction/1',
                             'expectedRevision': revision, 'operations': operations})
        self.assertTrue(result.get('ok') and result['preview']['valid'], result)
        self.ok('engineering-confirm ' + str(result['preview']['token']))

    def packet(self, command, value, session=None):
        path = self.directory / 'request.json'
        path.write_bytes(value if isinstance(value, bytes) else json.dumps(value).encode())
        target = session or self.session
        result = target.command(command + ' ' + str(path))
        target.receipts[-1]['request'] = deepcopy(value) if not isinstance(value, bytes) else value.decode(errors='replace')
        return result

    def read(self):
        result = self.packet('framing-template-read', {'schema': 'framing-template-read/1', 'boundaryId': 1})
        self.assertTrue(result.get('ok'), 'R03_NATIVE_ENTRY_AVAILABLE: ' + repr(result))
        return result

    def request(self, read=None, corner='min-min', along='v', parameters=None):
        read = read or self.read()
        return {'schema': 'framing-template-generate/1', 'expectedRevision': read['revision'],
                'contextKey': read['contextKey'], 'definitionFingerprint': read['definitionFingerprint'],
                'boundaryId': 1, 'on': 1,
                'template': {'id': 'flat-ceiling', 'version': 1, 'policyFingerprint': POLICY},
                'parameters': deepcopy(parameters or PARAMETERS),
                'sources': {'panel': {'id': 'r03-board', 'version': 1},
                            'threshold': {'parameterId': 90, 'fieldId': 1}},
                'layout': {'corner': corner, 'lengthAlong': along},
                'material': {'boundary': 'rc', 'timber': 'literal'}}

    def preview(self, **kwargs):
        return self.packet('framing-template-preview', self.request(**kwargs))

    def accepted(self, marker='R03_CANDIDATE_VALID', **kwargs):
        result = self.preview(**kwargs)
        self.assertTrue(result.get('ok') and result.get('preview', {}).get('valid'), marker + ': ' + repr(result))
        return result

    def terminal(self, result, cancel=False, session=None, owner=None):
        return (session or self.session).command('framing-template-' + ('cancel' if cancel else 'confirm') + ' ' +
                str(result['preview']['token']) + ' ' + (owner or result['ownerKey']))

    def snapshot(self):
        return self.ok('dump')['text'], self.ok('engineering-read')['revision'], self.ok('newid')

    @staticmethod
    def members(rows):
        return sorted((r['kind'], tuple(r['rect']), r['length']) for r in rows)

    def assert_oracle(self, room, corner, along, frozen=None):
        x0 = min(p[0] for p in room['outer']); y0 = min(p[1] for p in room['outer'])
        width = max(p[0] for p in room['outer']) - x0
        height = max(p[1] for p in room['outer']) - y0
        self.surface(width, height, x0, y0)
        result = self.accepted(corner=corner, along=along)
        starts = corner.split('-')
        layout = {'A': 'x' if along == 'v' else 'y',
                  'a_start': starts[0 if along == 'v' else 1],
                  'b_start': starts[1 if along == 'v' else 0]}
        params = {'P': 915, 'L': 1830, 'gap': 2, 'w': 27, 'M': 367, 'X': 8, 'min_piece': 27}
        oracle = self.oracle.build(room, layout, params)
        self.assertEqual([], self.oracle.check(oracle, params), 'test oracle must independently accept complete expected layout')
        self.assertEqual([], oracle['conflicts'])
        self.assertEqual([], oracle['core_limits'])
        expected = []
        for member in oracle['timbers']:
            kind = member['kind'] + (':' + member['role'] if member['kind'] == 'secondary' else '')
            rect = member['rect']
            expected.append((kind, tuple(rect), max(rect[2] - rect[0], rect[3] - rect[1])))
        self.assertEqual(sorted(expected), self.members(result['preview']['members']), 'R03_ORACLE_EVERY_MEMBER_VALUE')
        if frozen is not None:
            fixture = next(item for item in frozen if item['layout'] == layout)
            self.assertEqual(fixture['timbers'], [[r['kind'], r['rect']] for r in result['preview']['members']], 'R03_FROZEN_GOLDEN_EVERY_MEMBER')
        actual = result['preview']['members']
        self.assertEqual(sorted(expected), [(r['kind'], tuple(r['rect']), r['length']) for r in actual], 'R03_ORACLE_MEMBER_ORDER')
        self.assertEqual(sorted(oracle['seams_a']), result['preview']['seams']['u' if along == 'v' else 'v'], 'R03_ORACLE_WIDTH_SEAMS')
        self.assertEqual(sorted(oracle['seams_b']), result['preview']['seams'][along], 'R03_ORACLE_LENGTH_SEAMS')
        marks = sorted({t['at'] for t in oracle['timbers'] if t['kind'] == 'secondary' and t.get('role') == 'mark'})
        self.assertEqual(marks, result['preview']['marks'], 'R03_ORACLE_MARKS')
        for row in actual:
            geometry = row['geometry']
            role = 'boundary' if row['kind'] == 'boundary' else 'secondary' if row['kind'].startswith('secondary:') else 'primary'
            self.assertEqual(role, row['role'], 'R03_NATIVE_ROLE')
            self.assertEqual((27, 33, '+n'), (geometry['A'], geometry['B'], geometry['side']))
            self.assertEqual([0, 0, 1], geometry['axes'][2], 'R03_NATIVE_DEPTH_AXIS')
            self.assertEqual(2506, geometry['origin'][2], 'R03_FINISH_PLUS_PANEL_THICKNESS')
            # Reconstruct all eight actual solid vertices independently. This
            # checks origin, signed axes, faces and length, including nonzero
            # F3/F4 coordinates, rather than trusting the preview rect cache.
            vertices = [[geometry['origin'][d] + i * geometry['length'] * geometry['axes'][0][d]
                         + j * 27 * geometry['axes'][1][d] + k * 33 * geometry['axes'][2][d]
                         for d in range(3)] for i in (0, 1) for j in (0, 1) for k in (0, 1)]
            bounds = [min(v[d] for v in vertices) for d in range(3)] + [max(v[d] for v in vertices) for d in range(3)]
            self.assertEqual([row['rect'][0], row['rect'][1], 2506, row['rect'][2], row['rect'][3], 2539], bounds, 'R03_NATIVE_EIGHT_VERTEX_FACES')
        self.assertTrue(self.terminal(result, cancel=True)['cancelled'])

    def test_N01_read_fixed_version_and_explicit_source(self):
        before = self.snapshot()
        read = self.read()
        header = (ROOT / 'geometry-templates/woodworking/native/flat_ceiling.h').read_text()
        descriptor = re.search(r'#define WOOD_FLAT_POLICY_DESCRIPTOR "([^"\n]+)"', header).group(1)
        self.assertEqual(POLICY, hashlib.sha256(descriptor.encode('ascii')).hexdigest(), 'R03_POLICY_RECOMPUTABLE')
        self.assertEqual('framing-template-read-result/1', read['schema'])
        self.assertEqual(('flat-ceiling', 1, POLICY), tuple(read['generator'][k] for k in ('id', 'version', 'policyFingerprint')))
        self.assertEqual(PARAMETERS, read['generator']['defaults'])
        self.assertEqual(1, read['source']['boundaryId'])
        self.assertEqual([1], [r['id'] for r in read['source']['placements']])
        self.assertEqual(before, self.snapshot())

    def test_N02_existing_oracle_values_and_new_rectangle(self):
        golden = json.loads((ROOT / 'geometry-core/framing-template/oracle/oracle-golden.json').read_text())
        cases = []
        for name, along in [('F3次臥', 'u'), ('F4走道', 'v')]:
            room = golden['rooms'][name]['room']
            cases.append((room, along, golden['rooms'][name]['layouts']))
        cases.append(({'outer': [[0, 0], [3740, 0], [3740, 2000], [0, 2000]]}, 'v', None))
        for room, along, frozen in cases:
            for corner in ('min-min', 'max-min', 'min-max', 'max-max'):
                with self.subTest(room=room, along=along, corner=corner):
                    self.assert_oracle(room, corner, along, frozen)

    def test_N03_cancel_leaves_every_formal_value_unchanged(self):
        before = self.snapshot()
        pending = self.accepted()
        self.assertEqual(before, self.snapshot(), 'R03_PREVIEW_ZERO_WRITE')
        result = self.terminal(pending, cancel=True)
        self.assertTrue(result.get('ok') and result.get('cancelled'), result)
        self.assertEqual(before, self.snapshot(), 'R03_CANCEL_ZERO_WRITE')
        self.assertFalse(self.terminal(pending).get('ok'))

    def test_N04_confirm_one_history_and_cold_replay_no_generator(self):
        before = self.ok('dump')['text']
        pending = self.accepted()
        committed = self.terminal(pending)
        self.assertTrue(committed.get('ok') and committed.get('history_changed'), committed)
        after = self.ok('dump')['text']
        self.assertNotEqual(before, after)
        self.assertNotIn('framing-template', after, 'R03_WORLD_HAS_NO_RECIPE_OR_SEARCH')
        self.assertNotIn('flat-ceiling', after, 'R03_WORLD_HAS_NO_RECIPE_OR_SEARCH')
        self.assertFalse(self.preview().get('ok'), 'R03_NO_DUPLICATE_DERIVED_HOST_GENERATION')
        self.assertFalse(self.terminal(pending).get('ok'), 'R03_CONFIRM_EXACTLY_ONCE')
        self.ok('line undo')
        self.assertEqual(before, self.ok('dump')['text'], 'R03_ONE_HISTORY_FRAME')
        self.ok('line redo')
        self.assertEqual(after, self.ok('dump')['text'])
        file = self.directory / 'confirmed.scene'
        file.write_text(after, encoding='utf-8')
        cold = Session(self.executable)
        try:
            self.assertTrue(cold.command('reset')['ok'])
            self.assertTrue(cold.command('loadfile ' + str(file))['ok'])
            self.assertEqual(after, cold.command('dump')['text'], 'R03_COLD_REPLAY_ORDINARY_DEFINITIONS')
            self.assertEqual(0, self.packet('framing-template-read', {'schema': 'framing-template-read/1', 'boundaryId': 1}, cold)['generatorInvocations'], 'R03_COLD_OPEN_NO_SEARCH')
        finally:
            cold.stop()

    def test_N05_stale_owner_and_foreign_confirmation_rejected(self):
        pending = self.accepted()
        self.assertFalse(self.terminal(pending, owner='0' * 64).get('ok'))
        self.assertFalse(self.cmd('engineering-confirm ' + str(pending['preview']['token'])).get('ok'), 'R03_FOREIGN_KIND_TOKEN')
        self.assertFalse(self.preview().get('ok'), 'R03_FOREIGN_PREVIEW_NOT_REPLACED')
        self.ok('line spec r03_unrelated 123')
        self.assertFalse(self.terminal(pending).get('ok'), 'R03_STALE_CONFIRM_ZERO_WRITE')

    def test_N06_only_closed_rectangle_without_holes_or_obstacles(self):
        self.ok('line surface 1 origin 0 0 2500 u +x v +y outline 0,0 3740,0 3740,2000 0,2000 hole 1000,500 1200,500 1200,700 1000,700')
        before = self.snapshot()
        result = self.preview()
        self.assertFalse(result.get('ok'), 'R03_CONTINUOUS_MAIN_NOT_CUT_BY_COLUMN')
        self.assertEqual('UNSUPPORTED_SCOPE', result.get('code'))
        self.assertEqual(before, self.snapshot())
        self.surface(3740, 2000)
        self.ok('line column 1 at 900 900 size 100 100 z 0 3000')
        before = self.snapshot()
        result = self.preview()
        self.assertFalse(result.get('ok'), 'R03_COLUMN_CANNOT_SPLIT_MAIN')
        self.assertEqual('UNSUPPORTED_SCOPE', result.get('code'))
        self.assertEqual(before, self.snapshot())

    def test_N07_first_full_panel_not_centered(self):
        pending = self.accepted(marker='R03_NOT_CENTERED')
        self.assertEqual([916, 1833, 2750, 3667], pending['preview']['seams']['u'], 'R03_NOT_CENTERED')
        self.assertEqual([1831], pending['preview']['seams']['v'], 'R03_NOT_CENTERED')
        main = [r for r in pending['preview']['members'] if r['kind'] == 'main']
        self.assertEqual(4, len(main), 'R03_MAIN_CONTINUOUS')
        self.assertTrue(all(r['rect'][1] == 27 and r['rect'][3] == 1973 and r['length'] == 1946 for r in main), 'R03_MAIN_CONTINUOUS')

    def test_N08_3700_oracle_retreat_is_not_silently_adopted(self):
        for width, height, along, gap in ((3700, 2000, 'v', 2), (3700, 2000, 'u', 2), (3700, 4000, 'u', 3)):
            with self.subTest(width=width, height=height, along=along, gap=gap):
                self.surface(width, height)
                before = self.snapshot()
                params = dict(PARAMETERS, gap=gap)
                result = self.preview(along=along, parameters=params)
                self.assertFalse(result.get('ok'), 'R03_ONLY_OPPOSITE_WALL_TRIM')
                self.assertEqual('POLICY_RULE_CONFLICT', result.get('code'), result)
                self.assertEqual(before, self.snapshot())

    def test_N09_ceil_marks_and_policy_difference(self):
        pending = self.accepted(marker='R03_CEIL_MARKS')
        self.assertEqual([363, 730, 1097, 1464], pending['preview']['marks'], 'R03_CEIL_MARKS')
        self.terminal(pending, cancel=True)
        self.surface(3720, 2631)
        result = self.preview()
        self.assertFalse(result.get('ok'), 'R03_POLICY_DIFFERENCE_REJECTED')
        self.assertEqual('POLICY_RULE_CONFLICT', result.get('code'))

    def test_N10_required_material_frame_version_and_exact_schema(self):
        request = self.request()
        variants = []
        for key in ('on', 'material', 'definitionFingerprint'):
            r = deepcopy(request); del r[key]; variants.append(r)
        r = deepcopy(request); r['template']['version'] = 2; variants.append(r)
        r = deepcopy(request); r['template']['policyFingerprint'] = '0' * 64; variants.append(r)
        r = deepcopy(request); r['material']['boundary'] = 'guessed'; variants.append(r)
        r = deepcopy(request); r['parameters']['gap'] = True; variants.append(r)
        r = deepcopy(request); r['parameters']['panelWidth'] = 915.5; variants.append(r)
        for value in variants:
            with self.subTest(value=value):
                before = self.snapshot()
                result = self.packet('framing-template-preview', value)
                self.assertFalse(result.get('ok'), 'R03_STRICT_SOURCE_AND_VERSION')
                self.assertEqual(before, self.snapshot())

    def test_N11_existing_source_grid_not_overwritten(self):
        self.ok('line grid 0 on 1 u 100 v 200')
        before = self.snapshot()
        self.assertFalse(self.preview().get('ok'), 'R03_NO_EXISTING_DEFINITION_OVERWRITE')
        self.assertEqual(before, self.snapshot())

    def test_N12_support_and_complete_native_validation(self):
        self.seed_sources(threshold='14')
        before = self.snapshot()
        result = self.preview()
        self.assertFalse(result.get('ok'), 'R03_SUPPORT_EACH_SIDE')
        self.assertEqual(before, self.snapshot())
        self.surface(3720, 2000)
        before = self.snapshot()
        result = self.preview()
        self.assertFalse(result.get('ok'), 'R03_ORACLE_SLIVER_STILL_NEEDS_R43')
        self.assertEqual('NATIVE_INVALID', result.get('code'))
        self.assertIn('R43', result.get('error', ''))
        self.assertEqual(before, self.snapshot())

    def test_N13_actual_finish_fill_derived_and_live_grid_sources(self):
        pending = self.accepted()
        self.assertTrue(self.terminal(pending)['ok'])
        scene = self.ok('dump')['text']
        self.assertIn('finish-surface ', scene, 'R03_TRUE_FINISH')
        fill_lines = [line for line in scene.splitlines() if line.startswith('panel-fill ')]
        self.assertEqual(1, len(fill_lines), 'R03_TRUE_FILL')
        definition = json.loads(bytes.fromhex(fill_lines[0].split()[3]))
        self.assertEqual({'parameterId': 90, 'fieldId': 1}, definition['threshold'], 'R03_X_PARAMETER_REF')
        self.assertEqual({'id': 'r03-board', 'version': 1}, definition['panel'])
        self.assertEqual(1, sum(line.startswith('derived-placement ') for line in scene.splitlines()), 'R03_TRUE_DERIVED_HOST')
        self.assertEqual(1, sum(' from-fill ' in line for line in scene.splitlines()), 'R03_LIVE_FROM_FILL')
        state = self.ok('panel-fill-read')['state']['panelFills'][0]['derived']
        self.assertTrue(state['support'], 'R03_COMPLETE_SUPPORT')
        self.assertTrue(all(s['supported'] for s in state['support']), 'R03_EACH_SEGMENT_EACH_SIDE')
        self.assertTrue(all(s['left'] >= 8 and s['right'] >= 8 for s in state['support']), 'R03_EACH_SEGMENT_EACH_SIDE')

    def test_N14_fixed_sources_and_live_recalculation_do_not_regenerate(self):
        pending = self.accepted()
        self.assertTrue(self.terminal(pending)['ok'])
        before = self.ok('references')['timbers']
        invocations = self.read()['generatorInvocations']
        self.seed_sources(threshold='9')
        self.assertEqual(before, self.ok('references')['timbers'], 'R03_THRESHOLD_IS_NOT_GEOMETRY')
        self.assertEqual(invocations, self.read()['generatorInvocations'], 'R03_LIVE_RECALC_NO_GENERATOR')
        scene = self.ok('dump')['text']
        self.assertIn(' from-fill ', scene)
        definition = json.loads(bytes.fromhex(next(line.split()[3] for line in scene.splitlines() if line.startswith('panel-fill '))))
        definition['gap'] = 3
        result = self.packet('panel-fill-preview', {'schema': 'panel-fill-transaction/1',
                             'expectedRevision': self.ok('panel-fill-read')['revision'],
                             'operations': [{'op': 'put-panel-fill', 'value': definition}]})
        self.assertTrue(result.get('ok') and result['preview']['valid'], 'R03_LIVE_SOURCE_GAP_EDIT: ' + repr(result))
        self.ok('panel-fill-confirm ' + str(result['preview']['token']))
        rows = self.ok('references')['timbers']
        self.assertEqual([r['id'] for r in before], [r['id'] for r in rows], 'R03_SOURCE_EDIT_PRESERVES_IDS')
        main = [r for r in rows if r['role'] == 'primary' and r['definition']['anchor'].startswith('at-line grid ')]
        self.assertEqual([916, 1834, 2752, 3670], [r['geometry']['centerline'] for r in main], 'R03_SIGNED_FROM_FILL_RECALCULATES_REAL_MEMBERS')
        self.assertEqual(invocations, self.read()['generatorInvocations'], 'R03_SOURCE_EDIT_NEVER_SEARCHES_TEMPLATE')


class FramingTemplateHTTP(unittest.TestCase):
    def test_H01_real_http_receipts_cancel_and_single_confirm(self):
        executable = os.environ.get('GEOMETRY_TEST_BRIDGE')
        if not executable:
            self.skipTest('GEOMETRY_TEST_BRIDGE required for actual HTTP/native execution')
        if os.name != 'nt':
            import resource
            soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
            resource.setrlimit(resource.RLIMIT_STACK, (max(soft, 16 * 1024 * 1024), hard))
        with tempfile.TemporaryDirectory(prefix='r03-http-') as directory:
            directory = Path(directory)
            with socket.socket() as reserve:
                reserve.bind(('127.0.0.1', 0))
                port = reserve.getsockname()[1]
            log_path = directory / 'serve.log'
            env = dict(os.environ, GEOMETRY_BRIDGE_EXECUTABLE=executable,
                       GEOMETRY_FEEDBACK_DIR=str(directory / 'feedback'))
            receipts = []
            with log_path.open('wb') as log:
                process = subprocess.Popen([sys.executable, str(ROOT / 'geometry-web/serve.py'), str(port)],
                                           env=env, stdout=log, stderr=log)
                try:
                    base = f'http://127.0.0.1:{port}'
                    deadline = time.monotonic() + 15
                    while True:
                        try:
                            with urlopen(base + '/runtime', timeout=1) as reply:
                                runtime = json.load(reply)
                            break
                        except (OSError, URLError):
                            if process.poll() is not None or time.monotonic() >= deadline:
                                self.fail('R03_HTTP_START: ' + log_path.read_text())
                            time.sleep(.05)
                    self.assertTrue(runtime['fresh'], 'R03_HTTP_FRESH_BINARY')

                    def post(route, data, headers=None):
                        request = Request(base + route, json.dumps(data).encode(),
                                          {'Content-Type': 'application/json', **(headers or {})})
                        with urlopen(request, timeout=15) as reply:
                            result = json.load(reply)
                        receipts.append({'route': route, 'request': data, 'headers': headers or {}, 'reply': result})
                        return result

                    def command(text, **fields):
                        return post('/api', dict(cmd=text, **fields))

                    self.assertTrue(command('reset')['ok'])
                    self.assertTrue(command('line surface 1 origin 0 0 2500 u +x v +y outline 0,0 3740,0 3740,2000 0,2000')['ok'])
                    revision = command('engineering-read')['revision']
                    source = post('/engineering/preview', {'schema': 'engineering-transaction/1', 'expectedRevision': revision,
                        'operations': [{'op': 'publish-material', 'value': {'id': 'r03-board', 'version': 1, 'kind': 'panel',
                            'name': '明選試驗板材', 'width': 915, 'length': 1830, 'thickness': '6'}},
                            {'op': 'put-parameter', 'value': {'id': 90, 'name': '承接', 'fields': [
                                {'id': 1, 'name': 'X', 'type': 'dimension', 'input': '8'}]}}]})
                    self.assertTrue(source['ok'] and source['preview']['valid'], source)
                    self.assertTrue(command('engineering-confirm ' + str(source['preview']['token']))['ok'])
                    before = command('dump')['text']
                    read = post('/framing-template/read', {'schema': 'framing-template-read/1', 'boundaryId': 1})
                    self.assertTrue(read.get('ok'), 'R03_HTTP_NATIVE_READ: ' + repr(read))
                    body = {'schema': 'framing-template-generate/1', 'expectedRevision': read['revision'],
                            'contextKey': read['contextKey'], 'definitionFingerprint': read['definitionFingerprint'],
                            'boundaryId': 1, 'on': 1, 'template': {'id': 'flat-ceiling', 'version': 1, 'policyFingerprint': POLICY},
                            'parameters': PARAMETERS, 'sources': {'panel': {'id': 'r03-board', 'version': 1},
                                'threshold': {'parameterId': 90, 'fieldId': 1}},
                            'layout': {'corner': 'min-min', 'lengthAlong': 'v'}, 'material': {'boundary': 'rc', 'timber': 'literal'}}
                    headers = {'X-Geometry-Request-Id': str(uuid.uuid4()), 'X-Geometry-Session': runtime['session']}
                    pending = post('/framing-template/preview', body, headers)
                    self.assertTrue(pending.get('ok') and pending['preview']['valid'], pending)
                    self.assertEqual(pending, post('/framing-template/preview', body, headers), 'R03_HTTP_PREVIEW_EXACT_REPLAY')
                    receipt = post('/api', {'receipt': headers['X-Geometry-Request-Id'], 'session': runtime['session']})
                    self.assertEqual(pending, receipt['result'])
                    cancelled = command(f"framing-template-cancel {pending['preview']['token']} {pending['ownerKey']}",
                                        requestId=str(uuid.uuid4()), session=runtime['session'])
                    self.assertTrue(cancelled['ok'] and cancelled['cancelled'], cancelled)
                    self.assertEqual(before, command('dump')['text'], 'R03_HTTP_CANCEL_ZERO_WRITE')
                    headers['X-Geometry-Request-Id'] = str(uuid.uuid4())
                    pending = post('/framing-template/preview', body, headers)
                    self.assertTrue(pending['ok'], pending)
                    commit_id = str(uuid.uuid4())
                    commit_text = f"framing-template-confirm {pending['preview']['token']} {pending['ownerKey']}"
                    committed = command(commit_text, requestId=commit_id, session=runtime['session'])
                    self.assertTrue(committed['ok'] and committed['history_changed'], committed)
                    self.assertEqual(committed, command(commit_text, requestId=commit_id, session=runtime['session']), 'R03_HTTP_COMMIT_EXACT_REPLAY')
                    after = command('dump')['text']
                    self.assertIn(' from-fill ', after)
                    self.assertTrue(command('line undo')['ok'])
                    self.assertEqual(before, command('dump')['text'], 'R03_HTTP_ONE_HISTORY')
                    self.assertTrue(command('line redo')['ok'])
                    self.assertEqual(after, command('dump')['text'])
                finally:
                    process.terminate()
                    process.wait(timeout=10)
                    target = os.environ.get('GEOMETRY_FRAMING_RECEIPTS')
                    if target:
                        output = Path(target); output.mkdir(parents=True, exist_ok=True)
                        (output / 'HTTP-receipts.json').write_text(json.dumps(receipts, ensure_ascii=False, indent=2), encoding='utf-8')
                        (output / 'HTTP-serve.log').write_bytes(log_path.read_bytes())


if __name__ == '__main__':
    unittest.main()
