"""Tiny real Git tests of extracted candidate primitives, not formal adoption."""
from pathlib import Path
import argparse,ast,hashlib,importlib.util,json,os,sys,traceback
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
CAP_PIN='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
OWN=Path('/dev/shm/geometry-axiom-geo337-20261025')
def H(b):return hashlib.sha256(b).hexdigest()
def need(c,m):
 if not c:raise AssertionError(m)
def load(path,name):
 sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--subject',type=Path);p.add_argument('--subject-sha256');p.add_argument('--out',type=Path);p.add_argument('--case',choices=['cas','scope','preservation']);p.add_argument('--phase',choices=['fixed','withdrawn','restored']);a=p.parse_args()
 if not a.execute:print('PREPARATION_ONLY; no Git or source access');return 0
 need(not sys.flags.optimize,'assertions enabled')
 need(a.out.parent.parent==OWN and a.out.parent.name.startswith('geo337-candidate-adopter-tiny-') and a.out.parent.is_dir() and not a.out.exists(),'fresh root-bound tiny phase only')
 need(a.out.parent.resolve()==a.out.parent and not a.out.parent.is_symlink(),'canonical synthetic parent')
 subject_raw=a.subject.read_bytes();need(H(subject_raw)==a.subject_sha256,'subject pin');need(H(CAP.read_bytes())==CAP_PIN,'capture pin')
 a.out.mkdir();tmp=a.out/'tmp';tmp.mkdir();hooks=a.out/'empty-hooks';hooks.mkdir();templates=a.out/'empty-template';templates.mkdir();root=a.out/'work';remote=a.out/'local-remote.git'
 env={k:v for k,v in os.environ.items()if not k.startswith('GIT_') and k not in ('PYTHONPATH','PYTHONHOME','PYTHONOPTIMIZE','PYTHONSTARTUP','PYTHONPYCACHEPREFIX')}
 env.update(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_AUTHOR_NAME='Synthetic candidate proof',GIT_AUTHOR_EMAIL='fixture@example.invalid',GIT_COMMITTER_NAME='Synthetic candidate proof',GIT_COMMITTER_EMAIL='fixture@example.invalid',GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(tmp),TMP=str(tmp),TEMP=str(tmp),LC_ALL='C.UTF-8',LANG='C.UTF-8')
 cap=load(CAP,'cap');rec=cap.Recorder(a.out/'git-original',env,'SYNTHETIC_CANDIDATE_PRIMITIVES_ONLY');m=load(a.subject,'candidate_subject')
 result={'exit_code':1,'case':a.case,'phase':a.phase,'subject_sha256':a.subject_sha256,'formal_adoption_executed':False,'product_tests_executed':False,'network_used':False,'synthetic_schema_not_formal_acceptance':True,'original_capture_sha256':CAP_PIN}
 def command(argv,*,cwd=a.out,data=None,allow_nonzero=False):
  row,b,e=rec.run(['git','-c','gc.auto=0','-c','maintenance.auto=false','-c','core.hooksPath='+str(hooks),'-c','protocol.file.allow=always',*argv],cwd=cwd,data=data,timeout=30,check=False)
  need(not row['timeout_expired'],'synthetic Git timeout cannot be counterproof')
  if not allow_nonzero:need(row['actual_process_returncode']==0,'synthetic Git failure: '+row['directory'])
  return row,b,e
 def git(*args,data=None):return command(list(args),cwd=root,data=data)[1]
 try:
  command(['init','--template='+str(templates),str(root)])
  command(['init','--bare','--template='+str(templates),str(remote)])
  git('symbolic-ref','HEAD','refs/heads/'+m.HISTORICAL_PROVIDER_BRANCH)
  git('remote','add','origin',str(remote))
  leaves={n:m.oid(git('hash-object','-w','--stdin',data=('old '+n+'\n').encode()))for n in sorted(m.CHANGED|m.UNCHANGED|{'evidence/history.txt','geometry-core/domain-decoupling/unknown-source.c'})}
  def initial_tree(items):
   groups={}
   for path,blob in items.items():
    first,sep,tail=path.partition('/');groups.setdefault(first,{})[tail if sep else '']=blob
   rows=[]
   for name,g in groups.items():rows.append((b'100644 blob '+g[''].encode() if '' in g else b'040000 tree '+initial_tree(g).encode())+b'\t'+name.encode()+b'\0')
   return m.oid(git('mktree','-z',data=b''.join(rows)))
  tree=initial_tree(leaves);base=m.oid(git('commit-tree',tree,data=b'synthetic base\n'))
  git('update-ref','refs/heads/'+m.HISTORICAL_PROVIDER_BRANCH,base,'0'*40)
  git('read-tree','--reset','-u',base)
  git('update-ref','refs/heads/'+m.BRANCH,base,'0'*40)
  git('push','origin','refs/heads/'+m.HISTORICAL_PROVIDER_BRANCH+':refs/heads/'+m.HISTORICAL_PROVIDER_BRANCH,'refs/heads/'+m.BRANCH+':refs/heads/'+m.BRANCH)
  program=ast.parse(subject_raw);main_ast=next(n for n in program.body if isinstance(n,ast.FunctionDef)and n.name=='main')
  functions={n.name:n for n in main_ast.body if isinstance(n,ast.FunctionDef)}
  need('publisher_state'in functions and 'clean'in functions,'exact subject primitives')
  normal_clean=functions['clean'];normal_state=functions['publisher_state']
  calls=[n for n in ast.walk(main_ast)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='git'and len(n.args)>=1 and isinstance(n.args[0],ast.Constant)and n.args[0].value=='update-ref']
  need(len(calls)==1 and len(calls[0].args)==4,'exact original candidate CAS primitive')
  cas=calls[0];(a.out/'ORIGINAL_PRIMITIVES.py.txt').write_text(ast.unparse(ast.Module(body=[normal_state,normal_clean,ast.Expr(cas)],type_ignores=[]))+'\n')
  ns={'git':git,'ROOT':root,'BRANCH':m.BRANCH,'HISTORICAL_PROVIDER_BRANCH':m.HISTORICAL_PROVIDER_BRANCH,'oid':m.oid,'H':m.H,'need':m.need,'publisher_before':None}
  exec(compile(ast.fix_missing_locations(ast.Module(body=[normal_state,normal_clean],type_ignores=[])),str(a.subject),'exec'),ns)
  original=ns['publisher_state']();ns['publisher_before']=original
  need(original['head']==base and original['branch']==m.HISTORICAL_PROVIDER_BRANCH and original['train_ref']==base and original['status_hex']=='','synthetic original state')
  patch={n:m.oid(git('hash-object','-w','--stdin',data=('new '+n+'\n').encode()))for n in sorted(m.CHANGED)}
  newtree=m.build_tree(git,tree,patch);tip=m.oid(git('commit-tree',newtree,'-p',base,data=b'synthetic three leaves\n'))
  delta=m.paths(git('diff-tree','--no-commit-id','--no-renames','--name-only','-r','-z',base,tip));need(delta==m.CHANGED,'positive exact three leaves')
  for name,blob in leaves.items():
   if name not in m.CHANGED:need(m.oid(git('rev-parse',tip+':'+name))==blob,'other original leaf changed')
  ns.update(final=tip,parent=base);ns['clean'](base)
  exec(compile(ast.fix_missing_locations(ast.Expression(cas)),str(a.subject),'eval'),ns)
  ns['clean'](tip);git('push','origin','refs/heads/'+m.BRANCH+':refs/heads/'+m.BRANCH)
  remote_rows=git('ls-remote','--heads','origin','refs/heads/'+m.BRANCH,'refs/heads/'+m.HISTORICAL_PROVIDER_BRANCH).decode().splitlines();remote_refs={x.split('\t')[1]:x.split('\t')[0]for x in remote_rows}
  need(remote_refs=={'refs/heads/'+m.BRANCH:tip,'refs/heads/'+m.HISTORICAL_PROVIDER_BRANCH:base},'synthetic normal push scope')
  need(ns['publisher_state']()==original,'positive changed original publisher')
  result.update(base=base,tip=tip,positive_three_leaf_cas_and_push=True,positive_original_state=original,positive_state_after=ns['publisher_state'](),synthetic_remote_refs=remote_refs)
  if a.case=='cas':
   desired=m.oid(git('commit-tree',newtree,'-p',tip,data=b'synthetic desired child\n'));race=m.oid(git('commit-tree',newtree,'-p',tip,data=b'synthetic concurrent child\n'))
   ns['clean'](tip);git('update-ref','refs/heads/'+m.BRANCH,race,tip);ns.update(final=desired,parent=tip)
   selected=ast.parse(ast.unparse(cas),mode='eval').body
   if a.phase=='withdrawn':selected.args=selected.args[:-1]
   (a.out/'SELECTED_CAS.py.txt').write_text(ast.unparse(selected)+'\n')
   failures=[]
   def cas_git(*args,data=None):
    row,b,e=command(list(args),cwd=root,data=data,allow_nonzero=True);failures.append({'returncode':row['actual_process_returncode'],'stdout':b.hex(),'stderr':e.hex(),'directory':row['directory']});return b
   ns['git']=cas_git;eval(compile(ast.fix_missing_locations(ast.Expression(selected)),str(a.subject),'eval'),ns);ns['git']=git
   after=m.oid(git('rev-parse','refs/heads/'+m.BRANCH));need(len(failures)==1,'one real CAS command')
   row=failures[0];text=bytes.fromhex(row['stderr']);refused=row['returncode']!=0 and after==race and tip.encode()in text and race.encode()in text and b'expected'in text
   result['wrong_expected_parent']={'command':row,'candidate_after':after,'race':race,'desired':desired,'expected_old':tip,'refused':refused}
   need(ns['publisher_state']()==original,'CAS case changed original state')
   need(refused,'CAS_EXPECTED_PARENT_NOT_ENFORCED')
  elif a.case=='scope':
   bad='geometry-core/domain-decoupling/unknown-source.c';badpatch=dict(patch);badpatch[bad]=m.oid(git('hash-object','-w','--stdin',data=b'illegal fourth source\n'))
   if a.phase=='withdrawn':m.CHANGED=m.CHANGED|{bad}
   refused=False
   try:m.build_tree(git,tree,badpatch)
   except RuntimeError as exc:need(str(exc)=='exact three adoption leaves only','unexpected scope error');refused=True
   result['fourth_product_leaf']={'refused':refused,'withdrawal':'in-memory CHANGED includes one existing fourth product leaf'if a.phase=='withdrawn'else None}
   need(ns['publisher_state']()==original,'scope case changed original state');need(refused,'FOURTH_PRODUCT_PATH_NOT_REFUSED')
  else:
   selected=ast.parse(ast.unparse(normal_clean)).body[0]
   if a.phase=='withdrawn':selected.body[0]=ast.Pass()
   (a.out/'SELECTED_CLEAN.py.txt').write_text(ast.unparse(selected)+'\n');exec(compile(ast.fix_missing_locations(ast.Module(body=[selected],type_ignores=[])),str(a.subject),'exec'),ns)
   headraw=(root/'.git/HEAD').read_bytes();indexraw=(root/'.git/index').read_bytes();shadow='refs/heads/synthetic-shadow';git('update-ref',shadow,base,'0'*40)
   race=m.oid(git('commit-tree',tree,'-p',base,data=b'synthetic original-state mutation\n'));observed=[]
   for field in ['HEAD','index','train_ref']:
    try:
     if field=='HEAD':git('symbolic-ref','HEAD',shadow)
     elif field=='index':git('update-index','--add','--cacheinfo','100644',leaves['evidence/history.txt'],'synthetic-extra.txt')
     else:git('update-ref','refs/heads/'+m.HISTORICAL_PROVIDER_BRANCH,race,base)
     changed=ns['publisher_state']();need(changed!=original,'synthetic state mutation did not occur');refused=False
     try:ns['clean'](tip)
     except RuntimeError as exc:need(str(exc)=='historical publisher HEAD/index/train ref/status changed','unexpected state refusal');refused=True
     observed.append({'field':field,'changed_state':changed,'refused':refused})
    finally:
     if field=='HEAD':(root/'.git/HEAD').write_bytes(headraw)
     elif field=='index':(root/'.git/index').write_bytes(indexraw)
     else:git('update-ref','refs/heads/'+m.HISTORICAL_PROVIDER_BRANCH,base,race)
     need(ns['publisher_state']()==original,'synthetic original state not restored')
   result['state_counterexamples']=observed;need(all(x['refused']for x in observed),'HISTORICAL_PUBLISHER_CHANGE_NOT_DETECTED')
  result.update(exit_code=0,original_publisher_state_preserved=True)
 except BaseException as exc:
  result.update(exit_code=1,error_type=type(exc).__name__,error=str(exc));traceback.print_exc()
 finally:cap.dump(a.out/'RESULT.json',result)
 print(json.dumps({k:result.get(k)for k in ['case','phase','exit_code','error','positive_three_leaf_cas_and_push','formal_adoption_executed']}));return result['exit_code']
if __name__=='__main__':raise SystemExit(main())
