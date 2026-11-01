#!/usr/bin/env python3
from pathlib import Path, PurePosixPath
import hashlib,json,os,shutil,stat,sys,tarfile,time,traceback
M=Path('/workspace/geo337-F9-reader-and-api-publication-preparation-20261025/FILES.without-progress.json')
MPIN='2fdf0e429f0b757e613333d6224d3daee5bc4d48c1272e564bd2f0f1ebbefdcc'
O=Path('/workspace/geo337-F9-readers-and-identity-two-part-package-20261025')
PREFIX='evidence/geo337-train-20261024/F9-readers-and-verified-decision/'
F='4f8a794f4167c3562eb182045102e86e9e37cca9'
RESERVE=64*1024*1024
METADATA=1024*1024
def digest_bytes(b):return hashlib.sha256(b).hexdigest()
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
def identity(p):
 s=p.lstat()
 if not stat.S_ISREG(s.st_mode) or p.is_symlink():raise RuntimeError('nonregular source: '+str(p))
 return {'device':s.st_dev,'inode':s.st_ino,'size':s.st_size,'mode':s.st_mode,'mtime_ns':s.st_mtime_ns,'nlink':s.st_nlink}
def gz_overhead(n):
 # Upward-rounded zlib compressBound terms plus conservative gzip wrapper slack.
 return (n+4095)//4096+(n+16383)//16384+(n+33554431)//33554432+1024
def info_for(row):
 p=Path(row['source_path']);s=p.stat();info=tarfile.TarInfo(row['member'])
 info.size=row['bytes'];info.mode=s.st_mode&0o777;info.mtime=int(s.st_mtime)
 if len(info.tobuf(tarfile.PAX_FORMAT))+511>4096:raise RuntimeError('member exceeds fixed header/padding budget')
 return info
