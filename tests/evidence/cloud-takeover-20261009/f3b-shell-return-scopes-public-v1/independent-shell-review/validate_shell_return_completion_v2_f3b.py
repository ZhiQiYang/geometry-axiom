"""Independent bounded shell-return evidence census; never execute product or service."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
S=Path('<workspace-path>');R=Path('<workspace-path>')
B=S/'geometry-root-shell-cancel-completion-v2-f3b';stem='geometry-root-f3b82857-normal-shell-return-completion-v2'
G=S/(stem+'-gate');L=S/(stem+'-lifecycle');A=Path('/tmp')/(stem+'-gate-artifacts')
HEAD='f3b8285729b42cd22451c98cba1e2ec4514517f3';VERSION='efbcfff4ca94d6a1844228ea59628ee5de24dcd5e337c62f9c0587f5a38c8a11'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_bytes())
for p in [G/'receipt.json',L/'terminal.json',A/'results.json',A/'driver-receipt.json']:assert p.exists(),str(p)
g=load(G/'receipt.json');t=load(L/'terminal.json');s=load(L/'started.json');ready=load(L/'ready-runtime.json');prep=load(B/'preparation.json')
d=load(A/'driver-receipt.json');h=load(A/'results.json');stop=load(L/'owned-stop/terminal-receipt.json');owned=load(L/'owned-stop/identity.json')
raw=(G/'command.log').read_text();rows=[json.loads(x.removeprefix('SHELL_RETURN_RESULT ')) for x in raw.splitlines() if x.startswith('SHELL_RETURN_RESULT ')]
assert len(rows)==1;c=rows[0];checks={}
def ck(name,ok):checks[name]=bool(ok)
cases=[{'width':w,'family':f} for w in [1400,390] for f in ['ASM','SP']]
ck('unique canonical driver schema and bounded cases',c['schema']==d['schema']=='geometry-normal-shell-return-driver/1' and c['cases']==d['scope']['cases']==cases and c['scope']==d['scope'] and d['scope']['mode']=='bounded-normal-shell-return')
ck('all actual counts complete positive and consistent',c['completed'] is d['completed'] is h['completed'] is True and c['passed']==d['passed']==g['acceptanceResult']['passed']==40 and c['failed']==d['failed']==g['acceptanceResult']['failed']==0 and c['checks']==d['checks']==len(h['checks'])==40 and all(x['ok'] is True for x in h['checks']))
ck('all exact four cases complete in helper',h['results']==[{**x,'completed':True} for x in cases])
expected=[]
for w in [1400,390]:
 opener='#btnCreateObject' if w==1400 else '#mobileCreateObject'
 for f,entry,close in [('ASM','#btnNewAssembly','#asmClose'),('SP','#btnNewSectionProfile','#spClose')]:
  expected+=['unique visible original Create entry','one normal physical click precondition '+opener,'one normal physical click precondition '+entry,f'{w} {f} shared original row stays normal flow',f'{w} {f} actual return center hits original control']
  if f=='SP':expected+=['one normal physical click precondition #spCancel',f'{w} SP original Cancel preserves exact native dump']
  expected+=['one normal physical click precondition '+close,f'{w} {f} one original trusted return gesture',f'{w} {f} exact native full dump unchanged',f'{w} {f} same original project bar returns home']
ck('original forty check names and order exactly retained',[x['name'] for x in h['checks']]==expected)
ck('each original click actual positive hit enabled viewport',[x for x in h['checks'] if x['name'].startswith('one normal physical click precondition')] and all(x['detail']['hit'] and x['detail']['disabled'] is False and x['detail']['insideViewport'] and x['detail']['rect']['width']>0 and x['detail']['rect']['height']>0 for x in h['checks'] if x['name'].startswith('one normal physical click precondition')))
ck('four actual geometry cases complete',[{'width':x['width'],'family':x['family']} for x in h['measurements']]==cases)
ck('shared row stays relative original unique active bar',all(x['row']['position']=='relative' and x['identity']=={'barSame':True,'oneBar':True,'insideActive':True} for x in h['measurements']))
ck('return bounds true hit height44 and no shared-row overlap',all(x['button']['hit'] is True and x['button']['disabled'] is False and x['button']['insideViewport'] is True and x['button']['rect']['height']>=44 and x['row']['rect']['bottom']<=x['button']['rect']['top'] for x in h['measurements']))
ck('four original return gestures each exact trusted3',len(h['trusted'])==4 and all(x['width']==k['width'] and x['family']==k['family'] and x['events']==[{'type':v,'isTrusted':True,'id':'asmClose' if k['family']=='ASM' else 'spClose'} for v in ['pointerdown','pointerup','click']] for x,k in zip(h['trusted'],cases)))
ck('fresh zero-profile native fixture and global full dump same',d['started']['nativePrecondition']['profiles']==0 and d['started']['nativePrecondition']['runtime']==ready and d['started']['finalNativeMatchesBaseline'] is True)
ck('driver helper receipts original hashes exact',g['acceptanceResult']['driverReceiptSHA256']==sha(A/'driver-receipt.json') and g['acceptanceResult']['helperReceiptSHA256']==d['helperProbeSHA256']==sha(A/'results.json'))
b,a=g['before'],g['after']
ck('one frozen clean full SHA before after driver helper lifecycle',b['git']==a['git'] and b['git']['head']==HEAD and b['git']['status']=='' and d['started']['head']==d['finished']['head']==h['startedSource']['head']==h['finishedSource']['head']==t['headAfter']==HEAD and d['started']['dirty']==d['finished']['dirty']==h['startedSource']['dirty']==h['finishedSource']['dirty']==t['dirtyBefore']==t['dirtyAfter']=='')
ck('same exact owned fresh runtime',b['runtime']==a['runtime']==ready and ready['fresh'] is True and ready['root']==str(R) and ready['version']==b['sourceVersion']==a['sourceVersion']==VERSION)
for key in ['sourceSha256','executionFiles','executables','liveBridge','actualGatePython','native']:ck(key+' unchanged actual before after',b[key]==a[key])
source_errors=[]
for rel,v in b['sourceSha256'].items():
 if sha(G/'executed-harness-sources'/rel)!=v or hashlib.sha256(subprocess.check_output(['git','show',HEAD+':'+rel],cwd=R)).hexdigest()!=v:source_errors.append(rel)
ck('all recorded product sources exact Git and archive',not source_errors)
ck('actual immutable new helper driver wrapper hashes pinned',all(sha(p)==v==b['executionFiles'][p] and sha(G/'executed-harness-sources/scratch-source'/Path(p).name)==v for p,v in prep['newSources'].items() if Path(p).name!='owned_shell_lifecycle.py'))
ck('original immutable sources preserved',all(sha(p)==v for p,v in prep['originalSources'].items()))
ck('actual controller wrapper command hashes exact',s['controllerSHA256']==sha(B/'owned_shell_lifecycle.py')==prep['newSources'][str(B/'owned_shell_lifecycle.py')] and s['runnerSHA256']==sha(B/'run_normal_shell_return_gate.py') and t['testCommand']==s['testCommand'])
obs=g['executionIdentity'];node=obs['node'];chrome=obs['browser']
ck('actual Node binary PID argv cwd',node['pid']==g['execution']['pid'] and node['cmdline']==g['command']==d['started']['command'] and node['cwd']==str(R) and node['sha256']==b['executables']['node']['sha256']==d['started']['node']['sha256'] and sha(node['executable'])==node['sha256'])
ck('actual Chrome binary hash sandbox and owned profile',chrome['sha256']==b['executables']['actual-chrome']['sha256']==sha(chrome['executable']) and chrome['sandboxDisabledFlagsAbsent'] is True and '--user-data-dir='+chrome['ownedProfile'] in chrome['cmdline'] and not any(x.startswith('--type=') for x in chrome['cmdline']))
ck('observed actual actors during actual command',all(g['execution']['started']<=x['observedUtc']<=g['execution']['finished'] for x in [node,chrome]) if 'observedUtc' in node else g['execution']['started']<=chrome['observedUtc']<=g['execution']['finished'])
ck('actual observer no errors original v3 source',obs['errors']==[] and sha(S/'geometry-ui-verification/run_ui_gate_v3.py')=='94a30d7bd7b7f291e3913e5192f5640152ce27b9a80a7adaebe37e3f48b79f70')
ck('Node gate controller actual zero and bounded verified',g['execution']['exitCode']==g['gateExitCode']==t['actualGateExitCode']==0 and g['probeVerified'] is True and g['acceptanceResult']['completed'] is True and g['problems']==[] and g['execution']['timedOut'] is False and g['execution']['interrupted'] is False)
ck('generic command-only remains no full completion',g['kind']=='command' and g['evidence']['scope']=='command-only' and g['evidence']['completionVerified'] is False and g['releaseApproved'] is False)
ck('driver helper no errors sandbox true',d['error'] is h['error'] is c['error'] is None and d['errors']==c['errors']==[] and d['sandbox'] is c['sandbox'] is True)
ck('original command log hash size matches',g['log']['sha256']==sha(G/'command.log') and g['log']['bytes']==(G/'command.log').stat().st_size)
ck('lifecycle raw files hashes exact',all(sha(L/x['path'])==x['sha256'] and (L/x['path']).stat().st_size==x['bytes'] for x in t['rawFiles']))
ck('actual fresh native and direct bridge bound',len(b['liveBridge'])==1 and b['liveBridge'][0]['sha256']==b['native']['bridge']['sha256'] and all(x['state']=='fresh' and sha(x['path'])==x['sha256'] for x in b['native'].values()))
ck('exact owned stop preserved dump and original session',owned['runtime']==ready and owned['server']==ready['pid'] and set(owned['children'])=={x['pid'] for x in b['liveBridge']} and owned['rootDumpSHA256']==sha(L/'owned-stop/root-dump.raw.json') and stop['exitCode']==t['stopExitCode']==0 and stop['portObservation']['accepting'] is False)
old=Path(next(p for p in prep['originalSources'] if p.endswith('normal_asm_sp_return_probe.cjs'))).read_text()
new=(B/'normal_asm_sp_return_probe.cjs').read_text()
oldpart="if(cancel&&await page.locator(cancel).isEnabled()){await normalClick(cancel);check(width+' SP original Cancel preserves exact native dump',await dump()===before);}"
start=new.index('if(cancel&&await page.locator(cancel).isEnabled()){');end=new.index("\n        const count=",start)
ck('helper delta only original Cancel completion wait',new[:start]+oldpart+new[end:]==old)
ck('bounded success status and enablement added no retry force',"{timeout:20000}" in new[start:end] and "textContent==='已取消修改，未改動世界。'" in new[start:end] and "?.disabled===true" in new[start:end] and "?.disabled===false" in new[start:end] and new[start:end].count('normalClick(cancel)')==1)
current={'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'dirty':subprocess.check_output(['git','status','--porcelain'],cwd=R,text=True)}
ck('candidate still frozen after readonly census',current=={'head':HEAD,'dirty':''})
out=S/'geometry-ui-verification/supplementary-validation-f3b-shell-return-completion-v2.json';assert not out.exists()
log=out.with_suffix('.raw.log');log.write_text('\n'.join(('PASS ' if v else 'FAIL ')+k for k,v in checks.items())+'\n')
sources=[G/'receipt.json',G/'command.log',L/'terminal.json',L/'started.json',L/'ready-runtime.json',L/'owned-stop/terminal-receipt.json',L/'owned-stop/identity.json',A/'driver-receipt.json',A/'results.json',B/'preparation.json',Path(__file__)]
record={'schema':'geometry-bounded-shell-return-independent-census/1','checkedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'testedFullSHA':HEAD,'dirty':'','actor':'/root/ui_tail_contract','actualCommand':sys.orig_argv,'actualPython':str(Path('/proc/self/exe').resolve()),'actualPythonSHA256':sha('/proc/self/exe'),'checks':checks,'integrityVerified':all(checks.values()),'boundedFourCaseAccepted':all(checks.values()),'fullCompletionClaimed':False,'productCases':4,'productAssertions':40,'originalCanonical':c,'actualExecution':g['execution'],'actualObservedActors':obs,'stopProcessObservations':stop['processObservations'],'sourceHashErrors':source_errors,'sourceHashes':{str(p):sha(p) for p in sources},'rawReviewLogSHA256':sha(log),'exitCode':0 if all(checks.values()) else 1,'limits':['Metadata/log/source census only; no additional browser/native/product execution.','New20s wait observes original asynchronous Cancel completion; previous16/1 and ca3 bytes retained.','This is four bounded entry/Cancel/return cases, not full CDP/golden, standaloneSpace or all43 acceptance.','Original observed stopped zombie states remain reported, not relabeled absent.']}
out.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'proof':str(out),'sha256':sha(out),'checks':len(checks),'passed':sum(checks.values()),'failed':[k for k,v in checks.items() if not v],'boundedFourCaseAccepted':record['boundedFourCaseAccepted']}));sys.exit(record['exitCode'])

