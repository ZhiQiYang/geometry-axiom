import ast, collections, hashlib, json, subprocess, sys, tarfile
from pathlib import Path
L='7af8c5d80d34cb4f49d01ba67deb78a3a6d725db'
B=Path('/workspace/train337-q38-terminal-collection')
O=Path('/workspace/train337-canvas-peer-resume')
R=Path('/workspace/train337-L-q38-isolated-results-7af8c5d8')
A=Path('/workspace/train337-L-q38-isolated-launch-7af8c5d8')
E=Path('/workspace/train337-L-q38-execution-capture-20261024')
M=Path('/workspace/train337-L-q38-source-materialization-7af8c5d8')
P=Path('/workspace/train337-q38-terminal-collection-producer')
checks=0;findings=[]
def ck(ok,label):
 global checks
 checks+=1
 if not ok:findings.append(label)
def sh(b):return hashlib.sha256(b).hexdigest()
def h(p):return sh(Path(p).read_bytes())
def j(p):return json.loads(Path(p).read_text())
p=j(B/'PACKAGE.json');s=j(B/'SUMMARY.json');iv=j(B/'RAW_INVENTORY.json');r=j(R/'receipt.json');outer=j(A/'RESULT.json');receipt=j(R/'q38/q38/receipt.json');logs=R/'q38/q38/logs'
ck(h(p['archive']['path'])==p['archive']['sha256']=='acbf826d08488d4d678c68004d0c5e9e5979d0ba05951f5926dc73a6a28a1690','pinned original archive')
ck(h(B/'RAW_INVENTORY.json')==p['inventory']['sha256']=='ddfde6d17da329666ddc2af0278a646e76822fc2e6b69b9c6cfc9a281af29e3a','pinned inventory')
ivmap={x['name']:x for x in iv['members']};paths={x['source_path'] for x in iv['members']}
ck(len(ivmap)==len(iv['members'])==iv['regular_file_count']==448,'unique448 original members')
ck(sum(x['bytes'] for x in iv['members'])==iv['logical_original_bytes'],'logical original byte count')
with tarfile.open(p['archive']['path'],'r:gz') as t:
 ms=t.getmembers();ck(len(ms)==449 and len({m.name for m in ms})==449 and {m.name for m in ms}==set(ivmap)|{'RAW_INVENTORY.json'},'exact449 unique archive entries')
 for member in ms:
  ck(member.isfile() and not member.name.startswith('/') and '..' not in Path(member.name).parts,'safe regular '+member.name)
  data=t.extractfile(member).read()
  if member.name=='RAW_INVENTORY.json':ck(data==(B/'RAW_INVENTORY.json').read_bytes(),'embedded original inventory');continue
  item=ivmap[member.name];ck(len(data)==member.size==item['bytes'] and sh(data)==item['sha256'],'archive hash '+member.name)
  ck(data==Path(item['source_path']).read_bytes(),'actual original bytes '+member.name)
ck(p['source_sha']==s['source_sha']==r['source_sha']==outer['sourceSHA']==L,'all source L')
ck(s['source_before']==s['source_after']==j(R/'q38/before-source.json')==j(R/'q38/after-source.json') and s['source_before']['head']==L and s['source_before']['status']=='','closed original clean source binding')
ck(r['launcher_exit_code']==s['driver_exit']==outer['exitCode']==s['outer_exit']==j(E/'RESULT.json')['exitCode']==s['execution_capture_exit']==0,'all original wrapper exits zero')
ck(r['ended_utc'] and outer['endedUTC'] and len(r['gates'])==1 and r['gates'][0]['gate']=='q38' and r['gates'][0]['passed'] and not r['gates'][0]['errors'] and not outer['errors'],'closed one original gate')
def capture(c):
 d=Path(c['directory']);ck(j(d/'result.json')==c,'original c387 result '+str(d))
 ck(c['source_sha']==c['acceptance_sha']==L and c['actual_process_returncode']==0 and c['timeout_expired'] is False and c['ended_epoch']>=c['started_epoch'],'original c387 exit/SHA '+str(d))
 req=j(d/'request.json');ck(req['command']==c['command'] and req['cwd']==c['cwd'],'original c387 request '+str(d))
 for stream in ('stdout','stderr','stdin'):
  data=(d/(stream+'.bin')).read_bytes();ck(sh(data)==c[stream+'_sha256'],'raw stream hash '+str(d/stream))
  if stream!='stdin':ck(len(data)==c[stream+'_bytes'],'raw stream length '+str(d/stream))
