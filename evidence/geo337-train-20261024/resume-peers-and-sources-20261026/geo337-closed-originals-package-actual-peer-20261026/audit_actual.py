"""Read-only full package integrity audit; no extraction, collector or product run."""
from pathlib import Path,PurePosixPath
import collections,datetime,hashlib,json,os,stat,struct,tarfile,zlib

OUT=Path(__file__).parent
OWN=Path('/dev/shm/geometry-axiom-geo337-20261025')
BASE=OWN/'resume-closed-original-package-20261026';OUTER=OWN/'closed-collection-root-original-20261026'
RPIN='669dec81d62ad553ba3bc2886507c16e8f05fc9d5a9afdb9b4f9a25e35cc269a'
APIN='ac08de092c1ceefd01e01cec3091c69183aa834d31ac197c05b0b535f4694ce6'
IPIN='4fde9f8413bb9dfae8866e332391cb52ddcc41c116dc0d5ccf3eb8a04558375f'
CPIN='e3c516027d8868dda1c501631eb1d870e38269b78cf5856cdb6a470ba920eb7f'
F='cbf0fb621888596aa14ad5f2349b503e23b1b72d'
ROOTS=['a6-architecture-source-original-20261026','a6-source-root-original-20261026','a6-architecture-gates-original-20261026','a6-gates-root-original-20261026','a6-architecture-four-original-20261026','a6-assembly-root-original-20261026','candidate-three-leaf-adoption-original-20261026','candidate-adoption-root-original-20261026','recovery-publication-original-20261026','recovery-prbody-root-original-20261026','recovery-prbody-publication-20261026','geo337-candidate-adopter-tiny-20261026','candidate-tiny-root-original-20261026','geo337-native-final-focused-20261026','native-focused-root-original-20261026','final-light-root-original-20261026','F-final-light-gates-original-20261026']
FIELDS=['member','type','bytes','sha256','mode','device','inode','mtime_ns','nlink']
checks=0;findings=[]
def H(b):return hashlib.sha256(b).hexdigest()
def encoded(v):return json.dumps(v,ensure_ascii=False,separators=(',',':')).encode()
def load(p):return json.loads(p.read_bytes())
def need(ok,msg):
 global checks
 checks+=1
 if not ok:findings.append(msg);raise RuntimeError(msg)
def digest(p):
 h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b);n+=len(b)
 return h.hexdigest(),n

