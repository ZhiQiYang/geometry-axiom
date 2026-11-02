from pathlib import Path
import hashlib,importlib.util,json,os,sys
ROOT=Path('/dev/shm/geometry-axiom-geo337-20261025');F='4f8a794f4167c3562eb182045102e86e9e37cca9'
PREP=Path('/workspace/geo323-F9-public-comparison-preparation-v2-20261025');TOOL=PREP/'collect_public_part4.py'
PEER=Path('/workspace/geo323-F9-PUBLIC-collector-static-peer-f4au2tlj/REVIEW.json')
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(TOOL)=='529d363cc5d07dc0cca155c98dc028d0bff1dcdd27d29d7b192bee85d9d8cfdb'
assert sha(PEER)=='39dba4a22ffa9bae8a66f3b669965e1da4b6fe14fa4908910a6a6ebe2c6fe632'
assert sha(CAP)=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
out=ROOT/'PUBLIC-comparison-collection-root-original-20261025';out.mkdir()
q=json.loads((PREP/'PUBLIC_COLLECTION_REQUEST.unbound.json').read_bytes());q.update(execute=True,root_execution_lease=True,collector_peer=dict(path=str(PEER),sha256=sha(PEER)))
request=out/'ROOT_REQUEST.json';request.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
(out/'ROOT_LAUNCHER.py').write_bytes(Path(__file__).read_bytes())
spec=importlib.util.spec_from_file_location('capture',CAP);cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONOPTIMIZE',None);rec=cap.Recorder(out,env,F)
r,_,_=rec.run([sys.executable,'-B',str(TOOL),'--request',str(request),'--execute'],cwd='/workspace',timeout=None,check=False,source_variant='PUBLIC-only archival projection; formal comparison bytes unchanged; private profile retained locally')
j=dict(source_sha=F,exit_code=r['actual_process_returncode'],request_sha256=sha(request),collector_sha256=sha(TOOL),peer_sha256=sha(PEER),commands=rec.rows,subject_rerun=False,private_originals_unchanged=True,delivered=False,package_result=q['out']+'/RESULT.json');cap.dump(out/'RESULT.json',j)
print(json.dumps({k:j[k]for k in ['source_sha','exit_code','package_result','subject_rerun','delivered']}));raise SystemExit(r['actual_process_returncode'])
