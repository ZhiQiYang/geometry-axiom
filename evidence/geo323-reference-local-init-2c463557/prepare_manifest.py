from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;PREFIX='evidence/geo323-reference-local-init-2c463557'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):
 assert not p.exists(),str(p)
 p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
assert sha(Path('/tmp/geo337-h-init-resume-actual-peer-20261025/REVIEW.json'))=='6fde0efefd97340bf49c0529062e40b42663207cf8fe5c5d8ec4f7dd351c11c8'
assert sha(Path('/tmp/geo337-h-init-collector-peer-20261025/ACTUAL_PACKAGE_REVIEW.json'))=='5c19e8cd4bcbba52210c6b1dfb74e8fcc001bf54ce49a99e8118ecebe2970dea'
assert sha(Path('/tmp/geo337-h-init-collector-peer-20261025/PUBLICATION_STATIC_REVIEW.json'))=='e554d1439e6d379614d591a1e306890a4e44c46d2b259fb4f5c9ab4d4cc7d657'
files={}
def add(name,p):
 assert name not in files and p.is_file() and not p.is_symlink(),str(p)
 files[PREFIX+'/'+name]={'local':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
for name in ['PROGRESS.md','PACKAGE_PLAN.json','PREPARATION.json','PUBLICATION_TOOL.json','prepare.py','prepare_publication.py','prepare_manifest.py','collect.py','publish.py','launch_collect.py','ORIGINAL_TOOL_INITIAL.json','ORIGINAL_TOOL_FINAL.json']:
 add(name,H/name)
for label,p in [('package',H/'package'),('collection-launch',H/'collection-launch'),('actual-focused-peer',Path('/tmp/geo337-h-init-resume-actual-peer-20261025')),('collection-publication-peers',Path('/tmp/geo337-h-init-collector-peer-20261025'))]:
 for f in sorted(p.rglob('*')):
  assert not f.is_symlink()
  if f.is_dir():continue
  add(label+'/'+str(f.relative_to(p)),f)
dump(H/'PAYLOAD_INDEX.json',{'source_sha':'2c4635577a8fcb11e88b346547f7bb1c7b739fb7','files':files,'self_excluded':True,'body_branch_only':'PR_BODY.md'})
add('PAYLOAD_INDEX.json',H/'PAYLOAD_INDEX.json')
dump(H/'PUBLICATION_MANIFEST.json',{'source_sha':'2c4635577a8fcb11e88b346547f7bb1c7b739fb7','prefix':PREFIX,'files':files,'body_sha256':sha(H/'PR_BODY.template.md')})
print(json.dumps({'files':len(files),'bytes':sum(x['bytes']for x in files.values()),'manifest_sha256':sha(H/'PUBLICATION_MANIFEST.json')}))
