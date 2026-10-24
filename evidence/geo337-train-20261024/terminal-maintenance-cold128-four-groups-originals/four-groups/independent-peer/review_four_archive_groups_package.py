from pathlib import Path
import hashlib,json,tarfile,stat
B=Path('/workspace/four-archive-groups-originals-20261024');A=Path('/workspace/four-archive-groups-originals-collection-launch-20261024');O=Path('/workspace/train337-canvas-peer-resume');checks=0;find=[]
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sh(x):return hashlib.sha256(x).hexdigest()
def j(p):return json.loads(Path(p).read_text())
def ck(v,n):
 global checks
 checks+=1
 if not v:find.append(n)
p=j(B/'PACKAGE.json');iv=j(B/'MEMBER_INVENTORY.json');im={x['member']:x for x in iv['members']};sources={x['source'] for x in im.values()}
ck(h(p['archive'])==p['archive_sha256']=='fc852b7d53c9c0c41feb2ce6256e61723cf2903fcdff4142e1076bb237ce73e7' and Path(p['archive']).stat().st_size==p['archive_bytes']==248731,'fixed small tar hash/size')
ck(h(B/'MEMBER_INVENTORY.json')==p['inventory_sha256']=='df0c9c152626cf889768f97c02247a719a83523bce3e2acb5825fa995b3c9d87','fixed embedded inventory pin')
ck(len(im)==len(iv['members'])==p['original_member_count']==839 and sum(x['bytes'] for x in im.values())==p['original_bytes']==1694913,'exact count/bytes')
seen=set()
with tarfile.open(p['archive'],'r|gz') as t:
 for member in t:
  ck(member.isfile() and member.name not in seen and not member.name.startswith('/') and '..' not in Path(member.name).parts,'safe unique originalmember '+member.name);seen.add(member.name);data=t.extractfile(member).read()
  if member.name=='MEMBER_INVENTORY.json':ck(data==(B/'MEMBER_INVENTORY.json').read_bytes(),'full embedded inventory');continue
  x=im[member.name];ck(len(data)==member.size==x['bytes'] and sh(data)==x['sha256'],'complete member bytes '+member.name)
  q=Path(x['source']);ck(q.is_file() and not q.is_symlink() and data==q.read_bytes(),'original exact byte equality '+member.name)
  ck(not data.startswith(b'\x7fELF') and not q.name.endswith(('.tar.gz','.zip','.exe','.pyc')),'no archive/ELFpayload '+member.name)
ck(seen==set(im)|{'MEMBER_INVENTORY.json'} and len(seen)==p['member_count']==840,'exact archive coverage')
for prep,raw,outer in [('geo339-six-original-aliases-preparation-20261024','geo339-six-terminal-originals-preserving-links-execution-20261024','geo339-six-terminal-originals-preserving-links-launch-20261024'),('three-large-terminal-archives-preparation-20261024','three-large-terminal-archive-groups-preserving-links-execution-20261024','three-large-terminal-archive-groups-preserving-links-launch-20261024')]:
 plan=j(Path('/workspace')/prep/'PLAN.json');r=j(Path('/workspace')/raw/'RESULT.json');a=j(Path('/workspace')/outer/'RESULT.json')
 ck(r['exit_code']==a['actual_process_returncode']==0 and r['all_original_payload_paths_retained'] and r['all_original_receipt_bytes_preserved'],'true retained maintenance terminal '+raw)
 members=plan.get('members',[]) or [x for g in plan['groups'] for x in g['members']];ck(not {x['path'] for x in members}&sources,'all named archive bodies excluded '+prep)
 for root in [prep,raw,outer]:
  required={str(q) for q in (Path('/workspace')/root).rglob('*') if q.is_file() and '__pycache__' not in q.parts};ck(required<=sources,'complete original tree coverage '+root)
 for anchor in plan['anchors']:ck(anchor['path'] in sources and h(anchor['path'])==anchor['sha256'],'all original anchors unchanged '+anchor['path'])
ck(p['exit_code']==0 and p['roundtrip_original_bytes'] and p['configured_gross_source_block_saving']==476540928 and p['groups_added']=={'six_archive_alias_group':1,'large_archive_groups':3},'precise original summary distinction')
for n,pin in [('THREE_LARGE_ARCHIVE_GROUPS_ACTUAL_METADATA_PEER.json','4bad5355412503c588c0332df2800f87cb0bbcdaa73a64cdf5b45d6303b1316b'),('THREE_LARGE_ARCHIVE_GROUPS_STATIC_PEER.json','e12e1c88c4e0c014433eebb210e36350929f64d9d6b88e7ed8d37ed4d1e1b921'),('GEO339_SIX_ALIAS_STATIC_PEER.json','0bdc6f0114a5abd895aa9385a0a4236a130d98cc28f25d7748cb3c717a3e6fda')]:
 q=O/n;r=j(q);ck(str(q) in sources and h(q)==pin and r['exit_code']==0 and not r['findings'],'fixed original independentpeer '+n)
q=Path('/workspace/geo339-six-alias-independent-peer-20261024/REVIEW.json');r=j(q);ck(str(q) in sources and r['failed_checks']==0 and not r['findings'],'original6aliasactualpeer included')
a=j(A/'RESULT.json');ck(a['actual_process_returncode']==0 and not a['timeout_expired'] and a['ended_epoch'] and a['command'][-1]=='/workspace/collect_four_archive_groups_originals_combined_20261024.py','true original collector0')
for row in j(A/'subcommands.json'):
 d=Path(row['directory']);ck(j(d/'result.json')==row and j(d/'request.json')['command']==row['command'],'actual outer request/result')
 for stream in ['stdout','stderr']:
  q=d/(stream+'.bin');ck(q.stat().st_size==row[stream+'_bytes'] and h(q)==row[stream+'_sha256'],'complete actual collector outer '+stream)
 ck(h(d/'stdin.bin')==row['stdin_sha256'],'actual collectorstdin')
ck(h('/workspace/collect_four_archive_groups_originals_combined_20261024.py')=='778c03422749422fb2b522f7562920edc1f52bb8705ae5de3ff220d5f44e29da','actual fixed collector')
r={'schema':'four-archive-groups-complete-original-package-peer-v1','checks':checks,'exit_code':int(bool(find)),'findings':find,'archive_sha256':p['archive_sha256'],'archive_members':840,'original_bytes':1694913,'inventory_sha256':p['inventory_sha256'],'actual_collector_outer_exit':0,'limits':['Only1.7MB original metadata/fullstreams and248731B small tar read; no19 original archive bodies hashed or copied.','423cold,2cardref,1geo339-six,3large groups remain separate immutable write/reuse bans.','Original historical red outcomes remain red; no product gate executed or reclassified.','Source allocation saving476540928 remains distinct from actual df free-space delta.']};q=O/'FOUR_ARCHIVE_GROUPS_ACTUAL_PACKAGE_PEER.json';q.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(q),'sha256':h(q),'checks':checks,'exit_code':r['exit_code'],'findings':find}));raise SystemExit(r['exit_code'])
