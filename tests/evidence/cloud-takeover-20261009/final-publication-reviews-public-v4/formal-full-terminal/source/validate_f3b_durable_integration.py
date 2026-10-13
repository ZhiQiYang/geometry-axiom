"""Terminal-only independent census. Read original evidence; never run tests/services."""
from pathlib import Path
import argparse,datetime,hashlib,json,re,subprocess,sys

ROOT=Path('<workspace-path>');SCRATCH=Path('<workspace-path>')
HEAD='f3b8285729b42cd22451c98cba1e2ec4514517f3'
VERSION='efbcfff4ca94d6a1844228ea59628ee5de24dcd5e337c62f9c0587f5a38c8a11'
BASE=SCRATCH/'geometry-takeover-evidence-harness'
RUNNERS={'cdp':('run_full_cdp_identity.py','5ce8212de96e45d0b613b17888a053a7a679024dc1a230f4c734a6170cc5da89'),
 'space':('run_full_space_identity.py','8b9729cb300347361b2f6bf507e08fd6fab662ec2bc9f0fca107fb2da02dadae')}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def ident(p):return {'path':str(p),'bytes':Path(p).stat().st_size,'sha256':sha(p)}
def load(p):return json.loads(Path(p).read_bytes())
def gitbytes(rel,head=HEAD):return subprocess.check_output(['git','show',head+':'+rel],cwd=ROOT)
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT,text=True).strip()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=['cdp','space'],required=True)
 p.add_argument('--gate',type=Path,required=True);p.add_argument('--lifecycle',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();gate=a.gate.resolve();life=a.lifecycle.resolve();out=a.output.resolve()
 assert out.is_relative_to(SCRATCH) and not out.exists()
 # Explicitly refuse early/partial files: original sealed gate and lifecycle required.
 for required in [gate/'receipt.json',life/'terminal.json',life/'owned-stop/terminal-receipt.json']:assert required.is_file(),str(required)+' not terminal'
 receipt=load(gate/'receipt.json');terminal=load(life/'terminal.json');started=load(life/'started.json');ready=load(life/'ready-runtime.json')
 stop=load(life/'owned-stop/terminal-receipt.json');owned=load(life/'owned-stop/identity.json')
 before,after=receipt['before'],receipt['after'];raw=(gate/'command.log').read_text(errors='replace')
 prefix='CDP_RESULT ' if a.mode=='cdp' else 'SPACE_RESULT '
 rows=[json.loads(line[len(prefix):]) for line in raw.splitlines() if line.startswith(prefix)]
 assert len(rows)==1 and isinstance(rows[0],dict)
 actual=rows[0];scope=actual['scope'];command=['node','geometry-web/'+('cdp_test.js' if a.mode=='cdp' else 'space_model_test.js')]
 integrity={};acceptance={}
 def check(name,value):integrity[name]=bool(value)
 def accept(name,value):acceptance[name]=bool(value)
 runnername,runnerhash=RUNNERS[a.mode]
 check('canonical protocol unique and correct schema',actual['schema']==('geometry-cdp-result/1' if a.mode=='cdp' else 'geometry-space-result/1'))
 check('original canonical command exactly retained',receipt['command']==command)
 check('one same clean tested fullSHA before/after',before['git']==after['git'] and before['git']['head']==HEAD and before['git']['root']==str(ROOT) and before['git']['status']=='')
 check('all product source hashes unchanged across actual execution',before['sourceSha256']==after['sourceSha256'])
 mismatches=[]
 for rel,digest in before['sourceSha256'].items():
  if hashlib.sha256(gitbytes(rel)).hexdigest()!=digest or sha(gate/'executed-harness-sources'/rel)!=digest:mismatches.append(rel)
 check('every frozen Git source and immutable executed-source snapshot matches',not mismatches)
 for key in ['runnerSha256','identityObserverSha256','launchAdapterSha256','executables','native','liveBridge']:
  check(key+' unchanged before/after',before[key]==after[key])
 if a.mode=='space':check('identity sampler unchanged',before['identityProcessSamplerSha256']==after['identityProcessSamplerSha256'])
 check('actual runner is immutable original',before['runnerSha256']==runnerhash==sha(BASE/runnername)==started['runnerSHA256'])
 wrapper_snapshots={}
 for name,key in [(runnername,'runnerSha256'),('cdp_execution_identity_v2.py' if a.mode=='cdp' else 'space_execution_identity.py','identityObserverSha256')]:
  path=gate/'executed-wrapper-sources'/name
  if path.is_file():wrapper_snapshots[name]=sha(path)==before[key]
 for name,digest in before['launchAdapterSha256'].items():
  path=gate/'executed-wrapper-sources/full-launch-adapters'/name
  if path.is_file():wrapper_snapshots['full-launch-adapters/'+name]=sha(path)==digest
 check('available sealed wrapper snapshots match execution',all(wrapper_snapshots.values()))
 for snap in [before,after]:
  check(('before' if snap is before else 'after')+' runtime fresh exact owned source',snap['runtime']==ready and snap['runtime']['fresh'] is True and snap['sourceVersion']==snap['runtime']['version']==VERSION)
 check('actual original log hash and size match sealed receipt',ident(gate/'command.log')['sha256']==receipt['log']['sha256'] and (gate/'command.log').stat().st_size==receipt['log']['bytes'])
 check('original execution not timed out or interrupted',receipt['execution']['timedOut'] is False and receipt['execution']['interrupted'] is False)
 check('lifecycle original gate exit agrees receipt',terminal['actualGateExitCode']==receipt['gateExitCode'])
 check('lifecycle source command SHA matches actual clean candidate',terminal['expectedFullSHA']==HEAD and terminal['headAfter']==HEAD and terminal['dirtyBefore']==terminal['dirtyAfter']=='')
 check('lifecycle started/terminal records same original command',terminal['testCommand']==started['testCommand'] and terminal['runnerSHA256']==started['runnerSHA256']==runnerhash)
 check('lifecycle controller and Python actual hashes match source',started['controllerSHA256']==sha(SCRATCH/'geometry-owned-integration-lifecycle-f3b-v2.py') and started['actualPythonSHA256']==sha(started['actualPython']))
 check('sealed actual lifecycle raw files match recorded hashes',all(sha(life/r['path'])==r['sha256'] and (life/r['path']).stat().st_size==r['bytes'] for r in terminal['rawFiles']))
 native_checks=[]
 for value in before['native'].values():native_checks.append(value['state']=='fresh' and value['sha256']==sha(value['path']))
 check('actual native binary files fresh and hash-bound',all(native_checks) and len(native_checks)==2)
 check('one actual native child belongs to unique owned server',len(before['liveBridge'])==1 and before['liveBridge'][0]['parent']==ready['pid'] and before['liveBridge'][0]['sha256']==before['native']['bridge']['sha256'])
 binding=receipt['executionIdentity']['liveBinding'];processes=binding['processes']
 nodes=[x for x in processes if x['role']=='actual browser parent Node'];browsers=[x for x in processes if x['role']!='actual browser parent Node']
 check('exact one actual Node and one Chromium ELF observed',len(nodes)==len(browsers)==1 and len(processes)==2 and all(x['executableMagicHex']=='7f454c46' for x in processes))
 node=nodes[0];browser=browsers[0]
 check('actual observed Node matches canonical process/argv/cwd/configured hash',node['pid']==receipt['execution']['pid'] and node['cmdline']==command and node['cwd']==str(ROOT) and node['sha256']==before['executables']['node']['sha256'])
 check('actual observed main Chromium owned profile/debuggingport/cwd',browser['cwd']==str(ROOT) and Path(browser['exe']).name in {'chrome','chromium'} and '--user-data-dir='+receipt['ownedBrowserProfile'] in browser['cmdline'] and '--remote-debugging-port='+str(receipt['ownedCdpPort']) in browser['cmdline'] and not any(x.startswith('--type=') for x in browser['cmdline']))
 check('actual observed ELF executable files match hashes',all(sha(x['exe'])==x['sha256'] for x in processes))
 time=datetime.datetime.fromisoformat
 check('actual live observation occurred during canonical execution',time(receipt['execution']['started'])<=time(binding['observedUtc'])<=time(receipt['execution']['finished']))
 check('identity observer errors absent',receipt['executionIdentity']['errors']==[])
 check('root stopped same exact ready server/native session after preserving dump',owned['runtime']==ready and owned['server']==ready['pid'] and set(owned['children'])=={x['pid'] for x in before['liveBridge']} and sha(life/'owned-stop/root-dump.raw.json')==owned['rootDumpSHA256'])
 check('actual owned stop exited successfully and service terminated',stop['exitCode']==terminal['stopExitCode']==0 and terminal['actualServiceExitAfterStop'] is not None and stop['portObservation']['accepting'] is False)
 observed={r['pid']:r for r in stop['processObservations']};expected_pids={ready['pid'],*[v['pid'] for v in before['liveBridge']],*[v['pid'] for v in processes]}
 check('new stop collector includes actual complete gate process IDs',set(observed)==expected_pids)
 check('all observed stopped processes absent or explicitly zombie',all(not x['exists'] or x['state']=='Z' for x in observed.values()))
 accept('canonical completed',actual['completed'] is True)
 accept('actual gate and Node exit zero',receipt['execution']['exitCode']==receipt['gateExitCode']==terminal['actualGateExitCode']==0)
 accept('receipt execution verified with no release approval',receipt['executionVerified'] is True and receipt['releaseApproved'] is False and receipt['problems']==[] and receipt['status']=='execution-verified')
 accept('scope full without filters',scope['mode']==('full' if a.mode=='cdp' else 'full-space-suite') and scope['filters']==[] and scope['url']==('http://127.0.0.1:19182/' if a.mode=='cdp' else 'http://127.0.0.1:19180/'))
 extra={}
 if a.mode=='cdp':
  golden_bytes=gitbytes('geometry-web/cdp_sections.golden.json');golden=json.loads(golden_bytes)
  check('original golden unchanged from historical5174 bytes',golden_bytes==gitbytes('geometry-web/cdp_sections.golden.json','5174a8dafd8c48329d7166abbd3d104e3c28c0c4'))
  check('current committed golden section sum internally consistent',sum(golden['sections'].values())==golden['total'])
  scopes=[json.loads(line[len('CDP_SCOPE '):]) for line in raw.splitlines() if line.startswith('CDP_SCOPE ')]
  check('actual initial/terminal/live observed CDP scopes equal',len(scopes)==1 and scopes[0]==scope==binding['cdpScope'])
  check('browser PID corresponds to actual canonical scope',scope['browserPid']==browser['pid'])
  check('canonical pass/fail census agrees complete section maps',sum(actual['sections'].values())==actual['passedAssertions'] and sum(actual.get('sectionsFailed',{}).values())==actual['failedAssertions'])
  accept('zero failures and no skips under original gate contract',actual['failedAssertions']==0 and actual['skipped']==[] and actual.get('sectionsFailed',{})=={})
  expected_exception_rows=[line for line in raw.splitlines() if line.startswith('[EXPECTED EXCEPTION]')]
  unexpected_exception_rows=[line for line in raw.splitlines() if line.startswith('[UNEXPECTED EXCEPTION]')]
  check('exception census classified by unchanged original P38 expectation',expected_exception_rows==['[EXPECTED EXCEPTION] Error: fb-auto-probe'] and not unexpected_exception_rows and actual.get('uncaughtBrowserExceptions')==len(expected_exception_rows))
  accept('complete per-section census exactly matches original golden',actual['sections']==golden['sections'] and actual['passedAssertions']==golden['total'] and actual['goldenCompare']=='matched' and scope['modifiers']==[])
  accept('raw canonical complete-golden confirmation present','[CDP FLOOR] 與 golden 逐段相符('+str(len(golden['sections']))+' 段)' in raw)
  extra={'goldenSHA256':hashlib.sha256(golden_bytes).hexdigest(),'goldenSections':len(golden['sections']),'goldenTotal':golden['total'],'goldenCompared':actual['goldenCompare'],'unreachedGoldenSections':{k:v for k,v in golden['sections'].items() if k not in actual['sections']}}
 else:
  floorbytes=gitbytes('geometry-web/space_test_floor.js');floor=floorbytes.decode()
  included=re.findall(r"'([^']+)'",re.search(r'const FULL_SPACE_GROUPS = Object.freeze\(\[(.*?)\]\)',floor,re.S).group(1))
  pairs=re.findall(r"(?:'([^']+)'|([A-Za-z_][A-Za-z0-9_]*))\s*:\s*(\d+)",re.search(r'const EXPECTED = Object.freeze\(\{(.*?)\}\)',floor,re.S).group(1))
  expected={quoted or bare:int(n) for quoted,bare,n in pairs};groups=actual['groups']
  check('Space group/total canonical pass and fail census agrees',sum(x['passed'] for x in groups.values())==actual['passed'] and sum(x['failed'] for x in groups.values())==actual['failed'])
  accept('Space full declared five scope and seven census groups complete',scope['included']==included and set(groups)==set(['setup',*included,'browser-health']) and all(x['expected']==expected[k] and x['passed']==x['expected'] and x['failed']==0 and x['completed'] is True for k,x in groups.items()))
  accept('Space failures/browsererrors/completeness problems absent',actual['passed']>0 and actual['failed']==0 and actual['exceptions']==[] and actual['consoleErrors']==[] and actual['completenessProblems']==[])
  accept('optional timber groups remain disclosed omissions',scope['omitted']==['timber-material','timber-source-guards'])
  extra={'floorSourceSHA256':hashlib.sha256(floorbytes).hexdigest(),'declaredFullGroups':included,'declaredExpected':expected,'actualGroups':groups,'goldenCompared':'not applicable to standalone Space','omittedGroups':scope['omitted']}
 check('full accepted evidence itself agrees raw result',receipt.get('evidence',{}).get('canonicalResult')==actual if receipt['executionVerified'] else True)
 check('full accepted evidence completed verified',receipt.get('evidence',{}).get('completionVerified') is True if receipt['executionVerified'] else True)
 current={'head':git('rev-parse','HEAD'),'dirty':git('status','--porcelain=v1','--untracked-files=all')}
 check('candidate still frozen clean after readonly census',current=={'head':HEAD,'dirty':''})
 out.parent.mkdir(parents=True,exist_ok=True)
 log=out.with_suffix('.raw.log');log.write_text('\n'.join(('PASS ' if v else 'FAIL ')+'integrity: '+k for k,v in integrity.items())+'\n'+ '\n'.join(('PASS ' if v else 'FAIL ')+'acceptance: '+k for k,v in acceptance.items())+'\n')
 exitcode=0 if all(integrity.values()) else 1
 result={'schema':'geometry-recovered-full-independent-census/1','checkedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'mode':a.mode,'testedFullSHA':HEAD,'currentCandidate':current,
  'reviewExecutor':{'command':sys.orig_argv,'actualPython':str(Path('/proc/self/exe').resolve()),'actualPythonSHA256':sha('/proc/self/exe'),'scriptSHA256':sha(__file__)},'exitCode':exitcode,
  'sources':{str(p):ident(p) for p in [gate/'receipt.json',gate/'command.log',life/'started.json',life/'ready-runtime.json',life/'terminal.json',life/'owned-stop/terminal-receipt.json',life/'owned-stop/identity.json']},
  'rawReviewLog':ident(log),'integrityChecks':integrity,'integrityVerified':all(integrity.values()),'acceptanceChecks':acceptance,'boundedAcceptancePassed':all(integrity.values()) and all(acceptance.values()),
  'originalCanonicalResult':actual,'actualExecution':receipt['execution'],'actualGateExitCode':receipt['gateExitCode'],'actualObservedExecutionIdentity':receipt['executionIdentity'],'nativeBeforeAfter':[before['native'],after['native']],
  'runtimeBeforeAfter':[before['runtime'],after['runtime']],'sourceSnapshotMismatches':mismatches,'availableWrapperSnapshotChecks':wrapper_snapshots,'scopeDetails':extra,'serviceStopObservations':stop['processObservations'],
  'browserStarted':False,'servicesStartedOrStopped':False,'repoWritten':False,
  'limits':['Metadata/log/source census only; no independent product/browser/native execution.',
   'This recovered actual command is separate from old noReceipt CDP742/0false and Space168/2false; no aggregation or invented old exits.',
   'Current bound scope does not substitute for caption/SIX, #54, Resume, races, projection or all43/privateZIP acceptance.',
   'Historical 2207/0/0 remains attached to clean5174; any new equal count is established by this new actual receipt, never rebound.',
   'Original Windows logs remain unreceived; cloud results do not establish Windows full or golden acceptance.']}
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'proof':str(out),'sha256':sha(out),'integrityVerified':result['integrityVerified'],'boundedAcceptancePassed':result['boundedAcceptancePassed'],'originalPassed':actual.get('passedAssertions',actual.get('passed')),'originalFailed':actual.get('failedAssertions',actual.get('failed')),'failedIntegrity':[k for k,v in integrity.items() if not v],'failedAcceptance':[k for k,v in acceptance.items() if not v]}))
 return exitcode
if __name__=='__main__':sys.exit(main())
