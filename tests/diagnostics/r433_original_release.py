#!/usr/bin/env python3
"""Read-only historical-prefix probe for PR 433's original release report.

The exact e8155a9f test fixture is obtained from git, then augmented only with
observation and a release assertion. Its original LONG_PRESS inputs, blank()
selection order, hold and release remain unchanged. Both products receive the
same historical test bytes. No product source is copied from current into old.
No device input is added or reordered. Observation itself adds CDP reads, which
can affect scheduling; this probe cannot promise to reproduce the old report.
The candidate may be the fixed BASE or a verified descendant containing the
delivered T/P commits. The base never follows a remote branch implicitly.

This is diagnostic evidence, never the 16-case acceptance or a 0/1/0 receipt.
An old release that still preserves the sheet is explicitly blocked. A pass
means only that this historical prefix opened face 43 on old and preserved the
sheet on current. Later failures in the historical suite remain in the report.

  python3 -B tests/diagnostics/r433_original_release.py --self-test
  python3 -B tests/diagnostics/r433_original_release.py \
    --out /tmp/r433-original-prefix --prepare-only
  python3 -B tests/diagnostics/r433_original_release.py \
    --out /tmp/r433-original-replay --binary-dir /tmp/r433-native-cache

The last command delegates to the byte-pinned historical runner, including its
native receipts, isolation, runtime checks and 300-second build/CDP budgets.
--prepare-only starts neither Chrome nor a native build. Prepared snapshots,
overlay diff and fingerprints can be inspected before the cloud replay.
"""
from __future__ import annotations

import argparse
import copy
import difflib
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import types

ROOT = Path(__file__).resolve().parents[2]
OLD = 'e8155a9f006c514c53f4630c49a37c676cf83b87'
BASE = '53516c19db1393fdab109d90a770a07b45646907'
MAIN = '2562aee65c9f21a9ffdfd684100102d764bc2eb4'
TEST = 'geometry-web/canvas_touch_test.js'
CDP = 'geometry-web/cdp_test.js'
DRIVER = 'tests/canvas_touch_regression.py'
MARKER = 'R433_ORIGINAL_RELEASE_PRESERVES_MENU'
TAG = 'R433_ORIGINAL_RELEASE_OBSERVATION'
CASES = ['LONG_PRESS', 'BLANK_EQUIVALENCE', 'SHEET_KEYBOARD', 'SHORT_VIEWPORT',
         'DISABLED_REASON', 'VIEW_ACTION_FOCUS', 'TAP', 'DOUBLE_TAP', 'DRAG',
         'CARD_SECOND_TOUCH', 'TWO_FINGERS', 'RECT_CANCEL', 'CANCEL', 'ESCAPE',
         'STALE_OWNER', 'STALE_NODE']
