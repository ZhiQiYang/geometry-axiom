from pathlib import Path,PurePosixPath
import collections,datetime,gzip,hashlib,json,stat,tarfile

OWN=Path('/dev/shm/geometry-axiom-geo337-20261025')
INNER=OWN/'closed-first-publication-original-20261026'
OUTER=OWN/'closed-first-publication-root-original-20261026'
OUT=Path(__file__).parent
F='cbf0fb621888596aa14ad5f2349b503e23b1b72d'
E='f90db245f228b7a95a800cab176c3f9ca497133f'
HEAD='3e4f2560aa11ed2a626db98ba5ed6f129e791052'
BRANCH='codex/train337-recovered-evidence-20261026'
REF='refs/heads/'+BRANCH
PREFIX='evidence/geo337-train-20261024/'
PROGRESS=PREFIX+'resume-20261026/PROGRESS.md'
OLD_PROGRESS='62b8439952a9293969f8059145fd08c04d7822ec'
EXEC_PIN='988a3b851db4417d41c073d02e8d3e440ea7dd22c10c53421490da79174cb720'
MANIFEST_PIN='f19882de783c8c03bd1bcee417b5d19fbe71e444b7587b034589c16211a4454d'
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
need(ir['base_sha']==F and ir['evidence_head']==E and ir['branch']==BRANCH,'publication identity mismatch')
need(ir['published']and ir['delivered']and ir['existing_writer_unchanged']and not ir['product_modified']and not ir['train_ref_modified'],'terminal flags mismatch')
need(ir['source_execution_sha']is None and ir['recovery_anchor_sha']==F,'publication source wrongly relabelled')
need(orr['manifest_sha256']==MANIFEST_PIN and orr['source_sha']==F,'outer binding mismatch')
stable_pin(OUTER/'STATIC_PEER.json','125a0dee72a2d3d09fdd6af901aefdfe7693dbf1d43cbe0141c280d008da3917')
peer=load(OUTER/'STATIC_PEER.json');need(peer['exit_code']==0 and peer['blocking_findings']==[]and peer['subject_sha256']==EXEC_PIN,'publisher peer wrong')

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
  need(r['acceptance_sha']==F and r['source_sha']==F and r['ended_epoch']>=r['started_epoch'],'capture SHA/time mismatch')
  for name in ['stdin','stdout','stderr']:
   p=d/(name+'.bin');fact=stream(p);need(fact['sha256']==r[name+'_sha256'],'capture SHA mismatch')
   if name!='stdin':need(fact['bytes']==r[name+'_bytes'],'capture byte count mismatch')
   streams[(root.name,seq,name)]=fact
need(len(batches[INNER.name])==105 and len(batches[OUTER.name])==2,'unexpected command count')
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
need([data(r)for r in remote_refs]==[(x+'\t'+REF+'\n').encode()for x in [F,F,E,E]],'remote before/after refs disagree')
need(args(selected(['update-ref'])[0])==['update-ref',REF,E,F]and len(selected(['update-ref']))==1,'CAS not exact expected parent')
need(args(selected(['push'])[0])==['push','https://github.com/ZhiQiYang/geometry-axiom.git',REF+':'+REF]and len(selected(['push']))==1,'push not ordinary exact owned ref')
need(all('--force'not in args(r)and '-f'not in args(r)and not any(str(x).startswith('+refs/')for x in args(r))for r in batch),'force push option found')
local_parent=selected(['for-each-ref']);need(len(local_parent)==1 and data(local_parent[0])==(F+'\n').encode(),'local expected parent mismatch')
commit=selected(['commit-tree']);need(len(commit)==1 and args(commit[0])[-2:]==['-p',F]and data(commit[0])==(E+'\n').encode(),'commit parent mismatch')
need(data(commit[0],'stdin')==b'docs: append recovered architecture and acceptance evidence\n','commit message differs')
destinations=[x['destination']for x in manifest['files']];need(len(destinations)==27 and len(set(destinations))==27,'destination count/duplicate')
need(all(d.startswith(PREFIX)and '..'not in PurePosixPath(d).parts for d in destinations),'out of evidence destination')
diff=selected(['diff-tree']);need(len(diff)==1 and set(data(diff[0]).decode().strip('\0').split('\0'))==set(destinations),'actual commit scope differs')
prod_diff=selected(['diff','--name-only']);need(len(prod_diff)==2 and all(data(r)==b''for r in prod_diff),'product closure changed')
need(args(prod_diff[-1])==['diff','--name-only',F,E,'--','.',':(exclude)evidence'],'product diff wrong endpoints')
outer_cmd=batches[OUTER.name][-1]['command'];need('--expected-parent'in outer_cmd and outer_cmd[outer_cmd.index('--expected-parent')+1]==F and outer_cmd[outer_cmd.index('--expected-progress-blob')+1]==OLD_PROGRESS,'outer exact CAS inputs mismatch')
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
base_tree=data(selected(['rev-parse',F+'^{tree}'])[0]).decode().strip();new_tree=args(commit[0])[1]
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

