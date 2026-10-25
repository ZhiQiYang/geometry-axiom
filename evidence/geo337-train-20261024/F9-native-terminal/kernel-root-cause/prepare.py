from pathlib import Path
import ast,difflib,hashlib,json,subprocess,time
P=Path(__file__).parent;REPO='/workspace/geometry-axiom';F9='4f8a794f4167c3562eb182045102e86e9e37cca9';BASE='4b665fae21ab63aaffb7d84f6a32d5a469ba1675';I24='32f42e3d991c7d2d916d21bfe8ac5d3dd0f9b131';GENERIC='81b6c388f8b73e9aaf885b1d948e5f306b77bafd';EDGE='9430bae568feb98805072930c92f9a03a1250d4e';commands=[]
def H(b):return hashlib.sha256(b).hexdigest()
def git(*args):
 argv=['git','-c','gc.auto=0','-c','maintenance.auto=false',*args];n=len(commands)+1;d=P/'original-git'/f'{n:03}';d.mkdir(parents=True);start=time.time();r=subprocess.run(argv,cwd=REPO,capture_output=True);(d/'stdout.bin').write_bytes(r.stdout);(d/'stderr.bin').write_bytes(r.stderr);z={'command':argv,'cwd':REPO,'started_epoch':start,'ended_epoch':time.time(),'exit_code':r.returncode,'stdout_sha256':H(r.stdout),'stderr_sha256':H(r.stderr),'directory':str(d)};commands.append(z);assert r.returncode==0,z;return r.stdout
