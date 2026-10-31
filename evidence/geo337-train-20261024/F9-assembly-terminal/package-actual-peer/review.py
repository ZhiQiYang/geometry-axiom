from pathlib import Path, PurePosixPath
import hashlib,json,tarfile,stat,os,datetime

B=Path('/dev/shm/geometry-axiom-geo337-20261025')
P=B/'assembly-terminal-package-20261025'
C=B/'assembly-terminal-collection-original-20261025'
O=Path('/workspace/geo337-assembly-terminal-package-actual-peer-20261025')
F='4f8a794f4167c3562eb182045102e86e9e37cca9'
count=0
def ck(name,v):
 global count
 count+=1
 if not v:raise AssertionError(name)
def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def J(p):return json.loads(Path(p).read_bytes())
def state(p):
 s=p.lstat()
 return dict(device=s.st_dev,inode=s.st_ino,mode=s.st_mode,bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,nlink=s.st_nlink)
def source_check(r):
 p=Path(r['source_path']);ck('source state '+r['member'],state(p)==r['state'])
 if r['type']=='regular':ck('source hash '+r['member'],digest(p)==r['sha256'])
 else:ck('source link '+r['member'],os.readlink(p)==r['target'] and hashlib.sha256(os.fsencode(r['target'])).hexdigest()==r['sha256'])

result=J(P/'RESULT.json');inv=J(P/'INVENTORY.json');parts=J(P/'PARTS.json');outer=J(C/'RESULT.json')
hostpath=Path('/workspace/geo337-F9-assembly-terminal-collection-EXEC_FINAL-20261025.json');host=J(hostpath)
ck('package known pin',digest(P/'RESULT.json')=='58d68eb5f3af3b1011a0f3e4fd20dceed10edb0ca857d87b8a8b0af41b05b49f')
ck('real terminal zero',host['actual_tool_result']['exit_code']==outer['exit_code']==result['collection_exit']==0)
ck('host stdout exact outer',json.loads(host['actual_tool_result']['output'])==outer)
ck('package binding',outer['package_result_sha256']==digest(P/'RESULT.json'))
ck('original source identities',result['source_sha']==outer['source_sha']==inv['source_sha']==F)
ck('original1/0 preserved',[a['original_formal_exit']for a in result['attempts']]==[1,0])
ck('original15min gates preserved',all(a['original_15minute_gate_exit']==0 and a['original_elapsed_seconds']<900 for a in result['attempts']))
ck('collection not formal or delivered',result['subject_rerun'] is False and result['delivered'] is False and result['product_acceptance_rejudged'] is False)
ck('inventory exact binding',digest(P/'INVENTORY.json')==result['inventory_sha256'])
ck('parts exact binding',digest(P/'PARTS.json')==result['parts_sha256'])
records=inv['records'];excluded=inv['hash_only_excluded_sourceplan'];sockets=inv['nonregular_metadata_only'];idx={r['member']:r for r in records}
ck('833 unique members',len(records)==len(idx)==833)
ck('regular/symlink counts',sum(r['type']=='regular'for r in records)==result['regular_files']==828 and sum(r['type']=='symlink'for r in records)==result['symlinks']==5)
ck('bytes full',sum(r['bytes']for r in records if r['type']=='regular')==result['regular_bytes']==35366094)
ck('explicit5exclusion1socket',len(excluded)==5 and len(sockets)==1)
for r in records+excluded:
 ck('safe member',not PurePosixPath(r['member']).is_absolute() and '..' not in PurePosixPath(r['member']).parts)
 source_check(r)
