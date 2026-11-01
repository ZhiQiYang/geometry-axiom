from pathlib import Path
import ast,difflib,hashlib,json,sys
P=Path('/tmp/geo337-F8-full123-terminal-preparation-v3-20261025');V2=Path('/tmp/geo337-F8-full123-terminal-preparation-v2-20261025');OUT=Path(__file__).parent
checks=[];bindings={}
def raw(p):
 b=p.read_bytes();bindings[str(p)]=hashlib.sha256(b).hexdigest();return b
def j(p):return json.loads(raw(p))
def check(v,m):checks.append({'check':m,'passed':bool(v)})
def H(b):return hashlib.sha256(b).hexdigest()
prep=j(P/'PREPARATION.json');check(H(raw(P/'PREPARATION.json'))=='0ebbcaa071dded4b8baf0e6050fa4e5828641818bf2c77ea40ea2aaf17b6ec8a','fixed preparation pin')
for f in prep['files']:
 p=Path(f['path']);p=p if p.is_absolute() else P/p;b=raw(p);check(len(b)==f['bytes'] and H(b)==f['sha256'],'frozen leaf '+f['path'])
check(len(prep['files'])==270,'full270 frozen leaf scope')
check(H(raw(V2/'PREPARATION.json'))==prep['v2_preparation_sha256']=='45058091b308950ee18af616f6add2e4fe6535dc130cd5dc390f57f175d3369f','v2 unchanged preparation')
old=raw(V2/'terminal_guard.py').decode();new=raw(P/'terminal_guard.py').decode()
def funcs(s):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
a,b=funcs(old),funcs(new)
check(set(b)-set(a)=={'denied_foreign_cwd'},'only one new process classifier')
for name in set(a)-{'terminal_lease'}:check(a[name]==b[name],'original function unchanged '+name)
check('fcntl.LOCK_EX|fcntl.LOCK_NB' in new and "for name in LOCKS:" in new,'two original nonblocking leases retained')
for token in ["os.getresuid()==(task_uid,task_uid,task_uid)","target.stat().st_uid==task_uid","need(key not in fields", "fields.get('Pid')==[str(pid)]", "len(uid_fields)==4", "task_uid not in uids", "need(not hit", "except PermissionError as error:", "status_sha256", "'cwd_status':'permission-denied-not-inspected'", "'all_system_cwds_inspected':not foreign_denied"]:check(token in new,'narrow process scope guard '+token)
# Exact full diffs bind the only changes, independently generated from old/new files.
diff=''
for n in ['terminal_guard.py','verify_terminal.py','collect_terminal.py']:
 diff+=''.join(difflib.unified_diff(raw(V2/n).decode().splitlines(True),raw(P/n).decode().splitlines(True),fromfile='v2/'+n,tofile='v3/'+n))
check(diff==raw(P/'V2_TO_V3_PROCESS_SCOPE_ONLY.diff').decode(),'complete three-file diff exact')
for n in ['SCOPE.json','REQUEST.unbound.json','check_terminal_metadata.py','ADOPTION_PLAN.md']:
 check(raw(V2/n)==raw(P/n),'original scope/metadata/adoption unchanged '+n)