if sys.flags.optimize:raise RuntimeError('Python optimization forbidden')
if O.exists():raise RuntimeError('fresh output required')
O.mkdir()
result={'schema':'geo337-readers-api-two-part-package/2','source_sha':F,'collection_exit':None,'subject_rerun':False,'manifest_sha256':MPIN,'collector_sha256':digest(__file__),'parts':[],'started_epoch':time.time(),'errors':[]}
write(O/'RESULT.json',result)
try:
 raw=M.read_bytes()
 if digest_bytes(raw)!=MPIN:raise RuntimeError('fixed manifest drift')
 files=json.loads(raw)['files']
 if len(files)!=582 or sum(r['bytes'] for r in files)!=11063364:raise RuntimeError('fixed scope mismatch')
 if len({r['source_path'] for r in files})!=582 or len({r['destination'] for r in files})!=582:raise RuntimeError('duplicate manifest source/destination')
 inventory=[]
 for r in files:
  if not r['destination'].startswith(PREFIX):raise RuntimeError('destination outside reviewed prefix')
  name=r['destination'][len(PREFIX):];parts=PurePosixPath(name).parts
  if not name or PurePosixPath(name).is_absolute() or '..' in parts or '.git' in parts:raise RuntimeError('unsafe member')
  p=Path(r['source_path']);before=identity(p)
  if before['size']!=r['bytes'] or digest(p)!=r['sha256']:raise RuntimeError('source hash/size drift: '+str(p))
  inventory.append(dict(r,member=name,before=before))
 largest=max(inventory,key=lambda r:r['bytes'])
 if largest['source_path']!='/workspace/geo337-F9-readers-actual-urce1nqh/subcommands/000017/stdout.bin' or largest['bytes']!=9486959:raise RuntimeError('largest leaf changed')
 groups=[[largest],[r for r in inventory if r is not largest]]
 (O/'ORIGINAL_MANIFEST.json').write_bytes(raw)
 for number,group in enumerate(groups,1):
  logical=sum(r['bytes'] for r in group);tarupper=logical+4096*len(group)+10240;overhead=gz_overhead(tarupper)
  budget={'part':number,'fresh_epoch':time.time(),'fresh_workspace_free':shutil.disk_usage(O).free,'logical_original_bytes':logical,'members':len(group),'per_member_header_and_padding_bound':4096,'tar_end_alignment_bound':10240,'tar_upper_bytes':tarupper,'gzip_worst_case_overhead':overhead,'gzip_upper_bytes':tarupper+overhead,'metadata_bound_bytes':METADATA,'reserve_bytes':RESERVE,'required_bytes':tarupper+overhead+METADATA+RESERVE,'compression_ratio_assumed':False,'scope':'existing immutable evidence only; not a product or browser gate'}
  budget['admitted']=budget['fresh_workspace_free']>=budget['required_bytes'];write(O/f'PART{number}_BUDGET.json',budget)
  if not budget['admitted']:raise RuntimeError('fresh workspace budget rejected part '+str(number))
  print(json.dumps({'event':'part-budget','part':number,'free':budget['fresh_workspace_free'],'required':budget['required_bytes'],'reserve':RESERVE}),flush=True)
  archive=O/f'ORIGINAL_READERS_AND_IDENTITY_PART{number}.tar.gz'
  with tarfile.open(archive,'w:gz',compresslevel=1,format=tarfile.PAX_FORMAT) as tar:
   for r in group:
    p=Path(r['source_path'])
    if identity(p)!=r['before'] or digest(p)!=r['sha256']:raise RuntimeError('source changed before tar')
    info=info_for(r)
    with p.open('rb') as f:
     if f.fileno()<0:raise RuntimeError('invalid source fd')
     tar.addfile(info,f)
    if identity(p)!=r['before'] or digest(p)!=r['sha256']:raise RuntimeError('source changed during tar')
  if archive.stat().st_size>budget['gzip_upper_bytes']:raise RuntimeError('actual gzip exceeds budget bound')
  with tarfile.open(archive,'r:gz') as tar:
   members=tar.getmembers()
   if [m.name for m in members]!=[r['member'] for r in group]:raise RuntimeError('member list differs')
   for member,r in zip(members,group):
    if not member.isfile() or member.issym() or member.islnk() or member.size!=r['bytes']:raise RuntimeError('nonregular/size mismatch')
    f=tar.extractfile(member);h=hashlib.sha256();size=0
    if f is None:raise RuntimeError('missing extracted stream')
    with f:
     for b in iter(lambda:f.read(1024*1024),b''):h.update(b);size+=len(b)
    if size!=r['bytes'] or h.hexdigest()!=r['sha256']:raise RuntimeError('roundtrip bytes mismatch')
  part={'part':number,'archive_path':str(archive),'archive_bytes':archive.stat().st_size,'archive_sha256':digest(archive),'members':len(group),'original_logical_bytes':logical,'all_members_roundtrip':True,'fresh_free_after':shutil.disk_usage(O).free,'budget_path':str(O/f'PART{number}_BUDGET.json')}
  if part['fresh_free_after']<RESERVE:raise RuntimeError('64MiB reserve not preserved after part')
  for r in group:r['part']=number
  result['parts'].append(part);write(O/'RESULT.json',result);print(json.dumps({'event':'part-complete',**part}),flush=True)
 for r in inventory:
  p=Path(r['source_path'])
  if identity(p)!=r['before'] or digest(p)!=r['sha256']:raise RuntimeError('source changed after archive')
 if sorted(r['destination'] for r in inventory)!=sorted(r['destination'] for r in files):raise RuntimeError('scope coverage mismatch')
 write(O/'RAW_INVENTORY.json',inventory)
 metadata_bytes=sum(p.stat().st_size for p in O.iterdir() if p.is_file() and not p.name.endswith('.tar.gz'))
 if metadata_bytes+16384>METADATA:raise RuntimeError('actual metadata exceeds reserved budget')
 result.update(collection_exit=0,members=582,original_logical_bytes=11063364,part_member_counts=[1,581],all_manifest_members_exact_once=True,all_source_before_after_identity_and_hash_unchanged=True,full_user_profile_not_in_fixed_manifest=True,reader_original_exits=[0,0,0],reader_unit_count=51,native_exit_unchanged=1,old_R8_exit_unchanged=1,metadata_bytes_before_final_result=metadata_bytes,final_free=shutil.disk_usage(O).free)
except BaseException:
 result['collection_exit']=1;result['errors'].append(traceback.format_exc());traceback.print_exc()
finally:
 result['ended_epoch']=time.time();write(O/'RESULT.json',result);print(json.dumps(result,ensure_ascii=False),flush=True)
sys.exit(result['collection_exit'])
