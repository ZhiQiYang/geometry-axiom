"""Independent, read-only raw-artifact review; launches no browser or service."""
import ast
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys
import zipfile

BASE = pathlib.Path('<workspace-path>')
PROJ = BASE / 'geometry-ui-projection-supplement'
NORMAL = BASE / 'geometry-ui-normal-hole-control'
OUT = BASE / 'geometry-ui-hole-order-independent-review'
OLD = 'f98078dc150c22960cbe2d212afb3ded61954bb9'
NEW = 'c0f05baade2424482fab94c72f0592f7b02326ae'
A0 = 'boundary 1 outline 0,0 4000,0 4000,3000 0,3000'
A1 = A0 + ' hole 1000,1000 1400,1000 1400,1400 1000,1400'
B0 = 'boundary 7 outline 0,0 4000,0 4000,3000 0,3000'
OLD_LINE = "BH=B0+' hole 500,500 800,500 800,800 500,800'"
NEW_LINE = "BH=B0+' hole 800,800 500,800 500,500 800,500'"
BH = B0 + ' hole 800,800 500,800 500,500 800,500'
checks, artifacts, case_reports = [], {}, []

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read(path):
    path = pathlib.Path(path)
    data = path.read_bytes()
    artifacts[str(path)] = {'sha256': sha(data), 'bytes': len(data)}
    return data

def load(path):
    return json.loads(read(path))

def check(name, ok, details=None):
    checks.append({'check': name, 'ok': bool(ok), **({'details': details} if details is not None else {})})

def exact_replace(world, old, new):
    assert world.splitlines().count(old.encode()) == 1
    return world.replace(old.encode(), new.encode(), 1)

def trace_data(path):
    raw = read(path)
    import io
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        def payload(content):
            return z.read('resources/' + content['_sha1']) if content.get('_sha1') else content.get('text', '').encode()
        network = []
        served = {}
        for line in z.read('trace.network').decode().splitlines():
            item = json.loads(line)['snapshot']
            req, res = item['request'], item['response']
            if req['url'].endswith('/api') and req['method'] == 'POST':
                request = json.loads(payload(req['postData']))
                response = json.loads(payload(res['content']))
                network.append({'command': request.get('cmd'), 'reply': response,
                                'status': res['status'], 'at': item['startedDateTime'],
                                'version': next((h['value'] for h in req['headers'] if h['name'].lower() == 'x-geometry-version'), None)})
            if req['method'] == 'GET' and any(req['url'].endswith('/' + name) for name in ['app.js', 'app.css']):
                headers = {h['name'].lower(): h['value'] for h in res['headers']}
                content = res['content']
                served[req['url'].rsplit('/', 1)[-1]] = {
                    'sha256': sha(payload(content)) if content.get('_sha1') or 'text' in content else None,
                    'status': res['status'], 'version': headers.get('x-geometry-version'),
                    'contentLength': headers.get('content-length')}
        timeline = [json.loads(line) for line in z.read('trace.trace').decode().splitlines()]
    return network, timeline, served

