"""Collect complete original pure-Python guard proof; no product execution."""
from pathlib import Path
import hashlib,importlib.util,json,os,sys
P=Path(__file__).resolve().parent;OUT=P/'metadata-original-capture'
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert hashlib.sha256(CAP.read_bytes()).hexdigest()=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
assert not OUT.exists();OUT.mkdir()
spec=importlib.util.spec_from_file_location('original_metadata_capture',CAP);cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONOPTIMIZE',None)
rec=cap.Recorder(OUT,env,'75a1e93811a52b69385cbdaf6a09d773ed9052ad');rows=[]
for phase,args in [('fixed',[]),('withdrawn',['--withdraw-source-guard']),('restored',[])]:
 r,o,e=rec.run([sys.executable,'-B',str(P/'test_metadata_guards.py'),*args],cwd=P,timeout=None,check=False,source_variant='pure metadata guard self-proof; no C/performance/product execution')
 rows.append(dict(phase=phase,command=r,result=json.loads(o)))
assert [r['command']['actual_process_returncode']for r in rows]==[0,1,0]
assert rows[1]['result']['failures']==['wrong-source']
cap.dump(OUT/'RESULT.json',dict(exit=0,phases=rows,C_executed=False,product_mutation_proof=False,prior_short_capture_retained=True))
print(json.dumps(dict(exit=0,phase_exits=[0,1,0],C_executed=False)))
