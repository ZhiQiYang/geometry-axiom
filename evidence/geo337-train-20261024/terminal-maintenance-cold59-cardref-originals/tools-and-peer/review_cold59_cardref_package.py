from pathlib import Path
import hashlib,json,tarfile
B=Path('/workspace/cold59-and-cardref-links-originals-20261024');count=0;findings=[]
def ck(n,v):
 global count
 count+=1
 if not v:findings.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
def h(p):return sha(Path(p).read_bytes())
def rd(p):return json.loads(Path(p).read_text())
p=rd(B/'PACKAGE.json');i=rd(B/'MEMBER_INVENTORY.json');members={x['member']:x for x in i['members']};archive=Path(p['archive'])
ck('fixed archive pin',h(archive)==p['archive_sha256']=='0c9cb4ef4f425d7cb7ab7542c0b183ac55f09d6ada7350ea7e4e36bf7c95fcdb' and archive.stat().st_size==p['archive_bytes']==4160382)
ck('fixed inventory pin',h(B/'MEMBER_INVENTORY.json')==p['inventory_sha256']=='e5b53875bcb05cee8322f2b8aa7c11c698bdc775df9009ef53c3270391b708af')
ck('unique7486 originalmembers/bytes',len(members)==len(i['members'])==p['original_member_count']==7486 and sum(x['bytes'] for x in i['members'])==p['original_bytes']==20684123)
with tarfile.open(archive,'r:gz') as tar:
 seen=set()
 for m in tar:
  ck('safe unique regular '+m.name,m.name not in seen and m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts);seen.add(m.name);raw=tar.extractfile(m).read()
  if m.name=='MEMBER_INVENTORY.json':ck('embeddedinventory exact',raw==(B/'MEMBER_INVENTORY.json').read_bytes());continue
  x=members[m.name];ck('archived exact '+m.name,len(raw)==x['bytes'] and sha(raw)==x['sha256']);ck('original exact '+m.name,raw==Path(x['source']).read_bytes())
  ck('no ELF payload '+m.name,not raw.startswith(b'\x7fELF'))
 ck('7487 exactcomplete',seen==set(members)|{'MEMBER_INVENTORY.json'} and len(seen)==p['member_count']==7487)
ck('exact59cold295total and286375936 allocated',p['cold_receipt_alias_groups_added']==59 and p['all_established_cold_alias_groups']==295 and p['cold_preserving_dedup_allocated_saving']==286375936)
ck('separate2cardref groups79196160',p['cardref_elf_alias_groups_added']==2 and p['cardref_preserving_dedup_allocated_saving']==79196160)
mf=rd('/workspace/cold_text_59_exact_body_manifest_20261024.json');cp=rd('/workspace/cardref-preserving-elf-links-preparation-20261024/PLAN.json')
body_paths={m['path'] for item in mf['items'] for m in rd(item['plan'])['members']}|{x['source_path'] for x in rd(cp['original_excluded_inventory']['path'])}
sources={x['source'] for x in members.values()};ck('no177receipt or116ELF payload in collected namespace',not (sources&body_paths) and len(body_paths)==293)
expected_peers={'COLD59_ACTUAL_SUMMARY_HELPER_PEER.json':'6b726e8bd78c902b99a774c042486d640ece7227d1047c000c96d62ee6245d97','CARDREF_PRESERVING_LINKS_ACTUAL_CROSS_PEER.json':'d7c95c4019b447696bcafae807bad24dc6a93e65911488f94d4b4b33ec5e2ca5','COLD_59_EXACT_THREE_EXECUTOR_STATIC_PEER.json':'e68859506063e627721e248d30af14880e42479e32b8de5fc98d807aac9a33fc','COLD59_IMMUTABLE_SCOPE_PEER.json':'1808059aa577c213d38933b7a1a0b33cd4af67b1191f8ff39a72a8c4d13e2c2a'}
for name,pin in expected_peers.items():ck('fixed independently reviewed peer '+name,members['peers-and-review-tools/'+name]['sha256']==pin and rd(members['peers-and-review-tools/'+name]['source'])['exit_code']==0)
ck('original producer/reviewer errors preserved',all('peers-and-review-tools/'+x in members for x in ['COLD59_SCOPE_INITIAL_SCHEMA_ERROR.json','review_cold59_immutable_scope.v1.py.txt']))
for item in mf['items']:
 name=item['name'];prefix='actual/'+name+'/'
 ck('full exact operation original '+name,all(prefix+x in members for x in ['RESULT.json','JOURNAL.jsonl','COMMANDS.json']) and 'launch/'+name+'/RESULT.json' in members and 'preparation/'+name+'/PLAN.json' in members and 'tools/'+name+'-executor.py' in members)
ck('original collector pin',members['collector.py']['sha256']=='e4b0056a2dc08a5b1900f26abbeb7644726464a5a75d77b8a0fb226051a0c1b5')
outer=rd('/workspace/cold59-and-cardref-links-collection-launch-20261024/RESULT.json');d=Path(outer['directory']);ck('collector actual original0',outer['actual_process_returncode']==0 and not outer['timeout_expired'] and outer['command'][-1]=='/workspace/collect_cold59_and_cardref_originals_20261024.py' and outer['ended_epoch']>=outer['started_epoch'])
ck('collector original request/result',rd(d/'result.json')==outer and rd(d/'request.json')['command']==outer['command'])
for stream in ['stdout','stderr','stdin']:
 ck('collector complete stream '+stream,h(d/(stream+'.bin'))==outer[stream+'_sha256'])
 if stream!='stdin':ck('collector stream bytes '+stream,(d/(stream+'.bin')).stat().st_size==outer[stream+'_bytes'])
extra=Path('/workspace/cold59-root-sequential-execution-20261024.json');ck('root sequential original external only',extra.exists() and str(extra) not in sources)
r={'schema':'independent-cold59-cardref-original-package-peer-v1','checks':count,'exit_code':int(bool(findings)),'findings':findings,'archive_sha256':p['archive_sha256'],'archive_members':7487,'original_members':7486,'original_bytes':20684123,'root_sequential_external_path':str(extra),'root_sequential_external_sha256':h(extra),'limits':['All packaged original small metadata and full streams were independently byte-compared; no large cold receipt body or controlled ELF body rehash.','All295 cold groups and2 separate cardref ELF groups retain write/reuse bans until every alias delinked.','Both original actual metadata peers had already been independently checked; this verifies their exact packaged bytes, not a product gate.','Collector producer c387 outer and root sequential execution JSON are external attachments, not members of this fixed tar.','Configured allocated savings286375936 plus79196160 are not concurrent global free-space deltas.']}
out=Path('/workspace/train337-canvas-peer-resume/COLD59_CARDREF_ACTUAL_PACKAGE_PEER.json');out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(out),'sha256':h(out),'checks':count,'findings':findings,'exit_code':r['exit_code']}));raise SystemExit(r['exit_code'])
