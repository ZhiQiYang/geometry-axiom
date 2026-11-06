from pathlib import Path
import fcntl,hashlib,json,os,tarfile
HERE=Path(__file__).resolve().parent;PACKAGE=Path('/tmp/geo323-node-hint-R-package-20261024')
SCOPES={
'R3-source':Path('/tmp/geo323-node-hint-R-diagnostic-r3-20261024/source'),
'R3-execution':Path('/tmp/geo323-node-hint-R-diagnostic-r3-20261024/execution'),
'R2-prepare-failure':Path('/tmp/geo323-node-hint-R-diagnostic-20261024/execution'),
'R-tools-analysis-and-R1':Path('/workspace/geo323-node-hint-R-diagnostic-20261024'),
'original-instrumentation-draft':Path('/workspace/geo323-node-hint-diagnostic-draft-20261024'),
'original-static-peer':Path('/workspace/geo323-node-hint-peer-specials-20261024')}
def sha(b):return hashlib.sha256(b).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def main():
 locks=[];result={'exit':None,'scope':'Original diagnostic capture; not product/performance acceptance','excluded':[]}
 try:
  for name in ['/tmp/g261r3/heavy.lock','/tmp/g261r3/secondary.lock']:
   f=Path(name).open('a+')
   try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f);break
   except BlockingIOError:f.close()
  need(locks,'one shared heavy slot required for archive compression')
  need(not PACKAGE.exists(),'single fresh package');PACKAGE.mkdir()
  need(os.statvfs('/tmp').f_bavail*os.statvfs('/tmp').f_frsize>16*1024*1024,'archive resource margin only')
  rows=[]
  for label,root in SCOPES.items():
   for p in sorted(root.rglob('*')):
    need(not p.is_symlink(),'do not follow diagnostic symlink')
    if not p.is_file():continue
    raw=p.read_bytes();record={'archive_path':label+'/'+p.relative_to(root).as_posix(),'local':str(p),'bytes':len(raw),'sha256':sha(raw)}
    if raw[:4]==b'\x7fELF':result['excluded'].append({**record,'reason':'ELF original retained in place; hash only'});continue
    rows.append(record)
  need(len({r['archive_path']for r in rows})==len(rows),'unique archive paths')
  index={'source_sha':'a22df116c7e9f6b7d074451f1c8052d59e7e4f3e','rows':rows,'excluded':result['excluded'],'logical_bytes':sum(r['bytes']for r in rows),'members':len(rows)}
  (PACKAGE/'RAW_INDEX.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
  archive=PACKAGE/'ORIGINAL_DIAGNOSTIC.tar.gz'
  with tarfile.open(archive,'w:gz',compresslevel=6)as tf:
   for r in rows:
    p=Path(r['local']);need(sha(p.read_bytes())==r['sha256'],'original changed before capture');tf.add(p,arcname=r['archive_path'],recursive=False)
  with tarfile.open(archive,'r:gz')as tf:
   members=tf.getmembers();need([m.name for m in members]==[r['archive_path']for r in rows],'complete exact member order')
   for m,r in zip(members,rows):need(m.isfile()and m.size==r['bytes']and sha(tf.extractfile(m).read())==r['sha256'],'archive original byte roundtrip')
  for e in result['excluded']:need(Path(e['local']).is_file()and Path(e['local']).stat().st_size==e['bytes'],'excluded ELF retained')
  result.update(exit=0,members=len(rows),logical_bytes=index['logical_bytes'],archive={'path':str(archive),'bytes':archive.stat().st_size,'sha256':sha(archive.read_bytes())},raw_index_sha256=sha((PACKAGE/'RAW_INDEX.json').read_bytes()),roundtrip_all_original_bytes=True)
 except BaseException as exc:result.update(exit=1,error=repr(exc))
 finally:
  if PACKAGE.exists():(PACKAGE/'SUMMARY.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
  for f in locks:fcntl.flock(f,fcntl.LOCK_UN);f.close()
  print(json.dumps(result),flush=True)
 return result['exit']
if __name__=='__main__':raise SystemExit(main())
