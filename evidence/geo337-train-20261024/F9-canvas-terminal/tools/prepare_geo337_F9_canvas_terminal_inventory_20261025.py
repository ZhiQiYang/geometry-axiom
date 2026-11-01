from pathlib import Path,PurePosixPath
import json,hashlib,os,stat,time,shutil,tarfile,traceback,sys
O=Path('/workspace/geo337-F9-canvas-terminal-preparation-20261025')
LAUNCH=Path('/tmp/geo337-F9-browser-canvas-launch-20261025')
STORE=Path('/tmp/geo337-F9-browser-canvas-run-20261025')
PLAN=Path('/tmp/geo337-F9-canvas-sourceplan-20261025')
MATERIALIZE=Path('/tmp/geo337-F9-canvas-source-materialize-launch-20261025')
F='4f8a794f4167c3562eb182045102e86e9e37cca9'
RECEIPT_PIN='3ade07e1f8656fc7eacdf5a9c85d492bd842fd7429c2e84fbee1505dcaa4e9c2'
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
CAP_PIN='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
ROOT_REQUEST=Path('/workspace/geo337-F9-canvas-root-request-20261025.json')
EXEC_FINAL=Path('/workspace/geo337-F9-canvas-EXEC_FINAL-20261025.json')
WRAPPER=Path('/tmp/geo337-F9-browser-launch-preparation-v2-20261025/launch_F9_browser.py')
TARGET=16*1024*1024;RESERVE=64*1024*1024;META=2*1024*1024
def h(b):return hashlib.sha256(b).hexdigest()
def digest(p):
 x=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):x.update(b)
 return x.hexdigest()
