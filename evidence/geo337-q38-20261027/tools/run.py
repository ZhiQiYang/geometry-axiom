from pathlib import Path
import datetime,fcntl,hashlib,json,os,resource,runpy,shutil,subprocess,sys,tarfile,threading,time
sys.path.insert(0,'/workspace/scratch/geo337-pf3-tools-20261027')
import reaper
ROOT=Path('/workspace/geo337-native-F-cbf0fb62')
OUT=Path('/workspace/scratch/geo337-q38-F-cbf0fb62-20261027')
SHA='cbf0fb621888596aa14ad5f2349b503e23b1b72d'
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args],text=True).strip()
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert git('rev-parse','HEAD')==SHA and not git('status','--porcelain') and not OUT.exists()
lock=open('/tmp/geo337-native-owner.lock','a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
OUT.mkdir();(OUT/'tmp').mkdir();(OUT/'q38').mkdir();reaper.enable()
resource.setrlimit(resource.RLIMIT_STACK,(16777216,resource.getrlimit(resource.RLIMIT_STACK)[1]))
env={'PATH':os.environ['PATH'],'HOME':os.environ['HOME'],'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TMPDIR':str(OUT/'tmp'),'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8','GITHUB_SHA':SHA,'GITHUB_WORKSPACE':str(ROOT),'GEOMETRY_MODEL_BASE':str(OUT/'q38-bin/model-base'),'GEOMETRY_TEST_BRIDGE':str(OUT/'q38-bin/bridge')}
sys.dont_write_bytecode=True
scope=runpy.run_path(str(ROOT/'tests/section_profile_mutation_check.py'),run_name='q38_capture_scope')
assert len(scope['CASES'])==44
scope['copy_sources'](OUT/'source-snapshot',python=True)
source_map={str(p.relative_to(OUT/'source-snapshot')):h(p) for p in (OUT/'source-snapshot').rglob('*') if p.is_file()}
dump(OUT/'SOURCE_BEFORE.json',source_map);dump(OUT/'ORIGINAL_CASES.json',scope['CASES'])
shutil.copy2(ROOT/'geometry-core/SECTION-PROFILE-NATIVE-CONTRACT.md',OUT/'SECTION-PROFILE-NATIVE-CONTRACT.original.md')
shutil.copy2(ROOT/'evidence/geo337-train-20261024/prepared-during-F8/f9-nonperf-v2/tools/REQUESTS.json',OUT/'COMMAND_AUTHORITY.original.json')
build_code='from pathlib import Path; import sys; from tests import binaries; binaries.OUT_DIR=Path(sys.argv[1]); raise SystemExit(binaries.main(["build",sys.argv[2]]))'
commands=[('private-bridge-build',[sys.executable,'-B','-c',build_code,str(OUT/'q38-bin'),'bridge']),('model-base-build',[sys.executable,'-B','-c',build_code,str(OUT/'q38-bin'),'model-base']),('q38-complete',[sys.executable,'-B','-u','tests/section_profile_mutation_check.py','--receipt',str(OUT/'q38/receipt.json'),'--logs',str(OUT/'q38/logs'),'--jobs','1'])]
dump(OUT/'REQUEST.json',{'sha':SHA,'cwd':str(ROOT),'commands':commands,'environment':env,'started_utc':utc(),'stack_bytes':16777216,'original_timeouts_seconds':{'native_compile':600,'tests':900,'model_adapter_build':900},'outer_timeout_seconds':None,'jobs':1,'expected_cases':[f'SPM{i:02d}' for i in range(1,45)],'owner_lock':'/tmp/geo337-native-owner.lock','free_before':{p:shutil.disk_usage(p).free for p in ['/workspace','/tmp']},'note':'Private bridge prerequisite prevents model tests from accessing the preserved shared native output. Original producer still rebuilds every native variant. No selectors or explore mode.'})
stages=[];reaped=[];total=time.monotonic()
for name,argv in commands:
    stage=OUT/name;stage.mkdir();started=utc();stop=threading.Event()
    dump(stage/'REQUEST.json',{'argv':argv,'cwd':str(ROOT),'environment':env,'started_utc':started})
    with (stage/'stdout.bin').open('wb') as stdout,(stage/'stderr.bin').open('wb') as stderr:
        start=time.monotonic();proc=subprocess.Popen(argv,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
        def collect():
            while not stop.wait(.05):
                for row in reaper.reap({proc.pid}):reaped.append({'utc':utc(),'stage':name,**row})
        thread=threading.Thread(target=collect,daemon=True);thread.start()
        dump(OUT/'RUNNING.json',{'pid':proc.pid,'sha':SHA,'stage':name,'started_utc':started,'argv':argv})
        rc=proc.wait();elapsed=time.monotonic()-start;stop.set();thread.join()
    r={'stage':name,'actual_exit':rc,'elapsed_seconds':elapsed,'started_utc':started,'completed_utc':utc()};dump(stage/'RESULT.json',r);stages.append(r)
    if rc:break
status=git('status','--porcelain');head=git('rev-parse','HEAD')
unchanged=all(h(ROOT/p)==digest for p,digest in source_map.items())
receipt_path=OUT/'q38/receipt.json';receipt=json.loads(receipt_path.read_text()) if receipt_path.exists() else None
passed=len(stages)==3 and all(r['actual_exit']==0 for r in stages) and head==SHA and not status and unchanged and isinstance(receipt,dict)
if passed:
    passed=(set(r['id'] for r in receipt['results'])==set(f'SPM{i:02d}' for i in range(1,45)) and len(receipt['results'])==44 and all(r['verdict'] in ('killed','equivalent') for r in receipt['results']) and all(r['exit']==0 and r['exception_evidence']['skipped']==0 for r in receipt['baselines'].values()))
dump(OUT/'REAPED.json',reaped)
dump(OUT/'RESULT.json',{'sha':head,'passed':passed,'stages':stages,'elapsed_seconds':time.monotonic()-total,'completed_utc':utc(),'status_after':status,'source_unchanged':unchanged,'source_files_verified':len(source_map),'receipt_summary':receipt.get('summary') if receipt else None,'free_after':{p:shutil.disk_usage(p).free for p in ['/workspace','/tmp']},'temporary_source_policy':'The unmodified original producer deletes its disposable mutant source trees and binaries. Complete original persistent logs and exception receipts are preserved; the exact original source snapshot and mutation definitions are also retained. No discarded original temp is claimed to be archived.'})
with tarfile.open(OUT/'source-snapshot.original.tar.gz','w:gz') as tar:tar.add(OUT/'source-snapshot',arcname='source-snapshot')
print((OUT/'RESULT.json').read_text(),flush=True)
