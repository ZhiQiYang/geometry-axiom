from pathlib import Path,PurePosixPath
import json,hashlib,stat,datetime
O=Path(__file__).parent
P='evidence/geo337-train-20261024/F9-canvas-terminal/'
rows=[]
def H(p):
 d=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):d.update(b)
 return d.hexdigest()
def add(p,dest):
 p=Path(p);a=p.lstat()
 assert stat.S_ISREG(a.st_mode),(p,'not regular')
 assert not p.is_symlink()
 digest=H(p);b=p.lstat()
 assert (a.st_dev,a.st_ino,a.st_mode,a.st_size,a.st_mtime_ns,a.st_nlink)==(b.st_dev,b.st_ino,b.st_mode,b.st_size,b.st_mtime_ns,b.st_nlink)
 assert not PurePosixPath(dest).is_absolute() and '..' not in PurePosixPath(dest).parts
 assert not any(x['source_path']==str(p) or x['destination']==dest for x in rows)
 rows.append(dict(source_path=str(p),destination=dest,bytes=a.st_size,sha256=digest))
def tree(path,label):
 root=Path(path)
 for p in sorted(root.rglob('*')):
  if p.is_file() or p.is_symlink():add(p,P+label+'/'+p.relative_to(root).as_posix())
roots=[
('/tmp/geo337-F9-canvas-terminal-package-20261025','package'),
('/workspace/geo337-F9-canvas-terminal-preparation-20261025','inventory-preparation'),
('/workspace/geo337-F9-canvas-terminal-inventory-launch-20261025','inventory-original-capture'),
('/workspace/geo337-F9-canvas-terminal-output-device-delta-20261025','collector-v2-delta'),
('/workspace/geo337-F9-canvas-terminal-collector-static-peer-20261025','collector-v1-static-peer'),
('/workspace/geo337-F9-canvas-terminal-collector-v2-static-peer-20261025','collector-v2-static-peer'),
('/workspace/geo337-F9-canvas-terminal-root-collection-20261025','collection-original-capture'),
('/workspace/geo337-F9-canvas-terminal-package-actual-peer-20261025','package-actual-peer'),
('/workspace/geo337-F9-canvas-actual-peer-20261025','canvas-original-actual-peer'),
('/workspace/geo337-Ec32-current-CI-read-20261025','parent-Ec32-CI-original-read')]
for x,y in roots:tree(x,y)
for p in [
'/workspace/prepare_geo337_F9_canvas_terminal_inventory_20261025.py',
'/workspace/launch_geo337_F9_canvas_terminal_inventory_20261025.py',
'/workspace/collect_geo337_F9_canvas_terminal_parts_20261025.py',
'/workspace/collect_geo337_F9_canvas_terminal_parts_v2_20261025.py',
'/workspace/launch_geo337_canvas_terminal_collection_root_20261025.py']:
 add(p,P+'tools/'+Path(p).name)
for p in [
'/workspace/geo337-F9-canvas-EXEC_FINAL-20261025.json',
'/workspace/geo337-F9-canvas-root-request-20261025.json',
'/workspace/geo337-F9-canvas-terminal-inventory-EXEC_FINAL-20261025.json',
'/workspace/geo337-F9-canvas-terminal-collection-root-request-20261025.json',
'/workspace/geo337-F9-canvas-terminal-collection-EXEC_FINAL-20261025.json']:
 add(p,P+'terminal-and-requests/'+Path(p).name)
for name in ['README.md','PR_BODY.template.md','NEXT.delta.md','ORIGIN_BINDINGS.json','PREPARATION.json','prepare.py','build_publication_manifest.py']:
 add(O/name,P+'publication-preparation/'+name)
add(O/'PROGRESS.md','evidence/geo337-train-20261024/PROGRESS.md')
files={'files':rows}
(O/'FILES.json').write_text(json.dumps(files,ensure_ascii=False,indent=2)+'\n')
summary={'schema':'geo337-F9-canvas-publication-scope/1','source_sha':'4f8a794f4167c3562eb182045102e86e9e37cca9','parent_evidence_head':'c32e70aa2c848f89a0e2e9fd92ed232a4dd27bcc','expected_prbody_parent':'1c601b40a6f5e0e1d50461186736d469666db4b9','files':len(rows),'bytes':sum(x['bytes'] for x in rows),'manifest_sha256':H(O/'FILES.json'),'body_sha256':H(O/'PR_BODY.template.md'),'progress_sha256':H(O/'PROGRESS.md'),'next_delta_sha256':H(O/'NEXT.delta.md'),'payload_copy_performed':False,'publication_performed':False,'comparison_originals_included':False,'private_account_profile_included':False,'git_objects_included':False,'live_sources_read':False,'immutable_source_hash_validation':'每個selected原件只讀SHA256，前後lstat dev/inode/mode/size/mtime_ns/nlink同；不重收tar或產品。','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(O/'PUBLICATION_SCOPE.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
pins={p.name:H(p) for p in [O/'FILES.json',O/'PR_BODY.template.md',O/'PROGRESS.md',O/'NEXT.delta.md',O/'README.md',O/'PREPARATION.json',O/'PUBLICATION_SCOPE.json',O/'build_publication_manifest.py']}
(O/'PINS.json').write_text(json.dumps(pins,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False))
