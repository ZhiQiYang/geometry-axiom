from pathlib import Path
import ast,copy,gzip,hashlib,io,json,os,runpy,stat,subprocess,sys,tarfile,types

OUT=Path(__file__).parent
SRC=Path('/tmp/geo337-closed-originals-collection-preparation-20261026/collect_closed.py')
PIN='e3c516027d8868dda1c501631eb1d870e38269b78cf5856cdb6a470ba920eb7f'
PLAN=SRC.parent/'PLAN.all.json'
PLAN_PIN='3e91e87b2ba26ec42c6a4351af59ab0c873d7b269d8280ddcd93158ff9e97986'
sha=lambda b:hashlib.sha256(b).hexdigest()
def save(name,obj):
 (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
code=SRC.read_text();tree=ast.parse(code);env=runpy.run_path(str(SRC),run_name='independent_static_peer')
plan=json.loads(PLAN.read_bytes());inv=plan['inventory'];checks=[]
def check(name,ok):
 checks.append({'name':name,'passed':bool(ok)})
 if not ok:raise AssertionError(name)
def text(fragment):return fragment in code
check('exact_subject_pin',sha(SRC.read_bytes())==PIN)
check('exact_plan_all_pin',sha(PLAN.read_bytes())==PLAN_PIN)
check('fixed_17_unique_roots',inv['root_names']==env['BASE_ROOTS']+env['FINAL_ROOTS'] and len(set(inv['root_names']))==17)
check('no_active_product_checkouts',not set(inv['root_names'])&{'publisher-source','a6-architecture-source-20261026','F10-pool','source','cache'})
check('plan_every_root_has_closed_terminal',all(r['terminal_exit']==0 or (r['name']=='recovery-prbody-publication-20261026' and r['terminal_passed'] is True) for r in inv['roots']))
check('plan_counts',inv['file_count']==24966 and inv['directory_count']==7905 and inv['logical_bytes']==189987205 and inv['member_count']==32871)
check('fixed_original_capacity',env['RESERVE']==64*1024**2 and env['META']==16*1024**2 and env['CEILING']==2*1024**3)
check('exact_archive_bound',inv['tar_exact_bytes']==223508480 and inv['gzip_upper_bytes']==223577721 and inv['additional_bound_bytes']==307463801)
check('historical_admission_arithmetic',plan['capacity']['shared_allocated_bytes']+inv['additional_bound_bytes']==2107967097<=env['CEILING'])
check('pinned_request_plan_peer',all(text(s) for s in ["sha(raw)==a.request_sha256","sha(plan_raw)==q['plan']['sha256']","sha(peer_raw)==q['peer']['sha256']","peer.get('collector_sha256')==sha(tool)"]))
check('explicit_root_no_writers_lease',text("q.get('root_execution_lease')is True and q.get('root_no_writers_in_selected_roots')is True"))
check('peer_is_true_integer_zero',text("type(peer.get('exit_code'))is int and peer['exit_code']==0 and peer.get('blocking_findings')==[]"))
check('fresh_full_inventory_matches_plan_before_write',text("summary,rows=scan(plan['inventory']['root_names']);need(summary==plan['inventory']"))
check('fresh_direct_OWN_output',text("out.parent==OWN and out.name.startswith('resume-closed-original-package-')and not out.exists()"))
check('fresh_admission_before_SHM_mkdir',code.index("capacity=admission(summary);need(capacity['admitted']")<code.index('out.mkdir();result='))
check('metadata_bytes_measured_and_bounded',text("metadata_upper=len(index)+len(raw)+len(plan_raw)+len(peer_raw)+len(tool)+1024**2;need(metadata_upper<=META"))
check('OWN_physical_and_roots_no_symlinks',text('OWN.resolve()==OWN') and text("root.is_dir()and not root.is_symlink()") and text("terminal.is_file()and not terminal.is_symlink()"))
check('all_traversed_entries_checked',text('os.walk(root,followlinks=False)') and text('for leaf in dirs+files:rows.append(row_for(Path(directory)/leaf))'))
check('before_after_stat_and_sha',text("'st_mode','st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_nlink'") and text("def verify(row):need(row_for(OWN/row[0])==row"))
check('all_original_bytes_streamed_without_links',text("with (OWN/row[0]).open('rb')as f:tar.addfile(info,f)") and text('verify(row);info=info_for(row)') and text('    verify(row)'))
check('archive_scope_order_exact',text("[m.name for m in members]==[r[0]for r in rows]"))
check('every_member_size_mode_time_checked',text("m.size==r[2]and m.mode==(r[4]&0o777)and m.mtime==r[7]//10**9"))
check('every_regular_member_full_hash',text("m.isfile()and not m.islnk()and not m.issym()") and text("n==r[2]and hh.hexdigest()==r[3]"))
check('complete_gzip_crc_to_eof_and_exact_length',text("with gzip.open(archive,'rb')as f:") and text("need(n==summary['tar_exact_bytes']"))
check('final_entire_original_scope_unchanged',text("after,_=scan(summary['root_names']);need(after==summary"))
check('final_original_capacity_preserved',text("final_usage['shared_allocated_bytes']+RESERVE<=CEILING and final_usage['mount_free_bytes']>=RESERVE"))
check('no_source_sha_relabelling_or_delivery_claim',text("'source_execution_sha':None") and text("'published':False,'delivered':False,'storage_is_volatile':True"))
calls=[n.func.attr if isinstance(n.func,ast.Attribute) else n.func.id if isinstance(n.func,ast.Name) else '' for n in ast.walk(tree) if isinstance(n,ast.Call)]
check('no_deletion_or_subprocess_git_network',not set(calls)&{'unlink','rmdir','rmtree','remove','rename','replace','Popen','run','system','execve','request','urlopen'})
check('source_writes_only_named_new_package_outputs',not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='open' and n.args and isinstance(n.args[0],ast.Constant) and any(c in str(n.args[0].value) for c in 'wa+') for n in ast.walk(tree)))

