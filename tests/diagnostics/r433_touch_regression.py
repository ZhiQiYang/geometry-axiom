#!/usr/bin/env python3
"""PR 433 touch repair: exact old-head red, then two real-CDP 0/1/0 proofs.

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
MUTATIONS = (
    ('R433_WITHDRAW_TOUCH_CLICK_OWNERSHIP', RELEASE,
     b'    const owned = consumed.has(event.pointerId) || consumedTouchSequence;',
     b'    const owned = consumed.has(event.pointerId);'),
    ('R433_WITHDRAW_NEW_TOUCH_RESET', DELETE,
     b'      consumedTouchSequence = false;\n', b''),
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


def repair_red(row, marker):
    """Only the specified normal product assertion and trusted input are red."""
    try:
        if (marker not in {RELEASE, DELETE} or row.get('status') != 'assertions'
                or row.get('exit') != 1 or row.get('sourceUnchanged') is not True
                or row.get('runtime', {}).get('fresh') is not True
                or row.get('fatal') != [] or len(row.get('cdp', [])) != 1
                or len(row.get('touch', [])) != 1 or len(row.get('cases', [])) != 1):
            return False
        cdp, touch, case = row['cdp'][0], row['touch'][0], row['cases'][0]
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
                and touch.get('completed') is False and touch.get('failed') == ['LONG_PRESS']
                and touch.get('passed') == [] and len(touch.get('expectedCases', [])) == 16
                and failure.get('assertion') == marker and failure.get('kind') == 'assertion'
                and case.get('id') == 'LONG_PRESS' and case.get('status') == 'fail'
                and case.get('assertions', {}).get('failed') == 1
                and case.get('firstFailure') == failure
                and len(row.get('failed', [])) == 1
                and row['failed'][0].startswith('P1162 ' + marker + ' ✗')):
            return False
        detail = failure.get('detail', {})
        events = detail.get('state', {}).get('events', [])
        if marker == RELEASE:
            mark = detail.get('releaseMark')
            if type(mark) is not int or not 0 <= mark <= len(events):
                return False
            return ordered(events[:mark], (
                lambda e: e.get('type') == 'pointerdown' and e.get('pointerType') == 'touch'
                          and e.get('trusted') is True and e.get('card') == 'boundary:43',
                lambda e: e.get('type') == 'touchstart' and e.get('trusted') is True
                          and e.get('touches') == 1 and e.get('card') == 'boundary:43',
            )) and ordered(events[mark:], (
                lambda e: e.get('type') == 'touchend' and e.get('trusted') is True,
                lambda e: touch_click(e, 'open'),
            ))
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
    cases = ['LONG_PRESS', 'BLANK_EQUIVALENCE', 'SHEET_KEYBOARD', 'SHORT_VIEWPORT',
             'DISABLED_REASON', 'VIEW_ACTION_FOCUS', 'TAP', 'DOUBLE_TAP', 'DRAG',
             'CARD_SECOND_TOUCH', 'TWO_FINGERS', 'RECT_CANCEL', 'CANCEL', 'ESCAPE',
             'STALE_OWNER', 'STALE_NODE']

    def example(marker):
        events = [
            {'type': 'pointerdown', 'pointerType': 'touch', 'trusted': True,
             'card': 'boundary:43' if marker == RELEASE else 'boundary:41'},
            {'type': 'touchstart', 'trusted': True, 'touches': 1,
             'card': 'boundary:43' if marker == RELEASE else 'boundary:41'},
        ]
        if marker == DELETE:
            events += [
                {'type': 'pointerdown', 'pointerType': 'touch', 'trusted': True, 'action': 'delete'},
                {'type': 'touchstart', 'trusted': True, 'touches': 1, 'action': 'delete'},
            ]
        events += [
            {'type': 'touchend', 'trusted': True},
            {'type': 'click', 'trusted': True, 'pointerType': 'touch',
             'action': 'open' if marker == RELEASE else 'delete', 'pointerId': -1, 'x': 83, 'y': 673},
        ]
        failure = {'assertion': marker, 'kind': 'assertion',
                   'detail': {'state': {'events': events}, 'releaseMark': 2}}
        return {
            'status': 'assertions', 'exit': 1, 'sourceUnchanged': True, 'runtime': {'fresh': True},
            'fatal': [], 'failed': ['P1162 ' + marker + ' ✗'],
            'cdp': [{'completed': True, 'unexpectedBrowserExceptions': 0,
                     'scope': {'mode': 'partial', 'filters': ['GEOMETRY_CANVAS_TOUCH_ONLY'],
                               'url': 'http://127.0.0.1:12345/'},
                     'goldenCompare': 'not compared (partial mode)', 'failedAssertions': 1,
                     'sections': {'P1162': 1}, 'sectionsFailed': {'P1162': 1}}],
            'touch': [{'input': 'Input.dispatchTouchEvent', 'scope': 'object-canvas',
                       'completed': False, 'failed': ['LONG_PRESS'], 'passed': [],
                       'expectedCases': cases, 'firstFailure': failure}],
            'cases': [{'id': 'LONG_PRESS', 'status': 'fail',
                       'assertions': {'passed': 1, 'failed': 1}, 'firstFailure': failure}],
        }

    passed = []
    for marker in (RELEASE, DELETE):
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
            ('different case', lambda r: r['touch'][0].update(failed=['BLANK_EQUIVALENCE'])),
            ('other assertion', lambda r: r['touch'][0]['firstFailure'].update(assertion='CONTROL_REACHABLE')),
            ('non assertion', lambda r: r['touch'][0]['firstFailure'].update(kind='infrastructure')),
            ('untrusted events', lambda r: [e.update(trusted=False) for e in r['touch'][0]['firstFailure']['detail']['state']['events']]),
            ('no input', lambda r: r['touch'][0]['firstFailure']['detail']['state'].update(events=[])),
            ('wrong click action', lambda r: r['touch'][0]['firstFailure']['detail']['state']['events'][-1].update(action='home')),
            ('non touch click', lambda r: r['touch'][0]['firstFailure']['detail']['state']['events'][-1].update(pointerType='mouse', firesTouchEvents=False)),
            ('no touch end', lambda r: r['touch'][0]['firstFailure']['detail']['state']['events'].pop(-2)),
        ]
        for label, alter in variants:
            bad = copy.deepcopy(good)
            alter(bad)
            assert not repair_red(bad, marker), marker + ': ' + label
            passed.append(marker + ': rejects ' + label)
        if marker == RELEASE:
            for invalid_mark in (True, '2', 0, 4, 5):
                bad = copy.deepcopy(good)
                bad['touch'][0]['firstFailure']['detail']['releaseMark'] = invalid_mark
                assert not repair_red(bad, marker), 'invalid release boundary: ' + repr(invalid_mark)
                passed.append(marker + ': rejects release boundary ' + repr(invalid_mark))
    green = example(RELEASE)
    green.update(exit=0, failed=[])
    green['cdp'][0].update(failedAssertions=0, sectionsFailed={})
    green['touch'][0].update(completed=True, failed=[], passed=cases, firstFailure=None)
    assert original.green(green)
    green['touch'][0]['passed'] = cases[:-1]
    assert not original.green(green)
    passed += ['original green accepts 16 synthetic cases', 'original green rejects 15 synthetic cases']
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
        'schema': 'geometry-r433-touch-repair/1', 'base': BASE, 'status': 'blocked',
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
        for name, marker, anchor, replacement in MUTATIONS:
            phases = {}
            for phase in ('fixed-before', 'withdrawn', 'restored'):
                source = out / ('source-' + name + '-' + phase)
                original.candidate(source)
                phases[phase] = source
            target = phases['withdrawn'] / PRODUCT
            data = target.read_bytes()
            original.require(data.count(anchor) == 1, name + ': withdrawal anchor must occur exactly once')
            changed = data.replace(anchor, replacement, 1)
            target.write_bytes(changed)
            proof = {'name': name, 'firstFailure': marker, 'path': PRODUCT,
                     'anchor': anchor.decode(), 'replacement': replacement.decode(),
                     'before': identity(original, data), 'after': identity(original, changed),
                     'status': 'blocked'}
            report['proofs'].append(proof)
            fixed = run(name + '-fixed-before', phases['fixed-before'])
            original.require(fixed['sourceUnchanged'] and original.green(fixed),
                             name + ': candidate must pass the original complete 16-case green predicate')
            withdrawn = run(name + '-withdrawn', phases['withdrawn'])
            original.require(repair_red(withdrawn, marker), name + ': not the specified trusted product assertion')
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
