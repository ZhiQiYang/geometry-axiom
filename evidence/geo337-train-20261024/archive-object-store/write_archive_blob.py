"""Write only a future archive blob to a protected TMP Git store; never adopt it into refs/index."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,stat,sys,datetime,zlib
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
CAP_PIN='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
SAFE_CALLER_GIT_ENV={'GIT_OPTIONAL_LOCKS':'0'}
def need(ok,msg):
 if not ok:raise RuntimeError(msg)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def fsync_dir(p):
 fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
def durable(p,b):
 with Path(p).open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 fsync_dir(Path(p).parent)
def canonical(p,exists=True):
 p=Path(p);need(p.is_absolute() and p.resolve(strict=exists)==p,'absolute nonsymlink path required: '+str(p))
 for q in p.parents:need(not q.is_symlink(),'symlink parent rejected')
 return p
def record(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def file_identity(p):
 if not p.exists():return {'exists':False}
 need(p.is_file() and not p.is_symlink(),'regular metadata required');s=p.stat()
 return dict(exists=True,bytes=s.st_size,sha256=sha(p),device=s.st_dev,inode=s.st_ino,mode=s.st_mode,mtime_ns=s.st_mtime_ns)
def alt_data(p):
 need(not p.is_symlink(),'alternate symlink rejected')
 return p.read_bytes() if p.exists() else None
def alt_paths(objects):
 p=objects/'info/alternates';b=alt_data(p)
 if b is None:return []
 rows=[]
 for line in b.splitlines():
  if not line:continue
  need(not line.startswith(b'"') and b'\0' not in line,'quoted/NUL alternate requires separate handling')
  q=Path(os.fsdecode(line));q=q if q.is_absolute() else objects/q;rows.append(q.resolve(strict=True))
 return rows
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True,type=Path);ap.add_argument('--archive',required=True,type=Path);ap.add_argument('--store',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);ap.add_argument('--expected-head',required=True);ap.add_argument('--archive-source-sha',required=True);ap.add_argument('--expected-common-dir',required=True,type=Path);ap.add_argument('--expected-alternates',required=True,help='absent or SHA256 of exact original bytes');ap.add_argument('--expected-archive-sha256',required=True);ap.add_argument('--expected-archive-bytes',required=True,type=int);ap.add_argument('--expected-store-lease-sha256');ap.add_argument('--reader',action='append',default=[],type=Path);a=ap.parse_args()
 env_before=dict(os.environ);unsafe_git_keys=sorted(k for k,v in env_before.items() if k.startswith('GIT_') and SAFE_CALLER_GIT_ENV.get(k)!=v);need(not unsafe_git_keys,'Caller Git environment keys are not allowed: '+','.join(unsafe_git_keys));repo=canonical(a.repo);archive=canonical(a.archive);store=canonical(a.store,exists=False);out=canonical(a.out,exists=False);canonical(out.parent);canonical(store.parent);need(store.is_relative_to('/tmp') and not out.exists(),'new output and TMP-only private store required');need(not store.is_relative_to(repo) and not out.is_relative_to(repo) and not archive.is_relative_to(store),'independent locations required');out.mkdir();need(sha(CAP)==CAP_PIN,'original recorder changed')
 sp=importlib.util.spec_from_file_location('capture',CAP);c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c);env=dict(env_before,GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1');rec=c.Recorder(out/'commands',env,a.expected_head)
 result=dict(exit_code=1,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),archive_source_sha=a.archive_source_sha,expected_root_head=a.expected_head,product_tests_run=False,environment_scope='GIT_OBJECT_DIRECTORY only in one env->git hash-object child',original_objects_moved_or_deleted=False,refs_or_index_adopted=False,alternate_connected=False,store=str(store));lock=None;lock_inode=None;phase='preflight'
 def cmd(argv,cwd=repo,check=True):return rec.run(argv,cwd=cwd,timeout=None,check=check,source_variant='storage-only; no product gate')
 def git(args,cwd=repo,check=True):return cmd(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args],cwd,check)
 def value(args,cwd=repo):return git(args,cwd)[1].decode().strip()
 def gitpath(name,cwd=repo):
  q=Path(value(['rev-parse','--git-path',name],cwd));return canonical(q if q.is_absolute() else cwd/q)
 def snapshot():
  head=value(['rev-parse','--verify','HEAD']);refs=git(['for-each-ref','--format=%(refname)%00%(objectname)'])[1]
  return dict(head=head,refs_bytes=len(refs),refs_sha256=hashlib.sha256(refs).hexdigest(),index=file_identity(gitpath('index')),head_file=file_identity(gitpath('HEAD')))
 try:
  need(archive.is_file() and archive.name.endswith(('.tar.gz','.tar.xz','.zip')),'exact archive file required');archive_before=file_identity(archive);need(archive_before['bytes']==a.expected_archive_bytes and archive_before['sha256']==a.expected_archive_sha256,'archive bytes/hash mismatch')
  common=Path(value(['rev-parse','--git-common-dir']));common=canonical(common if common.is_absolute() else repo/common);need(common==canonical(a.expected_common_dir),'common Git dir mismatch');objects=gitpath('objects');need(not store.is_relative_to(objects) and not objects.is_relative_to(store),'store must be separate from original objects');alternate=objects/'info/alternates';canonical(alternate.parent);old=alt_data(alternate);old_id='absent' if old is None else hashlib.sha256(old).hexdigest();need(old_id==a.expected_alternates,'exact prior alternates mismatch');durable(out/'alternates.before.bin',old or b'');before=snapshot();need(before['head']==a.expected_head,'expected HEAD mismatch');fmt=value(['rev-parse','--show-object-format']);need(fmt in ('sha1','sha256'),'unsupported Git object format');header=b'blob '+str(a.expected_archive_bytes).encode()+b'\0';oid_hash=hashlib.new(fmt);oid_hash.update(header)
  with archive.open('rb') as f:
   for b in iter(lambda:f.read(1024*1024),b''):oid_hash.update(b)
  oid=oid_hash.hexdigest();result.update(object_oid=oid,object_format=fmt,original_objects=str(objects),common_dir=str(common),before=before,prior_alternates_identity=old_id,archive_identity=archive_before)
  readers=[repo]+[canonical(x) for x in a.reader];reader_objects={str(p):gitpath('objects',p) for p in readers};graphs={}
  for reader,start in reader_objects.items():
   seen_paths=[]
   def walk(node,stack):
    need(node not in stack,'alternate cycle detected');depth=len(stack);need(depth<=5,'planned alternate nesting exceeds5');seen_paths.append(dict(path=str(node),depth=depth))
    children=alt_paths(node) if node.exists() else []
    if node==objects and store not in children:children.append(store)
    for child in children:walk(child,stack+[node])
   walk(start,[]);graphs[reader]=seen_paths
  result['planned_reader_graphs']=graphs
  existing=git(['cat-file','-e',oid],check=False)[0]
  if existing['actual_process_returncode']==0:
   phase='preexisting-readers'
   for reader in readers:
    need(value(['cat-file','-t',oid],reader)=='blob' and value(['cat-file','-s',oid],reader)==str(a.expected_archive_bytes),'existing ordinary reader cannot resolve blob')
   need(snapshot()==before and file_identity(archive)==archive_before and alt_data(alternate)==old,'read-only invariants changed');result.update(exit_code=0,status='already-present; no store or alternate changes',ordinary_readers=[str(p) for p in readers]);return 0
  need(existing['actual_process_returncode']==1,'unexpected missing-object result')
  lease=store/'info/CODEX_PERMANENT_OBJECTS.json'
  if store.exists():
   canonical(store);need(lease.exists() and a.expected_store_lease_sha256==sha(lease),'existing store requires exact permanent lease pin');lease_data=json.loads(lease.read_text());need(lease_data['store']==str(store) and lease_data['original_objects']==str(objects) and lease_data['object_format']==fmt and lease_data['do_not_delete_git_objects'] is True,'store lease identity mismatch');need(not alt_paths(store),'new store must not persist reverse alternates')
  else:
   need(a.expected_store_lease_sha256 is None,'unexpected lease for new store');store.mkdir(mode=0o700);(store/'info').mkdir(mode=0o700);(store/'pack').mkdir(mode=0o700);fsync_dir(store.parent);lease_data=dict(store=str(store),original_objects=str(objects),object_format=fmt,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),do_not_delete_git_objects=True,not_a_rebuildable_cache=True,all_future_objects_protected=True,first_receipt=str(out),cleanup_rule='Never clean/prune/delete this TMP store. Once refs/index reference any object, preserve reachable store until copy-only durable migration and full affected closure verification.');durable(lease,(json.dumps(lease_data,ensure_ascii=False,indent=2)+'\n').encode());fsync_dir(store)
  result['permanent_lease']=dict(path=str(lease),sha256=sha(lease));phase='new-object-write'
  write_command=['env','GIT_OBJECT_DIRECTORY=' + str(store),'git','-c','gc.auto=0','-c','maintenance.auto=false','hash-object','-w','--no-filters','--',str(archive)]
  need(cmd(write_command)[1].decode().strip()==oid,'written OID mismatch');loose=store/oid[:2]/oid[2:];canonical(loose);need(loose.is_file(),'new object must be in private store');de=zlib.decompressobj();got=hashlib.new(fmt);payload_hash=hashlib.sha256();headbuf=b'';payload_count=0;header_done=False
  with loose.open('rb') as f:
   for raw in iter(lambda:f.read(1024*1024),b''):
    b=de.decompress(raw);got.update(b)
    if not header_done:
     headbuf+=b
     if b'\0' not in headbuf:continue
     actual_head,b=headbuf.split(b'\0',1);need(actual_head+b'\0'==header,'loose object header mismatch');header_done=True;headbuf=b''
    payload_hash.update(b);payload_count+=len(b)
  need(de.eof and not de.unused_data and header_done and got.hexdigest()==oid and payload_count==a.expected_archive_bytes and payload_hash.hexdigest()==a.expected_archive_sha256,'private loose object full-byte verification failed')
  fd=os.open(loose,os.O_RDONLY)
  try:os.fsync(fd)
  finally:os.close(fd)
  fsync_dir(loose.parent);fsync_dir(store);need(file_identity(archive)==archive_before,'original archive changed');need(snapshot()==before,'HEAD/refs/index changed before alternate append');need(alt_data(alternate)==old,'concurrent alternate change');phase='alternate-append'
  connected=store in alt_paths(objects)
  if not connected:
   lock=alternate.with_name('alternates.lock');fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,stat.S_IMODE(alternate.stat().st_mode) if alternate.exists() else 0o600);lock_inode=os.fstat(fd).st_ino
   try:
    need(alt_data(alternate)==old,'alternate changed before locked append');store_bytes=os.fsencode(str(store));need(not any(x in store_bytes for x in (b'\n',b'\r',b'\0',b':',b'"')),'unsupported object-store path encoding');new=(old or b'')+(b'\n' if old and not old.endswith(b'\n') else b'')+store_bytes+b'\n';need(os.write(fd,new)==len(new),'short alternate lock write');os.fsync(fd)
   finally:os.close(fd)
   durable(out/'alternates.appended.bin',new);need(alt_data(alternate)==old,'alternate changed before atomic replacement')
   os.replace(lock, alternate)
   fsync_dir(alternate.parent)
  need(alt_data(alternate)==(old if connected else new),'alternate bytes differ from exact append');need(store in alt_paths(objects),'store alternate missing');result['alternate_connected']=True;phase='ordinary-readers'
  for reader in readers:
   need(value(['cat-file','-t',oid],reader)=='blob' and value(['cat-file','-s',oid],reader)==str(a.expected_archive_bytes),'ordinary reader cannot resolve new blob')
  need(snapshot()==before and file_identity(archive)==archive_before,'HEAD/refs/index/archive changed');need(alt_data(alternate)==(old if connected else new),'alternate changed after reader checks');need(dict(os.environ)==env_before,'process environment polluted');result.update(exit_code=0,status='new protected blob readable; refs/index untouched',ordinary_readers=[str(p) for p in readers],new_object_identity=file_identity(loose),final_alternates_sha256=sha(alternate),after=before)
  return 0
 except BaseException as e:
  result.update(error=repr(e),failed_phase=phase);return 1
 finally:
  if lock is not None and lock.exists() and lock.lstat().st_ino==lock_inode:
   durable(out/'owned-uncommitted-alternates-lock.bin',lock.read_bytes());lock.unlink();fsync_dir(lock.parent);result['only_own_new_metadata_lock_removed']=True
  result.update(ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),global_git_environment_unchanged=dict(os.environ)==env_before);record(out/'RESULT.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':sys.exit(main())
