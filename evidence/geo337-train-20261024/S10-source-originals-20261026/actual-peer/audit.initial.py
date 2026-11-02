from pathlib import Path
import collections,datetime,gzip,hashlib,io,json,os,stat,sys,tarfile

OUT=Path(__file__).parent
BASE=Path('/dev/shm/geometry-axiom-geo337-20261025')
PKG=BASE/'geo337-S10-closed-original-package-20261026'
OUTER=BASE/'S10-closed-collection-root-original-20261026'
SOURCE='82c922a3941525d3a094ac0158bdc7dea57ea360'
DEST='evidence/geo337-train-20261024/S10-source-originals-20261026'
COUNT=0;FAIL=[]
def H(x):return hashlib.sha256(x).hexdigest()
def read(p):return json.loads(p.read_bytes())
def ck(v,label):
 global COUNT
 COUNT+=1
 if not v:FAIL.append(label)
def pin(p,h):ck(H(p.read_bytes())==h,'pin '+str(p))

request=read(PKG/'BOUND_REQUEST.json');result=read(PKG/'RESULT.json');inventory=read(PKG/'ORIGINAL_INVENTORY.json');parts=read(PKG/'ORIGINAL_PARTS.json');before=read(PKG/'ORIGINAL_RESULT.json')
pin(PKG/'COLLECTOR.py.txt','a0f8f4b37db678ced028297f52f8294daa339a2a9340d076dbdf047a5d8513a1')
pin(PKG/'ORIGINAL_INVENTORY.json','6a5d9a92aa8a32edfa16faec30c34b44cd378ebafe69bcdb16e9c63959d572a9')
pin(PKG/'ORIGINAL_PARTS.json','64037b6dd69ad57602383dad5fa5896949feb37a27a677302daa8296b713063e')
pin(PKG/'INDEPENDENT_STATIC_PEER.json','9fee31077be01107f4c6167fc38091bb0e2d69720c6b8ea77ed5c85054fe2dff')
ck(read(PKG/'INDEPENDENT_STATIC_PEER.json')['exit_code']==0,'static peer zero')
ck(before['inventory_exit']==0,'inventory original preparation zero')
ck(result['collection_exit']==read(OUTER/'RESULT.json')['exit_code']==0,'collection and root terminal zero')
ck(result['errors']==[] and result['source_sha']==inventory['source_sha']==request['source_sha']==SOURCE,'collection source/no errors')
ck((PKG/'BOUND_REQUEST.json').read_bytes()==(OUTER/'ROOT_REQUEST.json').read_bytes(),'request exact outer binding')
ck(request['root_execution_lease'] and request['execute'] and request['current_execution_admitted'],'root leases explicit true')
ck(result['subject_rerun'] is False and result['performance_rerun'] is False,'no product/performance rerun claim')
ck(inventory['subject_rerun'] is False and inventory['oracle_revalidated'] is False and inventory['active_source_or_cache_read'] is False,'inventory scoped closed originals')
ck(result['published'] is False and result['remote_hash_verified'] is False and result['delivered'] is False,'does not claim remote delivery')
ck(result['storage_is_volatile'] is True,'volatile storage disclosed')
ck(len(parts)==len(result['parts'])==1,'single full package part')
rawarchive=PKG/'ORIGINAL_S10_CLOSED_PART1.tar.gz'
pin(rawarchive,'b23b3662c4f35d59c047ad138e5e843ec1ac79bcb2fde2b9062d5fc521ac8305')
ck(rawarchive.stat().st_size==4072619==result['parts'][0]['archive_bytes'],'archive exact byte size')
uncompressed=gzip.decompress(rawarchive.read_bytes())
ck(len(uncompressed)==24401920==result['parts'][0]['decompressed_tar_bytes'],'full gzip CRC and tar length')
payload={};metadata={}
with tarfile.open(fileobj=io.BytesIO(uncompressed),mode='r:')as tar:
 for member in tar:
  name=member.name
  ck(name not in payload,'unique tar member '+name)
  ck(member.isfile() and not member.issym() and not member.islnk(),'regular tar member '+name)
  ck(not Path(name).is_absolute() and '..'not in Path(name).parts,'safe archive member '+name)
  f=tar.extractfile(member);data=f.read()if f else b''
  ck(len(data)==member.size,'complete member '+name)
  payload[name]=data;metadata[name]=member
