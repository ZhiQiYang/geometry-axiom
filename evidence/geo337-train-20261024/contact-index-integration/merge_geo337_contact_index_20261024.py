from pathlib import Path
import hashlib,importlib.util,json,os,shutil
R=Path('/workspace/geometry-axiom');O=Path('/workspace/geo337-contact-index-integration-20261024')
B=Path('evidence/geo337-train-20261024');T=B/'contact-index-integration'
BEFORE='2787ee3167deec7588bde26265152bcf6dc4a939';OTHER='a934a554ae58f16f124f1b264523947f170b3f0b'
BRANCH='codex/train-337-continue-20261024'
cp=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert hashlib.sha256(cp.read_bytes()).hexdigest()=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
spec=importlib.util.spec_from_file_location('cap',cp);c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
O.mkdir();env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',GIT_OPTIONAL_LOCKS='0');env.pop('PYTHONOPTIMIZE',None)
rec=c.Recorder(O,env,BEFORE)
def git(*args):
 row,out,err=rec.run(['git',*args],cwd=R,timeout=None,check=False,source_variant='normal-contact-index-integration')
 assert row['actual_process_returncode']==0,(args,err)
 return out.decode().strip()
assert git('rev-parse','HEAD')==BEFORE and git('branch','--show-current')==BRANCH
assert not git('status','--porcelain=v1','--untracked-files=all')
git('merge-base','--is-ancestor','df230da57619e437c30527dbede8c67fd0ec6b50',OTHER)
git('merge','--no-ff','--no-commit',OTHER)
assert not git('diff','--name-only','--diff-filter=U')
for path in ('geometry-core/kernel/source.c','tests/geo261_source_index_harness.c','tests/test_geo261_source_index.py','tests/mutants_results.json'):
 assert git('hash-object',path)==git('rev-parse',BEFORE+':'+path),path
for path in git('diff','--cached','--name-only').splitlines():
 if path.startswith(('evidence/','tests/','geometry-core/domain-decoupling/')):continue
 assert path=='geometry-templates/woodworking/native/contact_world.c',path
rows=json.loads((R/'tests/run_all.expected.json').read_text());rows=rows.get('suites',rows)
expected={'py:test_geo261_source_index':17,'py:test_geometry_host_sources':45,'py:test_rectangular_template':13,'py:test_geo261_wood_contact_world':12}
for name,count in expected.items():assert rows[name]['count']==count,(name,rows.get(name))
target=R/T;target.mkdir();shutil.copyfile(__file__,target/Path(__file__).name)
c.dump(target/'SOURCE_BINDING.json',{'previous_head':BEFORE,'merged_evidence_head':OTHER,'contact_execution_sha':'ccfaf057088a80c7aad4049f1c67e5eedfc2fdec','q38_evidence_head':'df230da57619e437c30527dbede8c67fd0ec6b50','counts':expected,'excluded_work_lines':['capacity512','cut-list-storage','panel-empty-rows'],'limits':['Whole active-compaction cost audit pending','New integration performance unrun','Final ledger and architecture pending','Existing results retain execution SHA']})
progress=R/B/'PROGRESS.md';s=progress.read_text();needle='**新來源尚未通過最終帳本、架構或整套驗收，也沒有新的效能結論。**';assert s.count(needle)==1
s=s.replace(needle,'本輪再一般 merge #343 `a934a554ae58f16f124f1b264523947f170b3f0b`，只納入同 load 路徑的 contact index／穩定排序及其祖先 #341、#342；容量 512、cut-list storage 與 panel empty-row 仍留後續分支。#343 原 34 方法／64 控制、318 compile 的實跑頭為 `ccfaf057088a80c7aad4049f1c67e5eedfc2fdec`，#342 原 44 案也保原 SHA；組合後效能及 #341 整段成本審查仍待，不以既有單元結果宣稱達標。tracked 帳本保 root 原 L 版本，檢查曾因新 source.c／測試閉包得到 120 stale／3 retired，最後固定來源後由 root 整份重產。詳見 `contact-index-integration/`。\n\n'+needle,1)
progress.write_text(s)
git('add','-f','--sparse',str(T),str(B/'PROGRESS.md'))
git('diff','--cached','--check','--',str(T),str(B/'PROGRESS.md'),'geometry-templates/woodworking/native/contact_world.c','tests/run_all.expected.json')
git('commit','-m','Merge verified contact indexing prerequisites into integration train')
head=git('rev-parse','HEAD');assert git('rev-list','--parents','-n','1',head).split()==[head,BEFORE,OTHER]
git('push','origin','HEAD:'+BRANCH);assert git('ls-remote','origin','refs/heads/'+BRANCH).split()[0]==head
assert not git('status','--porcelain=v1','--untracked-files=all')
c.dump(O/'RESULT.json',{'previous_head':BEFORE,'merged_head':OTHER,'integration_head':head,'published':True,'push_exit':0,'capacity_512_excluded':True,'product_performance_unrun':True})
print((O/'RESULT.json').read_text())
