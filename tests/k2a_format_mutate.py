"""P-054: isolated source variants, exact target test, raw restoration proof."""
from pathlib import Path
import hashlib, json, os, subprocess, tempfile
root=Path(__file__).resolve().parents[1]
out=Path(tempfile.gettempdir())/'k2aa-format-mutants-review'
out.mkdir(exist_ok=True)
original=root/'geometry-web/project-store.js'
source=original.read_bytes()
judge=root/'tests/test_shared_format17.js'
cases=[
 ('P054-other-owner-downgrade','manifest.format !== GRID_DRAFTS_FORMAT','false','P-054 unsupported other-owner capability and stripped capability reject whole /17 archive'),
 ('P054-own-format-only','if(projectCapabilities(manifest,scene).some(capability=>format17Capabilities.includes(capability)))', 'if(projectCapabilities(manifest,scene).includes(Features.GRID_DRAFTS_SCHEMA))', 'P-054 shared /17 accepts each registered feature alone and both without discarding attachments'),
 ('P054-drop-nested-capability','if(format17Capabilities.includes(capability))required.add(capability);','if(false)required.add(capability);','P-054 nested scenario leaves retain each /17 family and reject stripped root capability'),
]
results=[]
for ident,before,after,target in cases:
 assert source.count(before.encode())==1
 mutant=out/(ident+'.js');mutant.write_bytes(source.replace(before.encode(),after.encode()))
 command=['node','--test-reporter=tap','--test','--test-name-pattern=^'+target+'$',str(judge)]
 def run(name,cmd,env=None):
  r=subprocess.run(cmd,cwd=root,env=env,capture_output=True,text=True,timeout=60)
  (out/(ident+'-'+name+'.log')).write_text(r.stdout+r.stderr)
  return r
 baseline=run('baseline',command);assert baseline.returncode==0
 build=run('build',['node','--check',str(mutant)]);assert build.returncode==0
 red=run('red',command,dict(os.environ,GEOMETRY_PROJECT_STORE_SOURCE=str(mutant)))
 text=red.stdout+red.stderr
 assert red.returncode!=0 and 'not ok 1 - '+target in text and 'ERR_ASSERTION' in text and '# fail 1' in text and '# tests 1' in text,text
 restored=run('restored',command);assert restored.returncode==0
 assert original.read_bytes()==source
 results.append(dict(id=ident,target=target,detected=True,source_sha256=hashlib.sha256(source).hexdigest(),judge_sha256=hashlib.sha256(judge.read_bytes()).hexdigest(),logs={phase:hashlib.sha256((out/(ident+'-'+phase+'.log')).read_bytes()).hexdigest() for phase in ['baseline','build','red','restored']}))
 print(ident+' strict red and restored',flush=True)
(out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
