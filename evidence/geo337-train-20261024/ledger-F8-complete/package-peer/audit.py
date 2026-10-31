from pathlib import Path
import hashlib,json,tarfile,stat,os,datetime
O=Path('/tmp/geo337-F8-full123-package-actual-peer-20261025');P=Path('/tmp/geo337-F8-full123-terminal-package-20261025');L=Path('/tmp/geo337-F8-full123-terminal-collection-v3-launch-20261025');V=Path('/tmp/geo337-F8-full123-terminal-preparation-v3-20261025');F='75a1e93811a52b69385cbdaf6a09d773ed9052ad';LH='0123548b29bf8adbaf3cf896bfffb212134452f2574eaf8ae1d1b663104ead1b';checks=[]
H=lambda b:hashlib.sha256(b).hexdigest()
def ck(n,v):checks.append({'check':n,'passed':bool(v)})
def filehash(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(1024*1024),b''):h.update(x)
 return h.hexdigest()
def state(p):
 s=p.lstat();return [s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns]
indexraw=(P/'INDEX.json').read_bytes();j=json.loads(indexraw);rows=j['members'];archive=P/j['archive'];ck('sourceF8_collection0',j['source_sha']==F and j['collection_exit']==0);ck('1486regular_names',len(rows)==1486 and len({x['path'] for x in rows})==1486);ck('archive_pin_size',archive.stat().st_size==j['archive_bytes']==8584878 and filehash(archive)==j['archive_sha256']=='806ab05886963c6dd2673096e04272c734f09c602f830ded9561a79729e13be8');ck('logical49703520',sum(x['bytes'] for x in rows)==j['logical_bytes']==49703520)
prep=json.loads((V/'PREPARATION.json').read_text());ck('v3prep_pin',H((V/'PREPARATION.json').read_bytes())=='0ebbcaa071dded4b8baf0e6050fa4e5828641818bf2c77ea40ea2aaf17b6ec8a')
expected=[];job=Path('/tmp/geo337-full123-F8-job-20261025');outer=Path('/tmp/geo337-full123-F8-launch-20261025');cache=Path('/workspace/geo337-full123-F8-cache-20261025')
def leaves(root):
 found=[]
 for directory,ds,fs in os.walk(root,followlinks=False):
  for d in ds:ck('no_scope_symlink_dir:'+str(Path(directory)/d),not (Path(directory)/d).is_symlink())
  for n in fs:
   p=Path(directory)/n;ck('scope_regular:'+str(p),stat.S_ISREG(p.lstat().st_mode));found.append(p)
 return sorted(found)
for root in [job,outer]:expected.extend((root.name+'/'+p.relative_to(root).as_posix(),str(p)) for p in leaves(root))
for folder in sorted(cache.iterdir()):
 if folder.name.startswith('M') or folder.name in ('_baseline','_bridge-baseline'):
  for p in leaves(folder):
   if p.name.endswith(('.stdout','.stderr','.json')):expected.append(('original-cache-metadata-and-streams/'+p.relative_to(cache).as_posix(),str(p)))
