from pathlib import Path
import hashlib,json,os,subprocess,tempfile
REPO=Path('/workspace/geometry-axiom');REF='refs/heads/codex/train337-native-validation-20261027'
PREFIX='evidence/geo337-p52-20261027/'
def git(*args,env=None,input=None):return subprocess.check_output(['git','-C',str(REPO),*args],env=env,input=input).decode().strip()
parent=git('rev-parse',REF);assert parent=='dd2cbf6a558b4af240ab4702cc8402621380881b'
groups={'tools':Path(__file__).parent,'capture':Path('/workspace/scratch/geo337-p52-capture-20261027')}
r=json.loads((groups['capture']/'RESULT.json').read_text());v=json.loads((groups['capture']/'ARCHIVE_VERIFICATION.json').read_text())
assert r['passed'] and r['actual_exit']==0 and v['all_file_bytes_and_modes_and_symlink_targets_match']
with tempfile.TemporaryDirectory(prefix='geo337-p52-publish-',dir='/workspace/scratch') as d:
 env=dict(os.environ,GIT_INDEX_FILE=str(Path(d)/'index'));git('read-tree',parent,env=env);manifest={}
 paths={PREFIX+'README.md':groups['tools']/'HANDOFF.md'}
 for label,root in groups.items():
  for p in sorted(root.rglob('*')):
   if not p.is_file() or '__pycache__' in p.relative_to(root).parts:continue
   paths[PREFIX+label+'/'+str(p.relative_to(root))]=p
 for name,p in paths.items():
  data=p.read_bytes();assert len(data)<50*1024**2,(name,len(data))
  blob=git('hash-object','-w',str(p));git('update-index','--add','--cacheinfo','100644',blob,name,env=env)
  manifest[name]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
 data=(json.dumps({'source_F':'cbf0fb621888596aa14ad5f2349b503e23b1b72d','main':'adbaebf9c73ea6801d7b4d5214e4b846b132923b','files':manifest},indent=2)+'\n').encode()
 blob=git('hash-object','-w','--stdin',input=data);git('update-index','--add','--cacheinfo','100644',blob,PREFIX+'MANIFEST.json',env=env)
 tree=git('write-tree',env=env);commit=git('commit-tree',tree,'-p',parent,input=b'test(evidence): complete fixed-F P52 original interleaved performance and controls\n')
 git('update-ref',REF,commit,parent);print(json.dumps({'commit':commit,'parent':parent,'files':len(manifest),'prefix':PREFIX}))
