from pathlib import Path
import collections,hashlib,json,re,tarfile
L='7af8c5d80d34cb4f49d01ba67deb78a3a6d725db'
B=Path('/workspace/train337-final-required8-pf3-collection/required-eight')
R=Path('/workspace/train337-final-L-required-eight-7af8c5d8');A=Path(str(R)+'-launch')
O=Path('/workspace/train337-canvas-peer-resume/REQUIRED8_ACTUAL_PACKAGE_PEER.json')
checks=0;findings=[]
def ck(ok,name):
 global checks
 checks+=1
 if not ok:findings.append(name)
def sh(b):return hashlib.sha256(b).hexdigest()
def h(p):return sh(Path(p).read_bytes())
def j(p):return json.loads(Path(p).read_text())
p=j(B/'PACKAGE.json');s=j(B/'SUMMARY.json');iv=j(B/'RAW_INVENTORY.json');im={x['name']:x for x in iv['members']};paths={x['source_path'] for x in iv['members']}
ck(h(p['archive']['path'])==p['archive']['sha256']=='81937992087ce136bdc34ece9d9da468e05beba5c931add719c9fb2501e661e4','pinned tar')
ck(h(B/'RAW_INVENTORY.json')==p['inventory']['sha256']=='b71ba19597cece10c8f807f62aec71e0d213be8ff2630d51898184a74f282ac6','pinned inventory')
ck(len(im)==len(iv['members'])==iv['regular_file_count']==840,'840 distinct original files')
ck(sum(x['bytes'] for x in iv['members'])==iv['logical_original_bytes'],'original logical bytes')
with tarfile.open(p['archive']['path'],'r:gz') as tar:
 members=tar.getmembers();ck(len(members)==841 and len({x.name for x in members})==841 and {x.name for x in members}==set(im)|{'RAW_INVENTORY.json'},'exact841 unique members')
 for m in members:
  ck(m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts,'safe member '+m.name)
  data=tar.extractfile(m).read()
  if m.name=='RAW_INVENTORY.json':ck(data==(B/'RAW_INVENTORY.json').read_bytes(),'embedded original inventory');continue
  x=im[m.name];ck(len(data)==m.size==x['bytes'] and sh(data)==x['sha256'],'member hash '+m.name)
  ck(data==Path(x['source_path']).read_bytes(),'original bytes '+m.name)
r=j(R/'receipt.json');a=j(A/'RESULT.json');sub=R/'required-eight/subject';sr=j(sub/'receipt.json');stage=sr['stages']['required-eight']
ck(p['source_sha']==s['source_sha']==iv['source_sha']==r['source_sha']==a['source_sha']==sr['source_sha']==L,'fixed L throughout')
ck(r['passed'] and not r['errors'] and r['launcher_exit_code']==a['actual_exit']==s['driver_exit']==s['outer_exit']==s['original_exit']==0,'original driver and outer zero')
ck(r['ended_utc'] and len(r['gates'])==1 and r['gates'][0]['gate']=='required-eight' and r['gates'][0]['passed'],'one closed original gate')
ck(s['source_before']==s['source_after']==j(R/'required-eight/before-source.json')==j(R/'required-eight/after-source.json') and s['source_before']['head']==L and s['source_before']['status']=='','closed source guards exact L clean')
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
producer=j(B.parent/'required-eight-collection-launch/RESULT.json');capture(producer)
ck(producer['command'][-2:]==['--gate','required-eight'],'reviewed collector actual gate')
ck(len(captured)==len(set(captured))==34,'34 distinct capture records including collector')
names=['py:test_geo261_source_index','py:test_geo261_candidate_cache','py:test_geo261_graph_product','py:test_geo261_assembly_graph_product','py:test_bridge_integrity','c:integrity','core:run_tests','py:test_geo261_load_residual'];counts=[14,18,5,4,24,432,166,13]
aggregate=inner[2];expected=['-B','tests/run_all.py','--build']+sum((['--only',n] for n in names),[])
ck(aggregate['command'][1:]==expected and aggregate['directory']==s['selected_aggregate_capture'],'exact original eight-only argv')
raw=(Path(aggregate['directory'])/'stdout.bin').read_text();rows=[]
for line in raw.splitlines():
 m=re.match(r'^(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+\d+\.\d+(?:\s|$)',line)
 if m and m[1].startswith(('py:','c:','core:')):rows.append((m[1],*[int(m[k]) for k in range(2,6)]))
