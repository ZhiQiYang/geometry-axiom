"""Root-only three original architecture judges at actual a6, no relabelling."""
from pathlib import Path
import argparse,contextlib,fcntl,hashlib,importlib.util,json,os,resource,shutil,stat,sys
import prepare_source as shared

SOURCE=shared.SOURCE;ROOT=shared.ROOT;OWN=shared.OWN;OUT=OWN/'a6-architecture-gates-original-20261026'
CAP=shared.CAP;H=shared.H;need=shared.need;dump=shared.dump
JUDGES=[['tests/architecture_contract.py','--root','.','--manifest','geometry-core/domain-decoupling/product-architecture.json'],['tests/test_architecture_contract.py'],['tests/test_product_architecture.py']]
def pinned(item):
 p=Path(item['path']);raw=p.read_bytes();need(H(raw)==item['sha256'],'bound input '+str(p));return json.loads(raw)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--request',type=Path);ap.add_argument('--request-sha256');ap.add_argument('--execute-root-approved',action='store_true');a=ap.parse_args()
 if not a.execute_root_approved:print('PLAN_ONLY: actual a6 three architecture judges, source untouched');return 0
 need(not sys.flags.optimize and resource.getrlimit(resource.RLIMIT_STACK)[0]==16777216,'original16MiB stack and no optimization')
 raw=a.request.read_bytes();need(H(raw)==a.request_sha256,'exact root request');q=json.loads(raw)
 need(q['source_sha']==SOURCE and q['root_execution_lease']is True,'explicit actuala6 source lease')
 need(Path(q['source_result']['path'])==shared.OUT/'RESULT.json','exact actual source result path')
 prepared=pinned(q['source_result']);peer=pinned(q['source_actual_peer'])
 need(prepared['source_sha']==SOURCE and prepared['exit_code']==0 and prepared['materialized']is True,'actual newsource complete')
 need(peer['exit_code']==0 and not peer['blocking_findings']and peer['source_sha']==SOURCE and peer['source_result_sha256']==q['source_result']['sha256'],'actual newsource peer binding')
 manifest_path=shared.OUT/'SOURCE_MANIFEST.json';need(H(manifest_path.read_bytes())==prepared['source_manifest_sha256'],'new source manifest pin');manifest=json.loads(manifest_path.read_bytes())
 need(H(CAP.read_bytes())==shared.CAP_PIN and not OUT.exists(),'original recorder/fresh output')
 with contextlib.ExitStack()as stack:
  for p in map(Path,['/tmp/g261r3/heavy.lock','/tmp/g261r3/secondary.lock']):
   st=p.lstat();need(stat.S_ISREG(st.st_mode)and st.st_uid==os.getuid(),'existing owned scheduler locks');f=stack.enter_context(p.open('r+b'));need((os.fstat(f.fileno()).st_dev,os.fstat(f.fileno()).st_ino)==(st.st_dev,st.st_ino),'same lock');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  need(shared.combined_allocated()+64*1024**2<=2*1024**3 and shutil.disk_usage(OWN).free>=64*1024**2,'original64MiB and combined2GiB gate')
  OUT.mkdir(mode=0o700);(OUT/'tmp').mkdir();(OUT/'ROOT_REQUEST.json').write_bytes(raw);(OUT/'EXECUTOR.py').write_bytes(Path(__file__).read_bytes())
  sp=importlib.util.spec_from_file_location('capture',CAP);cap=importlib.util.module_from_spec(sp);sp.loader.exec_module(cap)
  env={k:v for k,v in os.environ.items()if not k.startswith(('GIT_','GEOMETRY_','MUTATE_'))and k not in ['PYTHONOPTIMIZE','PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','NODE_OPTIONS','LD_PRELOAD']}
  env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',LANG='C.UTF-8',LC_ALL='C.UTF-8',GIT_OPTIONAL_LOCKS='0',TMPDIR=str(OUT/'tmp'),TMP=str(OUT/'tmp'),TEMP=str(OUT/'tmp'),GITHUB_SHA=SOURCE,GITHUB_WORKSPACE=str(ROOT))
  index=ROOT/'.git/index';index_before=index.read_bytes();index_stat=index.stat();(OUT/'private-index').write_bytes(index_before)
  env.update(GIT_INDEX_FILE=str(OUT/'private-index'),GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='core.splitIndex',GIT_CONFIG_VALUE_0='false')
  rec=cap.Recorder(OUT,env,SOURCE);rows=[]
  result={'source_sha':SOURCE,'exit_code':1,'gates':rows,'full_native_executed':False,'full123_executed':False,'historical_gates_relabelled':False}
  def git(*args):return rec.run(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args],cwd=ROOT,timeout=None,check=True,source_sha=SOURCE,source_variant='a6 architecture original identity')[1]
  def state():
   head=git('rev-parse','HEAD').decode().strip();status=git('status','--porcelain=v1','--untracked-files=all').decode();idx=git('ls-files','--stage','-z')
   need(head==SOURCE and not status,'exact clean actuala6 source')
   return {'head':head,'status':status,'index':H(idx)}
  def snapshot():
   items=[]
   for name in manifest['architecture_paths']:
    p=ROOT/name;b=p.read_bytes();st=p.lstat();oid=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();need(stat.S_ISREG(st.st_mode)and st.st_nlink==1 and oid==manifest['files'][name]['oid'],'exact independent architecture source '+name)
    items.append({'path':name,'raw_sha256':H(b),'lf_sha256':H(b.replace(b'\r\n',b'\n')),'git_blob':oid})
   need(len(items)==604,'all604 source inputs')
   return items
  try:
   before=state();sources=snapshot();dump(OUT/'SOURCE_INPUTS.before.json',sources)
   for name,judge in zip(['architecture-contract','architecture-unit','product-architecture-unit'],JUDGES):
    row,stdout,stderr=rec.run([sys.executable,'-B',*judge],cwd=ROOT,timeout=None,check=False,source_sha=SOURCE,source_variant=name)
    rows.append({'gate':name,'exit_code':row['actual_process_returncode'],'command':row});dump(OUT/'PROGRESS.json',{'source_sha':SOURCE,'gates':rows,'terminal':False})
   after=state();after_sources=snapshot();dump(OUT/'SOURCE_INPUTS.after.json',after_sources)
   need(before==after and sources==after_sources,'full source identity unchanged across real judges')
   st=index.stat();need(index.read_bytes()==index_before and (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)==(index_stat.st_dev,index_stat.st_ino,index_stat.st_size,index_stat.st_mtime_ns),'real private source index untouched')
   ok=all(x['exit_code']==0 for x in rows)
   result.update(exit_code=0 if ok else 1,before=before,after=after,source_unchanged=True,all_gates_passed=ok,wrapper_exit=0 if ok else 1,source_inputs_before_sha256=H((OUT/'SOURCE_INPUTS.before.json').read_bytes()),source_inputs_after_sha256=H((OUT/'SOURCE_INPUTS.after.json').read_bytes()))
  except BaseException as e:result.update(exit_code=1,error=repr(e));raise
  finally:dump(OUT/'RESULT.json',result)
  print(json.dumps(result,ensure_ascii=False));return result['exit_code']
if __name__=='__main__':raise SystemExit(main())
