import hashlib, importlib.util, json, os, pathlib, resource, shutil, subprocess, sys, time
root=pathlib.Path('/workspace/geometry-axiom')
resource.setrlimit(resource.RLIMIT_STACK,(16*1024*1024,resource.getrlimit(resource.RLIMIT_STACK)[1]))
out=pathlib.Path('/tmp/geometry-198-review2')/sys.argv[1];out.mkdir(parents=True,exist_ok=True)
argv=sys.argv[2:]
spec=importlib.util.spec_from_file_location('identity',root/'tests/geo246/identity.py');identity=importlib.util.module_from_spec(spec);spec.loader.exec_module(identity)
binary_paths=sorted(p for p in pathlib.Path('/tmp/geometry-tests').glob('*') if p.is_file() and os.access(p,os.X_OK) and not p.suffix)
identity.write(out/'checkout-before.json',identity.capture(root,binary_paths))
def census():
    rows=[]
    for d in pathlib.Path('/proc').iterdir():
        if not d.name.isdigit():continue
        try:
            args=d.joinpath('cmdline').read_bytes().decode(errors='replace').split('\0')[:-1]
            if not args:continue
            exe=pathlib.Path(args[0]).name
            selected=exe in ('bridge','core','integrity','engjson','model-base','chromium') or (exe.startswith('python') and any(pathlib.Path(a).name=='serve.py' for a in args[1:]))
            if selected:
                stat=d.joinpath('stat').read_text().split(') ',1)[1].split()
                rows.append({'pid':int(d.name),'ppid':int(stat[1]),'argv':args})
        except (OSError,IndexError):pass
    return {'monotonic_seconds':time.monotonic(),'processes':rows}
started=time.monotonic();samples=[]
with (out/'run.log').open('wb') as log:
    proc=subprocess.Popen(argv,cwd=root,stdout=log,stderr=subprocess.STDOUT)
    while True:
        samples.append(census())
        code=proc.poll()
        if code is not None:break
        time.sleep(1)
seconds=time.monotonic()-started
identity.write(out/'checkout-after.json',identity.capture(root,binary_paths))
(out/'process-samples.json').write_text(json.dumps({'scope':'One-second /proc observations; sampling is not enforced exclusive isolation and may miss short processes. No formal WSL isolation claim.','runner_pid':proc.pid,'samples':samples},indent=2)+'\n')
row={'argv':argv,'cwd':str(root),'returncode':code,'seconds':seconds,'stack_soft_limit_bytes':resource.getrlimit(resource.RLIMIT_STACK)[0],'log_sha256':hashlib.sha256((out/'run.log').read_bytes()).hexdigest(),'receipt':'returncode comes directly from Popen.poll, not test result inference','sample_count':len(samples)}
if argv[1:2]==['tests/run_all.py']:
    shutil.copytree('/tmp/geometry-tests/run_all-logs',out/'logs',dirs_exist_ok=True)
    shutil.copy2(root/'tests/run_all.expected.json',out/'expected.json')
(out/'run.json').write_text(json.dumps(row,indent=2)+'\n')
print(json.dumps(row),flush=True)
sys.exit(code)
