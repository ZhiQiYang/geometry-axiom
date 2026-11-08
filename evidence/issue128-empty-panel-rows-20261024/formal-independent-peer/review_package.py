from pathlib import Path
import hashlib,json,tarfile
H=Path(__file__).resolve().parent;P=Path('/workspace/issue128-branch-publication-20261024/formal-package')
checks=[]
def h(b):return hashlib.sha256(b).hexdigest()
def check(n,v):checks.append({'check':n,'passed':bool(v)})
idx=json.loads((P/'FORMAL_RAW_INDEX.json').read_text());archive=P/idx['archive_name']
check('fixed-source',idx['source']=='324034812bb6effca68e0413bc0468595337b317')
check('archive-bytes-pin',archive.stat().st_size==idx['archive_bytes']==3308093 and h(archive.read_bytes())==idx['archive_sha256']=='ca40b62ec0462b02ecc1dd8727f4317bf03cf0a8ece286cf302b968725b0adda')
rows={x['member']:x for x in idx['members']};check('1250-unique',len(rows)==len(idx['members'])==1250)
with tarfile.open(archive,'r:gz') as tf:
    members=tf.getmembers();check('member-set',set(x.name for x in members)==set(rows) and len(members)==1250)
    for member in members:
        row=rows[member.name];check('regular:'+member.name,member.isfile())
        data=tf.extractfile(member).read();check('archive-pin:'+member.name,len(data)==row['bytes'] and h(data)==row['sha256'])
        original=Path(row['local']);check('original-bytes:'+member.name,original.is_file() and original.read_bytes()==data)
result={'source':idx['source'],'checks_total':len(checks),'failed_checks':sum(not x['passed'] for x in checks),'archive_sha256':idx['archive_sha256'],'members':1250,'scope':'Read-only original archive roundtrip, supplementary to actual execution peer 621/0.','limits':['No C rerun or global native/ledger/architecture; no current PR body approval implied.']}
(H/'PACKAGE_CHECKS.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n');(H/'PACKAGE_REVIEW.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({**result,'report_sha256':h((H/'PACKAGE_REVIEW.json').read_bytes())}));raise SystemExit(bool(result['failed_checks']))
