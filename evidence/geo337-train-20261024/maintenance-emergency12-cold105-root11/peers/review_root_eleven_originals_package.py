from pathlib import Path
import hashlib,json,tarfile,stat
O=Path('/workspace/train337-canvas-peer-resume');B=Path('/workspace/root-eleven-archive-extensions-originals-20261024');A=Path('/workspace/root-eleven-archive-extensions-originals-collection-launch-20261024');checks=0;findings=[]
def h(b):return hashlib.sha256(b).hexdigest()
def j(p):return json.loads(Path(p).read_bytes())
def ck(v,n):
 global checks
 checks+=1
 if not v:findings.append(n)
p=j(B/'PACKAGE.json');inv=Path(p['inventory']).read_bytes();rows=json.loads(inv)['members'];index={x['member']:x for x in rows};archive=Path(p['archive'])
ck(p['exit_code']==0 and p['roundtrip_original_bytes'] and p['original_member_count']==len(rows)==4319 and p['member_count']==4320,'original successful package cardinality')
ck(archive.stat().st_size==p['archive_bytes']==851884 and h(archive.read_bytes())==p['archive_sha256']=='8de4b7096edbd9a21998205c6c1fce7b81917c8dde0f5bec03a31edf1c9e0c3d','fixed unique archive hash')
ck(h(inv)==p['inventory_sha256']=='b59552954291fb67254528826e19f3792bd4634b492dcf0c1ae8cf459e25a140' and len(index)==len(rows),'fixed unique member inventory')
plan=j('/workspace/root-eleven-archive-alias-extension-preparation-20261024/PLAN.json');bodies={x['path'] for g in plan['groups'] for x in g['members']}
ck(len(bodies)==88 and all(x['source'] not in bodies for x in rows),'no88 original archive bodies duplicated')
ck(sum(x['bytes'] for x in rows)==p['original_bytes']==6395765,'exact original small bytes')
seen=set();objects={}
with tarfile.open(archive,'r|gz') as tf:
 for member in tf:
  ck(member.name not in seen and member.isfile() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts,'safe unique regular tar member '+member.name);seen.add(member.name);data=tf.extractfile(member).read()
  if member.name=='MEMBER_INVENTORY.json':ck(data==inv,'embedded exact inventory');continue
  x=index.get(member.name);ck(x is not None,'listed member '+member.name)
  if x is None:continue
  ck(len(data)==member.size==x['bytes'] and h(data)==x['sha256'],'original member full bytes '+member.name)
  src=Path(x['source']);ck(src.is_file() and not src.is_symlink() and src.stat().st_size==x['bytes'] and h(src.read_bytes())==x['sha256'],'original source full bytes '+member.name)
  ck(member.mode==stat.S_IMODE(x['mode']) and member.uid==x['uid'] and member.gid==x['gid'],'preserved tar metadata '+member.name)
  if member.name.endswith('.json'):
   try:objects[member.name]=json.loads(data)
   except (ValueError,UnicodeError):pass
ck(seen==set(index)|{'MEMBER_INVENTORY.json'},'exact complete member set')
act=objects['actual/root-eleven/RESULT.json'];launch=objects['launch/root-eleven/RESULT.json'];pl=objects['preparation/root-eleven/PLAN.json']
ck(act['exit_code']==launch['actual_process_returncode']==0 and not launch['timeout_expired'] and act['plan_sha256']==h(Path('/workspace/root-eleven-archive-alias-extension-preparation-20261024/PLAN.json').read_bytes()),'original actual and launcher true0')
ck(act['all_original_payload_paths_retained'] and act['all_original_receipt_bytes_preserved'] and [g['count'] for g in pl['groups']]==[8]*11,'original11 extension88paths retained')
for name in ['ROOT_ELEVEN_ALIAS_EXTENSIONS_STATIC_ACTUAL_PEER.json','ROOT_ELEVEN_ARCHIVE_EXTENSIONS_ACTUAL_METADATA_20261024.json']:
 q=objects['peers-and-review-tools/'+name];ck(q['exit_code']==0 and not q['findings'],'original actual peer '+name)
ck(p['old_aliases_preserved']==77 and p['new_root_aliases']==11 and p['existing_archive_groups_extended']==11 and p['total_aliases_in_scope']==88 and p['configured_gross_new_root_leaf_saving']==134045696,'exact scope; no new11groups claim')
ledger_count=0
for name,obj in objects.items():
 if isinstance(obj,dict) and 'actual_process_returncode'in obj and 'directory'in obj and 'stdout_sha256'in obj:
  d=Path(obj['directory']);ledger_count+=1
  ck(j(d/'result.json')==obj and j(d/'request.json')['command']==obj['command'],'original request/result crossbinding '+name)
  for stream in ['stdout','stderr']:
   q=d/(stream+'.bin');ck(q.stat().st_size==obj[stream+'_bytes'] and h(q.read_bytes())==obj[stream+'_sha256'],'full original ledger stream '+name+'/'+stream)
  ck(obj['ended_epoch']>=obj['started_epoch'] and not obj['timeout_expired'],'original terminal record '+name)
outer=j(A/'RESULT.json');ck(outer['actual_process_returncode']==0 and not outer['timeout_expired'],'actual collector outer0')
d=Path(outer['directory']);ck(j(d/'result.json')==outer and j(d/'request.json')['command']==outer['command'],'collector original request/result')
for stream in ['stdout','stderr']:
 q=d/(stream+'.bin');ck(q.stat().st_size==outer[stream+'_bytes'] and h(q.read_bytes())==outer[stream+'_sha256'],'collector full original '+stream)
ck(json.loads((d/'stdout.bin').read_bytes())==p,'collector original stdout package equality')
report={'schema':'root-eleven-extension-originals-actual-package-peer-v1','checks':checks,'exit_code':int(bool(findings)),'findings':findings,'package':str(B/'PACKAGE.json'),'package_sha256':h((B/'PACKAGE.json').read_bytes()),'archive_sha256':p['archive_sha256'],'archive_bytes':p['archive_bytes'],'inventory_sha256':p['inventory_sha256'],'members':4320,'original_bytes':6395765,'original_command_records_crosschecked':ledger_count,'collector_outer_sha256':h((A/'RESULT.json').read_bytes()),'limits':['One small metadata archive streamed; no88 archive payload body reads or new product tests.','Only11 root immutable leaves were added to existing seven-alias groups; old77 paths retained;19 total prior groups113paths is not30groups.','Preserved historical nlink facts and original failed receipts remain historical. No previous evidence is rewritten.','Collector original full stdout/stderr/RESULT are external post-package attachments and must be published alongside this peer; no self-reference.','Maintenance0 is not product acceptance. All affected aliases remain immutable until safely independently delinked.']}
q=O/'ROOT_ELEVEN_ORIGINALS_ACTUAL_PACKAGE_PEER.json';q.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(q),'sha256':h(q.read_bytes()),'checks':checks,'exit_code':report['exit_code'],'findings':findings}));raise SystemExit(report['exit_code'])
