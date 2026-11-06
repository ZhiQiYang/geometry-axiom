from pathlib import Path
import hashlib,json
O=Path('/tmp/geo337-R7-full-publication-preparation-20261024');B='evidence/geo337-train-20261024/';T=B+'full-R7-five-stage-raw/'
F='6df0264f75e84f03adb70746b6ac3db07a9910fc';E='bd5df6b7fb3c563fa10d0e4cfd37e2ee3ca2b99e'
files=[]
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def add(src,dest,pin=None,extra=None):
 p=Path(src);assert p.is_file() and not p.is_symlink();h=pin if extra else H(p)
 if pin:assert h==pin
 files.append(dict(source_path=str(p),destination=dest,bytes=p.stat().st_size,sha256=h,**(extra or {})))
def tree(src,dest):
 p=Path(src)
 for f in sorted(p.rglob('*')):
  assert not f.is_symlink()
  if f.is_file():add(f,dest+'/'+str(f.relative_to(p)))
O.mkdir()
preload=Path('/tmp/geo337-R7-archive-preload-20261024')
x=json.loads((preload/'RESULT.json').read_text());assert x['exit']==0 and x['root_head_unchanged']==E and x['product_source']==F
package=Path('/tmp/geo323-r7-full-package-20261024')
for p in sorted(package.iterdir()):
 if p.name.endswith('.tar.gz'):
  add(p,T+p.name,x['sha256'],{'preloaded_blob':x['oid'],'preload_receipt':x['receipt'],'preload_receipt_sha256':H(x['receipt'])})
 elif p.name=='RAW_INVENTORY.json':
  continue # Complete inventory is embedded in the immutable archive, pinned by PACKAGE.json.
 elif p.is_file():add(p,T+p.name)
tree('/tmp/geo323-r7-full-collection-20261024',T+'producer')
tree(preload,T+'object-preload')
tree('/tmp/geo323-r7-collector-static-peer-specials-20261024',T+'peer-collector')
for p in ['/tmp/preload_geo337_R7_archive_20261024.py',
          '/tmp/geo337-R7-preload-first-tool-result.json','/tmp/geo337-R7-preload-final-tool-result.json',
          '/tmp/train337-terminal-peer-20261024/R7_FULL_FIVE_STAGE_ACTUAL_PACKAGE_PEER.json',
          '/tmp/train337-terminal-peer-20261024/review_R7_full_package_actual.py',
          '/tmp/train337-publication-peer-20261024/R7_ARCHIVE_PRELOAD_WRAPPER_STATIC_PEER.json',
          '/tmp/train337-publication-peer-20261024/ROOT_R7_TERMINAL_PUBLICATION_ACTUAL_PEER.json',
          '/tmp/train337-publication-peer-20261024/review_R7_terminal_publication_actual.py',
          '/tmp/geo337-R7-terminal-publication-preparation-20261024/INITIAL_BAD_CLI_PIN.json']:
 add(p,T+'publication-inputs/'+Path(p).name)
add(__file__,T+'prepare_publication.py')
index={'schema':'R7-full-originals-publication-inputs/1','execution_source':F,
       'previous_evidence_head':E,'original_outer_exit':1,
       'original_target_outcomes':{'N64_main':'1.2292230778583162 <= 1.3',
                                   'N16_base':'1.05190582882169 > 1',
                                   'exact':'three original stdout mismatches'},
       'raw_inventory_location':'ORIGINAL_R7_FIVE_STAGE_RAW.tar.gz:RAW_INVENTORY.json',
       'archive_bytes':x['bytes'],'archive_sha256':x['sha256'],'preloaded_git_blob':x['oid'],
       'permanent_git_objects_store':x['protected_store'],'do_not_delete_git_objects':True,
       'historical_pending_annotations_preserved':True,
       'actual_package_peer_sha256':H('/tmp/train337-terminal-peer-20261024/R7_FULL_FIVE_STAGE_ACTUAL_PACKAGE_PEER.json')}
p=O/'PUBLICATION_INPUTS.json';p.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n');add(p,T+p.name)
progress=Path('/workspace/geometry-axiom/evidence/geo337-train-20261024/PROGRESS.md').read_text()
old='完整R7 inner／source preparation原件正在一次封包，尚未公開，小摘要不冒完整原包。'
new='''完整 R7 inner／source preparation 原件本提交已公開於 full-R7-five-stage-raw/：9128 members／31,359,550B，SHA256 8f2420a2c4a78cd99355b32183928d1c8ce14c893fdbe88db0f101104622cd7e，獨立原件 roundtrip 50504/0。完整 RAW_INVENTORY.json 已在 tar 內，外部 PACKAGE.json 另釘其 hash；七個 ELF 為 hash inventory，原 payload 全保留。原環境、source、每個指令／退出碼／全輸出、175 scenes、36樣本、四profiles與三份真工具poll均保；完整 producer 初次準備失敗、自驗反證及後續 true0 原件另附。封包0不解除原outer1、N16紅與三exact差。收件時 published:false／peer PENDING 等歷史字樣原封不回寫，當前發布事實由本提交與實際 peer 分欄證明。永久TMP Gitstore中的原已驗blob以普通提交／push公開，沒有移動或刪除原objects。'''
assert progress.count(old)==1
progress=progress.replace(old,new,1)
p=O/'PROGRESS.publish.md';p.write_text(progress);add(p,B+'PROGRESS.md')
assert len({x['destination'] for x in files})==len(files)
p=O/'FILES.json';p.write_text(json.dumps({'schema':'R7-full-originals-publication-manifest/1','product_source':F,'previous_evidence_head':E,'files':files},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'manifest':str(p),'sha256':H(p),'files':len(files),'bytes':sum(x['bytes'] for x in files)}))
