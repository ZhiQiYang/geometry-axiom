"""Independent read-only audit of completed original publication, no network."""
from pathlib import Path
import hashlib,json,os,stat,gzip,datetime,subprocess
OUT=Path(__file__).parent
OWN=Path('/dev/shm/geometry-axiom-geo337-20261025')
PUB=OWN/'recovery-publication-original-20261026'
E='9a57aea2128a7bc3985064932c24e2229fd8fcb8';BASE='a6f4013364e21bcb7239b5dcc25caac0f6d61f77';OLD='3e4f2560aa11ed2a626db98ba5ed6f129e791052'
BRANCH='codex/train337-recovered-evidence-20261026'
MAN=Path('/tmp/geo337-recovery-combined-manifest-v2-20261026.json')
MPIN='4429a5fc97d59204a4d2a24fcce5553194b6ef55497d7d830127b9921c8b2a9f'
def H(b):return hashlib.sha256(b).hexdigest()
def G(b,kind='blob'):return hashlib.sha1(kind.encode()+b' '+str(len(b)).encode()+b'\0'+b).hexdigest()
def J(p):return json.loads(Path(p).read_bytes())
checks=0;findings=[]
def C(ok,msg):
 global checks
 checks+=1
 if not ok:findings.append(msg)
def W(name,obj):(OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
result=J(PUB/'RESULT.json');remote=J(PUB/'REMOTE_BLOBS.json');host=J('/tmp/geo337-recovery-publication-EXEC_FINAL-20261026.json')
C(H(MAN.read_bytes())==MPIN,'manifest pin');C((PUB/'MANIFEST.json').read_bytes()==MAN.read_bytes(),'publication exact manifest copy')
manifest=J(MAN)['files'];C(len(manifest)==1058,'1058 source leaves')
C(result['exit_code']==0 and result['published'] is True and result['delivered'] is True,'published true final0')
C(result['evidence_head']==E and result['base_sha']==BASE and result['branch']==BRANCH,'exact publication identity')
C(host['exit_code']==0 and 'session_id' not in host,'actual host terminal0')
C(json.loads(host['output'])==result,'actual host stdout matches result')
executor=(PUB/'EXECUTOR.py').read_bytes();C(H(executor)=='c6a44de7ada360b6017a0e578507b81867471f583d8e9b6b591d56581ba41368','actual executed publisher pin')
C(b"need(snapshot()==before,'existing writer changed before push')" in executor and b"need(snapshot()==before,'existing writer changed after push')" in executor,'actual preserved index snapshot guards')
C(b"'index':h((ROOT/'.git/index').read_bytes())" in executor and b"need(not sys.flags.optimize" in executor,'index hash equality guard active')
rows=J(PUB/'subcommands.json');C(len(rows)==2167,'2167 original commands')
C({p.name for p in (PUB/'subcommands').iterdir()}=={f'{i:06d}' for i in range(1,len(rows)+1)},'exact command directory namespace')
parsed=[];raw_bytes=0
for i,row in enumerate(rows,1):
 p=PUB/'subcommands'/f'{i:06d}';request=J(p/'request.json');actual=J(p/'result.json')
 C(actual==row,f'command {i} original list/result identity')
 C(Path(row['directory'])==p,f'command {i} exact directory')
 C(row['actual_process_returncode']==0 and row['timeout_expired'] is False and row['ended_epoch']>=row['started_epoch'],f'command {i} true completed0')
 for key in ['command','cwd','acceptance_sha','source_sha','source_variant','environment','stdin_provided','stdin_sha256','started_epoch','directory']:
  C(request.get(key)==row.get(key),f'command {i} request/result {key}')
 C(request['actual_process_returncode'] is None,f'command {i} original request not relabelled')
 streams={k:(p/(k+'.bin')).read_bytes() for k in ['stdin','stdout','stderr']}
 for k,b in streams.items():
  C(H(b)==row[k+'_sha256'],f'command {i} {k} hash')
  if k!='stdin':C(len(b)==row[k+'_bytes'],f'command {i} {k} bytes')
  raw_bytes+=len(b)
 parsed.append((row['command'],streams))
remote_by_oid={x['blob_oid']:x for x in remote};C(len(remote)==len(remote_by_oid)==606,'606 unique remote identities')
api={};hashwrites={};trees={};newtrees={};snapshots={'head':[],'branch':[],'status':[]};pushes=[];updates=[];ref_reads=[];commits=[];diffs=[]
def parse_tree(b):
 d={}
 for row in b.split(b'\0'):
  if row:
   head,name=row.split(b'\t',1);mode,kind,oid=head.split(b' ');d[name.decode()]=(mode,kind,oid)
 return d
for cmd,streams in parsed:
 if cmd[0]=='gh':
  prefix=['gh','api','--hostname','github.com','-H','Accept: application/vnd.github.raw+json']
  C(cmd[:6]==prefix and len(cmd)==7,'API exact readonly GET argv')
  oid=cmd[-1].split('/')[-1];C(cmd[-1]=='repos/ZhiQiYang/geometry-axiom/git/blobs/'+oid,'API only intended repository blob GET')
  payload=streams['stdout'];C(oid not in api,'API no duplicate blob observation');api[oid]=payload
  C(oid in remote_by_oid,'API blob in remote index')
  if oid in remote_by_oid:
   ident=remote_by_oid[oid];C(ident['bytes']==len(payload) and ident['sha256']==H(payload) and G(payload)==oid,'remote complete bytes/hash/OID '+oid)
 elif cmd[0]=='git':
  C(cmd[:5]==['git','-c','gc.auto=0','-c','maintenance.auto=false'],'original Git no auto GC config')
  args=cmd[5:];op=args[0]
  C(op in ['rev-parse','status','branch','ls-remote','for-each-ref','merge-base','hash-object','ls-tree','mktree','commit-tree','diff-tree','diff','update-ref','push'],'no unexpected Git mutation operation')
  if op=='hash-object':
   C(args[1:4]==['-w','--no-filters','--'],'hash-object no filters')
   source=args[4];C(source not in hashwrites,'source hashed once');hashwrites[source]=streams['stdout'].decode().strip()
  elif op=='ls-tree':trees[args[-1]]=parse_tree(streams['stdout'])
  elif op=='mktree':
   oid=streams['stdout'].decode().strip();entries=parse_tree(streams['stdin']);newtrees[oid]=entries
   ordered=sorted(entries.items(),key=lambda x:x[0].encode()+(b'/' if x[1][1]==b'tree' else b''))
   raw=b''.join(mode.lstrip(b'0')+b' '+name.encode()+b'\0'+bytes.fromhex(obj.decode()) for name,(mode,kind,obj) in ordered)
   C(G(raw,'tree')==oid,'created tree full Git identity '+oid)
  elif op=='rev-parse' and args[1:] == ['HEAD']:snapshots['head'].append(streams['stdout'])
  elif op=='branch':snapshots['branch'].append(streams['stdout'])
  elif op=='status':snapshots['status'].append(streams['stdout'])
  elif op=='push':pushes.append(args)
  elif op=='update-ref':updates.append(args)
  elif op=='ls-remote':ref_reads.append((args,streams['stdout']))
  elif op=='commit-tree':commits.append((args,streams))
  elif op in ['diff','diff-tree']:diffs.append((args,streams['stdout']))
 else:C(False,'unexpected command program')
C(set(api)==set(remote_by_oid),'remote index exactly matches original API streams')
C(len(hashwrites)==len(manifest),'every manifest leaf hashed')
manifest_oids={};destinations=set();source_payload_bytes=0
for item in manifest:
 src=Path(item['source_path']);dst=item['destination'];C(dst not in destinations and dst.startswith('evidence/geo337-train-20261024/'),'unique evidence-only path');destinations.add(dst)
 C(src.is_file() and not src.is_symlink(),'original source remains regular '+str(src))
 b=src.read_bytes();C(len(b)==item['bytes'] and H(b)==item['sha256'],'original manifest bytes '+str(src));source_payload_bytes+=len(b)
 oid=G(b);C(hashwrites.get(str(src))==oid,'actual original hash-object result '+str(src));C(oid in api and api.get(oid)==b,'complete remote bytes same original '+str(src))
 manifest_oids[dst]=oid
C(len(commits)==1,'one new commit');args,streams=commits[0];tree=args[1]
C(args==['commit-tree',tree,'-p',BASE] and streams['stdout']==(E+'\n').encode(),'single correct evidence commit parent')
C(streams['stdin']==b'docs: recover completed S10 ledger and original acceptance evidence\n','English commit message')
def resolve(tree,path):
 parts=path.split('/')
 for i,name in enumerate(parts):
  C(tree in trees,'visited tree has original ls-tree observation '+tree)
  if tree not in trees:return None
  entry=trees[tree].get(name)
  if entry is None:return None
  if i==len(parts)-1:return entry
  if entry[1]!=b'tree':return None
  tree=entry[2].decode()
for dst,oid in manifest_oids.items():C(resolve(tree,dst)==(b'100644',b'blob',oid.encode()),'actual final tree exact destination '+dst)
for oid,expected in newtrees.items():C(trees.get(oid)==expected,'created tree observed unchanged '+oid)
C(pushes==[['push','https://github.com/ZhiQiYang/geometry-axiom.git','refs/heads/'+BRANCH+':refs/heads/'+BRANCH]],'only normal push to new recovery branch')
C(updates==[['update-ref','refs/heads/'+BRANCH,E,'0'*40]],'only new local branch update with absent guard')
C(len(ref_reads)==3 and ref_reads[0][1]==b'' and all(x[1]==(E+'\trefs/heads/'+BRANCH+'\n').encode() for x in ref_reads[1:]),'remote absent then same exact E before/after all blob GETs')
C(snapshots['head']==[(OLD+'\n').encode()]*3,'original HEAD preserved three actual observations')
C(snapshots['branch']==[b'codex/train-337-continue-20261024\n']*3,'original train branch preserved three observations')
C(snapshots['status']==[b'']*3,'original writer clean three observations')
C(result['existing_writer_unchanged'] is True and result['train_ref_modified'] is False,'executed complete snapshot guards accepted')
change=[(a,b) for a,b in diffs if a[0]=='diff-tree'];nondiff=[(a,b) for a,b in diffs if a[0]=='diff']
C(len(change)==1 and set(change[0][1].decode().strip('\0').split('\0'))==destinations,'exact diff equals manifest')
C(len(nondiff)==1 and nondiff[0][1]==b'' and nondiff[0][0]==['diff','--name-only',BASE,E,'--','.',':(exclude)evidence'],'original non-evidence diff empty')
# A single local immutable object read verifies commit serialization; no network or ref/index write.
env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')};env.update(GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1',GIT_NO_LAZY_FETCH='1')
argv=['git','--git-dir',str(OWN/'publisher-source/.git'),'cat-file','commit',E]
proc=subprocess.run(argv,capture_output=True,env=env,timeout=30)
(OUT/'LOCAL_COMMIT.stdout.bin').write_bytes(proc.stdout);(OUT/'LOCAL_COMMIT.stderr.bin').write_bytes(proc.stderr)
W('LOCAL_COMMIT_COMMAND.json',{'command':argv,'exit_code':proc.returncode,'stdout_sha256':H(proc.stdout),'stderr_sha256':H(proc.stderr),'network_requested':False,'ref_or_index_mutation_requested':False})
C(proc.returncode==0 and G(proc.stdout,'commit')==E,'actual immutable local commit complete bytes/OID')
C(proc.stdout.splitlines()[0]==('tree '+tree).encode() and [x for x in proc.stdout.splitlines() if x.startswith(b'parent ')]==[('parent '+BASE).encode()],'actual immutable commit tree/single parent')
archive_root=OWN/'native-TMP-preservation-20261025';ar=J(archive_root/'RESULT.json');arhash=H((archive_root/'RESULT.json').read_bytes())
C(arhash=='101f12889f90c14b4ab57d11c7d0d7893513c2496bad0fc281237a8220dd0385','exact original archive RESULT')
C(ar['exit_code']==0 and ar['originals_removed'] is False and len(ar['archives'])==26,'complete26 original preservation result')
preserved=[]
for item in ar['archives']:
 payloads=[]
 for member,size,pin in [(item['raw_member'],item['raw_bytes'],item['raw_sha256']),(item['gzip_member'],item['gzip_bytes'],item['gzip_sha256'])]:
  f=archive_root/member;b=f.read_bytes();oid=G(b)
  C(len(b)==size and H(b)==pin,'archive local member identity '+member)
  C(any(x['source_path']==str(f) and x['bytes']==size and x['sha256']==pin for x in manifest),'archive member actually in published manifest '+member)
  C(oid in api and api[oid]==b,'archive member complete remote payload '+member)
  payloads.append(b)
 C(gzip.decompress(payloads[1])==payloads[0],'26 gzip complete roundtrip '+item['original_path'])
 original=Path(item['original_path']);C(original.is_file() and H(original.read_bytes())==item['raw_sha256'],'original payload still present '+item['original_path'])
 preserved.append({'original_path':item['original_path'],'raw_blob':G(payloads[0]),'gzip_blob':G(payloads[1]),'raw_bytes':len(payloads[0]),'gzip_bytes':len(payloads[1])})
