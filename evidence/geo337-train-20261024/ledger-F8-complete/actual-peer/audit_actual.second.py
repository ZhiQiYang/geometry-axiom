import ast,collections,hashlib,json,pathlib,re,sys,time
P=pathlib.Path
OUT=P(__file__).parent
F='75a1e93811a52b69385cbdaf6a09d773ed9052ad'
J=P('/tmp/geo337-full123-F8-job-20261025'); O=P('/tmp/geo337-full123-F8-launch-20261025'); C=P('/workspace/geo337-full123-F8-cache-20261025')
R=P('/tmp/train337-323-f64d638f-source'); W=C/'_bridge-work'/F/'repo'
errors=[]; checks=0; files={}; bodies={}; rows=[]
def ck(ok,msg):
 global checks
 checks+=1
 if not ok: errors.append(msg)
def H(b):return hashlib.sha256(b).hexdigest()
def raw(p):
 p=str(p)
 if p not in bodies:
  q=P(p);ck(q.is_file() and not q.is_symlink(),'regular original '+p);b=q.read_bytes();bodies[p]=b;files[p]={'bytes':len(b),'sha256':H(b)}
 return bodies[p]
def js(p):return json.loads(raw(p))
def verify(p,h,n=None):
 b=raw(p);ck(H(b)==h,'sha256 '+str(p));ck(n is None or len(b)==n,'bytes '+str(p));return b
