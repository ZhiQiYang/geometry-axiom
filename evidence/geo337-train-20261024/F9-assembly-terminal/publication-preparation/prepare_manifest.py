"""Read only frozen SHM originals; write only this small OWN workspace draft."""
from pathlib import Path
import hashlib,json,os,stat,difflib
HERE=Path(__file__).parent
PREFIX='evidence/geo337-train-20261024/F9-assembly-terminal/'
PARENT='60909ad5062c6bc6f072442f5c2957b08b15f443'
F='4f8a794f4167c3562eb182045102e86e9e37cca9'
SHM=Path('/dev/shm/geometry-axiom-geo337-20261025')
PACKAGE=SHM/'assembly-terminal-package-20261025'
OUTER=SHM/'assembly-terminal-collection-original-20261025'
BASE=Path('/workspace/geo337-F9-shm-checkpoint-preparation-v3-20261025/PROGRESS.md')
PEER=Path('/workspace/geo337-assembly-terminal-package-actual-peer-20261025')
def need(v,m):
 if not v:raise RuntimeError(m)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def J(p):return json.loads(Path(p).read_bytes())
need(not (HERE/'FILES.json').exists(),'fresh manifest')
need(sha(BASE)=='0fb9aa7e011c758605835508e1e20ac556aad3b773d0999824269ea05f3e0d51','published parent PROGRESS exact')
need(sha(PACKAGE/'RESULT.json')=='58d68eb5f3af3b1011a0f3e4fd20dceed10edb0ca857d87b8a8b0af41b05b49f','original package pin')
need(sha(PEER/'REVIEW.json')=='5b1b277be93e07cd5278a8b8f3ee4e8385c5e74b95e2cfc59ef1004b2ed8e3e0' and J(PEER/'REVIEW.json')['exit_code']==0,'independent actual peer')
pkg=J(PACKAGE/'RESULT.json');need(pkg['collection_exit']==0 and [x['original_formal_exit']for x in pkg['attempts']]==[1,0],'original independent exits preserved')
old=BASE.read_bytes();marker=b'\n<details>\n';need(old.count(marker)>=1,'original historical boundary')
current,history=old.split(marker,1);text=current.decode()
def repl(a,b):
 global text
 need(text.count(a)==1,'unique current-state delta: '+a[:60]);text=text.replace(a,b)
repl('assembly兩次與documents原件、§7 axiom與新comparison完整原件尚待另批公開；本次是進度與已完成核對的checkpoint，並非這些完整封包已交付。','assembly兩次完整原件本批公開，索引見下；documents、grid、§7 axiom與新comparison完整原件尚待另批公開。封存成功不改任何產品判定，遠端逐blob驗證另以實際出版收據為準。')
repl('首次環境exit1完整保留，詳下文；兩次完整封包尚待公開','首次環境exit1完整保留，詳下文；[兩次完整封包](F9-assembly-terminal/)本批公開，封包actual peer6741/0')
repl('此checkpoint尚不宣稱assembly完整原件已遠端驗證。','本批公開assembly完整封包；是否已完成遠端逐blob驗證只依實際出版收據，不能以本段或原collection0代替。')
gridfinal=Path('/workspace/geo337-F9-grid-SHM-EXEC_FINAL-20261025.json');gj=J(gridfinal);gtool=gj['actual_tool_result'];gout=json.loads(gtool['output'])
need(gj['source_sha']==gout['source_sha']==F and gout['job']=='grid' and gtool['exit_code']==gout['original_process_returncode']==gout['wrapper_exit']==0,'new grid true terminal')
repl('| grid、space、timber | 三項各UNRUN at F9；原workflow，各獨立埠／TMP |','| grid | F9 真終態 exit0；原 host／sampler／launcher 一致；逐項actual peer與完整封包尚待完成／公開，本批附原host FINAL |\n| space、timber | 兩項各UNRUN at F9；原workflow，各獨立埠／TMP |')
repl('目前native1、三browser未跑，替代條件尚未達成','目前native1、兩browser未跑，替代條件尚未達成')
index='\n\n[F9 assembly兩次完整原件與封包獨審](F9-assembly-terminal/README.md)：三包保留828個regular檔35,366,094B＋5個symlink，gzip合計8,121,472B。首次環境exit1／第二次正式exit0與兩次原15分鐘gate0分列；兩次launch、runtime／build ELF、profile、screens、sampler、原commands／環境／mounts全收。只將5個sourceplan Git metadata／mutable latest葉作hash-only、1個Unix socket作metadata-only，seed/source payload原地保留。collector原0、封包actual6741/0不代產品gate；原828葉只在三包中，不另逐葉重複入Git。\n'
text+=index
new=text.encode()+marker+history;need(new.split(marker,1)[1]==history,'complete historical suffix unchanged')
(HERE/'PROGRESS.md').write_bytes(new)
(HERE/'PROGRESS.diff').write_text(''.join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),fromfile='E609/PROGRESS.md',tofile='prepared/PROGRESS.md')))
readme='''# F9 assembly 兩次完整原件

固定產品 SHA `4f8a794f4167c3562eb182045102e86e9e37cca9`。首次環境失敗 exit 1；第二次只縮短 fresh storage 路徑後，原 workflow／launcher／sampler／host 全 exit 0，150 assertions、零 fail／skip。兩次各守原 15 分鐘時限（85.372989／188.843305 秒）；首次尚未執行產品 assertions，不能改稱測試通過。

`package/INVENTORY.json` 逐一列出三個 `ORIGINAL_ASSEMBLY_PART*.tar.gz` 中的原始 argv、exit、完整 stdout／stderr、環境、SHA 與每一檔案 hash/stat。三包保留 828 regular files／35,366,094 B，加 5 symlink targets，gzip 合計 8,121,472 B。未省略 ELF、profile、cache、screens、diagnostic 或預期負例。5 個 sourceplan Git metadata／mutable latest 只記 hash；1 個 Unix socket 只記 metadata，原件未刪除；seed/source payload 不複製。

`collection-original/` 保存真正 c387 收件命令與全流；`collection-EXEC_FINAL.json` 是主機真 exit 0。`package-actual-peer/` 的獨審 6741／0 包含每 member bytes、type、link、mode、mtime；`r2-actual-peer/` 保留第二次產品裁判獨審。這些收件／審查出口不改首次產品 exit 1，也不代其他正式項。

本批只增加此 evidence prefix 並更新唯一 current-state PROGRESS；native 仍 exit 1，其餘未完成項維持。封包原 RESULT 的 delivered=false 是當時尚未出版的事實，保留原 bytes。正常 push 後仍須 GitHub API 下載每個公開 blob 核對完整 bytes／SHA256／Git OID，真驗證收據另列；不能以 ls-remote 或本 README 代替。
'''
(HERE/'README.md').write_text(readme)
rows=[];dest=set()
def add(p,relative,archive=None):
 p=Path(p);need(p.is_absolute()and not any(x.is_symlink()for x in [p,*p.parents]),'physical original input')
 before=p.stat();need(stat.S_ISREG(before.st_mode),'regular publication leaf');h=sha(p);after=p.stat();need((before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_size,after.st_mtime_ns,after.st_ctime_ns),'source unchanged during hash')
 if archive is not None:need(before.st_size==archive['archive_bytes']and h==archive['archive_sha256'],'original archive pin/bytes')
 d=PREFIX+relative;need(d not in dest,'unique destination');dest.add(d);rows.append(dict(source_path=str(p),destination=d,bytes=before.st_size,sha256=h))
