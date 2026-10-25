"""F9 native terminal-only binding and operational budget, not a replacement judge."""
from pathlib import Path
import argparse,fcntl,hashlib,json,os,stat,sys
F9='4f8a794f4167c3562eb182045102e86e9e37cca9'
JOB=Path('/tmp/geo337-F9-native-4f8a794f-20261025')
OUTER=Path('/tmp/geo337-F9-native-launch-20261025')
DEST=Path('/tmp/geo337-F9-native-terminal-package-20261025')
LOCKS=[]
def need(v,m):
 if not v:raise RuntimeError(m)
def H(b):return hashlib.sha256(b).hexdigest()
def h(p):
 v=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):v.update(b)
 return v.hexdigest()
def load(p):return json.loads(Path(p).read_bytes())
def own(p):
 p=Path(p);need(p.is_absolute() and '..' not in p.parts and any(p.is_relative_to(r) for r in [Path('/tmp'),Path('/workspace')]),'OWN_ABSOLUTE_INPUT')
 need(all(not q.is_symlink() for q in (p,*p.parents)) and p.is_file(),'REGULAR_NO_ALIAS_INPUT')
 return p
def begin():
 ap=argparse.ArgumentParser();ap.add_argument('--request',type=Path,required=True);ap.add_argument('--request-sha256',required=True);a=ap.parse_args()
 need(not sys.flags.optimize and 'PYTHONOPTIMIZE' not in os.environ,'ASSERTIONS_REQUIRED')
 need(h(own(a.request))==a.request_sha256,'EXACT_BOUND_REQUEST');q=load(a.request)
 need(q['schema']=='geo337-F9-native-terminal-collection/1' and q['source_sha']==F9 and q['root_source_cache_collection_lease'] is True,'EXACT_ROOT_COLLECTION_LEASE')
 need(q['job']==str(JOB) and q['outer']==str(OUTER) and q['destination']==str(DEST),'EXACT_F9_PATHS')
 need(not DEST.exists() and all(not p.is_symlink() for p in (DEST,*DEST.parents)),'FRESH_NO_ALIAS_DESTINATION')
 expected={'outer':OUTER/'RESULT.json','native':JOB/'RECEIPT.json','workflow':JOB/'workflow/native/receipt.json'}
 values={};bindings={}
 for role,p in expected.items():
  spec=q['terminal_files'][role];need(spec['path']==str(p),'EXACT_TERMINAL_PATH:'+role);need(h(own(p))==spec['sha256'],'TERMINAL_PIN:'+role);values[role]=load(p);bindings[role]=dict(path=str(p),sha256=spec['sha256'])
 spec=q['terminal_files']['exec_final'];p=own(spec['path']);need(h(p)==spec['sha256'],'ORIGINAL_EXEC_FINAL_PIN');final=load(p)
 need(type(final.get('exit_code')) is int and 'session_id' not in final,'ORIGINAL_EXEC_NOT_TERMINAL');values['exec_final']=final;bindings['exec_final']=dict(path=str(p),sha256=spec['sha256'])
 outer,r,w=values['outer'],values['native'],values['workflow']
 need(outer['source_sha']==r['source_sha']==w['sha']==F9 and w['job']=='native','EXACT_TERMINAL_SOURCE')
 need(type(outer.get('actual_exit')) is int and type(r.get('actual_exit')) is int and type(w.get('exit_code')) is int and bool(w.get('ended')),'ALL_ORIGINAL_TERMINAL_EXITS_REQUIRED')
 need(w['ci_timeout_minutes']==35 and w['watchdog_factor']==3 and type(w.get('over_ci_timeout')) is bool,'ORIGINAL_CI_GATE_METADATA')
 # A terminal red or inconsistent metadata remains collectable and visibly red.
 issues=[]
 try:
  output=json.loads(final['output'].strip())
  if output.get('source_sha')!=F9 or type(output.get('actual_exit')) is not int or output['actual_exit']!=final['exit_code']:issues.append('Original exec FINAL output source/exit differs')
 except (ValueError,TypeError,KeyError,AttributeError):issues.append('Original exec FINAL output is not a parseable source/exit object')
 if not final['exit_code']==outer['actual_exit']==r['actual_exit']:issues.append('Original exec/outer/native exits disagree')
 if r.get('original_workflow_exit')!=w['exit_code']:issues.append('Original native/workflow exits disagree')
 if r.get('ci_35_minute_gate_exit')!=(1 if w['over_ci_timeout'] else 0):issues.append('Original CI gate metadata disagrees')
 if r.get('workflow_receipt_sha256')!=bindings['workflow']['sha256']:issues.append('Original workflow receipt hash binding differs')
 original_command=outer.get('command',{})
 if original_command.get('actual_process_returncode')!=outer['actual_exit']:issues.append('Outer original command exit differs')
 need(q['minimum_archive_reserve_bytes']>=64*1024*1024,'ORIGINAL_64_MIB_COLLECTION_RESERVE')
 # Original root lease remains required; locks cannot establish universal process visibility.
 for name in ['/tmp/g261r3/heavy.lock','/tmp/g261r3/secondary.lock','/tmp/geometry-tests/build.lock','/tmp/geometry-tests/run_all.lock']:
  p=Path(name);st=p.lstat();need(stat.S_ISREG(st.st_mode) and not p.is_symlink() and st.st_nlink==1,'EXISTING_REGULAR_LOCK')
  f=p.open('r+b');LOCKS.append(f);need((os.fstat(f.fileno()).st_dev,os.fstat(f.fileno()).st_ino)==(st.st_dev,st.st_ino),'LOCK_IDENTITY');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for b in bindings.values():need(h(b['path'])==b['sha256'],'TERMINAL_CHANGED_BEFORE_COLLECTION')
 return dict(request=dict(path=str(a.request),sha256=a.request_sha256),bindings=bindings,outer=outer,native=r,workflow=w,exec_final=final,issues=issues,reserve=q['minimum_archive_reserve_bytes'],original_reported_pass=r.get('passed') is True,formal_candidate=not issues and r.get('passed') is True and final['exit_code']==outer['actual_exit']==r['actual_exit']==w['exit_code']==0 and not w['over_ci_timeout'],limits='Original full230/strict-registry/Windows-GDI-only allowed skip require independent actual review. Collection success is not formal acceptance. No new process-global visibility claim.')
