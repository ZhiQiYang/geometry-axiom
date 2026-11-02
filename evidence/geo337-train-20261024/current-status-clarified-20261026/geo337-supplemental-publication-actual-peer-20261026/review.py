from pathlib import Path,PurePosixPath
import collections,datetime,gzip,hashlib,json,stat,tarfile

OWN=Path('/dev/shm/geometry-axiom-geo337-20261025')
INNER=OWN/'supplemental-publication-original-20261026'
OUTER=OWN/'supplemental-publication-root-original-20261026'
OUT=Path(__file__).parent
F='cbf0fb621888596aa14ad5f2349b503e23b1b72d'
P='f90db245f228b7a95a800cab176c3f9ca497133f'
E='f99b6e63d52b1a87e6fe3546e2604cdf9bbb2304'
HEAD='3e4f2560aa11ed2a626db98ba5ed6f129e791052'
BRANCH='codex/train337-recovered-evidence-20261026'
REF='refs/heads/'+BRANCH
PREFIX='evidence/geo337-train-20261024/'
PROGRESS=PREFIX+'resume-20261026/PROGRESS.md'
OLD_PROGRESS='a7af4575b419763b5b48e459a9c9e2dfca33e772'
EXEC_PIN='988a3b851db4417d41c073d02e8d3e440ea7dd22c10c53421490da79174cb720'
MANIFEST_PIN='926d504d6c2ef425686370e5fea91d2a85f9ba4387dc7f6ef61cf33a11adb0aa'
check_count=0;read_facts={}
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(ok,msg):
 global check_count
 check_count+=1
 if not ok:raise AssertionError(msg)
def statid(p):
 s=p.lstat();need(stat.S_ISREG(s.st_mode),'not regular original: '+str(p));return (s.st_mode,s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_nlink)
def stream(p,keep=False):
 p=Path(p);before=statid(p);h=hashlib.sha256();g=hashlib.sha1(b'blob '+str(before[3]).encode()+b'\0');n=0;parts=[]
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):
   h.update(b);g.update(b);n+=len(b)
   if keep:parts.append(b)
 need(statid(p)==before and n==before[3],'original changed during read: '+str(p))
 fact={'bytes':n,'sha256':h.hexdigest(),'blob_oid':g.hexdigest()}
 if str(p)in read_facts:need(read_facts[str(p)]==fact,'repeated read changed')
 read_facts[str(p)]=fact
 return b''.join(parts)if keep else fact
def raw(p):return stream(p,True)
def load(p):return json.loads(raw(p))
def stable_pin(p,pin):need(stream(p)['sha256']==pin,'pin mismatch: '+str(p))
stable_pin(INNER/'EXECUTOR.py',EXEC_PIN);stable_pin(INNER/'MANIFEST.json',MANIFEST_PIN);stable_pin(OUTER/'MANIFEST.json',MANIFEST_PIN)
ir=load(INNER/'RESULT.json');orr=load(OUTER/'RESULT.json');manifest=load(INNER/'MANIFEST.json');remote_record=load(INNER/'REMOTE_BLOBS.json')
need(ir['exit_code']==0 and orr['exit_code']==0,'outer/inner not true0')
need(ir['base_sha']==P and ir['evidence_head']==E and ir['branch']==BRANCH,'publication identity mismatch')
need(ir['published']and ir['delivered']and ir['existing_writer_unchanged']and not ir['product_modified']and not ir['train_ref_modified'],'terminal flags mismatch')
need(ir['source_execution_sha']is None and ir['recovery_anchor_sha']==F,'publication source wrongly relabelled')
need(orr['manifest_sha256']==MANIFEST_PIN and orr['source_sha']==F,'outer binding mismatch')
stable_pin(Path('/tmp/geo337-recovery-evidence-append-peer-20261026/REVIEW.json'),'125a0dee72a2d3d09fdd6af901aefdfe7693dbf1d43cbe0141c280d008da3917')
peer=load(Path('/tmp/geo337-recovery-evidence-append-peer-20261026/REVIEW.json'));need(peer['exit_code']==0 and peer['blocking_findings']==[]and peer['subject_sha256']==EXEC_PIN,'publisher peer wrong')