for r in excluded:ck('only gitdir or latest exclusion',r['member'].startswith('sourceplan/layout/jobs/assembly/gitdir/') or r['member']=='sourceplan/layout/GUARD_LATEST.json')
for r in sockets:ck('socket original retained',state(Path(r['source_path']))==r['state'] and stat.S_ISSOCK(r['state']['mode']))
seen=[]
for plan,actual in zip(parts,result['parts']):
 archive=Path(actual['archive_path']);ck('archive pin/size',digest(archive)==actual['archive_sha256'] and archive.stat().st_size==actual['archive_bytes'])
 ck('plan index',plan['part']==actual['part'])
 budget=J(P/f"PART{plan['part']}_BUDGET.json")
 n=plan['logical_regular_bytes']+4096*len(plan['members_exact'])+10240
 bound=n+(n+4095)//4096+(n+16383)//16384+(n+33554431)//33554432+1024
 ck('conservative64MiB budget',plan['tar_upper_bytes']==n and plan['gzip_upper_bytes']==bound and plan['required_fresh_bytes']==bound+2*1024**2+64*1024**2)
 ck('admitted from fresh actual',budget['fresh_output_free']>=plan['required_fresh_bytes'] and budget['admitted'] is True and budget['compression_ratio_assumed'] is False)
 ck('original actual archive within bound',actual['archive_bytes']<=bound and actual['fresh_free_after']>=64*1024**2)
 with tarfile.open(archive,'r:gz')as t:
  members=t.getmembers();ck('member exact order',[m.name for m in members]==plan['members_exact']);ck('member count',len(members)==actual['members'])
  for m in members:
   r=idx[m.name];seen.append(m.name)
   ck('mode',m.mode==r['state']['mode']&0o777);ck('mtime',m.mtime==r['state']['mtime_ns']//1000000000)
   if r['type']=='symlink':ck('tar symbolic link',m.issym() and m.linkname==r['target'] and m.size==0)
   else:
    ck('tar regular type/size',m.isfile() and not m.islnk() and m.size==r['bytes'])
    h=hashlib.sha256();length=0
    with t.extractfile(m)as stream:
     for chunk in iter(lambda:stream.read(1024**2),b''):h.update(chunk);length+=len(chunk)
    ck('tar complete bytes',h.hexdigest()==r['sha256'] and length==r['bytes'])
ck('exact once allmembers',len(seen)==len(set(seen))==len(records) and set(seen)==set(idx))
ck('3 parts',len(parts)==len(result['parts'])==3)
# Verify original file-set coverage without opening any other job or the shared source seed.
prefixes={
 'attempts/assembly/launch':'/dev/shm/geo337-F9-browsers-20261025/launches/assembly',
 'attempts/assembly/storage':'/dev/shm/geo337-F9-browsers-20261025/runs/assembly',
 'attempts/assembly/sampler':'/dev/shm/geo337-F9-browsers-20261025/sampled/assembly',
 'attempts/assembly-r2/launch':'/dev/shm/geo337-F9-browsers-20261025/launches/assembly-r2',
 'attempts/assembly-r2/storage':'/dev/shm/geo337-F9-browsers-20261025/r/a2',
 'attempts/assembly-r2/sampler':'/dev/shm/geo337-F9-browsers-20261025/sampled/assembly-r2',
 'sourceplan':'/dev/shm/geo337-F9-browsers-20261025/plans/assembly',
 'source-materialization':'/dev/shm/geo337-F9-browsers-20261025/host/assembly-materialize',
 'source-plan-generation':'/dev/shm/geo337-F9-browsers-20261025/host/assembly-plan',
 'prior-actual-peer/first-attempt':'/workspace/geo337-F9-assembly-first-SHM-actual-peer-20261025',
 'prior-actual-peer/materialization':'/workspace/geo337-F9-assembly-SHM-materialize-actual-peer-20261025',
}
allrows=records+excluded+sockets
for prefix,rpath in prefixes.items():
 root=Path(rpath);observed=set()
 for parent,dirs,files in os.walk(root,followlinks=False):
  for name in dirs+files:
   p=Path(parent)/name
   if not stat.S_ISDIR(p.lstat().st_mode):observed.add(prefix+'/'+p.relative_to(root).as_posix())
 expected={r['member']for r in allrows if r['member'].startswith(prefix+'/')}
 ck('whole original scope '+prefix,observed==expected)
for r in records+excluded:ck('post review state unchanged',state(Path(r['source_path']))==r['state'])
rows=outer['commands'];ck('one original collector command',len(rows)==1)
for row in rows:
 d=Path(row['directory']);ck('capture SHA/source/exit',row['actual_process_returncode']==0 and row['timeout_expired'] is False and row['source_sha']==F)
 for stream in ['stdout','stderr']:
  p=d/(stream+'.bin');ck('capture '+stream,p.stat().st_size==row[stream+'_bytes'] and digest(p)==row[stream+'_sha256'])
 ck('captured full terminal stdout',json.loads((d/'stdout.bin').read_text().splitlines()[-1])==result)
 ck('capture exact request',digest(C/'ROOT_REQUEST.json')==row['command'][row['command'].index('--request-sha256')+1])
ck('launcher exact retained',digest(C/'LAUNCHER.py.txt')=='8a1a504f39010d5afa34c2c801ccf967283ba469b6951e8c508a529bcb7c3646')
ck('collector exact retained',digest(P/'COLLECTOR.py.txt')=='ff1aae84cd00a73190f3d8e7c3623087d9965804ae6821d872487a2b42b01049')
# Tiny immutable metadata copies only; original archives and full raw remain in SHM.
copies={}
for src,name in [(P/'RESULT.json','PACKAGE_RESULT.json'),(P/'INVENTORY.json','INVENTORY.json'),(P/'PARTS.json','PARTS.json'),(C/'RESULT.json','OUTER_RESULT.json'),(C/'ROOT_REQUEST.json','ROOT_REQUEST.json'),(hostpath,'EXEC_FINAL.json')]:
 data=src.read_bytes();dst=O/name;dst.write_bytes(data);copies[name]={'source':str(src),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
review={'schema':'F9-assembly-two-attempt-terminal-package-actual-peer/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':0,'checks':count,'source_sha':F,'package_result_sha256':digest(P/'RESULT.json'),'inventory_sha256':digest(P/'INVENTORY.json'),'outer_result_sha256':digest(C/'RESULT.json'),'host_final_sha256':digest(hostpath),'original_formal_exits':[1,0],'original15minute_gate_exits':[0,0],'regular_files':828,'symlinks':5,'logical_regular_bytes':35366094,'archive_bytes':sum(p['archive_bytes']for p in result['parts']),'archive_parts':result['parts'],'blocking_findings':[],'metadata_copies':copies,'limits':['Formal require_escalated read only of completed assembly originals/package; no test rerun, Git mutation, SHM writes or active grid payload access.','Package complete bytes/type/mode/mtime/linktarget and source states verified. Original first environment exit1 retained; original second exit0 not rejudged as a new product sample.','Five sourceplan Gitdir/latest files are hash-only; one Unix socket metadata-only. Seeds/source payload and Git objects excluded and retained.','r2 accepted original assertion peer belongs as a separate publication leaf; this review does not replace its150-assertion validation.','SHM remains volatile; publication and remote full blob delivery are subsequent separate actions.']}
q=O/'REVIEW.json';q.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'exit_code':0,'checks':count,'review_path':str(q),'sha256':digest(q),'metadata_copy_bytes':sum(x['bytes']for x in copies.values())}))
