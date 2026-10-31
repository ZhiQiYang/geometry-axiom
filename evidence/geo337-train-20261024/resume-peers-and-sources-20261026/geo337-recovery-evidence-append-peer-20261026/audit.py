import ast,copy,datetime,hashlib,json,subprocess,sys,types
from pathlib import Path,PurePosixPath

OUT=Path(__file__).parent
SUBJECT=Path('/tmp/geo337-recovery-evidence-append-preparation-20261026/publish_append.py')
ORIGINAL=Path('/tmp/geo337-recover-evidence-publisher-20261026.py')
F='cbf0fb621888596aa14ad5f2349b503e23b1b72d'
PREFIX='evidence/geo337-train-20261024/'
PROGRESS=PREFIX+'resume-20261026/PROGRESS.md'
OVERWRITE='refuse overwrite except exact explicitly bound PROGRESS blob'
def sha(b):return hashlib.sha256(b).hexdigest()
def need(ok,msg):
 if not ok:raise RuntimeError(msg)
def parsed():
 t=ast.parse(SUBJECT.read_bytes());m=next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name=='main');return t,m
def helper(m,name):return next(n for n in ast.walk(m)if isinstance(n,ast.FunctionDef)and n.name==name)
def guard(m,message):return next(n for n in ast.walk(m)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='need'and len(n.args)>1 and isinstance(n.args[1],ast.Constant)and n.args[1].value==message)
def evaluate_guard(m,message,ns):
 return eval(compile(ast.Expression(copy.deepcopy(guard(m,message))),'<exact-real-guard>','eval'),{'need':need,**ns})
def probe(phase):
 _,m=parsed();node=copy.deepcopy(helper(m,'update'))
 if phase=='withdrawn':
  class Withdraw(ast.NodeTransformer):
   def visit_Expr(self,n):
    c=n.value
    if isinstance(c,ast.Call)and isinstance(c.func,ast.Name)and c.func.id=='need'and len(c.args)>1 and isinstance(c.args[1],ast.Constant)and c.args[1].value==OVERWRITE:return ast.copy_location(ast.Pass(),n)
    return self.generic_visit(n)
  node=Withdraw().visit(node)
 trees={}
 def readtree(key):return dict(trees.get(key,{}))
 def git(*args,data=None):
  assert args==('mktree','-z'),'unexpected simulated command'
  rows={}
  for row in data.split(b'\0'):
   if row:
    hdr,name=row.split(b'\t',1);mode,kind,obj=hdr.split(b' ');assert name and b'/'not in name;rows[name.decode()]=(mode,kind,obj)
  key=hashlib.sha1(data).hexdigest();trees[key]=rows;return(key+'\n').encode()
 ns={'readtree':readtree,'git':git,'oid':lambda b:b.decode().strip(),'need':need,'a':types.SimpleNamespace(expected_progress_blob='a'*40),'PROGRESS':PROGRESS}
 exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<real-update-helper>','exec'),ns)
 update=ns['update'];other=PREFIX+'raw-original/RESULT.json';new=PREFIX+'append-new/RESULT.json'
 base=update(None,{PROGRESS:'a'*40,other:'b'*40})
 initial=copy.deepcopy(trees)
 def leaves(tree,prefix=''):
  result={}
  for name,(_,kind,obj)in readtree(tree).items():
   if kind==b'tree':result.update(leaves(obj.decode(),prefix+name+'/'))
   else:result[prefix+name]=obj.decode()
  return result
 changed=update(base,{PROGRESS:'c'*40,new:'d'*40})
 assert leaves(changed)=={PROGRESS:'c'*40,other:'b'*40,new:'d'*40},'positive exact PROGRESS/new path failed'
 assert all(trees[k]==v for k,v in initial.items()),'old tree was modified'
 try:update(base,{other:'e'*40})
 except RuntimeError as e:assert str(e)==OVERWRITE
 else:raise AssertionError('UNAUTHORIZED_EVIDENCE_OVERWRITE_NOT_REJECTED')
 for value in [None,'f'*40]:
  ns['a'].expected_progress_blob=value
  try:update(base,{PROGRESS:'c'*40})
  except RuntimeError as e:assert str(e)==OVERWRITE
  else:raise AssertionError('STALE_OR_UNBOUND_PROGRESS_NOT_REJECTED')
 print(json.dumps({'phase':phase,'exit_code':0,'real_helper_used':True,'memory_only':True,'formal_git_network_or_cleanup_executed':False}))

