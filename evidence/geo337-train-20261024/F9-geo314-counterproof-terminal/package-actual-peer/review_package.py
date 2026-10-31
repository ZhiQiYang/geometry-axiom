from pathlib import Path,PurePosixPath
import json,hashlib,stat,tarfile,gzip,os,datetime
B=Path('/dev/shm/geometry-axiom-geo337-20261025');P=B/'geo314-counterproof-terminal-package-20261025';C=B/'geo314-counterproof-terminal-collection-original-20261025';O=Path('/workspace/geo314-counterproof-terminal-package-actual-peer-20261025');O.mkdir(exist_ok=False)
F='4f8a794f4167c3562eb182045102e86e9e37cca9';n=0
H=lambda b:hashlib.sha256(b).hexdigest()
def J(p):return json.loads(Path(p).read_bytes())
def ck(k,v):
 global n
 n+=1
 if not v:raise AssertionError(k)
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def state(p):
 s=p.lstat();return dict(device=s.st_dev,inode=s.st_ino,mode=s.st_mode,bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,nlink=s.st_nlink)
r=J(P/'RESULT.json');inv=J(P/'INVENTORY.json');parts=J(P/'PARTS.json');outer=J(C/'RESULT.json');hp=Path('/workspace/geo314-counterproof-terminal-collection-EXEC_FINAL-20261025.json');host=J(hp);scope=J(P/'SCOPE.json')
ck('exact result',digest(P/'RESULT.json')=='2adc68d2c7a385f19bd32d3aa4057244f1e05910fc3d652f56f33c19d11e46cc')
ck('truehost0',host['status']=='FINISHED' and host['actual_tool_result']['exit_code']==outer['exit_code']==r['collection_exit']==0)
ck('fullhostoriginal',json.loads(host['actual_tool_result']['output'])==outer)
ck('sourceF9',outer['source_sha']==r['source_sha']==inv['source_sha']==F)
ck('fixedbindings',digest(P/'INVENTORY.json')==r['inventory_sha256'] and digest(P/'PARTS.json')==r['parts_sha256'] and digest(P/'RESULT.json')==outer['package_result_sha256'])
ck('fixedscope',digest(P/'SCOPE.json')=='f32dc1cfd20a24f85dce10fbb0db1fe851beeb4fb44b8edc38607b6b8732ecfe')
rows=inv['records'];index={x['member']:x for x in rows}
ck('1826 regular unique',len(rows)==len(index)==r['regular_files']==1826 and r['symlinks']==0 and all(x['type']=='regular'for x in rows))
ck('full36200174bytes',sum(x['bytes']for x in rows)==r['regular_bytes']==36200174)
ck('noexclusions',inv['hash_only_excluded_sourceplan']==inv['nonregular_metadata_only']==[] and inv['private_git_objects_and_indexes_included'] is True)
for x in rows:
 p=Path(x['source_path']);ck('safemember',not PurePosixPath(x['member']).is_absolute() and '..'not in PurePosixPath(x['member']).parts)
 ck('originalstat',state(p)==x['state'] and stat.S_ISREG(p.lstat().st_mode))
 ck('originalfullhash',digest(p)==x['sha256'])
