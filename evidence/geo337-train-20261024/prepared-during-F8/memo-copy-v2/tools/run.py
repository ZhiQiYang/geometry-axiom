"""Same-F two-C memo withdrawal: actual profile criterion 0/1/0 and exact isolated175 ABC."""
import argparse,datetime,difflib,fcntl,hashlib,importlib.util,json,os,resource,runpy,shutil,sys,traceback
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--repo',required=True,type=Path);p.add_argument('--sha',required=True);p.add_argument('--formal-out',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--heavy-lock',required=True,type=Path);p.add_argument('--phase',choices=['all','withdrawn','restored','abc'],default='all');a=p.parse_args();a.repo=a.repo.resolve();a.out=a.out.resolve();a.formal_out=a.formal_out.resolve()
for protected in [a.repo,a.formal_out]:
 if a.out==protected or a.out.is_relative_to(protected) or protected.is_relative_to(a.out):p.error('--out must not overlap repository or formal output')
 if a.heavy_lock.resolve()==protected or a.heavy_lock.resolve().is_relative_to(protected):p.error('--heavy-lock must remain outside repository and formal output')
V3=Path('/tmp/geo323-merge-20261023/acceptance-tools-v3');V4=Path('/tmp/geo323-train337-lineage-20261024/acceptance-tools-v4-scene-binding');CAP=Path('/workspace/geo288-main-merge-20261023/native-final-tools/capture.py');BASE='b74f9a2ae7ade1555b9be45283adecc097fb76e3';MAIN='adbaebf9c73ea6801d7b4d5214e4b846b132923b';H='3cbeb75926bb188e6c8f153d182303feadfa27dc'
PINS={CAP:'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762',V3/'geo323_record.py':'8aa05afded8738078cb319606422270345abc0317257d63e8879009acaaabb9b',V3/'profile_linux.py':'0dda20c3d4de8c4472ed7f936fcf7bbc48c4adacfdc779bc2bda6e300a0c853c',V3/'verify_linux.py':'ccbce3a5d32bee81f22be31a31c1f771ca05c54f53f21e4d94b11b4a08b4534d',V4/'run.py':'d4a38b7b60ac698eba4a274c5d26c83684cd1c665b8399f5e47546befae1f70e',V4/'verify_linux.py':'c3db1834c49365a08ef5720d38156253a355e9f5d5db0239486013871d0e2cac'}
PRODUCT={'geometry-core/references.inc': ('2f915779b14272a3cd9d2014d02d9476b05841145885e3d4b0717657e0a0378c', '093d5d7f06963a0f555c6614595791c99e250c019865006edadeacf956838a80'), 'geometry-app/native/reference_sources.inc': ('77c03a865a39f6ab0e0eff7005d04ccf91d36db92c9f218ed69630f28be9bd56', 'a6dece841da1a19d5df5c032a17d713363136c49aee09f7f641d374c26b85512')}
def sha(b):return hashlib.sha256(b).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
HERE=Path(__file__).resolve().parent
PINS.update({HERE/'memo_variant.py':'80f1c1c583d2b812f829035099e3612c5fd436915892437f27179f2072eb097e',HERE/'COUNTERFACTUAL.json':'4fb12fc272fb55e92f441f24f34f6657c64020b5c90c2c3c1f0fd117eff61a04'})
PINS.update({HERE/'copy_r8_elf.py':'07bc1f02c9d813fa20f7289e4fde687362ef5db5e9831b831dc9307a5a5a47e5',HERE/'R8_ELF_COPY_BINDINGS.json':'fa0d0cdc150addfa6107e203b00f54399145e2315516069dc339918c2e93f13b'})
for file,want in PINS.items():assert sha(file.read_bytes())==want,('tool pin',str(file))
if sys.flags.optimize:raise RuntimeError('Original assertions require optimize0')
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
memo_variant=load('memo_only_counterfactual',HERE/'memo_variant.py')
elf_copy=load('private_R8_ELF_copy',HERE/'copy_r8_elf.py')
assert a.sha==memo_variant.F8,'This counterfactual is fixed to actual F8, never ledger-adoption F9'
cap=load('original_capture',CAP);sys.path.insert(0,str(V3));import geo323_record as original_record
v3=load('original_verify',V3/'verify_linux.py');v4=load('bound_verify',V4/'verify_linux.py');bound=load('bound_session',V4/'run.py')
env=dict(os.environ);env['PATH']='/workspace/geo261-environment/bin:'+env['PATH']
for n in list(env):
 if n.startswith('GEOMETRY_') or n in ['NODE_OPTIONS','PYTHONOPTIMIZE','PYTHONPATH','PYTHONSTARTUP','LD_PRELOAD']:env.pop(n,None)
