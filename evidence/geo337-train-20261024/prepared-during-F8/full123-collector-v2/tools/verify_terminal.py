"""After root receives the true terminal only; no collection, adoption or test execution."""
from pathlib import Path
import argparse,json
from terminal_guard import HERE,JOB,OUTER,CACHE,ROOT,TMP,verify_preparation,terminal_lease,bound_terminal,need
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',type=Path,required=True);p.add_argument('--request-sha256',required=True);p.add_argument('--preparation-sha256',required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--root-terminal-lease',action='store_true',required=True);a=p.parse_args()
verify_preparation(a.preparation_sha256);a.out=a.out.resolve();need(not a.out.exists() and a.out.parent.is_dir(),'fresh external output required')
need(a.out.is_relative_to(Path('/tmp')) or a.out.is_relative_to(Path('/workspace')),'private output required')
for base in (HERE,JOB,OUTER,CACHE,ROOT,TMP):need(not a.out.is_relative_to(base) and not base.is_relative_to(a.out),'output must not overlap original source/data/tools')
with terminal_lease():
    result=bound_terminal(a.request,a.request_sha256);a.out.mkdir();(a.out/'TERMINAL.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'terminal_capture_ready':True,'formal_accepted':result['formal_accepted'],'failed_conditions':result['failed_conditions'],'receipt':str(a.out/'TERMINAL.json')},ensure_ascii=False))
# Exit0 means terminal metadata was faithfully received, never formal pass.
