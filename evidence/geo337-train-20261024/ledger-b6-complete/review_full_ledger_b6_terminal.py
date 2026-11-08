from pathlib import Path
import ast, collections, hashlib, json, posixpath, re, subprocess, tarfile
D=Path('/tmp/train337-adversarial');P=Path('/workspace/train337-ledger-b6e1e454-v5');C=Path('/workspace/train337-ledger-cache-b6e1e454');R=Path('/tmp/train337-323-f64d638f-source');F='b6e1e45425f055cd825b259f46ef2c454f3ff13a'
checks=0;findings=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def j(p):return json.loads(Path(p).read_text())
def ck(n,v):
 global checks
 checks+=1
 if not v:findings.append(n)
def git(*args):return subprocess.check_output(['git','-C',str(R),*args])
def val(n,env):
 if isinstance(n,ast.Constant):return n.value
 if isinstance(n,ast.Name):return env[n.id]
 if isinstance(n,(ast.List,ast.Tuple)):
  a=[]
  for x in n.elts:
   if isinstance(x,ast.Starred):a.extend(val(x.value,env))
   else:a.append(val(x,env))
  return tuple(a) if isinstance(n,ast.Tuple) else a
 if isinstance(n,ast.Dict):return {val(k,env):val(v,env) for k,v in zip(n.keys,n.values)}
 if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='dict' and not n.args:return {k.arg:val(k.value,env) for k in n.keywords}
 if isinstance(n,ast.BinOp) and isinstance(n.op,(ast.Add,ast.Mod)):
  a,b=val(n.left,env),val(n.right,env);return a+b if isinstance(n.op,ast.Add) else a%b
 if isinstance(n,ast.Subscript):
  s=n.slice;i=slice(*(val(x,env) if x is not None else None for x in (s.lower,s.upper,s.step))) if isinstance(s,ast.Slice) else val(s,env)
  return val(n.value,env)[i]
 if isinstance(n,ast.ListComp):
  assert len(n.generators)==1;g=n.generators[0];assert isinstance(g.target,ast.Name) and not g.ifs and not g.is_async
  return [val(n.elt,{**env,g.target.id:x}) for x in val(g.iter,env)]
 if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.USub):return -val(n.operand,env)
 raise ValueError(type(n).__name__)
def literals(raw,target):
 env={}
 for n in ast.parse(raw).body:
  if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):key=n.targets[0].id;expr=n.value;add=False
  elif isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and isinstance(n.op,ast.Add):key=n.target.id;expr=n.value;add=True
  else:continue
  try:v=val(expr,env)
  except (ValueError,KeyError,AssertionError):
   if key==target:raise
   continue
  env[key]=env[key]+v if add else v
 return env[target]
r=j(P/'receipt.json');ledger=j(P/'mutants_results.json');mapping=j(P/'CORE_RAW_MAPPING.json');bridge=j(P/'BRIDGE_RAW_INVENTORY.json');obsr=j(P/'observer/receipt.json');req=j(P/'observer/request.json')
tree={}
for z in git('ls-tree','-rz',F).split(b'\0'):
 if z:
  meta,path=z.split(b'\t');mode,typ,oid=meta.split();tree[path.decode()]=(mode.decode(),oid.decode())
paths=set(x['source_file'] for x in ledger.values())|{'tests/mutate.py','tests/mutation_bridge.py','tests/run_tests.py'}
for v in ledger.values():
 for key in ('baseline_identity','mutant_identity','restored_identity'):paths.update(v.get('execution',{}).get(key,{}).get('sidecar',{}).get('files',{}))
