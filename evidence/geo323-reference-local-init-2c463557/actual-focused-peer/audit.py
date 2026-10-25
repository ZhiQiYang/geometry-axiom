from pathlib import Path
import ast,collections,datetime,hashlib,json,subprocess
OUT=Path(__file__).resolve().parent
REPO=Path('/workspace/geometry-axiom')
S='2c4635577a8fcb11e88b346547f7bb1c7b739fb7';BASE='6df0264f75e84f03adb70746b6ac3db07a9910fc'
FORM=Path('/tmp/geo337-reference-local-init-formal-20261024'); OBS=FORM/'load-residual/observed'; LAUNCH=Path('/tmp/geo337-reference-local-init-formal-launch-20261024')
checks=collections.Counter();fail=[];bindings={}
def ck(group,ok,detail):
 checks[group]+=1
 if not ok:fail.append({'group':group,'detail':detail})
def sha(b):return hashlib.sha256(b).hexdigest()
def readj(p):return json.loads(p.read_bytes())
def bind(p):
 b=p.read_bytes();bindings[str(p)]={'bytes':len(b),'sha256':sha(b)};return b
def git(*args):return subprocess.check_output(['git',*args],cwd=REPO)
def blob(ref,name):return git('show',ref+':'+name)
def sameblob(ref,name,pin):return sha(blob(ref,name))==pin
report=readj(FORM/'RESULT.json');outer=readj(LAUNCH/'RESULT.json');runner=readj(FORM/'load-residual/runner.json');entry=readj(OBS/'ORIGINAL_ENTRY.json');observation=readj(OBS/'OBSERVATION.json');request=readj(OBS/'REQUEST.json');manifest=readj(FORM/'load-residual/manifest.json')
for p in (FORM/'RESULT.json',LAUNCH/'RESULT.json',FORM/'load-residual/runner.json',FORM/'load-residual/unittest.log',OBS/'ORIGINAL_ENTRY.json',OBS/'OBSERVATION.json',OBS/'REQUEST.json',FORM/'load-residual/manifest.json',FORM/'load-residual/native-executions.jsonl'):bind(p)
ck('source',git('rev-parse','origin/codex/train337-reference-local-init-20261024').decode().strip()==S,'remote tracking ref exact S')
ck('source',git('show','-s','--format=%P',S).decode().strip()==BASE,'single parent F7')
changed=git('diff','--name-only',BASE,S).decode().splitlines()
ck('source',set(changed)=={'geometry-core/references.inc','tests/test_geo261_load_residual.py','tests/run_all.expected.json','tests/geo337_reference_local_init_harness.c'},'exact four leaves')
old=blob(BASE,'geometry-core/references.inc').decode();new=blob(S,'geometry-core/references.inc').decode()
changes=[('    ReferenceEval local={0},*ctx=&local;bool persistent=false;','    ReferenceEval local,*ctx;bool persistent=false;'),('        if(!ctx)return false;persistent=true;\n    }\n    ctx->world=w;bool ok=true;','        if(!ctx)return false;persistent=true;\n    }else{\n        local=(ReferenceEval){0};ctx=&local;\n    }\n    ctx->world=w;bool ok=true;')]
x=old
for a,b in changes:
 ck('source',x.count(a)==1,'one expected product edit');x=x.replace(a,b)
