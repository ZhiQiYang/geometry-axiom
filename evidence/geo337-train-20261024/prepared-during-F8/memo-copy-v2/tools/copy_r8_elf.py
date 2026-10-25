"""Copy exact already-built R8 ELFs into fresh private inodes, never relink or rebuild."""
from pathlib import Path
import hashlib,os,shutil,stat
SOURCE_PINS = {'base-pg': {'name': 'original/work/base-pg/bridge', 'source_path': '/tmp/g337323R8/work/base-pg/bridge', 'bytes': 1039760, 'sha256': '4231f2559727262562164487f95da8544595561857886ee598ac5b20f9b1e47b', 'mode': 33216, 'mtime_ns': 1792910969788205716, 'reason': 'Only ELF body excluded; original path retained unchanged.'}, 'fix': {'name': 'original/work/fix/bridge', 'source_path': '/tmp/g337323R8/work/fix/bridge', 'bytes': 1126456, 'sha256': 'e07c98a5be1f28b151b2abf6b206bb2add438024424d5bb6c6d614428ead7088', 'mode': 33216, 'mtime_ns': 1792910818243020758, 'reason': 'Only ELF body excluded; original path retained unchanged.'}, 'fix-trace': {'name': 'original/work/fix-trace/bridge', 'source_path': '/tmp/g337323R8/work/fix-trace/bridge', 'bytes': 1134992, 'sha256': 'fa793dd393932b946bfe521e30c12c3ca8a8096f20b50818a1ce9a50f881a978', 'mode': 33216, 'mtime_ns': 1792910863148363979, 'reason': 'Only ELF body excluded; original path retained unchanged.'}}
def need(ok,message):
    if not ok:raise RuntimeError(message)
def digest_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def signature(path):
    p=Path(path);s=p.lstat();need(stat.S_ISREG(s.st_mode) and not p.is_symlink(),'regular non-symlink ELF required')
    return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns)
def _copy_exact(src,dst,expected):
    src,dst=Path(src),Path(dst)
    need(not dst.exists() and not dst.is_symlink() and dst.parent.is_dir(),'fresh private ELF destination required')
    before=signature(src);need(before[4]==expected['bytes'] and before[2]==expected['mode'],'pinned R8 ELF size/mode changed')
    need(digest_file(src)==expected['sha256'],'pinned R8 ELF bytes changed')
    with src.open('rb') as origin, dst.open('xb') as target:
        shutil.copyfileobj(origin,target,1024*1024)
    os.chmod(dst,stat.S_IMODE(before[2]))
    after=signature(src);copied=signature(dst)
    need(after==before and digest_file(src)==expected['sha256'],'original R8 ELF metadata/bytes changed during copy')
    need((copied[0],copied[1])!=(before[0],before[1]) and copied[3]==1,'ASSERT:memo-copy-must-use-private-distinct-inode')
    need(copied[2]==before[2] and copied[4]==before[4] and digest_file(dst)==expected['sha256'],'copied ELF bytes/mode differ from pinned original')
    return {'source':str(src),'destination':str(dst),'bytes':expected['bytes'],'sha256':expected['sha256'],'mode':copied[2],'source_before':list(before),'source_after':list(after),'destination_state':list(copied),'different_inode':True,'destination_nlink':1,'original_bytes_preserved':True,'storage':'private byte-identical copy; original ELF not rebuilt or linked'}
def copy_r8_binary(label,src,dst):
    need(label in SOURCE_PINS,'unknown R8 binary role')
    expected=SOURCE_PINS[label];src,dst=Path(src),Path(dst)
    need(src.is_absolute() and str(src)==expected['source_path'] and str(src.resolve())==expected['source_path'],'exact pinned original R8 ELF path required')
    formal=Path('/tmp/g337323R8');need(not dst.resolve().is_relative_to(formal),'copy destination must not modify R8 original output')
    return _copy_exact(src,dst,expected)
