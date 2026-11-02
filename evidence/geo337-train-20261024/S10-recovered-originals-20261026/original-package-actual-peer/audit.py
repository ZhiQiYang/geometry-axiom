from pathlib import Path
import hashlib,json,tarfile,stat,os,datetime,sys
OWN=Path('/dev/shm/geometry-axiom-geo337-20261025');P=OWN/'S10-ledger-complete-package';V=Path('/tmp/geo337-S10-full123-terminal-preparation-20261025');OUT=Path(__file__).parent
F='82c922a3941525d3a094ac0158bdc7dea57ea360';LH='a4b5f1957e4bde6d30e4c05328e8a8dc1282fa811c52260eb01670cd560d56e7'
H=lambda b:hashlib.sha256(b).hexdigest();count=0;errors=[]
def ck(ok,msg):
 global count
 count+=1
 if not ok:errors.append(msg)
def J(p):return json.loads(p.read_bytes())
def filehash(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(1024*1024),b''):h.update(x)
 return h.hexdigest()
def state(p):
 s=p.lstat();return [s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns]
indexraw=(P/'INDEX.json').read_bytes();j=json.loads(indexraw);rows=j['members'];archive=P/j['archive']
ck(j['source_sha']==F and j['collection_exit']==0,'S10 collection0');ck(len(rows)==1284 and len({r['path'] for r in rows})==1284,'1284 distinct members')
ck(archive.stat().st_size==j['archive_bytes']==9025694 and filehash(archive)==j['archive_sha256']=='1ffc61c1c0d8713653d599e34f2f3882b0535817097ffc44bc05a4b4a3b2a97e','full archive bytes/hash')
ck(sum(r['bytes'] for r in rows)==j['logical_bytes']==52999273,'full logical bytes')
prep=J(V/'PREPARATION.json');ck(H((V/'PREPARATION.json').read_bytes())=='1cc1b919c3d872e538b8f4ff4d461fc0c6fc257caa3e207adfcfd3ae8f6d5448','frozen accepted prep')
request=OWN/'S10-full123-BOUND_REQUEST-20261025.json';req=J(request);ck(H(request.read_bytes())=='a612272280b18c63d3a578237471de9d716d263b5763baf457f5db3caffbbb1c','exact bound request')
job=OWN/'F10-ledger-job';outer=OWN/'F10-ledger-launch';cache=OWN/'F10-cache';root=OWN/'F10-pool';tmp=OWN/'F10-ledger-tmp'
expected=[]
def leaves(base):
 found=[]
 for directory,ds,fs in os.walk(base,followlinks=False):
  for d in ds:ck(not (Path(directory)/d).is_symlink(),'no symlink directory '+str(Path(directory)/d))
  for name in fs:
   p=Path(directory)/name;ck(stat.S_ISREG(p.lstat().st_mode),'regular scoped leaf '+str(p));found.append(p)
 return sorted(found)
for base in [job,outer]:expected.extend((base.name+'/'+p.relative_to(base).as_posix(),str(p)) for p in leaves(base))
for folder in sorted(cache.iterdir()):
 if folder.name.startswith('M') or folder.name in ('_baseline','_bridge-baseline'):
  ck(folder.is_dir() and not folder.is_symlink(),'selected original cache directory')
  expected.extend(('original-cache-metadata-and-streams/'+p.relative_to(cache).as_posix(),str(p)) for p in leaves(folder) if p.name.endswith(('.stdout','.stderr','.json')))
