from pathlib import Path
import datetime,hashlib,importlib.util,json,os,shutil,sys,time
TOOLS=Path(__file__).parent
OUT=Path('/workspace/scratch/geo337-p52-capture-20261027')
SUBJECT=Path('/tmp/g337p52F27')
ROOT=Path('/workspace/geo337-p52-sources-20261027/fix')
MAIN=Path('/workspace/geo337-p52-sources-20261027/main')
SHA='cbf0fb621888596aa14ad5f2349b503e23b1b72d'
assert not OUT.exists() and not SUBJECT.exists();OUT.mkdir()
sys.dont_write_bytecode=True
capture_path=TOOLS/'capture.py';assert hashlib.sha256(capture_path.read_bytes()).hexdigest()=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
spec=importlib.util.spec_from_file_location('original_c387',capture_path);capture=importlib.util.module_from_spec(spec);spec.loader.exec_module(capture)
env={'PATH':os.environ['PATH'],'HOME':os.environ['HOME'],'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','PYTHONIOENCODING':'utf-8','PYTHONDONTWRITEBYTECODE':'1','GITHUB_SHA':SHA,'GITHUB_WORKSPACE':str(ROOT)}
argv=[sys.executable,'-B',str(TOOLS/'special/run_special.py'),'--gate','p52','--repo',str(ROOT),'--sha',SHA,'--out',str(SUBJECT),'--main-repo',str(MAIN),'--heavy-lock','/tmp/geo337-native-owner.lock','--preparation-sha256','254accbf8562210e339509c6bff0ab80f1ba625965bb70852ee428671f1a0805']
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
capture.dump(OUT/'REQUEST.json',{'sha':SHA,'main_sha':'adbaebf9c73ea6801d7b4d5214e4b846b132923b','argv':argv,'cwd':str(ROOT),'environment':env,'outer_timeout_seconds':None,'started_utc':started,'outer_pid':os.getpid(),'free_before':{p:shutil.disk_usage(p).free for p in ['/workspace','/tmp']},'original_scope':'Unmodified generic run_special, unmodified P52 formal body and independent verifier. No performance rerun if valid samples already exist. No source/test/assertion/time-limit change.'})
recorder=capture.Recorder(OUT,env,SHA);start=time.monotonic()
row,stdout,stderr=recorder.run(argv,cwd=ROOT,timeout=None,check=False,source_sha=SHA,source_variant='fixed-F-original-P52-formal-and-verifier')
receipt=json.loads((SUBJECT/'receipt.json').read_text()) if (SUBJECT/'receipt.json').exists() else None
capture.dump(OUT/'RESULT.json',{'sha':SHA,'main_sha':'adbaebf9c73ea6801d7b4d5214e4b846b132923b','actual_exit':row['actual_process_returncode'],'timeout_expired':row['timeout_expired'],'elapsed_seconds':time.monotonic()-start,'started_utc':started,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':row['actual_process_returncode']==0 and bool(receipt and receipt['passed']),'original_receipt_present':receipt is not None,'original_phases':receipt.get('phases') if receipt else None,'free_after':{p:shutil.disk_usage(p).free for p in ['/workspace','/tmp']}})
print(json.dumps({'actual_exit':row['actual_process_returncode'],'original_passed':receipt.get('passed') if receipt else None,'result':str(OUT/'RESULT.json')}),flush=True)
