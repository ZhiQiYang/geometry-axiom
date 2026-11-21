#!/usr/bin/env python3
"""Synthetic parser regressions for R433; never Chrome/CDP or product evidence.

The coordinates, targets and shared pointer ID model Claude's Chrome 153 report
7057279218. These in-memory examples test only release_witness's interpretation.
They do not replay input, certify a historical product failure, write a browser
receipt or satisfy the exact-old-head / fixed / withdrawal / restored gates.
"""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import unittest


SPEC = importlib.util.spec_from_file_location(
    'r433_touch_predicates_under_test', Path(__file__).with_name('r433_touch_regression.py'))
REPAIR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPAIR)


def reported_release():
    """A synthetic structural example, not a stored or fabricated CDP result."""
    point = {
        'x': 78, 'y': 673.6,
        'geometry': {'inside': True, 'card': None, 'control': False, 'target': 'DIV'},
        'cardBounds': {'left': 80, 'right': 380, 'top': 496, 'bottom': 736},
    }
    detail = {
        'point': point, 'releaseMark': 2,
        'mouseDown': {'type': 'pointerdown', 'pointerType': 'mouse', 'trusted': True,
                      'x': 78, 'y': 673.6, 'card': None, 'control': False},
    }
    events = [
        {'type': 'pointerdown', 'pointerType': 'touch', 'trusted': True, 'pointerId': 5,
         'x': 78, 'y': 673.6, 'target': 'rect', 'card': 'boundary:43',
         'canvas': True, 'control': False},
        {'type': 'touchstart', 'trusted': True, 'touches': 1,
         'target': 'rect', 'card': 'boundary:43', 'canvas': True, 'control': False,
         'changedTouches': [{'id': 1, 'x': 78, 'y': 673.6, 'target': 'rect'}]},
        {'type': 'pointerup', 'pointerType': 'touch', 'trusted': True, 'pointerId': 5,
         'x': 78, 'y': 673.6, 'target': 'ocv', 'canvas': True, 'control': False},
        {'type': 'touchend', 'trusted': True, 'touches': 0,
         'changedTouches': [{'id': 1, 'x': 78, 'y': 673.6, 'target': 'rect'}]},
        {'type': 'click', 'pointerType': 'touch', 'trusted': True, 'pointerId': 5,
         'x': 83, 'y': 673, 'target': 'BUTTON', 'action': 'open',
         'canvas': False, 'control': True, 'firesTouchEvents': True},
    ]
    return detail, events


