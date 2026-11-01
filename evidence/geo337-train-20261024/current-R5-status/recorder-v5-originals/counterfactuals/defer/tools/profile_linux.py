import gzip,json,resource,subprocess,os
from geo323_record import recorded_run
from pathlib import Path
root=Path(os.environ['GEO323_ROOT']);out=Path(os.environ['GEO323_EVIDENCE']);checks=out/'checks'
soft,hard=resource.getrlimit(resource.RLIMIT_STACK)
if hard!=resource.RLIM_INFINITY and hard<16777216:raise RuntimeError("環境 hard stack 小於16MiB")
resource.setrlimit(resource.RLIMIT_STACK,(16777216,hard))
for version in ['base','fix']:
    exe=Path(os.environ['GEO323_WORK'])/(version+'-pg')/'bridge'
    for n in [32,64]:
        work=(Path(os.environ['GEO323_WORK'])/'profile')/f'{version}-{n}';work.mkdir(parents=True,exist_ok=True)
        stdin=f'loadfile {out / "scenes" / f"s{n}.scene"}\n'.encode()
        for step,command,inp in [('load',[str(exe)],stdin),('gprof',['gprof',str(exe),str(work/'gmon.out')],None)]:
            r=recorded_run(command,input=inp,cwd=work,capture_output=True)
            name=f'profile-{version}-{n}-{step}'
            (checks/(name+'.stdout')).write_bytes(r.stdout);(checks/(name+'.stderr')).write_bytes(r.stderr)
            (checks/(name+'.json')).write_text(json.dumps({'command':command,'stdin':inp.decode() if inp else None,'cwd':str(work),'stack_bytes':16777216,'exit':r.returncode},indent=2))
            assert r.returncode==0,(name,r.stderr)
            if step=='load':assert json.loads(r.stdout)['ok']
            else:
                p=out/f'gprof-{version}-{n}.stdout'
                p.write_bytes(r.stdout)
        (out/f'gmon-{version}-{n}.gz').write_bytes(gzip.compress((work/'gmon.out').read_bytes(),mtime=0))
        print(version,n,'load=0 gprof=0',flush=True)
