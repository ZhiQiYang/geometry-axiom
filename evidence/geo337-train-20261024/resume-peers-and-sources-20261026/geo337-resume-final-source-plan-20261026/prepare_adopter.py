"""Prepare a pinned candidate-only adaptor copy; never run Git or adoption."""
from pathlib import Path
import hashlib,json,difflib
HERE=Path(__file__).parent
OLD=Path('/tmp/geo337-S10-three-leaf-adoption-preparation-20261025/adopt_three_leaves.py')
old=OLD.read_bytes()
assert hashlib.sha256(old).hexdigest()=='9e53c8275ba8861679bca6cebe16d7a9f8b3436ee5feb13d30d501139e04797b'
s=old.decode()
def replace(a,b):
 global s
 assert s.count(a)==1, (a[:100],s.count(a))
 s=s.replace(a,b)
replace("S10='82c922a3941525d3a094ac0158bdc7dea57ea360'", "S10='82c922a3941525d3a094ac0158bdc7dea57ea360'\nARCH='a6f4013364e21bcb7239b5dcc25caac0f6d61f77'\nHISTORICAL_PUBLISHER_HEAD='3e4f2560aa11ed2a626db98ba5ed6f129e791052'\nHISTORICAL_PROVIDER_BRANCH='codex/train-337-continue-20261024'")
replace("BRANCH='codex/train-337-continue-20261024';ART=", "BRANCH='codex/train337-recovered-evidence-20261026';ART=")
replace("MESSAGE='test: adopt verified S10 ledger and architecture receipts'", "MESSAGE='test: adopt S10 ledger and current architecture receipts on isolated candidate'")
replace("need(ar['sourceSHA']==S10", "need(ar['sourceSHA']==ARCH")
replace("receipt['headObservedAfter']==S10", "receipt['headObservedAfter']==ARCH")
replace("'architecture_actual':{'exit':0,'source':S10", "'architecture_actual':{'exit':0,'source':ARCH")
replace("q['schema']=='S10-three-leaf-byte-adoption/1' and q['source_sha']==S10", "q['schema']=='candidate-S10-A-three-leaf-byte-adoption/1' and q['source_sha']==S10 and q['architecture_source_sha']==ARCH and q['candidate_branch']==BRANCH and q['expected_publisher_head']==HISTORICAL_PUBLISHER_HEAD and q['root_candidate_ref_exclusive']is True")
replace("out.mkdir(mode=0o700);(out/'tmp').mkdir();cap,rec=m.recorder(out);rec.env.update", "out.mkdir(mode=0o700);(out/'tmp').mkdir();cap,rec=m.recorder(out);rec.sha=ARCH;rec.env.update")
replace("'source_sha':S10,'product_source':S10,'previous_head':parent", "'source_sha':ARCH,'ledger_execution_sha':S10,'architecture_execution_sha':ARCH,'product_source':ARCH,'candidate_branch':BRANCH,'previous_head':parent")
replace("source_sha=S10,source_variant='exact three-leaf byte adoption; original executions remain S10'", "source_sha=ARCH,source_variant='candidate exact adoption: ledger executions S10; architecture executions A; neither relabelled F'")
replace(" def clean(expected):need(oid(git('rev-parse','HEAD'))==expected and git('branch','--show-current').decode().strip()==BRANCH and git('status','--porcelain=v1','--untracked-files=all')==b'','exact clean publisher head/branch')", """ def publisher_state():
  return {'head':oid(git('rev-parse','HEAD')),'head_bytes_sha256':H((ROOT/'.git/HEAD').read_bytes()),'index_sha256':H((ROOT/'.git/index').read_bytes()),'branch':git('branch','--show-current').decode().strip(),'train_ref':oid(git('rev-parse','refs/heads/'+HISTORICAL_PROVIDER_BRANCH)),'status_hex':git('status','--porcelain=v1','--untracked-files=all').hex()}
 publisher_before=None
 def clean(expected):
  need(publisher_before is not None and publisher_state()==publisher_before,'historical publisher HEAD/index/train ref/status changed')
  need(oid(git('rev-parse','refs/heads/'+BRANCH))==expected,'candidate local ref moved')""")
