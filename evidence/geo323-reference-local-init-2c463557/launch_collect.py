from pathlib import Path
import hashlib,importlib.util,json,os,sys
H=Path(__file__).resolve().parent;O=H/'collection-launch'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not O.exists()
assert sha(H/'collect.py')=='164b736aa3edb334f7c1cf556e257ce13d8d8cf342bd494fb9af5338e4670cf0'
assert sha(H/'PACKAGE_PLAN.json')=='5123d82a4b372e167398309db262e9fa43f43ddce82cc22660a96998b2677b92'
assert sha(Path('/tmp/geo337-h-init-collector-peer-20261025/STATIC_REVIEW.json'))=='575da3c782bdbf277ca3d60404cea1923d631f6c18d08a111522ba3abec37fef'
C=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert sha(C)=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
O.mkdir();sp=importlib.util.spec_from_file_location('capture',C);c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c)
env=dict(os.environ);env.pop('PYTHONOPTIMIZE',None);env['PYTHONDONTWRITEBYTECODE']='1'
r=c.Recorder(O,env,'2c4635577a8fcb11e88b346547f7bb1c7b739fb7')
row,stdout,stderr=r.run([sys.executable,'-B',str(H/'collect.py')],cwd=H,timeout=None,check=False)
result={'source_sha':'2c4635577a8fcb11e88b346547f7bb1c7b739fb7','exit':row['actual_process_returncode'],'collector_sha256':sha(H/'collect.py'),'plan_sha256':sha(H/'PACKAGE_PLAN.json'),'stdout_sha256':hashlib.sha256(stdout).hexdigest(),'stderr_sha256':hashlib.sha256(stderr).hexdigest(),'command':row}
c.dump(O/'RESULT.json',result);print(stdout.decode(errors='replace'));print(stderr.decode(errors='replace'),file=sys.stderr)
sys.exit(result['exit'])
