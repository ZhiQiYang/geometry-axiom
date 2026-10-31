"""Collect closed #314 v2 failure and v3 focused proof; no current NATIVE access."""
from pathlib import Path, PurePosixPath
import argparse, hashlib, json, os, shutil, stat, sys, tarfile, time, traceback

F = '4f8a794f4167c3562eb182045102e86e9e37cca9'
SHM = Path('/dev/shm/geometry-axiom-geo337-20261025')
POLICY = '9b2945ff5c6214d985cdb0a623c18721bfec3948bd9ea9e4e443a8b3f5c22f6a'
TARGET = 16 * 1024**2
RESERVE = 64 * 1024**2
META = 8 * 1024**2  # Preserve the accepted collector metadata allowance.
CAP = Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
CAP_PIN = 'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
PREP = Path('/workspace/geo314-counterproof-terminal-preparation-20261025')
CONFIG = PREP/'SCOPE.json'
CONFIG_PIN = 'f32dc1cfd20a24f85dce10fbb0db1fe851beeb4fb44b8edc38607b6b8732ecfe'

def need(v, m):
 if not v: raise RuntimeError(m)
def sha(b): return hashlib.sha256(b).hexdigest()
def digest(p):
 h = hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda: f.read(1024**2), b''): h.update(b)
 return h.hexdigest()
def J(p): return json.loads(Path(p).read_bytes())
def write(p, j): p.write_text(json.dumps(j, ensure_ascii=False, indent=2) + '\n')
def safe(p):
 p = Path(p)
 need(p.is_absolute() and '..' not in p.parts and not any(x.is_symlink() for x in (p, *p.parents)), 'physical absolute root: ' + str(p))
 return p
def state(p):
 s = p.lstat()
 return dict(device=s.st_dev, inode=s.st_ino, mode=s.st_mode, bytes=s.st_size, mtime_ns=s.st_mtime_ns, ctime_ns=s.st_ctime_ns, nlink=s.st_nlink)
