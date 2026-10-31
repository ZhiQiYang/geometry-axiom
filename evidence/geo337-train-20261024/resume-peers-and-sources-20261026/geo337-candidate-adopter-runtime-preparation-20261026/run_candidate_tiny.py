"""Root-bound nine tiny real-Git phases; default preparation only."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,shutil,sys,time
OWN=Path('/dev/shm/geometry-axiom-geo337-20261025')
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
CAP_PIN='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
BOUND=16*1024*1024
def H(b):return hashlib.sha256(b).hexdigest()
def need(c,m):
 if not c:raise RuntimeError(m)
def used(root):
 seen=set();total=0
 for p in [root,*root.rglob('*')]:
  s=p.lstat();key=(s.st_dev,s.st_ino)
  if key not in seen:seen.add(key);total+=s.st_blocks*512
 return total
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--request',type=Path);p.add_argument('--request-sha256');a=p.parse_args()
 if not a.execute:print(json.dumps({'state':'PREPARATION_ONLY','formal_executed':False,'synthetic_phases':9,'additional_bound_bytes':BOUND}));return 0
 need(not sys.flags.optimize,'assertions enabled');raw=a.request.read_bytes();need(H(raw)==a.request_sha256,'request pin');q=json.loads(raw)
 need(q['execute']is True and q['root_capacity_admitted']is True and q['root_new_fixture_only_lease']is True,'root actual capacity and fixture lease required')
 need(q['schema']=='candidate-adopter-tiny-runtime/1'and q['additional_bound_bytes']==BOUND,'fixed synthetic scope/budget')
 subject=Path(q['subject']['path']);harness=Path(q['harness']['path']);need(H(subject.read_bytes())==q['subject']['sha256']=='71b0b4eb9ddde59f6b8e9ab90eb2492f8e403d1469a645d81864585a631fefba','fixed reviewed adopter')
 need(H(harness.read_bytes())==q['harness']['sha256'] and H(Path(__file__).read_bytes())==q['runner_sha256'],'pinned runtime helpers');need(H(CAP.read_bytes())==CAP_PIN,'original recorder')
 out=Path(q['out']);need(out.parent==OWN and out.name.startswith('geo337-candidate-adopter-tiny-')and not out.exists()and out.parent.resolve()==OWN and not out.parent.is_symlink(),'fresh canonical direct OWN fixture root')
 need(shutil.disk_usage(OWN).free>=BOUND,'actual synthetic capacity unavailable')
 sp=importlib.util.spec_from_file_location('capture',CAP);cap=importlib.util.module_from_spec(sp);sp.loader.exec_module(cap)
 out.mkdir();(out/'tmp').mkdir();(out/'REQUEST.json').write_bytes(raw);(out/'SUBJECT.py').write_bytes(subject.read_bytes());(out/'HARNESS.py').write_bytes(harness.read_bytes());(out/'RUNNER.py').write_bytes(Path(__file__).read_bytes())
 env={k:v for k,v in os.environ.items()if not k.startswith('GIT_') and k not in ('PYTHONPATH','PYTHONHOME','PYTHONOPTIMIZE','PYTHONSTARTUP','PYTHONPYCACHEPREFIX')};env.update(PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(out/'tmp'),TMP=str(out/'tmp'),TEMP=str(out/'tmp'))
 rec=cap.Recorder(out/'original-commands',env,'SYNTHETIC_CANDIDATE_PRIMITIVES_ONLY');result={'exit_code':1,'started_epoch':time.time(),'phases':[],'subject_sha256':q['subject']['sha256'],'request_sha256':a.request_sha256,'formal_adoption_executed':False,'schema_validations_or_actual_root_admission_proven':False,'additional_bound_bytes':BOUND,'runtime_allocated_max_observed':used(out)}
 markers={'cas':'CAS_EXPECTED_PARENT_NOT_ENFORCED','scope':'FOURTH_PRODUCT_PATH_NOT_REFUSED','preservation':'HISTORICAL_PUBLISHER_CHANGE_NOT_DETECTED'}
 try:
  for case in markers:
   exits=[]
   for phase,expected in [('fixed',0),('withdrawn',1),('restored',0)]:
    leaf=out/(case+'-'+phase);args=['python3','-B',str(harness),'--execute','--subject',str(subject),'--subject-sha256',q['subject']['sha256'],'--out',str(leaf),'--case',case,'--phase',phase]
    row,b,e=rec.run(args,cwd=out,timeout=120,check=False,source_variant=case+'/'+phase+'; only tiny fixture semantics')
    status=json.loads((leaf/'RESULT.json').read_bytes())if(leaf/'RESULT.json').exists()else None
    result['phases'].append({'case':case,'phase':phase,'command_directory':row['directory'],'actual_exit':row['actual_process_returncode'],'result':status})
    need(not row['timeout_expired']and type(row['actual_process_returncode'])is int and row['actual_process_returncode']==expected,'phase unexpected exit or timeout')
    need(status is not None and status['exit_code']==expected and status['case']==case and status['phase']==phase and status['positive_three_leaf_cas_and_push']is True,'phase setup or original positive missing')
    if expected==1:
     need(status['error_type']=='AssertionError'and status['error']==markers[case]and ('AssertionError: '+markers[case]).encode()in e,'withdrawal must fail the exact selected assertion')
    else:need(status['original_publisher_state_preserved']is True,'fixed/restored original state changed')
    exits.append(row['actual_process_returncode']);result['runtime_allocated_max_observed']=max(result['runtime_allocated_max_observed'],used(out));need(result['runtime_allocated_max_observed']<=BOUND,'synthetic allocation exceeded admitted 16MiB; originals retained')
    cap.dump(out/'RESULT.json',result)
   need(exits==[0,1,0],'exact three-phase exits');print(json.dumps({'case':case,'exits':exits}),flush=True)
  result.update(exit_code=0,synthetic_scope_only=True)
 except BaseException as exc:result['error']=repr(exc);raise
 finally:result['ended_epoch']=time.time();cap.dump(out/'RESULT.json',result)
 print(json.dumps({k:result[k]for k in ['exit_code','formal_adoption_executed','runtime_allocated_max_observed']}));return 0
if __name__=='__main__':raise SystemExit(main())
