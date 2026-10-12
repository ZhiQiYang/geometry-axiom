import importlib.util,json,pathlib,sys,types
root=pathlib.Path('/workspace/geometry-axiom');sys.path.insert(0,str(root/'tests'))
spec=importlib.util.spec_from_file_location('pr194_run_all',root/'tests/run_all.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
data=json.loads(pathlib.Path(sys.argv[1]).read_text());assert data['total']==21 and data['passed']==14 and data['failed']==0 and data['skipped']==7
results=[]
for platform in ('posix','nt'):
 runner.os=types.SimpleNamespace(name=platform)
 actual=runner.classify_skips('py:test_lan_review',data)
 results.append({'platform':platform,'allowed':actual,'unallowed':7-actual})
print(json.dumps({'raw_runner_counts':{k:data[k] for k in ('total','passed','failed','skipped')},'classifications':results}))
assert all(r['allowed']==7 for r in results),results
