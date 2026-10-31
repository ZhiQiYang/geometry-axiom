#!/usr/bin/env python3
"""Close source extraction and installed compiler/libc identities, no benchmark."""
import gzip,hashlib,json,os,platform,shlex,subprocess,time
from pathlib import Path
ROOT=Path('/tmp/pr338-b3-p189');OUT=ROOT/'build-environment';OUT.mkdir(exist_ok=False)
def digest(body):return hashlib.sha256(body).hexdigest()
records=[]
def run(cmd,cwd):
    started=time.time();p=subprocess.run(cmd,cwd=cwd,capture_output=True,timeout=60)
    number=len(records)+1
    for stream in ('stdout','stderr'):(OUT/f'{number:02d}-{stream}.bin.gz').write_bytes(gzip.compress(getattr(p,stream),mtime=0))
    records.append({'command':cmd,'cwd':str(cwd),'start_epoch_utc':started,'seconds':time.time()-started,
                    'actual_process_returncode':p.returncode,'timeout_seconds':60,
                    'stdout_bytes':len(p.stdout),'stdout_sha256':digest(p.stdout),'stderr_bytes':len(p.stderr),'stderr_sha256':digest(p.stderr)})
    assert p.returncode==0,(cmd,p.stderr)
    return p.stdout
cmd=['gcc','-std=c11','-O2','-E','geometry-web/web_bridge.c']
a=run(cmd,Path('/tmp/pr338-unblock'));b=run(cmd,ROOT/'work-v2/fix')
assert a==b,'Full preprocessed source changed in private closure copy'
dependencies=run(['gcc','-std=c11','-O2','-M','geometry-web/web_bridge.c'],ROOT/'work-v2/fix')
headers=[]
for name in sorted(set(shlex.split(dependencies.decode().replace('\\\n',' '))[1:])):
    path=Path(name)
    if not path.is_absolute():continue
    body=path.read_bytes();headers.append({'path':str(path),'bytes':len(body),'sha256':digest(body)})
runtime=[]
for label in ('main','base','fix'):
    body=run(['ldd',str(ROOT/'work-v2'/label/'bridge')],ROOT)
    for line in body.decode().splitlines():
        pieces=line.split()
        for piece in pieces:
            if piece.startswith('/'):
                path=Path(piece)
                if path.exists() and str(path) not in {x['path'] for x in runtime}:
                    data=path.read_bytes();runtime.append({'path':str(path),'bytes':len(data),'sha256':digest(data)})
compiler=Path('/usr/bin/gcc').resolve();cc1=Path(run(['gcc','-print-prog-name=cc1'],ROOT).decode().strip()).resolve()
compiler_files=[{'path':str(p),'bytes':p.stat().st_size,'sha256':digest(p.read_bytes())} for p in (compiler,cc1)]
(OUT/'RESULT.json').write_text(json.dumps({'exit':0,'source_sha':'0ae1728c2309e1d670369289a6b8da059fa63a50',
    'donor_private_preprocessed_equal':True,'preprocessed_sha256':digest(a),'system_headers':headers,
    'compiler_files':compiler_files,'runtime_libraries':runtime,'commands':records,
    'environment':{k:os.environ.get(k) for k in ('PATH','LANG','LC_ALL')}} ,indent=2)+'\n')
print('preprocessed source exact; system headers/compiler/runtime closure verified')
