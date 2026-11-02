"""Bounded pure-read audit of E Mutation artifacts; executes no source code."""
import ast
from collections import Counter
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile
import zipfile

OUT = Path(__file__).resolve().parent
DATA = OUT.parent.parent
SOURCE = Path('/tmp/geometry-pr344-20261102')
HEAD = '503cfc59354893859ae9e6e4a6ab7c11d7972517'
MERGE = '56250470746f8a7bf6b4a235a586f2744ae3cddf'
RUN = 41388718083
SNAPSHOT = DATA / 'api/20261102T050911Z'
inputs = {}
sha = lambda raw: hashlib.sha256(raw).hexdigest()
lf = lambda path: path.read_bytes().replace(b'\r\n', b'\n')
git = lambda *args: subprocess.check_output(['git', *args], cwd=SOURCE)


def load(path):
    raw = path.read_bytes()
    inputs[str(path)] = sha(raw)
    def unique(pairs):
        result = {}
        for key, value in pairs:
            assert key not in result, 'duplicate JSON key: ' + key
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)


def strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            assert key not in result, 'duplicate JSON key: ' + key
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)


# Fixed Git E objects remain authoritative if the single writer has started
# the authorized ledger-only successor. No source record is relabelled to it.
identity = load(DATA / 'adoption-source-identity.json')
assert identity['source_head'] == HEAD and identity['actual_integration_checkout'] == MERGE
assert identity['source'] == str(SOURCE) and identity['mutation_run_id'] == RUN
assert identity['source_tree'] == git('rev-parse', HEAD+'^{tree}').decode().strip() == git('rev-parse', MERGE+'^{tree}').decode().strip()
assert git('show','-s','--format=%P',MERGE).decode().split() == identity['merge_parents']
source_bytes = lambda rel: git('show', HEAD+':'+rel)
lf = lambda path: source_bytes(path.relative_to(SOURCE).as_posix()).replace(b'\r\n',b'\n')
observed_head = git('rev-parse','HEAD').decode().strip()
committed_changes = git('diff','--name-only',HEAD,observed_head).decode().splitlines()
working_changes = git('diff','--name-only',HEAD).decode().splitlines()
assert set(committed_changes + working_changes) <= {'tests/mutants_results.json'}
for row in identity['original_source_tools']:
    body = source_bytes(row['path'])
    assert sha(body) == row['sha256'] and sha(body.replace(b'\r\n',b'\n')) == row['lf_sha256']
assert identity['source_ROOT'] == {'mutate':str(SOURCE),'binaries':str(SOURCE),'supervisor_source':str(SOURCE/'.github/scripts/mutation_evidence.py')}
supervisor = source_bytes('.github/scripts/mutation_evidence.py').decode()
assert 'ROOT = Path(__file__).resolve().parents[2]' in supervisor and 'cwd=ROOT' in supervisor
assert 'ROOT = HERE.parent' in source_bytes('tests/mutate.py').decode()
supervisor_sha = sha(lf(SOURCE/'.github/scripts/mutation_evidence.py'))
tool_sha = sha(lf(SOURCE/'tests/mutate.py')+b'\0mutation_bridge.py\0'+lf(SOURCE/'tests/mutation_bridge.py'))
assert identity['original_tool_sha256'] == tool_sha
assert identity['mutation_source_input_count'] == len(identity['mutation_source_hashes']) == 185
for rel,digest in identity['mutation_source_hashes'].items():
    assert sha(lf(SOURCE/rel)) == digest
assert identity['mutation_closure_sha256'] == sha('\n'.join(rel+' '+digest for rel,digest in sorted(identity['mutation_source_hashes'].items())).encode())
assert len(identity['bridge_oracle_sha256']) == 53 and len(identity['native_build_inputs']) == 7
assert sum(len(row['inputs']) for row in identity['native_build_inputs'].values()) == identity['native_build_input_entries'] == 1369
for row in identity['native_build_inputs'].values():
    fingerprint = hashlib.sha256(row['command'].encode()+b'\0')
    for rel in sorted(row['inputs']):
        fingerprint.update((rel+'\0'+row['inputs'][rel]+'\n').encode())
    assert fingerprint.hexdigest() == row['fingerprint']
