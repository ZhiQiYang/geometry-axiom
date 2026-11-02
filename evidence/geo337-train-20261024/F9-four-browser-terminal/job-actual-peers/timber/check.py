from pathlib import Path
import datetime,hashlib,json
B=Path('/dev/shm/geo337-F9-browsers-20261025');O=Path('/worktimber/geo337-F9-timber-SHM-actual-peer-20261025');F='4f8a794f4167c3562eb182045102e86e9e37cca9'
checks=[];pins={};nbytes=0
def need(v,m):
 checks.append({'check':m,'passed':bool(v)});assert v,m
def read(p):
 global nbytes
 p=Path(p);need(not p.is_symlink(),'REGULAR_METADATA:'+str(p));r=p.read_bytes();nbytes+=len(r);pins[str(p)]=hashlib.sha256(r).hexdigest();return r
def j(p):return json.loads(read(p))
s=j(B/'sampled/timber/RESULT.json');l=j(B/'launches/timber/receipt.json');wp=B/'r/t/original/timber/receipt.json';w=j(wp);host=j('/worktimber/geo337-F9-timber-SHM-EXEC_FINAL-20261025.json')
need(s['source_sha']==l['source_sha']==w['sha']==F,'F9_ONE_SOURCE_IDENTITY');need(s['job']==l['job']==w['job']=='timber','ONE_TIMBER_JOB')
need(s['original_process_returncode']==s['wrapper_exit']==l['original_primary_exit']==l['wrapper_exit']==w['exit_code']==host['actual_tool_result']['exit_code']==0,'TRUE_ORIGINAL_AND_HOST_EXIT_0')
need(s['original_passed'] and l['passed'],'ORIGINAL_PASS_TRUE');need(not w['over_ci_timeout'] and w['ci_timeout_minutes']==20 and w['watchdog_factor']==3,'UNCHANGED_CI_NOT_TIMEOUT')
need(not s['errors'] and not s['sampling_errors'] and s['sampling_complete'] and not l['errors'],'RECORDER_NO_CONCEALMENT_ERRORS')
need(l['before_guard']['actual_process_returncode']==l['after_guard']['actual_process_returncode']==0,'ORIGINAL_BEFORE_AFTER_GUARDS_ZERO')
need(w['checkout_after']['head']==F and not w['checkout_after']['status'],'ORIGINAL_SOURCE_AFTER_CLEAN_RECORD')
need(s['original_receipt_sha256']==pins[str(B/'launches/timber/receipt.json')],'SAMPLER_TO_LAUNCHER_PIN');need(l['original_receipt_sha256']==pins[str(wp)],'LAUNCHER_TO_WORKFLOW_PIN')
for row in s['commands']+l['commands']:
 need(row['source_sha']==F and row['acceptance_sha']==F and not row['timeout_expired'],'CAPTURE_IDENTITY_AND_NO_TIMEOUT')
 d=Path(row['directory']);rr=j(d/'result.json');need(rr==row,'CAPTURE_ORIGINAL_RESULT_EXACT')
 for name in ['stdout','stderr']:
  b=read(d/(name+'.bin'));need(len(b)==row[name+'_bytes'] and hashlib.sha256(b).hexdigest()==row[name+'_sha256'],'CAPTURE_COMPLETE_'+name)
for rel,meta in w['files'].items():
 p=wp.parent/rel;need(p.is_relative_to(wp.parent) and '..' not in Path(rel).parts,'ORIGINAL_WORKFLOW_FILE_SCOPE');b=read(p);need(len(b)==meta['bytes'] and hashlib.sha256(b).hexdigest()==meta['sha256'],'ORIGINAL_WORKFLOW_FILE_EXACT:'+rel)
