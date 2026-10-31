from pathlib import Path
import ast,hashlib,json,types
T=Path('/tmp/geo323-train337-lineage-20261024/acceptance-tools-v4-scene-binding/geo323_record.py')
O=Path('/workspace/train337-canvas-peer-resume/V4_OUTER_SOURCE_ROLE_DIAGNOSTIC.json')
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
tree=ast.parse(T.read_text());cl=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Recorder');fn=next(n for n in cl.body if isinstance(n,ast.FunctionDef) and n.name=='role')
ns={};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(T),'exec'),ns)
L='7af8c5d80d34cb4f49d01ba67deb78a3a6d725db';BASE='b74f9a2ae7ade1555b9be45283adecc097fb76e3';MAIN='adbaebf9c73ea6801d7b4d5214e4b846b132923b'
receiver=types.SimpleNamespace(sha=L,env={'GEO323_BASE_SHA':BASE,'GEO323_MAIN_SHA':MAIN});items=[]
for gate in ['required-eight','pf3']:
 root=Path('/workspace/train337-final-L-'+gate+'-7af8c5d8/'+gate+'/subject');outer=next(root.glob('control/*/outer-command/000001/result.json'));r=json.loads(outer.read_text());actual=ns['role'](receiver,r['command'],r['cwd']);inner=json.loads(next(root.glob('invocations/*/commands/000003/result.json')).read_text())
 assert actual==r['source_role']=={'label':'base','sha':BASE}
 assert inner['source_sha']==inner['acceptance_sha']==r['acceptance_sha']==r['command'][r['command'].index('--sha')+1]==L
 items.append({'gate':gate,'original_result':str(outer),'original_result_sha256':h(outer),'reproduced_original_role':actual,'actual_subject_inner_source_sha':inner['source_sha'],'acceptance_sha':r['acceptance_sha'],'exit':inner['actual_process_returncode'],'cause':'Original Recorder.role searches the full argv string for base SHA before checking main. The orchestration argv includes --base as comparison configuration, so the outer label is base even though --sha and the actual inner test run target L.'})
report={'schema':'original-v4-source-role-metadata-diagnostic-v1','exit_code':0,'original_tool_sha256':h(T),'original_tool_unmodified':True,'only_original_role_function_executed_as_pure_python':True,'cases':items,'impact':'Metadata classification ambiguity in orchestration envelope only. Original inner subject source and before/after Git guard retain independent L binding. Do not relabel original recorded bytes.','conservative_future_recommendation':'Retain frozen original acceptance tool. For a later independently reviewed tool revision, pass explicit role at each invocation instead of scanning every argument; add baseline/main/orchestration counterexamples before adopting. Do not change current comparison, thresholds or tests to address this label.'}
O.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(O),'sha256':h(O),'exit_code':0,'cases':len(items)}))
