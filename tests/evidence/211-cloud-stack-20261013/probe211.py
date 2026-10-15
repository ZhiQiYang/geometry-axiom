import json, os, pathlib, resource, subprocess, time
root=pathlib.Path('/workspace/scratch/860de1a99063/geometry-axiom')
out=pathlib.Path('/tmp/geometry211-evidence'); out.mkdir(exist_ok=True)
def run(name,limit,cmd):
    def bounds(): resource.setrlimit(resource.RLIMIT_STACK,(limit*1024,resource.RLIM_INFINITY))
    start=time.monotonic(); p=subprocess.run(cmd,cwd=root,capture_output=True,preexec_fn=bounds)
    (out/(name+'.stdout')).write_bytes(p.stdout); (out/(name+'.stderr')).write_bytes(p.stderr)
    return dict(name=name,stack_kib=limit,command=cmd,exit=p.returncode,seconds=time.monotonic()-start,stdout_bytes=len(p.stdout),stderr_bytes=len(p.stderr))
rows=[]
for limit in (8192,16384):
    rows.append(run('model'+str(limit),limit,['/tmp/geometry211-model','211-stagger-source8.scene']))
for limit in range(8192,9217,64):
    for repeat in range(3): rows.append(run('boundary-'+str(limit)+'-'+str(repeat),limit,['/tmp/geometry211-core','--scene','subgrid-local.scene','--no-window','--out','/tmp/geometry211-boundary.svg']))
(out/'probe.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows,indent=2))
