import hashlib
import json
from pathlib import Path
import shutil
import tarfile

src=Path('/tmp/geo300-authority-20261024')
dest=Path('/tmp/geo300-prerequisites-20261024/evidence/geo300-prerequisites-20261024')
archive=dest/'AUTHORITY_ORIGINALS.tar.gz'
if archive.exists():raise SystemExit('fresh archive required')
files=[]
for path in sorted(src.rglob('*')):
    if path.is_symlink():raise RuntimeError('symlink input rejected')
    if path.is_file():
        raw=path.read_bytes()
        files.append({'original_path':str(path),'archive_path':'authority/'+path.relative_to(src).as_posix(),
                      'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
with tarfile.open(archive,'w:gz') as tar:
    for row in files:tar.add(row['original_path'],arcname=row['archive_path'],recursive=False)
with tarfile.open(archive,'r:gz') as tar:
    actual=tar.getmembers()
    if len(actual)!=len(files):raise RuntimeError('member count mismatch')
    for member,row in zip(actual,files):
        if not member.isfile() or member.name!=row['archive_path']:raise RuntimeError('member type/order mismatch')
        raw=tar.extractfile(member).read()
        if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise RuntimeError('archive roundtrip mismatch')
raw=archive.read_bytes()
result={'schema':'geo300-authority-complete-originals/1','archive':archive.name,'archive_bytes':len(raw),
        'archive_sha256':hashlib.sha256(raw).hexdigest(),'files':files,'file_count':len(files),
        'roundtrip_all_full_bytes_checked':True,'source_or_test_executed':False}
(dest/'AUTHORITY_INVENTORY.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
shutil.copy2(src/'AUTHORITY.json',dest/'AUTHORITY.json')
shutil.copy2('/tmp/geo300-prepare-authority.py',dest/'prepare_authority.py')
shutil.copy2(__file__,dest/'pack_authority.py')
print(json.dumps({'files':len(files),'archive_bytes':len(raw),'archive_sha256':result['archive_sha256']}))
