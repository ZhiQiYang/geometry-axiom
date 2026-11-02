"""Read completed tiny receipts and Git objects only; never execute subject/Git."""
from pathlib import Path
import ast, configparser, datetime, hashlib, json, os, stat, zlib

OUT=Path(__file__).parent
OWN=Path('/dev/shm/geometry-axiom-geo337-20261025')
BASE=OWN/'geo337-candidate-adopter-tiny-20261026'
OUTER=OWN/'candidate-tiny-root-original-20261026'
SUBJECT_PIN='71b0b4eb9ddde59f6b8e9ab90eb2492f8e403d1469a645d81864585a631fefba'
RESULT_PIN='00150f01d1c29fae10bad159b393e242bd090e21eaf598eb3c2d7df82fa2f402'
TRAIN='codex/train-337-continue-20261024'
CANDIDATE='codex/train337-recovered-evidence-20261026'
CHANGED={'tests/mutants_results.json','geometry-core/domain-decoupling/PRODUCT-ARCHITECTURE.md','geometry-core/domain-decoupling/product-architecture-receipt.json'}
MARKERS={'cas':'CAS_EXPECTED_PARENT_NOT_ENFORCED','scope':'FOURTH_PRODUCT_PATH_NOT_REFUSED','preservation':'HISTORICAL_PUBLISHER_CHANGE_NOT_DETECTED'}
checks=0;findings=[];capture_count=0;stream_bytes=0;objects={};phases=[]
def H(b):return hashlib.sha256(b).hexdigest()
def need(ok,msg):
 global checks
 checks+=1
 if not ok:findings.append(msg);raise RuntimeError(msg)
def load(p):return json.loads(p.read_bytes())
def read_capture(directory,identity):
 global capture_count,stream_bytes
 rows=load(directory/'subcommands.json')
 for number,row in enumerate(rows,1):
  d=directory/'subcommands'/f'{number:06d}'
  need(row['directory']==str(d),'exact original capture directory '+str(d))
  need(row==load(d/'result.json'),'original command index/result equality '+str(d))
  for key,value in load(d/'request.json').items():need(value is None if key=='actual_process_returncode'else row.get(key)==value,'request/result binding '+str(d)+' '+key)
  for name in ['stdin','stdout','stderr']:
   b=(d/(name+'.bin')).read_bytes();stream_bytes+=len(b)
   need(H(b)==row[name+'_sha256'],'complete original stream hash '+str(d)+' '+name)
   if name!='stdin':need(len(b)==row[name+'_bytes'],'complete original stream size '+str(d)+' '+name)
  need(row['source_sha']==row['acceptance_sha']==identity,'synthetic-only capture identity '+str(d))
  need(row['timeout_expired']is False and row['ended_epoch']>=row['started_epoch'],'closed original command/no timeout '+str(d))
  capture_count+=1
 return rows
def object_read(gitdir,oid):
 need(len(oid)==40 and all(c in '0123456789abcdef'for c in oid),'exact object id')
 key=(str(gitdir),oid)
 if key in objects:return objects[key]
 p=gitdir/'objects'/oid[:2]/oid[2:];s=p.lstat();need(stat.S_ISREG(s.st_mode),'actual loose Git object regular '+str(p))
 raw=zlib.decompress(p.read_bytes());need(hashlib.sha1(raw).hexdigest()==oid,'actual Git object hash '+str(p))
 header,payload=raw.split(b'\0',1);kind,size=header.split(b' ')
 need(int(size)==len(payload),'actual Git object declared size '+str(p));objects[key]=(kind,payload);return kind,payload
def commit(gitdir,oid):
 kind,raw=object_read(gitdir,oid);need(kind==b'commit','real commit object')
 lines=raw.split(b'\n\n',1)[0].splitlines();tree=next(x[5:].decode()for x in lines if x.startswith(b'tree '));parents=[x[7:].decode()for x in lines if x.startswith(b'parent ')]
 return tree,parents,raw
