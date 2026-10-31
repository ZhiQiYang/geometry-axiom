from pathlib import Path
import fcntl,hashlib,json,os,shutil,sys,tarfile,time
H=Path(__file__).resolve().parent;OUT=H/'package';LOCK=Path('/tmp/g261r3/secondary.lock')
def need(v,m):
 if not v:raise RuntimeError(m)
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
 plan=json.loads((H/'PACKAGE_PLAN.json').read_bytes());need(not OUT.exists(),'single fresh archive only');need(shutil.disk_usage(H).free>=100*1024*1024,'100MiB actual TMP filesystem guard')
 lock=LOCK.open('a+b');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);OUT.mkdir();r={'source_sha':plan['source_sha'],'exit':None,'originals_deleted':False,'product_tests_reexecuted':False,'archive_count':1,'started_epoch':time.time(),'lock':str(LOCK)}
 try:
  rows=[];seen=set()
  for item in plan['files']:
   n=item['archive'];p=Path(item['local']);need(n not in seen and not n.startswith('/')and '..'not in Path(n).parts,'exact safe unique member');seen.add(n);need(p.is_file()and not p.is_symlink(),'original regular file');b=p.read_bytes();need(len(b)==item['bytes'],'frozen metadata size changed');rows.append({**item,'sha256':sha(b)})
  archive=OUT/'ORIGINAL_PROVIDER_HINT_EVIDENCE.tar.gz'
  with tarfile.open(archive,'w:gz',compresslevel=6)as tar:
   for row in rows:tar.add(row['local'],arcname=row['archive'],recursive=False)
  with tarfile.open(archive,'r:gz')as tar:
   members=tar.getmembers();need(len(members)==len(rows),'exact archive count');need([m.name for m in members]==[x['archive']for x in rows],'archive order and names')
   for m,row in zip(members,rows):
    need(m.isfile(),'regular archive member');raw=tar.extractfile(m).read();need(len(raw)==row['bytes']and sha(raw)==row['sha256'],'roundtrip bytes/hash');need(Path(row['local']).read_bytes()==raw,'original bytes unchanged through collect')
  digest=hashlib.sha256()
  with archive.open('rb')as f:
   for block in iter(lambda:f.read(1024*1024),b''):digest.update(block)
  index={'source_sha':plan['source_sha'],'files':rows,'count':len(rows),'logical_bytes':sum(x['bytes']for x in rows)};dump(OUT/'RAW_INDEX.json',index)
  r.update(exit=0,archive={'path':str(archive),'bytes':archive.stat().st_size,'sha256':digest.hexdigest(),'members':len(rows)},logical_bytes=index['logical_bytes'],roundtrip=True,original_bytes_unchanged=True)
 except BaseException as e:r.update(exit=1,error=repr(e));raise
 finally:
  r['ended_epoch']=time.time();dump(OUT/'SUMMARY.json',r);fcntl.flock(lock,fcntl.LOCK_UN);lock.close();print(json.dumps({k:r.get(k)for k in ['exit','archive','error']}),flush=True)
 return r['exit']
if __name__=='__main__':sys.exit(main())
