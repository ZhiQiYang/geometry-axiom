from pathlib import Path
import json,os,signal,sys,urllib.request,hashlib
root=Path(sys.argv[1]).resolve();port=int(sys.argv[2]);out=Path(sys.argv[3]);out.mkdir(parents=True,exist_ok=False)
url=f'http://127.0.0.1:{port}/'
runtime=json.load(urllib.request.urlopen(url+'runtime',timeout=10))
assert Path(runtime['root']).resolve()==root
pid=runtime['pid'];proc=Path('/proc')/str(pid)
assert proc.joinpath('cwd').resolve()==root
assert str(root/'geometry-web/serve.py').encode() in proc.joinpath('cmdline').read_bytes()
assert port == 19182
bridge=Path('<isolated-test-directory>')
children=[]
for p in Path('/proc').iterdir():
    if not p.name.isdigit():continue
    try:
        parent=int(p.joinpath('stat').read_text().split(') ',1)[1].split()[1])
        if parent==pid:
            assert p.joinpath('exe').resolve()==bridge
            children.append(int(p.name))
    except FileNotFoundError:continue
request=urllib.request.Request(url+'api',json.dumps({'cmd':'dump'}).encode(),{'Content-Type':'application/json'})
raw=urllib.request.urlopen(request,timeout=30).read();assert json.loads(raw)['ok']
out.joinpath('root-dump.raw.json').write_bytes(raw)
out.joinpath('identity.json').write_text(json.dumps({'runtime':runtime,'server':pid,'children':children,'rootDumpSHA256':hashlib.sha256(raw).hexdigest()},indent=2)+'\n')
for child in children:os.kill(child,signal.SIGTERM)
os.kill(pid,signal.SIGTERM)
print(json.dumps({'stoppedOwnedServer':pid,'stoppedOwnedChildren':children}))
