import hashlib,json,pathlib,resource,subprocess,time
root=pathlib.Path('/workspace/geometry-axiom');out=pathlib.Path('/tmp/geometry-198-review3/world-cmp')
resource.setrlimit(resource.RLIMIT_STACK,(16777216,resource.getrlimit(resource.RLIMIT_STACK)[1]))
assert subprocess.check_output(['git','diff','ed877f5','HEAD','--','geometry-core','geometry-web'],cwd=root)==b''
rows=[]
for name,ref in [('before','ed877f5f05156511db24cc24cf6b90da1c4b0cda'),('after','299709e09974babff113718bfc3e32b853e09f4c')]:
    source=subprocess.check_output(['git','show',ref+':current_geometry.c'],cwd=root)
    path=out/(name+'-source.c');path.write_bytes(source)
    argv=['cc','-std=c11','-O2','-I',str(root),'-DGEOMETRY_SOURCE="'+str(path)+'"',str(out/'harness.c'),'-lm','-o',str(out/(name+'-harness'))]
    started=time.monotonic()
    with (out/(name+'-build.log')).open('wb') as log:compile_run=subprocess.run(argv,cwd=root,stdout=log,stderr=subprocess.STDOUT)
    assert compile_run.returncode==0
    run_argv=[str(out/(name+'-harness'))]
    with (out/(name+'.log')).open('wb') as log:run=subprocess.run(run_argv,cwd=root,stdout=log,stderr=subprocess.STDOUT)
    results=[json.loads(line.split(' ',1)[1]) for line in (out/(name+'.log')).read_text().splitlines() if line.startswith('WORLD_BYTE_RESULT ')]
    assert len(results)==4
    assert run.returncode==(1 if name=='before' else 0)
    assert all(r['accepted']==(name=='before') and r['world_bytes_equal']==(name=='after') for r in results)
    rows.append({'phase':name,'ref':ref,'source_c_sha256':hashlib.sha256(source).hexdigest(),'harness_sha256':hashlib.sha256((out/'harness.c').read_bytes()).hexdigest(),'compile_argv':argv,'compile_returncode':compile_run.returncode,'run_argv':run_argv,'run_returncode':run.returncode,'seconds':time.monotonic()-started,'binary_sha256':hashlib.sha256((out/(name+'-harness')).read_bytes()).hexdigest(),'log_sha256':hashlib.sha256((out/(name+'.log')).read_bytes()).hexdigest(),'results':results})
(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps([{'phase':r['phase'],'run_returncode':r['run_returncode'],'results':r['results']} for r in rows]),flush=True)