ck(len(payload)==1214==result['regular_files']==before['inventory_regular_files'],'exact1214 members')
ck(sum(map(len,payload.values()))==23510881==result['regular_bytes']==before['inventory_regular_bytes'],'exact23510881 logical bytes')
ck(parts[0]['members_exact']==list(payload),'ordered member set exact PARTS')
expected={};original_roots=inventory['roots'];roots_members=collections.Counter()
for rec in inventory['records']:
 root,rel,kind,size,sha,state,target=rec
 rootinfo=original_roots[root];name=rootinfo['prefix']+'/'+rel
 ck(name not in expected,'unique inventory member '+name);expected[name]=rec
 ck(kind=='regular' and target is None,'only regular inventoried members '+name)
 ck(name in payload and len(payload.get(name,b''))==size and H(payload.get(name,b''))==sha,'inventory exact archived bytes '+name)
 src=Path(rootinfo['source_root'])/rel
 ck('F10-pool'not in src.parts and 'F10-cache'not in src.parts,'not live source/cache '+name)
 st=src.lstat();ck(stat.S_ISREG(st.st_mode),'original regular file '+name)
 ck(st.st_size==size and H(src.read_bytes())==sha,'closed original current bytes '+name)
 ck([st.st_dev,st.st_ino,st.st_mode,st.st_size,st.st_mtime_ns,st.st_nlink]==state,'original metadata state preserved '+name)
 roots_members[root]+=1
ck(set(expected)==set(payload),'full inventory no missing or extra archive members')
ck(sum(roots_members[x]for x in [0,1,2])==1112==result['original_closed_raw_regular_files'],'three raw roots complete1112')
for i,r in enumerate(original_roots):
 if r['selection']=='whole-tree':
  actual={p.relative_to(r['source_root']).as_posix()for p in Path(r['source_root']).rglob('*')if p.is_file()or p.is_symlink()}
 else:actual=set(r['exact_files'])
 ck(actual=={rec[1]for rec in inventory['records']if rec[0]==i},'scope complete '+r['prefix'])

def J(n):return json.loads(payload[n])
def stream_check(prefix,row):
 req=J(prefix+'/request.json');actual=J(prefix+'/result.json')
 ck(actual==row,'row/result exact '+prefix)
 for key,value in req.items():ck(value is None if key=='actual_process_returncode'else actual.get(key)==value,'request binding '+prefix+' '+key)
 for stream in ['stdin','stdout','stderr']:
  b=payload[prefix+'/'+stream+'.bin'];ck(H(b)==actual[stream+'_sha256'],'full stream hash '+prefix+' '+stream)
  if stream!='stdin':ck(len(b)==actual[stream+'_bytes'],'full stream length '+prefix+' '+stream)
 ck(actual['timeout_expired']is False,'no timeout '+prefix)
 ck(actual['ended_epoch']>=actual['started_epoch'],'times ordered '+prefix)
 return actual

sp=J('source-preparation/RESULT.json')
ck(sp['exit']==0 and sp['source_sha']==SOURCE and sp['formal_executed']is False,'actual sourceprep0 not formal test')
ck(len(sp['commands'])==342,'342 source Git original commands')
for i,row in enumerate(sp['commands'],1):
 prefix=f'source-preparation/commands/{i:04d}'
 ck(J(prefix+'/RESULT.json')==row,'original source row exact '+str(i))
 ck(row['exit']==0 and row['argv'][0]=='git' and row['source_sha']==SOURCE,'source Git actual0 '+str(i))
 ck(row['ended_epoch']>=row['started_epoch'],'source original timing '+str(i))
 for stream in ['stdout','stderr']:ck(H(payload[prefix+'/'+stream+'.bin'])==row[stream+'_sha256'],'source full '+stream+' '+str(i))
for scope in ['source-root-original','preledger-original']:
 rows=J(scope+'/subcommands.json')
 for i,row in enumerate(rows,1):stream_check(scope+'/subcommands/'+f'{i:06d}',row)
ck(len(J('source-root-original/subcommands.json'))==1,'source root original one command')
ck(J('source-root-original/RESULT.json')['exit_code']==0 and J('source-root-original/subcommands.json')[0]['actual_process_returncode']==0,'source wrapper actual0')
pre=J('preledger-original/RESULT.json');exits=[g['exit_code']for g in pre['gates']]
ck(exits==[1,0,0,0,0,0]==result['original_preledger_gate_exits'],'stale1 and other five0 retained')
ck(pre['all_gates_passed']is False and pre['full_native_executed']is False and pre['full123_executed']is False,'preledger true scope not inflated')
ck(pre['before']==pre['after'] and pre['source_unchanged']is True and pre['source_sha']==SOURCE,'original source identity')
for i,g in enumerate(pre['gates']):
 row=g['command'];ck(row['actual_process_returncode']==g['exit_code'],'gate exit truth '+str(i));ck(row['source_sha']==row['acceptance_sha']==SOURCE,'gate source '+str(i))
ck(len(J('preledger-original/subcommands.json'))==12,'preledger all12 commands')
for name,pinvalue,count in [('source-actual-peer/REVIEW.json','c01f6d7337297ad36f617eecf1c9067cbb4bf9ce53ba4dd942930c723d38c1ed',18498),('preledger-actual-peer/REVIEW.json','1f945f9e84d04fe74c807388dc95d4076ff6ad814ac35e2fb93ff465efbaafd3',198)]:
 ck(H(payload[name])==pinvalue,'accepted peer original exact '+name);d=J(name);ck(d['exit_code']==0 and d['checks']==count,'accepted original peer result '+name)
