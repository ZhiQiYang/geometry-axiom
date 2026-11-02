from collections import Counter
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

OUT = Path(__file__).resolve().parent
ADOPTION = OUT.parent
DATA = ADOPTION.parent
SOURCE = Path('/tmp/geometry-pr345-20261102')
E = '79cf0f16bca9ce55b2b19e793650d5e4e2e2c5e6'
M = '577b2e81967b3019352f65df5ffe6dc48eb6202f'
LEDGER = 'tests/mutants_results.json'
OFFICIAL_SHA = '0be90a297b4f4b4fd5a2e60d528886845cc2c8d823e912ef3b0763ba68f7eb1c'
BEFORE_SHA = 'b02f378106bb16d7e392d77bad6f006a20ea5558afb67606368005642da7b295'
sha = lambda value: hashlib.sha256(value).hexdigest()
lf = lambda value: value.replace(b'\r\n',b'\n')
git = lambda *args: subprocess.check_output(['git',*args],cwd=SOURCE)
def load(path):
    def unique(pairs):
        out = {}
        for key,value in pairs:
            assert key not in out,'duplicate JSON key '+key
            out[key] = value
        return out
    return json.loads(path.read_bytes(),object_pairs_hook=unique)
def tree(commit):
    out = {}
    for entry in git('ls-tree','-rz','--full-tree',commit).split(b'\0'):
        if not entry:
            continue
        meta,name = entry.split(b'\t',1)
        mode,kind,oid = meta.decode().split()
        name = name.decode()
        assert name not in out
        out[name] = {'git_mode':mode,'git_kind':kind,'git_object':oid}
    return out

assert git('rev-parse','HEAD').decode().strip()==E
assert git('show','-s','--format=%P',E).decode().strip().split()==[M]
assert git('status','--porcelain')==b''
changed = git('diff-tree','--no-commit-id','--name-only','-r',E).decode().splitlines()
assert changed==[LEDGER]
subject = git('show','-s','--format=%s',E).decode().strip()
assert subject=='chore: adopt verified issue 214 mutation evidence' and subject.isascii()
index_paths = {name for name in git('ls-files','-z').decode().split('\0') if name}
official_path = DATA/'extracted/mutation-complete-evidence/mutants_results.json'
official = official_path.read_bytes()
current = (SOURCE/LEDGER).read_bytes()
blob_E,blob_M = git('show',E+':'+LEDGER),git('show',M+':'+LEDGER)
outer_before = ADOPTION/'committed-ledger.before.json'
assert sha(official)==sha(current)==sha(blob_E)==OFFICIAL_SHA
assert official==current==blob_E
assert sha(outer_before.read_bytes())==sha(blob_M)==BEFORE_SHA and outer_before.read_bytes()==blob_M
records = load(official_path)
assert len(records)==123 and sum(record['verdict']!='retired' for record in records.values())==120
assert Counter(record['verdict'] for record in records.values())==Counter({'killed':114,'crashed':1,'equivalent':5,'retired':3})
execution_heads = {record['execution']['head'] for record in records.values() if 'execution' in record}
assert execution_heads=={M}
assert all(record['execution']['head']==M for record in records.values() if record['verdict']!='retired')

before_path,after_path = ADOPTION/'identity-before.json',ADOPTION/'identity-after-write.json'
before,after = load(before_path),load(after_path)
assert set(before)==set(after)
assert {key:value for key,value in before.items() if key!='tracked'}=={key:value for key,value in after.items() if key!='tracked'}
old_rows,new_rows = {row['path']:row for row in before['tracked']},{row['path']:row for row in after['tracked']}
assert len(old_rows)==len(before['tracked']) and len(new_rows)==len(after['tracked'])
assert set(old_rows)==set(new_rows)==index_paths
assert [path for path in sorted(old_rows) if old_rows[path]!=new_rows[path]]==[LEDGER]
assert old_rows[LEDGER]['sha256']==BEFORE_SHA and new_rows[LEDGER]['sha256']==OFFICIAL_SHA
non_ledger = [row for row in after['tracked'] if row['path']!=LEDGER]
closure_digest = sha(json.dumps(non_ledger,sort_keys=True).encode())
assert before['non_ledger_tracked_closure_sha256']==after['non_ledger_tracked_closure_sha256']==closure_digest
materialized=sum(row['materialized'] for row in new_rows.values())
sparse=sum(not row['materialized'] for row in new_rows.values())
assert materialized==20946 and sparse==17742
for name,row in new_rows.items():
    if not row['materialized']:
        assert all(field in row for field in ['git_mode','git_kind','git_object'])
        assert row==old_rows[name]
mutation_closure = sha('\n'.join(name+' '+after['mutation_source_hashes'][name] for name in sorted(after['mutation_source_hashes'])).encode())
assert mutation_closure==after['mutation_closure_sha256']
tool_sha=sha(lf((SOURCE/'tests/mutate.py').read_bytes())+b'\0mutation_bridge.py\0'+lf((SOURCE/'tests/mutation_bridge.py').read_bytes()))
assert tool_sha==after['tool_sha256']
assert len(after['bridge_oracle_sha256'])==53
for rid,record in records.items():
    if record['verdict']=='retired':
        continue
    expected_oracle=after['bridge_oracle_sha256'].get(rid,after['core_oracle_sha256'])
    assert record['oracle_sha256']==expected_oracle and record['closure_sha256']==mutation_closure
    assert record['execution']['tool_sha256']==tool_sha