def overhead(n): return (n+4095)//4096 + (n+16383)//16384 + (n+33554431)//33554432 + 1024
def verify(row):
 p = Path(row['source_path']); need(state(p) == row['state'], 'source stat drift: ' + str(p))
 if row['type'] == 'regular': need(digest(p) == row['sha256'], 'source bytes drift: ' + str(p))
 else: need(os.readlink(p) == row['target'] and sha(os.fsencode(row['target'])) == row['sha256'], 'symlink drift')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--request',type=Path);ap.add_argument('--request-sha256');ap.add_argument('--execute-root-approved',action='store_true');a=ap.parse_args()
 if not a.execute_root_approved:
  print(json.dumps(dict(state='PREPARATION_ONLY',source_sha=F,attempts=['v2','v3'],product_rerun=False,live_NATIVE_access=False)));return 0
 need(not sys.flags.optimize and not os.environ.get('PYTHONOPTIMIZE'),'nonoptimized execution')
 need(a.request is not None and digest(safe(a.request))==a.request_sha256,'root request exact pin');q=J(a.request);pin=digest(__file__)
 need(q.get('source_sha')==F and q.get('root_execution_lease') is True and q.get('all_attempts_closed_no_more_writes') is True,'closed raw scope lease')
 need(q.get('collector_sha256')==pin,'collector identity');pp=safe(q['independent_peer']['path']);need(digest(pp)==q['independent_peer']['sha256'],'peer pin');peer=J(pp)
 need(type(peer.get('exit_code')) is int and peer['exit_code']==0 and peer.get('collector_sha256')==pin,'accepted exact collector')
 need(digest(safe(CONFIG))==CONFIG_PIN and digest(safe(CAP))==CAP_PIN,'fixed scope and original recorder');config=J(CONFIG)
 safe(SHM);need(digest(SHM/'STORAGE_POLICY.json')==POLICY,'original approved storage policy')
 out=safe(q['out']);need(out==SHM/'geo314-counterproof-terminal-package-20261025' and not out.exists(),'fresh exact own output')
 out.mkdir(mode=0o700);(out/'BOUND_REQUEST.json').write_bytes(a.request.read_bytes());(out/'COLLECTOR.py.txt').write_bytes(Path(__file__).read_bytes());(out/'SCOPE.json').write_bytes(CONFIG.read_bytes())
 result=dict(schema='geo314-v2-v3-complete-terminal-package/1',source_sha=F,collection_exit=None,started_epoch=time.time(),collector_sha256=pin,attempts=[],parts=[],errors=[],subject_rerun=False,live_NATIVE_access=False,formal_F9_native_original_exit=1,delivered=False,product_acceptance_rejudged=False)
 write(out/'RESULT.json',result)
 try:
  roots=[];extras={};expected_counts={}
  need(set(q['terminal_inputs'])==set(config['attempts'])=={'v2','v3'},'both terminal identities')
  for name,c in config['attempts'].items():
   root=safe(c['root']);finalpath=safe(c['final']);reqpath=safe(c['request']);executor=safe(c['executor'])
   need(digest(finalpath)==c['final_sha256']==q['terminal_inputs'][name]['final_sha256'],'host terminal identity')
   need(digest(root/'RESULT.json')==c['result_sha256'] and digest(reqpath)==c['request_sha256'] and digest(executor)==c['executor_sha256'],'original result/request/tool pins')
   final=J(finalpath);host=final['actual_tool_result'];summary=json.loads(host['output']);original=J(root/'RESULT.json');rq=J(reqpath)
   need(final['source_sha']==original['source_sha']==rq['source_sha']==F and final['executor_sha256']==rq['tool_sha256']==c['executor_sha256'] and final['request_sha256']==original['request_sha256']==c['request_sha256'],'original source/tool/request identity chain')
   need(rq['out']==str(root),'original own raw path')
   for value in [host['exit_code'],summary['exit_code'],original['exit_code']]:need(type(value) is int and value==c['exit_code'],'original v2 red/v3 zero preserved')
   need(summary['formal_F9_pass'] is False and original['formal_F9_pass'] is False and summary['counterproof_passed'] is True and original['counterproof_passed'] is True,'focused proof not whole native')
   need(original.get('ended_utc') and summary['restoration_errors']==original['restoration_errors'],'closed original restoration outcome')
   if name=='v2':need(len(original['restoration_errors'])==1 and 'original ROOT index bytes/inode/metadata untouched' in original['restoration_errors'][0] and (root/'INDEX_AFTER_FAILURE.bin').is_file(),'original index failure retained')
   else:need(original['restoration_errors']==[] and original['before']==original['after'] and original['shared_index_unchanged'] is True and (root/'ORIGINAL_INDEX.bin').is_file(),'v3 original restored identity')
   roots.append(('attempts/'+name,root,False));expected_counts['attempts/'+name]=(c['regular_files'],c['regular_bytes'])
   extras['attempts/'+name+'/original-host-final.json']=finalpath;extras['attempts/'+name+'/original-root-request.json']=reqpath
   result['attempts'].append(dict(name=name,source_sha=F,original_exit=c['exit_code'],counterproof_passed=True,formal_F9_pass=False,result_sha256=c['result_sha256'],host_sha256=c['final_sha256'],restoration_errors=original['restoration_errors']))
  for row in config['extra_files']:
   p=safe(row['path']);need(p.stat().st_size==row['bytes'] and digest(p)==row['sha256'],'pinned preparation/peer/tool original');need(row['member'] not in extras,'extra member collision');extras[row['member']]=p
  extras['collection-tool/collector.py']=Path(__file__);extras['collection-tool/SCOPE.json']=CONFIG;extras['collection-static-peer/REVIEW.json']=pp
  rows = []; excluded = []; specials = []; directories = []; used = set()
  def add_file(member, p, sourceplan=False):
   need(member not in used and not PurePosixPath(member).is_absolute() and '..' not in PurePosixPath(member).parts, 'unique safe member'); used.add(member); s = state(p)
   if stat.S_ISREG(s['mode']): row = dict(source_path=str(p), member=member, type='regular', bytes=s['bytes'], sha256=digest(p), state=s)
   elif stat.S_ISLNK(s['mode']):
    target = os.readlink(p); row = dict(source_path=str(p), member=member, type='symlink', bytes=len(os.fsencode(target)), sha256=sha(os.fsencode(target)), target=target, state=s)
   else:
    need(stat.S_ISSOCK(s['mode']), 'unexpected non-file payload: '+str(p)); specials.append(dict(source_path=str(p), member=member, state=s, reason='Unix IPC socket; metadata only, no serializable regular bytes; retained untouched')); return
   need(state(p) == s, 'inventory source changed')
   if sourceplan: row['reason'] = 'source Git metadata or mutable GUARD_LATEST; hash identity only, closed original per-guard logs included'; excluded.append(row)
   else: rows.append(row)
  for prefix, root, isplan in roots:
   safe(root); need(root.is_dir(), 'original root exists: '+str(root))
   for parent, subdirs, files in os.walk(root, followlinks=False):
    subdirs.sort(); files.sort()
    for name in sorted(subdirs+files):
     p = Path(parent)/name; rel = p.relative_to(root).as_posix(); s = state(p)
     if stat.S_ISDIR(s['mode']): directories.append(dict(scope=prefix, relative=rel, state=s)); continue
     add_file(prefix+'/'+rel, p, isplan and (rel.startswith('layout/jobs/') or rel == 'layout/GUARD_LATEST.json'))
  for member, p in sorted(extras.items()): add_file(member, p)
  for prefix,(count,nbytes) in expected_counts.items():
   selected=[r for r in rows if r['member'].startswith(prefix+'/') and r['member'] not in extras]
   need(len(selected)==count and all(r['type']=='regular' for r in selected) and sum(r['bytes'] for r in selected)==nbytes,'complete closed raw root inventory: '+prefix)
  need(not excluded and not specials,'no raw exclusion or nonregular omission')
  inv = dict(schema='geo314-complete-counterproof-terminal-inventory/1', source_sha=F, records=rows, hash_only_excluded_sourceplan=excluded, nonregular_metadata_only=specials, directory_metadata=directories, attempts=result['attempts'], selection=config['selection'], live_NATIVE_access=False, private_git_objects_and_indexes_included=True)
  write(out/'INVENTORY.json', inv)
  groups = []; group = []; logical = 0
  for row in rows:
   payload = row['bytes'] if row['type']=='regular' else 0
   # Preserve oversized original leaves as their own part; no truncation or omission.
   if group and logical+payload > TARGET: groups.append(group); group=[]; logical=0
   group.append(row['member']); logical += payload
   if logical >= TARGET: groups.append(group); group=[]; logical=0
  if group: groups.append(group)
  index = {r['member']:r for r in rows}; parts=[]
  for i,names in enumerate(groups,1):
   logical = sum(index[n]['bytes'] for n in names if index[n]['type']=='regular'); n=logical+4096*len(names)+10240
   parts.append(dict(part=i, members_exact=names, logical_regular_bytes=logical, tar_upper_bytes=n, gzip_upper_bytes=n+overhead(n), required_fresh_bytes=n+overhead(n)+META+RESERVE, reserve_bytes=RESERVE, metadata_bytes=META))
  write(out/'PARTS.json',parts); result.update(inventory_sha256=digest(out/'INVENTORY.json'), parts_sha256=digest(out/'PARTS.json'))
  write(out/'RESULT.json',result)
  for row in rows+excluded: verify(row)
  for part in parts:
   fresh=shutil.disk_usage(out).free; budget={k:v for k,v in part.items() if k!='members_exact'}; budget.update(fresh_output_free=fresh, admitted=fresh>=part['required_fresh_bytes'], compression_ratio_assumed=False); write(out/f'PART{part["part"]}_BUDGET.json',budget)
   need(budget['admitted'],'fresh full uncompressed bound plus original64MiB reserve'); archive=out/f'ORIGINAL_GEO314_COUNTERPROOF_PART{part["part"]}.tar.gz'
   with tarfile.open(archive,'w:gz',compresslevel=1,format=tarfile.PAX_FORMAT) as tar:
    for name in part['members_exact']:
     row=index[name]; verify(row); p=Path(row['source_path']); info=tarfile.TarInfo(name); info.mode=row['state']['mode']&0o777; info.mtime=row['state']['mtime_ns']//1000000000
     if row['type']=='symlink': info.type=tarfile.SYMTYPE; info.linkname=row['target']; info.size=0
     else: info.size=row['bytes']
     need(len(info.tobuf(tarfile.PAX_FORMAT))+511<=4096,'original fixed per-member header bound')
     if row['type']=='regular':
      with p.open('rb') as f: tar.addfile(info,f)
     else: tar.addfile(info)
     verify(row)
   need(archive.stat().st_size<=part['gzip_upper_bytes'],'conservative gzip upper bound')
   with tarfile.open(archive,'r:gz') as tar:
    members=tar.getmembers(); need([m.name for m in members]==part['members_exact'],'exact ordered tar scope')
    for m in members:
     row=index[m.name]
     if row['type']=='symlink': need(m.issym() and m.linkname==row['target'],'symlink roundtrip')
     else:
      need(m.isfile() and not m.islnk() and m.size==row['bytes'],'regular tar identity'); stream=tar.extractfile(m); need(stream is not None,'tar stream exists'); h=hashlib.sha256(); n=0
      with stream:
       for b in iter(lambda:stream.read(1024**2),b''):h.update(b); n+=len(b)
      need(h.hexdigest()==row['sha256'] and n==row['bytes'],'full member roundtrip')
   free=shutil.disk_usage(out).free; need(free>=RESERVE,'original64MiB reserve after archive')
   result['parts'].append(dict(part=part['part'],archive_path=str(archive),archive_sha256=digest(archive),archive_bytes=archive.stat().st_size,members=len(part['members_exact']),logical_regular_bytes=part['logical_regular_bytes'],roundtrip_complete=True,fresh_free_after=free)); write(out/'RESULT.json',result)
   print(json.dumps(dict(event='part-complete',**result['parts'][-1])),flush=True)
  for row in rows+excluded: verify(row)
  for row in specials: need(state(Path(row['source_path']))==row['state'],'socket metadata unchanged')
  # Reject new or removed original leaves as well as changed bytes, without following links.
  observed=set()
  for prefix,root,_ in roots:
   for parent,subdirs,files in os.walk(root,followlinks=False):
    for name in subdirs+files:
     p=Path(parent)/name
     if not stat.S_ISDIR(p.lstat().st_mode): observed.add(prefix+'/'+p.relative_to(root).as_posix())
  need(observed|set(extras)==used,'complete original leaf set unchanged')
  need(sum(p.stat().st_size for p in out.iterdir() if p.is_file() and not p.name.endswith('.tar.gz'))+32768<META,'actual metadata within original8MiB allowance')
  result.update(collection_exit=0,regular_files=sum(r['type']=='regular' for r in rows),symlinks=sum(r['type']=='symlink' for r in rows),regular_bytes=sum(r['bytes'] for r in rows if r['type']=='regular'),excluded_sourceplan_metadata_files=len(excluded),nonregular_metadata_nodes=len(specials),all_selected_sources_unchanged=True,all_members_exact_once=True,all_roundtrip_complete=True,final_free=shutil.disk_usage(out).free)
 except BaseException:
  result['collection_exit']=1;result['errors'].append(traceback.format_exc());traceback.print_exc()
 finally:
  result['ended_epoch']=time.time();write(out/'RESULT.json',result);print(json.dumps(result,ensure_ascii=False),flush=True)
 return result['collection_exit']

if __name__=='__main__': raise SystemExit(main())