ck('source',x==new,'only initialization relocation changes product')
pyold=blob(BASE,'tests/test_geo261_load_residual.py').decode();pynew=blob(S,'tests/test_geo261_load_residual.py').decode()
def methods(t):
 tree=ast.parse(t);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='LoadResidual');return {n.name:ast.get_source_segment(t,n) for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
mold=methods(pyold);mnew=methods(pynew)
ck('source',sum(k.startswith('test_') for k in mold)==13 and sum(k.startswith('test_') for k in mnew)==14,'13 original + 1 actual test')
for k,v in mold.items():ck('source',mnew.get(k)==v,'unchanged method '+k)
regold=json.loads(blob(BASE,'tests/run_all.expected.json'));regnew=json.loads(blob(S,'tests/run_all.expected.json'))
def replace_count(d):
 if isinstance(d,dict):
  for k,v in d.items():
   if k=='py:test_geo261_load_residual':v['count']=14
   else:replace_count(v)
 elif isinstance(d,list):
  for v in d:replace_count(v)
replace_count(regold);ck('source',regold==regnew,'only expected count 13 to 14')
for d in (report,outer,entry,observation,request,manifest):ck('identity',d['source_sha']==S,'exact source_sha')
ck('identity',entry['source_files_before']==entry['source_files_after']==manifest['files'],'before/after exact source closure')
ck('identity',sha((FORM/'load-residual/manifest.json').read_bytes())==request['manifest_sha256'],'manifest hash')
for name,pin in manifest['files'].items():
 ck('closure_git',sameblob(S,name,pin),name)
 ck('closure_disk',sha((Path(report['root'])/name).read_bytes())==pin,name)
ck('identity',bytes.fromhex(entry['postflight_head']['stdout_hex']).decode().strip()==S,'postflight exact HEAD')
ck('identity',entry['postflight_status']['exit']==0 and entry['postflight_status']['stdout_hex']=='','postflight clean')
ck('result',report['exit']==outer['exit']==outer['primary_exit']==outer['reaper_exit']==entry['original_exit']==0,'all original exits 0')
ck('result',report['errors']==outer['errors']==[],'no driver errors')
ck('result',runner['total']==runner['run']==runner['passed']==14,'runner 14/14')
for k in ('failed','skipped','explicit_skipped','unrun_skipped','blocked_by_error','expected_failed','extra_errors'):ck('result',runner[k]==0,k)
ck('result',runner['import_error'] is None and runner['failures']==[],'no missing/import failure')
ck('result',entry['observer_complete'] is True and observation['observer_complete'] is True and observation['observation_errors']==[] and observation['incomplete_sessions']==[],'complete observer')
ck('result',report['full_native'] is False and report['performance'] is False and report['ledger_regenerated'] is False,'claims correctly scoped')
ck('result',report['stack_after'][0]==16777216,'16MiB stack')
for where in (FORM,LAUNCH):
 for p in sorted((where/'subcommands').glob('*/result.json')):
  d=readj(p)
  for stream in ('stdout','stderr'):
   b=(p.parent/(stream+'.bin')).read_bytes();ck('outer_stream',len(b)==d[stream+'_bytes'] and sha(b)==d[stream+'_sha256'],str(p)+stream)
  ck('outer_stream',not d.get('timeout_expired'),'no timeout '+str(p))
receipts=[]
for p in sorted(OBS.glob('command-*/receipt.json')):
 d=readj(p);receipts.append((p,d))
 for stream in ('stdout','stderr'):
  meta=d[stream]
  if meta['captured']:
   b=(p.parent/(stream+'.bin')).read_bytes();ck('observed_stream',len(b)==meta['bytes'] and sha(b)==meta['sha256'],str(p)+stream)
 ck('observed_environment',d['selected_environment']['PYTHONOPTIMIZE'] is None,'asserts enabled '+str(p))
 ck('observed_environment',d['exception'] is None,'no exception '+str(p))
ck('result',len(receipts)==observation['commands']==169,'all 169 observed commands')
native=[json.loads(line)for line in (FORM/'load-residual/native-executions.jsonl').read_text().splitlines()]
for i,n in enumerate(native):
 ck('native_log',n['source_sha']==S and n['environment']['GITHUB_SHA']==S and not n['timeout_expired'],'native identity '+str(i))
 matches=[(p,d)for p,d in receipts if d['args']==[n['command']]]
 # Repeated executable/case invocations may match more than once; require a
 # complete corresponding raw command, not uniqueness of a legitimate repeat.
 ck('native_log',any(d['returncode']==n['actual_exit'] and d['executable'].get('sha256')==n['executable_sha256'] and (p.parent/'stdout.bin').read_bytes()==n['stdout'].encode() and (p.parent/'stderr.bin').read_bytes()==n['stderr'].encode() for p,d in matches),'native raw correspondence '+str(i))
local=[n for n in native if n['control'] in ('local-init-whole','local-init-whole-semantics')]
ck('proof',len(local)==15,'15 local phase/case executions')
proof=[]
for phase,code,calls,total in (('fixed',0,0,0),('withdrawn',1,2,255168),('restored',0,0,0)):
 rows=[n for n in local if n['phase']==phase]
 ck('proof',sorted(n['case']for n in rows)==['allocation-failure','fallback','ordered-graph','persistent','work'],'five cases '+phase)
 for n in rows:
  ck('proof',n['actual_exit']==(code if n['case']=='work'else 0),'expected phase/case exit '+phase+'/'+n['case'])
  if n['case']=='work':
   ck('proof','reference-local-calibration calls=1 bytes=127584 context_bytes=127584\n' in n['stdout'],'actual fallback calibration '+phase)
   ck('proof',f'reference-local-work scope=linux-link-wrap calls={calls} bytes={total}' in n['stdout'],'actual emitted memset '+phase)
   ck('proof',(n['stderr']=='') if code==0 else 'ASSERT:persistent-reference-local-zero-work line=166 expr=local_zero_calls==0&&local_zero_bytes==0\n'==n['stderr'],'precise failure '+phase)
   proof.append({'phase':phase,'exit':n['actual_exit'],'stdout':n['stdout'],'stderr':n['stderr'],'executable_sha256':n['executable_sha256']})
seen={};snapshots=readj(OBS/'native-inputs/compiler-input-snapshots.json')
ck('compiler',len(snapshots)==entry['compiler_snapshots']==52,'52 compiler snapshots')
for snap in snapshots:
 for item in snap['inputs']:
  p=Path(item['retained'])
  if str(p)not in seen:
   b=p.read_bytes();seen[str(p)]=(len(b),sha(b))
  ck('compiler_input',seen[str(p)]==(item['bytes'],item['sha256']),item['original'])
for phase in ('fixed','withdrawn','restored'):
 comp=[d for p,d in receipts if d['args'] and isinstance(d['args'][0],list) and any(('local-'+phase+'-local-client.c')in str(arg)for arg in d['args'][0])]
 ck('compiler',len(comp)==1 and '-O0' in comp[0]['args'][0] and '-DREFERENCE_LOCAL_WRAP=1' in comp[0]['args'][0],phase+' real O0 wrap compile')
 link=[d for p,d in receipts if d['args'] and isinstance(d['args'][0],list) and '-Wl,--wrap=memset' in d['args'][0] and any(str(arg).endswith('/local-init-local-'+phase)for arg in d['args'][0])]
 ck('compiler',len(link)==1 and link[0]['returncode']==0,phase+' real linker wrap')
for tool,pin in outer['tools'].items():ck('tool_pin',sha(Path(tool).read_bytes())==pin,tool)
for tool,pin in request['observer_tools'].items():ck('tool_pin',sha((Path('/tmp/geo337-reference-local-init-draft-20261024/observer')/tool).read_bytes())==pin,tool)
result={'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'/root/h_init_actual_review','scope':'read-only existing product diff and focused actual receipts; no heavy rerun, no branch write','source_sha':S,'base_sha':BASE,'changed_paths':changed,'checks':sum(checks.values()),'groups':dict(checks),'failures':fail,'exit':0 if not fail else 1,'source_manifest_leaves':len(manifest['files']),'native_cases':len(native),'observed_commands':len(receipts),'retained_unique_compiler_inputs':len(seen),'proof':proof,'bindings':bindings,'limitations':['此 focused 原測試使用 -O0；未執行 O2 R8/N16 正式交錯效能。','Windows 未執行；portable 分支只計 initializer 路徑，不宣稱 actual memset 量測。','原 observer 只保留 native ELF hash，payload_retained=false；編譯輸入完整原件與所有命令/輸出已核對。','完整 native、browser、全帳本與架構重產不在本次 focused 審查範圍。'],'findings':[] if not fail else ['需檢查 failures；不可將本審查標成通過。']}
(OUT/'REVIEW.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':sum(checks.values()),'failures':fail,'exit':result['exit'],'manifest_leaves':len(manifest['files']),'compiler_inputs':len(seen)},ensure_ascii=False))
raise SystemExit(result['exit'])
