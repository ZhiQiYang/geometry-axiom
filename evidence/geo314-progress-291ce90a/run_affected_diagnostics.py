#!/usr/bin/env python3
"""Run only the five parent-authorized affected suites with a private fresh bridge."""
import datetime,hashlib,json,os,pathlib,platform,subprocess,sys,tarfile,time
root=pathlib.Path('/tmp/g261-next314');out=pathlib.Path(sys.argv[1]);bridge=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=False)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=root)
for when in ['before']:
 (out/(when+'-head.txt')).write_bytes(git('rev-parse','HEAD'));(out/(when+'-status.txt')).write_bytes(git('status','--porcelain=v1'));(out/(when+'.patch')).write_bytes(git('diff','--binary','HEAD'))
paths=[p for p in git('ls-files','-z').decode().split('\0') if p and pathlib.Path(p).suffix in {'.c','.h','.inc','.py','.scene'} and not any(t in p.split('/') for t in ('evidence','release-evidence','.git'))]
with tarfile.open(out/'source-inputs.tar.gz','w:gz') as archive:
 for p in paths:archive.add(root/p,arcname=p,recursive=False)
(out/'source-inputs.json').write_text(json.dumps({'head':head,'files':{p:sha(root/p) for p in paths}},indent=2)+'\n')
wrapper=out/'capture_suite.py';wrapper.write_text('''import hashlib,json,pathlib,runpy,sys,tarfile\nout=pathlib.Path(sys.argv[1]);root=pathlib.Path(sys.argv[2]);suite=sys.argv[3];tmp=out/'native-tmp'\nsys.argv=[str(root/'tests/_unittest_runner.py'),str(root/'tests'/suite),'--json-out',str(out/'result.json'),'--log',str(out/'unittest.log')]\nstatus=0\ntry:runpy.run_path(sys.argv[0],run_name='__main__')\nexcept SystemExit as exc:status=exc.code if isinstance(exc.code,int) else int(bool(exc.code))\nfinally:\n files=sorted(p for p in tmp.rglob('*') if p.is_file())\n with tarfile.open(out/'native-build-inputs-and-binaries.tar.gz','w:gz') as archive:\n  for p in files:archive.add(p,arcname=p.relative_to(tmp),recursive=False)\n rows={p.relative_to(tmp).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns} for p in files}\n (out/'native-build-files.json').write_text(json.dumps(rows,indent=2)+'\\n')\n for i,p in enumerate(sorted(tmp.rglob('build-log.json'))):(out/('native-build-'+str(i)+'.json')).write_bytes(p.read_bytes())\nsys.exit(status)\n''')
suites=['test_geo314_stagger_commit.py','test_geo314_commit_paths.py','test_geo314_ordered_facts.py','test_geo261_wood_grid_application.py','test_mutation_freshness.py']
summary={'schema':'geo314-affected-private-diagnostics/1','head':head,'scope':suites,'bridge':str(bridge),'bridge_sha256':sha(bridge),'bridge_sidecar_sha256':sha(pathlib.Path(str(bridge)+'.fingerprint.json')),'wrapper_sha256':sha(wrapper),'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'suites':[]}
for suite in suites:
 directory=out/pathlib.Path(suite).stem;directory.mkdir();tmp=directory/'native-tmp';tmp.mkdir()
 env=dict(os.environ);env['TMPDIR']=str(tmp);env['GEOMETRY_TEST_BRIDGE']=str(bridge);env['GEO314_DIAGNOSTIC_SCOPE']='five-affected-suites-only'
 command=[sys.executable,str(wrapper),str(directory),str(root),suite];start=time.monotonic()
 print('START '+suite,flush=True)
 with (directory/'stdout.raw').open('wb') as stdout,(directory/'stderr.raw').open('wb') as stderr:r=subprocess.run(command,cwd=root,env=env,stdout=stdout,stderr=stderr)
 row={'suite':suite,'command':command,'exit_code':r.returncode,'elapsed_seconds':time.monotonic()-start,'head':head,'cwd':str(root),'environment':{k:env.get(k) for k in ['PATH','TMPDIR','GEOMETRY_TEST_BRIDGE','CC','GEO314_DIAGNOSTIC_SCOPE']},'platform':platform.platform(),'output_files':{p.name:{'sha256':sha(p),'size':p.stat().st_size} for p in sorted(directory.iterdir()) if p.is_file()}}
 if (directory/'result.json').is_file():row['result']=json.loads((directory/'result.json').read_text())
 (directory/'receipt.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n');summary['suites'].append(row);(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
 print('END '+suite+' exit='+str(r.returncode)+' result='+json.dumps(row.get('result'),ensure_ascii=False),flush=True)
for when in ['after']:
 (out/(when+'-head.txt')).write_bytes(git('rev-parse','HEAD'));(out/(when+'-status.txt')).write_bytes(git('status','--porcelain=v1'));(out/(when+'.patch')).write_bytes(git('diff','--binary','HEAD'))
summary['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();summary['exit_code']=int(any(row['exit_code'] for row in summary['suites']));(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');sys.exit(summary['exit_code'])
