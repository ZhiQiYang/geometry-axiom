"""Publish accepted original six-phase evidence and a body with one current matrix."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,os,shutil,traceback
P=Path(__file__).resolve().parent;O=P/'publication';R=Path('/workspace/issue214-http-fixture-work-20261024')
S='2199cda8896b47c7ad2b6c10479e5e0cbdb67c83';E0='9896410a84b31fb742b5e92bc5601715bf242267';D0='ac478611e683c3b5684104e811804acaa23a1558'
B='codex/issue214-http-fixture-20261024';PREFIX='evidence/geo345-final-2199cda8';URL='https://github.com/ZhiQiYang/geometry-axiom.git'
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
def sha(b):return hashlib.sha256(b).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
manifest=json.loads((P/'PUBLICATION_FILES.json').read_bytes())
need(not O.exists(),'fresh publication output');need(sha(CAP.read_bytes())=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762','original capture')
for x in manifest['files']:
 raw=Path(x['source']).read_bytes();need(len(raw)==x['bytes'] and sha(raw)==x['sha256'],'exact publication input '+x['name'])
need(sha((P/'PR_BODY.template.md').read_bytes())==manifest['body_sha256'],'frozen body')
need(shutil.disk_usage('/workspace').free>=20*1024*1024,'20MiB metadata publication storage admission')
O.mkdir();env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',GIT_OPTIONAL_LOCKS='0',GIT_NO_LAZY_FETCH='1',LANG='C.UTF-8',LC_ALL='C.UTF-8')
for k in list(env):
 if k.startswith('GIT_') and k not in ('GIT_OPTIONAL_LOCKS','GIT_NO_LAZY_FETCH') or k in ('PYTHONOPTIMIZE','PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','LD_PRELOAD'):env.pop(k)
spec=importlib.util.spec_from_file_location('cap',CAP);cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap);rec=cap.Recorder(O,env,S)
report={'source_sha':S,'source_branch':B,'evidence_parent':E0,'body_parent':D0,'exit':None,'pushed':{},'errors':[],'no_product_test_ledger_architecture_changes':True,'formal_run_by_publisher':False}
def git(*args,data=None,index=None):
 cmd=['git','-c','gc.auto=0','-c','maintenance.auto=false','-c','remote.origin.url='+URL,*args]
 if index:cmd=['env','GIT_INDEX_FILE='+str(index),*cmd]
 row,out,err=rec.run(cmd,cwd=R,data=data,timeout=None,check=False,source_sha=S,source_variant='evidence-publication-only')
 need(row['actual_process_returncode']==0,'original Git failure '+row['directory']);return out
def head(branch):
 rows=git('ls-remote','--heads','origin','refs/heads/'+branch).decode().splitlines();need(len(rows)==1 and rows[0].split('\t')[1]=='refs/heads/'+branch,'one exact remote ref');return rows[0].split('\t')[0]
def source_guard():
 need(git('rev-parse','HEAD').decode().strip()==S and git('rev-parse','--abbrev-ref','HEAD').strip()==b'HEAD','original tested source remains detached S')
 need(git('status','--porcelain=v1','--untracked-files=all')==b'' and git('diff','--cached','--name-status')==b'','original tested worktree and index clean')
def tree_for(old,files,label):
 index=O/(label+'.index');need(not index.exists(),'fresh separate metadata index');git('read-tree',old,index=index)
 for name,raw in files.items():
  oid=git('hash-object','-w','--stdin',data=raw).decode().strip();git('update-index','--add','--cacheinfo','100644,'+oid+','+name,index=index)
 return git('write-tree',index=index).decode().strip()
try:
 source_guard();need(git('rev-parse','refs/heads/'+B).decode().strip()==E0 and git('rev-parse','refs/heads/'+B+'-prbody').decode().strip()==D0,'owned local parent pins')
 need(head(B)==E0 and head(B+'-prbody')==D0,'remote parents exact; no force')
 need(all(p.startswith('evidence/') for p in git('diff','--name-only',S,E0).decode().splitlines()),'old E has exact original source closure')
 need(git('ls-tree',E0,'--',PREFIX)==b'','new evidence prefix only')
 files={PREFIX+'/'+x['name']:Path(x['source']).read_bytes()for x in manifest['files']}
 files[PREFIX+'/PUBLICATION_INDEX.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
 tree=tree_for(E0,files,'evidence')
 delta=git('diff-tree','--no-commit-id','--name-status','-r',E0,tree).decode().splitlines();need(sorted(delta)==sorted('A\t'+p for p in files),'only exact new evidence additions; preserve all old source and omitted receipts')
 git('diff','--check',E0,tree)
 E=git('commit-tree',tree,'-p',E0,data=b'Record original HTTP fixture timing and equivalent withdrawal evidence\n').decode().strip()
 need(git('show','-s','--format=%P',E).decode().strip()==E0,'normal evidence parent')
 template=(P/'PR_BODY.template.md').read_text();need(template.count('__EVIDENCE_HEAD__')==1,'one current evidence placeholder');body=template.replace('__EVIDENCE_HEAD__',E).encode();(O/'PR_BODY.md').write_bytes(body)
 dtree=tree_for(D0,{'PR_BODY.md':body},'body');need(git('diff-tree','--no-commit-id','--name-status','-r',D0,dtree).decode().splitlines()==['M\tPR_BODY.md'],'only body changes')
 D=git('commit-tree',dtree,'-p',D0,data=b'Update HTTP fixture PR body with six original acceptance phases\n').decode().strip();need(git('show','-s','--format=%P',D).decode().strip()==D0,'normal body parent')
 report.update(evidence_sha=E,body_sha=D,body_sha256=sha(body));dump(O/'LIVE.json',report)
 need(head(B)==E0 and head(B+'-prbody')==D0,'remote parents still exact')
 git('update-ref','refs/heads/'+B,E,E0);git('push','origin',E+':refs/heads/'+B);need(head(B)==E,'published evidence exact');report['pushed']['evidence']=True;dump(O/'LIVE.json',report)
 git('update-ref','refs/heads/'+B+'-prbody',D,D0);git('push','origin',D+':refs/heads/'+B+'-prbody');need(head(B+'-prbody')==D,'published body exact');report['pushed']['body']=True
 source_guard();report['exit']=0
except BaseException as exc:report['exit']=1;report['errors'].append(traceback.format_exc())
finally:
 report['commands']=rec.rows;report['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();dump(O/'RESULT.json',report);print(json.dumps({k:v for k,v in report.items()if k!='commands'},ensure_ascii=False))
raise SystemExit(report['exit'])
