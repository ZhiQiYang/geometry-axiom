from pathlib import Path
import hashlib,json,tarfile,stat
B=Path('/workspace/four-additional-archive-groups-originals-20261024');A=Path('/workspace/four-additional-archive-groups-originals-collection-launch-20261024');O=Path('/workspace/train337-canvas-peer-resume');checks=0;find=[]
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sh(x):return hashlib.sha256(x).hexdigest()
def j(p):return json.loads(Path(p).read_text())
def ck(v,n):
 global checks
 checks+=1
 if not v:find.append(n)
p=j(B/'PACKAGE.json');iv=j(B/'MEMBER_INVENTORY.json');im={x['member']:x for x in iv['members']};sources={x['source'] for x in im.values()}
ck(h(p['archive'])==p['archive_sha256']=='e85764f616d5801a9fa13e23ea56cbfdaf32d8ccc203b1b0f48012c423bd31b6' and Path(p['archive']).stat().st_size==p['archive_bytes']==359949,'fixed small tar hash/size')
ck(h(B/'MEMBER_INVENTORY.json')==p['inventory_sha256']=='4db25ad5ef500ae8139a79e48b8b1494aab4a833d44c183d93bc03a8ae2177ec','fixed embedded inventory pin')
ck(len(im)==len(iv['members'])==p['original_member_count']==1596 and sum(x['bytes'] for x in im.values())==p['original_bytes']==2618843,'exact count/bytes')
seen=set()
with tarfile.open(p['archive'],'r|gz') as t:
 for member in t:
  ck(member.isfile() and member.name not in seen and not member.name.startswith('/') and '..' not in Path(member.name).parts,'safe unique originalmember '+member.name);seen.add(member.name);data=t.extractfile(member).read()
  if member.name=='MEMBER_INVENTORY.json':ck(data==(B/'MEMBER_INVENTORY.json').read_bytes(),'full embedded inventory');continue
  x=im[member.name];ck(len(data)==member.size==x['bytes'] and sh(data)==x['sha256'],'complete member bytes '+member.name)
  q=Path(x['source']);ck(q.is_file() and not q.is_symlink() and data==q.read_bytes(),'original exact byte equality '+member.name)
  ck(not data.startswith(b'\x7fELF') and not q.name.endswith(('.tar.gz','.zip','.exe','.pyc')),'no archive/ELFpayload '+member.name)
ck(seen==set(im)|{'MEMBER_INVENTORY.json'} and len(seen)==p['member_count']==1597,'exact archive coverage')
for prep,raw,outer in [('four-additional-terminal-archives-preparation-r2-20261024','four-additional-terminal-archive-groups-preserving-links-execution-20261024','four-additional-terminal-archive-groups-preserving-links-launch-20261024')]:
 plan=j(Path('/workspace')/prep/'PLAN.json');r=j(Path('/workspace')/raw/'RESULT.json');a=j(Path('/workspace')/outer/'RESULT.json')
 ck(r['exit_code']==a['actual_process_returncode']==0 and r['all_original_payload_paths_retained'] and r['all_original_receipt_bytes_preserved'],'true retained maintenance terminal '+raw)
 members=plan.get('members',[]) or [x for g in plan['groups'] for x in g['members']];ck(not {x['path'] for x in members}&sources,'all named archive bodies excluded '+prep)
 for root in [prep,raw,outer]:
  required={str(q) for q in (Path('/workspace')/root).rglob('*') if q.is_file() and '__pycache__' not in q.parts};ck(required<=sources,'complete original tree coverage '+root)
 for anchor in plan['anchors']:ck(anchor['path'] in sources and h(anchor['path'])==anchor['sha256'],'all original anchors unchanged '+anchor['path'])
ck(p['exit_code']==0 and p['roundtrip_original_bytes'] and p['configured_gross_source_block_saving']==300097536 and p['groups_added']=={'additional_large_archive_groups':4},'precise original summary distinction')
for n,pin in [('FOUR_ADDITIONAL_ARCHIVE_GROUPS_ACTUAL_METADATA_PEER.json','c504e4d807c8e3016fcf0de5e31e5d69064690c301bee4daa39e0d4b5b4fa2f5'),('FOUR_ADDITIONAL_ARCHIVE_GROUPS_STATIC_PEER.json','bf0879cc6a97b844c75fc0408f6d95c2ee215f2d5b1ffdb75dc95ef1868094f6')]:
 q=O/n;r=j(q);ck(str(q) in sources and h(q)==pin and r['exit_code']==0 and not r['findings'],'fixed original independentpeer '+n)
initial=Path('/workspace/four-additional-terminal-archives-preparation-20261024');required={str(q) for q in initial.rglob('*') if q.is_file() and '__pycache__' not in q.parts};ck(required<=sources,'initial prefix failure complete original tree retained')
q=Path('/workspace/FOUR_ADDITIONAL_ARCHIVE_GROUPS_ACTUAL_METADATA_20261024.json');r=j(q);ck(str(q) in sources and r['exit_code']==0 and not r['findings'],'owner actual metadata peer included')
a=j(A/'RESULT.json');ck(a['actual_process_returncode']==0 and not a['timeout_expired'] and a['ended_epoch'] and a['command'][-1]=='/workspace/collect_four_additional_archive_groups_originals_20261024.py','true original collector0')
for row in j(A/'subcommands.json'):
 d=Path(row['directory']);ck(j(d/'result.json')==row and j(d/'request.json')['command']==row['command'],'actual outer request/result')
 for stream in ['stdout','stderr']:
  q=d/(stream+'.bin');ck(q.stat().st_size==row[stream+'_bytes'] and h(q)==row[stream+'_sha256'],'complete actual collector outer '+stream)
 ck(h(d/'stdin.bin')==row['stdin_sha256'],'actual collectorstdin')
ck(h('/workspace/collect_four_additional_archive_groups_originals_20261024.py')=='dcb9f8adf69e3485c56858a366aa2167d7a2b3df91d0bc97ae9d5ac03464427b','actual fixed collector')
r={'schema':'four-additional-archive-groups-complete-original-package-peer-v1','checks':checks,'exit_code':int(bool(find)),'findings':find,'archive_sha256':p['archive_sha256'],'archive_members':1597,'original_bytes':2618843,'inventory_sha256':p['inventory_sha256'],'actual_collector_outer_exit':0,'limits':['Only2.6MB original metadata/fullstreams and359949B small tar read; no28 original archive bodies hashed or copied.','423cold,2cardref,1geo339-six,3large,4additional groups remain separate immutable write/reuse bans.','Original historical red outcomes remain red; no product gate executed or reclassified.','Source allocation saving300097536 remains distinct from actual df free-space delta.']};q=O/'FOUR_ADDITIONAL_ARCHIVE_GROUPS_ACTUAL_PACKAGE_PEER.json';q.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(q),'sha256':h(q),'checks':checks,'exit_code':r['exit_code'],'findings':find}));raise SystemExit(r['exit_code'])
