"""Terminal-only durable FULL launcher/kernel chain review; no product/service execution."""
from pathlib import Path
import ast,datetime,hashlib,json,os,subprocess,sys
S=Path('<workspace-path>');R=Path('<workspace-path>');stem='geometry-root-f3b82857-durable-full-cdp'
L=S/(stem+'-lifecycle');D=S/(stem+'-detached-launch');G=S/(stem+'-gate')
proof=S/'geometry-ui-verification/supplementary-validation-f3b-durable-full-cdp.json'
OUT=S/'geometry-ui-verification/f3b-durable-full-launch-kernel-review-v2';assert not OUT.exists()
for p in [proof,L/'terminal.json',D/'launch.json',G/'receipt.json']:assert p.is_file(),str(p)+' not sealed'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_bytes())
main=load(proof);launch=load(D/'launch.json');start=load(L/'started.json');terminal=load(L/'terminal.json');gate=load(G/'receipt.json')
launcher=S/'geometry-launch-detached-owned-integration-f3b.py';controller=S/'geometry-owned-integration-lifecycle-f3b-v2.py';stop=S/'geometry-stop-with-terminal-receipt-f3b.py'
pid=launch['actualControllerPID'];initial=(D/'launched-controller.stat.raw').read_text().rsplit(')',1)[1].strip().split()
checks={}
def ck(n,v):checks[n]=bool(v)
ck('new FULL independently accepted by sealed original canonical command',main['integrityVerified'] is True and main['boundedAcceptancePassed'] is True)
ck('same clean f3b full40SHA launch terminal actual gate',launch['fullSHA']==terminal['expectedFullSHA']==main['testedFullSHA']==gate['before']['git']['head']=='f3b8285729b42cd22451c98cba1e2ec4514517f3' and launch['dirty']==terminal['dirtyBefore']==terminal['dirtyAfter']=='')
ck('exact unchanged launcher source at actual launch',launch['launcherSourceSHA256']==sha(launcher)=='1bd4791d7745744634a093b9df3bbb31901ffbe4723e5858712b1ca3d11d6333')
ck('exact unchanged controller source at actual start',launch['controllerSourceSHA256']==start['controllerSHA256']==sha(controller)=='5a33421c7b84919c212ebf3c444bed22a950177462cd87c073e4d99fdda0e5ae')
ck('original FULL wrapper pinned at actual start',start['runnerSHA256']=='5ce8212de96e45d0b613b17888a053a7a679024dc1a230f4c734a6170cc5da89')
ck('exact launcher controller original cdp command',launch['launcherCommand']==[str(launcher),'cdp',stem] and launch['controllerCommand']==[start['actualPython'],str(controller),'cdp',stem])
ck('actual launcher Python executable hash',launch['actualPythonSHA256']==start['actualPythonSHA256']==sha(launch['actualPython']))
ck('actual detached own PID PGID SID at launch',launch['actualControllerPID']==launch['actualControllerPGID']==launch['actualControllerSID']==int(initial[2])==int(initial[3]))
ck('launch raw stat original hash retained',sha(D/'launched-controller.stat.raw')==[x for x in launch['rawFiles'] if x['path']=='launched-controller.stat.raw'][0]['sha256'])
ck('launch status truthfully launch-only pending',launch['launchExitCode']==0 and launch['productGateExitCodeAtLaunch'] is None and launch['productCompletionAtLaunch']=='pending')
ck('original controller terminal waited Node gate and stop0',terminal['actualGateExitCode']==gate['gateExitCode']==gate['execution']['exitCode']==terminal['stopExitCode']==0)
ck('actual owned stop exact source',terminal['stopCommand'][1]==str(stop) and sha(stop)=='cc505b94c1011bed31d350a8670422808ded123e6b058e54e3c7853ff79286a2')
ck('controller final stdout refers same original terminal',json.loads((D/'controller.stdout.raw.log').read_text().splitlines()[-1])=={'lifecycleReceipt':str(L/'terminal.json'),'gateExitCode':0})
ck('controller stderr preserved empty',(D/'controller.stderr.raw.log').stat().st_size==0)
OUT.mkdir()
proc=Path('/proc')/str(pid)/'stat';observed={'observedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':pid,'procStatPath':str(proc),'exists':proc.exists(),'state':None,'kernelWaitStatus':None,'actualControllerExitCode':None,'kernelSignal':None}
if proc.exists():
 raw=proc.read_bytes();(OUT/'controller.terminal.stat.raw').write_bytes(raw);fields=raw.decode().rsplit(')',1)[1].strip().split()
 ck('terminal kernel stat belongs to original controller start time and group',raw.decode().split(' ',1)[0]==str(pid) and fields[19]==initial[19] and int(fields[2])==int(fields[3])==pid)
 observed.update({'state':fields[0],'rawPath':str(OUT/'controller.terminal.stat.raw'),'rawSHA256':hashlib.sha256(raw).hexdigest(),'rawBytes':len(raw)})
 if fields[0]=='Z' and len(fields)>=50:
  encoded=int(fields[49]);signal=encoded&127
  observed.update({'kernelWaitStatus':encoded,'kernelSignal':signal,'actualControllerExitCode':encoded>>8 if signal==0 else None})
 actual0=observed['state']=='Z' and observed['kernelWaitStatus']==0
