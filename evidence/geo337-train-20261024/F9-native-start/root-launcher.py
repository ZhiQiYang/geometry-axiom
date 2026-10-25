from pathlib import Path
import fcntl, hashlib, importlib.util, json, os, shutil, sys
F9='4f8a794f4167c3562eb182045102e86e9e37cca9'
ROOT=Path('/tmp/train337-323-f64d638f-source')
TOOL=Path('/tmp/native-final-executable-preparation/run_full_native_workflow_v2.py')
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
OUT=Path('/tmp/geo337-F9-native-launch-20261025')
JOB=Path('/tmp/geo337-F9-native-4f8a794f-20261025')
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert h(TOOL)=='763a6e8064be212a020522a43a80bdb6cd353d329997c83479f469c2359f4d21'
assert h(CAP)=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
assert not OUT.exists() and not JOB.exists()
assert shutil.disk_usage('/tmp').free>=134217728,'Original native operational resource allowance unavailable'
secondary=Path('/tmp/g261r3/secondary.lock').open('r+b')
fcntl.flock(secondary,fcntl.LOCK_EX|fcntl.LOCK_NB)
OUT.mkdir()
spec=importlib.util.spec_from_file_location('capture',CAP);cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
env={k:v for k,v in os.environ.items() if not k.startswith(('MUTATE_','GIT_')) and k not in ('PYTHONOPTIMIZE','PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','NODE_OPTIONS')}
env.update(PYTHONDONTWRITEBYTECODE='1',LANG='C.UTF-8',LC_ALL='C.UTF-8',PYTHONIOENCODING='utf-8')
rec=cap.Recorder(OUT,env,F9)
row,head,err=rec.run(['git','-C',str(ROOT),'rev-parse','HEAD'],cwd='/workspace',timeout=120,check=False,source_variant='original complete native at fixed F9')
assert row['actual_process_returncode']==0 and head.decode().strip()==F9
argv=[sys.executable,'-B',str(TOOL),'--repo',str(ROOT),'--sha',F9,'--out',str(JOB),'--resource-lock','/tmp/g261r3/heavy.lock','--root-cache-quiescent']
cap.dump(OUT/'REQUEST.json',{'source_sha':F9,'root':str(ROOT),'argv':argv,'tool_sha256':h(TOOL),'free_before':{p:shutil.disk_usage(p).free for p in ['/workspace','/tmp']},'root_quiescence_authorized':True,'root_secondary_exclusion':True,'original_ci_timeout_minutes':35,'source_or_tests_modified':False,'all_MUTATE_environment_removed':not any(k.startswith('MUTATE_') for k in env)})
row,stdout,stderr=rec.run(argv,cwd='/workspace',timeout=None,check=False,source_variant='original full native workflow; 35 minute CI gate unchanged')
result={'source_sha':F9,'actual_exit':row['actual_process_returncode'],'command':row,'job':str(JOB),'tests_modified':False}
cap.dump(OUT/'RESULT.json',result)
print(stdout.decode(errors='replace'));print(stderr.decode(errors='replace'),file=sys.stderr)
secondary.close()
sys.exit(row['actual_process_returncode'])
