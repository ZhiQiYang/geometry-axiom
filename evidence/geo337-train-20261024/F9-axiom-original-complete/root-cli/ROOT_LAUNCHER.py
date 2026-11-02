from pathlib import Path
import hashlib,importlib.util,json,os,sys
ROOT=Path('/dev/shm/geometry-axiom-geo337-20261025');F='4f8a794f4167c3562eb182045102e86e9e37cca9'
PREP=Path('/workspace/geo337-F9-axiom-collection-preparation-20261025');TOOL=PREP/'collect_axiom.py'
PEER=Path('/workspace/geo337-F9-axiom-collector-static-peer-20261025/REVIEW.json')
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(TOOL)=='0587f5a2730f8ce66406235e3dce176bd1e22e99865351e04ef85ebf34774787'
assert sha(PEER)=='ce6da9ebf9fc389900831d1b254df83851682899ee983bbb5cad2a667e8566ec'
assert sha(CAP)=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
out=ROOT/'axiom-collection-root-original-20261025';out.mkdir()
q=json.loads((PREP/'COLLECTION_REQUEST.unbound.json').read_bytes());q.update(source_sha=F,execute=True,root_execution_lease=True,collector_sha256=sha(TOOL),independent_peer=dict(path=str(PEER),sha256=sha(PEER)),out=str(ROOT/'geo337-F9-axiom-terminal-package-20261025'))
request=out/'ROOT_REQUEST.json';request.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
(out/'ROOT_LAUNCHER.py').write_bytes(Path(__file__).read_bytes())
spec=importlib.util.spec_from_file_location('capture',CAP);cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONOPTIMIZE',None);rec=cap.Recorder(out,env,F)
r,_,_=rec.run([sys.executable,'-B',str(TOOL),'--request',str(request),'--execute'],cwd='/workspace',timeout=None,check=False,source_variant='collect already-completed original F9 axiom raw; no subject rerun')
j=dict(source_sha=F,exit_code=r['actual_process_returncode'],request_sha256=sha(request),collector_sha256=sha(TOOL),peer_sha256=sha(PEER),commands=rec.rows,subject_rerun=False,delivered=False,package_result=q['out']+'/RESULT.json');cap.dump(out/'RESULT.json',j)
print(json.dumps({k:j[k]for k in ['source_sha','exit_code','package_result','subject_rerun','delivered']}));raise SystemExit(r['actual_process_returncode'])