api_jobs,zip_rows = {},[]
for kind,run_id in [('integration',41388718270),('mutation',RUN)]:
    run = load(SNAPSHOT/(kind+'-run.json'))
    assert run['id']==run_id and run['head_sha']==HEAD and run['run_attempt']==1 and run['status']=='completed'
    jobs = load(SNAPSHOT/(kind+'-jobs.json'))['jobs']
    assert len(jobs)==10 and all(row['status']=='completed' for row in jobs)
    if kind=='mutation':
        assert run['conclusion']=='success' and all(row['conclusion']=='success' for row in jobs)
    else:
        assert run['conclusion']=='failure'
        assert {row['name'] for row in jobs if row['conclusion']!='success'} == {'native (2/3)','native complete coverage'}
    api_jobs[kind] = {row['name']:row for row in jobs}
    for artifact in load(SNAPSHOT/(kind+'-artifacts.json'))['artifacts']:
        path=DATA/'official-zips'/f"{artifact['id']}-{artifact['name']}.zip"
        assert artifact['workflow_run']['id']==run_id and artifact['workflow_run']['head_sha']==HEAD
        assert artifact['digest']=='sha256:'+sha(path.read_bytes())
        zip_rows.append({'kind':kind,'id':artifact['id'],'name':artifact['name'],'digest':artifact['digest']})
assert len(zip_rows)==21
source_identity = identity
verify = load(DATA / 'mutation-verify-receipt.json')
assert verify['cwd'] == str(SOURCE) and verify['head'] == HEAD and verify['exit_code'] == 0
assert verify['command'][1:] == ['-B', '.github/scripts/mutation_evidence.py', 'verify', '--artifacts', str(DATA / 'extracted'), '--out', str(DATA / 'mutation-local-verified')]
for stream in ('stdout', 'stderr'):
    assert verify[stream + '_sha256'] == sha((DATA / ('mutation-verify.' + stream)).read_bytes())
official = DATA / 'extracted/mutation-complete-evidence'
local = DATA / 'mutation-local-verified'
for name in ('summary.json', 'mutants_results.json'):
    assert (official / name).read_bytes() == (local / name).read_bytes()
summary, ledger = load(official / 'summary.json'), load(official / 'mutants_results.json')
assert summary == verify['summary'] and summary['schema'] == 'geometry-mutation-ci-summary/1' and summary['head'] == HEAD
assert summary['table_size'] == len(ledger) == 123 and summary['active'] == sum(row['verdict'] != 'retired' for row in ledger.values()) == 120
assert summary['ledger_sha256'] == verify['ledger_sha256'] == sha((official / 'mutants_results.json').read_bytes())
assert verify['official_summary_and_ledger_byte_equal'] and verify['summary_sha256'] == sha((official / 'summary.json').read_bytes())
assert summary['binary_bytes_verified'] is True and summary['full_table_strict_exit'] == 0
counts = Counter(row['verdict'] for row in ledger.values())
assert {key: value for key, value in summary['counts'].items() if value} == dict(counts)
assert all(summary['counts'][key] == 0 for key in ('survived', 'invalid', 'stale', 'blocked', 'unrun'))

# Derive exactly the unchanged current source table and seven shard assignments
# from AST; never import the source runner or execute any mutation.
mutants = []
for node in ast.parse(source_bytes('tests/mutate.py').decode()).body:
    value = None
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'MUTANTS' for t in node.targets):
        value = node.value
    elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name) and node.target.id == 'MUTANTS':
        value = node.value
    if value is not None:
        assert isinstance(value, ast.List)
        for call in value.elts:
            fields = {kw.arg: kw.value for kw in call.keywords}
            mutants.append({'id': ast.literal_eval(fields['id']), 'binary': ast.literal_eval(fields['binary']) if 'binary' in fields else 'core'})