W('ARCHIVE_26_REMOTE_BINDINGS.json',preserved)
report={'schema':'recovery-publication-actual-independent-peer/1','reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':0 if not findings else 1,'evidence_head':E,'base_sha':BASE,'branch':BRANCH,'checks':checks,'findings':findings,'full_remote_delivery_verified':not findings,'archive_result_sha256':arhash,'remote_result_sha256':H((PUB/'RESULT.json').read_bytes()),'remote_blobs_sha256':H((PUB/'REMOTE_BLOBS.json').read_bytes()),'manifest_sha256':MPIN,'publisher_sha256':H(executor),'host_final_sha256':H(Path('/tmp/geo337-recovery-publication-EXEC_FINAL-20261026.json').read_bytes()),'original_command_count':len(rows),'original_stream_bytes_verified':raw_bytes,'manifest_files':len(manifest),'manifest_logical_bytes':source_payload_bytes,'unique_complete_API_blobs':len(api),'archive_raw_members_verified':26,'archive_gzip_members_verified':26,'archive_raw_and_gzip_full_bytes_remote':not findings,'original_payloads_still_present':not findings,'product_changed':False,'existing_HEAD_status_branch_original_three_snapshots_equal':True,'original_index_integrity_basis':'Actual pinned nonoptimized publisher executed snapshot hash equality before and after normal push; true host exit0. Separate pre/post physical index hashes were not persisted and are not invented by this reviewer.','original_train_ref_integrity_basis':'Only new recovery update-ref/push argv occur; existing HEAD and branch remain train E3e4 in all three complete original snapshots.','network_reread':False,'product_tests_executed':False,'retirement_executed':False,'raw_originals_modified':False,'limits':['Independent evidence integrity review is not product acceptance.','No current global scheduler lease or retirement authorization is granted.','Index pre/post exact hashes were runtime guard values, not independently archived values.']}
W('REVIEW.json',report)
print(json.dumps(report,ensure_ascii=False))
raise SystemExit(report['exit_code'])