def tree(gitdir,oid,prefix=''):
 kind,raw=object_read(gitdir,oid);need(kind==b'tree','real tree object');pos=0;leaves={}
 while pos<len(raw):
  end=raw.index(b'\0',pos);mode,name=raw[pos:end].split(b' ',1);obj=raw[end+1:end+21].hex();need(len(raw[end+1:end+21])==20,'complete tree entry');pos=end+21
  path=prefix+name.decode()
  if mode==b'40000':leaves.update(tree(gitdir,obj,path+'/'))
  else:
   need(mode==b'100644','synthetic regular leaf mode');kind,b=object_read(gitdir,obj);need(kind==b'blob','actual blob leaf');leaves[path]=(obj,b)
 return leaves
def ref(gitdir,name):
 p=gitdir/'refs/heads'/name;s=p.lstat();need(stat.S_ISREG(s.st_mode),'actual regular ref');v=p.read_text().strip();need(len(v)==40,'actual complete ref');return v

report={'schema':'candidate-adopter-nine-phase-tiny-runtime-actual-peer/1','exit_code':1,'blocking_findings':findings,'subject_sha256':SUBJECT_PIN,'runtime_result_sha256':RESULT_PIN,'formal_adoption_executed':False,'formal_schema_or_real_root_admission_proven':False,'product_tests_executed':False,'network_used_by_reviewer':False,'git_executed_by_reviewer':False,'fixtures_rerun':False,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
try:
 result_raw=(BASE/'RESULT.json').read_bytes();need(H(result_raw)==RESULT_PIN,'fixed actual tiny result');result=json.loads(result_raw)
 subject_raw=(BASE/'SUBJECT.py').read_bytes();need(H(subject_raw)==SUBJECT_PIN,'actual subject exact pin')
 request_raw=(BASE/'REQUEST.json').read_bytes();request=json.loads(request_raw);need(H(request_raw)==result['request_sha256']and request_raw==(OUTER/'REQUEST.json').read_bytes(),'root/runner exact request')
 need(H(Path(request['subject']['path']).read_bytes())==SUBJECT_PIN,'original subject remains byte-exact')
 for name,pin in [('HARNESS.py','473e8668b6120179b102da9437d87e204566d50cf0b10ea78f894b85617206a7'),('RUNNER.py','ef136f13a7037f37e98e19f0e7e72f9da6fd8d3e07e446031c7ba7bb8d381d0c')]:need(H((BASE/name).read_bytes())==pin,'actual helper exact reviewed pin '+name)
 need(result['exit_code']==0 and result['formal_adoption_executed']is False and result['schema_validations_or_actual_root_admission_proven']is False and result['synthetic_scope_only']is True,'honest terminal/synthetic boundary')
 need(load(OUTER/'RESULT.json')=={'exit_code':0,'formal_adoption_executed':False},'outer actual terminal zero')
 capacity=load(OUTER/'CAPACITY.json');need(capacity['synthetic_bound']==16777216 and capacity['reserve']==67108864 and capacity['shared_ceiling']==2147483648 and capacity['shared_used']+capacity['synthetic_bound']+capacity['reserve']<capacity['shared_ceiling'],'original shared bound and reserve')
 need(result['additional_bound_bytes']==16777216 and result['runtime_allocated_max_observed']==14647296<=16777216,'recorded observed allocation within admitted bound')
 outer=read_capture(OUTER,'SYNTHETIC_CANDIDATE_PRIMITIVES_ONLY');runs=read_capture(BASE/'original-commands','SYNTHETIC_CANDIDATE_PRIMITIVES_ONLY')
 need(len(outer)==1 and outer[0]['actual_process_returncode']==0 and len(runs)==len(result['phases'])==9,'one actual runner/nine actual phases')
 need(outer[0]['command']==['python3','-B','/tmp/geo337-candidate-adopter-runtime-preparation-20261026/run_candidate_tiny.py','--execute','--request',str(OUTER/'REQUEST.json'),'--request-sha256',H(request_raw)],'outer exact pinned runner request')
 program=ast.parse(subject_raw);main=next(n for n in program.body if isinstance(n,ast.FunctionDef)and n.name=='main');functions={n.name:n for n in main.body if isinstance(n,ast.FunctionDef)}
 calls=[n for n in ast.walk(main)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='git'and n.args and isinstance(n.args[0],ast.Constant)and n.args[0].value=='update-ref']
 need(len(calls)==1 and len(calls[0].args)==4,'one exact original CAS primitive with expected old OID')
 primitives=ast.unparse(ast.Module(body=[functions['publisher_state'],functions['clean'],ast.Expr(calls[0])],type_ignores=[]))+'\n'
 expected=[(case,phase)for case in MARKERS for phase in ['fixed','withdrawn','restored']]
 need([(p['case'],p['phase'])for p in result['phases']]==expected,'exact complete ordered nine phases')
 for number,(phase,run)in enumerate(zip(result['phases'],runs),1):
  case=phase['case'];mode=phase['phase'];expected_exit=1 if mode=='withdrawn'else 0;d=BASE/(case+'-'+mode);r=load(d/'RESULT.json')
  need(r==phase['result']and run['actual_process_returncode']==phase['actual_exit']==r['exit_code']==expected_exit,'actual phase terminal identity '+d.name)
  need(run['directory']==phase['command_directory']and run['cwd']==str(BASE),'phase exact original command binding '+d.name)
  need(run['command']==['python3','-B',request['harness']['path'],'--execute','--subject',request['subject']['path'],'--subject-sha256',SUBJECT_PIN,'--out',str(d),'--case',case,'--phase',mode],'exact actual harness arguments '+d.name)
  need(r['subject_sha256']==SUBJECT_PIN and r['positive_three_leaf_cas_and_push']is True and r['positive_original_state']==r['positive_state_after'],'real positive setup completed and preserved state '+d.name)
  need(r['formal_adoption_executed']is False and r['product_tests_executed']is False and r['network_used']is False and r['synthetic_schema_not_formal_acceptance']is True,'phase synthetic boundary '+d.name)
  stderr=(Path(run['directory'])/'stderr.bin').read_bytes()
  if expected_exit:
   need(r['error_type']=='AssertionError'and r['error']==MARKERS[case]and ('AssertionError: '+MARKERS[case]).encode()in stderr,'exact selected assertion, not setup failure '+d.name)
  else:need(r['original_publisher_state_preserved']is True and 'error'not in r,'fixed/restored passed entire phase '+d.name)
  need((d/'ORIGINAL_PRIMITIVES.py.txt').read_text()==primitives,'extracted primitives exact subject AST '+d.name)
  work=d/'work';gd=work/'.git';remote=d/'local-remote.git';cfg=configparser.ConfigParser();cfg.read(gd/'config');rcfg=configparser.ConfigParser();rcfg.read(remote/'config')
  need(cfg['remote "origin"']['url']==str(remote)and cfg['core'].getboolean('bare')is False and rcfg['core'].getboolean('bare')is True,'actual isolated worktree/local bare origin '+d.name)
  need(not(gd/'objects/info/alternates').exists()and not(remote/'objects/info/alternates').exists(),'no real product/provider object alternate '+d.name)
  gitrows=read_capture(d/'git-original','SYNTHETIC_CANDIDATE_PRIMITIVES_ONLY');nonzero=[]
  for i,row in enumerate(gitrows,1):
   need(row['command'][:9]==['git','-c','gc.auto=0','-c','maintenance.auto=false','-c','core.hooksPath='+str(d/'empty-hooks'),'-c','protocol.file.allow=always'],'isolated Git invocation '+d.name)
   need(Path(row['cwd'])in [d,work],'actual Git cwd fixture only '+d.name)
   args=row['command'][9:]
   if args[0]=='init':need(args[-1]in[str(work),str(remote)]and args[1]=='--template='+str(d/'empty-template')or args[0]=='init'and args[1:3]==['--bare','--template='+str(d/'empty-template')]and args[-1]==str(remote),'actual Git init only local fixtures '+d.name)
   if args[0]=='remote':need(args==['remote','add','origin',str(remote)],'only configured remote is this local bare '+d.name)
   if args[0]in['push','ls-remote']:need('origin'in args and not any('://'in x or 'github.com'in x for x in args),'no network remote '+d.name)
   if row['actual_process_returncode']!=0:nonzero.append((i,row))
  need(ref(remote,TRAIN)==r['base']and ref(remote,CANDIDATE)==r['tip'],'actual local bare published refs '+d.name)
  base_tree,base_parents,base_commit=commit(gd,r['base']);tip_tree,tip_parents,tip_commit=commit(gd,r['tip']);need(base_parents==[]and tip_parents==[r['base']],'actual positive parent identity '+d.name)
  need(commit(remote,r['base'])[2]==base_commit and commit(remote,r['tip'])[2]==tip_commit,'actual local bare complete commit bytes '+d.name)
  oldleaves=tree(gd,base_tree);newleaves=tree(gd,tip_tree);remoteleaves=tree(remote,tip_tree)
  need(newleaves==remoteleaves and set(oldleaves)==set(newleaves),'actual full tree and remote byte equality '+d.name)
  need({n for n in oldleaves if oldleaves[n]!=newleaves[n]}==CHANGED,'exact positive three-leaf delta '+d.name)
  for n,(blob,content)in oldleaves.items():need(content==('old '+n+'\n').encode(),'actual synthetic old payload '+d.name)
  for n in CHANGED:need(newleaves[n][1]==('new '+n+'\n').encode(),'actual synthetic adopted payload '+d.name)
  original=r['positive_original_state'];need(original['head']==original['train_ref']==r['base']and original['branch']==TRAIN and original['status_hex']=='','recorded original synthetic state '+d.name)
  need(H((gd/'HEAD').read_bytes())==original['head_bytes_sha256']and(gd/'HEAD').read_text().strip()=='ref: refs/heads/'+TRAIN and H((gd/'index').read_bytes())==original['index_sha256']and ref(gd,TRAIN)==r['base'],'current synthetic HEAD/index/train actually preserved, including withdrawn '+d.name)
  if case=='cas':
   w=r['wrong_expected_parent'];selected=ast.parse(ast.unparse(calls[0]),mode='eval').body
   if mode=='withdrawn':selected.args=selected.args[:-1]
   need((d/'SELECTED_CAS.py.txt').read_text()==ast.unparse(selected)+'\n','CAS withdrawal only removes expected-old argument '+d.name)
   expected_nonzero=0 if mode=='withdrawn'else 1;need(len(nonzero)==expected_nonzero,'no unrelated Git failures '+d.name)
   c=next(x for x in gitrows if x['directory']==w['command']['directory']);err=(Path(c['directory'])/'stderr.bin').read_bytes()
   need(c['actual_process_returncode']==w['command']['returncode']and err.hex()==w['command']['stderr'],'CAS underlying command exact original '+d.name)
   if mode=='withdrawn':need(w['refused']is False and w['candidate_after']==w['desired']and c['actual_process_returncode']==0,'withdrawn actually overwrites race ref '+d.name)
   else:need(w['refused']is True and w['candidate_after']==w['race']and c['actual_process_returncode']==128 and w['race'].encode()in err and w['expected_old'].encode()in err and b'expected'in err,'real CAS mismatch rejection exact observed/expected '+d.name)
   need(ref(gd,CANDIDATE)==w['candidate_after'],'actual CAS final local candidate ref '+d.name)
  elif case=='scope':
   need(not nonzero and r['fourth_product_leaf']['refused']is(mode!='withdrawn'),'fourth leaf rule refusal/withdrawal without unrelated Git failure '+d.name)
   need(ref(gd,CANDIDATE)==r['tip'],'scope leaves positive published candidate unchanged '+d.name)
  else:
   selected=ast.parse(ast.unparse(functions['clean'])).body[0]
   if mode=='withdrawn':selected.body[0]=ast.Pass()
   need((d/'SELECTED_CLEAN.py.txt').read_text()==ast.unparse(selected)+'\n','preservation withdrawal only removes publisher-state guard '+d.name)
   controls=r['state_counterexamples'];need(not nonzero and [x['field']for x in controls]==['HEAD','index','train_ref'],'three state controls all collected '+d.name)
   for x in controls:
    need(x['changed_state']!=original and x['refused']is(mode!='withdrawn'),'actual state mutation/refusal '+d.name+' '+x['field'])
   need(ref(gd,CANDIDATE)==r['tip'],'preservation leaves positive candidate unchanged '+d.name)
  phases.append({'case':case,'phase':mode,'exit_code':expected_exit,'exact_assertion':r.get('error'),'setup_positive_passed':True,'current_synthetic_original_state_preserved':True,'git_commands':len(gitrows),'nonzero_git_commands':[{'ordinal':i,'exit_code':v['actual_process_returncode'],'directory':v['directory']}for i,v in nonzero],'raw_result_sha256':H((d/'RESULT.json').read_bytes()),'commands_sha256':H((d/'git-original/subcommands.json').read_bytes()),'local_base':r['base'],'local_tip':r['tip'],'actual_local_bare_refs':r['synthetic_remote_refs']})
 seen=set();allocated=0
 for p in [BASE,*BASE.rglob('*')]:
  st=p.lstat();key=(st.st_dev,st.st_ino)
  if key not in seen:seen.add(key);allocated+=st.st_blocks*512
 need(allocated>=result['runtime_allocated_max_observed']and allocated<=16777216,'current persisted fixture allocation within original bound')
 need(H(Path(request['subject']['path']).read_bytes())==SUBJECT_PIN,'original subject still unchanged after peer')
 report.update(exit_code=0,phases=phases,actual_capture_commands=capture_count,actual_full_stream_bytes=stream_bytes,actual_unique_repository_objects=len(objects),current_fixture_allocated_bytes=allocated,runtime_allocated_max_observed=result['runtime_allocated_max_observed'],capacity=capacity,outer_result_sha256=H((OUTER/'RESULT.json').read_bytes()),request_sha256=H(request_raw),all_selected_assertions_verified=True,all_positive_setups_verified=True,all_original_streams_verified=True,all_synthetic_head_index_train_states_preserved=True,real_local_bare_git_verified=True,formal_refs_not_used_by_recorded_commands=True,scope_limits=['Only pinned extracted candidate primitives were exercised in fresh tiny fixtures. The formal adopter main, formal originals/schema/peer validation, actual root admission, real candidate branch update and GitHub delivery remain unexecuted by these tests.','All original Git commands and configured origins are confined to synthetic phase directories. HEAD/index/train preservation claims here refer to those actual synthetic repositories; this is not a substitute for formal provider before/after receipts.','14,647,296 bytes is the original per-phase observed allocation maximum, not continuous peak/RSS. Current final packet allocation includes terminal metadata written after the last phase observation.','No original test was rerun, no Git subprocess/network/product access or cleanup was performed by this peer. Git objects were checked by read-only decompression and SHA-1, with full local/bare tree comparison.','No publication/delivery or final-product acceptance is certified by this synthetic runtime peer.'])
except BaseException as exc:
 if not findings:findings.append(repr(exc))
 report['exception']=repr(exc)
finally:
 report.update(exit_code=1 if findings else 0,blocking_findings=findings,checked_count=checks)
 (OUT/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'exit_code':report['exit_code'],'checked_count':checks,'blocking_findings':findings,'review_sha256':H((OUT/'REVIEW.json').read_bytes()),'review_bytes':(OUT/'REVIEW.json').stat().st_size},ensure_ascii=False))
raise SystemExit(report['exit_code'])
