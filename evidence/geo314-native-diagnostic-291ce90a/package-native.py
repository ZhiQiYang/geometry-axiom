import hashlib,json,pathlib,shutil,tarfile,time
src=pathlib.Path('/workspace/geo314-work/native-p2-001');out=pathlib.Path('/tmp/g261-next314/evidence/geo314-native-diagnostic-291ce90a')
manifest=json.loads((src/'observed-build-manifest.json').read_text());suffixes={'.c','.h','.inc','.py','.js','.scene','.json','.log','.txt'}
selected={r['sha256'] for r in manifest['files'] if pathlib.PurePosixPath(r['path']).suffix.lower() in suffixes}
with (src/'observed-build-events.jsonl').open() as stream:
 for line in stream:
  r=json.loads(line)
  if r.get('kind')=='file-version' and pathlib.PurePosixPath(r['path']).suffix.lower() in suffixes:selected.add(r['sha256'])
# Preserve exact original metadata/source/log bytes already cold-stored; do not reconstruct missing observations.
archive=pathlib.Path('/tmp/geo314-native-p2-observed-objects.tar.gz');kept=[]
with tarfile.open(out/'observed-source-buildlog-payloads.tar.gz','w:gz',compresslevel=1) as dst,tarfile.open(archive,'r:gz') as cold:
 for member in cold:
  key=pathlib.PurePosixPath(member.name).name
  if member.isfile() and key in selected:
   f=cold.extractfile(member);raw=f.read();assert hashlib.sha256(raw).hexdigest()==key
   import io
   entry=tarfile.TarInfo('observed-build-objects/'+key);entry.size=len(raw);entry.mode=0o600;dst.addfile(entry,io.BytesIO(raw));kept.append({'sha256':key,'bytes':len(raw)})
assert {r['sha256'] for r in kept}==selected, 'selected source/log payload missing from verified cold archive'
with tarfile.open(out/'native-forensics.tar.gz','w:gz',compresslevel=1) as bundle:
 for p in sorted(src.iterdir()):
  if p.is_file() and p.name not in ('source-inputs-before.tar.gz','source-inputs-after.tar.gz'):
   bundle.add(p,arcname='native-p2-001/'+p.name,recursive=False)
 for name in ('run_native_diagnostic.py',):bundle.add(src.parent/name,arcname='tools/'+name,recursive=False)
 for name in ('geo314-observed-payload-members.json','geo314-observed-payload-cold-storage.json','geo314-native-observer-budget-protection.json'):
  p=pathlib.Path('/workspace/geo261-environment')/name;bundle.add(p,arcname='environment/'+name,recursive=False)
 # Per-suite raw is also present in official cache archive; include plain paths for convenient review.
 bundle.add(src/'private-cache/run_all-logs',arcname='original-run_all-logs',recursive=True)
for n in ('source-inputs-before.tar.gz','source-inputs-after.tar.gz'):shutil.copyfile(src/n,out/n)
record={'schema':'geo314-native-publication/1','source_sha':'291ce90abf9c3bfaf68bd61c4969f2ff9a1be6f6','original_exit_code':1,'scope':'complete original native diagnostic raw, not formal final-SHA acceptance','original_observer_coverage':'observed-only; see original manifest/events/missing and 23:34:10.820863Z payload protection cutoff','public_selected_payloads':kept,'selected_method':'every retained file-version event or final manifest row whose original path suffix is .c/.h/.inc/.py/.js/.scene/.json/.log/.txt; original missing observations remain missing','cold_all_payloads_archive':str(archive),'cold_all_payloads_sha256':'bfa7cdf071b652425bedecf758b53679a29e1183eb7e73ade09edbd25de93b12','nonpublic_extra_payloads':'reconstructable ELF/object/compiler assembly and other optional observer payload bytes remain in full verified cold archive; all metadata and original source/log selected payloads public','files':[]}
for p in sorted(out.iterdir()):
 if p.is_file() and p.name!='PUBLICATION.json':
  h=hashlib.sha256();
  with p.open('rb') as f:
   while chunk:=f.read(1024*1024):h.update(chunk)
  record['files'].append({'path':p.name,'bytes':p.stat().st_size,'sha256':h.hexdigest()})
(out/'PUBLICATION.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');print('selected',len(kept),'source/log bytes',sum(r['bytes'] for r in kept));print([(r['path'],r['bytes']) for r in record['files'] if r['path'].endswith('.gz')])