PINS = {
    TEST: (33251, 'b8cc87291174f540b38d35d0bc5d61f878011414',
           '1d178f1d6b7b94f9d8c7452cf0823e08ff30fec1562e7cd714e51942de1f535a'),
    CDP: (534595, 'add288e9e9b1e311812dc400d2e2d90c27813b5f',
          '86c44ff3ff12aff06cd30a0863d22d5a399cee0dde8032d34302c4dc3f535f57'),
    DRIVER: (17121, '2b973b704f67b43b58bb84fb10779b5b20df9311',
             '171c8e44464bf224ff8dc8c8ddc8cb1fa290ea7abc7ceaba60ffcfcbec89cbda'),
}
OBSERVER_ANCHOR = b'      pointerType:event.pointerType, pointerId:event.pointerId, key:event.key,\n'
OBSERVER_ADDITION = b'''      isPrimary:event.isPrimary, button:event.button, buttons:event.buttons,
      firesTouchEvents:event.sourceCapabilities?.firesTouchEvents ?? null,
      canvas:event.target===document.getElementById('canvasViewport') || !!event.target?.closest?.('#ocv'),
      control:!!event.target?.closest?.('button,input,select,textarea,a,[role="button"],[contenteditable]'),
'''
PREFIX_ANCHOR = b'''  async function blankEquivalence() {
    await fixture(390,844); const p = await blank(), before = await checkpoint();
    await hold(p); const touchModel = await model(); await touch('touchEnd');
'''
PREFIX_REPLACEMENT = b'''  async function blankEquivalence() {
    await fixture(390,844); const p = await blank(), before = await checkpoint();
    // Historical-prefix diagnosis: observation only; no preparatory mouse input.
    const originalGeometry = await read(`(()=>{const h=document.elementFromPoint(${p.x},${p.y});
      return {inside:!!h&&$('canvasViewport').contains(h),card:h?.closest('.ocard')?.dataset.id||null,
        control:!!h?.closest('button,input,select,textarea,[role="button"]')};})()`);
    await hold(p); const touchModel = await model();
    const originalBeforeRelease = await state(), originalReleaseMark = originalBeforeRelease.events.length;
    await touch('touchEnd');
    // Read immediately after the original release. Do not add a wait or another
    // input before the original Escape. A click not observed yet is blocked.
    const originalAfterRelease = await state(), originalAfterModel = await model();
    const originalPreserved = originalAfterRelease.menu.hidden===false && originalAfterRelease.menu.sheet===true &&
      originalAfterRelease.focus===null && same(originalAfterModel,touchModel);
    const originalObservation = {schema:'geometry-r433-original-release-observation/1',point:p,
      geometry:originalGeometry,releaseMark:originalReleaseMark,before:originalBeforeRelease,
      after:originalAfterRelease,beforeModel:touchModel,afterModel:originalAfterModel,preserved:originalPreserved};
    console.log('R433_ORIGINAL_RELEASE_OBSERVATION '+JSON.stringify(originalObservation));
    check('R433_ORIGINAL_RELEASE_CLICK_OBSERVED',originalAfterRelease.events.slice(originalReleaseMark).some(e=>
      e.type==='click'&&e.trusted&&(e.pointerType==='touch'||e.firesTouchEvents===true)),originalObservation);
    check('R433_ORIGINAL_RELEASE_PRESERVES_MENU',originalPreserved,originalObservation);
'''


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def identity(data):
    return {'bytes': len(data),
            'blob': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest(),
            'sha256': hashlib.sha256(data).hexdigest()}


def candidate_allowed(head, ancestor_returncode):
    if not isinstance(head, str) or len(head) != 40 or any(c not in '0123456789abcdef' for c in head):
        return False
    if head == BASE:
        return ancestor_returncode is None
    return type(ancestor_returncode) is int and ancestor_returncode == 0


def git_bytes(reference, path):
    return subprocess.check_output(['git', 'show', reference + ':' + path], cwd=ROOT)


def historical_sources():
    result = {}
    for path, (size, blob, sha256) in PINS.items():
        data = git_bytes(OLD, path)
        require(identity(data) == {'bytes': size, 'blob': blob, 'sha256': sha256},
                'Historical byte pin differs: ' + path)
        require(b'\r' not in data, 'Historical source must be pure LF: ' + path)
        result[path] = data
    return result


def instrument(source):
    require(source.count(OBSERVER_ANCHOR) == 1, 'Historical observer anchor is not unique')
    require(source.count(PREFIX_ANCHOR) == 1, 'Historical blank prefix anchor is not unique')
    result = source.replace(OBSERVER_ANCHOR, OBSERVER_ANCHOR + OBSERVER_ADDITION, 1)
    result = result.replace(PREFIX_ANCHOR, PREFIX_REPLACEMENT, 1)
    # The reversal proves that every historical byte outside these additions is
    # retained, including LONG_PRESS, blank(), input helpers and all assertions.
    restored = result.replace(PREFIX_REPLACEMENT, PREFIX_ANCHOR, 1)
    restored = restored.replace(OBSERVER_ANCHOR + OBSERVER_ADDITION, OBSERVER_ANCHOR, 1)
    require(restored == source, 'Instrumentation changed historical source outside its two anchors')
    require(b'\r' not in result, 'Instrumentation must be pure LF')
    return result


def load_runner(historical):
    # historical_sources() verified its exact bytes/blob/SHA-256 from OLD.
    # Execute those bytes, not the current fragmented runner. __file__ only
    # supplies the real source root; it does not read today's runner or fixture.
    module = types.ModuleType('r433_original_release_runner')
    module.__file__ = str(ROOT / DRIVER)
    exec(compile(historical[DRIVER], module.__file__ + '@' + OLD, 'exec'), module.__dict__)
    require(module.ROOT == ROOT and tuple(module.TEST_OVERLAY) == (CDP, TEST),
            'Unexpected original runner root or test-overlay scope')
    return module


