"""Root-only S10 ledger/A architecture adoption on one isolated candidate; default does nothing.
Tree construction and normal ff/push follow the accepted private SHM publisher.
No tests, source transition, ledger head rewriting, or original-provider writes.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,re,shutil,stat,sys
S10='82c922a3941525d3a094ac0158bdc7dea57ea360'
ARCH='a6f4013364e21bcb7239b5dcc25caac0f6d61f77'
HISTORICAL_PUBLISHER_HEAD='3e4f2560aa11ed2a626db98ba5ed6f129e791052'
HISTORICAL_PROVIDER_BRANCH='codex/train-337-continue-20261024'
OWN=Path('/dev/shm/geometry-axiom-geo337-20261025');ROOT=OWN/'publisher-source'
BRANCH='codex/train337-recovered-evidence-20261026';ART='geometry-core/domain-decoupling/'
LEDGER='tests/mutants_results.json';REPORT=ART+'PRODUCT-ARCHITECTURE.md';RECEIPT=ART+'product-architecture-receipt.json'
CHANGED=frozenset([LEDGER,REPORT,RECEIPT]);UNCHANGED=frozenset([ART+'product-architecture.json',ART+'product-architecture-scan.json'])
HELPER=Path('/workspace/geo337-F10-shm-publication-preparation-20261025/bootstrap_private_publisher.py');HELPER_PIN='bcc565b8b4d12e65aa4bf81e00d7adc4634960e7f37fc67f789851b3eafde659'
PUBLISHER=HELPER.parent/'publish_evidence_shm_v2.py';PUBLISHER_PIN='3ef65a16e289ece72d2bdc9f9a7f48347af13f2192016b79f33ebc9539bdf4a7'
MESSAGE='test: adopt S10 ledger and current architecture receipts on isolated candidate'
def need(ok,why):
 if not ok:raise RuntimeError(why)
def H(raw):return hashlib.sha256(raw).hexdigest()
def blob_id(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def oid(raw):
 value=raw.decode().strip();need(re.fullmatch('[0-9a-f]{40}',value),'exact Git OID');return value
def safe(p):
 p=Path(p);need(p.is_absolute() and '..'not in p.parts and all(not x.is_symlink()for x in (p,*p.parents)),'absolute nonalias path');return p
def pinned(item):
 p=safe(item['path']);s=p.lstat();need(stat.S_ISREG(s.st_mode),'regular original');raw=p.read_bytes();need(H(raw)==item['sha256'] and len(raw)==item['bytes'],'original bytes changed: '+str(p));stable=lambda z:(z.st_dev,z.st_ino,z.st_mode,z.st_nlink,z.st_size,z.st_mtime_ns,z.st_ctime_ns);need(stable(s)==stable(p.lstat()),'original state changed during read');return raw
def paths(raw):return set(raw.decode().rstrip('\0').split('\0'))if raw else set()
def validate_targets(entries):need(set(entries)==CHANGED,'exact three adoption leaves only')
def at(value,keypath):
 need(isinstance(keypath,list) and keypath and all(isinstance(k,(str,int))and not isinstance(k,bool)for k in keypath),'explicit actual peer JSON key path')
 for key in keypath:value=value[key]
 return value

def build_tree(git,tree_oid,changes):
 """Accepted publisher recursive mktree; existing three 100644 leaves only."""
 validate_targets(changes)
 def read_tree(tree):
  rows={}
  for row in git('ls-tree','-z',tree).split(b'\0'):
   if row:
    header,name=row.split(b'\t',1);mode,kind,obj=header.split(b' ');rows[name.decode()]=(mode,kind,obj)
  return rows
 def update_tree(tree,changes,prefix=''):
  rows=read_tree(tree);groups={}
  for path,blob in changes.items():
   name,sep,tail=path.partition('/');groups.setdefault(name,{})[tail if sep else '']=blob
  for name,group in groups.items():
   old=rows.get(name)
   if ''in group:
    need(len(group)==1,'file/tree collision');need(prefix+name in CHANGED and old is not None and old[:2]==(b'100644',b'blob'),'only existing 100644 adoption leaf');rows[name]=(b'100644',b'blob',group[''].encode())
   else:
    need(old is not None and old[:2]==(b'040000',b'tree'),'existing tree required');child=update_tree(old[2].decode(),group,prefix+name+'/');rows[name]=(b'040000',b'tree',child.encode())
  stream=b''.join(mode+b' '+kind+b' '+obj+b'\t'+name.encode()+b'\0'for name,(mode,kind,obj)in rows.items());new=oid(git('mktree','-z',data=stream));need(read_tree(new)==rows,'tree roundtrip mismatch');return new
 return update_tree(tree_oid,changes)

def validate_originals(q):
 need(set(q['artifacts'])==CHANGED|UNCHANGED,'five exact original artifacts required')
 raw={name:pinned(item)for name,item in q['artifacts'].items()}
 originals={name:json.loads(pinned(item))for name,item in q['original_receipts'].items()}
 need(set(originals)=={'terminal','ledger_index','architecture_result'},'three exact source receipts')
 terminal=originals['terminal'];index=originals['ledger_index'];ar=originals['architecture_result'];ledger_hash=H(raw[LEDGER])
 for t in [terminal,index['terminal']]:
  need(t['source_sha']==S10 and t['formal_accepted']is True and t['failed_conditions']==[] and t['record_count']==123 and t['execution_head_counts']=={S10:120} and len(t['retired_ids'])==3,'original S10 full123 terminal required')
  need(t['root_exit']==t['outer_exit']==t['original_cli_exit']==0 and t['terminal_files']['ledger']['sha256']==ledger_hash,'original ledger terminal identity')
 need(index['source_sha']==S10 and index['collection_exit']==0,'complete original collection')
 need(index['terminal']['terminal_files']['ledger']['path']==q['artifacts'][LEDGER]['path'],'adopt only original generated ledger path')
 ledger=json.loads(raw[LEDGER]);need(len(ledger)==123,'original 123 ledger rows');heads=[x['execution']['head']for x in ledger.values()if isinstance(x.get('execution'),dict)]
 need(len(heads)==120 and set(heads)=={S10} and sum(x.get('verdict')=='retired'for x in ledger.values())==3,'natural execution heads remain S10')
 need(ar['sourceSHA']==ARCH and ar['exit_code']==0 and ar['originalGateExits']==[0,0,0] and ar['inputCount']==604 and ar['sourceBeforeAfterClean']is True and ar['changedArtifacts']==['PRODUCT-ARCHITECTURE.md','product-architecture-receipt.json'],'actual architecture assembly required')
 for name in (CHANGED|UNCHANGED)-{LEDGER}:
  info=ar['outputs'][name[len(ART):]];need(info['rawSha256']==H(raw[name]) and info['bytes']==len(raw[name]),'assembly original output identity')
 receipt=json.loads(raw[RECEIPT]);need(receipt['sourceBaseHead']==receipt['headObservedBefore']==receipt['headObservedAfter']==ARCH,'architecture actual source must not be relabelled')
 need(receipt['counts']['executableFiles']==604 and receipt['scanPassed']is True and receipt['manifestRefresh']['originalThreeGateExits']==[0,0,0],'three original judges/604 binding')
 need(receipt['manifestRefresh']['manifestByteUnchangedFromExecutionSource']is True and receipt['manifestRefresh']['scanByteUnchangedFromExecutionSource']is True,'manifest/scan no changes')
 need(receipt['reportSha256']==H(raw[REPORT].replace(b'\r\n',b'\n')),'exact report hash')
 expected={'ledger_actual':{'exit':0,'source':S10,'ledger_sha256':ledger_hash},'ledger_package':{'exit':0,'source':S10,'index_sha256':q['original_receipts']['ledger_index']['sha256'],'archive_sha256':index['archive_sha256']},'architecture_actual':{'exit':0,'source':ARCH,'result_sha256':q['original_receipts']['architecture_result']['sha256']}}
 need(set(q['peers'])==set(expected),'all three independent peers required')
 for role,fields in expected.items():
  item=q['peers'][role];peer=json.loads(pinned(item));need(set(item['key_paths'])==set(fields),'exact actual peer bindings for '+role)
  for key,value in fields.items():
   actual=at(peer,item['key_paths'][key]);need(type(actual)==type(value) and actual==value,'peer binding mismatch '+role+':'+key)
 return raw,originals

def main():
 p=argparse.ArgumentParser();p.add_argument('--execute-root-approved',action='store_true');p.add_argument('--request',type=Path);p.add_argument('--request-sha256');a=p.parse_args()
 if not a.execute_root_approved:
  print(json.dumps({'status':'PLAN_ONLY','source_sha':S10,'allowed_changes':sorted(CHANGED),'SHM_access':False,'formal_execution':False}));return 0
 need(not sys.flags.optimize and 'PYTHONOPTIMIZE'not in os.environ,'assertions required')
 request_raw=safe(a.request).read_bytes();need(H(request_raw)==a.request_sha256,'root request pin');q=json.loads(request_raw)
 need(q['schema']=='candidate-S10-A-three-leaf-byte-adoption/1' and q['source_sha']==S10 and q['architecture_source_sha']==ARCH and q['candidate_branch']==BRANCH and q['expected_publisher_head']==HISTORICAL_PUBLISHER_HEAD and q['root_candidate_ref_exclusive']is True and q['root_execution_lease']is True and q['root_exclusive_publisher_window']is True and q['root_originals_and_peers_reviewed']is True,'root explicit adoption lease')
 parent=q['expected_parent'];need(isinstance(parent,str)and re.fullmatch('[0-9a-f]{40}',parent),'full root-declared current evidence parent')
 need(H(HELPER.read_bytes())==HELPER_PIN and H(PUBLISHER.read_bytes())==PUBLISHER_PIN,'reviewed publisher/helper pins')
 sp=importlib.util.spec_from_file_location('accepted_private_publisher',HELPER);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);m.shared_root_guard()
 out=safe(q['out']);need(out.parent==OWN and not out.exists(),'fresh direct OWN output')
 raws,originals=validate_originals(q)
 for item in q['artifacts'].values():
  src=safe(item['path']);need(not src.is_relative_to(ROOT) and not src.is_relative_to(out),'original artifact outside publisher/output')
 estimate=3*sum(len(raws[x])for x in CHANGED)+2*(ROOT/'.git/index').stat().st_size+64*1024*1024
 need(shutil.disk_usage(OWN).free>=estimate,'original private publisher 3x payload+2x index+64MiB resource reserve')
 out.mkdir(mode=0o700);(out/'tmp').mkdir();cap,rec=m.recorder(out);rec.sha=ARCH;rec.env.update(TMPDIR=str(out/'tmp'),TMP=str(out/'tmp'),TEMP=str(out/'tmp'))
 (out/'ADOPTER.py').write_bytes(Path(__file__).read_bytes());(out/'REQUEST.json').write_bytes(request_raw)
 result={'source_sha':ARCH,'ledger_execution_sha':S10,'architecture_execution_sha':ARCH,'product_source':ARCH,'candidate_branch':BRANCH,'previous_head':parent,'request_sha256':a.request_sha256,'exit_code':1,'published':False,'delivered':False,'old_repo_changed':None,'final_sha':None,'source_execution_heads_rewritten':False,'new_final_tracked_check':'UNRUN; root must run original check in complete new-final checkout','formal_product_tests_executed':False,'resource_estimate_bytes':estimate,'original_artifact_hashes':{k:H(v)for k,v in raws.items()},'commands':rec.rows}
 def save():cap.dump(out/'RESULT.json',result)
 def git(*argv,data=None):
  r,b,e=rec.run(['git','-c','gc.auto=0','-c','maintenance.auto=false',*argv],cwd=ROOT,data=data,timeout=None,check=False,source_sha=ARCH,source_variant='candidate exact adoption: ledger executions S10; architecture executions A; neither relabelled F');need(r['actual_process_returncode']==0,'Git failed: '+r['directory']);return b
 def remote():
  rows=git('ls-remote','--heads','origin','refs/heads/'+BRANCH).splitlines();need(len(rows)==1,'one remote branch');value,ref=rows[0].split(b'\t');need(ref.decode()=='refs/heads/'+BRANCH,'exact remote ref');return oid(value)
 def publisher_state():
  return {'head':oid(git('rev-parse','HEAD')),'head_bytes_sha256':H((ROOT/'.git/HEAD').read_bytes()),'index_sha256':H((ROOT/'.git/index').read_bytes()),'branch':git('branch','--show-current').decode().strip(),'train_ref':oid(git('rev-parse','refs/heads/'+HISTORICAL_PROVIDER_BRANCH)),'status_hex':git('status','--porcelain=v1','--untracked-files=all').hex()}
 publisher_before=None
 def clean(expected):
  need(publisher_before is not None and publisher_state()==publisher_before,'historical publisher HEAD/index/train ref/status changed')
  need(oid(git('rev-parse','refs/heads/'+BRANCH))==expected,'candidate local ref moved')
 def api(endpoint,raw=False):
  media='application/vnd.github.raw+json'if raw else 'application/vnd.github+json';r,b,e=rec.run(['gh','api','--hostname','github.com','--method','GET','-H','Accept: '+media,endpoint],cwd=ROOT,timeout=None,check=False,source_sha=ARCH,source_variant='remote exact candidate commit and three original blobs, no acceptance rerun');need(r['actual_process_returncode']==0 and not r['timeout_expired'],'remote read failed: '+r['directory']);return b
 before=None;save()
 try:
  need((ROOT/'.git').is_dir() and not(ROOT/'.git').is_symlink(),'physical private Gitdir')
  need(Path(git('rev-parse','--absolute-git-dir').decode().strip())==ROOT/'.git','private Gitdir identity')
  common=Path(git('rev-parse','--git-common-dir').decode().strip());common=common if common.is_absolute()else ROOT/common;need(common.resolve()==ROOT/'.git','no shared Git index/refs')
  need(Path(git('rev-parse','--show-toplevel').decode().strip())==ROOT,'exact private worktree')
  need((ROOT/'.git/objects/info/alternates').read_text()==str(m.OLD/'.git/objects')+'\n','original one-way readonly object provider')
  before=m.old_snapshot(rec);cap.dump(out/'OLD_BEFORE.json',before);need(before['head']==m.PARENT and before['branch']==HISTORICAL_PROVIDER_BRANCH and before['status_hex']=='','old WS historical provider identity')
  publisher_before=publisher_state();cap.dump(out/'PUBLISHER_BEFORE.json',publisher_before)
  need(publisher_before['head']==HISTORICAL_PUBLISHER_HEAD and publisher_before['train_ref']==HISTORICAL_PUBLISHER_HEAD and publisher_before['branch']==HISTORICAL_PROVIDER_BRANCH and publisher_before['status_hex']=='','historical publisher identity')
  need(re.fullmatch('[0-9a-f]{64}',q['expected_publisher_index_sha256']) and publisher_before['index_sha256']==q['expected_publisher_index_sha256'],'root-bound original publisher index')
  clean(parent);need(remote()==parent,'candidate remote parent moved');git('merge-base','--is-ancestor',ARCH,parent);git('merge-base','--is-ancestor',S10,ARCH)
  need(paths(git('diff','--no-renames','--name-only','-z',S10,ARCH,'--','.',':(exclude)evidence'))=={'決策佇列.md'},'S10 to A exact decision-only difference')
  delta=q['s10_to_architecture_decision'];need(set(delta)=={'old','new'},'complete decision delta binding')
  for side,rev in [('old',S10),('new',ARCH)]:
   b=git('show',rev+':決策佇列.md');d=delta[side];need(set(d)=={'mode','oid','bytes','sha256'} and d['mode']=='100644' and d['oid']==blob_id(b) and d['bytes']==len(b) and d['sha256']==H(b),'exact original decision blob '+side)
   need(git('ls-tree','-z',rev,'--','決策佇列.md')==b'100644 blob '+d['oid'].encode()+b'\t'+ '決策佇列.md'.encode()+b'\0','decision mode binding '+side)
  need(not git('diff','--no-renames','--name-only','-z',ARCH,parent,'--','.',':(exclude)evidence'),'candidate parent non-evidence closure differs from A')
  for name in UNCHANGED:
   original=git('show',ARCH+':'+name);need(original==raws[name] and git('show',parent+':'+name)==original,'manifest/scan must remain original bytes')
  entries={name:blob_id(raws[name])for name in CHANGED};validate_targets(entries)
  for name in CHANGED:
   old=git('ls-tree','-z',parent,'--',name);need(old.startswith(b'100644 blob ') and old.endswith(b'\t'+name.encode()+b'\0'),'existing regular adoption path')
   need(oid(git('rev-parse',parent+':'+name))!=entries[name],'each of three leaves must actually change')
   need(oid(git('hash-object','-w','--no-filters','--',q['artifacts'][name]['path']))==entries[name] and H(pinned(q['artifacts'][name]))==H(raws[name]),'exact immutable bytes written')
  tree=build_tree(git,oid(git('rev-parse',parent+'^{tree}')),entries)
  final=oid(git('commit-tree',tree,'-p',parent,data=(MESSAGE+'\n').encode()));result['final_sha']=final;save()
  need(git('show','-s','--format=%P',final).decode().strip()==parent,'single parent only')
  changed=paths(git('diff-tree','--no-commit-id','--no-renames','--name-only','-r','-z',parent,final));need(changed==CHANGED,'commit changes exactly three named leaves')
  need(paths(git('diff','--no-renames','--name-only','-z',ARCH,final,'--','.',':(exclude)evidence'))==CHANGED,'all other product/test/SSOT paths unchanged')
  for name in CHANGED:need(oid(git('rev-parse',final+':'+name))==entries[name],'committed bytes OID differs')
  for name in UNCHANGED:need(git('show',final+':'+name)==raws[name],'final manifest/scan bytes changed')
  visible=git('sparse-checkout','check-rules','-z',data=b''.join(x.encode()+b'\0'for x in sorted(CHANGED)));need(visible==b'','three artifacts must remain outside sparse publisher; no large working copy')
  need(BRANCH!=HISTORICAL_PROVIDER_BRANCH,'candidate must not be historical train branch')
  clean(parent);need(remote()==parent,'remote moved before ff');need(m.old_snapshot(rec)==before,'old WS changed before ff')
  git('update-ref','refs/heads/'+BRANCH,final,parent);clean(final);git('push','origin','refs/heads/'+BRANCH+':refs/heads/'+BRANCH);need(remote()==final,'remote did not resolve candidate final');result.update(published=True,push_exit=0);save()
  ref=json.loads(api('repos/ZhiQiYang/geometry-axiom/git/ref/heads/'+BRANCH));need(ref['object']['type']=='commit'and ref['object']['sha']==final,'remote branch differs')
  commit=json.loads(api('repos/ZhiQiYang/geometry-axiom/git/commits/'+final));need(commit['sha']==final and commit['tree']['sha']==tree and [x['sha']for x in commit['parents']]==[parent],'remote exact commit/tree/parent')
  remote_rows=[]
  for name in sorted(CHANGED):
   b=api('repos/ZhiQiYang/geometry-axiom/git/blobs/'+entries[name],True);need(b==raws[name] and blob_id(b)==entries[name],'remote full original blob bytes differ');remote_rows.append({'path':name,'oid':entries[name],'bytes':len(b),'sha256':H(b)})
  cap.dump(out/'REMOTE_THREE_BLOBS.json',remote_rows);need(json.loads(api('repos/ZhiQiYang/geometry-axiom/git/ref/heads/'+BRANCH))['object']['sha']==final,'remote moved during verification');clean(final)
  for name in raws:need(pinned(q['artifacts'][name])==raws[name],'original artifact changed after adoption')
  cap.dump(out/'PUBLISHER_AFTER.json',publisher_state());need(publisher_state()==publisher_before,'historical publisher changed after candidate publication')
  result.update(exit_code=0,delivered=True,historical_publisher_unchanged=True,changed_paths=sorted(changed),remote_commit_resolved=True,ledger_adopted_byte_exact=True,manifest_scan_byte_unchanged=True,other_product_test_ssot_unchanged=True)
 except BaseException as exc:result.update(exit_code=1,error=repr(exc));raise
 finally:
  if publisher_before is not None:
   try:
    current=publisher_state();cap.dump(out/'PUBLISHER_FINAL.json',current)
    if current!=publisher_before:result.update(exit_code=1,delivered=False,historical_publisher_error='original publisher HEAD/index/train ref/status changed')
   except BaseException as exc:result.update(exit_code=1,delivered=False,historical_publisher_error=repr(exc))
  if before is not None:
   try:
    after=m.old_snapshot(rec);cap.dump(out/'OLD_AFTER.json',after);result['old_repo_changed']=after!=before
    if after!=before:result.update(exit_code=1,delivered=False,old_repo_error='original provider changed')
   except BaseException as exc:result.update(exit_code=1,delivered=False,old_repo_error=repr(exc))
  save()
 need(result['exit_code']==0 and result['old_repo_changed']is False,'adoption or old-provider preservation failed');print(json.dumps({k:result[k]for k in ['exit_code','final_sha','published','delivered','old_repo_changed']}));return 0
if __name__=='__main__':raise SystemExit(main())