def stable(term):
 for b in term['bindings'].values():need(h(b['path'])==b['sha256'],'ORIGINAL_TERMINAL_CHANGED_DURING_COLLECTION')
def budget(term,inv):
 logical=sum(r['bytes'] for r in inv.values())
 inventory_bytes=len((json.dumps(inv,ensure_ascii=False,indent=2)+'\n').encode())
 # Conservative tar/PAX/gzip framing plus exact inventory and small budget/package records.
 tar_metadata_upper=4096*(len(inv)+4)+10240
 json_metadata_upper=inventory_bytes*2+65536
 uncompressed_upper=logical+tar_metadata_upper+json_metadata_upper
 # zlib default-deflate compressBound terms, rounded upward, plus conservative gzip header/name/trailer allowance.
 deflate_gzip_upper=((uncompressed_upper+4095)//4096)+((uncompressed_upper+16383)//16384)+((uncompressed_upper+33554431)//33554432)+1024
 required=uncompressed_upper+deflate_gzip_upper+term['reserve']
 sv=os.statvfs(DEST.parent);free=sv.f_bavail*sv.f_frsize
 result=dict(selectedOriginalLogicalBytes=logical,exactInventoryBytes=inventory_bytes,tarAndFramingUpperBytes=tar_metadata_upper,jsonMetadataUpperBytes=json_metadata_upper,uncompressedTarAndMetadataUpperBytes=uncompressed_upper,deflateGzipExpansionUpperBytes=deflate_gzip_upper,minimumReserveBytes=term['reserve'],requiredBeforeArchiveBytes=required,freeBeforeArchiveBytes=free,admitted=free>=required,noCompressedSizeGuess=True,productThresholdChanged=False)
 need(result['admitted'],'INSUFFICIENT_UNCOMPRESSED_ARCHIVE_PLUS_METADATA_AND_64MIB_RESERVE:'+json.dumps(result))
 return result
