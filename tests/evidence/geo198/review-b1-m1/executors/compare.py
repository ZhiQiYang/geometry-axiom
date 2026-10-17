import hashlib, io, json, pathlib, resource, shutil, subprocess, sys, tarfile, time
root=pathlib.Path('/workspace/geometry-axiom');out=pathlib.Path('/tmp/geometry-198-review2/comparison');out.mkdir(exist_ok=True)
resource.setrlimit(resource.RLIMIT_STACK,(16*1024*1024,resource.getrlimit(resource.RLIMIT_STACK)[1]))
sys.path.insert(0,str(root));from tests._bridge import BridgeSession
previous='fc4859bb2bddb3dcb343e66c7d895802e70cbee3';base='635dd86ee368579aec444fb3ba16e48bccf4877e'
source=out/'previous-source';source.mkdir(exist_ok=True)
closure=json.loads(pathlib.Path('/tmp/geometry-tests/bridge.fingerprint.json').read_text())['files']
archive=subprocess.check_output(['git','archive',previous,*closure],cwd=root)
with tarfile.open(fileobj=io.BytesIO(archive)) as tar:tar.extractall(source,filter='data')
argv=['cc','-std=c11','-O2','geometry-web/web_bridge.c','-lm','-o',str(out/'previous-bridge')]
start=time.monotonic()
with (out/'previous-build.log').open('wb') as log:p=subprocess.run(argv,cwd=source,stdout=log,stderr=subprocess.STDOUT)
assert p.returncode==0
meta={'compile':{'argv':argv,'cwd':str(source),'returncode':p.returncode,'seconds':time.monotonic()-start},'previous_source_sha256':{str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file()}}
removed=json.loads(pathlib.Path('/tmp/geometry-198-review2/remove-fix/results.json').read_text())['removed']
shutil.copy2('/tmp/geometry-198-remove-fix/removed/bridge',out/'base-bridge')
assert hashlib.sha256((out/'base-bridge').read_bytes()).hexdigest()==removed['binary_sha256']['bridge']
meta['base_compilation_receipt']=removed
notch='0,0 100,0 100,100 60,100 60,40 40,40 40,100 0,100'
cases=[('B1',0,notch,['column 1 at 45 0 size 10 40 z 0 100','column 2 at 30 50 size 30 30 z 0 100'],'apply-proj 1 c1 c2'),('B1-strip',100,notch,['beam 2 along x from 30 to 60 at 65 width 30 depth 10 top 100'],'apply-proj 1 b2 cut-strip'),('B1-point',0,'0,0 100,0 100,100 60,100 60,80 80,80 80,40 40,40 40,100 0,100',['column 1 at 30 50 size 30 30 z 0 100'],'apply-proj 1 c1'),('M1',100,notch,['beam 1 along x from 30 to 70 at 65 width 30 depth 10 top 100'],'apply-proj 1 b1'),('M1-missing',100,notch,['beam 1 along x from 30 to 70 at 65 width 30 depth 10 top 100'],'apply-proj 1 b1 c99')]
for phase,head,binary in [('base',base,out/'base-bridge'),('previous',previous,out/'previous-bridge'),('fixed',subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),pathlib.Path('/tmp/geometry-tests/bridge'))]:
    rows=[]
    for name,z,outline,items,command in cases:
        with BridgeSession(str(binary),cwd=root) as s:
            fixture=[]
            for c in ['line reset',f'line surface 1 origin 0 0 {z} u +x v +y outline '+outline]+['line '+x for x in items]:
                response=s.send(c);assert response['ok'];fixture.append({'command':c,'response':response})
            query=s.send('obstacles 1');before=s.send('dump');result=s.send('line '+command);after=s.send('dump')
        rows.append({'name':name,'fixture':fixture,'query':query,'before':before,'command':command,'result':result,'after':after,'dump_equal':before['text']==after['text'],'bridge_returncode':s.process.returncode})
    (out/(phase+'.json')).write_text(json.dumps({'head':head,'binary':str(binary),'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'cases':rows},ensure_ascii=False,indent=2)+'\n')
    print(phase,[(r['name'],r['result']['ok'],r['dump_equal']) for r in rows],flush=True)
(out/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
