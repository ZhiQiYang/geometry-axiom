#!/usr/bin/env python3
"""Fragmented R433 sheet-own-scroll Chrome withdrawal; never edits the checkout.

This reuses the reviewed, byte-pinned fragmented registration candidate/run/green.
Product/native sources stay pinned to the reviewed 82b7b765 PR head, with only
the exact 16 copied R13 paths adopted from the reviewed main 883e6868 merge.
Its three *candidate* snapshots are baseline/control, withdrawn, restored.
It is NOT the registration runner's historical-baseline 1/0/1/0 experiment.
Only the withdrawn snapshot loses the one sheet-own-scroll guard. No harness,
case, assertion, 500 ms / 8 px constant, browser flag or timeout is changed.

  python3 -B tests/diagnostics/r433_sheet_own_scroll.py --root /path/repo --self-test
  GEOMETRY_CHROME=/absolute/path/chrome LANG=C.UTF-8 \
    python3 -B tests/diagnostics/r433_sheet_own_scroll.py --root /path/repo \
      --out /tmp/r433-own-scroll-NEW --binary-dir /tmp/r433-native-cache

Keep the execution environment's existing GEOMETRY_CHROME_FLAGS. The original
runner keeps its 300-second build/CDP budgets and creates isolated services,
feedback directories and Chrome profiles. A new TEMP output directory is
required. Native cache reuse is judged by the original registry on every run.
--self-test is synthetic: it starts neither Chrome nor a native build.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
BASE = '82b7b76526ab9e926ac2d6eb4e3f3de1163155b5'
MERGED_MAIN = '883e68688f6480a5f1de6e86e6a056cc20339cb9'
MERGED_MAIN_PARENT = 'e0db7e478f15df4a90ea130ad17d74406db75586'
MAIN_SOURCE_PATHS = (
    'geometry-core/card-reference/run_axiom_mutations.py',
    'geometry-core/domain-decoupling/product-architecture.d/exclusions/geometry-core/card-reference/run_axiom_mutations.py.json',
    'geometry-core/modeling/__init__.py',
    'geometry-guide/公理層-白話.md',
    'geometry-guide/公理層-閱讀器.html',
    'tests/fixtures/q38j-b-native-model.json',
    'tests/fixtures/r13-approved-delta.json',
    'tests/fixtures/r13-main-3ef07683/card.json',
    'tests/fixtures/r13-main-3ef07683/profile.json',
    'tests/fixtures/r13-main-3ef07683/provenance.json',
    'tests/fixtures/r13-main-3ef07683/stagger.json',
    'tests/make_r13_approved_delta.py',
    'tests/mutation_r14_repeat_panel.py',
    'tests/test_domain_decoupling_adoption.py',
    'tests/test_engineering_model_compatibility.py',
    '公理層.md',
)
NAME = 'R433_WITHDRAW_SHEET_OWN_SCROLL_GUARD'
DRIVER = 'tests/canvas_touch_regression.py'
PRODUCT = 'geometry-web/touch-gestures.js'
ANCHOR = b"if (g.phase === 'menu' && sheet?.contains(event.target)) return;"
REPLACEMENT = b"if (false && sheet?.contains(event.target)) return;"
MARKER = 'LONG_PRESS_OPENS_MENU'
CASES = ['LONG_PRESS', 'BLANK_EQUIVALENCE', 'SHEET_KEYBOARD', 'SHORT_VIEWPORT',
         'DISABLED_REASON', 'VIEW_ACTION_FOCUS', 'TAP', 'DOUBLE_TAP', 'DRAG',
         'CARD_SECOND_TOUCH', 'TWO_FINGERS', 'RECT_CANCEL', 'CANCEL', 'ESCAPE',
         'STALE_OWNER', 'STALE_NODE']
PIN_PATHS = (PRODUCT, 'geometry-web/cdp_helpers.js',
             'geometry-web/app.js', 'geometry-web/app.css', 'geometry-web/index.html',
             'geometry-web/context-menu-shell.js', 'geometry-web/canvas-context-menu.js',
             'geometry-web/face-context-menu.css', 'geometry-web/start_local.py',
             'geometry-web/runtime_version.py', 'tests/binaries.py')
DRIVER_SHA256 = '9cdc391b89b20a4737b47fba03c35704e8130979badb3b5c3c8d9fad225e227b'
REVIEWED_TEST_SHA256 = {
    DRIVER: DRIVER_SHA256,
    'geometry-web/cdp_test.js': 'df33995488e0b4d2e938ffb4b5da86b192d81c436b232c1e8d423d89b3298fbb',
    'geometry-web/canvas_sections/P1162.js': 'b815719fd7e81ed48a9befc10bb2b6ee9e0f4d8c35962d634973372ec835d6c8',
}
NATIVE = ('core', 'bridge', 'model-base')
SELECTION = [{'kind': 'boundary', 'id': 41}, {'kind': 'boundary', 'id': 42}]
ADOPTION_PATHS = {
    DRIVER, 'geometry-web/cdp_test.js', 'geometry-web/canvas_touch_test.js',
    'geometry-web/canvas_sections/P1162.js', 'geometry-web/cdp_sections.d/P1162.json',
    'tests/diagnostics/r433_touch_regression.py', 'tests/diagnostics/r433_original_release.py',
    'tests/diagnostics/r433_touch_probe_test.cjs', 'tests/diagnostics/r433_sheet_own_scroll.py',
    'tests/diagnostics/r433_fragment_contract_test.cjs', 'tests/diagnostics/test_r433_fragment_runners.py',
    'tests/diagnostics/test_r433_main_projection.py',
    'geometry-core/domain-decoupling/product-architecture.d/exclusions/geometry-web/canvas_touch_test.js.json',
    'geometry-core/domain-decoupling/product-architecture.d/exclusions/geometry-web/canvas_sections/P1162.js.json',
}



def require(value, message):
    if not value:
        raise RuntimeError(message)


def identity(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
            'blob': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()}


def file_identity(path):
    digest = hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
            size += len(block)
    return {'bytes': size, 'sha256': digest.hexdigest()}


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pinned_runner(root):
    # A caller cannot silently replace the fixed reference with its current HEAD.
    pins = {}
    for path in PIN_PATHS:
        raw = subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=root)
        require((root / path).read_bytes() == raw, 'Fixed-base source pin differs: ' + path)
        pins[path] = identity(raw)
    for path, sha256 in REVIEWED_TEST_SHA256.items():
        raw = (root / path).read_bytes()
        require(identity(raw)['sha256'] == sha256, 'Reviewed fragmented test source pin differs: ' + path)
        pins[path] = identity(raw)
    require(pins[DRIVER]['sha256'] == DRIVER_SHA256, 'Original execution authority pin differs')
    original = load_module(root / DRIVER, 'r433_own_scroll_original')
    require(original.ROOT == root, 'Original runner belongs to a different root')
    return original, pins


def fixed_source_tree(root, original, reference=BASE):
    """Pin all copied source bytes; only the reviewed fragment conversion may differ."""
    raw = subprocess.check_output(['git', 'ls-tree', '-rz', '--full-tree', reference], cwd=root)
    expected = {}
    for entry in raw.split(b'\0'):
        if not entry:
            continue
        metadata, path = entry.split(b'\t', 1)
        mode, kind, blob = metadata.decode().split()
        path = path.decode('utf-8')
        if (not original.wanted(path)
                or not (path.split('/')[0] in original.DIRECTORIES or path in original.ROOT_FILES
                        or '/' not in path and Path(path).suffix in {'.h', '.inc'})):
            continue
        require(kind == 'blob' and mode in {'100644', '100755'}, 'Unsupported fixed source entry: ' + path)
        expected[path] = blob
    return expected


def verified_main_projection(root, original, fixed, control):
    """Permit the named ordinary merge only at its exact before/after blobs."""
    before = fixed_source_tree(root, original, MERGED_MAIN_PARENT)
    after = fixed_source_tree(root, original, MERGED_MAIN)
    changed = tuple(sorted(name for name in before.keys() | after.keys()
                           if before.get(name) != after.get(name)))
    require(changed == MAIN_SOURCE_PATHS, 'R433_MERGED_MAIN_EXACT_PATH_SET')
    paths = {}
    for name in MAIN_SOURCE_PATHS:
        require(fixed.get(name) == before.get(name),
                'R433_MERGED_MAIN_BEFORE_PIN: ' + name)
        require(control.get(name, {}).get('blob') == after.get(name),
                'R433_MERGED_MAIN_SOURCE_PIN: ' + name)
        paths[name] = {'before': before.get(name), 'after': after.get(name)}
    return {'main': MERGED_MAIN, 'parent': MERGED_MAIN_PARENT, 'paths': paths}


def integer(value, minimum=0):
    return type(value) is int and value >= minimum


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def clean_result(row):
    try:
        cdp, touch = row['cdp'][0], row['touch'][0]
        return (row['status'] == 'assertions' and row.get('sourceUnchanged') is True
                and row.get('runtime', {}).get('fresh') is True and row.get('fatal') == []
                and not row.get('error') and len(row['cdp']) == len(row['touch']) == 1
                and cdp.get('completed') is True
                and type(cdp.get('unexpectedBrowserExceptions')) is int
                and cdp['unexpectedBrowserExceptions'] == 0
                and type(cdp.get('uncaughtBrowserExceptions')) is int
                and cdp['uncaughtBrowserExceptions'] == 0
                and cdp.get('scope', {}).get('mode') == 'partial'
                and cdp['scope'].get('filters') == ['GEOMETRY_CANVAS_MODULE_ONLY']
                and cdp['scope'].get('module') == 'P1162'
                and cdp['scope'].get('modifiers') == [] and cdp['scope'].get('acceptance') is False
                and cdp.get('goldenCompare') == 'not compared (partial mode)'
                and set(cdp.get('sections', {})) == {'P1162'}
                and integer(cdp['sections']['P1162'], 1)
                and cdp.get('passedAssertions') == cdp['sections']['P1162']
                and touch.get('input') == 'Input.dispatchTouchEvent'
                and touch.get('scope') == 'object-canvas' and touch.get('expectedCases') == CASES)
    except (KeyError, IndexError, TypeError, AttributeError):
        return False


def green(row, original):
    try:
        if not clean_result(row) or not original.green(row):
            return False
        cases, cdp = row['cases'], row['cdp'][0]
        return (type(row['exit']) is int and row['exit'] == 0
                and type(cdp.get('failedAssertions')) is int and cdp['failedAssertions'] == 0
                and cdp.get('sectionsFailed', {}) == {} and row['touch'][0].get('firstFailure') is None
                and len(cases) == len(CASES)
                and all(case.get('id') == name and case.get('status') == 'pass'
                        and integer(case.get('assertions', {}).get('passed'), 1)
                        and type(case['assertions'].get('failed')) is int
                        and case['assertions']['failed'] == 0 and not case.get('firstFailure')
                        for case, name in zip(cases, CASES)))
    except (KeyError, IndexError, TypeError, AttributeError):
        return False


def own_scroll_witness(state):
    """Require this defect's causal trace, not just an assertion of the same name."""
    try:
        events, menus = state['events'], state['menus']
        downs = [e for e in events if e.get('type') == 'pointerdown']
        starts = [e for e in events if e.get('type') == 'touchstart']
        scrolls = [e for e in events if e.get('type') == 'scroll']
        if len(downs) != 1 or len(starts) != 1 or not scrolls or len(menus) != 1:
            return False
        down, start, scroll, menu = downs[0], starts[0], scrolls[0], menus[0]
        prepared = down.get('preDispatch') or {}
        if not (down.get('pointerType') == 'touch' and integer(down.get('pointerId'))
                and all(e.get('trusted') is True for e in (down, start, scroll))
                and down.get('defaultPrevented') is True and down.get('lateWindowCapture') is False
                and down.get('card') == start.get('card') == 'boundary:41'
                and down.get('canvas') is True and down.get('control') is False
                and start.get('touches') == 1 and prepared.get('selection') == SELECTION
                and prepared.get('sel') is None and prepared.get('focus') is None
                and prepared.get('tool') == 'select' and not prepared.get('drawTool')
                and prepared.get('on') is True and prepared.get('view3') is False
                and prepared.get('hidden') is False and prepared.get('card') is False
                and prepared.get('pan') is False and prepared.get('marquee') is False
                and prepared.get('dialogs') == [] and prepared.get('owner', {}).get('phase') == 'ready'
                and scroll.get('target') == 'canvasCtxMenu' and menu.get('sheet') is True
                and all(number(v) for v in (down.get('at'), down.get('timestamp'),
                                            start.get('at'), menu.get('at'), scroll.get('at')))
                and down['at'] <= start['at'] <= menu['at'] <= scroll['at']
                and menu['at'] >= down['timestamp'] + 500
                and events.index(down) < events.index(start) < events.index(scroll)
                and state.get('selection') == SELECTION and state.get('menu', {}).get('hidden') is True):
            return False
        # Ignore neither an earlier viewport interruption nor a release/new input.
        before_scroll = events[:events.index(scroll)]
        if any(e.get('type') in {'pointerup', 'pointercancel', 'touchend', 'touchcancel',
                                'resize', 'lostpointercapture', 'click', 'mousedown', 'mouseup'}
               for e in before_scroll):
            return False
        for event in before_scroll:
            if event.get('type') == 'pointermove':
                if (event.get('pointerId') != down['pointerId']
                        or not all(number(e.get(k)) for e in (event, down) for k in ('x', 'y'))
                        or math.hypot(event['x'] - down['x'], event['y'] - down['y']) > 8):
                    return False
        return True
    except (KeyError, IndexError, TypeError, AttributeError, ValueError):
        return False


