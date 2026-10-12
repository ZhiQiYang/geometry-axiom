#!/usr/bin/env python3
"""Run one isolated UI209 prefix, not the full runner. A red prefix stays exit 1.

python3 tests/diagnostics/ui209_run.py --case p70-hold3 --out /tmp/ui209-held
Cases: p70-baseline, p70-hold3, p70-abort18, p88-wheel.
P88 materializes b40620c in TEMP; it does not checkout or mutate another branch.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import socket
import subprocess
import sys
import tarfile
import tempfile
import time
from urllib.request import urlopen

REPO = Path(__file__).resolve().parents[2]
TOOLS = Path(__file__).resolve().parent
OLD = 'b40620cd433ae36c6a3905c4293313dfd6e7f745'
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--case', required=True, choices=['p70-baseline','p70-hold3','p70-abort18','p88-wheel'])
p.add_argument('--out', type=Path, required=True)
p.add_argument('--bridge', type=Path)
args = p.parse_args()
out = args.out.resolve()
if Path(tempfile.gettempdir()) not in out.parents or out.exists():
    p.error('--out must be a new directory under TEMP')
out.mkdir(parents=True)
soft,hard = resource.getrlimit(resource.RLIMIT_STACK)
resource.setrlimit(resource.RLIMIT_STACK,(max(soft,16*1024*1024),hard))
root = REPO
head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
source_ref = head
commands = []
def digest(file): return hashlib.sha256(Path(file).read_bytes()).hexdigest()
def record(argv,cwd,code,elapsed):
    row=dict(argv=list(map(str,argv)),cwd=str(cwd),exit=code,seconds=elapsed)
    commands.append(row);(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');print(json.dumps(row),flush=True)
def run(argv,name,cwd=None,**kw):
    start=time.monotonic();cwd=cwd or root
    with (out/(name+'.log')).open('wb') as log:
        proc=subprocess.Popen(argv,cwd=cwd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,**kw)
        try: code=proc.wait(timeout=180)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGTERM)
            try: proc.wait(timeout=10)
            except subprocess.TimeoutExpired: os.killpg(proc.pid,signal.SIGKILL);proc.wait()
            code=124
    record(argv,cwd,code,time.monotonic()-start);return code
if args.case=='p88-wheel':
    root=out/'source';root.mkdir();source_ref=OLD
    archive=out/'source.tar';argv=['git','archive','--format=tar',OLD];start=time.monotonic()
    with archive.open('wb') as file: proc=subprocess.run(argv,cwd=REPO,stdout=file,check=True)
    record(argv,REPO,proc.returncode,time.monotonic()-start)
    with tarfile.open(archive) as tar: tar.extractall(root,filter='data')
    archive.unlink()
sys.path.insert(0,str(root/'geometry-web'))
from runtime_version import source_files
files=[x for x in source_files(root) if x.is_file()]
tool_files=[x for x in TOOLS.glob('ui209_*') if x.is_file()]+[TOOLS/'p78_server.py']
def sources(): return {**{str(x.relative_to(root)):digest(x) for x in files},**{'diagnostic-tools/'+x.name:digest(x) for x in tool_files}}
before=sources();(out/'sources-before.json').write_text(json.dumps(before,indent=2)+'\n')
run(['git','status','--short'],'git-status',cwd=REPO)
bridge=args.bridge.resolve() if args.bridge else out/'bridge'
if args.bridge is None:
    code=run(['gcc','-std=c11','-O2','geometry-web/web_bridge.c','-o',str(bridge),'-lm'],'compile')
    if code: sys.exit(code)
run(['gcc','-MM','geometry-web/web_bridge.c'],'include-closure')
for name,argv in [('compiler',['gcc','--version']),('node',['node','--version']),('chromium',['/usr/bin/chromium','--version'])]:run(argv,name+'-version')
with socket.socket() as probe: probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
hold={'p70-hold3':3,'p70-abort18':18}.get(args.case,0)
url=f'http://127.0.0.1:{port}/'
env={k:v for k,v in os.environ.items() if not k.startswith(('GEOMETRY_','P78_','UI209_'))}
env.update(UI209_SOURCE_ROOT=str(root),GEOMETRY_CHROME='/usr/bin/chromium',GEOMETRY_FEEDBACK_DIR=str(out/'feedback'))
argv=[sys.executable,'-u',str(TOOLS/'ui209_server.py'),str(port),str(out),str(bridge),str(hold)]
identity=dict(head=head,sourceRef=source_ref,root=str(root),case=args.case,url=url,python=sys.version,platform=sys.platform,
    argv=sys.argv,serverArgv=argv,holdSeconds=hold,fullRunner=False,historicalWSL=False,
    bridge=str(bridge),bridgeSha256=digest(bridge),stackBytes=resource.getrlimit(resource.RLIMIT_STACK)[0],
    tools={str(Path(x).resolve()):digest(Path(x).resolve()) for x in [sys.executable,shutil.which('node'),shutil.which('gcc'),'/usr/bin/chromium','/usr/lib/chromium/chromium']},
    envOverrides={k:v for k,v in env.items() if k.startswith(('GEOMETRY_','UI209_'))})
code=2
with (out/'host.log').open('wb') as log:
    server=subprocess.Popen(argv,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    try:
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            if server.poll() is not None: raise RuntimeError('server exited before ready')
            try:
                with urlopen(url+'runtime',timeout=1) as r: runtime=json.load(r)
                if runtime['fresh'] and runtime['pid']==server.pid and runtime['root']==str(root):
                    (out/'runtime.json').write_text(json.dumps(runtime,indent=2)+'\n');break
            except (OSError,ValueError): pass
            time.sleep(.2)
        else: raise RuntimeError('runtime readiness deadline')
        code=run(['node',str(TOOLS/'ui209_browser.cjs'),url,str(out),args.case],'browser',env=env)
    finally:
        server.terminate()
        try: server.wait(timeout=35)
        except subprocess.TimeoutExpired: os.killpg(server.pid,signal.SIGKILL);server.wait()
        after=sources();(out/'sources-after.json').write_text(json.dumps(after,indent=2)+'\n')
        identity.update(serverPid=server.pid,serverExit=server.returncode,browserExit=code,sourcesUnchanged=before==after,bridgeSha256After=digest(bridge))
        (out/'identity.json').write_text(json.dumps(identity,indent=2)+'\n')
if before!=after or identity['bridgeSha256']!=identity['bridgeSha256After']: raise RuntimeError('source/binary changed during run')
sys.exit(code)