else:actual0=False
ck('actual terminal kernel controller wait status zero',actual0)
current={'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'dirty':subprocess.check_output(['git','status','--porcelain'],cwd=R,text=True)}
ck('candidate still frozen clean after read',current=={'head':'f3b8285729b42cd22451c98cba1e2ec4514517f3','dirty':''})
log=OUT/'review.raw.log';log.write_text('\n'.join(('PASS ' if v else 'UNKNOWN ' if n=='actual terminal kernel controller wait status zero' and observed['actualControllerExitCode'] is None else 'FAIL ')+n for n,v in checks.items())+'\n')
inputs=[proof,D/'launch.json',D/'launched-controller.stat.raw',D/'controller.stdout.raw.log',D/'controller.stderr.raw.log',L/'started.json',L/'terminal.json',G/'receipt.json',launcher,controller,stop,Path(__file__)]
record={'schema':'geometry-durable-full-detached-kernel-independent-addendum/1','checkedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actor':'/root/ui_tail_contract','actualCommand':sys.orig_argv,'actualPython':str(Path('/proc/self/exe').resolve()),'actualPythonSHA256':sha('/proc/self/exe'),'testedFullSHA':current['head'],'dirty':current['dirty'],'checks':checks,'checksPassed':sum(checks.values()),'completeChainVerified':all(checks.values()),'actualControllerTerminalObservation':observed,'sourceHashes':{str(p):sha(p) for p in inputs},'rawReviewLogSHA256':sha(log),'exitCode':0 if all(checks.values()) else 1,'productTestsExecuted':False,'limits':['No browser/service/native/product or repo mutation.','launchExitCode0 remains launch-only; controller actual0 is established only by retained zombie kernel stat wait-status0, never final-source exit statement.','If kernel terminal state is unavailable actual controller exit stays unknown; collect a new dated addendum when observable, do not overwrite this proof or rerun product.','This new durable full evidence never supplies the earlier unreceipted full actor executable or old unknown exits.','Original P38 expected fb-auto-probe exception1 is independently classified by unchanged source and is not failedAssertions1.']}
out=OUT/'receipt.json';out.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'proof':str(out),'sha256':sha(out),'passed':sum(checks.values()),'total':len(checks),'actualControllerExitCode':observed['actualControllerExitCode'],'kernelWaitStatus':observed['kernelWaitStatus'],'completeChainVerified':record['completeChainVerified']}));sys.exit(record['exitCode'])


