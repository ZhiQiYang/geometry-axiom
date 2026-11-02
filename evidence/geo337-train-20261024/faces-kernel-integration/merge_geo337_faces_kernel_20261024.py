from pathlib import Path
import hashlib,importlib.util,json,os,shutil
R=Path('/workspace/geometry-axiom'); O=Path('/workspace/geo337-faces-kernel-integration-20261024')
B=Path('evidence/geo337-train-20261024');T=B/'faces-kernel-integration'
BEFORE='caf6c9ca7286b2ab83ec3ab767690a22a1227064'
OTHER='8f39025be6708bd9d58e576ed5b349b7ef628624'
BRANCH='codex/train-337-continue-20261024'
cp=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert hashlib.sha256(cp.read_bytes()).hexdigest()=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
spec=importlib.util.spec_from_file_location('cap',cp);c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
peer=Path('/workspace/geo340-339-convergence-evidence-peer-20261024/actual-publication/REVIEW.json')
assert hashlib.sha256(peer.read_bytes()).hexdigest()=='d8e39909a53af70cdb4f34afb6247a68f7634c6a5c1171d87e98e95f5abe80ef'
O.mkdir();env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',GIT_OPTIONAL_LOCKS='0');env.pop('PYTHONOPTIMIZE',None)
rec=c.Recorder(O,env,BEFORE)
def git(*args):
 row,out,err=rec.run(['git',*args],cwd=R,timeout=None,check=False,source_variant='normal-faces-kernel-integration')
 assert row['actual_process_returncode']==0,(args,err)
 return out.decode().strip()
assert git('rev-parse','HEAD')==BEFORE and git('branch','--show-current')==BRANCH
assert not git('status','--porcelain=v1','--untracked-files=all')
git('merge-base','--is-ancestor','175cee44c56c89871803d955c0c525236727ba65',OTHER)
git('merge','--no-ff','--no-commit',OTHER)
assert not git('diff','--name-only','--diff-filter=U')
for path in ('geometry-core/kernel/source.c','tests/geo261_source_index_harness.c','tests/test_geo261_source_index.py'):
 assert git('hash-object',path)==git('rev-parse',BEFORE+':'+path)
counts=json.loads((R/'tests/run_all.expected.json').read_text())
rows=counts.get('suites',counts)
assert rows['py:test_geo261_source_index']['count']==17
assert rows['py:test_geometry_host_sources']['count']==45
assert rows['py:test_rectangular_template']['count']==13
target=R/T;target.mkdir()
shutil.copyfile(peer,target/'SOURCE_PUBLICATION_REVIEW.json');shutil.copyfile(__file__,target/Path(__file__).name)
c.dump(target/'SOURCE_BINDING.json',{'previous_head':BEFORE,'merged_evidence_head':OTHER,'faces_source':'616ce7538d23fbe7f3bbefae7f2a04e25ebd75a4','kernel_source':'175cee44c56c89871803d955c0c525236727ba65','method_counts':{'source_index':17,'host_sources':45,'rectangular_template':13},'kernel_original_aggregate_exit':0,'kernel_original_aggregate_count':13,'faces_original_142_execution_sha':'38da31bcac91db631e6325e40b228f8604810e82','limits':['Prior evidence retains original execution SHA','No final-union tests or performance claimed','Final union ledger and architecture pending']})
progress=R/B/'PROGRESS.md';s=progress.read_text();needle='**新來源尚未通過最終帳本、架構或整套驗收，也沒有新的效能結論。**'
assert s.count(needle)==1
s=s.replace(needle,'已再一般 merge #339 證據頭 `8f39025be6708bd9d58e576ed5b349b7ef628624`（含 #340）。#340 原 strict aggregate 13／13、exit0 已公開；#339 舊 F38 的 142 方法／三組反證保原 execution SHA，與新 F616 的 498 項 executable closure 全等收據已公開。合流保留核心新 17 方法、host 45、rectangle 13；這些定向結果不冒作合流後完整驗收。詳見 `faces-kernel-integration/`。\n\n'+needle,1)
progress.write_text(s)
git('add','-f','--sparse',str(T),str(B/'PROGRESS.md'))
git('diff','--cached','--check','--',str(T),str(B/'PROGRESS.md'),'tests/run_all.expected.json','geometry-templates/woodworking/geometry_woodworking/model_sources.py','tests/test_geometry_host_sources.py','tests/test_rectangular_template.py')
git('commit','-m','Merge verified faces and kernel isolation work into integration train')
head=git('rev-parse','HEAD');assert git('rev-list','--parents','-n','1',head).split()==[head,BEFORE,OTHER]
git('push','origin','HEAD:'+BRANCH)
assert git('ls-remote','origin','refs/heads/'+BRANCH).split()[0]==head
assert not git('status','--porcelain=v1','--untracked-files=all')
c.dump(O/'RESULT.json',{'previous_head':BEFORE,'merged_head':OTHER,'integration_head':head,'published':True,'push_exit':0,'final_union_unfixed':True})
print((O/'RESULT.json').read_text())