sources={};hash_commands=selected(['hash-object']);need(len(hash_commands)==27,'source hash command count')
for item in manifest['files']:
 p=Path(item['source_path']);fact=stream(p);need(fact['bytes']==item['bytes']and fact['sha256']==item['sha256'],'original publication source changed')
 matching=[r for r in hash_commands if args(r)==['hash-object','-w','--no-filters','--',str(p)]];need(len(matching)==1,'missing exact source hash-object')
 oid=data(matching[0]).decode().strip();need(oid==fact['blob_oid']==changes[item['destination']][1][2].decode(),'source/tree Git blob mismatch')
 sources[item['destination']]={**fact,'source_path':str(p)}
remote={}
for r in batch:
 c=r['command']
 if c[:2]!=['gh','api']:continue
 need(c[:6]==['gh','api','--hostname','github.com','-H','Accept: application/vnd.github.raw+json']and c[6].startswith('repos/ZhiQiYang/geometry-axiom/git/blobs/'),'remote command not raw GitHub blob API')
 oid=c[6].rsplit('/',1)[-1];fact=stream(Path(r['directory'])/'stdout.bin')
 need(oid==fact['blob_oid']and oid not in remote,'remote raw Git OID mismatch or duplicate fetch')
 remote[oid]={**fact,'captured_stdout':str(Path(r['directory'])/'stdout.bin'),'original_started_epoch':r['started_epoch'],'original_ended_epoch':r['ended_epoch']}
need(len(remote)==25==ir['remote_blobs_verified'],'remote distinct count mismatch')
need({r['blob_oid']:(r['bytes'],r['sha256'])for r in remote_record}=={o:(r['bytes'],r['sha256'])for o,r in remote.items()},'REMOTE_BLOBS metadata differs from raw streams')
need(set(remote)=={v['blob_oid']for v in sources.values()},'remote/source blob set mismatch')
for dest,s in sources.items():need(remote[s['blob_oid']]['sha256']==s['sha256']and remote[s['blob_oid']]['bytes']==s['bytes'],'remote delivered bytes differ from source')
need(batch[74]['ended_epoch']<=min(r['original_started_epoch']for r in remote.values()),'remote reads precede push')