def review_receipt(folder, head, script_path, expected_pass, expected_fail):
    receipt = load(folder / 'receipt.json')
    wrapper = load(pathlib.Path(str(folder) + '-wrapper-receipt.json'))
    before, after = receipt['before'], receipt['after']
    tag = folder.name + ':' + folder.parent.name
    check(tag + ':complete-result', receipt['completed'] is True and receipt['fatal'] is None and receipt['pass'] == expected_pass and receipt['fail'] == expected_fail and receipt['expected'] == expected_pass + expected_fail and receipt['exitCode'] == (1 if expected_fail else 0))
    check(tag + ':exact-clean-source', before['head'] == head == after['head'] and before['dirty'] == '' == after['dirty'])
    check(tag + ':identity-stable', all(before[k] == after[k] for k in ['head', 'dirty', 'tree', 'sources', 'scripts', 'native']) and all(before['runtime'][k] == after['runtime'][k] for k in ['root', 'pid', 'session', 'version']))
    check(tag + ':runtime-fresh', before['runtime']['fresh'] is True and after['runtime']['fresh'] is True and before['pwd'] == before['runtime']['root'])
    expected_script_sha = sha(read(script_path))
    wrapper_script_sha = wrapper.get('script', {}).get('sha256', wrapper.get('scriptSHA256'))
    wrapper_exit = wrapper.get('exitCode', wrapper.get('actualUnifiedExecExitCode'))
    check(tag + ':executor-script-bound', before['scripts']['projection_supplement.py'] == expected_script_sha == wrapper_script_sha)
    check(tag + ':wrapper-bound', wrapper['sourceSHA'] == head and wrapper_exit == receipt['exitCode'] and wrapper['scriptResult']['sha256'] == sha(read(folder / 'receipt.json')) and wrapper['command'] == receipt['argv'])
    check(tag + ':raw-log-bound', sha(read(wrapper['rawLog']['path'])) == wrapper['rawLog']['sha256'])
    processes = before['actualServiceProcesses']
    service = next(p for p in processes if p['pid'] == before['runtime']['pid'])
    bridge = before['native']['bridge']
    bridge_proc = next(p for p in processes if p['exe'] == bridge['path'])
    check(tag + ':actual-service-native-bound', service['sha256'] == before['executor']['sha256'] and bridge_proc['parent'] == service['pid'] and bridge_proc['sha256'] == bridge['sha256'] and bridge['state'] == 'fresh' and before['native']['model-base']['state'] == 'fresh')
    browser = load(folder / 'browser.json')
    owned = browser['actualOwnedProcesses']
    main = next(p for p in owned if 'chromium' in p['exe'] and not any(a.startswith('--type=') for a in p['argv']))
    driver = next(p for p in owned if p['pid'] == main['parent'])
    python = next(p for p in owned if p['pid'] == driver['parent'])
    check(tag + ':actual-browser-chain', browser['sandbox'] is True and main['sha256'] and 'node' in driver['exe'] and driver['sha256'] and python['sha256'] == before['executor']['sha256'])
    check(tag + ':actual-executable-hashes-now', all(sha(pathlib.Path(p['exe']).read_bytes()) == p['sha256'] for p in [service, bridge_proc, main, driver, python]))
    for source, expected in before['sources'].items():
        content = subprocess.check_output(['git', '-C', before['pwd'], 'show', head + ':' + source])
        check(tag + ':git-object-source:' + source, sha(content) == expected)
    return receipt

original = read(PROJ / 'executed-r2-sources/projection_supplement.py').decode()
patch = read(PROJ / 'historical-hole-order-expected-only.patch').decode()
check('original-executor-preserved', original == read(PROJ / 'projection_supplement.py').decode())
check('patch-exact-one-removed-one-added-line', [l for l in patch.splitlines() if l.startswith('-') and not l.startswith('---')] == ['-' + OLD_LINE] and [l for l in patch.splitlines() if l.startswith('+') and not l.startswith('+++')] == ['+' + NEW_LINE])
check('patch-original-one-occurrence', original.splitlines().count(OLD_LINE) == 1)
corrected = original.replace(OLD_LINE, NEW_LINE, 1)
old_ast, new_ast = ast.parse(original), ast.parse(corrected)
old_asserts = [ast.dump(n) for n in ast.walk(old_ast) if isinstance(n, ast.Assert)]
new_asserts = [ast.dump(n) for n in ast.walk(new_ast) if isinstance(n, ast.Assert)]
check('all-assertions-preserved', old_asserts == new_asserts, {'assertCount': len(old_asserts)})
for tree in [old_ast, new_ast]:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'BH' for t in node.targets):
            node.value = ast.Constant(value='normalized-BH-only')
