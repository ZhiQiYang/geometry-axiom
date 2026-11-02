from pathlib import Path
import datetime,hashlib,json
B=Path('/dev/shm/geo337-F9-browsers-20261025');O=Path('/workspace/geo337-F9-space-SHM-actual-peer-20261025');F='4f8a794f4167c3562eb182045102e86e9e37cca9'
checks=[];pins={};nbytes=0
def need(v,m):
 checks.append({'check':m,'passed':bool(v)});assert v,m
def read(p):
 global nbytes
 p=Path(p);need(not p.is_symlink(),'REGULAR_METADATA:'+str(p));r=p.read_bytes();nbytes+=len(r);pins[str(p)]=hashlib.sha256(r).hexdigest();return r
def j(p):return json.loads(read(p))
s=j(B/'sampled/space/RESULT.json');l=j(B/'launches/space/receipt.json');wp=B/'r/s/original/space/receipt.json';w=j(wp);host=j('/workspace/geo337-F9-space-SHM-EXEC_FINAL-20261025.json')
need(s['source_sha']==l['source_sha']==w['sha']==F,'F9_ONE_SOURCE_IDENTITY');need(s['job']==l['job']==w['job']=='space','ONE_SPACE_JOB')
need(s['original_process_returncode']==s['wrapper_exit']==l['original_primary_exit']==l['wrapper_exit']==w['exit_code']==host['actual_tool_result']['exit_code']==0,'TRUE_ORIGINAL_AND_HOST_EXIT_0')
need(s['original_passed'] and l['passed'],'ORIGINAL_PASS_TRUE');need(not w['over_ci_timeout'] and w['ci_timeout_minutes']==15 and w['watchdog_factor']==3,'UNCHANGED_CI_NOT_TIMEOUT')
need(not s['errors'] and not s['sampling_errors'] and s['sampling_complete'] and not l['errors'],'RECORDER_NO_CONCEALMENT_ERRORS')
need(l['before_guard']['actual_process_returncode']==l['after_guard']['actual_process_returncode']==0,'ORIGINAL_BEFORE_AFTER_GUARDS_ZERO')
need(w['checkout_after']['head']==F and not w['checkout_after']['status'],'ORIGINAL_SOURCE_AFTER_CLEAN_RECORD')
need(s['original_receipt_sha256']==pins[str(B/'launches/space/receipt.json')],'SAMPLER_TO_LAUNCHER_PIN');need(l['original_receipt_sha256']==pins[str(wp)],'LAUNCHER_TO_WORKFLOW_PIN')
for row in s['commands']+l['commands']:
 need(row['source_sha']==F and row['acceptance_sha']==F and not row['timeout_expired'],'CAPTURE_IDENTITY_AND_NO_TIMEOUT')
 d=Path(row['directory']);rr=j(d/'result.json');need(rr==row,'CAPTURE_ORIGINAL_RESULT_EXACT')
 for name in ['stdout','stderr']:
  b=read(d/(name+'.bin'));need(len(b)==row[name+'_bytes'] and hashlib.sha256(b).hexdigest()==row[name+'_sha256'],'CAPTURE_COMPLETE_'+name)
for rel,meta in w['files'].items():
 p=wp.parent/rel;need(p.is_relative_to(wp.parent) and '..' not in Path(rel).parts,'ORIGINAL_WORKFLOW_FILE_SCOPE');b=read(p);need(len(b)==meta['bytes'] and hashlib.sha256(b).hexdigest()==meta['sha256'],'ORIGINAL_WORKFLOW_FILE_EXACT:'+rel)
