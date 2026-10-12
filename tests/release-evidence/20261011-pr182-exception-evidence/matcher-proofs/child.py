import importlib.util,inspect,pathlib,sys,unittest
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
