import os,sys,json,hashlib
from pathlib import Path
sys.path.insert(0,'/workspace/geo261-environment/final-f-contact-checker-proof-tools')
from capture import Recorder,dump
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
O=Path('/dev/shm/geometry-axiom-geo337-20261025');P=O/'publisher-source';out=O/'supplemental-publication-root-original-20261026';inner=O/'supplemental-publication-original-20261026';parent='f90db245f228b7a95a800cab176c3f9ca497133f';F='cbf0fb621888596aa14ad5f2349b503e23b1b72d';prefix='evidence/geo337-train-20261024/';assert not out.exists() and not inner.exists()
tool=Path('/tmp/geo337-recovery-evidence-append-preparation-20261026/publish_append.py');assert h(tool)=='988a3b851db4417d41c073d02e8d3e440ea7dd22c10c53421490da79174cb720'
peer=Path('/tmp/geo337-closed-first-publication-actual-peer-20261026/REVIEW.json');assert h(peer)=='79f5995387e6c5c4c41ac2be0750b3c0348639c3c474c0bab3554b27865edcc0';j=json.loads(peer.read_bytes());assert j['exit_code']==0 and not j['blocking_findings']
names=json.loads(Path('/tmp/geo337-supplemental-publication-roots-20261026.json').read_bytes());assert len(names)==len(set(names))==23
m={'schema':'final-candidate-complete-supplemental-evidence/1','source_sha':F,'previous_evidence_head':parent,'files':[]}
def add(p,dst):
 p=Path(p);assert p.is_file() and not p.is_symlink();m['files'].append({'source_path':str(p),'destination':prefix+dst,'bytes':p.stat().st_size,'sha256':h(p)})
for name in names:
 root=Path('/tmp')/name;assert root.parent==Path('/tmp') and root.is_dir() and not root.is_symlink()
 for p in sorted(root.rglob('*')):
  assert not p.is_symlink()
  if p.is_file():add(p,'resume-peers-and-sources-20261026/'+name+'/'+p.relative_to(root).as_posix())
for name in ['RESULT.json','REMOTE_BLOBS.json','MANIFEST.json','EXECUTOR.py']:
 add(O/'closed-first-publication-original-20261026'/name,'final-cbf0fb62-20261026/first-publication/'+name)
for name in ['RESULT.json','EXECUTOR.py']:
 add(O/'closed-first-publication-root-original-20261026'/name,'final-cbf0fb62-20261026/first-publication-outer/'+name)
for p in [Path('/tmp/geo337-final-light-EXEC_FINAL-20261026.json'),Path('/tmp/geo337-candidate-adoption-EXEC_FINAL-20261026.json'),Path('/tmp/geo337-closed-collection-EXEC_FINAL-20261026.json'),Path('/tmp/geo337-closed-first-publication-EXEC_FINAL-20261026.json')]:add(p,'final-cbf0fb62-20261026/host-final/'+p.name)
add('/tmp/geo337-current-PROGRESS-cbf0fb62-20261026.md','resume-20261026/PROGRESS.md')
assert len({x['destination']for x in m['files']})==len(m['files'])
out.mkdir();(out/'EXECUTOR.py').write_bytes(Path(__file__).read_bytes());(out/'FIRST_PUBLICATION_ACTUAL_PEER.json').write_bytes(peer.read_bytes());dump(out/'MANIFEST.json',m)
env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')};env.update(GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1');rec=Recorder(out,env,F)
row,b,e=rec.run(['git','rev-parse',parent+':'+prefix+'resume-20261026/PROGRESS.md'],cwd=P,timeout=60,check=True,source_variant='read exact current PROGRESS blob for evidence-only supplement');blob=b.decode().strip();assert len(blob)==40
row,b,e=rec.run(['python3','-B',str(tool),'--execute','--manifest',str(out/'MANIFEST.json'),'--sha256',h(out/'MANIFEST.json'),'--out',str(inner),'--expected-parent',parent,'--expected-progress-blob',blob],cwd='/workspace',timeout=600,check=False,source_variant='ordinary evidence-only append of complete peer sources, original API checks and capacity static audit')
dump(out/'RESULT.json',{'exit_code':row['actual_process_returncode'],'source_sha':F,'manifest_sha256':h(out/'MANIFEST.json')});print(json.dumps({'exit_code':row['actual_process_returncode'],'stdout':b.decode(),'stderr':e.decode()}));sys.exit(row['actual_process_returncode'])