raw=read(B/'sampled/space/SAMPLES.jsonl');samples=[json.loads(x)for x in raw.splitlines()];obs=s['sampled_observations'];need(len(samples)==obs['samples']==214,'ALL_214_SAMPLES_PRESENT')
need(all(not x['errors'] for x in samples),'SAMPLE_READ_ERRORS_ZERO')
for fs in ['/dev/shm','/workspace','/tmp']:
 rows=[r['filesystems'][fs] for r in samples];v=obs['filesystems'][fs]
 need(v['minimum_sampled_free_bytes']==min(r['free_bytes']for r in rows),'RECOMPUTED_MIN_FREE:'+fs)
 need(v['maximum_sampled_filesystem_used_bytes']==max(r['total_bytes']-r['free_bytes']for r in rows),'RECOMPUTED_MAX_SHARED_USED:'+fs)
need(obs['maximum_sampled_cgroup_memory_bytes']==max(r['memory.current']for r in samples),'RECOMPUTED_MAX_CGROUP')
need(obs['maximum_observed_gap_seconds']==max(b['monotonic']-a['monotonic']for a,b in zip(samples,samples[1:])),'RECOMPUTED_MAX_SAMPLE_GAP')
need(all(r['memory.events']['oom']==r['memory.events']['oom_kill']==0 for r in samples),'NO_OBSERVED_OOM_OR_OOM_KILL')
for k in ['before','after']:
 own=j(B/f'sampled/space/OWN_{k.upper()}.json');need(own==s['own_'+k],'ENDPOINT_INVENTORY_ORIGINAL_'+k);need(own['unique_allocated_bytes']==sum(r['unique_allocated_bytes']for r in own['roots']),'ENDPOINT_SUM_'+k)