class ReleaseWitness(unittest.TestCase):
    """Only parser booleans are asserted; no row is labelled CDP pass or killed."""

    def test_reported_same_click_id_is_observation_only(self):
        detail, events = reported_release()
        self.assertTrue(REPAIR.release_witness(detail, events),
                        'R433_PARSER_ACCEPTS_REPORTED_SAME_ID')

    def test_different_and_absent_click_ids_are_observation_only(self):
        for click_id in (107, None):
            with self.subTest(click_id=click_id):
                detail, events = reported_release()
                if click_id is None:
                    events[-1].pop('pointerId')
                else:
                    events[-1]['pointerId'] = click_id
                self.assertTrue(REPAIR.release_witness(detail, events),
                                'R433_PARSER_CLICK_ID_IS_NOT_OWNERSHIP')

    def test_touch_origin_can_be_reported_by_either_browser_field(self):
        for removed in ('pointerType', 'firesTouchEvents'):
            with self.subTest(removed=removed):
                detail, events = reported_release()
                events[-1].pop(removed)
                self.assertTrue(REPAIR.release_witness(detail, events),
                                'R433_PARSER_ACCEPTS_OBSERVED_TOUCH_ORIGIN')

    def assert_rejected(self, mutate, label):
        detail, events = reported_release()
        # A different ID also satisfies T2's obsolete ID precondition, so these
        # tests independently retain each causal guard instead of passing only
        # because T2 rejects the reported same-ID example first.
        events[-1]['pointerId'] = 107
        mutate(detail, events)
        self.assertFalse(REPAIR.release_witness(detail, events), label)

    def test_every_required_input_is_trusted(self):
        for index in range(5):
            with self.subTest(event=index):
                self.assert_rejected(lambda _d, e, i=index: e[i].update(trusted=False),
                                     'R433_PARSER_REJECTS_UNTRUSTED_INPUT')
        self.assert_rejected(lambda d, _e: d['mouseDown'].update(trusted=False),
                             'R433_PARSER_REJECTS_UNTRUSTED_MOUSE')

    def test_release_order_and_required_events(self):
        for index in range(5):
            with self.subTest(missing=index):
                def remove(detail, events, index=index):
                    events.pop(index)
                    if index < detail['releaseMark']:
                        detail['releaseMark'] -= 1
                self.assert_rejected(remove, 'R433_PARSER_REQUIRES_COMPLETE_SEQUENCE')
        for first, second in ((0, 1), (2, 3), (3, 4)):
            with self.subTest(swapped=(first, second)):
                def swap(_detail, events, first=first, second=second):
                    events[first], events[second] = events[second], events[first]
                self.assert_rejected(swap, 'R433_PARSER_REQUIRES_ORDERED_SEQUENCE')

    def test_release_boundary_is_exact_integer(self):
        for mark in (True, '2', -1, 0, 1, 3, 4, 5, 6):
            with self.subTest(mark=mark):
                self.assert_rejected(lambda d, _e, value=mark: d.update(releaseMark=value),
                                     'R433_PARSER_REJECTS_WRONG_RELEASE_BOUNDARY')

    def test_down_and_up_keep_one_integer_pointer_identity(self):
        for value in (None, '5', True, 6):
            with self.subTest(up_id=value):
                self.assert_rejected(lambda _d, e, value=value: e[2].update(pointerId=value),
                                     'R433_PARSER_REJECTS_WRONG_UP_ID')
        for value in (None, '5', True):
            with self.subTest(down_id=value):
                self.assert_rejected(lambda _d, e, value=value: e[0].update(pointerId=value),
                                     'R433_PARSER_REJECTS_INVALID_DOWN_ID')

    def test_one_contact_ends_with_the_same_touch_identifier(self):
        variants = (
            ('touches remain', lambda _d, e: e[3].update(touches=1)),
            ('missing end count', lambda _d, e: e[3].pop('touches')),
            ('boolean start count', lambda _d, e: e[1].update(touches=True)),
            ('boolean end count', lambda _d, e: e[3].update(touches=False)),
            ('missing start contacts', lambda _d, e: e[1].pop('changedTouches')),
            ('missing end contacts', lambda _d, e: e[3].pop('changedTouches')),
            ('empty start contacts', lambda _d, e: e[1].update(changedTouches=[])),
            ('empty end contacts', lambda _d, e: e[3].update(changedTouches=[])),
            ('two start contacts', lambda _d, e: e[1]['changedTouches'].append({'id': 2})),
            ('two end contacts', lambda _d, e: e[3]['changedTouches'].append({'id': 2})),
            ('different contact', lambda _d, e: e[3]['changedTouches'][0].update(id=2)),
            ('missing start identifier', lambda _d, e: e[1]['changedTouches'][0].pop('id')),
            ('missing end identifier', lambda _d, e: e[3]['changedTouches'][0].pop('id')),
            ('boolean contact identifier', lambda _d, e: e[3]['changedTouches'][0].update(id=True)),
        )
        for label, mutate in variants:
            with self.subTest(label=label):
                self.assert_rejected(mutate, 'R433_PARSER_REQUIRES_SINGLE_RELEASED_CONTACT: ' + label)

    def test_array_order_does_not_assume_cross_event_timestamp_order(self):
        for timestamps in ((0, 0, 0, 0, 0), (5, 4, 3, 2, 1)):
            with self.subTest(timestamps=timestamps):
                detail, events = reported_release()
                for event, value in zip(events, timestamps):
                    event['timestamp'] = value
                self.assertTrue(REPAIR.release_witness(detail, events),
                                'R433_PARSER_USES_OBSERVED_EVENT_ARRAY_ORDER')

    def test_card_edge_and_actual_input_targets_remain_required(self):
        variants = (
            ('point outside', lambda d, _e: d['point']['geometry'].update(inside=False)),
            ('point on card', lambda d, _e: d['point']['geometry'].update(card='boundary:43')),
            ('point on control', lambda d, _e: d['point']['geometry'].update(control=True)),
            ('inside card bounds', lambda d, _e: d['point']['cardBounds'].update(left=78)),
            ('too far from card', lambda d, _e: d['point']['cardBounds'].update(left=89)),
            ('outside card height', lambda d, _e: d['point']['cardBounds'].update(bottom=600)),
            ('mouse on card', lambda d, _e: d['mouseDown'].update(card='boundary:43')),
            ('mouse on control', lambda d, _e: d['mouseDown'].update(control=True)),
            ('nonmouse probe', lambda d, _e: d['mouseDown'].update(pointerType='touch')),
            ('DOWN on other card', lambda _d, e: e[0].update(card='boundary:41')),
            ('touchstart on other card', lambda _d, e: e[1].update(card='boundary:41')),
            ('multitouch start', lambda _d, e: e[1].update(touches=2)),
            ('click in canvas', lambda _d, e: e[-1].update(canvas=True)),
            ('click not control', lambda _d, e: e[-1].update(control=False)),
            ('click wrong action', lambda _d, e: e[-1].update(action='delete')),
            ('click not touch', lambda _d, e: e[-1].update(pointerType='mouse', firesTouchEvents=False)),
            ('click no coordinate drift', lambda _d, e: e[-1].update(x=78, y=673.6)),
        )
        for label, mutate in variants:
            with self.subTest(label=label):
                self.assert_rejected(mutate, 'R433_PARSER_RETAINS_TARGET_GUARD: ' + label)

    def test_nonfinite_or_non_numeric_coordinates_are_rejected(self):
        for target in ('point', 'bounds', 'up', 'click'):
            for value in (float('nan'), float('inf'), -float('inf'), True, '78', None):
                with self.subTest(target=target, value=value):
                    def mutate(detail, events, target=target, value=value):
                        destination = {'point': detail['point'], 'bounds': detail['point']['cardBounds'],
                                       'up': events[2], 'click': events[-1]}[target]
                        destination['left' if target == 'bounds' else 'x'] = value
                    self.assert_rejected(mutate, 'R433_PARSER_REJECTS_NONFINITE_COORDINATE')

    def test_new_touch_down_cannot_be_misattributed_to_released_sequence(self):
        for index in (1, 2, 3, 4):
            for trusted in (True, False):
                with self.subTest(index=index, trusted=trusted):
                    def insert(detail, events, index=index, trusted=trusted):
                        independent = copy.deepcopy(events[0])
                        independent.update(pointerId=9, trusted=trusted)
                        events.insert(index, independent)
                        if index < detail['releaseMark']:
                            detail['releaseMark'] += 1
                    self.assert_rejected(insert, 'R433_PARSER_REJECTS_INTERVENING_TOUCH_DOWN')

    def test_extra_touchstart_cannot_be_misattributed_to_released_sequence(self):
        for index in (1, 2, 3, 4):
            for trusted in (True, False):
                with self.subTest(index=index, trusted=trusted):
                    def insert(detail, events, index=index, trusted=trusted):
                        independent = copy.deepcopy(events[1])
                        independent['trusted'] = trusted
                        events.insert(index, independent)
                        if index < detail['releaseMark']:
                            detail['releaseMark'] += 1
                    self.assert_rejected(insert, 'R433_PARSER_REJECTS_EXTRA_TOUCHSTART')


if __name__ == '__main__':
    unittest.main(verbosity=2)