ck('threeparts',len(parts)==len(r['parts'])==3)
seen=[];crcs=[]
for plan,a in zip(parts,r['parts']):
 ap=Path(a['archive_path']);ck('archivefullhash',ap.parent==P and digest(ap)==a['archive_sha256'] and ap.stat().st_size==a['archive_bytes'])
 ck('partidentity',plan['part']==a['part'])
 logical=sum(index[m]['bytes']for m in plan['members_exact']);upper=logical+4096*len(plan['members_exact'])+10240;over=(upper+4095)//4096+(upper+16383)//16384+(upper+33554431)//33554432+1024
 ck('fullbudgetformula',logical==a['logical_regular_bytes']==plan['logical_regular_bytes'] and plan['tar_upper_bytes']==upper and plan['gzip_upper_bytes']==upper+over and plan['required_fresh_bytes']==upper+over+72*1024**2)
 budget=J(P/f"PART{plan['part']}_BUDGET.json")
 ck('original64reserve8meta',plan['reserve_bytes']==64*1024**2 and plan['metadata_bytes']==8*1024**2 and budget['admitted']is True and budget['fresh_output_free']>=plan['required_fresh_bytes'] and a['fresh_free_after']>=64*1024**2 and budget['compression_ratio_assumed']is False)
 with tarfile.open(ap,'r:gz')as tar:
  members=tar.getmembers();ck('orderedmembers',[m.name for m in members]==plan['members_exact'] and len(members)==a['members'])
  for m in members:
   x=index[m.name];seen.append(m.name);ck('type/size',m.isfile()and not m.islnk()and not m.issym()and m.size==x['bytes'])
   ck('mode/mtime',m.mode==(x['state']['mode']&0o777)and m.mtime==x['state']['mtime_ns']//1000000000)
   hh=hashlib.sha256();count=0
   with tar.extractfile(m)as stream:
    for b in iter(lambda:stream.read(1024**2),b''):hh.update(b);count+=len(b)
   ck('memberfullbytes',hh.hexdigest()==x['sha256'] and count==x['bytes'])
 decompressed=0
 with gzip.open(ap,'rb')as stream:
  for b in iter(lambda:stream.read(1024**2),b''):decompressed+=len(b)
 ck('gzipEOFCRCupper',decompressed<=upper and ap.stat().st_size<=plan['gzip_upper_bytes'])
 crcs.append({'part':a['part'],'decompressed_tar_bytes':decompressed,'crc_trailer_verified':True})
ck('allonce',len(seen)==len(set(seen))==len(index)and set(seen)==set(index))
originals=[]
for name,c in scope['attempts'].items():
 root=Path(c['root']);observed=set()
 for parent,dirs,files in os.walk(root,followlinks=False):
  for leaf in dirs+files:
   p=Path(parent)/leaf
   if not stat.S_ISDIR(p.lstat().st_mode):observed.add('attempts/'+name+'/'+p.relative_to(root).as_posix())
 expected={x['member']for x in rows if x['member'].startswith('attempts/'+name+'/')} - {'attempts/'+name+'/original-host-final.json','attempts/'+name+'/original-root-request.json'}
 ck('complete raw root '+name,observed==expected and len(observed)==c['regular_files'] and sum(index[m]['bytes']for m in observed)==c['regular_bytes'])
 original=J(root/'RESULT.json');fj=J(c['final']);summary=json.loads(fj['actual_tool_result']['output']);rq=J(c['request']);a=next(x for x in r['attempts']if x['name']==name)
 ck('exactoriginalpin',digest(root/'RESULT.json')==c['result_sha256']==a['result_sha256'] and digest(c['final'])==c['final_sha256']==a['host_sha256'] and digest(c['request'])==c['request_sha256'])
 ck('source/tool/request',fj['source_sha']==original['source_sha']==rq['source_sha']==F and fj['executor_sha256']==rq['tool_sha256']==c['executor_sha256'] and digest(c['executor'])==c['executor_sha256'] and fj['request_sha256']==original['request_sha256']==c['request_sha256'])
 ck('originalexit preserved',original['exit_code']==fj['actual_tool_result']['exit_code']==summary['exit_code']==a['original_exit']==c['exit_code']==(1 if name=='v2'else 0))
 ck('noformalrewrite',original['formal_F9_pass']is False and summary['formal_F9_pass']is False and original['counterproof_passed']is True and summary['counterproof_passed']is True and original['product_or_test_commit_created']is False)
 if name=='v2':
  ck('index failure preserved',len(original['restoration_errors'])==1 and 'original ROOT index bytes/inode/metadata untouched'in original['restoration_errors'][0] and 'attempts/v2/INDEX_AFTER_FAILURE.bin'in index)
  ck('failedindex exact',index['attempts/v2/INDEX_AFTER_FAILURE.bin']['sha256']=='ad03de61dae2e621503443050fb230baf80e2192bd84662140c9e73d597163c2')
 else:ck('v3 source restored',original['restoration_errors']==[] and original['before']==original['after'] and original['shared_index_unchanged']is True and 'attempts/v3/ORIGINAL_INDEX.bin'in index)
 originals.append({'attempt':name,'exit':original['exit_code'],'formal_F9_pass':False,'counterproof_passed':True,'restoration_errors':original['restoration_errors']})
ck('1357fixedsupplements',len(scope['extra_files'])==1357)
for x in scope['extra_files']:
 m=index[x['member']];ck('supplementexact',m['source_path']==x['path'] and m['bytes']==x['bytes'] and m['sha256']==x['sha256'])
ck('noliveNATIVE',all(not x['source_path'].startswith('/tmp/train337-323-f64d638f-source')for x in rows))
ck('oneouterCLI',len(outer['commands'])==1)
for row in outer['commands']:
 d=Path(row['directory']);ck('capture true0/source',row['actual_process_returncode']==0 and not row['timeout_expired'] and row['source_sha']==F)
 for stream in ['stdout','stderr']:
  raw=(d/(stream+'.bin')).read_bytes();ck('originalfullstream',H(raw)==row[stream+'_sha256']and len(raw)==row[stream+'_bytes'])
 ck('stdinfull',H((d/'stdin.bin').read_bytes())==row['stdin_sha256'])
 ck('c387result',J(d/'result.json')==row)
 ck('fullterminalstdout',json.loads((d/'stdout.bin').read_text().splitlines()[-1])==r)
 ck('boundrequest',(P/'BOUND_REQUEST.json').read_bytes()==(C/'ROOT_REQUEST.json').read_bytes()and digest(C/'ROOT_REQUEST.json')==row['command'][row['command'].index('--request-sha256')+1])
ck('exactreviewedtool',digest(P/'COLLECTOR.py.txt')=='1c313dca29e47629da572e4afe54f42b5a3ea3c04d97bc16b3afe2de4c89b72f'and digest(C/'LAUNCHER.py.txt')=='8af2986eb1680e5af2e0c2402781933e94838b4b6acfa1f20b1c420ec221bf6c')
ck('terminalpins',digest(C/'TERMINAL_PINS.json')==outer['terminal_pins_sha256']=='5dd0744b2b7dd9ef84d7ea7316ed751ce6a0453984edc49eb9a6e9f70591fb0a')
ck('wholeoutputnotgate',r['subject_rerun']is False and r['product_acceptance_rejudged']is False and r['formal_F9_native_original_exit']==1 and r['delivered']is False and r['live_NATIVE_access']is False)
for x in rows:ck('sourcepoststat',state(Path(x['source_path']))==x['state'])
report={'schema':'geo314-v2-v3-full-package-actual-peer/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':0,'checks':n,'source_sha':F,'package_result_sha256':digest(P/'RESULT.json'),'inventory_sha256':r['inventory_sha256'],'parts_sha256':r['parts_sha256'],'outer_result_sha256':digest(C/'RESULT.json'),'host_final_sha256':digest(hp),'regular_files':1826,'logical_regular_bytes':36200174,'symlinks':0,'hash_only_exclusions':0,'archives':r['parts'],'archive_bytes':sum(x['archive_bytes']for x in r['parts']),'gzip_crc_checks':crcs,'attempts':originals,'blocking_findings':[],'limits':['唯讀正式 require_escalated；未重跑產品、未重收封包、未讀活動 NATIVE/seed、未改來源或分支。','全部1826原件完整雜湊、3tar全部成員 bytes/type/mode/mtime、gzip EOF/CRC、完整兩root葉集合與1357固定補件均核；private Git objects/index完整保留。','v2原exit1及INDEX_AFTER_FAILURE保全，v3局部反證exit0；完整F9 native仍1，無全專案READY主張。','原語意反證沿用349項獨審，不另抽產品樣本；本次是證據完整性審查。','SHM封包仍volatile，只有後續普通push及完整遠端blob核對才算delivered；本報告不宣稱已公開。']}
q=O/'REVIEW.json';q.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'exit_code':0,'checks':n,'path':str(q),'sha256':H(q.read_bytes()),'archive_bytes':report['archive_bytes']}))