raw=read(B/'sampled/timber/SAMPLES.jsonl');samples=[json.loads(x)for x in raw.splitlines()];obs=s['sampled_observations'];need(len(samples)==obs['samples']==129,'ALL_129_SAMPLES_PRESENT')
need(all(not x['errors'] for x in samples),'SAMPLE_READ_ERRORS_ZERO')
for fs in ['/dev/shm','/worktimber','/tmp']:
 rows=[r['filesystems'][fs] for r in samples];v=obs['filesystems'][fs]
 need(v['minimum_sampled_free_bytes']==min(r['free_bytes']for r in rows),'RECOMPUTED_MIN_FREE:'+fs)
 need(v['maximum_sampled_filesystem_used_bytes']==max(r['total_bytes']-r['free_bytes']for r in rows),'RECOMPUTED_MAX_SHARED_USED:'+fs)
need(obs['maximum_sampled_cgroup_memory_bytes']==max(r['memory.current']for r in samples),'RECOMPUTED_MAX_CGROUP')
need(obs['maximum_observed_gap_seconds']==max(b['monotonic']-a['monotonic']for a,b in zip(samples,samples[1:])),'RECOMPUTED_MAX_SAMPLE_GAP')
need(all(r['memory.events']['oom']==r['memory.events']['oom_kill']==0 for r in samples),'NO_OBSERVED_OOM_OR_OOM_KILL')
for k in ['before','after']:
 own=j(B/f'sampled/timber/OWN_{k.upper()}.json');need(own==s['own_'+k],'ENDPOINT_INVENTORY_ORIGINAL_'+k);need(own['unique_allocated_bytes']==sum(r['unique_allocated_bytes']for r in own['roots']),'ENDPOINT_SUM_'+k)
