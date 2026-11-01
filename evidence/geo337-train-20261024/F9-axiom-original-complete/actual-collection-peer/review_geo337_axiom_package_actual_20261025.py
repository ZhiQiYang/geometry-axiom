from pathlib import Path,PurePosixPath
import hashlib,json,tarfile,gzip,datetime,stat,os
B=Path('/dev/shm/geometry-axiom-geo337-20261025');P=B/'geo337-F9-axiom-terminal-package-20261025';C=B/'axiom-collection-root-original-20261025';O=Path('/workspace/geo337-F9-axiom-package-actual-peer-20261025');O.mkdir(exist_ok=False)
F='4f8a794f4167c3562eb182045102e86e9e37cca9';n=0
H=lambda b:hashlib.sha256(b).hexdigest()
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def ck(name,v):
 global n
 n+=1
 if not v:raise AssertionError(name)
def J(p):return json.loads(Path(p).read_bytes())
def state(p):
 s=p.lstat();return [s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_nlink]
r=J(P/'RESULT.json');outer=J(C/'RESULT.json');hostpath=Path('/workspace/geo337-F9-axiom-terminal-collection-EXEC_FINAL-20261025.json');host=J(hostpath);hostout=json.loads(host['actual_tool_result']['output']);inv=J(P/'ORIGINAL_INVENTORY.json');parts=J(P/'ORIGINAL_PARTS.json')
ck('package expectedpin',digest(P/'RESULT.json')=='d3bbf12653fc89edabea15a901450a9ef17ef29d040f8c2b4ec713f258e836aa');ck('true terminal0 chain',host['actual_tool_result']['exit_code']==hostout['exit_code']==outer['exit_code']==r['collection_exit']==0);ck('allsourceF9',hostout['source_sha']==outer['source_sha']==r['source_sha']==inv['source_sha']==F)
for filename,key in [('ORIGINAL_INVENTORY.json','inventory_sha256'),('ORIGINAL_PARTS.json','parts_sha256'),('ORIGINAL_RESULT.json','inventory_result_sha256'),('COLLECTOR.py.txt','collector_sha256'),('INDEPENDENT_STATIC_PEER.json','peer_sha256')]:ck('frozen exact '+filename,digest(P/filename)==r[key])
ck('accepted staticpeer655',J(P/'INDEPENDENT_STATIC_PEER.json')['exit_code']==0 and J(P/'INDEPENDENT_STATIC_PEER.json')['checks']==655)
ck('one archive',len(r['parts'])==len(parts)==1)
ck('counts bytes',r['regular_files']==len(inv['records'])==206 and r['symlinks']==0 and r['regular_bytes']==12652356)
index={};originalrows=[]
for ri,rel,typ,size,h,st,target in inv['records']:
 root=inv['roots'][ri];name=root['prefix']+'/'+rel;p=Path(root['source_root'])/rel
 ck('safe regular mapping',typ=='regular'and target is None and '..'not in PurePosixPath(name).parts and not PurePosixPath(name).is_absolute())
 ck('source original stat',state(p)==st and stat.S_ISREG(p.lstat().st_mode))
 ck('source fullbytes',p.stat().st_size==size and digest(p)==h)
 index[name]=(p,size,h,st);originalrows.append((ri,rel))
ck('exact206unique',len(index)==206)
for i,root in enumerate(inv['roots']):
 wanted={rel for ri,rel in originalrows if ri==i}
 if root['selection']=='whole-tree':
  actual=set()
  for parent,dirs,files in os.walk(root['source_root'],followlinks=False):
   for name in dirs+files:
    p=Path(parent)/name
    if not stat.S_ISDIR(p.lstat().st_mode):actual.add(p.relative_to(root['source_root']).as_posix())
 else:actual=set(root['exact_files'])
 ck('root entire original scope',actual==wanted)
