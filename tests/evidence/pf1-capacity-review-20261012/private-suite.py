import json,pathlib,sys,unittest
sys.path.insert(0,'/workspace/geometry-axiom')
from tests import test_panel_fill_finish_surface as module
module.find_bridge=lambda: sys.argv[1]
names=sys.argv[2:]
suite=unittest.TestSuite(module.FinishSurfaceNative(n) for n in names)
class Result(unittest.TextTestResult):
 def __init__(self,*a,**k):super().__init__(*a,**k);self.events=[]
 def addFailure(self,t,e):self.events.append({'test':t.id(),'type':e[0].__name__,'message':str(e[1])});super().addFailure(t,e)
 def addError(self,t,e):self.events.append({'test':t.id(),'type':e[0].__name__,'message':str(e[1])});super().addError(t,e)
 def addSubTest(self,t,sub,e):
  if e:self.events.append({'test':t.id(),'subtest':str(sub),'type':e[0].__name__,'message':str(e[1])})
  super().addSubTest(t,sub,e)
r=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(suite)
print(json.dumps({'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skips':len(r.skipped),'events':r.events}))
sys.exit(0 if r.wasSuccessful() and not r.skipped else 1)