# Exercise the actual admission function with synthetic usage metadata; no FS access.
original_usage=env['admission'].__globals__['usage'];cap=[]
for shared,free,want in [(env['CEILING']-inv['additional_bound_bytes'],inv['additional_bound_bytes'],True),(env['CEILING']-inv['additional_bound_bytes']+1,inv['additional_bound_bytes'],False),(0,inv['additional_bound_bytes']-1,False)]:
 env['admission'].__globals__['usage']=lambda shared=shared,free=free:{'shared_allocated_bytes':shared,'shared_ceiling_bytes':env['CEILING'],'mount_free_bytes':free}
 result=env['admission'](inv);cap.append({'shared':shared,'free':free,'admitted':result['admitted'],'expected':want});check('actual_capacity_case_'+str(len(cap)),result['admitted']==want)
env['admission'].__globals__['usage']=original_usage

# Actual row_for guard, withdrawn only in memory, then restored. No source files.
def row_guard(withdrawn):
 ns=dict(env);node=copy.deepcopy(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='row_for'))
 if withdrawn:
  target=next(n for n in node.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='need')
  target.value.args[0]=ast.Constant(True)
 exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<actual-row_for-memory>','exec'),ns)
 s=types.SimpleNamespace(st_mode=stat.S_IFLNK|0o777,st_dev=1,st_ino=1,st_size=0,st_mtime_ns=1,st_ctime_ns=1,st_nlink=1)
 class Fake:
  def lstat(self):return s
  def relative_to(self,other):return Path('fixed-root/leaf')
  def __str__(self):return '<memory-symlink>'
 try:ns['row_for'](Fake())
 except RuntimeError as e:
  return {'exit_code':0,'output':str(e)} if 'refuse symlink/special member' in str(e) else {'exit_code':1,'output':str(e)}
 return {'exit_code':1,'output':'SYMLINK_MEMBER_NOT_REJECTED'}
counter=[row_guard(False),row_guard(True),row_guard(False)]
check('actual_row_guard_withdraw_restore_010',[r['exit_code']for r in counter]==[0,1,0] and counter[1]['output']=='SYMLINK_MEMBER_NOT_REJECTED')