def write(n,j):(O/n).write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
def state(p):
 s=p.lstat();return {'device':s.st_dev,'inode':s.st_ino,'mode':s.st_mode,'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'nlink':s.st_nlink}
def exact_json(p):return json.loads(Path(p).read_bytes())
if sys.flags.optimize:raise RuntimeError('optimization forbidden')
if O.exists():raise RuntimeError('fresh own inventory output required')
O.mkdir();r={'schema':'geo337-F9-canvas-terminal-inventory/1','source_sha':F,'inventory_exit':None,'archive_execution_authorized':False,'archive_created':False,'subject_rerun':False,'started_epoch':time.time(),'errors':[]}
write('RESULT.json',r)
try:
 wr=exact_json(LAUNCH/'receipt.json');wf=exact_json(STORE/'original/canvas/receipt.json');request=exact_json(ROOT_REQUEST);final=exact_json(EXEC_FINAL);finalout=json.loads(final['output'])
 if not (wr['source_sha']==wf['sha']==request['source_sha']==finalout['source_sha']==F and wr['job']==wf['job']==request['job']==finalout['job']=='canvas'):raise RuntimeError('terminal source/job mismatch')
 if not (final['exit_code']==wr['wrapper_exit']==wr['original_primary_exit']==wf['exit_code']==finalout['wrapper_exit']==finalout['original_primary_exit']==0 and wr['passed'] and finalout['passed']):raise RuntimeError('expected actual terminal binding absent')
 if digest(STORE/'original/canvas/receipt.json')!=RECEIPT_PIN or wr['original_receipt_sha256']!=RECEIPT_PIN:raise RuntimeError('original workflow receipt changed')
 if digest(ROOT_REQUEST)!=wr['request_sha256'] or wf['ci_timeout_minutes']!=35 or wf['watchdog_factor']!=3 or wf['over_ci_timeout'] is not False:raise RuntimeError('request/35minute gate binding mismatch')
 if wf['checkout_before']!=wf['checkout_after']:raise RuntimeError('workflow checkout drift')
 for phase in ['before_guard','after_guard']:
  if wr[phase]['actual_process_returncode']!=0 or wr[phase]['timeout_expired']:raise RuntimeError('original source guard lacks zero')
 records=[];excluded=[];special=[];dirs=[];used=set()
 def add(prefix,root,sourceplan=False):
  for parent,subdirs,names in os.walk(root,followlinks=False):
   for name in sorted(subdirs+names):
    p=Path(parent)/name;rel=p.relative_to(root).as_posix();s=state(p)
    if stat.S_ISDIR(s['mode']):dirs.append({'scope':prefix,'relative':rel,'state':s});continue
    member=prefix+'/'+rel
    if member in used or '..' in PurePosixPath(member).parts:raise RuntimeError('duplicate or unsafe member')
    used.add(member)
    if sourceplan and (rel.startswith('layout/jobs/') or rel=='layout/GUARD_LATEST.json'):
     # Gitdir source/index/alternates stays in place; mutable latest guard is not relabelled.
     data=os.readlink(p).encode() if stat.S_ISLNK(s['mode']) else None
     if not stat.S_ISREG(s['mode']) and data is None:raise RuntimeError('unexpected sourceplan special')
     excluded.append({'source_path':str(p),'member':member,'state':s,'sha256':h(data) if data is not None else digest(p),'reason':'source Git metadata; hash identity only, not copied' if rel.startswith('layout/jobs/') else 'mutable GUARD_LATEST; original closed per-guard logs included instead'})
     continue
    if stat.S_ISREG(s['mode']):
     rawhash=digest(p)
     if state(p)!=s:raise RuntimeError('regular source changed during inventory')
     records.append({'source_path':str(p),'member':member,'type':'regular','bytes':s['bytes'],'sha256':rawhash,'state':s})
    elif stat.S_ISLNK(s['mode']):
     target=os.readlink(p);records.append({'source_path':str(p),'member':member,'type':'symlink','target':target,'bytes':len(os.fsencode(target)),'sha256':h(os.fsencode(target)),'state':s})
    else:special.append({'source_path':str(p),'member':member,'state':s,'reason':'nonregular IPC node; metadata only, no serializable file payload, retained untouched'})
 add('launch',LAUNCH);add('storage',STORE);add('sourceplan',PLAN,True);add('source-materialization',MATERIALIZE)
 extras=[('true-exec-final.json',EXEC_FINAL),('root-request.json',ROOT_REQUEST),('tools/launch_F9_browser.py',WRAPPER),('tools/original_collect_terminal_browser.py',Path('/workspace/train337-browser-terminal-collection/collect_terminal_browser.py')),('tools/inventory.py',Path(__file__)),('source-materialization-peer/REVIEW.json',Path('/workspace/geo337-F9-canvas-materialize-actual-peer-20261025/REVIEW.json'))]
 extras += [('tools/'+Path(p).name,Path(p)) for p in wr['driver_pins']]
 for name,p in extras:
  s=state(p)
  if not stat.S_ISREG(s['mode']) or name in used:raise RuntimeError('invalid extra')
  used.add(name);records.append({'source_path':str(p),'member':name,'type':'regular','bytes':s['bytes'],'sha256':digest(p),'state':s})
 for p,pin in wr['driver_pins'].items():
  if digest(p)!=pin:raise RuntimeError('executed driver drift')
 if digest(CAP)!=CAP_PIN:raise RuntimeError('original capture drift')
 guardbindings=[]
 for phase in ['before_guard','after_guard']:
  cmd=wr[phase];matches=[p for p in (PLAN/'layout/guard-logs').iterdir() if p.is_dir() and (p/'COMMANDS.json').is_file() and cmd['started_epoch']<=p.stat().st_mtime<=cmd['ended_epoch']]
  if len(matches)!=1:raise RuntimeError('original guard log scope ambiguous')
  guardbindings.append({'phase':phase,'directory':str(matches[0]),'selection':'unique closed COMMANDS directory mtime within original command interval','original_command':cmd})
 groups=[];group=[];logical=0
 for row in records:
  payload=row['bytes'] if row['type']=='regular' else 0
  if payload>TARGET:raise RuntimeError('single payload needs separately reviewed larger part')
  if group and logical+payload>TARGET:groups.append(group);group=[];logical=0
  group.append(row['member']);logical+=payload
 if group:groups.append(group)
 index={x['member']:x for x in records};budgets=[]
 for i,names in enumerate(groups,1):
  n=sum(index[name]['bytes'] for name in names if index[name]['type']=='regular');tarupper=n+4096*len(names)+10240;overhead=(tarupper+4095)//4096+(tarupper+16383)//16384+(tarupper+33554431)//33554432+1024
  budgets.append({'part':i,'members':len(names),'logical_regular_bytes':n,'header_padding_bound':4096*len(names),'tar_end_alignment_bound':10240,'tar_upper_bytes':tarupper,'gzip_worst_case_overhead':overhead,'gzip_upper_bytes':tarupper+overhead,'metadata_bytes':META,'reserve_bytes':RESERVE,'required_fresh_bytes':tarupper+overhead+META+RESERVE,'members_exact':names})
 inv={'schema':'geo337-F9-canvas-complete-selected-inventory/1','source_sha':F,'records':records,'hash_only_excluded_sourceplan':excluded,'nonregular_metadata_only':special,'directory_metadata':dirs,'original_guard_bindings':guardbindings,'selection':'all launch and storage regular bytes plus symlink targets; no ELF/cache/profile/diagnostic excluded; all non-Git immutable sourceplan and original preparation/guard streams/tools retained','source_and_seed_payload_copied':False,'git_objects_copied':False}
 write('INVENTORY.json',inv);write('PARTS.json',budgets)
 r.update(inventory_exit=0,selected_regular_files=sum(x['type']=='regular' for x in records),selected_symlinks=sum(x['type']=='symlink' for x in records),selected_regular_bytes=sum(x['bytes'] for x in records if x['type']=='regular'),excluded_sourceplan_files=len(excluded),excluded_sourceplan_bytes=sum(x['state']['bytes'] for x in excluded),nonregular_nodes=len(special),part_count=len(groups),max_required_fresh_bytes=max(x['required_fresh_bytes'] for x in budgets),workspace_free_observed=shutil.disk_usage('/workspace').free,temporary_free_observed=shutil.disk_usage('/tmp').free,inventory_sha256=digest(O/'INVENTORY.json'),parts_sha256=digest(O/'PARTS.json'),original_workflow_receipt_sha256=RECEIPT_PIN,original_formal_exit=0,original_35minute_gate_exit=0,original_elapsed_seconds=wf['seconds'],unknown_ELFs_excluded=False,cache_files_excluded=False,expected_fb_auto_probe_exit1_preserved_in_original_streams=True)
except BaseException:
 r['inventory_exit']=1;r['errors'].append(traceback.format_exc());traceback.print_exc()
finally:
 r['ended_epoch']=time.time();write('RESULT.json',r);print(json.dumps(r,ensure_ascii=False),flush=True)
sys.exit(r['inventory_exit'])
