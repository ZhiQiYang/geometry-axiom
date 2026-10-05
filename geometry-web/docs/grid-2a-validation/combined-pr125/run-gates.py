from pathlib import Path
import datetime, json, os, subprocess, time

repo = Path('/workspace/pr130-integration')
out = Path('/tmp/pr130-combined-20261004')
identity = json.loads((out/'identity.json').read_text())
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip() == identity['testedHead']
jobs = {}
for index, (label, flag) in enumerate([('grid','GEOMETRY_GRID_SYSTEM_ONLY'), ('infinite-face','GEOMETRY_INFINITE_FACE_ONLY'), ('selection','GEOMETRY_SELECTION_CURSOR_ONLY')]):
    service = identity['services'][label]
    env = dict(os.environ, GEOMETRY_TEST_URL=f"http://127.0.0.1:{service['port']}/", GEOMETRY_FEEDBACK_DIR=service['feedback'], GEOMETRY_CHROME='/usr/bin/chromium', GEOMETRY_CHROME_FLAGS='--no-sandbox', GEOMETRY_CDP_PORT=str(9370+index), GEOMETRY_CHROME_PROFILE=str(out/('chrome-'+label)))
    env[flag] = '1'
    jobs[label] = (['node','geometry-web/cdp_test.js'], env)
service = identity['services']['b-menu']
jobs['b-menu'] = (['node','--require',str(out/'chromium-environment.cjs'),'tests/test_issue116_browser.js'], dict(os.environ, GEOMETRY_TEST_URL=f"http://127.0.0.1:{service['port']}/", GEOMETRY_FEEDBACK_DIR=service['feedback'], GEOMETRY_ISSUE116_EVIDENCE=str(out/'b-menu')))
service = identity['services']['pointer']
jobs['pointer'] = (['python','geometry-web/grid_definition_interaction_browser_test.py'], dict(os.environ, GEOMETRY_VERIFY_ROOT=str(repo), GEOMETRY_TEST_URL=f"http://127.0.0.1:{service['port']}/", GEOMETRY_GRID_INTERACTION_OUT=str(out/'pointer')))
jobs['diagram'] = (['node','--test','tests/test_grid_definition_diagram.js'], dict(os.environ))
jobs['viewer'] = (['node','tests/test_model_viewer.cjs'], dict(os.environ))
processes = {}
receipts = {}
for label, (cmd, env) in jobs.items():
    log = open(out/(label+'.log'),'wb')
    process = subprocess.Popen(cmd,cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT)
    log.close()
    processes[label] = process
    receipts[label] = {'command':cmd,'pid':process.pid,'startedAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'testedHead':identity['testedHead'],'testedTree':identity['testedTree']}
    print(json.dumps({'started':label,'pid':process.pid}),flush=True)
while processes:
    for label, process in list(processes.items()):
        code = process.poll()
        if code is None: continue
        receipts[label].update(exitCode=code,finishedAtUTC=datetime.datetime.now(datetime.timezone.utc).isoformat())
        print(json.dumps({'finished':label,'exitCode':code}),flush=True)
        del processes[label]
    (out/'gate-exits.json').write_text(json.dumps(receipts,indent=2)+'\n')
    if processes: time.sleep(.5)
print(json.dumps({'completed':True,'failed':[name for name,r in receipts.items() if r['exitCode']]}),flush=True)
raise SystemExit(any(r['exitCode'] for r in receipts.values()))