# Independently re-read every captured stdin/stdout/stderr, including all remote bytes.
streams={};batches={}
for root in [INNER,OUTER]:
 batch=load(root/'subcommands.json');batches[root.name]=batch
 need(len(list((root/'subcommands').iterdir()))==len(batch),'capture directory count mismatch')
 for seq,r in enumerate(batch,1):
  d=Path(r['directory']);need(d==root/'subcommands'/f'{seq:06d}','capture order/scope mismatch')
  need(load(d/'result.json')==r,'batch result differs from individual raw result')
  q=load(d/'request.json');need(all(q.get(k)==r.get(k)for k in ['command','cwd','acceptance_sha','source_sha','source_variant','environment','started_epoch','stdin_provided','stdin_sha256','directory']),'request/result command binding differs')
  need(type(r['actual_process_returncode'])is int and r['actual_process_returncode']==0 and r['timeout_expired']is False,'nonzero/timeout original command')
  need(r['acceptance_sha']==(P if root==INNER else F) and r['source_sha']==(P if root==INNER else F) and r['ended_epoch']>=r['started_epoch'],'capture SHA/time mismatch')
  for name in ['stdin','stdout','stderr']:
   p=d/(name+'.bin');fact=stream(p);need(fact['sha256']==r[name+'_sha256'],'capture SHA mismatch')
   if name!='stdin':need(fact['bytes']==r[name+'_bytes'],'capture byte count mismatch')
   streams[(root.name,seq,name)]=fact
need(len(batches[INNER.name])==722 and len(batches[OUTER.name])==2,'unexpected command count')
batch=batches[INNER.name]
def args(r):
 c=r['command'];return c[5:]if c[:5]==['git','-c','gc.auto=0','-c','maintenance.auto=false']else c
def selected(cmd):return[r for r in batch if args(r)[:len(cmd)]==cmd]
def data(r,name='stdout'):return raw(Path(r['directory'])/(name+'.bin'))
need(all(r['cwd']==str(OWN/'publisher-source')for r in batch),'unexpected publisher cwd')
need(all(not any(str(k).startswith('GIT_')for k in r['environment']) for r in batch),'unexpected captured foreign Git env')
need(all(data(r)==(HEAD+'\n').encode()for r in selected(['rev-parse','HEAD']))and len(selected(['rev-parse','HEAD']))==3,'historical HEAD drift')
need(all(data(r)==b'codex/train-337-continue-20261024\n'for r in selected(['branch','--show-current']))and len(selected(['branch','--show-current']))==3,'historical branch drift')
need(all(data(r)==b''for r in selected(['status','--porcelain=v1']))and len(selected(['status','--porcelain=v1']))==3,'historical worktree dirty')
remote_refs=selected(['ls-remote']);need(len(remote_refs)==4,'remote ref boundary count')
need([data(r)for r in remote_refs]==[(x+'\t'+REF+'\n').encode()for x in [P,P,E,E]],'remote before/after refs disagree')
need(args(selected(['update-ref'])[0])==['update-ref',REF,E,P]and len(selected(['update-ref']))==1,'CAS not exact expected parent')
need(args(selected(['push'])[0])==['push','https://github.com/ZhiQiYang/geometry-axiom.git',REF+':'+REF]and len(selected(['push']))==1,'push not ordinary exact owned ref')
need(all('--force'not in args(r)and '-f'not in args(r)and not any(str(x).startswith('+refs/')for x in args(r))for r in batch),'force push option found')
local_parent=selected(['for-each-ref']);need(len(local_parent)==1 and data(local_parent[0])==(P+'\n').encode(),'local expected parent mismatch')
commit=selected(['commit-tree']);need(len(commit)==1 and args(commit[0])[-2:]==['-p',P]and data(commit[0])==(E+'\n').encode(),'commit parent mismatch')
need(data(commit[0],'stdin')==b'docs: append recovered architecture and acceptance evidence\n','commit message differs')
destinations=[x['destination']for x in manifest['files']];need(len(destinations)==302 and len(set(destinations))==302,'destination count/duplicate')
need(all(d.startswith(PREFIX)and '..'not in PurePosixPath(d).parts for d in destinations),'out of evidence destination')
diff=selected(['diff-tree']);need(len(diff)==1 and set(data(diff[0]).decode().strip('\0').split('\0'))==set(destinations),'actual commit scope differs')
prod_diff=selected(['diff','--name-only']);need(len(prod_diff)==2 and all(data(r)==b''for r in prod_diff),'product closure changed')
need(args(prod_diff[-1])==['diff','--name-only',P,E,'--','.',':(exclude)evidence'],'product diff wrong endpoints')
outer_cmd=batches[OUTER.name][-1]['command'];need('--expected-parent'in outer_cmd and outer_cmd[outer_cmd.index('--expected-parent')+1]==P and outer_cmd[outer_cmd.index('--expected-progress-blob')+1]==OLD_PROGRESS,'outer exact CAS inputs mismatch')
need(data(batches[OUTER.name][0]).decode().strip()==OLD_PROGRESS,'original PROGRESS raw OID mismatch')
outer_print=json.loads(data(batches[OUTER.name][-1]));need(outer_print==ir,'raw host stdout not equal final inner result')

