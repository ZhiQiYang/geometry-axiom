from pathlib import Path
import ast,hashlib,json,os,stat
O=Path('/workspace/train337-canvas-peer-resume');B=Path('/workspace/root-eleven-archive-alias-extension-preparation-20261024');R=Path('/workspace/root-eleven-archive-alias-extension-execution-20261024');A=Path('/workspace/root-eleven-archive-alias-extension-launch-20261024');checks=0;find=[]
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def j(p):return json.loads(Path(p).read_text())
def ck(v,n):
 global checks
 checks+=1
 if not v:find.append(n)
p=j(B/'PLAN.json');r=j(R/'RESULT.json');a=j(A/'RESULT.json')
pins={'PLAN.json':'14d1725cd02e9c0d2eacb720f02f439f5592cf556909f805435b65a27191f6b1','exact_seven_plus_one_archive_link_core.py':'f8a86ab62d37d9c0699846fd6fbdd0d2c2be9a7875701b7c1c1b3b511e6eac47','extend_exact_eleven_root_archive_aliases.py':'6f54cc3cde975bdae9fd0fbe490123c1a8c092c3b7e5f5f659b9aaac0ea19e24'}
for n,v in pins.items():ck(h(B/n)==v,'fixed pin '+n)
ck(h('/workspace/launch_root_eleven_archive_alias_extensions_20261024.py')=='0b30452566a848f2375681241b24cbca2eccf94fa9b88c4a1b46b66ebc9c7757','fixed launcher pin')
old=Path(p['original_core']['path']).read_text();new=(B/'exact_seven_plus_one_archive_link_core.py').read_text()
expected=old.replace("assert len(members) in (2, 4, 7) and len({x['path'] for x in members}) == len(members)","assert len(members) == 8 and len({x['path'] for x in members}) == len(members)").replace("assert len({(x['dev'], x['inode']) for x in members}) == len(members)","assert len({(x['dev'], x['inode']) for x in members[:7]}) == 1\n    assert len({(x['dev'], x['inode']) for x in members}) == 2\n    assert all(x['nlink'] == 7 for x in members[:7]) and members[7]['nlink'] == 1").replace('linked = set()','linked = set(range(1, 7))').replace('for item in members[1:]]','for item in members[7:]]').replace('expected_alias_count=1, temporary_paths=','expected_alias_count=7, temporary_paths=').replace('enumerate(temporary, 1)','enumerate(temporary, 7)')
ck(new==expected and h(p['original_core']['path'])=='354d49ff43303bbc9e8256389f75d72bcb250e68ab79f97f02cff7cf357d1eec','core exact original except six explicit shared-seven to eight changes')
def fns(t):return {x.name:ast.dump(x,include_attributes=False) for x in ast.parse(t).body if isinstance(x,ast.FunctionDef)}
for n,v in fns(old).items():
 if n!='link_exact':ck(fns(new)[n]==v,'original full body/metadata/durability helper '+n)
ck(r['plan_sha256']==pins['PLAN.json'] and r['core_sha256']==pins['exact_seven_plus_one_archive_link_core.py'],'execution fixed source pins')
ck(r['exit_code']==a['actual_process_returncode']==0 and r['ended_utc'] and a['ended_epoch'] and not a['timeout_expired'],'actual terminal inner and outer zero')
ck(r['actual_replacement_performed'] and r['all_original_payload_paths_retained'] and r['all_original_receipt_bytes_preserved'],'all original paths/receipt bytes retained by original executor')
ck(p['target_count']==88 and p['new_replacements']==11 and len(p['owners'])==7 and len({x['path'] for g in p['groups'] for x in g['members']})==88,'exact eleven root leaves and77 existing aliases')
ck([g['count'] for g in p['groups']]==[8]*11 and [g['count'] for g in r['groups']]==[8]*11 and r['expected_allocated_saving']==p['expected_allocated_saving']==134045696,'exact group counts and configured allocation')
ck(sum(g['members'][7]['allocated_bytes'] for g in p['groups'])==134045696,'only replaced root leaf allocation counted')
for k,g in enumerate(p['groups'],1):
 m=g['members'];can=m[0];root=m[7];events=[json.loads(x) for x in (R/f'GROUP-{k}.jsonl').read_text().splitlines()]
 ck(all(x['nlink']==7 for x in m[:7]) and root['nlink']==1 and len({(x['dev'],x['inode']) for x in m[:7]})==1 and len({(x['dev'],x['inode']) for x in m})==2,'original seven plus one metadata '+str(k))
 ck(root['path']==g['new_root_alias']==str(Path(p['root'])/root['git_path']) and root['owner_root']==p['root'] and all(x['owner_root']!=p['root'] for x in m[:7]),'exact isolated root target '+str(k))
 ck(root['git_path'].startswith(('tests/evidence/','tests/release-evidence/')) and root['git_path'].endswith('.tar.gz') and all(x['git_path']==root['git_path'] and x['git_blob']==root['git_blob'] and x['sha256']==g['sha256'] for x in m),'same immutable Git leaf and original hashes '+str(k))
 ck([x['event'] for x in events]==['initial_verified','before_link','temporary_link_verified','replacement_verified','complete'],'one original atomic transition '+str(k))
 ck(events[0]['originals']==m and events[0]['expected_alias_count']==7 and events[-1]['expected_alias_count']==8 and events[-1]['bytes_unchanged'] and events[-1]['all_original_paths_present'],'journal exact originals and complete '+str(k))
 ck(all(x['index']==7 for x in events[1:4]) and [x['expected_alias_count'] for x in events[1:4]]==[7,8,8] and events[1]['destination']==root['path'],'only root index7 replaced '+str(k))
 ck(not any(os.path.lexists(x) for x in events[0]['temporary_paths']),'no leftover pending alias '+str(k))
 for x in m:
  q=Path(x['path']);s=q.lstat();ck(stat.S_ISREG(s.st_mode) and q.resolve()==q,'original path retained '+str(q))
  ck((s.st_dev,s.st_ino,s.st_nlink,s.st_mode,s.st_size,s.st_uid,s.st_gid,s.st_mtime_ns)==(can['dev'],can['inode'],8,can['mode'],can['size'],can['uid'],can['gid'],can['mtime_ns']),'current exact eight alias metadata '+str(q))