need(s['startup_planning_increment_bytes']==416*1024**2 and s['startup_planned_total_bytes']==s['own_before']['unique_allocated_bytes']+416*1024**2<=2*1024**3,'STARTUP_ONLY_CAPACITY_ORIGINAL_PASS')
stdout=read(wp.parent/'steps/03.stdout').decode();lines=[x for x in stdout.splitlines()if x.startswith('SPACE_RESULT ')];need(len(lines)==1,'ONE_SPACE_RESULT');suite=json.loads(lines[0][len('SPACE_RESULT '):])
need(suite['completed'] and suite['passed']==242 and suite['failed']==0,'ORIGINAL_242_ASSERTIONS_ZERO_FAILED')
expected={'setup':2,'space-height-library':112,'projection-lifecycle':18,'projection-placement':36,'font-layout':19,'space-flow':39,'projection-close':14,'browser-health':2}
need(set(suite['groups'])==set(expected),'ORIGINAL_GROUP_SET')
for k,n in expected.items():need(suite['groups'][k]=={'expected':n,'passed':n,'failed':0,'completed':True},'ORIGINAL_COMPLETE_GROUP:'+k)
need(sum(x['passed']for x in suite['groups'].values())==suite['passed'] and sum(line.startswith('PASS ')for line in stdout.splitlines())==242,'ALL_242_ORIGINAL_PASS_LINES_GROUP_SUM')
need(suite['completenessProblems']==suite['exceptions']==suite['consoleErrors']==[],'NO_COMPLETENESS_EXCEPTIONS_CONSOLE_ERRORS')
need(suite['scope']['mode']=='full-space-suite' and suite['scope']['filters']==[] and suite['scope']['omitted']==['timber-material','timber-source-guards'],'ORIGINAL_FULL_SPACE_SCOPE_SEPARATE_TIMBER')
need(suite['scope']['included']==['space-height-library','projection-lifecycle','projection-placement','font-layout','space-flow','projection-close'],'ORIGINAL_SIX_INCLUDED_GROUPS')
need(suite['scope']['url']=='http://127.0.0.1:19085/','ORIGINAL_SPACE_HTTP_PORT')
q=j(B/'requests/space.json');need(q['storage']==str(B/'r/s') and q['source_sha']==F,'FRESH_SHORT_SPACE_STORAGE')
need(pins[str(B/'requests/space.json')]==host['request_sha256']==l['request_sha256'],'ORIGINAL_REQUEST_HASH_CHAIN')
need(s['request_sha256']==host['sampled_request_sha256'],'SAMPLER_REQUEST_HOST_CHAIN')
p=j(q['source_preparation']['path']);need(pins[q['source_preparation']['path']]==q['source_preparation']['sha256'] and p['actual_process_returncode']==0 and p['source_sha']==F and not p['timeout_expired'],'ORIGINAL_MATERIALIZE_ZERO_BOUND')
need(w['workflow_sha256']=='b491142a6767e78588710f90bf0ea03b9b5af9ef6eb851cd9e28d32f0c262d6d','UNCHANGED_ORIGINAL_WORKFLOW_PIN')
need(w['driver_sha256']=='4cdfe3dd250bc9bba6f8e8a513bbd2007176dc914b60b034b2aa7761e295affd','ORIGINAL_SHM_DRIVER_PIN')
need(all(r['actual_process_returncode']==0 for r in s['commands']+l['commands']),'ALL_ORIGINAL_SUBCOMMAND_EXITS_ZERO')
need(w['seconds']<15*60,'ORIGINAL_CI_DURATION_15_MINUTES')
socket=str(B/'r/s/tmp/original/space/com.google.Chrome.ABCDEF/SingletonSocket');need(len(socket.encode())==100 and len(socket.encode())+1<108,'FULL_LITERAL_SOCKET_100_PLUS_NUL_SAFE')
mounts=s['mountinfo_before'];need(any(' /dev/shm 'in m and ' - tmpfs 'in m for m in mounts),'ORIGINAL_SHM_TMPFS_MOUNT_RECORDED')
summary=[x for x in stdout.splitlines()if x.startswith('RESULT 242 passed / 0 failed; completed: true; scope: full-space-suite;')];need(len(summary)==1,'ORIGINAL_HUMAN_RESULT_EXACT')
artifact=Path(summary[0].split('; artifacts: ',1)[1]);need(artifact.is_relative_to(B/'r/s/tmp/original/space') and artifact.is_dir() and not artifact.is_symlink(),'CLOSED_SUITE_ARTIFACT_DIRECTORY_PRESENT')
result={'schema':'geo337-F9-space-SHM-formal-and-sampler-actual-peer/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha':F,'exit_code':0,'checks':len(checks),'blocking_findings':[],'original_formal_exit':0,'formal_status':'GREEN_ORIGINAL_FULL_SPACE_JOB; remote delivery separate','original_SPACE_result':suite,'assertions':{'passed':242,'failed':0,'groups':suite['groups']},'reported_suite_artifact_directory':str(artifact),'original_seconds':w['seconds'],'original_ci_minutes':w['ci_timeout_minutes'],'original_argv_full_streams_checked':len(s['commands'])+len(l['commands']),'original_workflow_files_checked':len(w['files']),'raw_metadata_bytes_read':nbytes,'pins':pins,'sampled_observations_recomputed':obs,'own_before':s['own_before'],'own_after':s['own_after'],'mountinfo_at_original_launch':mounts,'socket_literal':{'path':socket,'bytes':100,'including_NUL':101},'limits':['Only formally require_escalated read of terminal space metadata/raw; no SHM writes, source or active timber scan, no tests/guards rerun.','Sampler peaks are sampled shared mount/cgroup values, not continuous or this-job-only peaks; no R8 or P189 inference.','Endpoint OWN inventories compared to original recorded sums, not rewalked.','Original space scope omits the two timber groups; timber is its own formal job, never claimed covered here.','Workflow file manifest40 and reported suite artifact-directory presence checked. Extra per-test artifact payloads are for full terminal collector, not recursively scanned by this lightweight peer.','Complete archive roundtrip, normal publication, and remote full blob hash confirmation remain separate.'],'check_details':checks}
p=O/'REVIEW.json';need(not p.exists(),'FRESH_PEER_OUTPUT');p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'checks':result['checks'],'exit_code':0,'original_formal_exit':0,'sampled_shared_SHM_max':obs['filesystems']['/dev/shm']['maximum_sampled_filesystem_used_bytes']}))
