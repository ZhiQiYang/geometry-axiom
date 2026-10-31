#!/usr/bin/env python3
"""Resume the unchanged P189 timing tail once, after source/exact comparison."""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback

ROOT=Path('/tmp/pr338-b3-p189'); TOOLS=ROOT/'tools'; OUT=ROOT/'formal-v2'; WORK=ROOT/'work-v2'
M='0ae1728c2309e1d670369289a6b8da059fa63a50'
os.environ.update(GEO261_P189_OUT=str(OUT),GEO261_P189_WORK=str(WORK),GEO261_FINAL_REPO='/tmp/r02-ui1')
sys.argv=[str(TOOLS/'p189_verify.original.py'),M]
spec=importlib.util.spec_from_file_location('original_p189',TOOLS/'p189_verify.original.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)

if (OUT/'timing-reuse.json').exists(): raise SystemExit('Refuse second timing attempt')
assert json.loads((OUT/'outer-result.json').read_bytes())['actual_process_returncode']==0
assert json.loads((OUT/'exact-result.json').read_bytes())['exit']==0
provenance=json.loads((OUT/'provenance.json').read_bytes())
for label,expected in provenance['binaries_sha256'].items():
    assert hashlib.sha256((WORK/label/'bridge').read_bytes()).hexdigest()==expected
old.RUN_CAPTURE_INDEX=max(int(p.name) for p in (OUT/'subcommands').iterdir())
source=(TOOLS/'p189_verify.original.py').read_text(); tree=ast.parse(source)
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
start=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='timing' for t in n.targets))
tail=ast.Module(body=fn.body[start:],type_ignores=[])
started=time.time()
record={'source_sha':M,'start_epoch_utc':started,
        'start_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(started)),
        'tail_ast_sha256':hashlib.sha256(ast.dump(tail,include_attributes=False).encode()).hexdigest(),
        'original_driver_sha256':hashlib.sha256((TOOLS/'p189_verify.original.py').read_bytes()).hexdigest(),
        'resume_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'method':'Unmodified original driver AST from timing assignment through final threshold; 36 samples, 3 rounds, all raw values retained; no retry'}
(OUT/'timing-reuse.json').write_text(json.dumps(record,indent=2)+'\n')
print('TIMING_START '+record['start_utc'],flush=True)
env=vars(old).copy();env.update(provenance=provenance,dumps=json.loads((OUT/'dump-equivalence.json').read_bytes()),started=started)
code=0
try:
    exec(compile(tail,str(TOOLS/'p189_verify.original.py')+'::unchanged_timing_tail','exec'),env)
except BaseException as error:
    code=error.code if isinstance(error,SystemExit) and isinstance(error.code,int) else 1
    traceback.print_exc()
finally:
    record.update(actual_process_returncode=code,ended_epoch_utc=time.time(),seconds=time.time()-started)
    (OUT/'timing-outer-result.json').write_text(json.dumps(record,indent=2)+'\n')
raise SystemExit(code)
