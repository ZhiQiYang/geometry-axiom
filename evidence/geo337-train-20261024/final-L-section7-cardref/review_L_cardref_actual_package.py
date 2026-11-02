import ast,hashlib,json,pathlib,subprocess,tarfile
P=pathlib.Path; B=P('/tmp/train337-section7-terminal-collection/cardref');R=P('/workspace/train337-final-L-cardref-7af8c5d8');S=R/'cardref/subject';L='7af8c5d80d34cb4f49d01ba67deb78a3a6d725db';O=P('/tmp/train337-adversarial'); count=0;find=[]
def ck(n,v):
 global count;count+=1
 if not v:find.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(P(p).read_text())
def gh(rel):
 q=subprocess.run(['git','-C','/workspace/geometry-axiom','show',L+':'+rel],capture_output=True);ck('Git '+rel,q.returncode==0);return q.stdout
summary=load(B/'SUMMARY.json');pkg=load(B/'PACKAGE.json');inv=load(B/'RAW_INVENTORY.json');rep=load(S/'report.json');receipt=load(R/'receipt.json');outer=load(str(R)+'-launch/RESULT.json')
ck('archive pin',sha(P(pkg['archive']['path']).read_bytes())==pkg['archive']['sha256']=='5c7c8f70e3493818600a0c3c13457c30934ec1312d98e34f01203fc50c22724a');ck('inventory pin',sha((B/'RAW_INVENTORY.json').read_bytes())==pkg['inventory']['sha256']=='f0e229e376f5a4c95930ca25b2f7a6b5f922d5ad7d4f032271db84d8757eb1fd')
expected={x['name']:x for x in inv['members']};ck('unique inventory',len(expected)==len(inv['members'])==931);nbytes=0
with tarfile.open(pkg['archive']['path'],'r:gz') as tf:
 members=tf.getmembers();ck('exact932 archive members',len(members)==932 and len({m.name for m in members})==932 and {m.name for m in members}==set(expected)|{'RAW_INVENTORY.json'})
 for m in members:
  ck('safe regular member '+m.name,m.isfile() and not P(m.name).is_absolute() and '..' not in P(m.name).parts);data=tf.extractfile(m).read()
  if m.name=='RAW_INVENTORY.json':ck('embedded inventory exact',data==(B/'RAW_INVENTORY.json').read_bytes());continue
  r=expected[m.name];ck('member size '+m.name,len(data)==m.size==r['bytes']);ck('member hash '+m.name,sha(data)==r['sha256']);ck('original immutable bytes '+m.name,data==P(r['source_path']).read_bytes());nbytes+=len(data)
ck('inventory total original bytes',nbytes==inv['logical_original_bytes']==9868629)
ck('terminal source and gate',receipt['source_sha']==rep['source_head']==summary['source_sha']==outer['source_sha']==L and summary['gate']==outer['gate']=='cardref')
ck('true terminal exits',receipt['launcher_exit_code']==outer['actual_exit']==summary['original_exit']==summary['driver_exit']==summary['outer_exit']==0 and receipt['passed'] is True and receipt['errors']==[] and receipt['ended_utc'])
before=load(R/'cardref/before-source.json');after=load(R/'cardref/after-source.json');ck('exact closed source/index/refs restored',before==after==summary['source_before']==summary['source_after'] and before['head']==L and before['status']=='')
rows=load(R/'subcommands.json')+load(str(R)+'-launch/subcommands.json');ck('27 original capture commands',len(rows)==27)
for i,r in enumerate(rows):
 ck(f'capture{i} true exit/sha',r['actual_process_returncode']==0 and not r['timeout_expired'] and r['source_sha']==r['acceptance_sha']==L)
 for stream in ('stdout','stderr'):
  p=P(r['directory'])/(stream+'.bin');data=p.read_bytes();ck(f'capture{i} {stream}',len(data)==r[stream+'_bytes'] and sha(data)==r[stream+'_sha256'])