check('all-other-executable-AST-identical', ast.dump(old_ast) == ast.dump(new_ast))
check('fixed-byte-comparison-retained', "assert dump(page,name,'B-finished')==expected" in corrected and "expected=fixed(world,B0,BH if kind=='hole'else BV)" in corrected)
corrected_dir = BASE / 'geometry-ui-projection-supplement-corrected-v2'
check('actual-separate-corrected-copy-exact', read(corrected_dir / 'projection_supplement.py').decode() == corrected)
for unchanged_file in ['projection_instrumentation.js', 'fixture.json']:
    check('actual-separate-copy-unchanged:' + unchanged_file, read(corrected_dir / unchanged_file) == read(PROJ / unchanged_file))
ledger = load(corrected_dir / 'expected-order-correction-receipt.json')
check('version-ledger-actual-hashes', all(sha(read(ledger[k]['path'])) == ledger[k]['sha256'] for k in ['originalExecutor', 'newExecutor', 'exactExpectedOnlyPatch', 'historicalControlProof']))

sets = [
    ('baseline-normal', NORMAL / 'baseline-f980-r1', OLD, NORMAL / 'projection_supplement.py', 2, 0),
    ('after-normal', NORMAL / 'after-c0f05baa-r1', NEW, NORMAL / 'projection_supplement.py', 2, 0),
    ('after-held-original', PROJ / 'after-c0f05baa-r1', NEW, PROJ / 'executed-r2-sources/projection_supplement.py', 8, 2),
]
loaded = {}
for kind, folder, head, script_path, passed, failed in sets:
    receipt = review_receipt(folder, head, script_path, passed, failed)
    loaded[kind] = {'receipt': receipt, 'widths': {}}
    for width in [1382, 390]:
        name = ('held-A-B-hole-' if kind == 'after-held-original' else 'normal-hole-') + str(width)
        row = load(folder / (name + '.json'))
        audit = row['audit']
        network, timeline, served = trace_data(folder / (name + '-trace.zip'))
        expected_version = receipt['before']['runtime']['version']
        command = 'line ' + BH
        commands = [n for n in network if n['command'] == command]
        check(kind + ':' + name + ':one-exact-native-hole-command', len(commands) == 1 and commands[0]['status'] == 200 and commands[0]['reply'] == {'ok': True})
        check(kind + ':' + name + ':network-version', all(n['version'] == expected_version for n in network))
        check(kind + ':' + name + ':trace-css-body-bound', served['app.css']['sha256'] == receipt['before']['sources']['geometry-web/app.css'])
        app_bytes = subprocess.check_output(['git', '-C', receipt['before']['pwd'], 'show', head + ':geometry-web/app.js'])
        check(kind + ':' + name + ':trace-app-response-metadata-bound', served['app.js']['status'] == 200 and served['app.js']['version'] == expected_version and int(served['app.js']['contentLength']) == len(app_bytes))
        check(kind + ':' + name + ':trusted-events', len(audit['events']) > 0 and all(e['trusted'] is True for e in audit['events']) and len([e for e in audit['events'] if e['type'] == 'click' and e['id'] == 'feApplyProj']) == 1)
        check(kind + ':' + name + ':terminal-functions', all(c['phase'] == 'settled' for k in ['apply', 'downs', 'moves', 'ups', 'loads'] for c in audit[k]) and len(audit['apply']) == len(audit['downs']) == len(audit['ups']) == 1 and len(audit['moves']) == 4)
        start_drag = {'kind': 'holeRect', 'x0': 500, 'y0': 500, 'x1': 500, 'y1': 500}
        final_drag = {**start_drag, 'x1': 800, 'y1': 800}
        check(kind + ':' + name + ':normal-gesture-coordinates', audit['downs'][0]['trusted'] is True and audit['downs'][0]['after']['drag'] == start_drag and audit['ups'][0]['before']['drag'] == final_drag and audit['ups'][0]['after']['drag'] is None and audit['ups'][0]['after']['work'] is None)
        mouse_calls = [t for t in timeline if t['type'] == 'before' and t.get('method') in ['mouseMove', 'mouseDown', 'mouseUp']]
        check(kind + ':' + name + ':one-ordinary-trace-gesture', [t['method'] for t in mouse_calls] == ['mouseMove', 'mouseDown', 'mouseMove', 'mouseUp'] and mouse_calls[2]['params'].get('steps') == 3 and not any(t.get('params', {}).get('force') for t in timeline))
        check(kind + ':' + name + ':no-page-or-harness-errors', row['pageErrors'] == [] and row.get('harnessError') is None)
        if kind == 'after-held-original':
            check(kind + ':' + name + ':original-failure-kept', row['ok'] is False and row['error'] == 'B real completion differs from fixed exact geometry')
            check(kind + ':' + name + ':owner-preservation-actually-passed', row.get('before') is None and load(folder / (name + '-owners.json'))['before'] == load(folder / (name + '-owners.json'))['after'] and audit['gate']['nativeReply'] == {'ok': True} and audit['gate']['phase'] == 'released')
            applied_phase = 'A-held'
        else:
            check(kind + ':' + name + ':normal-control-no-gate', row['ok'] is True and row['noHeldGate'] is True and audit['gate'] is None and row['BCompletion']['exactBWorld'] is True)
            check(kind + ':' + name + ':A-consumed-before-B', audit['apply'][0]['after']['edit']['bid'] == 1 and len(audit['apply'][0]['after']['actualModel']) == 2 and audit['downs'][0]['before']['edit']['bid'] == 7)
            applied_phase = 'normal-A-applied'
        worlds = {phase: read(folder / (name + '-world-' + phase + '.scene')) for phase in ['before', applied_phase, 'B-preview', 'B-finished']}
        expected_A = exact_replace(worlds['before'], A0, A1)
        expected_B = exact_replace(expected_A, B0, BH)
        check(kind + ':' + name + ':complete-world-exact-A-preview-B', worlds[applied_phase] == expected_A == worlds['B-preview'] and worlds['B-finished'] == expected_B)
        dumps = [n for n in network if n['command'] == 'dump' and n['reply'].get('ok') is True]
        check(kind + ':' + name + ':world-raw-network-bound', all(any(n['reply'].get('text', '').encode() == world for n in dumps) for world in worlds.values()))
        hole_index = next(i for i, n in enumerate(network) if n['command'] == command)
        apply_index = next(i for i, n in enumerate(network) if n['command'] == 'line apply-proj 1 c1')
        check(kind + ':' + name + ':world-chronology', apply_index < hole_index and all(n['reply']['text'].encode() == expected_A for n in network[apply_index + 1:hole_index] if n['command'] == 'dump') and all(n['reply']['text'].encode() == expected_B for n in network[hole_index + 1:] if n['command'] == 'dump'))
        trace_origin = next(t for t in timeline if t['type'] == 'context-options')
        up_wall = trace_origin['wallTime'] + mouse_calls[-1]['startTime'] - trace_origin['monotonicTime']
        command_wall = datetime.datetime.fromisoformat(commands[0]['at'].replace('Z', '+00:00')).timestamp() * 1000
        check(kind + ':' + name + ':native-submit-after-mouse-up', command_wall >= up_wall, {'commandWallMs': command_wall, 'mouseUpWallMs': up_wall})
        held_expected = read(folder / (name + '-world-B-expected.scene'))
        check(kind + ':' + name + ':expected-file-bound', held_expected == (exact_replace(expected_A, B0, B0 + ' hole 500,500 800,500 800,800 500,800') if kind == 'after-held-original' else expected_B))
        loaded[kind]['widths'][width] = {'worlds': worlds, 'events': audit['events'][-7:], 'mouseCalls': mouse_calls, 'network': network}
        case_reports.append({'group': kind, 'name': name, 'sourceSHA': head, 'dirty': receipt['before']['dirty'], 'nativeCommand': command, 'nativeReply': commands[0]['reply'], 'worlds': {p: sha(w) for p, w in worlds.items()}, 'pointerGestureEvents': audit['events'][-7:], 'traceMouseCalls': mouse_calls, 'traceSourceCapture': served})

