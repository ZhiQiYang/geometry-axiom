from pathlib import Path

OUT = Path(__file__).resolve().parent
reference = Path('/tmp/geometry-resume-20261102/ci-followup/pr345-E79cf0f16/independent-review/E_MUTATION_REVIEW.py').read_text()
reference = reference.replace("DATA = OUT.parent", "DATA = OUT.parent.parent")
reference = reference.replace('/tmp/geometry-pr345-20261102', '/tmp/geometry-pr344-20261102')
reference = reference.replace('79cf0f16bca9ce55b2b19e793650d5e4e2e2c5e6', '503cfc59354893859ae9e6e4a6ab7c11d7972517')
reference = reference.replace('058f793590301e1e58074be072d0296d432e184b', '56250470746f8a7bf6b4a235a586f2744ae3cddf')
reference = reference.replace('41387497118', '41388718083').replace('41387497096', '41388718270')
reference = reference.replace('20261102T045557Z', '20261102T050911Z')
prefix = reference[:reference.index("assert git('rev-parse'")]
prefix += '''# Fixed Git E objects remain authoritative if the single writer has started
# the authorized ledger-only successor. No source record is relabelled to it.
identity = load(DATA / 'adoption-source-identity.json')
assert identity['source_head'] == HEAD and identity['actual_integration_checkout'] == MERGE
assert identity['source'] == str(SOURCE) and identity['mutation_run_id'] == RUN
assert identity['source_tree'] == git('rev-parse', HEAD+'^{tree}').decode().strip() == git('rev-parse', MERGE+'^{tree}').decode().strip()
assert git('show','-s','--format=%P',MERGE).decode().split() == identity['merge_parents']
source_bytes = lambda rel: git('show', HEAD+':'+rel)
lf = lambda path: source_bytes(path.relative_to(SOURCE).as_posix()).replace(b'\\r\\n',b'\\n')
observed_head = git('rev-parse','HEAD').decode().strip()
committed_changes = git('diff','--name-only',HEAD,observed_head).decode().splitlines()
working_changes = git('diff','--name-only',HEAD).decode().splitlines()
assert set(committed_changes + working_changes) <= {'tests/mutants_results.json'}
for row in identity['original_source_tools']:
    body = source_bytes(row['path'])
    assert sha(body) == row['sha256'] and sha(body.replace(b'\\r\\n',b'\\n')) == row['lf_sha256']
assert identity['source_ROOT'] == {'mutate':str(SOURCE),'binaries':str(SOURCE),'supervisor_source':str(SOURCE/'.github/scripts/mutation_evidence.py')}
supervisor = source_bytes('.github/scripts/mutation_evidence.py').decode()
assert 'ROOT = Path(__file__).resolve().parents[2]' in supervisor and 'cwd=ROOT' in supervisor
assert 'ROOT = HERE.parent' in source_bytes('tests/mutate.py').decode()
supervisor_sha = sha(lf(SOURCE/'.github/scripts/mutation_evidence.py'))
tool_sha = sha(lf(SOURCE/'tests/mutate.py')+b'\\0mutation_bridge.py\\0'+lf(SOURCE/'tests/mutation_bridge.py'))
assert identity['original_tool_sha256'] == tool_sha
assert identity['mutation_source_input_count'] == len(identity['mutation_source_hashes']) == 185
for rel,digest in identity['mutation_source_hashes'].items():
    assert sha(lf(SOURCE/rel)) == digest
assert identity['mutation_closure_sha256'] == sha('\\n'.join(rel+' '+digest for rel,digest in sorted(identity['mutation_source_hashes'].items())).encode())
assert len(identity['bridge_oracle_sha256']) == 53 and len(identity['native_build_inputs']) == 7
assert sum(len(row['inputs']) for row in identity['native_build_inputs'].values()) == identity['native_build_input_entries'] == 1369
for row in identity['native_build_inputs'].values():
    fingerprint = hashlib.sha256(row['command'].encode()+b'\\0')
    for rel in sorted(row['inputs']):
        fingerprint.update((rel+'\\0'+row['inputs'][rel]+'\\n').encode())
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
'''
middle_start = reference.index("verify = load(DATA / 'mutation-verify-receipt.json')")
middle = reference[middle_start:reference.index("result = {'passed':", middle_start)]
middle = middle.replace("(SOURCE / 'tests/mutate.py').read_text()", "source_bytes('tests/mutate.py').decode()")
middle = middle.replace("assert execution['head'] == HEAD and execution['tool_sha256'] == tool_sha and execution['platform'] == 'posix'", "assert execution['head'] == HEAD and execution['tool_sha256'] == tool_sha and execution['platform'] == 'posix'\n        assert record['closure_sha256'] == source_identity['mutation_closure_sha256']\n        if name.startswith('bridge'):\n            assert execution['oracle_sha256'] == source_identity['bridge_oracle_sha256'][rid]")
suffix = '''architecture = load(DATA/'architecture-audit.json')
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
assert sha('\\n'.join(row['path']+' '+row['lfSha256'] for row in arch_receipt['inputs']).encode())==arch_receipt['inputLfClosureSha256']==architecture['input_closure_sha256']
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
(OUT/'MUTATION_PEER.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\\n')
print(json.dumps({key:result[key] for key in ('passed','source_E','observed_working_HEAD','mutation_accepted','overall_ci_accepted','original_verifier_actual_exit','counts','ledger_sha256','official_zip_count','bridge_raw_markers_reparsed')},ensure_ascii=False))
'''
(OUT / 'MUTATION_PEER.py').write_text(prefix + middle + suffix)
