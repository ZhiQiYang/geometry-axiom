#!/usr/bin/env python3
import fcntl,hashlib,json,stat,tarfile,time
from pathlib import Path
B=Path('/workspace/geo323-union-full-collection-20261024');P=Path('/workspace/train337-canvas-peer-resume');U='ca7838e0f4950452b9befcf40899d606db9b81fa';checks=0;findings=[]
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
lease=Path('/tmp/g261r3/heavy.lock').open('a+b');fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
start=time.time()
try:
 package=j(B/'package/PACKAGE.json');inventory=j(B/'package/RAW_INVENTORY.json');summary=j(B/'package/SUMMARY.json');plan=j(B/'PLAN.json');archive=Path(package['archive']['path']);elf=j(B/'package/EXCLUDED_ELF_PAYLOADS.json')
 need(package==j(B/'COLLECTOR_RESULT.json') and package['exit']==0,'original collector complete0')
 need(package['source_sha']==inventory['source_sha']==summary['source_sha']==U,'same original U across all package fields')
 need(archive.stat().st_size==package['archive']['bytes']==31361891 and digest(archive)==package['archive']['sha256']=='a276bd4fe2468ab2f51e61b4bfe802a502f6907ff052c1fad8abf234083f8d3a','actual sole archive hash and bytes')
 need(digest(B/'package/RAW_INVENTORY.json')==package['inventory']['sha256']=='d95588b94db4b2a75cc855edebb6c7c3c8d24300fd5acb4dccf6aa947b950a8d','full original inventory pin')
 need(len(inventory['members'])==inventory['regular_file_count']==9090,'9090 regular inventory members plus inventory itself')
 need(sum(x['bytes'] for x in inventory['members'])==inventory['logical_original_bytes']==110253126,'logical110253126 bytes')
 expected={x['name']:x for x in inventory['members']};need(len(expected)==9090,'unique names');seen=set();verified={};archive_names=[]
 with tarfile.open(archive,'r:gz') as tf:
  for member in tf:
   need(member.isfile() and member.name not in seen and not member.name.startswith('/') and '..' not in Path(member.name).parts,'regular unique safe member '+member.name);seen.add(member.name)
   if member.name=='RAW_INVENTORY.json':
    data=tf.extractfile(member).read();need(data==(B/'package/RAW_INVENTORY.json').read_bytes(),'exact embedded inventory original');continue
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
 need(seen==set(expected)|{'RAW_INVENTORY.json'} and len(seen)==package['archive']['members']==9091,'exact9091 all members')
 selected={x['name']:x for x in plan['original_files'] if x['kind']=='original-payload'}
 need(set(selected)<=set(expected) and len(selected)==9084,'all9084 planned payloads included')
 for name,row in selected.items():need(expected[name]['source_path']==row['path'] and expected[name]['bytes']==row['bytes'],'exact planned original '+name)
 need(len(elf)==7 and {x['name'] for x in elf}=={x['name'] for x in plan['original_files'] if x['kind']=='ELF-hash-only'},'exact seven omitted ELF bodies')
 for row in elf:
  p=Path(row['source_path']);need(row['name'] not in seen and p.is_file() and p.stat().st_size==row['bytes'] and digest(p)==row['sha256'],'original omitted ELF retained '+row['name'])
 result=j(B/'execution/RESULT.json');need(result['actual_process_exit']==0 and result['source_sha']==U and result['subject_executed'] is False,'actual outer0 at U without subject')
 for stream in ['stdout','stderr']:need(digest(B/'execution'/stream)==result[stream+'_sha256'],'outer original complete '+stream)
 need(j(B/'execution/stdout')==package,'outer stdout complete original PACKAGE')
 need(not any(x.startswith('execution/') for x in seen),'late outer not falsely inside archive')
 r=j(Path('/workspace/g337323U/receipt.json'))
 for key in ['source_sha','base','main','stages','errors','quantitative_targets','wrapper_exit','all_executed_stage_commands_passed','all_measured_original_targets_met','all_required_stages_completed','full_acceptance_passed']:need(summary[key]==r[key],'summary no changed original field '+key)
 stages=['prepare','build','compare','perf','profile'];need(summary['formal_stage_scope']==stages and summary['original_cli_exits']==[0,0,1,1,1],'true original five cumulative CLI exits')
 need([r['stages'][x]['execution_exit'] for x in stages]==[0,0,1,0,0],'separate own stage exits')
 need(r['all_required_stages_completed'] is False and r['full_acceptance_passed'] is None and 'ABC_result' not in r,'three missing stages and absent ABC key not invented')
 need(r['quantitative_targets']['N64_fix_main']['actual']==1.429347781620555 and r['quantitative_targets']['N64_fix_main']['target_met'] is False,'N64 original quantitative red retained')
 need(r['quantitative_targets']['geo_eval_source_64_32']['actual']==4.407618425509266 and r['quantitative_targets']['geo_eval_source_64_32']['target_met'] is True,'sourcecall original green retained')
 all_commands=[]
 for p in sorted(Path('/workspace/g337323U').rglob('commands.json')):
  for row in j(p):
   d=Path(row['directory']);need(j(d/'result.json')==row,'atomic original result identity '+str(d));need(type(row['actual_process_returncode']) is int,'atomic true terminal '+str(d))
   for stream in ['stdout','stderr']:
    v=verified[str(d/(stream+'.bin'))];need(v['bytes']==row[stream+'_bytes'] and v['sha256']==row[stream+'_sha256'],'atomic raw captured exact '+stream+str(d))
   inp=d/'stdin.bin'
   if inp.exists():need(verified[str(inp)]['sha256']==row['stdin_sha256'],'atomic input bytes '+str(d))
   else:need(row['stdin_provided'] is False and row['stdin_sha256']==hashlib.sha256(b'').hexdigest(),'atomic absent input explicit '+str(d))
   all_commands.append({'index':str(p),'directory':str(d),'exit':row['actual_process_returncode'],'timeout':row['timeout_expired'],'source_sha':row['source_sha'],'acceptance_sha':row['acceptance_sha']})
 need(all_commands==summary['original_capture_rows'],'complete original atomic command list')
 oldpeer=j(P/'U_FIVE_STAGE_TERMINAL_METADATA_PEER.json');need(oldpeer['exit_code']==0 and not oldpeer['findings'],'independent original175/350 and36samples metadata peer retained')
 for row in j(Path('/workspace/geo323-union-stage-tools-20261024/TERMINAL_SUMMARY.json'))['raw_locators']:
  need(verified[row['path']]=={'bytes':row['bytes'],'sha256':row['sha256']},'previous metadata originals now fully sealed '+row['path'])
 need(package['subject_executions']==0 and package['published'] is False and summary['published'] is False,'packaging not execution or prior publication')
 report={'scope':'Independent actual complete U five-stage raw package; original red results retained','source_sha':U,'checks':checks,'exit_code':int(bool(findings)),'findings':findings,'archive_sha256':digest(archive),'archive_bytes':archive.stat().st_size,'archive_members':len(seen),'regular_members':9090,'logical_original_bytes':110253126,'atomic_commands':len(all_commands),'inventory_sha256':package['inventory']['sha256'],'lease':'/tmp/g261r3/heavy.lock','elapsed_seconds':time.time()-start,'limits':['Actual107MB+ collection tools/raw inventory all member bytes compared to originals; no duplicate payload created.','Seven original ELF bodies remain excluded but exact hash verified at original paths.','Original compare1/N64red/CLIperf1/profile1/full_acceptance null retained; source-role heuristic not rewritten.','Original8-stage driver only five ran at U; three late stages not credited.','Collector outer/RESULT and package peer are post-package external attachments, not falsely inside own tar.','No C/subject, new timing or network operation.']}
 out=P/'U_FULL_FIVE_STAGE_ACTUAL_PACKAGE_PEER.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(out),'sha256':digest(out),'checks':checks,'exit_code':report['exit_code'],'findings':findings}))
finally:fcntl.flock(lease,fcntl.LOCK_UN);lease.close()
raise SystemExit(bool(findings))
