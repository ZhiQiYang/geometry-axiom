from pathlib import Path
import json,hashlib,struct,datetime,re
P=Path('/tmp/geo348-synthetic-c-protocol-20261025');O=Path('/tmp/geo348-synthetic-c-protocol-actual-peer-20261025');O.mkdir(exist_ok=True)
checks=[];findings=[];bindings={}
def h(b):return hashlib.sha256(b).hexdigest()
def ck(v,n):
 checks.append(n)
 if not v:findings.append(n)
def read(p):
 p=Path(p);b=p.read_bytes();bindings[str(p)]={'bytes':len(b),'sha256':h(b)};return b
def j(p):return json.loads(read(p))
result=j(P/'RESULT.json');driver=j(P/'DRIVER_COMMAND_RESULT.json');request=j(P/'DRIVER_COMMAND.json')
ck(h(read(P/'RESULT.json'))=='58310d85b42628c2fc55bb790cd51bb23d803def2454bde225e56b0bdf8afa11','original final RESULT pin')
ck(driver['returncode']==0 and all(driver[k]==v for k,v in request.items()),'actual driver request/result exit0')
for s in ['stdout','stderr']:ck(h(read(P/('driver.'+s+'.bin')))==driver[s+'_sha256'],'actual driver full '+s)
summary=json.loads(read(P/'driver.stdout.bin'));ck(summary['exit']==0 and summary['checks']==61 and summary['failed']==[],'actual driver terminal stdout')
ck(result['exit']==0 and len(result['checks'])==61 and all(x['passed'] for x in result['checks']),'61 reported original controls all true')
for key in ['original_wrapper','original_parser','stub','driver','guard']:
 row=result[key];raw=read(row['path']);ck(len(raw)==row['bytes'] and h(raw)==row['sha256'],'pinned actual '+key)
ck(driver['driver_sha256']==result['driver']['sha256'],'caller/producer exact driver identity')
wrapper=read(result['original_wrapper']['path']);parser=read(result['original_parser']['path'])
ck(read(P/'sources/trace_wrap.original.c')==wrapper and read(P/'sidecar_snapshot.py')==parser,'original wrapper/parser exact snapshots')
payload=('loadfile '+str(P/'fixture.txt')+'\ndump\nobjects\nreferences\n').encode()
rows={}
for link in result['commands']:
 r=j(link['path']);name=link['name'];base=P/'runs'/name;rows[name]=r
 ck(h(Path(link['path']).read_bytes())==link['sha256'] and len(Path(link['path']).read_bytes())==link['bytes'],'complete recorded command binding '+name)
 rq=j(base/'COMMAND.json');ck(all(r[k]==v for k,v in rq.items()),'original request/result metadata '+name)
 ck(r['synthetic_protocol_only'] and not r['product_process'],'synthetic-only source scope '+name)
 ck(r['cwd']==str(P),'isolated actual cwd '+name)
 for s in ['stdout','stderr']:
  desc=r[s]
  if desc.get('captured',True):
   b=read(base/(s+'.bin'));ck(h(b)==desc['sha256'] and len(b)==desc['bytes'],'full original stream '+name+'/'+s)
 if (base/'stdin.bin').exists():
  raw=read(base/'stdin.bin');ck(raw==payload,'same four-command actual synthetic batch '+name)
  pin=r.get('input',{}).get('sha256',r.get('input_sha256'));ck(h(raw)==pin,'original stdin binding '+name)
 if 'child_after_run' in r:
  c=r['child_after_run'];ck(c['pid']==int(read(base/'pid.txt')) and c['no_child'] and c['already_reaped'] and c['process_absent'] and c['waitpid_errno']==10,'original pid/reap/absence observation '+name)
 for s in ['events','status','chunks']:
  if s in r:
   d=r[s];b=read(d['path']);ck(len(b)==d['bytes'] and h(b)==d['sha256'],'original side stream binding '+name+'/'+s)
ck(len(rows)==26,'all26 original command records')
for name,r in rows.items():
 expected=1 if name=='044-guard-withdrawn' else 23 if name in ['024-unwrapped-stdin_error','025-fixed-stdin_error'] else 24 if name in ['026-unwrapped-stdout_error','027-fixed-stdout_error'] else None if name=='031-real-timeout-0.25s' else 0
 ck(r['returncode']==expected,'exact actual exit '+name)
 if 'compile-' in name:
  a=r['argv'];inputs=[Path(x) for x in a if x.endswith('.c')];ck('-O0' in a and '-Werror' in a and all(x==P/'stub.c' or (x.parent.parent==P/'builds' and x.name=='trace_wrap.c') for x in inputs),'only small stub/wrapper inputs compiled '+name)
  ck(not any(x.startswith('/workspace') or 'geometry' in x for x in a),'no product compiler argument '+name)
