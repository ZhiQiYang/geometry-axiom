from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
S='2c4635577a8fcb11e88b346547f7bb1c7b739fb7'
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,v):
 assert not p.exists(),str(p)
 p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
scopes={
 'formal':Path('/tmp/geo337-reference-local-init-formal-20261024'),
 'formal-outer':Path('/tmp/geo337-reference-local-init-formal-launch-20261024'),
 'source-and-tools':Path('/tmp/geo337-reference-local-init-draft-20261024'),
 'product-static-peer':Path('/tmp/geo337-reference-local-init-product-peer-evidence-20261024'),
 'harness-static-peer':Path('/tmp/geo337-reference-local-init-harness-peer-specials-20261024'),
 'driver-static-peer':Path('/tmp/geo337-reference-local-init-tool-peer-specials-20261024'),
 'root-cause-originals':Path('/tmp/geo323-N16-fixed-cost-static-peer-20261024'),
}
rows=[]
for label,root in scopes.items():
 assert root.is_dir()
 for path in sorted(root.rglob('*')):
  assert not path.is_symlink(),str(path)
  if path.is_dir():continue
  assert path.is_file(),str(path)
  b=path.read_bytes()
  rows.append({'archive':label+'/'+str(path.relative_to(root)),'local':str(path),'bytes':len(b),'sha256':sha(b)})
dump(H/'PACKAGE_PLAN.json',{'source_sha':S,'files':rows,'scope':'Complete originals, no product rerun, no O2/wall claim','count':len(rows),'bytes':sum(x['bytes']for x in rows)})
original=Path('/tmp/geo323-provider-hint-publication-20261024/collect.py').read_text()
assert original.count('ORIGINAL_PROVIDER_HINT_EVIDENCE.tar.gz')==1
candidate=original.replace('ORIGINAL_PROVIDER_HINT_EVIDENCE.tar.gz','ORIGINAL_REFERENCE_LOCAL_INIT_EVIDENCE.tar.gz').replace("tarfile.open(archive,'w:gz',compresslevel=6)","tarfile.open(archive,'w:gz',compresslevel=6,dereference=True)")
old="need(len(b)==item['bytes'],'frozen metadata size changed');rows.append({**item,'sha256':sha(b)})"
new="need(len(b)==item['bytes'],'frozen metadata size changed');need(sha(b)==item['sha256'],'frozen original hash changed');rows.append({**item,'sha256':sha(b)})"
assert candidate.count(old)==1
candidate=candidate.replace(old,new)
assert not (H/'collect.py').exists()
(H/'collect.py').write_text(candidate)
dump(H/'PREPARATION.json',{'source_sha':S,'original_collector':sha(original.encode()),'collector':sha(candidate.encode()),'plan':sha((H/'PACKAGE_PLAN.json').read_bytes()),'files':len(rows),'bytes':sum(x['bytes']for x in rows),'only_changes':['archive filename','force regular tar members for alias-safe collection','verify frozen original SHA before archive'],'formal_tests_reexecuted':False})
print((H/'PREPARATION.json').read_text())
