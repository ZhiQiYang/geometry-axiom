from pathlib import Path
import hashlib,json,tarfile
B=Path('/workspace/emergency-twelve-and-cold105-originals-20261024');A=Path('/workspace/emergency-twelve-and-cold105-originals-collection-launch-20261024');O=Path('/workspace/train337-canvas-peer-resume');checks=0;find=[]
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sh(x):return hashlib.sha256(x).hexdigest()
def j(p):return json.loads(Path(p).read_text())
def ck(v,n):
 global checks
 checks+=1
 if not v:find.append(n)
p=j(B/'PACKAGE.json');iv=j(B/'MEMBER_INVENTORY.json');im={x['member']:x for x in iv['members']};sources={x['source'] for x in im.values()}
ck(h(p['archive'])==p['archive_sha256']=='280cff70d2a7c3460da26af7153d88c865a4e1016a4bc036107856471f140eed' and Path(p['archive']).stat().st_size==p['archive_bytes']==933474,'fixed small metadata tar hash/size')
ck(h(B/'MEMBER_INVENTORY.json')==p['inventory_sha256']=='2086e5e1a3b172621a65ca93403aa2b92d227be81c59d2dd98fc57324eeafd98','fixed embedded inventory pin')
ck(len(im)==len(iv['members'])==p['original_member_count']==4083 and sum(x['bytes'] for x in im.values())==p['original_bytes']==6821690,'exact original count/bytes')
seen=set()
with tarfile.open(p['archive'],'r|gz') as t:
 for member in t:
  ck(member.isfile() and member.name not in seen and not member.name.startswith('/') and '..' not in Path(member.name).parts,'safe unique member '+member.name);seen.add(member.name);data=t.extractfile(member).read()
  if member.name=='MEMBER_INVENTORY.json':ck(data==(B/'MEMBER_INVENTORY.json').read_bytes(),'complete embedded inventory');continue
  x=im[member.name];ck(len(data)==member.size==x['bytes'] and sh(data)==x['sha256'],'complete member bytes '+member.name)
  q=Path(x['source']);ck(q.is_file() and not q.is_symlink() and data==q.read_bytes(),'original exact bytes '+member.name)
  ck(not data.startswith(b'\x7fELF') and not q.name.endswith(('.tar.gz','.zip','.exe','.pyc')),'no archive/ELF payload '+member.name)
ck(seen==set(im)|{'MEMBER_INVENTORY.json'} and len(seen)==p['member_count']==4084,'exact archive member coverage')
specs=[('three-emergency-terminal-archives-preparation-20261024','three-emergency-terminal-archive-groups-preserving-links-execution-20261024','three-emergency-terminal-archive-groups-preserving-links-launch-20261024'),('two-prer5-terminal-archives-preparation-20261024','two-prer5-terminal-archive-groups-preserving-links-execution-20261024','two-prer5-terminal-archive-groups-preserving-links-launch-20261024'),('seven-postr5-terminal-archives-preparation-20261024','seven-postr5-terminal-archive-groups-preserving-links-execution-20261024','seven-postr5-terminal-archive-groups-preserving-links-launch-20261024')]
allarchive=set();plans=[]
def fulltree(root,exclude=()):
 q=Path(root);required={str(x) for x in q.rglob('*') if x.is_file() and '__pycache__' not in x.parts and str(x) not in exclude};ck(required<=sources,'complete original tree '+str(q))
for prep,raw,outer in specs:
 plan=j(Path('/workspace')/prep/'PLAN.json');r=j(Path('/workspace')/raw/'RESULT.json');a=j(Path('/workspace')/outer/'RESULT.json');plans.append(plan)
 ck(r['exit_code']==a['actual_process_returncode']==0 and r['all_original_payload_paths_retained'] and r['all_original_receipt_bytes_preserved'] and r['plan_sha256']==h(Path('/workspace')/prep/'PLAN.json'),'original actual outcome and fixed plan '+raw)
 members=[x for g in plan['groups'] for x in g['members']];allarchive.update(x['path'] for x in members)
 for root in [prep,raw,outer]:fulltree(Path('/workspace')/root)
 for x in plan['anchors']:ck(x['path'] in sources and h(x['path'])==x['sha256'],'original anchor '+x['path'])
 for x in plan['terminal_rows']:ck(x['path'] in sources and j(x['path'])==x['original_rows'],'original historical outcome rows '+x['path'])
ck(len(allarchive)==61 and not allarchive&sources,'all61 archive payloads excluded')
ck([[len(g['members']) for g in plan['groups']] for plan in plans]==[[7,7,7],[7,7],[4,7,7,2,2,2,2]],'original batch grouping retained')
ck(p['exit_code']==0 and p['roundtrip_original_bytes'] and p['configured_gross_archive_source_block_saving']==sum(x['expected_allocated_saving'] for x in plans)==365010944 and p['groups_added']=={'emergency':3,'preR5':2,'postR5':7} and p['cold105_gross_retired']==54906880,'precise original summary and allocation distinction')
peerpins={'THREE_EMERGENCY_ARCHIVE_GROUPS_STATIC_ACTUAL_METADATA_PEER.json':'46b3a926de36ea7e6846aac6dd67d961f2b8f4b6d0f3386cc81a30821b46009d','TWO_PRER5_ARCHIVE_GROUPS_STATIC_ACTUAL_METADATA_PEER.json':'ecae3c3ed3c6fb5ae626ad38a660c883bc9da603b463d6985812cfaa05c56225','SEVEN_POSTR5_ARCHIVE_GROUPS_STATIC_ACTUAL_METADATA_PEER.json':'31259dd572cb6fbe6954c9fe0751d484f60b384c342dff09710457cb503da11b','COLD105_RETIREMENT_ACTUAL_PEER.json':'fe9c935cbfd8b184ac90ad4be00a5ebbfdecb73b147c48b42f61e7de032545df'}
for name,pin in peerpins.items():
 q=O/name;r=j(q);ck(str(q) in sources and h(q)==pin and r['exit_code']==0 and not r['findings'],'fixed original independentpeer '+name)