for name in ['host-and-reviewers/geo337-S10-source-preparation-EXEC_FINAL-20261025.json','host-and-reviewers/geo337-S10-preledger-checks-EXEC_FINAL-20261025.json']:ck(J(name)['exit_code']==0,'actual host zero '+name)
outer_rows=read(OUTER/'subcommands.json');ck(len(outer_rows)==1,'one collector outer command')
for row in outer_rows:
 folder=OUTER/'subcommands/000001';rr=read(folder/'result.json');rq=read(folder/'request.json');ck(row==rr,'outer row/result exact')
 ck(row['actual_process_returncode']==0 and row['timeout_expired']is False,'actual collector return0')
 ck(row['source_sha']==row['acceptance_sha']==SOURCE,'collector source binding')
 for k,v in rq.items():ck(v is None if k=='actual_process_returncode'else row.get(k)==v,'outer request '+k)
 for stream in ['stdin','stdout','stderr']:
  b=(folder/(stream+'.bin')).read_bytes();ck(H(b)==row[stream+'_sha256'],'outer full '+stream)
  if stream!='stdin':ck(len(b)==row[stream+'_bytes'],'outer bytes '+stream)
 ck(row['started_epoch']<=result['started_epoch']<=result['ended_epoch']<=row['ended_epoch'],'collector start/end within actual subprocess')
budget=read(PKG/'PART1_BUDGET.json');resources=read(OUTER/'RESOURCE_PLAN.json')
ck(budget['reserve_bytes']==67108864 and budget['required_fresh_bytes']==97710427,'original capacity figures retained')
ck(budget['admitted'] and budget['fresh_output_free']>=budget['required_fresh_bytes'],'actual fresh output admission')
ck(resources['combined_used_before']+resources['collection_increment_bound']+resources['concurrent_publication_reserved']<=resources['shared_ceiling']==2147483648,'shared2GiB complete reservation')
review={'schema':'geo337-S10-source-package-actual-review/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha':SOURCE,'exit_code':int(bool(FAIL)),'checks':COUNT,'blocking_findings':FAIL,'original_collection_exit':0,'original_source_preparation_exit':sp['exit'],'original_preledger_gate_exits':exits,'original_source_git_commands':len(sp['commands']),'original_preledger_commands':len(J('preledger-original/subcommands.json')),'archived_members':len(payload),'archived_logical_bytes':sum(map(len,payload.values())),'archive_bytes':rawarchive.stat().st_size,'archive_sha256':H(rawarchive.read_bytes()),'full_gzip_crc_verified':True,'all_members_original_bytes_reverified':not FAIL,'accepted_source_peer_checks':18498,'accepted_preledger_peer_checks':198,'accepted_oracle_peers_rerun':False,'active_source_cache_read':False,'formal_product_tests_rerun':False,'git_commands_executed':False,'package_modified':False,'publication_performed':False,'collection_started_utc':datetime.datetime.fromtimestamp(result['started_epoch'],datetime.timezone.utc).isoformat(),'collection_ended_utc':datetime.datetime.fromtimestamp(result['ended_epoch'],datetime.timezone.utc).isoformat(),'script_sha256':H(Path(__file__).read_bytes()),'limits':['Package integrity review only; the accepted source/oracle peer predicates were not reexecuted.','The original stale ledger exit1 remains a preledger failure; packaging exit0 does not change it.','Current archive storage is volatile and is not delivered until ordinary push and complete remote verification.','Source/execution identity remains S10; no later head relabelling.']}
(OUT/'REVIEW.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
files=[]
for root,part in [(PKG,'package'),(OUTER,'outer'),(OUT,'actual-peer')]:
 for p in sorted(root.rglob('*')):
  if p.is_file()and p.name not in ['PUBLICATION_FILES.json','SUMS.sha256']:
   files.append({'source_path':str(p),'destination':DEST+'/'+part+'/'+p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':H(p.read_bytes())})
manifest={'schema':'geo337-S10-source-complete-package-publication-input/1','source_sha':SOURCE,'publisher_expected_parent':'ROOT_MUST_BIND_CURRENT_HEAD','files':files,'archived_members':len(payload),'original_gate_exits':exits,'published':False,'remote_hash_verified':False,'delivered':False}
(OUT/'PUBLICATION_FILES.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(OUT/'SUMS.sha256').write_text(''.join(H(p.read_bytes())+'  '+p.name+'\n'for p in sorted(OUT.iterdir())if p.is_file()and p.name!='SUMS.sha256'))
written=sum(p.stat().st_size for p in OUT.iterdir()if p.is_file())
assert written<=131072
print(json.dumps({'exit_code':review['exit_code'],'checks':COUNT,'failures':FAIL,'review_sha256':H((OUT/'REVIEW.json').read_bytes()),'manifest_sha256':H((OUT/'PUBLICATION_FILES.json').read_bytes()),'files':len(files),'payload_bytes':sum(x['bytes']for x in files),'new_bytes':written},ensure_ascii=False))
sys.exit(review['exit_code'])
