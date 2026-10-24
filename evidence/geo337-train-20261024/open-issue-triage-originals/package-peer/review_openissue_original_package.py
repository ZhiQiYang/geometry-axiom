from pathlib import Path
import hashlib,json,tarfile
B=Path('/workspace/open-issue-triage-originals-publication-20261024');P=B/'package';idx=json.loads((P/'INDEX.json').read_text());res=json.loads((P/'RESULT.json').read_text());checks=0;findings=[]
def h(b):return hashlib.sha256(b).hexdigest()
def ck(v,n):
 global checks
 checks+=1
 if not v:findings.append(n)
a=Path(res['archive']);ck(a.stat().st_size==534257==res['archive_bytes'] and h(a.read_bytes())=='fb43e78c03e176f4a700e6aa3481804d07b4c1081537522f3a3d12db70f3bbb9','archive exact pin');ck(h((P/'INDEX.json').read_bytes())==res['index_sha256'],'index pin');ck(res['exit_code']==0 and res['roundtrip_all_member_bytes'] and res['original_source_bytes_unchanged'],'producer complete result');rows=idx['entries'];ck(len(rows)==idx['source_member_count']==89 and res['members']==90,'89 originals plus index')
with tarfile.open(a,'r:gz') as t:
 members=t.getmembers();ck(len(members)==len({m.name for m in members})==90,'unique 90 members');names=set(t.getnames());ck(names=={r['member'] for r in rows}|{'INDEX.json'},'exact membership')
 for r in rows:
  m=t.getmember(r['member']);b=t.extractfile(m).read();orig=Path(r['source_path']).read_bytes();ck(m.isfile() and not r['member'].startswith('/') and '..' not in Path(r['member']).parts,'regular safe '+r['member']);ck(len(b)==r['bytes'] and h(b)==r['sha256'],'member bytes/hash '+r['member']);ck(b==orig,'original exact '+r['member'])
 ck(t.extractfile('INDEX.json').read()==(P/'INDEX.json').read_bytes(),'index own payload bytes')
ck(sum(r['bytes'] for r in rows)==res['original_member_bytes']==1482357,'original byte sum')
required=['r1/HANDOFF_DRAFT.md','r1/TRIAGE.json','r1/INDEX.json','independent-peer/OPENISSUE_TRIAGE_REFRESH_INITIAL_PEER.json','independent-peer/OPENISSUE_TRIAGE_REFRESH_PEER.json','independent-peer/OPENISSUE_TRIAGE_R2_NARROW_CORRECTION_PEER.json','producer/INITIAL_LAUNCH_FAILURE.txt']
for n in required:ck(n in names,'original history retained '+n)
ck(len([r for r in rows if r['source_path'].endswith('.json') and '/issue-' in r['source_path'] and '/open-issues-triage-r2/' in r['source_path']])==38,'38 exact captured issue JSON included')
rr=json.loads((B/'producer/RESULT.json').read_text());cc=json.loads((B/'producer/subcommands.json').read_text());ck(rr['actual_exit']==0 and len(cc)==1 and cc[0]['actual_process_returncode']==0 and not cc[0]['timeout_expired'],'actual collector outer 0')
for stream in ['stdout','stderr']:
 q=Path(cc[0]['directory'])/(stream+'.bin');v=q.read_bytes();ck(h(v)==cc[0][stream+'_sha256'] and len(v)==cc[0][stream+'_bytes'],'collector exposed '+stream)
report=dict(schema='independent-openissue-small-original-package-peer/1',checks=checks,findings=findings,exit_code=int(bool(findings)),archive_sha256=res['archive_sha256'],member_count=90,original_bytes=1482357,classification_scope='No repeat of129/19 classifications. Old340 finding1, checker wording false-positive and corrected draft retained without rewriting original status.',limits=['No API/subject/source mutation; streamed tar reads only, no extraction or new archive.','Collector terminal RESULT/subcommands/stdout/stderr live outside the immutable90-member archive; publication should retain those small external producer receipts too.','All38 issue JSON are historical capture, not fresh complete current GitHub enumeration.'])
o=Path('/tmp/train337-adversarial/OPENISSUE_R1_R2_ORIGINAL_PACKAGE_PEER.json');o.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'report':str(o),'sha256':h(o.read_bytes()),'checks':checks,'findings':findings}));raise SystemExit(bool(findings))