# Reconstruct tree objects from captured ls-tree streams; independently prove only one overwrite.
trees={}
for r in selected(['ls-tree','-z']):
 oid=args(r)[2];entries={}
 for line in data(r).split(b'\0'):
  if not line:continue
  hdr,name=line.split(b'\t',1);mode,kind,obj=hdr.split(b' ');entries[name]=(mode,kind,obj)
 ordered=sorted(entries.items(),key=lambda kv:kv[0]+(b'/'if kv[1][1]==b'tree'else b''))
 body=b''.join(mode.lstrip(b'0')+b' '+name+b'\0'+bytes.fromhex(obj.decode())for name,(mode,kind,obj)in ordered)
 need(hashlib.sha1(b'tree '+str(len(body)).encode()+b'\0'+body).hexdigest()==oid,'captured tree object hash mismatch')
 if oid in trees:need(trees[oid]==entries,'repeated tree differs')
 trees[oid]=entries
base_tree=data(selected(['rev-parse',P+'^{tree}'])[0]).decode().strip();new_tree=args(commit[0])[1]
changes={}
def tree_diff(a,b,prefix=b''):
 if a==b:return
 old=trees[a]if a else{};new=trees[b]if b else{}
 for name in sorted(set(old)|set(new)):
  x=old.get(name);y=new.get(name)
  if x==y:continue
  path=prefix+name
  if (x is None or x[1]==b'tree')and(y is None or y[1]==b'tree'):
   tree_diff(x[2].decode()if x else None,y[2].decode()if y else None,path+b'/')
  else:changes[path.decode()]=(x,y)
tree_diff(base_tree,new_tree)
need(set(changes)==set(destinations),'recursive tree delta differs from manifest')
need([p for p,(old,new)in changes.items()if old is not None]==[PROGRESS],'existing evidence overwritten outside PROGRESS')
need(changes[PROGRESS][0]==(b'100644',b'blob',OLD_PROGRESS.encode()),'old PROGRESS identity mismatch')
need(all(new and new[:2]==(b'100644',b'blob')for old,new in changes.values()),'new evidence not regular blobs')

sources={};local_drifts=[];hash_commands=selected(['hash-object']);need(len(hash_commands)==302,'source hash command count')
for item in manifest['files']:
 p=Path(item['source_path']);fact=stream(p)
 matching=[r for r in hash_commands if args(r)==['hash-object','-w','--no-filters','--',str(p)]];need(len(matching)==1,'missing exact source hash-object')
 oid=data(matching[0]).decode().strip();need(oid==changes[item['destination']][1][2].decode(),'original hash-object/tree Git blob mismatch')
 if fact['bytes']!=item['bytes']or fact['sha256']!=item['sha256']:
  need(item['destination']==PROGRESS and str(p)=='/tmp/geo337-current-PROGRESS-cbf0fb62-20261026.md','non-PROGRESS original source changed')
  need(item['bytes']==5747 and item['sha256']=='71f838b5b5230f392e55332ee1bf7c7bec74f4f2cb4955130a8254d712812c26','unexpected historical PROGRESS version')
  need(fact['bytes']==6022 and fact['sha256']=='148402318284618623b950e330e877c9ccf46e39e0b2aafd5c3a0796c2c37956','newly changed local PROGRESS requires explicit reclassification')
  local_drifts.append({'path':str(p),'destination':item['destination'],'historical_bytes':item['bytes'],'historical_sha256':item['sha256'],'current':fact,'historical_blob_oid':oid,'historical_remote_must_match':True,'current_bytes_not_claimed_delivered':True})
 else:need(oid==fact['blob_oid'],'current original source Git blob mismatch')
 sources[item['destination']]={'bytes':item['bytes'],'sha256':item['sha256'],'blob_oid':oid,'source_path':str(p)}
