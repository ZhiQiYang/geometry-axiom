#!/usr/bin/env python3
import fcntl,hashlib,json,stat,tarfile,time
from pathlib import Path
B=Path('/tmp/geo323-r7-full-collection-20261024');PK=Path('/tmp/geo323-r7-full-package-20261024');P=Path('/tmp/train337-terminal-peer-20261024');U='6df0264f75e84f03adb70746b6ac3db07a9910fc';checks=0;findings=[]
def need(v,n):
 global checks
 checks+=1
 if not v:findings.append(n)
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 return h.hexdigest()
def j(p):return json.loads(p.read_text())
lease=None;slot=None
for name in ['/tmp/g261r3/secondary.lock']:
 handle=Path(name).open('a+b')
 try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);lease=handle;slot=name;break
 except BlockingIOError:handle.close()
if lease is None:raise SystemExit('Both heavy slots busy; no archive read or retry.')
start=time.time()
try:
 package=j(PK/'PACKAGE.json');inventory=j(PK/'RAW_INVENTORY.json');summary=j(PK/'SUMMARY.json');plan=j(B/'PLAN.json');archive=Path(package['archive']['path']);elf=j(PK/'EXCLUDED_ELF_PAYLOADS.json')
 need(package==j(B/'COLLECTOR_RESULT.json') and package['exit']==0,'original collector complete0')
 need(package['source_sha']==inventory['source_sha']==summary['source_sha']==U,'same original U across all package fields')
 need(archive.stat().st_size==package['archive']['bytes']==31359550 and digest(archive)==package['archive']['sha256']=='8f2420a2c4a78cd99355b32183928d1c8ce14c893fdbe88db0f101104622cd7e','actual sole archive hash and bytes')
 need(digest(PK/'RAW_INVENTORY.json')==package['inventory']['sha256']=='dd9610815497cafcf633e1718da833022bc125384738158d8151c2aa28d0474d','full original inventory pin')
 need(len(inventory['members'])==inventory['regular_file_count']==9127,'9127 regular inventory members plus inventory itself')
 need(sum(x['bytes'] for x in inventory['members'])==inventory['logical_original_bytes']==111382355,'logical111382355 bytes')
 expected={x['name']:x for x in inventory['members']};need(len(expected)==9127,'unique names');seen=set();verified={};archive_names=[]
 with tarfile.open(archive,'r:gz') as tf:
  for member in tf:
   need(member.isfile() and member.name not in seen and not member.name.startswith('/') and '..' not in Path(member.name).parts,'regular unique safe member '+member.name);seen.add(member.name)
   if member.name=='RAW_INVENTORY.json':
    data=tf.extractfile(member).read();need(data==(PK/'RAW_INVENTORY.json').read_bytes(),'exact embedded inventory original');continue
   row=expected.get(member.name);need(row is not None,'listed archive member '+member.name)
   if row is None:continue
   p=Path(row['source_path']);st=p.lstat();need(stat.S_ISREG(st.st_mode) and st.st_size==row['bytes']==member.size,'actual regular source/member sizes '+member.name)
   h=hashlib.sha256();size=0;equal=True
   with tf.extractfile(member) as af,p.open('rb') as sf:
    while True:
     part=af.read(1048576)
     if not part:equal=equal and sf.read(1)==b'';break
     size+=len(part);h.update(part);equal=equal and part==sf.read(len(part))
   need(equal and size==row['bytes'] and h.hexdigest()==row['sha256'],'complete original byte-for-byte and hash '+member.name)
   verified[str(p)]={'sha256':h.hexdigest(),'bytes':size}
 need(seen==set(expected)|{'RAW_INVENTORY.json'} and len(seen)==package['archive']['members']==9128,'exact9128 all members')
 selected={x['name']:x for x in plan['original_files'] if x['kind']=='original-payload'}
 need(set(selected)<=set(expected) and len(selected)==9114,'all9114 planned payloads included')
 for name,row in selected.items():need(expected[name]['source_path']==row['path'] and expected[name]['bytes']==row['bytes'],'exact planned original '+name)
 need(len(elf)==7 and {x['name'] for x in elf}=={x['name'] for x in plan['original_files'] if x['kind']=='ELF-hash-only'},'exact seven omitted ELF bodies')
 for row in elf:
  p=Path(row['source_path']);need(row['name'] not in seen and p.is_file() and p.stat().st_size==row['bytes'] and digest(p)==row['sha256'],'original omitted ELF retained '+row['name'])
 result=j(B/'execution/RESULT.json');need(result['actual_process_exit']==0 and result['source_sha']==U and result['subject_executed'] is False,'actual outer0 at U without subject')
 for stream in ['stdout','stderr']:need(digest(B/'execution'/stream)==result[stream+'_sha256'],'outer original complete '+stream)
 need(j(B/'execution/stdout')==package,'outer stdout complete original PACKAGE')
 need(not any(x.startswith('execution/') for x in seen),'late outer not falsely inside archive')
 r=j(Path('/tmp/g337323R7/receipt.json'))
 for key in ['source_sha','base','main','stages','errors','quantitative_targets','wrapper_exit','all_executed_stage_commands_passed','all_measured_original_targets_met','all_required_stages_completed','full_acceptance_passed']:need(summary[key]==r[key],'summary no changed original field '+key)
 stages=['prepare','build','compare','perf','profile'];need(summary['formal_stage_scope']==stages and summary['original_cli_exits']==[0,0,1,1,1],'true original five cumulative CLI exits')
 need([r['stages'][x]['execution_exit'] for x in stages]==[0,0,1,0,0],'separate own stage exits')
 need(r['all_required_stages_completed'] is False and r['full_acceptance_passed'] is None and 'ABC_result' not in r,'three missing stages and absent ABC key not invented')
 need(r['quantitative_targets']['N64_fix_main']['actual']==1.2292230778583162 and r['quantitative_targets']['N64_fix_main']['target_met'] is True,'N64 original quantitative green retained')
 need(r['quantitative_targets']['small_N_no_regression']['points']['16']['fix_base']==1.05190582882169 and r['quantitative_targets']['small_N_no_regression']['points']['16']['target_met'] is False,'N16 original quantitative red retained')
 need(r['quantitative_targets']['geo_eval_source_64_32']['actual']==4.407618425509266 and r['quantitative_targets']['geo_eval_source_64_32']['target_met'] is True,'sourcecall original green retained')
 all_commands=[]
 for p in sorted(Path('/tmp/g337323R7').rglob('commands.json')):
  for row in j(p):
   d=Path(row['directory']);need(j(d/'result.json')==row,'atomic original result identity '+str(d));need(type(row['actual_process_returncode']) is int,'atomic true terminal '+str(d))
   for stream in ['stdout','stderr']:
    v=verified[str(d/(stream+'.bin'))];need(v['bytes']==row[stream+'_bytes'] and v['sha256']==row[stream+'_sha256'],'atomic raw captured exact '+stream+str(d))
   inp=d/'stdin.bin'
   if inp.exists():need(verified[str(inp)]['sha256']==row['stdin_sha256'],'atomic input bytes '+str(d))
   else:need(row['stdin_provided'] is False and row['stdin_sha256']==hashlib.sha256(b'').hexdigest(),'atomic absent input explicit '+str(d))
   all_commands.append({'index':str(p),'directory':str(d),'exit':row['actual_process_returncode'],'timeout':row['timeout_expired'],'source_sha':row['source_sha'],'acceptance_sha':row['acceptance_sha']})
 need(all_commands==summary['original_capture_rows'],'complete original atomic command list')
 oldpeer=j(P/'R7_TERMINAL_CI_LEDGER_ACTUAL_PEER.json');need(oldpeer['exit_code']==0 and not oldpeer['findings'],'independent original175/350 and36samples metadata peer retained')
 for row in j(Path('/tmp/geo323-r7-terminal-summary-20261024/SUMMARY.json'))['original_file_bindings'].values():
  need(verified[row['path']]=={'bytes':row['bytes'],'sha256':row['sha256']},'previous metadata originals now fully sealed '+row['path'])
 need(summary['outer_tool_transcript_sequence_completeness']=='not independently inferred' and summary['outer_tool_transcript_annotation']['stdout_stderr_reconstructed'] is False,'API sequence completeness not invented')
 polls=summary['outer_tool_transcript_annotation']['supplied_api_files'];need(len(polls)==3,'three original supplied API polls')
 for pin in polls:
  need(verified[pin['path']]=={'sha256':pin['sha256'],'bytes':pin['bytes']},'exact original API poll member')
 poll=j(Path(polls[-1]['path']));need(poll['exit_code']==1 and poll['chunk_id']=='87c3e8' and json.loads(poll['output'])=={'source_sha':U,'exit':1,'original_commands':2},'true original formal terminal API1')

 outer=j(Path('/tmp/geo323-final-r7-stage-tools-20261024/outer-five/RESULT.json'))
 need(summary['outer_original_recorder']==outer and outer['exit']==1 and [x['actual_exit'] for x in outer['commands']]==[0,1],'true original outer df0 and launch1')
 for i,row in enumerate(outer['commands'],1):
  d=Path('/tmp/geo323-final-r7-stage-tools-20261024/outer-five/commands')/f'{i:03d}'
  for stream in ['stdout','stderr']:need(verified[str(d/stream)]['sha256']==row[stream+'_sha256'],'original outer full '+str(i)+stream)
 need(j(B/'EXEC_COMPLETION.json')['actual_exit']==0 and j(B/'EXEC_COMPLETION.json')['session_id']==92515 and 'not reconstructed complete API' in j(B/'EXEC_COMPLETION.json')['kind'],'collector completion annotation honest; original OSexit separate')
 need(package['subject_executions']==0 and package['published'] is False and summary['published'] is False,'packaging not execution or prior publication')
 report={'scope':'Independent actual complete R7 five-stage raw package; original red results retained','source_sha':U,'checks':checks,'exit_code':int(bool(findings)),'findings':findings,'archive_sha256':digest(archive),'archive_bytes':archive.stat().st_size,'archive_members':len(seen),'regular_members':9127,'logical_original_bytes':111382355,'atomic_commands':len(all_commands),'inventory_sha256':package['inventory']['sha256'],'lease':slot,'elapsed_seconds':time.time()-start,'limits':['Actual111382355B of collection tools/raw inventory all member bytes compared to originals; no duplicate payload created.','Seven original ELF bodies remain excluded but exact hash verified at original paths.','Original compare1/N16red/N64green/CLIperf1/profile1/full_acceptance null retained; source-role heuristic not rewritten.','Original8-stage driver only five ran at R7; three late stages not credited.','Collector outer/RESULT and package peer are post-package external attachments, not falsely inside own tar.','No C/subject, new timing or network operation.','Formal session73841 has three supplied original API polls including terminal87c3e8 exit1 inside archive. Complete launch/poll sequence not independently inferred. Original outer Recorder launch exit1 and all streams preserved. Collector session92515 observation annotation external.']}
 out=P/'R7_FULL_FIVE_STAGE_ACTUAL_PACKAGE_PEER.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(out),'sha256':digest(out),'checks':checks,'exit_code':report['exit_code'],'findings':findings}))
finally:fcntl.flock(lease,fcntl.LOCK_UN);lease.close()
raise SystemExit(bool(findings))
