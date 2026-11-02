from pathlib import Path
import hashlib,json,tarfile
B=Path('/workspace/cold212-and-sevenfinal15-originals-20261024');count=0;findings=[]
def ck(n,v):
 global count
 count+=1
 if not v:findings.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
def h(p):return sha(Path(p).read_bytes())
def rd(p):return json.loads(Path(p).read_text())
p=rd(B/'PACKAGE.json');i=rd(B/'MEMBER_INVENTORY.json');members={x['member']:x for x in i['members']};archive=Path(p['archive'])
ck('fixed archive pin',h(archive)==p['archive_sha256']=='0e96fa4a6b07fa9b9d54cfc0821c7b92a40f1ddb0b03c07f4d918d6361f75cc4' and archive.stat().st_size==p['archive_bytes']==4353391)
ck('fixed inventory pin',h(B/'MEMBER_INVENTORY.json')==p['inventory_sha256']=='dd90dc1b126ed1317fedd7b408b28ad890305fe96a7868694609f1ecde87dd90')
ck('unique26375 originalmembers/bytes',len(members)==len(i['members'])==p['original_member_count']==26375 and sum(x['bytes'] for x in i['members'])==p['original_bytes']==24230100)
with tarfile.open(archive,'r:gz') as tar:
 seen=set()
 for m in tar:
  ck('safe unique regular '+m.name,m.name not in seen and m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts);seen.add(m.name);raw=tar.extractfile(m).read()
  if m.name=='MEMBER_INVENTORY.json':ck('embeddedinventory exact',raw==(B/'MEMBER_INVENTORY.json').read_bytes());continue
  x=members[m.name];ck('archived exact '+m.name,len(raw)==x['bytes'] and sha(raw)==x['sha256']);ck('original exact '+m.name,raw==Path(x['source']).read_bytes())
  ck('no ELF payload '+m.name,not raw.startswith(b'\x7fELF'))
 ck('26376 exactcomplete',seen==set(members)|{'MEMBER_INVENTORY.json'} and len(seen)==p['member_count']==26376)
ck('correct212new/236total',p['archive_alias_groups_added']==212 and p['all_established_cold_alias_groups']==236 and p['preserving_dedup_allocated_saving']==401981440)
ck('retired15scope allocated',p['ordinary_elf_cache_retired_allocated_bytes']==14745600)
fifteen=rd('/workspace/terminal-sevenfinal-five-browser-15-elf-preparation-20261024/PLAN.json')
retired=rd('/workspace/terminal-sevenfinal-exact-15-runtime-elf-retirement-execution-20261024/RESULT.json')
ck('15 actual exact original0',retired['exit_code']==0 and set(retired['removed'])=={x['path'] for x in fifteen['targets']} and all(not Path(x['path']).exists() for x in fifteen['targets']))
for x in fifteen['terminal_receipts']+fifteen['sidecars']+[fifteen['root_historical_receipt']]:ck('retained15 sidecar/receipt '+x['path'],Path(x['path']).stat().st_size==x['bytes'] and h(x['path'])==x['sha256'])
ck('15 existing actualpeer67/0',h('/workspace/SEVENFINAL_15_ELF_ACTUAL_METADATA_PEER_20261024.json')=='30982488de96b819e75100a7f6e06003cc0483d10ffa717a33d0e486b3424989' and rd('/workspace/SEVENFINAL_15_ELF_ACTUAL_METADATA_PEER_20261024.json')['exit_code']==0)
outer=rd('/workspace/cold212-and-sevenfinal15-collection-launch-20261024/RESULT.json');ck('outercollector true0',outer['actual_process_returncode']==0 and not outer['timeout_expired'])
for stream in ('stdout','stderr'):
 q=Path(outer['directory'])/(stream+'.bin');ck('outercomplete '+stream,q.stat().st_size==outer[stream+'_bytes'] and h(q)==outer[stream+'_sha256'])
r={'schema':'independent-cold212-sevenfinal15-package-peer/1','checks':count,'findings':findings,'exit_code':int(bool(findings)),'archive_sha256':h(archive),'member_count':26376,'original_bytes':24230100,'scope':'All original package members independently compared against source bytes; new212 metadata actual review already separately accepted; exact15 retirement outcome and all21preserved sidecars/receipts rechecked.','limits':['No original large archive payload or ELF body rehash or subject rerun. All packaged command/receipt/tool bodies, including full preserved small streams, were checked.','Allocated401981440B dedup and14745600B executable cache retirement are not concurrent free-space deltas.','236 cold archive alias groups stay write/reuse barred until each is independently de-linked.','Package collector outer RESULT/subcommands/full streams are outside this archive and must accompany publication.']};out=Path('/workspace/train337-canvas-peer-resume/COLD212_SEVENFINAL15_PACKAGE_PEER.json');out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(out),'sha256':h(out),'checks':count,'exit_code':r['exit_code'],'findings':findings}));raise SystemExit(r['exit_code'])
