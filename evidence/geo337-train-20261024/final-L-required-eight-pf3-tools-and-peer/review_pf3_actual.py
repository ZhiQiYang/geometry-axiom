from pathlib import Path
import ast,collections,hashlib,json,re,subprocess,tarfile
L='7af8c5d80d34cb4f49d01ba67deb78a3a6d725db'
B=Path('/workspace/train337-final-required8-pf3-collection/pf3')
R=Path('/workspace/train337-final-L-pf3-7af8c5d8');A=Path(str(R)+'-launch')
O=Path('/workspace/train337-canvas-peer-resume/PF3_ACTUAL_PACKAGE_PEER.json')
checks=0;findings=[]
def ck(ok,name):
 global checks
 checks+=1
 if not ok:findings.append(name)
def sh(b):return hashlib.sha256(b).hexdigest()
def h(p):return sh(Path(p).read_bytes())
def j(p):return json.loads(Path(p).read_text())
p=j(B/'PACKAGE.json');s=j(B/'SUMMARY.json');iv=j(B/'RAW_INVENTORY.json');im={x['name']:x for x in iv['members']};paths={x['source_path'] for x in iv['members']}
ck(h(p['archive']['path'])==p['archive']['sha256']=='fb3fc268318ec6844433fb35ef6a0c2dc1f72715f11f52d1417e633e068bd127','pinned tar')
ck(h(B/'RAW_INVENTORY.json')==p['inventory']['sha256']=='c9fd3d048f73a79e6cec8aa281356ac3c1bb2ce0f4ac84ac090a527cc7deecd0','pinned inventory')
ck(len(im)==len(iv['members'])==iv['regular_file_count']==4758,'4758 distinct original files')
ck(sum(x['bytes'] for x in iv['members'])==iv['logical_original_bytes'],'original logical bytes')
with tarfile.open(p['archive']['path'],'r:gz') as tar:
 members=tar.getmembers();ck(len(members)==4759 and len({x.name for x in members})==4759 and {x.name for x in members}==set(im)|{'RAW_INVENTORY.json'},'exact4759 unique members')
 for m in members:
  ck(m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts,'safe member '+m.name)
  data=tar.extractfile(m).read()
  if m.name=='RAW_INVENTORY.json':ck(data==(B/'RAW_INVENTORY.json').read_bytes(),'embedded original inventory');continue
  x=im[m.name];ck(len(data)==m.size==x['bytes'] and sh(data)==x['sha256'],'member hash '+m.name)
  ck(data==Path(x['source_path']).read_bytes(),'original bytes '+m.name)
r=j(R/'receipt.json');a=j(A/'RESULT.json');sub=R/'pf3/subject';sr=j(sub/'receipt.json');stage=sr['stages']['pf3']
ck(p['source_sha']==s['source_sha']==iv['source_sha']==r['source_sha']==a['source_sha']==sr['source_sha']==L,'fixed L throughout')
ck(r['passed'] and not r['errors'] and r['launcher_exit_code']==a['actual_exit']==s['driver_exit']==s['outer_exit']==s['original_exit']==0,'original driver and outer zero')
ck(r['ended_utc'] and len(r['gates'])==1 and r['gates'][0]['gate']=='pf3' and r['gates'][0]['passed'],'one closed original gate')
ck(s['source_before']==s['source_after']==j(R/'pf3/before-source.json')==j(R/'pf3/after-source.json') and s['source_before']['head']==L and s['source_before']['status']=='','closed source guards exact L clean')
ck(stage['source_before']==stage['source_after']=={'head':L,'status':''} and stage['execution_exit']==sr['wrapper_exit']==0 and not stage['errors'] and stage['ended_utc'],'nested stage zero source clean')
ck(sr['full_acceptance_passed'] is None and sr['all_required_stages_completed'] is False,'partial stage does not imply full acceptance')
captured=[]
def capture(c,stdin=True,source=L):
 d=Path(c['directory']);captured.append(str(d));ck(j(d/'result.json')==c,'capture result exact '+str(d))
 ck(c['actual_process_returncode']==0 and not c['timeout_expired'] and c['source_sha']==source and c['acceptance_sha']==L and c['ended_epoch']>=c['started_epoch'],'capture exit/sha '+str(d))
 req=j(d/'request.json');ck(req['command']==c['command'] and req['cwd']==c['cwd'],'capture request '+str(d))
 for stream in ['stdout','stderr']:
  raw=(d/(stream+'.bin')).read_bytes();ck(len(raw)==c[stream+'_bytes'] and sh(raw)==c[stream+'_sha256'],'full stream '+str(d/stream))
 if stdin:ck(h(d/'stdin.bin')==c['stdin_sha256'],'original stdin '+str(d))
 else:ck(c['stdin_provided'] is False and c['stdin_sha256']==sh(b'') and not (d/'stdin.bin').exists(),'original absent stdin explicit '+str(d))
