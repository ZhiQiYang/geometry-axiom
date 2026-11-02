from pathlib import Path,PurePosixPath
import hashlib,json,tarfile,gzip,datetime,stat,os
B=Path('/dev/shm/geometry-axiom-geo337-20261025');P=B/'remaining-browser-terminal-package-20261025';C=B/'remaining-browser-terminal-collection-original-20261025';O=Path('/workspace/geo337-F9-four-browser-package-actual-peer-20261025');O.mkdir(exist_ok=False)
F='4f8a794f4167c3562eb182045102e86e9e37cca9';JOBS={'documents':('d',10),'grid':('g',15),'space':('s',15),'timber':('t',20)};n=0
H=lambda b:hashlib.sha256(b).hexdigest()
def ck(name,v):
 global n
 n+=1
 if not v:raise AssertionError(name)
def J(p):return json.loads(Path(p).read_bytes())
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def state(p):
 s=p.lstat();return dict(device=s.st_dev,inode=s.st_ino,mode=s.st_mode,bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,nlink=s.st_nlink)
r=J(P/'RESULT.json');inv=J(P/'INVENTORY.json');parts=J(P/'PARTS.json');outer=J(C/'RESULT.json');hostpath=Path('/workspace/geo337-F9-four-browser-terminal-collection-EXEC_FINAL-20261025.json');host=J(hostpath)
ck('expected terminalpin',digest(P/'RESULT.json')=='2103cda1f7549b6a183a1b63cbe2bc2e94e0e673cf6b4f961a16514f7548c969');ck('actual terminal0',host['actual_tool_result']['exit_code']==outer['exit_code']==r['collection_exit']==0);ck('full host stdout',json.loads(host['actual_tool_result']['output'])==outer)
ck('sourceF9',outer['source_sha']==r['source_sha']==inv['source_sha']==F);ck('inventory frozen',digest(P/'INVENTORY.json')==r['inventory_sha256']);ck('parts frozen',digest(P/'PARTS.json')==r['parts_sha256']);ck('outer package binding',outer['package_result_sha256']==digest(P/'RESULT.json'))
records=inv['records'];excluded=inv['hash_only_excluded_sourceplan'];special=inv['nonregular_metadata_only'];index={x['member']:x for x in records};allrows=records+excluded+special
ck('2419 unique',len(records)==len(index)==2419);ck('2411regular8links',sum(x['type']=='regular'for x in records)==2411==r['regular_files'] and sum(x['type']=='symlink'for x in records)==8==r['symlinks']);ck('125944310bytes',sum(x['bytes']for x in records if x['type']=='regular')==125944310==r['regular_bytes']);ck('20metadata2socket',len(excluded)==20 and len(special)==2)
for x in records+excluded:
 p=Path(x['source_path']);ck('safe member',not PurePosixPath(x['member']).is_absolute() and '..'not in PurePosixPath(x['member']).parts);ck('original stat',state(p)==x['state'])
 if x['type']=='regular':ck('original fullhash',stat.S_ISREG(p.lstat().st_mode) and digest(p)==x['sha256'])
 else:ck('original symlink',os.readlink(p)==x['target'] and H(os.fsencode(x['target']))==x['sha256'])
