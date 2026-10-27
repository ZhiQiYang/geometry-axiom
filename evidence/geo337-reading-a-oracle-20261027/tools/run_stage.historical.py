"""One explicit original #318 acceptance stage with SHA/environment/raw capture.

Does not schedule tests automatically. Requires a clean checkout at --sha and
an explicitly assigned root scheduler slot. Original unlocked semantic stages
stay unlocked; the existing golden proof retains its original internal R3.
"""
from pathlib import Path
import argparse,datetime,fcntl,hashlib,importlib.util,json,os,platform,resource,sys,traceback

STAGES=('reader-generate','reader-check','reader-unit','native-7','oracle-13','golden-source-proof','golden-generate','golden-compare','oracle-mutants','oracle-quick','cli-build','cli-order','architecture-contract','architecture-unit','product-architecture')
CAPTURE=Path('/workspace/geo288-main-merge-20261023/bound-3d681636/p73/capture.py')
CAPTURE_SHA='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
REAPER=Path('/workspace/geo261-environment/reap_children.py')
REAPER_SHA='7d848d6c135b7f329852d16c6da5743effde8b29ccbbc6e70092b6ba25877760'
def digest(raw):return hashlib.sha256(raw).hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--root',required=True,type=Path);p.add_argument('--sha',required=True)
 p.add_argument('--output',required=True,type=Path);p.add_argument('--stage',choices=STAGES,required=True)
 p.add_argument('--scheduler-slot',type=int,choices=(1,2),required=True)
 p.add_argument('--heavy-lock',type=Path,default=Path('/tmp/g261r3/heavy.lock'))
 a=p.parse_args();root=a.root.resolve();out=a.output.resolve();base=Path(__file__).resolve().parent
 if sys.flags.optimize:raise RuntimeError('Formal runner assertions must be enabled')
 if out.exists() or not root.is_dir() or out.is_relative_to(root):raise RuntimeError('Need existing source and new external stage directory')
 if digest(CAPTURE.read_bytes())!=CAPTURE_SHA or digest(REAPER.read_bytes())!=REAPER_SHA:raise RuntimeError('Original capture/reaper bytes drifted')
 out.mkdir(parents=True);(out/'tmp').mkdir();(out/'artifacts').mkdir()
 spec=importlib.util.spec_from_file_location('_original_geo318_capture',CAPTURE);capture=importlib.util.module_from_spec(spec);spec.loader.exec_module(capture)
 env=dict(os.environ);cleared=[]
 for key in list(env):
  if key.startswith('GEOMETRY_') or key in ('NODE_OPTIONS','PYTHONPATH','PYTHONSTARTUP','PYTHONOPTIMIZE','LD_PRELOAD'):
   cleared.append(key);env.pop(key)
 env.update(LANG='C.UTF-8',LC_ALL='C.UTF-8',PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',PYTHONOPTIMIZE='0',
            GITHUB_SHA=a.sha,GITHUB_WORKSPACE=str(root),TMPDIR=str(out/'tmp'),GEO318_ARTIFACT_DIR=str(out/'artifacts'),
            GEO299316_EXECUTION_LOG=str(out/'native-execution.jsonl'),GEO261_REAPER_LOG=str(out/'reaper.jsonl'))
 recorder=capture.Recorder(out,env,a.sha);guards=[];errors=[]
 safe=('PATH','LANG','LC_ALL','PYTHONDONTWRITEBYTECODE','PYTHONIOENCODING','PYTHONOPTIMIZE','TMPDIR','GITHUB_SHA','GITHUB_WORKSPACE','GEO318_ARTIFACT_DIR','GEO299316_EXECUTION_LOG','GEO261_REAPER_LOG','CC','CFLAGS','CPPFLAGS','LDFLAGS','C_INCLUDE_PATH','CPATH','LIBRARY_PATH','LD_LIBRARY_PATH','GCC_EXEC_PREFIX','COMPILER_PATH')
 receipt={'schema':'geo318-reading-a-original-stage/1','stage':a.stage,'sha':a.sha,'root':str(root),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'environment':{k:env.get(k) for k in safe},'cleared_environment_names':cleared,'platform':platform.platform(),'python':sys.version,'guards':guards,'errors':errors,
          'tool_sha256':{str(q):digest(q.read_bytes()) for q in (Path(__file__),base/'native_with_compile_log_retention.py',CAPTURE,REAPER)},'root_scheduler_slot':a.scheduler_slot,'actual_exit_code':None,'passed':False}
 save(out/'receipt.json',receipt)
 def run(argv,timeout=120):return recorder.run(list(map(str,argv)),cwd=root,timeout=timeout,check=False,source_sha=a.sha,source_variant='original-'+a.stage)
 def guard(label):
  row={'label':label}
  for name,args in [('head',['git','rev-parse','HEAD']),('status',['git','status','--porcelain=v1','--untracked-files=all']),('cached',['git','diff','--cached','--name-only'])]:
   result,stdout,stderr=run(args);row[name]=stdout.decode('utf-8','replace');row[name+'_exit']=result['actual_process_returncode']
  guards.append(row)
  if row['head'].strip()!=a.sha or row['status'] or row['cached'] or any(row[k+'_exit'] for k in ('head','status','cached')):raise RuntimeError('Original source guard failed: '+label)
  return row
 lock=None;soft,hard=resource.getrlimit(resource.RLIMIT_STACK)
 try:
  if hard!=resource.RLIM_INFINITY and hard<16384*1024:raise RuntimeError('Hard stack below required16MiB')
  resource.setrlimit(resource.RLIMIT_STACK,(16384*1024,hard));receipt['stack_during']=[16384*1024,hard]
  if a.stage=='golden-source-proof':
   if a.heavy_lock.resolve()!=Path('/tmp/g261r3/heavy.lock') or not a.heavy_lock.is_file():raise RuntimeError('Need the existing original global R3 lock, never a new or alternate lock')
   receipt['R3']={'path':str(a.heavy_lock),'mode':'existing prove_golden_witness.py self-lock; not double-wrapped','acquired_by_outer':False}
  else:receipt['R3']={'mode':'original entry has no lock; no additional R3 added; root explicitly assigns at most two semantic slots','acquired_by_outer':False}
  guard('before')
  oracle=root/'geometry-core/framing-template/oracle';tools=root/'evidence/issue318-reading-a-20261023/tools';py=sys.executable
  receipt['versions']=[]
  for version_argv in ([py,'--version'],['node','--version']):
   version_row,version_stdout,version_stderr=run(version_argv)
   receipt['versions'].append({'result':version_row,'stdout':version_stdout.decode('utf-8','replace'),'stderr':version_stderr.decode('utf-8','replace')})
   if version_row['actual_process_returncode']!=0:raise RuntimeError('Environment version command failed before original stage')
  if a.stage=='reader-generate':argv=[py,'-B',root/'geometry-guide/sync_axiom_reader.py'];timeout=300
  elif a.stage=='reader-check':argv=[py,'-B',root/'geometry-guide/sync_axiom_reader.py','--check'];timeout=300
  elif a.stage=='reader-unit':argv=[py,'-B',root/'tests/test_axiom_reader.py'];timeout=1200
  elif a.stage=='native-7':argv=[py,'-B',base/'native_with_compile_log_retention.py','--root',root,'--artifacts',out/'compile-logs'];timeout=1800
  elif a.stage=='oracle-13':argv=[py,'-B',root/'tests/test_geo318_reading_a_oracle.py','-v'];timeout=300
  elif a.stage=='golden-source-proof':argv=[py,'-B',tools/'prove_golden_witness.py','--root',root,'--sha',a.sha,'--output',out/'proof','--heavy-lock',a.heavy_lock];timeout=300
  elif a.stage=='golden-generate':argv=[py,'-B',oracle/'make_golden.py',oracle/'rooms.json',out.parent/'golden-generated.json'];timeout=300
  elif a.stage=='golden-compare':
   code="from pathlib import Path;import hashlib,json,sys;a=Path(sys.argv[1]).read_bytes();b=Path(sys.argv[2]).read_bytes();print(json.dumps({'generated_sha256':hashlib.sha256(a).hexdigest(),'committed_sha256':hashlib.sha256(b).hexdigest(),'byte_identical':a==b}));sys.exit(0 if a==b else 1)"
   argv=[py,'-B','-c',code,out.parent/'golden-generated.json',oracle/'oracle-golden.json'];timeout=30
  elif a.stage=='oracle-mutants':argv=[py,'-B',oracle/'selftest.py','--mutants-only'];timeout=1200
  elif a.stage=='oracle-quick':argv=[py,'-B',oracle/'selftest.py','--quick'];timeout=7200
  elif a.stage=='cli-build':argv=[py,'-B',root/'geometry-web/start_local.py','--build-only','--binary-dir',out.parent/'cli-runtime'];timeout=900
  elif a.stage=='cli-order':argv=[py,'-B',tools/'probe_cli_order.py','--bridge',out.parent/'cli-runtime/bridge','--sha',a.sha,'--output',out/'cli-order.json'];timeout=120
  elif a.stage=='architecture-contract':argv=[py,'-B',root/'tests/architecture_contract.py','--root',root,'--manifest',root/'geometry-core/domain-decoupling/product-architecture.json'];timeout=300
  elif a.stage=='architecture-unit':argv=[py,'-B',root/'tests/test_architecture_contract.py'];timeout=300
  elif a.stage=='product-architecture':argv=[py,'-B',root/'tests/test_product_architecture.py'];timeout=300
  receipt['original_command']=list(map(str,argv));receipt['outer_timeout_seconds']=None;receipt['original_internal_timeouts_unchanged']=True;save(out/'receipt.json',receipt)
  # The original subreaper gives the actual test its own session. Do not apply
  # c387's SIGKILL watchdog to that reaper: its children could otherwise survive
  # a killed forwarder. All original test/internal deadlines remain unchanged.
  row,stdout,stderr=run([py,'-B',REAPER,*argv],timeout=None);receipt['original_result']=row;receipt['actual_exit_code']=row['actual_process_returncode']
  receipt['reaper_final']=json.loads((out/'reaper.jsonl').read_text().splitlines()[-1])
  if receipt['reaper_final'].get('event')!='完成':raise RuntimeError('Original stage subreaper lacks terminal completion')
  guard('after')
  receipt['passed']=row['actual_process_returncode']==0 and not row['timeout_expired']
  if a.stage=='native-7' and receipt['passed']:
   receipt['compile_log_retention']=json.loads((out/'compile-logs/retention.json').read_text())
   if not receipt['compile_log_retention']:raise RuntimeError('Native originals lack retained compile diagnostics')
  if a.stage=='cli-order':
   rows=json.loads((out/'cli-order.json').read_text())['rows']
   receipt['scope']='reachability diagnostic; transport0 alone is never construction acceptance, and no new order-independence rule is imposed'
   receipt['diagnostic_completed']=receipt['passed'] and all(x['protocol_complete'] for x in rows)
   receipt['observed_orders']=[{'order':x['order'],'both_place_accepted':x['both_place_accepted']} for x in rows]
   receipt['construction_route_observed']=any(x['both_place_accepted'] for x in rows)
   receipt['both_orders_succeeded']=all(x['both_place_accepted'] for x in rows)
   receipt['passed']=receipt['diagnostic_completed'] and receipt['construction_route_observed']
 except BaseException:
  errors.append(traceback.format_exc());receipt['passed']=False
 finally:
  resource.setrlimit(resource.RLIMIT_STACK,(soft,hard))
  if lock is not None:lock.close()
  receipt['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save(out/'receipt.json',receipt)
 print(json.dumps({'stage':a.stage,'sha':a.sha,'actual_exit':receipt['actual_exit_code'],'passed':receipt['passed'],'errors':errors,'receipt':str(out/'receipt.json')},ensure_ascii=False))
 if receipt.get('busy'):return 75
 return 0 if receipt['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
