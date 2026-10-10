"""Read-only source/VM review; never execute controller, launch or stop scripts."""
from pathlib import Path
import ast, copy, datetime, difflib, hashlib, json, subprocess, sys

ROOT=Path('<workspace-path>')
OUT=Path('<workspace-path>')
EXPECTED='9eb670110379ec0d726914f3e5b2d8e7237f2b9c'
VERSION='7c6a3a77c727ec51537923b5accfb69e1e3acefcf59a553749bc986b82f87cd7'
BASE=Path('<workspace-path>')
FILES={name:BASE/name for name in [
 'geometry-owned-integration-lifecycle.py','geometry-stop-with-terminal-receipt.py',
 'geometry-stop-with-terminal-receipt-v2.py','geometry-stage-launch.py',
 'geometry-owned-full-stage-stop.py','geometry-stage-stop.py']}
FILES.update({name:BASE/'geometry-takeover-evidence-harness'/name for name in [
 'run_full_cdp_identity.py','run_full_space_identity.py']})
LIFE=BASE/'geometry-root-9eb67011-recovered-full-cdp-lifecycle'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
before={'head':git('rev-parse','HEAD'),'dirty':git('status','--porcelain=v1','--untracked-files=all')}
checks=[]
def check(name,ok,detail=None):checks.append({'name':name,'ok':bool(ok),'detail':detail})
def rejects(code,env):
 try:exec(code,env);return False
 except (AssertionError,KeyError,TypeError):return True
def compile_nodes(nodes):return compile(ast.fix_missing_locations(ast.Module(body=copy.deepcopy(nodes),type_ignores=[])),'<extracted-original-guards>','exec')
texts={k:p.read_text() for k,p in FILES.items()}
trees={k:ast.parse(v,filename=str(FILES[k])) for k,v in texts.items()}
check('all eight scripts parse without execution',len(trees)==8)
check('current tracked candidate clean and exact',before=={'head':EXPECTED,'dirty':''},before)
expected_hashes={
 'run_full_cdp_identity.py':'5ce8212de96e45d0b613b17888a053a7a679024dc1a230f4c734a6170cc5da89',
 'run_full_space_identity.py':'8b9729cb300347361b2f6bf507e08fd6fab662ec2bc9f0fca107fb2da02dadae'}
for k,h in expected_hashes.items():check(k+' original runner exact bytes',sha(FILES[k])==h)
controller=texts['geometry-owned-integration-lifecycle.py']; tree=trees['geometry-owned-integration-lifecycle.py']
stop=texts['geometry-stop-with-terminal-receipt-v2.py'];old=texts['geometry-stop-with-terminal-receipt.py']
added="for gate in gates:\n    binding = gate.get('executionIdentity', {}).get('liveBinding') or {}\n    for process in binding.get('processes', []):\n        if process.get('pid'):\n            pids[process['pid']] = process.get('role', 'actual full integration process')\n"
check('stop v2 delta only records liveBinding process observations',stop.replace(added,'',1)==old and stop.count(added)==1)
check('stop v2 adds no signal or broadened helper call',not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('kill','killpg','terminate') for n in ast.walk(trees['geometry-stop-with-terminal-receipt-v2.py'])))
check('controller launches no filtered or override suite',all(x not in controller for x in ['--groups','--probe-source','--probe-sha','GEOMETRY_CDP_FROM','_ONLY','UPDATE_GOLDEN']))
check('original CDP and Space canonical commands retained',"command=['node','geometry-web/cdp_test.js']" in texts['run_full_cdp_identity.py'] and "command=['node','geometry-web/space_model_test.js']" in texts['run_full_space_identity.py'])
check('launch retains service PID through execve and checks port twice',texts['geometry-stage-launch.py'].count('launcher.check_port(port)')==2 and 'os.execve(sys.executable' in texts['geometry-stage-launch.py'])
runtime_asserts=[n for n in ast.walk(tree) if isinstance(n,ast.Assert) and 'runtime' in ast.unparse(n.test)]
assert len(runtime_asserts)==2
runtime_guards=compile_nodes(runtime_asserts)
from types import SimpleNamespace
normal={'pid':232256,'root':str(ROOT),'fresh':True,'version':VERSION}
env={'runtime':normal,'service':SimpleNamespace(pid=232256),'root':ROOT,'runtime_version':VERSION}
exec(runtime_guards,env);check('exact owned ready runtime accepted in VM',True)
for label,value in [('missing',None),('wrong PID',{**normal,'pid':123}),('wrong root',{**normal,'root':'<workspace-path>'}),('stale',{**normal,'fresh':False}),('wrong version',{**normal,'version':'old'})]:
 check('ready guard rejects '+label,rejects(runtime_guards,{**env,'runtime':value}))
