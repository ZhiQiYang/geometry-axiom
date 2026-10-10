from pathlib import Path
import ast,datetime,hashlib,json,subprocess,sys
root=Path('<workspace-path>');scratch=Path('<workspace-path>');base=scratch/'geometry-ui-verification/f3b-source-and-census-preparation'
life=scratch/'geometry-root-f3b82857-durable-full-space-lifecycle';launch=scratch/'geometry-root-f3b82857-durable-full-space-detached-launch'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_bytes())
proofpath=scratch/'geometry-ui-verification/supplementary-validation-f3b-durable-full-space.json'
launchpath=launch/'launch.json';record=load(launchpath);started=load(life/'started.json');terminal=load(life/'terminal.json');proof=load(proofpath)
launcher=scratch/'geometry-launch-detached-owned-integration-f3b.py';controller=scratch/'geometry-owned-integration-lifecycle-f3b-v2.py';stop=scratch/'geometry-stop-with-terminal-receipt-f3b.py'
controllerbytes=controller.read_bytes();launcherbytes=launcher.read_bytes();launch_ast=ast.parse(launcherbytes)
pid=record['actualControllerPID'];fields=(launch/'launched-controller.stat.raw').read_text().rsplit(')',1)[1].strip().split()
checks={
 'sealed Space independently accepted':proof['integrityVerified'] is True and proof['boundedAcceptancePassed'] is True,
 'exact frozen candidate launch and terminal':record['fullSHA']==terminal['expectedFullSHA']=='f3b8285729b42cd22451c98cba1e2ec4514517f3' and record['dirty']==terminal['dirtyAfter']=='',
 'unchanged owned controller source pinned by both phases':record['controllerSourceSHA256']==started['controllerSHA256']==sha(controller)=='5a33421c7b84919c212ebf3c444bed22a950177462cd87c073e4d99fdda0e5ae',
 'unchanged launcher source recorded at launch':record['launcherSourceSHA256']==sha(launcher)=='1bd4791d7745744634a093b9df3bbb31901ffbe4723e5858712b1ca3d11d6333',
 'exact launcher command mode and stem':record['launcherCommand']==[str(launcher),'space','geometry-root-f3b82857-durable-full-space'],
 'exact controller command same Python source and mode':record['controllerCommand']==[started['actualPython'],str(controller),'space','geometry-root-f3b82857-durable-full-space'],
 'actual Python hash consistent':record['actualPythonSHA256']==started['actualPythonSHA256']==sha(record['actualPython']),
 'launch PID PGID SID own fresh group':record['actualControllerPGID']==record['actualControllerSID']==pid and int(fields[2])==int(fields[3])==pid,
 'launch raw stat hash unchanged':sha(launch/'launched-controller.stat.raw')==[v for v in record['rawFiles'] if v['path']=='launched-controller.stat.raw'][0]['sha256'],
 'launcher explicitly detached stdout stderr and session':any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='Popen' and any(k.arg=='start_new_session' and isinstance(k.value,ast.Constant) and k.value.value is True for k in n.keywords) for n in ast.walk(launch_ast)),
 'launcher launch-only pending metadata honest':record['launchExitCode']==0 and record['productGateExitCodeAtLaunch'] is None and record['productCompletionAtLaunch']=='pending',
 'terminal actual gate and stop zero':terminal['actualGateExitCode']==terminal['stopExitCode']==0,
 'terminal exact candidate stop source':terminal['stopCommand'][1]==str(stop) and sha(stop)=='cc505b94c1011bed31d350a8670422808ded123e6b058e54e3c7853ff79286a2',
 'controller stdout final structured terminal matches sealed file':json.loads((launch/'controller.stdout.raw.log').read_text().splitlines()[-1])=={'lifecycleReceipt':str(life/'terminal.json'),'gateExitCode':0},
 'controller stderr empty':(launch/'controller.stderr.raw.log').stat().st_size==0,
 'controller successful final exit is exactly original actual gate return':controllerbytes.endswith(b"sys.exit(record['actualGateExitCode'])\n"),
}
# Keep original failed static check (string contained its own disallowed token) intact;
# classify actual AST calls instead of scanning a string literal.
prep=base/'prepare_durable_full_census.py';prep_ast=ast.parse(prep.read_bytes());forbidden={'Popen','run_gate','launch','launch_persistent_context','stop_child'}
checks['preparer AST contains no product/browser/service call']=not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in forbidden for n in ast.walk(prep_ast))
checks['all other previous exception delta and mock checks passed']=all(v for k,v in load(base/'durable-census-preparation-review.json')['checks'].items() if k!='no product/browser/service execution in preparer')
current_proc=Path('/proc')/str(pid)/'stat';proc_observation={'path':str(current_proc),'exists':current_proc.exists(),'actualControllerExitFromKernel':None}
if current_proc.exists():
 raw=current_proc.read_bytes();parts=raw.decode().rsplit(')',1)[1].strip().split();proc_observation.update({'raw':raw.decode(),'sha256':hashlib.sha256(raw).hexdigest(),'state':parts[0]})
 if parts[0]=='Z' and len(parts)>=50:
  encoded=int(parts[49]);proc_observation.update({'kernelWaitStatus':encoded,'actualControllerExitFromKernel':encoded>>8 if encoded&127==0 else None,'kernelSignal':encoded&127})
  checks['retained controller kernel exit actually zero']=encoded==0
out=scratch/'geometry-ui-verification/supplementary-validation-f3b-durable-space-launch-addendum.json';assert not out.exists()
log=out.with_suffix('.raw.log');log.write_text('\n'.join(('PASS ' if v else 'FAIL ')+k for k,v in checks.items())+'\n')
paths=[proofpath,launchpath,launch/'launched-controller.stat.raw',launch/'controller.stdout.raw.log',launch/'controller.stderr.raw.log',launcher,controller,stop,life/'started.json',life/'terminal.json',prep,base/'durable-census-preparation-review.json',Path(__file__)]
result={'schema':'geometry-durable-space-launch-independent-addendum/1','checkedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'testedFullSHA':record['fullSHA'],
 'actualReviewCommand':sys.orig_argv,'actualPython':str(Path('/proc/self/exe').resolve()),'actualPythonSHA256':sha('/proc/self/exe'),'exitCode':0 if all(checks.values()) else 1,
 'checks':checks,'allChecksPassed':all(checks.values()),'sourceHashes':{str(p):sha(p) for p in paths},'rawReviewLogSHA256':sha(log),'currentControllerKernelObservation':proc_observation,
 'actualControllerExitReportedByRoot':0,'actualControllerExitRecordedByOriginalLaunch':None,
 'limits':['Independent metadata/source/kernel observation only; no browser/service/product execution.','Launch-time stdout/stderr hashes attest then-empty files, not their subsequent final contents; current sealed hashes recorded separately.','Original static preparation failure retained: literal search matched its own token; AST correction separately proves no product launch.','Space228 applies only five declared groups; two timber groups stay omitted.']}
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'proof':str(out),'sha256':sha(out),'checks':len(checks),'allChecksPassed':all(checks.values()),'actualKernelControllerExit':proc_observation['actualControllerExitFromKernel']}));sys.exit(result['exitCode'])
