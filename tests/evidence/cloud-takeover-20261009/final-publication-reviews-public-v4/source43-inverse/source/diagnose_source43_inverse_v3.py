from pathlib import Path
import ast,difflib,hashlib,json,sys,datetime
source=Path('<workspace-path>')
tree=ast.parse(source.read_text());selected=[]
for n in tree.body:
 if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef)):selected.append(n)
 elif isinstance(n,ast.Assign) and all(isinstance(t,ast.Name) and t.id in {'B','P','R','O','sha','TOKEN','PREFIX','inverse_records'} for t in n.targets):selected.append(n)
env={};exec(compile(ast.Module(body=selected,type_ignores=[]),str(source),'exec'),env)
original=env['inverse_text'];errors=[]
def observed(old,new,where,record=True):
 ok=original(old,new,where,record)
 if not ok and record:
  normalized=env['TOKEN'].sub('<machine-path-token>',old)
  public=new
  for k,v in env['PREFIX'].items():public=public.replace(v,'<machine-path-token>')
  for label in ['<workspace-path>','<isolated-test-directory>','<execution-runtime-path>','<isolated-browser-profile>']:public=public.replace(label,'<machine-path-token>')
  diff=list(difflib.unified_diff(normalized.splitlines(),public.splitlines(),fromfile='original-non-token',tofile='public-non-token',n=1))
  errors.append({'where':where,'originalValue':old,'publicValue':new,'normalizedDiff':diff})
 return ok
env['inverse_text']=observed
proof=json.loads(Path('<workspace-path>').read_text());root=env['P']
results=[]
for x in proof['publicReferences']:
 if x['inverseExact']:continue
 raw=Path(x['originalPaths'][0]).read_bytes();new=(root/x['publicPath']).read_bytes();start=len(errors)
 ok=env['inverse_value'](env['load'](raw),env['load'](new),x['publicPath']) if x['publicPath'].endswith('.json') else observed(raw.decode(),new.decode(),x['publicPath'])
 results.append({'publicPath':x['publicPath'],'rechecked':ok,'errors':errors[start:]})
out=Path('<workspace-path>');assert not out.exists()
record={'schema':'geometry-source43-inverse-diagnostic/1','checkedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':sys.orig_argv,'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'results':results,'productExecuted':False}
out.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'diagnostic':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'results':[{'path':x['publicPath'],'errors':[{'where':v['where'],'diff':v['normalizedDiff']} for v in x['errors']]} for x in results]},ensure_ascii=False))

