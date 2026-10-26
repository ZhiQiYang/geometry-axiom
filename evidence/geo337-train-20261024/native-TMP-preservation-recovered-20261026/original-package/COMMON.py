"""Shared exact-scope guards; no top-level source writes or executions."""
from pathlib import Path
import contextlib, datetime, fcntl, hashlib, importlib.util, json, os, stat

BASE=Path(__file__).parent
PLAN=BASE/'PLAN.v2.json'
PLAN_PIN='38e28b2e0b63ad263d2eb22beb6f80e90190073d68a40ad9cc9b81f6e1ac83be'
OWN=Path('/dev/shm/geometry-axiom-geo337-20261025')
OTHER_OWN=Path('/dev/shm/geo337-F9-browsers-20261025')
ORIGINAL=Path('/workspace/geo337-four-retired-WS-index-preservation-20261025/archive_indexes.py')
ORIGINAL_PIN='b7e3f6c5c1f5ad18c1ea9db697c035d01a439991819ad160ae502374c15663ab'
LOCKS=(Path('/tmp/g261r3/heavy.lock'),Path('/tmp/g261r3/secondary.lock'))

def need(ok,message):
    if not ok:raise RuntimeError(message)
def H(raw):return hashlib.sha256(raw).hexdigest()
def load(path,pin,name):
    need(H(path.read_bytes())==pin,'helper pin: '+str(path))
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
original=load(ORIGINAL,ORIGINAL_PIN,'original_four_index_archive_helpers')
dump=original.dump
syncdir=original.syncdir
metadata=original.metadata
original_bytes=original.original_bytes

def save_mutable(path,value):
    # A new task-owned receipt may update atomically; never an original artifact.
    temp=path.with_name(path.name+'.new')
    need(not temp.exists(),'unexpected pending receipt')
    dump(temp,value);os.replace(temp,path);syncdir(path.parent)

def read_plan():
    raw=PLAN.read_bytes();need(H(raw)==PLAN_PIN,'exact accepted combined plan pin')
    plan=json.loads(raw)
    for path,pin in plan['bindings'].items():
        p=Path(path);need(p.stat().st_size==pin['bytes'] and H(p.read_bytes())==pin['sha256'],'plan prerequisite pin: '+path)
    source=[json.loads(line) for line in (BASE/'source-readonly-validation/VALIDATED.jsonl').read_text().splitlines()]
    aux=BASE/'auxiliary-readonly-validation'
    indexes=json.loads((aux/'EXACT_INDEX_LEAVES.json').read_bytes())
    elfs=json.loads((aux/'EXACT_ELF_LEAVES.json').read_bytes())
    chrome=json.loads((aux/'EXACT_CHROME_CACHE_LEAVES.json').read_bytes())
    need(len(source)==2439 and len(indexes)==2 and len(elfs)==24 and len(chrome)==45,'exact current counts')
    need(sum(len(c['files']) for c in chrome)==691,'exact cache file count')
    leaves=source+[dict(path=x['effective_index'],original_state=x['original_state']) for x in indexes]+elfs+[dict(path=str(Path(c['path'])/f['relative']),original_state=f['original_state']) for c in chrome for f in c['files']]
    need(len({x['path'] for x in leaves})==len(leaves),'all original leaves distinct')
    need(sum(x['original_state']['allocated'] for x in leaves)==107233280,'exact byte scope')
    return plan,source,indexes,elfs,chrome

def exact_file(path,state,guard):
    guard.ancestors(path)
    s=path.lstat()
    need(stat.S_ISREG(s.st_mode) and s.st_nlink==1,'regular independent leaf: '+str(path))
    got=dict(device=s.st_dev,inode=s.st_ino,mode=s.st_mode,uid=s.st_uid,gid=s.st_gid,nlink=s.st_nlink,bytes=s.st_size,allocated=s.st_blocks*512,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns)
    need(all(got[k]==state[k] for k in got),'exact original leaf state: '+str(path))
    body=original_bytes(path)
    need(len(body)==state['bytes'] and H(body)==state['sha256'],'exact original leaf bytes: '+str(path))
    need({n:os.getxattr(path,n,follow_symlinks=False).hex() for n in os.listxattr(path,follow_symlinks=False)}==state['xattrs'],'xattrs changed: '+str(path))
    after=path.lstat()
    need((after.st_dev,after.st_ino,after.st_mode,after.st_size,after.st_mtime_ns,after.st_ctime_ns,after.st_nlink)==(s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_nlink),'leaf changed during read')
    return body

def group_paths(source,indexes,elfs,chrome):
    scope=json.loads((BASE/'SOURCE_SCOPE.v2.json').read_bytes())
    return sorted({r['root'] for r in indexes}|{str(Path(r['path']).parent) for r in elfs}|{c['profile'] for c in chrome}|{r['root'] for r in scope['retained_rows']})