expected.extend(('tools/'+x['archive_name'],x['path']) for x in prep['original_tools']);expected.extend(('collector-tools/'+x['path'],str(V/x['path'])) for x in prep['files']);expected.extend([('collector-tools/PREPARATION.json',str(V/'PREPARATION.json')),('terminal-control/BOUND_REQUEST.json',str(L/'BOUND_REQUEST.json')),('terminal-control/ORIGINAL_TOOL_FINAL.json','/tmp/geo337-full123-F8-EXEC_FINAL-20261025.json')]);ck('exact_original_scope_order',expected==[(x['path'],x['source']) for x in rows]);ck('no_git_objects_or_extras',all('.git' not in Path(x['path']).parts for x in rows))
by_source={x['source']:x for x in rows};ck('all_source_regular_before',all(stat.S_ISREG(Path(x['source']).lstat().st_mode) for x in rows))
with tarfile.open(archive,'r:gz') as tar:
 entries=tar.getmembers();ck('archive_member_closure_order',[e.name for e in entries]==[x['path'] for x in rows]);ck('archive_all_regular',all(e.isreg() for e in entries))
 for n,(entry,row) in enumerate(zip(entries,rows)):
  raw=tar.extractfile(entry).read();ck(f'member:{n}:size_hash',len(raw)==row['bytes']==entry.size and H(raw)==row['sha256']);ck(f'member:{n}:safe_path',not Path(entry.name).is_absolute() and '..' not in Path(entry.name).parts);ck(f'member:{n}:mode_time',entry.mode==(row['source_state'][2]&0o777) and entry.mtime==row['source_state'][5]//1000000000)
  src=Path(row['source']);before=state(src);ck(f'member:{n}:source_before',before==row['source_state']);ck(f'member:{n}:source_bytes',filehash(src)==row['sha256']);ck(f'member:{n}:source_after',state(src)==before)
term=j['terminal'];ck('terminal_file_exact',json.loads((P/'TERMINAL.json').read_text())==term);ck('formalaccepted',term['formal_accepted'] is True and term['failed_conditions']==[] and all(term['conditions'].values()));ck('4phase1000',list(term['phase_exits'].values())==[1,0,0,0]);ck('120F8_3retired',term['record_count']==123 and term['execution_head_counts']=={F:120} and term['retired_ids']==['M35','M51','M55']);ck('originalverdicts_not_normalized',term['verdicts']=={'killed':114,'equivalent':5,'crashed':1,'retired':3});ck('ledger_exact',term['terminal_files']['ledger']['sha256']==LH and by_source[str(job/'mutants_results.json')]['sha256']==LH)
originalpeer=Path('/tmp/geo337-F8-full123-actual-peer-20261025/REVIEW.json');ap=json.loads(originalpeer.read_text());ck('actualpeer_original_pin',H(originalpeer.read_bytes())=='e0ebc7a897466fbb2d7a7d36bec3e84d10994f5bcca85ef6d78370f136cd8153');ck('actualpeer_source_ledger0',ap['source_sha']==F and ap['exit_code']==0 and ap['ledger_sha256']==LH)
for p,sha in ap['bindings'].items():ck('actualpeer_binding:'+p,p in by_source and by_source[p]['sha256']==sha)
for name,row in term['terminal_bindings'].items():ck('terminal_root:'+name,by_source[row['path']]['sha256']==row['sha256'])
proc=j['process_scope'];ck('process_scope_exact',json.loads((P/'PROCESS_SCOPE.json').read_text())==proc);ck('foreign_cwd_unknown_not_hidden',proc['task_uid']==1000 and proc['all_system_cwds_inspected'] is False and len(proc['unreadable_foreign_cwds'])==2)
for r in proc['unreadable_foreign_cwds']:
 ck('foreign_uid:'+str(r['pid']),len(r['uids'])==4 and 1000 not in r['uids'] and r['cwd'] is None and r['cwd_status']=='permission-denied-not-inspected' and r['not_a_claim_of_system_wide_cwd_visibility'] is True)
 ck('foreign_argv_scope:'+str(r['pid']),not any(x==str(p) or x.startswith(str(p)+'/') for x in r['argv'] for p in [job,outer,cache,Path('/tmp/train337-323-f64d638f-source'),Path('/tmp/geo337-full123-F8-tmp-20261025')]))
launch=json.loads((L/'RESULT.json').read_text());cr=json.loads((L/'subcommands.json').read_text());ck('verify_collect_original0',launch['collection_driver_exit']==0 and len(cr)==2 and launch['commands']==cr and [x['actual_process_returncode'] for x in cr]==[0,0])
for i,r in enumerate(cr):
 ck(f'capture{i}_F8envtime',r['source_sha']==F and r['environment']['PYTHONOPTIMIZE'] is None and r['ended_epoch']>=r['started_epoch'] and not r['timeout_expired'])
 for k in ['stdout','stderr']:
  b=(Path(r['directory'])/(k+'.bin')).read_bytes();ck(f'capture{i}_{k}',H(b)==r[k+'_sha256'] and len(b)==r[k+'_bytes'])
ck('same_request_and_prep',all('--request-sha256' in r['command'] and '3d59b96ed322eac32b76ebbd2b5387043ca1f1b805d328c7ad25761217475357' in r['command'] and '0ebbcaa071dded4b8baf0e6050fa4e5828641818bf2c77ea40ea2aaf17b6ec8a' in r['command'] for r in cr))
ad=j['storage_admission'];required=j['logical_bytes']+j['logical_bytes']//1000+sum(((x['bytes']+511)//512*512-x['bytes'])+2048 for x in rows)+4*1024*1024+ad['reserve_bytes'];ck('same_device_budget_exact',required==ad['required_before'] and ad['free_before']>=required and ad['reserve_bytes']==67108864)
ck('all_sources_final_state',all(state(Path(x['source']))==x['source_state'] for x in rows));ck('index_final_unchanged',H((P/'INDEX.json').read_bytes())==H(indexraw))
verdict=all(x['passed'] for x in checks);result={'schema':'F8-full123-original-package-independent-actual-peer/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha':F,'exit_code':0 if verdict else 1,'passed':verdict,'archive':str(archive),'archive_sha256':j['archive_sha256'],'archive_bytes':j['archive_bytes'],'index':str(P/'INDEX.json'),'index_sha256':H(indexraw),'ledger_sha256':LH,'members':len(rows),'logical_bytes':j['logical_bytes'],'checks_performed':len(checks),'checks':checks,'original_row_peer':str(originalpeer),'original_row_peer_sha256':H(originalpeer.read_bytes()),'original_root_phase_exits':term['phase_exits'],'process_scope':proc,'scope':'逐tar member原bytes與INDEX、完整明列scope、原sourcebytes/state及capture流核對；不重跑mutator、不重做123逐列語意審查。','limits':['原120自然execution.head仍F8；M20 crashed與五equivalent不改判。','正式收件使用獲批環境；兩個foreign UID0的dockerd/containerd cwd仍未知，原scope明載，不宣稱全系統可見。','v2兩次verify失敗原流、v3收藏外層完整原流及PROCESS_SCOPE需作出版附件；原archive含V2_FAILURE_BINDINGS而非兩個失敗launch全目錄。','ELF/source/git/cache非stdout-stderr-json payload仍在原處，沒有加入此tar；原inline source preflight bytes保原完整。','本peer沒有做Git寫入、採帳本、trackedF9check、native/browser/其他專項或新性能；需要root按已審採用工具固定F9。'],'adoption_performed':False,'git_write':False,'formal_tests_rerun':False}
(O/'REVIEW.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');(O/'REVIEW.md').write_text('封包actual通過。1,486個regular成員、49,703,520原bytes逐一核對tar/INDEX/原sourcehash/state；archive8,584,878bytes。原123逐列審查由另一peer完成，這裡只核其八個根binding吻合。保原tracked1、M20crashed、F8 executionheads。foreignUID cwd未知、兩次v2環境紅與v3完整收件流須公開，沒有因此冒全系統可見或其他正式驗收已跑。\n');print(json.dumps({'exit_code':result['exit_code'],'checks':len(checks),'failed':[x['check'] for x in checks if not x['passed']],'review_sha256':H((O/'REVIEW.json').read_bytes()),'index_sha256':H(indexraw)}))
