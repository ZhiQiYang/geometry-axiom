from pathlib import Path
import ast,datetime,fcntl,hashlib,json,os,resource,shutil,subprocess,sys,threading,time,tarfile
import reaper
ROOT=Path('/workspace/geo337-native-F-cbf0fb62')
OUT=Path('/workspace/scratch/geo337-pf3-F-cbf0fb62-20261027')
SHA='cbf0fb621888596aa14ad5f2349b503e23b1b72d'
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args],text=True).strip()
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert git('rev-parse','HEAD')==SHA and not git('status','--porcelain') and not OUT.exists()
lock=open('/tmp/geo337-native-owner.lock','a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
OUT.mkdir();(OUT/'tmp').mkdir();reaper.enable()
resource.setrlimit(resource.RLIMIT_STACK,(16777216,resource.getrlimit(resource.RLIMIT_STACK)[1]))
env={'PATH':os.environ['PATH'],'HOME':os.environ['HOME'],'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TMPDIR':str(OUT/'tmp'),'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8','GITHUB_SHA':SHA,'GITHUB_WORKSPACE':str(ROOT)}
argv=[sys.executable,'-B','tests/pf3_mutation_check.py','--out',str(OUT/'subject'),'--jobs','1']
script=ROOT/'tests/pf3_mutation_check.py'
source_h=h(script)
dump(OUT/'REQUEST.json',{'sha':SHA,'cwd':str(ROOT),'argv':argv,'environment':env,'started_utc':utc(),'stack_bytes':16777216,'original_child_timeout_seconds':900,'outer_timeout_seconds':None,'jobs':1,'expected_source_variants':21,'expected_baseline_tests':20,'expected_semantic_kills':19,'expected_restored_tests':20,'owner_lock':'/tmp/geo337-native-owner.lock','subject_sha256':source_h,'free_before':{p:shutil.disk_usage(p).free for p in ['/workspace','/tmp']}})
shutil.copy2(script,OUT/'pf3_mutation_check.original.py');shutil.copy2(ROOT/'geometry-core/panel-fill/PF3-NATIVE.md',OUT/'PF3-NATIVE.original.md')
reaped=[];stop=threading.Event()
with (OUT/'stdout.bin').open('wb') as stdout,(OUT/'stderr.bin').open('wb') as stderr:
    start=time.monotonic();proc=subprocess.Popen(argv,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
    def collect():
        while not stop.wait(.05):
            for row in reaper.reap({proc.pid}):reaped.append({'utc':utc(),**row})
    thread=threading.Thread(target=collect,daemon=True);thread.start()
    dump(OUT/'RUNNING.json',{'pid':proc.pid,'sha':SHA,'started_utc':utc(),'argv':argv})
    rc=proc.wait();elapsed=time.monotonic()-start;stop.set();thread.join()
status=git('status','--porcelain');head=git('rev-parse','HEAD')
summary_path=OUT/'subject/summary.json';summary=json.loads(summary_path.read_text()) if summary_path.exists() else None
source_map_path=OUT/'subject/sources.json'
source_map=json.loads(source_map_path.read_text()) if source_map_path.exists() else {}
unchanged=bool(source_map) and all(h(ROOT/p)==expected for p,expected in source_map.items()) and h(script)==source_h
passed=rc==0 and head==SHA and not status and unchanged and isinstance(summary,dict) and summary.get('originalSourcesUnchanged') is True
if passed:
    passed=(summary['baseline']['verdict']=='pass' and summary['baseline']['counts']==dict(run=20,failures=0,errors=0,skipped=0) and summary['restored']['verdict']=='pass' and summary['restored']['counts']==dict(run=20,failures=0,errors=0,skipped=0) and len(summary['mutations'])==19 and all(r['verdict']=='killed' and r['counts']==dict(run=1,failures=1,errors=0,skipped=0) for r in summary['mutations']))
dump(OUT/'REAPED.json',reaped)
dump(OUT/'RESULT.json',{'sha':head,'actual_exit':rc,'passed':passed,'elapsed_seconds':elapsed,'completed_utc':utc(),'status_after':status,'original_source_hashes_verified':len(source_map),'source_unchanged':unchanged,'subject_summary_present':summary is not None,'free_after':{p:shutil.disk_usage(p).free for p in ['/workspace','/tmp']}})
with tarfile.open(OUT/'subject.original.tar.gz','w:gz') as tar:tar.add(OUT/'subject',arcname='subject')
dump(OUT/'ARCHIVE.json',{'path':'subject.original.tar.gz','bytes':(OUT/'subject.original.tar.gz').stat().st_size,'sha256':h(OUT/'subject.original.tar.gz')})
print((OUT/'RESULT.json').read_text(),flush=True)
