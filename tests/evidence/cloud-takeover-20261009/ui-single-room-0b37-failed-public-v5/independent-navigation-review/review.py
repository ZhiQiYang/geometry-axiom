"""Read-only navigation adaptation review; no browser/service/product run."""
import ast
import copy
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

base = Path('<workspace-path>')
out = Path('<workspace-path>')
out.mkdir(exist_ok=True)
proposal_path = base / 'normal-ui-navigation-adaptation-proposal.json'
artifacts, checks, rows = {}, [], []
def sha(data): return hashlib.sha256(data).hexdigest()
def read(path):
    path = Path(path)
    data = path.read_bytes()
    artifacts[str(path)] = {'sha256': sha(data), 'bytes': len(data)}
    return data
def check(name, ok, detail=None):
    checks.append({'check': name, 'ok': bool(ok), **({'detail': detail} if detail is not None else {})})
raw = read(proposal_path)
check('original-proposal-hash', sha(raw) == '730d87cb0b9940d211b651e9b1ae833dad019b090586611dbf04b1dc27f909f4')
proposal = json.loads(raw)
(out / 'reviewed-proposal-730d87cb.json').write_bytes(raw)
for row in proposal['rows']:
    group = row['group']
    old_path, new_path = Path(row['original']['path']), Path(row['adapted']['path'])
    old, new, patch = read(old_path), read(new_path), read(row['patch']['path'])
    check(group + ':source-patch-hashes-bound', sha(old) == row['original']['sha256'] and sha(new) == row['adapted']['sha256'] and sha(patch) == row['patch']['sha256'])
    a, b = ast.parse(old), ast.parse(new)
    counts = {}
    for node_type in [ast.Assert, ast.BoolOp, ast.Compare]:
        first = [ast.dump(n) for n in ast.walk(a) if isinstance(n, node_type)]
        second = [ast.dump(n) for n in ast.walk(b) if isinstance(n, node_type)]
        check(group + ':all-' + node_type.__name__ + '-AST-identical', first == second)
        counts[node_type.__name__] = len(first)
    old_strings = {n.value for n in ast.walk(a) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    new_strings = {n.value for n in ast.walk(b) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    check(group + ':all-geometry-command-oracle-literals-retained', all(s in new_strings for s in old_strings if any(t in s for t in ['outline ', 'hole ', 'arm(', 'gate.', 'commit', 'boundary ', 'A native', 'B completion', 'Stale A', 'late successful', 'changed World'])))
    check(group + ':ordinary-visible-picker-actions-only', '#v3ToolbarSurf' in new.decode() and '[data-v3-tool="rect"]' in new.decode() and not any("click(page,'#workSurf')" == line.strip() or "click(page, '#workSurf')" == line.strip() for line in new.decode().splitlines()))
    related = []
    for p in old_path.parent.iterdir():
        if p.is_file() and p.name != old_path.name and (p.suffix in ['.js', '.md'] or p.name.startswith('run_')) and (new_path.parent / p.name).is_file():
            original, adapted = read(p), read(new_path.parent / p.name)
            check(group + ':related-source-byte-identical:' + p.name, original == adapted)
            related.append({'name': p.name, 'sha256': sha(original)})
    rows.append({'group': group, 'original': row['original'], 'adapted': row['adapted'], 'ASTNodeCounts': counts, 'relatedSources': related,
                 'staticVerdict': 'needs-trusted-visible-route-contract-adaptation' if group == 'cross-b' else 'accepted-navigation-only-pending-real-execution'})

cross = ast.parse(read(base / 'cross-b/edge_transition_probe.py'))
run_case = next(n for n in cross.body if isinstance(n, ast.FunctionDef) and n.name == 'run_case')
route_assignment = next(n for n in run_case.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'route' for t in n.targets))
route_ok_assignment = next(n for n in run_case.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'route_ok' for t in n.targets))
route_fixtures = []
for scope in ['main', 'face']:
    nav = [{'type': 'click', 'id': 'btnObj', 'tool': None, 'trusted': True},
           {'type': 'click', 'id': None, 'tool': 'rect', 'trusted': True},
           {'type': 'change', 'id': 'workSurf', 'value': '732', 'trusted': False},
           {'type': 'click', 'id': None, 'tool': 'edit', 'trusted': True}]
    required = [('click', 'btnObj'), ('change', 'workSurf'), ('click', None)]
    if scope == 'face':
        nav.insert(0, {'type': 'click', 'id': 'workspaceBackButton', 'tool': None, 'trusted': True})
        required.insert(0, ('click', 'workspaceBackButton'))
    env = {'nav': nav, 'required': required, 'held': True}
    env['route'] = eval(compile(ast.Expression(route_assignment.value), '<route-only>', 'eval'), env)
    actual = eval(compile(ast.Expression(route_ok_assignment.value), '<route-ok-only>', 'eval'), env)
    legacy = copy.deepcopy(nav)
    next(v for v in legacy if v.get('id') == 'workSurf')['trusted'] = True
    env['nav'] = legacy
    env['route'] = eval(compile(ast.Expression(route_assignment.value), '<legacy-route-only>', 'eval'), env)
    legacy_ok = eval(compile(ast.Expression(route_ok_assignment.value), '<legacy-route-ok-only>', 'eval'), env)
    check('CrossB:' + scope + ':adopted-trusted-picker-synthetic-consumer-counterexample', actual is False and legacy_ok is True)
    route_fixtures.append({'scope': scope, 'adoptedCapturedRoute': nav, 'currentRouteOracle': actual, 'legacyTrustedConsumerOracle': legacy_ok})