# Execute only the collector's exact archive readback/CRC AST against tiny /tmp archives.
main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');attempt=next(n for n in main.body if isinstance(n,ast.Try))
start=next(i for i,n in enumerate(attempt.body)if isinstance(n,ast.With) and ast.unparse(n.items[0].context_expr)=="tarfile.open(archive, 'r:gz')")
end=next(i for i,n in enumerate(attempt.body)if isinstance(n,ast.Assign) and any(isinstance(t,ast.Tuple)for t in n.targets))
readback=compile(ast.fix_missing_locations(ast.Module(body=attempt.body[start:end],type_ignores=[])),'<actual-archive-readback>','exec')
payload=b'collector-peer-original\n';name='root/'+('long-segment/'*10)+'leaf';row=[name,'file',len(payload),sha(payload),stat.S_IFREG|0o644,1,1,1000000000,1];rows=[row]
def tiny(data):
 b=io.BytesIO()
 with tarfile.open(fileobj=b,mode='w:gz',compresslevel=1,format=tarfile.PAX_FORMAT)as t:t.addfile(env['info_for'](row),io.BytesIO(data))
 return b.getvalue()
good=tiny(payload);probes=[]
for label,raw,want in [('valid',good,0),('wrong_member_bytes',tiny(b'X'+payload[1:]),1),('truncated_gzip_footer',good[:-6],1)]:
 archive=OUT/(label+'.tar.gz');archive.write_bytes(raw);ns=dict(env);ns.update(archive=archive,rows=rows,summary={'tar_exact_bytes':len(gzip.decompress(good))})
 try:exec(readback,ns);actual=0;message='exact original readback and full gzip CRC passed'
 except Exception as e:actual=1;message=type(e).__name__+': '+str(e)
 probes.append({'case':label,'exit_code':actual,'expected':want,'output':message,'archive_bytes':len(raw),'archive_sha256':sha(raw)});check('actual_archive_readback_'+label,actual==want)
check('wrong_bytes_precise_failure','member full-byte SHA mismatch' in probes[1]['output'])
check('truncated_footer_rejected','EOFError' in probes[2]['output'])
default=subprocess.run([sys.executable,'-B',str(SRC)],capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
check('default_PLAN_ONLY_exit0',default.returncode==0 and default.stdout.startswith('PLAN_ONLY:') and default.stderr=='')
save('PROOFS.json',{'capacity':cap,'symlink_guard_withdraw_restore':counter,'exact_archive_readback':probes,'default':{'argv':[sys.executable,'-B',str(SRC)],'exit_code':default.returncode,'stdout':default.stdout,'stderr':default.stderr}})
review={'schema':'closed-originals-collector-independent-static-peer/1','exit_code':0,'collector_sha256':PIN,'collector_path':str(SRC),'plan_sha256':PLAN_PIN,'plan_path':str(PLAN),'blocking_findings':[],'checks':checks,'check_count':len(checks),'formal_execution':False,'SHM_access':False,'Git_or_network':False,'product_tests_rerun':False,'cleanup_permitted':False,'approval_scope':'Only the pinned fixed-17-roots PLAN.all collection, with exact peer/request/plan binding and fresh unchanged original capacity guards; root owns formal execution.','conditions':['Root must bind PLAN.all and preserve no-writers lease through collection.','Actual package needs independent member/hash/CRC review and durable publication before delivery.','Historical capacity sample is not a current admission.','Archive includes synthetic proof Git fixtures as evidence, never active publisher/product checkout.','No product, native, browser or full123 success is established by this static review.'],'proofs_sha256':sha((OUT/'PROOFS.json').read_bytes()),'total_generated_bytes_before_review':sum(p.stat().st_size for p in OUT.iterdir()if p.is_file())}
save('REVIEW.json',review)
(OUT/'SUMS.sha256').write_text(''.join(sha(p.read_bytes())+'  '+p.name+'\n' for p in sorted(OUT.iterdir())if p.is_file()and p.name!='SUMS.sha256'))
print(json.dumps({'exit_code':0,'checks':len(checks),'review_sha256':sha((OUT/'REVIEW.json').read_bytes()),'generated_bytes':sum(p.stat().st_size for p in OUT.iterdir()if p.is_file())}))
