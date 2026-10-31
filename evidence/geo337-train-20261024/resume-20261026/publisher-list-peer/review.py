from pathlib import Path
import ast,datetime,difflib,hashlib,json,subprocess,sys

OUT=Path(__file__).parent
OLDROOT=Path('/tmp/geo337-recovery-publisher-peer-20261026')
OLD=OLDROOT/'SUBJECT.final.py'
NEW=Path('/tmp/geo337-recover-evidence-publisher-20261026.py')
CONSUMER=Path('/tmp/geo337-native-TMP-combined-preservation-20261025/retire_exact_leaves_v2.py')
OLDPIN='b2037b477e115afcc061d5e673318f8864f0941216cba298b6583244a8d6c005'
NEWPIN='c6a44de7ada360b6017a0e578507b81867471f583d8e9b6b591d56581ba41368'
COUNT=0;FAIL=[]
def H(b):return hashlib.sha256(b).hexdigest()
def ck(ok,msg):
 global COUNT
 COUNT+=1
 if not ok:FAIL.append(msg)
original_files={p.name:H(p.read_bytes())for p in OLDROOT.iterdir()if p.is_file()}
peer=json.loads((OLDROOT/'REVIEW.json').read_bytes());old=OLD.read_text();new=NEW.read_text()
ck(H(OLD.read_bytes())==OLDPIN,'prior reviewed subject exact pin')
ck(H(NEW.read_bytes())==NEWPIN,'new reviewed subject exact pin')
ck(peer['subject_sha256']==OLDPIN and peer['exit_code']==0 and peer['checks']==peer['passed_checks']==24 and peer['blocking_findings']==[],'original independent24check acceptance intact')
ck([x['exit_code']for x in peer['environment_counterproof']]==[0,1,0],'original environment010 preserved')
line_old="  cap.dump(a.out/'REMOTE_BLOBS.json',checked)"
line_new="  cap.dump(a.out/'REMOTE_BLOBS.json',[dict(blob_oid=blob,**identity) for blob,identity in checked.items()])"
ck(old.count(line_old)==1 and new.count(line_new)==1,'unique changed serializer line')
ck(old.replace(line_old,line_new)==new,'one-line delta only; all guards byte-identical')
ck(ast.dump(ast.parse(old))==ast.dump(ast.parse(new.replace(line_new,line_old))),'all other parsed behavior unchanged')
consumer_raw=CONSUMER.read_bytes();ck(H(consumer_raw)=='612de38f3cdcc84febf77c7dcbbff455f76c0887d4fd91e37ac439dff6402fba','original reviewed retirement consumer unchanged')
consumer_ast=ast.parse(consumer_raw)
preserve=next(n for n in consumer_ast.body if isinstance(n,ast.FunctionDef)and n.name=='preserved_payloads')
found=[n.value for n in ast.walk(preserve)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='found'for t in n.targets)]
ck(len(found)==1 and isinstance(found[0],ast.ListComp),'exact original consumer found expression')
expr=ast.unparse(found[0])
ck(expr=="[r for r in remote if r['bytes'] == size and r['sha256'] == pin]",'original consumer schema is list of identity records')
checked_expr=ast.parse("[dict(blob_oid=blob,**identity) for blob,identity in checked.items()]",mode='eval')
sample={'a'*40:{'bytes':17,'sha256':'b'*64},'c'*40:{'bytes':29,'sha256':'d'*64}}
sample_before=json.dumps(sample,sort_keys=True)
converted=eval(compile(checked_expr,'<serializer>','eval'),{'dict':dict},{'checked':sample})
ck(isinstance(converted,list)and len(converted)==len(sample),'output is exact unique-oid list')
ck({x['blob_oid']:{k:v for k,v in x.items()if k!='blob_oid'}for x in converted}==sample,'all verified identities bijectively retained')
ck(json.dumps(sample,sort_keys=True)==sample_before,'serialization does not mutate verified map')
ck(all(set(x)=={'blob_oid','bytes','sha256'}for x in converted),'retains only original identity fields plus blob_oid')
code="""import json,sys
checked={'a'*40:{'bytes':17,'sha256':'b'*64},'c'*40:{'bytes':29,'sha256':'d'*64}}
remote=checked if sys.argv[1]=='withdrawn' else [dict(blob_oid=blob,**identity) for blob,identity in checked.items()]
for blob,identity in checked.items():
 size,pin=identity['bytes'],identity['sha256']
 found=[r for r in remote if r['bytes']==size and r['sha256']==pin]
 assert len(found)==1 and found[0]['blob_oid']==blob
print(json.dumps({'case':sys.argv[1],'matched':len(checked),'same_verified_identities':True}))
"""
proof=[]
for case in ['fixed','withdrawn','restored']:
 args=[sys.executable,'-B','-c',code,case]
 proc=subprocess.run(args,capture_output=True,text=True)
 proof.append({'case':case,'argv':args,'actual_process_returncode':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr})
