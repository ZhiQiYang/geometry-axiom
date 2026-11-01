import hashlib,json,pathlib,runpy,sys,tarfile
out=pathlib.Path(sys.argv[1]);root=pathlib.Path(sys.argv[2]);suite=sys.argv[3];tmp=out/'native-tmp'
sys.argv=[str(root/'tests/_unittest_runner.py'),str(root/'tests'/suite),'--json-out',str(out/'result.json'),'--log',str(out/'unittest.log')]
status=0
try:runpy.run_path(sys.argv[0],run_name='__main__')
except SystemExit as exc:status=exc.code if isinstance(exc.code,int) else int(bool(exc.code))
finally:
 files=sorted(p for p in tmp.rglob('*') if p.is_file())
 with tarfile.open(out/'native-build-inputs-and-binaries.tar.gz','w:gz') as archive:
  for p in files:archive.add(p,arcname=p.relative_to(tmp),recursive=False)
 rows={p.relative_to(tmp).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns} for p in files}
 (out/'native-build-files.json').write_text(json.dumps(rows,indent=2)+'\n')
 for i,p in enumerate(sorted(tmp.rglob('build-log.json'))):(out/('native-build-'+str(i)+'.json')).write_bytes(p.read_bytes())
sys.exit(status)
