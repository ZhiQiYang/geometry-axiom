"""Root invokes with formal require_escalated; unchanged c387 records collection."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, os, sys

ROOT=Path('/dev/shm/geometry-axiom-geo337-20261025')
F='4f8a794f4167c3562eb182045102e86e9e37cca9'
TOOL=Path('/workspace/geo337-assembly-terminal-preparation-20261025/collect_assembly_terminal.py')
TOOL_PIN='ff1aae84cd00a73190f3d8e7c3623087d9965804ae6821d872487a2b42b01049'
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
CAP_PIN='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--peer',type=Path);ap.add_argument('--peer-sha256');ap.add_argument('--execute-root-approved',action='store_true');a=ap.parse_args()
 if not a.execute_root_approved:
  print(json.dumps(dict(state='PREPARATION_ONLY',source_sha=F,collector_sha256=TOOL_PIN,requires='root require_escalated with exact accepted static peer; both attempts closed')));return 0
 need(not sys.flags.optimize and not os.environ.get('PYTHONOPTIMIZE'),'nonoptimized execution')
 need(sha(TOOL)==TOOL_PIN and sha(CAP)==CAP_PIN,'exact tool/capture')
 need(a.peer is not None and a.peer_sha256 is not None and a.peer.is_absolute() and not any(p.is_symlink() for p in [a.peer,*a.peer.parents]) and sha(a.peer)==a.peer_sha256,'exact peer')
 peer=json.loads(a.peer.read_bytes());need(type(peer.get('exit_code')) is int and peer['exit_code']==0 and peer.get('collector_sha256')==TOOL_PIN and peer.get('launcher_sha256')==sha(__file__),'exact accepted subject and launcher')
 need(ROOT.is_dir() and not any(p.is_symlink() for p in [ROOT,*ROOT.parents]),'existing physical task root')
 out=ROOT/'assembly-terminal-collection-original-20261025';package=ROOT/'assembly-terminal-package-20261025'
 need(not out.exists() and not package.exists(),'fresh raw/package outputs');out.mkdir(mode=0o700)
 q=dict(source_sha=F,root_execution_lease=True,both_attempts_closed_no_more_guard_writes=True,collector_sha256=TOOL_PIN,independent_peer=dict(path=str(a.peer),sha256=a.peer_sha256),out=str(package))
 request=out/'ROOT_REQUEST.json';request.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
 (out/'LAUNCHER.py.txt').write_bytes(Path(__file__).read_bytes())
 spec=importlib.util.spec_from_file_location('original_capture',CAP);cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
 env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1'
 for k in ['PYTHONOPTIMIZE','PYTHONPATH','PYTHONHOME','PYTHONSTARTUP']:env.pop(k,None)
 recorder=cap.Recorder(out,env,F)
 row,_,_=recorder.run([sys.executable,'-B',str(TOOL),'--request',str(request),'--request-sha256',sha(request),'--execute-root-approved'],cwd='/workspace',timeout=None,check=False,source_variant='collect both closed F9 assembly attempts without product rerun')
 result=dict(source_sha=F,exit_code=row['actual_process_returncode'],collection_only=True,product_rerun=False,delivered=False,collector_sha256=TOOL_PIN,peer_sha256=a.peer_sha256,commands=recorder.rows,package_result=str(package/'RESULT.json'))
 if (package/'RESULT.json').is_file():result['package_result_sha256']=sha(package/'RESULT.json')
 cap.dump(out/'RESULT.json',result);print(json.dumps(result,ensure_ascii=False),flush=True);return row['actual_process_returncode']
if __name__=='__main__':raise SystemExit(main())
