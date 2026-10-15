"""Actual CLI comparison; keeps each input, raw copy, receipt and OS exit."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path('/tmp/geometry-209-segments')
out = Path('/tmp/geometry-wake38/collector-matrix')
out.mkdir(exist_ok=True)
feedback = out / 'writer-feedback'
spec = importlib.util.spec_from_file_location('matrix_writer', root / 'geometry-web/wait_trace.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
writer = module.Writer(str(feedback), run_id='b1-real-writer-run')
for stage in ('request_begin', 'bridge_lock_release', 'request_end'):
    assert writer.submit(dict(stage=stage, traceRequestId='b1-request'))
assert writer.close()
original = (feedback / 'wait-trace.jsonl').read_bytes()
rows = [json.loads(line) for line in original.splitlines()]
assert len(rows) == 5 and rows[-1]['acceptedEvents'] == 3 and rows[-1]['writtenEvents'] == 4
keys = ('acceptedEvents', 'writtenEvents', 'droppedEvents', 'writeErrors')
cases = [('real-writer-complete', rows, True)]
lost = [row for row in rows[:-1] if row['stage'] != 'bridge_lock_release']
cases.append(('lost-release-counts-present', lost + [rows[-1]], False))
for stem, prefix in [('complete', rows[:-1]), ('lost-release', lost)]:
    for omit in (keys, ('acceptedEvents', 'writtenEvents')):
        marker = {k: v for k,v in rows[-1].items() if k not in omit}
        cases.append((stem+'-missing-'+('-'.join(omit)), prefix+[marker], False))
for key in keys:
    marker = dict(rows[-1]); del marker[key]
    cases.append(('missing-'+key, rows[:-1]+[marker], False))
    for tag, value in [('float',float(rows[-1][key])),('string',str(rows[-1][key])),('null',None),('negative',-1)]:
        cases.append((key+'-'+tag, rows[:-1]+[dict(rows[-1],**{key:value})], False))
    base = rows if key in ('droppedEvents','writeErrors') else [rows[0],dict(rows[-1],acceptedEvents=0,writtenEvents=1)]
    value = key == 'writtenEvents'
    cases.append((key+'-boolean', base[:-1]+[dict(base[-1],**{key:value})], False))

old = out / 'original-collector.py'
old.write_bytes(subprocess.check_output(['git','show','8030d343:geometry-web/archive_wait_trace.py'],cwd=root))
summary = []
for name, changed, expected in cases:
    directory = out / name; directory.mkdir(exist_ok=True)
    source = directory / 'source'; source.mkdir(exist_ok=True)
    raw = original if expected else ''.join(json.dumps(row)+'\n' for row in changed).encode()
    (source/'wait-trace.jsonl').write_bytes(raw)
    env = dict(os.environ, GEOMETRY_WAIT_TRACE='1', GEOMETRY_FEEDBACK_DIR=str(source),
               GEOMETRY_BROWSER_SUITE='canvas',GEOMETRY_WAIT_TRACE_RUN_ID=writer.run_id)
    record = dict(case=name, expectedFixedExit=0 if expected else 1, inputSha256=hashlib.sha256(raw).hexdigest())
    for variant, script in [('original',old),('fixed',root/'geometry-web/archive_wait_trace.py')]:
        target = directory / variant
        run = subprocess.run([sys.executable,str(script),str(target)],cwd=root,env=env,capture_output=True)
        target.joinpath('stdout').write_bytes(run.stdout); target.joinpath('stderr').write_bytes(run.stderr)
        receipt = json.loads(target.joinpath('receipt.json').read_text())
        assert target.joinpath('wait-trace.jsonl').read_bytes() == raw
        record[variant] = dict(exit=run.returncode,status=receipt['status'],collectorSha256=hashlib.sha256(script.read_bytes()).hexdigest())
    assert record['fixed']['exit'] == record['expectedFixedExit'], record
    summary.append(record)
(out/'matrix.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(dict(cases=len(summary),fixedCorrect=len(summary),originalWrong=sum(r['original']['exit']!=r['expectedFixedExit'] for r in summary))))
