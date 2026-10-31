from pathlib import Path
import hashlib,importlib.util,json,os,shutil,sys,traceback
H=Path(__file__).resolve().parent;ROOT=Path('/tmp/geo337-reference-local-init-work-20261024');BODYROOT=Path('/tmp/geo337-reference-local-init-prbody-work-20261025');OUT=H/'publication'
S='2c4635577a8fcb11e88b346547f7bb1c7b739fb7';BRANCH='codex/train337-reference-local-init-20261024';DBRANCH=BRANCH+'-prbody';PREFIX='evidence/geo323-reference-local-init-2c463557'
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
def need(v,m):
 if not v:raise RuntimeError(m)
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
 need(not OUT.exists()and not BODYROOT.exists(),'fresh publication');need(shutil.disk_usage('/tmp').free>=64*1024*1024,'64MiB ordinary publication only resource budget on TMP')
 need(sha(CAP.read_bytes())=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762','original capture')
 manifest=json.loads((H/'PUBLICATION_MANIFEST.json').read_bytes());need(manifest['source_sha']==S,'sourcepin');need(manifest['prefix']==PREFIX,'evidence allowlist prefix')
 for name,item in manifest['files'].items():need(name.startswith(PREFIX+'/')and'..'not in Path(name).parts and sha(Path(item['local']).read_bytes())==item['sha256'],'exact evidence before Git '+name)
 template=(H/'PR_BODY.template.md').read_bytes();need(template.count(b'__EVIDENCE_SHA__')==1 and sha(template)==manifest['body_sha256'],'fixed single placeholder body')
 OUT.mkdir();env={k:v for k,v in os.environ.items()if not k.startswith('GIT_')};env['PYTHONDONTWRITEBYTECODE']='1'
 sp=importlib.util.spec_from_file_location('capture',CAP);c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c);rec=c.Recorder(OUT,env,S)
 r={'source_sha':S,'source_branch':BRANCH,'body_branch':DBRANCH,'exit':None,'source_pushed':False,'evidence_pushed':False,'body_pushed':False,'force_push':False,'product_tests_reexecuted':False}
 def git(*a,cwd=ROOT,data=None,check=True):return rec.run(['git','-c','gc.auto=0','-c','maintenance.auto=false',*a],cwd=cwd,data=data,check=check)
 def g(*a,**kw):return git(*a,**kw)[1]
 try:
  need(g('rev-parse','HEAD').decode().strip()==S,'source HEAD');need(g('branch','--show-current').decode().strip()==BRANCH,'owned branch');need(g('status','--porcelain=v1','--untracked-files=all')==b'','clean before E')
  remote=g('ls-remote','--heads','origin',BRANCH).decode();need(remote.strip()==S+'\trefs/heads/'+BRANCH,'remote source still S')
  need(g('ls-remote','--heads','origin',DBRANCH)==b'','fresh owned body remote branch')
  for n,item in manifest['files'].items():
   dst=ROOT/n;need(not dst.exists(),'new exact evidence leaf');dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(item['local'],dst);need(sha(dst.read_bytes())==item['sha256'],'copied evidence bytes')
  g('add','--sparse','-f','--',*manifest['files'])
  need(set(g('diff','--cached','--name-only').decode().splitlines())==set(manifest['files']),'exact stage allowlist')
  g('diff','--cached','--check');g('commit','-m','Record reference initialization proofs and focused validation')
  E=g('rev-parse','HEAD').decode().strip();r['evidence_sha']=E;need(g('show','-s','--format=%P',E).decode().strip()==S,'ordinary E parent S')
  for n in manifest['files']:
   oid=g('hash-object','--',n).decode().strip();need(g('rev-parse',E+':'+n).decode().strip()==oid,'published evidence exact blob')
  need(g('status','--porcelain=v1','--untracked-files=all')==b'','clean E');g('push','origin','HEAD:refs/heads/'+BRANCH);need(g('ls-remote','--heads','origin',BRANCH).decode().strip()==E+'\trefs/heads/'+BRANCH,'remoteE');r['evidence_pushed']=True;r['source_pushed']=True
  g('worktree','add','--no-checkout','-b',DBRANCH,str(BODYROOT),E)
  g('sparse-checkout','set','--no-cone','--stdin',cwd=BODYROOT,data=b'/PR_BODY.md\n')
  indexpath=Path(g('rev-parse','--path-format=absolute','--git-path','index',cwd=BODYROOT).decode().strip());need(not indexpath.exists(),'fresh body index absent')
  g('read-tree','--dry-run','-m','-u',E,cwd=BODYROOT);g('read-tree','-m','-u',E,cwd=BODYROOT);need(g('status','--porcelain=v1','--untracked-files=all',cwd=BODYROOT)==b'','clean body bootstrap')
  body=template.replace(b'__EVIDENCE_SHA__',E.encode());(BODYROOT/'PR_BODY.md').write_bytes(body)
  g('add','--sparse','-f','--','PR_BODY.md',cwd=BODYROOT);need(g('diff','--cached','--name-only',cwd=BODYROOT)==b'PR_BODY.md\n','body only');g('diff','--cached','--check',cwd=BODYROOT);g('commit','-m','Document reference initialization validation state',cwd=BODYROOT)
  D=g('rev-parse','HEAD',cwd=BODYROOT).decode().strip();r.update(body_sha=D,body_sha256=sha(body));need(g('show','-s','--format=%P',D,cwd=BODYROOT).decode().strip()==E,'ordinary D parent E');need(g('show',D+':PR_BODY.md',cwd=BODYROOT)==body,'exact finalbody')
  g('push','origin','HEAD:refs/heads/'+DBRANCH,cwd=BODYROOT);need(g('ls-remote','--heads','origin',DBRANCH,cwd=BODYROOT).decode().strip()==D+'\trefs/heads/'+DBRANCH,'remoteD');r['body_pushed']=True
  need(g('rev-parse','HEAD').decode().strip()==E and g('status','--porcelain=v1','--untracked-files=all')==b'','original E checkout remains clean');r['exit']=0
 except BaseException as e:r.update(exit=1,error=repr(e),traceback=traceback.format_exc())
 finally:dump(OUT/'RESULT.json',r);print(json.dumps(r,ensure_ascii=False),flush=True)
 return r['exit']
if __name__=='__main__':sys.exit(main())