source=git('show',F9+':tests/test_geo314_commit_paths.py');(P/'test_geo314_commit_paths.F9.original.py').write_bytes(source)
changed=git('diff','--name-only','--no-renames',BASE,F9,'--','geometry-core/kernel');assert changed==b'geometry-core/kernel/source.c\n'
initial=git('diff','--name-only','--no-renames',BASE,I24,'--','geometry-core/kernel');assert initial==b''
selected=git('diff','--name-only','--no-renames',BASE,'3b0b634feb54266700cc61f26c34d7aeac4c0314','--','geometry-core/kernel');assert selected==b''
current=git('diff','--name-only','--no-renames',GENERIC,F9,'--','geometry-core/kernel');assert current==b''
for sha in [I24,GENERIC,EDGE]:git('merge-base','--is-ancestor',sha,F9)
for sha in [I24,EDGE,GENERIC,'f61413ba785b67d2f455e4977e8b8da06050d654']:git('show','--format=fuller','--stat',sha)
delta=git('diff','--full-index','--no-renames',BASE,F9,'--','geometry-core/kernel');(P/'ACTUAL_F9_KERNEL_DELTA.diff').write_bytes(delta)
log=git('log','--format=%H %s','--reverse',BASE+'..'+F9,'--','geometry-core/kernel');assert [l.split(b' ',1)[0].decode() for l in log.splitlines()]==[EDGE,GENERIC]
for sha in [BASE,GENERIC,F9]:git('ls-tree','-r','-z',sha,'--','geometry-core/kernel')
old=source.decode();new=old.replace('INTEGRATION_BASE = "'+BASE+'"','''INTEGRATION_BASE = "'''+BASE+'''"
# The original I24 implementation must remain kernel-neutral. Later train
# work may adopt separately reviewed generic K changes; pin its complete K
# tree instead of exempting source.c or accepting arbitrary future edits.
I24_IMPLEMENTATION_HEAD = "'''+I24+'''"
# 9430bae568feb98805072930c92f9a03a1250d4e: reuse a missing edge's slot.
# 81b6c388f8b73e9aaf885b1d948e5f306b77bafd: generic provider hint bucket.
GENERIC_SOURCE_INDEX_KERNEL_HEAD = "'''+GENERIC+'''"''',1)
oldmethod='''    def test_kernel_has_no_changes_against_the_fixed_integration_base(self):
        changed = subprocess.run(["git", "diff", "--name-only", INTEGRATION_BASE, "--", "geometry-core/kernel"],
                                 cwd=ROOT, capture_output=True, text=True, check=True)
        added = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "--", "geometry-core/kernel"],
                               cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertEqual("", changed.stdout + added.stdout, "I24 submission policy must not change K files")
'''
newmethod='''    def test_kernel_has_no_changes_against_the_fixed_integration_base(self):
        introduced = subprocess.run(
            ["git", "diff", "--name-only", "--no-renames", INTEGRATION_BASE,
             I24_IMPLEMENTATION_HEAD, "--", "geometry-core/kernel"],
            cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertEqual("", introduced.stdout, "original I24 implementation must not change K files")
        changed = subprocess.run(
            ["git", "diff", "--name-only", "--no-renames", GENERIC_SOURCE_INDEX_KERNEL_HEAD,
             "--", "geometry-core/kernel"],
            cwd=ROOT, capture_output=True, text=True, check=True)
        added = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "--", "geometry-core/kernel"],
                               cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertEqual("", changed.stdout + added.stdout,
                         "I24 submission policy must not change K files outside the exact reviewed generic K tree")
'''
assert old.count(oldmethod)==1;new=new.replace(oldmethod,newmethod,1);ast.parse(new)
(P/'test_geo314_commit_paths.proposed.py').write_text(new)
patch=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/tests/test_geo314_commit_paths.py',tofile='b/tests/test_geo314_commit_paths.py'))
(P/'PROPOSED.patch').write_text(patch)
# Verify proposal changes only constants and the single targeted source contract;
# every other test/method body and number remains byte/AST-identical.
a=ast.parse(old);b=ast.parse(new)
def functions(t):return {(getattr(n,'name',''),x.name):ast.dump(x,include_attributes=False) for n in t.body if isinstance(n,ast.ClassDef) for x in n.body if isinstance(x,ast.FunctionDef)}
afunc,bfunc=functions(a),functions(b);target=('Geo314CommitPaths','test_kernel_has_no_changes_against_the_fixed_integration_base');assert set(afunc)==set(bfunc);assert all(afunc[k]==bfunc[k] for k in afunc if k!=target)
report={'schema':'F9-geo314-kernel-scope-rootcause-and-unapplied-patch/1','analysis_exit':0,'source_sha':F9,'classification':'test scope defect after unrelated generic K changes; not environment and not I24 semantics in K','exact_assertion':'self.assertEqual("", changed.stdout + added.stdout, "I24 submission policy must not change K files")','assertion_source':'tests/test_geo314_commit_paths.py:261','exact_observed_git_delta':changed.decode(),'frozen_old_base':BASE,'original_I24_commit':I24,'user_selected_I24_head':'3b0b634feb54266700cc61f26c34d7aeac4c0314','generic_kernel_commits':[EDGE,GENERIC],'generic_kernel_snapshot':GENERIC,'original_I24_kernel_diff_empty':True,'user_selected_I24_kernel_diff_empty':True,'generic_snapshot_F9_kernel_diff_empty':True,'patch_applied':False,'tests_or_mutants_executed':False,'source_or_branch_modified':False,'new_tests_count_changed':False,'all_other_test_method_AST_equal':True,'original_source_sha256':H(source),'proposed_source_sha256':H(new.encode()),'patch_sha256':H(patch.encode()),'commands':commands,'remaining_required':['root/another peer must review proposal; no acceptance inferred from AST parse','after full F9 red collection, apply only in the new correction source, not the frozen F9','run original method old/fixed/restored on independent same-source checkouts for exact 1/0/0 evidence; separately require fixed/withdrawn/fixed 0/1/0','prove extra edit in source.c, another K file, staged new K file and untracked K file each still red then restored green','retain original historical I24 zero-K assertion; add a synthetic I24 K-change negative if the guard implementation is exercised in fixtures','mutate.py --check after test change; if stale regenerate whole final ledger once with all fixes; refresh architecture closure per rules','run affected full native and any additional gates whose closure changed; never relabel completed F9 runs']}
(P/'RESULT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'analysis_exit':0,'patch_applied':False,'test_method_count':sum(k[1].startswith('test_') for k in afunc),'kernel_delta':changed.decode(),'patch_sha256':H(patch.encode())}))