gate=receipt['gates'][0]; original=gate['commands'][0]; argv=original['original_argv'];ck('full original cardref argv',len(receipt['gates'])==1 and original['primary_command_exit']==original['outer_process_exit']==0 and argv[1:4]==['-B','-u','geometry-core/card-reference/run_mutations.py'] and argv[4:]==['--output',str(S)] and not any(x in argv for x in ['--only','--case']))
ck('no new timeout and original stack',receipt['outer_timeout'] is None and receipt['original_judges_counts_limits_changed'] is False and receipt['stack_during'][0]==16777216)
events=[json.loads(x) for x in (R/'cardref/cardref-reaper.jsonl').read_text().splitlines()];ck('reaper primary0 completed',events[-1]['event']=='完成' and events[-1]['primary_returncode']==0 and any(x.get('primary') and x.get('returncode')==0 for x in events))
# Evaluate only literal metadata constructors from the immutable mutation table AST, never import or run the subject.
table=gh('geometry-core/card-reference/mutations.py');tree=ast.parse(table);env={}
def ev(n):
 if isinstance(n,ast.Constant):return n.value
 if isinstance(n,ast.Name):return env[n.id]
 if isinstance(n,(ast.List,ast.Tuple)):return [ev(x) for x in n.elts]
 if isinstance(n,ast.Dict):return {ev(k):ev(v) for k,v in zip(n.keys,n.values)}
 if isinstance(n,ast.Call) and isinstance(n.func,ast.Name):
  aa=[ev(x) for x in n.args];kw={x.arg:ev(x.value) for x in n.keywords}
  if n.func.id=='change':return dict(zip(['path','old','new'],aa))
  if n.func.id=='mutant':return {'id':aa[0],'case':aa[1],'patches':aa[2:],'model':kw.get('model',False)}
 raise ValueError(ast.dump(n))
for node in tree.body:
 if isinstance(node,ast.Assign):
  for target in node.targets:
   if isinstance(target,ast.Name):env[target.id]=ev(node.value)
mutations=env['MUTATIONS'];ck('complete53 exact registry IDs/order',len(mutations)==len(rep['mutants'])==53 and [m['id'] for m in mutations]==[m['id'] for m in rep['mutants']])
for rel,key in [('geometry-core/card-reference/mutations.py','table_sha256'),('geometry-core/card-reference/run_mutations.py','runner_sha256'),('geometry-core/card-reference/confirmation_probe.c','confirmation_probe_sha256'),('tests/test_grid_card_reference.py','test_sha256')]:ck('original Git tool '+rel,sha(table if key=='table_sha256' else gh(rel))==rep[key])
originals={p:gh(p) for p in rep['source_sha256']}
for p,b in originals.items():ck('original source Git hash '+p,sha(b)==rep['source_sha256'][p])
registered=load('/tmp/train337-final-nonperf-specials-prep/PREPARATION.json')
expected_json=json.loads(gh('tests/run_all.expected.json'));entry=expected_json['suites']['py:test_grid_card_reference'];expected_count=entry['count'] if isinstance(entry,dict) else entry
# schema is inspected without altering the original expected registry.
if isinstance(expected_count,dict):raise ValueError(expected_count)
baseline=rep['baseline'];bc=baseline['counts'];ck('full original baseline43',bc==load(S/'baseline/tests.json') and bc['testsRun']==expected_count==43 and all(bc[x]==0 for x in ['failures','errors','skips','compile_failures','infrastructure_failures']) and baseline['run']['exit_code']==0)
inner=load(B/'INNER_COMMANDS.json'); ck('223 original inner commands',len(inner)==223);compiles=[r for r in inner if P(r['path']).name.startswith('compile-')];ck('116 real compile exit0',len(compiles)==116 and all(r['exit_code']==0 for r in compiles))
for r in inner:
 path=P(r['path']);record=load(path);ck('inner command exact '+str(path),record['command']==r['command'] and record['exit_code']==r['exit_code'])
 for ext in ('.stdout','.stderr'):ck('full exposed inner stream '+str(path)+ext,path.with_name(path.name.replace('.command.json',ext)).exists() and any(v['source_path']==str(path.with_name(path.name.replace('.command.json',ext))) for v in inv['members']))
