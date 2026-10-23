"""Targeted 0/1/0 for the reviewed nonempty current golden witness.

This runs only when explicitly invoked in a formal resource slot. It never edits
repository source or regenerates the repository golden/ledger. Each child uses
an isolated copy of the actual oracle and generator. The withdrawal restores
the old STEP20 witness geometry, retaining all original nonempty assertions.
This targeted proof does not replace the full oracle self-test or 64-layout
comparison. Its empty rooms input still exercises the generator's three EXTRA
rooms plus its separate witness, with the original params.
"""
from __future__ import annotations
import argparse
import ast
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

SOURCE = ('FZ120_WITNESS = {"outer": [[0, 0], [4100, 0], [4100, 3672], '
          '[1450, 3672], [1450, 3720], [1000, 3720], [1000, 3675], [0, 3675]]}')
WITHDRAWN = ('FZ120_WITNESS = {"outer": [[0, 0], [4100, 0], [4100, 3680], '
             '[2600, 3680], [2600, 3700], [0, 3700]]}')
NONEMPTY = 'assert len(witness_rows) == 1 and witness_rows[0]["core_limits"], witness_rows'
MARKER = 'ASSERT:golden-current-witness-nonempty'
CHILD = r'''
import importlib.util,json,pathlib,sys,traceback
root=pathlib.Path(sys.argv[1]); spec_path=pathlib.Path(sys.argv[2]);golden_path=pathlib.Path(sys.argv[3])
sys.path.insert(0,str(root))
spec=importlib.util.spec_from_file_location("make_golden",root/"make_golden.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
params=json.loads(spec_path.read_text(encoding="utf-8"))["params"]
try:
    now=m.snapshot({"params":params,"rooms":{}})
except AssertionError as e:
    frames=traceback.extract_tb(e.__traceback__)
    last=frames[-1]
    if pathlib.Path(last.filename)==root/"make_golden.py" and last.line==sys.argv[4]:
        print("ASSERT:golden-current-witness-nonempty",flush=True)
        traceback.print_exc()
        sys.exit(1)
    raise
expected=json.loads(golden_path.read_text(encoding="utf-8"))["core_limit_witness"]
actual=now["core_limit_witness"]
assert actual==expected,("golden witness differs",actual,expected)
rows=actual["layouts"]
assert len(rows)==1 and rows[0]["core_limits"],"nonempty current witness"
want=["CORE_LIMIT_EXTENSION_END_FREE",1,1000,[1000,3645,4100,3672]]
assert rows[0]["core_limits"]==[want],"exact I22 tuple"
rects=[r[1] for r in rows[0]["timbers"]]
assert want[3] in rects and rects[want[1]]!=want[3],"construction id is not sorted index"
print("PASS:current-nonempty-I22-golden-witness; targeted only, not full64")
'''


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',required=True,type=Path)
    ap.add_argument('--sha',required=True)
    ap.add_argument('--output',required=True,type=Path)
    args=ap.parse_args()
    root=args.root.resolve(); out=args.output.resolve()
    if out==root or root in out.parents:
        ap.error('--output must be outside the repository')
    source=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    if source!=args.sha:
        ap.error('--sha must equal the actual checkout HEAD')
    dirty=subprocess.check_output(['git','-C',str(root),'status','--porcelain'],text=True)
    if dirty:
        ap.error('source checkout must be clean')
    out.mkdir(parents=True,exist_ok=False)
    oracle=root/'geometry-core/framing-template/oracle'
    raws={name:(oracle/name).read_bytes() for name in ('framing_oracle.py','make_golden.py')}
    text=raws['make_golden.py'].decode('utf-8')
    if text.count(SOURCE)!=1 or text.count(NONEMPTY)!=1:
        ap.error('source-control anchors must each occur exactly once')
    withdrawn=text.replace(SOURCE,WITHDRAWN).encode('utf-8')
    ast.parse(withdrawn)
    records=[]
    result={'scope':'Targeted golden witness source withdrawal, not full self-test or room scan',
            'source_sha':source,'source_dirty':dirty,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'driver_sha256':digest(Path(__file__).read_bytes()),
            'environment':{'platform':platform.platform(),'python':sys.version,
                           **{k:os.environ.get(k) for k in ('LANG','LC_ALL','PYTHONDONTWRITEBYTECODE','GITHUB_SHA')}},
            'source_sha256':{k:digest(v) for k,v in raws.items()},
            'commands':records}
    for label, generator in [('baseline',raws['make_golden.py']),('withdrawn',withdrawn),('restored',raws['make_golden.py'])]:
        variant=out/label; variant.mkdir()
        for name,raw in raws.items():
            (variant/name).write_bytes(generator if name=='make_golden.py' else raw)
        argv=[sys.executable,'-B','-c',CHILD,str(variant),str(oracle/'rooms.json'),str(oracle/'oracle-golden.json'),NONEMPTY]
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
        try:
            p=subprocess.run(argv,cwd=variant,env=env,text=True,capture_output=True,timeout=45)
            rc,stdout,stderr=p.returncode,p.stdout,p.stderr
        except subprocess.TimeoutExpired as e:
            rc=124;stdout=(e.stdout or b'');stderr=(e.stderr or b'')
            if isinstance(stdout,bytes):stdout=stdout.decode('utf-8','replace')
            if isinstance(stderr,bytes):stderr=stderr.decode('utf-8','replace')
        (variant/'stdout.txt').write_text(stdout)
        (variant/'stderr.txt').write_text(stderr)
        records.append({'variant':label,'argv':argv,'cwd':str(variant),'exit_code':rc,
                        'stdout':stdout,'stderr':stderr,
                        'compiled_source':False,'generator_sha256':digest(generator),
                        'oracle_sha256':digest(raws['framing_oracle.py'])})
        (out/'receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    result['passed']=(records[0]['exit_code']==0 and records[1]['exit_code']==1
                      and MARKER in records[1]['stdout'] and records[2]['exit_code']==0)
    result['source_bytes_unchanged']=all((oracle/k).read_bytes()==v for k,v in raws.items())
    result['passed'] &= result['source_bytes_unchanged']
    (out/'receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'source_sha':source,'exits':[r['exit_code'] for r in records],
                      'passed':result['passed'],'output':str(out)},ensure_ascii=False))
    return 0 if result['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