for name in ['THREE_EMERGENCY_INITIAL_PATH_PREFIX_ASSUMPTION.json','review_three_emergency_archive_groups_actual.initial.py.txt','COLD105_RETIREMENT_INITIAL_OUTER_SCHEMA_ASSUMPTION.json','review_cold105_retirement_actual.initial.py.txt','COLD105_EXECUTOR_STATIC_PEER.json']:
 ck(str(O/name) in sources,'reviewer initial mistake/static original retained '+name)
cp=Path('/workspace/cold105-source-retirement-body-preparation-20261024');ce=Path('/workspace/cold105-source-retirement-execution-20261024');pr=j(cp/'PREPARED.json');cr=j(ce/'RESULT.json');pres=p['preserved_source_archive']
ck(pr['files']==105 and pr['unique_payloads']==16 and pr['full_byte_roundtrip'] and j(cp/'RESULT.json')['exit_code']==cr['exit_code']==0 and len(cr['removed'])==105 and cr['git_and_terminal_identities_unchanged'],'original105 actual source retention outcome')
ck(pres['path']==pr['archive'] and pres['bytes']==pr['archive_bytes']==2849441 and pres['sha256']==pr['archive_sha256']==cr['original_source_archive_sha256']=='9daa4fc1743fe2c864740dfeb679170da2adaa851a25b471f00e176b7f00c340' and pres['included_in_metadata_tar'] is False and pres['path'] not in sources and Path(pres['path']).stat().st_size==pres['bytes'],'separate preserved source payload exact locator/pin, not claimed included')
ck('alongside' in pres['publication_requirement'] and 'does not rehash' in pres['hash_provenance'],'mandatory separate payload publication and honest hash provenance')
fulltree(cp,{pres['path']});fulltree(ce);fulltree('/workspace/cold105-source-retirement-metadata-20261024')
for phase in ['prepare','execute']:
 q=Path('/workspace/cold105-source-retirement-'+phase+'-launch-20261024');fulltree(q);ck(j(q/'RESULT.json')['actual_exit']==0,'original105 outer0 '+phase)
fulltree('/workspace/L175-elf-retirement-preparation-20261024')
for path in ['/workspace/EMERGENCY_TWELVE_IMMUTABLE_ALIAS_REGISTRY_20261024.json','/workspace/FINAL_ACCEPTANCE_RESOURCE_PLAN_20261024.md']:
 ck(path in sources,'exact historical registry/resource-plan included '+path)
a=j(A/'RESULT.json');ck(a['actual_process_returncode']==0 and not a['timeout_expired'] and a['ended_epoch'] and a['command'][-1]=='/workspace/collect_emergency_twelve_and_cold105_originals_20261024.py','true original collector0')
for row in j(A/'subcommands.json'):
 d=Path(row['directory']);ck(j(d/'result.json')==row and j(d/'request.json')['command']==row['command'],'original collector request/result')
 for stream in ['stdout','stderr']:
  q=d/(stream+'.bin');ck(q.stat().st_size==row[stream+'_bytes'] and h(q)==row[stream+'_sha256'],'complete original collector '+stream)
 ck(h(d/'stdin.bin')==row['stdin_sha256'],'original collector stdin')
ck(h('/workspace/collect_emergency_twelve_and_cold105_originals_20261024.py')=='af535a120f4250510a43249cdc3fcd5f2c9b5e7069a46022af0e8c490a004802','actual final collector pin')
r={'schema':'emergency12-cold105-complete-original-package-peer-v1','checks':checks,'exit_code':int(bool(find)),'findings':find,'archive_sha256':p['archive_sha256'],'archive_members':4084,'original_bytes':6821690,'inventory_sha256':p['inventory_sha256'],'actual_collector_outer_exit':0,'preserved_source_archive':pres,'limits':['Only6.8MB original metadata/fullstreams and933474B small tar read; no61 original archive body or second cold105 payload hash.','Cold105 preserved16-payload tar is intentionally separate and must be published alongside this metadata tar.','Historical registry alias counts preserved as captured, not compared with current counts after root11-alias extension; new legitimate extension has separate3136/0 peer.','423cold,2cardref,1geo339-six,3large,4additional and new12groups keep their immutable alias write/reuse bans.','Original historical failures remain red; no product gate executed or reclassified.','Gross allocated block sums remain distinct from original df net changes; old175 absent ELF observation does not claim newly recovered space.']};q=O/'EMERGENCY12_COLD105_ACTUAL_PACKAGE_PEER.json';q.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(q),'sha256':h(q),'checks':checks,'exit_code':r['exit_code'],'findings':find}));raise SystemExit(r['exit_code'])
