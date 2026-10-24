from pathlib import Path
import hashlib,io,json,tarfile,datetime
O=Path(__file__).resolve().parent/'package';assert not O.exists();O.mkdir()
R=Path('/workspace/geo345-six-original-requests-20261024');r=json.loads((R/'RESULT.json').read_bytes());terminal=json.loads((R/'EXEC_COMPLETION.json').read_bytes());assert terminal['result']['exit_code']==r['exitCode']==0 and len(r['requests'])==6
roots={'scheduler-originals':R,'actual-peer':Path('/workspace/geo345-six-phase-actual-peer-evidence-20261024'),'scheduler-static-peer':Path('/workspace/geo345-six-request-scheduler-peer-evidence-20261024'),'original-helper-preparation':Path('/tmp/issue214-http-fixture-preparation-20261024'),'original-helper-peer':Path('/tmp/issue214-http-fixture-helper-peer'),'descriptive-analysis':Path('/workspace/geo345-runtime-analysis-20261024')}
for n in ('original-formal','original-components','fixed-formal','fixed-components','withdrawn-components','restored-components'):roots['phase-'+n]=Path('/workspace/issue214-'+n+'-once')
items={}
for label,root in roots.items():
 assert root.is_dir()
 for p in sorted(root.rglob('*')):
  if p.is_file():
   assert not p.is_symlink() and '__pycache__' not in p.parts
   items[label+'/'+p.relative_to(root).as_posix()]=p
P=Path('/workspace/geo345-runtime-launch-preparation-20261024')
for n in ('launch_six_original_requests.py','READ_ONLY_PREFLIGHT.json','EXCLUSIVE_ADMISSION_NOT_LAUNCHED.json'):items['scheduler-preparation/'+n]=P/n
for p in (P/'read-only-preflight').rglob('*'):
 if p.is_file():items['scheduler-preparation/read-only-preflight/'+p.relative_to(P/'read-only-preflight').as_posix()]=p
items['collector/collect_originals.py']=Path(__file__)
def sha(b):return hashlib.sha256(b).hexdigest()
rows=[];archive=O/'ORIGINAL_SIX_PHASES_AND_ANALYSIS.tar.gz'
with tarfile.open(archive,'w:gz',compresslevel=6)as tf:
 for name,p in sorted(items.items()):
  raw=p.read_bytes();assert raw[:4]!=b'\x7fELF';info=tarfile.TarInfo(name);info.size=len(raw);info.mode=0o644;info.mtime=0;tf.addfile(info,io.BytesIO(raw));rows.append({'member':name,'source':str(p),'bytes':len(raw),'sha256':sha(raw)})
with tarfile.open(archive,'r:gz')as tf:
 members=tf.getmembers();assert len(members)==len(rows)
 for member,row in zip(members,rows):
  raw=tf.extractfile(member).read();assert member.name==row['member'] and sha(raw)==row['sha256'] and raw==Path(row['source']).read_bytes()
index={'archive':archive.name,'archive_sha256':sha(archive.read_bytes()),'archive_bytes':archive.stat().st_size,'files':rows}
(O/'RAW_INDEX.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
summary={k:v for k,v in index.items()if k!='files'};summary.update(source_original=r['sourceOriginal'],source_fixed=r['sourceFixed'],actual_six_exits=[x['actualProcessExit']for x in r['requests']],roundtrip_all_bytes_equal=True,member_count=len(rows),original_bytes=sum(x['bytes']for x in rows),created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),limits=['All six original correctness exits0; polling withdrawal is equivalent behavior, not killed correctness mutation.','Formal and component measurements separate; component wall/process-CPU spans inclusive, no nested sum.','Original inner run_process exposes decoded combined text only; all exposed original text retained, no fabricated separate inner pipes.','Native cache executable payload remains original in /tmp/geometry-tests; before/after hash and exact sidecar bytes retained, not a copy of the ELF.','Only these two formal selected19 and four observed19 requests; no full native/browser/final ledger/architecture credit.'])
(O/'SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False))
