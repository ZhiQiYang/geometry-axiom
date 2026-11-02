from pathlib import Path
import datetime,hashlib,json
B=Path('/dev/shm/geo337-F9-browsers-20261025');O=Path('/workspace/geo337-F9-documents-SHM-actual-peer-20261025');F='4f8a794f4167c3562eb182045102e86e9e37cca9'
checks=[];pins={};nbytes=0
def need(v,m):
 checks.append({'check':m,'passed':bool(v)});assert v,m
def read(p):
 global nbytes
 p=Path(p);need(not p.is_symlink(),'REGULAR_METADATA:'+str(p));r=p.read_bytes();nbytes+=len(r);pins[str(p)]=hashlib.sha256(r).hexdigest();return r
def j(p):return json.loads(read(p))
s=j(B/'sampled/documents/RESULT.json');l=j(B/'launches/documents/receipt.json');wp=B/'r/d/original/documents/receipt.json';w=j(wp);host=j('/workspace/geo337-F9-documents-SHM-EXEC_FINAL-20261025.json')
need(s['source_sha']==l['source_sha']==w['sha']==F,'F9_ONE_SOURCE_IDENTITY');need(s['job']==l['job']==w['job']=='documents','ONE_DOCUMENTS_JOB')
need(s['original_process_returncode']==s['wrapper_exit']==l['original_primary_exit']==l['wrapper_exit']==w['exit_code']==host['actual_tool_result']['exit_code']==0,'TRUE_ORIGINAL_AND_HOST_EXIT_0')
need(s['original_passed'] and l['passed'],'ORIGINAL_PASS_TRUE');need(not w['over_ci_timeout'] and w['ci_timeout_minutes']==10 and w['watchdog_factor']==3,'UNCHANGED_CI_NOT_TIMEOUT')
need(not s['errors'] and not s['sampling_errors'] and s['sampling_complete'] and not l['errors'],'RECORDER_NO_CONCEALMENT_ERRORS')
need(l['before_guard']['actual_process_returncode']==l['after_guard']['actual_process_returncode']==0,'ORIGINAL_BEFORE_AFTER_GUARDS_ZERO')
need(w['checkout_after']['head']==F and not w['checkout_after']['status'],'ORIGINAL_SOURCE_AFTER_CLEAN_RECORD')
need(s['original_receipt_sha256']==pins[str(B/'launches/documents/receipt.json')],'SAMPLER_TO_LAUNCHER_PIN');need(l['original_receipt_sha256']==pins[str(wp)],'LAUNCHER_TO_WORKFLOW_PIN')
for row in s['commands']+l['commands']:
 need(row['source_sha']==F and row['acceptance_sha']==F and not row['timeout_expired'],'CAPTURE_IDENTITY_AND_NO_TIMEOUT')
 d=Path(row['directory']);rr=j(d/'result.json');need(rr==row,'CAPTURE_ORIGINAL_RESULT_EXACT')
 for name in ['stdout','stderr']:
  b=read(d/(name+'.bin'));need(len(b)==row[name+'_bytes'] and hashlib.sha256(b).hexdigest()==row[name+'_sha256'],'CAPTURE_COMPLETE_'+name)
for rel,meta in w['files'].items():
 p=wp.parent/rel;need(p.is_relative_to(wp.parent) and '..' not in Path(rel).parts,'ORIGINAL_WORKFLOW_FILE_SCOPE');b=read(p);need(len(b)==meta['bytes'] and hashlib.sha256(b).hexdigest()==meta['sha256'],'ORIGINAL_WORKFLOW_FILE_EXACT:'+rel)
raw=read(B/'sampled/documents/SAMPLES.jsonl');samples=[json.loads(x)for x in raw.splitlines()];obs=s['sampled_observations'];need(len(samples)==obs['samples']==68,'ALL_68_SAMPLES_PRESENT')
need(all(not x['errors'] for x in samples),'SAMPLE_READ_ERRORS_ZERO')
for fs in ['/dev/shm','/workspace','/tmp']:
 rows=[r['filesystems'][fs] for r in samples];v=obs['filesystems'][fs]
 need(v['minimum_sampled_free_bytes']==min(r['free_bytes']for r in rows),'RECOMPUTED_MIN_FREE:'+fs)
 need(v['maximum_sampled_filesystem_used_bytes']==max(r['total_bytes']-r['free_bytes']for r in rows),'RECOMPUTED_MAX_SHARED_USED:'+fs)
need(obs['maximum_sampled_cgroup_memory_bytes']==max(r['memory.current']for r in samples),'RECOMPUTED_MAX_CGROUP')
need(obs['maximum_observed_gap_seconds']==max(b['monotonic']-a['monotonic']for a,b in zip(samples,samples[1:])),'RECOMPUTED_MAX_SAMPLE_GAP')
need(all(r['memory.events']['oom']==r['memory.events']['oom_kill']==0 for r in samples),'NO_OBSERVED_OOM_OR_OOM_KILL')
for k in ['before','after']:
 own=j(B/f'sampled/documents/OWN_{k.upper()}.json');need(own==s['own_'+k],'ENDPOINT_INVENTORY_ORIGINAL_'+k);need(own['unique_allocated_bytes']==sum(r['unique_allocated_bytes']for r in own['roots']),'ENDPOINT_SUM_'+k)
