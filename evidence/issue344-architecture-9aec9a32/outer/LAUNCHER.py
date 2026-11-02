from pathlib import Path
import datetime, hashlib, importlib.util, json, os, resource, sys
if sys.flags.optimize: raise RuntimeError('Python optimization forbidden')
ROOT=Path('/workspace/issue320-work-20261024')
F='9aec9a32630fc65f94c53d49e99969e546574d6e'
BRANCH='codex/issue320-connection-recovery-20261024'
OUT=Path('/tmp/geo344-architecture-outer-20261025')
RUN=Path('/tmp/geo344-architecture-exact-20261025')
DRIVER=Path('/workspace/geo344-architecture-adapter-preparation-20261025/refresh_architecture_cdp_exclusion.py')
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
def H(b):return hashlib.sha256(b).hexdigest()
assert H(DRIVER.read_bytes())=='71cb2e314a3d3e7c3419bbe436f2c308a702d6b3be5f9668594fe729248de2de'
assert H(CAP.read_bytes())=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
assert not OUT.exists() and not RUN.exists()
OUT.mkdir()
(OUT/'LAUNCHER.py').write_bytes(Path(__file__).read_bytes())
(OUT/'ADAPTER.py').write_bytes(DRIVER.read_bytes())
(OUT/'capture.py').write_bytes(CAP.read_bytes())
spec=importlib.util.spec_from_file_location('capture',CAP)
cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
env=dict(os.environ);cleared=[]
for k in list(env):
    if k.startswith(('GIT_','MUTATE_')) or k in ('PYTHONOPTIMIZE','PYTHONPATH','PYTHONSTARTUP','NODE_OPTIONS'):
        cleared.append(k);env.pop(k)
env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',LANG='C.UTF-8',LC_ALL='C.UTF-8',GITHUB_SHA=F,GITHUB_WORKSPACE=str(ROOT),TMPDIR='/tmp')
rec=cap.Recorder(OUT,env,F)
def git(*args,data=None):
    return rec.run(['git',*args],cwd=ROOT,data=data,timeout=1200,source_sha=F,
      source_variant='exact #344 owned clean source materialization only; architecture formal follows')[1]
def free(p):
    x=os.statvfs(p);return x.f_bavail*x.f_frsize
def gitpath(name):
    p=Path(git('rev-parse','--git-path',name).decode().strip())
    return p if p.is_absolute() else ROOT/p
assert git('rev-parse','HEAD').decode().strip()==F
assert git('branch','--show-current').decode().strip()==BRANCH
assert not git('status','--porcelain=v1','--untracked-files=all')
assert git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()==[F,'refs/heads/'+BRANCH]
ART='geometry-core/domain-decoupling/'
names=['product-architecture.json','product-architecture-scan.json','PRODUCT-ARCHITECTURE.md','product-architecture-receipt.json']
manifest=json.loads((ROOT/ART/names[0]).read_bytes())
sources=sorted(x['path'] for k in ['sources','exclusions'] for x in manifest[k])
needed=sorted(set(sources+[ART+n for n in names]+['tests/architecture_contract.py','tests/test_architecture_contract.py','tests/test_product_architecture.py','公理層.md','決策佇列.md']))
assert len(sources)==604 and len(needed)==613
assert not any(any(c in n for c in '*?[]\\') for n in needed)
raw=git('ls-tree','-r','-l','-z',F,'--',*needed);rows=[]
for entry in raw.split(b'\0'):
    if not entry:continue
    a,p=entry.split(b'\t',1);mode,kind,oid,size=a.split();name=p.decode()
    assert kind==b'blob' and mode!=b'120000'
    rows.append({'path':name,'bytes':int(size),'oid':oid.decode(),'missing':not (ROOT/name).exists()})
