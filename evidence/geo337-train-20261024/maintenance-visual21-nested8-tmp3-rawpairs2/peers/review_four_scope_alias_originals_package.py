from pathlib import Path
import hashlib,json,tarfile,stat
O=Path('/workspace/train337-canvas-peer-resume');B=Path('/workspace/visual-nested-tmp-stdout-alias-originals-20261024');A=Path('/workspace/visual-nested-tmp-stdout-alias-originals-collection-launch-20261024');checks=0;findings=[]
def h(b):return hashlib.sha256(b).hexdigest()
def j(p):return json.loads(Path(p).read_bytes())
def ck(v,n):
 global checks
 checks+=1
 if not v:findings.append(n)
p=j(B/'PACKAGE.json');inv=Path(p['inventory']).read_bytes();rows=json.loads(inv)['members'];index={x['member']:x for x in rows};archive=Path(p['archive'])
ck(p['exit_code']==0 and p['roundtrip_original_bytes'] and p['original_member_count']==len(rows)==10458 and p['member_count']==10459,'original successful package cardinality')
ck(archive.stat().st_size==p['archive_bytes']==2030733 and h(archive.read_bytes())==p['archive_sha256']=='bfe387358f4f0c4216ad6c1ad2a52a8de02646f3a7288149dbfa4c04008c7bf9','fixed unique archive hash')
ck(h(inv)==p['inventory_sha256']=='d3669dd4ab59ba4d29d22d851a6312d0d758d807bb0d17a7a29a11b4bd105af3' and len(index)==len(rows),'fixed unique member inventory')
plans={}
for label,base in [('visual21','twentyone-cold-visual-groups'),('nested8','eight-cold-nested-archive-groups'),('tmp3','tmp-three-cold-archive-groups'),('rawpairs2','r5-r6-two-archive-stdout-pairs')]:plans[label]=j('/workspace/'+base+'-preparation-20261024/PLAN.json')
bodymap={x['path']:x for plan in plans.values() for g in plan['groups'] for x in g['members']};bodies=set(bodymap)
ck(len(bodies)==221 and all(x['source'] not in bodies for x in rows),'no221 original payload bodies duplicated')
ck(sum(x['bytes'] for x in rows)==p['original_bytes']==16235098,'exact original small bytes')
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
for label,groups,paths in [('visual21',21,147),('nested8',8,56),('tmp3',3,14),('rawpairs2',2,4)]:
 act=objects['actual/'+label+'/RESULT.json'];launch=objects['launch/'+label+'/RESULT.json'];pl=objects['preparation/'+label+'/PLAN.json']
 ck(act['exit_code']==launch['actual_process_returncode']==0 and not launch['timeout_expired'],'actual and original outer true0 '+label)
 ck(act['plan_sha256']==index['preparation/'+label+'/PLAN.json']['sha256'] and pl==plans[label],'fixed original plan bytes '+label)
 ck(act['all_original_payload_paths_retained'] and act['all_original_receipt_bytes_preserved'] and len(pl['groups'])==groups and sum(len(g['members']) for g in pl['groups'])==paths,'exact original retained scope '+label)
for name in ['VISUAL21_NESTED8_STATIC_ACTUAL_METADATA_PEER.json','TMP_THREE_ARCHIVE_STATIC_ACTUAL_METADATA_PEER.json','R5_R6_ARCHIVE_STDOUT_PAIRS_STATIC_ACTUAL_PEER.json']:
 q=objects['peers-and-review-tools/'+name];ck(q['exit_code']==0 and not q['findings'],'original independent actual peer '+name)
ck(p['group_counts']==[21,8,3,2] and p['preserved_path_counts']==[147,56,14,4] and p['configured_gross_saving']==706985984,'exact four scopes configured figures')
for name in ['peers-and-review-tools/VISUAL21_NESTED8_INITIAL_ARCHIVE_SUFFIX_ASSUMPTION.json','peers-and-review-tools/R5_R6_STDOUT_PAIRS_REVIEW_INITIAL_ARGV_ASSUMPTION.json','preparation/rawpairs2/INITIAL_STDIN_ASSUMPTION.json']:ck(name in objects,'original review/producer error retained '+name)
ledger_count=0
for name,obj in objects.items():
 if isinstance(obj,dict) and 'actual_process_returncode'in obj and 'directory'in obj and 'stdout_sha256'in obj:
  d=Path(obj['directory']);ledger_count+=1
  ck(j(d/'result.json')==obj and j(d/'request.json')['command']==obj['command'],'original request/result crossbinding '+name)
  for stream in ['stdout','stderr']:
   q=d/(stream+'.bin')
   if str(q) in bodies:ck(q.stat().st_size==obj[stream+'_bytes']==bodymap[str(q)]['size'] and obj[stream+'_sha256']==bodymap[str(q)]['sha256'],'excluded original raw payload pin unchanged; no rehash')
   else:ck(q.stat().st_size==obj[stream+'_bytes'] and h(q.read_bytes())==obj[stream+'_sha256'],'full original ledger stream '+name+'/'+stream)
  ck(obj['ended_epoch']>=obj['started_epoch'] and not obj['timeout_expired'],'original terminal record '+name)
outer=j(A/'RESULT.json');ck(outer['actual_process_returncode']==0 and not outer['timeout_expired'],'actual collector outer0')
d=Path(outer['directory']);ck(j(d/'result.json')==outer and j(d/'request.json')['command']==outer['command'],'collector original request/result')
for stream in ['stdout','stderr']:
 q=d/(stream+'.bin');ck(q.stat().st_size==outer[stream+'_bytes'] and h(q.read_bytes())==outer[stream+'_sha256'],'collector full original '+stream)
ck(json.loads((d/'stdout.bin').read_bytes())==p,'collector original stdout package equality')
report={'schema':'four-alias-scopes-originals-actual-package-peer-v1','checks':checks,'exit_code':int(bool(findings)),'findings':findings,'package':str(B/'PACKAGE.json'),'package_sha256':h((B/'PACKAGE.json').read_bytes()),'archive_sha256':p['archive_sha256'],'archive_bytes':p['archive_bytes'],'inventory_sha256':p['inventory_sha256'],'members':10459,'original_bytes':16235098,'original_command_records_crosschecked':ledger_count,'collector_outer_sha256':h((A/'RESULT.json').read_bytes()),'limits':['One small16MB metadata archive streamed and every member compared with its original; no221 archive/image/raw stdout payload body read or test rerun.','21visual147paths/8nested56paths/TMP3fourteenpaths/two raw stdout pairs4paths are separate exact scopes. Configured gross706985984 is not global df recovery.','Four excluded archive stdout bodies are bound by original command+plan SHA/size without rereading large bodies; complete original raw packages stay intact.','Original failure records and historical registry facts remain unchanged. Collector full original stdout/stderr/RESULT and actual peer must be external post-package attachments.','Maintenance0 is not product acceptance. Every affected immutable alias remains forbidden to write until safely delinked.']}
q=O/'FOUR_SCOPE_ALIAS_ORIGINALS_ACTUAL_PACKAGE_PEER.json';q.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(q),'sha256':h(q.read_bytes()),'checks':checks,'exit_code':report['exit_code'],'findings':findings}));raise SystemExit(report['exit_code'])
