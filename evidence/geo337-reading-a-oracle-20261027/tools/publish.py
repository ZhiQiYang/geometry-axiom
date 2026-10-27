from pathlib import Path
import hashlib,json,os,subprocess,tempfile
REPO=Path('/workspace/geometry-axiom');REF='refs/heads/codex/train337-native-validation-20261027'
PREFIX='evidence/geo337-reading-a-oracle-20261027/'
def git(*args,env=None,input=None):return subprocess.check_output(['git','-C',str(REPO),*args],env=env,input=input).decode().strip()
parent=git('rev-parse',REF)
assert parent=='732ef20e34876379a37eb69693a481becebea43e'
groups={'tools':Path(__file__).parent,'oracle':Path('/workspace/scratch/geo337-reading-a-oracle-F-cbf0fb62-20261027'),'reader':Path('/workspace/scratch/geo337-reading-a-reader-F-cbf0fb62-20261027'),'rc':Path('/workspace/scratch/geo337-reading-a-rc-F-cbf0fb62-20261027')}
for label in ['oracle','reader','rc']:
    d=json.loads((groups[label]/'RESULT.json').read_text());assert d['passed'] and d['sha']=='cbf0fb621888596aa14ad5f2349b503e23b1b72d'
with tempfile.TemporaryDirectory(prefix='geo337-oracle-publish-',dir='/workspace/scratch') as d:
    env=dict(os.environ,GIT_INDEX_FILE=str(Path(d)/'index'));git('read-tree',parent,env=env);manifest={}
    paths={PREFIX+'README.md':groups['tools']/'HANDOFF.md'}
    for label,root in groups.items():
        for p in sorted(root.rglob('*')):
            if not p.is_file() or any(part in ('__pycache__','tmp') for part in p.relative_to(root).parts) or p.name.endswith('.lock'):continue
            paths[PREFIX+label+'/'+str(p.relative_to(root))]=p
    for name,p in paths.items():
        data=p.read_bytes();blob=git('hash-object','-w',str(p));git('update-index','--add','--cacheinfo','100644',blob,name,env=env)
        manifest[name]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    data=(json.dumps({'source_F':'cbf0fb621888596aa14ad5f2349b503e23b1b72d','files':manifest},indent=2)+'\n').encode()
    blob=git('hash-object','-w','--stdin',input=data);git('update-index','--add','--cacheinfo','100644',blob,PREFIX+'MANIFEST.json',env=env)
    tree=git('write-tree',env=env);commit=git('commit-tree',tree,'-p',parent,input=b'test(evidence): complete fixed-F Reading A oracle, reader and RC validation\n')
    git('update-ref',REF,commit,parent);print(json.dumps({'commit':commit,'parent':parent,'files':len(manifest),'prefix':PREFIX}))