def red(row):
    try:
        if not clean_result(row):
            return False
        cdp, touch, cases = row['cdp'][0], row['touch'][0], row['cases']
        failure = touch.get('firstFailure') or {}
        if not (type(row['exit']) is int and row['exit'] == 1
                and type(cdp.get('failedAssertions')) is int and cdp['failedAssertions'] == 1
                and cdp.get('sectionsFailed') == {'P1162': 1}
                and touch.get('completed') is False and touch.get('passed') == CASES[:4]
                and touch.get('failed') == ['DISABLED_REASON'] and len(cases) == 5
                and failure.get('kind') == 'assertion' and failure.get('assertion') == MARKER
                and len(row.get('failed', [])) == 1
                and row['failed'][0].startswith('P1162 ' + MARKER + ' \u2717')
                and all(case.get('id') == name and case.get('status') == 'pass'
                        and integer(case.get('assertions', {}).get('passed'), 1)
                        and case['assertions'].get('failed') == 0 and not case.get('firstFailure')
                        for case, name in zip(cases[:4], CASES[:4]))
                and cases[4].get('id') == 'DISABLED_REASON' and cases[4].get('status') == 'fail'
                and integer(cases[4].get('assertions', {}).get('passed'), 1)
                and cases[4]['assertions'].get('failed') == 1 and cases[4].get('firstFailure') == failure):
            return False
        return own_scroll_witness(failure.get('detail', {}).get('state', {}))
    except (KeyError, IndexError, TypeError, AttributeError):
        return False


