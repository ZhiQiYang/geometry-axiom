"""Old full-ledger scope, bound only after true terminal. No Git/source/cache writes."""
from pathlib import Path
import argparse,hashlib,io,json,os,stat,tarfile,time
from terminal_guard import HERE,F8,JOB,OUTER,CACHE,ROOT,TMP,need,digest,read_regular,verify_preparation,terminal_lease,bound_terminal

def state(p):
    s=p.lstat();need(stat.S_ISREG(s.st_mode) and not p.is_symlink(),'regular leaf required: '+str(p));return [s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns]
def walk(base):
    need(base.is_dir() and not base.is_symlink(),'original directory required')
    found=[]
    for directory,dirs,files in os.walk(base,followlinks=False):
        for name in dirs:need(not (Path(directory)/name).is_symlink(),'symlink directory excluded, do not silently omit')
        for name in files:
            p=Path(directory)/name;state(p);found.append(p)
    return sorted(found)
def scope(prep,request):
    files=[]
    for base in (JOB,OUTER):files += [(base.name+'/'+p.relative_to(base).as_posix(),p) for p in walk(base)]
    need(CACHE.is_dir() and not CACHE.is_symlink(),'original cache directory required')
    for folder in sorted(CACHE.iterdir()):
        if not(folder.name.startswith('M') or folder.name in ('_baseline','_bridge-baseline')):continue
        need(folder.is_dir() and not folder.is_symlink(),'original cache row must be real directory')
        files += [('original-cache-metadata-and-streams/'+p.relative_to(CACHE).as_posix(),p) for p in walk(folder) if p.name.endswith(('.stdout','.stderr','.json'))]
    for item in prep['original_tools']:files.append(('tools/'+item['archive_name'],Path(item['path'])))
    for item in prep['files']:files.append(('collector-tools/'+item['path'],HERE/item['path']))
    files += [('collector-tools/PREPARATION.json',HERE/'PREPARATION.json'),('terminal-control/BOUND_REQUEST.json',request)]
    control=json.loads(request.read_bytes())['terminal_bindings']['original_tool_final'];files.append(('terminal-control/ORIGINAL_TOOL_FINAL.json',Path(control['path'])))
    names=[n for n,p in files];need(len(names)==len(set(names)),'duplicate archive paths');need(all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in names),'safe relative archive paths');return files

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',type=Path,required=True);p.add_argument('--request-sha256',required=True);p.add_argument('--preparation-sha256',required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--root-terminal-lease',action='store_true',required=True);p.add_argument('--reserve-bytes',type=int,required=True);a=p.parse_args();out=a.out.resolve();request=a.request.resolve()
    need(a.reserve_bytes>=0,'explicit accepted nonnegative free reserve');need(not out.exists() and out.parent.is_dir(),'fresh output with existing parent');need(out.is_relative_to(Path('/tmp')) or out.is_relative_to(Path('/workspace')),'private output only')
    for base in (JOB,OUTER,CACHE,ROOT,TMP,HERE):need(not out.is_relative_to(base) and not base.is_relative_to(out),'output must not overlap originals/source/tools')
    prep=verify_preparation(a.preparation_sha256)
    with terminal_lease():
        terminal=bound_terminal(request,a.request_sha256);files=scope(prep,request);states={n:state(p) for n,p in files};logical=sum(x[4] for x in states.values());fs=os.statvfs(out.parent);free=fs.f_bavail*fs.f_frsize
        # Conservative compressBound-like upper bound plus headers/index, no compression-ratio promise.
        required=logical+logical//1000+sum(((x[4]+511)//512*512-x[4])+2048 for x in states.values())+4*1024*1024+a.reserve_bytes
        need(free>=required,'same-filesystem collector admission failed before creating output')
        out.mkdir();archive=out/'complete-original-commands-and-streams.tar.gz';members=[]
        with tarfile.open(archive,'w:gz',dereference=True) as tar:
            for name,path in files:
                need(state(path)==states[name],'source metadata changed before capture');body=read_regular(path);need(len(body)==states[name][4] and state(path)==states[name],'source changed during capture')
                info=tarfile.TarInfo(name);info.size=len(body);info.mode=states[name][2]&0o777;info.mtime=states[name][5]//1000000000;tar.addfile(info,io.BytesIO(body))
                members.append({'path':name,'source':str(path),'bytes':len(body),'sha256':digest(body),'source_state':states[name]})
        with tarfile.open(archive,'r:gz') as tar:
            entries=tar.getmembers();need([x.name for x in entries]==[x['path'] for x in members] and all(x.isreg() for x in entries),'archive regular-member closure')
            for entry,item in zip(entries,members):
                body=tar.extractfile(entry).read();need(len(body)==item['bytes'] and digest(body)==item['sha256'],'archive member bytes mismatch')
        need([(n,str(p)) for n,p in scope(prep,request)]==[(n,str(p)) for n,p in files],'scope changed while collecting')
        need(all(state(p)==states[n] for n,p in files),'original metadata changed while collecting')
        need(bound_terminal(request,a.request_sha256)==terminal,'terminal changed while collecting')
        # Stream the archive hash; avoid an additional whole-archive in-memory copy.
        h=hashlib.sha256()
        with archive.open('rb') as f:
            for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
        index={'schema':'geo337.F8-full-ledger-terminal-originals/1','source_sha':F8,'collection_exit':0,'terminal':terminal,'archive':archive.name,'archive_bytes':archive.stat().st_size,'archive_sha256':h.hexdigest(),'members':members,'logical_bytes':logical,'storage_admission':{'free_before':free,'required_before':required,'reserve_bytes':a.reserve_bytes},'limits':['Original F8 execution heads/dates/verdicts unchanged; collection0 never means formal0.','Full JOB and original outer raw plus cache M*/_baseline/_bridge-baseline stdout/stderr/json.','No extra ELF or source tree payload archived; original inline source preflight bytes inside raw remain intact. ELF/source/Git/cache objects remain at original paths.','No adoption, Git write, publication or formal rerun performed. Independent actual/package peer required before byte-for-byte adoption.']}
        (out/'INDEX.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n');(out/'TERMINAL.json').write_text(json.dumps(terminal,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'collection_exit':0,'formal_accepted':terminal['formal_accepted'],'source_sha':F8,'members':len(members),'archive_bytes':index['archive_bytes'],'archive_sha256':index['archive_sha256'],'index':str(out/'INDEX.json')},ensure_ascii=False))
if __name__=='__main__':main()
