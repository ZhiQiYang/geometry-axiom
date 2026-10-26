"""Read-only peer of completed a6 source preparation; no tests or source writes."""
from pathlib import Path
import datetime, hashlib, json, os, stat, subprocess, time

OUT=Path(__file__).parent
OWN=Path('/dev/shm/geometry-axiom-geo337-20261025')
ROOT=OWN/'a6-architecture-source-20261026'
SRC=OWN/'a6-architecture-source-original-20261026'
OUTER=OWN/'a6-source-root-original-20261026'
OWNER=OWN/'publisher-source'
OLD=OWN/'F10-source-preparation-reserve-anchor/SOURCE_MANIFEST.json'
SOURCE='a6f4013364e21bcb7239b5dcc25caac0f6d61f77'
S10='82c922a3941525d3a094ac0158bdc7dea57ea360'
RESULT_PIN='2c8542df06b79b21a2a94ef5ce382d07a697a562e035ea86613dfb4a135274c4'
TOOL_PIN='8f08d1325d5fa43fef2c3a46ef8bca94693568d7318b1c1326496c44c48fee16'
PEER_PIN='c46793c42cec2bf893f27a3eaeb8482caeca2a2dee25df84d82c8eb3f94890c2'
checks=0; findings=[]; current_commands=[]
def H(b):return hashlib.sha256(b).hexdigest()
def oid(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def check(ok,msg):
 global checks
 checks+=1
 if not ok:findings.append(msg)
def need(ok,msg):
 check(ok,msg)
 if not ok:raise RuntimeError(msg)
def load(p):return json.loads(p.read_bytes())
def identity(p):
 s=p.lstat();return {'device':s.st_dev,'inode':s.st_ino,'mode':s.st_mode,'nlink':s.st_nlink,'size':s.st_size,'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns,'sha256':H(p.read_bytes())}
def audit_capture(directory):
 rows=load(directory/'subcommands.json'); streams=0; summary=[]
 for number,row in enumerate(rows,1):
  d=directory/'subcommands'/f'{number:06d}'
  need(row['directory']==str(d),'original capture directory '+str(d))
  req=load(d/'request.json');result=load(d/'result.json')
  need(row==result,'original command index equals result '+str(d))
  for key,value in req.items():
   need(value is None if key=='actual_process_returncode' else row.get(key)==value,'original request/result '+str(d)+' '+key)
  for n in ['stdin','stdout','stderr']:
   raw=(d/(n+'.bin')).read_bytes();streams+=len(raw)
   need(H(raw)==row[n+'_sha256'],'original full stream SHA '+str(d)+' '+n)
   if n!='stdin':need(len(raw)==row[n+'_bytes'],'original stream size '+str(d)+' '+n)
  need(row['source_sha']==row['acceptance_sha']==SOURCE,'original source/acceptance SHA '+str(d))
  need(row['actual_process_returncode']==0 and row['timeout_expired']is False,'original actual zero/no timeout '+str(d))
  need(row['ended_epoch']>=row['started_epoch'],'original times '+str(d))
  summary.append({'ordinal':number,'directory':str(d),'command_sha256':H(json.dumps(row['command'],ensure_ascii=False,separators=(',',':')).encode()),'argv_prefix':row['command'][:11],'argv_count':len(row['command']),'cwd':row['cwd'],'exit_code':row['actual_process_returncode'],'stdout_bytes':row['stdout_bytes'],'stderr_bytes':row['stderr_bytes'],'stdout_sha256':row['stdout_sha256'],'stderr_sha256':row['stderr_sha256'],'started_epoch':row['started_epoch'],'ended_epoch':row['ended_epoch']})
 return rows,{'commands':len(rows),'full_stream_bytes':streams,'subcommands_sha256':H((directory/'subcommands.json').read_bytes()),'rows':summary}
env={k:v for k,v in os.environ.items()if not k.startswith(('GIT_','GEOMETRY_','MUTATE_'))and k not in ['PYTHONOPTIMIZE','PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','NODE_OPTIONS','LD_PRELOAD']}
env.update(GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1',LANG='C.UTF-8',LC_ALL='C.UTF-8')
def git(cwd,*args):
 argv=['git','-c','gc.auto=0','-c','maintenance.auto=false',*args];start=time.time()
 p=subprocess.run(argv,cwd=cwd,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=120)
 current_commands.append({'command':argv if len(argv)<50 else argv[:10]+['<all selected paths bound by manifest>'],'full_argv_sha256':H(json.dumps(argv,ensure_ascii=False,separators=(',',':')).encode()),'cwd':str(cwd),'exit_code':p.returncode,'started_epoch':start,'ended_epoch':time.time(),'stdout_bytes':len(p.stdout),'stderr_bytes':len(p.stderr),'stdout_sha256':H(p.stdout),'stderr_sha256':H(p.stderr),'small_stdout':p.stdout.decode(errors='replace') if len(p.stdout)<512 else None,'stderr':p.stderr.decode(errors='replace')})
 need(p.returncode==0,'current read-only Git zero: '+str(args[:3]));return p.stdout

report={'source_sha':SOURCE,'source_result_sha256':RESULT_PIN,'exit_code':1,'blocking_findings':findings,'review_type':'independent actual source verification','source_materialization_rerun':False,'formal_gates_executed':False,'cleanup_performed':False,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
try:
 result_raw=(SRC/'RESULT.json').read_bytes();need(H(result_raw)==RESULT_PIN,'fixed actual source result pin');res=json.loads(result_raw)
 need(res['source_sha']==SOURCE and res['exit_code']==0 and res['materialized']is True,'actual source terminal zero')
 need(res['source_root']==str(ROOT) and res['source_hardlinks_used']is False and res['historical_sources_modified']is False and res['canonical_writer_unchanged']is True,'source original preservation result')
 need(load(OUTER/'RESULT.json')['exit_code']==0,'outer actual zero')
 need(H((SRC/'EXECUTOR.py').read_bytes())==TOOL_PIN,'actual executed source tool exact static-reviewed pin')
 need(H((OUTER/'STATIC_PEER.json').read_bytes())==PEER_PIN,'outer bound independent static peer')
 old_raw=OLD.read_bytes();need(H(old_raw)==res['old_selected_manifest_sha256']=='e919aab396841642d093495b6fa7c7f4a20f55e1557929471dd6b2a81065057a','old selected manifest pin');old=json.loads(old_raw)
 manifest_raw=(SRC/'SOURCE_MANIFEST.json').read_bytes();need(H(manifest_raw)==res['source_manifest_sha256'],'actual source manifest pin');manifest=json.loads(manifest_raw)
 observed_raw=(SRC/'pool-materialized.json').read_bytes();need(H(observed_raw)==res['source_rows_sha256'],'actual materialized row pin');observed=json.loads(observed_raw)
 need(old['source_sha']==S10 and manifest['source_sha']==SOURCE and manifest['blueprint_source_sha']==S10 and manifest['blueprint_manifest_sha256']==H(old_raw),'old/new blueprint source boundary')
 need(len(manifest['files'])==len(observed)==res['source_files']==3763,'complete 3763 leaves')
 need(manifest['seed_paths']==old['seed_paths'] and manifest['architecture_paths']==old['architecture_paths'] and manifest['fixture_paths']==old['fixture_paths'],'same full selected / architecture / fixture lists')
 need(len(set(manifest['architecture_paths']))==res['architecture_inputs']==604 and len(set(manifest['fixture_paths']))==res['mandatory_fixtures']==5,'604 architecture inputs and five mandatory fixtures')
 need(set(manifest['files'])==set(old['files']),'old full selected set retained')
 need([p for p in sorted(manifest['files'])if manifest['files'][p]!=old['files'][p]]==['決策佇列.md'],'only decision selected blob changed')
 floor=sum((x['bytes']+4095)//4096*4096 for x in old['files'].values());cap=res['capacity']
 need(floor==cap['source_floor']==148652032,'source floor recomputed from original full selection')
 need(cap['additional_bound']==floor+4096+16*1024**2+32*1024**2+16*1024**2+64*1024**2==282873856,'full original source plus overhead and reserve bound')
 need(cap['original_reserve_bytes']==67108864 and cap['shared_ceiling']==2147483648 and cap['shared_before']+cap['additional_bound']<=cap['shared_ceiling'],'original 64 MiB/2 GiB guard not lowered')
 inner,inner_summary=audit_capture(SRC);outer,outer_summary=audit_capture(OUTER)
 need(len(inner)==19 and len(outer)==1,'original complete 19 Git commands plus one outer executor')
 need(outer[0]['command']==['python3','-B','/tmp/geo337-a6-architecture-preparation-20261026/prepare_source.py','--execute-root-approved'],'outer exact original executable argv')
 need(json.loads((OUTER/'subcommands/000001/stdout.bin').read_bytes())==res,'outer stdout equals actual terminal source result')
 for i,row in enumerate(inner,1):
  need(row['command'][:5]==['git','-c','gc.auto=0','-c','maintenance.auto=false'],'original Git-only command '+str(i))
 need((SRC/'subcommands/000001/stdout.bin').read_bytes()==(SRC/'subcommands/000018/stdout.bin').read_bytes(),'original provider HEAD before/after equality')
 need((SRC/'subcommands/000002/stdout.bin').read_bytes()==(SRC/'subcommands/000019/stdout.bin').read_bytes()==b'','original provider clean status before/after')
 need((SRC/'subcommands/000015/stdout.bin').read_bytes().strip().decode()==SOURCE and (SRC/'subcommands/000016/stdout.bin').read_bytes()==b'','original new checkout exact HEAD/clean status')
 need((SRC/'subcommands/000006/stdout.bin').read_bytes()=='決策佇列.md\0'.encode(),'original non-evidence change only decision')
 need(H((SRC/'subcommands/000008/stdout.bin').read_bytes())=='e6f2aee291850d9aaf8cc0026994f6c86894bb2a7849798ddd11cd63c5558740','original a6 decision bytes pin')
 original_tree=(SRC/'subcommands/000007/stdout.bin').read_bytes();tree={}
 for line in original_tree.split(b'\0'):
  if not line:continue
  meta,name=line.split(b'\t',1);mode,kind,git_oid,size=meta.split();need(kind==b'blob','original selected tree all blobs')
  tree[os.fsdecode(name)]={'mode':mode.decode(),'oid':git_oid.decode(),'bytes':int(size)}
 need(tree==manifest['files'],'original Git tree equals entire selected manifest')
 sparse=(SRC/'pool-sparse-checkout.txt').read_bytes()
 need((ROOT/'.git/info/sparse-checkout').read_bytes()==sparse,'actual sparse rules exact original')
 need((ROOT/'.git/objects/info/alternates').read_text().splitlines()==[str(OWNER/'.git/objects')],'single explicit existing provider alternate')
 need((ROOT/'.git/HEAD').read_text().strip()==SOURCE,'actual detached a6 HEAD bytes')
 idx_before=identity(ROOT/'.git/index');owner_idx_before=identity(OWNER/'.git/index')
 current_head=git(ROOT,'rev-parse','HEAD').decode().strip();current_status=git(ROOT,'status','--porcelain=v1','--untracked-files=all')
 need(current_head==SOURCE and current_status==b'','current frozen new source exact clean a6')
 ls=git(ROOT,'ls-files','-t','-z');need(ls==(SRC/'subcommands/000017/stdout.bin').read_bytes(),'entire current index sparse selection equals original')
 selected={os.fsdecode(x[2:])for x in ls.split(b'\0')if x and x[:1]!=b'S'}
 need(selected==set(manifest['files']),'exact current 3763 materialized Git entries')
 current_tree=git(ROOT,'ls-tree','-r','-l','-z',SOURCE,'--',*sorted(manifest['files']))
 need(current_tree==original_tree,'independent current Git tree exact original full selection')
 actual_physical=set();directory_symlinks=[]
 for parent,dirs,files in os.walk(ROOT,followlinks=False):
  if Path(parent)==ROOT:dirs[:]=[d for d in dirs if d!='.git']
  for n in dirs:
   if (Path(parent)/n).is_symlink():directory_symlinks.append(str(Path(parent)/n))
  for n in files:actual_physical.add((Path(parent)/n).relative_to(ROOT).as_posix())
 need(not directory_symlinks and actual_physical==selected,'physical worktree has exact selected leaf set; no extra files or symlink dirs')
 need(not any(x.startswith('evidence/')for x in actual_physical),'root evidence excluded')
 fixtures=set(manifest['fixture_paths']);need({x for x in actual_physical if x.startswith(('tests/evidence/','tests/release-evidence/'))}=={x for x in fixtures if x.startswith(('tests/evidence/','tests/release-evidence/'))},'excluded test evidence contains only explicitly required fixtures')
 rows={x['path']:x for x in observed};need(len(rows)==len(observed),'unique original materialized rows')
 inodes=set();allocated=0;totalbytes=0;fixture_rows=[];digest=hashlib.sha256()
 for n in sorted(selected):
  p=ROOT/n;st=p.lstat();m=manifest['files'][n];o=rows[n]
  need(stat.S_ISREG(st.st_mode)and st.st_nlink==1,'actual regular independent nlink=1 '+n)
  need((st.st_dev,st.st_ino)not in inodes,'unique new source inode '+n);inodes.add((st.st_dev,st.st_ino))
  need((st.st_dev,st.st_ino,st.st_nlink,st.st_blocks*512)==(o['device'],o['inode'],o['nlink'],o['allocated_bytes']),'actual inode/lstat exact materialization '+n)
  b=p.read_bytes();sha=H(b);blob=oid(b)
  need(blob==m['oid']==o['oid']and sha==o['raw_sha256']and len(b)==m['bytes']==o['bytes'],'actual raw bytes/SHA256/Git blob exact '+n)
  need(bool(st.st_mode&0o111)==(m['mode']=='100755'),'actual executable mode equals Git '+n)
  allocated+=st.st_blocks*512;totalbytes+=len(b);digest.update(n.encode()+b'\0'+bytes.fromhex(sha))
  if n in fixtures:fixture_rows.append({'path':n,'bytes':len(b),'raw_sha256':sha,'git_blob_oid':blob,'nlink':st.st_nlink,'device':st.st_dev,'inode':st.st_ino})
 need(allocated==res['allocated_source_files']==148656128,'actual full selected allocation agrees with receipt')
 need(H((ROOT/'決策佇列.md').read_bytes())=='e6f2aee291850d9aaf8cc0026994f6c86894bb2a7849798ddd11cd63c5558740','physical a6 decision pin')
 current_owner_head=git(OWNER,'rev-parse','HEAD');need(current_owner_head==(SRC/'subcommands/000018/stdout.bin').read_bytes(),'canonical provider HEAD still original')
 need(identity(ROOT/'.git/index')==idx_before and identity(OWNER/'.git/index')==owner_idx_before,'peer own read-only Git left both real index identities/bytes unchanged')
 report.update(original_inner=inner_summary,original_outer=outer_summary,source_files=len(selected),architecture_inputs=604,mandatory_fixtures=fixture_rows,full_selected_bytes=totalbytes,allocated_source_files=allocated,ordered_path_raw_sha256_digest=digest.hexdigest(),source_manifest_sha256=H(manifest_raw),source_rows_sha256=H(observed_raw),outer_result_sha256=H((OUTER/'RESULT.json').read_bytes()),source_executor_sha256=TOOL_PIN,root_executor_sha256=H((OUTER/'EXECUTOR.py').read_bytes()),current_head=current_head,current_source_index=idx_before,current_provider_index=owner_idx_before,original_provider_head=current_owner_head.decode().strip(),capacity=cap,all_source_bytes_git_oids_and_inodes_verified=True,source_exclusions_verified=True,source_fixtures_retained=True,source_independent_inodes=True,current_readonly_git=current_commands)
 report['limitations']=['Original provider index before/after hashes were compared in the pinned successful original executor but not written individually. This peer independently proves current provider index unchanged during its own read-only commands; it does not invent historical index values.','Original actual-mount free capacity was tested by pinned source executor before allocation but not separately persisted as a numeric value. Shared-before/bound/reserve are recorded and independently recomputed; no new admission is inferred.','Source resides on tmpfs and uses publisher-source Git alternate. Preserve provider and original packets; this peer is not remote delivery proof.','S10 ledger and earlier mutation probes are historical; no product judge, ledger, native or browser execution performed by this peer.','Decision raw hash is source identity only and does not approve new semantics.']
except BaseException as exc:
 if not findings:findings.append(repr(exc))
 report['exception']=repr(exc)
finally:
 report.update(exit_code=1 if findings else 0,blocking_findings=findings,checked_count=checks)
 (OUT/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'exit_code':report['exit_code'],'checked_count':checks,'blocking_findings':findings,'review_sha256':H((OUT/'REVIEW.json').read_bytes()),'review_bytes':(OUT/'REVIEW.json').stat().st_size},ensure_ascii=False))
raise SystemExit(report['exit_code'])
