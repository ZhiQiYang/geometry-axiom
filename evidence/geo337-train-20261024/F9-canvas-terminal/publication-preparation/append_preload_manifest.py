from pathlib import Path
import json,hashlib,stat
O=Path(__file__).parent
P='evidence/geo337-train-20261024/F9-canvas-terminal/'
def H(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
base=O/'FILES.json';assert H(base)=='5c4c2520c9373f8cf402b179369e8db0036fa1127ff451ffde230aeddf53944d'
j=json.loads(base.read_bytes());rows=j['files'];pre=Path('/tmp/geo337-F9-canvas-archive-preload-20261025');q=json.loads((pre/'RESULT.json').read_bytes())
assert q['exit_code']==0 and len(q['archives'])==4 and q['source_sha']=='4f8a794f4167c3562eb182045102e86e9e37cca9' and q['root_head_unchanged']=='c32e70aa2c848f89a0e2e9fd92ed232a4dd27bcc'
for r in q['archives']:
 a=r['archive'];match=[row for row in rows if row['source_path']==a['archive_path']];assert len(match)==1
 m=match[0];assert m['bytes']==a['archive_bytes'] and m['sha256']==a['archive_sha256']
 assert H(r['receipt'])==r['receipt_sha256'];k=json.loads(Path(r['receipt']).read_bytes())
 assert k['exit_code']==0 and k['object_oid']==r['oid'] and k['alternate_connected'] and not k['refs_or_index_adopted']
 m.update(preloaded_blob=r['oid'],preload_receipt=r['receipt'],preload_receipt_sha256=r['receipt_sha256'])
def add(p,d):
 p=Path(p);a=p.lstat();assert stat.S_ISREG(a.st_mode) and not p.is_symlink()
 sha=H(p);b=p.lstat();assert (a.st_dev,a.st_ino,a.st_mode,a.st_size,a.st_mtime_ns,a.st_nlink)==(b.st_dev,b.st_ino,b.st_mode,b.st_size,b.st_mtime_ns,b.st_nlink)
 assert all(v['source_path']!=str(p) and v['destination']!=d for v in rows)
 rows.append(dict(source_path=str(p),destination=d,bytes=a.st_size,sha256=sha))
for p in sorted(pre.rglob('*')):
 if p.is_file() or p.is_symlink():add(p,P+'archive-preload-original/'+p.relative_to(pre).as_posix())
for p in ['/workspace/preload_geo337_F9_canvas_parts_20261025.py','/workspace/git-archive-object-store-tool-20261024/write_archive_blob.py']:
 add(p,P+'tools/'+Path(p).name)
add('/workspace/geo337-F9-canvas-archive-preload-EXEC_FINAL-20261025.json',P+'terminal-and-requests/geo337-F9-canvas-archive-preload-EXEC_FINAL-20261025.json')
add(O/'append_preload_manifest.py',P+'publication-preparation/append_preload_manifest.py')
add(O/'PRELOAD_ADDENDUM.md',P+'publication-preparation/PRELOAD_ADDENDUM.md')
(O/'FILES.v2.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
s={'schema':'geo337-F9-canvas-publication-preload-delta/1','parent_manifest_sha256':H(base),'manifest_sha256':H(O/'FILES.v2.json'),'files':len(rows),'bytes':sum(x['bytes'] for x in rows),'preloaded_archive_rows':4,'preloaded_archive_bytes':sum(x['bytes'] for x in rows if 'preloaded_blob' in x),'body_sha256':H(O/'PR_BODY.template.md'),'progress_sha256':H(O/'PROGRESS.md'),'next_delta_sha256':H(O/'NEXT.delta.md'),'document_bytes_changed':False,'original_archives_copied_or_deleted':False,'publication_performed':False,'permanent_store_do_not_delete':q['permanent_store_do_not_delete']}
(O/'PUBLICATION_SCOPE.v2.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(s,ensure_ascii=False))
