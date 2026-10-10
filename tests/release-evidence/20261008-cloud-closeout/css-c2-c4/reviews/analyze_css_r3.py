"""Read saved CSS r3 evidence only; no browser/native launch or product edits."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import zipfile

root = Path('/workspace/geometry-axiom')
base = Path('/workspace/closure-evidence')
source = base / 'async-review/browser-css-5174-390-3'
out = base / 'css-review'

def read(p):
    return json.loads(Path(p).read_text())
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):
    return {'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)}

events = read(source / 'slots-390/browser-input-events.json')
index = next(i for i, e in enumerate(events) if e['type'] == 'pointerdown' and e['card'] == 'space' and e['cardId'] == '1')
gesture = events[index:]
downs = [e for e in gesture if e['type'] == 'pointerdown']
assert len(downs) == 2
first, second = downs
assert first['trusted'] and first['region'] and first['selected'] is None and first['focus'] is None
assert second['trusted'] and second['id'] == 'btnZoom' and not second['region'] and second['focus'] is None
assert second['selection'] == [{'kind': 'space', 'id': 1}] and second['selected'] == {'kind': 'space', 'id': 1}
assert all(first[k] == second[k] for k in ['pointerId', 'pointerType', 'context', 'x', 'y'])
assert 0 <= second['timeStamp'] - first['timeStamp'] <= 450
assert gesture[-1]['type'] == 'dblclick' and gesture[-1]['id'] == 'btnZoom' and gesture[-1]['focus'] is None
with zipfile.ZipFile(source / 'slots-390/trace.zip') as z:
    raw = z.read('trace.trace')
trace = [(i + 1, json.loads(line)) for i, line in enumerate(raw.splitlines())]
double = next(e for _, e in trace if e.get('type') == 'before' and e.get('method') == 'dblclick')
wait = next(e for _, e in trace if e.get('type') == 'before' and e.get('method') == 'waitForFunction' and "oc.focus?.t==='space'" in e.get('params', {}).get('expression', ''))
selected_trace = [{'member_line': i, 'event': e} for i, e in trace if e.get('callId') in [double['callId'], wait['callId']] and e.get('type') in ['before', 'input', 'log', 'after']]
assert any(row['event'].get('type') == 'after' and row['event'].get('callId') == double['callId'] and 'error' not in row['event'] for row in selected_trace)
assert any(row['event'].get('type') == 'after' and row['event'].get('callId') == wait['callId'] and row['event'].get('error', {}).get('name') == 'TimeoutError' for row in selected_trace)
(out / 'css-r3-slots390-entry-trace-events.json').write_text(json.dumps(selected_trace, ensure_ascii=False, indent=2) + '\n')
beam = read(source / 'beam-390/result.json')
styles = read(source / 'beam-390/computed-style.json')
assert beam['passed'] and not beam['page_errors'] and not beam['network_capture_errors'] and not beam['cleanup_errors']
assert read(source / 'beam-390/before.json') == read(source / 'beam-390/after.json')
assert styles['stroke'] == styles['color'] == 'rgb(72, 105, 135)'
assert styles['fill'] == styles['background'] == 'rgb(237, 243, 248)'
slots = read(source / 'slots-390/result.json')
assert not slots['passed'] and not slots['page_errors'] and not slots['network_capture_errors'] and not slots['cleanup_errors']
assert not (source / 'slots-390/initial-nonhover-slots.json').exists()
git = subprocess.run(['git', 'diff', '5174a8d^', '5174a8d', '--', 'geometry-web/app.css'], cwd=root, capture_output=True, text=True)
assert git.returncode == 0 and not git.stderr
(out / 'css-5174-product-diff.patch').write_text(git.stdout)
report = {
    'checked_at': datetime.now(timezone.utc).isoformat(),
    'source_head': '5174a8dafd8c48329d7166abbd3d104e3c28c0c4',
    'probe_sha256': 'b81a9f25b08c581168e63f5d407a89c3afc386a160cb1dd1384dcd1cb1754a9c',
    'classification': 'Observed positional double-click entry failure on the integration candidate: first click correctly selects space 1; layout places btnZoom under the same second-down point; that existing control receives click/dblclick and workspace does not open.',
    'css_classification': 'Beam 390 assertions pass in full; slot 390 CSS/navigation assertions were not reached and remain unverified. Do not count the failed entry as a slot-color/discoverability failure.',
    'not_p5_wrong_first_target': True,
    'not_observer_precondition_failure': True,
    'not_single_tap_route': True,
    'raw_gesture': gesture,
    'source_basis': [
        'app.js:9005-9028 first pointer-up selects the object and renders the inspector; app.js:9329-9332 toggles canvas-has-inspector.',
        'app.css:2368-2373 positions canvas controls at the viewport bottom and makes the mobile selected-object inspector participate in layout.',
        'app.js:9622-9638 intentionally limits second-down continuation to ocv / sidebar-right / canvasViewport. btnZoom is outside that allowed region.',
        'index.html:274-280 places btnZoom in canvas-controls; app.js:1875-1878 implements its normal Fit All action.',
        'The exact 5174 CSS diff only changes space-plan-beam and slot-empty child styles. No responsible main-canvas entry/layout handler was edited by that commit. This is source impact analysis, not a runtime comparison against its parent.'
    ],
    'minimal_separate_css_precondition': {
        'route': 'Fresh fixture -> real single click on space:1 card -> wait for exact selected identity and visible #inspEnter -> real click #inspEnter -> await space workspace/render completion.',
        'source': ['app.js:9452-9454 creates existing Enter Space button', 'app.js:9494-9497 binds existing enterFocus handler', 'DOM-CONTRACT.md:383 lists double-click and inspector-button entry'],
        'must_preserve': ['all computed CSS/visibility/native World/slot pointer/Tab-Enter assertions', 'original r3 failure, raw events and trace', 'separate status of the card-double-click entry defect'],
        'must_not': ['force clicks', 'call enterFocus internally', 'add btnZoom to accepted double-click region', 'treat an inspector-button pass as a repaired double-click route', 'retry the unchanged failed double-click until lucky']
    },
    'next_product_step': 'Existing app.js/layout owner should review the same-coordinate second-down collision with canvas-controls while preserving real zoom-control behavior; retain as a concrete internal unresolved entry defect.',
    'evidence': [bind(source / p) for p in ['receipt.json', 'script.py', 'beam-390/result.json', 'beam-390/computed-style.json', 'beam-390/before.json', 'beam-390/after.json', 'beam-390/space-entry-gesture.json', 'slots-390/result.json', 'slots-390/browser-input-events.json', 'slots-390/trace.zip', 'slots-390/failed.png', 'slots-390/failed-state.json']],
    'private_trace_member_sha256': hashlib.sha256(raw).hexdigest(),
    'analysis_script_sha256': sha(Path(__file__)),
    'product_diff_command': {'argv': git.args, 'exit_code': git.returncode, 'stdout_file': 'css-5174-product-diff.patch', 'stderr': git.stderr},
    'browser_or_native_launched': False
}
path = out / 'css-r3-slots390-entry-diagnosis.json'
path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'receipt': str(path), 'sha256': sha(path), 'beam390': 'PASS confirmed', 'slots390': 'CSS not reached; exact btnZoom collision observed'}))
