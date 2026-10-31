from pathlib import Path
import json,hashlib,stat,re,datetime
O=Path(__file__).parent;B=Path('/workspace/geo337-F9-readers-actual-urce1nqh');P=B/'environment-retry1';S=B/'source';F='4f8a794f4167c3562eb182045102e86e9e37cca9';C=[];bounds=[]
def h(b):return hashlib.sha256(b).hexdigest()
def J(p):return json.loads(Path(p).read_bytes())
def ck(n,b):C.append({'name':n,'ok':bool(b)})
def bind(p):
 p=Path(p);b=p.read_bytes();bounds.append({'path':str(p),'bytes':len(b),'sha256':h(b)});return b
summary=J(P/'SUMMARY.json');res=J(P/'RESULT.json');old=J(B/'RESULT.json');proof=J(B/'NECESSARY_LEAVES.json')
ck('summary_pin',h(bind(P/'SUMMARY.json'))=='a08d1aa92b2f1fcb6cb2b6c7cdbe46c3ab2002f4a2b10867432c87db1c756b4f')
ck('result_pin',h(bind(P/'RESULT.json'))==summary['result_sha256'])
ck('source_exactF9',summary['sha']==res['sha']==proof['sha']==F and res['source']==str(S))
ck('three_result_pass',res['exit']==0 and res['errors']==[] and res['all_three_passed'] is True and summary['all_three_passed'] is True and summary['exit']==0)
ck('sourceprepost_clean',res['source_before']==res['source_after']=={'head':F,'status':'','cached':''})
ck('nativeROOT_recorded_identity_unchanged',res['native_before']==res['native_after'] and res['nativeROOT_identity_unchanged'] is True and summary['nativeROOT_identity_unchanged'] is True)
ck('nativeROOT_exactF9',res['native_before']['state']=={'head':F,'status':'','cached':''})
ck('old_environment_red_preserved',h(bind(B/'RESULT.json'))==res['previous_attempt']['sha256'] and old['exit']==1 and old['all_three_passed'] is False and res['previous_attempt']['outer_exits']==[1,1,1] and res['previous_attempt']['readers_started'] is False)
ck('old_nativeROOT_unchanged',old['native_before']==old['native_after'] and old['nativeROOT_identity_unchanged'] is True)
ck('269_leaf_manifest_pin',h(bind(B/'NECESSARY_LEAVES.json'))==res['necessary_leaves_preverified']['sha256'] and len(proof['proof'])==269 and res['necessary_leaves_preverified']['bad']==[])
ck('269_leaf_size',sum(x['bytes'] for x in proof['proof'])==9473113)
allcmd=[]
for folder,expected_red in [(B,3),(P,0)]+[(P/n,0) for n in ('reader-generate','reader-check','reader-unit')]:
 cmds=J(folder/'subcommands.json');bind(folder/'subcommands.json');allcmd.extend(cmds)
 ck(str(folder)+':redcount',sum(x['actual_process_returncode']!=0 for x in cmds)==expected_red)
 for i,row in enumerate(cmds):
  key=folder.name+':'+str(i)
  ck(key+':source_env_terminal',row['source_sha']==F and row['acceptance_sha']==F and not row['timeout_expired'] and row['ended_epoch']>=row['started_epoch'] and isinstance(row['environment'],dict))
  for n in ['stdout','stderr']:
   raw=(Path(row['directory'])/(n+'.bin')).read_bytes();ck(key+':'+n,len(raw)==row[n+'_bytes'] and h(raw)==row[n+'_sha256'])
  inp=(Path(row['directory'])/'stdin.bin').read_bytes();ck(key+':stdin',h(inp)==row['stdin_sha256'])
  ck(key+':result_exact',J(Path(row['directory'])/'result.json')==row)
parentcmds=J(B/'subcommands.json')
lsrow=next(x for x in parentcmds if 'ls-tree' in x['command'] and '-l' in x['command']);lsraw=(Path(lsrow['directory'])/'stdout.bin').read_bytes();ls={}
for item in lsraw.split(b'\0'):
 if not item:continue
 info,path=item.split(b'\t');mode,typ,oid,size=info.split();ls[path.decode()]={'mode':mode.decode(),'type':typ.decode(),'oid':oid.decode(),'bytes':int(size)}
ck('source_tree_exact269',len(ls)==269 and set(ls)=={x['path'] for x in proof['proof']} and F in lsrow['command'])
batch=next(x for x in parentcmds if 'cat-file' in x['command'] and '--batch' in x['command']);data=(Path(batch['directory'])/'stdout.bin').read_bytes();requests=(Path(batch['directory'])/'stdin.bin').read_text().splitlines();pos=0;blob={}
for oid in requests:
 end=data.index(b'\n',pos);hdr=data[pos:end].decode().split();pos=end+1
 ck('batch_header:'+str(len(blob)),len(hdr)==3 and hdr[0]==oid and hdr[1]=='blob')
 n=int(hdr[2]);raw=data[pos:pos+n];pos+=n;ck('batch_terminator:'+str(len(blob)),data[pos:pos+1]==b'\n');pos+=1
 ck('batch_git_oid:'+str(len(blob)),hashlib.sha1(b'blob '+str(n).encode()+b'\0'+raw).hexdigest()==oid);blob[oid]=raw