@contextlib.contextmanager
def leases():
    handles=[]
    try:
        for path in LOCKS:
            s=path.lstat();need(stat.S_ISREG(s.st_mode) and not path.is_symlink(),'existing ordinary scheduler lock')
            handle=path.open('r+b');handles.append(handle)
            need((os.fstat(handle.fileno()).st_dev,os.fstat(handle.fileno()).st_ino)==(s.st_dev,s.st_ino),'lock identity drift')
            fcntl.flock(handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield
    finally:
        for handle in reversed(handles):handle.close()

def consumers(out,label,guard,paths):
    guard.OUT=out/('consumers-'+label);guard.OUT.mkdir();guard.consumer_check(paths)

def original_D():
    old=json.loads(Path('/workspace/ordinary-code-retirement-20261023/RESULT.json').read_bytes())
    recent=json.loads(Path('/workspace/geo337-retired-three-source-retirement-execution-20261025/RESULT.json').read_bytes())
    need(old['exit_code']==recent['exit_code']==0,'original successful retirement receipts')
    paths={r['path'] for r in old['removed']}|set(recent['removed_paths'])
    paths|={json.loads(line)['path'] for line in Path('/workspace/tmp-coldcode-cleanup-20261024/execution-r2/UNLINKED.jsonl').read_text().splitlines()}
    return paths

def git(rec,root,args,sha,stdin=None):
    row,so,se=rec.run(['git','--no-optional-locks','-c','gc.auto=0','-c','maintenance.auto=false',*args],cwd=Path(root),timeout=None,check=False,source_sha=sha,source_variant='Exact inactive cache preservation; not a formal product test',**({'data':stdin} if stdin is not None else {}))
    need(row['actual_process_returncode']==0 and not row['timeout_expired'] and not se,'Git guard failed')
    return so

def source_state(rec,removed=()):
    scope=json.loads((BASE/'SOURCE_SCOPE.v2.json').read_bytes());roots={r['root']:r['head'] for r in scope['retained_rows']};old=original_D()|set(removed);result={}
    for root,head in roots.items():
        need(git(rec,root,['rev-parse','HEAD'],head).decode().strip()==head,'HEAD changed')
        members=[r for r in scope['retained_rows'] if r['root']==root]
        object_input=''.join(r['Git_blob']+'\n' for r in members).encode()
        objects=git(rec,root,['cat-file','--batch-check=%(objectname) %(objecttype) %(objectsize)'],head,object_input)
        need(objects.decode().splitlines()==[f"{r['Git_blob']} blob {r['Git_bytes']}" for r in members],'retained original Git objects unavailable')
        need(not git(rec,root,['diff','--cached','--no-ext-diff','--name-status','-z'],head),'staged changes')
        status=git(rec,root,['status','--porcelain=v1','-z','--untracked-files=all'],head)
        records=[r for r in status.split(b'\0') if r]
        wanted={p[len(root)+1:] for p in old if p.startswith(root+'/')}
        need(len(records)==len(wanted) and {r[3:].decode() for r in records if r.startswith(b' D ')}==wanted,'unknown dirty state: '+root)
        refs=git(rec,root,['for-each-ref','--format=%(refname) %(objectname)'],head)
        result[root]=dict(head=head,status_sha256=H(status),refs_sha256=H(refs))
    return result

def private_index_state(rec,index):
    root=index['root'];head=index['head'];path=Path(index['effective_index']);gd=Path(index['effective_gitdir'])
    need(git(rec,root,['rev-parse','--absolute-git-dir'],head).decode().strip()==str(gd),'effective Git directory')
    common=git(rec,root,['rev-parse','--git-common-dir'],head).decode().strip();common=Path(common) if Path(common).is_absolute() else Path(root)/common
    actual=git(rec,root,['rev-parse','--git-path','index'],head).decode().strip();actual=Path(actual) if Path(actual).is_absolute() else Path(root)/actual
    need(gd==Path(root)/'.git' and gd.resolve()==gd and common.resolve()==gd and actual.resolve()==path and path==gd/'index','private effective index/common')
    need(gd.is_dir() and not gd.is_symlink() and not list(gd.glob('*.lock')) and not list((gd/'refs').rglob('*.lock')),'active Git lock')
    need(not git(rec,root,['diff','--cached','--no-ext-diff','--name-status','-z'],head),'staged index changes')

def chrome_namespace(chrome):
    for c in chrome:
        root=Path(c['path']);wanted={f['relative'] for f in c['files']}|{d['relative'] for d in c['directories']}
        need(root.is_dir() and not root.is_symlink() and {str(p.relative_to(root)) for p in root.rglob('*')}==wanted,'Chrome exact namespace changed')
        for d in c['directories']:
            p=root/d['relative'];s=p.lstat()
            need(stat.S_ISDIR(s.st_mode) and not p.is_symlink() and (s.st_dev,s.st_ino,s.st_mode,s.st_mtime_ns,s.st_nlink)==(d['device'],d['inode'],d['mode'],d['mtime_ns'],d['nlink']),'Chrome directory drift')

def owned_allocated():
    seen=set();total=0
    for root in (OWN,OTHER_OWN):
        if not root.exists():continue
        for base,dirs,files in os.walk(root,followlinks=False):
            for name in dirs+files:
                p=Path(base)/name;s=p.lstat();key=(s.st_dev,s.st_ino)
                if key not in seen:seen.add(key);total+=s.st_blocks*512
    return total

def bind_request(q,peerkey,executor):
    need(q['plan_sha256']==PLAN_PIN,'plan request pin')
    for key in ('root_exact_old_roots_no_reuse_lease','root_no_active_consumers_lease'):
        need(q[key] is True,'missing root lease: '+key)
    p=Path(q[peerkey]['path']);raw=p.read_bytes();need(H(raw)==q[peerkey]['sha256'],'independent executor peer pin')
    peer=json.loads(raw);need(peer['exit_code']==0 and not peer['blocking_findings'] and peer['executor_sha256']==H(executor.read_bytes()),'exact executor not accepted')