# Collector retains original scope/state/admission/tar logic; only explicit audit object attachment changes.
oldc=raw(V2/'collect_terminal.py').decode();newc=raw(P/'collect_terminal.py').decode()
newc=newc.replace('with terminal_lease() as process_scope:', 'with terminal_lease():').replace("'process_scope':process_scope,",'').replace("        (out/'PROCESS_SCOPE.json').write_text(json.dumps(process_scope,ensure_ascii=False,indent=2)+'\\n')\n",'')
check(newc==oldc,'collector whole-byte equality after only scope metadata attachments')
proof=j(P/'PROCESS_SCOPE_PROOF.json');check(proof['actual_exits']==[0,1,0] and proof['exit']==0 and proof['cases_per_phase']==13,'synthetic true013 exits')
check(H(raw(P/'PROCESS_SCOPE_PROOF.json'))==prep['metadata_proof_sha256'],'proof exact binding')
capture=j(P/'process-scope-original-capture-r2/subcommands.json')
for i,row in enumerate(proof['rows']):
 c=row['original_command'];check(c==capture[i],'original c387 command catalog '+str(i));d=Path(c['directory']);check(j(d/'result.json')==c,'original result'+str(i))
 for s in ['stdout','stderr']:
  body=raw(d/(s+'.bin'));check(H(body)==c[s+'_sha256'] and len(body)==c[s+'_bytes'],'raw '+str(i)+s)
 check(H(raw(d/'stdin.bin'))==c['stdin_sha256'],'stdin'+str(i));check(c['actual_process_returncode']==[0,1,0][i] and not c['timeout_expired'],'actual exit '+str(i))
 phase=row['phase'];r=j(P/f'process-scope-fixtures-r2/{phase}/RESULT.json');check(json.loads(raw(d/'stdout.bin'))==r,'complete original stdout equal fixture RESULT '+phase)
 check(r['exit']==c['actual_process_returncode'] and len(r['cases'])==13,'all13 original vectors '+phase)
 check(r['actual_proc_read'] is False and r['actual_global_locks_used'] is False and r['product_test_executed'] is False,'private proof scope '+phase)
 check(r['source_sha256']==H(raw(V2/'terminal_guard.py' if phase=='withdrawn' else P/'terminal_guard.py')),'actual original v2/v3 subject pin '+phase)
 check([x['case'] for x in r['cases'] if not x['passed']]==(['foreign-denied-recorded'] if phase=='withdrawn' else []),'exact negative control cause '+phase)
 for cse in r['cases']:
  check(cse['actual_allowed']==(cse['case'] in (['same-uid-readable-nonconsumer'] if phase=='withdrawn' else ['foreign-denied-recorded','same-uid-readable-nonconsumer'])),'actual allowed case '+phase+cse['case'])
  if cse['case']=='foreign-denied-recorded' and phase!='withdrawn':
   x=cse['audit'];check(x['all_system_cwds_inspected'] is False and len(x['unreadable_foreign_cwds'])==1,'unknown foreign remains explicit '+phase)
   q=x['unreadable_foreign_cwds'][0];check(q['cwd'] is None and q['cwd_status']=='permission-denied-not-inspected' and q['not_a_claim_of_system_wide_cwd_visibility'] is True,'no fabricated cwd '+phase)
   status=P/f'process-scope-fixtures-r2/{phase}/foreign-denied-recorded/proc/90101/status';check(q['status_sha256']==H(raw(status)),'original synthetic status pin '+phase)
script=raw(P/'check_process_scope.py').decode();check("def __init__(self,*args,**kwargs):" in script and "assert FakeProcPath('/proc')==fakeproc" in script and script.index("assert FakeProcPath('/proc')==fakeproc")<script.index('with m.terminal_lease()'),'r2 fake proc exact mapped before context call')
correction=j(P/'INITIAL_SYNTHETIC_ISOLATION_CORRECTION.json');check(correction['initial_preparation_exit']==1 and 'incorrect' in correction['correction'] and 'real /proc' in correction['correction'],'initial erroneous proc claim explicitly corrected')
fails=j(P/'V2_FAILURE_BINDINGS.json');check(len(fails['attempts'])==2,'both true v2 failures retained')
for entry in fails['attempts']:
 p=Path(entry['path']);body=raw(p);check(len(body)==entry['bytes'] and H(body)==entry['sha256'] and json.loads(body)==entry['original_result'],'v2 failure original binding '+str(p))
 r=entry['original_result'];check(r['collection_driver_exit']==1,'v2 original failure not relabelled')
 for c in r['commands']:
  for s in ['stdout','stderr']:
   body=raw(Path(c['directory'])/(s+'.bin'));check(H(body)==c[s+'_sha256'] and len(body)==c[s+'_bytes'],'v2 original stream '+str(p)+s)
  check(c['actual_process_returncode']==1 and b'PermissionError' in raw(Path(c['directory'])/'stderr.bin'),'v2 actual permission cause')
report={'schema':'F8-terminal-v3-process-scope-static-and-original-synthetic-peer/1','exit_code':int(any(not c['passed'] for c in checks)),'checks':len(checks),'failures':[c for c in checks if not c['passed']],'accepted_scope':'Root-authorized same-task-UID original producers; explicit unknown foreign UID cwd audit only. No system permission or security change.','synthetic_actual_exits':[0,1,0],'synthetic_vectors':39,'formal_verify_or_collection_executed_by_peer':False,'live_proc_or_payload_read_by_peer':False,'limits':['真正 verify/collect 仍須 root 原授權環境且同UID cwd 可讀；本審沒有執行。','foreign denied cwd 明確未知；接受依據是 root 已核原 producers 同 UID 且無 sudo/docker/升權，不代表全系統 cwd 可見。','原 v2 兩次 PermissionError 與首輪 synthetic fake-Path 隔離錯誤保全，不把它們改判成功。','原 full123/classify/tar/resource/lock 門檻未修改；包實績需另審。'],'bindings':bindings}
(OUT/'CHECKS.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n');(OUT/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['exit_code','checks','failures']},ensure_ascii=False));sys.exit(report['exit_code'])