def dump(name,x):(OUT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def safe(n,env={}):
 if isinstance(n,ast.Constant):return n.value
 if isinstance(n,ast.Name):return env[n.id]
 if isinstance(n,(ast.List,ast.Tuple)):
  out=[]
  for e in n.elts:out.extend(safe(e.value,env)) if isinstance(e,ast.Starred) else out.append(safe(e,env))
  return out
 if isinstance(n,ast.Dict):return {safe(k,env):safe(v,env) for k,v in zip(n.keys,n.values)}
 if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='dict':return {k.arg:safe(k.value,env) for k in n.keywords}
 if isinstance(n,ast.BinOp) and isinstance(n.op,ast.Add):return safe(n.left,env)+safe(n.right,env)
 if isinstance(n,ast.BinOp) and isinstance(n.op,ast.Mod):return safe(n.left,env)%safe(n.right,env)
 if isinstance(n,ast.Slice):return slice(safe(n.lower,env) if n.lower else None,safe(n.upper,env) if n.upper else None,safe(n.step,env) if n.step else None)
 if isinstance(n,ast.Subscript):return safe(n.value,env)[safe(n.slice,env)]
 if isinstance(n,ast.ListComp) and len(n.generators)==1:
  g=n.generators[0];assert isinstance(g.target,ast.Name) and not g.ifs
  return [safe(n.elt,{**env,g.target.id:v}) for v in safe(g.iter,env)]
 raise ValueError(ast.dump(n))
def registry(filename,target):
 env={}
 for n in ast.parse(raw(R/filename)).body:
  if isinstance(n,ast.Assign) and all(isinstance(t,ast.Name) for t in n.targets):
   try:v=safe(n.value,env)
   except (ValueError,KeyError):
    if any(t.id==target for t in n.targets):raise
    continue
   for t in n.targets:env[t.id]=v
  elif isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id==target:env[target]+=safe(n.value,env)
 return env[target]

job=js(J/'receipt.json');outer=js(O/'RESULT.json');terminal=js('/tmp/geo337-full123-F8-EXEC_FINAL-20261025.json')
ledger=js(J/'mutants_results.json');req=js(J/'observer/request.json');obs=js(J/'observer/receipt.json');mapping=js(J/'CORE_RAW_MAPPING.json');inventory=js(J/'BRIDGE_RAW_INVENTORY.json')
ck(job['sourceSHA']==F and outer['source_sha']==F,'all terminal heads F8')
ck(terminal['exit_code']==0 and not terminal.get('session_id'),'true tool terminal 0 no session')
ck(outer['actual_exit']==0 and job['exit_code']==0 and job['original_cli_exit']==0,'outer job original CLI exits')
ck(job['ledger_sha256']==H(raw(J/'mutants_results.json')),'job ledger binding')
verify(job['prepared'],job['prepared_sha256'])
ck(job['source_before']==job['source_after']==job['source_final'],'source before/after/final exact states')
ck(job['source_or_tests_modified_by_driver'] is False and job['original_child_timeouts_changed'] is False,'no driver source/timeouts changes')
commands=[]
for folder in [J,O]:
 for c in js(folder/'subcommands.json'):
  d=P(c['directory']);q=js(d/'request.json');z=js(d/'result.json');ck(z==c,'subcommand catalog '+str(d))
  for k,v in q.items():
   if k not in ('actual_process_returncode','timeout_expired'):ck(c[k]==v,'request binding '+str(d)+' '+k)
  for s in ['stdout','stderr']:verify(d/(s+'.bin'),c[s+'_sha256'],c[s+'_bytes'])
  verify(d/'stdin.bin',c['stdin_sha256']);ck(not c['timeout_expired'],'original no timeout '+str(d))
  ck(c['ended_epoch']>=c['started_epoch'],'original timing '+str(d));commands.append(c)
sub=js(J/'subcommands.json');ck(job['commands']==sub,'job command catalog equals raw')
ck(outer['command']==js(O/'subcommands.json')[0],'outer command equals raw')
ck(terminal['output'].encode()==raw(O/'subcommands/000001/stdout.bin'),'tool output equals original outer stdout')
expected={'original-tracked-ledger-check':1,'original-full123-passive-observer':0,'original-core-stream-map':0,'original-new-ledger-check':0}
ck([p['phase'] for p in job['phases']]==list(expected),'exact four formal phases')
for p in job['phases']:
 ck(p['command'] in sub and p['command']['actual_process_returncode']==expected[p['phase']],'phase original exit '+p['phase'])
for offset,label,role in [(0,'before','root'),(4,'before','seed'),(14,'after','root'),(18,'after','seed'),(22,'final','root'),(26,'final','seed')]:
 state=job['source_'+label][role];cs=sub[offset:offset+4]
 ck([c['command'] for c in cs]==[['git','rev-parse','HEAD'],['git','rev-parse','HEAD^{tree}'],['git','status','--porcelain=v1','--untracked-files=all'],['git','ls-files','--stage','-z']],'state exact commands '+label+role)
 ck(all(c['actual_process_returncode']==0 for c in cs),'state exits '+label+role)
 vals=[raw(P(c['directory'])/'stdout.bin') for c in cs]
 ck(vals[0].decode().strip()==state['head']==F,'state head '+label+role)
 ck(vals[1].decode().strip()==state['tree'],'state tree '+label+role)
 ck(vals[2].decode()==state['status']=='','state clean '+label+role)
 ck(H(vals[3])==state['index'],'state tracked index '+label+role)
for row in job['generated_outputs']:verify(row['snapshot'],row['sha256'],row['bytes'])
ck(req['source_sha']==obs['source_sha']==F and req['original_argv']==['tests/mutate.py'],'original unselected mutator F8')
ck(req['environment']['MUTATE_RESULTS']==str(J/'mutants_results.json') and req['environment']['MUTATE_CACHE']==str(C),'original cache/result scope')
ck(obs['original_completed'] and obs['original_exit']==0 and obs['original_exception'] is None and obs['observer_complete'] and not obs['observation_errors'] and not obs['subject_verdicts_changed'],'observer real complete unmodified')
ck(req['source_tool_sha256_before']==obs['source_tool_sha256_after'] and obs['source_tool_bytes_unchanged'],'original tools before/after')
for name,pin in req['source_tool_sha256_before'].items():
 verify(R/name,pin)
 matches=[p for p in req['source_preflights'] if p['argv']==['git','show',F+':'+name]]
 ck(len(matches)==1 and matches[0]['exit_code']==0 and H(bytes.fromhex(matches[0]['stdout_hex']))==pin,'source original Git bytes '+name)
for label,ps in [('pre',req['source_preflights'][:2]),('post',obs['source_postflights'])]:
 ck([p['exit_code'] for p in ps]==[0,0] and bytes.fromhex(ps[0]['stdout_hex']).decode().strip()==F and ps[1]['stdout_hex']=='','observer source '+label)
verify(req['outer_argv'][0],req['observer_sha256'])
mutants=registry('tests/mutate.py','MUTANTS');defs={m['id']:m for m in mutants}; tests=registry('tests/run_tests.py','TESTS'); restored=registry('tests/mutation_bridge.py','RESTORED')
ck(len(mutants)==len(defs)==len(ledger)==123 and set(defs)==set(ledger),'exact source registry 123 IDs')
ck(len(tests)==166 and len(restored)==43 and len(set(restored))==43,'source core166 bridge43 full oracle list')
cs=obs['commands'];ck([c['number'] for c in cs]==list(range(1,len(cs)+1)),'all observer command numbering')
by_number={c['number']:c for c in cs}
for c in cs:
 ck(c['completed_process_returned'] and c['exception'] is None,'observed completed '+str(c['number']))
 for s in ['stdout','stderr']:
  f=c[s];ck(f['captured'],'observed full stream '+str(c['number'])+s);verify(f['path'],f['sha256'],f['bytes'])
  ck(P(f['path']).is_relative_to(J/'observer/commands'/f"{c['number']:06}"),'observed owned raw '+str(c['number'])+s)
 ck(c['ended_epoch']>=c['started_epoch'],'observer timing '+str(c['number']))
runner=[req['python_executable'],str(R/'tests/run_tests.py')]
corecalls=[c for c in cs if len(c['args'][0])==3 and c['args'][0][:2]==runner]
mapby={m['mutant']:m for m in mapping['mappings']};used=set();expectedinventory=[]
ck(mapping['ledger_sha256']==H(raw(J/'mutants_results.json')) and mapping['observer_request_sha256']==H(raw(J/'observer/request.json')) and mapping['observer_receipt_sha256']==H(raw(J/'observer/receipt.json')),'core map originals pins')
ck(not mapping['failures'] and mapping['passed'],'original mapper pass exact')
ck(not inventory['errors'],'original bridge inventory errors')
def mapped(c):return {'command_number':c['number'],'original_args':c['args'],'returncode':c['returncode'],'stdout':c['stdout'],'stderr':c['stderr']}
def parse(b,prefix,portable):
 lines=[s[len(prefix):] for s in b.decode('utf-8',errors='replace').splitlines() if s.startswith(prefix)]
 if len(lines)!=1:return None
 s=lines[0]
 for a,z in portable:s=s.replace(str(a),z)
 return json.loads(s)
def native(c,e,label):
 ck(c['keyword_arguments_except_env']['cwd']==str(R) and c['selected_environment']['MUTATE_CACHE']==str(C),'core cwd/cache '+label)
 ck(c['returncode']==e['exit_code'],'core original exit '+label)
 for s in ['stdout','stderr']:ck(c[s]['sha256']==e[s+'_sha256'],'core ledger raw '+label+s)
 result=parse(raw(c['stdout']['path']),'GEOMETRY_TEST_RESULT ',[(R,'<repo>')]);ck(result==e['result'],'core full structured raw '+label)
 ck(result['schema']=='geometry-native-tests/1' and result['total']==len(tests) and [t['scene'] for t in result['cases']]==[t['scene'] for t in tests],'core exact declared166 '+label)
 counts={s:sum(t['status']==s for t in result['cases']) for s in ['pass','fail','infrastructure']};ck(counts==result['counts'] and sum(counts.values())==166,'core original counts '+label)
 return counts
for mid,r in ledger.items():
 m=defs[mid];body={k:v for k,v in r.items() if k not in ('record_sha256','stale_from','stale_why')};ck(H(json.dumps(body,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode())==r['record_sha256'],'record integrity '+mid)
 e=r.get('execution'); row={'id':mid,'verdict':r['verdict']}
 if r['verdict']=='retired':
  ck(not e and m.get('retired')==r['why'],'retired source reason no execution '+mid);rows.append(row);continue
 ck(e['head']==F and e['platform']=='posix','actual F8 execution '+mid)
 if e['schema']=='geometry-mutation-execution/1':
  mm=mapby[mid];calls=[c for c in corecalls if c['args'][0][-1]==str(C/mid/'_mut.exe')];ck(len(calls)==len(e['attempts']) and len(calls)>0,'distinct observed attempt count '+mid)
  baseline=[c for c in corecalls if c['args'][0][-1]==str(C/'_baseline/baseline.exe') and c['number']<calls[0]['number']][-1]
  ck(mm['baseline']==mapped(baseline),'last actual baseline mapping '+mid);used.add(baseline['number']);counts=native(baseline,e['baseline'],mid+' baseline');ck(counts=={'pass':166,'fail':0,'infrastructure':0} and baseline['returncode']==0,'baseline fully green '+mid)
  attempt_counts=[]
  for i,(c,a) in enumerate(zip(calls,e['attempts']),1):
   ck(mm['attempts'][i-1]=={'attempt':i,'observed':mapped(c),'matches_original_attempt':True},'exact mapping '+mid+str(i));used.add(c['number']);attempt_counts.append(native(c,a,mid+' attempt '+str(i)))
  ck(e['compile_exit_code']==0 and e['test_command']==['<python>','tests/run_tests.py','<binary>'],'core compile/test original argv '+mid)
  comp=[c for c in cs if '-o' in c['args'][0] and str(C/mid/'_mut.exe') in c['args'][0] and c['number']<calls[0]['number']];ck(len(comp)==1 and comp[0]['returncode']==0,'observed real compile0 '+mid)
  for key,pin in [('baseline_binary',e['baseline_exe_sha256']),('mutant_binary',e['exe_sha256'])]:ck(mm[key]['sha256']==pin and mm[key]['matches_original_execution'] and mm[key]['cache_present'],'mapper original binary verification '+mid+key)
  last=e['attempts'][-1]; counts=attempt_counts[-1]
  if r['verdict']=='killed':ck(last['exit_code']==1 and counts['fail']>0 and counts['infrastructure']==0 and r['killed_by']==[t['scene'] for t in last['result']['cases'] if t['status']=='fail'][:5],'named assertion kill '+mid)
  elif r['verdict']=='equivalent':ck(last['exit_code']==0 and counts=={'pass':166,'fail':0,'infrastructure':0} and bool(m.get('equivalent')),'declared equivalent executed green '+mid)
  elif r['verdict']=='crashed':
   sigs=[[t['scene'] for t in a['result']['cases'] if t['status']=='infrastructure'] for a in e['attempts']]
   ck(len(calls)==3 and len({c['number'] for c in calls})==3 and sigs[0]==sigs[1]==sigs[2]==r['crashed_on'],'three actual same crash scenes '+mid)
   ck(all(a['exit_code']==2 and ac['fail']==0 and all(re.match(r'^INFRA abnormal executable exit -11:',t['detail']) for t in a['result']['cases'] if t['status']=='infrastructure') for a,ac in zip(e['attempts'],attempt_counts)),'three original AV not assertion '+mid)
  else:ck(False,'unexpected core verdict '+mid)
  row.update(schema=e['schema'],head=F,baseline_command=baseline['number'],attempt_commands=[c['number'] for c in calls],attempt_exits=[a['exit_code'] for a in e['attempts']],compile_command=comp[0]['number'])
 else:
  ck(e['schema']=='geometry-bridge-mutation-execution/1' and m.get('binary')=='bridge','bridge source registry '+mid)
  ck(e['methods']==m['tests'] and e['restored_methods']==restored and e['byte_restored'],'bridge exact methods restored '+mid)
  phases=['baseline_build','baseline','mutant_build','mutant','restored_build','restored']
  ck('mutant_attempts' not in e,'no unaccounted bridge retry '+mid)
  for phase in phases:
   a=e[phase];folder=C/'_bridge-baseline'/F if phase in ['baseline_build','baseline'] else C/mid
   for s in ['stdout','stderr']:
    p=folder/a[s+'_file'];b=verify(p,a[s+'_sha256']);expectedinventory.append({'id':mid,'phase':phase,'stream':s,'path':str(p),'bytes':len(b),'sha256':H(b)})
   parsed=parse(raw(folder/a['stdout_file']),'GEOMETRY_BRIDGE_MUTATION_RESULT ',[(W,'<work>'),(R,'<repo>'),(C,'<cache>')]);ck(parsed==a['result'],'bridge complete raw structured result '+mid+phase)
   ck(not a['timed_out'] and a['exit_code']==a['process_returncode'],'bridge original process exit '+mid+phase)
   if phase.endswith('_build'):ck(a['exit_code']==0 and parsed is None,'bridge official compile0 '+mid+phase);continue
   methods=restored if phase in ['baseline','restored'] else m['tests']
   ck(parsed['schema']=='geometry-bridge-mutation-tests/1' and parsed['requested']==methods and parsed['started']==methods and parsed['total']==len(methods),'bridge no missing/reordered methods '+mid+phase)
   ck(not parsed['errors'] and not parsed['skipped'] and parsed['expected_failures']==0 and parsed['unexpected_successes']==0,'bridge no error/skip/XFAIL '+mid+phase)
   ck(a['command'][2]=='tests/bridge_mutation_oracle.py' and a['command'][-len(methods):]==methods,'bridge original exact test argv '+mid+phase)
   green=phase in ['baseline','restored'] or r['verdict']=='equivalent'
   ck((a['exit_code']==0 and not parsed['failures']) if green else (a['exit_code']==1 and bool(parsed['failures']) and all(t['kind']=='assertion' for t in parsed['failures'])),'bridge original green or named assertion kill '+mid+phase)
  for identity in ['baseline_identity','mutant_identity','restored_identity']:
   x=e[identity];ck(x['freshness']=='fresh' and x['exe_sha256']==x['sidecar']['exe_sha256'],'bridge original identity '+mid+identity)
  ck(e['baseline_identity']['exe_sha256']==e['restored_identity']['exe_sha256'],'bridge baseline/restored original ELF match '+mid)
  if r['verdict']=='equivalent':ck(bool(m.get('equivalent')),'bridge declared equivalent '+mid)
  row.update(schema=e['schema'],head=F,phase_exits={p:e[p]['exit_code'] for p in phases},methods=e['methods'],restored_count=len(restored),mutant_failure_tests=[t['test'] for t in e['mutant']['result']['failures']])
 rows.append(row)
ck(set(mapby)=={m for m,r in ledger.items() if r.get('execution',{}).get('schema')=='geometry-mutation-execution/1'} and len(mapby)==67,'all67 core mappings no extra')
ck(mapping['not_core_execution']==[{'id':m,'verdict':r['verdict'],'schema':r.get('execution',{}).get('schema')} for m,r in ledger.items() if m not in mapby],'all56 noncore mappings exact')
ck(inventory['files']==expectedinventory and len(expectedinventory)==636,'bridge exact53 x6 x2 inventory')
notused=[{'command_number':c['number'],'command':c['args'][0],'completed_process_returned':c['completed_process_returned'],'returncode':c['returncode'],'exception':c['exception']} for c in corecalls if c['number'] not in used]
ck(mapping['unmapped_original_run_tests_observations']==notused,'unmapped original core observation exact')
verdicts=dict(collections.Counter(r['verdict'] for r in ledger.values()));heads=dict(collections.Counter(r['execution']['head'] for r in ledger.values() if 'execution' in r));ck(verdicts==job['verdicts'] and heads==job['execution_head_counts']=={F:120},'actual heads/verdicts recomputed')
ck(verdicts=={'killed':114,'equivalent':5,'crashed':1,'retired':3},'expected actual counts')
summary={'schema':'independent-original-full123-actual-peer/1','source_sha':F,'exit_code':0 if not errors else 1,'checks':checks,'errors':errors,'verdicts':verdicts,'execution_head_counts':heads,'core_rows':67,'bridge_rows':53,'retired':[m for m,r in ledger.items() if r['verdict']=='retired'],'equivalent':[m for m,r in ledger.items() if r['verdict']=='equivalent'],'crashed':[m for m,r in ledger.items() if r['verdict']=='crashed'],'observer_commands':len(cs),'original_c387_commands':len(commands),'formal_phase_exits':expected,'ledger_sha256':H(raw(J/'mutants_results.json')),'raw_files_verified':len(files),'raw_bytes_verified':sum(v['bytes'] for v in files.values()),'unmapped_core_calls':notused,'limits':['唯讀審核已終態原件；沒有執行 mutator、正式測試、編譯或新 check。','core 完整 stream 為原 subprocess.run 捕獲 str 的 UTF-8 bytes；沒有冒稱 pre-decode OS pipe bytes。','本審逐筆核原始 mapper 的二進位 hash 與 ledger 綁定，未再次讀取 ELF；原 mapper 與新 check 的正式實績均為 0。','封包完整性、採用 commit 及其他 native/browser/special gates 不在本次接受範圍。','原 tracked-ledger check 1 與 M20 crashed 保持原判，沒有改成 killed 或全專案可合併。'],'bindings':{str(p):H(raw(p)) for p in [J/'receipt.json',J/'mutants_results.json',J/'observer/request.json',J/'observer/receipt.json',J/'CORE_RAW_MAPPING.json',J/'BRIDGE_RAW_INVENTORY.json',O/'RESULT.json',P('/tmp/geo337-full123-F8-EXEC_FINAL-20261025.json')]}}
dump('ROWS.json',rows);dump('RAW_FILES.json',files);dump('ORIGINAL_COMMANDS.json',{'original_c387':commands,'observer_commands':cs});dump('REVIEW.json',summary)
print(json.dumps({k:summary[k] for k in ['exit_code','checks','errors','verdicts','raw_files_verified','raw_bytes_verified']},ensure_ascii=False))
sys.exit(summary['exit_code'])
