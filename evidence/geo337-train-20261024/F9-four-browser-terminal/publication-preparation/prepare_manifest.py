"""Read fixed terminal metadata/archives; prepare additive evidence only, no PROGRESS."""
from pathlib import Path
import hashlib,json,stat
HERE=Path(__file__).parent
F='4f8a794f4167c3562eb182045102e86e9e37cca9'
PARENT='3447ab384c4c777f9d2685128044b9b9d043e17d'
PREFIX='evidence/geo337-train-20261024/F9-four-browser-terminal/'
SHM=Path('/dev/shm/geometry-axiom-geo337-20261025')
PACKAGE=SHM/'remaining-browser-terminal-package-20261025'
OUTER=SHM/'remaining-browser-terminal-collection-original-20261025'
PEER=Path('/workspace/geo337-F9-four-browser-package-actual-peer-20261025/REVIEW.json')
FINAL=Path('/workspace/geo337-F9-four-browser-terminal-collection-EXEC_FINAL-20261025.json')
def need(v,m):
 if not v:raise RuntimeError(m)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def J(p):return json.loads(Path(p).read_bytes())
need(not (HERE/'FILES.json').exists(),'fresh draft')
need(sha(PEER)=='dae2910813bbe3277f6ebd3a744a7c222cbb2db846946b7789055219e4b552b0','package actual peer pin')
peer=J(PEER);need(peer['exit_code']==0 and not peer['blocking_findings'],'package actual peer accepted')
need(sha(PACKAGE/'RESULT.json')==peer['package_result_sha256']=='2103cda1f7549b6a183a1b63cbe2bc2e94e0e673cf6b4f961a16514f7548c969','fixed package result')
need(sha(OUTER/'RESULT.json')==peer['outer_result_sha256'] and sha(FINAL)==peer['host_final_sha256'],'original outer and host final')
pkg=J(PACKAGE/'RESULT.json');need(pkg['collection_exit']==0 and pkg['source_sha']==F,'actual package zero/F9')
need(pkg['parts']==peer['archives'] and pkg['attempts']==peer['jobs'],'actual peer same package source and job rows')
need(pkg['regular_files']==2411 and pkg['symlinks']==8 and pkg['regular_bytes']==125944310,'complete original scope')
jobs=[];job_peer_dirs=[]
keys={'documents':'original_DOCUMENTS_result','grid':'original_CDP_result','space':'original_SPACE_result','timber':'original_SPACE_result'}
for row in peer['jobs']:
 job=row['name'];d=Path('/workspace')/f'geo337-F9-{job}-SHM-actual-peer-20261025';p=d/'REVIEW.json';j=J(p)
 need(j['source_sha']==F and j['exit_code']==0 and not j['blocking_findings'] and j['original_formal_exit']==row['original_formal_exit']==0,'accepted original per-job peer '+job)
 need(j['original_seconds']==row['original_elapsed_seconds'] and j['original_ci_minutes']==row['original_ci_timeout_minutes'],'original timing definition and result '+job)
 detail=j[keys[job]];passed=detail['passedAssertions']if job in ['documents','grid']else detail['passed'];failed=detail['failedAssertions']if job in ['documents','grid']else detail['failed']
 need(failed==0,'original assertions zero failure '+job)
 jobs.append(dict(job=job,source_sha=F,formal_exit=row['original_formal_exit'],wrapper_exit=row['original_wrapper_exit'],ci_gate_exit=row['original_ci_gate_exit'],seconds=row['original_elapsed_seconds'],ci_timeout_minutes=row['original_ci_timeout_minutes'],passed_assertions=passed,failed_assertions=failed,original_result_scope=detail.get('scope',{'coverage':detail.get('coverage')}),golden_compare=detail.get('goldenCompare','not reinterpreted by this manifest'),peer_path=str(p),peer_sha256=sha(p)))
 job_peer_dirs.append((job,d))
