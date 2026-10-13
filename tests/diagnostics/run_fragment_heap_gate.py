"""Formal Linux fragment-heap gate: fresh builds, OOM injection and raw receipts."""
import argparse, hashlib, json, os, pathlib, platform, re, resource, shutil, subprocess, sys, time
root = pathlib.Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True)
parser.add_argument('--cc', default=os.environ.get('CC', 'cc'))
args = parser.parse_args()
out = pathlib.Path(args.output).resolve()
if out == root or root in out.parents or (out.exists() and any(out.iterdir())):
    parser.error('output must be a new empty directory outside the checkout')
out.mkdir(parents=True, exist_ok=True)
rows = []
def snapshot():
    pending = [root/'current_geometry.c', root/'geometry-web/web_bridge.c']
    seen = {}
    while pending:
        path = pending.pop().resolve()
        if path in seen: continue
        data = path.read_bytes()
        seen[path] = hashlib.sha256(data).hexdigest()
        for name in re.findall(rb'#include\s+"([^"]+)"', data):
            pending.append(path.parent/name.decode())
    return {str(p.relative_to(root)): digest for p,digest in seen.items()}
sources = snapshot()
oracle_paths = ['tests/diagnostics/run_fragment_heap_gate.py', 'tests/diagnostics/reference_fragment_stack.py', 'tests/diagnostics/fragment_oom.py', '_ax_r13_anchor_follows.scene']
oracles = {p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in oracle_paths}
def bounded():
    _, hard = resource.getrlimit(resource.RLIMIT_STACK)
    resource.setrlimit(resource.RLIMIT_STACK, (16384*1024, hard))
def run(name, command, timeout=180):
    start = time.monotonic()
    timed_out = False
    error_message = None
    try:
        p = subprocess.run(command, cwd=root, capture_output=True, preexec_fn=bounded, timeout=timeout)
        stdout, stderr, code = p.stdout, p.stderr, p.returncode
    except subprocess.TimeoutExpired as error:
        stdout, stderr, code = error.stdout or b'', error.stderr or b'', 2
        timed_out = True
        error_message = str(error)
    except (OSError, subprocess.SubprocessError) as error:
        stdout, stderr, code = b'', str(error).encode(), 2
        error_message = str(error)
    if isinstance(stdout, str): stdout = stdout.encode()
    if isinstance(stderr, str): stderr = stderr.encode()
    (out/(name+'.stdout')).write_bytes(stdout)
    (out/(name+'.stderr')).write_bytes(stderr)
    rows.append(dict(name=name, command=list(map(str,command)), exit=code, seconds=time.monotonic()-start,
                     timed_out=timed_out, error=error_message))
    (out/'commands.json').write_text(json.dumps(rows, indent=2))
    if code: raise RuntimeError(f'{name} exited {code}; see raw output')
try:
    if platform.system() != 'Linux': raise RuntimeError('This gate requires Linux RLIMIT_STACK')
    _, hard = resource.getrlimit(resource.RLIMIT_STACK)
    if hard != resource.RLIM_INFINITY and hard < 16384*1024:
        raise RuntimeError('ENVIRONMENT BLOCKED: hard stack limit below 16 MiB')
    core, bridge = out/'core', out/'bridge'
    for name, source, binary in [('core-build',root/'current_geometry.c',core),('bridge-build',root/'geometry-web/web_bridge.c',bridge)]:
        run(name,[args.cc,'-std=c11','-O2',str(source),'-lm','-o',str(binary)])
    mirror = out/'fault-source'
    for path in sources:
        target=mirror/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/path,target)
    inc=mirror/'geometry-core/subgrid_rebind.inc'
    data=inc.read_bytes()
    anchor=b'World *candidate=malloc(sizeof *candidate);'
    if data.count(anchor)!=1: raise RuntimeError('fault anchor is missing or ambiguous')
    hook=b'''static void *fragment_fault_malloc(size_t bytes) {
    static unsigned calls;
    const char *value=getenv("FRAGMENT_OOM_AT");
    if (++calls==(value?strtoul(value,NULL,10):0)) return NULL;
    return malloc(bytes);
}
'''
    inc.write_bytes(hook+data.replace(anchor,b'World *candidate=fragment_fault_malloc(sizeof *candidate);'))
    fault=out/'fault-bridge'
    run('fault-build',[args.cc,'-std=c11','-O2',str(mirror/'geometry-web/web_bridge.c'),'-lm','-o',str(fault)])
    run('stack-regression',[sys.executable,str(root/'tests/diagnostics/reference_fragment_stack.py'),str(core),str(bridge)])
    run('oom-regression',[sys.executable,str(root/'tests/diagnostics/fragment_oom.py'),str(fault)])
    if snapshot()!=sources or {p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in oracle_paths}!=oracles:
        raise RuntimeError('product sources or oracle changed during gate')
    result=dict(exit=0, scope='fragment heap Linux stack and two guide OOM cases only', sources=sources,
                oracles=oracles, binaries={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (core,bridge,fault)},
                environment=dict(platform=platform.platform(),python=platform.python_version(),stack=resource.getrlimit(resource.RLIMIT_STACK)), commands=rows)
except Exception as error:
    result=dict(exit=2 if not rows or rows[-1]['exit']==2 else 1,error=str(error),sources=sources,commands=rows)
(out/'receipt.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
sys.exit(result['exit'])
