import ast,hashlib,json,pathlib,subprocess,tarfile
P=pathlib.Path;B=P('/tmp/train337-section7-terminal-collection/axiom');R=P('/workspace/train337-final-L-axiom-7af8c5d8');S=R/'axiom/subject';L='7af8c5d80d34cb4f49d01ba67deb78a3a6d725db';count=0;find=[]
def ck(n,v):
 global count;count+=1
 if not v:find.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(P(p).read_text())
def gh(rel):
 q=subprocess.run(['git','-C','/workspace/geometry-axiom','show',L+':'+rel],capture_output=True);ck('Git '+rel,q.returncode==0);return q.stdout
pkg=load(B/'PACKAGE.json');inv=load(B/'RAW_INVENTORY.json');summary=load(B/'SUMMARY.json');rep=load(S/'report.json');receipt=load(R/'receipt.json');outer=load(str(R)+'-launch/RESULT.json')
ck('archive pin',sha(P(pkg['archive']['path']).read_bytes())==pkg['archive']['sha256']=='c4110ebca24746b9434c49d4bc8e43b7a3b914a25c07aa5307368c9a83574778');ck('inventory pin',sha((B/'RAW_INVENTORY.json').read_bytes())==pkg['inventory']['sha256']=='ce0ab03dc35bc78953f36cb0acb74ffba03a695eeedd8142e030ec1e6ec008f0')
expected={x['name']:x for x in inv['members']};ck('unique187 inventory',len(expected)==len(inv['members'])==187);size=0
with tarfile.open(pkg['archive']['path'],'r:gz') as tf:
 ms=tf.getmembers();ck('exact188 tar members',len(ms)==188 and len({m.name for m in ms})==188 and {m.name for m in ms}==set(expected)|{'RAW_INVENTORY.json'})
 for m in ms:
  ck('safe regular '+m.name,m.isfile() and not P(m.name).is_absolute() and '..' not in P(m.name).parts);data=tf.extractfile(m).read()
  if m.name=='RAW_INVENTORY.json':ck('embedded inventory exact',data==(B/'RAW_INVENTORY.json').read_bytes());continue
  r=expected[m.name];ck('member size '+m.name,len(data)==m.size==r['bytes']);ck('member hash '+m.name,sha(data)==r['sha256']);ck('original bytes '+m.name,data==P(r['source_path']).read_bytes());size+=len(data)
ck('exact total bytes',size==inv['logical_original_bytes']);ck('no ELF in selected OUT and OUTER',load(B/'EXCLUDED_ELF_PAYLOADS.json')==[] and summary['elf_payload_excluded_count']==summary['elf_payload_excluded_bytes']==0)
ck('source L/gate identity',summary['source_sha']==rep['source_head']==receipt['source_sha']==outer['source_sha']==L and summary['gate']==outer['gate']=='axiom');ck('true terminal exits',summary['original_exit']==summary['driver_exit']==summary['outer_exit']==receipt['launcher_exit_code']==outer['actual_exit']==0 and receipt['passed'] and receipt['errors']==[] and receipt['ended_utc'])
before=load(R/'axiom/before-source.json');after=load(R/'axiom/after-source.json');ck('closed source restored',before==after==summary['source_before']==summary['source_after'] and before['head']==L and before['status']=='')
rows=load(R/'subcommands.json')+load(str(R)+'-launch/subcommands.json');ck('27 original c387',len(rows)==27)
for i,r in enumerate(rows):
 ck(f'capture{i} actualexit/identity',r['actual_process_returncode']==0 and not r['timeout_expired'] and r['source_sha']==r['acceptance_sha']==L)
 for stream in ('stdout','stderr'):
  data=(P(r['directory'])/(stream+'.bin')).read_bytes();ck(f'capture{i} {stream}',len(data)==r[stream+'_bytes'] and sha(data)==r[stream+'_sha256'])