# Verify the remote API's archive directly against its remote API INDEX, without a duplicate INDEX on disk.
archive_dest=next(p for p in destinations if p.endswith('/CLOSED_ORIGINALS.tar.gz'))
index_dest=next(p for p in destinations if p.endswith('/INDEX.json'))
archive=Path(remote[sources[archive_dest]['blob_oid']]['captured_stdout']);index_path=Path(remote[sources[index_dest]['blob_oid']]['captured_stdout'])
index=load(index_path);inventory=index['inventory'];rows=index['members'];members={r[0]:r for r in rows}
need(len(rows)==len(members)==32871 and inventory['file_count']==24966 and inventory['directory_count']==7905,'remote INDEX counts mismatch')
need(sha(json.dumps(rows,ensure_ascii=False,separators=(',',':')).encode())==inventory['identity_sha256'],'remote inventory identity mismatch')
need(len(inventory['root_names'])==17 and {p.split('/',1)[0]for p in members}==set(inventory['root_names']),'remote archive root scope mismatch')
names=[];seen_members=set();full_bytes=0;terminal_fields={}
with tarfile.open(archive,'r:gz')as tar:
 for m in tar:
  need(m.name in members and m.name not in seen_members,'unindexed or duplicate remote member');seen_members.add(m.name);names.append(m.name);r=members[m.name]
  need(m.size==r[2]and m.mode==(r[4]&0o777)and m.mtime==r[7]//10**9,'remote archive member metadata mismatch')
  if r[1]=='directory':need(m.isdir(),'directory kind mismatch');continue
  need(m.isfile()and not m.issym()and not m.islnk(),'nonregular remote member');h=hashlib.sha256();n=0;parts=[];terminal=m.name.endswith('/RESULT.json')and m.name.count('/')==1
  with tar.extractfile(m)as f:
   for b in iter(lambda:f.read(1024**2),b''):
    h.update(b);n+=len(b)
    if terminal:parts.append(b)
  need(n==r[2]and h.hexdigest()==r[3],'remote member complete SHA mismatch');full_bytes+=n
  if terminal:
   body=b''.join(parts);j=json.loads(body);root=m.name.split('/')[0];terminal_fields[root]={'sha256':sha(body),'identity_fields':{k:j[k]for k in ['source_sha','sourceSHA','prepared_source_sha','final_sha','evidence_head','ledger_execution_sha','architecture_execution_sha','formal_adoption_executed','product_tests_executed','full_native_executed','full123_executed']if k in j}}
need(names==[r[0]for r in rows]and full_bytes==189987205,'remote complete archive order/byte total mismatch')
n=0
with gzip.open(archive,'rb')as f:
 for b in iter(lambda:f.read(1024**2),b''):n+=len(b)
need(n==inventory['tar_exact_bytes']==223508480,'remote gzip CRC/trailer or exact tar length mismatch')
for r in inventory['roots']:need(terminal_fields[r['name']]['sha256']==r['terminal_sha256'],'original per-root terminal SHA changed')
collection_peer=load('/tmp/geo337-closed-originals-package-actual-peer-20261026/REVIEW.json')
need(collection_peer['exit_code']==0 and collection_peer['blocking_findings']==[]and collection_peer['originals_unchanged']and collection_peer['archive_sha256']==sources[archive_dest]['sha256']and collection_peer['index_sha256']==sources[index_dest]['sha256'],'remote archive differs from independent actual package peer')
executor=raw(INNER/'EXECUTOR.py').decode();need("need(snapshot()==before,'existing writer changed before push')"in executor and "need(snapshot()==before,'existing writer changed after push')"in executor and "'index':h((ROOT/'.git/index').read_bytes())"in executor,'exact index runtime guard absent')
need(ir['capacity']['used']+ir['capacity']['additional_bound']<=2*1024**3,'original publication capacity bound exceeded')

review={'schema':'closed-first-publication-independent-actual-peer/1','exit_code':0,'blocking_findings':[],'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checked_count':check_count,'evidence_head':E,'product_anchor_sha':F,'branch':BRANCH,'publication_execution_source_sha':None,'source_identity_rule':'Each archived original retains its S10/a6/F/synthetic identity. Publication parent is never an execution-source relabel.','files':27,'distinct_remote_blobs':25,'total_publication_file_bytes':sum(x['bytes']for x in manifest['files']),'total_unique_remote_bytes':sum(x['bytes']for x in remote.values()),'raw_original_commands_checked':107,'actual_outer_exit':0,'actual_inner_exit':0,'expected_parent_CAS':{'old':F,'new':E,'ref':REF,'ordinary_push':True,'exact_one_ref_update':True},'scope':{'manifest_sha256':MANIFEST_PIN,'recursive_tree_delta_exactly_27_evidence_paths':True,'existing_evidence_overwrites':[PROGRESS],'old_progress_blob':OLD_PROGRESS,'product_modified':False,'train_ref_modified':False},'writer_preservation':{'historical_HEAD':HEAD,'historical_branch':'codex/train-337-continue-20261024','three_HEAD_branch_status_snapshots_match':True,'index_runtime_pre_post_hash_equality_guard_executed':True,'index_independent_archived_pre_post_values_available':False,'limitation':'The exact pinned executor compares raw index SHA256 before push and after all remote reads. Actual exit0 proves those comparisons passed; the individual index hash values were not emitted as separate artifacts, so no independently archived before/after index bytes are claimed.'},'remote_archive':{'destination':archive_dest,**remote[sources[archive_dest]['blob_oid']],'index_destination':index_dest,'index_sha256':sources[index_dest]['sha256'],'index_bytes':sources[index_dest]['bytes'],'root_count':17,'member_count':32871,'file_count':24966,'directory_count':7905,'logical_bytes':full_bytes,'tar_exact_bytes':n,'all_members_exact_once':True,'every_file_sha256_from_remote_archive_checked':True,'complete_remote_gzip_crc_checked':True,'terminal_identity_fields':terminal_fields},'original_receipts':{'inner_result_sha256':stream(INNER/'RESULT.json')['sha256'],'outer_result_sha256':stream(OUTER/'RESULT.json')['sha256'],'inner_subcommands_sha256':stream(INNER/'subcommands.json')['sha256'],'outer_subcommands_sha256':stream(OUTER/'subcommands.json')['sha256'],'executor_sha256':EXEC_PIN,'remote_blobs_metadata_sha256':stream(INNER/'REMOTE_BLOBS.json')['sha256']},'remote_readback_details':list(remote.values()),'persistent_delivery_scope':'Only these 27 files, including the complete fixed 17-root original archive plus INDEX. Remote raw GitHub bytes were recorded after ordinary push and independently re-read here.','limits':['This is historical E1 remote publication evidence at the recorded capture times, not a new live API observation.','Other peer full drafts, #300 originals, and subsequent API identity work are outside this first batch.','No native/browser/full123 product verdict is added by publication or this review.','The publisher and Git/API commands were not rerun. No originals, fixtures, Git objects or cache were deleted or modified.','No duplicate large INDEX or archive was written; all verification streamed existing original/captured files.'],'audit_git_or_network_executed':False,'audit_product_tests_rerun':False,'audit_SHM_mutation':False,'originals_removed':False,'durable_delivery_verified':True}
(OUT/'REVIEW.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
(OUT/'SUMS.sha256').write_text(''.join(sha(p.read_bytes())+'  '+p.name+'\n'for p in sorted(OUT.iterdir())if p.is_file()and p.name!='SUMS.sha256'))
print(json.dumps({'exit_code':0,'checks':check_count,'review_sha256':sha((OUT/'REVIEW.json').read_bytes()),'new_bytes':sum(p.stat().st_size for p in OUT.iterdir()if p.is_file())}))
