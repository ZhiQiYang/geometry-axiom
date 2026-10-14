import hashlib,json,os,pathlib,re,subprocess,sys,time
root=pathlib.Path.cwd();out=pathlib.Path('/tmp/geometry-182-cause/checks');out.mkdir(parents=True,exist_ok=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();assert subprocess.check_output(['git','status','--porcelain'])==b''
rows=[]
for name,argv in [('guard',[sys.executable,'tests/test_section_profile_mutation_check.py']),
                  ('runner-subset',[sys.executable,'tests/run_all.py','--only','py:test_section_profile_mutation_check']),
                  ('core-freshness',[sys.executable,'tests/mutate.py','--check'])]:
    env=dict(os.environ)
    if name=='core-freshness':
        cache=pathlib.Path('/tmp/geometry-182-cause/no-core-cache');assert not cache.exists();env['MUTATE_CACHE']=str(cache)
    start=time.monotonic()
    with (out/(name+'.log')).open('wb') as log:run=subprocess.run(argv,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
    row={'name':name,'argv':argv,'returncode':run.returncode,'seconds':time.monotonic()-start,'log_sha256':hashlib.sha256((out/(name+'.log')).read_bytes()).hexdigest()}
    if name=='core-freshness':row.update(cache_override=str(cache),scope='Receipt freshness only, no 48-case rerun, cache absent; historical shared-cache failure preserved')
    rows.append(row);assert run.returncode==0,row
    if name=='guard':assert re.search(r'Ran 29 tests.*\n\s*\nOK', (out/(name+'.log')).read_text())
assert subprocess.check_output(['git','status','--porcelain'])==b''
(out/'receipt.json').write_text(json.dumps({'head':head,'before_after_clean':True,'commands':rows,'scope':'29-method guard, original one-suite runner only; not a new full 84-suite aggregate or formal seven jobs'},indent=2)+'\n')
print(json.dumps(rows))
