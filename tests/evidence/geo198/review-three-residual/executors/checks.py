import hashlib,importlib.util,json,os,pathlib,resource,subprocess,sys,time
root=pathlib.Path('/workspace/geometry-axiom');sys.path.insert(0,str(root/'tests'));import binaries,run_all
spec=importlib.util.spec_from_file_location('identity',root/'tests/geo246/identity.py');identity=importlib.util.module_from_spec(spec);spec.loader.exec_module(identity)
resource.setrlimit(resource.RLIMIT_STACK,(16777216,resource.getrlimit(resource.RLIMIT_STACK)[1]))
out=pathlib.Path('/tmp/geometry-198-review3')/sys.argv[1];out.mkdir(exist_ok=True)
paths=[pathlib.Path('/tmp/geometry-tests')/n for n in ('core','integrity','bridge')]
paths=[p for p in paths if p.exists()]
def snapshot():
    value=identity.capture(root,paths)
    for p in paths:
        s=pathlib.Path(str(p)+'.fingerprint.json')
        value['binaries'][str(p)]['sidecar_sha256']=hashlib.sha256(s.read_bytes()).hexdigest() if s.exists() else None
    value['judge_sources']={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ('tests/test_core_integrity.c','tests/test_reference_contract.py','tests/run_tests.py','tests/mutate.py','_ax_r8_three_residual_components.scene','_ax_r8_three_residual_strip.scene')}
    return value
identity.write(out/'checkout-before.json',snapshot());env=run_all.child_env(binaries.inspect_all(),[])
commands={'native':['/tmp/geometry-tests/integrity'],'reference':[sys.executable,'tests/test_reference_contract.py'],'scenes':[sys.executable,'tests/run_tests.py','/tmp/geometry-tests/core']}
rows={}
for name,argv in commands.items():
    started=time.monotonic()
    with (out/(name+'.log')).open('wb') as log:
        proc=subprocess.Popen(argv,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT);code=proc.wait(timeout=600)
    rows[name]={'argv':argv,'cwd':str(root),'returncode':code,'seconds':time.monotonic()-started,'log_sha256':hashlib.sha256((out/(name+'.log')).read_bytes()).hexdigest()}
    (out/'runs.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,code,flush=True)
identity.write(out/'checkout-after.json',snapshot());sys.exit(int(any(r['returncode'] for r in rows.values())))