retained_elf=[]
for phase in ['unwrapped','fixed','withdrawn','restored']:
 b=read(P/'builds'/phase/'stub');ck(b.startswith(b'\x7fELF'),'retained actual stub ELF '+phase);retained_elf.append({'phase':phase,'bytes':len(b),'sha256_at_review':h(b)})
 if phase!='unwrapped':
  raw=read(P/'builds'/phase/'trace_wrap.c')
  expected=wrapper if phase!='withdrawn' else wrapper.replace(b'trace_emit("stdout_flush_return", result, 0, eof_flag, error_flag);',b'/* PROTOCOL-ONLY NEGATIVE CONTROL: omit flush-return event. */')
  ck(raw==expected,'one exact C withdrawal/restoration '+phase)
  nm=read(P/'runs'/({'fixed':'007-nm-fixed','withdrawn':'008-nm-withdrawn','restored':'009-nm-restored'}[phase])/'stdout.bin').decode()
  ck(' T __wrap_fgets\n' in nm and ' T __wrap_fflush\n' in nm and ' U fgets@' in nm and ' U fflush@' in nm,'actual linker symbols '+phase)
def raw(name,s):return read(P/'runs'/name/(s+'.bin'))
def events(name):return [json.loads(x) for x in read(P/'runs'/name/'events.jsonl').splitlines()]
for a,b in [('020-unwrapped-normal','021-fixed-normal'),('022-unwrapped-stress','023-fixed-stress'),('024-unwrapped-stdin_error','025-fixed-stdin_error'),('026-unwrapped-stdout_error','027-fixed-stdout_error'),('021-fixed-normal','030-event-write-failure'),('023-fixed-stress','032-real-pipe-chunks')]+[('020-unwrapped-normal',x) for x in ['040-c-control-fixed','041-c-control-withdrawn','042-c-control-restored']]:
 for stream in ['stdout','stderr']:ck(raw(a,stream)==raw(b,stream),'whole unchanged bytes '+a+'/'+b+'/'+stream)
for name in ['021-fixed-normal','023-fixed-stress','032-real-pipe-chunks','040-c-control-fixed','042-c-control-restored']:
 e=events(name);status=struct.unpack('=8Q',read(P/'runs'/name/'status.bin'))
 ck(status==(0x3334384449414731,1,1,13,13,0,0,0),'real attached13-event status '+name)
 want=[k for i in range(4) for k in ['stdin_line_returned','stdout_flush_enter','stdout_flush_return']]+['stdin_eof']
 ck([x['kind'] for x in e]==want and [x['seq'] for x in e]==list(range(1,14)),'real complete wrapper boundary order '+name)
 ck([x['length'] for x in e if x['kind']=='stdin_line_returned']==[len(x) for x in payload.splitlines(keepends=True)],'actual input line lengths '+name)
 ck([x['command'] for x in e]==[i for i in range(1,5) for _ in range(3)]+[4],'actual command identities '+name)
 ck(all(x['rc']==0 for x in e if 'flush' in x['kind']) and e[-1]['feof']>0 and not e[-1]['ferror'],'actual normal return/EOF '+name)
 ck(all(b['monotonic_ns']>=a['monotonic_ns'] for a,b in zip(e,e[1:])),'actual clock ordering '+name)
normal=raw('021-fixed-normal','stderr').decode()
ck(all(s in normal for s in ['file_ok=1 file_errno=33','tmp_rc=0 tmp_errno=34','all_rc=0 all_errno=75','bad_null=1 bad_errno=9','read_errno=16,16,16,16,16','flush_errno=34,34,34,34']),'actual Linux nonmatching streams and errno unchanged')
e=events('025-fixed-stdin_error');ck(len(e)==1 and e[0]['kind']=='stdin_error' and e[0]['ferror']>0 and not e[0]['feof'],'actual stdin EBADF is not EOF')
e=events('027-fixed-stdout_error');ck(e[-1]['kind']=='stdout_flush_return' and e[-1]['rc']==-1 and e[-1]['ferror']>0,'actual stdout EBADF saved')
status=struct.unpack('=8Q',read(P/'runs/030-event-write-failure/status.bin'));ck(status[5]>0 and status[3]>status[4],'actual sidecar write fault marked not silently accepted')
obs=j(P/'runs/030-event-write-failure/OBSERVATION.json');ck(not obs['valid'],'sidecar failure rejected')
t=rows['031-real-timeout-0.25s'];e=events('031-real-timeout-0.25s')
ck(t['timeout_seconds']==0.25 and t['exception']['type']=='TimeoutExpired' and not t['completed_process_returned'] and t['returncode'] is None,'true synthetic timeout retained, no fake exit')
ck(raw('031-real-timeout-0.25s','stdout')==b'{"ok":true,"command":1}\n{"ok":' and raw('031-real-timeout-0.25s','stderr')==b'synthetic timeout partial stderr\n','actual timeout exact partial raw bytes')
ck([x['kind'] for x in e]==['stdin_line_returned','stdout_flush_enter','stdout_flush_return','stdin_line_returned'] and e[-1]['command']==2,'actual timeout stops within second handler boundary')
chunks=j(P/'runs/032-real-pipe-chunks/CHUNKS.json');positions={'stdout':0,'stderr':0};streams={s:raw('032-real-pipe-chunks',s) for s in positions}
for c in chunks:
 s=c['stream'];b=streams[s][c['offset']:c['offset']+c['bytes']];ck(c['offset']==positions[s] and len(b)==c['bytes'] and h(b)==c['sha256'] and b.endswith(b'\n')==c['ends_with_newline'],'actual chunk complete coverage '+s+'/'+str(c['offset']));positions[s]+=len(b)
