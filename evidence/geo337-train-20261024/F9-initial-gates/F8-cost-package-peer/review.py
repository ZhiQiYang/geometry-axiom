import os,pathlib,json,hashlib,tarfile,stat,datetime,collections,io
P=pathlib.Path
D=P('/tmp/geo341-F8-fallback-cost-package-20261025')
O=P('/tmp/geo341-F8-fallback-cost-run-20261025')
T=P('/tmp/geo341-cost-preparation-v2-20261025')
C=P('/tmp/geo341-F8-cost-collection-preparation-20261025')
R=P('/tmp/geo341-F8-fallback-cost-package-peer-20261025')
counts=collections.Counter();fail=[]
def ck(cat,condition,detail):
 counts[cat]+=1
 if not condition:fail.append({'category':cat,'detail':detail})
def read(p):
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NOATIME)
 with os.fdopen(fd,'rb') as f:return f.read()
def h(b):return hashlib.sha256(b).hexdigest()
def js(p):return json.loads(read(p))
p=js(D/'PACKAGE.json');idx=js(D/'INDEX.json');pins=js(T/'PINS.json');result=js(O/'RESULT.json')
ck('pins',h(read(D/'PACKAGE.json'))=='e7efffb7bbdc551e428f073ac1c3b89a9268da9f89c088202d433206cb73f475','PACKAGE identity')
ck('pins',h(read(D/'INDEX.json'))==p['index_sha256']=='d225e9f50ffb25d0df2f0a27325fe8394fdd47c08f0cf4153a22a991e8eba9c6','INDEX identity')
tarbytes=read(D/'originals.tar')
ck('pins',len(tarbytes)==p['archive_bytes']==19312640 and h(tarbytes)==p['archive_sha256']=='155b1088870e583e560ffced76dd550e259d87afbcfd689e4a3605bccccf4698','archive identity')
ck('scope',len(idx)==p['members']==2894,'members')
ck('scope',len({r['member'] for r in idx})==len(idx)==len({r['source'] for r in idx}),'unique names and sources')
expected={}
for f in O.rglob('*'):
 s=f.lstat()
 ck('scope',stat.S_ISREG(s.st_mode) or stat.S_ISDIR(s.st_mode),str(f))
 if stat.S_ISREG(s.st_mode):expected['original/'+f.relative_to(O).as_posix()]=str(f)
ck('scope',len(expected)==p['original_files']==2871,'all original files')
expected['terminal/EXEC_FINAL.json']='/tmp/geo341-F8-fallback-cost-EXEC_FINAL-20261025.json'
expected['tools/PINS.json']=str(T/'PINS.json')
for name,pin in pins.items():
 expected['tools/'+name]=str(T/name)
 ck('pins',h(read(T/name))==pin,name)
