from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,resource,signal,subprocess,sys,time
from task_child_reaper import ChildReaper
ROOT=Path('/tmp/geometry-r06-main359-integration-20261102')
OUT=Path(__file__).resolve().parent
TMP=Path('/dev/shm/g-r06-node-20261102');TMP.mkdir(exist_ok=False)
HEAD='c2eb5edc99d2880a65583f46085617d99a6f191b'
NODE='/tmp/geometry-resume-20261102/pr363/node-v24.22.1-linux-x64/bin'
SHA=lambda b:hashlib.sha256(b).hexdigest()
def save(n,d):
 with (OUT/n).open('x') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT,env=dict(os.environ,GIT_NO_LAZY_FETCH='1')).decode().strip()
def limit():resource.setrlimit(resource.RLIMIT_STACK,(16777216,16777216))
assert git('rev-parse','HEAD')==HEAD and git('status','--porcelain=v1','--untracked-files=all')==''
expected=ROOT/'tests/run_all.expected.json';before=expected.read_bytes()
inputs={p.relative_to(ROOT).as_posix():SHA(p.read_bytes()) for p in [ROOT/'tests/run_all.py',ROOT/'tests/binaries.py',*sorted((ROOT/'tests').glob('test_*.js'))]}
env=dict(os.environ,PATH=NODE+os.pathsep+os.environ['PATH'],TMPDIR=str(TMP),PYTHONDONTWRITEBYTECODE='1',GIT_NO_LAZY_FETCH='1')
assert os.statvfs(TMP).f_bavail*os.statvfs(TMP).f_frsize>536870912
cmd=[sys.executable,'-u','tests/run_all.py','--build','--only','node:tests-js','--report',str(OUT/'run-all-report.json')]
save('REQUEST.json',{'utc':datetime.now(timezone.utc).isoformat(),'argv':cmd,'cwd':str(ROOT),'head':HEAD,'tree':git('rev-parse','HEAD^{tree}'),'scope':'Original partial Node aggregate diagnostic; NOT full census, no expected update or formal full-native credit','timeoutSeconds':2100,'originalNodeSuiteLimitSeconds':900,'stackBytes':16777216,'environmentOverrides':{k:env[k] for k in ['PATH','TMPDIR','PYTHONDONTWRITEBYTECODE','GIT_NO_LAZY_FETCH']},'expectedBeforeSha256':SHA(before),'primaryDriverAndNodeSuiteHashes':inputs,'reaperSha256':SHA((OUT/'task_child_reaper.py').read_bytes()),'onlyOwnTerminatedAdoptedChildrenReaped':True})
r=ChildReaper(OUT/'reaper.jsonl');started=time.monotonic();startUtc=datetime.now(timezone.utc).isoformat();timeout=False
with (OUT/'stdout.log').open('wb') as stdout,(OUT/'stderr.log').open('wb') as stderr:
 proc=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,start_new_session=True,preexec_fn=limit)
 save('STARTED.json',{'utc':startUtc,'supervisorPid':os.getpid(),'childPid':proc.pid,'deadlineUtc':datetime.fromtimestamp(time.time()+2100,timezone.utc).isoformat()})
 code=r.wait_main(proc,started+2100)
 if code is None:
  timeout=True;os.killpg(proc.pid,signal.SIGTERM)
  try:code=proc.wait(timeout=5)
  except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
r.tick(proc.pid)
result={'utc':datetime.now(timezone.utc).isoformat(),'source':HEAD,'childExit':code,'outerExit':124 if timeout else code,'seconds':time.monotonic()-started,'timedOut':timeout,'expectedUnchanged':expected.read_bytes()==before,'sourceHeadUnchanged':git('rev-parse','HEAD')==HEAD,'sourceStatus':git('status','--porcelain=v1','--untracked-files=all'),'stdoutSha256':SHA((OUT/'stdout.log').read_bytes()),'stderrSha256':SHA((OUT/'stderr.log').read_bytes()),'fullCensus':False,'expectedWasNotUpdated':True}
save('RESULT.json',result);print(json.dumps(result,ensure_ascii=False),flush=True);sys.exit(result['outerExit'])