allcaptures=[]
for root,n in ((R,28),(A,1),(E,2),(M,17)):
 cs=j(root/'subcommands.json');ck(len(cs)==n,'exact original command count '+str(root));allcaptures.extend(cs)
 for c in cs:capture(c)
ck(len(allcaptures)==48 and len({x['directory'] for x in allcaptures})==48 and len(s['capture_rows'])==48,'48 distinct original execution/materialization commands')
producer=j(P/'RESULT.json');capture(producer)
ck(producer['command'][-1]=='/workspace/train337-q38-terminal-tools/collect_terminal_q38.py','actual reviewed collector invocation')
mat=j(M/'RESULT.json');ck(mat['sourceSHA']==L and mat['exitCode']==0 and mat['errors']==[] and mat['materializedFileCount']==565 and mat['old22Preserved'] and mat['originalJudgesUnchanged'],'original sameL565 materialization')
ck(s['original_commands']==r['gates'][0]['commands'] and [x['name'] for x in s['original_commands']]==['private-bridge-build','model-base-build','q38'],'exact private build/build/originalq38 commands')
for c in s['original_commands']:
 ck(c['primary_command_exit']==c['outer_process_exit']==0 and c['capture'] in allcaptures,'actual gate command0 '+c['name'])
 env=c['environment_explicit'];ck(env['GITHUB_SHA']==L and env['GEOMETRY_MODEL_BASE']==str(R/'q38/q38-bin/model-base') and all(env[k] is None for k in ('PYTHONOPTIMIZE','PYTHONPATH','PYTHONHOME','NODE_OPTIONS','LD_PRELOAD','AXIOM_ONLY')),'private unmodified assertion environment '+c['name'])
 if c['name']!='private-bridge-build':ck(env['GEOMETRY_TEST_BRIDGE']==str(R/'q38/q38-bin/bridge'),'private bridge '+c['name'])
 reapers=[json.loads(x) for x in Path(c['reaper_log']).read_text().splitlines()]
 ck(h(c['reaper_log'])==c['reaper_sha256'] and reapers[0]['command']==c['original_argv'] and reapers[-1]['event']=='完成' and reapers[-1]['primary_returncode']==0 and any(x.get('primary') and x.get('returncode')==0 for x in reapers),'actual complete reaper '+c['name'])
ck(s['original_commands'][-1]['original_argv'][1:]==['-B','-u','tests/section_profile_mutation_check.py','--receipt',str(R/'q38/q38/receipt.json'),'--logs',str(logs),'--jobs','1'],'exact unfiltered original Q38 CLI')
ck(h(R/'q38/q38/receipt.json')==s['subject_receipt_sha256']=='5381301a30ed3f1182c3ee916cbea831ae513d696ae80f5aa0e3b2a021878a66','subject receipt exact')
# Read fixed Git blob; AST data evaluation never imports or executes the subject.
cmd=['git','-C','/workspace/geometry-axiom','show',L+':tests/section_profile_mutation_check.py']
git=subprocess.run(cmd,capture_output=True);(O/'Q38_ORIGINAL_L_SOURCE.py.txt').write_bytes(git.stdout);(O/'Q38_ORIGINAL_L_SOURCE.stderr.bin').write_bytes(git.stderr)
(O/'Q38_ORIGINAL_L_SOURCE_COMMAND.json').write_text(json.dumps({'command':cmd,'exit_code':git.returncode,'stdout_sha256':sh(git.stdout),'stderr_sha256':sh(git.stderr)},indent=2)+'\n')
ck(git.returncode==0,'Git original Q38 source available')
env={}
def ev(n):
 if isinstance(n,ast.Constant):return n.value
 if isinstance(n,ast.Name):return env[n.id]
 if isinstance(n,(ast.List,ast.Tuple,ast.Set)):
  v=[ev(x) for x in n.elts];return tuple(v) if isinstance(n,ast.Tuple) else set(v) if isinstance(n,ast.Set) else v
 if isinstance(n,ast.Dict):return {ev(k):ev(v) for k,v in zip(n.keys,n.values)}
 if isinstance(n,ast.BinOp) and isinstance(n.op,ast.Add):return ev(n.left)+ev(n.right)
 if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='case':
  names=['id','clause','desc','file','before','after','tests','cause','equivalent','group','error_types','more'];d={'equivalent':None,'group':'native','error_types':(),'more':()};d.update(zip(names,[ev(x) for x in n.args]));d.update({x.arg:ev(x.value) for x in n.keywords});return d
 raise ValueError(ast.dump(n))
