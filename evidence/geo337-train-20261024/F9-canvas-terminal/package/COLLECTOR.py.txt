#!/usr/bin/env python3
from pathlib import Path,PurePosixPath
import argparse,json,hashlib,os,stat,sys,shutil,tarfile,time,traceback
PREP=Path('/workspace/geo337-F9-canvas-terminal-preparation-20261025')
IPIN='9608b89734fa688bfd9c40c5b0377a6e80cb117caaf389336f11cef27415986d'
PPIN='aca3014a5cfb4dab89d128dc4cbe2bf654724a5f94df3a228dae6b51d143de60'
F='4f8a794f4167c3562eb182045102e86e9e37cca9';RESERVE=64*1024*1024;META=2*1024*1024
def sha(b):return hashlib.sha256(b).hexdigest()
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def J(p):return json.loads(Path(p).read_bytes())
def state(p):
 s=p.lstat();return {'device':s.st_dev,'inode':s.st_ino,'mode':s.st_mode,'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'nlink':s.st_nlink}
def write(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
def verify(row):
 p=Path(row['source_path'])
 if state(p)!=row['state']:raise RuntimeError('source stat changed: '+str(p))
 if row['type']=='regular':
  if not stat.S_ISREG(p.lstat().st_mode) or digest(p)!=row['sha256']:raise RuntimeError('regular source hash changed')
 elif row['type']=='symlink':
  target=os.readlink(p)
  if target!=row['target'] or sha(os.fsencode(target))!=row['sha256']:raise RuntimeError('symlink identity changed')
 else:raise RuntimeError('unknown inventory type')
def overhead(n):return (n+4095)//4096+(n+16383)//16384+(n+33554431)//33554432+1024
p=argparse.ArgumentParser();p.add_argument('--request',type=Path);p.add_argument('--execute',action='store_true');a=p.parse_args()
if not a.execute:
 print(json.dumps({'state':'PREPARATION_ONLY','source_sha':F,'inventory_sha256':IPIN,'parts_sha256':PPIN,'archive_created':False,'requires':'root true execution lease, exact tool/inventory/parts/peer bindings and fresh per-part64MiB reserve'}));raise SystemExit(0)
if sys.flags.optimize or a.request is None:raise RuntimeError('nonoptimized explicit request required')
request=J(a.request)
if request.get('source_sha')!=F or request.get('root_execution_lease') is not True or request.get('execute') is not True:raise RuntimeError('root bound execution lease required')
toolpin=digest(__file__)
if request.get('collector_sha256')!=toolpin or request.get('inventory_sha256')!=IPIN or request.get('parts_sha256')!=PPIN:raise RuntimeError('exact collector/input binding required')
peerpath=Path(request['independent_peer']['path']);peerraw=peerpath.read_bytes();peer=json.loads(peerraw)
if sha(peerraw)!=request['independent_peer']['sha256'] or type(peer.get('exit_code')) is not int or peer['exit_code']!=0 or peer.get('collector_sha256')!=toolpin or peer.get('inventory_sha256')!=IPIN or peer.get('parts_sha256')!=PPIN:raise RuntimeError('exact accepted independent static peer required')
if digest(PREP/'INVENTORY.json')!=IPIN or digest(PREP/'PARTS.json')!=PPIN or J(PREP/'RESULT.json')['inventory_exit']!=0:raise RuntimeError('frozen inventory changed')
inv=J(PREP/'INVENTORY.json');parts=J(PREP/'PARTS.json');rows=inv['records'];index={r['member']:r for r in rows}
if len(index)!=len(rows) or inv['source_sha']!=F:raise RuntimeError('duplicate or wrong-source inventory')
flatten=[n for part in parts for n in part['members_exact']]
if len(flatten)!=len(set(flatten)) or set(flatten)!=set(index) or len(parts)!=4:raise RuntimeError('exact once four-part scope required')
for name in index:
 if PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts:raise RuntimeError('unsafe member path')
out=Path(request['out'])
if not out.is_absolute() or out.parent not in (Path('/workspace'),Path('/tmp')) or not out.name.startswith('geo337-F9-canvas-terminal-package-') or out.exists():raise RuntimeError('fresh direct OWN workspace or tmp output required')
out.mkdir();(out/'BOUND_REQUEST.json').write_bytes(a.request.read_bytes());(out/'COLLECTOR.py.txt').write_bytes(Path(__file__).read_bytes())
result={'schema':'geo337-F9-canvas-terminal-complete-package/1','source_sha':F,'collection_exit':None,'collector_sha256':toolpin,'inventory_sha256':IPIN,'parts_sha256':PPIN,'peer_sha256':sha(peerraw),'started_epoch':time.time(),'parts':[],'errors':[],'subject_rerun':False,'no_source_seed_git_object_payload_copied':True,'no_regular_launch_storage_payload_excluded':True}
write(out/'RESULT.json',result)
try:
 # Input/metadata copies are bounded by the declared 2MiB metadata reserve, not payload duplicates.
 for name in ['INVENTORY.json','PARTS.json','RESULT.json']:(out/('ORIGINAL_'+name)).write_bytes((PREP/name).read_bytes())
 for row in rows:verify(row)
 for row in inv['hash_only_excluded_sourceplan']:
  p=Path(row['source_path'])
  if state(p)!=row['state'] or digest(p)!=row['sha256']:raise RuntimeError('excluded sourceplan metadata identity changed')
 for row in inv['nonregular_metadata_only']:
  if state(Path(row['source_path']))!=row['state']:raise RuntimeError('nonregular node metadata changed')
 for part in parts:
  names=part['members_exact'];logical=sum(index[n]['bytes'] for n in names if index[n]['type']=='regular');n=logical+4096*len(names)+10240
  required=n+overhead(n)+META+RESERVE
  if required!=part['required_fresh_bytes'] or part['reserve_bytes']!=RESERVE or part['metadata_bytes']!=META:raise RuntimeError('fixed budget formula mismatch')
  budget=dict(part);budget.pop('members_exact');budget.update(fresh_epoch=time.time(),fresh_output_free=shutil.disk_usage(out).free,required_bytes=required,compression_ratio_assumed=False)
  budget['admitted']=budget['fresh_output_free']>=required;write(out/f'PART{part["part"]}_BUDGET.json',budget)
  if not budget['admitted']:raise RuntimeError('fresh space insufficient for part '+str(part['part']))
  print(json.dumps({'event':'part-budget','part':part['part'],'free':budget['fresh_output_free'],'required':required}),flush=True)
  archive=out/f'ORIGINAL_CANVAS_PART{part["part"]}.tar.gz'
  with tarfile.open(archive,'w:gz',compresslevel=1,format=tarfile.PAX_FORMAT) as tar:
   for name in names:
    row=index[name];verify(row);p=Path(row['source_path']);info=tarfile.TarInfo(name);info.mode=row['state']['mode']&0o777;info.mtime=row['state']['mtime_ns']//1000000000
    if row['type']=='symlink':info.type=tarfile.SYMTYPE;info.linkname=row['target'];info.size=0
    else:info.size=row['bytes']
    if len(info.tobuf(tarfile.PAX_FORMAT))+511>4096:raise RuntimeError('member header exceeds fixed bound')
    if row['type']=='regular':
     with p.open('rb') as f:tar.addfile(info,f)
    else:tar.addfile(info)
    verify(row)
  if archive.stat().st_size>part['gzip_upper_bytes']:raise RuntimeError('actual gzip exceeds conservative bound')
  with tarfile.open(archive,'r:gz') as tar:
   members=tar.getmembers()
   if [m.name for m in members]!=names:raise RuntimeError('tar member scope differs')
   for m in members:
    row=index[m.name]
    if row['type']=='symlink':
     if not m.issym() or m.linkname!=row['target']:raise RuntimeError('symlink roundtrip mismatch')
    else:
     if not m.isfile() or m.issym() or m.islnk() or m.size!=row['bytes']:raise RuntimeError('regular tar metadata mismatch')
     f=tar.extractfile(m);hh=hashlib.sha256();size=0
     if f is None:raise RuntimeError('missing tar stream')
     with f:
      for b in iter(lambda:f.read(1024*1024),b''):hh.update(b);size+=len(b)
     if hh.hexdigest()!=row['sha256'] or size!=row['bytes']:raise RuntimeError('tar roundtrip hash mismatch')
  free=shutil.disk_usage(out).free
  if free<RESERVE:raise RuntimeError('64MiB reserve not preserved after archive')
  row={'part':part['part'],'archive_path':str(archive),'archive_sha256':digest(archive),'archive_bytes':archive.stat().st_size,'members':len(names),'logical_regular_bytes':logical,'roundtrip_complete':True,'fresh_free_after':free};result['parts'].append(row);write(out/'RESULT.json',result);print(json.dumps({'event':'part-complete',**row}),flush=True)
 for row in rows:verify(row)
 metadata=sum(p.stat().st_size for p in out.iterdir() if p.is_file() and not p.name.endswith('.tar.gz'))
 if metadata+16384>META:raise RuntimeError('actual metadata exceeds2MiB reserve')
 result.update(collection_exit=0,regular_files=sum(r['type']=='regular' for r in rows),symlinks=sum(r['type']=='symlink' for r in rows),regular_bytes=sum(r['bytes'] for r in rows if r['type']=='regular'),all_selected_sources_unchanged=True,all_members_exact_once=True,all_roundtrip_complete=True,excluded_sourceplan_metadata_files=len(inv['hash_only_excluded_sourceplan']),nonregular_metadata_nodes=len(inv['nonregular_metadata_only']),original_formal_exit=0,original_35minute_gate_exit=0,final_free=shutil.disk_usage(out).free)
except BaseException:result['collection_exit']=1;result['errors'].append(traceback.format_exc());traceback.print_exc()
finally:result['ended_epoch']=time.time();write(out/'RESULT.json',result);print(json.dumps(result,ensure_ascii=False),flush=True)
sys.exit(result['collection_exit'])