env.update(LANG='C.UTF-8',LC_ALL='C.UTF-8',PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',GITHUB_SHA=a.sha,GITHUB_WORKSPACE=str(a.repo),GEO323_BASE_SHA=BASE,GEO323_MAIN_SHA=MAIN)
def dump(path,value):cap.dump(path,value)
def guard(rec):
 head=rec.run(['git','rev-parse','HEAD'],cwd=a.repo)[1].decode().strip();status=rec.run(['git','status','--porcelain=v1','--untracked-files=all'],cwd=a.repo)[1].decode();assert head==a.sha and status=='';return {'head':head,'status':status}
def inv(root):return {p.relative_to(root).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(root.rglob('*')) if p.is_file()}
class VariantRecorder(original_record.Recorder):
 def role(self,command,cwd):
  role=super().role(command,cwd);is_base=role['label']=='base'
  if a.phase=='abc':role.update(sha=a.sha,variant='withdrawn-two-C' if is_base else 'fixed-F',scope='isolated323 ABC; never formal performance base')
  else:role.update(sha=BASE if is_base else a.sha,variant='canonical-b74' if is_base else a.phase+'-two-C',scope='controlled profile; formal denominator unchanged')
  return role
assert sha((a.formal_out/'receipt.json').read_bytes())=='979680e78a381d28a6d1c6825b7b1b8af850bebec381ec3cee3ef42e9e46ea15','exact original R8 formal receipt required; no rewritten ABC/source'
formal=json.loads((a.formal_out/'receipt.json').read_text());assert formal['source_sha']==a.sha and formal['base']==BASE and formal['main']==MAIN and formal['stages']['profile']['execution_exit']==0
assert formal['stages']['profile']['source_before']==formal['stages']['profile']['source_after']=={'head':a.sha,'status':''}
if a.phase=='all':
 assert not a.out.exists();a.out.mkdir();rec=cap.Recorder(a.out,env,a.sha);r={'sha':a.sha,'started_utc':now(),'ended_utc':None,'commands':rec.rows,'source_before':None,'source_after':None,'phases':[],'errors':[],'fixed_formal_criterion':formal['quantitative_targets']['geo_eval_source_64_32'],'formal_receipt_sha256':sha((a.formal_out/'receipt.json').read_bytes()),'scope':'Whole-memo profile withdrawal/restoration and isolated175 ABC; original cross-feature3diag red retained; formal36/4 not resampled','driver_sha256':sha(Path(__file__).read_bytes()),'tool_hashes':{str(k):v for k,v in PINS.items()}}
 try:
  r['source_before']=guard(rec)
  for phase in ['withdrawn','restored','abc']:
   command=[sys.executable,'-B',str(Path(__file__).resolve()),'--repo',str(a.repo),'--sha',a.sha,'--formal-out',str(a.formal_out),'--out',str(a.out/phase),'--heavy-lock',str(a.heavy_lock),'--phase',phase]
   row={'phase':phase,'actual_exit':None};r['phases'].append(row);dump(a.out/'receipt.json',r)
   raw=rec.run(command,cwd=a.repo,check=False,timeout=None,source_variant=phase)[0];row.update(actual_exit=raw['actual_process_returncode'],receipt=str(a.out/phase/'receipt.json'))
   if (a.out/phase/'receipt.json').exists():row['result']=json.loads((a.out/phase/'receipt.json').read_text())
   dump(a.out/'receipt.json',r)
 except BaseException:r['errors'].append(traceback.format_exc())
 finally:
  try:r['source_after']=guard(rec)
  except BaseException:r['errors'].append(traceback.format_exc())
  expected={'withdrawn':1,'restored':0,'abc':0};r['passed']=not r['errors'] and r['fixed_formal_criterion']['target_met'] is True and len(r['phases'])==3 and all(x['actual_exit']==expected[x['phase']] and x.get('result',{}).get('execution_complete') is True for x in r['phases']);r['ended_utc']=now();r['exit']=0 if r['passed'] else 1;dump(a.out/'receipt.json',r)
 print(json.dumps({'passed':r['passed'],'phases':[(x['phase'],x['actual_exit']) for x in r['phases']],'errors':r['errors']},ensure_ascii=False));raise SystemExit(r['exit'])
assert not a.out.exists();a.out.mkdir();(a.out/'tmp').mkdir();(a.out/'evidence').mkdir();env['TMPDIR']=str(a.out/'tmp');env['GEO323_BASE_SHA']=a.sha if a.phase=='abc' else BASE;os.environ.clear();os.environ.update(env)
rec=cap.Recorder(a.out,env,a.sha);r={'sha':a.sha,'phase':a.phase,'started_utc':now(),'ended_utc':None,'commands':rec.rows,'errors':[],'source_before':None,'source_after':None,'execution_complete':False,'criterion_exit':None,'driver_sha256':sha(Path(__file__).read_bytes()),'tool_hashes':{str(k):v for k,v in PINS.items()},'canonical_base_performance':BASE,'main_performance':MAIN}
soft,hard=resource.getrlimit(resource.RLIMIT_STACK)
try:
 assert hard==resource.RLIM_INFINITY or hard>=16777216;resource.setrlimit(resource.RLIMIT_STACK,(16777216,hard));r['stack_during']=list(resource.getrlimit(resource.RLIMIT_STACK));r['source_before']=guard(rec)
 a.heavy_lock.parent.mkdir(parents=True,exist_ok=True)
 with a.heavy_lock.open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  original=VariantRecorder(a.out/'original-commands',a.repo,a.sha,env);original_record.ACTIVE=original;r['original_commands']=original.rows
  evidence=a.out/'evidence';work=a.out/'work';work.mkdir();(evidence/'scenes').mkdir();(evidence/'checks').mkdir()
  for name in ['s16.scene','s32.scene','s48.scene','s64.scene']:(evidence/'scenes'/name).write_bytes((a.formal_out/'evidence/scenes'/name).read_bytes())
  (evidence/'scene-inventory.json').write_bytes((a.formal_out/'evidence/scene-inventory.json').read_bytes())
  if a.phase in ['withdrawn','restored']:
   source=a.out/'source';v3.closure(a.repo,source,'geometry-web/web_bridge.c');r['source_before_variant']=inv(source);product_before={path:(source/path).read_text() for path in PRODUCT}
   for path,(fixed,withdrawn) in PRODUCT.items():
    assert sha((source/path).read_bytes())==fixed
    if a.phase=='withdrawn':
     raw=memo_variant.withdraw_memo(path,(source/path).read_bytes());assert sha(raw)==withdrawn;(source/path).write_bytes(raw)
   r['source_after_variant']=inv(source);changed=[p for p in r['source_before_variant'] if r['source_before_variant'][p]!=r['source_after_variant'][p]];assert set(changed)==(set(PRODUCT) if a.phase=='withdrawn' else set());r['changed_source_paths']=changed
   patch=''.join(''.join(difflib.unified_diff(product_before[path].splitlines(keepends=True),(source/path).read_text().splitlines(keepends=True),fromfile='F/'+path,tofile=a.phase+'/'+path)) for path in PRODUCT);(a.out/'product-variant.patch').write_text(patch);r['product_variant_patch_sha256']=sha(patch.encode())
   src=a.formal_out/'work/base-pg/bridge';dst=work/'base-pg/bridge';dst.parent.mkdir();copy_binding=elf_copy.copy_r8_binary('base-pg',src,dst);r['base_binary_binding']={'path':str(src),'sha256':copy_binding['sha256'],'source_sha':BASE,'private_copy':copy_binding}
   v3.build(source,work/'fix-pg',profile=True);r['fix_binary_binding']={'path':str(work/'fix-pg/bridge'),'sha256':sha((work/'fix-pg/bridge').read_bytes()),'source_sha':a.sha,'variant':a.phase};os.environ.update(GEO323_ROOT=str(source),GEO323_WORK=str(work),GEO323_EVIDENCE=str(evidence));original.env.update(GEO323_ROOT=str(source),GEO323_WORK=str(work),GEO323_EVIDENCE=str(evidence));runpy.run_path(str(V3/'profile_linux.py'),run_name='__main__')
   counts={}
   for version in ['base','fix']:
    for n in [32,64]:
     raw=(evidence/f'gprof-{version}-{n}.stdout').read_bytes();matches=[line for line in raw.decode().split('Call graph')[0].splitlines() if len(line.split())==7 and line.split()[-1]=='geo_eval_source'];assert len(matches)==1;counts[f'{version}-{n}']={'calls':int(matches[0].split()[3]),'original_line':matches[0],'gprof_sha256':sha(raw)}
   lower=counts['fix-32']['calls'];upper=counts['fix-64']['calls'];assert lower>0;ratio=upper/lower;assert inv(source)==r['source_after_variant'];r.update(profile_counts=counts,actual=ratio,target='<=4.5',target_met=ratio<=4.5,criterion_exit=0 if ratio<=4.5 else 1,execution_complete=True)
  else:
   withdrawn=a.out.parent/'withdrawn/source';restored=a.out.parent/'restored/source';w=json.loads((a.out.parent/'withdrawn/receipt.json').read_text());s=json.loads((a.out.parent/'restored/receipt.json').read_text());assert inv(withdrawn)==w['source_after_variant'] and inv(restored)==s['source_after_variant'];r['variant_sources']={'withdrawn':w['source_after_variant'],'fixed':s['source_after_variant']}
   for label in ['fix','fix-trace']:
    src=a.formal_out/'work'/label/'bridge';dst=work/label/'bridge';dst.parent.mkdir();assert sha(src.read_bytes())==next(x['binary_sha256'] for x in formal['builds'] if x['label']==label);copy_binding=elf_copy.copy_r8_binary(label,src,dst);r.setdefault('fixed_binary_bindings',[]).append({'label':label,'source':str(src),'sha256':copy_binding['sha256'],'private_copy':copy_binding})
   v4.build(withdrawn,work/'base');v4.build(withdrawn,work/'base-trace',trace=True)
   session=object.__new__(bound.Session);session.a=argparse.Namespace(repo=a.repo);session.work=work;session.evidence=evidence;session.v=v4;session.record={'builds':[{'label':x,'execution_exit':0} for x in ['base','fix','base-trace','fix-trace']]}
   try:bound.Session.compare(session)
   finally:
    r['variant_sources_after_ABC']={'withdrawn':inv(withdrawn),'fixed':inv(restored)};assert r['variant_sources_after_ABC']==r['variant_sources']
   r.update(ABC_result=session.record['ABC_result'],criterion_exit=0,execution_complete=True)
  r['original_commands']=original.rows
except BaseException:r['errors'].append(traceback.format_exc())
finally:
 try:r['source_after']=guard(rec)
 except BaseException:r['errors'].append(traceback.format_exc())
 resource.setrlimit(resource.RLIMIT_STACK,(soft,hard));r['ended_utc']=now();r['exit']=r['criterion_exit'] if r['execution_complete'] and not r['errors'] else 2;dump(a.out/'receipt.json',r)
print(json.dumps({k:r.get(k) for k in ['phase','actual','target_met','ABC_result','execution_complete','exit','errors']},ensure_ascii=False));raise SystemExit(r['exit'])
