import hashlib,importlib.util,json,pathlib,resource,subprocess,sys,time
root=pathlib.Path.cwd(); phase=sys.argv[1];out=pathlib.Path('/tmp/geometry-182-cause')/phase;out.mkdir(parents=True,exist_ok=True)
resource.setrlimit(resource.RLIMIT_STACK,(16777216,resource.getrlimit(resource.RLIMIT_STACK)[1]))
spec=importlib.util.spec_from_file_location('gate',root/'tests/section_profile_mutation_check.py');gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
case=next(c for c in gate.CASES if c['id']=='SPM08');binary=pathlib.Path('/tmp/geometry-tests/bridge');report=out/'exceptions.json'
name=gate.NATIVE_MODULE+'.'+gate.NATIVE_CLASS+'.'+gate.PANEL
child='''import copy,sys,unittest
from unittest.mock import patch
from tests import test_section_profile_native as native
original=native.SectionProfileNative.read
def read_without_rect(self,*args,**kwargs):
    result=copy.deepcopy(original(self,*args,**kwargs))
    for member in result.get('state',{}).get('members',[]):member.pop('rect',None)
    return result
with patch.object(native,'find_bridge',return_value=sys.argv[1]), patch.object(native.SectionProfileNative,'read',read_without_rect):
    if sys.argv[2]=='before':unittest.main(module=None,argv=['x','-v',sys.argv[4]])
    else:
        from tests.section_profile_mutation_runner import run_tests
        sys.exit(run_tests([sys.argv[4]],sys.argv[3]))
'''
argv=[sys.executable,'-c',child,str(binary),phase,str(report),name];start=time.monotonic();run=subprocess.run(argv,cwd=root,capture_output=True,text=True)
(out/'stdout.log').write_text(run.stdout);(out/'stderr.log').write_text(run.stderr);log=run.stdout+run.stderr;(out/'combined.log').write_text(log)
assert run.returncode==1 and "KeyError: 'rect'" in log
assert case['cause'][0] in log
evidence=json.loads(report.read_text()) if report.exists() else None
judgment=gate.verdict(case,run.returncode,log,evidence) if phase!='before' else gate.verdict(case,run.returncode,log)
assert (judgment['verdict']=='killed')==(phase=='before'),judgment
sources=['tests/section_profile_mutation_check.py','tests/test_section_profile_native.py','tests/test_section_profile_mutation_check.py','current_geometry.c']
if phase!='before':sources+=['tests/section_profile_mutation_runner.py']
data={'phase':phase,'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
      'status':subprocess.check_output(['git','status','--porcelain'],text=True).splitlines(),
      'sources':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in sources},
      'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'binary_sidecar':json.loads(pathlib.Path(str(binary)+'.fingerprint.json').read_text()),
      'argv':argv,'child_source':child,'returncode':run.returncode,'seconds':time.monotonic()-start,'verdict':judgment,
      'scope':'Actual unmodified baseline bridge and original SPM08 method; adversarial read-reply interception only, not a real product mutation'}
(out/'receipt.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'phase':phase,'child_exit':run.returncode,'verdict':judgment['verdict']}))
