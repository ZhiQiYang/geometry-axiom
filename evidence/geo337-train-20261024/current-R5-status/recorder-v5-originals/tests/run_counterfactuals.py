"""Withdraw each external recorder fix in isolated copies; never run product."""
from pathlib import Path
import hashlib, json, os, subprocess, sys, time

P=Path(__file__).resolve().parents[1]
O=P/'counterfactuals-r2';O.mkdir(exist_ok=False)
files=sorted(x for x in (P/'tools-v5').iterdir() if x.is_file())
pins={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in files}
file_destination='''import tempfile
def _legacy_file_run(command, **kwargs):
    kwargs.pop('capture_output')
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        result = subprocess.run(command, stdout=stdout, stderr=stderr, **kwargs)
        stdout.seek(0); stderr.seek(0)
        result.stdout = stdout.read(); result.stderr = stderr.read()
        return result
_ORIGINAL_RUN = _legacy_file_run'''
definitions=[('pipe','geo323_record.py','_ORIGINAL_RUN = subprocess.run',file_destination,
              'AssertionError: recorded child stdout/stderr remain original PIPE'),
             ('defer','run.py','        with self.r.defer_flush():\n            self.v.perf(self.a.repo, self.work, self.evidence)',
              '        self.v.perf(self.a.repo, self.work, self.evidence)',
              'AssertionError: no recorder disk serialization inside original perf')]
allrows=[]
for scope,leaf,before,after,expected_assertion in definitions:
    root=O/scope;root.mkdir();tools=root/'tools';tools.mkdir()
    for path in files:(tools/path.name).write_bytes(path.read_bytes())
    fixed=(tools/leaf).read_text();assert fixed.count(before)==1
    withdrawn=fixed.replace(before,after)
    rows=[]
    for phase,body,expected in [('fixed',fixed,0),('withdrawn',withdrawn,1),('restored',fixed,0)]:
        (tools/leaf).write_text(body);(root/(phase+'-'+leaf+'.txt')).write_text(body)
        outer=root/(phase+'-launch');outer.mkdir()
        argv=[sys.executable,'-B',str(P/'tests/test_recorder_contract.py'),'--tools',str(tools),'--out',str(root/(phase+'-result')),'--only',scope]
        started=time.time()
        with (outer/'stdout.bin').open('wb') as stdout,(outer/'stderr.bin').open('wb') as stderr:
            result=subprocess.run(argv,cwd=root,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=stdout,stderr=stderr)
        row={'phase':phase,'argv':argv,'cwd':str(root),'started_epoch':started,'ended_epoch':time.time(),
             'actual_exit':result.returncode,'expected_exit':expected,'modified_leaf':leaf,
             'leaf_sha256':hashlib.sha256(body.encode()).hexdigest(),
             'scope':'Synthetic external collector contract, not product mutation or performance qualification'}
        (outer/'RESULT.json').write_text(json.dumps(row,indent=2)+'\n');rows.append(row)
        assert result.returncode==expected,(scope,phase,result.returncode)
        if phase=='withdrawn':assert expected_assertion.encode() in (outer/'stderr.bin').read_bytes()
    assert (tools/leaf).read_bytes()==(P/'tools-v5'/leaf).read_bytes()
    allrows.append({'scope':scope,'phases':rows,'negative_exact_assertion':expected_assertion,'restored_exact':True})
assert {x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in files}==pins
(O/'RESULT.json').write_text(json.dumps({'scope':'Two independent recorder withdrawals, no C/product/performance samples',
    'variants':allrows,'original_v5_tools_unchanged':True,'exit_code':0},indent=2)+'\n')
print(json.dumps({'exit_code':0,'scopes':{x['scope']:[r['actual_exit'] for r in x['phases']] for x in allrows}}))