need([j['job']for j in jobs]==['documents','grid','space','timber'],'four fixed named jobs')
(HERE/'JOBS.json').write_text(json.dumps(dict(source_sha=F,jobs=jobs,scope='Original job results, not new execution; native1 unchanged; no whole-train readiness claim',delivered=False),ensure_ascii=False,indent=2)+'\n')
table='\n'.join(f"| {r['job']} | {r['formal_exit']}/{r['wrapper_exit']}/{r['ci_gate_exit']} | {r['passed_assertions']}／{r['failed_assertions']} | {r['seconds']:.6f}／{r['ci_timeout_minutes']*60} |"for r in jobs)
readme='''# F9 documents／grid／space／timber 完整原件

固定來源 `4f8a794f4167c3562eb182045102e86e9e37cca9`，四項各依原workflow、各自source／gitdir／port／TMP。下表出口依序為原workflow／wrapper／CI gate；時間上限為原值，沒有新增skip、改golden或放寬判定。

| Job | 原出口 | 通過／失敗assertions | 秒數／原上限秒 |
|---|---|---|---|
'''+table+'''

grid 是原 `GEOMETRY_GRID_SYSTEM_ONLY` job（356 assertions，原 partial-mode 不比較 full-canvas golden）；timber 是原 `GEOMETRY_TIMBER_ONLY` job（79 assertions），不冒完整space suite。space 的原 full-space suite為242 assertions；documents為47。原具體scope、各組完整性、診斷、截圖與完整取樣均在包中及各job獨審。

九包共31,278,535 B，保留2411 regular files／125,944,310原bytes及8 symlink targets。`package/INVENTORY.json`、`PARTS.json`逐一記錄原指令、完整stdout／stderr、環境、SHA、檔案hash/stat與分包位置；所有ELF／cache／profile／screens／診斷均收。20個sourceplan Git metadata／mutable latest葉作hash-only，2個Unix socket只記metadata；原件未刪，seed/source payload未複製。包內上千原葉沒有再逐一入Git。

`collection-original/`為原c387收件argv／exit／全流，`collection-EXEC_FINAL.json`為主機真exit0。`package-actual-peer/`的17156／0包含全members、原sourcehash/stat、mode／mtime／links與9個gzip EOF／CRC；它不代產品gate。`job-actual-peers/`保存各job獨審及其原checker，包括timber reviewer初版修正說明。

`collector-preparation/`保留原稿及精確v3差分；`terminal-bindings/`保留12份原host／plan／materialize身分綁定。首次metadata binder因yielded host封裝出現KeyError而exit1，記錄仍在；只修收件工具對真host封裝的解析，沒有重跑產品或改原FINAL。

這份清單只新增本prefix，不寫PROGRESS或PR正文。主代理將與其他證據合成唯一current-state矩陣。native原exit1仍保留；#314當次outer1／indexguard未因本包變綠，其新修補尚無本包驗收結論。也不代P52／P189／其餘專項，不標READY。

SHM是揮發性。原RESULT的delivered=false保留當時原值；正常push後還須GitHub API逐blob下載完整raw並核bytes／SHA256／GitOID，實際出版收據另列。此README與collector0均不能替代遠端驗證。
'''
(HERE/'README.md').write_text(readme)
snippet='固定F9四個原browser job的workflow／wrapper／CI gate皆0：documents47／0、63.197160秒≤10分鐘；grid356／0、464.984065秒≤15分鐘；space242／0、209.339005秒≤15分鐘；timber79／0、124.531604秒≤20分鐘。grid／timber保原job範圍，不冒full-canvas golden／full-space。九包31,278,535B已收件，2411regular／125,944,310B＋8links，package actual17156／0；本草案未發布，需正常push及remote完整hash後才交付。native1、#314當次outer1/indexguard仍不因本批消失，新v3成果另待真驗收。\n'
(HERE/'CURRENT_STATE_SNIPPET.md').write_text(snippet)
rows=[];dest=set()
def add(p,relative,archive=None):
 p=Path(p);need(p.is_absolute()and not any(x.is_symlink()for x in [p,*p.parents]),'physical regular publication source')
 s=p.stat();need(stat.S_ISREG(s.st_mode),'regular leaf');h=sha(p);after=p.stat();need((s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(after.st_size,after.st_mtime_ns,after.st_ctime_ns),'source stable while hashing')
 if archive is not None:need(s.st_size==archive['archive_bytes']and h==archive['archive_sha256'],'archive bytes/pin matches17156 peer')
 target=PREFIX+relative;need(target not in dest,'unique destination');dest.add(target);rows.append(dict(source_path=str(p),destination=target,bytes=s.st_size,sha256=h))
def directory(root,relative):
 root=Path(root)
 for p in sorted(root.rglob('*')):
  if p.is_file():add(p,relative+'/'+p.relative_to(root).as_posix())
archives={Path(r['archive_path']).name:r for r in pkg['parts']};need(len(archives)==9,'nine archives')
for p in sorted(PACKAGE.iterdir()):add(p,'package/'+p.name,archives.get(p.name))
directory(OUTER,'collection-original')
add(PEER,'package-actual-peer/REVIEW.json');add(Path('/workspace/review_geo337_four_browser_package_20261025.py'),'package-actual-peer/review.py')
for job,d in job_peer_dirs:directory(d,'job-actual-peers/'+job)
for source,rel in [('geo337-remaining-browser-terminal-preparation-20261025','collector-preparation'),('geo337-four-browser-terminal-bindings-20261025','terminal-bindings'),('geo337-four-browser-collector-static-peer-20261025','collector-v2-static-peer'),('geo337-four-browser-collector-v3-delta-peer-20261025','collector-v3-delta-peer')]:directory(Path('/workspace')/source,rel)
add(FINAL,'collection-EXEC_FINAL.json')
for name in ['README.md','JOBS.json','CURRENT_STATE_SNIPPET.md']:add(HERE/name,name)
add(Path(__file__),'publication-preparation/prepare_manifest.py')
need(all(r['destination'].startswith(PREFIX)for r in rows),'only new prefix; no PROGRESS/body/source changed')
manifest=dict(files=rows,source_sha=F,prepared_against_evidence_parent=PARENT,scope='Additive four-browser fullpackage evidence only; root merges with other manifests and owns single current-state PROGRESS',publication_executed=False,delivered=False)
(HERE/'FILES.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
summary=dict(source_sha=F,prepared_against_evidence_parent=PARENT,files=len(rows),bytes=sum(r['bytes']for r in rows),archive_count=9,archive_bytes=sum(r['archive_bytes']for r in pkg['parts']),regular_members=2411,symlink_members=8,package_peer_sha256=sha(PEER),files_sha256=sha(HERE/'FILES.json'),source_prefix=PREFIX,SHM_written=False,PROGRESS_written=False,published=False,delivered=False)
(HERE/'BINDING.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False))