need(s['startup_planning_increment_bytes']==416*1024**2 and s['startup_planned_total_bytes']==s['own_before']['unique_allocated_bytes']+416*1024**2<=2*1024**3,'STARTUP_ONLY_CAPACITY_ORIGINAL_PASS')
stdout=read(wp.parent/'steps/03.stdout').decode();lines=[x for x in stdout.splitlines()if x.startswith('DOCUMENTS_RESULT ')];need(len(lines)==1,'ONE_DOCUMENTS_RESULT');cdp=json.loads(lines[0][len('DOCUMENTS_RESULT '):])
need(cdp['passedAssertions']==47 and cdp['failedAssertions']==0,'ORIGINAL_47_ASSERTIONS_ZERO_FAILED')
need(sum(x.startswith('PASS ') for x in stdout.splitlines())==47,'ALL_47_ORIGINAL_PASS_LINES')
need(cdp['viewport']==[1400,900,390,844],'ORIGINAL_DESKTOP_MOBILE_VIEWPORTS')
for line in ['PASS all reading actions preserve scene','PASS unsaved drafts and undo history preserved','PASS local documents and case metadata make no remote requests','PASS no uncaught browser exceptions','PASS no failed asset requests']:
 need(line in stdout.splitlines(),'ORIGINAL_ASSERTION:'+line)
screens={k:v for k,v in w['files'].items()if k.endswith('.png')};need(len(screens)==8 and sum('desktop' in k for k in screens)==4 and sum('mobile' in k for k in screens)==4,'EIGHT_ORIGINAL_HASHED_SCREENSHOTS_4_DESKTOP_4_MOBILE')
q=j(B/'requests/documents.json');need(q['storage']==str(B/'r/d') and q['source_sha']==F,'FRESH_SHORT_DOCUMENTS_STORAGE')
p=j(q['source_preparation']['path']);need(pins[q['source_preparation']['path']]==q['source_preparation']['sha256'] and p['actual_process_returncode']==0 and p['source_sha']==F and not p['timeout_expired'],'ORIGINAL_MATERIALIZE_ZERO_BOUND')
need(w['workflow_sha256']=='b491142a6767e78588710f90bf0ea03b9b5af9ef6eb851cd9e28d32f0c262d6d','UNCHANGED_ORIGINAL_WORKFLOW_PIN')
paths=[]
for job,storage in [('assembly','r/a2'),('documents','r/d'),('grid','r/g'),('space','r/s'),('timber','r/t'),('assembly-old','runs/assembly')]:
 suite='assembly'if job=='assembly-old'else job;p=B/storage/'tmp/original'/suite/'com.google.Chrome.ABCDEF/SingletonSocket';n=len(str(p).encode());paths.append(dict(job=job,path=str(p),utf8_path_bytes=n,with_terminating_NUL_bytes=n+1,below_108_with_NUL=n+1<108))
need(all(r['below_108_with_NUL']for r in paths[:-1]) and not paths[-1]['below_108_with_NUL'],'SHORT_LITERAL_PATHS_PASS_OLD_FAIL')
mounts=s['mountinfo_before'];need(any(' /dev/shm 'in m and ' - tmpfs 'in m for m in mounts),'ORIGINAL_SHM_TMPFS_MOUNT_RECORDED')
result={'schema':'geo337-F9-documents-SHM-formal-and-sampler-actual-peer/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha':F,'exit_code':0,'checks':len(checks),'blocking_findings':[],'original_formal_exit':0,'formal_status':'GREEN_ORIGINAL_FULL_DOCUMENTS_JOB; not yet remote delivered','original_DOCUMENTS_result':cdp,'assertions':{'passed':47,'failed':0,'viewports':cdp['viewport'],'scene_and_unsaved_state_preserved':True},'original_screenshots':screens,'original_seconds':w['seconds'],'original_ci_minutes':w['ci_timeout_minutes'],'original_argv_full_streams_checked':len(s['commands'])+len(l['commands']),'original_workflow_files_checked':len(w['files']),'raw_metadata_bytes_read':nbytes,'pins':pins,'sampled_observations_recomputed':obs,'own_before':s['own_before'],'own_after':s['own_after'],'mountinfo_at_original_launch':mounts,'short_storage_literal_paths':paths,'correction_of_initial_chat_arithmetic':'Initial base+40 calculation omitted one slash separator. Full literal UTF8 is104/104/99/100/101; includingNUL105/105/100/101/102. Original path113/NUL114. Prior original files unchanged.','next_change_scope':'Root changes only fresh request storage/output names to approved exactOWN short paths; original source plan/launcher/driver/CI/golden/ports unchanged. New run must succeed independently; first environment red retained.','limits':['Only formally require_escalated read of terminal metadata/raw; no SHM writes, source or payload scan, no tests/guards rerun.','Sampler peaks are sampled shared mount/cgroup values, not continuous or this-job-only peaks; no R8 inference.','Endpoint OWN inventories compared to original recorded sums, not rewalked during active r2.','Assembly first attempt remains a separate environment red; this is the distinct documents job.','Remote publication/full archive verification remains separate.'],'check_details':checks}
p=O/'REVIEW.json';need(not p.exists(),'FRESH_PEER_OUTPUT');p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'checks':result['checks'],'exit_code':0,'original_formal_exit':0,'sampled_shared_SHM_max':obs['filesystems']['/dev/shm']['maximum_sampled_filesystem_used_bytes']}))
