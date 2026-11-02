from pathlib import Path
import hashlib,json,tarfile,io,stat
P=Path(__file__).resolve().parent;O=Path('/tmp/geo344-S540-convergence-package-20261024');O.mkdir(exist_ok=False)
H=lambda b:hashlib.sha256(b).hexdigest()
roots={'merge-originals':Path('/workspace/geo344-F2bbe-normal-merge-20261024'),'plan-and-original-reads':Path('/workspace/geo344-F2bbe-convergence-plan-20261024'),'merge-peer':Path('/workspace/geo344-F2bbe-merge-peer-backlog-20261024')}
rows=[]
for label,r in roots.items():
 for p in sorted(r.rglob('*')):
  s=p.lstat()
  if stat.S_ISDIR(s.st_mode):continue
  assert stat.S_ISREG(s.st_mode) and not p.is_symlink()
  raw=p.read_bytes();rows.append({'member':label+'/'+p.relative_to(r).as_posix(),'original':str(p),'bytes':len(raw),'sha256':H(raw)})
cap=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py');raw=cap.read_bytes();assert H(raw)=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762';rows.append({'member':'tools/capture.py','original':str(cap),'bytes':len(raw),'sha256':H(raw)})
archive=O/'ORIGINAL_MERGE_AND_CLOSURE.tar.gz'
with tarfile.open(archive,'w:gz')as tf:
 for row in rows:
  raw=Path(row['original']).read_bytes();assert len(raw)==row['bytes']and H(raw)==row['sha256'];t=tarfile.TarInfo(row['member']);t.size=len(raw);t.mode=0o644;t.mtime=0;tf.addfile(t,io.BytesIO(raw))
with tarfile.open(archive,'r:gz')as tf:
 assert len(tf.getmembers())==len(rows)
 for row in rows:assert tf.extractfile(row['member']).read()==Path(row['original']).read_bytes()
(O/'RAW_INDEX.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
summary={'source_sha':'5402765c795769a77a7b249de1e3db80045a41de','members':len(rows),'logical_bytes':sum(x['bytes']for x in rows),'archive_bytes':archive.stat().st_size,'archive_sha256':H(archive.read_bytes()),'roundtrip_original_bytes':True,'new_formal_executions':0,'limitations':['Merge exit0 and whitespace2 retained separately. No product tests run. Publication is not included in this pre-publication original archive.']};(O/'SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary))