for root,num in [(R,26),(A,1)]:
 rows=j(root/'subcommands.json');ck(len(rows)==num,'top capture count '+str(root))
 for row in rows:capture(row)
invocations=list((sub/'invocations').iterdir());ck(len(invocations)==1,'one invocation')
inner=j(invocations[0]/'commands/commands.json');ck(len(inner)==5,'five nested captures')
for row in inner:capture(row,False)
control=list((sub/'control').glob('*/outer-command/000001/result.json'));ck(len(control)==1,'one nested outer CLI')
capture(j(control[0]),False,'b74f9a2ae7ade1555b9be45283adecc097fb76e3')
ctrl=j(control[0]);ck(ctrl['source_role']=={'label':'base','sha':'b74f9a2ae7ade1555b9be45283adecc097fb76e3'} and ctrl['command'][ctrl['command'].index('--sha')+1]==L and ctrl['command'][ctrl['command'].index('--base')+1]==ctrl['source_sha'],'original outer role heuristic disclosed; actual CLI sha L')
producer=j(B.parent/'pf3-collection-launch/RESULT.json');capture(producer)
ck(producer['command'][-2:]==['--gate','pf3'],'reviewed collector actual gate')
ck(len(captured)==len(set(captured))==34,'34 distinct capture records including collector')
evidence=sub/'evidence/pf3';report=j(evidence/'summary.json');original=s['original_pf3_report']
ck(h(evidence/'summary.json')==original['sha256']=='99e698a0785bea2869931db9ac9e79638a74a8a0aaafc3d47f2df48fd7f2d1f4','original PF3 summary binding')
ck(all(report[k]==original[k] for k in ['baseline','mutations','restored','originalSourcesUnchanged']),'collector copies original report unchanged')
ck(inner[2]['command'][1:]==['-B','tests/pf3_mutation_check.py','--out',str(evidence),'--jobs','1'],'original complete PF3 argv jobs1')
source=evidence/'baseline/source/tests/pf3_mutation_check.py';env={}
def ev(n):
 if isinstance(n,ast.Constant):return n.value
 if isinstance(n,ast.Name):return env[n.id]
 if isinstance(n,(ast.List,ast.Tuple)):return [ev(x) for x in n.elts]
 raise ValueError(ast.dump(n))
for n in ast.parse(source.read_text()).body:
 if isinstance(n,ast.Assign):
  try:v=ev(n.value)
  except (ValueError,KeyError):continue
  for target in n.targets:
   if isinstance(target,ast.Name):env[target.id]=v
cases=env['CASES'];ck(len(cases)==19 and len({x[0] for x in cases})==19,'original nineteen distinct mutation declarations')
ck([x['id'] for x in report['mutations']]==[x[0] for x in cases],'all original nineteen cases in table order')
sources=j(evidence/'sources.json');ck(len(sources)==205,'205 original snapshot paths')
gitcmd=['git','-C','/workspace/geometry-axiom','ls-tree','-r',L];g=subprocess.run(gitcmd,capture_output=True)
og=O.parent/'PF3_ORIGINAL_L_TREE';og.with_suffix('.stdout.bin').write_bytes(g.stdout);og.with_suffix('.stderr.bin').write_bytes(g.stderr)
og.with_suffix('.COMMAND.json').write_text(json.dumps({'command':gitcmd,'exit_code':g.returncode,'stdout_sha256':sh(g.stdout),'stderr_sha256':sh(g.stderr)},indent=2)+'\n')
ck(g.returncode==0,'read original fixed Git L tree')
tree={line.split(b'\t',1)[1].decode():line.split(b'\t',1)[0].decode().split() for line in g.stdout.splitlines()}
baseline={rel:(evidence/'baseline/source'/rel).read_bytes() for rel in sources}
for rel,data in baseline.items():
 ck(sh(data)==sources[rel],'original source recorded hash '+rel)
 ck(rel in tree and tree[rel][1]=='blob' and hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==tree[rel][2],'original source Git L blob '+rel)
