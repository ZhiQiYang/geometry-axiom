"""Capture only the reviewed F9 terminal collector; never launch native."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,sys
F9='4f8a794f4167c3562eb182045102e86e9e37cca9'
TOOL=Path(__file__).with_name('collect_terminal_native.py')
TOOL_PIN='17352ac43c5dbd911143c5771e0280d61e58a487293d2b3ad38e8cb272001e54'
GUARD_PIN='226015a2722a447ec3fceb5b18eaa5c918f7b0befd730cf2925fdf96aaef1834'
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
OUT=Path('/tmp/geo337-F9-native-terminal-collection-launch-20261025')
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--request',type=Path,required=True);ap.add_argument('--request-sha256',required=True);a=ap.parse_args()
 assert not sys.flags.optimize and 'PYTHONOPTIMIZE' not in os.environ
 assert h(TOOL)==TOOL_PIN and h(CAP)=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
 assert h(a.request)==a.request_sha256;q=json.loads(a.request.read_bytes());assert q['source_sha']==F9 and q['root_source_cache_collection_lease'] is True
 peer=q['independent_static_review'];assert h(peer['path'])==peer['sha256'];r=json.loads(Path(peer['path']).read_bytes());code=r.get('exit_code',r.get('exit'));assert type(code) is int and code==0
 assert r['collector_sha256']==TOOL_PIN and r['guard_sha256']==GUARD_PIN,'Independent review must bind these exact collector and guard bytes'
 assert not OUT.exists();OUT.mkdir()
 spec=importlib.util.spec_from_file_location('cap',CAP);cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
 env={k:v for k,v in os.environ.items() if not k.startswith(('GIT_','MUTATE_')) and k not in ['PYTHONOPTIMIZE','PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','LD_PRELOAD']};env['PYTHONDONTWRITEBYTECODE']='1'
 rec=cap.Recorder(OUT,env,F9);argv=[sys.executable,'-B',str(TOOL),'--request',str(a.request),'--request-sha256',a.request_sha256]
 cap.dump(OUT/'REQUEST.json',dict(source_sha=F9,command=argv,collector_sha256=TOOL_PIN,original_bound_request=str(a.request),original_bound_request_sha256=a.request_sha256,subject_rerun=False))
 row,stdout,stderr=rec.run(argv,cwd='/workspace',timeout=None,check=False,source_sha=F9,source_variant='F9 already-terminal original native complete collection; no subject rerun')
 result=dict(source_sha=F9,actual_exit=row['actual_process_returncode'],command=row,collector_only=True,subject_rerun=False,collection_success_is_not_formal_success=True)
 cap.dump(OUT/'RESULT.json',result);print(json.dumps({k:result[k] for k in ['source_sha','actual_exit','collector_only','subject_rerun']}));return row['actual_process_returncode']
if __name__=='__main__':raise SystemExit(main())