def historical_baseline(original, target):
    """Materialize OLD directly; never call an overlay using retired live paths."""
    target.mkdir()
    tree = subprocess.check_output(['git', 'ls-tree', '-rz', '--full-tree', OLD], cwd=ROOT)
    entries = []
    for entry in tree.split(b'\0'):
        if not entry:
            continue
        metadata, raw_name = entry.split(b'\t', 1)
        mode, kind, object_id = metadata.decode().split()
        name = raw_name.decode()
        if not original.wanted(name) or not (name.split('/')[0] in original.DIRECTORIES or
                name in original.ROOT_FILES or '/' not in name and Path(name).suffix in {'.h', '.inc'}):
            continue
        require(kind == 'blob' and mode in {'100644', '100755'}, 'Unsupported historical source: ' + name)
        entries.append((name, object_id, mode))
    batch = subprocess.run(['git', 'cat-file', '--batch'], cwd=ROOT,
                           input=''.join(oid + '\n' for _, oid, _ in entries).encode(), capture_output=True, check=True)
    stream = io.BytesIO(batch.stdout)
    for name, object_id, mode in entries:
        header = stream.readline().decode().strip().split()
        require(len(header) == 3 and header[:2] == [object_id, 'blob'], 'Missing historical source: ' + name)
        size = int(header[2]); data = stream.read(size)
        require(len(data) == size and stream.read(1) == b'\n' and original.blob(data) == object_id,
                'Invalid historical object bytes: ' + name)
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        path.chmod(int(mode, 8) & 0o777)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def causal_probe(observation):
    """Recognize the original retargeted input, without inventing an ID change."""
    try:
        before, after = observation['before'], observation['after']
        point, geometry = observation['point'], observation['geometry']
        events, mark = after['events'], observation['releaseMark']
        if not (observation.get('schema') == 'geometry-r433-original-release-observation/1'
                and finite(point['x']) and finite(point['y'])
                and geometry == {'inside': True, 'card': None, 'control': False}
                and type(mark) is int and mark > 0 and mark < len(events)
                and before['events'] == events[:mark]
                and before['menu'] == {'hidden': False, 'sheet': True} and before['focus'] is None):
            return False
        prefix, released = events[:mark], events[mark:]
        downs = [e for e in prefix if e.get('type') == 'pointerdown']
        starts = [e for e in prefix if e.get('type') == 'touchstart']
        ups = [e for e in released if e.get('type') == 'pointerup']
        ends = [e for e in released if e.get('type') == 'touchend']
        clicks = [e for e in released if e.get('type') == 'click']
        if len(downs) != 1 or len(starts) != 1 or len(ups) != 1 or len(ends) != 1 or len(clicks) != 1:
            return False
        down, start, up, end, click = downs[0], starts[0], ups[0], ends[0], clicks[0]
        if (any(e.get('type') in {'pointerdown', 'touchstart', 'pointercancel', 'touchcancel'} for e in released)
                or any(e.get('type') in {'mousedown', 'mouseup', 'click'} for e in prefix)):
            return False
        if not (all(e.get('trusted') is True for e in (down, start, up, end, click))
                and down.get('pointerType') == up.get('pointerType') == 'touch'
                and type(down.get('pointerId')) is int and up.get('pointerId') == down['pointerId']
                and down.get('card') == start.get('card') == 'boundary:43'
                and start.get('touches') == 1 and end.get('touches') == 0
                and click.get('action') == 'open' and click.get('canvas') is False
                and (click.get('pointerType') == 'touch' or click.get('firesTouchEvents') is True)
                and all(finite(e.get(k)) for e in (up, click) for k in ('x', 'y'))
                and (up['x'] != click['x'] or up['y'] != click['y'])
                and prefix.index(down) < prefix.index(start)
                and released.index(up) < released.index(end) < released.index(click)):
            return False
        return True
    except (AttributeError, KeyError, TypeError, ValueError, IndexError):
        return False