assertion_details=[]
allcases=[['baseline',[],'all','']]+cases+[['restored',[],'all','']]
records=[report['baseline']]+report['mutations']+[report['restored']]
for case,record in zip(allcases,records):
 name,changes,selection,marker=case;d=evidence/name;normal=name in ['baseline','restored'];expected_exit=0 if normal else 1;expected_counts={'run':20 if normal else 1,'failures':0 if normal else 1,'errors':0,'skipped':0}
 ck(record==j(d/'result.json') and record['id']==name and record['exit']==expected_exit and record['verdict']==('pass' if normal else 'killed') and record['requiredMarker']==marker,'original verdict '+name)
 ck(record['counts']==j(d/'binaries/tests.json')==expected_counts,'full original counts no crash or skip '+name)
 build=j(d/'build/execution.json');tests=j(d/'tests/execution.json')
 ck(build['exit']==0 and tests['exit']==expected_exit and tests['argv'][1:]==['tests/pf3_mutation_check.py','--child',str(d/'binaries'),selection] and build['cwd']==tests['cwd']==str(d/'source'),'original build and named child argv/exits '+name)
 ck(build['seconds']>=0 and tests['seconds']>=0 and all((d/phase/stream).is_file() for phase in ['build','tests'] for stream in ['stdout','stderr']),'all original build/test streams '+name)
 stderr=(d/'tests/stderr').read_text();stdout=(d/'tests/stdout').read_bytes()
 if normal:
  ck('Ran 20 tests in ' in stderr and '\nOK\n' in stderr and stderr.count(' ... ok\n')==20,'complete20 baseline/restored transcript '+name)
 else:
  ck(('FAIL: '+selection+' (tests.test_panel_fill_support.PanelFillSupport.'+selection+')') in stderr and '\nAssertionError:' in stderr and marker in stderr.split('\nAssertionError:',1)[1] and 'FAILED (failures=1)' in stderr and 'Ran 1 test in ' in stderr and '\nERROR:' not in stderr,'exact named assertion cause '+name)
  ck(record['artifacts']['bridge']!=report['baseline']['artifacts']['bridge'],'distinct mutant bridge '+name)
  assertion_details.append({'id':name,'selection':selection,'required_marker':marker,'exit':tests['exit'],'cause':'AssertionError in exact selected test; original marker present in assertion text'})
 expected=dict(baseline)
 for rel,old,new in changes:
  old=old.encode();new=new.encode();ck(expected[rel].count(old)==1,'single original mutation anchor '+name+' '+rel);expected[rel]=expected[rel].replace(old,new)
 actual_paths={str(f.relative_to(d/'source')) for f in (d/'source').rglob('*') if f.is_file()}
 ck(actual_paths==set(expected),'exact205 variant source namespace '+name)
 for rel,data in expected.items():ck((d/'source'/rel).read_bytes()==data,'exact original variant or restored bytes '+name+' '+rel)
 for artifact,digest in record['artifacts'].items():ck(h(d/'binaries'/artifact)==digest,'original artifact bytes '+name+' '+artifact)
 for binary in ['bridge','pf3-algorithm']:
  fp=j(d/'binaries'/(binary+'.fingerprint.json'));f=d/'binaries'/binary
  ck(fp['exe_sha256']==record['artifacts'][binary] and fp['exe_size']==f.stat().st_size and f.read_bytes()[:4]==b'\x7fELF','fresh exact binary and sidecar '+name+' '+binary)
ck(report['originalSourcesUnchanged'] is True,'original source preservation true')
excluded=j(B/'EXCLUDED_ELF_PAYLOADS.json');ck(len(excluded)==42 and sum(x['bytes'] for x in excluded)==42641000,'42 original ELF payloads excluded only from tar')
for x in excluded:ck(Path(x['source_path']).stat().st_size==x['bytes'] and h(x['source_path'])==x['sha256'] and x['name'] not in im,'original excluded ELF retained '+x['name'])
for root in [R,A]:
 actual={str(x) for x in root.rglob('*') if x.is_file() or x.is_symlink()};ck(actual<=paths|{x['source_path'] for x in excluded},'complete original root '+str(root))
events=[json.loads(x) for x in next(sub.rglob('reaper.jsonl')).read_text().splitlines()]
ck(events[-1]['event']=='完成' and events[-1]['primary_returncode']==0 and any(x.get('primary') and x.get('returncode')==0 for x in events),'actual original reaper0')
result={'schema':'independent-PF3-actual-package-peer-v1','checks':checks,'exit_code':int(bool(findings)),'findings':findings,'source_sha':L,'archive_sha256':p['archive']['sha256'],'original_files':4758,'archive_members':4759,'original_bytes':iv['logical_original_bytes'],'baseline_tests':20,'mutants':19,'restored_tests':20,'all_mutants_exact_named_assertion_exit1':True,'original_snapshot_files':205,'original_snapshot_count':21,'build_commands':21,'fresh_binaries':42,'original_cli_exit':inner[2]['actual_process_returncode'],'nested_wrapper_exit':sr['wrapper_exit'],'stage_execution_exit':stage['execution_exit'],'driver_exit':r['launcher_exit_code'],'outer_exit':a['actual_exit'],'capture_records_including_collector':len(captured),'negative_causes':assertion_details,'limitations':['Original v4 outer Recorder.role() labels orchestration source_role=base because --base occurs in argv. acceptance_sha, explicit --sha, actual subject child, and before/after Git guards independently bind L. Original metadata retained.','21 original build invocations build 42 binaries; no unexposed individual compiler OS exit invented. Compiler counts are not tests or mutation kills.','All 42 original ELF payloads remain in their original locations, omitted only from tar; actual bytes/sidecars/recipes retained and checked.','No subject or compile rerun by reviewer; original source snapshots checked directly against fixed L Git blob tree and exact original case mutations. Other performance/CI gates not inferred.']}
O.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(O),'sha256':h(O),'checks':checks,'findings':findings,'exit_code':result['exit_code']}));raise SystemExit(result['exit_code'])
