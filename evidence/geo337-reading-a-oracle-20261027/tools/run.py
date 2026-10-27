from pathlib import Path
import datetime,fcntl,hashlib,json,os,resource,shutil,signal,subprocess,sys,threading,time
import reaper

ROOT=Path('/workspace/geo337-native-F-cbf0fb62')
OUT=Path('/workspace/scratch/geo337-reading-a-oracle-F-cbf0fb62-20261027')
SHA='cbf0fb621888596aa14ad5f2349b503e23b1b72d'
ORACLE=ROOT/'geometry-core/framing-template/oracle'
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args],text=True).strip()
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def binding():
    paths=[p for p in ORACLE.iterdir() if p.is_file()]
    paths += list((ROOT/'evidence/issue318-reading-a-20261023/tools').glob('*.py'))
    paths += [ROOT/p for p in ['AGENTS.md','決策佇列.md','公理層.md','tests/test_geo318_reading_a_oracle.py','tests/test_geo318_reading_a_native.py','.github/workflows/integration-tests.yml']]
    return {str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(paths)}
assert git('rev-parse','HEAD')==SHA and not git('status','--porcelain')
assert not OUT.exists()
owner=open('/tmp/geo337-native-owner.lock','a+')
fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
OUT.mkdir(); (OUT/'tmp').mkdir()
resource.setrlimit(resource.RLIMIT_STACK,(16777216,resource.getrlimit(resource.RLIMIT_STACK)[1]))
reaper.enable()
env={'PATH':os.environ['PATH'],'HOME':os.environ['HOME'],'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TMPDIR':str(OUT/'tmp'),'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8','PYTHONOPTIMIZE':'0','GITHUB_SHA':SHA,'GITHUB_WORKSPACE':str(ROOT)}
before=binding();dump(OUT/'SOURCE_BEFORE.json',before)
dump(OUT/'REQUEST.json',{'sha':SHA,'cwd':str(ROOT),'started_utc':utc(),'environment':env,'stack_bytes':16777216,'owner_lock':'/tmp/geo337-native-owner.lock','oracle_witness_lock':str(OUT/'heavy.lock'),'stage_limit_source':'run_stage.historical.py branches; historical wrapper assigned these values but invoked reaper with timeout=None; this launcher explicitly enforces those declared caps without changing the test commands','free_before':{p:shutil.disk_usage(p).free for p in ['/tmp','/workspace']}})
native=Path('/workspace/scratch/geo337-native-F-cbf0fb62-20261027-r2')
assert json.loads((native/'RESULT.json').read_text())['sha']==SHA
assert json.loads((native/'RESULT.json').read_text())['actual_process_returncode']==0
reuse=OUT/'same-F-native-originals';reuse.mkdir()
for name in ['REQUEST.json','RESULT.json','SUMMARY.json']:
    shutil.copy2(native/name,reuse/name)
for name in ['py_test_geo318_reading_a_oracle.json','py_test_geo318_reading_a_oracle.log','py_test_geo318_reading_a_oracle.unittest.log','py_test_geo318_reading_a_native.json','py_test_geo318_reading_a_native.log','py_test_geo318_reading_a_native.unittest.log','oracle_framing-selftest.log']:
    shutil.copy2(Path('/tmp/geometry-tests/run_all-logs')/name,reuse/name)
py=sys.executable
compare="from pathlib import Path;import hashlib,json,sys;a=Path(sys.argv[1]).read_bytes();b=Path(sys.argv[2]).read_bytes();print(json.dumps({'generated_sha256':hashlib.sha256(a).hexdigest(),'committed_sha256':hashlib.sha256(b).hexdigest(),'byte_identical':a==b}));sys.exit(0 if a==b else 1)"
stages=[
 ('golden-source-proof',[py,'-B',str(ROOT/'evidence/issue318-reading-a-20261023/tools/prove_golden_witness.py'),'--root',str(ROOT),'--sha',SHA,'--output',str(OUT/'golden-proof'),'--heavy-lock',str(OUT/'heavy.lock')],300),
 ('golden-generate',[py,'-B',str(ORACLE/'make_golden.py'),str(ORACLE/'rooms.json'),str(OUT/'golden-generated.json')],300),
 ('golden-compare',[py,'-B','-c',compare,str(OUT/'golden-generated.json'),str(ORACLE/'oracle-golden.json')],30),
 ('oracle-mutants',[py,'-B',str(ORACLE/'selftest.py'),'--mutants-only'],1200),
 ('oracle-quick',[py,'-B',str(ORACLE/'selftest.py'),'--quick'],7200),
]
rows=[];all_reaped=[]
for name,argv,timeout in stages:
    assert git('rev-parse','HEAD')==SHA and not git('status','--porcelain') and binding()==before
    stage=OUT/name;stage.mkdir()
    row={'name':name,'argv':argv,'cwd':str(ROOT),'sha':SHA,'timeout_seconds':timeout,'started_utc':utc()}
    dump(stage/'request.json',row)
    stop=threading.Event()
    with (stage/'stdout.bin').open('wb') as stdout,(stage/'stderr.bin').open('wb') as stderr:
        start=time.monotonic();proc=subprocess.Popen(argv,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
        def collect():
            while not stop.wait(.05):
                for item in reaper.reap({proc.pid}):all_reaped.append({'stage':name,'utc':utc(),**item})
        thread=threading.Thread(target=collect,daemon=True);thread.start()
        dump(OUT/'RUNNING.json',{'stage':name,'pid':proc.pid,'sha':SHA,'started_utc':row['started_utc'],'timeout_seconds':timeout})
        expired=False
        try:rc=proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            expired=True;os.killpg(proc.pid,signal.SIGINT)
            try:rc=proc.wait(timeout=10)
            except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);rc=proc.wait()
        finally:stop.set();thread.join()
    row.update(actual_exit=rc,timed_out=expired,elapsed_seconds=time.monotonic()-start,ended_utc=utc(),sha_after=git('rev-parse','HEAD'),status_after=git('status','--porcelain'),source_unchanged=binding()==before)
    row['passed']=rc==0 and not expired and row['sha_after']==SHA and not row['status_after'] and row['source_unchanged']
    dump(stage/'result.json',row);rows.append(row);dump(OUT/'STAGES.json',rows)
    print(json.dumps(row,ensure_ascii=False),flush=True)
    assert row['sha_after']==SHA and not row['status_after'] and row['source_unchanged'],'source drift; stop dependent work'
dump(OUT/'REAPED.json',all_reaped);dump(OUT/'SOURCE_AFTER.json',binding())
dump(OUT/'RESULT.json',{'sha':SHA,'completed_utc':utc(),'passed':all(r['passed'] for r in rows),'stages':rows,'same_F_native_reused':True,'source_unchanged':binding()==before,'status_after':git('status','--porcelain'),'free_after':{p:shutil.disk_usage(p).free for p in ['/tmp','/workspace']}})
print((OUT/'RESULT.json').read_text(),flush=True)
