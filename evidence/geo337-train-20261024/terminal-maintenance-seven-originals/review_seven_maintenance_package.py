from pathlib import Path
import json,hashlib,tarfile,stat,sys,datetime
B=Path('/workspace/storage-maintenance-originals-package-20261023'); O=Path('/tmp/train337-adversarial'); checks=0; findings=[]
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ck(ok,label):
 global checks
 checks+=1
 if not ok:findings.append(label)
p=json.loads((B/'PACKAGE.json').read_text());i=json.loads((B/'INDEX.json').read_text())
ck(h(B/'INDEX.json')=='3219237bad264ad406dfda7eb44bcce0b727a29c4737c92b33571d68785a5197'==p['index_sha256'],'index pin')
ck(h(B/'maintenance-originals.tar.gz')=='eba221475730fefff24833b058e4aa5adc365771e1a4b9875341dc08aba3c51a'==p['archive_sha256'],'archive pin')
ck(p['exit_code']==0 and p['member_count']==1677 and p['payload_bytes']==7711908 and p['archive_bytes']==1635347,'producer exact totals')
files={x['member']:x for x in i['files']};sources={x['source']:x for x in i['files']}
ck(len(files)==len(i['files'])==1677,'no duplicate member')
ck(sum(x['bytes'] for x in files.values())==7711908,'logical byte total')
with tarfile.open(B/'maintenance-originals.tar.gz','r:gz') as t:
 members=t.getmembers();ck(len(members)==len(files) and {x.name for x in members}==set(files),'exact archive members')
 for m in members:
  x=files[m.name]; path=Path(x['source']);r=t.extractfile(m).read();sr=path.read_bytes()
  ck(m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts,'safe regular '+m.name)
  ck(len(r)==x['bytes']==m.size and hashlib.sha256(r).hexdigest()==x['sha256'],'archive bytes '+m.name)
  ck(r==sr,'original bytes '+m.name)
  ck(m.mode==stat.S_IMODE(x['mode']) and m.uid==x['uid'] and m.gid==x['gid'],'archive metadata '+m.name)
  ck(path.name not in ('index','private.index') and path.suffix not in ('.exe','.pyc') and not path.name.endswith(('.tar.gz','.zip')) and len(r)<=4*1024*1024,'bounded original scope '+m.name)
ck(i['executionContextSHA']=='7af8c5d80d34cb4f49d01ba67deb78a3a6d725db' and i['maintenanceOnly'] and not i['productOrTestSourcesChanged'],'context non-product')
expected=['receipt-archive-three-dedup','release-receipt-archive-three-dedup','architecture-receipt-archive-three-dedup','exact-four-closed-publication-index','exact-eight-additional-index','L-ledger-exact-175-elf-retirement','terminal-raw-one-relocation']
ck([x['action'] for x in i['actions']]==expected,'seven exact actions')
allocation=0
for a in i['actions']:
 rpath=Path(a['result_source']);r=json.loads(rpath.read_text());outer=Path('/workspace')/(a['action']+'-launch-20261023')/'receipt.json';oo=json.loads(outer.read_text())
 ck(str(rpath) in sources and str(outer) in sources,'action and outer included '+a['action'])
 ck(h(rpath)==a['result_sha256'] and h(outer)==a['outer_sha256'],'action immutable pins '+a['action'])
 ck(r['exit_code']==a['actual_exit']==a['outer_exit']==oo['actual_process_returncode']==0 and bool(r['ended_utc']) and oo['ended_epoch'] and not oo['timeout_expired'],'terminal actual '+a['action'])
 ck(a['free_before']==r['free_before'] and a['free_after']==r['free_after'],'original free observations '+a['action'])
 for root in (rpath.parent,outer.parent):
  expected_paths={str(q) for q in root.rglob('*') if q.is_file() and q.suffix!='.pyc' and '__pycache__' not in q.parts}
  ck(expected_paths <= set(sources),'complete bounded original action tree '+str(root))
 allocation+=r.get('expected_allocated_saving',0)+r.get('removed_allocated_bytes',0)+sum(r.get('removed_allocated_by_fs',{}).values())+r.get('retired_allocated_file_bytes',0)
ck(allocation==i['allocatedReductionFromDedupAndRebuildableCaches']==439607296,'allocated total independent sum')
last=json.loads(Path(i['actions'][-1]['result_source']).read_text());ck(last['retired_original_allocated_file_bytes']==i['rawRelocationAllocatedFileBytes']==82776064 and last['no_receipt_content_removed'],'raw transfer separate')
ck(i['checkoutWriteBan']==['/workspace/geo261-cold/g261seal/'+x for x in ('p-source','a-source','l-source')] and 'until all three archive groups are de-linked' in i['lease'],'cold write ban preserved')
ck(len([x for x in files if x.startswith('references/elf-sidecars/')])==175,'175 sidecar bodies retained')
ck(any('not a claim' in x for x in i['limits']) and any('unknown' in x for x in i['limits']) and any('changed device/inode' in x for x in i['limits']),'limits retained')
launch=Path('/workspace/storage-maintenance-package-launch-20261023'); req=json.loads((launch/'REQUEST.json').read_text());res=json.loads((launch/'RESULT.json').read_text());commands=json.loads((launch/'subcommands.json').read_text())
ck(req['tool_sha256']==h(req['tool'])=='9bf419eaa404f2cc0b9c54c92c02ef11f909c9ebdf99e37707367a74d6edb999','collector tool pin')
ck(len(commands)==1 and res['command_result']==commands[0] and res['exit_code']==0,'collector terminal')
c=commands[0];d=Path(c['directory']);ck(c['actual_process_returncode']==0 and not c['timeout_expired'] and c['ended_epoch']>c['started_epoch'],'collector command exit')
for n in ('stdout','stderr'):
 raw=(d/(n+'.bin')).read_bytes();ck(len(raw)==c[n+'_bytes'] and hashlib.sha256(raw).hexdigest()==c[n+'_sha256'],'collector complete '+n)
ck(json.loads((d/'stdout.bin').read_text())==p,'collector printed exact package')
report={'schema':'independent-seven-maintenance-original-package-peer/1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'exit_code':int(bool(findings)),'findings':findings,'member_count':1677,'payload_bytes':7711908,'archive_sha256':p['archive_sha256'],'index_sha256':p['index_sha256'],'scope':'Streamed every archive member and compared original bytes; seven action trees and terminal receipts, sidecars, scope arithmetic, collector raw checked. No extraction, cleanup or subject test.','publication_companions_required':[str(B/'INDEX.json'),str(B/'PACKAGE.json'),str(launch)],'limits':['Metadata maintenance is not product validation. No executable/archive/relocated-body payload in this package.','Configured allocations differ from concurrent observed free bytes; raw move is cross-filesystem transfer.','Nine original archive paths/bytes retained with aliases; three cold checkouts remain barred until de-link.','Independent action acceptance is in included prior peers; package review does not rerun any action.']}
q=O/'SEVEN_MAINTENANCE_ORIGINAL_PACKAGE_PEER.json';q.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'checks':checks,'exit_code':report['exit_code'],'findings':findings,'report':str(q),'sha256':h(q)},ensure_ascii=False));sys.exit(report['exit_code'])
