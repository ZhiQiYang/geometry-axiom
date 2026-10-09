"""Read sealed ASM gate and distinct failed lifecycle/recovered-stop evidence."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
ROOT=Path('<workspace-path>');S=Path('<workspace-path>')
HEAD='f3b8285729b42cd22451c98cba1e2ec4514517f3';VERSION='efbcfff4ca94d6a1844228ea59628ee5de24dcd5e337c62f9c0587f5a38c8a11'
G=S/'geometry-root-f3b82857-original-assembly-gate';L=S/'geometry-root-f3b82857-original-assembly-lifecycle';T=S/'geometry-root-f3b82857-original-assembly-stop-recovery'
OUT=S/'geometry-ui-verification/supplementary-validation-f3b-original-assembly.json'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def load(p):return json.loads(Path(p).read_bytes())
def ident(p):return {'path':str(p),'bytes':Path(p).stat().st_size,'sha256':sha(p)}
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
assert not OUT.exists()
r=load(G/'receipt.json');error=load(L/'controller-error.json');started=load(L/'started.json');ready=load(L/'ready-runtime.json');stop=load(T/'terminal-receipt.json');owned=load(T/'identity.json')
raw=(G/'command.log').read_text(errors='replace');rows=[json.loads(l[len('CDP_RESULT '):]) for l in raw.splitlines() if l.startswith('CDP_RESULT ')];scopes=[json.loads(l[len('CDP_SCOPE '):]) for l in raw.splitlines() if l.startswith('CDP_SCOPE ')]
assert len(rows)==len(scopes)==1
actual=rows[0];before,after=r['before'],r['after'];scope=actual['scope'];checks={}
def check(n,v):checks[n]=bool(v)
check('actual partial completed with original150 positive assertions',actual['completed'] is True and actual['passedAssertions']==150 and actual['failedAssertions']==0 and actual['skipped']==[] and actual['uncaughtBrowserExceptions']==0)
check('original P77/P82 complete exact section census',actual['sections']=={'P77':134,'P82':16} and sum(actual['sections'].values())==actual['passedAssertions'])
check('explicit original partial soleflag with no golden claim',scope['mode']=='partial' and scope['filters']==['GEOMETRY_ASSEMBLY_ONLY'] and scope['modifiers']==[] and actual['goldenCompare']=='not compared (partial mode)')
check('initial/canonical/live observed original scopes exactly agree',scope==scopes[0]==r['executionIdentity']['liveBinding']['cdpScope'])
check('original Node and gate actual exit0 verified',r['execution']['exitCode']==r['gateExitCode']==error['actualGateExitCode']==0 and r['executionVerified'] is True and r['status']=='execution-verified' and r['problems']==[] and r['releaseApproved'] is False)
check('original canonical command retained',r['command']==['node','geometry-web/cdp_test.js'])
check('exact tested candidate clean before/after',before['git']==after['git'] and before['git']['head']==HEAD and before['git']['status']=='')
check('same original runtime fresh/same unique native session',before['runtime']==after['runtime']==ready and ready['pid']==252331 and ready['fresh'] is True and ready['root']==str(ROOT) and ready['version']==before['sourceVersion']==VERSION)
for key in ['sourceSha256','executables','native','liveBridge','runnerSha256','identityObserverSha256','launchAdapterSha256']:
 check(key+' unchanged across actual scope',before[key]==after[key])
mismatches=[]
for rel,digest in before['sourceSha256'].items():
 if hashlib.sha256(subprocess.check_output(['git','show',HEAD+':'+rel],cwd=ROOT)).hexdigest()!=digest or sha(G/'executed-harness-sources'/rel)!=digest:mismatches.append(rel)
check('all original source snapshots and fullSHA Git bytes exact',not mismatches)
check('actual source runner is declared7ab original explicitflag',before['runnerSha256']==started['runnerSHA256']==sha(S/'geometry-takeover-evidence-harness/run_original_assembly_identity_f3b.py')=='7ab184ee4572d40b9c2b1ff86910b373b59c73fb6fac462c3a0e11b7cf2d3cc4')
check('original raw log exact digest and size',sha(G/'command.log')==r['log']['sha256'] and (G/'command.log').stat().st_size==r['log']['bytes'])
check('no timeout/interruption of actual productscope',r['execution']['timedOut'] is False and r['execution']['interrupted'] is False)
binding=r['executionIdentity']['liveBinding'];processes=binding['processes'];node=next(x for x in processes if x['role']=='actual browser parent Node');browser=next(x for x in processes if x['role']=='actual CDP_SCOPE Chromium main process')
check('actual Node/Chromium ELF actors are unique and exact',len(processes)==2 and node['pid']==r['execution']['pid'] and node['cmdline']==r['command'] and node['sha256']==before['executables']['node']['sha256'] and browser['pid']==scope['browserPid'] and all(x['cwd']==str(ROOT) and x['executableMagicHex']=='7f454c46' and sha(x['exe'])==x['sha256'] for x in processes))
check('observed actual Chrome main profile/port binds explicit original scope','--user-data-dir='+scope['browserProfile'] in browser['cmdline'] and '--remote-debugging-port='+str(scope['cdpPort']) in browser['cmdline'] and not any(x.startswith('--type=') for x in browser['cmdline']))
tm=datetime.datetime.fromisoformat
check('live actual actor observation timestamp inside scope',tm(r['execution']['started'])<=tm(binding['observedUtc'])<=tm(r['execution']['finished']))
check('identity observer no errors',r['executionIdentity']['errors']==[])
check('native actual files fresh and exact',len(before['native'])==2 and all(n['state']=='fresh' and sha(n['path'])==n['sha256'] for n in before['native'].values()))
check('direct native bridge belongs actual ready server',len(before['liveBridge'])==1 and before['liveBridge'][0]['parent']==252331 and before['liveBridge'][0]['pid']==252332 and before['liveBridge'][0]['sha256']==before['native']['bridge']['sha256'])
check('original lifecycle cleanup error retained after verified gate',error['stopExitCode']==1 and error['serviceExitBeforeStop'] is None and error['actualServiceExitAfterStop'] is None and "line 9" in error['controllerError'] and '9eb670110379ec0d726914f3e5b2d8e7237f2b9c' in error['controllerError'] and not (L/'terminal.json').exists())
check('original rejection stderr retains exact oldhead assertion','9eb670110379ec0d726914f3e5b2d8e7237f2b9c' in (L/'stop-controller.stderr.raw.log').read_text() and 'AssertionError' in (L/'stop-controller.stderr.raw.log').read_text())
check('original executed controller bytes preserved',started['controllerSHA256']==sha(S/'geometry-owned-integration-lifecycle-f3b.py')=='ef1936a5e400626f21402f89ab205611df42e276062c2b6405357bfc2e0ce15a')
check('new recovered stop source binds exactcc505 candidate',stop['wrapperSHA256']==sha(S/'geometry-stop-with-terminal-receipt-f3b.py')=='cc505b94c1011bed31d350a8670422808ded123e6b058e54e3c7853ff79286a2')
check('recovered stop actual exit0 and same owned ready server',stop['exitCode']==0 and owned['runtime']==ready and owned['server']==252331 and owned['children']==[252332] and stop['portObservation']['accepting'] is False)
check('root preserved actual native dump before stop',sha(T/'root-dump.raw.json')==owned['rootDumpSHA256'])
check('recovery stop hashes all original raw observations',all(sha(T/f['path'])==f['sha256'] and (T/f['path']).stat().st_size==f['bytes'] for f in stop['rawFiles']))
states=stop['processObservations'];check('stop observations include exact actual actors/native',{x['pid'] for x in states}=={252331,252332,node['pid'],browser['pid']})
check('zombies truthfully remain recorded without absence claim',sum(x['exists'] and x['state']=='Z' for x in states)==3 and all(not x['exists'] or x['state']=='Z' for x in states))
check('candidate still clean f3b and reviewer never changed source',git('rev-parse','HEAD')==HEAD and git('status','--porcelain=v1','--untracked-files=all')=='')
log=OUT.with_suffix('.raw.log');log.write_text('\n'.join(('PASS ' if v else 'FAIL ')+n for n,v in checks.items())+'\n')
record={'schema':'geometry-original-assembly-with-independent-stop-recovery-census/1','checkedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'testedFullSHA':HEAD,'dirtyBeforeAfter':'',
 'reviewExecutor':{'command':sys.orig_argv,'actualPython':str(Path('/proc/self/exe').resolve()),'actualPythonSHA256':sha('/proc/self/exe'),'scriptSHA256':sha(__file__)},'exitCode':0 if all(checks.values()) else 1,
 'checks':checks,'passedIntegrityChecks':sum(checks.values()),'failedIntegrityChecks':sum(not v for v in checks.values()),'boundedAssemblyAcceptancePassed':all(checks.values()),
 'originalCanonicalResult':actual,'originalActualExecution':r['execution'],'originalGateExitCode':r['gateExitCode'],'originalLifecycle':{'controllerError':error['controllerError'],'postGateStopExitCode':error['stopExitCode'],'terminalMissing':not (L/'terminal.json').exists(),'actualControllerExitCodeFromOriginalFiles':'unknown; parent reports actual unifiedexec70298 exit1 separately'},
 'recoveredCleanup':{'actualExitCode':stop['exitCode'],'identity':owned,'processObservations':states,'portObservationAtStop':stop['portObservation']},
 'actualObservedActors':r['executionIdentity'],'sources':[ident(p) for p in [G/'receipt.json',G/'command.log',L/'started.json',L/'ready-runtime.json',L/'controller-error.json',L/'stop-controller.stdout.raw.log',L/'stop-controller.stderr.raw.log',T/'terminal-receipt.json',T/'identity.json',T/'root-dump.raw.json']],
 'rawReviewLog':ident(log),'sourceSnapshotMismatches':mismatches,'browserExecuted':False,'serviceStartedOrStopped':False,'repoWritten':False,
 'limits':['Product150/0/0 Node/gate0 and completed partial scope are distinct from post-gate original lifecycle rejection and subsequent exactowned stop0.',
 'Original lifecycle70298 exit1 is parent-reported actual tool terminal; source receipt records stop1/error, not a controller process returncode. Do not manufacture missing lifecycle terminal.',
 'Three observed zombies remain Z, not absent; no historical process state is reconstructed and no currently running fresh FULL service is queried/stopped.',
 'Original explicit ASM scope is not fullCDP/golden, SP workspace, standaloneSpace, caption/SIX or all43 acceptance.',
 'No product run or re-run was started for this review; full f3b terminal is still independent and pending.']}
OUT.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'proof':str(OUT),'sha256':sha(OUT),'passed':record['passedIntegrityChecks'],'failed':record['failedIntegrityChecks'],'assemblyAcceptance':record['boundedAssemblyAcceptancePassed'],'fullAcceptance':False}))
sys.exit(record['exitCode'])
