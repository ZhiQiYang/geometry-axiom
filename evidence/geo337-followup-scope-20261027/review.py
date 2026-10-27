from pathlib import Path
import hashlib,json,shutil,subprocess,tarfile
OUT=Path(__file__).parent;ROOT=Path('/workspace/geo337-native-F-cbf0fb62');F='cbf0fb621888596aa14ad5f2349b503e23b1b72d';F8='75a1e93811a52b69385cbdaf6a09d773ed9052ad'
def h(b):return hashlib.sha256(b).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
native=Path('/workspace/scratch/geo337-native-F-cbf0fb62-20261027-r2')
summary=json.loads((native/'SUMMARY.json').read_text());assert summary['sha']==F and summary['actual_exit']==0 and not summary['timed_out']
reuse=OUT/'geo314';reuse.mkdir(exist_ok=True)
names=['test_geo261_native_grid_product','test_geo261_wood_grid_application','test_geo314_commit_paths','test_geo314_ordered_facts','test_geo314_stagger_commit','test_grid_inspector_contract']
stdout=(native/'stdout.bin').read_text();rows=[s for s in stdout.splitlines() if any(s.startswith('py:'+n+' ') for n in names)];assert len(rows)==6
assert all(int(s.split()[1])==int(s.split()[2]) and s.split()[3:5]==['0','0'] for s in rows)
members={}
with tarfile.open(native/'native-output.original.tar.gz') as tar:
 for m in tar:
  if m.isfile() and (m.name.endswith('/node_tests-js.log') or any(m.name.endswith('/py_'+n+'.log') for n in names) or 'mutation-freshness' in m.name):
   data=tar.extractfile(m).read();p=reuse/Path(m.name).name;p.write_bytes(data);members[m.name]={'file':p.name,'bytes':len(data),'sha256':h(data)}
assert (reuse/'node_tests-js.log').exists() and all((reuse/('py_'+n+'.log')).exists() for n in names)
node=(reuse/'node_tests-js.log').read_text();inspector=[s for s in node.splitlines() if '✔ GEO263_' in s];assert len(inspector)==12
shutil.copy2(native/'SUMMARY.json',reuse/'NATIVE_SUMMARY.original.json')
ledger=(ROOT/'tests/mutants_results.json').read_bytes();(reuse/'mutants_results.original.json').write_bytes(ledger);record=json.loads(ledger)['M121'];execution=record['execution'];assert record['verdict']=='killed' and execution['byte_restored']
assert [execution[x]['exit_code'] for x in ['baseline','mutant','restored']]==[0,1,0]
assert all(execution[x]['exit_code']==0 and not execution[x]['timed_out'] for x in ['baseline_build','mutant_build','restored_build'])
assert len(execution['methods'])==2
for stage in ['baseline','mutant','restored']:
 result=execution[stage]['result'];assert not result['errors'] and not result['skipped'] and not execution[stage]['timed_out']
 assert len(result['failures'])==(1 if stage=='mutant' else 0)
archive=ROOT/'evidence/geo337-train-20261024/S10-recovered-originals-20261026/ledger-package/complete-original-commands-and-streams.tar.gz'
m121=reuse/'M121-original-streams';m121.mkdir(exist_ok=True);stream_rows=[]
with tarfile.open(archive) as tar:
 for stage in ['baseline_build','baseline','mutant_build','mutant','restored_build','restored']:
  r=execution[stage]
  parent=('original-cache-metadata-and-streams/_bridge-baseline/'+execution['head']) if stage.startswith('baseline') else 'original-cache-metadata-and-streams/M121'
  for stream in ['stdout','stderr']:
   member=parent+'/'+r[stream+'_file'];data=tar.extractfile(member).read();assert h(data)==r[stream+'_sha256'];dest=m121/(stage+'.'+stream);dest.write_bytes(data);stream_rows.append({'stage':stage,'stream':stream,'original_member':member,'sha256':h(data),'bytes':len(data)})
 for role,parent in [('baseline','original-cache-metadata-and-streams/_bridge-baseline/'+execution['head']),('mutant','original-cache-metadata-and-streams/M121/bridge-mutant'),('restored','original-cache-metadata-and-streams/M121/bridge-restored')]:
  member=parent+'/bridge.fingerprint.json';data=tar.extractfile(member).read();assert h(data)==execution[role+'_identity']['sidecar_sha256'];(m121/(role+'.fingerprint.json')).write_bytes(data)
coverage={'acceptance_source':F,'new_test_execution':False,'native_original_evidence_commit':'732ef20e34876379a37eb69693a481becebea43e','six_native_original_rows':rows,'six_native_pass_count':sum(int(s.split()[2]) for s in rows),'native_archive_members':members,'inspector_original_pass_lines':inspector,'inspector_cases_passed':12,'node_combined_summary':node.splitlines()[-8:],'M121':{'original_execution_sha':execution['head'],'adopted_ledger_sha':F,'record_sha256':record['record_sha256'],'whole_ledger_sha256':h(ledger),'methods':execution['methods'],'baseline_mutant_restored_exit':[execution[x]['exit_code'] for x in ['baseline','mutant','restored']],'baseline_mutant_restored_test_counts':[execution[x]['result']['total'] for x in ['baseline','mutant','restored']],'byte_restored':True,'original_streams_hash_checked':stream_rows},'limitation':'Native did not set GEOMETRY_263_TRANSCRIPT. Existing assertion coverage is verified; no standalone command or protocol-transcript sidecar is invented. The original raw Node stdout and six suite logs are retained.'}
dump(reuse/'COVERAGE.json',coverage)
memo=OUT/'whole-memo';memo.mkdir(exist_ok=True)
toolroot=ROOT/'evidence/geo337-train-20261024/prepared-during-F8/memo-copy-v2/tools'
for name in ['README.md','run.py','memo_variant.py','COUNTERFACTUAL.json','copy_r8_elf.py','R8_ELF_COPY_BINDINGS.json']:shutil.copy2(toolroot/name,memo/name)
r8=ROOT/'evidence/geo337-train-20261024/full-R8-five-stage-raw/ORIGINAL_R8_FIVE_STAGE_RAW.tar.gz'
with tarfile.open(r8) as tar:
 raw=tar.extractfile('original/receipt.json').read();assert h(raw)=='979680e78a381d28a6d1c6825b7b1b8af850bebec381ec3cee3ef42e9e46ea15';(memo/'R8_receipt.original.json').write_bytes(raw)
 excluded=tar.extractfile('collection/EXCLUDED_ELF_PAYLOADS.json').read();assert h(excluded)=='0c71f729418d551859c88227f5ddb9bdb3e0ecc250c4d72aa571838554c07071';(memo/'R8_EXCLUDED_ELF_PAYLOADS.original.json').write_bytes(excluded)
