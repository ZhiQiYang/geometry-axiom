import hashlib,inspect,json,pathlib,subprocess,sys,time
root=pathlib.Path.cwd();out=pathlib.Path('/tmp/geometry-182-cause/matcher-proofs');out.mkdir(parents=True,exist_ok=True)
old=out/'historical_gate.py';old.write_bytes(subprocess.check_output(['git','show','f2d332be37eb9c4d66d5c2c82edd72e966f91f5a:tests/section_profile_mutation_check.py']))
child='''import importlib.util,inspect,pathlib,sys,unittest
from tests import section_profile_mutation_check as gate
from tests import test_section_profile_mutation_check as guards
mode=sys.argv[1]
if mode=='historical-whole-log':
    spec=importlib.util.spec_from_file_location('old',sys.argv[2]);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old);gate.verdict=old.verdict
elif mode!='current':
    source=inspect.getsource(gate.verdict)
    if mode=='remove-method-binding':source=source.replace("named = [e for e in detected if e['test_id'] in expected]",'named = detected')
    elif mode=='borrow-log-cause':source=source.replace("caused = any(all(text in e['message'] for text in case['cause']) for e in named)","caused = all(text in log for text in case['cause'])")
    else:raise ValueError(mode)
    namespace=dict(gate.__dict__);exec(compile(source,'<matcher-mutant>','exec'),namespace);gate.verdict=namespace['verdict']
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(guards.ExceptionEvidence))
print('GUARD_COUNTS',result.testsRun,len(result.failures),len(result.errors),len(result.skipped),flush=True)
sys.exit(0 if result.wasSuccessful() else 1)
'''
rows=[]
for mode in ('current','historical-whole-log','borrow-log-cause','remove-method-binding','current'):
    key=mode if mode!='current' or not rows else 'restored';argv=[sys.executable,'-c',child,mode,str(old)];start=time.monotonic();run=subprocess.run(argv,cwd=root,capture_output=True,text=True)
    (out/(key+'.stdout.log')).write_text(run.stdout);(out/(key+'.stderr.log')).write_text(run.stderr)
    counts=[int(x) for x in run.stdout.split('GUARD_COUNTS ')[-1].split()]
    assert counts[0]==16 and counts[2:]==[0,0],counts
    assert run.returncode==(0 if mode=='current' else 1)
    rows.append({'mode':mode,'key':key,'argv':argv,'returncode':run.returncode,'seconds':time.monotonic()-start,'counts':dict(zip(('tests','failures','errors','skips'),counts))})
(out/'child.py').write_text(child)
sources=['tests/section_profile_mutation_check.py','tests/section_profile_mutation_runner.py','tests/test_section_profile_mutation_check.py']
(out/'receipt.json').write_text(json.dumps({'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'status':subprocess.check_output(['git','status','--porcelain'],text=True).splitlines(),
 'source_sha256':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in sources},'historical_gate_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'rows':rows},indent=2)+'\n')
print(json.dumps([{'mode':r['key'],'exit':r['returncode'],'counts':r['counts']} for r in rows]))
