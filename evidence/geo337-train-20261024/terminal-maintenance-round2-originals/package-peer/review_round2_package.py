from pathlib import Path
import hashlib,json,tarfile
B=Path('/workspace/terminal-storage-maintenance-round2-originals-20261024');checks=[]
def ck(n,v):checks.append({'check':n,'ok':bool(v)})
def sha(b):return hashlib.sha256(b).hexdigest()
def h(p):return sha(Path(p).read_bytes())
def rd(p):return json.loads(Path(p).read_text())
package=rd(B/'PACKAGE.json');index=rd(B/'INDEX.json');archive=Path(package['archive']);members={r['member']:r for r in index['files']}
ck('frozen archive pin',h(archive)==package['archive_sha256']=='6b43f60093971b791838c969133984fef91e3fb025f01b0a87628ba44e9d16c6' and archive.stat().st_size==package['archive_bytes']==1250636)
ck('index pin',h(B/'INDEX.json')==package['index_sha256']=='4ea6a32f9eb28d854a7f3e832f51da64115e072b4c77f4f328e289a05243d444')
ck('exact3101 original members and payload',len(members)==len(index['files'])==3101 and sum(r['bytes'] for r in index['files'])==package['payload_bytes']==8127937)
with tarfile.open(archive,'r:gz') as tar:
 seen=set()
 for member in tar:
  ck('safe unique regular '+member.name,member.name not in seen and member.isfile() and not member.name.startswith('/') and '..' not in Path(member.name).parts);seen.add(member.name);body=tar.extractfile(member).read()
  if member.name=='INDEX.json':ck('embedded INDEX exact',body==(B/'INDEX.json').read_bytes());continue
  row=members[member.name];ck('tar member '+member.name,len(body)==row['bytes'] and sha(body)==row['sha256']);ck('original bytes '+member.name,body==Path(row['source']).read_bytes())
 ck('all3101 exactmembers',seen==set(members) and len(seen)==package['member_count']==3101)
ck('27maintenance only actions terminal',len(index['actions'])==27 and index['maintenanceOnly'] and not index['productGateExecutedOrRelabeled'] and all(x['original_exit']==x['outer_exit']==0 for x in index['actions']))
ck('new212 not mislabeled included',not any('cold-extra-' in x or 'cold-later-' in x for x in members) and any('twenty-four' in x for x in index['limits']))
frozen=list({x['source']:x for x in index['files'] if '/FROZEN_SIDECARS/' in x['source']}.values());ck('12 old sidecars frozen not native r2',len(frozen)==12 and sum(x['bytes'] for x in frozen)==276698)
ck('native oldlive sidecars not substituted',not any(x['source'].startswith('/tmp/geometry-tests/') and x['source'].endswith('.fingerprint.json') for x in index['files']))
ck('exactcollector original pin',h('/workspace/collect_terminal_storage_maintenance_round2_20261024.py')=='2363f745aed994eb90d656e3a607f0c2724b0d71fabcd0130279b5bf62805bee')
outer=rd('/workspace/terminal-storage-maintenance-round2-collection-launch-20261024/RESULT.json');ck('originalcollector outeractual0',outer['actual_process_returncode']==0 and not outer['timeout_expired'])
for stream in ('stdout','stderr'):
 p=Path(outer['directory'])/(stream+'.bin');ck('outerfull '+stream,p.stat().st_size==outer[stream+'_bytes'] and h(p)==outer[stream+'_sha256'])
f=[x for x in checks if not x['ok']];r={'schema':'independent-round2-terminal-maintenance-originals-package-peer/1','checks':len(checks),'findings':f,'exit_code':int(bool(f)),'archive_sha256':h(archive),'member_count':3101,'original_payload_bytes':8127937,'limits':['No maintenance action or product acceptance rerun; all packaged members roundtrip compared with original retained bytes.','12 native sidecars use explicit frozen original copies before r2 reuse; current regenerated cache bytes are not substituted.','This package closes original27 actions/24 archive alias groups only, not later212 groups.','Outer collector RESULT and raw c387 streams are outside archive and must be published alongside it.','Initial peer mistook collector schema as3100plus embeddedINDEX and counted two archive labels for each frozen sidecar as24 distinctfiles; retained initial report/helper, corrected only actual schema lookup; no source or collector rerun.']};out=Path('/workspace/train337-canvas-peer-resume/ROUND2_MAINTENANCE_PACKAGE_PEER.json');out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(out),'sha256':h(out),'checks':len(checks),'exit_code':r['exit_code'],'findings':f}));raise SystemExit(r['exit_code'])