def native_inputs(source, binaries):
    registry = load_module(source / 'tests/binaries.py', 'r433_own_scroll_native')
    registry.OUT_DIR = binaries
    inputs = {}
    for name in NATIVE:
        fingerprint, files, command = registry.compute_fingerprint(registry.BY_NAME[name])
        inputs[name] = {'fingerprint': fingerprint, 'files': files, 'command': command}
    return registry, inputs


def native_evidence(registry, folder):
    folder.mkdir()
    evidence = {}
    for name in NATIVE:
        binary = registry.BY_NAME[name]
        info = registry.inspect_one(binary)
        row = {'status': info.state, 'reason': info.reason, 'path': str(binary.path)}
        if binary.sidecar.is_file():
            raw = binary.sidecar.read_bytes()
            (folder / binary.sidecar.name).write_bytes(raw)
            row['sidecar'] = identity(raw)
        if binary.path.is_file():
            row['binary'] = file_identity(binary.path)
        evidence[name] = row
    save(folder / 'index.json', evidence)
    return evidence


def chrome_identity(out):
    value = os.environ.get('GEOMETRY_CHROME', '')
    path = Path(value)
    require(value and path.is_absolute() and path.is_file() and os.access(path, os.X_OK),
            'Set GEOMETRY_CHROME to the existing absolute Chrome executable; no flags are added')
    before = file_identity(path)
    process = subprocess.run([str(path), '--version'], capture_output=True, timeout=15)
    (out / 'chrome-version.stdout').write_bytes(process.stdout)
    (out / 'chrome-version.stderr').write_bytes(process.stderr)
    require(process.returncode == 0 and process.stdout.strip(), 'Chrome --version was not available')
    require(file_identity(path) == before, 'Chrome executable changed during version collection')
    return {'path': str(path), **before, 'version': process.stdout.decode('utf-8', errors='replace').strip(),
            'flagsUnchanged': os.environ.get('GEOMETRY_CHROME_FLAGS', ''),
            'versionEvidence': 'Executable --version; no independent Browser.getVersion query',
            'launcherDigestOnlyIfWrapper': True}