for x in p['anchors']:ck(Path(x['path']).stat().st_size==x['bytes'] and h(x['path'])==x['sha256'],'original small anchor '+x['path'])
for x in p['terminal_rows']:ck(j(x['path'])==x['original_rows'],'historical red/green rows unchanged '+x['path'])
expected=[]
for o in p['owners']:expected.append((o['root'],['git','rev-parse','HEAD'],o['head']))
for g in p['groups']:
 for x in g['members']:
  expected.extend([(x['owner_root'],['git','ls-tree','HEAD' if x['owner_root']==p['root'] else x['owner_head'],'--',x['git_path']],f"100644 blob {x['git_blob']}\t{x['git_path']}"),(x['owner_root'],['git','cat-file','-s',x['git_blob']],str(x['size'])),(x['owner_root'],['git','hash-object',x['path']],x['git_blob'])])
  if x['owner_root']==p['root']:expected.append((x['owner_root'],['git','ls-files','--stage','--',x['git_path']],f"100644 {x['git_blob']} 0\t{x['git_path']}"))
rows=j(R/'git-originals/subcommands.json');ck(len(rows)==564==len(expected)*2,'282 original exact Git reads before and after')
for row,(cwd,argv,out) in zip(rows,expected+expected):
 d=Path(row['directory']);ck(row['cwd']==cwd and row['command']==argv and (d/'stdout.bin').read_text().strip()==out and row['stderr_bytes']==0,'exact before/after Git '+str(d))
for base in [R/'git-originals',A]:
 for row in j(base/'subcommands.json'):
  d=Path(row['directory']);ck(j(d/'result.json')==row and row['actual_process_returncode']==0 and not row['timeout_expired'] and row['ended_epoch']>=row['started_epoch'],'true captured exit/time '+str(d))
  ck(bool(j(d/'request.json')) and h(d/'stdin.bin')==row['stdin_sha256'],'original request/stdin '+str(d))
  for stream in ['stdout','stderr']:
   q=d/(stream+'.bin');ck(q.stat().st_size==row[stream+'_bytes'] and h(q)==row[stream+'_sha256'],'complete original stream '+str(q))
cons=sorted(R.glob('consumers-*/CONSUMERS.json'));ck(len(cons)==r['consumer_checks']==12,'12 fresh consumer records')
for q in cons:
 d=j(q);ck(not d['hits'] and bool(d['limitation']),'consumer no visible hit and visibility limitation '+str(q))
ck(a==j(A/'subcommands.json')[-1],'outer RESULT original captured row')
ck(j(B/'SELF_REVIEW.json')['independent_peer'] is False and j(A/'REQUEST.json')['independent_peer_status_at_start']=='requested in parallel; not claimed complete','root authorization and independent peer timing honest')
ck(p['consumer_prefixes'][-11:]==[g['new_root_alias'] for g in p['groups']] and p['root'] not in p['consumer_prefixes'],'root-only eleven leaf consumer scope, no whole-root freeze')
ck('Only eleven new root leaves are frozen' in r['reservation'] and 'All88' in r['reservation'] and 'de-linked' in r['reservation'],'all88 alias write lease retained')
report={'schema':'root-eleven-alias-extension-static-actual-peer-v1','checks':checks,'exit_code':int(bool(find)),'findings':find,'plan_sha256':h(B/'PLAN.json'),'actual_result_sha256':h(R/'RESULT.json'),'outer_sha256':h(A/'RESULT.json'),'executor_sha256':h(B/'extend_exact_eleven_root_archive_aliases.py'),'core_sha256':h(B/'exact_seven_plus_one_archive_link_core.py'),'groups':11,'retained_paths':88,'original_alias_paths':77,'new_root_replacements':11,'original_git_commands':564,'consumer_checks':12,'expected_allocated_saving':134045696,'free_before':r['free_before'],'free_after':r['free_after'],'limits':['No second archive payload hash; actual original full-byte executor, all small Git streams/journals/anchors, and fresh metadata independently checked.','Root explicitly authorized self-reviewed execution with parallel independent peer; this report is after execution.','Only11 exact immutable root leaves join existing groups; all88 aliases must be de-linked before any applicable write/reuse.','Root other docs/publications remain outside frozen leaf scope; historical product failures unchanged.','Configured allocated saving is not df net change; original consumer visibility limitation remains.']}
q=O/'ROOT_ELEVEN_ALIAS_EXTENSIONS_STATIC_ACTUAL_PEER.json';q.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(q),'sha256':h(q),'checks':checks,'exit_code':report['exit_code'],'findings':find}));raise SystemExit(report['exit_code'])