ck('scope',len(pins)==21 and {r['member']:r['source'] for r in idx}==expected,'exact entire source and pinned tool coverage')
ck('scope',sum(r['bytes'] for r in idx)==p['logical_bytes']==14394847,'logical bytes')
before=js(D/'SOURCE_STATE_BEFORE.json');after=js(D/'SOURCE_STATE_AFTER.json')
ck('state',before==after and h(read(D/'SOURCE_STATE_BEFORE.json'))==p['source_state_before_sha256']==p['source_state_after_sha256']==h(read(D/'SOURCE_STATE_AFTER.json')),'producer before/after equality')
ck('state',set(before)==set(expected.values()),'exact state scope')
by={r['member']:r for r in idx};seen=[];atime_changes=[];source_hashes={}
with tarfile.open(fileobj=io.BytesIO(tarbytes),mode='r:') as tf:
 for member in tf:
  seen.append(member.name)
  ck('tar',member.isfile() and not member.issym() and not member.islnk(),'regular '+member.name)
  ck('tar',not member.name.startswith('/') and '..' not in P(member.name).parts and member.name in by,'safe named '+member.name)
  if member.name not in by:continue
  row=by[member.name];payload=tf.extractfile(member).read();s=P(row['source']).lstat();b=read(row['source'])
  ck('payload',len(payload)==member.size==row['bytes']==len(b) and h(payload)==row['sha256']==h(b),member.name)
  ck('metadata',member.mode==row['mode']==stat.S_IMODE(s.st_mode) and member.uid==s.st_uid and member.gid==s.st_gid,member.name)
  ck('metadata',member.pax_headers.get('mtime')==str(row['original_state']['st_mtime_ns']//10**9)+'.'+str(row['original_state']['st_mtime_ns']%10**9).zfill(9),member.name)
  ck('state',row['original_state']==before[row['source']],'index state '+member.name)
  ck('state',all(getattr(s,k)==v for k,v in before[row['source']].items() if k!='st_atime_ns'),'current non-atime identity '+member.name)
  if s.st_atime_ns!=before[row['source']]['st_atime_ns']:atime_changes.append(member.name)
  source_hashes[row['source']]=row['sha256']
ck('tar',seen==[r['member'] for r in idx] and len(set(seen))==2894,'exact ordered complete members')
ck('commands',len(result['commands'])==p['original_commands']==546,'546 CLI')
for c in result['commands']:
 for stream in ['stdout','stderr']:
  # Original stream names are captured from the run record rather than regenerated.
  path=P(c['directory'])/(stream+'.bin')
  ck('commands',source_hashes.get(str(path))==c[stream+'_sha256'],str(path))
ck('elf',len(result['elfs'])==p['original_elfs']==9,'9 ELF')
for elf in result['elfs']:
 path=elf['path'];ck('elf',source_hashes.get(path)==elf['sha256'],path)
final=js(expected['terminal/EXEC_FINAL.json']);summary=json.loads(final['output'])
ck('status',p['collection_exit']==final['exit_code']==result['exit']==summary['exit']==0,'actual separate0s')
ck('status',p['source_sha']==result['source_sha']==summary['source_sha']=='75a1e93811a52b69385cbdaf6a09d773ed9052ad','fixed source')
ck('status',p['performance_acceptance_decided'] is result['performance_acceptance_decided'] is summary['performance_acceptance_decided'] is False and p['whole_341_B1_discharged'] is False,'limits retained')
cr=js(C/'COLLECT.result.json')
ck('producer',cr['exit_code']==0 and cr['command']==['python3','-B',str(C/'collect.py')],'original capture0')
ck('producer',h(read(C/'collect.py'))==cr['tool_sha256'],'producer pin')
for s in ['stdout','stderr']:ck('producer',h(read(C/('COLLECT.'+s+'.bin')))==cr[s+'_sha256'],s)
ck('producer',json.loads(read(C/'COLLECT.stdout.bin'))==p and read(C/'COLLECT.stderr.bin')==b'','complete captured summary')
ck('producer',p['resource']['tmp_free_before']-p['resource']['conservative_budget_bytes']>=p['resource']['reserve_bytes']==67108864 and p['tmp_free_after']>=67108864,'recorded reserve bound')
report={'schema':'geo341-original-archive-independent-peer/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit':1 if fail else 0,'checks':sum(counts.values()),'checks_by_category':dict(counts),'findings':fail,'source_sha':p['source_sha'],'package_sha256':h(read(D/'PACKAGE.json')),'archive_sha256':h(tarbytes),'index_sha256':p['index_sha256'],'members':len(seen),'logical_bytes':sum(r['bytes'] for r in idx),'archive_bytes':len(tarbytes),'original_commands':546,'original_elfs':9,'original_files':2871,'product_or_performance_rerun':False,'performance_acceptance_decided':False,'whole_341_B1_discharged':False,'state_scope':'Producer saved before/after state bytes match; reviewer compared current source identity except atime. Subsequent reads may update atime; no claim of eternal atime equality. Reviewer read all original payloads using O_NOATIME.','later_atime_changes_count':len(atime_changes),'later_atime_changes':atime_changes,'limitations':['No new product execution or performance acceptance.','Tar preserves complete OUT plus named final/PINS21 tools; external historical protocol proof directories are not in this tar unless pinned by name. They remain separate prior preparation evidence.','Independent semantic actual review remains separate: /tmp/geo341-F8-fallback-cost-actual-peer-20261025/REVIEW.json.']}
(R/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['later_atime_changes']},ensure_ascii=False))
raise SystemExit(report['exit'])