for x in excluded:ck('only known source metadata',any(x['member'].startswith(f'sourceplan/{job}/layout/jobs/{job}/gitdir/')or x['member']==f'sourceplan/{job}/layout/GUARD_LATEST.json'for job in JOBS))
for x in special:ck('only socket metadata',state(Path(x['source_path']))==x['state'] and stat.S_ISSOCK(x['state']['mode']))
seen=[];gzip_eof=[]
ck('nine parts',len(parts)==len(r['parts'])==9)
for plan,a in zip(parts,r['parts']):
 archive=Path(a['archive_path']);ck('full gzip hash/size',digest(archive)==a['archive_sha256'] and archive.stat().st_size==a['archive_bytes']);ck('part identity',a['part']==plan['part'])
 logical=sum(index[name]['bytes']for name in plan['members_exact']if index[name]['type']=='regular');upper=logical+4096*len(plan['members_exact'])+10240;over=(upper+4095)//4096+(upper+16383)//16384+(upper+33554431)//33554432+1024;budget=J(P/f"PART{plan['part']}_BUDGET.json")
 ck('bound formula/8MiB metadata64MiB',plan['tar_upper_bytes']==upper and plan['gzip_upper_bytes']==upper+over and plan['required_fresh_bytes']==upper+over+72*1024**2 and plan['metadata_bytes']==8*1024**2 and plan['reserve_bytes']==64*1024**2)
 ck('fresh admission',budget['admitted'] is True and budget['fresh_output_free']>=plan['required_fresh_bytes'] and budget['compression_ratio_assumed'] is False and a['fresh_free_after']>=64*1024**2)
 with tarfile.open(archive,'r:gz')as tar:
  members=tar.getmembers();ck('tar exact order',[m.name for m in members]==plan['members_exact']);ck('member count',len(members)==a['members'])
  for m in members:
   x=index[m.name];seen.append(m.name);ck('mode/mtime',m.mode==(x['state']['mode']&0o777)and m.mtime==x['state']['mtime_ns']//1000000000)
   if x['type']=='symlink':ck('symlink target/type',m.issym() and m.linkname==x['target'] and m.size==0)
   else:
    ck('regular member type/size',m.isfile()and not m.islnk()and not m.issym()and m.size==x['bytes']);hh=hashlib.sha256();size=0
    with tar.extractfile(m)as stream:
     for b in iter(lambda:stream.read(1024**2),b''):hh.update(b);size+=len(b)
    ck('member fullhash',hh.hexdigest()==x['sha256'] and size==x['bytes'])
 decomp=0
 with gzip.open(archive,'rb')as g:
  for b in iter(lambda:g.read(1024**2),b''):decomp+=len(b)
 ck('full gzip CRC/trailer and upper',decomp<=upper);gzip_eof.append({'part':a['part'],'decompressed_tar_bytes':decomp,'crc_trailer_verified':True})
ck('exact once allmembers',len(seen)==len(set(seen))==len(index) and set(seen)==set(index))
# Exact whole-tree scopes, excluding active nativeROOT and shared browser seed/source payload.
for job,(short,minutes)in JOBS.items():
 roots={f'attempts/{job}/launch':f'/dev/shm/geo337-F9-browsers-20261025/launches/{job}',f'attempts/{job}/storage':f'/dev/shm/geo337-F9-browsers-20261025/r/{short}',f'attempts/{job}/sampler':f'/dev/shm/geo337-F9-browsers-20261025/sampled/{job}',f'sourceplan/{job}':f'/dev/shm/geo337-F9-browsers-20261025/plans/{job}',f'source-materialization/{job}':f'/dev/shm/geo337-F9-browsers-20261025/host/{job}-materialize',f'source-plan-generation/{job}':f'/dev/shm/geo337-F9-browsers-20261025/host/{job}-plan'}
 for prefix,rootpath in roots.items():
  root=Path(rootpath);actual=set()
  for parent,dirs,files in os.walk(root,followlinks=False):
   for name in dirs+files:
    p=Path(parent)/name
    if not stat.S_ISDIR(p.lstat().st_mode):actual.add(prefix+'/'+p.relative_to(root).as_posix())
  expected={x['member']for x in allrows if x['member'].startswith(prefix+'/')};ck('whole original closed root '+prefix,actual==expected)
 a=next(x for x in r['attempts']if x['name']==job);wfpath=Path(index[f'attempts/{job}/storage/original/{job}/receipt.json']['source_path']);wf=J(wfpath);wr=J(Path(roots[f'attempts/{job}/launch'])/'receipt.json');sr=J(Path(roots[f'attempts/{job}/sampler'])/'RESULT.json');fp=Path(f'/workspace/geo337-F9-{job}-SHM-EXEC_FINAL-20261025.json');fj=J(fp);fo=json.loads(fj['actual_tool_result']['output'])
 ck('original receipt exact identity',digest(wfpath)==a['original_receipt_sha256'] and wf['sha']==F and wf['job']==job)
 ck('formal original actualzero preserved',wf['exit_code']==wr['original_primary_exit']==wr['wrapper_exit']==sr['wrapper_exit']==fj['actual_tool_result']['exit_code']==fo['wrapper_exit']==a['original_formal_exit']==0)
 ck('original CI10/15/15/20 preserved',wf['ci_timeout_minutes']==a['original_ci_timeout_minutes']==minutes and wf['over_ci_timeout'] is False and a['original_ci_gate_exit']==0 and wf['seconds']==a['original_elapsed_seconds']<minutes*60)
 ck('original sourceguard0/clean',wf['checkout_before']==wf['checkout_after'] and all(wr[k]['actual_process_returncode']==0 and not wr[k]['timeout_expired']for k in ['before_guard','after_guard']))
 ck('sampler true closed',sr['sampling_complete'] is True and fo['sampling_complete'] is True)
for x in records+excluded:ck('postread unchanged source',state(Path(x['source_path']))==x['state'])
ck('one original collectorCLI',len(outer['commands'])==1)
for row in outer['commands']:
 d=Path(row['directory']);ck('c387 actual exit/source',row['actual_process_returncode']==0 and not row['timeout_expired'] and row['source_sha']==F)
 for stream in ['stdout','stderr']:
  data=(d/(stream+'.bin')).read_bytes();ck('original full '+stream,len(data)==row[stream+'_bytes'] and H(data)==row[stream+'_sha256'])
 ck('captured full package terminal',json.loads((d/'stdout.bin').read_text().splitlines()[-1])==r)
 ck('exact request',(P/'BOUND_REQUEST.json').read_bytes()==(C/'ROOT_REQUEST.json').read_bytes() and digest(C/'ROOT_REQUEST.json')==row['command'][row['command'].index('--request-sha256')+1])
ck('original reviewed tool',digest(P/'COLLECTOR.py.txt')=='813a770b414c6b57f4ffde568e6242614ed3bf28287a3e487ed9811f1113d741' and digest(C/'LAUNCHER.py.txt')=='d50cfaa1bd6f9377fc44149dc51f6a365a50de0f4999addfbfb6f6c597b17545')
ck('original terminal12binding',digest(C/'TERMINAL_PINS.json')==outer['terminal_pins_sha256']=='37453a0a48043e206127a591c5b6c02c13c535cd4150c7890aa63d312b5face0')
ck('not rejudged or delivered',r['subject_rerun'] is False and r['product_acceptance_rejudged'] is False and r['delivered'] is False)
report={'schema':'F9-four-browser-complete-terminal-package-actual-peer/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':0,'checks':n,'source_sha':F,'package_result_sha256':digest(P/'RESULT.json'),'outer_result_sha256':digest(C/'RESULT.json'),'host_final_sha256':digest(hostpath),'inventory_sha256':r['inventory_sha256'],'regular_files':2411,'symlinks':8,'logical_regular_bytes':125944310,'archives':r['parts'],'gzip_crc_checks':gzip_eof,'archive_bytes':sum(a['archive_bytes']for a in r['parts']),'jobs':r['attempts'],'blocking_findings':[],'limits':['Read-only formal require_escalated on closed four-browser original roots/archives, no active314 nativeROOT/seed/source payload, no product rerun or recollection.','All2419 tar members full bytes/type/mode/mtime/links checked plus all sourcehash/stat and9 gzip EOF/CRC/trailers.','20 sourceplan Git metadata/GUARD_LATEST hash-only and2 Unix sockets metadata-only explicitly checked; originals retained.','Product assertions/golden stay attributed to original per-job actual peers; this packagepeer verifies their original formal exits and evidence completeness.','Native remains1; no claim whole train READY. Volatile package not delivered until normal push and complete remote blob verification.']}
p=O/'REVIEW.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'exit_code':0,'checks':n,'path':str(p),'sha256':H(p.read_bytes()),'archive_bytes':report['archive_bytes']}))
