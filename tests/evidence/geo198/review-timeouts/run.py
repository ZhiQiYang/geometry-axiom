import hashlib,json,os,pathlib,resource,subprocess,sys,time
root=pathlib.Path('/workspace/geometry-axiom');sys.path.insert(0,str(root/'tests'))
import binaries,run_all
spec=__import__('importlib.util',fromlist=['x']).spec_from_file_location('identity',root/'tests/geo246/identity.py')
identity=__import__('importlib.util',fromlist=['x']).module_from_spec(spec);spec.loader.exec_module(identity)
resource.setrlimit(resource.RLIMIT_STACK,(16777216,resource.getrlimit(resource.RLIMIT_STACK)[1]))
mode=sys.argv[1];out=pathlib.Path('/tmp/geometry-198-timeouts')/mode;out.mkdir(exist_ok=True)
argv=['node','--require','/tmp/geometry-198-timeouts/preload.cjs','--test','--test-reporter=spec']
argv+=sorted(run_all.NODE_TEST_FILES) if mode=='whole-node' else ['tests/test_reference_workspace_races.js']
env=run_all.child_env(binaries.inspect_all(),[]);env['TIMEOUT_DIAGNOSTIC_DIR']=str(out)
identity.write(out/'checkout-before.json',identity.capture(root))
samples=[];started=time.monotonic()
with (out/'run.log').open('wb') as log:
    proc=subprocess.Popen(argv,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
    while True:
        nodes=[]
        for item in pathlib.Path('/proc').iterdir():
            if not item.name.isdigit():continue
            try:
                raw=(item/'cmdline').read_bytes().decode(errors='replace').split('\0')[:-1]
                if raw and pathlib.Path(raw[0]).name=='node':nodes.append({'pid':int(item.name),'argv':raw})
            except OSError:pass
        samples.append({'seconds':time.monotonic()-started,'cpu_stat':pathlib.Path('/sys/fs/cgroup/cpu.stat').read_text(),'nodes':nodes})
        code=proc.poll()
        if code is not None:break
        time.sleep(.5)
identity.write(out/'checkout-after.json',identity.capture(root))
(out/'samples.json').write_text(json.dumps(samples,indent=2)+'\n')
receipt={'mode':'instrumented diagnostic, original tests and 5000ms timeouts retained; not formal acceptance','argv':argv,'cwd':str(root),'returncode':code,'seconds':time.monotonic()-started,'log_sha256':hashlib.sha256((out/'run.log').read_bytes()).hexdigest(),'geometry_environment':{k:v for k,v in env.items() if k.startswith('GEOMETRY_')}}
(out/'run.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True);sys.exit(code)
