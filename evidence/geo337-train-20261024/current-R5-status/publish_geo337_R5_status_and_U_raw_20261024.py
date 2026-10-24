from pathlib import Path
import hashlib,importlib.util,json,os,shutil
R=Path('/workspace/geometry-axiom');O=Path('/workspace/geo337-R5-status-publication-20261024');B=Path('evidence/geo337-train-20261024');T=B/'current-R5-status';A=B/'full-U-five-stage-raw';F='a22df116c7e9f6b7d074451f1c8052d59e7e4f3e';BEFORE='39a48b7309f8f037543cee7f016f51837f3ff39c';BR='codex/train-337-continue-20261024'
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
S=Path('/workspace/geo323-r5-terminal-summary-20261024/SUMMARY.json');assert H(S)=='3b8ed2e4c82826cdf9a91039c3d639004c1edbe17aad40e8bc7ed1447d84ac89';summary=json.loads(S.read_text());assert summary['source_sha']==F and summary['original_outer_exit']==1
UP=Path('/workspace/geo323-union-full-collection-20261024/package/PACKAGE.json');u=json.loads(UP.read_text());assert u['source_sha']=='ca7838e0f4950452b9befcf40899d606db9b81fa' and u['all_original_selected_bytes_roundtrip'] and u['exit']==0 and u['archive']['members']==9091
p=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py');assert H(p)=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762';sp=importlib.util.spec_from_file_location('cap',p);c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c)
assert shutil.disk_usage('/workspace').free>u['archive']['bytes']+32*1024*1024
O.mkdir();env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONOPTIMIZE',None);r=c.Recorder(O,env,F)
def git(*args):
 row,out,err=r.run(['git',*args],cwd=R,timeout=None,check=True,source_variant='publish original R5 red and immutable complete U archive');return out.decode().strip()
assert git('rev-parse','HEAD')==BEFORE and git('branch','--show-current')==BR and not git('status','--porcelain=v1') and not git('diff','--name-only',F,BEFORE,'--','.',':(exclude)evidence')
inv=[]
def copy(src,dest,pin=None,size=None):
 src=Path(src);dest=R/dest;assert src.is_file() and not src.is_symlink() and not dest.exists();raw=src.read_bytes();h=hashlib.sha256(raw).hexdigest()
 if pin:assert h==pin
 if size is not None:assert len(raw)==size
 dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);assert H(dest)==h;inv.append({'path':str(dest.relative_to(R)),'source':str(src),'bytes':len(raw),'sha256':h})
def tree(src,dest):
 src=Path(src);assert src.is_dir()
 for f in sorted(src.rglob('*')):
  assert not f.is_symlink()
  if f.is_file():copy(f,dest/f.relative_to(src))
