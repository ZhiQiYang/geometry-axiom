"""R03 third slice: real native L candidates against the unchanged policy A oracle.

This suite uses the real bridge and ordinary World definitions.  Oracle output
is test data only; product code must not import the oracle or its goldens.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import unittest

from test_framing_template import FramingTemplateHarness, PARAMETERS, POLICY as V1
from test_timber_edit import Session


DESCRIPTOR = ('flat-ceiling/3;rectangle-or-single-notch-l-no-holes-no-obstacles;'
              'explicit-fixed-rc-boundary;panel-version-and-threshold-parameter-ref;'
              'literal-timber-dimensions;oracle-fixed-jig;rc-connected-main-spans;'
              'reflex-boundary-extension-custom3-custom4;centered-seams-unmodified-jig-marks;'
              'no-seam-retreat;no-r-butt;no-fill-or-doubling;one-global-origin;'
              'finish-fill-derived-from-fill;whole-candidate-native-validation;'
              'ordinary-world-definitions;no-search-on-load')
POLICY = hashlib.sha256(DESCRIPTOR.encode('ascii')).hexdigest()
V2 = '3641dec4060cfcf062e2f1d55f341ecb5ae5023da4a4d8a3aba2c3c4110b6d58'
ROOM = [[0, 0], [3740, 0], [3740, 2000], [2500, 2000], [2500, 3301], [0, 3301]]
RECTANGLE = [[0, 0], [3740, 0], [3740, 3301], [0, 3301]]
RECTANGLE_FIELDS = ('members', 'seams', 'marks', 'support', 'sources', 'definitionChain')


def rectangle_cases():
    """The complete 128-input domain, not a filter on whichever calls succeed."""
    for gap in (2, 3):
        for along in ('u', 'v'):
            for corner in ('min-min', 'max-min', 'min-max', 'max-max'):
                for reverse in (False, True):
                    ring = list(reversed(RECTANGLE)) if reverse else RECTANGLE
                    for start in range(4):
                        yield {'id': f'g{gap}-{along}-{corner}-{"reverse" if reverse else "forward"}-{start}',
                               'gap': gap, 'along': along, 'corner': corner,
                               'reverse': reverse, 'start': start,
                               'points': ring[start:] + ring[:start]}


def rectangle_expected_acceptance(case):
    # Characterize the released v2 edge-index defect; this is not a claim that
    # reordered valid rings should be rejected. v3 maps the complete real edge.
    return {'v2': 'accepted' if not case['reverse'] and case['start'] == 0 else 'NATIVE_INVALID',
            'v3': 'accepted'}


def native_outcome(reply):
    return ('accepted' if reply.get('ok') is True and reply.get('preview', {}).get('valid') is True
            else reply.get('code', 'INVALID_REPLY'))


class FramingTemplateNotch(FramingTemplateHarness):
    def polygon(self, points=ROOM):
        self.ok('reset')
        vertices = ' '.join(f'{x},{y}' for x, y in points)
        self.ok('line surface 1 origin 0 0 2500 u +x v +y outline ' + vertices)
        self.seed_sources()

    def read_version(self, version=3):
        packet = {'schema': f'framing-template-read/{version}', 'boundaryId': 1}
        if version != 1:
            packet['template'] = {'id': 'flat-ceiling', 'version': version,
                                  'policyFingerprint': POLICY if version == 3 else V2}
        result = self.packet('framing-template-read', packet)
        self.assertTrue(result.get('ok'), 'R03B_VERSION3_AVAILABLE: ' + repr(result))
        return result

    def read(self):
        return self.read_version()

    def request(self, read=None, corner='min-min', along='v', parameters=None, version=3):
        result = super().request(read or self.read_version(version), corner, along, parameters)
        result['template'] = {'id': 'flat-ceiling', 'version': version,
                              'policyFingerprint': {1: V1, 2: V2, 3: POLICY}[version]}
        return result

    def assert_notch_oracle(self, points=ROOM, gap=2, corner='min-min', along='v'):
        self.polygon(points)
        params = dict(PARAMETERS, gap=gap)
        pending = self.accepted(marker='R03B_L_NATIVE_CANDIDATE', corner=corner, along=along,
                                parameters=params)
        start = corner.split('-')
        layout = {'A': 'x' if along == 'v' else 'y',
                  'a_start': start[0 if along == 'v' else 1],
                  'b_start': start[1 if along == 'v' else 0]}
        op = {'P': 915, 'L': 1830, 'gap': gap, 'w': 27, 'M': 367, 'X': 8, 'min_piece': 27}
        expected = self.oracle.build({'outer': points}, layout, op)
        self.assertEqual([], self.oracle.check(expected, op), 'R03B_ORACLE_INDEPENDENT_CHECKS')
        self.assertEqual([], expected['conflicts'])
        self.assertEqual([], expected['core_limits'])
        rows = []
        for item in expected['timbers']:
            kind = item['kind'] + (':' + item['role'] if item['kind'] == 'secondary' else '')
            role = item.get('core_role', 'boundary' if item['kind'] == 'boundary'
                            else 'secondary' if item['kind'] == 'secondary' else 'primary')
            rect = item['rect']
            axis = (1 if along == 'v' else 0) if item['kind'] in ('main', 'rc_parallel') else (0 if along == 'v' else 1)
            rows.append((kind, tuple(rect), rect[axis + 2] - rect[axis], role,
                         item.get('priority', {'boundary': 1, 'primary': 2, 'secondary': 3}[role] if role != 'custom' else 0)))
        actual = pending['preview']['members']
        got = [(r['kind'], tuple(r['rect']), r['length'], r['role'], r['priority']) for r in actual]
        self.assertEqual(sorted(rows), sorted(got), 'R03B_ORACLE_EVERY_MEMBER')
        self.assertEqual(sorted(expected['seams_a']), pending['preview']['seams']['u' if along == 'v' else 'v'], 'R03B_GLOBAL_ORIGIN')
        self.assertEqual(sorted(expected['seams_b']), pending['preview']['seams'][along], 'R03B_GLOBAL_ORIGIN')
        self.assertLessEqual(len(actual), 512, 'R03B_COMPLETE_CAPACITY')
        self.assertTrue(pending['preview']['supportComplete'], 'R03B_NATIVE_R43_REQUIRED')
        self.assertTrue(all(p['supported'] for p in pending['preview']['support']), 'R03B_NATIVE_R43_REQUIRED')
        self.assertTrue(any(r['role'] == 'custom' and r['priority'] == 3 for r in actual), 'R03B_REFLEX_CUSTOM3')
        self.assertTrue(any(r['role'] == 'custom' and r['priority'] == 4 for r in actual), 'R03B_REFLEX_CUSTOM4')
        return pending

    def assert_rectangle_true_output(self, pending, points, gap=2, corner='min-min', along='v'):
        """Check real native values against the unchanged policy constructor.

        Ring acceptance and output equality are separate assertions. In
        particular, the known v3-only counterexample must verify every member;
        accepting a self-reported member count cannot establish equivalence.
        """
        start = corner.split('-')
        a, b = (0, 1) if along == 'v' else (1, 0)
        layout = {'A': 'xy'[a], 'a_start': start[a], 'b_start': start[b]}
        params = {'P': 915, 'L': 1830, 'gap': gap, 'w': 27, 'M': 367, 'X': 8, 'min_piece': 27}
        expected = self.oracle.build({'outer': points}, layout, params)
        self.assertEqual(([], [], []), (expected['conflicts'], expected['core_limits'],
                                      self.oracle.check(expected, params)),
                         'R03B_RECTANGLE_REFERENCE_VALID')
        rows = []
        for member in expected['timbers']:
            kind = member['kind'] + (':' + member['role'] if member['kind'] == 'secondary' else '')
            role = 'boundary' if member['kind'] == 'boundary' else 'secondary' if member['kind'] == 'secondary' else 'primary'
            axis = b if member['kind'] in ('main', 'rc_parallel') else a
            rect = member['rect']
            rows.append((kind, tuple(rect), rect[axis + 2] - rect[axis], role,
                         {'boundary': 1, 'primary': 2, 'secondary': 3}[role]))
        preview = pending['preview']
        actual = [(r['kind'], tuple(r['rect']), r['length'], r['role'], r['priority'])
                  for r in preview['members']]
        self.assertEqual(sorted(rows), sorted(actual), 'R03B_RECTANGLE_TRUE_OUTPUT_EVERY_MEMBER')
        self.assertEqual({'uv'[a]: sorted(expected['seams_a']), 'uv'[b]: sorted(expected['seams_b'])},
                         preview['seams'], 'R03B_RECTANGLE_TRUE_OUTPUT_SEAMS')
        marks = sorted({m['at'] for m in expected['timbers']
                        if m['kind'] == 'secondary' and m.get('role') == 'mark'})
        self.assertEqual(marks, preview['marks'], 'R03B_RECTANGLE_TRUE_OUTPUT_MARKS')
        self.assertEqual({'panel': {'id': 'r03-board', 'version': 1},
                          'threshold': {'parameterId': 90, 'fieldId': 1}},
                         preview['sources'], 'R03B_RECTANGLE_TRUE_OUTPUT_SOURCES')
        self.assertEqual(['finish-surface', 'panel-fill', 'derived-placement', 'from-fill',
                          'guide', 'timber', 'place'], preview['definitionChain'],
                         'R03B_RECTANGLE_TRUE_OUTPUT_DEFINITION_CHAIN')
        self.assertTrue(preview['supportComplete'] and preview['support'] and
                        all(part['supported'] for part in preview['support']),
                        'R03B_RECTANGLE_TRUE_OUTPUT_NATIVE_SUPPORT')
        for row in preview['members']:
            geometry = row['geometry']
            self.assertEqual((row['length'], 27, 33, '+n'),
                             (geometry['length'], geometry['A'], geometry['B'], geometry['side']),
                             'R03B_RECTANGLE_TRUE_OUTPUT_SOLID')
            vertices = [[geometry['origin'][d] + i * geometry['length'] * geometry['axes'][0][d]
                         + j * 27 * geometry['axes'][1][d] + k * 33 * geometry['axes'][2][d]
                         for d in range(3)] for i in (0, 1) for j in (0, 1) for k in (0, 1)]
            bounds = [min(v[d] for v in vertices) for d in range(3)] + [max(v[d] for v in vertices) for d in range(3)]
            self.assertEqual([row['rect'][0], row['rect'][1], 2506,
                              row['rect'][2], row['rect'][3], 2539], bounds,
                             'R03B_RECTANGLE_TRUE_OUTPUT_EIGHT_VERTICES')

    def test_B01_explicit_immutable_v3_read(self):
        self.polygon()
        before = self.snapshot()
        read = self.read()
        self.assertEqual('framing-template-read-result/3', read['schema'], 'R03B_VERSION3_AVAILABLE')
        self.assertEqual({'id': 'flat-ceiling', 'version': 3, 'policyFingerprint': POLICY},
                         {k: read['generator'][k] for k in ('id', 'version', 'policyFingerprint')})
        self.assertEqual(PARAMETERS, read['generator']['defaults'])
        self.assertEqual(before, self.snapshot(), 'R03B_READ_ZERO_WRITE')

    def test_B02_L_every_member_native_and_oracle(self):
        for gap in (2, 3):
            for along in ('u', 'v'):
                for corner in ('min-min', 'max-min', 'min-max', 'max-max'):
                    with self.subTest(gap=gap, along=along, corner=corner):
                        pending = self.assert_notch_oracle(gap=gap, along=along, corner=corner)
                        self.assertTrue(self.terminal(pending, cancel=True)['cancelled'])

    def test_B03_rectangle_degeneracy_preserves_v2_exact_rows(self):
        for width, height in ((3740, 3301), (2500, 3000), (3740, 2000)):
            self.surface(width, height)
            p2 = self.accepted(version=2, marker='R03B_V2_BASELINE')
            self.assertTrue(self.terminal(p2, cancel=True)['ok'])
            p3 = self.accepted(marker='R03B_ZERO_NOTCH_EQUALS_V2')
            rows3 = [{k: v for k, v in row.items() if k != 'priority'} for row in p3['preview']['members']]
            self.assertEqual(p2['preview']['members'], rows3, 'R03B_ZERO_NOTCH_EQUALS_V2')
            for field in ('seams', 'marks', 'support', 'sources', 'definitionChain'):
                self.assertEqual(p2['preview'][field], p3['preview'][field], 'R03B_ZERO_NOTCH_EQUALS_V2')
            self.assertTrue(self.terminal(p3, cancel=True)['ok'])

    def test_B04_cancel_commit_undo_redo_and_cold_native_load(self):
        self.polygon()
        before = self.snapshot()
        pending = self.accepted(marker='R03B_L_NATIVE_CANDIDATE')
        self.assertEqual(before, self.snapshot(), 'R03B_PREVIEW_ZERO_WRITE')
        self.assertTrue(self.terminal(pending, cancel=True)['cancelled'])
        self.assertEqual(before, self.snapshot(), 'R03B_CANCEL_ZERO_WRITE')
        pending = self.accepted(marker='R03B_L_NATIVE_CANDIDATE')
        want_hash = pending['preview']['definitionFingerprint']
        self.assertTrue(self.terminal(pending)['history_changed'])
        committed = self.snapshot()
        self.assertEqual(want_hash, self.read()['definitionFingerprint'], 'R03B_CONFIRM_EXACT_PREVIEW')
        self.ok('line undo')
        self.assertEqual(before[0], self.snapshot()[0], 'R03B_SINGLE_HISTORY')
        self.ok('line redo')
        self.assertEqual(committed[0], self.snapshot()[0], 'R03B_REDO_EXACT_WORLD')
        saved = self.directory / 'notch.scene'
        saved.write_text(committed[0], encoding='utf-8')
        cold = Session(self.executable)
        try:
            self.assertTrue(cold.command('loadfile ' + str(saved)).get('ok'), 'R03B_COLD_LOAD_VALID')
            self.assertEqual(committed[0], cold.command('dump')['text'], 'R03B_COLD_WORLD_EXACT')
            read = self.packet('framing-template-read', {'schema': 'framing-template-read/3', 'boundaryId': 1,
                               'template': {'id': 'flat-ceiling', 'version': 3, 'policyFingerprint': POLICY}}, session=cold)
            self.assertTrue(read.get('ok'), read)
            self.assertEqual(0, read['generatorInvocations'], 'R03B_COLD_NO_REGENERATION')
        finally:
            cold.stop()

    def test_B05_unsupported_U_and_holes_zero_write(self):
        self.polygon([[0, 0], [3740, 0], [3740, 1500], [2500, 1500], [2500, 1900], [3740, 1900], [3740, 3301], [0, 3301]])
        before = self.snapshot()
        result = self.preview()
        self.assertFalse(result.get('ok'), 'R03B_U_EXPLICITLY_UNSUPPORTED')
        self.assertEqual('UNSUPPORTED_SCOPE', result.get('code'))
        self.assertEqual(before, self.snapshot(), 'R03B_REJECT_ZERO_WRITE')
        self.surface(3740, 3301)
        self.ok('line surface 1 origin 0 0 2500 u +x v +y outline 0,0 3740,0 3740,3301 0,3301 hole 1000,500 1200,500 1200,700 1000,700')
        before = self.snapshot()
        result = self.preview()
        self.assertFalse(result.get('ok'), 'R03B_HOLES_NOT_APPROXIMATED')
        self.assertEqual('UNSUPPORTED_SCOPE', result.get('code'))
        self.assertEqual(before, self.snapshot(), 'R03B_REJECT_ZERO_WRITE')

    def test_B06_retreat_conflict_and_native_support_still_reject(self):
        self.surface(3700, 2000)
        before = self.snapshot()
        result = self.preview()
        self.assertFalse(result.get('ok'), 'R03B_NO_RETREAT')
        self.assertEqual('POLICY_RULE_CONFLICT', result.get('code'))
        self.assertEqual(before, self.snapshot(), 'R03B_REJECT_ZERO_WRITE')
        self.surface(3720, 2000)
        before = self.snapshot()
        result = self.preview()
        self.assertFalse(result.get('ok'), 'R03B_NATIVE_R43_REQUIRED')
        self.assertEqual('NATIVE_INVALID', result.get('code'))
        self.assertIn('R43', result.get('error', ''))
        self.assertEqual(before, self.snapshot(), 'R03B_REJECT_ZERO_WRITE')

    def test_B07_exact_version_and_source_guards(self):
        self.polygon()
        original = self.request()
        for mutate in (lambda p: p['template'].update(policyFingerprint='0' * 64),
                       lambda p: p['template'].update(version=4),
                       lambda p: p['material'].update(boundary='free'),
                       lambda p: p.update(extra=True)):
            value = deepcopy(original)
            mutate(value)
            before = self.snapshot()
            result = self.packet('framing-template-preview', value)
            self.assertFalse(result.get('ok'), 'R03B_EXACT_POLICY_SOURCE')
            self.assertEqual(before, self.snapshot(), 'R03B_REJECT_ZERO_WRITE')

    def test_B08_capacity_is_whole_candidate_refusal(self):
        self.surface(19000, 19000)
        before = self.snapshot()
        result = self.preview()
        self.assertFalse(result.get('ok'), 'R03B_CAPACITY_NO_TRUNCATION')
        self.assertEqual('CAPACITY', result.get('code'), 'R03B_CAPACITY_NO_TRUNCATION')
        self.assertEqual(before, self.snapshot(), 'R03B_REJECT_ZERO_WRITE')

    def test_B09_no_bbox_or_new_origin_for_translated_notch(self):
        points = [[x + 127, y - 202] for x, y in ROOM]
        pending = self.assert_notch_oracle(points)
        self.assertTrue(self.terminal(pending)['ok'])
        text = self.ok('dump')['text']
        fills = [line for line in text.splitlines() if line.startswith('panel-fill ')]
        self.assertEqual(1, len(fills), 'R03B_ONE_FILL_ONE_ORIGIN')
        fill = json.loads(bytes.fromhex(fills[0].split()[3]))
        self.assertEqual([127, -202], fill['origin'], 'R03B_ONE_FILL_ONE_ORIGIN')
        self.assertEqual(1, sum(line.startswith('derived-placement ') for line in text.splitlines()), 'R03B_ONE_DERIVED_HOST')

    def test_B10_transport_read_three_is_exact_and_private(self):
        path = Path(__file__).resolve().parents[1] / 'geometry-web/framing_template_transport.py'
        spec = importlib.util.spec_from_file_location('r03b_transport', path)
        transport = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(transport)
        self.polygon()
        paths, seen = [], []

        def ask(command):
            private = Path(command.split(' ', 1)[1])
            paths.append(private)
            seen.append(json.loads(private.read_bytes()))
            return json.dumps(self.cmd(command)).encode()

        body = {'schema': 'framing-template-read/3', 'boundaryId': 1,
                'template': {'id': 'flat-ceiling', 'version': 3, 'policyFingerprint': POLICY}}
        read = json.loads(transport.request(json.dumps(body).encode(), ask, mode='read'))
        self.assertTrue(read.get('ok'), 'R03B_TRANSPORT_READ_THREE: ' + repr(read))
        self.assertEqual(body, seen[-1], 'R03B_TRANSPORT_EXACT_PAYLOAD')
        self.assertEqual(POLICY, read['generator']['policyFingerprint'])
        bad = [dict(body, extra=1), dict(body, schema='framing-template-read/2'),
               {'schema': 'framing-template-read/0', 'boundaryId': 1}]
        for template in ({}, {'id': 'flat-ceiling', 'version': 3},
                         dict(body['template'], version=2), dict(body['template'], version=True),
                         dict(body['template'], extra=1)):
            bad.append(dict(body, template=template))
        calls = len(seen)
        for value in bad:
            rejected = json.loads(transport.request(json.dumps(value).encode(), ask, mode='read'))
            self.assertEqual('SCHEMA', rejected.get('code'), 'R03B_TRANSPORT_STRICT_SCHEMA')
            self.assertFalse(rejected.get('ok'))
        self.assertEqual(calls, len(seen), 'R03B_BAD_TRANSPORT_ZERO_NATIVE_CALLS')
        wrong = dict(body, template=dict(body['template'], policyFingerprint='0' * 64))
        rejected = json.loads(transport.request(json.dumps(wrong).encode(), ask, mode='read'))
        self.assertFalse(rejected.get('ok'), 'R03B_NATIVE_POLICY_GATE')
        self.assertEqual(calls + 1, len(seen))
        self.assertTrue(all(not p.exists() for p in paths), 'R03B_PRIVATE_FILES_CLEANED')

    def test_B11_cyclic_and_reversed_rings_keep_exact_edge_sources(self):
        for reverse in (False, True):
            ring = list(reversed(ROOM)) if reverse else ROOM
            for start in range(len(ring)):
                with self.subTest(reverse=reverse, start=start):
                    points = ring[start:] + ring[:start]
                    pending = self.assert_notch_oracle(points)
                    self.assertTrue(self.terminal(pending, cancel=True)['cancelled'])

    def test_B12_uint32_wrapped_zero_is_a_real_member_identity(self):
        self.polygon()
        self.ok('line timber 4294967295 27 33 role primary')
        pending = self.accepted(marker='R03B_ZERO_ID_IS_NOT_UNPLACED')
        self.assertTrue(self.terminal(pending)['ok'])
        self.assertIn('timber 0 27 33 role boundary', self.ok('dump')['text'], 'R03B_ZERO_ID_IS_NOT_UNPLACED')

    def test_B13_notch_needs_seam_member_shift_not_silent_omission(self):
        points = [[0, 3299], [3730, 3299], [3730, 3199], [100, 3199], [100, 0], [0, 0]]
        self.polygon(points)
        before = self.snapshot()
        result = self.preview(corner='max-min', along='u')
        self.assertFalse(result.get('ok'), 'R03B_SEAM_BAND_CANNOT_BE_DROPPED')
        self.assertEqual('POLICY_RULE_CONFLICT', result.get('code'), 'R03B_SEAM_BAND_CANNOT_BE_DROPPED')
        self.assertEqual(before, self.snapshot(), 'R03B_REJECT_ZERO_WRITE')

    def test_B14_rectangle_acceptance_matrix_and_common_exact_values(self):
        expected, observed, canonical = {}, {}, {}
        self.rectangle_matrix = []
        for case in rectangle_cases():
            expected[case['id']] = rectangle_expected_acceptance(case)
            with self.subTest(**{k: case[k] for k in ('gap', 'along', 'corner', 'reverse', 'start')}):
                self.polygon(case['points'])
                before = self.snapshot()
                replies = {}
                for version in (2, 3):
                    result = self.preview(version=version, parameters=dict(PARAMETERS, gap=case['gap']),
                                          corner=case['corner'], along=case['along'])
                    replies[f'v{version}'] = result
                    self.assertEqual(before, self.snapshot(), 'R03B_RECTANGLE_PREVIEW_ZERO_WRITE')
                    if native_outcome(result) == 'accepted':
                        self.assertTrue(self.terminal(result, cancel=True)['cancelled'],
                                        'R03B_RECTANGLE_CANCELLED')
                    self.assertEqual(before, self.snapshot(), 'R03B_RECTANGLE_CANCEL_OR_REJECT_ZERO_WRITE')
                outcomes = {version: native_outcome(reply) for version, reply in replies.items()}
                observed[case['id']] = outcomes
                self.rectangle_matrix.append({'input': case, 'expected': expected[case['id']],
                                              'observed': outcomes, 'native': replies})
                # This pin precedes every conditional comparison, so a newly
                # rejected or newly accepted input is a failure, never a skip.
                self.assertEqual(expected[case['id']], outcomes, 'R03B_RECTANGLE_ACCEPTANCE_SET_EXACT')
                p3 = replies['v3']['preview']
                if expected[case['id']]['v2'] == 'accepted':
                    rows3 = [{k: v for k, v in row.items() if k != 'priority'} for row in p3['members']]
                    self.assertEqual(replies['v2']['preview']['members'], rows3,
                                     'R03B_RECTANGLE_COMMON_MEMBERS')
                    for field in RECTANGLE_FIELDS[1:]:
                        self.assertEqual(replies['v2']['preview'][field], p3[field],
                                         'R03B_RECTANGLE_COMMON_' + field.upper())
                    canonical[(case['gap'], case['along'], case['corner'])] = p3
                else:
                    self.assertFalse(replies['v2']['ok'], 'R03B_RECTANGLE_V2_REJECTION_EXACT')
                    self.assertTrue(replies['v2'].get('error'), 'R03B_RECTANGLE_V2_REJECTION_REASON')
                    self.assertNotIn('preview', replies['v2'], 'R03B_RECTANGLE_REJECTION_HAS_NO_CANDIDATE')
                # Every reordered v3 result is compared with all values of the
                # same layout's common-domain baseline, including full support.
                for field in RECTANGLE_FIELDS:
                    self.assertEqual(canonical[(case['gap'], case['along'], case['corner'])][field],
                                     p3[field], 'R03B_RECTANGLE_RING_INVARIANT_' + field.upper())
                self.assert_rectangle_true_output(replies['v3'], case['points'], case['gap'],
                                                  case['corner'], case['along'])
        self.assertEqual(128, len(expected), 'R03B_RECTANGLE_INPUT_DOMAIN_COMPLETE')
        self.assertEqual(expected, observed, 'R03B_RECTANGLE_ACCEPTANCE_SET_EXACT')

    def test_B15_reordered_rectangle_known_difference_has_true_output(self):
        points = RECTANGLE[1:] + RECTANGLE[:1]
        self.polygon(points)
        before = self.snapshot()
        old = self.preview(version=2)
        self.assertEqual({'ok': False, 'code': 'NATIVE_INVALID',
                          'error': 'I9/I13 timber 53: one or more referenced objects cannot be reconstructed'},
                         old, 'R03B_RECTANGLE_REPORTED_V2_FAILURE')
        self.assertEqual(before, self.snapshot(), 'R03B_RECTANGLE_REPORTED_REJECT_ZERO_WRITE')
        new = self.preview()
        self.assertEqual('accepted', native_outcome(new), 'R03B_RECTANGLE_REPORTED_V3_ACCEPTS')
        self.assert_rectangle_true_output(new, points)
        self.assertTrue(self.terminal(new, cancel=True)['cancelled'], 'R03B_RECTANGLE_REPORTED_CANCEL')
        self.assertEqual(before, self.snapshot(), 'R03B_RECTANGLE_REPORTED_CANCEL_ZERO_WRITE')

    def test_B16_real_native_scope_reads_reach_app_specific_reason(self):
        self.polygon([[0, 0], [3740, 0], [3740, 1500], [2500, 1500],
                      [2500, 1900], [3740, 1900], [3740, 3301], [0, 3301]])
        before = self.snapshot()
        cases = [{'label': 'U', 'read': self.read_version(), 'reasonIncludes': 'U 形'}]
        self.assertEqual(0, cases[0]['read']['source']['holes'], 'R03B_REAL_READ_U_HOLE_COUNT')
        self.assertEqual(8, len(cases[0]['read']['source']['outer']), 'R03B_REAL_READ_U_RING')
        self.assertEqual(before, self.snapshot(), 'R03B_REAL_SCOPE_READ_ZERO_WRITE')
        self.surface(3740, 3301)
        self.ok('line surface 1 origin 0 0 2500 u +x v +y outline 0,0 3740,0 3740,3301 0,3301 hole 1000,500 1200,500 1200,700 1000,700')
        before = self.snapshot()
        cases.append({'label': 'holes', 'read': self.read_version(), 'reasonIncludes': '孔'})
        self.assertIn(' hole 1000,500 1200,500 1200,700 1000,700', before[0],
                      'R03B_REAL_READ_HOLE_DEFINITION')
        self.assertEqual(1, cases[1]['read']['source']['holes'], 'R03B_REAL_READ_HOLE_COUNT')
        self.assertEqual(before, self.snapshot(), 'R03B_REAL_SCOPE_READ_ZERO_WRITE')
        script = Path(__file__).resolve().parent / 'diagnostics/r03_notch_scope_read_probe.cjs'
        body = {'cases': cases}
        run = subprocess.run(['node', str(script)], input=json.dumps(body, ensure_ascii=False),
                             capture_output=True, text=True)
        self.session.receipts.append({'command': ['node', str(script)], 'request': body,
                                      'exit': run.returncode, 'stdout': run.stdout, 'stderr': run.stderr})
        self.assertEqual(0, run.returncode, 'R03B_REAL_READ_SCOPE_REASON: ' + run.stderr)
        parsed = json.loads(run.stdout)
        self.assertIs(parsed.get('ok'), True, 'R03B_REAL_READ_SCOPE_REASON: ' + run.stdout)
        self.assertEqual(before, self.snapshot(), 'R03B_REAL_SCOPE_APP_ZERO_NATIVE_WRITE')


if __name__ == '__main__':
    unittest.main()
