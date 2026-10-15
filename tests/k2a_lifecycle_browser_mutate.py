from pathlib import Path
import os,subprocess,json,re,hashlib
root=Path(__file__).resolve().parents[1];out=Path('/tmp/k2aa-lifecycle-browser-mutants');out.mkdir(exist_ok=True)
cases=[('M1-empty-lost-selection','grid-system-workspace.js','GEOMETRY_GRID_WORKSPACE_SOURCE','if(before?.lost&&!next){','if(false &&before?.lost&&!next){','M1 empty source selection restores the previous source control'),('M3-undo-scan-reflags','reference-workspace.js','GEOMETRY_TEST_REFERENCE_WORKSPACE','let changed=false;\n    for(const d of c.drafts){','let changed=false;if(objects&&history.redo.length){for(const d of c.drafts)for(const r of d.inputRefs)r.lost=true;changed=true;}\n    for(const d of c.drafts){','native Undo and subsequent object scan preserve restored valid input')]
results=[];command=['node','tests/k2a_native_browser.cjs']
for name,file,key,before,after,expected in cases:
 d=out/name;d.mkdir(exist_ok=True);source=(root/'geometry-web'/file).read_bytes();assert source.decode().count(before)==1;p=d/file;p.write_text(source.decode().replace(before,after))
 def run(label,cmd=command,override=False):
  env=dict(os.environ,GEOMETRY_BROWSER_RECEIPT=str(d/(label+'-identity')))
  if override:env[key]=str(p)
  r=subprocess.run(cmd,cwd=root,env=env,capture_output=True,text=True,timeout=240);raw=r.stdout+r.stderr;(d/(label+'.log')).write_text(raw);return r.returncode,raw
 code,raw=run('baseline');assert code==0,(name,raw)
 code,raw=run('build',['node','--check',str(p)]);assert code==0
 code,raw=run('red',override=True);assert code!=0 and re.search(r'AssertionError \[ERR_ASSERTION\]: '+re.escape(expected)+r'(?:\n|$)',raw),(name,raw)
 code,raw=run('restored');assert code==0,(name,raw)
 results.append({'id':name,'detected':True,'expected_assertion':expected,'command':command,'override_env':key,'source_sha256':hashlib.sha256(source).hexdigest(),'mutant_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'judge_sha256':hashlib.sha256((root/command[1]).read_bytes()).hexdigest(),'logs':{label:hashlib.sha256((d/(label+'.log')).read_bytes()).hexdigest() for label in ['baseline','build','red','restored']}});print(name,flush=True)
(out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