for n in ast.parse(git.stdout).body:
 if not isinstance(n,ast.Assign):continue
 try:value=ev(n.value)
 except (ValueError,KeyError):continue
 for target in n.targets:
  if isinstance(target,ast.Name):env[target.id]=value
cases=env['CASES'];case_map={c['id']:c for c in cases};results=receipt['results']
ck(len(cases)==len(case_map)==len(results)==42 and set(case_map)=={f'SPM{i:02d}' for i in range(1,43)},'original exact42 declared cases')
ck(collections.Counter(c['group'] for c in cases)=={'native':37,'model':5},'37native5model case groups')
ck([x['id'] for x in results]==[c['id'] for g in ('native','model') for c in cases if c['group']==g],'exact original execution order without duplicates')
ck(receipt['summary']==s['original_summary']=={'killed':41,'equivalent':1},'original exact summary')
for group,count in (('native',27),('model',20)):
 base=receipt['baselines'][group];ee=base['exception_evidence'];ck(base['exit']==0 and ee['tests_run']==count and ee['requested']==ee['executed']==ee['passed'] and len(set(ee['executed']))==count,'full baseline '+group)
 ck(all(ee[k]==0 for k in ('failures','errors','skipped','expected_failures','unexpected_successes')) and ee['events']==[],'baseline no skip/error '+group)
 ck(j(logs/(group+'-baseline.exceptions.json'))==ee and ('Ran '+str(count)+' tests in ') in (logs/(group+'-baseline.log')).read_text() and '\nOK\n' in (logs/(group+'-baseline.log')).read_text(),'original full baseline output '+group)
caused_types=collections.Counter();case_details=[]
for result in results:
 key=result['id'];case=case_map[key];ee=result['exception_evidence'];group=case['group'];prefix=env['NATIVE_MODULE']+'.'+env['NATIVE_CLASS']+'.' if group=='native' else env['MODEL_MODULE']+'.'+env['MODEL_CLASS']+'.';expected={prefix+x for x in case['tests']}
 ck(result['group']==group and result['clause']==case['clause'] and result['desc']==case['desc'],'original declaration '+key)
 ck(set(ee['requested'])==expected and ee['requested']==ee['executed'] and ee['tests_run']==len(expected)==len(set(ee['executed'])),'all original named methods executed '+key)
 ck(all(ee[k]==0 for k in ('skipped','expected_failures','unexpected_successes')),'no skipped/xfail '+key)
 ck(j(logs/(key+'.exceptions.json'))==ee and ('Ran '+str(len(expected))+' test') in (logs/(key+'.log')).read_text(),'raw original exceptions/log '+key)
 detected=[event for event in ee['events'] if (event['kind']=='failure' and event['exception_type']=='builtins.AssertionError') or (event['kind']=='error' and event['exception_type'] in case['error_types'])]
 caused=[event for event in detected if event['test_id'] in expected and all(token in event['message'] for token in case['cause'])]
 if case['equivalent']:
  ck(key=='SPM24' and result['exit']==0 and result['verdict']=='equivalent' and not ee['events'] and ee['passed']==ee['executed'],'only explicitly declared equivalent SPM24')
 else:
  ck(result['exit']==1 and result['verdict']=='killed' and bool(caused),'original named cause—not crash/wrong-killer '+key)
  if caused:caused_types[caused[0]['exception_type']]+=1
 if group=='native':
  comp=j(logs/('bridge-'+key+'.compile.json'));ck(comp['binary_sha256']==result['binary_sha256'] and result['binary_sha256']!=receipt['baselines']['native']['binary_sha256'],'distinct compiled mutation '+key)
 elif key in ('SPM36','SPM39'):
  comp=j(logs/(key+'.model-base.compile.json'));ck(comp['binary_sha256']==result['adapter_sha256'] and result['adapter_sha256']!=receipt['baselines']['model']['adapter_sha256'],'distinct rebuilt adapter '+key)
 case_details.append({'id':key,'group':group,'exit':result['exit'],'verdict':result['verdict'],'named_methods':len(expected),'cause_types':sorted({x['exception_type'] for x in caused})})
