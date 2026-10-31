"""Generate one minimal after-FF gate runner; do not touch any source or ref."""
from pathlib import Path
import ast,difflib,hashlib,json
HERE=Path(__file__).parent
OLD=Path('/tmp/geo337-a6-architecture-preparation-20261026/run_original_gates.py')
OLD_PIN='51e25963f5ede37b2fe516b14862cf73b895c9780fad62d4083ec56109a9962f'
SHARED=OLD.with_name('prepare_source.py')
SHARED_PIN='8f08d1325d5fa43fef2c3a46ef8bca94693568d7318b1c1326496c44c48fee16'
def h(b):return hashlib.sha256(b).hexdigest()
original=OLD.read_bytes();assert h(original)==OLD_PIN and h(SHARED.read_bytes())==SHARED_PIN
s=original.decode()
def replace(old,new):
 global s
 assert s.count(old)==1,old
 s=s.replace(old,new)
replace('import prepare_source as shared',f"""SHARED=Path({str(SHARED)!r})
if hashlib.sha256(SHARED.read_bytes()).hexdigest()!={SHARED_PIN!r}:raise RuntimeError('original shared helper pin')
spec=importlib.util.spec_from_file_location('original_a6_source_helpers',SHARED);shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)""")
replace("SOURCE=shared.SOURCE;ROOT=shared.ROOT;OWN=shared.OWN;OUT=OWN/'a6-architecture-gates-original-20261026'", """PREPARED_SOURCE=shared.SOURCE
SOURCE='cbf0fb621888596aa14ad5f2349b503e23b1b72d'
ROOT=shared.ROOT;OWN=shared.OWN;OUT=OWN/'F-final-light-gates-original-20261026'
CHANGED={'tests/mutants_results.json','geometry-core/domain-decoupling/PRODUCT-ARCHITECTURE.md','geometry-core/domain-decoupling/product-architecture-receipt.json'}""")
replace("JUDGES=[[", "JUDGES=[['tests/mutate.py','--check'],[")
replace("'PLAN_ONLY: actual a6 three architecture judges, source untouched'", "'PLAN_ONLY: after root-recorded ordinary FF only; actual final tracked check and three architecture judges'")
replace("need(q['source_sha']==SOURCE and q['root_execution_lease']is True,'explicit actuala6 source lease')", """need(q['schema']=='final-after-ff-four-light-gates/1' and q['source_sha']==SOURCE and q['prepared_source_sha']==PREPARED_SOURCE and q['root_execution_lease']is True and q['root_source_exclusive']is True and q['root_adoption_actual_peer_reviewed']is True,'explicit final execution and historical source binding')
 adopted=pinned(q['adoption_result'])
 need(adopted['exit_code']==0 and adopted['final_sha']==SOURCE and adopted['source_sha']==PREPARED_SOURCE and adopted['ledger_execution_sha']==shared.S10 and adopted['architecture_execution_sha']==PREPARED_SOURCE and adopted['published']is True and adopted['delivered']is True and adopted['remote_commit_resolved']is True and adopted['historical_publisher_unchanged']is True and adopted['old_repo_changed']is False and set(adopted['changed_paths'])==CHANGED,'actual published exact-three-leaf final adoption')
 need(adopted['candidate_branch']=='codex/train337-recovered-evidence-20261026' and adopted['other_product_test_ssot_unchanged']is True and adopted['manifest_scan_byte_unchanged']is True,'fixed candidate and source closure')""")