def execute(args, original, pins):
    root, out, temp = args.root, args.out.resolve(), Path(tempfile.gettempdir()).resolve()
    require(temp in out.parents and not out.exists() and root not in out.parents,
            '--out must be a new directory under TEMP, outside the checkout')
    binaries = (args.binary_dir or out / 'binaries').resolve()
    require(temp in binaries.parents and root not in binaries.parents and binaries != root,
            '--binary-dir must be under TEMP, outside the checkout')
    out.mkdir(parents=True)
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    checkout = original.fingerprint(root)
    save(out / 'checkout-before.json', checkout)
    report = {'schema': 'geometry-r433-sheet-own-scroll/2', 'fixedBase': BASE,
              'candidateHead': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
              'mutant': NAME, 'status': 'blocked', 'inputPins': pins, 'runs': [], 'problems': [],
              'runner': identity(Path(__file__).read_bytes()), 'nativeCache': str(binaries),
              'baselineMeaning': 'Unmodified current candidate control, not historical old product',
              'formalCI': False, 'goldenProduced': False, 'historicalReleaseEvidence': False,
              'limitations': ['Only original object-canvas P1162; no physical-device/L5 claim',
                              'Original green output does not retain the successful own-scroll event trace',
                              'Withdrawn stops at DISABLED_REASON hold; later no-write assertions were not reached',
                              'No historical release failure, official mutation ledger or whole-PR CI is certified']}
    save(out / 'summary.json', report)
    try:
        report['chrome'] = chrome_identity(out)
        sources = {label: out / ('source-' + label) for label in ('baseline', 'withdrawn', 'restored')}
        require(all(binaries != source and source not in binaries.parents for source in sources.values()),
                'Native cache must not be inside a source snapshot')
        for source in sources.values():
            original.candidate(source)
        product = sources['withdrawn'] / PRODUCT
        before = product.read_bytes()
        require(before.count(ANCHOR) == 1 and before.count(REPLACEMENT) == 0,
                'Own-scroll withdrawal requires exactly one unmodified guard anchor')
        after = before.replace(ANCHOR, REPLACEMENT, 1)
        require(after.count(REPLACEMENT) == 1 and after.replace(REPLACEMENT, ANCHOR, 1) == before,
                'Own-scroll mutation is not exactly reversible')
        product.write_bytes(after)
        report['withdrawal'] = {'path': PRODUCT, 'anchor': ANCHOR.decode(),
                                'replacement': REPLACEMENT.decode(), 'before': identity(before), 'after': identity(after)}
        fingerprints = {label: original.fingerprint(source) for label, source in sources.items()}
        fixed_tree = fixed_source_tree(root, original)
        control = fingerprints['baseline']
        base_changes = sorted(path for path in fixed_tree.keys() | control.keys()
                              if fixed_tree.get(path) != control.get(path, {}).get('blob'))
        # import-cost may add verified original ZIP/receipt inputs. The loader
        # validates them; this never permits changing a legacy fragment or code.
        measured_inputs = {path for path in original.test_overlay()
                           if path.startswith('geometry-web/canvas-registry/costs/P1162/')}
        main_projection = verified_main_projection(root, original, fixed_tree, control)
        require(set(base_changes) <= ADOPTION_PATHS | measured_inputs | set(main_projection['paths']),
                'Runtime source differs outside the reviewed fragment conversion: ' + ', '.join(base_changes))
        report['changesFromFixedBase'] = base_changes
        report['mainProjection'] = main_projection
        save(out / 'fixed-base-source-blobs.json', fixed_tree)
        require(fingerprints['baseline'] == fingerprints['restored'], 'Restored source differs from baseline')
        changed = sorted(p for p in fingerprints['baseline'].keys() | fingerprints['withdrawn'].keys()
                         if fingerprints['baseline'].get(p) != fingerprints['withdrawn'].get(p))
        require(changed == [PRODUCT], 'Withdrawal changed more than the single product guard')
        expected_native = None
        binary_bytes = []
        for label, source in sources.items():
            registry, native = native_inputs(source, binaries)
            if expected_native is None:
                expected_native = native
            require(native == expected_native, 'Native inputs/compile commands differ between phases')
            save(out / (label + '-native-inputs.json'), native)
            destination = out / ('run-' + label)
            native_before = native_evidence(registry, out / (label + '-native-before'))
            row = original.run(label, source, destination, binaries)
            row['sourceUnchanged'] = (json.loads((destination / 'source-before.json').read_text(encoding='utf-8')) ==
                                      json.loads((destination / 'source-after.json').read_text(encoding='utf-8')))
            row['sourceMatchesPrepared'] = original.fingerprint(source) == fingerprints[label]
            row['nativeBefore'] = native_before
            row['nativeAfter'] = native_evidence(registry, out / (label + '-native-after'))
            row['rawFiles'] = {p.name: identity(p.read_bytes()) for p in destination.iterdir() if p.is_file()}
            # Keep original result.json/stdout/stderr untouched. This is a separate audit.
            row['verdict'] = ('green' if green(row, original) else 'blocked') if label != 'withdrawn' else (
                              'specified-own-scroll-red' if red(row) else 'blocked')
            save(destination / 'own-scroll-audit.json', row)
            report['runs'].append(row)
            save(out / 'summary.json', report)
            require(row['sourceMatchesPrepared'] and row['sourceUnchanged'], label + ': source changed during run')
            require(all(item['status'] == 'fresh' for item in row['nativeAfter'].values()),
                    label + ': original native registry did not confirm fresh binaries')
            binary_bytes.append({name: item.get('binary') for name, item in row['nativeAfter'].items()})
            require(row['verdict'] != 'blocked', label + ': not the required normal assertion result; inspect raw logs')
        require(binary_bytes[0] == binary_bytes[1] == binary_bytes[2], 'Native binary bytes changed between phases')
        require(original.fingerprint(sources['baseline']) == original.fingerprint(sources['restored']),
                'Restored snapshot is not byte-for-byte identical after execution')
        require(file_identity(Path(report['chrome']['path'])) ==
                {key: report['chrome'][key] for key in ('bytes', 'sha256')}, 'Chrome executable changed during proof')
        report.update(status='pass', sequence=[row['exit'] for row in report['runs']],
                      sourceRestoredByteForByte=True, nativeInputsIdentical=True, nativeBinaryBytesIdentical=True)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        report['problems'].append(str(error))
    finally:
        current = original.fingerprint(root)
        save(out / 'checkout-after.json', current)
        report['checkoutUnchanged'] = current == checkout
        if not report['checkoutUnchanged']:
            report['status'] = 'blocked'
            report['problems'].append('Checkout source changed during the experiment')
        save(out / 'summary.json', report)
    print('R433_SHEET_OWN_SCROLL ' + json.dumps({key: report.get(key) for key in
          ('status', 'fixedBase', 'mutant', 'sequence', 'checkoutUnchanged', 'problems')}, ensure_ascii=False))
    return 0 if report['status'] == 'pass' else 2


