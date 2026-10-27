from pathlib import Path
import fcntl, hashlib, json, os, shutil, datetime
receipt=Path('/workspace/scratch/geo337-native-aprime-a4bd77e-20261027')
lock=open('/tmp/geo337-native-owner.lock','a+')
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
result=json.loads((receipt/'RESULT.json').read_text())
assert result['sha']=='a4bd77e8090f5a82f0c8934c30c5335782293922'
for name,expected in json.loads((receipt/'SHA256.json').read_text()).items():
    p=receipt/name
    assert p.stat().st_size==expected['bytes']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==expected['sha256'],name
src=Path('/tmp/geometry-tests'); dst=Path('/tmp/geo337-a4bd77e-native-output-preserved')
assert src.is_dir() and not dst.exists()
for name in ['run_all.lock','build.lock']:
    f=(src/name).open('a+')
    fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    f.close()
src.rename(dst)
(receipt/'OUTPUT_PRESERVATION.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'rename own completed output after verifying all archived original hashes','from':str(src),'to':str(dst),'archive_verified':True,'deleted_files':False},indent=2)+'\n')
shutil.copy2('/workspace/scratch/geo337-native-audit-20261027/run_native.py',receipt/'launcher.original.py')