ck(all(positions[s]==len(streams[s]) for s in positions),'all raw pipe bytes covered once in order')
sc=[x for x in chunks if x['stream']=='stdout'];ck(len(sc)==5 and sum(not x['ends_with_newline'] for x in sc)==4,'actual five stdout chunks with four partial endings')
ck(streams['stderr'].startswith(b'E'*(256*1024)),'actual256KiB stderr pipe pressure')
proof=j(P/'C_WITHDRAWAL_PROOF.json');ck([x['guard_exit'] for x in proof['phases']]==[0,1,0],'actual C withdrawal guard exits0/1/0')
for phase in proof['phases']:
 g=json.loads(raw(phase['guard_run'],'stdout'));ck(g==phase['guard'] and g['product_gate_verdict'] is None and g['root_cause'] is None,'guard original stdout binding '+phase['phase'])
ck(proof['phases'][1]['guard']['errors']==['input-command-identity'],'withdrawal dies on missing boundary order, not output or timeout')
ck(all(result[k] is False for k in ['product_sources_compiled','product_elf_calibrated','n512_executed','performance_tested','browser_used','heavy_lock_used']),'all product scope remains unrun')
ck(not (P/'r2/runs').exists() and not (P/'r2/builds').exists(),'later r2 preparation unexecuted')
review={'schema':'geo348-synthetic-real-c-protocol-actual-independent-peer/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'/root/r8_terminal_peer','checks':len(checks),'exit':int(bool(findings)),'findings':findings,'source_result_sha256':h((P/'RESULT.json').read_bytes()),'original_checks':61,'original_commands':26,'original_driver_exit':0,'actual_c_withdrawal_exits':[0,1,0],'retained_stub_elf_hashes_at_review':retained_elf,'bindings':bindings,'checks_performed':checks,'limits':['Read-only existing actual receipts/source/bytes review; no rerun, C compile, product, browser, network or branch write by reviewer.','Only synthetic stub ELF protocol calibrated. Actual product wrapper ELF, N512, geometry, performance and formal gates remain unrun.','The0.25-second timeout belongs to a synthetic hanging stub; original product600 unchanged.','First run did not seal initial disk preflight or PYTHONOPTIMIZE; not reconstructed retroactively. Exact source/hash/header facts independently checked here; primary parser uses must(), not assert.','Later r2 preparatory files/preflight remain unrun; original successful collection was not repeated merely for missing metadata.','This separate calibration driver is not the production launcher. Its true-pipe tests do not claim the production launcher has itself been exercised end-to-end with this C stub.','Compiler/run original commands and retained stub ELFs are preserved. ELF hashes recorded above were computed at review time, not fabricated as historical per-invocation hash observations.']}
(O/'REVIEW.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
(O/'REVIEW.md').write_text('最小真 C protocol actual 獨審：'+str(len(checks))+'核對／exit '+str(review['exit'])+'。原61checks、26CLI一致；4個stub編譯與nm原流、13事件、非匹配FILE/NULL及errno、256KiB stderr／5段stdout、真0.25s TimeoutExpired partial／reap、eventFD失敗均核對。C撤回flush-return讓原guard在input-command-identity紅，恢復綠，原輸出不變。僅stub協定通過，產品ELF／N512未驗。首輪缺env/disk preflight不補稱已記，r2只有準備且UNRUN；ELF hash為獨審時現存artifact，不偽稱每次原執行前已取hash。\n')
print(json.dumps({'checks':len(checks),'exit':review['exit'],'findings':findings,'sha256':h((O/'REVIEW.json').read_bytes())}));raise SystemExit(review['exit'])
