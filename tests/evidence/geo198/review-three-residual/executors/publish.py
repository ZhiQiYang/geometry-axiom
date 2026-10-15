import hashlib,json,pathlib,re,shutil,subprocess
root=pathlib.Path('/workspace/geometry-axiom');scratch=pathlib.Path('/tmp/geometry-198-review3')
out=root/'tests/evidence/geo198/review-three-residual';out.mkdir(exist_ok=True)
agg=scratch/'aggregate';receipt=json.loads((agg/'run.json').read_text());log=(agg/'run.log').read_text()
match=re.search(r'^合計\(已執行、有計數者\)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)',log,re.M);assert match
total,passed,failed,skipped=map(int,match.groups())
assert len(re.findall(r'^\[\d+/83\]',log,re.M))==83
before=json.loads((agg/'checkout-before.json').read_text());after=json.loads((agg/'checkout-after.json').read_text())
assert before['head']==after['head']=='299709e09974babff113718bfc3e32b853e09f4c'
assert before['tracked_diff']==[] and after['tracked_diff']==['tests/run_all.expected.json']
assert before['sources']==after['sources']
assert before['binaries']==after['binaries']
old=json.loads(subprocess.check_output(['git','show','HEAD:tests/run_all.expected.json'],cwd=root,text=True));new=json.loads((root/'tests/run_all.expected.json').read_text())
changed={k:{'before':old['suites'][k],'after':new['suites'][k]} for k in old['suites'] if old['suites'][k]!=new['suites'][k]}
assert set(changed)=={'c:integrity','core:run_tests','py:test_reference_contract'}
reader=json.loads((agg/'logs/py_test_axiom_reader.json').read_text());assert (reader['total'],reader['passed'],reader['failed'])==(41,35,6)
node=(agg/'logs/node_tests-js.log').read_text();assert re.search(r'^ℹ tests 651$',node,re.M)
metadata={'aggregate':{'total':total,'passed':passed,'failed':failed,'skipped':skipped,**receipt},'expected_changes':changed,'source_bytes_equal':True,'binary_and_sidecar_snapshots_equal':True,'aggregate_before_clean':True,'aggregate_after_expected_dirty':True,'reader_failed_tests':[r['test'] for r in reader['failures']]}
cache_map={str(p.relative_to(agg/'logs')):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'modified_after_checkout_before':p.stat().st_mtime>=(agg/'checkout-before.json').stat().st_mtime} for p in sorted((agg/'logs').rglob('*')) if p.is_file()}
metadata['cache_logs']='Cached log directory copied verbatim; log-index distinguishes files modified during this run from older unused cache files. Full run.log and per-suite current JSON/native logs identify the executed results.'
(scratch/'summary.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n');(agg/'log-index.json').write_text(json.dumps(cache_map,indent=2)+'\n')
paragraph=f'原完整 `python3 tests/run_all.py --build --update-expected`：83 suite 全部執行，{total} 個有計數項＝{passed} pass／{failed} fail／{skipped} 個具名允許 Windows GDI skip，直接 returncode {receipt["returncode"]}、{receipt["seconds"]:.2f} 秒。reader 35/41、6 fail；完整原 Node 的結果見原 log，沒有用插樁探針拼接本次全量。原 5 秒 timeout／斷言／concurrency 不變。'
readme=(scratch/'README.md').read_text().replace('%AGGREGATE%',paragraph)
assert '%AGGREGATE%' not in readme
(out/'README.md').write_text(readme)
for name in ('before','after','mutations','aggregate','reader-diagnostic'):
    shutil.copytree(scratch/name,out/name,dirs_exist_ok=True)
for path in (scratch/'comparison').glob('*.json'):
    (out/'comparison').mkdir(exist_ok=True);shutil.copy2(path,out/'comparison'/path.name)
for path in (scratch/'world-cmp').iterdir():
    if path.name in ('harness.c','run.py','results.json') or path.suffix=='.log':
        (out/'world-cmp').mkdir(exist_ok=True);shutil.copy2(path,out/'world-cmp'/path.name)
for name in ('before-build.log','after-build.log','scene-comparison.json','reader-diagnostic.log','summary.json','owner192.json'):
    shutil.copy2(scratch/name,out/name)
executors=out/'executors';executors.mkdir(exist_ok=True)
for name in ('checks.py','compare.py','edit_core.py','refresh.py','aggregate.py','reader-diagnostic.py','verify-scenes.py','publish.py'):
    shutil.copy2(scratch/name,executors/name)
shutil.copy2('/tmp/geometry-198-review2/reader-diagnostic.py',executors/'reader-diagnostic-original.py')
manifest={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file() and p.name!='sha256.json'}
(out/'sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'payloads':len(manifest),'bytes':sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),'total':total,'passed':passed,'failed':failed,'skipped':skipped,'returncode':receipt['returncode'],'seconds':receipt['seconds']},ensure_ascii=False))
