import hashlib,json,pathlib,tarfile
base=pathlib.Path('/workspace/geo314-work');out=pathlib.Path('/tmp/g261-next314/evidence/geo314-repairs-4f669733');out.mkdir(parents=True,exist_ok=True)
groups={'candidate-repair.tar.gz':['candidate-repair-001','candidate-repair-002','candidate_repair_driver.py'],'reader-repair.tar.gz':['reader-repair-001','reader-validation-001','run_reader_repair.py'],'environment-node-repair.tar.gz':['environment-repair-001'],'manifest-registration.tar.gz':['manifest-repair-001']}
rows=[]
for name,paths in groups.items():
 with tarfile.open(out/name,'w:gz',compresslevel=1) as archive:
  for rel in paths:
   p=base/rel
   assert p.exists();archive.add(p,arcname=rel,recursive=True)
 p=out/name;rows.append({'path':name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(out/'PUBLICATION.json').write_text(json.dumps({'schema':'geo314-repair-publication/1','classification':'affected diagnostics and environment retry; not formal final-SHA acceptance','product_sha':'4f669733282613a6f1e4a627c448374716496daa','checkout_sha':'c0a2007898f544e658efa72b9b51528a03f7ce51','environment_retry_product_sha':'291ce90abf9c3bfaf68bd61c4969f2ff9a1be6f6','files':rows},ensure_ascii=False,indent=2)+'\n');print(rows)
