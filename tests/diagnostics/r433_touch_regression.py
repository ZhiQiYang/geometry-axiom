#!/usr/bin/env python3
"""PR 433 touch repair: old-head red, two product and one fixture CDP 0/1/0 proofs.

This diagnostic imports the original canvas_touch_regression.py unchanged.
Its snapshot, native build, runtime probe, Chrome execution, 300 s budgets,
16-case green predicate and source checks remain the execution authority.
No Chrome is started by --self-test; those receipts are explicitly synthetic.

Use the formal execution environment's existing GEOMETRY_CHROME and
GEOMETRY_CHROME_FLAGS. This wrapper adds no browser flags.

  python3 -B tests/diagnostics/r433_touch_regression.py \
    --out /tmp/r433-touch-proof --binary-dir /tmp/r433-touch-binaries
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BASE = 'e8155a9f006c514c53f4630c49a37c676cf83b87'
PRODUCT = 'geometry-web/touch-gestures.js'
DRIVER = 'tests/canvas_touch_regression.py'
RELEASE = 'R433_RELEASE_PRESERVES_MENU'
DELETE = 'TOUCH_DELETE_COMPLETED'
BLANK = 'R433_BLANK_TOUCH_TARGET'
TOUCH_TEST = 'geometry-web/canvas_touch_test.js'
CASES = ['LONG_PRESS', 'BLANK_EQUIVALENCE', 'SHEET_KEYBOARD', 'SHORT_VIEWPORT',
         'DISABLED_REASON', 'VIEW_ACTION_FOCUS', 'TAP', 'DOUBLE_TAP', 'DRAG',
         'CARD_SECOND_TOUCH', 'TWO_FINGERS', 'RECT_CANCEL', 'CANCEL', 'ESCAPE',
         'STALE_OWNER', 'STALE_NODE']
MUTATIONS = (
    ('R433_WITHDRAW_TOUCH_CLICK_OWNERSHIP', 'product', PRODUCT, RELEASE,
     b'    const owned = consumed.has(event.pointerId) || consumedTouchSequence;',
     b'    const owned = consumed.has(event.pointerId);'),
    ('R433_WITHDRAW_NEW_TOUCH_RESET', 'product', PRODUCT, DELETE,
     b'      consumedTouchSequence = false;\n', b''),
    ('R433_WITHDRAW_TOUCH_BLANK_FIXTURE', 'fixture', TOUCH_TEST, BLANK,
     b'    const candidate = await prepareBlank();',
     b'    const candidate = await reportedGutterPoint();'),
)


def original_runner():
    spec = importlib.util.spec_from_file_location('r433_original_touch_runner', ROOT / DRIVER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if module.ROOT != ROOT:
        raise RuntimeError('Original runner belongs to another source root')
    return module


def ordered(events, predicates):
    """Witness the physical input sequence without assuming an ID or location."""
    index = 0
    for predicate in predicates:
        while index < len(events) and not predicate(events[index]):
            index += 1
        if index == len(events):
            return False
        index += 1
    return True


def touch_click(event, action):
    return (event.get('type') == 'click' and event.get('trusted') is True
            and event.get('action') == action
            and (event.get('pointerType') == 'touch' or event.get('firesTouchEvents') is True))


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def mouse_blank(point):
    geometry = point.get('geometry', {})
    return (finite_number(point.get('x')) and finite_number(point.get('y'))
            and geometry.get('inside') is True and geometry.get('card') is None
            and geometry.get('control') is False)


def release_witness(detail, events):
    """Witness retargeting from trusted input; click IDs do not prove ownership.

    Chrome 153 can retain the touch pointer ID on its compatibility click.
    Accepting that observation does not establish an old-product failure: the
    exact-old-head run must still fail RELEASE through repair_red below.
    """
    mark = detail.get('releaseMark')
    if type(mark) is not int or not 0 <= mark <= len(events):
        return False
    point, mouse = detail.get('point', {}), detail.get('mouseDown', {})
    bounds = point.get('cardBounds', {})
    if not (mouse_blank(point) and all(finite_number(bounds.get(key)) for key in ('left', 'right', 'top', 'bottom'))
            and 0 < bounds['left'] - point['x'] <= 10
            and bounds['top'] < point['y'] < bounds['bottom']
            and mouse.get('type') == 'pointerdown' and mouse.get('pointerType') == 'mouse'
            and mouse.get('trusted') is True and mouse.get('card') is None
            and mouse.get('control') is False):
        return False
    down_index = next((i for i, e in enumerate(events[:mark]) if e.get('type') == 'pointerdown'
                       and e.get('pointerType') == 'touch' and e.get('trusted') is True), -1)
    down = events[down_index] if down_index >= 0 else {}
    start_index = next((i for i, e in enumerate(events[:mark])
                        if e.get('type') == 'touchstart' and e.get('trusted') is True), -1)
    start = events[start_index] if start_index >= 0 else {}
    up = next((e for e in events[mark:] if e.get('type') == 'pointerup'
               and e.get('pointerType') == 'touch' and e.get('trusted') is True), {})
    end = next((e for e in events[mark:] if e.get('type') == 'touchend' and e.get('trusted') is True), {})
    click_index = next((i for i, e in enumerate(events[mark:], mark) if touch_click(e, 'open')), -1)
    click = events[click_index] if click_index >= 0 else {}
    start_contacts, end_contacts = start.get('changedTouches'), end.get('changedTouches')
    if not (type(down.get('pointerId')) is int and type(up.get('pointerId')) is int
            and up['pointerId'] == down['pointerId']
            and type(start.get('touches')) is int and start['touches'] == 1
            and type(end.get('touches')) is int and end['touches'] == 0
            and isinstance(start_contacts, list) and len(start_contacts) == 1
            and isinstance(end_contacts, list) and len(end_contacts) == 1
            and isinstance(start_contacts[0], dict) and isinstance(end_contacts[0], dict)
            and type(start_contacts[0].get('id')) is int and type(end_contacts[0].get('id')) is int
            and start_contacts[0]['id'] == end_contacts[0]['id']
            and click.get('canvas') is False and click.get('control') is True
            and all(finite_number(event.get(key)) for event in (up, click) for key in ('x', 'y'))
            and (click['x'] != up['x'] or click['y'] != up['y'])):
        return False
    # A later independent touch retires the consumed sequence. Its click must
    # never be misattributed to the earlier release, even when an ID is reused.
    if any(e.get('type') == 'pointerdown' and e.get('pointerType') == 'touch'
           for e in events[down_index + 1:click_index]):
        return False
    if any(e.get('type') == 'touchstart' and i != start_index
           for i, e in enumerate(events[down_index + 1:click_index], down_index + 1)):
        return False
    return ordered(events[:mark], (
        lambda e: e is down and e.get('card') == 'boundary:43',
        lambda e: e is start and e.get('card') == 'boundary:43',
    )) and ordered(events[mark:], (
        lambda e: e is up,
        lambda e: e is end,
        lambda e: e is click,
    ))


def blank_witness(detail):
    """A fixture withdrawal must expose a real mouse/touch target mismatch."""
    point, probes = detail.get('point', {}), detail.get('probes', [])
    if not mouse_blank(point) or len(probes) != 1:
        return False
    probe = probes[0]
    down, start = probe.get('down', {}), probe.get('start', {})
    pointercancel, cancel = probe.get('pointercancel', {}), probe.get('cancel', {})
    if not (probe.get('point') == point and probe.get('trusted') is True
            and down.get('type') == 'pointerdown' and down.get('pointerType') == 'touch'
            and down.get('trusted') is True and down.get('card') == 'boundary:43'
            and down.get('canvas') is True and down.get('control') is False
            and type(down.get('pointerId')) is int
            and start.get('type') == 'touchstart' and start.get('trusted') is True
            and start.get('touches') == 1 and start.get('card') == 'boundary:43'
            and start.get('canvas') is True and start.get('control') is False
            and pointercancel.get('type') == 'pointercancel' and pointercancel.get('pointerType') == 'touch'
            and pointercancel.get('trusted') is True and pointercancel.get('pointerId') == down['pointerId']
            and cancel.get('type') == 'touchcancel' and cancel.get('trusted') is True):
        return False
    return ordered(probe.get('events', []), (
        lambda e: e == down, lambda e: e == start,
        lambda e: e == pointercancel, lambda e: e == cancel,
    ))


def repair_red(row, marker):
    """Only the specified normal assertion with its causal trusted input is red."""
    try:
        expected_case = 'BLANK_EQUIVALENCE' if marker == BLANK else 'LONG_PRESS'
        passed_cases = ['LONG_PRESS'] if marker == BLANK else []
        if (marker not in {RELEASE, DELETE, BLANK} or row.get('status') != 'assertions'
                or row.get('exit') != 1 or row.get('sourceUnchanged') is not True
                or row.get('runtime', {}).get('fresh') is not True
                or row.get('fatal') != [] or len(row.get('cdp', [])) != 1
                or len(row.get('touch', [])) != 1 or len(row.get('cases', [])) != len(passed_cases) + 1):
            return False
        cdp, touch, case = row['cdp'][0], row['touch'][0], row['cases'][-1]
        failure = touch.get('firstFailure') or {}
        if not (cdp.get('completed') is True and cdp.get('unexpectedBrowserExceptions') == 0
                and cdp.get('scope', {}).get('mode') == 'partial'
                and cdp.get('scope', {}).get('filters') == ['GEOMETRY_CANVAS_TOUCH_ONLY']
                and cdp.get('goldenCompare') == 'not compared (partial mode)'
                and cdp.get('failedAssertions') == 1
                and set(cdp.get('sections', {})) == {'P1162'}
                and cdp.get('sectionsFailed') == {'P1162': 1}
                and touch.get('input') == 'Input.dispatchTouchEvent'
                and touch.get('scope') == 'object-canvas'
                and touch.get('completed') is False and touch.get('failed') == [expected_case]
                and touch.get('passed') == passed_cases and touch.get('expectedCases') == CASES
                and failure.get('assertion') == marker and failure.get('kind') == 'assertion'
                and case.get('id') == expected_case and case.get('status') == 'fail'
                and case.get('assertions', {}).get('failed') == 1
                and case.get('firstFailure') == failure
                and all(prior.get('id') == name and prior.get('status') == 'pass'
                        and prior.get('assertions', {}).get('failed') == 0
                        for prior, name in zip(row['cases'][:-1], passed_cases))
                and len(row.get('failed', [])) == 1
                and row['failed'][0].startswith('P1162 ' + marker + ' ✗')):
            return False
        detail = failure.get('detail', {})
        events = detail.get('state', {}).get('events', [])
        if marker == RELEASE:
            return release_witness(detail, events)
        if marker == BLANK:
            return blank_witness(detail)
        return ordered(events, (
            lambda e: e.get('type') == 'pointerdown' and e.get('pointerType') == 'touch'
                      and e.get('trusted') is True and e.get('card') == 'boundary:41',
            lambda e: e.get('type') == 'pointerdown' and e.get('pointerType') == 'touch'
                      and e.get('trusted') is True and e.get('action') == 'delete',
            lambda e: e.get('type') == 'touchstart' and e.get('trusted') is True
                      and e.get('touches') == 1 and e.get('action') == 'delete',
            lambda e: e.get('type') == 'touchend' and e.get('trusted') is True,
            lambda e: touch_click(e, 'delete'),
        ))
    except (AttributeError, KeyError, TypeError, ValueError, IndexError):
        return False


def same_source(original, output, row):
    before = json.loads((output / 'source-before.json').read_text(encoding='utf-8'))
    after = json.loads((output / 'source-after.json').read_text(encoding='utf-8'))
    row['sourceUnchanged'] = before == after
    if not row['sourceUnchanged']:
        row['status'] = 'infra'
        row['error'] = 'Snapshot source bytes changed during the original run'
    original.save(output / 'result.json', row)
    return row


def identity(original, raw):
    return {'bytes': len(raw), 'blob': original.blob(raw), 'sha256': original.sha(raw)}


def predicate_selftest(original):
    """Synthetic predicate checks only; never a Chrome or mutation receipt."""
    def example(marker):
        point = {'x': 78, 'y': 673.6,
                 'geometry': {'inside': True, 'card': None, 'control': False, 'target': 'DIV'},
                 'cardBounds': {'left': 80, 'right': 380, 'top': 496, 'bottom': 736}}
        events = [
            {'type': 'pointerdown', 'pointerType': 'touch', 'trusted': True, 'pointerId': 7,
             'x': 78, 'y': 673.6, 'canvas': True, 'control': False,
             'card': 'boundary:41' if marker == DELETE else 'boundary:43'},
            {'type': 'touchstart', 'trusted': True, 'touches': 1, 'canvas': True, 'control': False,
             'card': 'boundary:41' if marker == DELETE else 'boundary:43', 'changedTouches': [{'id': 1}]},
        ]
        if marker == BLANK:
            events += [
                {'type': 'pointercancel', 'pointerType': 'touch', 'trusted': True, 'pointerId': 7},
                {'type': 'touchcancel', 'trusted': True, 'touches': 0},
            ]
            detail = {'point': point, 'probes': [{'point': point, 'trusted': True,
                      'down': events[0], 'start': events[1], 'pointercancel': events[2],
                      'cancel': events[3], 'events': events}]}
        else:
            if marker == DELETE:
                events += [
                    {'type': 'pointerdown', 'pointerType': 'touch', 'trusted': True, 'action': 'delete'},
                    {'type': 'touchstart', 'trusted': True, 'touches': 1, 'action': 'delete'},
                ]
            events += [
                {'type': 'pointerup', 'pointerType': 'touch', 'trusted': True, 'pointerId': 7, 'x': 78, 'y': 673.6},
                {'type': 'touchend', 'trusted': True, 'touches': 0, 'changedTouches': [{'id': 1}]},
                {'type': 'click', 'trusted': True, 'pointerType': 'touch', 'canvas': False,
                 'control': True, 'firesTouchEvents': True,
                 'action': 'open' if marker == RELEASE else 'delete', 'pointerId': 7, 'x': 83, 'y': 673},
            ]
            detail = {'state': {'events': events}, 'releaseMark': 2, 'point': point,
                      'mouseDown': {'type': 'pointerdown', 'pointerType': 'mouse', 'trusted': True,
                                    'x': 78, 'y': 673.6, 'card': None, 'control': False}}
        failure = {'assertion': marker, 'kind': 'assertion', 'detail': detail}
        previous = ['LONG_PRESS'] if marker == BLANK else []
        failed_case = 'BLANK_EQUIVALENCE' if marker == BLANK else 'LONG_PRESS'
        return {
            'status': 'assertions', 'exit': 1, 'sourceUnchanged': True, 'runtime': {'fresh': True},
            'fatal': [], 'failed': ['P1162 ' + marker + ' ✗'],
            'cdp': [{'completed': True, 'unexpectedBrowserExceptions': 0,
                     'scope': {'mode': 'partial', 'filters': ['GEOMETRY_CANVAS_TOUCH_ONLY'],
                               'url': 'http://127.0.0.1:12345/'},
                     'goldenCompare': 'not compared (partial mode)', 'failedAssertions': 1,
                     'sections': {'P1162': 1}, 'sectionsFailed': {'P1162': 1}}],
            'touch': [{'input': 'Input.dispatchTouchEvent', 'scope': 'object-canvas',
                       'completed': False, 'failed': [failed_case], 'passed': previous,
                       'expectedCases': CASES, 'firstFailure': failure}],
            'cases': [{'id': name, 'status': 'pass', 'assertions': {'passed': 1, 'failed': 0}}
                      for name in previous] + [{'id': failed_case, 'status': 'fail',
                      'assertions': {'passed': 1, 'failed': 1}, 'firstFailure': failure}],
        }

    def details(row):
        return row['touch'][0]['firstFailure']['detail']

    def observed(row):
        detail = details(row)
        return detail['probes'][0]['events'] if 'probes' in detail else detail['state']['events']

    passed = []
    for marker in (RELEASE, DELETE, BLANK):
        good = example(marker)
        assert repair_red(good, marker), marker
        passed.append(marker + ': accepts required trusted assertion')
        variants = [
            ('infra', lambda r: r.update(status='infra')),
            ('timeout', lambda r: r.update(status='infra', exit=None, error='CDP exceeded 300 s')),
            ('fatal', lambda r: r.update(fatal=['FATAL: transport failed'])),
            ('changed source', lambda r: r.update(sourceUnchanged=False)),
            ('stale runtime', lambda r: r.update(runtime={'fresh': False})),
            ('wrong exit', lambda r: r.update(exit=2)),
            ('two failures', lambda r: r['cdp'][0].update(failedAssertions=2)),
            ('incomplete CDP', lambda r: r['cdp'][0].update(completed=False)),
            ('browser exception', lambda r: r['cdp'][0].update(unexpectedBrowserExceptions=1)),
            ('wrong scope', lambda r: r['cdp'][0].update(scope={'mode': 'full'})),
            ('different case', lambda r: r['touch'][0].update(failed=['STALE_NODE'])),
            ('missing required cases', lambda r: r['touch'][0].update(expectedCases=CASES[:-1])),
            ('other assertion', lambda r: r['touch'][0]['firstFailure'].update(assertion='CONTROL_REACHABLE')),
            ('non assertion', lambda r: r['touch'][0]['firstFailure'].update(kind='infrastructure')),
            ('untrusted events', lambda r: [e.update(trusted=False) for e in observed(r)]),
            ('no input', lambda r: observed(r).clear()),
        ]
        if marker != BLANK:
            variants += [
                ('wrong click action', lambda r: observed(r)[-1].update(action='home')),
                ('non touch click', lambda r: observed(r)[-1].update(pointerType='mouse', firesTouchEvents=False)),
                ('no touch end', lambda r: observed(r).pop(-2)),
            ]
        if marker == RELEASE:
            variants += [
                ('card-interior mouse fixture', lambda r: details(r)['point']['geometry'].update(card='boundary:43')),
                ('raw point inside card bounds', lambda r: details(r)['point']['cardBounds'].update(left=78)),
                ('untrusted mouse', lambda r: details(r)['mouseDown'].update(trusted=False)),
                ('mouse actually hit card', lambda r: details(r)['mouseDown'].update(card='boundary:43')),
                ('same UP and click coordinates', lambda r: observed(r)[-1].update(x=78, y=673.6)),
                ('click remains in canvas', lambda r: observed(r)[-1].update(canvas=True)),
                ('click does not hit control', lambda r: observed(r)[-1].update(control=False)),
                ('new touch DOWN during release', lambda r: observed(r).insert(3, copy.deepcopy(observed(r)[0]))),
                ('untrusted touch DOWN during release', lambda r: observed(r).insert(3, dict(observed(r)[0], trusted=False))),
                ('extra touchstart during release', lambda r: observed(r).insert(3, copy.deepcopy(observed(r)[1]))),
                ('touch remains at end', lambda r: observed(r)[3].update(touches=1)),
                ('missing start contact', lambda r: observed(r)[1].pop('changedTouches')),
                ('missing end contact', lambda r: observed(r)[3].pop('changedTouches')),
                ('two start contacts', lambda r: observed(r)[1]['changedTouches'].append({'id': 2})),
                ('two end contacts', lambda r: observed(r)[3]['changedTouches'].append({'id': 2})),
                ('different end contact', lambda r: observed(r)[3]['changedTouches'][0].update(id=2)),
                ('missing start identifier', lambda r: observed(r)[1]['changedTouches'][0].pop('id')),
                ('missing UP', lambda r: observed(r).pop(2)),
                ('wrong UP pointer ID', lambda r: observed(r)[2].update(pointerId=9)),
                ('nonfinite click coordinate', lambda r: observed(r)[-1].update(x=float('nan'))),
            ]
        if marker == BLANK:
            variants += [
                ('unpassed earlier case', lambda r: r['touch'][0].update(passed=[])),
                ('failed earlier case', lambda r: r['cases'][0].update(status='fail')),
                ('geometry was not blank', lambda r: details(r)['point']['geometry'].update(card='boundary:43')),
                ('touch was also blank', lambda r: observed(r)[0].update(card=None)),
                ('inconsistent start target', lambda r: observed(r)[1].update(card='boundary:42')),
                ('missing pointercancel', lambda r: observed(r).pop(2)),
                ('untrusted cancellation', lambda r: observed(r)[-1].update(trusted=False)),
                ('wrong cancellation pointer ID', lambda r: observed(r)[2].update(pointerId=9)),
                ('more than one probe', lambda r: details(r)['probes'].append(details(r)['probes'][0])),
            ]
        for label, alter in variants:
            bad = copy.deepcopy(good)
            alter(bad)
            assert not repair_red(bad, marker), marker + ': ' + label
            passed.append(marker + ': rejects ' + label)
        if marker == RELEASE:
            for click_id in (107, None):
                alternate = copy.deepcopy(good)
                click = observed(alternate)[-1]
                if click_id is None:
                    click.pop('pointerId')
                else:
                    click['pointerId'] = click_id
                assert repair_red(alternate, marker), 'click pointer ID is observation only: ' + repr(click_id)
                passed.append(marker + ': accepts observed click pointer ID ' + repr(click_id))
            for invalid_mark in (True, '2', 0, 3, 4, 5):
                bad = copy.deepcopy(good)
                bad['touch'][0]['firstFailure']['detail']['releaseMark'] = invalid_mark
                assert not repair_red(bad, marker), 'invalid release boundary: ' + repr(invalid_mark)
                passed.append(marker + ': rejects release boundary ' + repr(invalid_mark))
    green = example(RELEASE)
    green.update(exit=0, failed=[])
    green['cdp'][0].update(failedAssertions=0, sectionsFailed={})
    green['touch'][0].update(completed=True, failed=[], passed=CASES, firstFailure=None)
    assert original.green(green)
    green['touch'][0]['passed'] = CASES[:-1]
    assert not original.green(green)
    passed += ['original green accepts 16 synthetic cases', 'original green rejects 15 synthetic cases']
    for name, _kind, path, _marker, anchor, _replacement in MUTATIONS:
        assert (ROOT / path).read_bytes().count(anchor) == 1, name + ': unique source anchor'
        passed.append(name + ': unique source anchor (not executed)')
    print('R433_TOUCH_PREDICATE_SELFTEST ' + json.dumps(
        {'synthetic': True, 'chromeStarted': False, 'checks': len(passed), 'status': 'pass',
         'cases': passed}, ensure_ascii=False))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--out', type=Path)
    choice.add_argument('--self-test', action='store_true')
    parser.add_argument('--binary-dir', type=Path)
    args = parser.parse_args()
    original = original_runner()
    if args.self_test:
        return predicate_selftest(original)

    out, temp = args.out.resolve(), Path(tempfile.gettempdir()).resolve()
    original.require(temp in out.parents and not out.exists() and ROOT not in out.parents,
                     '--out must be a new directory under TEMP, outside the repository')
    binaries = (args.binary_dir or out / 'binaries').resolve()
    original.require(temp in binaries.parents and ROOT not in binaries.parents,
                     '--binary-dir must be under TEMP, outside the repository')
    old_driver = subprocess.check_output(['git', 'show', BASE + ':' + DRIVER], cwd=ROOT)
    original.require((ROOT / DRIVER).read_bytes() == old_driver,
                     'The original R11 registration runner must remain unchanged')
    out.mkdir(parents=True)
    checkout_before = original.fingerprint(ROOT)
    original.save(out / 'checkout-before.json', checkout_before)
    report = {
        'schema': 'geometry-r433-touch-repair/2', 'base': BASE, 'status': 'blocked',
        'originalDriver': identity(original, old_driver), 'runs': [], 'proofs': [], 'problems': [],
        'candidateHead': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'testOverlay': {name: identity(original, (ROOT / name).read_bytes()) for name in original.TEST_OVERLAY},
    }

    def run(label, source):
        destination = out / ('run-' + label)
        row = original.run(label, source, destination, binaries)
        row = same_source(original, destination, row)
        report['runs'].append(row)
        original.require(row['status'] == 'assertions', label + ': infrastructure cannot count as red')
        return row

    try:
        before_root = out / 'source-before'
        original.baseline(before_root, BASE)
        original.require(all((before_root / name).read_bytes() == (ROOT / name).read_bytes()
                             for name in original.TEST_OVERLAY), 'Baseline must use the identical T harness')
        baseline = run('before', before_root)
        original.require(repair_red(baseline, RELEASE), 'Exact old head did not reach ' + RELEASE)
        for name, kind, path, marker, anchor, replacement in MUTATIONS:
            phases = {}
            for phase in ('fixed-before', 'withdrawn', 'restored'):
                source = out / ('source-' + name + '-' + phase)
                original.candidate(source)
                phases[phase] = source
            target = phases['withdrawn'] / path
            data = target.read_bytes()
            original.require(data.count(anchor) == 1, name + ': withdrawal anchor must occur exactly once')
            changed = data.replace(anchor, replacement, 1)
            target.write_bytes(changed)
            proof = {'name': name, 'kind': kind, 'firstFailure': marker, 'path': path,
                     'anchor': anchor.decode(), 'replacement': replacement.decode(),
                     'before': identity(original, data), 'after': identity(original, changed),
                     'status': 'blocked'}
            report['proofs'].append(proof)
            fixed = run(name + '-fixed-before', phases['fixed-before'])
            original.require(fixed['sourceUnchanged'] and original.green(fixed),
                             name + ': candidate must pass the original complete 16-case green predicate')
            withdrawn = run(name + '-withdrawn', phases['withdrawn'])
            original.require(repair_red(withdrawn, marker), name + ': not the specified trusted ' + kind + ' assertion')
            restored = run(name + '-restored', phases['restored'])
            original.require(restored['sourceUnchanged'] and original.green(restored),
                             name + ': restored candidate must pass the original complete 16-case green predicate')
            original.require(original.fingerprint(phases['fixed-before']) == original.fingerprint(phases['restored']),
                             name + ': restored snapshot is not byte-for-byte identical')
            proof.update(status='pass', sequence=[fixed['exit'], withdrawn['exit'], restored['exit']],
                         sourceRestoredByteForByte=True)
        report['status'] = 'pass'
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        report['problems'].append(str(error))
    finally:
        checkout_after = original.fingerprint(ROOT)
        original.save(out / 'checkout-after.json', checkout_after)
        report['checkoutUnchanged'] = checkout_before == checkout_after
        if not report['checkoutUnchanged']:
            report['status'] = 'blocked'
            report['problems'].append('Source checkout bytes changed during the proof')
        original.save(out / 'summary.json', report)
    print('R433_TOUCH_REPAIR ' + json.dumps(
        {key: report.get(key) for key in ('status', 'base', 'proofs', 'checkoutUnchanged', 'problems')},
        ensure_ascii=False))
    if report['status'] == 'pass':
        return 0
    return 2 if not report['runs'] or any(row.get('status') == 'infra' for row in report['runs']) else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        print('R433_TOUCH_REPAIR_SETUP ' + str(error), file=sys.stderr)
        sys.exit(2)
