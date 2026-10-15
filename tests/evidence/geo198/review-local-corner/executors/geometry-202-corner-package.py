import hashlib,json,pathlib,shutil,subprocess
root=pathlib.Path.cwd(); scratch=pathlib.Path('/tmp/geometry-202-corner')
out=root/'tests/evidence/geo198/review-local-corner'
assert (scratch/'aggregate/run.json').exists(), 'Wait for the original aggregate to finish'
before=json.loads((scratch/'aggregate/checkout-before.json').read_text())
after=json.loads((scratch/'aggregate/checkout-after.json').read_text())
assert before['head']==after['head']=='1b5919787df1124c0eb6122a886d4403ada21fd2'
assert before['status']==[]
assert after['tracked_diff']==['tests/run_all.expected.json'],after['tracked_diff']
assert before['sources']==after['sources']
assert before['binaries']==after['binaries']
assert before['judge_sources']==after['judge_sources']
assert len(before['binaries'])==5
assert not out.exists()
out.mkdir(parents=True)
for folder in ('before','after','mutations','aggregate'):
    shutil.copytree(scratch/folder,out/folder)
for folder in ('comparison','world-cmp'):
    (out/folder).mkdir()
    for p in (scratch/folder).iterdir():
        if p.suffix in ('.json','.log','.txt') or p.name=='harness.c':shutil.copyfile(p,out/folder/p.name)
shutil.copytree(scratch/'reader-diagnostic/artifacts',out/'reader-diagnostic')
shutil.copyfile(scratch/'reader-diagnostic.log',out/'reader-diagnostic/stdout.log')
shutil.copyfile(scratch/'scene-comparison.json',out/'scene-comparison.json')
(out/'executors').mkdir()
for p in pathlib.Path('/tmp').glob('geometry-202-corner-*.py'):
    shutil.copyfile(p,out/'executors'/p.name)
shutil.copyfile('/tmp/geometry-202-corner-world.c',out/'executors/world.c')
original=root/'tests/evidence/geo198/review-three-residual/executors/reader-diagnostic-original.py'
shutil.copyfile(original,out/'executors/reader-diagnostic-original.py')
shutil.copyfile(root/'tests/geo246/identity.py',out/'executors/identity.py')
closure={'aggregate_tested_head':before['head'],'product_commit':'adfb5d87eb174cc19ffd15be7bbfdbf1ad607aa6',
         'product_raw_sha256':before['sources']['current_geometry.c']['raw_sha256'],
         'base_bridge_compilation_receipt_path':'tests/evidence/geo198/review-b1-m1/comparison/metadata.json',
         'base_bridge_compilation_receipt_sha256':hashlib.sha256((root/'tests/evidence/geo198/review-b1-m1/comparison/metadata.json').read_bytes()).hexdigest(),
         'ledger_path':'tests/mutants_results.json','ledger_sha256':hashlib.sha256((root/'tests/mutants_results.json').read_bytes()).hexdigest(),
         'validation':{'aggregate_started_clean':True,'aggregate_after_only_expected':True,'five_native_binaries_and_sidecars_unchanged':True,'source_and_judges_unchanged':True},
         'scope':'Cloud native aggregate only; no final-SHA seven-job/WSL/Windows GDI/browser claim'}
(out/'closure.json').write_text(json.dumps(closure,ensure_ascii=False,indent=2)+'\n')
shutil.copyfile('/tmp/geometry-202-corner-README.md',out/'README.md')
manifest=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file())
(out/'SHA256SUMS').write_text(manifest)
print(json.dumps({'payload_files':len(manifest.splitlines()),'bytes':sum(p.stat().st_size for p in out.rglob('*') if p.is_file())}))
