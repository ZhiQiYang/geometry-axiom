"""Read-only verification of completed formal candidate adoption and raw delivery."""
from pathlib import Path
import collections,datetime,hashlib,json,os,re,stat,zlib

OUT=Path(__file__).parent
OWN=Path('/dev/shm/geometry-axiom-geo337-20261025')
BASE=OWN/'candidate-three-leaf-adoption-original-20261026'
OUTER=OWN/'candidate-adoption-root-original-20261026'
ROOT=OWN/'publisher-source';OLD=Path('/workspace/geometry-axiom')
A='a6f4013364e21bcb7239b5dcc25caac0f6d61f77';S10='82c922a3941525d3a094ac0158bdc7dea57ea360'
F='cbf0fb621888596aa14ad5f2349b503e23b1b72d';PARENT='9a57aea2128a7bc3985064932c24e2229fd8fcb8'
PIN='51dc88fae03dfca5dc08ba20aadd8c7beea42cbcb5e9dc292e77d9f8c1019558'
SUBJECT_PIN='71b0b4eb9ddde59f6b8e9ab90eb2492f8e403d1469a645d81864585a631fefba'
BRANCH='codex/train337-recovered-evidence-20261026';TRAIN='codex/train-337-continue-20261024'
ART='geometry-core/domain-decoupling/';LEDGER='tests/mutants_results.json';REPORT=ART+'PRODUCT-ARCHITECTURE.md';RECEIPT=ART+'product-architecture-receipt.json'
CHANGED={LEDGER,REPORT,RECEIPT};UNCHANGED={ART+'product-architecture.json',ART+'product-architecture-scan.json'}
checks=0;findings=[];captures=0;streambytes=0
def H(b):return hashlib.sha256(b).hexdigest()
def gid(kind,b):return hashlib.sha1(kind+b' '+str(len(b)).encode()+b'\0'+b).hexdigest()
def blob(b):return gid(b'blob',b)
def need(ok,msg):
 global checks
 checks+=1
 if not ok:findings.append(msg);raise RuntimeError(msg)
def load(p):return json.loads(p.read_bytes())
def pinned(item):
 p=Path(item['path']);s=p.lstat();need(stat.S_ISREG(s.st_mode),'regular original '+str(p));b=p.read_bytes();need(H(b)==item['sha256']and len(b)==item['bytes'],'exact original bytes '+str(p));return b
def stdout(row):return(Path(row['directory'])/'stdout.bin').read_bytes()
def stdin(row):return(Path(row['directory'])/'stdin.bin').read_bytes()
def captures_read(directory):
 global captures,streambytes
 rows=load(directory/'subcommands.json')
 for i,row in enumerate(rows,1):
  d=directory/'subcommands'/f'{i:06d}';need(row['directory']==str(d)and row==load(d/'result.json'),'original capture identity '+str(d))
  for key,value in load(d/'request.json').items():need(value is None if key=='actual_process_returncode'else row.get(key)==value,'original request/result '+str(d)+' '+key)
  for name in ['stdin','stdout','stderr']:
   b=(d/(name+'.bin')).read_bytes();streambytes+=len(b);need(H(b)==row[name+'_sha256'],'original full stream SHA '+str(d)+' '+name)
   if name!='stdin':need(len(b)==row[name+'_bytes'],'original stream size '+str(d)+' '+name)
  need(row['acceptance_sha']==A and row['source_sha']in[A,S10],'original explicit source/acceptance identities '+str(d))
  need(row['actual_process_returncode']==0 and row['timeout_expired']is False and row['ended_epoch']>=row['started_epoch'],'original true zero/no timeout '+str(d));captures+=1
 return rows
def parse_tree_ls(raw):
 rows={}
 for line in raw.split(b'\0'):
  if not line:continue
  meta,name=line.split(b'\t',1);mode,kind,obj=meta.split();need(name not in rows,'unique tree entry');rows[name]=(mode,kind,obj)
 return rows
def binary_tree(rows):
 raw=b''
 for name,(mode,kind,obj)in sorted(rows.items(),key=lambda p:p[0]+(b'/'if p[1][1]==b'tree'else b'')):
  raw+=mode.lstrip(b'0')+b' '+name+b'\0'+bytes.fromhex(obj.decode())
 return raw
