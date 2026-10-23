"""Extract bounded observations without changing the diagnostic's original verdict."""
import hashlib
import json
from pathlib import Path

root = Path('/tmp/g288p88q')
out = Path(__file__).resolve().parent / 'ACTUAL_QUERY_OBSERVATIONS_v2.json'
original = json.loads((root / 'receipt.json').read_text())
assert original['actual_driver_exit_code'] is not None, 'Wait for all declared phases'
assert [p['variant'] for p in original['phases']] == ['fixed', 'withdrawn', 'restored']
report = {
    'schema': 'geo288-p88-actual-query-observations/2',
    'metadata_correction': 'The v1 extractor used an absent response_json_unchanged key and emitted null. The preserved raw trace names this field parsed_json_unchanged; v2 reads that exact key. Parsed JSON is not HTTP wire bytes; no original trace or outcome changed.',
    'source_sha': original['sha'],
    'scope': 'Diagnostic memory-loader variants on F13; not a formal gate or execution of a future source commit.',
    'original_driver_exit': original['actual_driver_exit_code'],
    'original_proof_passed': original['passed'],
    'natural_cause_proven': False,
    'phases': [],
    'limitations': [
        'Original full canvas three runs had no pointer target trace; this diagnostic cannot identify their exact query or cause.',
        'Synchronous observation and layout reads have nonzero timing cost; the controlled query adds an explicit response barrier.',
        'A failed displacement precondition is a failed diagnostic, not a successful original assertion counterexample.',
        'Stable node/rectangle samples do not guarantee that no future repaint can occur before a CDP input arrives.',
    ],
}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def compact_state(state):
    if not state:
        return None
    return {
        'parent_scroll_top': state.get('parent_scroll_top'),
        'pane_scroll_top': state.get('pane_scroll_top'),
        'grid_preview_seq': state.get('grid_preview_seq'),
        'active': state.get('active'),
        'mode_node': state.get('mode_node'),
        'ratio_node': state.get('ratio_node'),
    }

for phase in original['phases']:
    name = phase['variant']
    trace_path = root / name / 'trace.json'
    trace = json.loads(trace_path.read_text())
    stdout = root / name / 'workflow/grid/steps/03.stdout'
    results = [json.loads(s.removeprefix('CDP_RESULT ')) for s in stdout.read_text().splitlines() if s.startswith('CDP_RESULT ')]
    assert len(results) == 1
    inj = trace.get('injection') or {}
    wanted = {k: inj.get(k) for k in ('name', 'attempted', 'applied', 'valid', 'count', 'before', 'after', 'original_measure', 'old_center', 'parsed_json_unchanged', 'error')}
    start = next((e['serial'] for e in trace['events'] if e['kind'] == 'query-response-held'), None)
    end = next((e['serial'] for e in trace['events'] if e['kind'] == 'controlled-query-release'), None)
    events = []
    for event in trace['events']:
        if start is not None and end is not None and start <= event['serial'] <= end:
            events.append({k: event.get(k) for k in ('serial', 'kind', 'epoch_ms', 'monotonic_ms', 'stack', 'target', 'trusted', 'x', 'y')} | {'state': compact_state(event.get('state'))})
    report['phases'].append({
        'variant': name,
        'original_test_exit': phase.get('original_test_exit'),
        'original_phase_passed': phase.get('passed'),
        'trace_path': str(trace_path), 'trace_sha256': digest(trace_path),
        'stdout_path': str(stdout), 'stdout_sha256': digest(stdout),
        'cdp_result': results[0], 'injection': wanted, 'events': events,
        'observation_errors': trace.get('errors'),
        'browser_errors': trace.get('browser_trace', {}).get('errors'),
        'browser_stopped': trace.get('browser_trace', {}).get('stopped'),
    })
report['receipt_path'] = str(root / 'receipt.json')
report['receipt_sha256'] = digest(root / 'receipt.json')
out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'path': str(out), 'sha256': digest(out), 'original_driver_exit': report['original_driver_exit'], 'original_proof_passed': report['original_proof_passed']}, ensure_ascii=False))
