from pathlib import Path
import hashlib,json,os,subprocess,sys,tempfile

REPO=Path('/workspace/geometry-axiom')
BRANCH='codex/train337-native-validation-20261027'
REF='refs/heads/'+BRANCH
PREFIX='evidence/geo337-native-validation-20261027/'
def git(*args,env=None,input=None):
    return subprocess.check_output(['git','-C',str(REPO),*args],env=env,input=input).decode().strip()
exists=subprocess.run(['git','-C',str(REPO),'show-ref','--verify','--quiet',REF]).returncode==0
parent=git('rev-parse',REF if exists else '45dd4d662eac9297eda8473742c9943a1cb336cb')
groups={'audit':Path(__file__).parent,'a4bd-withdrawn':Path('/workspace/scratch/geo337-native-aprime-a4bd77e-20261027'),'F-interrupted':Path('/workspace/scratch/geo337-native-F-cbf0fb62-20261027')}
final='--final' in sys.argv
if final: groups['F-complete']=Path('/workspace/scratch/geo337-native-F-cbf0fb62-20261027-r2')
with tempfile.TemporaryDirectory(prefix='geo337-publish-',dir='/workspace/scratch') as d:
    env=dict(os.environ,GIT_INDEX_FILE=str(Path(d)/'index'))
    git('read-tree',parent,env=env)
    manifest={}
    for label,root in groups.items():
        for p in sorted(root.iterdir()):
            if not p.is_file() or p.name.startswith('F-r2-launcher.'): continue
            name=PREFIX+label+'/'+p.name
            blob=git('hash-object','-w',str(p))
            git('update-index','--add','--cacheinfo','100644',blob,name,env=env)
            manifest[name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    data=(json.dumps({'source_F':'cbf0fb621888596aa14ad5f2349b503e23b1b72d','complete_F_included':final,'files':manifest},indent=2)+'\n').encode()
    blob=git('hash-object','-w','--stdin',input=data)
    git('update-index','--add','--cacheinfo','100644',blob,PREFIX+'MANIFEST.json',env=env)
    tree=git('write-tree',env=env)
    msg='test(evidence): preserve complete recovery F native result' if final else 'test(evidence): preserve withdrawn native failure and interrupted launcher originals'
    commit=git('commit-tree',tree,'-p',parent,input=(msg+'\n').encode())
    git('update-ref',REF,commit,parent if exists else '0'*40)
    print(json.dumps({'branch':BRANCH,'commit':commit,'parent':parent,'file_count':len(manifest),'complete_F_included':final}),flush=True)