need(len(local_drifts)==1,'expected classified PROGRESS drift missing or duplicated')
remote={}
for r in batch:
 c=r['command']
 if c[:2]!=['gh','api']:continue
 need(c[:6]==['gh','api','--hostname','github.com','-H','Accept: application/vnd.github.raw+json']and c[6].startswith('repos/ZhiQiYang/geometry-axiom/git/blobs/'),'remote command not raw GitHub blob API')
 oid=c[6].rsplit('/',1)[-1];fact=stream(Path(r['directory'])/'stdout.bin')
 need(oid==fact['blob_oid']and oid not in remote,'remote raw Git OID mismatch or duplicate fetch')
 remote[oid]={**fact,'captured_stdout':str(Path(r['directory'])/'stdout.bin'),'original_started_epoch':r['started_epoch'],'original_ended_epoch':r['ended_epoch']}
need(len(remote)==256==ir['remote_blobs_verified'],'remote distinct count mismatch')
need({r['blob_oid']:(r['bytes'],r['sha256'])for r in remote_record}=={o:(r['bytes'],r['sha256'])for o,r in remote.items()},'REMOTE_BLOBS metadata differs from raw streams')
need(set(remote)=={v['blob_oid']for v in sources.values()},'remote/source blob set mismatch')
for dest,s in sources.items():need(remote[s['blob_oid']]['sha256']==s['sha256']and remote[s['blob_oid']]['bytes']==s['bytes'],'remote delivered bytes differ from source')
need(selected(['push'])[0]['ended_epoch']<=min(r['original_started_epoch']for r in remote.values()),'remote reads precede push')

