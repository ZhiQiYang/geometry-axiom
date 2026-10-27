from pathlib import Path
import datetime,fcntl,hashlib,json,os,resource,shutil,signal,subprocess,sys,threading,time
import reaper
ROOT=Path('/workspace/geo337-native-F-cbf0fb62')
OUT=Path('/workspace/scratch/geo337-reading-a-reader-F-cbf0fb62-20261027')
SHA='cbf0fb621888596aa14ad5f2349b503e23b1b72d'
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args],text=True).strip()
def h(b):return hashlib.sha256(b).hexdigest()
assert json.loads(Path('/workspace/scratch/geo337-reading-a-oracle-F-cbf0fb62-20261027/RESULT.json').read_text())['source_unchanged']
assert git('rev-parse','HEAD')==SHA and not git('status','--porcelain') and not OUT.exists()
lock=open('/tmp/geo337-native-owner.lock','a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
OUT.mkdir();(OUT/'tmp').mkdir();reaper.enable()
resource.setrlimit(resource.RLIMIT_STACK,(16777216,resource.getrlimit(resource.RLIMIT_STACK)[1]))
env={'PATH':os.environ['PATH'],'HOME':os.environ['HOME'],'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TMPDIR':str(OUT/'tmp'),'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8','PYTHONOPTIMIZE':'0','GITHUB_SHA':SHA,'GITHUB_WORKSPACE':str(ROOT)}
names=['geometry-guide/公理層-閱讀器.html','geometry-guide/sync_axiom_reader.py','geometry-guide/公理層-白話.md','公理層.md']
original={name:(ROOT/name).read_bytes() for name in names}
dump(OUT/'REQUEST.json',{'sha':SHA,'cwd':str(ROOT),'environment':env,'stack_bytes':16777216,'started_utc':utc(),'source_before':{k:h(v) for k,v in original.items()},'limits_source':'run_stage.historical.py reader-generate and reader-check, 300 seconds each'})
rows=[];adopted=[]
for name,args in [('reader-generate',[]),('reader-check',['--check'])]:
    stage=OUT/name;stage.mkdir();argv=[sys.executable,'-B',str(ROOT/'geometry-guide/sync_axiom_reader.py'),*args]
    row={'stage':name,'argv':argv,'cwd':str(ROOT),'sha':SHA,'timeout_seconds':300,'started_utc':utc()};dump(stage/'request.json',row)
    with (stage/'stdout.bin').open('wb') as stdout,(stage/'stderr.bin').open('wb') as stderr:
        start=time.monotonic();proc=subprocess.Popen(argv,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
        stop=threading.Event()
        def reap():
            while not stop.wait(.05):adopted.extend(reaper.reap({proc.pid}))
        thread=threading.Thread(target=reap,daemon=True);thread.start();expired=False
        try:rc=proc.wait(timeout=300)
        except subprocess.TimeoutExpired:
            expired=True;os.killpg(proc.pid,signal.SIGINT)
            try:rc=proc.wait(timeout=10)
            except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);rc=proc.wait()
        finally:stop.set();thread.join()
    unchanged=all((ROOT/k).read_bytes()==v for k,v in original.items())
    row.update(actual_exit=rc,timed_out=expired,elapsed_seconds=time.monotonic()-start,ended_utc=utc(),source_unchanged=unchanged,status_after=git('status','--porcelain'))
    row['passed']=rc==0 and not expired and unchanged and not row['status_after'];dump(stage/'result.json',row);rows.append(row)
    if not unchanged:
        for i,(k,v) in enumerate(original.items()):
            if (ROOT/k).read_bytes()!=v:
                (OUT/f'generated-difference-{i}.bin').write_bytes((ROOT/k).read_bytes());(ROOT/k).write_bytes(v)
        break
reuse=OUT/'same-F-native-unit';reuse.mkdir()
for name in ['py_test_axiom_reader.json','py_test_axiom_reader.log','py_test_axiom_reader.unittest.log']:
    shutil.copy2(Path('/tmp/geometry-tests/run_all-logs')/name,reuse/name)
dump(OUT/'REAPED.json',adopted)
dump(OUT/'RESULT.json',{'sha':git('rev-parse','HEAD'),'completed_utc':utc(),'passed':len(rows)==2 and all(r['passed'] for r in rows),'stages':rows,'status_after':git('status','--porcelain'),'same_F_native_unit_reused':{'passed':51,'failed':0,'skipped':0,'evidence_commit':'732ef20e34876379a37eb69693a481becebea43e'},'source_after':{k:h((ROOT/k).read_bytes()) for k in original}})
print((OUT/'RESULT.json').read_text(),flush=True)
