import ast,json,pathlib,subprocess
root=pathlib.Path('/workspace/geometry-axiom');out=pathlib.Path('/tmp/geometry-198-review3')
def tests_at(ref):
    source=subprocess.check_output(['git','show',ref+':tests/run_tests.py'],cwd=root,text=True)
    tree=ast.parse(source)
    return next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='TESTS' for t in n.targets))
current=tests_at('HEAD');lookup={r['scene']:r for r in current}
result=json.loads(next(line.split(' ',1)[1] for line in (out/'after/scenes.log').read_text().splitlines() if line.startswith('GEOMETRY_TEST_RESULT ')))
cases={r['scene']:r for r in result['cases']}
report={}
for ref in ('635dd86ee368579aec444fb3ba16e48bccf4877e','ed877f5f05156511db24cc24cf6b90da1c4b0cda'):
    old=tests_at(ref);assert all(lookup[r['scene']]==r and cases[r['scene']]['status']=='pass' for r in old)
    report[ref]={'original_count':len(old),'specifications_changed':0,'original_accept_reject_changes':0}
report['new_count']=result['total'];report['new_cases']=[r for r in result['cases'] if 'three_residual' in r['scene']]
(out/'scene-comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
