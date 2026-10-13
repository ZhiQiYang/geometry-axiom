"""Read-only analysis of saved CSS and edge browser evidence; no browser/native launch."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import zipfile

BASE = Path('/workspace/closure-evidence')
OUT = BASE / 'css-review'
ROOT = Path('/workspace/geometry-axiom')
CSS = BASE / 'async-review/browser-css-5174-2'
EDGE = BASE / 'async-review/browser-edge-transition-ce74'
OUT.mkdir(parents=True, exist_ok=True)

def digest(path):
    p = Path(path)
    return {'path': str(p), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}

def read(path):
    return json.loads(Path(path).read_text())

def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def trace(path):
    with zipfile.ZipFile(path) as archive:
        return [json.loads(line) for line in archive.read('trace.trace').splitlines()]

commands = []
for argv in [['pwd'], ['git', 'status', '--short'], ['git', 'rev-parse', 'HEAD'], ['git', 'rev-parse', 'origin/main']]:
    r = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    commands.append({'argv': argv, 'stdout': r.stdout, 'stderr': r.stderr, 'exit_code': r.returncode})
    assert r.returncode == 0
identity = {'checked_at': datetime.now(timezone.utc).isoformat(), 'commands': commands,
            'source': [digest(ROOT / p) for p in ['geometry-web/app.js', 'geometry-web/app.css', 'geometry-web/docs/DOM-CONTRACT.md']],
            'analysis_script': digest(__file__)}
write('review-identity.json', identity)

inputs = read(CSS / 'beam-390/browser-input-events.json')
card_index = next(i for i, e in enumerate(inputs) if e['type'] == 'pointerdown' and e['card'] == 'space' and e['cardId'] == '1')
gesture = inputs[card_index:]
downs = [e for e in gesture if e['type'] == 'pointerdown']
assert len(downs) == 2
first, second = downs
assert first['card'] == 'space' and first['cardId'] == '1'
assert second['tag'] == 'DIV' and second['card'] is None
assert all(e['trusted'] and e['button'] == 0 for e in downs)
assert first['pointerId'] == second['pointerId'] and first['pointerType'] == second['pointerType'] == 'mouse'
assert 0 <= second['timeStamp'] - first['timeStamp'] <= 450
assert all(abs(first[k] - second[k]) <= 6 for k in ['x', 'y'])
doubles = [e for e in gesture if e['type'] == 'dblclick']
assert len(doubles) == 1 and doubles[0]['trusted'] and doubles[0]['detail'] == 2
events = trace(CSS / 'beam-390/trace.zip')
call = next(e for e in events if e.get('type') == 'before' and e.get('method') == 'dblclick')
call_id = call['callId']
call_events = [e for e in events if e.get('callId') == call_id]
snapshot_names = [e['snapshot']['snapshotName'] for e in events if e.get('type') == 'frame-snapshot' and call_id in e['snapshot']['snapshotName']]
assert any(e.get('type') == 'after' and 'error' not in e for e in call_events)
css = {
    'classification': 'observer precondition failure; CSS mobile assertions were not reached',
    'not_mobile_single_tap': True,
    'gesture': gesture,
    'double_click_call': call_events,
    'trace_snapshot_names': snapshot_names,
    'exact_second_target_ancestor': 'unknown: recorded event only has tag=DIV; trace has no intermediate snapshot between downs',
    'source_supported_route': 'app.js:9594-9638 explicitly accepts same-position second down on #ocv / #app .sidebar-right / canvasViewport with stable selection and context; it does not require both targets to remain the card',
    'recommendation': 'Retain exact locator.dblclick and all CSS/World/slot oracles. Add passive target-region/selection/context capture; require first down on space:1 and second down in allowed region, same selected identity/context, no intervening focus and same pointer/time/position. Do not accept one pointerdown or force clicks.',
    'preserve_failure': True,
    'sources': [digest(CSS / p) for p in ['receipt.json', 'script.py', 'beam-390/browser-input-events.json', 'beam-390/result.json', 'beam-390/trace.zip']],
}
write('css-entry-diagnosis.json', css)

initial = 'boundary 731 outline 0,0 4000,0 4000,3000 0,3000 hole 3000,1000 3500,1000 3500,1500 3000,1500'
expected_line = 'boundary 731 outline 0,0 4200,0 4200,3000 0,3000 hole 3000,1000 3500,1000 3500,1500 3000,1500'
rows = read(EDGE / 'results.json')
checks = []
for r in rows:
    name = r['name']
    before = (EDGE / (name + '-world-before.scene')).read_bytes()
    expected = (EDGE / (name + '-world-expected.scene')).read_bytes()
    assert before.count(initial.encode()) == 1
    assert expected == before.replace(initial.encode(), expected_line.encode(), 1)
    held = r['mode'] == 'held-success-to-B'
    stages = ['gate', 'B-ready', 'released'] if held else ['completed']
    assert all((EDGE / (name + '-world-' + stage + '.scene')).read_bytes() == expected for stage in stages)
    assert not r.get('pageErrors') and not r.get('error')
    assert r['singleTrusted4200Change'] and r['exactNativeCommand'] and r['realNavigationRoute']
    observed = {'name': name, 'original_ok': r['ok'], 'all_world_stages_equal_fixed_expected': True,
                'world_artifacts': [digest(EDGE / (name + '-world-' + stage + '.scene')) for stage in ['before', 'expected'] + stages],
                'case_json': digest(EDGE / (name + '.json'))}
    if held:
        before_b, after_b = r['beforeB'], r['afterB']
        differences = {key: {'before': before_b[key], 'after': after_b[key]} for key in before_b if before_b[key] != after_b[key]}
        assert set(differences) == {'editToken'}
        assert differences['editToken'] == {'before': 2, 'after': 3}
        draws = [{k: d[k] for k in ['token', 'bid', 'phase']} for d in r['audit']['draws']]
        assert draws == [{'token': 2, 'bid': 732, 'phase': 'settled'}, {'token': 3, 'bid': 732, 'phase': 'settled'}]
        assert before_b['handles'] == after_b['handles'] == 5
        events = trace(EDGE / (name + '-trace.zip'))
        release = next(e for e in events if e.get('type') == 'before' and '__edgeTransitionAudit.gate.release()' == e.get('params', {}).get('expression'))
        calls = [e for e in events if e.get('type') == 'before' and e.get('startTime', 0) >= release['startTime']]
        observed.update(all_state_differences=differences, draws=draws, handles_before_after=[5, 5],
                        release_and_following_calls=[{k: e.get(k) for k in ['callId', 'startTime', 'class', 'method', 'params']} for e in calls[:12]],
                        interpretation='Old A success continuation triggers render + refreshSurfaces; refreshSurfaces enters current B again and increments editToken. Existing probe sees same B geometry, handles and final World. The fixed ownership-token category still fails; no lost-handle or corruption claim is supported.',
                        limitation='No live B drag/draft or pending B operation during release. Token-only change alone does not establish user-visible harm. Source risk of cancelling B transient edit remains separate.')
    checks.append(observed)
gate = read(BASE / 'gates/edge-transition-ce74/receipt.json')
assert gate['execution']['exitCode'] == gate['gateExitCode'] == 1
assert gate['before']['git']['head'] == gate['after']['git']['head'] == '5174a8dafd8c48329d7166abbd3d104e3c28c0c4'
assert gate['before']['git']['status'] == gate['after']['git']['status'] == ''
assert not gate['before']['problems'] and not gate['after']['problems']
assert gate['before']['runtime'] == gate['after']['runtime']
assert digest(BASE / 'gates/edge-transition-ce74/command.log')['sha256'] == gate['log']['sha256']
write('edge-transition-diagnosis.json', {
    'original_result': {'success_controls_passed': 4, 'held_transitions_ownership_token_failed': 4, 'aggregate_exit_code': 1},
    'canonical_gate_identity_valid': True,
    'retokenization_source_path': ['app.js:1195-1201 emitLine await success then global previewClear/render/refreshSurfaces', 'app.js:1238-1255 refreshSurfaces preserves current workSurf=732 then calls enterEdit', 'app.js:1270-1285 enterEdit increments token and resets transient edit before reading/drawing current B'],
    'classification': 'fixed ownership-token category failure; old response re-enters current B. No changed final geometry, missing handles or World corruption observed. User-visible effect on active B work requires a bounded follow-up; do not silently drop token oracle or report 8 passes.',
    'checks': checks,
    'evidence': [digest(EDGE / p) for p in ['results.json', 'receipt.json', 'before.json', 'after.json', 'identity-comparison.json', 'executed-edge_transition_probe.py', 'executed-edge_transition_instrumentation.js', 'executed-source-plan.md']] + [digest(BASE / 'gates/edge-transition-ce74/receipt.json'), digest(BASE / 'gates/edge-transition-ce74/command.log')]
})
print(json.dumps({'css': 'observer precondition failure; two trusted downs, second target DIV ancestry unknown', 'edge': '4 controls pass; 4 fixed token-category failures; all 8 World expectations independently match', 'out': str(OUT)}))
