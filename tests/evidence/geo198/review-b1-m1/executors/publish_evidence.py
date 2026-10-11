import hashlib,json,pathlib,shutil,subprocess
root=pathlib.Path('/workspace/geometry-axiom');scratch=pathlib.Path('/tmp/geometry-198-review2');out=root/'tests/evidence/geo198/review-b1-m1'
out.mkdir(parents=True,exist_ok=True)
for name in ('before','after','final','remove-fix','remove-fix-clean','scenes-clean','all-build','mutations','mutations-final','browser','space','reader-diagnostic','comparison-final','comparison-run','aggregate','node-isolated','node-isolated-fresh','node-repeat'):
    source=scratch/name
    for p in source.rglob('*'):
        if not p.is_file() or any(x in ('profile','downloads','feedback') for x in p.relative_to(source).parts):continue
        if name=='node-repeat' and p.relative_to(source).parts[0]=='logs' and p.name!='node_tests-js.log':continue
        target=out/name/p.relative_to(source);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
for name in ('base.json','previous.json','fixed.json','metadata.json','previous-build.log','previous-build-attempt1.log'):
    target=out/'comparison'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(scratch/'comparison'/name,target)
for name in ('capture.py','compare.py','probe.py','run_checks.py','check_scenes.py','prepare_browser.py','browser.cjs','stop_server.py','edit_core.py','publish_evidence.py','verify_mutations.py','reader-diagnostic.py','prepare_reader.py','node-isolated-fresh.py','finalize_docs.py'):
    target=out/'executors'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(scratch/name,target)
for name in ('after-build.log','after-integrity-build.log','remove-fix.log','original-scenes.log','server.log','server-final-dump.json','runtime-before.json','runtime-after.json'):
    shutil.copy2(scratch/name,out/name)
for p in (scratch/'original-scenes').rglob('*'):
    if p.is_file():
        target=out/'stack-8m-attempt'/p.relative_to(scratch/'original-scenes');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
for p in pathlib.Path('/tmp/geometry-tests').glob('*.fingerprint.json'):
    target=out/'aggregate'/p.name;shutil.copy2(p,target)
baseline=json.loads((out/'aggregate'/'checkout-before.json').read_text());after=json.loads((out/'aggregate'/'checkout-after.json').read_text())
summary={'product_commit':'f32f57449c8cb6df983aba035115159be91677f8','mutation_definition_commit':'865f543028c2b657ef09f98e358b4a6d36a13211','aggregate_head':baseline['head'],'aggregate_tracked_diff_before':baseline['tracked_diff'],'aggregate_tracked_diff_after':after['tracked_diff'],'binary_bytes_equal_before_after':baseline['binaries'].keys()==after['binaries'].keys() and all(b['sha256']==after['binaries'][p]['sha256'] for p,b in baseline['binaries'].items()),'scope':'Linux evidence, not WSL or enforced exclusive isolation; final integrated head seven jobs remain pending owner #192 canonical sync','service_pid':json.loads((out/'runtime-before.json').read_text())['pid'],'own_service_stopped':True,'service_broken_pipe_count':(out/'server.log').read_text().count('BrokenPipeError')}
(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
manifest={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file() and p.name!='sha256.json'}
(out/'sha256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'files':len(manifest),'bytes':sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),'summary':summary},ensure_ascii=False))