ck('batch_complete',pos==len(data) and len(requests)==269)
for i,leaf in enumerate(proof['proof']):
 path=S/leaf['path'];raw=path.read_bytes();mode='100755' if path.stat().st_mode&stat.S_IXUSR else '100644';expected=ls[leaf['path']]
 ck('leaf'+str(i)+':all_bindings',expected['type']=='blob' and expected['oid']==leaf['oid'] and expected['mode']==leaf['mode']==mode and expected['bytes']==leaf['bytes']==len(raw) and leaf['byte_equal_to_F9_blob'] is True and leaf['mode_equal'] is True)
 ck('leaf'+str(i)+':full_original_blob_and_physical_bytes',raw==blob[leaf['oid']] and h(raw)==leaf['sha256'] and not path.is_symlink() and stat.S_ISREG(path.lstat().st_mode))
ck('objects_only_alternates',[str(x.relative_to(S/'.git/objects')) for x in (S/'.git/objects').rglob('*') if x.is_file()]==['info/alternates'])
ck('own_HEAD_F9',(S/'.git/HEAD').read_text().strip()==F)
# Each old failure precedes run_stage: no child receipt and exact environment KeyError preserved.
for stage in old['stages']:
 row=stage['outer_result'];err=(Path(row['directory'])/'stderr.bin').read_text();ck('old_'+stage['stage']+':prelaunch_failure',stage['actual_exit']==1 and row['actual_process_returncode']==1 and "KeyError: 'GEO261_REAPER_LOG'" in err and not Path(stage['inner_receipt']).exists())
# Original tools, command plan and three actual stage receipts.
tools=P/'tool-sources';toolmap={'environment-retry1-driver.py.txt':res['driver_sha256'],'first-preparation-driver.py.txt':old['driver_sha256'],'original-c387-capture.py.txt':res['capture_sha256'],'original-command-plan-v2.json':res['plan_sha256']}
for name,pin in toolmap.items():ck('retainedtool:'+name,h(bind(tools/name))==pin)
plan=J(tools/'original-command-plan-v2.json');items={x['name']:x for x in plan['commands']};times={};unit_count=None;warn_count=0
for idx,stage in enumerate(res['stages']):
 name=stage['stage'];a=summary['stages'][idx];receipt=J(P/name/'receipt.json');bind(P/name/'receipt.json')
 expected=[str(v).replace('<PRIVATE_F9_READING_A_SOURCE>',str(S)).replace('<F9_FULL40_UNBOUND>',F).replace('<FRESH_READING_A_OUT>',str(P)) for v in items['readingA-'+name]['argv']]
 ck(name+':exact_original_plan',stage['argv']==expected and stage['outer_result']['command']==expected)
 ck(name+':source_all_clean',stage['source_before']==stage['source_after']==res['source_before'] and stage['canonical_before_sha256']==stage['canonical_after_sha256'] and stage['canonical_bytes_unchanged'] is True)
 ck(name+':all_exits_zero',stage['actual_exit']==stage['inner_actual_exit']==receipt['actual_exit_code']==a['outer_original_exit']==a['inner_original_exit']==0 and stage['passed'] and receipt['passed'] and receipt['errors']==[])
 ck(name+':receipt_source',receipt['sha']==F and receipt['root']==str(S) and receipt['original_result']==stage['original_result'])
 original=receipt['original_result'];py=receipt['original_command'][0];expectedinner=[py,'-B',str(S/('tests/test_axiom_reader.py' if name=='reader-unit' else 'geometry-guide/sync_axiom_reader.py'))]+(['--check'] if name=='reader-check' else [])
 ck(name+':direct_entry_no_selector',receipt['original_command']==expectedinner and a['original_argv']==expectedinner and original['command']==[py,'-B','/workspace/geo261-environment/reap_children.py',*expectedinner])
 ck(name+':no_optimization',original['environment']['PYTHONOPTIMIZE']=='0' and original['environment']['PYTHONDONTWRITEBYTECODE']=='1')
 ck(name+':timeout_honest',receipt['outer_timeout_seconds'] is None and stage['actual_outer_wrapper_timeout_seconds'] is None and a['actual_original_wrapper_timeout_seconds'] is None and a['assigned_original_timeout_seconds']==(1200 if name=='reader-unit' else 300))
 for path,pin in receipt['tool_sha256'].items():ck(name+':toolpin:'+Path(path).name,h(Path(path).read_bytes())==pin)
 for kind,path in [('inner',P/name/'reaper.jsonl'),('outer',P/(name+'-outer-reaper.jsonl'))]:
  events=[json.loads(l) for l in bind(path).splitlines()];ck(name+':'+kind+'_reaper_terminal',events[0]['event']=='啟用子程序回收' and events[-1]['event']=='完成' and events[-1]['primary_returncode']==0 and len([e for e in events if e.get('primary') is True and e.get('returncode')==0])==1)
  ck(name+':'+kind+'_reaper_argv',events[0]['command']==(expectedinner if kind=='inner' else expected[3:]))
  ck(name+':'+kind+'_summary_terminal',events[-1]==a[kind+'_reaper_final'])
 for stream in ['stdout','stderr']:
  raw=(Path(original['directory'])/(stream+'.bin')).read_bytes();ck(name+':summary_'+stream,raw.decode()==a[stream] and h(raw)==a[stream+'_sha256'] and str(Path(original['directory'])/(stream+'.bin'))==a['original_'+stream+'_path'])
 stdout=(Path(original['directory'])/'stdout.bin').read_text();stderr=(Path(original['directory'])/'stderr.bin').read_text();elapsed=original['ended_epoch']-original['started_epoch'];times[name]=elapsed
 ck(name+':original_elapsed',elapsed==a['seconds'] and elapsed<a['assigned_original_timeout_seconds'])
 if name=='reader-unit':
  unit_count=len(re.findall(r'^test_\w+ ',stderr,re.M));warn_count=stderr.count('ResourceWarning: unclosed file')
  ck('unit51_no_skip',unit_count==51 and re.search(r'Ran 51 tests in [0-9.]+s\n\nOK\n\Z',stderr) is not None and 'skipped' not in stderr.lower() and 'FAIL' not in stderr and 'ERROR' not in stderr)
 else:
  report=json.loads(stdout);ck(name+':actual_report',report==a['original_report_json'] and report['clauses']==207 and report['blocks']==1261 and report['documentHash']=='0bdc4ac2c5a62965c472122a15d6d5bd19ff00ed84e3831b72ebb127b7ae8309' and all(report[k]=='pass' for k in ['five_asserts','independent_ssot','source_sections','counts_single_source','geo120','search','color_tokens']))
  ck(name+':patchcount_original',report['patches']==(90 if name=='reader-generate' else 0))
