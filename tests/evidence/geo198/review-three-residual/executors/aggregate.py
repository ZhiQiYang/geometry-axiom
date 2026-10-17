import hashlib,importlib.util,json,os,pathlib,resource,shutil,subprocess,sys,time
root=pathlib.Path('/workspace/geometry-axiom');scratch=pathlib.Path('/tmp/geometry-198-review3');out=scratch/'aggregate';out.mkdir(exist_ok=True)
resource.setrlimit(resource.RLIMIT_STACK,(16777216,resource.getrlimit(resource.RLIMIT_STACK)[1]))
spec=importlib.util.spec_from_file_location('identity',root/'tests/geo246/identity.py');identity=importlib.util.module_from_spec(spec);spec.loader.exec_module(identity)
build_argv=[sys.executable,'tests/binaries.py','build'];build_started=time.monotonic()
with (out/'build.log').open('wb') as build_log:
    build=subprocess.run(build_argv,cwd=root,stdout=build_log,stderr=subprocess.STDOUT)
(out/'build-run.json').write_text(json.dumps({'argv':build_argv,'cwd':str(root),'returncode':build.returncode,'seconds':time.monotonic()-build_started,'log_sha256':hashlib.sha256((out/'build.log').read_bytes()).hexdigest()},indent=2)+'\n')
if build.returncode:sys.exit(build.returncode)
paths=sorted(p for p in pathlib.Path('/tmp/geometry-tests').glob('*') if p.is_file() and os.access(p,os.X_OK) and not p.suffix)
def snapshot():
    value=identity.capture(root,paths)
    for path in paths:
        sidecar=pathlib.Path(str(path)+'.fingerprint.json')
        value['binaries'][str(path)]['sidecar_sha256']=hashlib.sha256(sidecar.read_bytes()).hexdigest() if sidecar.exists() else None
    return value
def processes():
    rows=[]
    for p in pathlib.Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            tail=(p/'stat').read_text().rsplit(') ',1)[1].split()
            rows.append({'pid':int(p.name),'ppid':int(tail[1]),'comm':(p/'comm').read_text().strip()})
        except (OSError,IndexError):pass
    return {'seconds':time.monotonic()-started,'processes':rows}
identity.write(out/'checkout-before.json',snapshot());started=time.monotonic();samples=[]
argv=[sys.executable,'tests/run_all.py','--build','--update-expected']
with (out/'run.log').open('wb') as log:
    proc=subprocess.Popen(argv,cwd=root,stdout=log,stderr=subprocess.STDOUT)
    while True:
        samples.append(processes());code=proc.poll()
        if code is not None:break
        time.sleep(1)
identity.write(out/'checkout-after.json',snapshot())
shutil.copytree('/tmp/geometry-tests/run_all-logs',out/'logs',dirs_exist_ok=True)
shutil.copy2(root/'tests/run_all.expected.json',out/'expected.json')
(out/'process-samples.json').write_text(json.dumps({'scope':'One-second PID/PPID/comm observations only, no argv; may miss short processes and do not enforce isolation. Not formal WSL evidence.','runner_pid':proc.pid,'samples':samples},indent=2)+'\n')
receipt={'argv':argv,'cwd':str(root),'returncode':code,'seconds':time.monotonic()-started,'stack_soft_limit_bytes':resource.getrlimit(resource.RLIMIT_STACK)[0],'log_sha256':hashlib.sha256((out/'run.log').read_bytes()).hexdigest(),'sample_count':len(samples),'receipt':'Actual Popen.poll returncode, not inferred from counts'}
(out/'run.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True);sys.exit(code)
