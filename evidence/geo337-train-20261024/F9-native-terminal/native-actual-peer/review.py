from pathlib import Path
import ast,datetime,hashlib,json,re,subprocess
P=Path('/tmp/geo337-F9-native-4f8a794f-20261025');W=P/'workflow/native';OUT=Path(__file__).parent
F9='4f8a794f4167c3562eb182045102e86e9e37cca9';checks=[];errors=[];bindings=[]
def h(b):return hashlib.sha256(b).hexdigest()
def read(p):
 p=Path(p);b=p.read_bytes();bindings.append(dict(path=str(p),bytes=len(b),sha256=h(b)));return b
def j(p):return json.loads(read(p))
def ck(n,v):
 checks.append(n)
 if not v:errors.append(n)
def git_leaf(name):
 a=['git','-C','/workspace/geometry-axiom','show',F9+':'+name];r=subprocess.run(a,capture_output=True);ck('Git original '+name,r.returncode==0)
 f=OUT/name.replace('/','_');f.write_bytes(r.stdout);f.with_suffix(f.suffix+'.stderr').write_bytes(r.stderr)
 (OUT/(f.name+'.COMMAND.json')).write_text(json.dumps(dict(command=a,exit_code=r.returncode,stdout_bytes=len(r.stdout),stdout_sha256=h(r.stdout),stderr_bytes=len(r.stderr),stderr_sha256=h(r.stderr)),ensure_ascii=False,indent=2)+'\n')
 return r.stdout
final=j('/tmp/geo337-F9-native-EXEC_FINAL-20261025.json');outer=j('/tmp/geo337-F9-native-launch-20261025/RESULT.json');native=j(P/'RECEIPT.json');workflow=j(W/'receipt.json')
ck('all true original exits1',final['exit_code']==outer['actual_exit']==native['actual_exit']==workflow['exit_code']==1 and 'session_id' not in final)
ck('all sourceF9',outer['source_sha']==native['source_sha']==workflow['sha']==F9)
ck('native true source equality',native['source_before']==native['source_after'] and native['source_before']['head']==F9 and native['source_before']['status']=='')
ck('no metadata errors',native['metadata_errors']==[] and native['passed'] is False)
ck('exact original entry',native['original_native_cli']=='ulimit -s 16384; python3 tests/run_all.py --build' and native['all_suites_selected'] is True and native['selectors']==[] and native['tests_or_compiler_instrumented'] is False)
ck('original receipt binding',native['workflow_receipt_sha256']==h((W/'receipt.json').read_bytes()))
ck('original CI35 pass',native['ci_35_minute_gate_exit']==0 and workflow['ci_timeout_minutes']==35 and workflow['watchdog_factor']==3 and workflow['over_ci_timeout'] is False and workflow['seconds']<2100)
ck('original workflow product exit1',native['original_workflow_exit']==native['reaper_primary_exit']==1)
for name,meta in workflow['files'].items():
 b=read(W/name);ck('workflow original artifact:'+name,len(b)==meta['bytes'] and h(b)==meta['sha256'])
ck('all copied suite logs retained',len(list((W/'run_all-logs').iterdir()))==619)
step=workflow['steps'][1];s=read(W/'steps/01.stdout').decode();serr=read(W/'steps/01.stderr')
ck('native script exact',step['original_run']==step['executed_run'] and step['executed_run'].splitlines()[-1]=='python3 tests/run_all.py --build' and step['executed_run'].splitlines()[0]=='ulimit -s 16384')
ck('native subprocess no timeout',step['result']['exit_code']==step['result']['actual_process_returncode']==1 and step['result']['watchdog_expired'] is False)
expected=jbytes=json.loads(git_leaf('tests/run_all.expected.json'))['suites'];runall=git_leaf('tests/run_all.py')
tree=ast.parse(runall);allowed=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ALLOWED_SKIPS' for t in n.targets))
progress=re.findall(r'^\[(\d+)/230\] (\S+) …$',s,re.M);ck('all progress1to230',[int(x[0]) for x in progress]==list(range(1,231)))
table=[]
for l in s.splitlines():
 m=re.fullmatch(r'((?:c|core|mutation|oracle|py|node):\S+)\s+(\d+|-)\s+(\d+|ok|-)\s+(\d+|FAIL|-)\s+(\d+|-)\s+([0-9.]+|-)\s*(.*)',l)
 if m:table.append(dict(zip(['suite','total','pass','fail','skip','seconds','note'],m.groups())))
