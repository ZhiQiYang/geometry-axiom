from pathlib import Path
import argparse,hashlib,importlib.util,json,os,re
p=argparse.ArgumentParser();p.add_argument('--product-sha',required=True);p.add_argument('--execution-head');p.add_argument('--out',required=True,type=Path);a=p.parse_args()
R=Path('/workspace/geometry-axiom');O=a.out.resolve();F=a.product_sha;E=a.execution_head or F
assert re.fullmatch('[0-9a-f]{40}',F) and re.fullmatch('[0-9a-f]{40}',E) and not O.exists() and not O.is_relative_to(R)
assert not any(k.startswith('MUTATE_') for k in os.environ), 'tracked ledger check must not inherit a MUTATE_* override'
O.mkdir();(O/'check_tool.py').write_bytes(Path(__file__).read_bytes())
p=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py');assert hashlib.sha256(p.read_bytes()).hexdigest()=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762';s=importlib.util.spec_from_file_location('cap',p);c=importlib.util.module_from_spec(s);s.loader.exec_module(c);env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONOPTIMIZE',None);r=c.Recorder(O,env,E)
def run(argv,check=True):return r.run(argv,cwd=R,timeout=None,check=check,source_sha=E,source_variant='new R7 product source '+F+' at execution head '+E+'; exact non-evidence tree equality guarded')
assert run(['git','rev-parse','HEAD'])[1].decode().strip()==E and not run(['git','status','--porcelain=v1'])[1]
assert not run(['git','diff','--name-only',F,E,'--','.',':(exclude)evidence'])[1]
row,out,err=run(['python3','tests/mutate.py','--check'],check=False)
assert run(['git','rev-parse','HEAD'])[1].decode().strip()==E and not run(['git','status','--porcelain=v1'])[1]
c.dump(O/'RESULT.json',{'product_source':F,'execution_head':E,'command':['python3','tests/mutate.py','--check'],'exit':row['actual_process_returncode'],'source_unchanged':True,'ledger_regenerated':False,'driver_completed':True,'source_variant':'product F / physical E recorded separately; no check verdict relabeled','tool_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()});print((O/'RESULT.json').read_text());print(out.decode());print(err.decode())
