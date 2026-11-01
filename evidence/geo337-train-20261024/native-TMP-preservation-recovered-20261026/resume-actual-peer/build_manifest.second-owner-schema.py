from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, stat

OUT=Path('/tmp/geo337-resume-tmp-preservation-peer-20261026')
OWN=Path('/dev/shm/geometry-axiom-geo337-20261025')
PREP=Path('/tmp/geo337-native-TMP-combined-preservation-20261025')
MANIFEST=OUT/'publication-manifest.json'
DEST='evidence/geo337-train-20261024/native-TMP-preservation-recovered-20261026'
def H(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
def row(src,dst,pin=None):
    s=src.lstat()
    if not stat.S_ISREG(s.st_mode):raise RuntimeError('not regular: '+str(src))
    b=src.read_bytes();h=H(b)
    if pin is not None and h!=pin:raise RuntimeError('pin mismatch: '+str(src))
    s2=src.lstat()
    if (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)!=(s2.st_dev,s2.st_ino,s2.st_size,s2.st_mtime_ns):raise RuntimeError('changed: '+str(src))
    return {'source_path':str(src),'destination':DEST+'/'+dst,'bytes':len(b),'sha256':h}

assert read(OUT/'REVIEW.json')['exit_code']==0
files=[]
facts_path=Path('/workspace/geo337-old-TMP-cache-owner-metadata-20261025/FACTS.json')
facts=read(facts_path)
owner_files=[]
for i,owner in enumerate(facts['rows']):
    terminal_key='all_stages_terminal' if owner['cache']=='/tmp/geometry-tests-pre-geo323-f43e8d8b' else 'all_jobs_terminal'
    assert owner['terminal'][terminal_key] is True
    for key in ['isolation_receipt','successor_terminal_receipt','context']:
        v=owner[key];r=row(Path(v['path']),'original-owner-receipts/'+str(i)+'-'+key+'.json',v['sha256']);files.append(r);owner_files.append(r)
elfs=read(PREP/'auxiliary-readonly-validation/EXACT_ELF_LEAVES.json')
fingerprints=[]
for i,e in enumerate(elfs):
    r=row(Path(e['fingerprint_receipt']),'original-ELF-fingerprints/'+str(i)+'.json',e['fingerprint_sha256']);files.append(r);fingerprints.append(r)
facts_pin='656b7467da64843ad7de155379f6738f5652ee8915ba4e8bc0e2eec051bcf2ab'
files.append(row(facts_path,'original-owner-receipts/FACTS.json',facts_pin))
ownership={'schema':'TMP-preservation-owner-originals-readonly-check/1','reviewed_utc':datetime.now(timezone.utc).isoformat(),'exit_code':0,
           'facts_sha256':facts_pin,'owner_receipts':owner_files,'fingerprints':fingerprints,
           'reader_schema_correction':{'initial_tool_exit':1,'initial_exception':"KeyError: 'all_jobs_terminal'",'cause':'Original #323 metadata uses all_stages_terminal while the other three use all_jobs_terminal. Reader now selects the exact recorded key for that one cache; no terminal verdict changed.'},
           'limits':['Exact existing task-owned generated-cache metadata only; old failure exits preserved.','No inference that all runtime consumers are currently absent; no retirement or publication performed.']}
(OUT/'OWNER_ORIGINALS.json').write_text(json.dumps(ownership,ensure_ascii=False,indent=2)+'\n')
scopes=[(OWN/'native-TMP-preservation-20261025','original-package'),(OWN/'native-TMP-preservation-root-original-20261025','original-outer'),
        (OUT,'resume-actual-peer')]
scope_counts=[]
for root,prefix in scopes:
    before=len(files)
    for src in sorted(root.rglob('*')):
        if src==MANIFEST:continue
        if src.is_symlink():raise RuntimeError('symlink in scope: '+str(src))
        if src.is_file():files.append(row(src,prefix+'/'+src.relative_to(root).as_posix()))
    scope_counts.append({'source_path':str(root),'destination_prefix':prefix,'files':len(files)-before})
files.append(row(Path('/tmp/geo337-native-TMP-executors-static-peer-20261025/ARCHIVE_REVIEW.json'),'original-static-peer/ARCHIVE_REVIEW.json',
                 '8f8a6d704e2eb0a7ef0d7ae913296f19437d8434d9794e352e9f22cf9495a3e7'))
files.sort(key=lambda x:x['destination'])
assert len({x['destination'] for x in files})==len(files)
unique={x['sha256']:x['bytes'] for x in files}
result=read(OWN/'native-TMP-preservation-20261025/RESULT.json')
selected={(x['bytes'],x['sha256']) for x in files}
for a in result['archives']:
    assert (a['raw_bytes'],a['raw_sha256']) in selected
    assert (a['gzip_bytes'],a['gzip_sha256']) in selected
manifest={'schema':'native-TMP-complete-preservation-publication-input/1','prepared_utc':datetime.now(timezone.utc).isoformat(),
          'publisher_expected_parent':'ROOT_MUST_BIND_CURRENT_RECOVERY_BRANCH_HEAD',
          'archive_result_sha256':H((OWN/'native-TMP-preservation-20261025/RESULT.json').read_bytes()),
          'plan_sha256':result['plan_sha256'],'files':files,'scope_counts':scope_counts,
          'file_count':len(files),'total_selected_bytes':sum(x['bytes'] for x in files),
          'unique_sha256_blob_count':len(unique),'unique_sha256_blob_bytes':sum(unique.values()),
          'complete_raw_members':26,'complete_gzip_members':26,'gzip_does_not_replace_raw':True,
          'original_command_count':127,'all_original_raw_streams_included':True,'manifest_self_excluded':True,
          'published':False,'remote_hash_verified':False,'delivered':False,'actual_freed_bytes':0,
          'limits':['Every raw and gzip blob must be individually remote-verified before original retirement can be considered.',
                    'This manifest never authorizes unlink or changes any root lease, formal test, threshold, fixture, source or Git object.',
                    'Byte totals are actual selected payload costs, not a runtime/Git peak forecast.']}
MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:manifest[k] for k in ['file_count','total_selected_bytes','unique_sha256_blob_count','unique_sha256_blob_bytes','complete_raw_members','complete_gzip_members']}))
print(json.dumps({'manifest_bytes':MANIFEST.stat().st_size,'manifest_sha256':H(MANIFEST.read_bytes()),
                  'directory_bytes':sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())}))