assert len(mutants) == len({row['id'] for row in mutants}) == 123 and set(ledger) == {row['id'] for row in mutants}
plans = {}
for kind, parts in [('core', 4), ('bridge', 3)]:
    ids = [row['id'] for row in mutants if row['binary'] == kind]
    for index in range(parts):
        plans[kind + '-' + str(index + 1)] = ids[index::parts]
shard_audit = load(DATA / 'mutation-shard-audit.json')
assert shard_audit['exit_code'] == 0 and shard_audit['complete'] and shard_audit['missing_shards'] == []
assert shard_audit['head'] == HEAD and shard_audit['run_id'] == RUN and shard_audit['run_attempt'] == 1 and shard_audit['records'] == 123
merged, shard_rows, raw_markers = {}, [], 0
for shard_manifest in summary['shards']:
    name = shard_manifest['shard']
    folder = DATA / 'extracted' / ('mutation-shard-' + name)
    manifest = load(folder / 'manifest.json')
    assert manifest == shard_manifest and manifest['ids'] == plans[name]
    assert manifest['schema'] == 'geometry-mutation-ci-shard/1' and manifest['head'] == HEAD
    assert manifest['run_id'] == str(RUN) and manifest['run_attempt'] == '1' and manifest['platform'] == 'posix'
    assert manifest['tool_sha256'] == tool_sha and manifest['supervisor_sha256'] == supervisor_sha
    for filename, field in [('mutants_results.json', 'ledger_sha256'), ('cache.tar.gz', 'cache_sha256'), ('execution.log', 'execution_log_sha256')]:
        assert sha((folder / filename).read_bytes()) == manifest[field]
    records = load(folder / 'mutants_results.json')
    assert set(records) == set(plans[name]) and not set(records) & set(merged)
    assert all(ledger[rid] == record for rid, record in records.items())
    merged.update(records)
    audit = next(row for row in shard_audit['shards'] if row['shard'] == name)
    job = api_jobs['mutation']['mutation (' + name + ')']
    assert audit['job_id'] == job['id'] and audit['strict_exit'] == 0 and audit['binary_bytes_and_sidecars_verified']
    assert audit['negative_probe'] == manifest['negative_cache_probe'] and manifest['negative_cache_probe']['strict_exit'] == 1
    cache, cache_files = DATA / 'mutation-shard-local-check' / name, 0
    with tarfile.open(folder / 'cache.tar.gz', 'r:gz') as archive:
        for info in archive.getmembers():
            rel = Path(info.name)
            assert not rel.is_absolute() and '..' not in rel.parts and not info.issym() and not info.islnk()
            if info.isfile():
                assert archive.extractfile(info).read() == (cache / info.name).read_bytes()
                cache_files += 1
    log_path = DATA / 'job-logs' / (str(job['id']) + '.txt')
    lines = log_path.read_text().splitlines()
    assert audit['job_log_sha256'] == sha(log_path.read_bytes()) and any(line.endswith(' ' + HEAD) for line in lines)
    negative_line = audit['negative_probe_log']
    assert lines.count(negative_line) == 1
    at = lines.index(negative_line)
    before = [line for line in lines[:at] if '過期 stale ' in line]
    after = [line for line in lines[at + 1:] if '過期 stale ' in line]
    assert '過期 stale 0' in before[-2] and '過期 stale 1' in before[-1] and '過期 stale 0' in after[0]
    guard = 'bridge executable artifact changed' if name.startswith('bridge') else 'cached binary differs from executed receipt'
    assert guard in negative_line and guard == manifest['negative_cache_probe']['expected']
    shard_raw = 0
    for rid, record in records.items():
        if record['verdict'] == 'retired':
            continue
        execution = record['execution']
        assert execution['head'] == HEAD and execution['tool_sha256'] == tool_sha and execution['platform'] == 'posix'
        assert record['closure_sha256'] == source_identity['mutation_closure_sha256']
        if name.startswith('bridge'):
            assert execution['oracle_sha256'] == source_identity['bridge_oracle_sha256'][rid]
        assert sha(lf(SOURCE / record['source_file'])) == record['source_sha256']
        if name.startswith('bridge'):
            baseline, mutant = cache / '_bridge-baseline' / HEAD, cache / rid
            for binary, identity in [(baseline / 'bridge', execution['baseline_identity']), (mutant / 'bridge-mutant/bridge', execution['mutant_identity']), (mutant / 'bridge-restored/bridge', execution['restored_identity'])]:
                sidecar = binary.with_name(binary.name + '.fingerprint.json')
                assert sha(binary.read_bytes()) == identity['exe_sha256']
                assert sha(sidecar.read_bytes()) == identity['sidecar_sha256'] and load(sidecar) == identity['sidecar']
            trials = execution.get('mutant_attempts') or [execution['mutant']]
            raw_receipts = [(baseline, execution['baseline_build']), (baseline, execution['baseline']), (mutant, execution['mutant_build']), (mutant, execution['restored_build']), (mutant, execution['restored']), *[(mutant, trial) for trial in trials]]
            for directory, receipt in raw_receipts:
                for stream in ('stdout', 'stderr'):
                    assert sha((directory / receipt[stream + '_file']).read_bytes()) == receipt[stream + '_sha256']
                if receipt.get('result') is not None:
                    markers = [line.removeprefix('GEOMETRY_BRIDGE_MUTATION_RESULT ') for line in (directory / receipt['stdout_file']).read_text().splitlines() if line.startswith('GEOMETRY_BRIDGE_MUTATION_RESULT ')]
                    assert len(markers) == 1
                    normalized = markers[0]
                    for old, new in [('/home/runner/work/geometry-axiom/geometry-axiom', '<repo>'), ('/home/runner/work/_temp/mutation-evidence/cache/_bridge-work/' + HEAD + '/repo', '<work>'), ('/home/runner/work/_temp/mutation-evidence/cache', '<cache>')]:
                        normalized = normalized.replace(old, new)
                    assert strict_json(normalized) == receipt['result']
                    shard_raw += 1
            for label in ('baseline', 'restored'):
                receipt, result = execution[label], execution[label]['result']
                assert receipt['exit_code'] == receipt['process_returncode'] == 0 and not receipt['timed_out']
                assert result['requested'] == result['started'] and result['total'] == len(result['requested']) > 0
                assert not any(result[key] for key in ('failures', 'errors', 'skipped', 'expected_failures', 'unexpected_successes'))
            for receipt in trials:
                result = receipt['result']
                assert not receipt['timed_out'] and result['requested'] == result['started']
                assert not any(result[key] for key in ('errors', 'skipped', 'expected_failures', 'unexpected_successes'))
                if record['verdict'] == 'killed':
                    assert receipt['exit_code'] == receipt['process_returncode'] == 1 and result['failures']
                    assert all(row['kind'] == 'assertion' for row in result['failures'])
                else:
                    assert record['verdict'] == 'equivalent' and receipt['exit_code'] == receipt['process_returncode'] == 0 and not result['failures']
        else:
            for binary, digest in [(cache / rid / '_mut.exe', execution['exe_sha256']), (cache / '_baseline/baseline.exe', execution['baseline_exe_sha256'])]:
                assert sha(binary.read_bytes()) == digest and load(binary.with_name(binary.name + '.fingerprint.json'))['exe_sha256'] == digest
    assert shard_raw == audit['bridge_raw_markers_reparsed']
    raw_markers += shard_raw
    shard_rows.append(dict(shard=name, records=len(records), cache_members_byte_equal=cache_files,
                           official_negative_guard=guard, official_strict_before_probe_after=[0, 1, 0],
                           local_negative_control_reexecuted=False, bridge_raw_markers=shard_raw))