elfs=load(B/'EXCLUDED_ELF_PAYLOADS.json');elfmap={r['source_path']:r for r in elfs};ck('116 excluded ELF hashes not payloads',len(elfmap)==116 and sum(x['bytes'] for x in elfs)==150289288 and not set(x['name'] for x in elfs)&set(expected))
for r in elfs:ck('ELF original retained size '+r['name'],P(r['source_path']).stat().st_size==r['bytes'])
def link_binary(run,key,expectedhash):
 arg='--bridge' if key=='bridge' else '--model';path=run['command'][run['command'].index(arg)+1];ck('original reported '+path,path in elfmap and elfmap[path]['sha256']==expectedhash)
link_binary(baseline['run'],'bridge',baseline['bridge_sha256']);link_binary(baseline['run'],'model',baseline['model_sha256'])
for m,r in zip(mutations,rep['mutants']):
 ident=m['id'];ck('original mutation identity '+ident,r['case']==m['case'] and r['patches']==m['patches']);current={p:b.decode().replace('\r\n','\n') for p,b in originals.items()}
 for patch in m['patches']:
  p=patch['path'];ck('one exact original anchor '+ident,current[p].count(patch['old'])==1);current[p]=current[p].replace(patch['old'],patch['new'],1)
 for p,b in originals.items():
  data=(current[p].replace('\n','\r\n').encode() if b'\r\n' in b else current[p].encode()) if p in {x['path'] for x in m['patches']} else b
  ck('exact mutant source '+ident+':'+p,sha(data)==r['mutated_source_sha256'][p])
 for phase,folder,ex in [('red',S/ident,1),('restored',S/ident/'restored',0)]:
  rr=r[phase];counts=rr['counts'];ck(ident+' '+phase+' exact original command/count',rr['run']==load(folder/'test.command.json') and counts==load(folder/'tests.json') and rr['run']['exit_code']==ex)
  ck(ident+' '+phase+' normal assertion scope',counts['testsRun']>0 and counts['failures']>0 if phase=='red' else counts['testsRun']>0 and counts['failures']==0)
  ck(ident+' '+phase+' no error/skip/infra',all(counts[k]==0 for k in ['errors','skips','compile_failures','infrastructure_failures']))
  text=(folder/'test.stderr').read_text();ck(ident+' '+phase+' normal unittest stderr',('AssertionError' in text and 'FAILED (failures=' in text) if phase=='red' else '\nOK\n' in text)
  ck(ident+' '+phase+' exact named case argv',rr['run']['command'][rr['run']['command'].index('--case')+1]==m['case'])
  link_binary(rr['run'],'bridge',r['binary_sha256'] if phase=='red' else rr['bridge_sha256']);link_binary(rr['run'],'model',r['model_sha256'] if phase=='red' else rr['model_sha256'])
 ck(ident+' killed and byte restored executable hashes',r['verdict']=='killed' and r['restored']['bridge_sha256']==baseline['bridge_sha256'] and r['restored']['model_sha256']==baseline['model_sha256'])
result={'scope':'Original full card-reference section7 at L plus complete selected output archive; no subject rerun','source_sha':L,'checks':count,'findings':find,'exit_code':int(bool(find)),'original_exit':0,'baseline':bc,'mutants':53,'compile_commands':116,'inner_commands':223,'capture_commands':27,'archive_sha256':pkg['archive']['sha256'],'archive_members':932,'excluded_ELF_count':116,'excluded_ELF_bytes':150289288,'limits':['No hidden pipes or already-cleaned source snapshot are invented.','ELF payloads were not rehashed in this peer; preserved original report hashes are matched to exclusion metadata and current file sizes.','Current shared ROOT is not consulted; closed original HEAD/index/refs and immutable Git L bytes bind the execution.','Initial pure metadata lookup assumed outer receipt.json, then used original RESULT.json; initial reviewer used expected entry tests instead of count and raised KeyError. Both reviewer errors are retained separately, not subject failures.']};out=O/'FINAL_L_CARDREF_ACTUAL_PACKAGE_PEER.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(out),'sha256':sha(out.read_bytes()),'checks':count,'findings':find,'exit_code':result['exit_code']}));raise SystemExit(result['exit_code'])
