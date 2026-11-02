import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess

OUT = Path(__file__).resolve().parent
DATA = OUT.parent
SOURCE = Path('/tmp/geometry-pr340-20261102')
HEAD = 'b3a248607d7eb68d3167abbb926cf491d9b35a26'
MERGE = 'fc1c9f565a2e15660e931b3884dca2220cb1b7b2'
RUN = 41382015277
sha = lambda raw: hashlib.sha256(raw).hexdigest()
lf = lambda path: path.read_bytes().replace(b'\r\n', b'\n')
inputs = {}
def load(path):
    raw = path.read_bytes()
    inputs[str(path)] = sha(raw)
    def unique(pairs):
        out = {}
        for key, value in pairs:
            assert key not in out, 'duplicate JSON key ' + key
            out[key] = value
        return out
    return json.loads(raw, object_pairs_hook=unique)
git = lambda *args: subprocess.check_output(['git', *args], cwd=SOURCE).strip()
provenance = load(DATA / 'provenance.json')
assert provenance['source'] == str(SOURCE) and provenance['source_head'] == HEAD
assert provenance['execution_head'] == MERGE and provenance['integration_run_id'] == 41382015317
assert provenance['mutation_run_id'] == RUN and provenance['run_attempt'] == 1
assert git('rev-parse', 'HEAD').decode() == HEAD and git('status', '--porcelain') == b''
assert provenance['source_status'] == ''
tree = git('rev-parse', MERGE+'^{tree}').decode()
parents = git('show', '-s', '--format=%P', MERGE).decode().split()
assert provenance['tree'] == tree == git('rev-parse', HEAD+'^{tree}').decode()
assert provenance['merge_parents'] == parents == ['5775a9e9e46bca801a9a70aaeafcdab9f597bc4d', HEAD]
commit_path = DATA / 'api/execution-commit.json'
commit = load(commit_path)
assert commit['sha'] == MERGE and commit['tree']['sha'] == tree
assert [parent['sha'] for parent in commit['parents']] == parents
assert commit['verification']['verified'] is True
assert provenance['github_execution_commit']['sha256'] == sha(commit_path.read_bytes())
assert provenance['github_execution_commit']['api_sha_tree_parents_match'] is True
for row in provenance['original_tools_and_workflow_bytes']:
    file = SOURCE / row['path']
    assert row['sha256'] == sha(file.read_bytes()) and row['lf_sha256'] == sha(lf(file))
    committed = git('show', HEAD+':'+row['path'])
    # git helper strips trailing newlines, so compare with the same normalization.
    assert committed == file.read_bytes().strip()

# ROOT comes from each unchanged original file, not the receipt directory.
for relative in ['.github/scripts/mutation_evidence.py', '.github/scripts/architecture_evidence.py']:
    script = SOURCE / relative
    text = script.read_text()
    assert 'ROOT = Path(__file__).resolve().parents[2]' in text
    assert script.resolve().parents[2] == SOURCE
    assert 'cwd=ROOT' in text
supervisor_sha = sha(lf(SOURCE / '.github/scripts/mutation_evidence.py'))
tool_sha = sha(lf(SOURCE / 'tests/mutate.py') + b'\0mutation_bridge.py\0' + lf(SOURCE / 'tests/mutation_bridge.py'))
assert 'ROOT = HERE.parent' in (SOURCE / 'tests/mutate.py').read_text()

native = load(DATA / 'native-reverify-receipt.json')
assert native['sourceHead'] == HEAD and native['executionHead'] == MERGE and native['tree'] == tree
assert native['merge_parents'] == parents and native['exit_code'] == 0 and native['official_reaggregation_equal']
assert native['cwd'] == str(SOURCE)
assert native['env']['GIT_WORK_TREE'] == str(SOURCE)
metadata = Path(native['env']['GIT_DIR'])
metadata_head = subprocess.check_output(['git', '--git-dir', str(metadata), 'rev-parse', 'HEAD'], cwd=SOURCE).decode().strip()
assert metadata_head == MERGE
assert (DATA / 'native-reverified.json').read_bytes() == (DATA / 'extracted/native-complete-coverage/native-complete.json').read_bytes()
for proof_folder in [DATA / 'extracted/native-complete-coverage/native-sharding-proof', DATA / 'native-local-negative-control']:
    proof = load(proof_folder / 'receipt.json')
    assert proof['passed'] and proof['baseline_mutant_restored_exit'] == [0, 1, 0]
    for label, expected_exit in [('baseline', 0), ('removed', 1), ('restored', 0)]:
        record = load(proof_folder / (label+'.json'))
        log = (proof_folder / (label+'.log')).read_text()
        assert record['tests'] == 1 and record['failures'] == expected_exit and record['errors'] == record['skips'] == 0
        row = next(row for row in proof['rows'] if row['label'] == label)
        assert row['exit'] == expected_exit and all(row[key] == value for key, value in record.items())
        assert 'Ran 1 test in ' in log
        if expected_exit:
            assert record['removed'] == ['c:integrity'] and record['assertion_failure'] is True
            assert record['failure_ids'] == ['test_unittest_runner.NativeShardCoverage.test_partition_covers_actual_suite_registry_once']
            assert 'AssertionError: Counter(' in log and 'FAILED (failures=1)' in log
        else:
            assert re.search(r'^OK\s*$', log, re.M) and '... ok' in log

