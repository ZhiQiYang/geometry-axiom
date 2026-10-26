"""Prepare the reviewed recovery publisher's minimal append-only adaptation."""
from pathlib import Path
import ast,difflib,hashlib,json
HERE=Path(__file__).parent
OLD=Path('/tmp/geo337-recover-evidence-publisher-20261026.py')
raw=OLD.read_bytes();assert hashlib.sha256(raw).hexdigest()=='c6a44de7ada360b6017a0e578507b81867471f583d8e9b6b591d56581ba41368'
old=raw.decode();new=old
def change(a,b):
 global new
 assert new.count(a)==1,(a,new.count(a))
 new=new.replace(a,b)
change('"""Publish recovered immutable evidence on a new branch without moving train HEAD."""','"""Append evidence to the fixed recovery branch using ordinary expected-parent CAS."""')
change("BASE='a6f4013364e21bcb7239b5dcc25caac0f6d61f77'","BASE='cbf0fb621888596aa14ad5f2349b503e23b1b72d'")
change("PREFIX='evidence/geo337-train-20261024/'","PREFIX='evidence/geo337-train-20261024/'\nPROGRESS=PREFIX+'resume-20261026/PROGRESS.md'")
change("p.add_argument('--out',type=Path);a=p.parse_args()","p.add_argument('--out',type=Path);p.add_argument('--expected-parent');p.add_argument('--expected-progress-blob');a=p.parse_args()")
change("if not a.execute: print('PLAN_ONLY: new evidence branch; existing HEAD/index/train ref untouched');return","if not a.execute: print('PLAN_ONLY: append recovery evidence with expected-parent CAS; existing HEAD/index/train untouched');return")
change(" need(not sys.flags.optimize,'optimization forbidden')",""" need(not sys.flags.optimize,'optimization forbidden')
 need(isinstance(a.expected_parent,str) and re.fullmatch('[0-9a-f]{40}',a.expected_parent),'explicit full expected-parent SHA')
 need(a.expected_progress_blob is None or re.fullmatch('[0-9a-f]{40}',a.expected_progress_blob),'explicit old progress blob OID or no overwrite')""")
change(" rec=cap.Recorder(a.out,env,BASE)"," rec=cap.Recorder(a.out,env,a.expected_parent)")
change("result={'exit_code':None,'base_sha':BASE,'branch':BRANCH,'source_execution_sha':'82c922a3941525d3a094ac0158bdc7dea57ea360'","result={'exit_code':None,'base_sha':a.expected_parent,'recovery_anchor_sha':BASE,'branch':BRANCH,'source_execution_sha':None,'evidence_source_binding':'Original per-file receipts; publication parent is not relabelled as execution source','allowed_progress_update':PROGRESS,'expected_progress_blob':a.expected_progress_blob")
change("  need(not git('ls-remote','--heads','https://github.com/ZhiQiYang/geometry-axiom.git','refs/heads/'+BRANCH),'recovery remote already exists')","  expected_parent_ref=(a.expected_parent+'\\trefs/heads/'+BRANCH+'\\n').encode()\n  need(git('ls-remote','--heads','https://github.com/ZhiQiYang/geometry-axiom.git','refs/heads/'+BRANCH)==expected_parent_ref,'recovery remote parent changed')")
change("  need(not git('for-each-ref','--format=%(objectname)','refs/heads/'+BRANCH),'recovery local ref already exists')","  need(git('for-each-ref','--format=%(objectname)','refs/heads/'+BRANCH)==(a.expected_parent+'\\n').encode(),'recovery local parent changed')")
change("  need(git('merge-base','--is-ancestor',HEAD,BASE)==b'','base not descendant')","""  need(git('merge-base','--is-ancestor',HEAD,BASE)==b'','anchor not descendant of preserved train HEAD')
  need(git('merge-base','--is-ancestor',BASE,a.expected_parent)==b'','recovery parent outside fixed final-source ancestry')
  need(not git('diff','--name-only',BASE,a.expected_parent,'--','.',':(exclude)evidence'),'recovery parent contains product changes')""")
change("  def update(tree,changes):","  def update(tree,changes,prefix=''):")
change("     need(len(g)==1 and old is None,'refuse existing evidence overwrite')","""     need(len(g)==1,'leaf and subtree collision')
     if old is not None:
      need(prefix+name==PROGRESS and a.expected_progress_blob is not None and old==(b'100644',b'blob',a.expected_progress_blob.encode()),'refuse overwrite except exact explicitly bound PROGRESS blob')""")
change("child=update(old[2].decode() if old else None,g);","child=update(old[2].decode() if old else None,g,prefix+name+'/');")
change("  tree=update(oid(git('rev-parse',BASE+'^{tree}')),entries)","  tree=update(oid(git('rev-parse',a.expected_parent+'^{tree}')),entries)")
change("commit=oid(git('commit-tree',tree,'-p',BASE,data=b'docs: recover completed S10 ledger and original acceptance evidence\\n'))","commit=oid(git('commit-tree',tree,'-p',a.expected_parent,data=b'docs: append recovered architecture and acceptance evidence\\n'))")
change("'--name-only','-r','-z',BASE,commit","'--name-only','-r','-z',a.expected_parent,commit")
change("git('diff','--name-only',BASE,commit,'--','.',':(exclude)evidence')","git('diff','--name-only',a.expected_parent,commit,'--','.',':(exclude)evidence')")
change("  git('update-ref','refs/heads/'+BRANCH,commit,'0'*40)","  need(git('ls-remote','--heads','https://github.com/ZhiQiYang/geometry-axiom.git','refs/heads/'+BRANCH)==expected_parent_ref,'recovery remote moved before local CAS')\n  git('update-ref','refs/heads/'+BRANCH,commit,a.expected_parent)")
ast.parse(new)
(HERE/'publish_append.py').write_text(new)
(HERE/'DIFF.txt').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(OLD),tofile='publish_append.py')))
(HERE/'ORIGINAL_BINDING.json').write_text(json.dumps({'path':str(OLD),'sha256':hashlib.sha256(raw).hexdigest(),'adapted_sha256':hashlib.sha256(new.encode()).hexdigest(),'original_existing_peer_path':'/tmp/geo337-recovery-publisher-list-peer-20261026/REVIEW.json','original_existing_peer_sha256':'34dc74d4ebd91c0f7bf24e30da7e95633a227211c553a7d4d3f07cb952853796','actual_git_mutation_executed':False,'actual_publication_executed':False,'cleanup_related_changes':False},indent=2)+'\n')
print('Prepared only; formal publication requires independent review and root execution.')
