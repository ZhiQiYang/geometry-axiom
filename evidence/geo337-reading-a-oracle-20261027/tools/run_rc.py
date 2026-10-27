from pathlib import Path
import datetime,fcntl,hashlib,importlib.util,json,os,resource,shutil,signal,subprocess,sys,threading,time
import reaper
ROOT=Path('/workspace/geo337-native-F-cbf0fb62')
OUT=Path('/workspace/scratch/geo337-reading-a-rc-F-cbf0fb62-20261027')
SHA='cbf0fb621888596aa14ad5f2349b503e23b1b72d'
BASE=Path(__file__).parent;WORKER=BASE/'run_original_rc_method.py'
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args],text=True).strip()
assert git('rev-parse','HEAD')==SHA and not git('status','--porcelain') and not OUT.exists()
assert hashlib.sha256(WORKER.read_bytes()).hexdigest()=='34baecbd743921179327ec0700c9a3915f0a7f498dcf0850c372343b8edf5d4d'
lock=open('/tmp/geo337-native-owner.lock','a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
OUT.mkdir();(OUT/'tmp').mkdir();reaper.enable()
resource.setrlimit(resource.RLIMIT_STACK,(16777216,resource.getrlimit(resource.RLIMIT_STACK)[1]))
env={'PATH':os.environ['PATH'],'HOME':os.environ['HOME'],'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TMPDIR':str(OUT/'tmp'),'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8','GITHUB_SHA':SHA,'GITHUB_WORKSPACE':str(ROOT)}
spec=importlib.util.spec_from_file_location('original_rc_worker',WORKER);worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
original=(ROOT/worker.ORACLE).read_bytes()
template=json.loads((BASE/'RC_PROOF_REQUEST_TEMPLATE.json').read_text())
dump(OUT/'REQUEST.json',{'sha':SHA,'cwd':str(ROOT),'environment':env,'stack_bytes':16777216,'started_utc':utc(),'worker_sha256':hashlib.sha256(WORKER.read_bytes()).hexdigest(),'owner_lock':'/tmp/geo337-native-owner.lock','lock_mode':'EX|NB held across all six original method invocations; task-local replacement for unavailable historical container lock','watchdog_seconds':300,'watchdog_origin':'local conservative process-collection cap; original worker declares no internal timeout; no original test assertions or expected exits changed','requests':template['requests']})
rows=[];reaped=[]
for request in template['requests']:
    control=request['control'];variant_dir=OUT/control;variant_dir.mkdir()
    old,new=request['old'].encode(),request['new'].encode()
    assert original.count(old)==1
    variant=variant_dir/'framing_oracle.py';variant.write_bytes(original.replace(old,new,1))
    for phase in request['phases']:
        name=phase['phase'];expected=phase['expectedOriginalExit'];stage=variant_dir/name;stage.mkdir()
        source=variant if name=='withdrawn' else ROOT/worker.ORACLE
        argv=[sys.executable,'-B',str(WORKER),'--root',str(ROOT),'--sha',SHA,'--source',str(source),'--control',control if name=='withdrawn' else 'baseline']
        row={'control':control,'phase':name,'argv':argv,'cwd':str(ROOT),'sha':SHA,'expected_exit':expected,'started_utc':utc()};dump(stage/'request.json',row)
        with (stage/'stdout.bin').open('wb') as stdout,(stage/'stderr.bin').open('wb') as stderr:
            start=time.monotonic();proc=subprocess.Popen(argv,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
            stop=threading.Event()
            def reap():
                while not stop.wait(.05):reaped.extend(reaper.reap({proc.pid}))
            thread=threading.Thread(target=reap,daemon=True);thread.start();expired=False
            try:rc=proc.wait(timeout=300)
            except subprocess.TimeoutExpired:
                expired=True;os.killpg(proc.pid,signal.SIGINT)
                try:rc=proc.wait(timeout=10)
                except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);rc=proc.wait()
            finally:stop.set();thread.join()
        outcomes=[json.loads(line.removeprefix('RC_METHOD_OUTCOME ')) for line in (stage/'stdout.bin').read_text().splitlines() if line.startswith('RC_METHOD_OUTCOME ')]
        valid=len(outcomes)==1 and outcomes[0]['testsRun']==1 and outcomes[0]['errors']==0 and outcomes[0]['skips']==0 and outcomes[0]['originalFilesUnchanged'] and (outcomes[0]['assertionFailures']>0 if expected else outcomes[0]['assertionFailures']==0)
        row.update(actual_exit=rc,timed_out=expired,elapsed_seconds=time.monotonic()-start,ended_utc=utc(),outcomes=outcomes,passed=rc==expected and not expired and valid)
        dump(stage/'result.json',row);rows.append(row)
        assert (ROOT/worker.ORACLE).read_bytes()==original and git('rev-parse','HEAD')==SHA and not git('status','--porcelain')
dump(OUT/'REAPED.json',reaped)
dump(OUT/'RESULT.json',{'sha':SHA,'completed_utc':utc(),'passed':all(r['passed'] for r in rows),'stages':rows,'source_unchanged':(ROOT/worker.ORACLE).read_bytes()==original,'status_after':git('status','--porcelain')})
print((OUT/'RESULT.json').read_text(),flush=True)
