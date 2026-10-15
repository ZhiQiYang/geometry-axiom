import ast,json,pathlib,subprocess,sys
root=pathlib.Path('/workspace/geometry-axiom');sys.path.insert(0,str(root/'tests'));import run_tests
tree=ast.parse(subprocess.check_output(['git','show','635dd86:tests/run_tests.py'],cwd=root,text=True))
old=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='TESTS' for t in n.targets))
current={x['scene']:x for x in run_tests.TESTS}
assert all(current[x['scene']]==x for x in old)
line=next(x for x in pathlib.Path('/tmp/geometry-198-review2/scenes-clean/run.log').read_text().splitlines() if x.startswith('GEOMETRY_TEST_RESULT '))
result=json.loads(line.removeprefix('GEOMETRY_TEST_RESULT '));cases={x['scene']:x for x in result['cases']}
assert all(cases[x['scene']]['status']=='pass' for x in old),result['counts']
report={'base':'635dd86ee368579aec444fb3ba16e48bccf4877e','original_scene_count':len(old),'original_specs_changed':0,'original_accept_reject_changes':0,'current_total':result['total'],'counts':result['counts'],'scope':'Exact original TESTS specs unchanged and all original registered oracles pass. Does not claim all stdout identical.'}
pathlib.Path('/tmp/geometry-198-review2/scenes-clean/original-comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
