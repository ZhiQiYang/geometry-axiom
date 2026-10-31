"""Prepare a new independent thin checkout. No acceptance stage or C execution."""
from pathlib import Path,PurePosixPath
import argparse,datetime,hashlib,json,os,posixpath,re,subprocess,sys
HERE=Path(__file__).resolve().parent
TEMPLATE=HERE/'REQUEST.template.json'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def need(v,m):
    if not v:raise RuntimeError(m)
def clean_env():
    env=os.environ.copy()
    for key in list(env):
        if key.startswith(('GIT_','GEOMETRY_','MUTATE_')) or key in ('PYTHONPATH','PYTHONHOME','PYTHONOPTIMIZE','PYTHONSTARTUP','LD_PRELOAD','LD_LIBRARY_PATH','CC','CFLAGS','CPPFLAGS','LDFLAGS','CPATH','C_INCLUDE_PATH','COMPILER_PATH','LIBRARY_PATH','GCC_EXEC_PREFIX'):
            del env[key]
    env.update(LANG='C.UTF-8',LC_ALL='C.UTF-8',PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
    return env
def pins_ok(request):
    root=Path(request['original_tools'])
    actual={p.relative_to(root).as_posix()for p in root.rglob('*')if p.is_file()and'__pycache__'not in p.parts}
    need(actual==set(request['tool_files']),'accepted v5 toolkit file inventory changed')
    for path,pin in request['tool_files'].items():
        raw=(root/path).read_bytes();need(len(raw)==pin['bytes']and sha(raw)==pin['sha256'],'accepted v5 toolkit changed: '+path)
class Recorder:
    def __init__(self,out,source,env):
        self.out=out;self.source=source;self.env=env;self.rows=[]
    def run(self,argv,cwd,data=None):
        where=self.out/'commands'/f'{len(self.rows)+1:03d}';where.mkdir(parents=True)
        if data is not None:(where/'stdin').write_bytes(data)
        started=datetime.datetime.now(datetime.timezone.utc).isoformat()
        result=subprocess.run(argv,cwd=cwd,env=self.env,input=data,capture_output=True)
        (where/'stdout').write_bytes(result.stdout);(where/'stderr').write_bytes(result.stderr)
        row={'command':argv,'cwd':str(cwd),'source_sha':self.source,'started_utc':started,'environment':{key:self.env.get(key)for key in ('PATH','LANG','LC_ALL','TMPDIR','PYTHONDONTWRITEBYTECODE','PYTHONIOENCODING')},'actual_exit':result.returncode,'stdout_sha256':sha(result.stdout),'stderr_sha256':sha(result.stderr),'stdin_sha256':None if data is None else sha(data)}
        (where/'result.json').write_text(json.dumps(row,indent=2)+'\n');self.rows.append(row)
        need(result.returncode==0,'command failed; raw retained '+str(where))
        return result.stdout
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--sha',required=True);a=ap.parse_args()
    need(re.fullmatch('[0-9a-f]{40}',a.sha),'full fixed SHA required')
    request=json.loads(TEMPLATE.read_text());need(a.sha==request['selected_final_source'],'root-authorized final R must match request');request['source_sha']=a.sha
    owner=Path(request['source_owner_repo']);target=Path(request['source_checkout']);out=HERE/'preparation'
    need(not out.exists()and not target.exists()and not Path(request['acceptance_out']).exists(),'fresh preparation/source/acceptance paths required')
    out.mkdir();rec=Recorder(out,a.sha,clean_env());report={'source_sha':a.sha,'source_checkout':str(target),'formal_executed':False,'exit':None}
    def git(*args,cwd=owner):return rec.run(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args],cwd)
    try:
        pins_ok(request)
        fs=os.statvfs(target.parent);report['free_bytes_before']=fs.f_bavail*fs.f_frsize;report['resource_filesystem']=str(target.parent)
        need(report['free_bytes_before']>=request['source_resource_min_free_bytes'],'source/index storage admission')
        for value in (a.sha,request['base'],request['main'],'6366304eb787b2a50282e4132f45e51eb7d21290'):
            need(git('rev-parse',value+'^{commit}').decode().strip()==value,'fixed local object missing')
        need(git('rev-parse','--show-object-format').strip()==b'sha1','expected Git SHA1 object identity')
        entries={}
        for row in git('ls-tree','-r','-z','-l',a.sha).rstrip(b'\0').split(b'\0'):
            meta,path=row.split(b'\t',1);mode,kind,oid,size=meta.split()
            if kind==b'blob':entries[path.decode()]={'mode':mode.decode(),'oid':oid.decode(),'bytes':int(size)}
        scopes=('geometry-core/','geometry-app/','geometry-templates/','geometry-web/')
        selected={name for name in entries if (name=='current_geometry.c'or name.startswith(scopes))and name.endswith(('.c','.h','.inc'))}
        selected|={name for name in entries if'fixtures'in PurePosixPath(name).parts}
        selected|={name for name in entries if'/'not in name and name.endswith('.scene')}
        selected|={'.gitattributes','.gitignore','AGENTS.md',
          'tests/evidence/k2a-collection-capacity-20261012/legacy6a.gcanvas',
          'tests/evidence/k2a-collection-capacity-20261012/legacy6a-with-scene.gcanvas',
          'tests/evidence/k2a-boundary-review-20261012/legacy/base49-capacity.gcanvas'}
        need(selected<=entries.keys(),'required source/fixture is missing from fixed tree')
        # Complete quoted include closure from immutable Git bytes, regardless of suffix.
        pending=[name for name in selected if name.endswith(('.c','.h','.inc'))];seen=set();unresolved=[]
        while pending:
            name=pending.pop()
            if name in seen:continue
            seen.add(name);raw=git('show',a.sha+':'+name)
            for include in re.findall(rb'^\s*#\s*include\s*"([^"\r\n]+)"',raw,re.M):
                child=posixpath.normpath(posixpath.join(posixpath.dirname(name),os.fsdecode(include)))
                need(not child.startswith('../')and not child.startswith('/'),'quoted include escapes fixed repository')
                if child in entries:
                    selected.add(child);pending.append(child)
                else:unresolved.append({'from':name,'include':os.fsdecode(include),'relative':child})
        root_scenes=sorted(name for name in selected if'/'not in name and name.endswith('.scene'))
        base_roots=git('ls-tree','-z','--name-only',request['base']).decode().split('\0')
        base_scenes=sorted(name for name in base_roots if name.endswith('.scene'))
        extra='_i11_two_surfaces_same_uv_accept.scene'
        need(len(base_scenes)==171 and root_scenes==sorted(base_scenes+[extra]),'complete original171 plus unique I11 root fixtures')
        for name in base_scenes:need(entries[name]['oid']==git('rev-parse',request['base']+':'+name).decode().strip(),'original scene bytes changed: '+name)
        need(entries[extra]['oid']==git('rev-parse','6366304eb787b2a50282e4132f45e51eb7d21290:'+extra).decode().strip(),'named I11 fixture changed')
        need(all(entries[name]['mode']in('100644','100755')for name in selected),'no symlink/submodule source materialization')
        source_bytes=sum(entries[name]['bytes']for name in selected);need(source_bytes<request['source_budget_bytes'],'thin source exceeds reviewed storage budget')
        git('clone','--shared','--no-hardlinks','--no-checkout',str(owner),str(target))
        need(sorted(p.name for p in target.iterdir())==['.git'],'new clone unexpectedly checked out files')
        git('config','--local','core.autocrlf','false',cwd=target)
        git('config','--local','core.sparseCheckout','true',cwd=target)
        git('config','--local','core.sparseCheckoutCone','false',cwd=target)
        patterns=''.join('/'+name+'\n'for name in sorted(selected));(out/'SPARSE_STDIN.txt').write_text(patterns)
        sparse=target/'.git/info/sparse-checkout';sparse.write_text(patterns)
        need(not(target/'.git/index').exists(),'fresh clone index must not exist')
        git('update-ref','--no-deref','HEAD',a.sha,cwd=target)
        git('read-tree','--dry-run','-m','-u',a.sha,cwd=target)
        git('read-tree','-m','-u',a.sha,cwd=target)
        own_objects=Path(git('rev-parse','--git-common-dir').decode().strip())
        if not own_objects.is_absolute():own_objects=owner/own_objects
        alternates=(target/'.git/objects/info/alternates').read_text().splitlines()
        need(len(alternates)==1 and Path(alternates[0]).resolve()==(own_objects/'objects').resolve(),'borrow immutable Git objects only')
        manifest=[]
        for name in sorted(selected):
            path=target/name;raw=path.read_bytes();stat=path.stat();entry=entries[name]
            need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==entry['oid'],'checkout bytes differ from immutable Git blob: '+name)
            need(stat.st_nlink==1,'source file is hardlinked/shared: '+name)
            other=owner/name
            if other.exists():need((stat.st_dev,stat.st_ino)!=(other.stat().st_dev,other.stat().st_ino),'source file aliases original owner')
            path.chmod(0o555 if entry['mode']=='100755'else 0o444)
            manifest.append({'path':name,**entry,'sha256':sha(raw),'nlink':stat.st_nlink,'source_shared_writable':False})
        need(git('rev-parse','HEAD',cwd=target).decode().strip()==a.sha,'fixed detached source HEAD')
        need(git('status','--porcelain=v1','--untracked-files=all',cwd=target)==b'','prepared source must be clean')
        report.update(exit=0,entries=manifest,source_bytes=source_bytes,root_scenes=root_scenes,quoted_include_unresolved=unresolved,object_alternates=alternates)
        request['status']='FIXED_SOURCE_PREPARED; formal stages still UNRUN'
        (HERE/'REQUEST.json').write_text(json.dumps(request,ensure_ascii=False,indent=2)+'\n')
    except BaseException as exc:report.update(exit=1,error=repr(exc))
    finally:
        report['commands']=rec.rows;(out/'RESULT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({k:report.get(k)for k in('source_sha','source_bytes','exit','error')}),flush=True)
    return report['exit']
if __name__=='__main__':sys.exit(main())
