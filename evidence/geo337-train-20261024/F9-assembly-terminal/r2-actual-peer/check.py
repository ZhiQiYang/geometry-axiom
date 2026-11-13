from pathlib import Path
import datetime,hashlib,json
B=Path('/dev/shm/geo337-F9-browsers-20261025');O=Path('/workspace/geo337-F9-assembly-r2-SHM-actual-peer-20261025');F='4f8a794f4167c3562eb182045102e86e9e37cca9'
checks=[];pins={};nbytes=0
def need(v,m):
 checks.append({'check':m,'passed':bool(v)});assert v,m
def read(p):
 global nbytes
 p=Path(p);need(not p.is_symlink(),'REGULAR_METADATA:'+str(p));r=p.read_bytes();nbytes+=len(r);pins[str(p)]=hashlib.sha256(r).hexdigest();return r
def j(p):return json.loads(read(p))
s=j(B/'sampled/assembly-r2/RESULT.json');l=j(B/'launches/assembly-r2/receipt.json');wp=B/'r/a2/original/assembly/receipt.json';w=j(wp);host=j('/workspace/geo337-F9-assembly-short-path-SHM-EXEC_FINAL-20261025.json')
need(s['source_sha']==l['source_sha']==w['sha']==F,'F9_ONE_SOURCE_IDENTITY');need(s['job']==l['job']==w['job']=='assembly','ONE_ASSEMBLY_JOB')
need(s['original_process_returncode']==s['wrapper_exit']==l['original_primary_exit']==l['wrapper_exit']==w['exit_code']==host['actual_tool_result']['exit_code']==0,'TRUE_ORIGINAL_AND_HOST_EXIT_0')
need(s['original_passed'] and l['passed'],'ORIGINAL_PASS_TRUE');need(not w['over_ci_timeout'] and w['ci_timeout_minutes']==15 and w['watchdog_factor']==3,'UNCHANGED_CI_NOT_TIMEOUT')
need(not s['errors'] and not s['sampling_errors'] and s['sampling_complete'] and not l['errors'],'RECORDER_NO_CONCEALMENT_ERRORS')
need(l['before_guard']['actual_process_returncode']==l['after_guard']['actual_process_returncode']==0,'ORIGINAL_BEFORE_AFTER_GUARDS_ZERO')
need(w['checkout_after']['head']==F and not w['checkout_after']['status'],'ORIGINAL_SOURCE_AFTER_CLEAN_RECORD')
need(s['original_receipt_sha256']==pins[str(B/'launches/assembly-r2/receipt.json')],'SAMPLER_TO_LAUNCHER_PIN');need(l['original_receipt_sha256']==pins[str(wp)],'LAUNCHER_TO_WORKFLOW_PIN')
for row in s['commands']+l['commands']:
 need(row['source_sha']==F and row['acceptance_sha']==F and not row['timeout_expired'],'CAPTURE_IDENTITY_AND_NO_TIMEOUT')
 d=Path(row['directory']);rr=j(d/'result.json');need(rr==row,'CAPTURE_ORIGINAL_RESULT_EXACT')
 for name in ['stdout','stderr']:
  b=read(d/(name+'.bin'));need(len(b)==row[name+'_bytes'] and hashlib.sha256(b).hexdigest()==row[name+'_sha256'],'CAPTURE_COMPLETE_'+name)
for rel,meta in w['files'].items():
 p=wp.parent/rel;need(p.is_relative_to(wp.parent) and '..' not in Path(rel).parts,'ORIGINAL_WORKFLOW_FILE_SCOPE');b=read(p);need(len(b)==meta['bytes'] and hashlib.sha256(b).hexdigest()==meta['sha256'],'ORIGINAL_WORKFLOW_FILE_EXACT:'+rel)
raw=read(B/'sampled/assembly-r2/SAMPLES.jsonl');samples=[json.loads(x)for x in raw.splitlines()];obs=s['sampled_observations'];need(len(samples)==obs['samples']==193,'ALL_193_SAMPLES_PRESENT')
need(all(not x['errors'] for x in samples),'SAMPLE_READ_ERRORS_ZERO')
for fs in ['/dev/shm','/workspace','/tmp']:
 rows=[r['filesystems'][fs] for r in samples];v=obs['filesystems'][fs]
 need(v['minimum_sampled_free_bytes']==min(r['free_bytes']for r in rows),'RECOMPUTED_MIN_FREE:'+fs)
 need(v['maximum_sampled_filesystem_used_bytes']==max(r['total_bytes']-r['free_bytes']for r in rows),'RECOMPUTED_MAX_SHARED_USED:'+fs)
need(obs['maximum_sampled_cgroup_memory_bytes']==max(r['memory.current']for r in samples),'RECOMPUTED_MAX_CGROUP')
need(obs['maximum_observed_gap_seconds']==max(b['monotonic']-a['monotonic']for a,b in zip(samples,samples[1:])),'RECOMPUTED_MAX_SAMPLE_GAP')
need(all(r['memory.events']['oom']==r['memory.events']['oom_kill']==0 for r in samples),'NO_OBSERVED_OOM_OR_OOM_KILL')
for k in ['before','after']:
 own=j(B/f'sampled/assembly-r2/OWN_{k.upper()}.json');need(own==s['own_'+k],'ENDPOINT_INVENTORY_ORIGINAL_'+k);need(own['unique_allocated_bytes']==sum(r['unique_allocated_bytes']for r in own['roots']),'ENDPOINT_SUM_'+k)
