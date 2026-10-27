from pathlib import Path
import hashlib,json,os,subprocess,tempfile
REPO=Path('/workspace/geometry-axiom');REF='refs/heads/codex/train337-native-validation-20261027';ROOT=Path(__file__).parent
PREFIX='evidence/geo337-followup-scope-20261027/'
def git(*args,env=None,input=None):return subprocess.check_output(['git','-C',str(REPO),*args],env=env,input=input).decode().strip()
parent=git('rev-parse',REF);assert parent=='a08a036db335e88608ead761539d3e60b75e8e5d'
c=json.loads((ROOT/'geo314/COVERAGE.json').read_text());assert c['six_native_pass_count']==103 and c['inspector_cases_passed']==12 and not c['new_test_execution']
with tempfile.TemporaryDirectory(prefix='geo337-followup-publish-',dir='/workspace/scratch') as d:
 env=dict(os.environ,GIT_INDEX_FILE=str(Path(d)/'index'));git('read-tree',parent,env=env);manifest={}
 for p in sorted(ROOT.rglob('*')):
  if not p.is_file() or '__pycache__' in p.relative_to(ROOT).parts:continue
  name=PREFIX+str(p.relative_to(ROOT));data=p.read_bytes();assert len(data)<50*1024**2
  blob=git('hash-object','-w',str(p));git('update-index','--add','--cacheinfo','100644',blob,name,env=env)
  manifest[name]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
 data=(json.dumps({'source_F':'cbf0fb621888596aa14ad5f2349b503e23b1b72d','new_product_test_execution':False,'files':manifest},indent=2)+'\n').encode()
 blob=git('hash-object','-w','--stdin',input=data);git('update-index','--add','--cacheinfo','100644',blob,PREFIX+'MANIFEST.json',env=env)
 tree=git('write-tree',env=env);commit=git('commit-tree',tree,'-p',parent,input=b'docs(evidence): index existing GEO314 coverage and exact whole-memo input gap\n')
 git('update-ref',REF,commit,parent);print(json.dumps({'commit':commit,'parent':parent,'files':len(manifest),'prefix':PREFIX}))
