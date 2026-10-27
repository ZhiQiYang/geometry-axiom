from pathlib import Path
import hashlib,json,runpy,subprocess,tarfile,sys
sys.dont_write_bytecode=True
ROOT=Path('/workspace/geo337-native-F-cbf0fb62');OUT=Path('/workspace/scratch/geo337-q38-F-cbf0fb62-20261027');TOOLS=Path(__file__).parent
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def h(b):return hashlib.sha256(b).hexdigest()
r=json.loads((OUT/'RESULT.json').read_text());assert r['passed']
receipt=json.loads((OUT/'q38/receipt.json').read_text())
scope=runpy.run_path(str(ROOT/'tests/section_profile_mutation_check.py'),run_name='q38_receipt_verifier')
cases={c['id']:c for c in scope['CASES']}
assert set(x['id'] for x in receipt['results'])==set(cases) and len(receipt['results'])==44
rows=[]
for item in receipt['results']:
    case=cases[item['id']]
    judged=scope['verdict'](case,item['exit'],'',item['exception_evidence'])
    assert judged['verdict']==item['verdict'] and item['verdict'] in ('killed','equivalent'),item['id']
    assert scope['evidence_problem'](item['exit'],item['exception_evidence']) is None
    if item['group']=='native':assert item['binary_sha256']!=receipt['baselines']['native']['binary_sha256']
    if scope['patches_native'](case) and item['group']=='model':assert item['adapter_sha256']!=receipt['baselines']['model']['adapter_sha256']
    rows.append({'id':item['id'],'group':item['group'],'verdict':item['verdict'],'failures':item['exception_evidence']['failures'],'errors':item['exception_evidence']['errors'],'skips':item['exception_evidence']['skipped'],'declared_equivalent':case['equivalent'],'declared_error_types':case['error_types']})
for key,item in receipt['baselines'].items():assert item['exit']==0 and scope['evidence_problem'](item['exit'],item['exception_evidence']) is None
inventory=json.loads((OUT/'SOURCE_BEFORE.json').read_text())
with tarfile.open(OUT/'source-snapshot.original.tar.gz','r:gz') as tar:
    actual={m.name.removeprefix('source-snapshot/'):h(tar.extractfile(m).read()) for m in tar.getmembers() if m.isfile()}
assert actual==inventory
assert all(h((ROOT/p).read_bytes())==digest for p,digest in inventory.items())
running=json.loads((OUT/'RUNNING.json').read_text());owned=[]
for p in Path('/proc').glob('[0-9]*'):
    try:
        s=(p/'stat').read_text().rsplit(')',1)[1].split()
        if int(s[2])==running['pid']:owned.append({'pid':int(p.name),'stat':s,'cmdline':(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')})
    except OSError:pass
dump(OUT/'OWNED_PROCESSES_AFTER.json',owned);assert not owned
dump(OUT/'VERIFICATION.json',{'sha':r['sha'],'cases':rows,'all_44_original_verdicts_rechecked':True,'source_snapshot_archive_all_bytes_match':True,'source_files':len(inventory),'baselines':{k:{f:v['exception_evidence'][f] for f in ['tests_run','failures','errors','skipped']} for k,v in receipt['baselines'].items()}})
logs={str(p.relative_to(OUT/'q38')):{'bytes':p.stat().st_size,'sha256':h(p.read_bytes())} for p in sorted((OUT/'q38').rglob('*')) if p.is_file()}
dump(OUT/'ORIGINAL_OUTPUT_INVENTORY.json',logs)
report=f'''# Fixed-F Q38 complete mutation acceptance

Execution source `{r['sha']}`; original complete Q38 producer exit **0**. All 44 original cases SPM01–SPM44 executed with no selector, group filter or explore mode. Summary: `{json.dumps(receipt['summary'],sort_keys=True)}`. Both original baselines passed with zero skips.

Exact commands, UTC start/end, actual exit codes, explicit environment and streams are preserved per stage. The private bridge and model-base prerequisites were freshly built from F. The acceptance command was `python3 -B -u tests/section_profile_mutation_check.py --receipt <OUT>/q38/receipt.json --logs <OUT>/q38/logs --jobs 1`. Stack 16 MiB; original native-compile limit 600 seconds, test/model-adapter limits 900 seconds; no new overall time limit. Total prerequisite plus producer elapsed {r['elapsed_seconds']:.3f} seconds. Original source hashes remain unchanged and checkout clean.

The original equivalent classification is retained. Cause-labelled ModelError outcomes remain ERROR; they are not relabelled AssertionError failures. The independent collection pass reapplies the unmodified original verdict function to every original exception receipt, checks the complete registry and binary-difference requirements, and compares every archived source byte with the original snapshot. No tests are rerun during collection. See VERIFICATION.json for per-case classifications and baseline counts.

Complete original persistent raw logs, exception evidence, compile receipts, final receipt and outer streams are included. The unmodified producer itself removes its disposable mutant trees and binaries; no claim is made that those discarded temporary files were retained. The exact original source snapshot, original full case definitions and retained prerequisite ELF/fingerprint files are included. This source snapshot and the unmodified producer define every patch; no replacement judge or weaker assertion was introduced.

Operational changes are private output/TMPDIR and private prerequisite bridge paths, an exclusive owner lock, and the same process-local child subreaper used for accepted native validation. No shared /tmp/geometry-tests writes, mounts, product edits, main merge or deployment. No remaining process in the original producer's process group was found.

This result is bound to F, not the historical L/F9 receipts. It does not re-run valid native, oracle, reader, required-eight or another task's browser scopes. P189 exact comparison rules remain unchanged.
'''
(TOOLS/'HANDOFF.md').write_text(report)
print(json.dumps({'passed':True,'summary':receipt['summary'],'baselines':{k:v['exception_evidence']['tests_run'] for k,v in receipt['baselines'].items()},'original_log_files':len(logs)}))
