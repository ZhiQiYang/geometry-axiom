import os,sys,json,hashlib,argparse
from pathlib import Path
sys.path.insert(0,'/workspace/geo261-environment/final-f-contact-checker-proof-tools')
from capture import Recorder,dump
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
ap=argparse.ArgumentParser();ap.add_argument('--collection-peer',required=True);ap.add_argument('--collection-peer-sha256',required=True);a=ap.parse_args()
O=Path('/dev/shm/geometry-axiom-geo337-20261025');P=O/'publisher-source';out=O/'closed-first-publication-root-original-20261026';inner=O/'closed-first-publication-original-20261026';F='cbf0fb621888596aa14ad5f2349b503e23b1b72d';prefix='evidence/geo337-train-20261024/';assert not out.exists() and not inner.exists()
tool=Path('/tmp/geo337-recovery-evidence-append-preparation-20261026/publish_append.py');assert h(tool)=='988a3b851db4417d41c073d02e8d3e440ea7dd22c10c53421490da79174cb720'
static=Path('/tmp/geo337-recovery-evidence-append-peer-20261026/REVIEW.json');assert h(static)=='125a0dee72a2d3d09fdd6af901aefdfe7693dbf1d43cbe0141c280d008da3917'
cp=Path(a.collection_peer);assert h(cp)==a.collection_peer_sha256;v=json.loads(cp.read_bytes());assert v['exit_code']==0 and not v['blocking_findings']
package=O/'resume-closed-original-package-20261026';j=json.loads((package/'RESULT.json').read_bytes());assert j['exit_code']==0 and j['archive_sha256']=='ac08de092c1ceefd01e01cec3091c69183aa834d31ac197c05b0b535f4694ce6' and j['index_sha256']=='4fde9f8413bb9dfae8866e332391cb52ddcc41c116dc0d5ccf3eb8a04558375f'
m=json.loads((package/'PUBLICATION_MANIFEST.json').read_bytes());m.update(schema='final-candidate-closed-originals-first-publication/1',source_sha=F)
def add(src,dst):
 p=Path(src);assert p.is_file() and not p.is_symlink();m['files'].append({'source_path':str(p),'destination':prefix+dst,'bytes':p.stat().st_size,'sha256':h(p)})
for p in sorted((O/'closed-collection-root-original-20261026').rglob('*')):
 if p.is_file():add(p,'resume-closed-originals-20261026/collection-outer/'+p.relative_to(O/'closed-collection-root-original-20261026').as_posix())
for src,dst in [('/tmp/geo337-current-PROGRESS-cbf0fb62-20261026.md','resume-20261026/PROGRESS.md'),('/tmp/geo337-final-candidate-NEXT-20261026.md','final-cbf0fb62-20261026/NEXT.md'),('/tmp/geo337-current-QUESTIONS-cbf0fb62-20261026.md','final-cbf0fb62-20261026/QUESTIONS.md'),('/tmp/geo337-retirement-approval-packet-20261026/REPORT.md','final-cbf0fb62-20261026/approval-packet/REPORT.md'),('/tmp/geo337-retirement-approval-packet-20261026/SCOPE.json','final-cbf0fb62-20261026/approval-packet/SCOPE.json'),('/tmp/geo337-native-retirement-approval-rejection-20261026.json','final-cbf0fb62-20261026/approval-packet/REJECTION.json'),(O/'F-final-light-gates-original-20261026/RESULT.json','final-cbf0fb62-20261026/four-gates/RESULT.json'),('/tmp/geo337-final-light-gates-actual-peer-20261026/REVIEW.json','final-cbf0fb62-20261026/four-gates/ACTUAL_PEER.json'),('/tmp/geo337-candidate-three-leaf-actual-peer-20261026/REVIEW.json','final-cbf0fb62-20261026/adoption/ACTUAL_PEER.json'),(cp,'resume-closed-originals-20261026/COLLECTION_ACTUAL_PEER.json')]:add(src,dst)
assert len({x['destination']for x in m['files']})==len(m['files'])
out.mkdir();(out/'EXECUTOR.py').write_bytes(Path(__file__).read_bytes());(out/'STATIC_PEER.json').write_bytes(static.read_bytes());dump(out/'MANIFEST.json',m)
env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')};env.update(GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1');rec=Recorder(out,env,F)
row,b,e=rec.run(['git','rev-parse',F+':'+prefix+'resume-20261026/PROGRESS.md'],cwd=P,timeout=60,check=True,source_variant='read exact historical PROGRESS blob before evidence-only append');blob=b.decode().strip();assert len(blob)==40
row,b,e=rec.run(['python3','-B',str(tool),'--execute','--manifest',str(out/'MANIFEST.json'),'--sha256',h(out/'MANIFEST.json'),'--out',str(inner),'--expected-parent',F,'--expected-progress-blob',blob],cwd='/workspace',timeout=600,check=False,source_variant='evidence-only ordinary CAS push of complete closed original package and current state')
dump(out/'RESULT.json',{'exit_code':row['actual_process_returncode'],'source_sha':F,'manifest_sha256':h(out/'MANIFEST.json')});print(json.dumps({'exit_code':row['actual_process_returncode'],'stdout':b.decode(),'stderr':e.decode()}));sys.exit(row['actual_process_returncode'])
