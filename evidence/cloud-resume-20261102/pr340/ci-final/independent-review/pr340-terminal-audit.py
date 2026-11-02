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


import tarfile
import zipfile

snapshot = DATA / 'api/20261102T035059Z'
api_jobs = {}
zip_rows, whole_logs = [], []
for kind, run_id in [('integration',41382015317),('mutation',41382015277)]:
    run = load(snapshot / (kind+'-run.json'))
    assert run['id'] == run_id and run['head_sha'] == HEAD and run['run_attempt'] == 1
    assert run['status'] == 'completed' and run['conclusion'] == 'success'
    jobs = load(snapshot / (kind+'-jobs.json'))['jobs']
    assert len(jobs) == 10 and all(job['status']=='completed' and job['conclusion']=='success' for job in jobs)
    api_jobs[kind] = {job['name']:job for job in jobs}
    artifacts = load(snapshot / (kind+'-artifacts.json'))['artifacts']
    for artifact in artifacts:
        archive_path = DATA / 'official-zips' / f"{artifact['id']}-{artifact['name']}.zip"
        assert artifact['workflow_run']['id'] == run_id and artifact['workflow_run']['head_sha'] == HEAD
        assert artifact['digest'] == 'sha256:'+sha(archive_path.read_bytes())
        with zipfile.ZipFile(archive_path) as archive:
            assert len(archive.namelist()) == len(set(archive.namelist()))
            members = 0
            for info in archive.infolist():
                rel = Path(info.filename)
                assert not rel.is_absolute() and '..' not in rel.parts
                assert (info.external_attr >> 16) & 0o170000 != 0o120000
                if not info.is_dir():
                    assert archive.read(info.filename) == (DATA / 'extracted' / artifact['name'] / info.filename).read_bytes()
                    members += 1
        zip_rows.append(dict(kind=kind,run_id=run_id,id=artifact['id'],name=artifact['name'],digest=artifact['digest'],members=members))
    archive_path = DATA / 'official-run-logs' / f'{kind}-{run_id}.zip'
    with zipfile.ZipFile(archive_path) as archive:
        for job in jobs:
            names = [name for name in archive.namelist() if re.fullmatch(r'\d+_'+re.escape(job['name'].replace('/','_'))+r'\.txt',name)]
            assert len(names) == 1
            direct = DATA / 'job-logs' / (str(job['id'])+'.txt')
            assert archive.read(names[0]) == direct.read_bytes()
            whole_logs.append(dict(kind=kind,job_id=job['id'],name=job['name'],sha256=sha(direct.read_bytes())))
assert len(zip_rows) == 21 and len(whole_logs) == 20

verify = load(DATA / 'mutation-verify-receipt.json')
assert verify['cwd'] == str(SOURCE) and verify['head'] == HEAD and verify['exit_code'] == 0
assert verify['command'][1:] == ['-B','.github/scripts/mutation_evidence.py','verify','--artifacts',str(DATA / 'extracted'),'--out',str(DATA / 'mutation-local-verified')]
for stream in ['stdout','stderr']:
    assert verify[stream+'_sha256'] == sha((DATA / ('mutation-verify.'+stream)).read_bytes())
official = DATA / 'extracted/mutation-complete-evidence'
local = DATA / 'mutation-local-verified'
for name in ['summary.json','mutants_results.json']:
    assert (official/name).read_bytes() == (local/name).read_bytes()
