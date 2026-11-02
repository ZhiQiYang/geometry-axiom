from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, stat

OUT = Path('/tmp/geo337-resume-terminal-audit-20261026')
OWN = Path('/dev/shm/geometry-axiom-geo337-20261025')
DEST = 'evidence/geo337-train-20261024/S10-recovered-originals-20261026'
MANIFEST = OUT/'publication-manifest.json'
SCOPES = [
    (OWN/'S10-ledger-complete-package', 'ledger-package'),
    (Path('/tmp/geo337-S10-full123-actual-peer-20261025'), 'original-actual-peer'),
    (Path('/tmp/geo337-S10-full123-package-actual-peer-20261025'), 'original-package-actual-peer'),
    (OUT, 'resume-actual-peer'),
    (Path('/tmp/geo337-S10-full123-host-results-20261025'), 'original-host-results'),
    (OWN/'S10-full123-terminal-verify-root-original-20261025', 'original-terminal-verify-outer'),
    (OWN/'S10-full123-terminal-collection-root-original-20261025', 'original-terminal-collection-outer'),
    (OWN/'S10-ledger-terminal-verify', 'original-terminal-verification'),
]
EXTRA = [
    'S10-full123-collection-admission-20261025.json',
    'S10-full123-BOUND_REQUEST-20261025.json',
    'S10-full123-root-admission-20261025.json',
    'S10-full123-filesystem-admission-20261025.json',
]
def row(path, relative):
    s=path.lstat()
    if not stat.S_ISREG(s.st_mode):
        raise RuntimeError('not a regular source: '+str(path))
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    s2=path.lstat()
    if (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)!=(s2.st_dev,s2.st_ino,s2.st_size,s2.st_mtime_ns):
        raise RuntimeError('source changed during hash: '+str(path))
    return {'source_path':str(path),'destination':DEST+'/'+relative,'bytes':s.st_size,'sha256':h.hexdigest()}

files=[];scope_counts=[]
for root,prefix in SCOPES:
    if not root.is_dir():
        raise RuntimeError('missing scope: '+str(root))
    before=len(files)
    for base,dirs,names in os.walk(root,followlinks=False):
        dirs.sort();names.sort()
        for n in dirs:
            if (Path(base)/n).is_symlink():
                raise RuntimeError('symlink directory in scope: '+str(Path(base)/n))
        for n in names:
            p=Path(base)/n
            if p==MANIFEST:
                continue
            files.append(row(p,prefix+'/'+p.relative_to(root).as_posix()))
    scope_counts.append({'source_directory':str(root),'destination_prefix':prefix,'files':len(files)-before})
for n in EXTRA:
    files.append(row(OWN/n,'original-root-bindings/'+n))
files.sort(key=lambda r:r['destination'])
assert len({r['destination'] for r in files})==len(files)
unique={r['sha256']:r['bytes'] for r in files}
index=json.loads((OWN/'S10-ledger-complete-package/INDEX.json').read_bytes())
manifest={
    'schema':'S10-recovered-originals-publication-input/1',
    'prepared_utc':datetime.now(timezone.utc).isoformat(),
    'source_sha':'82c922a3941525d3a094ac0158bdc7dea57ea360',
    'publisher_expected_parent':'ROOT_MUST_BIND_RECOVERY_BRANCH_PARENT',
    'scope':'Evidence-only recovery branch; original source identity retained; no adoption or final-product green claim.',
    'files':files,
    'scope_counts':scope_counts,
    'file_count':len(files),
    'total_selected_bytes':sum(r['bytes'] for r in files),
    'unique_sha256_blob_count':len(unique),
    'unique_sha256_blob_bytes':sum(unique.values()),
    'archived_regular_members':len(index['members']),
    'archived_logical_bytes':index['logical_bytes'],
    'original_large_streams_published_via_existing_archive':True,
    'historical_failed_review_files_included':True,
    'manifest_self_excluded':True,
    'architecture_four_artifacts_included':False,
    'architecture_host_terminal_included':True,
    'published':False,
    'remote_hash_verified':False,
    'delivered':False,
    'limits':['The four architecture artifacts and their full assembly originals require a separate manifest; the original host exit receipt here is not a substitute.',
              'Costs are exact selected payload byte counts, not Git packing or runtime peak estimates.',
              'ELF/source/private Git originals remain protected and are not authorized for deletion by this list.'],
}
MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:manifest[k] for k in ['file_count','total_selected_bytes','unique_sha256_blob_count','unique_sha256_blob_bytes','archived_regular_members','archived_logical_bytes']},ensure_ascii=False))
print('manifest_sha256='+hashlib.sha256(MANIFEST.read_bytes()).hexdigest())
