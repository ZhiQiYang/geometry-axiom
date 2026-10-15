"""Run real compiled CR mutants and recompile each byte-restored control.

Outputs go to a new directory outside the checkout. No compiler/launch failure,
timeout, crash, unittest error or skip counts as killed. Stop at the first bad
proof; raw compiler output, test output and hashes remain available.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import re
import subprocess
import sys
import time
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(Path(__file__).parent))
from mutations import MUTATIONS


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def execute(command, directory, label, *, env=None):
    start=time.monotonic()
    result=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=180)
    (directory/(label+'.stdout')).write_bytes(result.stdout)
    (directory/(label+'.stderr')).write_bytes(result.stderr)
    record={'command':command,'exit_code':result.returncode,'seconds':time.monotonic()-start}
    (directory/(label+'.command.json')).write_text(json.dumps(record,indent=2)+'\n')
    return record


def compile_binary(directory, name):
    source=ROOT/('geometry-web/web_bridge.c' if name=='bridge' else 'geometry-core/model_base.c')
    binary=directory/name
    result=execute(['cc','-std=c11','-O0',str(source),'-lm','-o',str(binary)],directory,'compile-'+name)
    if result['exit_code']:
        raise RuntimeError('compiler failure: '+str(directory/('compile-'+name)))
    return binary


def child(args):
    from tests import _bridge
    from tests.test_grid_card_reference import GridCardReference
    os.environ['GEOMETRY_MODEL_BASE']=str(args.model)
    # Explicit, freshly instrumented binaries have their own source/binary hashes
    # in this runner's receipt; do not forge an official binaries.py sidecar.
    with mock.patch.object(_bridge,'find_bridge',return_value=str(args.bridge)):
        names=unittest.defaultTestLoader.getTestCaseNames(GridCardReference)
        names=[name for name in names if args.case=='all' or name.startswith('test_'+args.case+'_')]
        if not names: raise RuntimeError('no named CR selected: '+args.case)
        result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(GridCardReference(name) for name in names))
    record={'testsRun':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
            'skips':len(result.skipped),'failure_names':[str(test) for test,trace in result.failures],
            'compile_failures':sum('compile_result.returncode' in trace for test,trace in result.failures),
            'infrastructure_failures':sum(any(int(code)!=1 for code in re.findall(r'0 != (-?\d+) : CANDIDATE_LIFECYCLE injection:',trace)) for test,trace in result.failures)}
    args.result.write_text(json.dumps(record,indent=2)+'\n')
    return 0 if result.wasSuccessful() else 1


def test_case(directory, bridge, model, case):
    path=directory/'tests.json'
    run=execute([sys.executable,str(Path(__file__).resolve()),'--child','--bridge',str(bridge),'--model',str(model),
                 '--case',case,'--result',str(path)],directory,'test')
    if not path.exists(): raise RuntimeError('test process did not emit counts: '+str(directory))
    return run,json.loads(path.read_text())


def main(args):
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    selected=[m for m in MUTATIONS if not args.only or m['id'] in args.only]
    files={p['path'] for m in selected for p in m['patches']}
    originals={path:(ROOT/path).read_bytes() for path in files}
    # Mechanical exact-match preflight before any source is changed or compiled.
    for m in selected:
        current={p:originals[p].decode().replace('\r\n','\n') for p in originals}
        for p in m['patches']:
            count=current[p['path']].count(p['old'])
            if count!=1: raise RuntimeError(f"{m['id']} exact patch count={count}: {p['path']} {p['old']}")
            current[p['path']]=current[p['path']].replace(p['old'],p['new'],1)
    baseline=out/'baseline';baseline.mkdir()
    bridge=compile_binary(baseline,'bridge');model=compile_binary(baseline,'model')
    run,counts=test_case(baseline,bridge,model,'all')
    if run['exit_code'] or counts['testsRun']!=36 or counts['skips']:
        raise RuntimeError('instrumented full baseline is not green')
    report={'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'test_sha256':sha(ROOT/'tests/test_grid_card_reference.py'),'runner_sha256':sha(__file__),
            'confirmation_probe_sha256':sha(Path(__file__).with_name('confirmation_probe.c')),
            'table_sha256':sha(Path(__file__).with_name('mutations.py')),
            'source_sha256':{p:hashlib.sha256(b).hexdigest() for p,b in originals.items()},
            'baseline':{'run':run,'counts':counts,'bridge_sha256':sha(bridge),'model_sha256':sha(model)},'mutants':[]}
    try:
        for m in selected:
            directory=out/m['id'];directory.mkdir()
            current={p:originals[p].decode().replace('\r\n','\n') for p in originals}
            for p in m['patches']: current[p['path']]=current[p['path']].replace(p['old'],p['new'],1)
            receipt={'id':m['id'],'case':m['case'],'patches':m['patches']}
            try:
                for path in {p['path'] for p in m['patches']}:
                    text=current[path];data=text.replace('\n','\r\n').encode() if b'\r\n' in originals[path] else text.encode()
                    (ROOT/path).write_bytes(data)
                receipt['mutated_source_sha256']={p:sha(ROOT/p) for p in files}
                mutant_bridge=compile_binary(directory,'bridge')
                mutant_model=compile_binary(directory,'model') if m['model'] else model
                receipt['binary_sha256']=sha(mutant_bridge);receipt['model_sha256']=sha(mutant_model)
                run,counts=test_case(directory,mutant_bridge,mutant_model,m['case'])
                receipt['red']={'run':run,'counts':counts}
                receipt['verdict']='killed' if run['exit_code']==1 and counts['failures']>0 and counts['errors']==0 and counts['skips']==0 and counts['compile_failures']==0 and counts['infrastructure_failures']==0 else 'NOT_KILLED'
            finally:
                for path,data in originals.items(): (ROOT/path).write_bytes(data)
                if any((ROOT/p).read_bytes()!=data for p,data in originals.items()): raise RuntimeError('byte restoration failed')
            restored=directory/'restored';restored.mkdir()
            restored_bridge=compile_binary(restored,'bridge')
            restored_model=compile_binary(restored,'model') if m['model'] else model
            run,counts=test_case(restored,restored_bridge,restored_model,m['case'])
            receipt['restored']={'run':run,'counts':counts,'bridge_sha256':sha(restored_bridge),'model_sha256':sha(restored_model)}
            report['mutants'].append(receipt)
            (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
            print(m['id'],receipt['verdict'],'restore',run['exit_code'],flush=True)
            if receipt['verdict']!='killed' or run['exit_code'] or counts['skips']: return 1
    finally:
        for path,data in originals.items(): (ROOT/path).write_bytes(data)
    print('All',len(selected),'actual mutants killed; each control recompiled and green.',flush=True)
    return 0


if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_STACK,(16*1024*1024,resource.getrlimit(resource.RLIMIT_STACK)[1]))
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path);parser.add_argument('--only',nargs='*')
    parser.add_argument('--child',action='store_true');parser.add_argument('--bridge',type=Path);parser.add_argument('--model',type=Path)
    parser.add_argument('--case',default='all');parser.add_argument('--result',type=Path)
    args=parser.parse_args()
    raise SystemExit(child(args) if args.child else main(args))