gate=receipt['gates'][0];cmd=gate['commands'][0];argv=cmd['original_argv'];ck('full original axioms argv',len(receipt['gates'])==1 and cmd['primary_command_exit']==cmd['outer_process_exit']==0 and argv[1:4]==['-B','-u','geometry-core/card-reference/run_axiom_mutations.py'] and argv[4:]==['--output',str(S)]);ck('original outerlimits',receipt['outer_timeout'] is None and receipt['original_judges_counts_limits_changed'] is False and receipt['stack_during'][0]==16777216)
events=[json.loads(x) for x in (R/'axiom/axiom-reaper.jsonl').read_text().splitlines()];ck('original reaper0 completed',events[-1]['event']=='完成' and events[-1]['primary_returncode']==0)
runner=gh('geometry-core/card-reference/run_axiom_mutations.py');source=gh('geometry-core/modeling/__init__.py');test=gh('tests/test_engineering_model_compatibility.py');ck('original source bytes hash',sha(source)==rep['source_sha256']);ck('original test Git hash',sha(test)==rep['test_sha256'])
# Only literal string/tuple metadata from immutable AST, never execute the runner.
env={}
def ev(n):
 if isinstance(n,ast.Constant):return n.value
 if isinstance(n,ast.Name):return env[n.id]
 if isinstance(n,ast.BinOp) and isinstance(n.op,ast.Add):return ev(n.left)+ev(n.right)
 if isinstance(n,(ast.List,ast.Tuple)):return [ev(x) for x in n.elts]
 raise ValueError(ast.dump(n))
for node in ast.parse(runner).body:
 if isinstance(node,ast.Assign):
  for target in node.targets:
   if isinstance(target,ast.Name) and target.id in ('SCENE','MANIFEST','CONDITION','BASE','CLASS','MUTATIONS','SUITE_TESTS'):env[target.id]=ev(node.value)
ck('all5 original IDs/order',len(rep['mutants'])==len(env['MUTATIONS'])==5 and [x['id'] for x in rep['mutants']]==[x[0] for x in env['MUTATIONS']]);ck('original44 expected',env['SUITE_TESTS']==44)
def phase(d,r,ex,tests,name,label=None):
 ck(name+' original receipt exact',r==load(d/'receipt.json'));ck(name+' correct original exit/count',r['exit_code']==ex and r['tests']==tests and r['errors']==r['skips']==0 and (r['failures']>0 if ex else r['failures']==0))
 for stream in ('stdout','stderr'):ck(name+' '+stream+' original hash',sha((d/(stream+'.log')).read_bytes())==r[stream+'_sha256'])
 text=(d/'stderr.log').read_text();ck(name+' true unittest result',('AssertionError' in text and 'FAILED (failures=' in text and label in text) if ex else '\nOK\n' in text)
 if ex:ck(name+' selected exact method',r['command'][1:]==['-m','unittest',env['CLASS']+name.split('/')[0]] and 'FAIL: '+name.split('/')[0] in text)
 else:ck(name+' full original suite command',r['command'][1:]==['-m','unittest',env['BASE']])
phase(S/'baseline',rep['baseline'],0,44,'baseline');text=source.decode()
for m,r in zip(env['MUTATIONS'],rep['mutants']):
 ident,old,new,testname,label=m;ck(ident+' exact original table',r['id']==ident and r['old']==old and r['new']==new and r['named_test']==testname);ck(ident+' unique original anchor',text.count(old)==1);ck(ident+' exact mutant hash',sha(text.replace(old,new,1).encode())==r['mutant_sha256']);ck(ident+' killed verdict',r['verdict']=='killed');phase(S/ident/'red',r['red'],1,1,testname+'/red',label);phase(S/ident/'restored',r['restored'],0,44,ident+'/restored')
result={'scope':'Original full axiom-version section7 at L plus selected complete OUT/OUTER package, no subject rerun','source_sha':L,'checks':count,'findings':find,'exit_code':int(bool(find)),'original_exit':0,'baseline':{'tests':44,'failures':0,'errors':0,'skips':0},'mutants':5,'restored_full_suite_per_mutant':44,'archive_members':188,'archive_sha256':pkg['archive']['sha256'],'limits':['Only OUT/OUTER selected scope has zero ELF files; this is not a claim about all internal caches or cleanup.','Original exposed stdout/stderr retained, hidden pipes not invented.','Current shared ROOT not consulted; immutable L source and closed source/index/refs captures bind past execution.']};out=P('/tmp/train337-adversarial/FINAL_L_AXIOM_ACTUAL_PACKAGE_PEER.json');out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(out),'sha256':sha(out.read_bytes()),'checks':count,'findings':find,'exit_code':result['exit_code']}));raise SystemExit(result['exit_code'])
