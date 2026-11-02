from pathlib import Path
import hashlib,importlib.util,json,os,shutil
R=Path('/workspace/geometry-axiom');O=Path('/workspace/geo337-U-terminal-publication-20261024');B=Path('evidence/geo337-train-20261024');T=B/'current-U-323-terminal-status'
U='ca7838e0f4950452b9befcf40899d606db9b81fa';BEFORE='76ba3b2dad42f5d68fdd3bbdd7e54f5b0c337c65';BR='codex/train-337-continue-20261024'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
S=Path('/workspace/geo323-union-stage-tools-20261024/TERMINAL_SUMMARY.json');assert sha(S)=='cc1a5ed2d2b0d4513f5e1f2c836f3029e477c3f1b508c1713a1b0839ff9d6588';summary=json.loads(S.read_text());assert summary['source_sha']==U and summary['launcher_exit']==1 and len(summary['raw_locators'])==24
M=Path('/workspace/four-additional-maintenance-publication-preparation-20261024/MANIFEST.json');assert sha(M)=='1dc82d48773bb9ffd399435607f64a2279d024460fcfe9ef3f83185970bc8777';m=json.loads(M.read_text());assert m['expected_head']==BEFORE and len(m['files'])==19
D=Path('/workspace/geo337-U-terminal-docs-preparation-20261024');assert sha(D/'PROGRESS.U-terminal.FROZEN-append.md')=='d077c20e1b6a04a39da050037e83e917ec1c35071419f33a3891ea670ff9acd8';assert sha(D/'QUESTIONS.U-terminal.FROZEN-append.md')=='b4f6369a24dfc9b6a9b81962a04e279fd88c02e029ca48e4c0df8e7a50e754d2'
p=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py');assert sha(p)=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762';sp=importlib.util.spec_from_file_location('cap',p);c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c)
O.mkdir();env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',GIT_OPTIONAL_LOCKS='0');env.pop('PYTHONOPTIMIZE',None);r=c.Recorder(O,env,U)
def git(*args):
 row,out,err=r.run(['git',*args],cwd=R,timeout=None,check=True,source_variant='publish original U terminal red and historical storage receipts');return out.decode().strip()
assert git('rev-parse','HEAD')==BEFORE and git('branch','--show-current')==BR and not git('status','--porcelain=v1')
assert not git('diff','--name-only',U,BEFORE,'--','.',':(exclude)evidence')
inv=[]
def copy(src,dest,expected=None,nbytes=None):
 src=Path(src);dest=R/dest;assert src.is_file() and not src.is_symlink() and not dest.exists();raw=src.read_bytes();h=hashlib.sha256(raw).hexdigest()
 if expected:assert h==expected
 if nbytes is not None:assert len(raw)==nbytes
 dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);assert sha(dest)==h
 inv.append({'source':str(src),'destination':str(dest.relative_to(R)),'bytes':len(raw),'sha256':h})
copy(S,T/'TERMINAL_SUMMARY.json')
for x in summary['raw_locators']:
 src=Path(x['path']);assert str(src).startswith('/workspace/');copy(src,T/'originals'/src.relative_to('/workspace'),x['sha256'],x['bytes'])
for name,h in [('U_FIVE_STAGE_TERMINAL_METADATA_PEER.json','a22c1e5c0ce1f4a3fc6fcd4c0ecf4eec307cf2643861b613c6b30aaa87132627'),('U_FIVE_STAGE_STAGE_ENUM_CORRECTION_PEER.json','5235f1e8db72405e0d50b6284caab42c6caddad7c3856a3a48487963bb45f1d4')]:copy(Path('/workspace/train337-canvas-peer-resume')/name,T/'peer'/name,h)
for x in m['files']:
 assert x['destination'].startswith(m['destination_prefix']+'/');copy(x['source_path'],Path(x['destination']),x['sha256'],x['bytes'])
copy(M,Path(m['destination_prefix'])/'PUBLICATION_MANIFEST.json')
copy(__file__,T/Path(__file__).name)
c.dump(R/T/'PUBLICATION_INVENTORY.json',{'product_source':U,'previous_evidence_head':BEFORE,'terminal_status_only':True,'full_U_raw_archive_published':False,'storage_is_not_U_gate':True,'files':inv})
progress=R/B/'PROGRESS.md';text=progress.read_text();old='**新來源尚未通過最終帳本、架構四檔重產或整套驗收，也沒有新的效能結論。**';assert text.count(old)==1
text=text.replace(old,'**新來源尚未通過最終帳本、架構四檔重產或整套驗收。U 原五 stage 已終態 1：compare 的三個 stdout 差異與 N64 fix/main=1.429347781620555>1.3 仍紅；完整結果見本文末新增 U 終態段落。**',1)
text+= (D/'PROGRESS.U-terminal.FROZEN-append.md').read_text()
text+='\n### 新增四組儲存收據公開\n\n本次另公開 maintenance-additional-four-archive-groups/：28 個原 archive 路徑與內容保留，四組 hardlink 維護原 exit0；原件包 359949B／1597 members，SHA256 e85764f616d5801a9fa13e23ea56cbfdaf32d8ccc203b1b0f48012c423bd31b6。完整收件原流與獨審 6417／0、alias registry 及其 77／0 另列；這是磁碟保全，不是 U 產品 gate。後續若要寫入任一共享副本，必須先解除該組全部 hardlink。\n'
progress.write_text(text)
q=R/B/'QUESTIONS.md';q.write_text(q.read_text()+(D/'QUESTIONS.U-terminal.FROZEN-append.md').read_text())
git('add','-f','--sparse',str(T),m['destination_prefix'],str(B/'PROGRESS.md'),str(B/'QUESTIONS.md'))
allowed=[str(T)+'/',m['destination_prefix']+'/'];assert all(x in [str(B/'PROGRESS.md'),str(B/'QUESTIONS.md')] or any(x.startswith(a) for a in allowed) for x in git('diff','--cached','--name-only').splitlines())
git('diff','--cached','--check','--',str(B/'PROGRESS.md'),str(B/'QUESTIONS.md'),str(T/'PUBLICATION_INVENTORY.json'),str(T/Path(__file__).name))
git('commit','-m','docs: publish union performance failures and preserved storage receipts');head=git('rev-parse','HEAD');git('push','origin','HEAD:'+BR)
assert git('ls-remote','origin','refs/heads/'+BR).split()[0]==head and not git('status','--porcelain=v1') and not git('diff','--name-only',U,head,'--','.',':(exclude)evidence')
c.dump(O/'RESULT.json',{'product_source':U,'previous_evidence_head':BEFORE,'evidence_head':head,'published':True,'push_exit':0,'terminal_status_only':True,'full_U_raw_archive_published':False,'original_launcher_exit':1,'files':len(inv),'bytes':sum(x['bytes'] for x in inv),'storage_archive_sha256':'e85764f616d5801a9fa13e23ea56cbfdaf32d8ccc203b1b0f48012c423bd31b6'})
print((O/'RESULT.json').read_text())
