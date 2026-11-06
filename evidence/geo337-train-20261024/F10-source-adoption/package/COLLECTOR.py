from pathlib import Path
import tarfile,gzip,hashlib,json,io,stat,os
ROOT=Path('/dev/shm/geometry-axiom-geo337-20261025')
SRC=ROOT/'F10-source-adoption-original-20261025';OUT=ROOT/'F10-source-adoption-package-20261025'
def h(b):return hashlib.sha256(b).hexdigest()
def inventory():
    rows={}
    for p in sorted(SRC.rglob('*')):
        st=p.lstat()
        if stat.S_ISDIR(st.st_mode):continue
        assert stat.S_ISREG(st.st_mode) and not p.is_symlink(),str(p)
        data=p.read_bytes();rows[p.relative_to(SRC).as_posix()]={'bytes':len(data),'sha256':h(data),'mode':stat.S_IMODE(st.st_mode),'mtime_ns':st.st_mtime_ns,'inode':st.st_ino}
    return rows
assert json.loads((SRC/'RESULT.json').read_bytes())['source_sha']=='82c922a3941525d3a094ac0158bdc7dea57ea360'
assert json.loads((SRC/'RESULT.json').read_bytes())['exit_code']==0
assert not OUT.exists()
before=inventory();total=sum(x['bytes']for x in before.values());fs=os.statvfs(ROOT);assert fs.f_bavail*fs.f_frsize>2*total+64*1024*1024
OUT.mkdir(mode=0o700);(OUT/'COLLECTOR.py').write_bytes(Path(__file__).read_bytes())
archive=OUT/'source-adoption.complete.tar.gz'
with archive.open('xb')as raw,gzip.GzipFile(fileobj=raw,mode='wb',mtime=0)as gz,tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT)as tf:
    for name,row in before.items():
        data=(SRC/name).read_bytes();assert len(data)==row['bytes']and h(data)==row['sha256']
        ti=tarfile.TarInfo(name);ti.size=len(data);ti.mode=row['mode'];ti.mtime=0;tf.addfile(ti,io.BytesIO(data))
seen=set()
with tarfile.open(archive,'r:gz')as tf:
    for member in tf:
        assert member.isfile()and member.name in before and member.name not in seen
        data=tf.extractfile(member).read();row=before[member.name];assert len(data)==row['bytes']and h(data)==row['sha256'];seen.add(member.name)
assert seen==set(before) and inventory()==before
with gzip.open(archive,'rb')as f:
    while f.read(1024*1024):pass
(OUT/'INVENTORY.json').write_text(json.dumps(before,ensure_ascii=False,indent=2)+'\n')
result={'exit_code':0,'source_sha':'82c922a3941525d3a094ac0158bdc7dea57ea360','input':str(SRC),'source_before_after_identical':True,'regular_files':len(before),'raw_bytes':total,'archive':str(archive),'archive_bytes':archive.stat().st_size,'archive_sha256':h(archive.read_bytes()),'all_members_roundtrip_verified':True,'collection_only':True,'product_tests_executed':False,'remote_delivery':False}
(OUT/'RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result))
