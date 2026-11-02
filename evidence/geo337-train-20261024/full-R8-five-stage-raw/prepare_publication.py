from pathlib import Path
import hashlib,json
O=Path('/tmp/geo337-R8-full-publication-preparation-20261025');B='evidence/geo337-train-20261024/';T=B+'full-R8-five-stage-raw/'
F='75a1e93811a52b69385cbdaf6a09d773ed9052ad';E='0687f3bd67c150de4856585dae1cbaeded460bc6'
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
preload=Path('/tmp/geo337-R8-archive-preload-20261025')
x=json.loads((preload/'RESULT.json').read_text());assert x['exit']==0 and x['root_head_unchanged']==E and x['product_source']==F
package=Path('/tmp/geo323-r8-full-package-20261025')
for p in sorted(package.iterdir()):
 if p.name.endswith('.tar.gz'):
  add(p,T+p.name,x['sha256'],{'preloaded_blob':x['oid'],'preload_receipt':x['receipt'],'preload_receipt_sha256':H(x['receipt'])})
 elif p.name=='RAW_INVENTORY.json':
  continue # Complete inventory is embedded in the immutable archive, pinned by PACKAGE.json.
 elif p.is_file():add(p,T+p.name)

tree('/tmp/geo323-r8-collection-preparation-20261025',T+'producer')
tree(preload,T+'object-preload')
for label,path in [('collector','/tmp/geo323-r8-collector-static-peer-20261025'),('full-package','/tmp/geo323-r8-full-package-actual-peer-20261025'),('preload','/tmp/geo337-R8-preload-peer-20261025'),('terminal-publication','/tmp/geo337-R8-terminal-publication-peer-20261025')]:tree(path,T+'peer/'+label)
add('/tmp/preload_geo337_R8_archive_20261025.py',T+'preload_archive.py')
add(__file__,T+'prepare_publication.py')
p=O/'PUBLICATION_INPUTS.json';p.write_text(json.dumps({'execution_source':F,'previous_evidence_head':E,'original_outer_exit':1,'quantitative_targets':'all original timing and source-call thresholds met','exact':'three original stdout mismatches','archive_bytes':x['bytes'],'archive_sha256':x['sha256'],'preloaded_git_blob':x['oid'],'permanent_git_objects_store':x['protected_store'],'do_not_delete_git_objects':True,'raw_inventory_location':'ORIGINAL_R8_FIVE_STAGE_RAW.tar.gz:RAW_INVENTORY.json','historical_pending_annotations_preserved':True},ensure_ascii=False,indent=2)+'\n');add(p,T+p.name)
progress=Path('/workspace/geometry-axiom/evidence/geo337-train-20261024/PROGRESS.md').read_text()
old='完整R8 inner/source preparation大型封包尚未公開，不能把小摘要冒完整原包；'
new='完整R8 inner/source preparation原件本提交已公開於full-R8-five-stage-raw/：9057members／31,362,296B，SHA2564503955cefc6fb1a6491ad2a146c259e59a2185401d0fbebc09908a47e3bf9d0。完整inventory在tar內且PACKAGE另釘hash，111,407,792B原件逐member/hash/source roundtrip經獨審；七ELF僅hash inventory，原payload仍保留。原正式outer1／compare1不因收包0而變綠，歷史published:false/PENDING字樣保原不回填；'
assert progress.count(old)==1
progress=progress.replace(old,new,1)
old='root將接續補全R8大包與全帳本、其餘正式驗收。'
new='native ROOT已在保留原refs／五fixtures／sparse與全部原件的條件下，普通detach切至F8並獨審通過；全帳本仍未啟動，正在按實際檔案系統配置新cache／seed與資源預算。root接續全帳本、其餘正式驗收。'
assert progress.count(old)==1
progress=progress.replace(old,new,1)
p=O/'PROGRESS.publish.md';p.write_text(progress);add(p,B+'PROGRESS.md')
assert len({v['destination']for v in files})==len(files)
p=O/'FILES.draft.json';p.write_text(json.dumps({'schema':'R8-full-originals-publication-manifest/1','product_source':F,'previous_evidence_head':E,'files':files},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'manifest':str(p),'sha256':H(p),'files':len(files),'bytes':sum(v['bytes']for v in files)}))