# Supplemental E2 contains documents/tools/peer/API originals, not a new full native/browser or 512 run.
stable_pin(OUTER/'FIRST_PUBLICATION_ACTUAL_PEER.json','79f5995387e6c5c4c41ac2be0750b3c0348639c3c474c0bab3554b27865edcc0')
first_peer=load(OUTER/'FIRST_PUBLICATION_ACTUAL_PEER.json')
need(first_peer['exit_code']==0 and first_peer['evidence_head']==P and first_peer['durable_delivery_verified'],'prior E1 actual binding mismatch')
need(args(prod_diff[0])==['diff','--name-only',F,P,'--','.',':(exclude)evidence'],'fixed product anchor to parent closure mismatch')
need(all(args(r)[0]not in ['checkout','reset','add','update-index','merge','rebase','clean']for r in batch),'worktree/index-changing Git verb present')
executor=raw(INNER/'EXECUTOR.py').decode()
need("need(snapshot()==before,'existing writer changed before push')"in executor and "need(snapshot()==before,'existing writer changed after push')"in executor and "'index':h((ROOT/'.git/index').read_bytes())"in executor,'exact index runtime guard absent')
need(ir['capacity']['used']+ir['capacity']['additional_bound']<=2*1024**3,'original publication capacity bound exceeded')
groups=collections.Counter('/'.join(d.split('/')[:4])for d in destinations)
by_oid={k:{'bytes':v['bytes'],'sha256':v['sha256'],'captured_stdout':v['captured_stdout']}for k,v in remote.items()}
remote_binding_sha=sha(json.dumps(by_oid,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
scope_identity_sha=sha(json.dumps(sources,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
report={'schema':'supplemental-publication-independent-actual-peer/1','exit_code':0,'blocking_findings':[],'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checked_count':check_count,'evidence_head':E,'parent_evidence_head':P,'product_anchor_sha':F,'branch':BRANCH,'publication_execution_source_sha':None,'files':302,'distinct_remote_blobs':256,'total_publication_file_bytes':sum(x['bytes']for x in manifest['files']),'total_unique_remote_bytes':sum(x['bytes']for x in remote.values()),'raw_original_commands_checked':724,'actual_outer_exit':0,'actual_inner_exit':0,'source_identity_rule':'E2 and its evidence parent identify publication only. Per-file original A/S10/F/synthetic/API identities remain unchanged.','expected_parent_CAS':{'old':P,'new':E,'ref':REF,'ordinary_push':True,'exact_one_ref_update':True,'remote_before_after_sequence':[P,P,E,E]},'scope':{'manifest_sha256':MANIFEST_PIN,'recursive_tree_delta_exactly_302_evidence_paths':True,'existing_evidence_overwrites':[PROGRESS],'old_progress_blob':OLD_PROGRESS,'new_regular_blobs_only':True,'product_modified':False,'train_ref_modified':False,'fixed_F_to_parent_product_closure_unchanged':True,'groups':dict(sorted(groups.items())),'source_mapping_identity_sha256':scope_identity_sha},'writer_preservation':{'historical_HEAD':HEAD,'historical_branch':'codex/train-337-continue-20261024','three_HEAD_branch_status_snapshots_match':True,'index_runtime_pre_post_hash_equality_guard_executed':True,'index_independent_archived_pre_post_values_available':False,'limitation':'Exact pinned executor compares raw index SHA256 before push and after all remote reads; actual exit0 proves both equality guards passed. Individual before/after values were not separately emitted and no independent archived index byte snapshot is claimed.'},'remote_full_reads':{'raw_blob_api_calls':256,'every_byte_SHA256_and_Git_blob_OID_independently_verified':True,'all_streams_captured_after_successful_push':True,'all_captured_request_result_and_stream_hashes_verified':True,'same_content_deduplicated_for_302_paths':True,'remote_bindings_identity_sha256':remote_binding_sha,'first_remote_started_epoch':min(x['original_started_epoch']for x in remote.values()),'last_remote_ended_epoch':max(x['original_ended_epoch']for x in remote.values())},'original_receipts':{'inner_result_sha256':stream(INNER/'RESULT.json')['sha256'],'outer_result_sha256':stream(OUTER/'RESULT.json')['sha256'],'inner_subcommands_sha256':stream(INNER/'subcommands.json')['sha256'],'outer_subcommands_sha256':stream(OUTER/'subcommands.json')['sha256'],'executor_sha256':EXEC_PIN,'remote_blobs_metadata_sha256':stream(INNER/'REMOTE_BLOBS.json')['sha256'],'E1_actual_peer_sha256':'79f5995387e6c5c4c41ac2be0750b3c0348639c3c474c0bab3554b27865edcc0'},'persistent_delivery_scope':'Only the exact 302 E2 manifest files: complete selected peer/tool drafts, API originals, #300 static materials, E1 publication metadata, terminal receipts and updated PROGRESS.','limits':['This audit certifies historical E2 remote raw bytes captured at the recorded times, not a new live Git/API observation.','Publication of #300 static findings is not a capacity-512 runtime verdict.','No full native, six browser, full123, performance threshold, axiom approval or all-product passing verdict is established by this publication audit.','E1 complete 17-root archive remains under its own unchanged proof; E2 does not replace or rerun it.','Index preservation is supported by exact executed runtime equality guards; individual hash values were not separately archived.','No duplicate INDEX, archive or remote payload was written; only compact review and audit script are created.'],'audit_git_or_network_executed':False,'audit_product_tests_rerun':False,'audit_SHM_mutation':False,'originals_removed':False,'durable_delivery_verified':True}
report.update(local_source_drift_classification=local_drifts,current_local_sources_matching_publication=301,initial_audit_exit=1,initial_audit_failure_retained='INITIAL_FAILURE.json',initial_audit_script_retained='review.initial.py')
report['limits'].append('Only PROGRESS advanced locally after the closed E2 publication: historical 5747 bytes are verified against manifest, recorded hash-object, commit tree and complete remote raw bytes; current 6022 bytes are not claimed delivered by E2. The initial strict current-source audit exit1 is preserved.')
(OUT/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(OUT/'SUMS.sha256').write_text(''.join(sha(p.read_bytes())+'  '+p.name+'\n'for p in sorted(OUT.iterdir())if p.is_file()and p.name!='SUMS.sha256'))
print(json.dumps({'exit_code':0,'checks':check_count,'review_sha256':sha((OUT/'REVIEW.json').read_bytes()),'new_bytes':sum(p.stat().st_size for p in OUT.iterdir()if p.is_file())}))