ck('exact230table',len(table)==230 and [x['suite'] for x in table]==[x[1] for x in progress] and len({x['suite'] for x in table})==230)
ck('strict expected registry equality',set(expected)=={x['suite'] for x in table})
rows={x['suite']:x for x in table};counted=[];skips=[];failures=[];py_count=0;node_count=0
for row in table:
 name=row['suite'];e=expected[name]
 if e['mode']=='count':
  ck('strict count:'+name,row['total'].isdigit() and int(row['total'])==e['count'])
  ck('count identity:'+name,int(row['pass'])+int(row['fail'])+int(row['skip'])==int(row['total']))
  counted.append(row)
  if int(row['fail']):failures.append(name)
  if int(row['skip']):skips.append(name)
 else:
  ck('exit-code-only no synthetic count:'+name,e['mode']=='exit-code-only' and row['total']=='-' and row['fail']=='-' and row['skip']=='-' and row['seconds']!='-')
  ck('exit-code-only original pass:'+name,row['pass']=='ok' or (name=='mutation:check' and 'exit 0' in row['note']))
 ck('no row environment/timeout/count error:'+name,not any(t in row['note'] for t in ['預期數不符','環境阻擋','逾時','未執行']))
 log=W/'run_all-logs'/(name.replace(':','_')+'.log');ck('every suite original log:'+name,log.is_file())
 if name.startswith('py:'):
  py_count+=1;d=j(log.with_suffix('.json'));u=read(log.with_suffix('.unittest.log')).decode()
  ck('unittest per row:'+name,[d[k] for k in ['total','passed','failed','skipped']]==[int(row[k]) for k in ['total','pass','fail','skip']])
  ck('unittest no hidden crash:'+name,d['import_error'] is None and d['extra_errors']==0 and d['blocked_by_error']==0 and d['unrun_skipped']==0 and d['expected_failed']==0)
  ck('unittest original terminal:'+name,('FAILED (failures=1)' in u) if name=='py:test_geo314_commit_paths' else ('\nOK' in u))
 if name.startswith('node:'):
  node_count+=1;raw=read(log).decode()
  if e['mode']=='count':
   if name=='node:canvas_direct':m=re.search(r'(\d+) pass / (\d+) fail',raw);ck('canvas direct original count',m is not None and [int(m[1]),int(m[2])]==[int(row['pass']),int(row['fail'])])
   else:
    nums={k:int(v) for k,v in re.findall(r'^[ℹ#]\s*(tests|pass|fail|cancelled|skipped|todo)\s+(\d+)\s*$',raw,re.M)}
    ck('node original totals:'+name,[nums.get(k) for k in ['tests','pass','fail','skipped']]==[int(row[k]) for k in ['total','pass','fail','skip']] and nums.get('cancelled')==nums.get('todo')==0)