top_asserts=[n for n in tree.body if isinstance(n,ast.Assert)]
git_guard=[n for n in top_asserts if 'rev-parse' in ast.unparse(n)][0]
guard=compile_nodes([git_guard])
for label,head,dirty in [('wrong HEAD','old',''),('dirty',EXPECTED,' M app.js')]:
 check('before source guard rejects '+label,rejects(guard,{'git':lambda a,h=head,d=dirty:h if a[0]=='rev-parse' else d,'expected':EXPECTED}))
hash_guard=[n for n in top_asserts if 'hexdigest' in ast.unparse(n)][0]
class BadRunner:
 def read_bytes(self):return b'changed original wrapper'
check('runner hash guard rejects changed wrapper',rejects(compile_nodes([hash_guard]),{'hashlib':hashlib,'runner':BadRunner(),'expected_runner':expected_hashes['run_full_cdp_identity.py']}))
check('receipt required before invoking any stop helper',controller.index("assert (output / 'receipt.json').exists()")<controller.index("result = subprocess.run(stop_command"))
check('actual gate exit propagated rather than invented',"record['actualGateExitCode'] = test.returncode" in controller and "sys.exit(record['actualGateExitCode'])" in controller)
check('readiness and original gate bounds retained',"time.monotonic() + 30" in controller and "'--timeout', '2400'" in controller)
check('controller writes actual error rather than green terminal on missing receipt',"record['controllerError'] = repr(exc)" in controller and "raise\nrecord['finishedUtc']" in controller)
loops=[n for n in trees['geometry-stop-with-terminal-receipt-v2.py'].body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='gate']
assert len(loops)==2
merge=compile_nodes(loops)
for label,gates,expected in [
 ('old node/browser',[{'executionIdentity':{'node':{'pid':3},'browser':{'pid':4}}}],{1,2,3,4}),
 ('new nested binding',[{'executionIdentity':{'liveBinding':{'processes':[{'pid':5,'role':'node'},{'pid':6,'role':'chrome'}]}}}],{1,2,5,6}),
 ('absent and null',[{}, {'executionIdentity':{'liveBinding':None}}],{1,2}),
 ('mixed duplicate/missing PID',[{'executionIdentity':{'node':{'pid':3},'liveBinding':{'processes':[{'pid':3},{'role':'missing PID'},{'pid':0}]}}}],{1,2,3})]:
 e={'gates':gates,'pids':{1:'owned server',2:'owned bridge'}};exec(merge,e);check('stop observation census '+label,set(e['pids'])==expected,e['pids'])
for name in ['geometry-owned-full-stage-stop.py','geometry-stage-stop.py']:
 s=texts[name];t=trees[name]
 check(name+' validates root/cwd/serve identity before signals',all(x in s for x in ["Path(runtime['root']).resolve()==root","proc.joinpath('cwd').resolve()==root","str(root/'geometry-web/serve.py').encode()"] ) and s.index("request=urllib.request.Request")<s.index('for child in children:os.kill'))
 check(name+' signals only validated direct-child native and server',"if parent==pid:" in s and "assert p.joinpath('exe').resolve()==bridge" in s and [ast.unparse(n.args[0]) for n in ast.walk(t) if isinstance(n,ast.Call) and ast.unparse(n.func)=='os.kill']==['pid','child'])
 check(name+' preserves genuine native dump before termination',"assert json.loads(raw)['ok']" in s and "root-dump.raw.json" in s and s.index("root-dump.raw.json")<s.index('os.kill'))