need(s['startup_planning_increment_bytes']==416*1024**2 and s['startup_planned_total_bytes']==s['own_before']['unique_allocated_bytes']+416*1024**2<=2*1024**3,'STARTUP_ONLY_CAPACITY_ORIGINAL_PASS')
stdout=read(wp.parent/'steps/03.stdout').decode();lines=[x for x in stdout.splitlines()if x.startswith('CDP_RESULT ')];need(len(lines)==1,'ONE_CDP_RESULT');cdp=json.loads(lines[0][len('CDP_RESULT '):]);need(cdp['completed'] and cdp['passedAssertions']==150 and cdp['failedAssertions']==0 and cdp['sections']=={'P77':134,'P82':16},'FULL_ORIGINAL_ASSEMBLY_150_ASSERTIONS');need(cdp['goldenCompare']=='not compared (partial mode)','ORIGINAL_ASSEMBLY_PARTIAL_MODE_NOT_CANVAS_GOLDEN')
need(cdp['scope']['filters']==['GEOMETRY_ASSEMBLY_ONLY'] and not cdp['skipped'] and cdp['uncaughtBrowserExceptions']==0 and cdp['firstNetworkFailure'] is None,'ORIGINAL_SCOPE_ZERO_SKIP_BROWSER_EXCEPTION')
need(cdp['firstTransportFailure']['error']=='Injected lost success response','REPORTED_EXPECTED_LOST_SUCCESS_RESPONSE_INJECTION')
q0=j(B/'requests/assembly.json');q2=j(B/'requests/assembly-r2.json');deltas={k:[q0.get(k),q2.get(k)]for k in set(q0)|set(q2) if q0.get(k)!=q2.get(k)}
need(set(deltas)=={'out','storage'},'ONLY_FRESH_OUTPUT_STORAGE_REQUEST_DELTA')
need(q2['storage']==str(B/'r/a2') and q2['out']==str(B/'launches/assembly-r2'),'EXACT_SHORT_STORAGE_REQUEST')
need(w['workflow_sha256']=='b491142a6767e78588710f90bf0ea03b9b5af9ef6eb851cd9e28d32f0c262d6d','UNCHANGED_ORIGINAL_WORKFLOW_PIN')
prior=j('/workspace/geo337-F9-assembly-first-SHM-actual-peer-20261025/REVIEW.json');need(prior['original_formal_exit']==1 and prior['exit_code']==0,'PRIOR_ENVIRONMENT_RED_RETAINED')
paths=[]
for job,storage in [('assembly','r/a2'),('documents','r/d'),('grid','r/g'),('space','r/s'),('timber','r/t'),('assembly-old','runs/assembly')]:
 suite='assembly'if job=='assembly-old'else job;p=B/storage/'tmp/original'/suite/'com.google.Chrome.ABCDEF/SingletonSocket';n=len(str(p).encode());paths.append(dict(job=job,path=str(p),utf8_path_bytes=n,with_terminating_NUL_bytes=n+1,below_108_with_NUL=n+1<108))
need(all(r['below_108_with_NUL']for r in paths[:-1]) and not paths[-1]['below_108_with_NUL'],'SHORT_LITERAL_PATHS_PASS_OLD_FAIL')
mounts=s['mountinfo_before'];need(any(' /dev/shm 'in m and ' - tmpfs 'in m for m in mounts),'ORIGINAL_SHM_TMPFS_MOUNT_RECORDED')
result={'schema':'geo337-F9-assembly-r2-SHM-formal-and-sampler-actual-peer/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha':F,'exit_code':0,'checks':len(checks),'blocking_findings':[],'original_formal_exit':0,'formal_status':'GREEN_ORIGINAL_FULL_ASSEMBLY_JOB; not yet remote delivered','original_CDP_result':cdp,'assertions':{'passed':150,'failed':0,'completed':True,'sections':cdp['sections'],'skipped':cdp['skipped'],'golden':cdp['goldenCompare']},'only_request_deltas':deltas,'original_seconds':w['seconds'],'original_ci_minutes':w['ci_timeout_minutes'],'prior_attempt_formal_exit':1,'original_argv_full_streams_checked':len(s['commands'])+len(l['commands']),'original_workflow_files_checked':len(w['files']),'raw_metadata_bytes_read':nbytes,'pins':pins,'sampled_observations_recomputed':obs,'own_before':s['own_before'],'own_after':s['own_after'],'mountinfo_at_original_launch':mounts,'short_storage_literal_paths':paths,'correction_of_initial_chat_arithmetic':'Initial base+40 calculation omitted one slash separator. Full literal UTF8 is104/104/99/100/101; includingNUL105/105/100/101/102. Original path113/NUL114. Prior original files unchanged.','next_change_scope':'Root changes only fresh request storage/output names to approved exactOWN short paths; original source plan/launcher/driver/CI/golden/ports unchanged. New run must succeed independently; first environment red retained.','limits':['Only formally require_escalated read of terminal metadata/raw; no SHM writes, source or payload scan, no tests/guards rerun.','Sampler peaks are sampled shared mount/cgroup values, not continuous or this-job-only peaks; no R8 inference.','Endpoint OWN inventories compared to original recorded sums, not rewalked during active r2.','First environment-red attempt remains retained; current green result is a distinct fresh run.','Remote publication/full archive verification remains separate.'],'check_details':checks}
p=O/'REVIEW.json';need(not p.exists(),'FRESH_PEER_OUTPUT');p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'checks':result['checks'],'exit_code':0,'original_formal_exit':0,'sampled_shared_SHM_max':obs['filesystems']['/dev/shm']['maximum_sampled_filesystem_used_bytes']}))