for width in [1382, 390]:
    group = [loaded[k]['widths'][width] for k in ['baseline-normal', 'after-normal', 'after-held-original']]
    for phase in ['before', 'B-preview', 'B-finished']:
        check(str(width) + ':historical-normal-and-held-full-world-match:' + phase, group[0]['worlds'][phase] == group[1]['worlds'][phase] == group[2]['worlds'][phase])
    check(str(width) + ':normal-and-held-input-events-exact-match', group[0]['events'] == group[1]['events'] == group[2]['events'])
    check(str(width) + ':normal-and-held-trace-pointer-params-exact-match', [t['params'] for t in group[0]['mouseCalls']] == [t['params'] for t in group[1]['mouseCalls']] == [t['params'] for t in group[2]['mouseCalls']])
    baseline = PROJ / 'baseline-f980-r2'
    name = 'held-A-B-hole-' + str(width)
    row = load(baseline / (name + '.json'))
    check(str(width) + ':earlier-baseline-failed-before-hole-completion', row['ok'] is False and row['error'] == 'A late successful apply-proj changed B live gesture/model/owner/DOM' and not (baseline / (name + '-world-B-finished.scene')).exists())

proof = load(NORMAL / 'normal-hole-historical-order-proof.json')
check('parent-proof-receipt-hashes-correct', proof['oldReceipt']['sha256'] == sha(read(proof['oldReceipt']['path'])) and proof['newReceipt']['sha256'] == sha(read(proof['newReceipt']['path'])))
failures = [c for c in checks if not c['ok']]
report = {
    'actor': '/root/race_review/hole_order_oracle_review',
    'independence': 'Distinct reviewer; not original probe author or executor. Read-only inspection of preserved raw artifacts. No browser/service launched and no product, repository, test or executor modified.',
    'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'verdict': 'pass' if not failures else 'fail',
    'checksPassed': len(checks) - len(failures), 'checksFailed': len(failures),
    'checks': checks, 'cases': case_reports, 'artifacts': artifacts,
    'conclusion': 'Both clean versions and both viewport widths submit the same exact ordered native hole command and preserve identical complete World bytes before, during preview and after finish; original held after result reproduces that historical normal flow. One-line BH expected-only correction retains every assertion and all other executable AST. Original 8/2 after failure remains preserved. Proposed correction is not a new executed green result.',
    'limits': ['Artifact review, not a fresh browser run.', 'Trace app.js response body is absent in all six raw traces: exact served app.js bytes are unknown from trace alone. Status, runtime header and Content-Length match recorded source/version; source git-object and receipt hashes separately verified. This extra limitation does not affect raw native command, World or pointer proof.', 'No Windows originals or golden comparison.', 'No aggregate full CDP or complete #123 acceptance.', 'No new public contract or product behavior approved.', 'Review r1 reader missed a wrapper schema alias and stopped; preserved. Review r2 extra body check treated absent trace JS body as an empty body mismatch; original 146-pass/6-fail review and script preserved, corrected to explicit unknown instead of asserting browser JS bytes. Neither iteration changed product, fixture, executor or product assertions.'],
}
OUT.mkdir(exist_ok=True)
path = OUT / 'independent-hole-order-review.json'
path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'verdict': report['verdict'], 'pass': report['checksPassed'], 'fail': report['checksFailed'], 'report': str(path), 'sha256': sha(path.read_bytes()), 'failures': failures}, ensure_ascii=False))
sys.exit(1 if failures else 0)
