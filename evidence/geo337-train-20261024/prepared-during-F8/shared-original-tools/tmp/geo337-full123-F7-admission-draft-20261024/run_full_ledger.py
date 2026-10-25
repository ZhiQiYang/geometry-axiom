"""Root-only fresh full123 execution; no mutation/judge definitions are copied.
Uses the original reviewed passive observer and stream verifier unchanged.
"""
from pathlib import Path
import argparse,datetime,fcntl,hashlib,importlib.util,json,os,resource,stat,sys,traceback
HERE=Path(__file__).resolve().parent
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
REAPER=Path('/workspace/geo261-environment/reap_children.py')
PINS={HERE/'resource_admission.py':'bc93c7e37c29ed0ef3c93819e6e67ae0674f4b054ac7ab7df48a25ee718ba121',CAP:'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762',REAPER:'7d848d6c135b7f329852d16c6da5743effde8b29ccbbc6e70092b6ba25877760',HERE/'retain_mutation_streams.py':'67af8f6768232aa8439a0815a490a8b1076560afd0e40656f6de7edaa009e895',HERE/'verify_observed_core_raw.py':'12aa2060d03078b96d81ee6b4d28facdb4d3727fb6ff7d0b4c41271f550ac46b'}
def sha(b):return hashlib.sha256(b).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
 ap=argparse.ArgumentParser()
 for n in ('root','job','cache','tmp','prepared'):ap.add_argument('--'+n,type=Path,required=True)
 ap.add_argument('--sha',required=True);ap.add_argument('--prepared-sha256',required=True)
 ap.add_argument('--min-free-workspace-bytes',type=int,required=True)
 ap.add_argument('--filesystem-admission',type=Path,required=True)
 ap.add_argument('--filesystem-admission-sha256',required=True)
 ap.add_argument('--root-execution-lease',action='store_true',required=True)
 a=ap.parse_args();need(a.min_free_workspace_bytes>=0,'nonnegative storage resource reserve');need(len(a.sha)==40 and all(c in '0123456789abcdef'for c in a.sha),'full source SHA')
 for n in ('root','job','cache','tmp','prepared'):setattr(a,n,getattr(a,n).resolve())
 seed=a.cache/'_bridge-work'/a.sha/'repo';results=a.job/'mutants_results.json';obs=a.job/'observer'
 need(a.root.is_dir()and seed.is_dir(),'prepared source and independent seed required')
 need(not a.job.exists()and not a.tmp.exists(),'fresh job/TMPDIR')
 need(a.job.parent.is_dir()and a.tmp.parent.is_dir(),'existing private parents')
 need(sha(a.prepared.read_bytes())==a.prepared_sha256,'fixed preparation result')
 prep=json.loads(a.prepared.read_text());need(prep['exit']==0 and prep['materialized']and prep.get('original_metadata_closure_equal')is True and prep['source_sha']==a.sha and prep['pool']==str(a.root)and prep['seed']==str(seed),'exact successful preparation')
 for p in (a.root,seed,a.job,a.tmp,a.cache):
  need(p.is_relative_to(Path('/workspace'))or p.is_relative_to(Path('/tmp')),'private task path')
 for x,y in ((a.root,a.job),(a.root,a.cache),(a.root,a.tmp),(a.job,a.cache),(a.job,a.tmp),(a.cache,a.tmp)):
  need(not x.is_relative_to(y)and not y.is_relative_to(x),'independent source/output/cache/tmp paths')
 for p,h in PINS.items():need(sha(p.read_bytes())==h,'original tool pin '+str(p))
 env={k:v for k,v in os.environ.items()if not k.startswith(('GIT_','GEOMETRY_','MUTATE_'))and k not in ('NODE_OPTIONS','PYTHONOPTIMIZE','PYTHONPATH','PYTHONSTARTUP')}
 env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',TMPDIR=str(a.tmp),GITHUB_SHA=a.sha,GITHUB_WORKSPACE=str(a.root))
 a.job.mkdir();a.tmp.mkdir();spec=importlib.util.spec_from_file_location('original_full_ledger_capture',CAP);cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap);rec=cap.Recorder(a.job,env,a.sha)
 report={'sourceSHA':a.sha,'root':str(a.root),'seed':str(seed),'cache':str(a.cache),'prepared':str(a.prepared),'prepared_sha256':a.prepared_sha256,'startedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'outer_timeout':None,'phases':[],'original_child_timeouts_changed':False,'source_or_tests_modified_by_driver':False,'original_cli_exit':None,'passed':False,'exit_code':1};locks=[]
 def run(argv,phase=None,root=a.root):
  row,out,err=rec.run(argv,cwd=root,timeout=None,check=False,source_sha=a.sha,source_variant='root-owned-original-full123-fresh-cache')
  if phase:report['phases'].append({'phase':phase,'command':row})
  return row,out,err
 def state(path):
  answer={}
  for name,argv in [('head',['git','rev-parse','HEAD']),('tree',['git','rev-parse','HEAD^{tree}']),('status',['git','status','--porcelain=v1','--untracked-files=all']),('index',['git','ls-files','--stage','-z'])]:
   r,o,e=run(argv,root=path);need(r['actual_process_returncode']==0,'source state read failed');answer[name]=sha(o)if name=='index'else o.decode().strip()
  need(answer['head']==a.sha and answer['status']=='','source must stay exact clean SHA');return answer
 def generated_svg(label):
  p=a.root/'current_geometry.svg'
  if not p.exists():return
  st=p.lstat();need(stat.S_ISREG(st.st_mode)and st.st_nlink==1,'generated SVG must not alias retained originals')
  r,o,e=run(['git','ls-files','--error-unmatch','--','current_geometry.svg']);need(r['actual_process_returncode']==1,'only original untracked generated SVG')
  r,o,e=run(['git','check-ignore','--','current_geometry.svg']);need(r['actual_process_returncode']==0,'only original ignored generated SVG')
  body=p.read_bytes();dest=a.job/(label+'-current_geometry.svg');dest.write_bytes(body)
  report.setdefault('generated_outputs',[]).append({'original':str(p),'snapshot':str(dest),'bytes':len(body),'sha256':sha(body),'scope':'exact before/after snapshot; original file not deleted, only original program may write it'})
 try:
  for p in ('/tmp/g261r3/heavy.lock','/tmp/g261r3/secondary.lock'):
   lock=Path(p).open('a+b');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(lock)
  fs=os.statvfs('/workspace');free=fs.f_bavail*fs.f_frsize;report['free_workspace_before']=free;need(free>=a.min_free_workspace_bytes,'resource reserve not available; no formal launch')
  admission_spec=importlib.util.spec_from_file_location('full123_resource_admission',HERE/'resource_admission.py');admission_module=importlib.util.module_from_spec(admission_spec);admission_spec.loader.exec_module(admission_module)
  admission=admission_module.validate(a.filesystem_admission,a.filesystem_admission_sha256,a.sha,{'root':a.root,'cache':a.cache,'job':a.job,'tmp':a.tmp,'workspace':Path('/workspace')})
  report['filesystem_admission_before']=admission
  need(admission['passed'],'actual writable filesystem resource admission failed; original full123 UNRUN')
  soft,hard=resource.getrlimit(resource.RLIMIT_STACK);need(hard==resource.RLIM_INFINITY or hard>=16777216,'16 MiB stack unavailable');resource.setrlimit(resource.RLIMIT_STACK,(16777216,hard));report['stack_before']=[soft,hard];report['stack_after']=list(resource.getrlimit(resource.RLIMIT_STACK))
  # The only prepopulated cache content is the independently materialized seed.
  need(sorted(p.name for p in a.cache.iterdir())==['_bridge-work'],'fresh cache must contain no old binaries/sidecars/results')
  need(sorted(p.name for p in (a.cache/'_bridge-work').iterdir())==[a.sha],'one exact prepared seed')
  for p in seed.rglob('*'):
   if '.git'in p.relative_to(seed).parts:continue
   if p.is_file():need(stat.S_ISREG(p.lstat().st_mode)and p.stat().st_nlink==1,'mutable seed source has alias '+str(p))
  before={'root':state(a.root),'seed':state(seed)};report['source_before']=before;generated_svg('before')
  # Original old ledger may legitimately be stale after product changes. Its
  # real check exit is retained, not changed into a success or an early abort.
  run([sys.executable,'-B','tests/mutate.py','--check'],'original-tracked-ledger-check')
  env.update(MUTATE_RESULTS=str(results),MUTATE_CACHE=str(a.cache),GEO261_REAPER_LOG=str(a.job/'full-ledger-reaper.jsonl'))
  report['execution_environment']={k:env[k]for k in ('MUTATE_RESULTS','MUTATE_CACHE','GEO261_REAPER_LOG','TMPDIR','GITHUB_SHA','GITHUB_WORKSPACE')}
  argv=[sys.executable,'-B',str(REAPER),sys.executable,'-B',str(HERE/'retain_mutation_streams.py'),'--root',str(a.root),'--sha',a.sha,'--out',str(obs),'--']
  run(argv,'original-full123-passive-observer')
  run([sys.executable,'-B',str(HERE/'verify_observed_core_raw.py'),'--ledger',str(results),'--observations',str(obs),'--out',str(a.job/'CORE_RAW_MAPPING.json')],'original-core-stream-map')
  run([sys.executable,'-B','tests/mutate.py','--check'],'original-new-ledger-check')
  original=json.loads((obs/'receipt.json').read_text());report['original_cli_exit']=original['original_exit'];ledger=json.loads(results.read_text());report['ledger_count']=len(ledger);report['ledger_sha256']=sha(results.read_bytes())
  inventory=[];errors=[]
  for mid,item in ledger.items():
   ex=item.get('execution',{})
   if ex.get('schema')!='geometry-bridge-mutation-execution/1':continue
   phases=[(p,ex[p])for p in ('baseline_build','baseline','mutant_build','mutant','restored_build','restored')]
   phases += [('mutant_attempt-'+str(i+1),r)for i,r in enumerate(ex.get('mutant_attempts',[]))]
   for phase,r in phases:
    parent=a.cache/'_bridge-baseline'/a.sha if phase in ('baseline_build','baseline')else a.cache/mid
    for stream in ('stdout','stderr'):
     try:
      name=r[stream+'_file'];need(Path(name).name==name,'original stream basename');path=parent/name;body=path.read_bytes();need(sha(body)==r[stream+'_sha256'],'original bridge stream hash mismatch')
      inventory.append({'id':mid,'phase':phase,'stream':stream,'path':str(path),'bytes':len(body),'sha256':sha(body)})
     except Exception as exc:errors.append({'id':mid,'phase':phase,'stream':stream,'error':repr(exc)})
  dump(a.job/'BRIDGE_RAW_INVENTORY.json',{'files':inventory,'errors':errors})
  heads=[r['execution']['head']for r in ledger.values()if isinstance(r.get('execution'),dict)]
  report['execution_head_counts']={h:heads.count(h)for h in set(heads)};report['verdicts']={v:sum(r.get('verdict')==v for r in ledger.values())for v in {r.get('verdict')for r in ledger.values()}}
  need(len(ledger)==123 and len(heads)==120 and set(heads)=={a.sha},'complete original123/120 execution heads required; never relabel')
  need(sum(r.get('verdict')=='retired'for r in ledger.values())==3,'original3 retired rows only')
  report['source_after']={'root':state(a.root),'seed':state(seed)};need(report['source_after']==before,'source/index changed during original full ledger')
  need(original['original_exit']==0 and original['original_completed']is True,'original full CLI must truly finish0')
  need(not errors and inventory,'complete original bridge stream inventory')
  need([p['command']['actual_process_returncode']for p in report['phases'][1:]]==[0,0,0],'original full/map/newcheck gate nonzero')
  report['passed']=True;report['exit_code']=0
 except BaseException as exc:report['error']=repr(exc);report['error_traceback']=traceback.format_exc()
 finally:
  if len(locks)==2:
   # Every failed attempt retains actual source facts; never reset/clean it.
   final={}
   for label,path in [('root',a.root),('seed',seed)]:
    try:final[label]=state(path)
    except BaseException as exc:final[label]={'error':repr(exc),'scope':'all attempted original Git streams retained above'};report['passed']=False;report['exit_code']=1
   report['source_final']=final
   try:generated_svg('after')
   except BaseException as exc:report['generated_snapshot_error']=repr(exc);report['passed']=False;report['exit_code']=1
  report['commands']=rec.rows;report['endedUtc']=datetime.datetime.now(datetime.timezone.utc).isoformat();dump(a.job/'receipt.json',report)
  for lock in reversed(locks):lock.close()
 print(json.dumps({k:report.get(k)for k in ('sourceSHA','passed','exit_code','original_cli_exit','ledger_count','error')}));return report['exit_code']
if __name__=='__main__':raise SystemExit(main())
