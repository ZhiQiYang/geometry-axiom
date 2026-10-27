from pathlib import Path
import datetime, fcntl, hashlib, json, os, shutil, signal, subprocess, tarfile, time
import ctypes, threading

ROOT = Path('/workspace/geo337-native-F-cbf0fb62')
OUT = Path('/workspace/scratch/geo337-native-F-cbf0fb62-20261027')
BIN = Path('/tmp/geometry-tests')
SHA = 'cbf0fb621888596aa14ad5f2349b503e23b1b72d'
def dump(name, value):
    (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
def git(*args):
    return subprocess.check_output(['git','-C',str(ROOT),*args], text=True).strip()
def space():
    return {str(p): {'resolved':str(p.resolve()), 'device':p.stat().st_dev, 'free':shutil.disk_usage(p).free} for p in [BIN,Path('/tmp'),ROOT,OUT]}
def sample():
    logical=allocated=0
    for p in BIN.rglob('*'):
        try:
            s=p.lstat(); logical+=s.st_size; allocated+=s.st_blocks*512
        except FileNotFoundError: pass
    return {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'logical_bytes':logical,'allocated_bytes':allocated,'space':space()}

assert git('rev-parse','HEAD') == SHA
assert not git('status','--porcelain')
assert not OUT.exists()
lock = open('/tmp/geo337-native-owner.lock','a+')
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not BIN.exists(), 'Preserve existing output; reassess ownership before run'
OUT.mkdir(parents=True)
BIN.mkdir()
tmp=OUT/'temp'; tmp.mkdir()
env={'PATH':os.environ['PATH'],'HOME':os.environ['HOME'],'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TMPDIR':str(tmp),'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8'}
argv=['bash','--noprofile','--norc','-c','ulimit -s 16384\npython3 tests/run_all.py --build']
assert shutil.disk_usage(BIN).free >= 134217728
assert shutil.disk_usage(OUT).free >= 67108864
shutil.copy2(ROOT/'.github/workflows/integration-tests.yml',OUT/'workflow.original.yml')
shutil.copy2(ROOT/'AGENTS.md',OUT/'AGENTS.original.md')
(OUT/'mountinfo.before.txt').write_text(Path('/proc/self/mountinfo').read_text())
(OUT/'processes.before.txt').write_bytes(subprocess.check_output(['ps','-eo','pid,ppid,comm,args']))
(OUT/'locks.before.txt').write_bytes(subprocess.check_output(['lslocks']))
dump('REQUEST.json',{'sha':SHA,'cwd':str(ROOT),'argv':argv,'environment':env,'environment_is_explicit_allowlist':True,'timeout_seconds':2100,'stack_kib':16384,'before':space(),'owner_lock':'/tmp/geo337-native-owner.lock','output_was_absent':True,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
libc=ctypes.CDLL(None,use_errno=True)
assert libc.prctl(36,1,0,0,0)==0, 'PR_SET_CHILD_SUBREAPER failed'
dump('REAPER.json',{'scope':'this launcher and its descendants only','reason':'Container PID 1 is tail; the prior original run left killed orphan children as zombies. Reap exited adopted children without changing any test or assertion.','prctl':'PR_SET_CHILD_SUBREAPER=1'})
stop_reaper=threading.Event(); reaped=[]
def reap_orphans(main_pid):
    while not stop_reaper.wait(0.05):
        children=Path('/proc/self/task/%d/children'%os.getpid()).read_text().split()
        for child in children:
            pid=int(child)
            if pid==main_pid: continue
            try:
                found,status=os.waitpid(pid,os.WNOHANG)
                if found: reaped.append({'pid':found,'wait_status':status,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
            except ChildProcessError: pass
start=time.monotonic(); samples=[]; timed_out=False
with (OUT/'stdout.bin').open('wb') as stdout, (OUT/'stderr.bin').open('wb') as stderr, (OUT/'samples.jsonl').open('w') as sf:
    proc=subprocess.Popen(argv,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
    reaper=threading.Thread(target=reap_orphans,args=(proc.pid,),daemon=True); reaper.start()
    dump('RUNNING.json',{'pid':proc.pid,'sha':SHA})
    while True:
        row=sample(); samples.append(row); sf.write(json.dumps(row)+'\n'); sf.flush()
        rc=proc.poll()
        if rc is not None: break
        left=2100-(time.monotonic()-start)
        if left<=0:
            timed_out=True; os.killpg(proc.pid,signal.SIGINT)
            try: proc.wait(timeout=10)
            except subprocess.TimeoutExpired: os.killpg(proc.pid,signal.SIGKILL); proc.wait()
            rc=proc.returncode; break
        try: proc.wait(timeout=min(5,left))
        except subprocess.TimeoutExpired: pass
elapsed=time.monotonic()-start
stop_reaper.set(); reaper.join()
dump('REAPED.json',reaped)
dump('RESULT.json',{'sha':git('rev-parse','HEAD'),'actual_process_returncode':rc,'timed_out':timed_out,'workflow_gate_exit':124 if timed_out else rc,'elapsed_seconds':elapsed,'after':space(),'sampled_max_allocated_bytes':max(x['allocated_bytes'] for x in samples),'sampled_max_logical_bytes':max(x['logical_bytes'] for x in samples),'sample_period_seconds':5,'status_after':git('status','--porcelain'),'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
with tarfile.open(OUT/'native-output.original.tar.gz','w:gz') as tar: tar.add(BIN,arcname='geometry-tests')
manifest={}
for p in sorted(OUT.iterdir()):
    if p.is_file():
        h=hashlib.sha256()
        with p.open('rb') as f:
            for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
        manifest[p.name]={'bytes':p.stat().st_size,'sha256':h.hexdigest()}
dump('SHA256.json',manifest)
print((OUT/'RESULT.json').read_text(),flush=True)
