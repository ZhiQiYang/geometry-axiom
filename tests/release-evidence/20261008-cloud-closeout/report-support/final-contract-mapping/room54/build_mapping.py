from pathlib import Path
import datetime, hashlib, json, subprocess

OUT = Path(__file__).resolve().parent
REPO = Path('/workspace/geometry-axiom')
EVIDENCE = Path('/workspace/closure-evidence')
GATES = EVIDENCE / 'public-candidate/gates'
TESTED = '5174a8dafd8c48329d7166abbd3d104e3c28c0c4'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
def cmd(args):
    r = subprocess.run(args, cwd=REPO, capture_output=True, text=True)
    return dict(command=args, stdout=r.stdout, stderr=r.stderr, exit_code=r.returncode)

identity = [cmd(['pwd']), cmd(['git','status','--short']), cmd(['git','rev-parse','HEAD'])]
identity += [cmd(['git','merge-base','--is-ancestor', h, TESTED]) for h in [
    '349e2a590f98ab783b7d3eeb952e95151db8e39e',
    'f1e020cba5051a331dd150d567698060bf1642b1']]
write('review-command-evidence.json', identity)
issue = EVIDENCE / 'inventory/issue-54.json'
issue_data = json.loads(issue.read_text())
(OUT / 'issue54-body.txt').write_text(issue_data['body'] + '\n')
prs_path = EVIDENCE / 'inventory/publication-review/remote-pre-publication-final/open-prs.json'
prs = [p for p in json.loads(prs_path.read_text()) if p['number'] in (153,155)]
write('pr153-pr155-deliveries.json', [{k:p[k] for k in ['number','html_url','title','updated_at','body']} | {
    'head': p['head']['sha'], 'base': p['base']['sha'],
} for p in prs])
for p in prs: (OUT / ('pr%d-body.txt' % p['number'])).write_text(p['body'] + '\n')

gate_data = []
sources = [issue, prs_path]
for name in ['room-acceptance','room-pan','room-worker','room-keyboard','room-keyboard-r2','full-cdp-r3']:
    p = GATES/name
    audit = json.loads((p/'audit.json').read_text())
    gate_data.append({k:audit.get(k) for k in ['gate','head','counts','command','commandExitCode','gateExitCode',
        'verdict','dirtyBefore','dirtyAfter','runtimeBefore','runtimeAfter','limitations']})
    sources += [p/'audit.json',p/'command.log']
    if (p/'receipt.json').exists(): sources += [p/'receipt.json']
    if (p/'artifacts/results.json').exists():
        r = json.loads((p/'artifacts/results.json').read_text())
        write(name+'-oracle-index.json', [{'index':i, 'name':v.get('name',v.get('label')), 'ok':v.get('ok')}
            for i,v in enumerate(r.get('results',[]))])
        sources += [p/'artifacts/results.json']
    sources += list((p/'sources/tests').glob('room_outline*'))
write('gates.json', gate_data)
acceptance = json.loads((GATES/'room-acceptance/artifacts/results.json').read_text())
cost = [{
    'scenario': m['scenario'], 'candidate': {k:m['candidate'][k] for k in ['actions','elapsedMs']},
    'manual': {k:m['manual'][k] for k in ['actions','elapsedMs']},
    'candidate_minus_manual_actions':m['candidate']['actions']-m['manual']['actions'],
    'identical_recorded_start': m['candidate']['start']==m['manual']['start'],
    'definition':m['definition'],
} for m in acceptance['measurements']]
write('acceptance-cost-measurements.json', cost)
full_cdp_measurements = []
for line in (GATES/'full-cdp-r3/command.log').read_text().splitlines():
    if 'ROOM_OUTLINE_MEASUREMENTS ' in line:
        full_cdp_measurements.extend(json.loads(line.split('ROOM_OUTLINE_MEASUREMENTS ',1)[1]))
write('full-cdp-p79-cost-measurements.json',full_cdp_measurements)
docs = ['AGENTS.md','geometry-guide/PRODUCT-VISION.md','公理層.md','BACKLOG.md','決策佇列.md',
    'geometry-guide/CONTINUATION-WORK-PACKAGES-20261003.md',
    'geometry-guide/CONTINUATION-DECISIONS-20261003.md',
    'geometry-guide/PROJECT-REVIEW-QUEUE-20261004.md',
    'geometry-web/docs/ROOM-OUTLINE.md','geometry-web/docs/ISSUE54-VALIDATION.md',
    'geometry-web/docs/issue54-closeout-20261006.md','tests/INTEGRATION-GATES.md',
    'tests/room_outline_acceptance_browser.js','tests/room_outline_pan_browser.js',
    'tests/room_outline_worker_browser.js','tests/room_outline_keyboard_browser.js',
    'geometry-web/room_outline_test.js']
sources += [REPO/p for p in docs]
source_manifest = [{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(sources))]
write('source-manifest.json', {
    'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'tested_head':TESTED, 'read_only_product_review':True,
    'no_new_browser_native_or_product_tests':True,
    'files':source_manifest,
})
print(json.dumps({'output':str(OUT),'sources':len(source_manifest),
    'current_acceptance_measurements':len(cost),'current_p79_measurements':len(full_cdp_measurements),
    'repo_identity':identity[:3]},ensure_ascii=False))
