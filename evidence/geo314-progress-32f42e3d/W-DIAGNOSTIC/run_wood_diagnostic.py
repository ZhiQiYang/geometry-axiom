#!/usr/bin/env python3
import datetime,hashlib,json,os,pathlib,platform,subprocess,sys,tarfile,time
root=pathlib.Path('/tmp/g261-next314')
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
out=pathlib.Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
tmp=out/'native-tmp';tmp.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=root)
(out/'before-head.txt').write_bytes(git('rev-parse','HEAD'))
(out/'before-status.txt').write_bytes(git('status','--porcelain=v1'))
(out/'before.patch').write_bytes(git('diff','--binary','HEAD'))
paths=[p for p in git('ls-files','-z').decode().split('\0') if p and pathlib.Path(p).suffix in {'.c','.h','.inc','.py'} and not any(t in p.split('/') for t in ('evidence','release-evidence','.git'))]
with tarfile.open(out/'source-inputs.tar.gz','w:gz') as archive:
 for p in paths:archive.add(root/p,arcname=p,recursive=False)
(out/'source-inputs.json').write_text(json.dumps({'head':head,'files':{p:sha(root/p) for p in paths}},indent=2)+'\n')
wrapper=out/'capture_runner.py'
wrapper.write_text('''import hashlib,json,pathlib,runpy,sys,tarfile\nout=pathlib.Path(sys.argv[1]);root=pathlib.Path(sys.argv[2]);tmp=out/'native-tmp'\nsys.argv=[str(root/'tests/_unittest_runner.py'),str(root/'tests/test_geo261_wood_grid_application.py'),'--json-out',str(out/'result.json'),'--log',str(out/'unittest.log')]\nstatus=0\ntry:\n runpy.run_path(sys.argv[0],run_name='__main__')\nexcept SystemExit as exc:\n status=exc.code if isinstance(exc.code,int) else int(bool(exc.code))\nfinally:\n files=sorted(p for p in tmp.rglob('*') if p.is_file())\n with tarfile.open(out/'native-build-inputs-and-binaries.tar.gz','w:gz') as archive:\n  for p in files:archive.add(p,arcname=p.relative_to(tmp),recursive=False)\n rows={p.relative_to(tmp).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns} for p in files}\n (out/'native-build-files.json').write_text(json.dumps(rows,indent=2)+'\\n')\n for i,p in enumerate(sorted(tmp.rglob('build-log.json'))):\n  (out/('native-build-'+str(i)+'.json')).write_bytes(p.read_bytes())\nsys.exit(status)\n''')
env=dict(os.environ);env['TMPDIR']=str(tmp);env['GEO314_DIAGNOSTIC_SCOPE']='isolated-wood-suite-only'
versions={}
for name,cmd in [('python',['python3','--version']),('cc',['cc','--version']),('node',['node','--version']),('chrome',['google-chrome','--version']),('uname',['uname','-a'])]:
 try:r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 except FileNotFoundError as exc:r=subprocess.CompletedProcess(cmd,127,b'',str(exc).encode())
 (out/(name+'.stdout')).write_bytes(r.stdout);(out/(name+'.stderr')).write_bytes(r.stderr);versions[name]={'command':cmd,'exit_code':r.returncode}
command=[sys.executable,str(wrapper),str(out),str(root)]
started=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.monotonic()
with (out/'stdout.raw').open('wb') as stdout,(out/'stderr.raw').open('wb') as stderr:
 result=subprocess.run(command,cwd=root,env=env,stdout=stdout,stderr=stderr)
receipt={'schema':'geo314-isolated-wood-diagnostic/1','scope':'Only tests/test_geo261_wood_grid_application.py; not full acceptance','head':head,'command':command,'stack_limit_bytes':16777216,'started_at':started,'elapsed_seconds':time.monotonic()-t,'exit_code':result.returncode,'cwd':str(root),'environment':{k:env.get(k) for k in ['PATH','TMPDIR','CC','GEO314_DIAGNOSTIC_SCOPE']},'platform':platform.platform(),'versions':versions}
(out/'after-head.txt').write_bytes(git('rev-parse','HEAD'));(out/'after-status.txt').write_bytes(git('status','--porcelain=v1'));(out/'after.patch').write_bytes(git('diff','--binary','HEAD'))
receipt['output_files']={p.name:{'sha256':sha(p),'size':p.stat().st_size} for p in sorted(out.iterdir()) if p.is_file()}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'outdir':str(out),'head':head,'exit_code':result.returncode,'elapsed_seconds':receipt['elapsed_seconds']},ensure_ascii=False),flush=True)
sys.exit(result.returncode)
