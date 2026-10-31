import os,sys,json,hashlib
from pathlib import Path
sys.path.insert(0,'/workspace/geo261-environment/final-f-contact-checker-proof-tools')
from capture import Recorder,dump
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
O=Path('/dev/shm/geometry-axiom-geo337-20261025');out=O/'closed-collection-root-original-20261026';assert not out.exists()
prep=Path('/tmp/geo337-closed-originals-collection-preparation-20261026');tool=prep/'collect_closed.py';plan=prep/'PLAN.all.json';peer=Path('/tmp/geo337-closed-originals-collection-static-peer-20261026/REVIEW.json')
assert h(tool)=='e3c516027d8868dda1c501631eb1d870e38269b78cf5856cdb6a470ba920eb7f';assert h(plan)=='3e91e87b2ba26ec42c6a4351af59ab0c873d7b269d8280ddcd93158ff9e97986';assert h(peer)=='c8212bdf6fa20eb46fdc8b0bd0e360d69afb7d5cc4ec92bdb0d1afd1cc5b1110'
j=json.loads(peer.read_bytes());assert j['exit_code']==0 and not j['blocking_findings']
q={'execute':True,'root_execution_lease':True,'root_no_writers_in_selected_roots':True,'collector_sha256':h(tool),'plan':{'path':str(plan),'sha256':h(plan)},'peer':{'path':str(peer),'sha256':h(peer)},'out':str(O/'resume-closed-original-package-20261026')}
out.mkdir();(out/'EXECUTOR.py').write_bytes(Path(__file__).read_bytes());dump(out/'REQUEST.json',q)
rec=Recorder(out,dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),'cbf0fb621888596aa14ad5f2349b503e23b1b72d')
row,b,e=rec.run(['python3','-B',str(tool),'--execute','--request',str(out/'REQUEST.json'),'--request-sha256',h(out/'REQUEST.json')],cwd='/workspace',timeout=600,check=False,source_variant='archive closed original receipts with their individual S10/a6/F identities; no source cleanup or tests')
dump(out/'RESULT.json',{'exit_code':row['actual_process_returncode'],'collected_fixed_roots':17,'originals_removed':False,'published':False});print(json.dumps({'exit_code':row['actual_process_returncode'],'stdout':b.decode(),'stderr':e.decode()}));sys.exit(row['actual_process_returncode'])