formal=json.loads(raw);assert formal['source_sha']==F8 and formal['stages']['profile']['execution_exit']==0
search=json.loads((OUT/'R8_ELF_LOCAL_SEARCH.json').read_text());assert not search['exact_payload_matches']
delta=subprocess.check_output(['git','-C',str(ROOT),'diff','--name-only',F8,F,'--','current_geometry.c','geometry-core','geometry-web','geometry-kernel','geometry-app','geometry-templates'],text=True).splitlines()
assert set(delta)=={'geometry-core/domain-decoupling/PRODUCT-ARCHITECTURE.md','geometry-core/domain-decoupling/product-architecture-receipt.json'}
memo_status={'status':'not executed; exact original ELF payloads unavailable in this environment','source_required_by_original_tool':F8,'current_acceptance_source':F,'original_formal_receipt_sha256':h(raw),'original_R8_performance_not_resampled':True,'original_R8_outer_exit_retained':1,'required_original_ELFs':search['original_pins'],'local_payload_search':{'roots':search['roots'],'same_size_candidates_hashed':len(search['same_size_candidates']),'exact_payload_matches':[]},'published_R8_payload_policy':'The pinned original R8 archive expressly excludes ELF bodies; all three bodies are needed, not a newly compiled substitute.','F8_to_F_product_paths_changed':delta,'source_identity_policy':'The prepared original tool explicitly asserts F8. Any future run retains actual F8 identity and separately assesses relevance to F; never relabel execution SHA.','next_action':'Retrieve the three original R8 ELF bodies from their preserving owner/environment, verifying exact bytes and modes. Other pinned tools/receipt/scenes can be restored from archived originals. Do not rebuild denominators or resample R8.','approval_request':False,'P189_comparator_changed':False}
dump(memo/'STATUS.json',memo_status)
memo_status['F8_to_F_product_code_unchanged']=True
memo_status['closure_note']='The full current_geometry.c and geometry-core/web/kernel/app/templates Git tree comparison has only two architecture-document/receipt changes. No C, Python or JavaScript product source differs. This establishes unchanged product code, while every future memo execution must still retain its original F8 SHA.'
dump(memo/'STATUS.json',memo_status)
report=f'''# Follow-up scope review after fixed-F P52

No new product test was run in this review. P52 original formal/verifier passed and was published at `a08a036db335e88608ead761539d3e60b75e8e5d`.

## #314 existing acceptance coverage

Fixed F `{F}` already ran all six requested native suites: **103 passed, zero fail/skip**, and all **12 GEO263 inspector subtests** inside the original Node run (**737 passed, zero fail/skip** overall). Complete original suite/Node stdout was extracted byte-for-byte from the accepted native archive, not regenerated.

M121 remains **killed**, with original execution SHA `{execution['head']}`. Its original build/test/restoration streams and sidecars match the hashes in F's adopted ledger; baseline/mutant/restored test exits are **0/1/0**, test counts **43/2/43**, and source byte restoration is true. The two original named methods are indexed in geo314/COVERAGE.json. The existing accepted F native mutation freshness check establishes the adopted ledger's current validity; no targeted mutation rerun was performed and no historical SHA was relabelled.

The native invocation did not request the optional GEOMETRY_263_TRANSCRIPT sidecar. Its absence is explicit; this review supplies actual original Node stdout, not an invented standalone protocol transcript. Test assertion coverage is already present and is not duplicated.

## Whole-memo specific missing original inputs

The original prepared v2 tool is fixed to actual **F8 `{F8}`**, and pins the exact original R8 formal receipt. That original receipt and the excluded-ELF inventory were recovered and verified byte-for-byte from the published archive. F8-to-F comparison of the complete product directories and current_geometry.c shows only the two architecture documentation/receipt changes; product code is unchanged. Any future memo execution must still report actual F8 identity. The valid R8 performance samples are not rerun, and its original outer red remains red.

The three required original ELF bodies at `/tmp/g337323R8/work/{{base-pg,fix,fix-trace}}/bridge` are absent here and expressly excluded from the published archive. A local workspace/tmp search hashed {len(search['same_size_candidates'])} same-size candidates and found no exact payload match. Exact hashes, sizes and modes are in whole-memo/STATUS.json. This is a missing-original-artifact prerequisite, not a product failure, resource-budget restriction or request to relax the test. A request for the preserving environment/readable original location is pending while other coverage review completes. No binary was rebuilt as a substitute, no original R8 sample was redrawn, and no P189 comparison rule changed.
'''
(OUT/'README.md').write_text(report);print(json.dumps({'geo314_native_pass':103,'inspector_cases':len(inspector),'M121_original_streams_verified':len(stream_rows),'whole_memo':'missing three original R8 ELF bodies','product_delta_paths':delta}))
