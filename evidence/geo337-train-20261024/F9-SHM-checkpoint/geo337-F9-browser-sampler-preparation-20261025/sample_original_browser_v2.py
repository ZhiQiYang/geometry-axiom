"""Observe one original F9 browser launch; root executes only by approved SHM access."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,stat,sys,threading,time,traceback
F9='4f8a794f4167c3562eb182045102e86e9e37cca9'
OWN=Path('/dev/shm/geo337-F9-browsers-20261025')
OTHER=Path('/dev/shm/geometry-axiom-geo337-20261025')
CAPTURE=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
CAPTURE_PIN='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
LAUNCHER=Path('/workspace/geo337-F9-five-browser-shm-preparation-20261025/launch_F9_browser_shm_v2.py')
LAUNCHER_PIN='58106e23496c9ee67c7c2162817283464e7af011e758658283139060b797fc3b'
CEILING=2*1024**3
RUNTIME_PLANNING_INCREMENT=416*1024**2  # Root:64raw+32archive+32Git+32remote+256transient; no source or runtime reserve.
JOBS=('assembly','documents','grid','space','timber')
def need(value,message):
 if not value:raise RuntimeError(message)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def safe(path):
 p=Path(path);need(p.is_absolute() and '..' not in p.parts,'ABSOLUTE_NO_DOTDOT')
 need(all(not x.is_symlink() for x in (p,*p.parents)),'NO_SYMLINK_PATH');return p
def inventory(roots):
 """Endpoint metadata only, unique inodes across roots, never follow any symlink."""
 seen=set();summary=[];total=0
 for root in roots:
  root=safe(root);need(root.is_dir(),'OWN_ROOT_PRESENT:'+str(root));pending=[root];rows=0;allocated=0;logical=0;duplicates=0;links=0
  while pending:
   p=pending.pop();s=p.lstat();rows+=1;key=(s.st_dev,s.st_ino)
   if key in seen:duplicates+=1;continue
   seen.add(key);allocated+=s.st_blocks*512;logical+=s.st_size
   if stat.S_ISLNK(s.st_mode):links+=1
   elif stat.S_ISDIR(s.st_mode):
    with os.scandir(p) as entries:pending.extend(Path(e.path) for e in entries)
  total+=allocated;summary.append(dict(root=str(root),entries=rows,unique_allocated_bytes=allocated,unique_lstat_logical_bytes=logical,duplicate_inode_paths=duplicates,symlinks_not_followed=links))
 return dict(roots=summary,unique_allocated_bytes=total,unique_inode_count=len(seen),endpoint_only=True,payload_read=False)
def sample():
 row=dict(epoch=time.time(),monotonic=time.monotonic(),filesystems={},errors=[])
 for name in ['/dev/shm','/workspace','/tmp']:
  try:
   v=os.statvfs(name);row['filesystems'][name]=dict(free_bytes=v.f_bavail*v.f_frsize,total_bytes=v.f_blocks*v.f_frsize)
  except Exception as e:row['errors'].append(dict(path=name,error=repr(e)))
 for name in ['memory.current','memory.events']:
  try:
   raw=(Path('/sys/fs/cgroup')/name).read_text()
   row[name]=int(raw.strip()) if name=='memory.current' else {k:int(v) for k,v in (line.split() for line in raw.splitlines())}
  except Exception as e:row['errors'].append(dict(path=name,error=repr(e)))
 return row
def summarize(rows):
 fs={}
 for path in ['/dev/shm','/workspace','/tmp']:
  selected=[r['filesystems'][path] for r in rows if path in r['filesystems']]
  if selected:fs[path]=dict(minimum_sampled_free_bytes=min(r['free_bytes'] for r in selected),maximum_sampled_filesystem_used_bytes=max(r['total_bytes']-r['free_bytes'] for r in selected),scope='Entire mount, includes other owners; not OWN-only runtime peak')
 memory=[r['memory.current'] for r in rows if isinstance(r.get('memory.current'),int)]
 gaps=[b['monotonic']-a['monotonic'] for a,b in zip(rows,rows[1:])]
 return dict(samples=len(rows),nominal_interval_seconds=1,maximum_observed_gap_seconds=max(gaps) if gaps else None,filesystems=fs,maximum_sampled_cgroup_memory_bytes=max(memory) if memory else None,first_memory_events=rows[0].get('memory.events') if rows else None,last_memory_events=rows[-1].get('memory.events') if rows else None,sample_read_errors=sum(len(r['errors']) for r in rows),continuous_true_peak_known=False,no_R8_or_P189_performance_inference=True)
def exit_status(child):
 return child if child>=0 else 128-child

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--request',type=Path,required=True);ap.add_argument('--request-sha256',required=True);a=ap.parse_args()
 need(not sys.flags.optimize and 'PYTHONOPTIMIZE' not in os.environ,'ASSERTIONS_REQUIRED')
 need(sha(safe(a.request))==a.request_sha256,'ROOT_REQUEST_PIN');q=json.loads(a.request.read_bytes())
 need(q['schema']=='geo337-F9-browser-sampled-launch/1' and q['source_sha']==F9 and q['job'] in JOBS,'EXACT_F9_JOB')
 need(q['root_execution_lease'] is True and q['root_single_job_shared_SHM_budget_window'] is True,'ROOT_LEASE')
 need(sha(CAPTURE)==CAPTURE_PIN and sha(LAUNCHER)==LAUNCHER_PIN,'ORIGINAL_TOOL_PINS')
 lp=safe(q['launch_request']['path']);need(sha(lp)==q['launch_request']['sha256'],'ORIGINAL_LAUNCH_REQUEST_PIN');l=json.loads(lp.read_bytes())
 need(l['schema']=='geo337-F9-single-browser-launch/1' and l['source_sha']==F9 and l['job']==q['job'] and l['root_execution_lease'] is True and l['root_scheduled_single_browser'] is True,'ORIGINAL_LAUNCH_IDENTITY')
 argv=q['launch_argv'];need(len(argv)==7 and argv[1:]==['-B',str(LAUNCHER),'--request',str(lp),'--request-sha256',q['launch_request']['sha256']],'ONLY_ORIGINAL_LAUNCH_ARGV')
 need(argv[0] in [sys.executable,'python3'],'ORIGINAL_PYTHON_ARGV')
 out=safe(q['out']);need(out.is_relative_to(OWN) and out!=OWN and not out.exists() and out.parent.is_dir(),'FRESH_OWN_OBSERVER_OUT')
 for value in [l[k] for k in ['out','storage','plan_dir','source_layout']]+[str(OWN/'seed')]:
  p=safe(value);need(out!=p and not out.is_relative_to(p) and not p.is_relative_to(out),'NO_OBSERVER_SUBJECT_OVERLAP')
 before=inventory([OWN,OTHER]);need(before['unique_allocated_bytes']+RUNTIME_PLANNING_INCREMENT<=CEILING,'SHARED_2GiB_STARTUP_PLANNING_ONLY')
 out.mkdir();dump(out/'BOUND_REQUEST.json',q);dump(out/'OWN_BEFORE.json',before)
 spec=importlib.util.spec_from_file_location('original_capture_for_sampler',CAPTURE);cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
 # Byte-for-byte inherited environment: no TMPDIR/PATH/timeout/port/judge changes.
 recorder=cap.Recorder(out,dict(os.environ),F9);stop=threading.Event();samples=[];sampling_errors=[]
 report=dict(source_sha=F9,job=q['job'],request_sha256=a.request_sha256,launcher_sha256=LAUNCHER_PIN,capture_sha256=CAPTURE_PIN,commands=recorder.rows,original_process_returncode=None,wrapper_exit=None,errors=[],sampling_errors=sampling_errors,original_environment_unchanged=True,original_timeout_unchanged=True,no_runtime_reserve_or_dynamic_budget_kill=True,startup_shared_budget_bytes=CEILING,startup_planning_increment_bytes=RUNTIME_PLANNING_INCREMENT,startup_planned_total_bytes=before['unique_allocated_bytes']+RUNTIME_PLANNING_INCREMENT,own_before=before,original_passed=None,test_execution_delegated_to_pinned_original_launcher=True)
 report['mountinfo_before']=[x for x in Path('/proc/self/mountinfo').read_text().splitlines() if len(x.split())>4 and x.split()[4] in ['/tmp','/workspace','/dev/shm']]
 def observe():
  try:
   with (out/'SAMPLES.jsonl').open('x') as stream:
    while True:
     row=sample();samples.append(row);stream.write(json.dumps(row,ensure_ascii=False)+'\n');stream.flush()
     if stop.wait(1):break
    row=sample();samples.append(row);stream.write(json.dumps(row,ensure_ascii=False)+'\n');stream.flush()
  except BaseException:sampling_errors.append(traceback.format_exc())
 thread=threading.Thread(target=observe,name='one-second-readonly-sampler');thread.start();code=2
 try:
  row,_,_=recorder.run(argv,cwd='/workspace',timeout=None,check=False,source_variant='unchanged-F9-SHM-browser-launch-with-external-observation')
  child=row['actual_process_returncode'];need(isinstance(child,int),'ORIGINAL_TRUE_EXIT_REQUIRED');report['original_process_returncode']=child;code=exit_status(child)
  receipt=Path(l['out'])/'receipt.json';r=json.loads(receipt.read_bytes())
  need(r['source_sha']==F9 and r['job']==q['job'] and r['wrapper_exit']==child,'ORIGINAL_RECEIPT_EXIT_AGREEMENT')
  report.update(original_receipt=str(receipt),original_receipt_sha256=sha(receipt),original_passed=r['passed'],original_primary_exit=r['original_primary_exit'])
 except BaseException:report['errors'].append(traceback.format_exc());code=2
 finally:
  stop.set();thread.join()
  try:report['own_after']=inventory([OWN,OTHER]);dump(out/'OWN_AFTER.json',report['own_after'])
  except BaseException:sampling_errors.append(traceback.format_exc())
  report.update(sampled_observations=summarize(samples),sampling_complete=bool(samples) and not sampling_errors and all(not r['errors'] for r in samples),wrapper_exit=code,ended_epoch=time.time())
  report['limitations']=['Sampled observations, not continuous peak; filesystem and cgroup counters include other workloads.','Only endpoint OWN metadata traversal; no per-second source scan or payload hash.','Observer failures are separate from unchanged original process result; inspect errors even if child exit is zero.','SHM is volatile: complete original collection, normal push and remote full archive size/hash confirmation still required before delivery.','Shared2GiB budget adds root-planned416MiB only before launch; no source64MiB or runtime64MiB reserve is added. No runtime kill/timeout/termination threshold was added.']
  dump(out/'RESULT.json',report)
 print(json.dumps({k:report[k] for k in ['source_sha','job','original_process_returncode','wrapper_exit','sampling_complete']}));return code
if __name__=='__main__':raise SystemExit(main())