root = Path('<workspace-path>')
app = read(root / 'geometry-web/app.js').decode()
contract = read(root / 'geometry-web/docs/DOM-CONTRACT.md').decode()
instrument = read(base / 'cross-b/edge_transition_instrumentation.js').decode()
check('source-contract-hidden-consumer-visible-picker', "sel.closest('label').hidden=true" in app and '原 `#workSurf` 作隱藏相容值／consumer' in contract and '唯一可見入口 `#v3ToolbarSurf`' in contract)
check('visible-picker-dispatches-synthetic-consumer-change', '$("workSurf").dispatchEvent(new Event("change"));' in app)
check('CrossB-observer-does-not-capture-trusted-visible-picker-change', "if (event.target.id === 'workSurf')" in instrument and 'v3ToolbarSurf' not in instrument)
identity = {'head': subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip(),
            'dirty': subprocess.check_output(['git', '-C', str(root), 'status', '--short'], text=True),
            'root': str(root)}
report = {
    'actor': '/root/race_review/hole_order_oracle_review', 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'verdict': 'three-navigation-proposals-accepted-cross-b-revision-required',
    'scope': 'Read-only source, contract and pure route-boolean fixture review. No browser, service, formal test or product execution. No proposal or repository modified.',
    'proposal': {'path': str(proposal_path), 'sha256': sha(raw)}, 'sourceIdentityAtReview': identity,
    'checks': checks, 'rows': rows, 'artifacts': artifacts, 'CrossBRouteCounterexamples': route_fixtures,
    'blockingProposalFinding': {'group': 'cross-b', 'problem': 'The adopted toolbar dispatches a trusted visible select change but invokes hidden workSurf with new Event(change), necessarily untrusted. Original instrumentation records only hidden workSurf change; route_ok still requires every recorded route event to be trusted. Four held cases will fail route_ok even if every owner/native/World race condition passes.',
        'next': 'Create an explicit separate observer/route-contract version requiring the real trusted visible picker event and the original intended user keyboard route; independently check hidden consumer synchronization and its internal synthetic event. Preserve every race/owner/token/model/World/native assertion. Do not drop all(trusted), force-click hidden controls, or label synthetic events trusted.'},
    'acceptedOtherScopes': {
        'held-bhit': 'Same A held native hit, real pointer-up before B, B complete handles before release, exact state/World preservation and trusted cv pointer census unchanged. Added toolbar actions occur outside cv and before B snapshot.',
        'held-proj': 'Same A held projection callback, original view switch, B handles ready before A release, complete B state comparison and World equality unchanged.',
        'formal-race': 'Only enter_three navigation changes; all exact native fixtures, geometry, held gates, cancellation paths, pointer provenance, old-up/new-gesture, owner preservation and normal B completion assertions retain identical AST.'},
    'scopeDifferences': ['Cross-B previously used trusted keyboard on legacy workSurf; new proposal changes event target but leaves a stale trusted-target oracle.', 'held-bhit and held-proj previously used select_option; new Home/ArrowDown/Enter produces real normal picker input. The proposal description saying same keyboard sequence applies literally only to Cross-B and formal-race.', 'Formal-race proposal is scratch-only; repository canonical source is merely read as its original and remains the sole root writer responsibility.'],
    'limits': ['No proof of physical actionability, layout or native-select behavior until authorized same-version real browser execution.', 'Additional rect-tool navigation changes intermediate gesture/token history as allowed by current UI route; snapshots and race/original geometry predicates remain unchanged.', 'Original Cross-B 4-pass/4-harness-failure evidence must stay recorded; navigation proposals do not convert it into a green run.']
}
p = out / 'adopted-navigation-independent-review.json'
p.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'verdict': report['verdict'], 'artifactChecksPassed': sum(c['ok'] for c in checks), 'artifactChecksFailed': sum(not c['ok'] for c in checks), 'report': str(p), 'sha256': sha(p.read_bytes())}, ensure_ascii=False))
assert all(c['ok'] for c in checks), [c for c in checks if not c['ok']]