fail=[x for x in C if not x['ok']]
r={'schema':'geo337-F9-readers-original-actual-peer/1','source_sha':F,'exit_code':int(bool(fail)),'review_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks_count':len(C),'failed_checks':fail,'formal_stage_exits':[0,0,0],'original_unit_tests':unit_count,'original_unit_skips':0,'original_resource_warning_count':warn_count,'original_command_count':len(allcmd),'source_leaves':269,'source_leaf_bytes':9473113,'stage_seconds':times,'initial_environment_exits':[1,1,1],'first_readers_started':False,'nativeROOT_recorded_identity_unchanged':True,'timeout_watchdog_enforced':False,'limits':['未重跑任何產品／閱讀器／Git mutation；只核原完整raw、原cat-file blobs及私有來源實際bytes。','母nativeROOT只核原before/after HEAD/status/index/canonical hash/inode/mtime，沒有重掃正在使用的母ROOT。','原run_stage名義300/300/1200但c387包subreaper實際timeout=None；本peer不聲稱watchdog生效，三項實耗均在原名義界內。','生成器原報patches90但canonical前後hash及Git clean不變；不把patch count改寫為產品變更。','51tests原stderr含ResourceWarning，完整保留，不是skip或fail。','原來源使用F9，不包含main405新政策，也不採用新的exact白名單或CI替代。','原內部未另存子管線不補造；此peer0只驗本三項閱讀器，不外推完整native/browser/SSOT後續變更。'],'bindings':bounds,'checks':C}
(O/'REVIEW.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');(O/'REVIEW.md').write_text(f'# F9 三項原閱讀器實績獨審\n\n{len(C)} 項核對／{len(fail)} 錯，peer exit={int(bool(fail))}。固定F9 `{F}`，269來源葉9,473,113 bytes與原ls-tree／cat-file完整blob及私有檔案一致。\n\n原generate/check/unit均0；單元51tests、零skip。首輪外層缺GEO261_REAPER_LOG的三個啟動前1完整保留，未冒稱執行過閱讀器。三項內外reaper均有完成0，母nativeROOT原前後身分完全相同。\n\n限制：原wrapper真timeout=None，未宣稱名義300/300/1200秒watchdog生效；原ResourceWarning保留。沒有重跑任何產品或修改來源，也不把本結果外推為其他gate通過。\n')
print(json.dumps({'exit_code':int(bool(fail)),'checks':len(C),'failures':fail,'review_sha256':h((O/'REVIEW.json').read_bytes()),'commands':len(allcmd),'unit':unit_count},ensure_ascii=False));raise SystemExit(bool(fail))
