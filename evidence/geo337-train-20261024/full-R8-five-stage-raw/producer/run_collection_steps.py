"""Capture the authorized original freeze and collector commands; never run the product."""
from pathlib import Path
import hashlib,importlib.util,json,os,sys
H=Path(__file__).resolve().parent;O=H/'collection-outer'
S='75a1e93811a52b69385cbdaf6a09d773ed9052ad'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not O.exists()
assert sha(H/'freeze_terminal_plan.py')=='f49ac614c307b0ac2c350dcd30af99bf4e510c5e809383a72b5245669237cda6'
assert sha(H/'collect.template.py')=='dffac4dfea4c954f15ef738b4a778e9d752c4da041b8ec27ec0eeb27a6ed4f5e'
assert sha(H/'launch.template.py')=='22e37f8e2eb8b8a012a45de5db275e6a0a4cf875658b5abe64806b947216e665'
assert sha(Path('/tmp/geo323-r8-collector-static-peer-20261025/REVIEW.json'))=='a187b89e5e089fddb07514a850e7c491abb78888b20844b6e1b9d41b6c6eba38'
C=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert sha(C)=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
O.mkdir();sp=importlib.util.spec_from_file_location('capture',C);c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c)
env=dict(os.environ);env.pop('PYTHONOPTIMIZE',None);env['PYTHONDONTWRITEBYTECODE']='1'
r=c.Recorder(O,env,S)
report={'source_sha':S,'source_subject_executed':False,'steps':[],'exit':None}
for phase,tool in [('freeze','freeze_terminal_plan.py'),('collect','launch.py')]:
 row,stdout,stderr=r.run([sys.executable,'-B',str(H/tool)],cwd=H,timeout=None,check=False)
 report['steps'].append({'phase':phase,'exit':row['actual_process_returncode'],'command':row})
 print(json.dumps({'phase':phase,'exit':row['actual_process_returncode'],'stdout':stdout.decode(errors='replace'),'stderr':stderr.decode(errors='replace')},ensure_ascii=False),flush=True)
 if row['actual_process_returncode']!=0:
  report['exit']=row['actual_process_returncode'];break
else:report['exit']=0
c.dump(O/'RESULT.json',report)
sys.exit(report['exit'])
