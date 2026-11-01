"""Root-only independent a6 architecture checkout; no tests or legacy edits."""
from pathlib import Path
import argparse,contextlib,fcntl,hashlib,importlib.util,json,os,shutil,stat,sys

OWN=Path('/dev/shm/geometry-axiom-geo337-20261025')
OTHER=Path('/dev/shm/geo337-F9-browsers-20261025')
OWNER=OWN/'publisher-source'
ROOT=OWN/'a6-architecture-source-20261026'
OUT=OWN/'a6-architecture-source-original-20261026'
SOURCE='a6f4013364e21bcb7239b5dcc25caac0f6d61f77'
S10='82c922a3941525d3a094ac0158bdc7dea57ea360'
OLD_MANIFEST=OWN/'F10-source-preparation-reserve-anchor/SOURCE_MANIFEST.json'
OLD_PIN='e919aab396841642d093495b6fa7c7f4a20f55e1557929471dd6b2a81065057a'
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
CAP_PIN='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
DECISION_PIN='e6f2aee291850d9aaf8cc0026994f6c86894bb2a7849798ddd11cd63c5558740'
EXCLUDED=('evidence/','tests/evidence/','tests/release-evidence/')
def H(b):return hashlib.sha256(b).hexdigest()
def need(v,msg):
 if not v:raise RuntimeError(msg)
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def combined_allocated():
 seen=set();total=0
 for root in [OWN,OTHER]:
  for p in [root,*root.rglob('*')]:
   st=p.lstat();key=(st.st_dev,st.st_ino)
   if key not in seen:seen.add(key);total+=st.st_blocks*512
 return total
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute-root-approved',action='store_true');a=ap.parse_args()
 if not a.execute_root_approved:print('PLAN_ONLY: fresh independent a6 checkout; no source or tests read/executed');return 0
 need(not sys.flags.optimize,'no optimized Python')
 need(H(CAP.read_bytes())==CAP_PIN and H(OLD_MANIFEST.read_bytes())==OLD_PIN,'fixed recorder and old selected manifest')
 need(ROOT.parent==OUT.parent==OWN and OWN.resolve()==OWN and not ROOT.exists()and not OUT.exists(),'fresh OWN paths only')
 old=json.loads(OLD_MANIFEST.read_bytes());need(old['source_sha']==S10 and len(old['files'])==3763,'complete old3763 selected inventory')
 # Original selected source has one newly larger decision file; add16MiB for
 # index,32MiB raw+metadata,16MiB directories,64MiB reserve. No shrink by ratio.
 floor=sum((x['bytes']+4095)//4096*4096 for x in old['files'].values())
 bound=floor+4096+16*1024**2+32*1024**2+16*1024**2+64*1024**2
 with contextlib.ExitStack()as stack:
  for p in map(Path,['/tmp/g261r3/heavy.lock','/tmp/g261r3/secondary.lock']):
   st=p.lstat();need(stat.S_ISREG(st.st_mode)and st.st_uid==os.getuid(),'existing owned scheduler lock')
   f=stack.enter_context(p.open('r+b'));need((os.fstat(f.fileno()).st_dev,os.fstat(f.fileno()).st_ino)==(st.st_dev,st.st_ino),'lock identity');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  used=combined_allocated();need(used+bound<=2*1024**3 and shutil.disk_usage(OWN).free>=bound,'original two-OWN2GiB and actual mount admission')
  OUT.mkdir(mode=0o700);(OUT/'EXECUTOR.py').write_bytes(Path(__file__).read_bytes())
  spec=importlib.util.spec_from_file_location('original_capture',CAP);cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
  env={k:v for k,v in os.environ.items()if not k.startswith(('GIT_','GEOMETRY_','MUTATE_'))and k not in ['PYTHONOPTIMIZE','PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','NODE_OPTIONS','LD_PRELOAD']}
  env.update(GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',LANG='C.UTF-8',LC_ALL='C.UTF-8',TMPDIR=str(OUT),TMP=str(OUT),TEMP=str(OUT))
  rec=cap.Recorder(OUT,env,SOURCE)
  result={'source_sha':SOURCE,'exit_code':1,'source_root':str(ROOT),'formal_tests_executed':False,'historical_sources_modified':False,'source_hardlinks_used':False,'old_selected_manifest_sha256':OLD_PIN,'capacity':{'shared_before':used,'source_floor':floor,'additional_bound':bound,'original_reserve_bytes':67108864,'shared_ceiling':2147483648}}
  def git(*args,cwd=OWNER):return rec.run(['git','-c','gc.auto=0','-c','maintenance.auto=false',*map(str,args)],cwd=cwd,timeout=180,check=True,source_sha=SOURCE,source_variant='new independent a6 architecture checkout identity')[1]
  try:
   owner_index=(OWNER/'.git/index').read_bytes();owner_head=git('rev-parse','HEAD');owner_status=git('status','--porcelain=v1','--untracked-files=all');need(not owner_status,'owner must be clean')
   need(git('rev-parse',SOURCE+'^{commit}').decode().strip()==SOURCE,'fixed a6 exists')
   need(git('rev-parse','--show-object-format').strip()==b'sha1','original SHA1 Git identities required')
   git('merge-base','--is-ancestor',S10,SOURCE)
   need(git('diff','--name-only','-z',S10,SOURCE,'--','.',':(exclude)evidence').split(b'\0')==['決策佇列.md'.encode(),b''],'only decision changed sinceS10 outside evidence')
   raw=git('ls-tree','-r','-l','-z',SOURCE,'--',*sorted(old['files']))
   files={}
   for row in raw.split(b'\0'):
    if not row:continue
    meta,name=row.split(b'\t',1);mode,kind,oid,size=meta.split();n=os.fsdecode(name)
    need(kind==b'blob'and mode in [b'100644',b'100755'],'regular selected Git blob')
    files[n]={'mode':mode.decode(),'oid':oid.decode(),'bytes':int(size)}
   need(set(files)==set(old['files']),'all3763 old selected paths retained')
   need([n for n in sorted(files)if files[n]!=old['files'][n]]==['決策佇列.md'],'only decision selected metadata differs')
   need(H(git('show',SOURCE+':決策佇列.md'))==DECISION_PIN,'exact new decision snapshot')
   newmanifest={**old,'source_sha':SOURCE,'files':files,'blueprint_source_sha':S10,'blueprint_manifest_sha256':OLD_PIN}
   dump(OUT/'SOURCE_MANIFEST.json',newmanifest)
   pattern='/*\n'+''.join('!/'+n+'\n'for n in EXCLUDED)+''.join('/'+n+'\n'for n in old['fixture_paths'])
   (OUT/'pool-sparse-checkout.txt').write_text(pattern)
   git('clone','--shared','--no-hardlinks','--no-checkout',OWNER,ROOT)
   need(sorted(p.name for p in ROOT.iterdir())==['.git'],'clone did not materialize default source')
   need((ROOT/'.git/objects/info/alternates').read_text().splitlines()==[str(OWNER/'.git/objects')],'private alternates point only to canonical publisher')
   git('config','--local','core.autocrlf','false',cwd=ROOT);git('config','--local','core.sparseCheckout','true',cwd=ROOT);git('config','--local','core.sparseCheckoutCone','false',cwd=ROOT)
   git('config','--local','core.splitIndex','false',cwd=ROOT)
   (ROOT/'.git/info/sparse-checkout').write_text(pattern)
   git('checkout','--detach',SOURCE,cwd=ROOT)
   need(git('rev-parse','HEAD',cwd=ROOT).decode().strip()==SOURCE and not git('status','--porcelain=v1','--untracked-files=all',cwd=ROOT),'new source clean exacta6')
   materialized=set()
   for row in git('ls-files','-t','-z',cwd=ROOT).split(b'\0'):
    if row and row[:1]!=b'S':materialized.add(os.fsdecode(row[2:]))
   need(materialized==set(files),'exact original selected physical leaf set')
   observed=[]
   for n in sorted(files):
    p=ROOT/n;st=p.lstat();need(stat.S_ISREG(st.st_mode)and st.st_nlink==1,'independent source inode '+n)
    b=p.read_bytes();oid=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
    need(oid==files[n]['oid']and len(b)==files[n]['bytes'],'exact Git bytes '+n)
    observed.append({'path':n,'oid':oid,'bytes':len(b),'raw_sha256':H(b),'device':st.st_dev,'inode':st.st_ino,'nlink':st.st_nlink,'allocated_bytes':st.st_blocks*512})
   dump(OUT/'pool-materialized.json',observed)
   need(owner_index==(OWNER/'.git/index').read_bytes()and git('rev-parse','HEAD')==owner_head and git('status','--porcelain=v1','--untracked-files=all')==owner_status,'canonical writer unchanged')
   result.update(exit_code=0,materialized=True,source_files=len(observed),architecture_inputs=len(old['architecture_paths']),mandatory_fixtures=len(old['fixture_paths']),allocated_source_files=sum(x['allocated_bytes']for x in observed),source_manifest_sha256=H((OUT/'SOURCE_MANIFEST.json').read_bytes()),source_rows_sha256=H((OUT/'pool-materialized.json').read_bytes()),canonical_writer_unchanged=True)
  except BaseException as e:result.update(exit_code=1,error=repr(e));raise
  finally:dump(OUT/'RESULT.json',result)
  print(json.dumps(result,ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
