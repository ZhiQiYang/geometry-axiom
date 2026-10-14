import hashlib,json,pathlib,subprocess
repo=pathlib.Path('/tmp/geometry-p095-201');out=repo/'tests/evidence/201-main-pf2-integration-20261014';out.mkdir(exist_ok=True)
def git(*a):return subprocess.check_output(['git',*a],cwd=repo).decode().strip()
def get(ref):return json.loads(subprocess.check_output(['git','show',ref+':tests/run_all.expected.json'],cwd=repo))
base=git('merge-base','HEAD','MERGE_HEAD');heads={'base':base,'ours':git('rev-parse','HEAD'),'main':git('rev-parse','MERGE_HEAD')}
b=get(base);o=get('HEAD');m=get('MERGE_HEAD');result=json.loads(json.dumps(o));proof=[]
for key in set(b['suites'])|set(o['suites'])|set(m['suites']):
 bv=b['suites'].get(key);ov=o['suites'].get(key);mv=m['suites'].get(key)
 if ov==bv:chosen=mv
 elif mv==bv or mv==ov:chosen=ov
 else:raise RuntimeError(('independent manual choice required',key,bv,ov,mv))
 if chosen is None:result['suites'].pop(key,None)
 else:result['suites'][key]=chosen
 if ov!=bv or mv!=bv:proof.append({'suite':key,'base':bv,'ours':ov,'main':mv,'result':chosen})
assert result['suites']['node:tests-js']['count']==703
assert result['suites']['node:grid_lesson_control_ownership']['count']==13
assert result['suites']['py:test_grid_system_contract']['count']==15
assert result['suites']['py:test_panel_fill_layout']['count']==17
assert result['suites']['py:test_engineering_model_compatibility']['count']==28
total=sum(x['count'] for x in result['suites'].values() if x['mode']=='count');assert total==2776
(repo/'tests/run_all.expected.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
equality={}
for name in ['current_geometry.c','tests/mutants_results.json','tests/mutate.py','tests/run_tests.py','tests/test_reference_workspace_races.js']:
 ref='HEAD' if name=='tests/test_reference_workspace_races.js' else 'MERGE_HEAD'
 actual=(repo/name).read_bytes();expected=subprocess.check_output(['git','show',ref+':'+name],cwd=repo);assert actual==expected,name
 equality[name]={'equals':ref,'raw_sha256':hashlib.sha256(actual).hexdigest()}
(out/'merge-proof.json').write_text(json.dumps({'heads':heads,'only_conflicted_path':'tests/run_all.expected.json','resolutions':proof,'total_counted_items':total,'counted_suites':sum(x['mode']=='count' for x in result['suites'].values()),'registered_suites':len(result['suites']),'byte_equality':equality,'note':'P104 four case budgets/callbacks unchanged; inherited P105 main core and ledger without rewriting hashes'},ensure_ascii=False,indent=2)+'\n')
for label,data in [('base',b),('ours',o),('main',m)]:
 (out/(label+'-expected.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'heads':heads,'resolutions':proof,'counted_total':total,'registered_suites':len(result['suites'])},ensure_ascii=False))