def classify(row, observations):
    """A normal tagged probe is required; arbitrary nonzero exits are not red."""
    try:
        if not (row.get('status') == 'assertions' and type(row.get('exit')) is int and row['exit'] in {0, 1}
                and row.get('sourceUnchanged') is True
                and row.get('runtime', {}).get('fresh') is True and row.get('fatal') == []
                and len(row.get('cdp', [])) == len(row.get('touch', [])) == 1
                and len(observations) == 1 and len(row.get('cases', [])) >= 2):
            return 'blocked'
        cdp, touch, first, second = row['cdp'][0], row['touch'][0], row['cases'][0], row['cases'][1]
        if not (cdp.get('completed') is True and cdp.get('unexpectedBrowserExceptions') == 0
                and cdp.get('scope', {}).get('mode') == 'partial'
                and cdp.get('scope', {}).get('filters') == ['GEOMETRY_CANVAS_TOUCH_ONLY']
                and cdp.get('goldenCompare') == 'not compared (partial mode)'
                and set(cdp.get('sections', {})) == {'P1162'}
                and touch.get('input') == 'Input.dispatchTouchEvent'
                and touch.get('scope') == 'object-canvas'
                and touch.get('expectedCases') == CASES
                and first.get('id') == 'LONG_PRESS' and first.get('status') == 'pass'
                and first.get('assertions', {}).get('failed') == 0
                and second.get('id') == 'BLANK_EQUIVALENCE'):
            return 'blocked'
        probe = observations[0]
        if not causal_probe(probe):
            return 'blocked'
        preserved = (probe['after']['menu'] == {'hidden': False, 'sheet': True}
                     and probe['after']['focus'] is None
                     and probe['beforeModel'] == probe['afterModel'])
        if probe.get('preserved') is not preserved:
            return 'blocked'
        if preserved:
            # The unmodified historical blank/menu comparison can fail later.
            # Keep that failure visible; it cannot certify full-suite green.
            if (second.get('firstFailure') or {}).get('assertion') == MARKER:
                return 'blocked'
            return 'preserved'
        failure = second.get('firstFailure') or {}
        focus = probe['after'].get('focus') or {}
        if (row.get('exit') == 1 and second.get('status') == 'fail'
                and second.get('assertions', {}).get('failed') == 1
                and cdp.get('failedAssertions') == 1
                and cdp.get('sectionsFailed') == {'P1162': 1}
                and len(row['cases']) == 2 and touch.get('completed') is False
                and touch.get('passed') == ['LONG_PRESS'] and touch.get('failed') == ['BLANK_EQUIVALENCE']
                and len(row.get('failed', [])) == 1 and row['failed'][0].startswith('P1162 ' + MARKER + ' \u2717')
                and touch.get('firstFailure') == failure
                and failure.get('kind') == 'assertion' and failure.get('assertion') == MARKER
                and failure.get('detail') == probe
                and probe['after']['menu'].get('hidden') is True
                and focus.get('t') == 'face' and focus.get('id') == 43):
            return 'opened-face-43'
        return 'blocked'
    except (AttributeError, KeyError, TypeError, ValueError, IndexError):
        return 'blocked'


def pair_verdict(old, current):
    if old == 'opened-face-43' and current == 'preserved':
        return 'pass', 'Historical release reproduced on old; this same probe preserves the sheet on current'
    if old == current == 'preserved':
        return 'blocked', 'Both products preserve the sheet; the original release leak has not been reproduced'
    return 'blocked', 'Required old leak/current preservation pair is absent; other failures cannot replace it'


def same_input(old, current):
    """The same historical program must also have chosen the same physical input."""
    try:
        if any(old[key] != current[key] for key in ('point', 'geometry', 'beforeModel')):
            return False
        keys = ('type', 'trusted', 'pointerType', 'x', 'y', 'touches', 'card', 'action', 'canvas', 'control')
        return ([{key: event.get(key) for key in keys} for event in old['before']['events']] ==
                [{key: event.get(key) for key in keys} for event in current['before']['events']])
    except (AttributeError, KeyError, TypeError):
        return False