ck([x['actual_process_returncode']for x in proof]==[0,1,0],'real pure-memory subprocess010')
ck('TypeError' in proof[1]['stderr'] and "string indices must be integers"in proof[1]['stderr'],'withdrawn fails original consumer schema exact reason')
ck(original_files=={p.name:H(p.read_bytes())for p in OLDROOT.iterdir()if p.is_file()},'original peer history unchanged')
ck(H(NEW.read_bytes())==NEWPIN and H(CONSUMER.read_bytes())=='612de38f3cdcc84febf77c7dcbbff455f76c0887d4fd91e37ac439dff6402fba','subjects unchanged after review')
(OUT/'PROOF.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
(OUT/'DIFF.txt').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(OLD),tofile=str(NEW))))
review={'schema':'recovery-evidence-publisher-list-static-peer/1','reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'subject_sha256':NEWPIN,'executor_sha256':NEWPIN,'exit_code':int(bool(FAIL)),'blocking_findings':FAIL,'checks':COUNT,'passed_checks':COUNT-len(FAIL),'prior_independent_peer':{'path':str(OLDROOT/'REVIEW.json'),'sha256':original_files['REVIEW.json'],'subject_sha256':OLDPIN,'checks':24,'exit_code':0,'environment_counterproof_exits':[0,1,0]},'original_peer_files_preserved':original_files,'delta':'Only REMOTE_BLOBS.json representation changed from OID-to-identity mapping to list of dict(blob_oid=OID, **identity).','serialization_preserves_all_verified_identity_fields':True,'original_capacity_validation_push_and_remote_guards_byte_unchanged':True,'retirement_consumer_sha256':H(consumer_raw),'original_consumer_expression':expr,'serialization_counterproof_actual_exits':[x['actual_process_returncode']for x in proof],'proof_sha256':H((OUT/'PROOF.json').read_bytes()),'formal_product_tests_executed':False,'git_fixture_created':False,'network_used':False,'publication_executed':False,'retirement_executed':False,'original_subjects_modified':False,'reviewer_sha256':H(Path(__file__).read_bytes()),'limits':['Static one-line compatibility review and pure in-memory schema counterproof only; not a delivery receipt.','Root must bind the new publisher pin and use actual completed RESULT/REMOTE_BLOBS plus independent actual publication review before any retirement.','This change does not authorize deletion, publication concurrency, or any capacity/identity guard exemption.']}
(OUT/'REVIEW.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
(OUT/'SUMS.sha256').write_text(''.join(H(p.read_bytes())+'  '+p.name+'\n'for p in sorted(OUT.iterdir())if p.is_file()and p.name!='SUMS.sha256'))
total=sum(p.stat().st_size for p in OUT.iterdir()if p.is_file());assert total<=32768
print(json.dumps({'exit_code':review['exit_code'],'checks':COUNT,'failures':FAIL,'review_sha256':H((OUT/'REVIEW.json').read_bytes()),'total_new_bytes':total,'counterproof_exits':review['serialization_counterproof_actual_exits']}))
sys.exit(review['exit_code'])