replace("prepared['source_sha']==SOURCE", "prepared['source_sha']==PREPARED_SOURCE")
replace("peer['source_sha']==SOURCE", "peer['source_sha']==PREPARED_SOURCE")
replace("'actual newsource peer binding'", "'actual a6 preparation peer binding; never relabelled as F'")
replace("source_variant='a6 architecture original identity'", "source_variant='final four light gates: source preparation remains a6; actual checkout is F'")
replace("'exact clean actuala6 source'", "'exact clean final source after root-recorded FF'")
replace("result={'source_sha':SOURCE,", "result={'source_sha':SOURCE,'prepared_source_sha':PREPARED_SOURCE,'native_source_claimed':False,'source_selected_count':3763,")
replace("  try:\n   before=state();sources=snapshot();", """  def publisher_state():
   # Read protected metadata only; never run Git against the publisher with the
   # source's private index override. The candidate ref is already final.
   result={}
   for owner in [shared.OWNER,Path('/workspace/geometry-axiom')]:
    base=owner/'.git';need(base.is_dir()and not base.is_symlink(),'protected physical Gitdir')
    paths=[base/'HEAD',base/'index',base/'config']
    for rel in ['packed-refs','objects/info/alternates']:
     if (base/rel).exists():paths.append(base/rel)
    paths+=sorted(p for p in (base/'refs').rglob('*')if p.is_file())
    rows={}
    for p in paths:
     st=p.lstat();need(stat.S_ISREG(st.st_mode)and not p.is_symlink(),'protected metadata regular')
     rows[str(p.relative_to(base))]={'sha256':H(p.read_bytes()),'device':st.st_dev,'inode':st.st_ino,'mode':st.st_mode,'bytes':st.st_size,'mtime_ns':st.st_mtime_ns}
    result[str(owner)]=rows
   return result
  def selected_inventory():
   selected={os.fsdecode(x[2:])for x in git('ls-files','-t','-z').split(b'\\0')if x and x[:1]!=b'S'}
   need(selected==set(manifest['files'])and len(selected)==3763,'all original3763 selected leaves retained')
   rows=[]
   for name in sorted(selected):
    p=ROOT/name;st=p.lstat();b=p.read_bytes();oid=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\\0'+b).hexdigest()
    need(stat.S_ISREG(st.st_mode)and st.st_nlink==1 and not p.is_symlink(),'independent selected source '+name)
    mode='100755'if st.st_mode&0o111 else'100644';expected=final_files[name]
    need(oid==expected['oid']and len(b)==expected['bytes']and mode==expected['mode'],'exact final selected bytes '+name)
    if name in manifest['fixture_paths']:need(expected==manifest['files'][name],'five protected fixture identities unchanged')
    rows.append({'path':name,'oid':oid,'raw_sha256':H(b),'mode':mode,'bytes':len(b)})
   need(len(manifest['fixture_paths'])==5,'original five fixtures required')
   return rows
  try:
   publisher_before=publisher_state();dump(OUT/'PUBLISHER.before.json',publisher_before)
   before=state()
   git('merge-base','--is-ancestor',PREPARED_SOURCE,SOURCE)
   changed={os.fsdecode(x)for x in git('diff','--no-renames','--name-only','-z',PREPARED_SOURCE,SOURCE,'--','.',':(exclude)evidence').split(b'\\0')if x}
   need(changed==CHANGED,'exact three non-evidence changes from actual a6 preparation')
   final_files={}
   for raw in git('ls-tree','-r','-l','-z',SOURCE,'--',*sorted(manifest['files'])).split(b'\\0'):
    if not raw:continue
    meta,name=raw.split(b'\\t',1);mode,kind,oid,size=meta.split();need(kind==b'blob'and mode in (b'100644',b'100755'),'regular final selected Git entry')
    final_files[os.fsdecode(name)]={'mode':mode.decode(),'oid':oid.decode(),'bytes':int(size)}
   need(set(final_files)==set(manifest['files']),'complete final selected Git inventory')
   need({n for n in final_files if final_files[n]!=manifest['files'][n]}==CHANGED,'selected delta is only the three adopted leaves')
   for n in CHANGED:need(H((ROOT/n).read_bytes())==adopted['original_artifact_hashes'][n],'byte-exact adopted original '+n)
   selected_before=selected_inventory();dump(OUT/'SELECTED.before.json',selected_before)
   sources=snapshot();""")
replace("['architecture-contract','architecture-unit','product-architecture-unit']", "['tracked-mutation-check','architecture-contract','architecture-unit','product-architecture-unit']")
replace("   after=state();after_sources=snapshot();", """   after=state();after_sources=snapshot();
   selected_after=selected_inventory();dump(OUT/'SELECTED.after.json',selected_after)
   publisher_after=publisher_state();dump(OUT/'PUBLISHER.after.json',publisher_after)
   need(selected_before==selected_after and publisher_before==publisher_after,'selected3763 and historical publisher HEAD/index/refs unchanged during final gates');""")
replace("all_gates_passed=ok,wrapper_exit", "all_gates_passed=ok,publisher_preserved=True,selected_3763_preserved=True,five_fixtures_preserved=True,wrapper_exit")
ast.parse(s)
(HERE/'run_after_ff_four_gates.py').write_text(s)
(HERE/'MINIMAL_DIFF.txt').write_text(''.join(difflib.unified_diff(original.decode().splitlines(True),s.splitlines(True),fromfile=str(OLD),tofile='run_after_ff_four_gates.py')))
(HERE/'PINS.json').write_text(json.dumps({'historical_runner':{'path':str(OLD),'sha256':OLD_PIN},'shared_helper':{'path':str(SHARED),'sha256':SHARED_PIN},'candidate_runner':{'path':str(HERE/'run_after_ff_four_gates.py'),'sha256':h(s.encode())},'formal_execution_performed':False},indent=2)+'\n')
print(json.dumps({'prepared_bytes':len(s.encode()),'sha256':h(s.encode()),'formal_execution_performed':False}))
