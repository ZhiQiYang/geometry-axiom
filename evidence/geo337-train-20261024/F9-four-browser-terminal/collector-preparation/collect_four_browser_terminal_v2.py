"""Preserve four named terminated F9 jobs; root-approved SHM execution only."""
from pathlib import Path, PurePosixPath
import argparse, hashlib, json, os, shutil, stat, sys, tarfile, time, traceback

F = '4f8a794f4167c3562eb182045102e86e9e37cca9'
OWN = Path('/dev/shm/geo337-F9-browsers-20261025')
SHM = Path('/dev/shm/geometry-axiom-geo337-20261025')
POLICY = '9b2945ff5c6214d985cdb0a623c18721bfec3948bd9ea9e4e443a8b3f5c22f6a'
TARGET = 16 * 1024**2
RESERVE = 64 * 1024**2
META = 4 * 2 * 1024**2  # Four job inventories, retaining the original per-job metadata allowance.
CAP = Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
CAP_PIN = 'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
JOBS = {'documents': ('d', 10), 'grid': ('g', 15), 'space': ('s', 15), 'timber': ('t', 20)}

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
 ap = argparse.ArgumentParser(); ap.add_argument('--request', type=Path); ap.add_argument('--request-sha256'); ap.add_argument('--execute-root-approved', action='store_true'); a = ap.parse_args()
 if not a.execute_root_approved:
  print(json.dumps(dict(state='PREPARATION_ONLY', source_sha=F, jobs=list(JOBS), terminal_pins='UNBOUND until four true host terminals exist', archive_created=False, requires='root formal require_escalated execution plus exact independent static peer and closed-attempt lease'))); return 0
 need(not sys.flags.optimize and not os.environ.get('PYTHONOPTIMIZE'), 'nonoptimized execution required')
 need(a.request is not None and a.request_sha256 is not None and digest(safe(a.request)) == a.request_sha256, 'root request exact pin')
 q = J(a.request); pin = digest(__file__)
 need(q.get('source_sha') == F and q.get('root_execution_lease') is True and q.get('all_four_jobs_closed_no_more_guard_writes') is True, 'root closed-four-job lease')
 need(q.get('collector_sha256') == pin, 'collector exact binding')
 pp = safe(q['independent_peer']['path']); need(digest(pp) == q['independent_peer']['sha256'], 'peer exact pin'); peer = J(pp)
 need(type(peer.get('exit_code')) is int and peer['exit_code'] == 0 and peer.get('collector_sha256') == pin, 'accepted exact static peer')
 safe(OWN); safe(SHM); need(digest(SHM/'STORAGE_POLICY.json') == POLICY and digest(CAP) == CAP_PIN, 'original policy/capture identity')
 out = safe(q['out']); need(out.parent == SHM and out.name.startswith('remaining-browser-terminal-package-') and not out.exists(), 'fresh direct OWN output')
 out.mkdir(mode=0o700)
 (out/'BOUND_REQUEST.json').write_bytes(a.request.read_bytes()); (out/'COLLECTOR.py.txt').write_bytes(Path(__file__).read_bytes())
 result = dict(schema='geo337-F9-four-browser-full-package/1', source_sha=F, collection_exit=None, started_epoch=time.time(), collector_sha256=pin, attempts=[], parts=[], errors=[], subject_rerun=False, delivered=False, storage='protected volatile SHM; normal push and remote full bytes/hash verification required', product_acceptance_rejudged=False)
 write(out/'RESULT.json', result)
 try:
  # Establish real host/process/workflow termination before walking any runtime payload.
  extras = {}; roots = []; captured_tools = {str(CAP):CAP_PIN}; requests = []
  terminal_inputs=q['terminal_inputs']; need(set(terminal_inputs)==set(JOBS),'all four named terminal inputs')
  # Refuse an incomplete attempt list rather than silently omit a later environment retry.
  for job in JOBS:
   expected={job+'.json',job+'-sampled.json'}
   actual={p.name for p in (OWN/'requests').iterdir() if p.name.startswith(job) and p.suffix=='.json'}
   need(actual==expected,'unexpected additional attempt requires explicit reviewed scope: '+job)
  for attempt, (short, minutes) in JOBS.items():
   pins=terminal_inputs[attempt]; finalpin=pins['final_sha256']; finalpath=f'/workspace/geo337-F9-{attempt}-SHM-EXEC_FINAL-20261025.json'; storage_rel='r/'+short
   finalp = safe(finalpath); need(digest(finalp) == finalpin, 'true host final pin'); final = J(finalp); host = final['actual_tool_result']; hostout = json.loads(host['output'])
   code=host['exit_code']; need(type(code) is int, 'true host integer exit')
   rq = OWN/'requests'/f'{attempt}.json'; sq = OWN/'requests'/f'{attempt}-sampled.json'; req = J(rq); srq = J(sq)
   launch = safe(OWN/'launches'/attempt); sampled = safe(OWN/'sampled'/attempt); storage = safe(OWN/storage_rel)
   wr = J(launch/'receipt.json'); sr = J(sampled/'RESULT.json'); wfpath = storage/'original'/attempt/'receipt.json'; wf = J(wfpath)
   need(final['source_sha'] == hostout['source_sha'] == req['source_sha'] == srq['source_sha'] == wr['source_sha'] == sr['source_sha'] == wf['sha'] == F, 'all terminal source SHA identities')
   need(hostout['job'] == req['job'] == srq['job'] == wr['job'] == sr['job'] == wf['job'] == attempt, 'all terminal job identities')
   need(host['exit_code'] == hostout['wrapper_exit'] == hostout['original_process_returncode'] == sr['wrapper_exit'] == sr['original_process_returncode'] == wr['wrapper_exit'] == code, 'true host/sampler/launcher exit chain')
   primary=wf['exit_code']; need(type(primary) is int and wr['original_primary_exit']==primary, 'true original workflow exit preserved independently')
   need(type(sr['sampling_complete']) is bool and hostout['sampling_complete']==sr['sampling_complete'] and sr['original_receipt_sha256'] == digest(launch/'receipt.json') and wr['original_receipt_sha256'] == digest(wfpath), 'closed sampler and workflow receipt bindings; sampling failures preserved')
   need(req['out'] == str(launch) and req['storage'] == str(storage) and srq['out'] == str(sampled), 'exact original output roots')
   need(req['plan_dir'] == str(OWN/'plans'/attempt) and req['source_layout'] == str(OWN/'sources'/attempt), 'exact isolated source plan')
   need(digest(rq) == wr['request_sha256'] == srq['launch_request']['sha256'] and srq['launch_request']['path'] == str(rq) and digest(sq) == sr['request_sha256'], 'request identity chain')
   need(wf['ci_timeout_minutes'] == minutes and wf['watchdog_factor'] == 3 and type(wf['over_ci_timeout']) is bool, 'unchanged original time definitions; actual gate result preserved')
   for phase in ['before_guard', 'after_guard']:
    need(type(wr[phase]['actual_process_returncode']) is int and type(wr[phase]['timeout_expired']) is bool, 'closed original source guard; original red preserved')
   events = [json.loads(line) for line in (launch/'reaper.jsonl').read_text().splitlines()]; done = [e for e in events if e.get('event') == '完成']
   need(len(done) == 1 and events[-1] == done[0] and done[0]['primary_returncode'] == primary, 'true reaper terminal')
   need(wr['original_command']['actual_process_returncode'] == primary, 'original captured command terminal')
   for path, h in wr['driver_pins'].items():
    need(digest(safe(path)) == h, 'executed driver pin'); captured_tools[path] = h
   launcher = Path(srq['launch_argv'][2]); need(digest(launcher) == sr['launcher_sha256'], 'executed launcher pin'); captured_tools[str(launcher)] = sr['launcher_sha256']
   for p in [rq, sq, finalp, Path('/workspace/launch_geo337_F9_next_browser_root_20261025.py')]: extras[f'attempts/{attempt}/inputs/{p.name}'] = safe(p)
   roots += [(f'attempts/{attempt}/launch', launch, False), (f'attempts/{attempt}/storage', storage, False), (f'attempts/{attempt}/sampler', sampled, False)]
   requests.append(req)
   result['attempts'].append(dict(name=attempt, source_sha=F, original_formal_exit=primary, original_wrapper_exit=wr['wrapper_exit'], original_ci_timeout_minutes=minutes, original_ci_gate_exit=1 if wf['over_ci_timeout'] else 0, original_elapsed_seconds=wf['seconds'], original_receipt_sha256=digest(wfpath), host_final_sha256=finalpin, passed=wr['passed'], failure_classification='not inferred by collector', sampling_complete=sr['sampling_complete'], checkout_before_after_equal=wf['checkout_before']==wf['checkout_after'], guard_exits={phase:wr[phase]['actual_process_returncode'] for phase in ['before_guard','after_guard']}))
  for req in requests:
   job=req['job']; pins=terminal_inputs[job]; plan=OWN/'plans'/job
   need(req['plan_sha256']==digest(plan/'PLAN.json'),'original single-job plan identity')
   prep=req['source_preparation']; need(digest(safe(prep['path']))==prep['sha256'] and J(prep['path'])['actual_process_returncode']==0,'original materialization true zero')
   roots += [(f'sourceplan/{job}',plan,True),(f'source-materialization/{job}',OWN/'host'/(job+'-materialize'),False),(f'source-plan-generation/{job}',OWN/'host'/(job+'-plan'),False)]
   for phase in ['plan','materialize']:
    p=safe(f'/workspace/geo337-F9-{job}-SHM-{phase}-EXEC_FINAL-20261025.json')
    need(digest(p)==pins[phase+'_final_sha256'] and J(p)['exit_code']==0,'original preparation host terminal')
    extras[f'source-preparation/{job}/{phase}-EXEC_FINAL.json']=p
  sampler = Path('/workspace/geo337-F9-browser-sampler-preparation-20261025/sample_original_browser_v2.py')
  need(digest(sampler) == '919eafb54f20454ee44a27754ce04f6f63f05f6e1c9b32a5b51652058735af30', 'original sampler source'); captured_tools[str(sampler)] = digest(sampler)
  for i, (path, h) in enumerate(sorted(captured_tools.items())): extras[f'tools/{i:02d}-{Path(path).name}'] = Path(path)
  extras['tools/collector.py'] = Path(__file__); extras['static-peer/REVIEW.json'] = pp
  # Per-job actual peers are published as separate evidence leaves after collection, not invented here.
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
  inv = dict(schema='geo337-F9-four-browser-complete-terminal-inventory/1', source_sha=F, records=rows, hash_only_excluded_sourceplan=excluded, nonregular_metadata_only=specials, directory_metadata=directories, attempts=result['attempts'], selection='All regular bytes and symlink targets of four isolated launch/storage/sampler roots, original preparation/closed guards/tools; no ELF/cache/profile/diagnostic exclusions.', no_seed_source_payload_copied=True, no_git_object_payload_copied=True)
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
   need(budget['admitted'],'fresh full uncompressed bound plus original64MiB reserve'); archive=out/f'ORIGINAL_FOUR_BROWSER_PART{part["part"]}.tar.gz'
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
  need(sum(p.stat().st_size for p in out.iterdir() if p.is_file() and not p.name.endswith('.tar.gz'))+32768<META,'actual metadata within four original2MiB allowances')
  result.update(collection_exit=0,regular_files=sum(r['type']=='regular' for r in rows),symlinks=sum(r['type']=='symlink' for r in rows),regular_bytes=sum(r['bytes'] for r in rows if r['type']=='regular'),excluded_sourceplan_metadata_files=len(excluded),nonregular_metadata_nodes=len(specials),all_selected_sources_unchanged=True,all_members_exact_once=True,all_roundtrip_complete=True,final_free=shutil.disk_usage(out).free)
 except BaseException:
  result['collection_exit']=1;result['errors'].append(traceback.format_exc());traceback.print_exc()
 finally:
  result['ended_epoch']=time.time();write(out/'RESULT.json',result);print(json.dumps(result,ensure_ascii=False),flush=True)
 return result['collection_exit']

if __name__=='__main__': raise SystemExit(main())
