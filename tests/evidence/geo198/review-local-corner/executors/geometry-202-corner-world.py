import hashlib,json,pathlib,resource,shutil,subprocess,time
root=pathlib.Path.cwd();out=pathlib.Path('/tmp/geometry-202-corner/world-cmp');out.mkdir(parents=True,exist_ok=True)
shutil.copyfile('/tmp/geometry-202-corner-world.c',out/'harness.c')
resource.setrlimit(resource.RLIMIT_STACK,(16777216,resource.getrlimit(resource.RLIMIT_STACK)[1]))
assert subprocess.check_output(['git','diff','8515307','--','geometry-core','geometry-web'])==b''
rows=[]
for name,ref in [('before','851530708fee6373b95e45e28a784c627d970da6'),('after','working-tree')]:
    source=subprocess.check_output(['git','show',ref+':current_geometry.c']) if name=='before' else (root/'current_geometry.c').read_bytes()
    path=out/(name+'-source.c');path.write_bytes(source)
    argv=['cc','-std=c11','-O2','-I',str(root),'-DGEOMETRY_SOURCE="'+str(path)+'"',str(out/'harness.c'),'-lm','-o',str(out/(name+'-harness'))]
    start=time.monotonic()
    with (out/(name+'-build.log')).open('wb') as log:build=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT)
    assert build.returncode==0
    command=[str(out/(name+'-harness'))]
    with (out/(name+'.log')).open('wb') as log, (out/(name+'.stderr.log')).open('wb') as errors:
        run=subprocess.run(command,stdout=log,stderr=errors)
    results=[json.loads(s.split(' ',1)[1]) for s in (out/(name+'.log')).read_text().splitlines() if s.startswith('WORLD_BYTE_RESULT ')]
    assert len(results)==64
    assert run.returncode==(1 if name=='before' else 0)
    if name=='after':assert all(not r['accepted'] and r['world_bytes_equal'] for r in results)
    rows.append({'phase':name,'ref':ref,'source_c_sha256':hashlib.sha256(source).hexdigest(),'harness_sha256':hashlib.sha256((out/'harness.c').read_bytes()).hexdigest(),
                 'compile_argv':argv,'compile_returncode':build.returncode,'run_argv':command,'run_returncode':run.returncode,'seconds':time.monotonic()-start,
                 'binary_sha256':hashlib.sha256((out/(name+'-harness')).read_bytes()).hexdigest(),'results':results})
(out/'results.json').write_text(json.dumps(rows,indent=2));print(json.dumps([{'phase':r['phase'],'exit':r['run_returncode'],'accepted':sum(x['accepted'] for x in r['results']),
    'world_bytes_equal':sum(x['world_bytes_equal'] for x in r['results'])} for r in rows]))