native_inputs_compared=0
for name,build in after['native_build_inputs'].items():
    fingerprint=hashlib.sha256()
    fingerprint.update(build['command'].encode())
    fingerprint.update(b'\0')
    for relative in sorted(build['inputs']):
        digest=build['inputs'][relative]
        fingerprint.update((relative+'\0'+digest+'\n').encode())
        native_inputs_compared+=1
    assert fingerprint.hexdigest()==build['fingerprint'],name
assert len(after['native_build_inputs'])==7

cache=Path('/tmp/geometry-tests/mutants')
assert before['selected_cache']==after['selected_cache']=={'path':str(cache),'exists':False,'files':[]}
assert not cache.exists()
assert 'MUTATE_CACHE' not in os.environ and 'MUTATE_RESULTS' not in os.environ
preparation=load(ADOPTION/'preparation-receipt.json')
assert preparation['identity_before_sha256']==sha(before_path.read_bytes())
assert preparation['identity_after_sha256']==sha(after_path.read_bytes())
assert preparation['original_ledger_sha256']==BEFORE_SHA and preparation['official_ledger_sha256']==OFFICIAL_SHA
prior_review=DATA.parent/'pr340/independent-review/pr345-mutation-terminal-adversarial-review.json'
prior=load(prior_review)
assert prior['passed'] and prior['mutation_accepted'] and prior['pr_head']==M
assert prior['mutation_ledger_sha256']==OFFICIAL_SHA and prior['bridge_raw_markers_independently_reparsed']==159
assert len(prior['local_cache_probe_shards'])==7

command=[sys.executable,'-B','tests/mutate.py','--check']
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (OUT/'logical-check.stdout').open('wb') as output,(OUT/'logical-check.stderr').open('wb') as errors:
    process=subprocess.run(command,cwd=SOURCE,stdout=output,stderr=errors)
finish=datetime.datetime.now(datetime.timezone.utc).isoformat()
logical={'command':command,'cwd':str(SOURCE),'candidate_head':E,'utc_start':start,'utc_finish':finish,
         'exit_code':process.returncode,'stdout_sha256':sha((OUT/'logical-check.stdout').read_bytes()),
         'stderr_sha256':sha((OUT/'logical-check.stderr').read_bytes()),
         'cache_overrides_added':False,'inherited_MUTATE_CACHE_present':False,'inherited_MUTATE_RESULTS_present':False,
         'default_cache':str(cache),'default_cache_existed_before':False,'default_cache_exists_after':cache.exists(),
         'limitation':'Original logical freshness/receipt --check once at E only. Earlier official artifact binaries/sidecars were already verified at M. This is not a new product run or downloaded-artifact execution.'}
(OUT/'logical-check-receipt.json').write_text(json.dumps(logical,ensure_ascii=False,indent=2)+'\n')
assert process.returncode==0
stdout=(OUT/'logical-check.stdout').read_text()
assert '變異表 123 筆,紀錄 123 筆' in stdout and '過期 stale 0 / 受阻 blocked 0 / 退役 retired 3' in stdout
assert not cache.exists() and (SOURCE/LEDGER).read_bytes()==official
assert git('rev-parse','HEAD').decode().strip()==E and git('status','--porcelain')==b''

result={'passed':True,'blocking_findings':[],'candidate_E':E,'parent_M':M,'parents_exactly':[M],
        'subject':subject,'changed_paths':changed,'working_tree_clean_before_and_after':True,
        'official_ledger_sha256':OFFICIAL_SHA,'git_blob_working_and_official_byte_equal':True,
        'original_M_ledger_sha256':BEFORE_SHA,'outer_before_backup_byte_equal_M_git_blob':True,
        'mutation_records':123,'active_records':120,'counts':dict(Counter(record['verdict'] for record in records.values())),
        'unchanged_execution_heads':sorted(execution_heads),'identity_changed_paths':[LEDGER],
        'tracked_identity_entries_compared':len(new_rows),'materialized_identity_entries_compared':materialized,'sparse_git_object_identities_compared':sparse,
        'non_ledger_tracked_closure_sha256':closure_digest,
        'C_Python_oracle_runner_tool_compile_and_native_build_identity_equal':True,
        'mutation_source_file_hash_identities_compared':len(after['mutation_source_hashes']),
        'mutation_closure_sha256':mutation_closure,'original_tool_sha256':tool_sha,
        'native_build_identities_compared':len(after['native_build_inputs']),'native_input_identity_entries_compared':native_inputs_compared,
        'core_oracle_sha256':after['core_oracle_sha256'],
        'bridge_oracle_identities_checked':len(after['bridge_oracle_sha256']),
        'identity_before_sha256':sha(before_path.read_bytes()),'identity_after_write_sha256':sha(after_path.read_bytes()),
        'logical_check':logical,'logical_check_receipt_sha256':sha((OUT/'logical-check-receipt.json').read_bytes()),
        'prior_downloaded_binary_sidecar_verification_receipt':str(prior_review),
        'prior_downloaded_binary_sidecar_verification_receipt_sha256':sha(prior_review.read_bytes()),
        'prior_downloaded_artifacts_reexecuted':False,'source_PR_API_or_remote_mutated_by_peer':False,
        'peer_script_sha256':sha(Path(__file__).read_bytes()),
        'scope':'Bounded actor-peer review before authorized ordinary push. No source/PR/API/push action; only one original read-only logical --check, with no cache override or cache deletion.'}
(OUT/'actor-peer-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({key:result[key]for key in ['passed','blocking_findings','candidate_E','changed_paths','tracked_identity_entries_compared','materialized_identity_entries_compared','sparse_git_object_identities_compared','unchanged_execution_heads']},ensure_ascii=False))
