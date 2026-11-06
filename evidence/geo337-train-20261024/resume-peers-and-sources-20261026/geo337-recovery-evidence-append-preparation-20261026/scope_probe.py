"""Pure in-memory simulation of the prepared real tree helper, never Git I/O."""
from pathlib import Path
import argparse,ast,copy,hashlib,json,types
HERE=Path(__file__).parent
source=ast.parse((HERE/'publish_append.py').read_bytes())
main=next(n for n in source.body if isinstance(n,ast.FunctionDef)and n.name=='main')
update=next(n for n in ast.walk(main)if isinstance(n,ast.FunctionDef)and n.name=='update')
PREFIX='evidence/geo337-train-20261024/';PROGRESS=PREFIX+'resume-20261026/PROGRESS.md'
ap=argparse.ArgumentParser();ap.add_argument('case',choices=['fixed','withdrawn-unlisted-overwrite','restored','stale-progress','unbound-progress','other-progress','new-only','stale-parent','parent-restored','product-path']);case=ap.parse_args().case
trees={}
def need(ok,msg):
 if not ok:raise RuntimeError(msg)
def readtree(key):return dict(trees.get(key,{}))
def git(*args,data=None):
 assert args==('mktree','-z'),'No actual Git or unexpected mocked command'
 rows={}
 for row in data.split(b'\0'):
  if row:
   hdr,name=row.split(b'\t',1);mode,kind,oid=hdr.split(b' ');rows[name.decode()]=(mode,kind,oid)
 key=hashlib.sha1(data).hexdigest();trees[key]=rows;return (key+'\n').encode()
def oid(b):return b.decode().strip()
a=types.SimpleNamespace(expected_progress_blob='a'*40,expected_parent='e'*40)
ns={'readtree':readtree,'git':git,'oid':oid,'need':need,'a':a,'PROGRESS':PROGRESS}
exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(update)],type_ignores=[])),'<real-update-helper>','exec'),ns)
update=ns['update'];raw=PREFIX+'old-originals/result.json';other=PREFIX+'PROGRESS.md'
base=update(None,{PROGRESS:'a'*40,raw:'b'*40,other:'1'*40})
base_objects={key:dict(value) for key,value in trees.items()}
def leaves(tree,prefix=''):
 result={}
 for name,(mode,kind,obj)in readtree(tree).items():
  if kind==b'tree':result.update(leaves(obj.decode(),prefix+name+'/'))
  else:result[prefix+name]=obj.decode()
 return result
base_leaves=leaves(base)
changes={PROGRESS:'c'*40,PREFIX+'new-originals/result.json':'d'*40}
if case=='withdrawn-unlisted-overwrite':changes={raw:'c'*40}
if case=='stale-progress':a.expected_progress_blob='f'*40
if case=='unbound-progress':a.expected_progress_blob=None
if case=='other-progress':changes={other:'c'*40}
if case=='new-only':a.expected_progress_blob=None;changes={PREFIX+'new-originals/result.json':'d'*40}
if case in ['stale-parent','parent-restored']:
 call=next(n for n in ast.walk(main)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='need'and len(n.args)>1 and isinstance(n.args[1],ast.Constant)and n.args[1].value=='recovery remote parent changed')
 branch='codex/train337-recovered-evidence-20261026';expected=(a.expected_parent+'\trefs/heads/'+branch+'\n').encode();actual=expected if case=='parent-restored'else ('f'*40+'\trefs/heads/'+branch+'\n').encode()
 eval(compile(ast.Expression(copy.deepcopy(call)),'<real-remote-parent-guard>','eval'),{'need':need,'git':lambda *args:actual,'BRANCH':branch,'expected_parent_ref':expected})
elif case=='product-path':
 call=next(n for n in ast.walk(main)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='need'and len(n.args)>1 and isinstance(n.args[1],ast.Constant)and n.args[1].value=='destination outside evidence')
 dst='tests/mutate.py';eval(compile(ast.Expression(copy.deepcopy(call)),'<real-path-guard>','eval'),{'need':need,'dst':dst,'parts':Path(dst).parts,'PREFIX':PREFIX})
else:
 final=update(base,changes)
 assert all(trees[key]==value for key,value in base_objects.items()),'original in-memory trees changed'
 assert leaves(final)=={**base_leaves,**changes},'unexpected sibling/path changes'
print(json.dumps({'case':case,'memory_only':True,'actual_git_called':False,'filesystem_or_network_mutation':False,'outcome':'accepted'}))
