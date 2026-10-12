import copy,importlib.util,json,pathlib,sys,types
root=pathlib.Path('/workspace/geometry-axiom');sys.path.insert(0,str(root/'tests'))
spec=importlib.util.spec_from_file_location('pr194_run_all',root/'tests/run_all.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
data=json.loads(pathlib.Path(sys.argv[1]).read_text());assert data['total']==21 and data['passed']==14 and data['failed']==0 and data['skipped']==7
names=['test_lan_review.PureReview.'+n for n in ('test_subject_whitelist_rejects_cn_variants_before_reuse','test_new_material_checks_subject_before_any_persistence','test_root_constraints_do_not_claim_to_disable_client_cn_fallback')]
original=runner.ALLOWED_SKIPS;rows=[]
for platform in ('posix','nt'):
 runner.os=types.SimpleNamespace(name=platform);runner.ALLOWED_SKIPS=original
 assert runner.classify_skips('py:test_lan_review',data)==7
 for name in names:
  runner.ALLOWED_SKIPS=[e for e in original if e['test']!=name]
  assert len(original)-len(runner.ALLOWED_SKIPS)==1
  actual=runner.classify_skips('py:test_lan_review',data);assert actual==6
  rows.append({'platform':platform,'removed':name,'allowed':actual,'unallowed':1,'specified_7_assertion_would_fail':True})
 runner.ALLOWED_SKIPS=original
 assert runner.classify_skips('py:test_lan_review',data)==7
 for field,value in (('test','unregistered.method'),('reason','unrelated reason'),('scope','class')):
  changed=copy.deepcopy(data);changed['skip_items'][0][field]=value;assert runner.classify_skips('py:test_lan_review',changed)==6
 duplicated=copy.deepcopy(data);duplicated['skip_items'].append(copy.deepcopy(data['skip_items'][0]));assert runner.classify_skips('py:test_lan_review',duplicated)==7
 assert runner.classify_skips('py:wrong-suite',data)==0
runner.os=types.SimpleNamespace(name='unsupported-platform');assert runner.classify_skips('py:test_lan_review',data)==0
print(json.dumps({'original_classifier':True,'deletions':rows,'restored_both_platforms_allowed':7,'unknown_method_reason_scope_platform_suite_and_duplicate_controls':True},indent=2))
