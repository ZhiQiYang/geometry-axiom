from concurrent.futures import ThreadPoolExecutor
import collections,hashlib,importlib.util,json,os,pathlib,re,resource,shutil,subprocess,sys,time
root=pathlib.Path.cwd();sys.path.insert(0,str(root/'tests'));import mutate
resource.setrlimit(resource.RLIMIT_STACK,(16777216,resource.getrlimit(resource.RLIMIT_STACK)[1]))
out=pathlib.Path('/tmp/geometry-202-corner/mutations');out.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('identity',root/'tests/geo246/identity.py');identity=importlib.util.module_from_spec(spec);spec.loader.exec_module(identity)
identity.write(out/'checkout-before.json',identity.capture(root))
def worker(name,ids):
    argv=[sys.executable,'-u','tests/mutate.py',*ids];start=time.monotonic()
    with (out/(name+'.log')).open('wb') as log:
        env=dict(os.environ);env.pop('MUTATE_RESULTS',None)
        if name!='freshness':env['MUTATE_RESULTS']=str(out/(name+'.json'))
        proc=subprocess.Popen(argv,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT);code=proc.wait()
    row={'name':name,'ids':ids,'argv':argv,'cwd':str(root),'returncode':code,'seconds':time.monotonic()-start,'log_sha256':hashlib.sha256((out/(name+'.log')).read_bytes()).hexdigest()}
    (out/(name+'-run.json')).write_text(json.dumps(row,indent=2));print(name,code,flush=True);return row
rows=[worker('seed',['M67'])]
if rows[0]['returncode']:sys.exit(rows[0]['returncode'])
ids=[m['id'] for m in mutate.MUTANTS if m['id']!='M67']
with ThreadPoolExecutor(max_workers=4) as pool:rows+=list(pool.map(lambda i:worker('worker-'+str(i),ids[i::4]),range(4)))
(out/'workers.json').write_text(json.dumps(rows,indent=2))
if any(r['returncode'] for r in rows):sys.exit(1)
merged={}
for row in rows:
    records=json.loads((out/(row['name']+'.json')).read_text());assert not set(merged)&set(records);merged.update(records)
assert set(merged)=={m['id'] for m in mutate.MUTANTS}
mutate.save_records(root/'tests/mutants_results.json',merged)
check=worker('freshness',['--check']);assert check['returncode']==0
compiled=[]
for row in rows:compiled+=re.findall(r'^(M\d+)  exe 已重編$',(out/(row['name']+'.log')).read_text(),re.M)
nonretired={m['id'] for m in mutate.MUTANTS if not m.get('retired')};assert set(compiled)==nonretired and len(compiled)==len(nonretired)
assert merged['M67']['verdict']=='killed' and any('remote_flush' in x for x in merged['M67']['killed_by'])
paths=[mutate.MUT_ROOT/identifier/'_mut.exe' for identifier in nonretired]
identity.write(out/'checkout-after.json',identity.capture(root,[p for p in paths if p.exists()]))
shutil.copy2(root/'tests/mutants_results.json',out/'ledger.json')
report={'inventory':len(merged),'non_retired_recompiled_and_run':len(compiled),'retirement_proofs':len(merged)-len(compiled),
        'counts':dict(collections.Counter(r['verdict'] for r in merged.values())),'M67':merged['M67'],'workers_returncodes':[r['returncode'] for r in rows]}
(out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='M67'}),flush=True)