def main():
 old=ORIGINAL.read_bytes();new=SUBJECT.read_bytes();t,m=parsed();ot=ast.parse(old);om=next(x for x in ot.body if isinstance(x,ast.FunctionDef)and x.name=='main');s=new.decode();osrc=old.decode();checks=[]
 def check(ok,msg):need(ok,msg);checks.append(msg)
 check(sha(old)=='c6a44de7ada360b6017a0e578507b81867471f583d8e9b6b591d56581ba41368','original publisher exact pin')
 constants={n.targets[0].id:ast.literal_eval(n.value)for n in t.body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and isinstance(n.value,ast.Constant)}
 check(constants['BASE']==F,'fixed final source anchor')
 check(constants['HEAD']=='3e4f2560aa11ed2a626db98ba5ed6f129e791052','historical writer HEAD fixed')
 check(constants['BRANCH']=='codex/train337-recovered-evidence-20261026','only owned evidence branch fixed')
 check(constants['PREFIX']==PREFIX and "PROGRESS=PREFIX+'resume-20261026/PROGRESS.md'"in s,'one fixed overwrite path')
 for n in ['run','git','oid','snapshot','readtree']:check(ast.dump(helper(m,n))==ast.dump(helper(om,n)),'unchanged helper '+n)
 lo=' total=sum(';hi=' spec=importlib.util'
 check(s[s.index(lo):s.index(hi)]==osrc[osrc.index(lo):osrc.index(hi)],'capacity accounting and 2GiB/actual mount reserve unchanged')
 lo='  checked={}\n';hi="  need(snapshot()==before,'existing writer changed after push')"
 check(s[s.index(lo):s.index(hi)]==osrc[osrc.index(lo):osrc.index(hi)],'full remote bytes/SHA256/Git OID and final ref unchanged')
 for text in ["env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')}","need(snapshot()==before,'existing writer changed before push')","need(snapshot()==before,'existing writer changed after push')","git('update-ref','refs/heads/'+BRANCH,commit,a.expected_parent)","git('push','https://github.com/ZhiQiYang/geometry-axiom.git','refs/heads/'+BRANCH+':refs/heads/'+BRANCH)","need(not git('diff','--name-only',BASE,a.expected_parent,'--','.',':(exclude)evidence'),'recovery parent contains product changes')","need(not git('diff','--name-only',a.expected_parent,commit,'--','.',':(exclude)evidence'),'product changed')","need(set(changed)==set(entries),'unexpected commit scope')","source_execution_sha':None"]:check(text in s,'present '+text)
 calls=[n for n in ast.walk(m)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='git']
 pushes=[n for n in calls if n.args and isinstance(n.args[0],ast.Constant)and n.args[0].value=='push']
 updates=[n for n in calls if n.args and isinstance(n.args[0],ast.Constant)and n.args[0].value=='update-ref']
 check(len(pushes)==1 and len(updates)==1,'one ordinary fixed-branch push and one expected-parent CAS')
 forbidden=['--force','--force-with-lease','reset','checkout','clean','merge','rebase','symbolic-ref','read-tree','add','rm']
 check(not any(isinstance(n,ast.Constant)and isinstance(n.value,str)and n.value in forbidden for n in ast.walk(t)),'no force/worktree/index-changing Git command')
 check(not any(isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr in ['unlink','rmdir','rmtree','remove','rename','replace']for n in ast.walk(t)),'no cleanup/deletion/ref-moving filesystem action')
 for dst,accepted in [(PREFIX+'new/receipt.json',True),('tests/mutate.py',False),(PREFIX+'../../tests/mutate.py',False),(PREFIX+'new\0bad',False)]:
  try:evaluate_guard(m,'destination outside evidence',{'dst':dst,'parts':PurePosixPath(dst).parts,'PREFIX':PREFIX});actual=True
  except RuntimeError as e:need(str(e)=='destination outside evidence','unexpected path rejection');actual=False
  check(actual==accepted,'exact destination guard '+repr(dst))
 for mismatch in [False,True]:
  expected=(F+'\trefs/heads/'+constants['BRANCH']+'\n').encode();actual=expected if not mismatch else ('f'*40+'\trefs/heads/'+constants['BRANCH']+'\n').encode()
  try:evaluate_guard(m,'recovery remote parent changed',{'git':lambda *args:actual,'BRANCH':constants['BRANCH'],'expected_parent_ref':expected});accepted=True
  except RuntimeError as e:need(str(e)=='recovery remote parent changed','unexpected remote rejection');accepted=False
  check(accepted!=mismatch,'exact remote parent '+('stale rejected'if mismatch else 'matching accepted'))
 for changed in [b'',b'tests/mutants_results.json\n']:
  try:evaluate_guard(m,'recovery parent contains product changes',{'git':lambda *args:changed,'BASE':F,'a':types.SimpleNamespace(expected_parent=F)});accepted=True
  except RuntimeError as e:need(str(e)=='recovery parent contains product changes','unexpected closure rejection');accepted=False
  check(accepted==(not bool(changed)),'final anchor closure '+('clean accepted'if not changed else 'unknown product rejected'))
 rows=[]
 for phase,exit_code in [('fixed',0),('withdrawn',1),('restored',0)]:
  argv=['python3','-B',str(Path(__file__)),'--probe',phase];p=subprocess.run(argv,capture_output=True,text=True)
  rows.append({'argv':argv,'actual_process_returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
  check(p.returncode==exit_code,'real helper overwrite guard counterproof '+phase)
  if phase=='withdrawn':check('UNAUTHORIZED_EVIDENCE_OVERWRITE_NOT_REJECTED'in p.stderr,'withdrawal hits exact assertion')
 (OUT/'MEMORY_PROOF.json').write_text(json.dumps({'subject_sha256':sha(new),'commands':rows,'formal_git_network_or_cleanup_executed':False},ensure_ascii=False,indent=2)+'\n')
 need(SUBJECT.read_bytes()==new,'subject changed during review')
 report={'schema':'recovery-evidence-append-independent-static-peer/1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':0,'blocking_findings':[],'subject_path':str(SUBJECT),'subject_sha256':sha(new),'original_subject_sha256':sha(old),'fixed_source_anchor':F,'checks':len(checks),'accepted_checks':checks,'counterproof_exits':[r['actual_process_returncode']for r in rows],'original_initial_finding_retained':'REVIEW.initial.json','formal_refs_network_or_cleanup_executed':False,'actual_publication_certified':False,'limits':['Static and extracted real-helper memory proof only; actual append manifest, expected parent/PROGRESS OID, capacity, publisher snapshots and remote full blobs still require original execution receipts.','Append failure after local CAS may leave the owned recovery ref advanced locally with delivered=false; no rollback or forced retry is authorized by this review.','Only fixed resume-20261026/PROGRESS.md may replace an existing 100644 blob with exact caller-bound old OID; all other old evidence remains immutable.','Source_execution_sha stays null at publication level; per-file receipts retain their original execution SHA.']}
 (OUT/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'exit_code':0,'checks':len(checks),'subject_sha256':sha(new),'review_sha256':sha((OUT/'REVIEW.json').read_bytes()),'counterproof_exits':report['counterproof_exits']}))

if __name__=='__main__':
 if len(sys.argv)==3 and sys.argv[1]=='--probe':probe(sys.argv[2])
 else:main()
