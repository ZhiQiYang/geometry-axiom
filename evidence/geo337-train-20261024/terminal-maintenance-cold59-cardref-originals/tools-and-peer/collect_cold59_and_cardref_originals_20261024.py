"""Collect exact completed maintenance originals; never archive receipt payloads or ELF bodies."""
from pathlib import Path
import datetime,hashlib,io,json,stat,tarfile
OUT=Path('/workspace/cold59-and-cardref-links-originals-20261024')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def readj(p):return json.loads(Path(p).read_text())
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
def main():
 OUT.mkdir();entries={}
 def add(p,n):
  p=Path(p);s=p.lstat()
  assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and not p.is_symlink()
  assert s.st_size<4*1024*1024 and not p.name.endswith(('.tar.gz','.zip','.exe','.pyc'))
  assert n not in entries
  entries[n]=dict(source=str(p),bytes=s.st_size,sha256=digest(p),mode=s.st_mode,mtime_ns=s.st_mtime_ns,uid=s.st_uid,gid=s.st_gid)
 def tree(p,n):
  p=Path(p);assert p.is_dir() and not p.is_symlink()
  for q in sorted(p.rglob('*')):
   assert not q.is_symlink()
   if q.is_dir() or '__pycache__' in q.parts:continue
   add(q,n+'/'+str(q.relative_to(p)))
 manifests=[('/workspace/cold_text_59_exact_body_manifest_20261024.json','482ad13ed12a4029dc4e79c6ab084ad034521abba16d073d74818178fb82f602')]
 items=[]
 for path,pin in manifests:
  assert digest(path)==pin
  m=readj(path);items.extend(m['items']);add(path,'manifest/'+Path(path).name)
 assert len(items)==59 and sum(i['expected_allocated_saving'] for i in items)==286375936
 for i in items:
  name=i['name'];plan=Path(i['plan']);out=Path('/workspace')/(name+'-receipt-archive-three-dedup-execution-20261023');outer=Path('/workspace')/(name+'-receipt-archive-three-dedup-launch-20261024')
  assert digest(plan)==i['plan_sha256'] and digest(i['tool'])==i['tool_sha256']
  r=readj(out/'RESULT.json');a=readj(outer/'RESULT.json')
  assert r['exit_code']==0 and r['all_three_paths_and_bytes_preserved'] and a['actual_process_returncode']==0
  tree(plan.parent,'preparation/'+name);tree(out,'actual/'+name);tree(outer,'launch/'+name);add(i['tool'],'tools/'+name+'-executor.py')
 tree('/workspace/cold-nonarchive-three-copy-metadata-20261024','preparation-source/cold59')
 tree('/workspace/cold-text-59-body-preparation-launch-20261024','preparation-launch/cold59')
 for path in ['/workspace/prepare_cold59_receipt_metadata_20261024.py','/workspace/scan_cold_nonarchive_metadata_20261024.py','/tmp/prepare_next_cold_archive_batch.py','/workspace/summarize_prepared_cold_archive_batch_20261024.py']:
  add(path,'preparation-source/'+Path(path).name)
 for path in ['/workspace/evidence-archive-dedup-readonly-20261023/deduplicate_release_exact_three_receipts.py','/workspace/evidence-archive-dedup-readonly-20261023/archive_link_core.py','/workspace/clear_terminal_chrome_caches.py','/workspace/run_approved_maintenance.py','/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py']:
  add(path,'original-tools/'+Path(path).name)
 base=Path('/workspace/cardref-preserving-elf-links-preparation-20261024')
 p=readj(base/'PLAN.json');assert digest(base/'PLAN.json')=='d8c7d397aa041080c3b98fadb242069abd12b301d19475fb1c2aa3b4cb08ea58'
 assert p['target_count']==63 and p['original_elf_count']==116 and p['excluded_unique_elf_count']==53
 tree(base,'cardref/preparation')
 for stem in ['execution','launch']:
  source=Path('/workspace')/('cardref-exact-two-elf-groups-preserving-dedup-'+stem+'-20261024');tree(source,'cardref/'+stem)
 for key in ['original_inventory','original_excluded_inventory','terminal_receipt']:
  x=p[key];assert digest(x['path'])==x['sha256'];add(x['path'],'cardref/preserved-original-inventory/'+key+'-'+Path(x['path']).name)
 for path in ['/workspace/cardref-original-116-elf-duplicate-metadata-20261024.json','/workspace/prepare_cardref_preserving_elf_links_20261024.py']:
  add(path,'cardref/preparation-source/'+Path(path).name)
 peers=['COLD_59_EXACT_THREE_EXECUTOR_STATIC_PEER.json','COLD59_IMMUTABLE_SCOPE_PEER.json','review_cold59_immutable_scope.py','review_cold_exact_preparation.py','COLD59_SCOPE_INITIAL_SCHEMA_ERROR.json','review_cold59_immutable_scope.v1.py.txt','COLD59_ACTUAL_SUMMARY_HELPER_PEER.json','review_cold59_actual_summary.py','CARDREF_PRESERVING_LINKS_STATIC_PEER.json','review_cardref_preserving_links.py','CARDREF_PRESERVING_LINKS_ACTUAL_CROSS_PEER.json','review_cardref_actual_crosscheck.py']
 for name in peers:
  add(Path('/workspace/train337-canvas-peer-resume')/name,'peers-and-review-tools/'+name)
 for path in ['/workspace/COLD_59_EXACT_THREE_ACTUAL_METADATA_REVIEW_20261024.json','/workspace/review_cold59_actual_metadata_20261024.py','/workspace/CARDREF_PRESERVING_LINKS_ACTUAL_METADATA_PEER_20261024.json','/workspace/review_cardref_preserving_links_actual_20261024.py']:
  add(path,'peers-and-review-tools/'+Path(path).name)
 add(__file__,'collector.py')
 add('/workspace/prepare_cold59_cardref_collection_20261024.py','collector-preparation.py')
 add('/workspace/collect_cold212_and_sevenfinal15_originals_20261024.py','original-collector.py')
 for path in ['/workspace/COLD_59_EXACT_THREE_ACTUAL_METADATA_REVIEW_20261024.json','/workspace/CARDREF_PRESERVING_LINKS_ACTUAL_METADATA_PEER_20261024.json','/workspace/train337-canvas-peer-resume/COLD59_ACTUAL_SUMMARY_HELPER_PEER.json','/workspace/train337-canvas-peer-resume/CARDREF_PRESERVING_LINKS_ACTUAL_CROSS_PEER.json']:
  r=readj(path);assert r['exit_code']==0 and not r['findings']
 total=sum(x['bytes'] for x in entries.values());assert total<64*1024*1024
 inventory=dict(schema='preserved-maintenance-original-member-inventory/1',members=[dict(member=n,**x) for n,x in sorted(entries.items())])
 inv=OUT/'MEMBER_INVENTORY.json';dump(inv,inventory)
 archive=OUT/'cold59-and-cardref-links-originals.tar.gz'
 with tarfile.open(archive,'w:gz',compresslevel=1) as tar:
  for n,x in sorted(entries.items()):
   data=Path(x['source']).read_bytes();assert len(data)==x['bytes'] and hashlib.sha256(data).hexdigest()==x['sha256']
   info=tarfile.TarInfo(n);info.size=len(data);info.mode=stat.S_IMODE(x['mode']);info.mtime=x['mtime_ns']/1e9;info.uid=x['uid'];info.gid=x['gid'];tar.addfile(info,io.BytesIO(data))
  data=inv.read_bytes();info=tarfile.TarInfo('MEMBER_INVENTORY.json');info.size=len(data);tar.addfile(info,io.BytesIO(data))
 with tarfile.open(archive,'r:gz') as tar:
  assert set(tar.getnames())==set(entries)|{'MEMBER_INVENTORY.json'}
  for n,x in entries.items():assert hashlib.sha256(tar.extractfile(n).read()).hexdigest()==x['sha256']
  assert tar.extractfile('MEMBER_INVENTORY.json').read()==inv.read_bytes()
 assert all(digest(x['source'])==x['sha256'] for x in entries.values())
 result=dict(schema='cold59-cardref-preserving-links-originals/1',createdUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit_code=0,member_count=len(entries)+1,original_member_count=len(entries),original_bytes=total,archive=str(archive),archive_bytes=archive.stat().st_size,archive_sha256=digest(archive),inventory=str(inv),inventory_sha256=digest(inv),roundtrip_original_bytes=True,cold_receipt_alias_groups_added=59,all_established_cold_alias_groups=295,cold_preserving_dedup_allocated_saving=286375936,cardref_elf_alias_groups_added=2,cardref_preserving_dedup_allocated_saving=79196160,limits=['Maintenance only; no product gate is executed or relabeled.','All177 cold receipt paths/bytes and all116 controlled cardref ELF paths/bytes remain. No actual receipt body or ELF executable bytes duplicated into this package.','All295 existing cold alias groups including236 older groups must be delinked before any writes/reuse of any of the three cold checkouts.','The two controlled cardref ELF alias groups are separate from the295 cold groups; all their aliases must be delinked before write/reuse.','Actual metadata reviews recheck metadata and original small command streams, not large payload bytes; original executors performed complete physical body comparisons.','Cardref original931 nonELF evidence artifacts remain preserved and are covered by the original published section7 inventory/package; this maintenance package references their exact inventory and does not duplicate them.','Original inode identities and per-path mtime are not preserved by hardlink sharing. All original per-path metadata stays in PLAN.','Physical allocated savings do not equal concurrent global free-space changes.','Independent reviewer reports created after this package remain adjacent attachments, not claimed present in this fixed archive.'])
 dump(OUT/'PACKAGE.json',result);print(json.dumps(result))
if __name__=='__main__':main()
