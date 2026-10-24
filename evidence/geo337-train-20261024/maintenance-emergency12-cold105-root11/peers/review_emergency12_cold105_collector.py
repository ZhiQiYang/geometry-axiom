from pathlib import Path
import ast,hashlib,json,stat
O=Path('/workspace/train337-canvas-peer-resume');N=Path('/workspace/collect_emergency_twelve_and_cold105_originals_20261024.py');P=Path('/workspace/collect_four_additional_archive_groups_originals_20261024.py');checks=0;findings=[]
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def j(p):return json.loads(Path(p).read_text())
def ck(v,n):
 global checks
 checks+=1
 if not v:findings.append(n)
new=N.read_text();old=P.read_text();ck(h(N)=='af535a120f4250510a43249cdc3fcd5f2c9b5e7069a46022af0e8c490a004802','final collector pin')
ck(h(P)=='dcb9f8adf69e3485c56858a366aa2167d7a2b3df91d0bc97ae9d5ac03464427b','prior original collector exactpin')
def functions(s):return {n.name:ast.dump(n,include_attributes=False) for n in ast.walk(ast.parse(s)) if isinstance(n,ast.FunctionDef)}
a,b=functions(new),functions(old)
for name in ['digest','readj','dump','add','tree']:ck(a[name]==b[name],'unchanged original helper AST '+name)
start=" with tarfile.open(archive,'w:gz',compresslevel=1) as tar:";end=' result=dict('
ck(new[new.index(start):new.index(end)]==old[old.index(start):old.index(end)],'entire original write/full-member-hash/roundtrip/post-original-bytes core unchanged')
for phrase in ["gross==365010944","[[7,7,7],[7,7],[4,7,7,2,2,2,2]]","len(archive_bodies)==61","r['exit_code']==0","a['actual_process_returncode']==0","not a['timeout_expired']","r['plan_sha256']==digest(prep/'PLAN.json')","peer['exit_code']==0 and not peer['findings']","cp['files']==105","cp['unique_payloads']==16","ce['gross_allocated_bytes_retired']==54906880","ce['original_source_archive_sha256']==cp['archive_sha256']","included_in_metadata_tar=False","q==preserved:continue","assert str(preserved) not in","not archive_bodies.intersection","total<64*1024*1024"]:ck(phrase in new,'exact scope/terminal/payload separation '+phrase)
for name in ['COLD105_RETIREMENT_INITIAL_OUTER_SCHEMA_ASSUMPTION.json','review_cold105_retirement_actual.initial.py.txt','THREE_EMERGENCY_INITIAL_PATH_PREFIX_ASSUMPTION.json','review_three_emergency_archive_groups_actual.initial.py.txt']:ck(name in new and (O/name).is_file(),'original reviewer failure retained '+name)
for name in ['THREE_EMERGENCY_ARCHIVE_GROUPS_STATIC_ACTUAL_METADATA_PEER.json','TWO_PRER5_ARCHIVE_GROUPS_STATIC_ACTUAL_METADATA_PEER.json','SEVEN_POSTR5_ARCHIVE_GROUPS_STATIC_ACTUAL_METADATA_PEER.json','COLD105_EXECUTOR_STATIC_PEER.json','COLD105_RETIREMENT_ACTUAL_PEER.json']:
 r=j(O/name);ck(r['exit_code']==0 and not r['findings'],'original required actual/static peer present0 '+name)
ck('no invented outer OS transcript is backfilled' in new and 'all175 already absent' in new,'directexec provenance and old175 missing observation not claimed new cleanup')
registry=Path('/workspace/EMERGENCY_TWELVE_IMMUTABLE_ALIAS_REGISTRY_20261024.json');r=j(registry);ck(len(r['proof'])==3 and len(r['groups'])==12,'additive registry exact three batches/twelve groups')
expected={}
for proof in r['proof']:
 ck(h(proof['plan'])==proof['plan_sha256'] and h(proof['actual'])==proof['actual_sha256'],'registry exact original PLAN/result pins '+proof['batch'])
 plan=j(proof['plan']);actual=j(proof['actual']);ck(actual['exit_code']==0 and actual['all_original_payload_paths_retained'],'registry refers true retained original result '+proof['batch'])
 for i,g in enumerate(plan['groups'],1):expected[(proof['batch'],i)]=g
ck({(g['batch'],g['group']) for g in r['groups']}==set(expected),'exact no extra/missing registry groups')
total=0
for g in r['groups']:
 e=expected[(g['batch'],g['group'])];ck([x['path'] for x in g['aliases']]==[x['path'] for x in e['members']],'exact original registry paths '+str((g['batch'],g['group'])))
 for x in g['aliases']:
  p=Path(x['path']);s=p.lstat();total+=1
  ck(x['sha256']==e['sha256'] and x['bytes']==e['members'][0]['size'],'registry original content hash attribution '+str(p))
  ck(stat.S_ISREG(s.st_mode) and p.resolve()==p and (x['bytes'],x['device'],x['inode'],x['nlink'])==(s.st_size,s.st_dev,s.st_ino,s.st_nlink) and s.st_nlink==e['count'],'registry actual alias metadata '+str(p))
ck(total==61 and '先前423 cold／2 cardref／1 GEO339／3 large／4 additional規則不變' in r['scope'],'61 only additive to all older leases')
ck('全部alias安全解除hardlink前禁止寫入' in r['write_ban'] and '105份ordinary source copies另有明確退休紀錄' in r['write_ban'],'allalias delink write ban not removed by105 retirement')
resource=Path('/workspace/FINAL_ACCEPTANCE_RESOURCE_PLAN_20261024.md');text=resource.read_text();ck('全部早已不存在' in text and '不能再把歷史 185 MB 算成現有可回收量' in text and '不是所有可行方案的最低需求' in text and 'full123' not in text,'resource old175 not current recovery; estimates not new threshold')
result={'schema':'emergency12-cold105-metadata-collector-and-registry-static-peer/1','checks':checks,'exit_code':int(bool(findings)),'findings':findings,'collector_sha256':h(N),'registry_sha256':h(registry),'resource_plan_sha256':h(resource),'archive_groups':12,'immutable_archive_paths':61,'cold_source_paths':105,'limits':['Static collector scope/core and current small registry metadata only; no archive body rehash or package generation by reviewer.','105 preserved original source payload tar must be separately published alongside metadata tar; it is deliberately not nested or claimed inside this metadata package.','Original packager selfref avoided; eventual actual package peer remains an external attachment.','Resource plan is preparatory and does not certify source transition, available disk, final product source or acceptance.','Storage maintenance does not change any historical original red verdict; all old alias reservations remain.']}
q=O/'EMERGENCY12_COLD105_COLLECTOR_REGISTRY_STATIC_PEER.json';q.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(q),'sha256':h(q),'checks':checks,'exit_code':result['exit_code'],'findings':findings}));raise SystemExit(result['exit_code'])
