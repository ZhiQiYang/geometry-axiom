import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess

OUT = Path(__file__).resolve().parent
DATA = OUT.parent.parent / 'pr345'
SOURCE = Path('/tmp/geometry-pr345-20261102')
HEAD = '577b2e81967b3019352f65df5ffe6dc48eb6202f'
MERGE = 'f75739691f4e0d8fb73e82c22074922d8766e601'
RUN = 41382891805
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
assert provenance['execution_head'] == MERGE and provenance['integration_run_id'] == 41382891799
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


import tarfile
import zipfile
snapshot = DATA / 'api/20261102T035855Z'
api_jobs, zip_rows, job_logs = {}, [], []
for kind, run_id in [('integration',41382891799),('mutation',41382891805)]:
    run = load(snapshot / (kind+'-run.json'))
    assert run['id'] == run_id and run['head_sha'] == HEAD and run['run_attempt'] == 1
    jobs = load(snapshot / (kind+'-jobs.json'))['jobs']
    assert len(jobs) == 10
    if kind == 'mutation':
        assert run['status']=='completed' and run['conclusion']=='success'
        assert all(job['status']=='completed' and job['conclusion']=='success' for job in jobs)
    else:
        assert run['status']=='in_progress' and run['conclusion'] is None
        assert {job['name'] for job in jobs if job['conclusion']=='failure'} == {'native (2/3)','native complete coverage'}
        assert {job['name'] for job in jobs if job['status']!='completed'} == {'browser (canvas)'}
    api_jobs[kind] = {job['name']:job for job in jobs}
    if kind == 'mutation':
        for job in jobs:
            log_path = DATA / 'job-logs' / (str(job['id'])+'.txt')
            assert log_path.is_file()
            job_logs.append(dict(id=job['id'],name=job['name'],conclusion=job['conclusion'],sha256=sha(log_path.read_bytes())))
    for artifact in load(snapshot / (kind+'-artifacts.json'))['artifacts']:
        archive_path = DATA / 'official-zips' / f"{artifact['id']}-{artifact['name']}.zip"
        assert artifact['workflow_run']['id']==run_id and artifact['workflow_run']['head_sha']==HEAD
        assert artifact['digest']=='sha256:'+sha(archive_path.read_bytes())
        with zipfile.ZipFile(archive_path) as archive:
            assert len(archive.namelist()) == len(set(archive.namelist()))
            members = 0
            for info in archive.infolist():
                rel = Path(info.filename)
                assert not rel.is_absolute() and '..' not in rel.parts and (info.external_attr >> 16) & 0o170000 != 0o120000
                if not info.is_dir():
                    assert archive.read(info.filename) == (DATA / 'extracted' / artifact['name'] / info.filename).read_bytes()
                    members += 1
            if artifact['name']=='native-complete-coverage':
                assert 'native-complete.json' not in archive.namelist()
        zip_rows.append(dict(kind=kind,run_id=run_id,id=artifact['id'],name=artifact['name'],digest=artifact['digest'],members=members))
assert len(zip_rows)==19 and len(job_logs)==10

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


prior_native = load(OUT / 'pr345-independent-native-browser-check.json')
assert prior_native['audit_passed'] and prior_native['native_accepted'] is False
assert prior_native['pr_head']==HEAD and prior_native['execution_commit']==MERGE
rejection = load(DATA / 'native-rejection-receipt.json')
assert rejection['sourceHead']==HEAD and rejection['executionHead']==MERGE and rejection['exit_code']==1
assert rejection['native_complete_summary_present'] is False and not (DATA / 'extracted/native-complete-coverage/native-complete.json').exists()
for stream in ['stdout','stderr']:
    assert rejection[stream+'_sha256']==sha((DATA / ('native-reverify.'+stream)).read_bytes())
result = dict(passed=True,mutation_accepted=True,overall_ci_accepted=False,blocking_findings=[],
              pr_head=HEAD,execution_commit=MERGE,execution_tree=tree,
              integration_run_id=41382891799,mutation_run_id=41382891805,
              mutation_official_conclusion='success',integration_official_status='in_progress',integration_official_conclusion=None,
              integration_failed_jobs=['native (2/3)','native complete coverage'],integration_pending_jobs=['browser (canvas)'],
              official_mutation_terminal_jobs=job_logs,official_zip_count=len(zip_rows),official_zips=zip_rows,
              original_verifier_exit=verify['exit_code'],original_verifier_summary_and_ledger_byte_equal=True,
              mutation_counts=summary['counts'],mutation_active=summary['active'],mutation_table_size=summary['table_size'],
              mutation_ledger_sha256=summary['ledger_sha256'],original_mutation_tool_sha256=tool_sha,original_supervisor_sha256=supervisor_sha,
              local_cache_probe_shards=shard_rows,bridge_raw_markers_independently_reparsed=raw_markers,
              reprobe_script_sha256=sha(probe_code.read_bytes()),native_rejection_actual_exit=rejection['exit_code'],
              prior_native_raw_review_sha256=sha((OUT/'pr345-independent-native-browser-check.json').read_bytes()),
              audit_script_sha256=sha(Path(__file__).read_bytes()),input_sha256=inputs,
              limitations=['The original mutation workflow passes at this source head. Integration remains failed in native2/complete and pending in canvas; no overall green claim.',
                           'Only saved API/artifact/log/cache bytes and read-only Git metadata reviewed. No network, source changes, product tests or binaries executed.'])
(OUT / 'pr345-mutation-terminal-adversarial-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({key:result[key] for key in ['passed','mutation_accepted','overall_ci_accepted','official_zip_count','original_verifier_exit','mutation_counts','bridge_raw_markers_independently_reparsed']},ensure_ascii=False))