fresh_control = load(DATA / 'native-control-receipt.json')
assert fresh_control['exit_code'] == 0 and fresh_control['cwd'] == str(SOURCE)
for stream in ['stdout', 'stderr']:
    assert fresh_control[stream+'_sha256'] == sha((DATA / ('native-control.'+stream)).read_bytes())
assert fresh_control['receipt'] == load(DATA / 'native-local-negative-control/receipt.json')
assert fresh_control['receipt']['baseline_mutant_restored_exit'] == [0,1,0]

architecture = load(DATA / 'architecture-audit.json')
official_arch = load(DATA / 'extracted/pr357-architecture-refresh/product-architecture-receipt.json')
assert architecture['sourceHead'] == HEAD and architecture['run_id'] == RUN and architecture['exit_code'] == 0
assert official_arch['sourceHead'] == HEAD and official_arch['runId'] == str(RUN) and official_arch['runAttempt'] == '1'
assert architecture['original_commands'] == official_arch['commands']
manifest_path = SOURCE / 'geometry-core/domain-decoupling/product-architecture.json'
manifest = load(manifest_path)
closure = sorted([{'path': row['path'], 'lfSha256': sha(lf(SOURCE / row['path']))}
                  for row in manifest['sources'] + manifest['exclusions']], key=lambda row: row['path'])
assert official_arch['inputs'] == closure and official_arch['manifestLfSha256'] == sha(lf(manifest_path))
assert official_arch['inputLfClosureSha256'] == sha('\n'.join(row['path']+' '+row['lfSha256'] for row in closure).encode())
assert official_arch['scannerLfSha256'] == sha(lf(SOURCE / 'tests/architecture_contract.py'))
for path, digest in official_arch['testScriptsLfSha256'].items():
    assert digest == sha(lf(SOURCE / path))
for row in official_arch['commands']:
    assert row['cwd'] == '<repo>' and row['exitCode'] == 0 and 'completenessProblem' not in row
    for stream in ['stdout', 'stderr']:
        assert sha((DATA / 'extracted/pr357-architecture-refresh' / row[stream]).read_bytes()) == row[stream+'Sha256']
    if row.get('testsRun'):
        log = (DATA / 'extracted/pr357-architecture-refresh' / row['stderr']).read_text()
        assert len(re.findall(r'Ran (\d+) tests? in ', log)) == 1
        assert int(re.findall(r'Ran (\d+) tests? in ', log)[0]) == row['testsRun'] > 0
        assert re.search(r'^OK\s*$', log, re.M) and not re.search(r'FAILED|skipped=[1-9]', log)

mutation = load(DATA / 'mutation-shard-audit.json')
assert mutation['head'] == HEAD and mutation['run_id'] == RUN and mutation['run_attempt'] == 1
assert mutation['complete'] is False and mutation['downloaded_shards'] == 4 and mutation['records'] == 70
assert set(mutation['missing_shards']) == {'bridge-1','bridge-2','bridge-3'}
for row in mutation['shards']:
    folder = DATA / 'extracted' / ('mutation-shard-'+row['shard'])
    shard = load(folder / 'manifest.json')
    assert shard['head'] == HEAD and shard['run_id'] == str(RUN) and shard['run_attempt'] == '1'
    assert shard['supervisor_sha256'] == supervisor_sha and shard['tool_sha256'] == tool_sha
    records = load(folder / 'mutants_results.json')
    assert len(records) == row['records'] and set(records) == set(shard['ids'])
    assert dict(Counter(record['verdict'] for record in records.values())) == row['counts']
    for record in records.values():
        if record['verdict'] != 'retired':
            assert record['execution']['head'] == HEAD
    for filename, field in [('mutants_results.json','ledger_sha256'),('cache.tar.gz','cache_sha256'),('execution.log','execution_log_sha256')]:
        assert sha((folder / filename).read_bytes()) == shard[field]
    log_path = DATA / 'job-logs' / (str(row['job_id'])+'.txt')
    lines = log_path.read_text().splitlines()
    assert row['job_log_sha256'] == sha(log_path.read_bytes()) and row['negative_probe_log'] in lines
    at = lines.index(row['negative_probe_log'])
    summaries = [line for line in lines[:at] if '過期 stale ' in line]
    after = [line for line in lines[at+1:] if '過期 stale ' in line]
    assert '過期 stale 0' in summaries[-2] and '過期 stale 1' in summaries[-1] and '過期 stale 0' in after[0]
    assert shard['negative_cache_probe']['strict_exit'] == 1 and row['strict_exit'] == 0
    assert row['binary_bytes_and_sidecars_verified']

