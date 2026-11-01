from pathlib import Path
import hashlib,json,sys,tarfile
B=Path('/workspace/cold128-originals-20261024');O=Path('/workspace/train337-canvas-peer-resume');checks=0;find=[]
def ck(v,n):
 global checks
 checks+=1
 if not v:find.append(n)
def sh(b):return hashlib.sha256(b).hexdigest()
def h(p):return sh(Path(p).read_bytes())
def j(p):return json.loads(Path(p).read_text())
p=j(B/'PACKAGE.json');iv=j(B/'MEMBER_INVENTORY.json');im={x['member']:x for x in iv['members']};archive=Path(p['archive'])
ck(h(archive)==p['archive_sha256']==sys.argv[1] and archive.stat().st_size==p['archive_bytes'],'pinned compressed original package')
ck(h(B/'MEMBER_INVENTORY.json')==p['inventory_sha256']==sys.argv[2],'pinned full member inventory')
ck(len(im)==len(iv['members'])==p['original_member_count'] and sum(x['bytes'] for x in iv['members'])==p['original_bytes'],'exact unique original members and logical bytes')
seen=set()
with tarfile.open(archive,'r:gz') as tar:
 for m in tar:
  ck(m.isfile() and m.name not in seen and not m.name.startswith('/') and '..' not in Path(m.name).parts,'safe unique member '+m.name);seen.add(m.name);raw=tar.extractfile(m).read()
  if m.name=='MEMBER_INVENTORY.json':ck(raw==(B/'MEMBER_INVENTORY.json').read_bytes(),'embedded original inventory');continue
  x=im[m.name];ck(len(raw)==m.size==x['bytes'] and sh(raw)==x['sha256'],'exact member '+m.name);ck(raw==Path(x['source']).read_bytes(),'original full bytes '+m.name);ck(not raw.startswith(b'\x7fELF'),'no ELF '+m.name)
ck(seen==set(im)|{'MEMBER_INVENTORY.json'} and len(seen)==p['member_count'],'full exact archive coverage')
ck(p['exit_code']==0 and p['roundtrip_original_bytes'] and p['cold_receipt_alias_groups_added']==128 and p['all_established_cold_alias_groups']==423 and p['configured_gross_source_block_saving']==150953984,'maintenance128 only and423 reservation exact')
mf=j('/workspace/cold_small_128_exact_body_manifest_20261024.json');bodypaths={x['path'] for item in mf['items'] for x in j(item['plan'])['members']};sources={x['source'] for x in im.values()}
ck(len(bodypaths)==384 and not bodypaths&sources,'no duplicated384 actual receipt payloads')
for item in mf['items']:
 name=item['name'];ck(all('actual/'+name+'/'+x in im for x in ['RESULT.json','JOURNAL.jsonl','COMMANDS.json']) and 'launch/'+name+'/RESULT.json' in im and 'preparation/'+name+'/PLAN.json' in im and 'tools/'+name+'-executor.py' in im,'full original closed per-item proof '+name)
peerpins={'COLD128_NETPLAN_STATIC_PEER.json':'41e49f48b6cd5abf1c2cedc0696170924acff953ed54a33a0cdde95cb5563c15','COLD_128_EXACT_THREE_EXECUTOR_STATIC_PEER.json':'6475a978370bd7b97302cc2c73dff738211d167c561336cf1edc56dd62e201db','COLD128_ROOT_WRAPPER_STATIC_PEER.json':'205d447b6d838d29f1957aacca5ce5e42c5214e10dd36297453ea44324636aef','COLD128_ACTUAL_SUMMARY_HELPER_PEER.json':'28f54feb000438662e41c0e8bd8aa0ddd7b2eb2df74a338a1f7fa07bec68309d'}
for name,pin in peerpins.items():
 row=im['peers-and-review-tools/'+name];ck(row['sha256']==pin and j(row['source'])['exit_code']==0,'independent peer exact '+name)
ck(im['collector.py']['sha256']=='ecf974c68609a926c57d52da43e3d1fa12dd0366a12b6cd0d45a119feab5a153','reviewed exact collector source')
ck(im['prior-proof-reference/COLD59_CARDREF_PACKAGE.json']['sha256']=='43759f9d932eb66581fc3aad6a94e936e4c6334355c5e7fb56cc359646e0ab7d','prior original tree proof reference exact')
ck('root-sequential-execution.json' in im and im['root-sequential-execution.json']['source']=='/workspace/cold128-root-sequential-execution-20261024.json','complete root sequence original in package')
sequence=j(im['root-sequential-execution.json']['source']);ck(len(sequence)==128 and [x['name'] for x in sequence]==[x['name'] for x in mf['items']] and all(x['exit_code']==0 and isinstance(x['stdout'],str) and isinstance(x['stderr'],str) for x in sequence),'root sequential128 original exits and full decoded streams')
outer=j('/workspace/cold128-originals-collection-launch-20261024/RESULT.json');d=Path(outer['directory']);ck(outer['actual_process_returncode']==0 and not outer['timeout_expired'] and outer['ended_epoch']>=outer['started_epoch'] and outer['command'][-1]=='/workspace/collect_cold128_originals_20261024.py','collector actual zero')
ck(j(d/'result.json')==outer and j(d/'request.json')['command']==outer['command'],'collector original request/result')
for stream in ['stdin','stdout','stderr']:
 q=d/(stream+'.bin');ck(h(q)==outer[stream+'_sha256'],'collector original full stream '+stream)
 if stream!='stdin':ck(q.stat().st_size==outer[stream+'_bytes'],'collector original stream length '+stream)
r={'schema':'independent-cold128-original-package-peer-v1','checks':checks,'exit_code':int(bool(find)),'findings':find,'archive_sha256':p['archive_sha256'],'inventory_sha256':p['inventory_sha256'],'archive_members':p['member_count'],'original_members':p['original_member_count'],'original_bytes':p['original_bytes'],'new_groups':128,'all_reserved_cold_groups':423,'original_receipt_paths_retained':384,'root_sequential_original_included':True,'limits':['All packaged original small metadata and complete original streams independently byte-checked. No384 receipt payload rehash or duplication and no ELF read by this peer.','150953984 gross configured source-block savings are not net df recovery; original net sensitivity and overhead samples retained.','423 includes295 prior reserved groups. Only128 actual groups are in this new batch. All aliases remain write/reuse-banned until independently delinked; separate cardref2 groups excluded.','Original12.3MB Git-tree proof referenced via pinned already-published prior package, not recollected. Original selector direct exec provenance does not invent a c387 outer.','This collector outer and this later peer remain external attachments to the frozen archive. No product gate, source, fixture, Git object or branch modified.']}
q=O/'COLD128_ACTUAL_PACKAGE_PEER.json';q.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'path':str(q),'sha256':h(q),'checks':checks,'exit_code':r['exit_code'],'findings':find}));raise SystemExit(r['exit_code'])