ck(len(rows)==8 and collections.Counter(x[0] for x in rows)==collections.Counter(names),'eight unique current aggregate rows')
ck(dict((x[0],x[1:]) for x in rows)=={n:(c,c,0,0) for n,c in zip(names,counts)},'exact original typed counts 676/676/0/0')
ck(re.search(r'合計\(已執行、有計數者\)\s+676\s+676\s+0\s+0',raw) is not None,'actual aggregate total')
ck('部分／示範執行，不可當完整驗收' in raw,'original partial scope disclosure')
ck([(x['name'],x['count'],x['passed'],x['failed'],x['skipped']) for x in s['original_selected_counts']]==[(n,c,c,0,0) for n,c in zip(names,counts)],'summary accurately reproduces original rows')
logs=sub/'evidence/required-eight-suite-logs'
for n,cnt in zip(names,counts):
 if not n.startswith('py:'):continue
 prefix=n.replace(':','_');rr=j(logs/(prefix+'.json'))
 ck(rr['total']==rr['run']==rr['passed']==cnt and all(rr[k]==0 for k in ['failed','skipped','explicit_skipped','unrun_skipped','blocked_by_error','expected_failed','extra_errors']) and rr['import_error'] is None,'current selected Python no skips/errors '+n)
 log=(logs/(prefix+'.unittest.log')).read_text();ck(('Ran '+str(cnt)+' tests in ') in log and '\nOK\n' in log,'selected original unittest transcript '+n)
reapers=list(sub.rglob('reaper.jsonl'));ck(len(reapers)==1,'one original reaper log')
events=[json.loads(x) for x in reapers[0].read_text().splitlines()];ck(events[-1]['event']=='完成' and events[-1]['primary_returncode']==0 and any(x.get('primary') and x.get('returncode')==0 for x in events),'actual nested reaper zero')
ck(j(B/'EXCLUDED_ELF_PAYLOADS.json')==[],'no ELF payload in selected roots')
for root in [R,A]:
 actual={str(x) for x in root.rglob('*') if x.is_file() or x.is_symlink()};ck(actual<=paths,'complete original root '+str(root))
copied=sum('/required-eight-suite-logs/' in x['name'] for x in iv['members'])
result={'schema':'independent-required-eight-actual-package-peer-v1','exit_code':int(bool(findings)),'checks':checks,'findings':findings,'source_sha':L,'archive_sha256':p['archive']['sha256'],'original_files':840,'archive_members':841,'original_bytes':iv['logical_original_bytes'],'original_cli_exit':aggregate['actual_process_returncode'],'nested_wrapper_exit':sr['wrapper_exit'],'stage_execution_exit':stage['execution_exit'],'driver_exit':r['launcher_exit_code'],'outer_exit':a['actual_exit'],'current_selected_suites':8,'current_typed_registered_units':676,'current_passed':676,'current_failed':0,'current_skipped':0,'copied_log_files':copied,'capture_records_including_collector':len(captured),'limitations':['Original v4 outer Recorder.role() labels its orchestration CLI source_role=base/source_sha=b74f9a2 because --base appears in argv. Original field retained; acceptance_sha, explicit --sha L, actual run_all inner source, and before/after Git guards independently bind execution to L.', '676 combines Python tests, C checkpoints and core scenarios; it is not 676 unittest methods.','619 copied suite-log files include older unselected outputs. Only original --only eight argv and its eight current rows count as this execution.','This original runner reused original source/hash-matched native binaries; full native R2 was separately verified. Current mutable ROOT/global cache were not read.','Only required-eight stage passed here; performance, comparison, memo, Q38/PF3 and full acceptance are not inferred. No subject rerun or source edit by reviewer.']}
O.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(O),'sha256':h(O),'checks':checks,'findings':findings,'exit_code':result['exit_code']}));raise SystemExit(result['exit_code'])