def selftest(historical):
    instrument(historical[TEST])
    prefix = [
        {'type': 'pointerdown', 'pointerType': 'touch', 'pointerId': 5, 'trusted': True, 'card': 'boundary:43'},
        {'type': 'touchstart', 'touches': 1, 'trusted': True, 'card': 'boundary:43'},
    ]
    events = prefix + [
        {'type': 'pointerup', 'pointerType': 'touch', 'pointerId': 5, 'trusted': True, 'x': 78, 'y': 673.6},
        {'type': 'touchend', 'touches': 0, 'trusted': True},
        {'type': 'click', 'pointerType': 'touch', 'pointerId': 5, 'trusted': True,
         'action': 'open', 'canvas': False, 'firesTouchEvents': True, 'x': 83, 'y': 673},
    ]
    probe = {'schema': 'geometry-r433-original-release-observation/1', 'point': {'x': 78, 'y': 673.6},
             'geometry': {'inside': True, 'card': None, 'control': False}, 'releaseMark': 2,
             'before': {'events': prefix, 'menu': {'hidden': False, 'sheet': True}, 'focus': None},
             'after': {'events': events, 'menu': {'hidden': False, 'sheet': True}, 'focus': None},
             'beforeModel': {'title': '43'}, 'afterModel': {'title': '43'}, 'preserved': True}
    require(causal_probe(probe), 'Synthetic same-ID precondition was rejected')
    other_id = copy.deepcopy(probe); other_id['after']['events'][-1]['pointerId'] = 105
    require(causal_probe(other_id), 'Pointer ID must not decide retargeted-click causality')
    row = {'status': 'assertions', 'sourceUnchanged': True, 'runtime': {'fresh': True}, 'fatal': [], 'exit': 1,
           'cdp': [{'completed': True, 'unexpectedBrowserExceptions': 0, 'failedAssertions': 1,
                    'sections': {'P1162': 1}, 'sectionsFailed': {'P1162': 1},
                    'scope': {'mode': 'partial', 'filters': ['GEOMETRY_CANVAS_TOUCH_ONLY']},
                    'goldenCompare': 'not compared (partial mode)'}],
           'touch': [{'input': 'Input.dispatchTouchEvent', 'scope': 'object-canvas', 'expectedCases': CASES,
                      'completed': False, 'passed': ['LONG_PRESS'], 'failed': ['BLANK_EQUIVALENCE']}],
           'cases': [{'id': 'LONG_PRESS', 'status': 'pass', 'assertions': {'failed': 0}},
                     {'id': 'BLANK_EQUIVALENCE', 'status': 'fail', 'assertions': {'failed': 1},
                      'firstFailure': {'assertion': 'BLANK_MOUSE_MENU_VISIBLE'}}]}
    require(classify(row, [probe]) == 'preserved', 'Later historical failure hid a preserved prefix')
    opened = copy.deepcopy(probe)
    opened['after'].update(menu={'hidden': True, 'sheet': True}, focus={'t': 'face', 'id': 43})
    opened['preserved'] = False
    red = copy.deepcopy(row)
    failure = {'assertion': MARKER, 'kind': 'assertion', 'detail': opened}
    red['cases'][1]['firstFailure'] = failure; red['touch'][0]['firstFailure'] = failure
    red['failed'] = ['P1162 ' + MARKER + ' \u2717']
    require(classify(red, [opened]) == 'opened-face-43', 'Required synthetic old failure was rejected')
    require(pair_verdict('opened-face-43', 'preserved')[0] == 'pass', 'Required pair was rejected')
    require(pair_verdict('preserved', 'preserved')[0] == 'blocked', 'Same-ID old preservation became success')
    passed_case = copy.deepcopy(row)
    passed_case['cases'][1].update(status='pass', firstFailure=None, assertions={'failed': 0})
    require(classify(passed_case, [probe]) == 'preserved', 'Passed case with a null failure was rejected')
    require(same_input(opened, probe), 'Identical original physical input was rejected')
    other_point = copy.deepcopy(probe); other_point['point']['x'] = 80
    require(not same_input(opened, other_point), 'Different physical point became the same probe')
    descendant = '0123456789abcdef0123456789abcdef01234567'
    require(candidate_allowed(BASE, None), 'Fixed candidate base was rejected')
    require(candidate_allowed(descendant, 0), 'Verified candidate descendant was rejected')
    for head, code in ((descendant, 1), (descendant, 128), (descendant, None),
                       (descendant, False), ('not-a-full-sha', 0)):
        require(not candidate_allowed(head, code), 'Unverified or non-descendant candidate was accepted')
    checks = 17
    for label, change in (
        ('untrusted', lambda p: p['after']['events'][-1].update(trusted=False)),
        ('wrong UP', lambda p: p['after']['events'][2].update(pointerId=6)),
        ('same coordinates', lambda p: p['after']['events'][-1].update(x=78, y=673.6)),
        ('canvas click', lambda p: p['after']['events'][-1].update(canvas=True)),
        ('different action', lambda p: p['after']['events'][-1].update(action='delete')),
        ('no release', lambda p: p['after']['events'].pop(2)),
        ('new DOWN', lambda p: p['after']['events'].insert(3, {'type': 'pointerdown'})),
        ('changed prefix', lambda p: p['before']['events'].append({'type': 'click'})),
    ):
        bad = copy.deepcopy(probe); change(bad)
        require(not causal_probe(bad), 'Accepted synthetic bad precondition: ' + label); checks += 1
    for label, change in (
        ('infra', lambda r: r.update(status='infra')),
        ('source changed', lambda r: r.update(sourceUnchanged=False)),
        ('stale runtime', lambda r: r.update(runtime={'fresh': False})),
        ('browser error', lambda r: r['cdp'][0].update(unexpectedBrowserExceptions=1)),
        ('wrong marker', lambda r: r['cases'][1]['firstFailure'].update(assertion='OTHER')),
        ('wrong exit', lambda r: r.update(exit=2)),
        ('wrong case list', lambda r: r['touch'][0].update(expectedCases=CASES[:-1])),
        ('wrong failure section', lambda r: r['cdp'][0].update(sectionsFailed={'P1162': 2})),
    ):
        bad = copy.deepcopy(red); change(bad)
        require(classify(bad, [opened]) == 'blocked', 'Accepted synthetic bad red: ' + label); checks += 1
    print('R433_ORIGINAL_RELEASE_SELFTEST ' + json.dumps(
        {'status': 'pass', 'synthetic': True, 'chromeStarted': False, 'checks': checks,
         'historicalAnchors': 'unique and reversible', 'historicalPins': PINS}, ensure_ascii=False))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--out', type=Path)
    choice.add_argument('--self-test', action='store_true')
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--binary-dir', type=Path)
    args = parser.parse_args()
    historical = historical_sources()
    original = load_runner(historical)
    if args.self_test:
        require(not args.prepare_only and args.binary_dir is None, '--self-test accepts no execution options')
        return selftest(historical)
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    ancestor_returncode = None
    if head != BASE:
        ancestor_returncode = subprocess.run(
            ['git', 'merge-base', '--is-ancestor', BASE, head], cwd=ROOT, capture_output=True).returncode
    require(candidate_allowed(head, ancestor_returncode),
            'Candidate must equal or descend from the fixed PR head: ' + BASE)
    out, temp = args.out.resolve(), Path(tempfile.gettempdir()).resolve()
    require(temp in out.parents and not out.exists() and ROOT not in out.parents,
            '--out must be a new directory under TEMP, outside the checkout')
    binaries = (args.binary_dir or out / 'binaries').resolve()
    require(temp in binaries.parents and ROOT not in binaries.parents,
            '--binary-dir must be under TEMP, outside the checkout')
    overlay = {CDP: historical[CDP], TEST: instrument(historical[TEST]), DRIVER: historical[DRIVER]}
    out.mkdir(parents=True)
    checkout_before = original.fingerprint(ROOT)
    original.save(out / 'checkout-before.json', checkout_before)
    report = {'schema': 'geometry-r433-original-release-diagnostic/1', 'base': BASE, 'main': MAIN,
              'old': OLD, 'candidateHead': head, 'scope': 'historical-prefix-only', 'status': 'blocked',
              'candidateBaseRelation': 'equal' if head == BASE else 'verified-ancestor',
              'formalAcceptanceEvidence': False, 'mutationEvidence': False,
              'originalDeviceInputOrderPreserved': True, 'observationMayAffectTiming': True,
              'originalDriver': identity(historical[DRIVER]), 'snapshots': [], 'runs': [], 'problems': [],
              'overlay': {path: {'before': identity(historical[path]), 'after': identity(data)}
                          for path, data in overlay.items()}, 'chromeStarted': False}
    try:
        diff = ''.join(difflib.unified_diff(historical[TEST].decode().splitlines(keepends=True),
                                           overlay[TEST].decode().splitlines(keepends=True),
                                           fromfile='a/' + TEST, tofile='b/' + TEST)).encode()
        (out / 'historical-observer.diff').write_bytes(diff)
        report['overlayDiff'] = identity(diff)
        sources = {}
        for label in ('old', 'current'):
            source = out / ('source-' + label)
            if label == 'old':
                historical_baseline(original, source)
            else:
                original.candidate(source)
            before = original.fingerprint(source)
            for path, data in overlay.items():
                (source / path).write_bytes(data)
            after = original.fingerprint(source)
            changed = sorted(path for path in before.keys() | after.keys() if before.get(path) != after.get(path))
            require(set(changed) <= set(overlay), 'Historical overlay changed a product file')
            require((source / DRIVER).read_bytes() == historical[DRIVER], 'Snapshot runner differs from authority')
            for path in ('geometry-web/touch-gestures.js', 'geometry-web/app.js'):
                expected = git_bytes(OLD, path) if label == 'old' else (ROOT / path).read_bytes()
                require((source / path).read_bytes() == expected, 'Product source moved between revisions: ' + path)
            original.save(out / (label + '-prepared-source.json'), after)
            report['snapshots'].append({'label': label, 'root': str(source), 'changedByHistoricalOverlay': changed,
                                        'sourceFingerprint': label + '-prepared-source.json'})
            sources[label] = source
        require(all((sources['old'] / path).read_bytes() == (sources['current'] / path).read_bytes()
                    for path in overlay), 'Products do not share identical historical fixture bytes')
        if args.prepare_only:
            report['status'] = 'prepared'
            report['problems'].append('Not executed: no browser, old red, current green or 0/1/0 has been observed')
        else:
            outcomes = {}
            for label, source in sources.items():
                destination = out / ('run-' + label)
                # The original runner may fail before launching Chrome. A
                # requested replay is not itself proof that Chrome was started.
                if report['chromeStarted'] is False:
                    report['chromeStarted'] = None
                row = original.run(label, source, destination, binaries)
                if row.get('status') == 'assertions':
                    report['chromeStarted'] = True
                source_before = json.loads((destination / 'source-before.json').read_text(encoding='utf-8'))
                source_after = json.loads((destination / 'source-after.json').read_text(encoding='utf-8'))
                row['sourceUnchanged'] = source_before == source_after
                stdout_path = destination / 'stdout.log'
                stdout = stdout_path.read_text(encoding='utf-8', errors='replace') if stdout_path.exists() else ''
                observations = original.tagged(stdout, TAG)
                row['historicalObservations'] = observations
                row['historicalOutcome'] = classify(row, observations)
                row['originalFullSuiteGreen'] = original.green(row)
                original.save(destination / 'historical-result.json', row)
                outcomes[label] = row['historicalOutcome']; report['runs'].append(row)
            report['status'], reason = pair_verdict(outcomes['old'], outcomes['current'])
            if report['status'] == 'pass' and not same_input(
                    report['runs'][0]['historicalObservations'][0], report['runs'][1]['historicalObservations'][0]):
                report['status'], reason = 'blocked', 'Historical fixtures chose different physical input or menu models'
            report['historicalFinding'] = reason
            if report['status'] != 'pass':
                report['problems'].append(reason)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        report['status'] = 'blocked'; report['problems'].append(str(error))
    finally:
        checkout_after = original.fingerprint(ROOT)
        original.save(out / 'checkout-after.json', checkout_after)
        report['checkoutUnchanged'] = checkout_before == checkout_after
        if not report['checkoutUnchanged']:
            report['status'] = 'blocked'; report['problems'].append('Checkout bytes changed during this diagnostic')
        original.save(out / 'summary.json', report)
    print('R433_ORIGINAL_RELEASE_DIAGNOSTIC ' + json.dumps(
        {key: report.get(key) for key in ('status', 'scope', 'formalAcceptanceEvidence', 'mutationEvidence',
                                         'chromeStarted', 'historicalFinding', 'checkoutUnchanged', 'problems')},
        ensure_ascii=False))
    return 0 if report['status'] in {'prepared', 'pass'} else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        print('R433_ORIGINAL_RELEASE_SETUP ' + str(error), file=sys.stderr)
        sys.exit(2)
