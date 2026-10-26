"""Read completed original F four-gate packet. No tests, Git or source writes."""
from pathlib import Path
import collections,datetime,hashlib,json,os,re,stat

OUT=Path(__file__).parent
OWN=Path('/dev/shm/geometry-axiom-geo337-20261025')
BASE=OWN/'F-final-light-gates-original-20261026';OUTER=OWN/'final-light-root-original-20261026'
ROOT=OWN/'a6-architecture-source-20261026';PREP=OWN/'a6-architecture-source-original-20261026'
F='cbf0fb621888596aa14ad5f2349b503e23b1b72d';A='a6f4013364e21bcb7239b5dcc25caac0f6d61f77';S10='82c922a3941525d3a094ac0158bdc7dea57ea360'
PIN='4ef99c7b38f0ab5f451e508d6fffd4e78e30d52a6df133f9a9fd7f9210359784'
TOOL_PIN='dde595446f259dac13a81e39ec43d64c8df9f28831b2c542ec631acc99b9b4f4'
CHANGED={'tests/mutants_results.json','geometry-core/domain-decoupling/PRODUCT-ARCHITECTURE.md','geometry-core/domain-decoupling/product-architecture-receipt.json'}
JUDGES=[['tests/mutate.py','--check'],['tests/architecture_contract.py','--root','.','--manifest','geometry-core/domain-decoupling/product-architecture.json'],['tests/test_architecture_contract.py'],['tests/test_product_architecture.py']]
checks=0;findings=[];captures=0;streambytes=0
def H(b):return hashlib.sha256(b).hexdigest()
def oid(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def need(ok,msg):
 global checks
 checks+=1
 if not ok:findings.append(msg);raise RuntimeError(msg)
def load(p):return json.loads(p.read_bytes())
def pinned(item):
 b=Path(item['path']).read_bytes();need(H(b)==item['sha256'],'bound actual input '+item['path']);return json.loads(b)
def stdout(row):return(Path(row['directory'])/'stdout.bin').read_bytes()
def read_captures(directory,outer=False):
 global captures,streambytes
 rows=load(directory/'subcommands.json')
 for i,row in enumerate(rows,1):
  d=directory/'subcommands'/f'{i:06d}';need(row['directory']==str(d)and row==load(d/'result.json'),'exact original captured command '+str(d))
  for key,value in load(d/'request.json').items():need(value is None if key=='actual_process_returncode'else row.get(key)==value,'request/result exact '+str(d)+' '+key)
  for name in ['stdin','stdout','stderr']:
   b=(d/(name+'.bin')).read_bytes();streambytes+=len(b);need(H(b)==row[name+'_sha256'],'full original stream hash '+str(d)+' '+name)
   if name!='stdin':need(len(b)==row[name+'_bytes'],'full original stream size '+str(d)+' '+name)
  need(row['acceptance_sha']==F and row['source_sha']==(A if outer and i<9 else F),'original FF/actual gate source boundary '+str(d))
  need(row['actual_process_returncode']==0 and row['timeout_expired']is False and row['ended_epoch']>=row['started_epoch'],'actual command zero/no timeout '+str(d));captures+=1
 return rows
def metadata(p):
 s=p.lstat();need(stat.S_ISREG(s.st_mode),'protected metadata regular '+str(p));return {'sha256':H(p.read_bytes()),'device':s.st_dev,'inode':s.st_ino,'mode':s.st_mode,'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}

report={'schema':'final-four-original-light-gates-actual-peer/1','source_sha':F,'final_sha':F,'result_sha256':PIN,'exit_code':1,'blocking_findings':findings,'prepared_source_sha':A,'ledger_execution_sha':S10,'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'formal_gates_rerun_by_peer':False,'source_modified_by_peer':False,'git_or_network_executed_by_peer':False,'native_or_browser_certified':False}
try:
 raw=(BASE/'RESULT.json').read_bytes();need(H(raw)==PIN,'fixed final four-gate original result pin');r=json.loads(raw)
 need(r['source_sha']==F and r['prepared_source_sha']==A and r['exit_code']==r['wrapper_exit']==0 and r['all_gates_passed']is True,'true final four-gate terminal zero')
 need(r['before']==r['after']and r['before']['head']==F and r['before']['status']=='','actual final source clean before/after')
 need(r['source_selected_count']==3763 and r['selected_3763_preserved']is True and r['five_fixtures_preserved']is True and r['publisher_preserved']is True,'actual source/fixture/provider terminal protections')
 need(r['native_source_claimed']is False and r['full_native_executed']is False and r['full123_executed']is False and r['historical_gates_relabelled']is False,'no native/full123/historical relabel claim')
 need(H((BASE/'EXECUTOR.py').read_bytes())==TOOL_PIN,'actual final runner exact static-reviewed bytes')
 static=load(OUTER/'static-peer.json');need(static['exit_code']==0 and not static['blocking_findings']and static['subject_sha256']==TOOL_PIN and static['fixed_final_sha']==F,'outer bound successful exact static peer')
 adpeer=load(OUTER/'adoption-peer.json');need(H((OUTER/'adoption-peer.json').read_bytes())=='819f0d2f9f2db05eb3ec6ae7e70d8a98fff7463203e92143de7f33ede58b0eb6'and adpeer['exit_code']==0 and adpeer['final_sha']==F and adpeer['full_remote_delivery_verified']is True,'original adoption actual peer bound')
 qraw=(BASE/'ROOT_REQUEST.json').read_bytes();need(qraw==(OUTER/'REQUEST.json').read_bytes(),'same root/inner request');q=json.loads(qraw)
 need(q['source_sha']==F and q['prepared_source_sha']==A and all(q[x]is True for x in ['root_execution_lease','root_source_exclusive','root_adoption_actual_peer_reviewed']),'exact final/source exclusive root request')
 prep=pinned(q['source_result']);sp=pinned(q['source_actual_peer']);adopt=pinned(q['adoption_result'])
 need(prep['source_sha']==sp['source_sha']==A and prep['exit_code']==sp['exit_code']==0 and sp['source_result_sha256']==q['source_result']['sha256'],'original a6 preparation not relabelled F')
 need(adopt['final_sha']==F and adopt['source_sha']==adopt['architecture_execution_sha']==A and adopt['ledger_execution_sha']==S10 and adopt['exit_code']==0 and adopt['published']and adopt['delivered'],'actual adopted final bytes retain S10/A execution sources')
 mraw=(PREP/'SOURCE_MANIFEST.json').read_bytes();need(H(mraw)==prep['source_manifest_sha256'],'original selected manifest pin');manifest=json.loads(mraw)
 need(manifest['source_sha']==A and len(manifest['files'])==3763 and len(manifest['architecture_paths'])==604 and len(manifest['fixture_paths'])==5,'original full source selection not reduced')
 outer=read_captures(OUTER,True);inner=read_captures(BASE)
 need(len(outer)==9 and len(inner)==15,'complete original FF/executor and four-gate command counts')
 need(load(OUTER/'RESULT.json')=={'exit_code':0,'source_sha':F,'prepared_source_sha':A,'ff_completed':True,'publisher_unchanged':True,'stack_soft_bytes':16777216},'actual root terminal, FF and original stack')
 need(outer[5]['command']==['git','-c','gc.auto=0','-c','maintenance.auto=false','merge','--ff-only',F]and outer[5]['cwd']==str(ROOT),'one ordinary FF in private source checkout')
 need([x for x in outer if 'merge'in x['command']]==[outer[5]],'no other merge operation')
 need(stdout(outer[0]).decode().strip()==A and stdout(outer[6]).decode().strip()==F and stdout(outer[1])==stdout(outer[7])==b'','root actual A-to-F clean source transition')
 need(outer[8]['command']==['python3','-B','/tmp/geo337-final-light-gates-preparation-20261026/run_after_ff_four_gates.py','--execute-root-approved','--request',str(OUTER/'REQUEST.json'),'--request-sha256',H(qraw)],'exact root original formal-gate argv')
 need(json.loads(stdout(outer[8]))==r,'root captured actual inner terminal bytes')
 before_ff=load(OUTER/'SOURCE_BEFORE.json');after_ff=load(OUTER/'SOURCE_AFTER_FF.json');idx=(ROOT/'.git/index').read_bytes()
 need(before_ff['head']==A and before_ff['selected']==3763 and before_ff['fixtures']==5 and H((OUTER/'SOURCE_INDEX.before.bin').read_bytes())==before_ff['index_sha256']==sp['current_source_index']['sha256'],'original pre-FF physical index preserved and bound to a6 peer')
 need(after_ff['head']==F and after_ff['publisher_unchanged']is True and H(idx)==after_ff['index_sha256'],'actual source real index unchanged since FF through all four judges')
 need(idx[:4]==b'DIRC'and hashlib.sha1(idx[:-20]).digest()==idx[-20:]and(ROOT/'.git/HEAD').read_text().strip()==F,'current real native index checksum/current final HEAD')
 admission=load(OUTER/'CAPACITY.json');need(admission['additional_bound']==67108864 and admission['shared_ceiling']==2147483648 and admission['shared_before']+67108864<=2147483648,'original reserve/shared capacity not lowered')
 sb=(BASE/'SELECTED.before.json').read_bytes();sa=(BASE/'SELECTED.after.json').read_bytes();need(sb==sa,'entire selected before/after raw metadata identical');selected=json.loads(sb);selected_map={x['path']:x for x in selected};need(len(selected)==len(selected_map)==3763 and set(selected_map)==set(manifest['files']),'all3763 unique selected paths exact original')
 tree={}
 need(inner[5]['command'][5:11]==['ls-tree','-r','-l','-z',F,'--'],'actual final Git inventory command exact SHA')
 for entry in stdout(inner[5]).split(b'\0'):
  if not entry:continue
  meta,name=entry.split(b'\t',1);mode,kind,obj,size=meta.split();need(kind==b'blob','selected final tree regular blob');tree[name.decode()]={'mode':mode.decode(),'oid':obj.decode(),'bytes':int(size)}
 need(set(tree)==set(manifest['files'])and{n for n in tree if tree[n]!=manifest['files'][n]}==CHANGED,'final selected Git inventory differs by exact three adopted leaves')
 for n in [6,14]:need({os.fsdecode(x[2:])for x in stdout(inner[n]).split(b'\0')if x and x[:1]!=b'S'}==set(tree),'actual Git sparse materialized set before/after complete')
 physical=set();inode_set=set();fixture_rows=[];ledger_raw=None
 for parent,dirs,files in os.walk(ROOT,followlinks=False):
  if Path(parent)==ROOT:dirs[:]=[x for x in dirs if x!='.git']
  need(all(not(Path(parent)/x).is_symlink()for x in dirs),'no source symlink directories')
  for name in files:physical.add((Path(parent)/name).relative_to(ROOT).as_posix())
 need(physical==set(tree),'current physical source exact3763 with no unknown files')
 for n in sorted(tree):
  p=ROOT/n;s=p.lstat();b=p.read_bytes();need(stat.S_ISREG(s.st_mode)and s.st_nlink==1 and(s.st_dev,s.st_ino)not in inode_set,'independent regular source inode '+n);inode_set.add((s.st_dev,s.st_ino))
  observed={'path':n,'oid':oid(b),'raw_sha256':H(b),'mode':'100755'if s.st_mode&0o111 else'100644','bytes':len(b)}
  need(observed==selected_map[n]and{k:observed[k]for k in ['mode','oid','bytes']}==tree[n],'current complete selected bytes match original F snapshots/Git '+n)
  if n in CHANGED:need(H(b)==adopt['original_artifact_hashes'][n],'current three adopted byte identities '+n)
  if n in manifest['fixture_paths']:
   need(tree[n]==manifest['files'][n],'mandatory fixture unchanged from a6');fixture_rows.append(observed)
  if n=='tests/mutants_results.json':ledger_raw=b
 need(len(fixture_rows)==5,'all five physical fixtures verified')
 source_before=(BASE/'SOURCE_INPUTS.before.json').read_bytes();source_after=(BASE/'SOURCE_INPUTS.after.json').read_bytes();need(source_before==source_after and H(source_before)==r['source_inputs_before_sha256']==r['source_inputs_after_sha256'],'complete604 source snapshots byte/hash exact')
 sources=json.loads(source_before);need(len(sources)==604 and{x['path']for x in sources}==set(manifest['architecture_paths']),'source closure exact604')
 for x in sources:
  b=(ROOT/x['path']).read_bytes();need(x=={'path':x['path'],'raw_sha256':H(b),'lf_sha256':H(b.replace(b'\r\n',b'\n')),'git_blob':oid(b)},'current architecture input exact original F '+x['path'])
 ap=OWN/'a6-architecture-gates-original-20261026';need(source_before==(ap/'SOURCE_INPUTS.before.json').read_bytes(),'F executable604 inputs byte-identical to original a6 gate closure')
 need(stdout(inner[2])==stdout(inner[13])and H(stdout(inner[2]))==r['before']['index'],'full actual tracked index output before/after equal')
 for n in [0,11]:need(stdout(inner[n]).decode().strip()==F,'actual inner HEAD F')
 for n in [1,12]:need(stdout(inner[n])==b'','actual inner clean status')
 gates=[];need([x['gate']for x in r['gates']]==['tracked-mutation-check','architecture-contract','architecture-unit','product-architecture-unit'],'all four named gates present in order')
 for i,g in enumerate(r['gates']):
  row=inner[i+7];need(g['command']==row and g['exit_code']==0 and row['command'][1:]==['-B',*JUDGES[i]]and row['cwd']==str(ROOT)and row['source_sha']==row['acceptance_sha']==F,'actual exact original gate source/argv/exit '+g['gate'])
  out=stdout(row);err=(Path(row['directory'])/'stderr.bin').read_bytes();testcount=None;details={}
  if i==0:
   ledger=json.loads(ledger_raw);headcounts=collections.Counter(v['execution']['head']for v in ledger.values()if isinstance(v.get('execution'),dict));verdicts=collections.Counter(v['verdict']for v in ledger.values())
   need(len(ledger)==123 and headcounts=={S10:120}and verdicts=={'killed':114,'crashed':1,'equivalent':5,'retired':3},'adopted S10 full ledger identity/classifications retained')
   text=out.decode();need('變異表 123 筆,紀錄 123 筆'in text,'actual full mutation record count')
   for name,count in [('killed',114),('crashed',1),('survived',0),('equivalent',5),('invalid',0),('stale',0),('blocked',0),('retired',3)]:need(re.search(r'\b'+name+r' '+str(count)+r'\b',text)is not None,'actual tracked check verdict '+name)
   need('CRASHED M20'in text and err==b'','M20 remains crashed, not silently relabelled killed')
   details={'records':123,'killed':114,'crashed':1,'survived':0,'equivalent':5,'invalid':0,'stale':0,'blocked':0,'retired':3,'historical_crashed_id':'M20','ledger_execution_head_counts':dict(headcounts)}
  elif i==1:
   scan=json.loads(out);need(scan['ok']is True and scan['diagnostics']==[]and len(scan['edges'])==798 and out==(ROOT/'geometry-core/domain-decoupling/product-architecture-scan.json').read_bytes(),'actual original architecture scan complete and exact stored scan')
   details={'edges':798,'diagnostics':0}
  else:
   text=(out+b'\n'+err).decode();m=re.findall(r'^Ran (\d+) tests? in ([0-9.]+)s$',text,re.M);testcount=205 if i==2 else 18
   need(len(m)==1 and int(m[0][0])==testcount and text.rstrip().endswith('OK'),'original complete unittest count/zero skips')
  gates.append({'name':g['gate'],'exit_code':0,'command':row['command'],'source_sha':F,'cwd':str(ROOT),'test_count':testcount,'skip_count':0,'stdout_bytes':len(out),'stderr_bytes':len(err),'stdout_sha256':H(out),'stderr_sha256':H(err),'started_epoch':row['started_epoch'],'ended_epoch':row['ended_epoch'],'details':details})
 pubbefore=load(BASE/'PUBLISHER.before.json');need(pubbefore==load(BASE/'PUBLISHER.after.json'),'full publisher+oldWS protected snapshot before/after equal')
 need(set(pubbefore)=={str(OWN/'publisher-source'),'/workspace/geometry-axiom'},'both publisher and original workspace protected')
 for owner,items in pubbefore.items():
  for name,value in items.items():need(metadata(Path(owner)/'.git'/name)==value,'current protected original metadata still equal '+owner+' '+name)
 outerpub=load(OUTER/'PUBLISHER.before.json');need(outerpub==load(OUTER/'PUBLISHER.after.json'),'root source-FF and full-gate window publisher preservation')
 for path,value in outerpub.items():need(H(Path(path).read_bytes())==value,'current root-protected publisher bytes unchanged')
 receipt=load(ROOT/'geometry-core/domain-decoupling/product-architecture-receipt.json');need(receipt['sourceBaseHead']==receipt['headObservedBefore']==receipt['headObservedAfter']==A and receipt['supplementalStaticGuardProbes']['executedAtCurrentHead']is False,'adopted architecture receipt remains a6, historical probes not relabelled')
 need(H((ROOT/'.git/index').read_bytes())==after_ff['index_sha256'],'peer did not change real F source index')
 report.update(exit_code=0,four_gates=gates,gate_exits={x['name']:0 for x in gates},tracked_mutation_check_exit=0,architecture_contract_exit=0,architecture_unit_exit=0,product_architecture_unit_exit=0,selected_source_count=3763,architecture_input_count=604,fixture_count=5,fixtures=fixture_rows,source_inputs_sha256=H(source_before),selected_before_after_sha256=H(sb),source_real_index_sha256_after_ff=after_ff['index_sha256'],source_unchanged_during_gates=True,publisher_preserved=True,old_workspace_preserved=True,ordinary_source_ff_verified=True,historical_gates_relabelled=False,S10_ledger_execution_heads_unchanged=True,original_command_count=captures,original_full_stream_bytes=streambytes,original_executor_sha256=TOOL_PIN,outer_result_sha256=H((OUTER/'RESULT.json').read_bytes()),root_request_sha256=H(qraw),limits=['Only tracked mutate --check and three original architecture judges were executed at F. This is not native6997/browser3759 acceptance; actual selected source has3763 leaves.','The S10 ledger was checked for applicability at F; its120 execution records remain S10, with114 killed,1 crashed(M20),5 equivalent and3 retired. No full mutation regeneration occurred in this gate batch.','The adopted architecture artifact receipt retains actual a6 executions. These separate new F judge receipts do not rewrite it or historical M probes.','Native, six browser jobs and remaining special gates need separate original receipts; this peer makes no pass claim for them.','Original capture streams were verified without rerunning tests or Git. Current source and protected publisher/oldWS metadata were read only.','This validates original local receipts, not remote publication of the entire four-gate raw packet.'])
except BaseException as exc:
 if not findings:findings.append(repr(exc))
 report['exception']=repr(exc)
finally:
 report.update(exit_code=1 if findings else 0,blocking_findings=findings,checked_count=checks)
 (OUT/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'exit_code':report['exit_code'],'checked_count':checks,'blocking_findings':findings,'review_sha256':H((OUT/'REVIEW.json').read_bytes()),'review_bytes':(OUT/'REVIEW.json').stat().st_size},ensure_ascii=False))
raise SystemExit(report['exit_code'])
