"""Root binds two true counterproof terminal pins and runs unchanged c387, without product rerun."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, os, sys
ROOT=Path('/dev/shm/geometry-axiom-geo337-20261025')
F='4f8a794f4167c3562eb182045102e86e9e37cca9'
TOOL=Path('/workspace/geo314-counterproof-terminal-preparation-20261025/collect_counterproof_terminal.py')
TOOL_PIN='1c313dca29e47629da572e4afe54f42b5a3ea3c04d97bc16b3afe2de4c89b72f'
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
CAP_PIN='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
JOBS=('v2','v3')
FINALS={'v2': '/workspace/geo314-F9-shm-counterproof-EXEC_FINAL-20261025.json', 'v3': '/workspace/geo314-F9-all-private-counterproof-EXEC_FINAL-20261025.json'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def physical(p):
 p=Path(p);need(p.is_absolute()and not any(x.is_symlink()for x in [p,*p.parents]),'physical path');return p
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--peer',type=Path);ap.add_argument('--peer-sha256');ap.add_argument('--terminal-pins',type=Path);ap.add_argument('--terminal-pins-sha256');ap.add_argument('--execute-root-approved',action='store_true');a=ap.parse_args()
 if not a.execute_root_approved:
  print(json.dumps(dict(state='PREPARATION_ONLY',source_sha=F,collector_sha256=TOOL_PIN,jobs=JOBS,requires='root formal require_escalated, all two true counterproof terminal pins and accepted static peer')));return 0
 need(not sys.flags.optimize and not os.environ.get('PYTHONOPTIMIZE'),'nonoptimized execution')
 need(sha(TOOL)==TOOL_PIN and sha(CAP)==CAP_PIN,'exact tool/capture')
 need(a.peer is not None and a.peer_sha256 is not None and sha(physical(a.peer))==a.peer_sha256,'exact peer')
 peer=json.loads(a.peer.read_bytes());need(type(peer.get('exit_code')) is int and peer['exit_code']==0 and peer.get('collector_sha256')==TOOL_PIN and peer.get('launcher_sha256')==sha(__file__),'exact accepted subject and launcher')
 need(a.terminal_pins is not None and a.terminal_pins_sha256 is not None and sha(physical(a.terminal_pins))==a.terminal_pins_sha256,'explicit terminal pins')
 terminals=json.loads(a.terminal_pins.read_bytes());need(set(terminals)==set(JOBS),'all four named jobs')
 for job in JOBS:
  need(set(terminals[job])=={'final_sha256'},'exact host terminal pin')
  need(sha(physical(FINALS[job]))==terminals[job]['final_sha256'],'true host terminal exact hash')
 need(physical(ROOT).is_dir(),'existing physical task root')
 out=ROOT/'geo314-counterproof-terminal-collection-original-20261025';package=ROOT/'geo314-counterproof-terminal-package-20261025'
 need(not out.exists() and not package.exists(),'fresh raw/package outputs');out.mkdir(mode=0o700)
 q=dict(source_sha=F,root_execution_lease=True,all_attempts_closed_no_more_writes=True,collector_sha256=TOOL_PIN,independent_peer=dict(path=str(a.peer),sha256=a.peer_sha256),terminal_inputs=terminals,out=str(package))
 request=out/'ROOT_REQUEST.json';request.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
 (out/'TERMINAL_PINS.json').write_bytes(a.terminal_pins.read_bytes());(out/'LAUNCHER.py.txt').write_bytes(Path(__file__).read_bytes())
 spec=importlib.util.spec_from_file_location('original_capture',CAP);cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
 env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1'
 for k in ['PYTHONOPTIMIZE','PYTHONPATH','PYTHONHOME','PYTHONSTARTUP']:env.pop(k,None)
 recorder=cap.Recorder(out,env,F)
 row,_,_=recorder.run([sys.executable,'-B',str(TOOL),'--request',str(request),'--request-sha256',sha(request),'--execute-root-approved'],cwd='/workspace',timeout=None,check=False,source_variant='collect closed F9 temporary-patch v2 failure and v3 proof without product rerun or live NATIVE read')
 result=dict(source_sha=F,exit_code=row['actual_process_returncode'],collection_only=True,product_rerun=False,delivered=False,collector_sha256=TOOL_PIN,peer_sha256=a.peer_sha256,terminal_pins_sha256=a.terminal_pins_sha256,commands=recorder.rows,package_result=str(package/'RESULT.json'))
 if (package/'RESULT.json').is_file():result['package_result_sha256']=sha(package/'RESULT.json')
 cap.dump(out/'RESULT.json',result);print(json.dumps(result,ensure_ascii=False),flush=True);return row['actual_process_returncode']
if __name__=='__main__':raise SystemExit(main())
