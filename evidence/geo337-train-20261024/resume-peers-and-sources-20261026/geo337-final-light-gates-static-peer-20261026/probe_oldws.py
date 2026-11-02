"""Counterproof using the real metadata function and memory-only fake files."""
from pathlib import Path,PurePosixPath
import argparse,ast,copy,hashlib,stat,types,json
HERE=Path(__file__).parent
ap=argparse.ArgumentParser();ap.add_argument('case',choices=['fixed','withdrawn','restored']);case=ap.parse_args().case
subject=HERE/'SUBJECT.before-oldws-fix.py'if case=='withdrawn'else Path('/tmp/geo337-final-light-gates-preparation-20261026/run_after_ff_four_gates.py')
tree=ast.parse(subject.read_bytes());main=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='main');fn=next(x for x in ast.walk(main)if isinstance(x,ast.FunctionDef)and x.name=='publisher_state')
owners=['/dev/shm/geometry-axiom-geo337-20261025/publisher-source','/workspace/geometry-axiom']
data={root+'/.git/'+leaf:b'original-'+leaf.encode()for root in owners for leaf in ['HEAD','index','config','packed-refs','objects/info/alternates','refs/heads/train']}
dirs={root+'/.git'for root in owners}
class FakePath:
 def __init__(self,path):self.path=str(path)
 def __str__(self):return self.path
 def __truediv__(self,other):return FakePath(self.path+'/'+str(other))
 def __lt__(self,other):return self.path<other.path
 def is_dir(self):return self.path in dirs
 def is_symlink(self):return False
 def is_file(self):return self.path in data
 def exists(self):return self.is_file()or self.is_dir()
 def rglob(self,pattern):return [FakePath(p)for p in data if p.startswith(self.path+'/')]
 def relative_to(self,base):return PurePosixPath(self.path).relative_to(str(base))
 def read_bytes(self):return data[self.path]
 def lstat(self):return types.SimpleNamespace(st_mode=stat.S_IFREG|0o600,st_dev=1,st_ino=int(hashlib.sha256(self.path.encode()).hexdigest()[:8],16),st_size=len(data[self.path]),st_mtime_ns=1000)
def need(v,msg):
 if not v:raise RuntimeError(msg)
namespace={'Path':FakePath,'shared':types.SimpleNamespace(OWNER=FakePath(owners[0])),'stat':stat,'H':lambda b:hashlib.sha256(b).hexdigest(),'need':need}
exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(fn)],type_ignores=[])),'<actual-metadata-function>','exec'),namespace)
before=namespace['publisher_state']();data[owners[1]+'/.git/index']=b'changed-original-index';after=namespace['publisher_state']()
need(before!=after,'OLD_WS_INDEX_MUTATION_UNDETECTED')
need(before[owners[0]]==after[owners[0]],'synthetic publisher should remain unchanged')
print(json.dumps({'case':case,'memory_only':True,'actual_git_or_shm_read':False,'original_old_ws_index_change_detected':True}))