assert [x['path'] for x in rows]==needed
patterns=gitpath('info/sparse-checkout');index=gitpath('index')
before=patterns.read_bytes();(OUT/'sparse-before.bin').write_bytes(before)
missing_alloc=sum(((x['bytes']+4095)//4096)*4096 for x in rows if x['missing'])
snapshot_alloc=sum(((x['bytes']+4095)//4096)*4096 for x in rows if x['path'] in set(sources))
kset={x['path'] for x in manifest['sources'] if x['layer']=='K'}
kalloc=sum(((x['bytes']+4095)//4096)*4096 for x in rows if x['path'] in kset)
dirs={str(Path(n).parent) for n in needed}
artifact_bytes=sum(x['bytes'] for x in rows if x['path'].startswith(ART) and x['path'][len(ART):] in names)
tmp_estimate=snapshot_alloc+kalloc+len(dirs)*4096+artifact_bytes*8+len(raw)*4+16*1024*1024
budget={'source_sha':F,'source_files':604,'materialized_needed':613,'paths':rows,
    'missing_alloc4K':missing_alloc,'temporary_index_bytes':index.stat().st_size,
    'source_directory_allowance':len(dirs)*4096,'workspace_free':free('/workspace'),'tmp_free':free('/tmp'),
    'root_workspace_admission_bytes':60000000,'tmp_estimated_peak_with_reserve':tmp_estimate,
    'tmp_basis':{'full_product_snapshot_alloc4K':snapshot_alloc,'concurrent_K_snapshot_alloc4K':kalloc,
      'directories4K':len(dirs)*4096,'artifact_eightfold_allowance':artifact_bytes*8,'tree_fourfold_allowance':len(raw)*4,
      'generic_fixture_and_metadata_reserve':16*1024*1024},
    'scope':'resource admission only; no product threshold, assertion, golden or timeout changed',
    'environment_cleared':cleared,'python_optimization':sys.flags.optimize}
cap.dump(OUT/'RESOURCE_PLAN.json',budget)
assert budget['workspace_free']>=60000000
assert budget['workspace_free']>missing_alloc+index.stat().st_size+len(dirs)*4096+8*1024*1024
assert budget['tmp_free']>tmp_estimate
git('sparse-checkout','add','--stdin',data=('\n'.join('/'+n for n in needed)+'\n').encode())
after=patterns.read_bytes();(OUT/'sparse-after.bin').write_bytes(after)
assert set(after.splitlines())==set(before.splitlines())|{('/'+n).encode() for n in needed}
for row in rows:
    p=ROOT/row['path'];assert p.is_file() and not p.is_symlink()
    b=p.read_bytes();assert len(b)==row['bytes'] and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['oid']
assert not git('status','--porcelain=v1','--untracked-files=all')
assert git('rev-parse','HEAD').decode().strip()==F
cap.dump(OUT/'MATERIALIZED.json',{'source_sha':F,'files':613,'all_git_blob_equal':True,
    'source_clean':True,'free':{p:free(p) for p in ['/workspace','/tmp']}})
old_stack=resource.getrlimit(resource.RLIMIT_STACK)
resource.setrlimit(resource.RLIMIT_STACK,(16777216,old_stack[1]))
cap.dump(OUT/'STACK.json',{'before':old_stack,'after':resource.getrlimit(resource.RLIMIT_STACK),'same_as_ulimit_s_16384':True})
argv=['python3','-B',str(DRIVER),'--execute','--root-scheduled-architecture-run','--root',str(ROOT),'--sha',F,'--out',str(RUN)]
row,out,err=rec.run(argv,cwd=ROOT,timeout=None,check=False,source_sha=F,
    source_variant='formal exact architecture original three judges, single digest0/1/0, original nine W controls')
code=row['actual_process_returncode']
cap.dump(OUT/'RESULT.json',{'exit_code':code,'source_sha':F,'actual_command':row,
  'adapter_result':str(RUN/'RESULT.json'),'adapter_result_exists':(RUN/'RESULT.json').exists(),
  'free':{p:free(p) for p in ['/workspace','/tmp']},'native_browser_strict9_executed':False})
print(json.dumps({'exit_code':code,'source_sha':F,'result':str(OUT/'RESULT.json')}))
raise SystemExit(code if isinstance(code,int) and code>=0 else 1)
