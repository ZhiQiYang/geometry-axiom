import hashlib,importlib.util,json,os,pathlib,resource,shutil,subprocess,sys,time
root=pathlib.Path.cwd();out=pathlib.Path('/tmp/geometry-202-corner/aggregate');out.mkdir(parents=True,exist_ok=True)
resource.setrlimit(resource.RLIMIT_STACK,(16777216,resource.getrlimit(resource.RLIMIT_STACK)[1]))
spec=importlib.util.spec_from_file_location('identity',root/'tests/geo246/identity.py');identity=importlib.util.module_from_spec(spec);spec.loader.exec_module(identity)
argv=[sys.executable,'tests/binaries.py','build'];start=time.monotonic()
with (out/'build.log').open('wb') as log:build=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT)
(out/'build-run.json').write_text(json.dumps({'argv':argv,'cwd':str(root),'returncode':build.returncode,'seconds':time.monotonic()-start},indent=2))
if build.returncode:sys.exit(build.returncode)
paths=sorted(p for p in pathlib.Path('/tmp/geometry-tests').glob('*') if p.is_file() and os.access(p,os.X_OK) and not p.suffix)
def snapshot():
    value=identity.capture(root,paths)
    for p in paths:
        s=pathlib.Path(str(p)+'.fingerprint.json')
        value['binaries'][str(p)]['sidecar_sha256']=hashlib.sha256(s.read_bytes()).hexdigest() if s.exists() else None
    judges=set(root.glob('*.scene'))|set((root/'tests').glob('*.py'))|set((root/'tests').glob('*.js'))|set((root/'tests').glob('*.c'))
    judges|=set((root/'geometry-web').glob('*.js'))|set((root/'geometry-web').glob('*.py'))|set((root/'geometry-core').rglob('*.py'))
    value['judge_sources']={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(judges)}
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
identity.write(out/'checkout-before.json',snapshot());started=time.monotonic();started_wall=time.time();samples=[]
argv=[sys.executable,'tests/run_all.py','--build','--update-expected']
with (out/'run.log').open('wb') as log:
    proc=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT)
    while True:
        samples.append(processes());code=proc.poll()
        if code is not None:break
        time.sleep(1)
identity.write(out/'checkout-after.json',snapshot())
cache=pathlib.Path('/tmp/geometry-tests/run_all-logs');index=[]
for p in sorted(cache.rglob('*')):
    if not p.is_file():continue
    target=out/'logs'/p.relative_to(cache);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
    index.append({'path':str(target.relative_to(out)),'modified_after_runner_start':p.stat().st_mtime>=started_wall,
                  'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(out/'log-index.json').write_text(json.dumps(index,indent=2))
shutil.copyfile(root/'tests/run_all.expected.json',out/'expected.json')
(out/'process-samples.json').write_text(json.dumps({'scope':'One-second PID/PPID/comm observations only, no argv; short processes may be missed. No enforced isolation or formal WSL claim.','runner_pid':proc.pid,'samples':samples},indent=2))
receipt={'argv':argv,'cwd':str(root),'returncode':code,'seconds':time.monotonic()-started,'stack_soft_limit_bytes':resource.getrlimit(resource.RLIMIT_STACK)[0],
         'log_sha256':hashlib.sha256((out/'run.log').read_bytes()).hexdigest(),'sample_count':len(samples),'receipt':'Direct Popen.poll returncode, not inferred from counts'}
(out/'run.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt),flush=True);sys.exit(code)