expected.extend(('tools/'+x['archive_name'],x['path']) for x in prep['original_tools']);expected.extend(('collector-tools/'+x['path'],str(V/x['path'])) for x in prep['files'])
expected.extend([('collector-tools/PREPARATION.json',str(V/'PREPARATION.json')),('terminal-control/BOUND_REQUEST.json',str(request)),('terminal-control/ORIGINAL_TOOL_FINAL.json',req['terminal_bindings']['original_tool_final']['path'])])
expected.extend(('terminal-control/'+name+'.json',item['path']) for name,item in req['additional_originals'].items())
ck(expected==[(r['path'],r['source']) for r in rows],'exact independent full scope/order')
ck(all(not Path(r['source']).is_relative_to(root) and not Path(r['source']).is_relative_to(cache/'_bridge-work') for r in rows),'no repository/seed payload sources')
by_source={r['source']:r for r in rows}
with tarfile.open(archive,'r:gz') as tar:
 entries=tar.getmembers();ck([e.name for e in entries]==[r['path'] for r in rows],'tar member order closure');ck(all(e.isreg() for e in entries),'all regular no hidden links')
 for i,(e,r) in enumerate(zip(entries,rows)):
  raw=tar.extractfile(e).read();ck(len(raw)==r['bytes']==e.size and H(raw)==r['sha256'],'tar full bytes '+str(i));ck(not Path(e.name).is_absolute() and '..' not in Path(e.name).parts,'safe archive path '+str(i))
  ck(e.mode==(r['source_state'][2]&0o777) and e.mtime==r['source_state'][5]//1000000000,'tar mode/mtime '+str(i))
  p=Path(r['source']);before=state(p);ck(before==r['source_state'] and stat.S_ISREG(before[2]),'original state '+str(i));ck(filehash(p)==r['sha256'],'original full hash '+str(i));ck(state(p)==before,'source stable after read '+str(i))
term=j['terminal'];ck(J(P/'TERMINAL.json')==term,'terminal file exact');ck(term['formal_accepted'] and not term['failed_conditions'] and all(term['conditions'].values()),'formal accepted all conditions')
ck(list(term['phase_exits'].values())==[1,0,0,0],'four phases original1000');ck(term['record_count']==123 and term['execution_head_counts']=={F:120} and term['retired_ids']==['M35','M51','M55'],'123/120/3')
ck(term['verdicts']=={'killed':114,'equivalent':5,'crashed':1,'retired':3},'original verdicts retained');ck(term['terminal_files']['ledger']['sha256']==LH and by_source[str(job/'mutants_results.json')]['sha256']==LH,'exact ledger hash')
peer=Path('/tmp/geo337-S10-full123-actual-peer-20261025/REVIEW.json');ap=J(peer);ck(H(peer.read_bytes())=='1a766fb7d0130ecd378d62afd73e94378728669fe873fc11f4c5fe6d877df8cb','7575 actual peer pin');ck(ap['exit_code']==0 and ap['source_sha']==F and ap['ledger_sha256']==LH,'original peer source ledger0')
for path,pin in ap['bindings'].items():ck(path in by_source and by_source[path]['sha256']==pin,'actual row root binding '+path)
for name,item in term['terminal_bindings'].items():ck(by_source[item['path']]['sha256']==item['sha256'],'terminal bindings '+name)
for name,item in term['additional_originals'].items():ck(by_source[item['path']]['sha256']==item['sha256']==req['additional_originals'][name]['sha256'],'additional controls '+name)
proc=j['process_scope'];ck(J(P/'PROCESS_SCOPE.json')==proc,'process scope exact');ck(proc['same_task_uid_denial_is_blocking'] and proc['unknown_uid_denial_is_blocking'] and proc['foreign_argv_hits_are_blocking'],'process conservative boundaries')
ck(proc['all_system_cwds_inspected']==(not proc['unreadable_foreign_cwds']),'unknown cwd explicit')
for r in proc['unreadable_foreign_cwds']:
 ck(len(r['uids'])==4 and proc['task_uid'] not in r['uids'] and r['cwd'] is None and r['not_a_claim_of_system_wide_cwd_visibility'],'foreign uid unknown explicit')
 ck(not any(x==str(p) or x.startswith(str(p)+'/') for x in r['argv'] for p in [job,outer,cache,root,tmp]),'foreign argv no exact protected paths')
# These collector launch receipts are publication supplements, not silently claimed inside archive.
launch_bindings={};capture_rows=[]
for label in ['verify','collection']:
 d=OWN/('S10-full123-terminal-'+label+'-root-original-20261025');lr=J(d/'RESULT.json');cs=J(d/'subcommands.json');ck(lr['actual_exit']==0 and lr['source_sha']==F and len(cs)==1,'original '+label+' true0')
 c=cs[0];ck(lr['argv']==c['command'] and c['actual_process_returncode']==0 and not c['timeout_expired'],'actual '+label+' argv/exit');ck('a612272280b18c63d3a578237471de9d716d263b5763baf457f5db3caffbbb1c' in c['command'] and '1cc1b919c3d872e538b8f4ff4d461fc0c6fc257caa3e207adfcfd3ae8f6d5448' in c['command'],'same bound/prep '+label)
 z=Path(c['directory']);ck(J(z/'result.json')==c,'original command result exact')
 rq=J(z/'request.json');ck(all(c[k]==v for k,v in rq.items() if k not in ('actual_process_returncode','timeout_expired')) and rq['actual_process_returncode'] is None and c['actual_process_returncode']==0 and rq['timeout_expired'] is False and c['timeout_expired'] is False,'original full request/env retained')
 for s in ['stdout','stderr']:
  raw=(z/(s+'.bin')).read_bytes();ck(H(raw)==c[s+'_sha256'] and len(raw)==c[s+'_bytes'],'original '+label+' '+s)
 ck(H((z/'stdin.bin').read_bytes())==c['stdin_sha256'],'original '+label+' stdin');ck(c['source_sha']==F and c['environment']['PYTHONOPTIMIZE'] is None and c['ended_epoch']>=c['started_epoch'],'original '+label+' source/env/time')
 launch_bindings[str(d/'RESULT.json')]=H((d/'RESULT.json').read_bytes());launch_bindings[str(d/'subcommands.json')]=H((d/'subcommands.json').read_bytes());capture_rows+=cs
cf=Path('/tmp/geo337-S10-full123-host-results-20261025/COLLECTION_FINAL.json');host=J(cf);ck(host['exit_code']==0 and not host.get('session_id'),'true collection FINAL');ck(host['output'].encode()==(Path(capture_rows[-1]['directory'])/'stdout.bin').read_bytes(),'host exact full collector stdout')
ck(J(OWN/'S10-ledger-terminal-verify/TERMINAL.json')==term,'verify and collection facts equal')
ad=j['storage_admission'];required=j['logical_bytes']+j['logical_bytes']//1000+sum(((r['bytes']+511)//512*512-r['bytes'])+2048 for r in rows)+4*1024**2+ad['reserve_bytes'];ck(required==ad['required_before']==127182599 and ad['free_before']>=required and ad['reserve_bytes']==67108864,'unchanged full uncompressed admission formula64MiB')
adp=OWN/'S10-full123-collection-admission-20261025.json';rootad=J(adp);ck(rootad['source_sha']==F and rootad['members']==len(rows) and rootad['logical_bytes']==j['logical_bytes'],'root admission identities');ck(rootad['shared_allocated_before']+required==rootad['projected_total']<=rootad['planning_ceiling']==2147483648,'twoOWN2GiB original admission');ck(J(OWN/'S10-full123-terminal-collection-root-original-20261025/RESULT.json')['admission_sha256']==H(adp.read_bytes()),'admission exact original pin')
ck(all(state(Path(r['source']))==r['source_state'] for r in rows),'all originals final unchanged');ck(H((P/'INDEX.json').read_bytes())==H(indexraw),'index unchanged')
result={'schema':'S10-full123-package-independent-actual-peer/1','source_sha':F,'exit_code':1 if errors else 0,'blocking_findings':errors,'checks':count,'archive_sha256':j['archive_sha256'],'archive_bytes':j['archive_bytes'],'index_sha256':H(indexraw),'ledger_sha256':LH,'members':len(rows),'logical_bytes':j['logical_bytes'],'original_row_peer_sha256':H(peer.read_bytes()),'original_phase_exits':term['phase_exits'],'verdicts':term['verdicts'],'source_preservation_verified':True,'original_capture_rows':len(capture_rows),'collector_launch_bindings':launch_bindings,'collection_final_sha256':H(cf.read_bytes()),'source_or_seed_payloads_read':False,'formal_tests_or_collection_rerun':False,'limitations':['此peer完整tar／INDEX／original bytes-state及scope核對，不重跑mutator或source185閉包；逐列語意用已完成7575原件審。','原ELF/source/privateGit未入tar且原處保留；這不是刪除許可。','collector verify/collection外層及rootadmission/hostFINAL需另完整公開；本tar只含原full123 JOB/OUTER/cache兩流與已列工具／控制。','foreign denied cwd依原policy顯式unknown，不冒全OS可見。','原trackedcheck1與M20crashed保；collection0不是整專案READY，帳本未採入新F。'],'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
p=OUT/'REVIEW.json';p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'exit_code':result['exit_code'],'checks':count,'errors':errors,'review_sha256':H(p.read_bytes()),'index_sha256':H(indexraw)}));sys.exit(result['exit_code'])
