#!/usr/bin/env python3
"""Current-source P-189 only; original R8 timing is not rerun or edited."""
from __future__ import annotations
import ast
import csv
import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import statistics
import subprocess
import sys
import tarfile
import time
import traceback
from types import SimpleNamespace
from exact_p189 import POLICY, compare

ROOT = Path('/tmp/pr338-b3-p189')
TOOLS = ROOT / 'tools'
OUT = ROOT / 'formal-v2'
WORK = ROOT / 'work-v2'
REPO = '/tmp/r02-ui1'
M = '0ae1728c2309e1d670369289a6b8da059fa63a50'
F = 'cbf0fb621888596aa14ad5f2349b503e23b1b72d'
L = '7af8c5d80d34cb4f49d01ba67deb78a3a6d725db'
SHAS = {'main': 'adbaebf9c73ea6801d7b4d5214e4b846b132923b',
        'base': '3e600772076465fc65a26ac09055028301c0fb0b', 'fix': M}
ELF = {
    'main': (673216, '8f9b8ed6498986d33b6789d2839761d3b9814d91782a0ad2e98f6f4eda08c045'),
    'base': (1100248, 'b8c16ffceee42f33c6452d91942473ad84af6d71d1fe5307f824819d4821212f'),
}
ENV = dict(os.environ, PATH='/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
           LANG='C.UTF-8', LC_ALL='C.UTF-8', PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1')
GEN = TOOLS / 'gen_scene.py'
def digest(data): return hashlib.sha256(data).hexdigest()
def write(name, value): (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
def copy_result(p, **kw):
    return SimpleNamespace(stdout=kw.get('stdout',p.stdout), stderr=kw.get('stderr',p.stderr), returncode=kw.get('returncode',p.returncode))

def main():
    if OUT.exists() or WORK.exists():
        raise RuntimeError('Refuse to overwrite any previous receipt or work tree')
    OUT.mkdir(); WORK.mkdir()
    os.environ.update(GEO261_P189_OUT=str(OUT), GEO261_P189_WORK=str(WORK), GEO261_FINAL_REPO=REPO)
    sys.argv = [str(TOOLS/'p189_verify.original.py'), M]
    spec = importlib.util.spec_from_file_location('original_p189', TOOLS/'p189_verify.original.py')
    old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
    run = old.run
    def git(*args): return run(['git','-c','safe.directory=*','-C',REPO,*args]).stdout
    started = time.time()
    write('environment.json', {'utc_epoch':started,'uname':platform.uname()._asdict(),
          'python':sys.version,'available_tmp_bytes':shutil.disk_usage(ROOT).free,
          'filesystem':run(['df','-B1',str(ROOT),'/workspace']).stdout.decode(),
          'process_snapshot':run(['ps','-eo','pid,ppid,etimes,args']).stdout.decode(),
          'source_sha':M,'product_F':F,'method':'original P189 three-way timing; no R8 resampling'})
    assert shutil.disk_usage(ROOT).free > 256*1024*1024
    provenance={'shas':SHAS,'execution_sha':M,'product_F':F,'old_timing_execution_sha':L,
       'compiler':run(['gcc','--version']).stdout.decode().splitlines()[0],
       'binaries_sha256':{},'generator_sha256':digest(GEN.read_bytes()),
       'timing_script_sha256':digest((TOOLS/'scale_compare2.py').read_bytes()),
       'original_driver_sha256':digest((TOOLS/'p189_verify.original.py').read_bytes()),
       'new_driver_sha256':digest(Path(__file__).read_bytes()),
       'comparator_sha256':digest((TOOLS/'exact_p189.py').read_bytes())}
    prior_path=Path('/workspace/g337p189L/measurement/provenance.json')
    prior_bytes=prior_path.read_bytes(); prior=json.loads(prior_bytes)
    (OUT/'original-L-provenance.json').write_bytes(prior_bytes)
    assert provenance['generator_sha256']==prior['generator_sha256']
    assert provenance['timing_script_sha256']==prior['timing_script_sha256']
    assert provenance['original_driver_sha256']==prior['verification_script_sha256']
    for label,sha in SHAS.items():
        assert git('rev-parse',sha).decode().strip()==sha
        target=WORK/label; target.mkdir()
        if label != 'fix':
            source=Path('/workspace/g337p189L/work')/label/'bridge'
            before=source.stat(); body=source.read_bytes(); expected_bytes,expected_hash=ELF[label]
            assert len(body)==expected_bytes and digest(body)==expected_hash
            assert prior['shas'][label]==sha and prior['binaries_sha256'][label]==expected_hash
            assert before.st_mode & 0o777 == 0o700
            shutil.copy2(source,target/'bridge')
            assert (target/'bridge').read_bytes()==body and (target/'bridge').stat().st_mode&0o777==0o700
            after=source.stat()
            assert (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
            reference_checks=[]
            for item in prior['reference_raw_files']:
                if item['source_sha']!=sha: continue
                stored=Path(item['stored_file']).read_bytes(); raw=gzip.decompress(stored)
                assert digest(stored)==item['stored_sha256'] and len(stored)==item['stored_bytes']
                assert digest(raw)==item['raw_sha256'] and len(raw)==item['raw_bytes']
                reference_checks.append(item)
            provenance.setdefault('reference_builds',{})[label]={
                'source_sha':sha,'original_elf_path':str(source),'bytes':len(body),'mode':'0700',
                'sha256':expected_hash,'recompiled':False,'original_provenance_sha256':digest(prior_bytes),
                'original_raw_build_provenance_verified':reference_checks,
                'published_M_path':'evidence/geo337-train-20261024/final-L-performance-complete/p189/ORIGINAL_PERFORMANCE_LOGS_REPORTS_AND_ELF_HASHES.tar.gz'}
            provenance['binaries_sha256'][label]=expected_hash
            print(f'{label}: original pinned ELF copied and provenance verified',flush=True)
        else:
            # The original archive command encountered a promisor fetch ENOSPC before
            # any compile/sample. Reuse the already materialized M checkout instead.
            # gcc gives the full include closure; every private byte must match M's
            # Git blob, independent of this other checkout's branch/working state.
            donor=Path('/tmp/pr338-unblock')
            donor_deps=run(['gcc','-std=c11','-O2','-MM','geometry-web/web_bridge.c'],cwd=donor).stdout
            donor_names=shlex.split(donor_deps.decode().replace('\\\n',' '))[1:]
            tree={}
            for row in git('ls-tree','-rz',M,'--','current_geometry.c','geometry-core','geometry-app','geometry-templates','geometry-web').split(b'\0'):
                if not row: continue
                metadata,path=row.split(b'\t',1); mode,kind,blob=metadata.decode().split()
                if kind=='blob': tree[path.decode()]=(mode,blob)
            manifest=[]
            for name in sorted(set(str((donor/n).resolve().relative_to(donor)) for n in donor_names)):
                source=donor/name; before=source.stat(); body=source.read_bytes()
                mode,blob=tree[name]
                assert hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==blob,(name,'dirty donor')
                destination=target/name; destination.parent.mkdir(parents=True,exist_ok=True)
                destination.write_bytes(body); destination.chmod(int(mode,8)&0o777)
                after=source.stat(); assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
                manifest.append({'path':name,'bytes':len(body),'sha256':digest(body),'git_blob':blob,'git_mode':mode})
            write('archive-closure.json',{'source_sha':sha,'method':'Exact Git-verified compiler input copies, no source mutation; archive attempt 1 failed before compilation',
                                        'donor':str(donor),'files':manifest})
            deps=run(['gcc','-std=c11','-O2','-MM','geometry-web/web_bridge.c'],cwd=target).stdout
            names=shlex.split(deps.decode().replace('\\\n',' '))[1:]
            closure=[]
            for name in names:
                p=(target/name).resolve(); rel=str(p.relative_to(target))
                closure.append({'path':rel,'sha256':digest(p.read_bytes()),'bytes':p.stat().st_size})
            changed=git('diff','--name-only',L,M,'--',*[r['path'] for r in closure]).decode().splitlines()
            assert changed, 'A rerun needs actual timing input changes, not evidence-only changes'
            actual_diff=git('diff',L,M,'--',*changed)
            (OUT/'L-to-M-actual-build-input.diff').write_bytes(actual_diff)
            write('build-closure.json',{'execution_sha':M,'old_timing_sha':L,'compiler_generated_dependencies':closure,
                'changed_inputs_since_L':changed,'rerun_reason':'Only published P189 timing is L; real compiler input changed.',
                'M_vs_F_non_evidence_diff':git('diff','--name-only',F,M,'--',':(exclude)evidence').decode().splitlines()})
            p=run(['gcc','-std=c11','-O2','geometry-web/web_bridge.c','-o','bridge','-lm'],cwd=target)
            (OUT/'build-fix.log').write_bytes(p.stdout+p.stderr)
            provenance['binaries_sha256'][label]=digest((target/'bridge').read_bytes())
            print(f'fix: {M} built; {len(changed)} actual build inputs changed since L',flush=True)
    write('provenance.json',provenance)
    scenes=[]
    for n in (16,32,48,64):
        scenes.append((f's{n}.scene',run(['python3',str(GEN),str(n),'--family','single']).stdout))
    for name in git('ls-tree','-z','--name-only',SHAS['base']).decode().split('\0'):
        if name.endswith('.scene'): scenes.append((name,git('show',SHAS['base']+':'+name)))
    pinned={name:digest(data) for name,data in scenes}
    assert set(POLICY)<=set(pinned)
    write('scene-inventory.json',{'scene_source_sha':SHAS['base'],'generator_sha256':provenance['generator_sha256'],
         'count':len(scenes),'scenes':[{'name':name,'bytes':len(data),'sha256':digest(data)} for name,data in scenes]})
    dumps=[]; strict_red=[]; failures=[]; controls=[]
    for name,data in scenes:
        scene=WORK/name; scene.write_bytes(data); results={}
        for label in SHAS:
            p=run(['bash','-c','ulimit -s 16384; exec "$1"','x',str(WORK/label/'bridge')],
                  cwd=WORK,data=f'loadfile {scene}\ndump\n'.encode(),timeout=900)
            results[label]=p
            lines=p.stdout.splitlines(); assert len(lines)==2,(name,label,len(lines))
            parsed=[json.loads(x) for x in lines]
            assert all(isinstance(x,dict) for x in parsed)
            assert isinstance(parsed[0].get('ok'),bool) and parsed[1].get('ok') is True
            if name in ('s16.scene','s32.scene','s48.scene','s64.scene'): assert parsed[0]['ok'] is True
        outcomes={}
        for reference in ('main','base'):
            a=results[reference]; b=results['fix']
            strict=a.stdout==b.stdout and a.stderr==b.stderr and a.returncode==b.returncode
            if not strict: strict_red.append({'scene':name,'reference':reference,'stdout_equal':a.stdout==b.stdout,'stderr_equal':a.stderr==b.stderr})
            ok,reason=compare(name,scene,a,b,pinned[name],pinned)
            outcomes[reference]={'passed':ok,'reason':reason,'strict_equal':strict}
            if not ok: failures.append({'scene':name,'reference':reference,'reason':reason})
        dumps.append({'scene':name,'sha256':pinned[name],'comparisons':outcomes,'load_ok':parsed[0]['ok'],
                      'stdout_sha256':{k:digest(v.stdout) for k,v in results.items()},
                      'stderr_sha256':{k:digest(v.stderr) for k,v in results.items()}})
        if name in POLICY:
            a=results['main']; b=results['fix']; suffix=POLICY[name][2].encode()
            cases={
                'wrong_text':copy_result(b,stdout=b.stdout.replace(suffix,suffix+b'!',1)),
                'wrong_position':copy_result(b,stdout=b.stdout.replace(suffix,b'',1)+suffix),
                'fourth_difference':copy_result(b,stdout=b.stdout+b'\n'),
                'other_dump_byte':copy_result(b,stdout=b.stdout.replace(b'"revision":',b'"revisioN":',1)),
                'returncode':copy_result(b,returncode=1),
                'stderr_wrong_text':copy_result(b,stderr=b.stderr.replace(suffix,suffix+b'!',1)),
                'stderr_wrong_position':copy_result(b,stderr=suffix+b.stderr.replace(suffix,b'',1)),
            }
            for control,mutant in cases.items():
                killed,why=compare(name,scene,a,mutant,pinned[name],pinned)
                controls.append({'scene':name,'control':control,'comparator_exit':0 if killed else 1,'reason':why})
                assert not killed,(name,control,'survived')
            ok,why=compare(name,scene,a,b,'0'*64,pinned)
            controls.append({'scene':name,'control':'scene_input_changed','comparator_exit':0 if ok else 1,'reason':why})
            assert not ok
            ok,why=compare('fourth-unlisted.scene',scene,a,b,pinned[name],pinned)
            controls.append({'scene':name,'control':'fourth_unlisted_scene','comparator_exit':0 if ok else 1,'reason':why})
            assert not ok
        print(f'exact {name}: {outcomes}',flush=True)
    write('dump-equivalence.json',dumps)
    write('strict-original-policy-red.json',{'exit':1 if strict_red else 0,'differences':strict_red,'preserved':True})
    write('negative-controls.json',{'count':len(controls),'results':controls,'exit':0})
    expected={(name,ref) for name in POLICY for ref in ('main','base')}
    assert {(r['scene'],r['reference']) for r in strict_red}==expected,strict_red
    write('exact-result.json',{'exit':1 if failures else 0,'failures':failures,'scenes':len(scenes),'executions':len(scenes)*3,
        'required_main_comparisons':len(scenes),'additional_historical_base_comparisons':len(scenes),
        'allowed_exact_scene_names':list(POLICY),'controls':len(controls),'execution_sha':M})
    if os.environ.get('GEO_P189_COMPARE_ONLY')=='1':
        print('COMPARE_COMPLETE; timing not started pending exclusive window',flush=True)
        if failures: raise SystemExit(1)
        return
    # Keep the timing command, sample validation and medians exactly as the original driver.
    # Only binding changes: explicit current source M, fresh OUT/WORK, already verified dumps.
    source=(TOOLS/'p189_verify.original.py').read_text(); tree=ast.parse(source)
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    start=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='timing' for t in n.targets))
    tail=ast.Module(body=fn.body[start:],type_ignores=[])
    write('timing-reuse.json',{'original_driver_sha256':provenance['original_driver_sha256'],
         'tail_ast_sha256':digest(ast.dump(tail,include_attributes=False).encode()),
         'method':'Unmodified original timing command, 36 samples, median of original four-decimal samples.tsv, fix/main <= 2; no retry or discarded samples.',
         'start_epoch_utc':time.time(),'source_sha':M})
    print('TIMING_START '+time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),flush=True)
    env=vars(old).copy(); env.update(run=run,provenance=provenance,dumps=dumps,started=started)
    exec(compile(tail,str(TOOLS/'p189_verify.original.py')+'::unchanged_timing_tail','exec'),env)
    receipt=json.loads((OUT/'receipt.json').read_bytes())
    receipt.update(exact_comparison_passed=not failures,strict_original_policy_passed=not strict_red,
                   negative_controls_passed=True,overall_pass=receipt['pass'] and not failures)
    write('receipt.json',receipt)
    if failures: raise SystemExit(1)

if __name__=='__main__':
    began=time.time(); code=0
    try: main()
    except BaseException as error:
        code=error.code if isinstance(error,SystemExit) and isinstance(error.code,int) else 1
        traceback.print_exc()
    finally:
        if OUT.exists(): write('outer-result.json',{'actual_process_returncode':code,'started_epoch_utc':began,
                            'ended_epoch_utc':time.time(),'seconds':time.time()-began,'execution_sha':M})
    raise SystemExit(code)