archives={Path(x['archive_path']).name:x for x in pkg['parts']};need(len(archives)==3,'three fixed archives')
for p in sorted(PACKAGE.iterdir()):add(p,'package/'+p.name,archives.get(p.name))
for p in sorted(OUTER.rglob('*')):
 if p.is_file():add(p,'collection-original/'+str(p.relative_to(OUTER)))
for name in ['REVIEW.json','review.py']:add(PEER/name,'package-actual-peer/'+name)
for dirname,relative in [('geo337-F9-assembly-r2-SHM-actual-peer-20261025','r2-actual-peer'),('geo337-assembly-terminal-static-peer-20261025','collector-static-peer')]:
 for p in sorted((Path('/workspace')/dirname).iterdir()):
  if p.is_file():add(p,relative+'/'+p.name)
for p in sorted(Path('/workspace/geo337-assembly-terminal-preparation-20261025').iterdir()):
 if p.is_file():add(p,'collector-preparation/'+p.name)
add(Path('/workspace/geo337-F9-assembly-terminal-collection-EXEC_FINAL-20261025.json'),'collection-EXEC_FINAL.json')
add(gridfinal,'other-job-checkpoint/grid-EXEC_FINAL.json')
add(HERE/'README.md','README.md');add(Path(__file__),'publication-preparation/prepare_manifest.py');add(HERE/'PROGRESS.diff','publication-preparation/PROGRESS.diff')
progress=HERE/'PROGRESS.md';rows.insert(0,dict(source_path=str(progress),destination='evidence/geo337-train-20261024/PROGRESS.md',bytes=progress.stat().st_size,sha256=sha(progress)))
manifest=dict(files=rows,source_sha=F,expected_parent=PARENT,scope='three complete archives and original collection metadata/peers; no extracted828leaf duplication',publication_executed=False)
(HERE/'FILES.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
binding=dict(source_sha=F,parent=PARENT,parent_progress_sha256=sha(BASE),history_bytes=len(history),history_sha256=hashlib.sha256(history).hexdigest(),historical_suffix_unchanged=True,files=len(rows),bytes=sum(r['bytes']for r in rows),archive_count=3,archive_bytes=sum(x['archive_bytes']for x in pkg['parts']),package_actual_peer_sha256=sha(PEER/'REVIEW.json'),files_sha256=sha(HERE/'FILES.json'),progress_sha256=sha(progress),SHM_written=False,published=False,delivered=False)
(HERE/'BINDING.json').write_text(json.dumps(binding,ensure_ascii=False,indent=2)+'\n');print(json.dumps(binding,ensure_ascii=False))
