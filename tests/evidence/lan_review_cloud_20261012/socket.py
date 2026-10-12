import hashlib,importlib.util,json,pathlib,shutil,sys,unittest
sys.path.insert(0,'/workspace/geometry-axiom')
from tests import test_lan_review as module
root=pathlib.Path('/workspace/geometry-axiom');target='test_denied_late_body_is_drained_after_response_before_socket_release'
sys.path.insert(0,str(root/'geometry-web'))
mode=sys.argv[1]
if mode=='RESTORED':
 tmp=pathlib.Path('/tmp/geometry-tests/pr194-review/M23-source/geometry-web/serve.py')
 tmp.write_bytes((root/'geometry-web/serve.py').read_bytes());module.base.SERVE=tmp
 print(json.dumps({'mode':mode,'restored_sha256':hashlib.sha256(tmp.read_bytes()).hexdigest()}))
if mode=='M23':
 row=next(r for r in json.loads((root/'tests/evidence/lan_review_mutants.json').read_text())['mutants'] if r['id']=='M23')
 original=(root/row['path']).read_bytes();text=original.decode()
 for old,new in row['edits']:assert text.count(old)==1;text=text.replace(old,new)
 catalog_spec=importlib.util.spec_from_file_location('pr194_runtime_catalog',root/'geometry-web/runtime_version.py')
 catalog=importlib.util.module_from_spec(catalog_spec);catalog_spec.loader.exec_module(catalog)
 shadow=pathlib.Path('/tmp/geometry-tests/pr194-review/M23-source');shadow.mkdir(exist_ok=True)
 copied={}
 for p in catalog.source_files(root):
  rel=p.relative_to(root);dest=shadow/rel;dest.parent.mkdir(parents=True,exist_ok=True)
  if str(rel)=='geometry-guide/公理層-閱讀器.html':
   if not dest.exists():dest.symlink_to(p)
  else:shutil.copyfile(p,dest)
  copied[str(rel)]=hashlib.sha256(p.read_bytes()).hexdigest()
 tmp=shadow/row['path'];tmp.write_text(text)
 pathlib.Path('/tmp/geometry-tests/pr194-review/M23-source-closure.json').write_text(json.dumps(copied,ensure_ascii=False,indent=2)+'\n')
 module.base.SERVE=tmp
 print(json.dumps({'mode':mode,'mutation_registry_id':'M23','original_sha256':hashlib.sha256(original).hexdigest(),'mutated_sha256':hashlib.sha256(tmp.read_bytes()).hexdigest(),'path':str(tmp)}))
class Result(unittest.TextTestResult):
 def __init__(self,*a,**k):super().__init__(*a,**k);self.events=[]
 def addFailure(self,t,e):self.events.append({'test':t.id(),'type':e[0].__name__,'message':str(e[1])});super().addFailure(t,e)
 def addError(self,t,e):self.events.append({'test':t.id(),'type':e[0].__name__,'message':str(e[1])});super().addError(t,e)
suite=unittest.TestSuite(module.SocketReview(target) for _ in range(3))
r=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(suite)
print(json.dumps({'mode':mode,'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skips':len(r.skipped),'events':r.events}))
sys.exit(0 if r.wasSuccessful() and not r.skipped else 1)