assert merged == ledger and raw_markers == 159 and len(shard_rows) == 7

# Read only the new Mutation run ZIP's ten whole-job members. Integration/raw
# native/browser parsing remains bound to the earlier passed independent review.
whole_logs = load(DATA / 'official-run-log-audit.json')
assert whole_logs['exit_code'] == 0 and len(whole_logs['jobs']) == 20
with zipfile.ZipFile(DATA / f'official-run-logs/mutation-{RUN}.zip') as archive:
    for job in api_jobs['mutation'].values():
        direct = (DATA / 'job-logs' / (str(job['id']) + '.txt')).read_bytes()
        row = next(row for row in whole_logs['jobs'] if row['job_id'] == job['id'])
        assert row['run_id'] == RUN and row['byte_equal'] and row['sha256'] == sha(direct)
        assert archive.read(row['archive_member']) == direct
architecture = load(DATA/'architecture-audit.json')
assert architecture['sourceHead']==HEAD and architecture['run_id']==RUN and architecture['exit_code']==0 and architecture['inputs']==604
arch_folder=DATA/'extracted/pr357-architecture-refresh'
arch_receipt=load(arch_folder/'product-architecture-receipt.json')
assert arch_receipt['sourceHead']==HEAD and arch_receipt['runId']==str(RUN) and arch_receipt['complete']
assert sha((arch_folder/'product-architecture-receipt.json').read_bytes())==architecture['receipt_sha256']
assert len(architecture['original_commands'])==3 and architecture['original_commands']==arch_receipt['commands']
for command in arch_receipt['commands']:
    assert command['exitCode']==0 and command['cwd']=='<repo>'
    for stream in ('stdout','stderr'):
        assert sha((arch_folder/command[stream]).read_bytes())==command[stream+'Sha256']
