"""Synthetic receipt binding only; never a real architecture gate or source read."""
from pathlib import Path
import argparse,copy,hashlib,importlib.util,json
HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('prepared_assembler',HERE/'assemble_a6.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ap=argparse.ArgumentParser();ap.add_argument('case',choices=['fixed','withdrawn-old-source','restored','withdrawn-count']);a=ap.parse_args()
stdout=b'';stderr=b'Ran 205 tests in 0.001s\n\nOK\n'
if a.case=='withdrawn-count':stderr=b'Ran 204 tests in 0.001s\n\nOK\n'
row={'command':['python3','-B','tests/test_architecture_contract.py'],'source_sha':m.SOURCE,'acceptance_sha':m.SOURCE,'cwd':str(m.ROOT),'actual_process_returncode':0,'timeout_expired':False,'stdout_sha256':m.H(stdout),'stderr_sha256':m.H(stderr),'stdout_bytes':len(stdout),'stderr_bytes':len(stderr),'started_epoch':1.0,'ended_epoch':2.0}
if a.case=='withdrawn-old-source':row['source_sha']=row['acceptance_sha']='82c922a3941525d3a094ac0158bdc7dea57ea360'
m.validate_gate(row,stdout,stderr,1)
print(json.dumps({'case':a.case,'synthetic_only':True,'formal_judges_executed':False,'source_binding':row['source_sha']}))