# #345: classify an actual red shard from original raw output, without re-running.
DATA345 = DATA.parent / 'pr345'
SOURCE345 = Path('/tmp/geometry-pr345-20261102')
classification_path = DATA345 / 'integration-failure-classification.json'
classification = load(classification_path)
assert classification['source_head'] == '577b2e81967b3019352f65df5ffe6dc48eb6202f'
assert classification['integration_run_id'] == 41382891799 and classification['job_id'] == 125077322413
snapshot = Path(classification['snapshot'])
jobs = load(snapshot / 'integration-jobs.json')['jobs']
job = next(job for job in jobs if job['id'] == classification['job_id'])
assert job['name'] == 'native (2/3)' and job['conclusion'] == 'failure'
shard_path = DATA345 / 'extracted/native-shard-2/shard-2.json'
shard = load(shard_path)
assert shard['commit_sha'] == classification['execution_head'] and shard['exit_code'] == classification['official_native_exit'] == 1
assert shard['shard'] == classification['native_shard'] == [2,3] and len(shard['rows']) == classification['native_suites'] == 76
bad = [row for row in shard['rows'] if row['process_exit_code'] or row['failed'] or row['env_problem'] or row['crashed'] or row['expected_problem']]
assert bad == classification['bad_rows'] and len(bad) == 1 and bad[0]['name'] == 'mutation:check'
assert bad[0]['ran'] and bad[0]['failed'] == 1 and bad[0]['process_exit_code'] == 1 and not bad[0]['counted']
assert sum(not row['process_exit_code'] and not row['failed'] for row in shard['rows']) == classification['passing_other_rows'] == 75
raw_path = Path(classification['raw_log'])
raw = raw_path.read_text()
stale_lines = [line for line in raw.splitlines() if line.startswith('  STALE ')]
assert len(stale_lines) == classification['stale_count'] == 53 and stale_lines == classification['stale_records']
assert classification['inventory_summary'] in raw and '過期 stale 53 / 受阻 blocked 0 / 退役 retired 3' in raw
mutants_ast = ast.parse((SOURCE345 / 'tests/mutate.py').read_text())
mutants = []
for node in mutants_ast.body:
    value = None
    if isinstance(node, ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MUTANTS' for t in node.targets):
        value = node.value
    elif isinstance(node, ast.AugAssign) and isinstance(node.target,ast.Name) and node.target.id=='MUTANTS':
        value = node.value
    if value is not None:
        assert isinstance(value, ast.List)
        for call in value.elts:
            fields = {kw.arg: kw.value for kw in call.keywords}
            mutants.append({'id':ast.literal_eval(fields['id']), 'binary':ast.literal_eval(fields['binary']) if 'binary' in fields else 'core'})
assert len(mutants) == 123 and len({m['id'] for m in mutants}) == 123
bridge_ids = {m['id'] for m in mutants if m['binary']=='bridge'}
assert len(bridge_ids) == 53 and {re.search(r'STALE (M\d+)',line)[1] for line in stale_lines} == bridge_ids
assert classification['raw_log_sha256'] == sha(raw_path.read_bytes())
assert classification['official_shard_sha256'] == sha(shard_path.read_bytes())
assert classification['job_log_sha256'] == sha((DATA345 / 'job-logs/125077322413.txt').read_bytes())
assert classification['source_ledger_sha256'] == sha((SOURCE345 / 'tests/mutants_results.json').read_bytes())
assert classification['classification'] == 'committed-mutation-ledger-stale'
assert 'cannot be accepted as green' in classification['limitation']

result = {'passed':True, 'blocking_findings':[], 'pr340_head':HEAD, 'pr340_execution_commit':MERGE,
          'pr340_source_tool_root_binding':True, 'pr340_provenance_source_file_count':len(provenance['original_tools_and_workflow_bytes']),
          'pr340_native_original_and_local_negative_control':[0,1,0], 'pr340_mutation_complete':False,
          'pr340_mutation_pending':['bridge-1','bridge-2','bridge-3'], 'pr340_core_probes_confirmed':4,
          'pr345_classification':'committed-mutation-ledger-stale', 'pr345_native_failure_preserved':True,
          'pr345_exact_stale_bridge_ids':sorted(bridge_ids,key=lambda rid:int(rid[1:])),
          'pr345_stale_count':53, 'pr345_other_passing_suites':75,
          'limitations':['#340 canvas and bridge shards remain pending in the reviewed snapshot.',
                         '#345 red integration is not made green by classification; fresh mutation aggregate is still pending.',
                         'Only saved files and read-only Git metadata were inspected; no network, source writes, tests or binaries executed.'],
          'input_sha256':inputs, 'script_sha256':sha(Path(__file__).read_bytes())}
(OUT / 'adversarial-receipt-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({key:result[key] for key in ['passed','blocking_findings','pr340_source_tool_root_binding','pr340_mutation_complete','pr345_stale_count','pr345_other_passing_suites']}))
