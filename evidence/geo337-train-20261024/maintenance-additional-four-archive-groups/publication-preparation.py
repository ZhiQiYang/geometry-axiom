"""Prepare a small root-publication allowlist; never write repository branches."""
from pathlib import Path
import hashlib,json,stat
BASE=Path('/workspace/four-additional-maintenance-publication-preparation-20261024')
P=Path('/workspace/four-additional-archive-groups-originals-20261024')
OUTER=Path('/workspace/four-additional-archive-groups-originals-collection-launch-20261024')
PEERS=Path('/workspace/train337-canvas-peer-resume')
PREFIX='evidence/geo337-train-20261024/maintenance-additional-four-archive-groups'
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
package=json.loads((P/'PACKAGE.json').read_text());assert package['exit_code']==0 and package['member_count']==1597 and package['archive_bytes']==359949
assert package['archive_sha256']=='e85764f616d5801a9fa13e23ea56cbfdaf32d8ccc203b1b0f48012c423bd31b6'
files=[]
def add(path,relative,role='metadata',known_hash=None):
 p=Path(path);s=p.lstat();assert stat.S_ISREG(s.st_mode) and p.resolve()==p
 assert role=='archive' or s.st_size<4*1024*1024
 digest=known_hash or h(p)
 files.append(dict(source_path=str(p),destination=PREFIX+'/'+relative,bytes=s.st_size,sha256=digest,gate='historical-storage-maintenance',role=role))
add(package['archive'],Path(package['archive']).name,'archive',package['archive_sha256'])
add(P/'PACKAGE.json','PACKAGE.json')
for q in sorted(OUTER.rglob('*')):
 if q.is_dir():continue
 add(q,'collector-outer/'+str(q.relative_to(OUTER)))
for name in ['FOUR_ADDITIONAL_COLLECTOR_STATIC_PEER.json','review_four_additional_collector.py','FOUR_ADDITIONAL_ARCHIVE_GROUPS_ACTUAL_PACKAGE_PEER.json','review_four_additional_archive_groups_package.py']:
 add(PEERS/name,'post-collection-peers/'+name)
add('/workspace/FOUR_ADDITIONAL_IMMUTABLE_ALIAS_REGISTRY_20261024.json','FOUR_ADDITIONAL_IMMUTABLE_ALIAS_REGISTRY_20261024.json')
add(BASE/'NEXT_EXCERPT.md','NEXT.md')
add(__file__,'publication-preparation.py')
# Independent registry peer is added only by an explicit finalized-file argument.
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--registry-peer',required=True);parser.add_argument('--registry-helper',required=True);a=parser.parse_args()
for q in [Path(a.registry_peer),Path(a.registry_helper)]:
 assert q.parent==PEERS
 add(q,'post-collection-peers/'+q.name)
assert len({x['source_path'] for x in files})==len(files) and len({x['destination'] for x in files})==len(files)
assert sum(x['role']=='archive' for x in files)==1
result=dict(schema='additional-four-maintenance-publication-allowlist/1',source_sha='ca7838e0f4950452b9befcf40899d606db9b81fa',historical_maintenance_source_sha='7af8c5d80d34cb4f49d01ba67deb78a3a6d725db',expected_head='76ba3b2dad42f5d68fdd3bbdd7e54f5b0c337c65',destination_prefix=PREFIX,files=files,total_files=len(files),archive_bytes=sum(x['bytes'] for x in files if x['role']=='archive'),metadata_bytes=sum(x['bytes'] for x in files if x['role']=='metadata'),notes=['No repository, branch, source or PROGRESS mutation performed by this preparer. Root owns the eventual batch publication.','Unique359949B archive is referenced in place; no duplicate tar or28 source archive bodies created. Large MEMBER_INVENTORY already inside tar, not duplicated loose.','Archive SHA is bound to original PACKAGE and independent6417/0 actual peer, not a second payload hash in this metadata preparer.','Keep original PACKAGE fields and initial failed-preparation history unchanged.','Registry/NEXT are adjacent post-package artifacts; no archive repack/self-reference.','source_sha identifies root current U context only; historical maintenance does not execute or relabel a U product gate.'])
(BASE/'MANIFEST.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(manifest=str(BASE/'MANIFEST.json'),sha256=h(BASE/'MANIFEST.json'),files=len(files),archive_bytes=result['archive_bytes'],metadata_bytes=result['metadata_bytes'])))
