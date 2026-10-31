"""Parameterized original c387 outer launcher. Root execution only."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,sys
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
HERE=Path(__file__).resolve().parent

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--outer',type=Path,required=True);ap.add_argument('--sha',required=True)
 ap.add_argument('--driver-sha256',required=True);ap.add_argument('driver_args',nargs=argparse.REMAINDER)
 a=ap.parse_args();argv=a.driver_args[1:]if a.driver_args[:1]==['--']else a.driver_args
 if not (len(a.sha)==40 and all(c in '0123456789abcdef'for c in a.sha)):raise ValueError('full source SHA required')
 if argv.count('--sha')!=1 or argv[argv.index('--sha')+1]!=a.sha:raise ValueError('outer/driver exact same source SHA required')
 driver=HERE/'run_full_ledger.py';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 if h(driver)!=a.driver_sha256:raise ValueError('fixed driver SHA256 required')
 if h(CAP)!='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762':raise ValueError('original capture pin')
 outer=a.outer.resolve()
 if outer.exists()or not outer.parent.is_dir()or not(outer.is_relative_to(Path('/workspace'))or outer.is_relative_to(Path('/tmp'))):raise ValueError('fresh private outer path required')
 outer.mkdir();env=os.environ.copy()
 for key in list(env):
  if key.startswith(('GIT_','GEOMETRY_','MUTATE_'))or key in ('NODE_OPTIONS','PYTHONOPTIMIZE','PYTHONPATH','PYTHONSTARTUP'):del env[key]
 env['PYTHONDONTWRITEBYTECODE']='1'
 spec=importlib.util.spec_from_file_location('original_full_ledger_outer',CAP);cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
 command=[sys.executable,'-B',str(driver),*argv];rec=cap.Recorder(outer,env,a.sha)
 cap.dump(outer/'REQUEST.json',{'source_sha':a.sha,'argv':command,'driver_sha256':h(driver),'launcher_sha256':h(Path(__file__)),'original_capture_sha256':h(CAP),'outer_timeout':None,'scope':'root-owned original full123; no changed mutation definition or child threshold'})
 row,out,err=rec.run(command,cwd='/workspace',timeout=None,check=False,source_sha=a.sha,source_variant='root-owned-fresh-final-ledger-orchestrator')
 cap.dump(outer/'RESULT.json',{'source_sha':a.sha,'actual_exit':row['actual_process_returncode'],'command':row,'driver_sha256':h(driver)})
 sys.stdout.buffer.write(out);sys.stderr.buffer.write(err);return row['actual_process_returncode']
if __name__=='__main__':raise SystemExit(main())