paths.update(p for p in tree if (p.startswith('tests/') and p.count('/')==1 and p.endswith(('.py','.c'))) or (p.startswith('tests/fixtures/') and p.endswith('.scene')) or ('/' not in p and p.endswith('.scene')))
# Fixed Git blobs only, batched once; no imports or original judge execution.
names=sorted(paths);request=''.join(F+':'+p+'\n' for p in names).encode();raw=git('cat-file','--batch') if False else subprocess.run(['git','-C',str(R),'cat-file','--batch'],input=request,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout
blobs={};off=0
for p in names:
 end=raw.index(b'\n',off);head=raw[off:end].split();size=int(head[2]);off=end+1;blobs[p]=raw[off:off+size];off+=size+1
 ck('Git object '+p,head[0].decode()==tree[p][1] and head[1]==b'blob')
norm={p:b.replace(b'\r\n',b'\n') for p,b in blobs.items()};muts=literals(norm['tests/mutate.py'],'MUTANTS');defs={x['id']:x for x in muts};restored=literals(norm['tests/mutation_bridge.py'],'RESTORED');tests=literals(norm['tests/run_tests.py'],'TESTS');scenes=[x['scene'] for x in tests]
ck('123 exact unique original IDs',len(muts)==len(defs)==123 and set(defs)==set(ledger));ck('70core53bridge43restored',sum(m.get('binary')=='bridge' for m in muts)==53 and len(restored)==len(set(restored))==43)
retired={m['id'] for m in muts if m.get('retired')};equiv={m['id'] for m in muts if m.get('equivalent')};ck('exact allowed exceptions',retired=={'M35','M51','M55'} and equiv=={'M09','M23','M36','M56','M110'})
include=re.compile(rb'^[ \t]*#[ \t]*include[ \t]+"([^"]+)"',re.M);closure={}
def visit(p):
 if p in closure:return
 b=norm[p];closure[p]=sha(b)
 for match in include.findall(b):
  q=posixpath.normpath(posixpath.join(posixpath.dirname(p),match.decode()))
  if q in norm:visit(q)
  elif q in tree:raise AssertionError('missing Git closure input '+q)
visit('current_geometry.c');visit('geometry-web/web_bridge.c')
closure_hash=sha('\n'.join(p+' '+closure[p] for p in sorted(closure)).encode());core_oracle=sha((sha(norm['tests/run_tests.py'])+'\n'+'\n'.join(p+' '+sha(norm[p]) for p in sorted(set(scenes)))).encode());tool=sha(norm['tests/mutate.py']+b'\0mutation_bridge.py\0'+norm['tests/mutation_bridge.py'])
judgepaths=sorted(p for p in norm if (p.startswith('tests/') and p.count('/')==1 and p.endswith(('.py','.c'))) or (p.startswith('tests/fixtures/') and p.endswith('.scene')) or ('/' not in p and p.endswith('.scene')));judge_rows=[(p,sha(norm[p])) for p in judgepaths]
ck('terminal exact source',r['sourceSHA']==obsr['source_sha']==req['source_sha']==F);ck('original terminal0',r['passed'] and r['exit_code']==r['original_cli_exit']==0 and bool(r['endedUtc']))
verdicts=dict(collections.Counter(v['verdict'] for v in ledger.values()));ck('114/5/1/3 original counts',verdicts=={'killed':114,'equivalent':5,'crashed':1,'retired':3}==r['verdicts']);ck('immutable ledger digest',sha((P/'mutants_results.json').read_bytes())==r['ledger_sha256']==mapping['ledger_sha256']=='c0d6818ab664a3e9ee3250e9e914a17d502bb2a292d400f299b3d7b501d89cbe')
for id,v in ledger.items():
 m=defs[id];p=m.get('file','current_geometry.c');keyparts=[p,m['old'],m['new']]+(['bridge',m['tests']] if m.get('binary')=='bridge' else [])
 ck(id+' canonical record hash',sha(json.dumps({k:x for k,x in v.items() if k not in ('record_sha256','stale_from','stale_why')},sort_keys=True,ensure_ascii=False,separators=(',',':')).encode())==v['record_sha256'])
 ck(id+' exact definition hash',sha(json.dumps(keyparts,ensure_ascii=False).encode())==v['mutant_sha256']);ck(id+' source identity',p==v['source_file'] and p in closure)
 if id in retired:ck(id+' retired no fabricated execution',v['verdict']=='retired' and 'execution' not in v and norm[p].count(m['old'].encode())==0 and v['why']==m['retired']);continue
 ck(id+' unique original anchor',norm[p].count(m['old'].encode())==1);ck(id+' source and closure hashes',v['source_sha256']==sha(norm[p]) and v['closure_sha256']==closure_hash)
 e=v['execution'];oracle=sha(json.dumps([m['tests'],restored,judge_rows],ensure_ascii=False,separators=(',',':')).encode()) if m.get('binary')=='bridge' else core_oracle
 ck(id+' exact original oracle',v['oracle_sha256']==oracle);ck(id+' head and tool',e['head']==F and e['tool_sha256']==tool);ck(id+' equivalence exact', (v['verdict']=='equivalent')==(id in equiv))
phase={x['phase']:x['command'] for x in r['phases']};ck('generation original phases1/0/0/0',[x['command']['actual_process_returncode'] for x in r['phases']]==[1,0,0,0]);ck('original fullCLI scope and limits',r['full_outer_argv'][-1]=='--' and req['original_argv']==['tests/mutate.py'] and r['outer_capture_timeout'] is None and r['stack_after'][0]==16777216 and not r['original_child_timeouts_changed'])
for i,c in enumerate(r['commands']):
 ck('c387 no timeout '+str(i),not c['timeout_expired'])
 for s in ['stdin','stdout','stderr']:
  b=(Path(c['directory'])/(s+'.bin')).read_bytes();ck('c387 exact '+str(i)+s,sha(b)==c[s+'_sha256'] and (s=='stdin' or len(b)==c[s+'_bytes']))
checktxt=(Path(phase['original-external-new-ledger-check']['directory'])/'stdout.bin').read_text();ck('original fresh check no stale blocked or unrun',all(s in checktxt for s in ['紀錄 123 筆','過期 stale 0','受阻 blocked 0','存活 survived 0','無效 invalid 0']))
ck('passive observer complete',obsr['original_completed'] and obsr['original_exit']==0 and obsr['observer_complete'] and obsr['observation_errors']==[] and not obsr['subject_verdicts_changed'] and obsr['source_tool_bytes_unchanged'])
ck('observer tools fixedGit',{p:sha(blobs[p]) for p in obsr['source_tool_sha256_after']}==obsr['source_tool_sha256_after']==req['source_tool_sha256_before']);ck('observer source postflight clean',obsr['source_postflights'][0]['exit_code']==obsr['source_postflights'][1]['exit_code']==0 and bytes.fromhex(obsr['source_postflights'][0]['stdout_hex']).decode().strip()==F and obsr['source_postflights'][1]['stdout_hex']=='')
obs={c['number']:c for c in obsr['commands']};ck('observed original commands unique',len(obs)==len(obsr['commands'])==75)
for n,c in obs.items():
 for s in ['stdout','stderr']:
  x=c[s]
  if x.get('captured'):
   b=Path(x['path']).read_bytes();ck('original observed stream '+str(n)+s,len(b)==x['bytes'] and sha(b)==x['sha256'] and x['representation']=={'str':'original-text-encoded-utf8','bytes':'original-bytes'}[x['python_type']])
ck('rawmapping exactcomplete',mapping['passed'] and not mapping['failures'] and not mapping['unmapped_original_run_tests_observations'] and len(mapping['mappings'])==67);seen=set()
for x in mapping['mappings']:
 id=x['mutant'];e=ledger[id]['execution'];b=x['baseline'];bn=b['command_number'];ck(id+' baseline original argv',b['returncode']==e['baseline']['exit_code']==obs[bn]['returncode']==0 and b['original_args']==obs[bn]['args'] and b['original_args'][0]==[req['python_executable'],str(R/'tests/run_tests.py'),str(C/'_baseline/baseline.exe')]);ck(id+' complete baseline166',e['baseline']['result']['counts']=={'pass':166,'fail':0,'infrastructure':0} and [z['scene'] for z in e['baseline']['result']['cases']]==scenes)
 for s in ['stdout','stderr']:ck(id+' baseline hash '+s,b[s]['sha256']==e['baseline'][s+'_sha256']==obs[bn][s]['sha256'])
 ck(id+' compile0 exact',e['compile_exit_code']==0 and e['compile_command']==['cc','-std=c11','-O2','<source>','-o','<output>','-lm'] and e['compile_sha256']==sha(json.dumps(e['compile_command'],ensure_ascii=False).encode()))
 ck(id+' attempts exactcount',len(x['attempts'])==len(e['attempts']))
 for a,old in zip(x['attempts'],e['attempts']):
  o=a['observed'];n=o['command_number'];ck(id+' one-to-one originalattempt '+str(n),n not in seen and n>bn and a['matches_original_attempt'] and o['original_args']==obs[n]['args'] and o['original_args'][0]==[req['python_executable'],str(R/'tests/run_tests.py'),str(C/id/'_mut.exe')] and o['returncode']==obs[n]['returncode']==old['exit_code']);seen.add(n)
  for s in ['stdout','stderr']:ck(id+' attempt raw '+s,o[s]['sha256']==obs[n][s]['sha256']==old[s+'_sha256'])
  rawtext=Path(o['stdout']['path']).read_text();rows=[z[len('GEOMETRY_TEST_RESULT '):] for z in rawtext.splitlines() if z.startswith('GEOMETRY_TEST_RESULT ')];ck(id+' original structured outcome',len(rows)==1 and json.loads(rows[0].replace(str(R),'<repo>'))==old['result'])
  rr=old['result'];ck(id+' complete166 exactcases',rr['total']==166 and [z['scene'] for z in rr['cases']]==scenes and rr['counts']=={s:sum(z['status']==s for z in rr['cases']) for s in ('pass','fail','infrastructure')})
  if ledger[id]['verdict']=='killed':ck(id+' normal assertionkill',old['exit_code']==1 and rr['counts']['fail']>0 and rr['counts']['infrastructure']==0)
  if ledger[id]['verdict']=='equivalent':ck(id+' actualequivalent survives',old['exit_code']==0 and rr['counts']=={'pass':166,'fail':0,'infrastructure':0})
ck('M20 exact allowed three same crashes',ledger['M20']['verdict']=='crashed' and len(ledger['M20']['execution']['attempts'])==3 and all(a['exit_code']==2 and a['result']['counts']=={'pass':165,'fail':0,'infrastructure':1} and [z['scene'] for z in a['result']['cases'] if z['status']=='infrastructure']==['_test_lshape.scene'] and any(z['scene']=='_test_lshape.scene' and 'exit -11:' in z['detail'] for z in a['result']['cases']) for a in ledger['M20']['execution']['attempts']))
ck('636 bridge streams complete',len(bridge['files'])==636 and bridge['errors']==[]);bmap={}
for x in bridge['files']:
 b=Path(x['path']).read_bytes();ck('bridge stream '+x['id']+x['phase']+x['stream'],len(b)==x['bytes'] and sha(b)==x['sha256']==ledger[x['id']]['execution'][x['phase']][x['stream']+'_sha256']);bmap[(x['id'],x['phase'],x['stream'])]=x
for id,m in defs.items():
 if m.get('binary')!='bridge':continue
 v=ledger[id];e=v['execution'];ck(id+' methods and restoration',e['methods']==m['tests'] and e['restored_methods']==restored and e['byte_restored']);ck(id+' baseline/restored binaryequal',e['baseline_identity']['exe_sha256']==e['restored_identity']['exe_sha256'])
 for phase in ['baseline_build','baseline','mutant_build','mutant','restored_build','restored']:
  row=e[phase];want=1 if phase=='mutant' and id not in equiv else 0;ck(id+phase+' exactcodes',row['exit_code']==row['process_returncode']==want and not row['timed_out'])
  if phase.endswith('build'):continue
  rr=row['result'];methods=m['tests'] if phase=='mutant' else restored;ck(id+phase+' complete zeroerror noskip',rr['requested']==rr['started']==methods and rr['total']==len(methods) and not rr['errors'] and not rr['skipped'] and rr['expected_failures']==rr['unexpected_successes']==0)
  ck(id+phase+' originaloracleargv',row['command'][2]=='tests/bridge_mutation_oracle.py' and row['command'][-len(methods):]==methods)
  ck(id+phase+' exact assertions',all(z.get('kind')=='assertion' and any(z['test']==method or z['test'].startswith(method+' (') for method in methods) and 'bridge closed:' not in z['detail'] for z in rr['failures']) and bool(rr['failures'])==bool(want))
  rawtext=Path(bmap[(id,phase,'stdout')]['path']).read_text();marker='GEOMETRY_BRIDGE_MUTATION_RESULT ';lines=[z[len(marker):] for z in rawtext.splitlines() if z.startswith(marker)]
  portable=lines[0].replace(str(C/'_bridge-work'/F/'repo'),'<work>').replace(str(R),'<repo>').replace(str(C),'<cache>') if lines else ''
  ck(id+phase+' original resultjson',len(lines)==1 and json.loads(portable)==rr)
 for key in ['baseline_identity','mutant_identity','restored_identity']:
  identity=e[key];side=identity['sidecar'];ck(id+key+' freshbinarysidecar',identity['freshness']=='fresh' and identity['exe_sha256']==side['exe_sha256'] and m['file'] in side['files'])
  for p,h in side['files'].items():
   b=norm[p];b=b.replace(m['old'].encode(),m['new'].encode(),1) if key=='mutant_identity' and p==m['file'] else b
   ck(id+key+' source '+p,sha(b)==h)
ck('M118 restored genuinely0 and43 methods',ledger['M118']['execution']['restored_build']['exit_code']==ledger['M118']['execution']['restored']['exit_code']==0 and ledger['M118']['execution']['restored']['result']['total']==43)
report={'schema':'full-ledger-b6-original-actual-peer/1','source_sha':F,'check_count':checks,'findings':findings,'exit_code':int(bool(findings)),'ledger_sha256':r['ledger_sha256'],'coverage':{'definitions':123,'records':len(ledger),'execution_heads':dict(collections.Counter(v['execution']['head'] for v in ledger.values() if 'execution' in v)),'verdicts':verdicts,'core_mapped':67,'bridge':53,'bridge_streams':636,'restored_methods':len(restored),'closure_files':len(closure),'closure_sha256':closure_hash,'original_phases':[1,0,0,0]},'limits':['本輪是b6生成帳本：生成前tracked舊帳本check1保留；原fullCLI、rawmapping、新externalcheck各0。下一L重驗需四phase皆0，不能轉標本輪。','123原AST定義逐一核對；固定Git全部來源/closure/oracle/sidecar變異bytes核對，沒有import或重跑原裁判。','M20原政策允許3次同fixture SIGSEGV，列crashed非斷言killed；3retired無execution；5equivalent仍具原執行證據。','完整core/bridge原流hash與structured JSON核對；core是原text UTF8，非OS predecode bytes。','此報告不冒最終L、完整native、browser、P189或B2跨版本exact通過。','ELF可重建cache不另重封；本次審核來源sidecar/原execution binary identities，不假稱所有ELF payload入Git。']};out=D/'FULL_LEDGER_B6_TERMINAL_ACTUAL_PEER.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(out),'sha256':sha(out.read_bytes()),'checks':checks,'exit':report['exit_code'],'findings':findings[:30]},ensure_ascii=False));raise SystemExit(report['exit_code'])
