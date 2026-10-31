from pathlib import Path
import hashlib, importlib.util, json, os, shutil
L='7af8c5d80d34cb4f49d01ba67deb78a3a6d725db'
P=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert hashlib.sha256(P.read_bytes()).hexdigest()=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
s=importlib.util.spec_from_file_location('capture',P);c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
tool=Path('/tmp/native-final-executable-preparation/run_full_native_workflow_v2.py')
assert hashlib.sha256(tool.read_bytes()).hexdigest()=='763a6e8064be212a020522a43a80bdb6cd353d329997c83479f469c2359f4d21'
assert shutil.disk_usage('/tmp').free>=128*1024*1024, 'Original native operational reference; never lower to mask capacity.'
out=Path('/workspace/train337-native-L-7af8c5d8-r2-launch');out.mkdir()
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONOPTIMIZE',None)
rec=c.Recorder(out,env,L)
argv=['python3','-B',str(tool),'--repo','/tmp/train337-323-f64d638f-source','--sha',L,'--out','/tmp/train337-full-native-L-7af8c5d8-r2','--resource-lock','/tmp/g261r3/heavy.lock','--root-cache-quiescent']
c.dump(out/'launch-request.json',dict(source_sha=L,argv=argv,driver_sha256=hashlib.sha256(tool.read_bytes()).hexdigest(),native_scope='Original full workflow, no selectors, exact 35 minute CI gate retained',root_and_shared_cache_exclusively_leased=True,free_before={p:shutil.disk_usage(p).free for p in ['/tmp','/workspace']}))
row,stdout,stderr=rec.run(argv,cwd='/workspace',timeout=None,check=False,source_variant='original-final-L-complete-native-after-three-fixture-materialization')
result=dict(source_sha=L,actual_exit=row['actual_process_returncode'],command=row)
c.dump(out/'receipt.json',result);print(json.dumps({k:v for k,v in result.items() if k!='command'}));raise SystemExit(row['actual_process_returncode'])