started_path=LIFE/'started.json';ready_path=LIFE/'ready-runtime.json'
started=json.loads(started_path.read_bytes());ready=json.loads(ready_path.read_bytes())
check('actual started record binds controller/launch/runner bytes',started['controllerSHA256']==sha(FILES['geometry-owned-integration-lifecycle.py']) and started['launchSHA256']==sha(FILES['geometry-stage-launch.py']) and started['runnerSHA256']==expected_hashes['run_full_cdp_identity.py'])
check('actual recorded interpreter hash matches file',started['actualPythonSHA256']==sha(started['actualPython']))
check('actual recorded command has correct CDP root/SHA/native/url and no filters',started['testCommand']==[started['actualPython'],str(FILES['run_full_cdp_identity.py']),'--root',str(ROOT),'--url','http://127.0.0.1:19182/','--output',str(BASE/'geometry-root-9eb67011-recovered-full-cdp-gate'),'--expected-head',EXPECTED,'--bridge','<isolated-test-directory>','--model-base','<isolated-test-directory>','--feedback-dir','<isolated-test-directory>','--timeout','2400'])
check('actual ready record binds unique owned service',ready['pid']==232256 and ready['root']==str(ROOT) and ready['fresh'] is True and ready['version']==VERSION)
live={}
proc=Path('/proc')/str(ready['pid'])
for key in ['exe','cwd']:
 try:live[key]=str((proc/key).resolve(strict=True))
 except FileNotFoundError:live[key]=None
try:live['cmdline']=(proc/'cmdline').read_bytes().replace(b'\0',b' ').decode()
except FileNotFoundError:live['cmdline']=None
if live['exe']:
 live['exeSHA256']=sha(proc/'exe')
 check('actual current service exe/cwd/cmdline match ready owned identity',live['exeSHA256']==started['actualPythonSHA256'] and live['cwd']==str(ROOT) and str(ROOT/'geometry-web/serve.py')+' 19182' in (live['cmdline'] or ''),live)
else:check('current service no longer observable; no reconstructed live claim',True,live)
after={'head':git('rev-parse','HEAD'),'dirty':git('status','--porcelain=v1','--untracked-files=all')}
check('tracked source untouched by independent review',before==after)
OUT.mkdir(exist_ok=False)
log='\n'.join(('PASS ' if x['ok'] else 'FAIL ')+x['name'] for x in checks)+'\n'
(OUT/'command.raw.log').write_text(log)
receipt={'schema':'geometry-owned-lifecycle-readonly-source-review/1','checkedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'testedFullSHA':EXPECTED,'before':before,'after':after,'executor':{'command':sys.orig_argv,'actualPython':str(Path('/proc/self/exe').resolve()),'actualPythonSHA256':sha('/proc/self/exe'),'scriptSHA256':sha(__file__)},
 'sourceHashes':{str(p):sha(p) for p in FILES.values()},'recordHashes':{str(p):sha(p) for p in [started_path,ready_path]},'observedCurrentService':live,
 'checks':checks,'passed':sum(x['ok'] for x in checks),'failed':sum(not x['ok'] for x in checks),'exitCode':0 if all(x['ok'] for x in checks) else 1,
 'rawLog':{'path':str(OUT/'command.raw.log'),'sha256':sha(OUT/'command.raw.log')},'browserExecuted':False,'serviceStartedOrStopped':False,'repoWritten':False,
 'limits':['Source/VM and existing start/ready records only; never executes lifecycle/launch/stop or acceptance harness.',
 'Recovered integration is not counted complete before its original terminal receipt, canonical scope census and golden check.',
 'Stop v2 observes actual gate processes; only immutable helper signals root/port-validated server and direct native children.',
 'Helpers assume exclusively owned port. Final receipt must compare stopped identity with ready PID/runtime; source alone does not prove future stop ownership.',
 'On controller error, an error receipt is written and success is not manufactured; source does not guarantee automatic cleanup on every exception.',
 'Historical noReceipt outputs retain unknown original wrapper/Node exits and identity; no old partial is added to recovery counts.']}
(OUT/'review.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'review':str(OUT/'review.json'),'sha256':sha(OUT/'review.json'),'passed':receipt['passed'],'failed':receipt['failed'],'scope':'readonly source/VM, not product acceptance'}))
sys.exit(receipt['exitCode'])