report={'schema':'closed-originals-package-independent-actual-peer/1','result_sha256':RPIN,'archive_sha256':APIN,'index_sha256':IPIN,'exit_code':1,'blocking_findings':findings,'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'collector_rerun':False,'product_tests_rerun':False,'git_or_network_executed':False,'originals_removed':False,'cleanup_executed':False,'published':False,'delivered':False,'storage_is_volatile':True}
try:
 rb=(BASE/'RESULT.json').read_bytes();need(H(rb)==RPIN,'exact actual terminal result');r=json.loads(rb)
 need(r['exit_code']==0 and r['errors']==[]and r['archive_created']is True and r['source_execution_sha']is None and r['original_source_bindings_retained']is True,'closed successful packaging, no execution SHA relabel')
 for k in ['originals_removed','cleanup_executed','git_or_network_executed','product_tests_rerun','published','delivered']:need(r[k]is False,'honest original boundary '+k)
 need(r['storage_is_volatile']is True and r['archive_sha256']==APIN and r['index_sha256']==IPIN,'exact package identity/volatile storage')
 ib=(BASE/'INDEX.json').read_bytes();need(H(ib)==IPIN,'complete original INDEX pin');index=json.loads(ib);inv=index['inventory'];rows=index['members']
 need(index['schema']=='closed-originals-full-member-index/1'and index['record_fields']==FIELDS and inv['record_fields']==FIELDS,'index exact schema/field meanings')
 need(inv['root_names']==ROOTS and len(ROOTS)==len(set(ROOTS))==17 and [x['name']for x in inv['roots']]==ROOTS,'exact approved17 closed roots')
 need(len(rows)==r['member_count']==inv['member_count']==32871 and sum(x[1]=='file'for x in rows)==r['file_count']==inv['file_count']==24966 and sum(x[1]=='directory'for x in rows)==r['directory_count']==inv['directory_count']==7905 and sum(x[2]for x in rows)==r['logical_bytes']==inv['logical_bytes']==189987205,'exact original member/file/directory/payload counts')
 need(H(encoded(rows))==inv['identity_sha256'],'full member identity array digest')
 need(all(len(x)==9 for x in rows)and len({x[0]for x in rows})==len(rows),'complete unique member records')
 for x in rows:
  name=PurePosixPath(x[0]);need(not name.is_absolute()and '..'not in name.parts and name.parts[0]in ROOTS,'member path fixed roots only')
  need(x[1]in['file','directory']and ((stat.S_ISREG(x[4])and x[1]=='file')or(stat.S_ISDIR(x[4])and x[1]=='directory')),'only full regular files and directories; no links/special')
 qraw=(BASE/'REQUEST.json').read_bytes();q=json.loads(qraw);need(qraw==(OUTER/'REQUEST.json').read_bytes()and q['collector_sha256']==CPIN and all(q[k]is True for k in ['execute','root_execution_lease','root_no_writers_in_selected_roots']),'original root no-writers request')
 planraw=(BASE/'PLAN.json').read_bytes();peerraw=(BASE/'INDEPENDENT_STATIC_PEER.json').read_bytes();need(H(planraw)==q['plan']['sha256']and H(peerraw)==q['peer']['sha256'],'original plan/static peer pins')
 plan=json.loads(planraw);peer=json.loads(peerraw);need(plan['inventory']==inv and peer['exit_code']==0 and peer['blocking_findings']==[]and peer['collector_sha256']==CPIN and H((BASE/'COLLECTOR.py.txt').read_bytes())==CPIN,'exact plan/inventory/reviewed executed collector')
 root_summaries=[];physical=set();total_source_bytes=0
 for root_item in inv['roots']:
  name=root_item['name'];part=[x for x in rows if x[0]==name or x[0].startswith(name+'/')];need(part==sorted(part,key=lambda x:x[0]),'original root member order '+name)
  need(H(encoded(part))==root_item['member_identity_sha256']and sum(x[1]=='file'for x in part)==root_item['files']and sum(x[1]=='directory'for x in part)==root_item['directories']and sum(x[2]for x in part)==root_item['logical_bytes'],'entire root membership hash/count '+name)
  root=OWN/name;physical.add(name)
  for directory,dirs,files in os.walk(root,followlinks=False):
   for leaf in dirs+files:physical.add((Path(directory)/leaf).relative_to(OWN).as_posix())
  terminal_raw=(root/'RESULT.json').read_bytes();need(H(terminal_raw)==root_item['terminal_sha256'],'exact closed root terminal identity '+name);terminal=json.loads(terminal_raw)
  if name=='recovery-prbody-publication-20261026':need(terminal.get('passed')is True and terminal.get('errors')==[]and terminal.get('published')is True,'original prbody terminal specific schema')
  else:need(type(terminal.get('exit_code'))is int and terminal['exit_code']==0,'original root true terminal zero '+name)
  identities={k:terminal[k]for k in ['source_sha','sourceSHA','prepared_source_sha','final_sha','ledger_execution_sha','architecture_execution_sha','evidence_head','source_execution_sha','formal_adoption_executed','product_tests_executed','full_native_executed','full123_executed']if k in terminal}
  root_summaries.append({'name':name,'terminal_sha256':H(terminal_raw),'files':root_item['files'],'directories':root_item['directories'],'logical_bytes':root_item['logical_bytes'],'original_identity_fields':identities})
 need(physical=={x[0]for x in rows},'actual17 closed roots have no missing/extra members')
 for x in rows:
  name,kind,size,hh,mode,dev,ino,mtime,nlink=x;p=OWN/name;s=p.lstat()
  need([s.st_mode,s.st_dev,s.st_ino,s.st_mtime_ns,s.st_nlink]==[mode,dev,ino,mtime,nlink],'actual original exact lstat identity '+name)
  if kind=='file':
   h,n=digest(p);total_source_bytes+=n;need(n==size==s.st_size and h==hh,'actual original complete file SHA/size '+name)
  else:need(size==0 and hh==H(b''),'directory original empty payload identity '+name)
  after=p.lstat();need((s.st_mode,s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_nlink)==(after.st_mode,after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns,after.st_nlink),'original stable through peer read '+name)
 need(total_source_bytes==189987205,'all original file bytes independently hashed')
 archive=BASE/'CLOSED_ORIGINALS.tar.gz';before=archive.stat();need(before.st_size==r['archive_bytes']==62087411,'actual compressed archive size')
 tarfiles=tardirs=tarbytes=0;tar_member_names=[];headers=0;padded=0;pax=0
 with tarfile.open(archive,'r|gz')as tar:
  for number,m in enumerate(tar):
   need(number<len(rows),'no extra tar member');x=rows[number];name,kind,size,hh,mode,dev,ino,mtime,nlink=x
   need(m.name==name and m.size==size and m.mode==(mode&0o777)and m.mtime==mtime//10**9 and m.uid==m.gid==0 and m.uname==m.gname=='','exact tar scope/order/metadata '+name)
   need(not m.islnk()and not m.issym(),'tar contains bytes not links '+name);tar_member_names.append(m.name)
   expected=tarfile.TarInfo(name);expected.type=tarfile.REGTYPE if kind=='file'else tarfile.DIRTYPE;expected.mode=mode&0o777;expected.size=size;expected.mtime=mtime//10**9;expected.uid=expected.gid=0;expected.uname=expected.gname=''
   hb=len(expected.tobuf(tarfile.PAX_FORMAT));headers+=hb;pax+=hb>512;padded+=(size+511)//512*512
   if kind=='directory':need(m.isdir(),'exact directory member type');tardirs+=1;continue
   need(m.isfile(),'exact file member type');f=tar.extractfile(m);need(f is not None,'actual member data available');h=hashlib.sha256();n=0
   with f:
    for b in iter(lambda:f.read(1024**2),b''):h.update(b);n+=len(b)
   need(n==size and h.hexdigest()==hh,'every complete archived member hash '+name);tarfiles+=1;tarbytes+=n
 need(tar_member_names==[x[0]for x in rows]and tarfiles==24966 and tardirs==7905 and tarbytes==189987205,'all archive members once and complete payload')
 tar_exact=((headers+padded+1024+10239)//10240)*10240;gzip_bound=tar_exact+(tar_exact+4095)//4096+(tar_exact+16383)//16384+(tar_exact+33554431)//33554432+1024
 need(headers==inv['tar_headers_bytes']and padded==inv['tar_payload_padded_bytes']and pax==inv['pax_members']and tar_exact==inv['tar_exact_bytes']==223508480,'independent exact PAX/512 padding/full tar length budget')
 need(gzip_bound==inv['gzip_upper_bytes']==223577721 and inv['metadata_upper_bytes']==16777216 and inv['reserve_bytes']==67108864 and inv['additional_bound_bytes']==gzip_bound+16777216+67108864==307463801,'original conservative compression upper bound/16MiB metadata/64MiB reserve')
 # Read gzip entirely through its trailer independently of tar EOF; validates
 # CRC and refuses an extra gzip stream or trailing bytes without extracting.
 dec=zlib.decompressobj(31);chash=hashlib.sha256();cbytes=ubytes=crc=0
 with archive.open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):
   chash.update(b);cbytes+=len(b);data=dec.decompress(b);crc=zlib.crc32(data,crc);ubytes+=len(data);need(not dec.unused_data,'single gzip stream/no trailing data')
 data=dec.flush();crc=zlib.crc32(data,crc);ubytes+=len(data)
 need(dec.eof and not dec.unused_data and not dec.unconsumed_tail and ubytes==tar_exact,'complete gzip CRC/trailer/end-of-stream and exact decompressed bytes')
 with archive.open('rb')as f:f.seek(-8,2);stored_crc,stored_size=struct.unpack('<II',f.read(8))
 need(stored_crc==crc&0xffffffff and stored_size==ubytes&0xffffffff,'independent gzip CRC32 and ISIZE')
 need(cbytes==62087411 and chash.hexdigest()==APIN,'entire compressed archive SHA/size')
 after=archive.stat();need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'archive stable throughout independent reads')
 capacity=load(BASE/'CAPACITY.json');need(capacity==r['capacity_before']and capacity['additional_bound_bytes']==inv['additional_bound_bytes']and capacity['required_reserve_bytes']==67108864 and capacity['shared_ceiling_bytes']==2147483648,'actual original capacity sample bound to result')
 need(capacity['shared_allocated_bytes']+capacity['additional_bound_bytes']<=2147483648 and capacity['mount_free_bytes']>=capacity['additional_bound_bytes']and capacity['admitted']and capacity['shared_admitted']and capacity['mount_admitted'],'actual admission original shared/mount limits')
 need(r['capacity_after']['shared_allocated_bytes']+67108864<=2147483648 and r['capacity_after']['mount_free_bytes']>=67108864,'actual terminal original reserve preserved')
 pub=load(BASE/'PUBLICATION_MANIFEST.json');need(pub['originals_removed']is False and pub['delivered']is False and len(pub['files'])==8,'planned publication remains undelivered')
 need({Path(x['source_path']).name for x in pub['files']}=={p.name for p in BASE.iterdir()if p.is_file()and p.name!='PUBLICATION_MANIFEST.json'},'publication includes complete current package files')
 for item in pub['files']:
  p=Path(item['source_path']);need(p.parent==BASE and item['destination']=='evidence/geo337-train-20261024/resume-closed-originals-20261026/'+BASE.name+'/'+p.name,'fixed evidence destination only')
  hh,nn=digest(p);need(hh==item['sha256']and nn==item['bytes'],'publication entry full bytes '+p.name)
 outer_result=load(OUTER/'RESULT.json');need(outer_result=={'exit_code':0,'collected_fixed_roots':17,'originals_removed':False,'published':False},'outer actual true terminal')
 outer=load(OUTER/'subcommands.json');need(len(outer)==1,'one original collector invocation');row=outer[0];d=OUTER/'subcommands/000001'
 need(row==load(d/'result.json')and row['directory']==str(d),'outer original result/index identity')
 for key,value in load(d/'request.json').items():need(value is None if key=='actual_process_returncode'else row.get(key)==value,'outer original request/result '+key)
 for name in ['stdin','stdout','stderr']:
  b=(d/(name+'.bin')).read_bytes();need(H(b)==row[name+'_sha256'],'outer complete raw stream '+name)
  if name!='stdin':need(len(b)==row[name+'_bytes'],'outer complete raw stream size '+name)
 need(row['actual_process_returncode']==0 and row['timeout_expired']is False and row['source_sha']==row['acceptance_sha']==F and row['ended_epoch']>=row['started_epoch'],'outer original zero/time/coordination source')
 need(row['command']==['python3','-B','/tmp/geo337-closed-originals-collection-preparation-20261026/collect_closed.py','--execute','--request',str(OUTER/'REQUEST.json'),'--request-sha256',H(qraw)],'exact original collector command')
 need(json.loads((d/'stdout.bin').read_bytes())==r and(d/'stderr.bin').read_bytes()==b'','outer original full terminal output equals package result')
 need(H((BASE/'INDEX.json').read_bytes())==IPIN and H((BASE/'RESULT.json').read_bytes())==RPIN,'index and terminal remained unchanged through peer')
 report.update(exit_code=0,archive_bytes=cbytes,index_bytes=len(ib),root_count=17,member_count=32871,file_count=24966,directory_count=7905,logical_bytes=189987205,tar_exact_bytes=tar_exact,all_members_exact_once=True,all_member_sha256_verified=True,complete_gzip_crc_verified=True,gzip_crc32=f'{crc&0xffffffff:08x}',originals_unchanged=True,original_source_bindings_retained=True,collector_sha256=CPIN,root_request_sha256=H(qraw),outer_result_sha256=H((OUTER/'RESULT.json').read_bytes()),publication_manifest_sha256=H((BASE/'PUBLICATION_MANIFEST.json').read_bytes()),inventory_identity_sha256=inv['identity_sha256'],roots=root_summaries,capacity_before=capacity,capacity_after=r['capacity_after'],limits=['Only package completeness, raw integrity, original identities and original capacity guards are certified. Root terminal status is not a new product acceptance verdict.','Archive includes closed synthetic Git/fixture evidence as bytes; no active product checkout or publisher Git directory is an archive root.','All original17 roots remain in SHM and were independently reread. Nothing was deleted, retired, rewritten or extracted.','Archive, index and original outputs remain volatile and unpublished at this review. Durable remote publication and its full-blob check are separate steps.','Outer source F is collection coordination identity; original S10/a6/F/synthetic source fields are retained byte-exactly, not relabelled.','No collector, product test, native/browser job, Git command or network request was rerun by this peer.'])
except BaseException as exc:
 if not findings:findings.append(repr(exc))
 report['exception']=repr(exc)
finally:
 report.update(exit_code=1 if findings else 0,blocking_findings=findings,checked_count=checks)
 (OUT/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'exit_code':report['exit_code'],'checked_count':checks,'blocking_findings':findings,'review_sha256':H((OUT/'REVIEW.json').read_bytes()),'review_bytes':(OUT/'REVIEW.json').stat().st_size},ensure_ascii=False))
raise SystemExit(report['exit_code'])