need(s['startup_planning_increment_bytes']==416*1024**2 and s['startup_planned_total_bytes']==s['own_before']['unique_allocated_bytes']+416*1024**2<=2*1024**3,'STARTUP_ONLY_CAPACITY_ORIGINAL_PASS')
stdout=read(wp.parent/'steps/03.stdout').decode();lines=[x for x in stdout.splitlines()if x.startswith('SPACE_RESULT ')];need(len(lines)==1,'ONE_ORIGINAL_SPACE_RESULT_FOR_TIMBER');suite=json.loads(lines[0][len('SPACE_RESULT '):])
need(suite['completed'] and suite['passed']==79 and suite['failed']==0,'ORIGINAL_79_ASSERTIONS_ZERO_FAILED')
expected={'setup':2,'timber-material':48,'timber-source-guards':8,'font-layout':19,'browser-health':2}
need(set(suite['groups'])==set(expected),'ORIGINAL_GROUP_SET_TWO_TIMBER_PLUS_FONT_SETUP_HEALTH')
for k,n in expected.items():need(suite['groups'][k]=={'expected':n,'passed':n,'failed':0,'completed':True},'ORIGINAL_COMPLETE_GROUP:'+k)
need(sum(x['passed']for x in suite['groups'].values())==suite['passed'] and sum(line.startswith('PASS ')for line in stdout.splitlines())==79,'ALL_79_ORIGINAL_PASS_LINES_GROUP_SUM')
need(suite['completenessProblems']==suite['exceptions']==suite['consoleErrors']==[],'NO_COMPLETENESS_EXCEPTIONS_CONSOLE_ERRORS')
need(suite['scope']['mode']=='partial' and suite['scope']['filters']==['GEOMETRY_TIMBER_ONLY'] and suite['scope']['omitted']==['space-height-library','projection-lifecycle','projection-placement','space-flow','projection-close'],'ORIGINAL_TIMBER_ONLY_SCOPE_AND_OMISSIONS')
need(suite['scope']['included']==['timber-material','timber-source-guards','font-layout'],'ORIGINAL_TWO_TIMBER_GROUPS_PLUS_FONT_INCLUDED')
need(suite['scope']['url']=='http://127.0.0.1:19086/','ORIGINAL_TIMBER_HTTP_PORT')
q=j(B/'requests/timber.json');need(q['storage']==str(B/'r/t') and q['source_sha']==F,'FRESH_SHORT_TIMBER_STORAGE')
need(pins[str(B/'requests/timber.json')]==host['request_sha256']==l['request_sha256'],'ORIGINAL_REQUEST_HASH_CHAIN')
need(s['request_sha256']==host['sampled_request_sha256'],'SAMPLER_REQUEST_HOST_CHAIN')
p=j(q['source_preparation']['path']);need(pins[q['source_preparation']['path']]==q['source_preparation']['sha256'] and p['actual_process_returncode']==0 and p['source_sha']==F and not p['timeout_expired'],'ORIGINAL_MATERIALIZE_ZERO_BOUND')
need(w['workflow_sha256']=='b491142a6767e78588710f90bf0ea03b9b5af9ef6eb851cd9e28d32f0c262d6d','UNCHANGED_ORIGINAL_WORKFLOW_PIN')
need(w['driver_sha256']=='4cdfe3dd250bc9bba6f8e8a513bbd2007176dc914b60b034b2aa7761e295affd','ORIGINAL_SHM_DRIVER_PIN')
need(all(r['actual_process_returncode']==0 for r in s['commands']+l['commands']),'ALL_ORIGINAL_SUBCOMMAND_EXITS_ZERO')
need(w['seconds']<20*60,'ORIGINAL_CI_DURATION_20_MINUTES')
socket=str(B/'r/t/tmp/original/timber/com.google.Chrome.ABCDEF/SingletonSocket');need(len(socket.encode())==101 and len(socket.encode())+1<108,'FULL_LITERAL_SOCKET_101_PLUS_NUL_SAFE')
mounts=s['mountinfo_before'];need(any(' /dev/shm 'in m and ' - tmpfs 'in m for m in mounts),'ORIGINAL_SHM_TMPFS_MOUNT_RECORDED')
summary=[x for x in stdout.splitlines()if x.startswith('RESULT 79 passed / 0 failed; completed: true; scope: partial;')];need(len(summary)==1,'ORIGINAL_HUMAN_RESULT_EXACT')
artifact=Path(summary[0].split('; artifacts: ',1)[1]);need(artifact.is_relative_to(B/'r/t/tmp/original/timber') and artifact.is_dir() and not artifact.is_symlink(),'CLOSED_SUITE_ARTIFACT_DIRECTORY_PRESENT')
result={'schema':'geo337-F9-timber-SHM-formal-and-sampler-actual-peer/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha':F,'exit_code':0,'checks':len(checks),'blocking_findings':[],'original_formal_exit':0,'formal_status':'GREEN_ORIGINAL_FULL_TIMBER_WORKFLOW_JOB; remote delivery separate','original_SPACE_result':suite,'assertions':{'passed':79,'failed':0,'groups':suite['groups']},'reported_suite_artifact_directory':str(artifact),'original_seconds':w['seconds'],'original_ci_minutes':w['ci_timeout_minutes'],'original_argv_full_streams_checked':len(s['commands'])+len(l['commands']),'original_workflow_files_checked':len(w['files']),'raw_metadata_bytes_read':nbytes,'pins':pins,'sampled_observations_recomputed':obs,'own_before':s['own_before'],'own_after':s['own_after'],'mountinfo_at_original_launch':mounts,'socket_literal':{'path':socket,'bytes':101,'including_NUL':102},'limits':['Only formally require_escalated read of terminal timber metadata/raw; no SHM writes, no NATIVE/source reads, no tests/guards rerun.','Sampler peaks are sampled shared mount/cgroup values, not continuous or this-job-only peaks; no R8 or P189 inference.','Endpoint OWN inventories compared to original recorded sums, not rewalked.','Original GEOMETRY_TIMBER_ONLY scope includes two timber groups plus font-layout/setup/health; five separate space groups intentionally omitted per original workflow, never claimed covered here.','Workflow file manifest40 and reported suite artifact-directory presence checked. Extra per-test artifact payloads are for full terminal collector, not recursively scanned by this lightweight peer.','Complete archive roundtrip, normal publication, and remote full blob hash confirmation remain separate.'],'check_details':checks}
p=O/'REVIEW.json';need(not p.exists(),'FRESH_PEER_OUTPUT');p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'checks':result['checks'],'exit_code':0,'original_formal_exit':0,'sampled_shared_SHM_max':obs['filesystems']['/dev/shm']['maximum_sampled_filesystem_used_bytes']}))
