import hashlib, importlib.util, json, pathlib, resource, subprocess, sys, time
root=pathlib.Path('/workspace/geometry-axiom')
resource.setrlimit(resource.RLIMIT_STACK,(16*1024*1024,resource.getrlimit(resource.RLIMIT_STACK)[1]))
out=pathlib.Path('/tmp/geometry-198-review2')/sys.argv[1];out.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('identity',root/'tests/geo246/identity.py');identity=importlib.util.module_from_spec(spec);spec.loader.exec_module(identity)
identity.write(out/'checkout-before.json',identity.capture(root))
commands={'native':['/tmp/geometry-tests/integrity'],'reference':[sys.executable,'tests/test_reference_contract.py']}
if len(sys.argv)>2:commands={k:v for k,v in commands.items() if k in sys.argv[2:]}
rows={}
for name,argv in commands.items():
    started=time.monotonic()
    with (out/(name+'.log')).open('wb') as log:
        p=subprocess.run(argv,cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=300)
    rows[name]={'argv':argv,'cwd':str(root),'returncode':p.returncode,'seconds':time.monotonic()-started,'log_sha256':hashlib.sha256((out/(name+'.log')).read_bytes()).hexdigest()}
    (out/'runs.json').write_text(json.dumps(rows,indent=2))
    print(name,p.returncode,flush=True)
identity.write(out/'checkout-after.json',identity.capture(root))
sys.exit(1 if any(row['returncode']!=0 for row in rows.values()) else 0)
