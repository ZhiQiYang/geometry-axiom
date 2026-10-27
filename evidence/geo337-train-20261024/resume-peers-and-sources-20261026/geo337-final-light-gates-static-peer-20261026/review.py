from pathlib import Path
import ast,copy,datetime,difflib,hashlib,json,subprocess,types

OUT=Path(__file__).parent
PREP=Path('/tmp/geo337-final-light-gates-preparation-20261026')
SUBJECT=PREP/'run_after_ff_four_gates.py'
PIN='dde595446f259dac13a81e39ec43d64c8df9f28831b2c542ec631acc99b9b4f4'
F='cbf0fb621888596aa14ad5f2349b503e23b1b72d';A='a6f4013364e21bcb7239b5dcc25caac0f6d61f77';S10='82c922a3941525d3a094ac0158bdc7dea57ea360'
COUNT=0;FAIL=[]
def H(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(ok,label):
 global COUNT
 COUNT+=1
 if not ok:FAIL.append(label)
def need(ok,msg):
 if not ok:raise RuntimeError(msg)
raw=SUBJECT.read_bytes();src=raw.decode();tree=ast.parse(raw);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
ck(H(SUBJECT)==PIN,'fixed final subject pin')
pins=json.loads((PREP/'PINS.json').read_bytes())
for field in ['historical_runner','shared_helper','candidate_runner']:ck(H(Path(pins[field]['path']))==pins[field]['sha256'],'pinned dependency '+field)
ck(pins['formal_execution_performed']is False,'preparation is not actual execution')
literal={}
for n in tree.body:
 if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
  try:literal[n.targets[0].id]=ast.literal_eval(n.value)
  except Exception:pass
expected_judges=[['tests/mutate.py','--check'],['tests/architecture_contract.py','--root','.','--manifest','geometry-core/domain-decoupling/product-architecture.json'],['tests/test_architecture_contract.py'],['tests/test_product_architecture.py']]
changed={'tests/mutants_results.json','geometry-core/domain-decoupling/PRODUCT-ARCHITECTURE.md','geometry-core/domain-decoupling/product-architecture-receipt.json'}
ck(literal['SOURCE']==F and literal['JUDGES']==expected_judges and literal['CHANGED']==changed,'exact F four original argv and three product leaves')
historical=ast.parse(Path(pins['historical_runner']['path']).read_bytes());hm=next(n for n in historical.body if isinstance(n,ast.FunctionDef)and n.name=='main')
def fn(m,name):return next(n for n in ast.walk(m)if isinstance(n,ast.FunctionDef)and n.name==name)
ck(ast.dump(fn(main,'snapshot'))==ast.dump(fn(hm,'snapshot')),'604 original snapshot code unchanged')
for exact in ["resource.getrlimit(resource.RLIMIT_STACK)[0]==16777216","shared.combined_allocated()+64*1024**2<=2*1024**3 and shutil.disk_usage(OWN).free>=64*1024**2","if not k.startswith(('GIT_','GEOMETRY_','MUTATE_'))","GITHUB_SHA=SOURCE,GITHUB_WORKSPACE=str(ROOT)","row,stdout,stderr=rec.run([sys.executable,'-B',*judge],cwd=ROOT,timeout=None,check=False,source_sha=SOURCE,source_variant=name)","ok=all(x['exit_code']==0 for x in rows)","exit_code=0 if ok else 1","source_selected_count':3763","full_native_executed':False","full123_executed':False","historical_gates_relabelled':False"]:ck(exact in src,'original guard/scope '+exact)
ck("for owner in [shared.OWNER,Path('/workspace/geometry-axiom')]"in src,'both protected publisher and oldWS metadata')
for field in ['HEAD','index','config','packed-refs','objects/info/alternates','refs','sha256','device','inode','mode','bytes','mtime_ns']:ck(field in ast.get_source_segment(src,fn(main,'publisher_state')),'protected metadata field '+field)
ck('publisher_before==publisher_after'in src and "PUBLISHER.before.json"in src and"PUBLISHER.after.json"in src,'complete protected before/after snapshot enforcement')
ck('index.read_bytes()==index_before'in src and'st.st_mtime_ns'in src and'index_stat.st_mtime_ns'in src,'real source index bytes/stat unchanged')
ck('selected_before==selected_after'in src and 'len(selected)==3763'in src and"len(manifest['fixture_paths'])==5"in src,'selected3763/fivefixture preservation')
ck("expected==manifest['files'][name]"in src and"oid==expected['oid']"in src and"mode==expected['mode']"in src,'fixture and all selected Git identity')
ck("{n for n in final_files if final_files[n]!=manifest['files'][n]}==CHANGED"in src and"changed==CHANGED"in src,'both full non-evidence diff and selected delta exactly three')
ck("H((ROOT/n).read_bytes())==adopted['original_artifact_hashes'][n]"in src,'adopted three original bytes exact')
ck("PREPARED_SOURCE=shared.SOURCE"in src and"prepared['source_sha']==PREPARED_SOURCE"in src and"'prepared_source_sha':PREPARED_SOURCE"in src,'prepared A remains distinct from execution F')
ck("adopted['ledger_execution_sha']==shared.S10"in src and"adopted['architecture_execution_sha']==PREPARED_SOURCE"in src,'S10 ledger and A architecture execution sources retained')
ck(not any(s in src for s in ["git('merge'","git('checkout'","git('update-ref'","git('reset'",'.unlink(','.rmdir(','rmtree(','--force','--force-with-lease']),'runner cannot transition refs or delete/force')
ck('merge --ff-only'in(PREP/'README.md').read_text() and'runner 不移任何 source/ref'in(PREP/'README.md').read_text(),'root-recorded FF explicitly separate')
ck('6997'in(PREP/'README.md').read_text()and'3759'in(PREP/'README.md').read_text(),'native/browser source scope not falsely certified')

# Construct a byte-exact copy of the reviewed before-fix source for the narrow
# counterproof, without touching the author draft or any source checkout.
fixed=ast.get_source_segment(src,fn(main,'publisher_state'))
old_function="""def publisher_state():
   # Read protected metadata only; never run Git against the publisher with the
   # source's private index override. The candidate ref is already final.
   base=shared.OWNER/'.git';result={}
   paths=[base/'HEAD',base/'index']
   if (base/'packed-refs').exists():paths.append(base/'packed-refs')
   paths+=sorted(p for p in (base/'refs').rglob('*')if p.is_file())
   for p in paths:
    st=p.lstat();need(stat.S_ISREG(st.st_mode)and not p.is_symlink(),'protected metadata regular')
    result[str(p.relative_to(base))]={'sha256':H(p.read_bytes()),'device':st.st_dev,'inode':st.st_ino,'mode':st.st_mode,'bytes':st.st_size,'mtime_ns':st.st_mtime_ns}
   return result"""
old_src=src.replace(fixed,old_function);ck(hashlib.sha256(old_src.encode()).hexdigest()=='cb04d3ebf4f0d29691fcc603987490f2f99b85fe22cdbceb49fd7e0536c5b971','byte-exact original before-oldWS-fix reconstructed')
(OUT/'SUBJECT.before-oldws-fix.py').write_text(old_src)
(OUT/'INITIAL_FINDING.json').write_text(json.dumps({'subject_sha256':'cb04d3ebf4f0d29691fcc603987490f2f99b85fe22cdbceb49fd7e0536c5b971','static_exit_code':1,'blocking_findings':[{'id':'B1','reason':'Original protected metadata function omitted /workspace/geometry-axiom/.git; oldWS changes would be undetected.'}],'resolution':'New dde59544 pin snapshots both original Gitdirs; no product guard relaxed.','formal_execution_occurred':False},indent=2)+'\n')
counter=[]
for case in ['fixed','withdrawn','restored']:
 argv=['python3','-B',str(OUT/'probe_oldws.py'),case];p=subprocess.run(argv,capture_output=True,text=True);counter.append({'argv':argv,'actual_process_returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
ck([x['actual_process_returncode']for x in counter]==[0,1,0],'real memory oldWS counterproof010')
ck('OLD_WS_INDEX_MUTATION_UNDETECTED'in counter[1]['stderr'],'withdrawn named failure reason')
(OUT/'OLDWS_COUNTERPROOF.json').write_text(json.dumps({'memory_only':True,'subject_sha256':PIN,'commands':counter},indent=2)+'\n')

# Evaluate the actual guards over metadata dictionaries, no fake receipt is
# written into any producer directory and no formal gate is called.
calls={n.args[1].value:n for n in ast.walk(main)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='need'and len(n.args)==2 and isinstance(n.args[1],ast.Constant)and isinstance(n.args[1].value,str)}
def guard(name,ns):
 try:eval(compile(ast.Expression(copy.deepcopy(calls[name])),'<actual-receipt-binding-guard>','eval'),{'need':need,**ns});return 0
 except RuntimeError:return 1
q={'schema':'final-after-ff-four-light-gates/1','source_sha':F,'prepared_source_sha':A,'root_execution_lease':True,'root_source_exclusive':True,'root_adoption_actual_peer_reviewed':True}
cases=[]
for label,change,expected in [('fixed',{},0),('old-execution-sha',{'source_sha':A},1),('prepared-relabeled-F',{'prepared_source_sha':F},1),('lease-false',{'root_source_exclusive':False},1),('restored',{},0)]:
 got=guard('explicit final execution and historical source binding',{'q':{**q,**change},'SOURCE':F,'PREPARED_SOURCE':A});ck(got==expected,'actual request guard '+label);cases.append({'case':label,'observed_guard_exit':got})
for label,used,expected in [('at-original-bound',2*1024**3-64*1024**2,0),('one-byte-over',2*1024**3-64*1024**2+1,1),('restored',2*1024**3-64*1024**2,0)]:
 ns={'shared':types.SimpleNamespace(combined_allocated=lambda:used),'shutil':types.SimpleNamespace(disk_usage=lambda _:types.SimpleNamespace(free=64*1024**2)),'OWN':None}
 got=guard('original64MiB and combined2GiB gate',ns);ck(got==expected,'original resource guard '+label);cases.append({'case':label,'observed_guard_exit':got})
(OUT/'GUARD_PROOFS.json').write_text(json.dumps({'pure_metadata_only':True,'source_or_filesystem_admission_performed':False,'cases':cases},indent=2)+'\n')
argv=['python3','-B',str(SUBJECT)];p=subprocess.run(argv,capture_output=True,text=True);ck(p.returncode==0 and p.stdout.startswith('PLAN_ONLY:'),'default refuses execution without flag')
(OUT/'DEFAULT_RESULT.json').write_text(json.dumps({'argv':argv,'actual_process_returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2)+'\n')
ck(H(SUBJECT)==PIN,'author subject unchanged after review')
review={'schema':'final-after-ff-four-light-gates-independent-static-peer/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':int(bool(FAIL)),'blocking_findings':FAIL,'checks':COUNT,'subject_sha256':PIN,'executor_sha256':PIN,'fixed_final_sha':F,'historical_prepared_source_sha':A,'ledger_execution_sha':S10,'closed_findings':['B1']if not FAIL else[],'old_ws_counterproof_actual_exits':[x['actual_process_returncode']for x in counter],'source_transition_implemented_by_runner':False,'formal_gate_or_ff_executed':False,'actual_source_or_SHM_read':False,'cleanup_executed':False,'product_or_historical_files_modified':False,'oldws_and_publisher_protected_fields':['HEAD','index','config','packed-refs','refs/*','objects/info/alternates'],'three_changed_paths':sorted(changed),'four_original_argv_suffixes':expected_judges,'resource_thresholds':{'stack_bytes':16777216,'additional_bytes':67108864,'two_OWN_ceiling_bytes':2147483648},'conditions':['Root must complete and capture source ordinary FF with original preflight and source index/fixture preservation; this runner performs no FF.','Root alone binds actual adoption/source receipt pins and three true leases only after independent adoption peer accepts the actual F.','Do not run publisher/ref/oldWS writers concurrently; protected metadata is compared before/after.','All source/cache cleanup remains forbidden; no resource deficit may be solved by this runner.','This static peer is not actual F gate evidence and certifies no native or browser job.'],'limits':['Original selected source remains3763, not native6997/browser3759.','Actual new gate results remain unrun until root execution; S10 and A original receipts retain their original identities.'],'review_script_sha256':H(Path(__file__))}
(OUT/'REVIEW.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
(OUT/'SUMS.sha256').write_text(''.join(H(p)+'  '+p.name+'\n'for p in sorted(OUT.iterdir())if p.is_file()and p.name!='SUMS.sha256'))
print(json.dumps({'exit_code':review['exit_code'],'checks':COUNT,'blocking_findings':FAIL,'review_sha256':H(OUT/'REVIEW.json'),'new_bytes':sum(p.stat().st_size for p in OUT.iterdir()if p.is_file()),'counterproof':review['old_ws_counterproof_actual_exits']}))
raise SystemExit(review['exit_code'])