ck(caused_types=={'builtins.AssertionError':39,'geometry_app.model_common.ModelError':2},'39 assertion kills plus two original allowed ModelError kills')
compiles=list(logs.glob('*.compile.json'));ck(len(compiles)==40 and len(list(logs.glob('bridge-*.compile.json')))==38,'38native+2adapter original compile receipts')
for path in compiles:
 comp=j(path);ck(comp['exit']==0 and isinstance(comp['argv'],list) and isinstance(comp['stdout'],str) and isinstance(comp['stderr'],str) and len(comp['binary_sha256'])==64,'original compiler exit/full captured streams '+path.name)
ck(j(logs/'bridge-baseline.compile.json')['binary_sha256']==receipt['baselines']['native']['binary_sha256'],'baseline binary hash binding')
excluded=j(B/'EXCLUDED_ELF_PAYLOADS.json');ck(len(excluded)==2 and sum(x['bytes'] for x in excluded)==2091120,'only two original excluded ELF payloads')
for x in excluded:
 f=Path(x['source_path']);fp=j(f.with_name(f.name+'.fingerprint.json'));ck(f.read_bytes()[:4]==b'\x7fELF' and f.stat().st_size==x['bytes']==fp['exe_size'] and h(f)==x['sha256']==fp['exe_sha256'],'private ELF remains exact '+f.name)
 ck(x['name'] not in ivmap and str(f.with_name(f.name+'.fingerprint.json')) in paths,'payload excluded only, sidecar retained '+f.name)
for root in (R,A,E,M):
 actual={str(x) for x in root.rglob('*') if x.is_file() or x.is_symlink()};ck(actual<=paths|{x['source_path'] for x in excluded},'complete original root namespace '+str(root))
report={'schema':'independent-final-L-Q38-original-actual-peer/1','checks':checks,'exit_code':int(bool(findings)),'findings':findings,'source_sha':L,'original_exit':0,'outer_exit':0,'materialization_exit':0,'materialized_file_count':565,'archive_sha256':p['archive']['sha256'],'archive_members':449,'original_files':448,'original_bytes':iv['logical_original_bytes'],'original_command_captures':48,'collector_command_exit':producer['actual_process_returncode'],'baseline_native_tests':27,'baseline_model_tests':20,'original_mutants':42,'native_mutants':37,'model_mutants':5,'killed':41,'equivalent':1,'equivalent_id':'SPM24','cause_classification':dict(caused_types),'compile_receipts':40,'cases':case_details,'source_blob_sha256':sh(git.stdout),'limitations':['No subject, compiler or browser was rerun. Git L source was parsed as AST data only.','Private bridge/model-base ELF bytes remain in their original locations and are excluded only from archive payload. Original disposable mutant trees/binaries were already cleaned by the original TemporaryDirectory runner; only original exposed compiler/log/exception receipts and hashes can be retained.','Original model-adapter compile argv stores <ADAPTER_BUILD>; its exact code is available in the pinned Git L source. No unexposed subprocess stream or individual OS status is invented.','This is original L 42-case Q38, not the independent later branch with 44 cases. Native full run and other specialist gates are not inferred.']}
dst=O/'FINAL_L_Q38_ACTUAL_PACKAGE_PEER.json';dst.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'checks':checks,'exit_code':report['exit_code'],'findings':findings,'report':str(dst),'sha256':h(dst)},ensure_ascii=False));sys.exit(report['exit_code'])
