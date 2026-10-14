import hashlib,json,pathlib,tarfile
out=pathlib.Path('/tmp/geometry-p095-201/tests/evidence/201-p104-wsl-budgets-20261014')
def sha(data):return hashlib.sha256(data).hexdigest()
checks=[]
for archive,index in [('cloud-controls-originals.tar.gz','cloud-controls-originals.tar.gz.inventory.json'),('cloud-native-originals.tar.gz','cloud-native-originals.tar.gz.inventory.json'),('executed-sources.tar.gz','executed-sources.inventory.json')]:
 entries=json.loads((out/index).read_text());expected={e['path']:e for e in entries}
 with tarfile.open(out/archive) as t:
  actual={m.name:m for m in t.getmembers() if m.isfile()};assert set(actual)==set(expected)
  for name,m in actual.items():
   data=t.extractfile(m).read();row=expected[name];assert len(data)==row['bytes'] and sha(data)==row['sha256'],name
 checks.append({'archive':archive,'members':len(entries),'all_bytes_and_hashes_match':True,'sha256':sha((out/archive).read_bytes())})
with tarfile.open(out/'cloud-native-originals.tar.gz') as t,tarfile.open(out/'executed-sources.tar.gz') as sources:
 metadata=[]
 for m in t.getmembers():
  if m.name.startswith('binaries/') and m.name.endswith('.fingerprint.json'):
   fp=json.loads(t.extractfile(m).read());binary=t.extractfile('binaries/'+fp['exe']).read();assert sha(binary)==fp['exe_sha256']
   for name,expected in fp['files'].items():assert sha(sources.extractfile(name).read().replace(b'\r\n',b'\n'))==expected,name
   metadata.append({'sidecar':m.name,'binary':fp['exe'],'binary_sha256':fp['exe_sha256'],'source_references_verified':len(fp['files'])})
 assert len(metadata)==5
assert json.loads((out/'sources-before.json').read_text())==json.loads((out/'sources-after.json').read_text())
receipt={'archives':checks,'native_binary_source_closures':metadata,'fingerprint_normalization':'tests/binaries.py:_normalized_sha applies CRLF to LF; raw archive inventories retain exact bytes','tracked_before_after_equal':True,'scope':'local independently reopened delivery artifacts; WSL20 full TAP remains local-worker delivery, not independently obtained here'}
(out/'delivery-verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
