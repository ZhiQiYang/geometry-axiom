from pathlib import Path
import hashlib,json,os,subprocess,tempfile
REPO=Path('/workspace/geometry-axiom');REF='refs/heads/codex/train337-native-validation-20261027';ROOT=Path(__file__).parent;PREFIX='evidence/geo337-executor-handoff-20261027/'
def git(*args,env=None,input=None):return subprocess.check_output(['git','-C',str(REPO),*args],env=env,input=input).decode().strip()
parent=git('rev-parse',REF);assert parent=='cbf8df4facf87b40db0fe46581c0b20131afada2'
r=json.loads((ROOT/'HANDOFF.json').read_text());assert r['execution_released'] and r['new_diagnostic']['diagnostic_complete'] and not r['new_diagnostic']['construction_route_observed']
with tempfile.TemporaryDirectory(prefix='geo337-handoff-publish-',dir='/workspace/scratch') as d:
 env=dict(os.environ,GIT_INDEX_FILE=str(Path(d)/'index'));git('read-tree',parent,env=env);manifest={}
 for p in sorted(ROOT.rglob('*')):
  if not p.is_file() or any(x in ('__pycache__','tmp') for x in p.relative_to(ROOT).parts):continue
  name=PREFIX+str(p.relative_to(ROOT));data=p.read_bytes()
  blob=git('hash-object','-w',str(p));git('update-index','--add','--cacheinfo','100644',blob,name,env=env);manifest[name]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
 data=(json.dumps({'source_F':r['fixed_F'],'scope':'small existing-evidence index and original CLI diagnostic; no duplicate archives','files':manifest},indent=2)+'\n').encode()
 blob=git('hash-object','-w','--stdin',input=data);git('update-index','--add','--cacheinfo','100644',blob,PREFIX+'MANIFEST.json',env=env)
 tree=git('write-tree',env=env);commit=git('commit-tree',tree,'-p',parent,input=b'docs(evidence): hand off fixed-F coverage and original CLI reachability observation\n')
 git('update-ref',REF,commit,parent);print(json.dumps({'commit':commit,'files':len(manifest),'bytes':sum(r['bytes'] for r in manifest.values()),'prefix':PREFIX}))