replace("source_sha=S10,source_variant='remote exact adopted commit and three blobs, no acceptance rerun'", "source_sha=ARCH,source_variant='remote exact candidate commit and three original blobs, no acceptance rerun'")
replace("before['branch']==BRANCH", "before['branch']==HISTORICAL_PROVIDER_BRANCH")
replace("  clean(parent);need(remote()==parent,'remote parent moved');git('merge-base','--is-ancestor',S10,parent)\n  need(not git('diff','--no-renames','--name-only','-z',S10,parent,'--','.',':(exclude)evidence'),'parent non-evidence closure differs from S10')", """  publisher_before=publisher_state();cap.dump(out/'PUBLISHER_BEFORE.json',publisher_before)
  need(publisher_before['head']==HISTORICAL_PUBLISHER_HEAD and publisher_before['train_ref']==HISTORICAL_PUBLISHER_HEAD and publisher_before['branch']==HISTORICAL_PROVIDER_BRANCH and publisher_before['status_hex']=='','historical publisher identity')
  need(re.fullmatch('[0-9a-f]{64}',q['expected_publisher_index_sha256']) and publisher_before['index_sha256']==q['expected_publisher_index_sha256'],'root-bound original publisher index')
  clean(parent);need(remote()==parent,'candidate remote parent moved');git('merge-base','--is-ancestor',ARCH,parent);git('merge-base','--is-ancestor',S10,ARCH)
  need(paths(git('diff','--no-renames','--name-only','-z',S10,ARCH,'--','.',':(exclude)evidence'))=={'決策佇列.md'},'S10 to A exact decision-only difference')
  delta=q['s10_to_architecture_decision'];need(set(delta)=={'old','new'},'complete decision delta binding')
  for side,rev in [('old',S10),('new',ARCH)]:
   b=git('show',rev+':決策佇列.md');d=delta[side];need(set(d)=={'mode','oid','bytes','sha256'} and d['mode']=='100644' and d['oid']==blob_id(b) and d['bytes']==len(b) and d['sha256']==H(b),'exact original decision blob '+side)
   need(git('ls-tree','-z',rev,'--','決策佇列.md')==b'100644 blob '+d['oid'].encode()+b'\\t'+ '決策佇列.md'.encode()+b'\\0','decision mode binding '+side)
  need(not git('diff','--no-renames','--name-only','-z',ARCH,parent,'--','.',':(exclude)evidence'),'candidate parent non-evidence closure differs from A')""")
replace("original=git('show',S10+':'+name)", "original=git('show',ARCH+':'+name)")
replace("paths(git('diff','--no-renames','--name-only','-z',S10,final,'--','.',':(exclude)evidence'))==CHANGED", "paths(git('diff','--no-renames','--name-only','-z',ARCH,final,'--','.',':(exclude)evidence'))==CHANGED")
replace("  visible=git('sparse-checkout','check-rules','-z',data=b''.join(x.encode()+b'\\0'for x in sorted(CHANGED)));need(visible==b'','three artifacts must remain outside sparse publisher; no large working copy')", "  visible=git('sparse-checkout','check-rules','-z',data=b''.join(x.encode()+b'\\0'for x in sorted(CHANGED)));need(visible==b'','three artifacts must remain outside sparse publisher; no large working copy')\n  need(BRANCH!=HISTORICAL_PROVIDER_BRANCH,'candidate must not be historical train branch')")
replace("  git('merge','--ff-only',final);clean(final);git('push','origin','HEAD:refs/heads/'+BRANCH);need(remote()==final,'remote did not resolve final');result.update(published=True,push_exit=0);save()", "  git('update-ref','refs/heads/'+BRANCH,final,parent);clean(final);git('push','origin','refs/heads/'+BRANCH+':refs/heads/'+BRANCH);need(remote()==final,'remote did not resolve candidate final');result.update(published=True,push_exit=0);save()")
replace("  for name in raws:need(pinned(q['artifacts'][name])==raws[name],'original artifact changed after adoption')", "  for name in raws:need(pinned(q['artifacts'][name])==raws[name],'original artifact changed after adoption')\n  cap.dump(out/'PUBLISHER_AFTER.json',publisher_state());need(publisher_state()==publisher_before,'historical publisher changed after candidate publication')")
replace("result.update(exit_code=0,delivered=True,changed_paths=sorted(changed)", "result.update(exit_code=0,delivered=True,historical_publisher_unchanged=True,changed_paths=sorted(changed)")
replace("  if before is not None:\n   try:", "  if publisher_before is not None:\n   try:\n    current=publisher_state();cap.dump(out/'PUBLISHER_FINAL.json',current)\n    if current!=publisher_before:result.update(exit_code=1,delivered=False,historical_publisher_error='original publisher HEAD/index/train ref/status changed')\n   except BaseException as exc:result.update(exit_code=1,delivered=False,historical_publisher_error=repr(exc))\n  if before is not None:\n   try:")
replace('Root-only exact S10 ledger/architecture byte adoption; default does nothing.', 'Root-only S10 ledger/A architecture adoption on one isolated candidate; default does nothing.')
target=HERE/'adopt_candidate_three_leaves.py'
assert not target.exists();target.write_text(s)
(HERE/'ADOPTER_DELTA.diff').write_text(''.join(difflib.unified_diff(old.decode().splitlines(True),s.splitlines(True),fromfile=str(OLD),tofile=str(target))))
import ast
ast.parse(s)
print(json.dumps({'path':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size,'executed':False}))
