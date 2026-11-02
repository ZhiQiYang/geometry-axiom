"""Fixed/withdrawn/restored proof of diagnostic parser; Python only."""
import hashlib,json,os,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'python-proof-r2'
if OUT.exists():raise SystemExit('Fresh proof output required')
OUT.mkdir()
original=(ROOT/'sidecar.py').read_bytes()
anchor=b"must(event['length'] == len(lines[command - 1]), 'input-line-length')  # WITHDRAWAL_ANCHOR"
if original.count(anchor)!=1:raise SystemExit('Exact withdrawal anchor drift')
changed=original.replace(anchor,b'pass  # WITHDRAWAL_ANCHOR: deliberately omit original input line length check')
environment=dict(os.environ);environment.pop('PYTHONOPTIMIZE',None);environment['PYTHONDONTWRITEBYTECODE']='1'
phases=[]
for name,body in [('fixed',original),('withdrawn',changed),('restored',original)]:
    p=OUT/name;p.mkdir();(p/'sidecar.py').write_bytes(body)
    for f in ['launch_diagnostic.py','selftest_protocol.py']:(p/f).write_bytes((ROOT/f).read_bytes())
    argv=[sys.executable,'-B',str(p/'selftest_protocol.py'),'--out',str(p/'TEST_RESULT.json')]
    r=subprocess.run(argv,cwd=p,env=environment,capture_output=True)
    (p/'stdout.bin').write_bytes(r.stdout);(p/'stderr.bin').write_bytes(r.stderr)
    record={'argv':argv,'cwd':str(p),'exit':r.returncode,'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),
            'stderr_sha256':hashlib.sha256(r.stderr).hexdigest(),'sidecar_sha256':hashlib.sha256(body).hexdigest(),
            'environment':{'PYTHONOPTIMIZE':environment.get('PYTHONOPTIMIZE'),'PYTHONDONTWRITEBYTECODE':'1'},
            'product_executed':False,'wrapper_compiled':False}
    (p/'COMMAND_RESULT.json').write_text(json.dumps(record,indent=2)+'\n')
    tests=json.loads((p/'TEST_RESULT.json').read_bytes());failed=[x['name'] for x in tests['checks'] if not x['passed']]
    phases.append({'phase':name,**record,'failed':failed})
accepted=[x['exit'] for x in phases]==[0,1,0] and phases[1]['failed']==['reject-wrong-command-line-length']
summary={'schema':'geo348-python-tool-withdrawal-proof/1','exit':0 if accepted else 1,
         'phases':phases,'scope':'Synthetic Python tool protocol only; no C compile, product process, original512 rerun or new performance data.'}
(OUT/'RESULT.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({'exit':summary['exit'],'phases':[(x['phase'],x['exit'],x['failed']) for x in phases]}))
raise SystemExit(summary['exit'])
