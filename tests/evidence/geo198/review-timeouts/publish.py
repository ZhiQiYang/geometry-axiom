import hashlib,json,pathlib,shutil
scratch=pathlib.Path('/tmp/geometry-198-timeouts')
out=pathlib.Path('/workspace/geometry-axiom/tests/evidence/geo198/review-timeouts')
out.mkdir(exist_ok=True)
for name in ('whole-node','isolated'):
    shutil.copytree(scratch/name,out/name,dirs_exist_ok=True)
for name in ('README.md','preload.cjs','run.py','summarize.py','publish.py','case-timings.json','source-controls.json','owner192.json'):
    shutil.copy2(scratch/name,out/name)
manifest={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file() and p.name!='sha256.json'}
(out/'sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'files':len(manifest),'bytes':sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),'sha256_manifest':hashlib.sha256((out/'sha256.json').read_bytes()).hexdigest()}))