def obj_read(oid):
 p=ROOT/'.git/objects'/oid[:2]/oid[2:];s=p.lstat();need(stat.S_ISREG(s.st_mode),'actual newly created private object regular');raw=zlib.decompress(p.read_bytes());header,payload=raw.split(b'\0',1);kind,size=header.split(b' ');need(hashlib.sha1(raw).hexdigest()==oid and int(size)==len(payload),'actual private Git object hash/length');return kind,payload
def metadata_identity(p):
 if not p.exists():return {'exists':False}
 s=p.lstat();need(stat.S_ISREG(s.st_mode),'protected metadata regular '+str(p));b=p.read_bytes()
 return {'exists':True,'sha256':H(b),'bytes':s.st_size,'mode':s.st_mode,'device':s.st_dev,'inode':s.st_ino,'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns,'nlink':s.st_nlink}

report={'schema':'candidate-three-leaf-adoption-actual-peer/1','source_sha':A,'result_sha256':PIN,'final_sha':F,'exit_code':1,'blocking_findings':findings,'published':False,'delivered':False,'product_tests_executed_by_peer':False,'git_or_network_commands_rerun_by_peer':False,'source_or_refs_modified_by_peer':False,'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
try:
 result_raw=(BASE/'RESULT.json').read_bytes();need(H(result_raw)==PIN,'fixed actual terminal result pin');r=json.loads(result_raw)
 need(r['exit_code']==0 and r['final_sha']==F and r['previous_head']==PARENT and r['candidate_branch']==BRANCH and r['published']is True and r['delivered']is True and r['old_repo_changed']is False,'actual successful candidate publication/delivery')
 need(r['ledger_execution_sha']==S10 and r['architecture_execution_sha']==r['source_sha']==r['product_source']==A and r['source_execution_heads_rewritten']is False,'ledger/architecture source identities remain distinct')
 need(r['formal_product_tests_executed']is False and r['new_final_tracked_check'].startswith('UNRUN'),'adoption is not final-SHA acceptance')
 request_raw=(BASE/'REQUEST.json').read_bytes();need(H(request_raw)==r['request_sha256']and request_raw==(OUTER/'REQUEST.json').read_bytes(),'outer/inner exact request binding');q=json.loads(request_raw)
 need(q['expected_parent']==PARENT and q['source_sha']==S10 and q['architecture_source_sha']==A and q['candidate_branch']==BRANCH and all(q[x]is True for x in ['root_execution_lease','root_exclusive_publisher_window','root_originals_and_peers_reviewed','root_candidate_ref_exclusive']),'exact approved root scope and exclusive bindings')
 need(H((BASE/'ADOPTER.py').read_bytes())==SUBJECT_PIN and H(Path('/tmp/geo337-resume-final-source-plan-20261026/adopt_candidate_three_leaves.py').read_bytes())==SUBJECT_PIN,'executed subject unchanged')
 need(H((OUTER/'tiny-actual-peer.json').read_bytes())=='21ac8cda0e50f3fbd957e6a52310cae573d704abf5fae37a6439a1b9a6d9ad6d','actual tiny peer bound to formal outer')
 rawart={n:pinned(v)for n,v in q['artifacts'].items()};need(set(rawart)==CHANGED|UNCHANGED,'exact five original artifact set')
 for n,b in rawart.items():need(H(b)==r['original_artifact_hashes'][n],'result artifact hash '+n)
 original={n:json.loads(pinned(v))for n,v in q['original_receipts'].items()};ledger=json.loads(rawart[LEDGER]);heads=collections.Counter(x['execution']['head']for x in ledger.values()if isinstance(x.get('execution'),dict));retired=sorted(n for n,x in ledger.items()if x.get('verdict')=='retired')
 need(len(ledger)==123 and heads=={S10:120}and len(retired)==3,'entire adopted ledger retains natural 120 S10 execution heads plus three retired rows')
 for t in [original['terminal'],original['ledger_index']['terminal']]:
  need(t['source_sha']==S10 and t['formal_accepted']is True and t['failed_conditions']==[]and t['record_count']==123 and t['execution_head_counts']=={S10:120}and sorted(t['retired_ids'])==retired,'original accepted S10 terminal exact identity')
  need(t['root_exit']==t['outer_exit']==t['original_cli_exit']==0 and t['terminal_files']['ledger']['sha256']==H(rawart[LEDGER]),'original terminal zero and adopted ledger byte binding')
 ar=original['architecture_result'];receipt=json.loads(rawart[RECEIPT]);need(ar['sourceSHA']==A and ar['exit_code']==0 and ar['originalGateExits']==[0,0,0]and ar['inputCount']==604 and ar['changedArtifacts']==['PRODUCT-ARCHITECTURE.md','product-architecture-receipt.json'],'original a6 four-artifact identity')
 need(receipt['sourceBaseHead']==receipt['headObservedBefore']==receipt['headObservedAfter']==A and receipt['supplementalStaticGuardProbes']['executedAtCurrentHead']is False,'architecture and historical probe execution source not relabelled F')
 expected_peer={'ledger_actual':{'exit':0,'source':S10,'ledger_sha256':H(rawart[LEDGER])},'ledger_package':{'exit':0,'source':S10,'index_sha256':q['original_receipts']['ledger_index']['sha256'],'archive_sha256':original['ledger_index']['archive_sha256']},'architecture_actual':{'exit':0,'source':A,'result_sha256':q['original_receipts']['architecture_result']['sha256']}}
 for role,fields in expected_peer.items():
  item=q['peers'][role];peer=json.loads(pinned(item));need(set(item['key_paths'])==set(fields),'all exact peer key bindings '+role)
  for k,v in fields.items():
   found=peer
   for key in item['key_paths'][k]:found=found[key]
   need(type(found)==type(v)and found==v,'actual peer field exact '+role+' '+k)
 outer=captures_read(OUTER);rows=captures_read(BASE);need(len(outer)==3 and len(rows)==106 and r['commands']==rows,'complete actual commands bound to terminal result')
 need(load(OUTER/'RESULT.json')=={'exit_code':0,'architecture_source_sha':A,'ledger_source_sha':S10,'stack_soft_bytes':16777216},'outer actual zero and original stack')
 need(outer[-1]['command']==['python3','-B','/tmp/geo337-resume-final-source-plan-20261026/adopt_candidate_three_leaves.py','--request',str(OUTER/'REQUEST.json'),'--request-sha256',H(request_raw),'--execute-root-approved'],'outer exact actual formal adopter argv')
 need(json.loads(stdout(outer[-1]))=={'exit_code':0,'final_sha':F,'published':True,'delivered':True,'old_repo_changed':False},'outer stdout matches actual adopter terminal')
 gitrows=[];apirows=[]
 for row in rows:
  if row['command'][0]=='git':
   need(row['command'][:5]==['git','-c','gc.auto=0','-c','maintenance.auto=false'],'original Git command prefix')
   need(row['cwd']in[str(ROOT),str(OLD)],'only declared publisher or readonly old workspace command')
   if row['cwd']==str(OLD):need(row['command'][5]in['rev-parse','branch','status','for-each-ref']and row['source_sha']==S10,'old WS only readonly metadata commands')
   else:need(row['source_sha']==A,'publisher operation declares a6 source')
   gitrows.append(row)
  else:
   need(row['command'][:6]==['gh','api','--hostname','github.com','--method','GET']and row['cwd']==str(ROOT),'only original read-only GitHub verification');apirows.append(row)
 def selected(args,cwd=ROOT):return[x for x in gitrows if x['command'][5:]==args and x['cwd']==str(cwd)]
 def one(args,cwd=ROOT):
  found=selected(args,cwd);need(len(found)==1,'exact unique command '+str(args));return found[0]
 def paths(b):return set(x.decode()for x in b.split(b'\0')if x)
 need(paths(stdout(one(['diff','--no-renames','--name-only','-z',S10,A,'--','.',':(exclude)evidence'])))=={'決策佇列.md'},'S10/a6 exact decision-only non-evidence delta')
 need(stdout(one(['diff','--no-renames','--name-only','-z',A,PARENT,'--','.',':(exclude)evidence']))==b'','evidence parent has exact a6 non-evidence closure')
 for side,rev in [('old',S10),('new',A)]:
  d=q['s10_to_architecture_decision'][side];b=stdout(one(['show',rev+':決策佇列.md']));need({'mode':'100644','oid':blob(b),'bytes':len(b),'sha256':H(b)}==d,'complete decision source bytes '+side)
  need(stdout(one(['ls-tree','-z',rev,'--','決策佇列.md']))==b'100644 blob '+d['oid'].encode()+b'\t'+ '決策佇列.md\0'.encode(),'decision Git mode/OID '+side)
 for n in UNCHANGED:
  for rev in [A,PARENT,F]:need(stdout(one(['show',rev+':'+n]))==rawart[n],'unchanged manifest/scan exact original/final bytes '+n)
 entries={n:blob(rawart[n])for n in CHANGED};need(paths(stdout(one(['diff-tree','--no-commit-id','--no-renames','--name-only','-r','-z',PARENT,F])))==CHANGED and paths(stdout(one(['diff','--no-renames','--name-only','-z',A,F,'--','.',':(exclude)evidence'])))==CHANGED,'both full commit and a6 non-evidence deltas exactly three paths')
 for n in CHANGED:
  need(stdout(one(['hash-object','-w','--no-filters','--',q['artifacts'][n]['path']])).decode().strip()==entries[n],'actual hash-object original bytes OID '+n)
  need(stdout(one(['rev-parse',F+':'+n])).decode().strip()==entries[n],'actual final committed leaf OID '+n)
 trees={};newtrees={}
 for row in gitrows:
  args=row['command'][5:]
  if len(args)==3 and args[:2]==['ls-tree','-z']and re.fullmatch('[0-9a-f]{40}',args[2]):
   value=parse_tree_ls(stdout(row));need(gid(b'tree',binary_tree(value))==args[2],'independent original tree OID reconstruction');trees[args[2]]=value
  if args==['mktree','-z']:
   value=parse_tree_ls(stdin(row));treeoid=stdout(row).decode().strip();need(gid(b'tree',binary_tree(value))==treeoid,'independent new tree OID reconstruction');newtrees[treeoid]=value
 need(len(newtrees)==4 and all(trees[k]==v for k,v in newtrees.items()),'four new tree roundtrips exact')
 oldroot=stdout(one(['rev-parse',PARENT+'^{tree}'])).decode().strip();commitrows=[x for x in gitrows if x['command'][5]=='commit-tree'];need(len(commitrows)==1,'one new candidate commit only');cr=commitrows[0];newroot=cr['command'][6]
 need(cr['command'][5:]==['commit-tree',newroot,'-p',PARENT]and stdout(cr).decode().strip()==F and stdout(one(['show','-s','--format=%P',F])).decode().strip()==PARENT,'exact single-parent candidate commit')
 def compare_tree(oldoid,newoid,prefix=''):
  old=trees[oldoid];new=trees[newoid];need(set(old)==set(new),'unchanged full tree entry names '+prefix)
  changed=[]
  for name in old:
   if old[name]==new[name]:continue
   om,ok,oo=old[name];nm,nk,no=new[name];need(om==nm and ok==nk,'no Git mode/type drift '+prefix+name.decode())
   if ok==b'tree':changed+=compare_tree(oo.decode(),no.decode(),prefix+name.decode()+'/')
   else:
    path=prefix+name.decode();need(path in CHANGED and om==b'100644'and no.decode()==entries[path],'only exact original artifact leaf changes');changed.append(path)
  return changed
 need(set(compare_tree(oldroot,newroot))==CHANGED,'independent recursive full tree delta exact three')
 kind,commitbytes=obj_read(F);need(kind==b'commit','actual private final commit object');headers,message=commitbytes.split(b'\n\n',1);need(headers.splitlines()[0]==b'tree '+newroot.encode()and[x for x in headers.splitlines()if x.startswith(b'parent ')]==[b'parent '+PARENT.encode()]and message==stdin(cr),'actual full commit bytes parent/tree/message')
 for newoid,treerows in newtrees.items():need(obj_read(newoid)==(b'tree',binary_tree(treerows)),'actual private new tree bytes')
 for name,newoid in entries.items():need(obj_read(newoid)==(b'blob',rawart[name]),'actual private adopted blob byte equality '+name)
 cas=selected(['update-ref','refs/heads/'+BRANCH,F,PARENT]);push=selected(['push','origin','refs/heads/'+BRANCH+':refs/heads/'+BRANCH]);need(len(cas)==len(push)==1 and cas[0]['ended_epoch']<=push[0]['started_epoch'],'one exact expected-parent CAS before ordinary push')
 need([x for x in gitrows if x['command'][5]=='update-ref']==cas and[x for x in gitrows if x['command'][5]=='push']==push,'no other ref writes, force push or PR merge')
 remote_refs=selected(['ls-remote','--heads','origin','refs/heads/'+BRANCH]);need(len(remote_refs)==3 and[stdout(x).decode().split()for x in remote_refs]==[[PARENT,'refs/heads/'+BRANCH],[PARENT,'refs/heads/'+BRANCH],[F,'refs/heads/'+BRANCH]],'original remote parent checked twice then resolves final')
 need(stdout(one(['sparse-checkout','check-rules','-z']))==b'','three changed artifacts never materialized in historical publisher')
 remote_rows=load(BASE/'REMOTE_THREE_BLOBS.json');need(len(remote_rows)==3 and {x['path']for x in remote_rows}==CHANGED,'full remote three-blob table')
 endpoint_prefix='repos/ZhiQiYang/geometry-axiom/git/'
 ref_api=[x for x in apirows if x['command'][-1]==endpoint_prefix+'ref/heads/'+BRANCH];commit_api=[x for x in apirows if x['command'][-1]==endpoint_prefix+'commits/'+F]
 need(len(apirows)==6 and len(ref_api)==2 and len(commit_api)==1,'complete original remote verification command set')
 for x in ref_api:
  refobj=json.loads(stdout(x));need(refobj['object']['type']=='commit'and refobj['object']['sha']==F,'actual remote ref exact final before/after blob verification')
 rc=json.loads(stdout(commit_api[0]));need(rc['sha']==F and rc['tree']['sha']==newroot and[y['sha']for y in rc['parents']]==[PARENT]and rc['message'].encode()==message.rstrip(b'\n'),'actual remote complete commit identity')
 for remote in remote_rows:
  n=remote['path'];need(remote=={'path':n,'oid':entries[n],'bytes':len(rawart[n]),'sha256':H(rawart[n])},'remote table exact original artifact '+n)
  api=[x for x in apirows if x['command'][-1]==endpoint_prefix+'blobs/'+entries[n]];need(len(api)==1 and api[0]['command'][7]=='Accept: application/vnd.github.raw+json','original raw-media API blob request '+n)
  b=stdout(api[0]);need(b==rawart[n]and blob(b)==entries[n],'entire actual remote blob byte/OID equality '+n)
 publisher=load(BASE/'PUBLISHER_BEFORE.json');need(publisher==load(BASE/'PUBLISHER_AFTER.json')==load(BASE/'PUBLISHER_FINAL.json'),'original publisher full before/after/final state equal')
 need(publisher['head']==publisher['train_ref']==q['expected_publisher_head']=='3e4f2560aa11ed2a626db98ba5ed6f129e791052'and publisher['branch']==TRAIN and publisher['status_hex']==''and publisher['index_sha256']==q['expected_publisher_index_sha256'],'original publisher anchored HEAD/index/train')
 need(H((ROOT/'.git/HEAD').read_bytes())==publisher['head_bytes_sha256']and H((ROOT/'.git/index').read_bytes())==publisher['index_sha256']and(ROOT/'.git/refs/heads'/TRAIN).read_text().strip()==publisher['train_ref'],'current original publisher physical HEAD/index/train unchanged')
 need((ROOT/'.git/refs/heads'/BRANCH).read_text().strip()==F,'current only candidate ref resolves final')
 old=load(BASE/'OLD_BEFORE.json');need(old==load(BASE/'OLD_AFTER.json')and old['head']=='70d00309d7985db722c339c77331c436d26a7ab1'and old['branch']==TRAIN and old['status_hex']=='','original entire old-WS before/after snapshot equal')
 for name,value in old['files'].items():need(metadata_identity(OLD/'.git'/name)==value,'current old-WS protected metadata exact original '+name)
 need(metadata_identity(OLD/'evidence/geo337-train-20261024/PROGRESS.md')==old['progress'],'current old-WS PROGRESS original bytes/identity')
 for node in old['object_provider_graph']:need(metadata_identity(Path(node['objects'])/'info/alternates')==node['alternates'],'original borrowed object provider links unchanged')
 for root,head in [(ROOT,publisher['head']),(OLD,old['head'])]:
  for row in selected(['rev-parse','HEAD'],root):need(stdout(row).decode().strip()==head,'all actual original HEAD guard samples fixed')
  for row in selected(['status','--porcelain=v1','--untracked-files=all'],root):need(stdout(row)==b'','all actual original clean status guard samples')
 for row in selected(['rev-parse','refs/heads/'+TRAIN]):need(stdout(row).decode().strip()==publisher['train_ref'],'all actual original train ref guard samples fixed')
 for n,item in q['artifacts'].items():need(pinned(item)==rawart[n],'all source artifacts still original after adoption and peer '+n)
 report.update(exit_code=0,published=True,delivered=True,branch=BRANCH,previous_head=PARENT,final_tree_sha=newroot,changed_paths=sorted(CHANGED),push_exit=0,cas_expected_parent=PARENT,full_remote_delivery_verified=True,remote_three_blobs=remote_rows,remote_blobs_sha256=H((BASE/'REMOTE_THREE_BLOBS.json').read_bytes()),remote_commit_url='https://github.com/ZhiQiYang/geometry-axiom/commit/'+F,ledger_execution_sha=S10,ledger_records=123,ledger_execution_head_counts=dict(heads),retired_ids=retired,architecture_execution_sha=A,source_execution_heads_rewritten=False,manifest_scan_byte_unchanged=True,other_product_test_ssot_unchanged=True,historical_publisher_unchanged=True,old_repo_changed=False,original_commands=captures,original_full_stream_bytes=streambytes,original_subject_sha256=SUBJECT_PIN,original_request_sha256=H(request_raw),outer_result_sha256=H((OUTER/'RESULT.json').read_bytes()),original_publisher_snapshot_sha256=H((BASE/'PUBLISHER_BEFORE.json').read_bytes()),old_workspace_snapshot_sha256=H((BASE/'OLD_BEFORE.json').read_bytes()),formal_product_tests_executed=False,new_final_tracked_check='UNRUN in this adoption; requires separate actual receipt at F',limits=['This verifies actual byte-exact adoption, expected-parent CAS, ordinary push and full original remote GitHub commit/ref/blob responses. It does not rerun network calls or claim the remote branch cannot later advance.','S10 full-ledger execution heads and a6 architecture receipt remain their actual execution sources; no test is relabelled F. The final tracked mutation check and affected formal gates at F are separate work.','Current original publisher HEAD/index/train and old workspace protected Git metadata/PROGRESS match original snapshots; object storage additions and the intended separate candidate-ref advancement are allowed effects. Full old product payload was not reread.','The three adopted artifact blobs are verified remotely in full. Publication of this adopter raw receipt packet is a separate delivery step.','No product test, Git command, network request, source mutation, ref update or cleanup was executed by this peer.'])
except BaseException as exc:
 if not findings:findings.append(repr(exc))
 report['exception']=repr(exc)
finally:
 report.update(exit_code=1 if findings else 0,blocking_findings=findings,checked_count=checks)
 (OUT/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'exit_code':report['exit_code'],'checked_count':checks,'blocking_findings':findings,'review_sha256':H((OUT/'REVIEW.json').read_bytes()),'review_bytes':(OUT/'REVIEW.json').stat().st_size},ensure_ascii=False))
raise SystemExit(report['exit_code'])