assert len(arch_receipt['inputs'])==604
assert sha('\n'.join(row['path']+' '+row['lfSha256'] for row in arch_receipt['inputs']).encode())==arch_receipt['inputLfClosureSha256']==architecture['input_closure_sha256']
result={'passed':True,'blocking_findings':[],'source_E':HEAD,'actual_integration_checkout':MERGE,'source_tree':source_identity['source_tree'],
        'observed_working_HEAD':observed_head,'working_or_committed_changes_since_E':sorted(set(committed_changes+working_changes)),
        'artifact_source_not_relabelled':True,'mutation_accepted':True,'overall_ci_accepted':False,
        'integration_run_id':41388718270,'integration_conclusion':'failure','integration_failed_jobs':['native (2/3)','native complete coverage'],
        'mutation_run_id':RUN,'mutation_conclusion':'success','original_verifier_actual_exit':verify['exit_code'],
        'original_verifier_command':verify['command'],'original_verifier_cwd':verify['cwd'],
        'original_verifier_stdout_sha256':verify['stdout_sha256'],'original_verifier_stderr_sha256':verify['stderr_sha256'],
        'official_summary_ledger_byte_equal':True,'table_size':summary['table_size'],'active':summary['active'],'counts':summary['counts'],
        'ledger_sha256':verify['ledger_sha256'],'summary_sha256':verify['summary_sha256'],
        'official_zip_count':len(zip_rows),'official_zip_mapping':zip_rows,'original_tool_sha256':tool_sha,'original_supervisor_sha256':supervisor_sha,
        'mutation_source_input_count':185,'mutation_closure_sha256':source_identity['mutation_closure_sha256'],'bridge_oracle_identities':53,
        'native_build_fingerprints':7,'native_build_input_identities':1369,'architecture_original_command_exits':[0,0,0],'architecture_inputs':604,
        'official_negative_control_shards':shard_rows,'bridge_raw_markers_reparsed':raw_markers,
        'source_tests_validators_or_products_reexecuted':False,'audit_script_sha256':sha(Path(__file__).read_bytes()),'input_sha256':inputs,
        'scope':'Bounded pure read of saved receipts/Git E objects/artifact bytes/official raw outcomes; no source runner imports, validator reruns, product/native/browser/build/compiler/API/local negative-control execution or source edits. Other agent owns native/browser review.'}
(OUT/'MUTATION_PEER.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({key:result[key] for key in ('passed','source_E','observed_working_HEAD','mutation_accepted','overall_ci_accepted','original_verifier_actual_exit','counts','ledger_sha256','official_zip_count','bridge_raw_markers_reparsed')},ensure_ascii=False))