def self_test(original):
    """Exercise receipt predicates only; every fixture below is synthetic."""
    good = {'status': 'assertions', 'exit': 0, 'sourceUnchanged': True, 'runtime': {'fresh': True},
            'fatal': [], 'failed': [], 'cdp': [{'completed': True, 'unexpectedBrowserExceptions': 0,
                'uncaughtBrowserExceptions': 0, 'scope': {'mode': 'partial', 'filters': ['GEOMETRY_CANVAS_MODULE_ONLY'],
                    'module': 'P1162', 'modifiers': [], 'acceptance': False},
                'goldenCompare': 'not compared (partial mode)', 'sections': {'P1162': 17},
                'passedAssertions': 17, 'failedAssertions': 0}],
            'touch': [{'input': 'Input.dispatchTouchEvent', 'scope': 'object-canvas', 'expectedCases': CASES,
                       'completed': True, 'passed': CASES, 'failed': [], 'firstFailure': None}],
            'cases': [{'id': name, 'status': 'pass', 'assertions': {'passed': 1, 'failed': 0}} for name in CASES]}
    down = {'type': 'pointerdown', 'pointerType': 'touch', 'pointerId': 18, 'trusted': True,
            'at': 1000, 'timestamp': 1000, 'card': 'boundary:41', 'canvas': True, 'control': False,
            'defaultPrevented': True, 'lateWindowCapture': False, 'x': 137.2, 'y': 275.2,
            'preDispatch': {'selection': SELECTION, 'sel': None, 'focus': None, 'tool': 'select',
                            'drawTool': None, 'on': True, 'view3': False, 'hidden': False, 'card': False,
                            'pan': False, 'marquee': False, 'dialogs': [], 'owner': {'phase': 'ready'}}}
    state = {'selection': SELECTION, 'menu': {'hidden': True, 'sheet': False},
             'menus': [{'at': 1510, 'sheet': True}], 'events': [down,
             {'type': 'touchstart', 'trusted': True, 'touches': 1, 'at': 1001, 'card': 'boundary:41'},
             {'type': 'scroll', 'trusted': True, 'at': 1516, 'target': 'canvasCtxMenu'}]}
    failure = {'assertion': MARKER, 'kind': 'assertion', 'detail': {'state': state}}
    killed = copy.deepcopy(good)
    killed.update(exit=1, failed=['P1162 ' + MARKER + ' \u2717 false'])
    killed['cdp'][0].update(failedAssertions=1, sectionsFailed={'P1162': 1})
    killed['touch'][0].update(completed=False, passed=CASES[:4], failed=['DISABLED_REASON'], firstFailure=failure)
    killed['cases'] = killed['cases'][:5]
    killed['cases'][4].update(status='fail', assertions={'passed': 5, 'failed': 1}, firstFailure=failure)
    require(green(good, original) and not red(good), 'Synthetic all-16 green rejected or counted as red')
    require(red(killed) and not green(killed, original), 'Synthetic exact own-scroll kill rejected')
    checks = ['accept all-16 green', 'accept exact DISABLED_REASON own-scroll red']
    variants = [
        ('process timeout', lambda r: r.update(status='infra', exit=None, error='CDP exceeded 300 s')),
        ('normal nonzero without assertions', lambda r: r.update(cases=[], touch=[], cdp=[])),
        ('fatal', lambda r: r.update(fatal=['FATAL: no CDP'])),
        ('wrong first case / registration red', lambda r: r['touch'][0].update(passed=[], failed=['LONG_PRESS'])),
        ('wrong assertion', lambda r: r['touch'][0]['firstFailure'].update(assertion='R433_RELEASE_PRESERVES_MENU')),
        ('zero errors without input preconditions', lambda r: r['touch'][0]['firstFailure']['detail']['state'].update(events=[])),
        ('no prior open sheet', lambda r: r['touch'][0]['firstFailure']['detail']['state'].update(menus=[])),
        ('untrusted scroll', lambda r: r['touch'][0]['firstFailure']['detail']['state']['events'][2].update(trusted=False)),
        ('external scroll', lambda r: r['touch'][0]['firstFailure']['detail']['state']['events'][2].update(target='document')),
        ('sheet opens before deadline', lambda r: r['touch'][0]['firstFailure']['detail']['state']['menus'][0].update(at=1499)),
        ('not ready', lambda r: r['touch'][0]['firstFailure']['detail']['state']['events'][0]['preDispatch']['owner'].update(phase='loading')),
        ('wrong selection', lambda r: r['touch'][0]['firstFailure']['detail']['state']['events'][0]['preDispatch'].update(selection=[])),
        ('menu stayed visible', lambda r: r['touch'][0]['firstFailure']['detail']['state']['menu'].update(hidden=False)),
        ('source changed', lambda r: r.update(sourceUnchanged=False)),
        ('stale runtime', lambda r: r.update(runtime={'fresh': False})),
        ('retired touch-only scope', lambda r: r['cdp'][0]['scope'].update(filters=['GEOMETRY_CANVAS_TOUCH_ONLY'])),
        ('wrong module', lambda r: r['cdp'][0]['scope'].update(module='P999')),
        ('claimed acceptance', lambda r: r['cdp'][0]['scope'].update(acceptance=True)),
        ('two failures', lambda r: r['cdp'][0].update(failedAssertions=2)),
        ('browser exception', lambda r: r['cdp'][0].update(uncaughtBrowserExceptions=1)),
        ('missing case list', lambda r: r['touch'][0].update(expectedCases=CASES[:-1])),
    ]
    for label, change in variants:
        row = copy.deepcopy(killed)
        change(row)
        require(not red(row), 'Accepted invalid synthetic red: ' + label)
        checks.append('reject ' + label)
    for label, change in (
        ('zero assertions', lambda r: r['cdp'][0].update(sections={'P1162': 0}, passedAssertions=0)),
        ('only four cases', lambda r: r.update(cases=r['cases'][:4])),
        ('green timeout', lambda r: r.update(status='infra', error='timeout')),
        ('green stale runtime', lambda r: r.update(runtime={'fresh': False})),
    ):
        row = copy.deepcopy(good)
        change(row)
        require(not green(row, original), 'Accepted invalid synthetic green: ' + label)
        checks.append('reject ' + label)
    print('R433_SHEET_OWN_SCROLL_SELFTEST ' + json.dumps({'status': 'pass', 'synthetic': True,
          'chromeStarted': False, 'nativeBuilt': False, 'checks': len(checks), 'cases': checks}, ensure_ascii=False))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--root', type=Path, required=True)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--out', type=Path)
    choice.add_argument('--self-test', action='store_true')
    parser.add_argument('--binary-dir', type=Path)
    args = parser.parse_args()
    args.root = args.root.resolve()
    require(args.root.is_dir(), 'Repository root does not exist')
    original, pins = pinned_runner(args.root)
    if args.self_test:
        require(args.binary_dir is None, '--self-test does not accept execution options')
        return self_test(original)
    require(sys.platform.startswith('linux'), 'Original start_local runner requires Linux')
    return execute(args, original, pins)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        print('R433_SHEET_OWN_SCROLL_SETUP ' + str(error), file=sys.stderr)
        sys.exit(2)
