from pathlib import Path,PurePosixPath
import hashlib,json,sys,tarfile
B=Path(sys.argv[1]);expected=sys.argv[2];S=sys.argv[3];count=int(sys.argv[4]);expected_exit=int(sys.argv[5]);O=Path(sys.argv[6]);O.mkdir(exist_ok=False)
def sha(b):return hashlib.sha256(b).hexdigest()
checks=[]
def ck(v,l):
 checks.append({'check':l,'passed':bool(v)})
idx=json.loads((B/'RAW_INDEX.json').read_bytes());summ=json.loads((B/'SUMMARY.json').read_bytes());archive=B/idx['archive'];rows=idx['files'];ck(idx['source_sha']==summ['source_sha']==S,'source exact');ck(sha(archive.read_bytes())==idx['archive_sha256']==summ['archive_sha256']==expected,'archive whole pin');ck(archive.stat().st_size==idx['archive_bytes']==summ['archive_bytes'],'archive byte length');ck(len(rows)==idx['member_count']==summ['member_count']==count,'exact member count');ck(summ['original_exit']==expected_exit,'original exit preserved');ck(sum(r['bytes'] for r in rows)==summ['original_bytes'],'original byte total');ck(len({r['member'] for r in rows})==count,'unique member names');errors=[];total=0
with tarfile.open(archive,'r:gz') as tf:
 members=tf.getmembers();ck(len(members)==count,'tar members');
 for m,r in zip(members,rows):
  name=PurePosixPath(m.name);raw=tf.extractfile(m).read() if m.isfile() else b'';p=Path(r['source']);orig=p.read_bytes();total+=len(raw)
  ck(m.isfile() and m.name==r['member'] and not name.is_absolute() and '..' not in name.parts,'regular exact safe member '+m.name)
  ck(len(raw)==m.size==r['bytes'] and sha(raw)==r['sha256'],'archive bytes/hash '+m.name)
  ck(raw==orig and not p.is_symlink(),'whole original equality '+m.name)
  ck(not raw.startswith(b'\x7fELF'),'no ELF payload '+m.name)
ck(total==summ['original_bytes'],'roundtrip total')
report={'scope':'Independent archive/index/original-byte roundtrip audit only; no product or formal rerun','archive':str(archive),'source_sha':S,'archive_sha256':expected,'index_sha256':sha((B/'RAW_INDEX.json').read_bytes()),'summary_sha256':sha((B/'SUMMARY.json').read_bytes()),'member_count':count,'original_bytes':total,'passed':sum(x['passed']for x in checks),'failed':sum(not x['passed']for x in checks),'exit':0 if all(x['passed']for x in checks) else 1,'limitations':['This audit establishes archive fidelity; raw semantic verdict peer is a separate referenced output.','No Git/source/build mutation and no C or browser execution.'],'checks':checks}
(O/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['source_sha','member_count','original_bytes','passed','failed','exit']}));print(sha((O/'REVIEW.json').read_bytes()));raise SystemExit(report['exit'])
