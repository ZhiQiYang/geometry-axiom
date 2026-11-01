from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,traceback
HERE=Path(__file__).resolve().parent;ROOT=Path('/workspace/geometry-axiom');WORK=Path('/tmp/geo323-node-hint-evidence-work-20261024');BODY=Path('/tmp/geo323-node-hint-prbody-work-20261024');OUT=HERE/'publication'
S='a22df116c7e9f6b7d074451f1c8052d59e7e4f3e';BRANCH='codex/train337-node-hint-diagnostic-20261024';DBRANCH=BRANCH+'-prbody';PREFIX='evidence/geo323-node-hint-a22df116'
PACKAGE=Path('/tmp/geo323-node-hint-R-package-20261024');ANALYSIS=Path('/workspace/geo323-node-hint-R-diagnostic-20261024')
report={'source_sha':S,'branch':BRANCH,'body_branch':DBRANCH,'evidence_sha':None,'body_sha':None,'evidence_pushed':False,'body_pushed':False,'commands':[],'exit':None}
def sha(b):return hashlib.sha256(b).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def git(*args,cwd=ROOT,data=None):
 argv=['git','--no-optional-locks','-c','gc.auto=0','-c','maintenance.auto=false',*args];env={k:v for k,v in os.environ.items()if not k.startswith('GIT_')};q=OUT/'commands'/f'{len(report["commands"])+1:03d}';q.mkdir(parents=True)
 if data is not None:(q/'stdin').write_bytes(data)
 r=subprocess.run(argv,cwd=cwd,input=data,capture_output=True,env=env);(q/'stdout').write_bytes(r.stdout);(q/'stderr').write_bytes(r.stderr);row={'argv':argv,'cwd':str(cwd),'exit':r.returncode,'stdout_sha256':sha(r.stdout),'stderr_sha256':sha(r.stderr),'stdin_sha256':None if data is None else sha(data)};dump(q/'result.json',row);report['commands'].append(row);need(r.returncode==0,'original Git command failure '+str(q));return r.stdout
def fresh_worktree(path,branch,parent,patterns):
 need(not path.exists(),'fresh owned worktree')
 need(git('for-each-ref','--format=%(refname)','refs/heads/'+branch)==b'','fresh owned branch')
 need(git('ls-remote','--heads','origin','refs/heads/'+branch)==b'','fresh public branch')
 git('worktree','add','--no-checkout','-b',branch,str(path),parent)
 need(sorted(p.name for p in path.iterdir())==['.git'],'fresh worktree has only .git')
 gd=Path(git('rev-parse','--git-dir',cwd=path).decode().strip());need(not(gd/'index').exists()and not(gd/'index.lock').exists(),'new worktree index absent')
 git('sparse-checkout','set','--no-cone','--stdin',cwd=path,data=patterns)
 git('read-tree','--dry-run','-m','-u',parent,cwd=path);git('read-tree','-m','-u',parent,cwd=path)
 need(git('rev-parse','HEAD',cwd=path).decode().strip()==parent,'fixed original parent')
 need(git('status','--porcelain','--untracked-files=all',cwd=path)==b'','new worktree exact clean')
def main():
 OUT.mkdir(exist_ok=False)
 try:
  report['free_workspace']=shutil.disk_usage('/workspace').free;report['free_tmp']=shutil.disk_usage('/tmp').free
  need(report['free_workspace']>=24*1024*1024 and report['free_tmp']>=24*1024*1024,'index/raw publication storage margin only')
  manifest=json.loads((HERE/'PUBLICATION_MANIFEST.json').read_text());items={k:Path(v['path'])for k,v in manifest['files'].items()}
  need(manifest['source_sha']==S,'one fixed R')
  for k,p in items.items():need(p.is_file()and sha(p.read_bytes())==manifest['files'][k]['sha256'],'reviewed original publication pin '+k)
  template=(HERE/'PR_BODY.template.md').read_bytes();need(sha(template)==manifest['body_template_sha256']and template.count(b'__EVIDENCE_HEAD__')==1,'reviewed unique body placeholder')
  need(set(items)==set(manifest['allowlist'])and all(not x.startswith('/')and'..'not in Path(x).parts for x in items),'exact published relative allowlist')
  fresh_worktree(WORK,BRANCH,S,('/'+PREFIX+'/\n').encode())
  for name,p in items.items():
   dest=WORK/PREFIX/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
  allow=sorted(PREFIX+'/'+n for n in items);git('add','--sparse','-f','--',*allow,cwd=WORK)
  need(git('diff','--cached','--name-only',cwd=WORK).decode().splitlines()==allow,'exact evidence-only index')
  git('diff','--cached','--check',cwd=WORK)
  git('commit','-m','Archive fixed-source node hint diagnostics and preserved preparation failures',cwd=WORK)
  E=git('rev-parse','HEAD',cwd=WORK).decode().strip();report['evidence_sha']=E
  need(git('show','-s','--format=%P',E,cwd=WORK).decode().strip()==S,'normal E parent R')
  need(git('diff-tree','--no-commit-id','--name-only','-r',E,cwd=WORK).decode().splitlines()==allow,'only intended evidence leaves')
  for name,p in items.items():need(git('show',E+':'+PREFIX+'/'+name,cwd=WORK)==p.read_bytes(),'public exact original '+name)
  need(git('status','--porcelain','--untracked-files=all',cwd=WORK)==b'','evidence worktree clean')
  git('push','origin','HEAD:refs/heads/'+BRANCH,cwd=WORK);need(git('ls-remote','--heads','origin','refs/heads/'+BRANCH,cwd=WORK).decode().split()[0]==E,'public E exact');report['evidence_pushed']=True
  fresh_worktree(BODY,DBRANCH,E,b'/PR_BODY.md\n');body=template.replace(b'__EVIDENCE_HEAD__',E.encode());(BODY/'PR_BODY.md').write_bytes(body)
  git('add','--sparse','-f','--','PR_BODY.md',cwd=BODY);need(git('diff','--cached','--name-only',cwd=BODY)==b'PR_BODY.md\n','body-only index');git('diff','--cached','--check',cwd=BODY)
  git('commit','-m','Describe fixed-source diagnostic findings without changing performance gates',cwd=BODY);D=git('rev-parse','HEAD',cwd=BODY).decode().strip();report['body_sha']=D
  need(git('show','-s','--format=%P',D,cwd=BODY).decode().strip()==E,'normal D parent E')
  need(git('diff-tree','--no-commit-id','--name-only','-r',D,cwd=BODY)==b'PR_BODY.md\n','body-only commit')
  need(git('show',D+':PR_BODY.md',cwd=BODY)==body,'exact body E substitution')
  git('push','origin','HEAD:refs/heads/'+DBRANCH,cwd=BODY);need(git('ls-remote','--heads','origin','refs/heads/'+DBRANCH,cwd=BODY).decode().split()[0]==D,'public D exact');report['body_pushed']=True
  need(git('status','--porcelain','--untracked-files=all',cwd=BODY)==b'','body worktree clean');report['exit']=0
 except BaseException:report.update(exit=1,error=traceback.format_exc())
 finally:dump(OUT/'RESULT.json',report);print(json.dumps({k:report.get(k)for k in ['source_sha','evidence_sha','body_sha','evidence_pushed','body_pushed','exit','error']}),flush=True)
 return report['exit']
if __name__=='__main__':sys.exit(main())