summary = load(official / 'summary.json')
ledger = load(official / 'mutants_results.json')
assert summary == verify['summary'] and summary['head'] == HEAD
assert summary['schema'] == 'geometry-mutation-ci-summary/1' and summary['table_size'] == len(ledger) == 123
assert summary['active'] == sum(row['verdict']!='retired' for row in ledger.values()) == 120
assert summary['ledger_sha256'] == verify['ledger_sha256'] == sha((official / 'mutants_results.json').read_bytes())
assert summary['binary_bytes_verified'] is True and summary['full_table_strict_exit'] == 0
counts = Counter(row['verdict'] for row in ledger.values())
assert counts == Counter({'killed':114,'crashed':1,'equivalent':5,'retired':3})
assert {key:value for key,value in summary['counts'].items() if value} == dict(counts)
assert verify['official_summary_and_ledger_byte_equal'] is True
assert verify['summary_sha256'] == sha((official / 'summary.json').read_bytes())
ast_source = ast.parse((SOURCE / 'tests/mutate.py').read_text())
mutants = []
for node in ast_source.body:
    value = None
    if isinstance(node, ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MUTANTS' for t in node.targets):
        value = node.value
    elif isinstance(node,ast.AugAssign) and isinstance(node.target,ast.Name) and node.target.id=='MUTANTS':
        value = node.value
    if value is not None:
        assert isinstance(value,ast.List)
        for call in value.elts:
            fields = {kw.arg:kw.value for kw in call.keywords}
            mutants.append({'id':ast.literal_eval(fields['id']),'binary':ast.literal_eval(fields['binary']) if 'binary' in fields else 'core'})
assert len(mutants) == len({m['id'] for m in mutants}) == 123
assert set(ledger) == {m['id'] for m in mutants}
plans = {}
for kind, count in [('core',4),('bridge',3)]:
    ids = [m['id'] for m in mutants if m['binary']==kind]
    for index in range(count):
        plans[kind+'-'+str(index+1)] = ids[index::count]

probes = load(DATA / 'mutation-local-cache-probes.json')
assert probes['exit_code'] == 0 and probes['source_head'] == HEAD and probes['source_root'] == str(SOURCE)
assert probes['original_supervisor_sha256'] == probes['original_supervisor_lf_sha256'] == supervisor_sha
assert probes['original_tool_sha256'] == tool_sha
assert probes['stdout_sha256'] == sha((DATA / 'mutation-local-cache-probes.stdout').read_bytes())
probe_code = Path(probes['command'][2])
assert probe_code == DATA.parent / 'reprobe_downloaded_caches.py'
assert 'assert supervisor.ROOT == source and supervisor.head() == expected' in probe_code.read_text()
assert 'supervisor.negative_probe(mutants, ledger, records, cache)' in probe_code.read_text()
assert set(row['shard'] for row in probes['shards']) == set(plans)
shard_audit = load(DATA / 'mutation-shard-audit.json')
assert shard_audit['complete'] is True and shard_audit['missing_shards'] == [] and shard_audit['records'] == 123
assert shard_audit['head'] == HEAD and shard_audit['run_id'] == RUN and shard_audit['run_attempt'] == 1
merged, shard_rows, raw_markers = {}, [], 0
def strict_json(value):
    def unique(pairs):
        out = {}
        for key, item in pairs:
            assert key not in out
            out[key] = item
        return out
    return json.loads(value,object_pairs_hook=unique)
for shard_manifest in summary['shards']:
    name = shard_manifest['shard']
    folder = DATA / 'extracted' / ('mutation-shard-'+name)
    manifest = load(folder / 'manifest.json')
    assert manifest == shard_manifest and manifest['ids'] == plans[name]
    assert manifest['schema'] == 'geometry-mutation-ci-shard/1' and manifest['head'] == HEAD
    assert manifest['run_id'] == str(RUN) and manifest['run_attempt'] == '1' and manifest['platform'] == 'posix'
    assert manifest['tool_sha256'] == tool_sha and manifest['supervisor_sha256'] == supervisor_sha
    for filename, field in [('mutants_results.json','ledger_sha256'),('cache.tar.gz','cache_sha256'),('execution.log','execution_log_sha256')]:
        assert sha((folder / filename).read_bytes()) == manifest[field]
    records = load(folder / 'mutants_results.json')
    assert set(records) == set(plans[name]) and not set(records)&set(merged)
    assert all(ledger[rid] == record for rid,record in records.items())
    merged.update(records)
    audit = next(row for row in shard_audit['shards'] if row['shard']==name)
    job = api_jobs['mutation']['mutation ('+name+')']
    assert audit['job_id'] == job['id'] and audit['strict_exit'] == 0 and audit['binary_bytes_and_sidecars_verified']
    probe = next(row for row in probes['shards'] if row['shard']==name)
    assert probe['strict_baseline_mutant_restored_exit'] == [0,1,0]
    assert probe['original_negative_probe'] == manifest['negative_cache_probe'] == audit['negative_probe']
    assert probe['ledger_sha256'] == manifest['ledger_sha256'] and probe['records'] == len(records)
    cache = DATA / 'mutation-shard-local-check' / name
    cache_files = 0
    with tarfile.open(folder / 'cache.tar.gz','r:gz') as archive:
        for info in archive.getmembers():
            rel = Path(info.name)
            assert not rel.is_absolute() and '..' not in rel.parts
            assert not info.issym() and not info.islnk()
            if info.isfile():
                assert archive.extractfile(info).read() == (cache / info.name).read_bytes()
                cache_files += 1
    log_path = DATA / 'job-logs' / (str(job['id'])+'.txt')
    lines = log_path.read_text().splitlines()
    assert audit['job_log_sha256'] == sha(log_path.read_bytes())
    negative_line = audit['negative_probe_log']
    assert lines.count(negative_line) == 1
    at = lines.index(negative_line)
    before = [line for line in lines[:at] if '過期 stale ' in line]
    after = [line for line in lines[at+1:] if '過期 stale ' in line]
    assert '過期 stale 0' in before[-2] and '過期 stale 1' in before[-1] and '過期 stale 0' in after[0]
    guard = 'bridge executable artifact changed' if name.startswith('bridge') else 'cached binary differs from executed receipt'
    assert guard in negative_line and guard == probe['original_negative_probe']['expected']
    shard_raw = 0
    for rid,record in records.items():
        if record['verdict'] == 'retired':
            continue
        execution = record['execution']
        assert execution['head'] == HEAD and execution['tool_sha256'] == tool_sha and execution['platform'] == 'posix'
        assert sha(lf(SOURCE / record['source_file'])) == record['source_sha256']
        if name.startswith('bridge'):
            baseline, mutant = cache / '_bridge-baseline' / HEAD, cache / rid
            for binary,identity in [(baseline/'bridge',execution['baseline_identity']),
                                    (mutant/'bridge-mutant/bridge',execution['mutant_identity']),
                                    (mutant/'bridge-restored/bridge',execution['restored_identity'])]:
                sidecar = binary.with_name(binary.name+'.fingerprint.json')
                assert sha(binary.read_bytes()) == identity['exe_sha256']
                assert sha(sidecar.read_bytes()) == identity['sidecar_sha256'] and load(sidecar) == identity['sidecar']
            trials = execution.get('mutant_attempts') or [execution['mutant']]
            raw_receipts = [(baseline,execution['baseline_build']),(baseline,execution['baseline']),
                            (mutant,execution['mutant_build']),(mutant,execution['restored_build']),
                            (mutant,execution['restored']),*[(mutant,trial) for trial in trials]]
            for directory,receipt in raw_receipts:
                for stream in ['stdout','stderr']:
                    assert sha((directory/receipt[stream+'_file']).read_bytes()) == receipt[stream+'_sha256']
                if receipt.get('result') is not None:
                    markers = [line.removeprefix('GEOMETRY_BRIDGE_MUTATION_RESULT ') for line in (directory/receipt['stdout_file']).read_text().splitlines() if line.startswith('GEOMETRY_BRIDGE_MUTATION_RESULT ')]
                    assert len(markers) == 1
                    normalized = markers[0]
                    for old,new in [('/home/runner/work/geometry-axiom/geometry-axiom','<repo>'),('/home/runner/work/_temp/mutation-evidence/cache/_bridge-work/'+HEAD+'/repo','<work>'),('/home/runner/work/_temp/mutation-evidence/cache','<cache>')]:
                        normalized = normalized.replace(old,new)
                    assert strict_json(normalized) == receipt['result']
                    shard_raw += 1
            for label in ['baseline','restored']:
                receipt = execution[label]
                result = receipt['result']
                assert receipt['exit_code'] == receipt['process_returncode'] == 0 and not receipt['timed_out']
                assert result['requested'] == result['started'] and result['total'] == len(result['requested']) > 0
                assert not any(result[key] for key in ['failures','errors','skipped','expected_failures','unexpected_successes'])
            for receipt in trials:
                result = receipt['result']
                assert not receipt['timed_out'] and result['requested'] == result['started']
                assert not any(result[key] for key in ['errors','skipped','expected_failures','unexpected_successes'])
                if record['verdict'] == 'killed':
                    assert receipt['exit_code'] == receipt['process_returncode'] == 1
                    assert result['failures'] and all(row['kind']=='assertion' for row in result['failures'])
                else:
                    assert record['verdict']=='equivalent' and receipt['exit_code']==receipt['process_returncode']==0 and not result['failures']
        else:
            for binary,digest in [(cache/rid/'_mut.exe',execution['exe_sha256']),(cache/'_baseline/baseline.exe',execution['baseline_exe_sha256'])]:
                assert sha(binary.read_bytes()) == digest and load(binary.with_name(binary.name+'.fingerprint.json'))['exe_sha256'] == digest
    assert shard_raw == audit['bridge_raw_markers_reparsed']
    raw_markers += shard_raw
    shard_rows.append(dict(shard=name,records=len(records),cache_members_byte_equal=cache_files,negative_guard=guard,local_strict_exits=[0,1,0],bridge_raw_markers=shard_raw))
assert merged == ledger and raw_markers == 159 and len(shard_rows) == 7

browser_report = load(OUT / 'pr340-final-native-browser-check.json')
assert browser_report['passed'] and browser_report['integration_conclusion']=='success' and browser_report['all_browser_complete']
assert browser_report['pr_head']==HEAD and browser_report['execution_commit']==MERGE and len(browser_report['browser'])==6
result = dict(passed=True,blocking_findings=[],pr_head=HEAD,execution_commit=MERGE,execution_tree=tree,
              integration_run_id=41382015317,mutation_run_id=41382015277,both_official_conclusions='success',
              official_terminal_jobs=len(whole_logs),official_zip_count=len(zip_rows),official_zips=zip_rows,
              official_run_logs_byte_equal=whole_logs,original_verifier_exit=verify['exit_code'],
              original_verifier_summary_and_ledger_byte_equal=True,mutation_counts=summary['counts'],mutation_active=summary['active'],
              mutation_table_size=summary['table_size'],mutation_ledger_sha256=summary['ledger_sha256'],
              original_mutation_tool_sha256=tool_sha,original_supervisor_sha256=supervisor_sha,
              local_cache_probe_shards=shard_rows,bridge_raw_markers_independently_reparsed=raw_markers,
              reprobe_script_sha256=sha(probe_code.read_bytes()),browser_receipt_sha256=sha((OUT/'pr340-final-native-browser-check.json').read_bytes()),
              audit_script_sha256=sha(Path(__file__).read_bytes()),input_sha256=inputs,
              limitations=['Only saved API/artifact/log/cache bytes and read-only Git metadata reviewed. No network, source changes, product tests or binaries executed.',
                           'Canvas appended server log has one chained /sources/snapshot BrokenPipe request traceback (two exception lines); exact cause of client closure is not established. Browser result, controlled assertions, golden, exceptions and actual CI step all pass.'])
(OUT / 'pr340-terminal-adversarial-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({key:result[key] for key in ['passed','blocking_findings','official_terminal_jobs','official_zip_count','original_verifier_exit','mutation_counts','bridge_raw_markers_independently_reparsed']},ensure_ascii=False))
