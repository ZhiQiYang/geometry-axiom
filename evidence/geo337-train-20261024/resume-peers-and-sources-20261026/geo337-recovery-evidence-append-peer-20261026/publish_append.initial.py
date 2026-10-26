"""Append evidence to the fixed recovery branch using ordinary expected-parent CAS."""
import argparse,hashlib,importlib.util,json,os,re,shutil,sys
from pathlib import Path,PurePosixPath
OWN=Path('/dev/shm/geometry-axiom-geo337-20261025')
ROOT=OWN/'publisher-source'
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
BRANCH='codex/train337-recovered-evidence-20261026'
BASE='a6f4013364e21bcb7239b5dcc25caac0f6d61f77'
HEAD='3e4f2560aa11ed2a626db98ba5ed6f129e791052'
PREFIX='evidence/geo337-train-20261024/'
PROGRESS=PREFIX+'resume-20261026/PROGRESS.md'
def h(b): return hashlib.sha256(b).hexdigest()
def need(ok,msg):
 if not ok: raise RuntimeError(msg)
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--manifest',type=Path);p.add_argument('--sha256');p.add_argument('--out',type=Path);p.add_argument('--expected-parent');p.add_argument('--expected-progress-blob');a=p.parse_args()
 if not a.execute: print('PLAN_ONLY: append recovery evidence with expected-parent CAS; existing HEAD/index/train untouched');return
 need(not sys.flags.optimize,'optimization forbidden')
 need(isinstance(a.expected_parent,str) and re.fullmatch('[0-9a-f]{40}',a.expected_parent),'explicit full expected-parent SHA')
 need(a.expected_progress_blob is None or re.fullmatch('[0-9a-f]{40}',a.expected_progress_blob),'explicit old progress blob OID or no overwrite')
 need(h(CAP.read_bytes())=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762','capture pin')
 raw=a.manifest.read_bytes();need(h(raw)==a.sha256,'manifest pin');m=json.loads(raw)
 need(a.out.parent==OWN and not a.out.exists(),'fresh own output required')
 files=m['files'];need(files,'empty manifest')
 total=sum(x['bytes'] for x in files);budget=total*3+len(files)*65536+len(raw)*8+64*1024*1024
 seen=set();used=0
 for root in [OWN,Path('/dev/shm/geo337-F9-browsers-20261025')]:
  for f in root.rglob('*'):
   s=f.lstat();k=(s.st_dev,s.st_ino)
   if k not in seen:seen.add(k);used+=s.st_blocks*512
 need(used+budget<=2*1024**3,'combined original 2GiB planning bound')
 need(shutil.disk_usage(OWN).free>budget,'actual mount capacity')
 spec=importlib.util.spec_from_file_location('capture',CAP);cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
 a.out.mkdir();(a.out/'EXECUTOR.py').write_bytes(Path(__file__).read_bytes());(a.out/'MANIFEST.json').write_bytes(raw)
 env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')};env['GIT_OPTIONAL_LOCKS']='0';env['PYTHONDONTWRITEBYTECODE']='1'
 rec=cap.Recorder(a.out,env,a.expected_parent)
 result={'exit_code':None,'base_sha':a.expected_parent,'recovery_anchor_sha':BASE,'branch':BRANCH,'source_execution_sha':None,'evidence_source_binding':'Original per-file receipts; publication parent is not relabelled as execution source','allowed_progress_update':PROGRESS,'expected_progress_blob':a.expected_progress_blob,'published':False,'delivered':False,'product_modified':False,'train_ref_modified':False,'capacity':{'used':used,'additional_bound':budget}}
 def run(cmd,data=None):
  row,out,err=rec.run(cmd,cwd=ROOT,data=data,timeout=180,check=False)
  need(row['actual_process_returncode']==0,'command failed: '+row['directory']);return out
 def git(*args,data=None): return run(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args],data)
 def oid(b):
  s=b.decode().strip();need(re.fullmatch('[0-9a-f]{40}',s),'invalid OID');return s
 def snapshot():
  return {'HEAD':git('rev-parse','HEAD').decode(),'index':h((ROOT/'.git/index').read_bytes()),'status':git('status','--porcelain=v1').hex(),'branch':git('branch','--show-current').decode()}
 before=None
 try:
  before=snapshot();need(before['HEAD'].strip()==HEAD and not before['status'],'unexpected writer state')
  need(before['branch'].strip()=='codex/train-337-continue-20261024','wrong writer branch')
  expected_parent_ref=(a.expected_parent+'\trefs/heads/'+BRANCH+'\n').encode()
  need(git('ls-remote','--heads','https://github.com/ZhiQiYang/geometry-axiom.git','refs/heads/'+BRANCH)==expected_parent_ref,'recovery remote parent changed')
  need(git('for-each-ref','--format=%(objectname)','refs/heads/'+BRANCH)==(a.expected_parent+'\n').encode(),'recovery local parent changed')
  need(git('merge-base','--is-ancestor',HEAD,BASE)==b'','anchor not descendant of preserved train HEAD')
  need(git('merge-base','--is-ancestor',BASE,a.expected_parent)==b'','recovery parent outside fixed a6 ancestry')
  need(not git('diff','--name-only',BASE,a.expected_parent,'--','.',':(exclude)evidence'),'recovery parent contains product changes')
  entries={}
  for item in files:
   dst=item['destination'];parts=PurePosixPath(dst).parts;src=Path(item['source_path'])
   need(dst.startswith(PREFIX) and '..' not in parts and '\0' not in dst,'destination outside evidence')
   need(dst not in entries,'duplicate destination');need(src.is_file() and not src.is_symlink(),'missing regular source')
   b=src.read_bytes();need(len(b)==item['bytes'] and h(b)==item['sha256'],'source bytes changed')
   entries[dst]=oid(git('hash-object','-w','--no-filters','--',str(src)))
   need(h(src.read_bytes())==item['sha256'],'source changed during publication')
  def readtree(tree):
   result={}
   if tree:
    for row in git('ls-tree','-z',tree).split(b'\0'):
     if row:
      hdr,name=row.split(b'\t',1);mode,kind,obj=hdr.split(b' ');result[name.decode()]=(mode,kind,obj)
   return result
  def update(tree,changes,prefix=''):
   rows=readtree(tree);groups={}
   for path,blob in changes.items():
    first,sep,tail=path.partition('/');groups.setdefault(first,{})[tail if sep else '']=blob
   for name,g in groups.items():
    old=rows.get(name)
    if '' in g:
     need(len(g)==1,'leaf and subtree collision')
     if old is not None:
      need(prefix+name==PROGRESS and a.expected_progress_blob is not None and old==(b'100644',b'blob',a.expected_progress_blob.encode()),'refuse overwrite except exact explicitly bound PROGRESS blob')
     rows[name]=(b'100644',b'blob',g[''].encode())
    else:
     need(old is None or old[:2]==(b'040000',b'tree'),'file/tree collision')
     child=update(old[2].decode() if old else None,g,prefix+name+'/');rows[name]=(b'040000',b'tree',child.encode())
   stream=b''.join(mode+b' '+kind+b' '+obj+b'\t'+name.encode()+b'\0' for name,(mode,kind,obj) in rows.items())
   out=oid(git('mktree','-z',data=stream));need(readtree(out)==rows,'tree mismatch');return out
  tree=update(oid(git('rev-parse',a.expected_parent+'^{tree}')),entries)
  commit=oid(git('commit-tree',tree,'-p',a.expected_parent,data=b'docs: append recovered architecture and acceptance evidence\n'))
  changed=git('diff-tree','--no-commit-id','--name-only','-r','-z',a.expected_parent,commit).decode().strip('\0').split('\0')
  need(set(changed)==set(entries),'unexpected commit scope')
  need(not git('diff','--name-only',a.expected_parent,commit,'--','.',':(exclude)evidence'),'product changed')
  need(snapshot()==before,'existing writer changed before push')
  need(git('ls-remote','--heads','https://github.com/ZhiQiYang/geometry-axiom.git','refs/heads/'+BRANCH)==expected_parent_ref,'recovery remote moved before local CAS')
  git('update-ref','refs/heads/'+BRANCH,commit,a.expected_parent)
  git('push','https://github.com/ZhiQiYang/geometry-axiom.git','refs/heads/'+BRANCH+':refs/heads/'+BRANCH)
  result.update(published=True,evidence_head=commit,files=len(files));cap.dump(a.out/'RESULT.json',result)
  expected=(commit+'\trefs/heads/'+BRANCH+'\n').encode()
  need(git('ls-remote','--heads','https://github.com/ZhiQiYang/geometry-axiom.git','refs/heads/'+BRANCH)==expected,'remote ref mismatch')
  checked={}
  for item in files:
   blob=entries[item['destination']]
   if blob in checked:continue
   payload=run(['gh','api','--hostname','github.com','-H','Accept: application/vnd.github.raw+json','repos/ZhiQiYang/geometry-axiom/git/blobs/'+blob])
   need(len(payload)==item['bytes'] and h(payload)==item['sha256'],'remote payload mismatch')
   need(hashlib.sha1(b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest()==blob,'remote Git OID mismatch')
   checked[blob]={'bytes':len(payload),'sha256':h(payload)}
  cap.dump(a.out/'REMOTE_BLOBS.json',[dict(blob_oid=blob,**identity) for blob,identity in checked.items()])
  need(git('ls-remote','--heads','https://github.com/ZhiQiYang/geometry-axiom.git','refs/heads/'+BRANCH)==expected,'remote ref moved')
  need(snapshot()==before,'existing writer changed after push')
  result.update(exit_code=0,delivered=True,remote_blobs_verified=len(checked),existing_writer_unchanged=True)
 except BaseException as exc:
  result.update(exit_code=1,error=repr(exc));raise
 finally:cap.dump(a.out/'RESULT.json',result)
 print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
