"""Capture the small terminal projection only; do not freeze or pack raw evidence."""
from pathlib import Path
import hashlib,importlib.util,os,sys
H=Path(__file__).resolve().parent;O=H/'summary-launch'
S='75a1e93811a52b69385cbdaf6a09d773ed9052ad'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not O.exists()
assert sha(H/'summarize_terminal.py')=='7a9d89c5c0ef901e6b52dffe0385329d9837959a4cebd7872d18dbf624ef3e1e'
C=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert sha(C)=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
O.mkdir();sp=importlib.util.spec_from_file_location('capture',C);c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c)
env=dict(os.environ);env.pop('PYTHONOPTIMIZE',None);env['PYTHONDONTWRITEBYTECODE']='1'
r=c.Recorder(O,env,S)
row,stdout,stderr=r.run([sys.executable,'-B',str(H/'summarize_terminal.py')],cwd=H,timeout=None,check=False)
result={'source_sha':S,'exit':row['actual_process_returncode'],'summary_producer_sha256':sha(H/'summarize_terminal.py'),'command':row,'frozen_or_packed':False,'subject_executed':False}
c.dump(O/'RESULT.json',result);print(stdout.decode(errors='replace'));print(stderr.decode(errors='replace'),file=sys.stderr)
sys.exit(result['exit'])