ck('189originalfullbytes',len([k for k in index if k.startswith('axiom-original/')])==189 and sum(v[1]for k,v in index.items()if k.startswith('axiom-original/'))==12499444)
a=r['parts'][0];archive=Path(a['archive_path']);plan=parts[0];ck('archive exact fullhash',digest(archive)==a['archive_sha256']=='b7d6aea19c5bcc81770c06ee8982d4687d80bd7e6f7a7dabd71b0ac6badbd3b2' and archive.stat().st_size==a['archive_bytes']==2548379)
ck('all scope planned once',len(plan['members_exact'])==len(set(plan['members_exact']))==206 and set(plan['members_exact'])==set(index))
with tarfile.open(archive,'r:gz')as t:
 members=t.getmembers();ck('exact archive order',[m.name for m in members]==plan['members_exact'])
 for m in members:
  p,size,h,st=index[m.name];ck('tar regular/size',m.isfile()and not m.islnk()and not m.issym()and m.size==size);ck('tar mode/mtime',m.mode==(st[2]&0o777)and m.mtime==st[4]//1000000000)
  hh=hashlib.sha256();length=0
  with t.extractfile(m)as stream:
   for chunk in iter(lambda:stream.read(1024**2),b''):hh.update(chunk);length+=len(chunk)
  ck('member exactbytes',length==size and hh.hexdigest()==h)
length=0
with gzip.open(archive,'rb')as f:
 for b in iter(lambda:f.read(1024**2),b''):length+=len(b)
ck('gzip wholeCRC/trailer',length==a['decompressed_tar_bytes']==12800000 and length<=plan['tar_upper_bytes'])
logical=sum(v[1]for v in index.values());upper=logical+4096*206+11264;over=(upper+4095)//4096+(upper+16383)//16384+(upper+33554431)//33554432+1024;budget=J(P/'PART1_BUDGET.json')
ck('exactfull budget',plan['required_fresh_bytes']==upper+over+66*1024**2==82718560 and plan['gzip_upper_bytes']==upper+over)
ck('originalfreshbudgetadmitted',budget['admitted'] is True and budget['fresh_output_free']>=plan['required_fresh_bytes'] and budget['compression_ratio_assumed'] is False and a['fresh_free_after']>=64*1024**2)
for p,size,h,st in index.values():ck('all source poststat',state(p)==st)
rows=outer['commands'];ck('one true collectorCLI',len(rows)==1)
for row in rows:
 d=Path(row['directory']);ck('collector source and exit',row['source_sha']==F and row['actual_process_returncode']==0 and row['timeout_expired'] is False)
 for stream in ['stdout','stderr']:
  data=(d/(stream+'.bin')).read_bytes();ck('complete original '+stream,len(data)==row[stream+'_bytes'] and H(data)==row[stream+'_sha256'])
 ck('full captured package result',json.loads((d/'stdout.bin').read_text().splitlines()[-1])==r)
 ck('request exact bytes',(P/'BOUND_REQUEST.json').read_bytes()==(C/'ROOT_REQUEST.json').read_bytes() and digest(C/'ROOT_REQUEST.json')==outer['request_sha256'])
ck('not rerun or delivered',r['subject_rerun'] is False and r['performance_rerun'] is False and r['published'] is False and r['delivered'] is False)
review={'schema':'F9-axiom-complete-terminal-package-actual-peer/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':0,'checks':n,'source_sha':F,'package_result_sha256':digest(P/'RESULT.json'),'outer_result_sha256':digest(C/'RESULT.json'),'host_final_sha256':digest(hostpath),'inventory_sha256':r['inventory_sha256'],'archive_path':str(archive),'archive_sha256':a['archive_sha256'],'archive_bytes':2548379,'regular_members':206,'logical_regular_bytes':12652356,'original_axiom_regular_files':189,'original_axiom_bytes':12499444,'original_gate_exit':0,'collection_exit':0,'blocking_findings':[],'limits':['Read-only formal require_escalated on closed package/original evidence; no source checkout or active314 nativeROOT access, no product test rerun.','All206 original source hashes/stat plus exact206 tar member bytes/type/mode/mtime and completegzipCRC verified.','Existing original428/0 formal actual peer reused; this is package integrity, not a second product sample.','Only metadata/exact-file inventories and original frozen tools included; no source tree/Gitobjects copied.','SHM volatile remains deliveredfalse until normal publication and complete remote blob verification.']}
p=O/'REVIEW.json';p.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'exit_code':0,'checks':n,'path':str(p),'sha256':H(p.read_bytes())}))