ck('all Python194 Node32 rows',py_count==194 and node_count==32)
totals={k:sum(int(x[k]) for x in counted) for k in ['total','pass','fail','skip']};ck('aggregate totals',totals==dict(total=5329,**{'pass':5327,'fail':1,'skip':1}))
ck('unique reported failure',failures==['py:test_geo314_commit_paths'])
ck('only allowed GDI skip row',skips==['py:test_gdi_contract'])
gdi=j(W/'run_all-logs/py_test_gdi_contract.json');item=gdi['skip_items'][0]
ck('exact named POSIX skip',len(gdi['skip_items'])==1 and item['count']==1 and item['scope']=='test' and any(a['suite']=='py:test_gdi_contract' and a['test']==item['test'] and a['reason'] in item['reason'] and 'posix' in a['platforms'] for a in allowed))
bad=j(W/'run_all-logs/py_test_geo314_commit_paths.json');rawbad=read(W/'run_all-logs/py_test_geo314_commit_paths.unittest.log').decode()
ck('precise assertion and K leaf',len(bad['failures'])==1 and bad['failures'][0]['test']=='test_geo314_commit_paths.Geo314CommitPaths.test_kernel_has_no_changes_against_the_fixed_integration_base' and "AssertionError: '' != 'geometry-core/kernel/source.c\\n'" in rawbad and 'I24 submission policy must not change K files' in rawbad)
mutation=read(W/'run_all-logs/mutation_check.log').decode();ck('ledger true freshness0','變異表 123 筆,紀錄 123 筆' in mutation and '過期 stale 0 / 受阻 blocked 0 / 退役 retired 3' in mutation and '殺死 killed 114 / 崩潰 crashed 1' in mutation)
ck('strict registry/count diagnostics absent','預期數不符：' not in s and '\n登錄問題' not in s and '沒有登記在 run_all.py' not in s)
for v in workflow['versions']:ck('original environment version exit',v['exit_code']==v['actual_process_returncode']==0 and v['watchdog_expired'] is False)
ck('Node24 and Chrome156 actual',read(workflow['versions'][1]['stdout']).startswith(b'v24.') and read(workflow['versions'][0]['stdout']).startswith(b'Google Chrome 156.'))
limits=['本 peer exit 0 表示收據完整且紅燈分類可信；native 正式結果仍為 1，不標 READY。','未重新執行任何 suite／產品或改來源。未重新讀 ELF payload；完整 cache/sidecar 封包由獨立 collector 接手。','原 per-suite 內部 stdout/stderr 是原 run_all 合併保存方式；沒有冒稱原未另存的 capture_output 管線存在。','exit-code-only 原件沒有 test 級計數，保留原 ok／mutation freshness exit0，不補造斷言數。','必要 browser/owner 整合皆由原總表列為另驗；此 native 結果不外推其通過。','唯一紅是固定整合基底的 K 路徑禁止變更 assertion；是否為舊基底範圍不適用列車需另核授權／來源歷史，不能據本收據免除或放寬。']
report=dict(schema='geo337-F9-full-native-original-actual-peer/1',exit_code=0 if not errors else 1,review_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha=F9,checks=len(checks),failed_checks=errors,formal_native_exit=1,CI35MinuteGateExit=0,over_ci_timeout=False,workflow_seconds=workflow['seconds'],suite_rows=len(table),python_json_suites=py_count,node_suites=node_count,original_workflow_artifacts=len(workflow['files']),original_workflow_artifact_bytes=sum(x['bytes'] for x in workflow['files'].values()),counts=totals,allowed_skip=item,only_failure=bad['failures'][0],failure_original_extra_stdout='geometry-core/kernel/source.c\n',strict_expected_count_registry_equal=True,source_before=native['source_before'],source_after=native['source_after'],limits=limits,bindings=bindings)
(OUT/'ROWS.json').write_text(json.dumps(table,ensure_ascii=False,indent=2)+'\n');(OUT/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(OUT/'REVIEW.md').write_text('# F9 native 完整原件核對\n\n'+f"審查 {len(checks)} 項，{len(errors)} 個證據錯誤；native 原 exit 1，CI35 gate 0。230 suite、5329 計數：5327 pass／1 fail／1 具名 Windows GDI skip。\n\n"+'唯一失敗：`Geo314CommitPaths.test_kernel_has_no_changes_against_the_fixed_integration_base`，斷言 `I24 submission policy must not change K files`，實際差異 `geometry-core/kernel/source.c`。\n\n'+'\n'.join('- '+x for x in limits)+'\n')
print(json.dumps({k:report[k] for k in ['exit_code','checks','failed_checks','formal_native_exit','CI35MinuteGateExit','suite_rows','counts']},ensure_ascii=False));print('REVIEW_SHA256',h((OUT/'REVIEW.json').read_bytes()))
raise SystemExit(report['exit_code'])
