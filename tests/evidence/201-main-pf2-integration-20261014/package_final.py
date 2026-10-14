import datetime,hashlib,io,json,pathlib,shutil,subprocess,tarfile
repo=pathlib.Path('/tmp/geometry-p095-201');root=pathlib.Path('/tmp/geometry-wake26-201');out=repo/'tests/evidence/201-main-pf2-integration-20261014'
native=root/'native';receipt=json.loads((native/'native-receipt.json').read_text());assert receipt['sources_unchanged']
started=datetime.datetime.fromisoformat(receipt['started_at']).timestamp()
selection=out/'native-log-selection.json'
excluded=json.loads(selection.read_text())['excluded_prior_run'] if selection.exists() else []
included=[];quarantine=root/'excluded-prior-logs';quarantine.mkdir(exist_ok=True)
for p in sorted((native/'run_all-logs').rglob('*')):
 if not p.is_file():continue
 row={'path':p.relative_to(native/'run_all-logs').as_posix(),'mtime_ns':p.stat().st_mtime_ns,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 if p.stat().st_mtime<started:
  excluded.append(row);dest=quarantine/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.move(p,dest)
 else:included.append(row)
(out/'native-log-selection.json').write_text(json.dumps({'rule':'include only logs written at or after this native process started; exclude prior-run shared-directory leftovers','started_at':receipt['started_at'],'included':included,'excluded_prior_run':excluded},indent=2)+'\n')
for name in ['run_native.py','package_final.py','resolve_merge.py','finish_report.py','verify_delivery.py','review-aa6d.md','native-runner.stdout','native-runner.stderr','native-runner.exit','merge-tree-after.stdout','merge-tree-after.exit','main-core-diff.txt','p104-diff.txt','protected-main-diff.txt']:
 shutil.copy2(root/name,out/name)
for name in ['native-receipt.json','native-actual-exit.json','native-start.json','native.stdout','native.stderr','sources-before.json','sources-after.json']:
 shutil.copy2(native/name,out/name)
generated=pathlib.Path('/tmp/geometry-tests/src/engineering-json-test.c').read_bytes()
(native/'binaries/engineering-json-test.c').write_bytes(generated)
for origin,name in [(native,'cloud-native-originals.tar.gz')]:
 inventory=[]
 with tarfile.open(out/name,'w:gz') as archive:
  for p in sorted(origin.rglob('*')):
   if p.is_file():
    relative=p.relative_to(origin).as_posix();data=p.read_bytes();inventory.append({'path':relative,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()});archive.add(p,arcname=relative,recursive=False)
 (out/(name+'.inventory.json')).write_text(json.dumps(inventory,indent=2)+'\n')
before=json.loads((native/'sources-before.json').read_text());entries=[];required=set()
for p in (native/'binaries').glob('*.fingerprint.json'):required.update(json.loads(p.read_text())['files'])
with tarfile.open(out/'executed-sources.tar.gz','w:gz') as archive:
 for relative,sha in sorted(before.items()):
  if ('/evidence/' in relative or '/release-evidence/' in relative) and relative not in required:continue
  p=repo/relative
  if p.suffix.lower() in ['.png','.jpg','.jpeg','.gif','.webp','.ico','.woff','.woff2','.ttf','.mp4'] and not relative.startswith('tests/fixtures/'):continue
  data=p.read_bytes();assert hashlib.sha256(data).hexdigest()==sha
  archive.add(p,arcname=relative,recursive=False);entries.append({'path':relative,'bytes':len(data),'sha256':sha})
 label='tests/test_engineering_json.py#HARNESS'
 meta=tarfile.TarInfo(label);meta.size=len(generated);archive.addfile(meta,io.BytesIO(generated))
 entries.append({'path':label,'bytes':len(generated),'sha256':hashlib.sha256(generated).hexdigest(),'materialized_source':'/tmp/geometry-tests/src/engineering-json-test.c'})
(out/'executed-sources.inventory.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n')
heads=json.loads((out/'merge-proof.json').read_text())['heads']
for label,ref in heads.items():
 data=subprocess.check_output(['git','show',ref+':tests/run_all.expected.json'],cwd=repo)
 (out/(label+'-expected.raw.json')).write_bytes(data)
files=[]
for p in sorted(out.iterdir()):
 if p.is_file() and p.name!='inventory.json':files.append({'path':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(out/'inventory.json').write_text(json.dumps(files,indent=2)+'\n');print(json.dumps({'native_exit':receipt['exit'],'archives':[{k:x[k] for k in ['path','bytes','sha256']} for x in files if '.tar.gz' in x['path'] and not x['path'].endswith('.json')],'source_files':len(entries)},indent=2))
