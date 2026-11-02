"""Capture the reviewed read-only terminal collector, never a subject gate."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,sys
p=argparse.ArgumentParser();p.add_argument('--gate',choices=['required-eight','pf3'],required=True);a=p.parse_args()
BASE=Path(__file__).parent;TOOL=BASE/'collect_original_nonperf.py'
assert hashlib.sha256(TOOL.read_bytes()).hexdigest()=='ce93f88fa5bd8f409977adf7731dcbd418f286afe64838ec3e2d5cad80acfeb4'
PEER=Path('/workspace/train337-canvas-peer-resume/REQUIRED8_PF3_COLLECTOR_STATIC_PEER.json')
assert hashlib.sha256(PEER.read_bytes()).hexdigest()=='844814f17219ac00ac1c42c845916fdb7144912982429eec87ae5dd622353d59'
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py');assert hashlib.sha256(CAP.read_bytes()).hexdigest()=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
s=importlib.util.spec_from_file_location('cap',CAP);c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
out=BASE/(a.gate+'-collection-launch');out.mkdir();env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONOPTIMIZE',None)
r=c.Recorder(out,env,'7af8c5d80d34cb4f49d01ba67deb78a3a6d725db')
row,stdout,stderr=r.run([sys.executable,'-B',str(TOOL),'--gate',a.gate],cwd='/workspace',timeout=None,check=False,source_variant='terminal original output collection only; no subject execution')
c.dump(out/'RESULT.json',row);print(json.dumps(dict(exit_code=row['actual_process_returncode'],stdout=stdout.decode(),stderr=stderr.decode())));raise SystemExit(row['actual_process_returncode'])