copy(S,T/'SUMMARY.json')
for label,x in summary['original_file_bindings'].items():copy(x['path'],T/'original-terminal'/(label+'.json'),x['sha256'],x['bytes'])
for label,src in [('launch-five','/workspace/geo323-final-r5-stage-tools-20261024/launch-five'),('outer-five','/workspace/geo323-final-r5-stage-tools-20261024/outer-five'),('required-ci','/workspace/geo337-R-current-required-ci-20261024'),('ledger-freshness','/workspace/geo337-R-ledger-freshness-20261024'),('recorder-v5-originals','/workspace/geo323-recorder-fidelity-v5-draft-20261024')]:tree(src,T/label)
for name,pin in [('R5_TERMINAL_CI_LEDGER_ACTUAL_PEER.json','2858b10f5423560a5110a33d1101f8a39f797fa06a98618d627999978cc3bd98'),('GEO323_RECORDER_V5_STATIC_AND_SELFTEST_PEER.json','625dec7bd40c137981aac2a4366e6a91b69d2726f8ca4a0a08a9e84a2dc3153c')]:copy(Path('/workspace/train337-canvas-peer-resume')/name,T/'peer'/name,pin)
copy(UP,A/'PACKAGE.json');copy('/workspace/train337-canvas-peer-resume/U_FULL_FIVE_STAGE_ACTUAL_PACKAGE_PEER.json',A/'U_FULL_FIVE_STAGE_ACTUAL_PACKAGE_PEER.json','96769065c4e8b5e8092d7c76370c8569ccec8c2c671268253701d9f3e6286930');copy('/workspace/train337-canvas-peer-resume/review_U_full_package_actual.py',A/'review_U_full_package_actual.py')
tree('/workspace/geo323-union-full-collection-20261024/execution',A/'collector-outer')
archive=Path(u['archive']['path']);target=R/A/archive.name;assert not target.exists() and archive.is_file() and not archive.is_symlink();assert archive.stat().st_size==u['archive']['bytes'] and H(archive)==u['archive']['sha256'];before=archive.stat()
# Publish an additional immutable pathname without duplicating the archive payload.
os.link(archive,target);after=archive.stat();assert (after.st_dev,after.st_ino)==(target.stat().st_dev,target.stat().st_ino) and after.st_nlink==before.st_nlink+1
alias={'scope':'exact immutable U archive only; no raw content deletion or edit','sha256':u['archive']['sha256'],'bytes':u['archive']['bytes'],'paths':[str(archive),str(target)],'device':after.st_dev,'inode':after.st_ino,'links_before':before.st_nlink,'links_after':after.st_nlink,'reuse_rule':'Before either pathname is overwritten, delink every registered alias into independent inodes; never mutate the shared payload in place.'}
c.dump(R/A/'IMMUTABLE_ALIAS_REGISTRY.json',alias);c.dump(Path('/workspace/ROOT_U_ARCHIVE_IMMUTABLE_ALIAS_REGISTRY_20261024.json'),alias)
inv.append({'path':str(target.relative_to(R)),'source':str(archive),'bytes':after.st_size,'sha256':u['archive']['sha256'],'immutable_hardlink':True});copy(__file__,T/Path(__file__).name)
c.dump(R/T/'PUBLICATION_INVENTORY.json',{'product_source':F,'previous_evidence_head':BEFORE,'R5_full_raw_archive_published':False,'U_full_raw_archive_included':True,'U_source':u['source_sha'],'files':inv})
p=R/B/'PROGRESS.md';t=p.read_text();start=t.index('## 唯一 current-state');end=t.index('### 前輪 U 終態與歷史矩陣',start)
current='''## 唯一 current-state（2026-10-24；R5 正式五階段已終態）

當前產品／架構產物來源 **R=`a22df116c7e9f6b7d074451f1c8052d59e7e4f3e`**。它已一般合入排序修正與9個Reading A架構guard；後續純證據提交不改受測來源。R5在獨立乾淨R checkout以v5收件工具執行原prepare/build/compare/perf/profile各一次，execution=0/0/1/0/0、CLI=0/0/1/1/1，outer1，雙鎖已正常釋放。**N64 fix/main=1.3369644933292553>1.3仍紅**；small-N fix/base16/32/48=0.9903333938/0.8627250817/0.7692726791均綠；source calls82668/364369比4.4076184255≤4.5綠。原36樣本全保、不重抽、不放寬門檻。

compare完成175 scenes/350 runs，仍於原verify_linux.py:156正常assert1，三個stdout差為role_priority與P8低／高凹角。原ABC_result缺席、all_required_stages_completed=false、full_acceptance_passed=null；不能把比較前段graph／guards相同冒作後段audit或完整八stage通過。新R完整native、六browser、P52/Q38/§7/P189、required-eight/PF3、reader/ReadingA與全帳本尚未跑。

R的tracked帳本check已在同非evidence tree的physical E39a執行1：123筆、120stale／3retired／0invalid，原件在current-R5-status/ledger-freshness。源碼仍需修性能，root待穩定來源整份生成，不讓子代理各自重產。架構三原裁判及四檔生成真執行於b9c9fb818f031828530994a4d66f1976da0d8138：0/0/0、205/18零skip、604inputs與九組guard反證0/1/0；R只採非執行性report／receipt。原件已公開architecture-b9-complete，不移標執行SHA。

最新CI原讀：R的run40063478544與當時E39a的run40063689734，各7個job均failure／steps=[]，annotation明載付款失敗或支出上限未啟動；另有Ubuntu label notice。沒有修改付款／required checks或取得正式替代接受，B3仍未解除；這不是產品程式執行失敗或成功。新純證據head的CI不以這兩run冒充。

v5只恢復原subprocess.run PIPE並把性能收據落盤延至原perf返回後，原judge、36樣本、timer、timeout、門檻都未改；48合成契約及兩組0/1/0、87/0peer完整公開於current-R5-status/recorder-v5-originals。R5終態／CI／check原件及671/0獨審已同批公開，但R5完整graph／gprof／所有command原件仍在雲端待完整封包。上一輪U五stage完整9091member原包（31,361,891B，SHAa276bd4f…）本次已公開於full-U-five-stage-raw，50331/0獨審；包內原published:false保收件時間，發布事實由本提交另證。沒有用U包代R5原流。

排序修正Saa16的35方法、332compile/link與整刀128→896→128／四細控制真0/1/0已完整合入evidence/geo343-monotonic-aa16e73d；實跑來源仍Saa16。下一刀由W owner針對17,741,288次plane_compare尋因，K僅做觀察儀表、不並改產品策略。原三診斷版本界線與CI限制照QUESTIONS保留。**尚未READY-TO-MERGE；所有原skip、斷言、golden、時限均未放寬。**

'''
t=t[:start]+current+t[end:];p.write_text(t)
q=R/B/'QUESTIONS.md';q.write_text(q.read_text()+'''\n\n### R5 本輪原判補記\n\nR=a22df116c7e9f6b7d074451f1c8052d59e7e4f3e，v5原36樣本N64/main=1.3369644933292553>1.3，屬繼續自主修正的性能缺陷；其餘小N與sourcecalls目標綠不解除它。跨版本compare仍同三個I22 stdout差，未改原裁判或刪新版必要診斷，既有版本界線待決仍有效。最新R／E39a required CI原run40063478544／40063689734明為帳戶付款或支出上限未啟動，不能自行將它們標綠。完整R5未封包與未跑正式項明列PROGRESS，沒有要求使用者停下回覆。\n''')
git('add','-f','--sparse',str(T),str(A),str(B/'PROGRESS.md'),str(B/'QUESTIONS.md'));assert all(x in [str(B/'PROGRESS.md'),str(B/'QUESTIONS.md')] or x.startswith(str(T)+'/') or x.startswith(str(A)+'/') for x in git('diff','--cached','--name-only').splitlines())
git('diff','--cached','--check','--',str(B/'PROGRESS.md'),str(B/'QUESTIONS.md'),str(T/'PUBLICATION_INVENTORY.json'),str(T/Path(__file__).name));git('commit','-m','docs: publish current performance failures and complete union raw evidence');head=git('rev-parse','HEAD');git('push','origin','HEAD:'+BR)
assert git('ls-remote','origin','refs/heads/'+BR).split()[0]==head and not git('status','--porcelain=v1') and not git('diff','--name-only',F,head,'--','.',':(exclude)evidence')
c.dump(O/'RESULT.json',{'product_source':F,'previous_evidence_head':BEFORE,'evidence_head':head,'published':True,'push_exit':0,'U_archive_published':True,'U_archive_sha256':u['archive']['sha256'],'R5_full_archive_published':False,'R5_original_outer_exit':1,'files':len(inv),'bytes':sum(x['bytes'] for x in inv),'new_immutable_alias_registry':str(R/A/'IMMUTABLE_ALIAS_REGISTRY.json')});print((O/'RESULT.json').read_text())
