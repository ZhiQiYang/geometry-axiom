"""Verify downloaded official bytes without executing product binaries/tests."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile
import tarfile

sys.dont_write_bytecode = True

OUT = Path(__file__).resolve().parent
SOURCE = Path('/tmp/geometry-pr340-20261102')
HEAD = 'b3a248607d7eb68d3167abbb926cf491d9b35a26'
MERGE = 'fc1c9f565a2e15660e931b3884dca2220cb1b7b2'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        assert key not in result, 'duplicate JSON key: ' + key
        result[key] = value
    return result


def read_json(path):
    return json.loads(path.read_text(), object_pairs_hook=unique)


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def extract(snapshot):
    rows = []
    for kind in ['integration', 'mutation']:
        for artifact in read_json(snapshot / (kind + '-artifacts.json'))['artifacts']:
            path = OUT / 'official-zips' / f"{artifact['id']}-{artifact['name']}.zip"
            if not path.exists():
                continue
            assert artifact['workflow_run']['id'] == {'integration':41382015317, 'mutation':41382015277}[kind]
            assert artifact['workflow_run']['head_sha'] == HEAD
            digest = sha(path.read_bytes())
            assert artifact['digest'] == 'sha256:' + digest
            destination = OUT / 'extracted' / artifact['name']
            destination.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(path) as archive:
                names = archive.namelist()
                assert len(names) == len(set(names)), 'duplicate archive names'
                for info in archive.infolist():
                    member = Path(info.filename)
                    assert not member.is_absolute() and '..' not in member.parts
                    assert (info.external_attr >> 16) & 0o170000 != 0o120000, 'symlink in zip'
                archive.extractall(destination)
            rows.append({'artifact_id': artifact['id'], 'name':artifact['name'], 'zip_sha256':digest, 'github_digest_matches':True,
                         'entries': [{'path':str(p.relative_to(destination)), 'sha256':sha(p.read_bytes()), 'bytes':p.stat().st_size}
                                     for p in sorted(destination.rglob('*')) if p.is_file()]})
    save(OUT / 'artifact-byte-audit.json', {'command': 'python audit_downloads.py extract ' + str(snapshot), 'exit_code':0, 'artifacts':rows})
    print('Verified official ZIP digests and extracted', len(rows), 'artifacts')


def architecture():
    folder = OUT / 'extracted' / 'pr357-architecture-refresh'
    receipt = read_json(folder / 'product-architecture-receipt.json')
    assert receipt['schema'] == 'geometry-architecture-ci-receipt/1'
    assert receipt['sourceHead'] == HEAD and receipt['runId'] == '41382015277' and receipt['runAttempt'] == '1'
    assert receipt['adoptedMain'] == '8f82b207e87c086705a1d8b7a00e2f215c07cbcf' and receipt['complete'] is True
    commands = [
        ['<python>','-B','tests/architecture_contract.py','--root','.','--manifest','geometry-core/domain-decoupling/product-architecture.json'],
        ['<python>','-B','tests/test_architecture_contract.py'],
        ['<python>','-B','tests/test_product_architecture.py']]
    assert len(receipt['commands']) == 3
    for index, row in enumerate(receipt['commands']):
        assert row['command'] == commands[index] and row['cwd'] == '<repo>' and row['exitCode'] == 0
        assert 'completenessProblem' not in row
        for stream in ['stdout','stderr']:
            assert sha((folder / row[stream]).read_bytes()) == row[stream + 'Sha256']
        if index:
            raw = (folder / row['stderr']).read_bytes()
            count = re.search(rb'Ran (\d+) tests? in ', raw)
            assert count and int(count[1]) == row['testsRun'] > 0
            assert re.search(rb'\bOK\b', raw) and not re.search(rb'\bskipped=[1-9]\d*', raw)
    normalized = lambda path: (SOURCE / path).read_bytes().replace(b'\r\n', b'\n')
    manifest_raw = normalized('geometry-core/domain-decoupling/product-architecture.json')
    manifest = json.loads(manifest_raw, object_pairs_hook=unique)
    inputs = sorted([{'path':entry['path'], 'lfSha256':sha(normalized(entry['path']))}
                     for entry in manifest['sources'] + manifest['exclusions']], key=lambda row:row['path'])
    assert receipt['inputs'] == inputs
    assert receipt['inputLfClosureSha256'] == sha('\n'.join(row['path'] + ' ' + row['lfSha256'] for row in inputs).encode())
    assert receipt['manifestLfSha256'] == sha(manifest_raw)
    assert receipt['scannerLfSha256'] == sha(normalized('tests/architecture_contract.py'))
    for path,digest in receipt['testScriptsLfSha256'].items():
        assert digest == sha(normalized(path))
    scan_raw = (folder/'product-architecture-scan.json').read_bytes()
    assert scan_raw == (folder/'architecture-cli.stdout').read_bytes()
    assert receipt['scanSha256'] == sha(scan_raw)
    scan = json.loads(scan_raw, object_pairs_hook=unique)
    assert scan['ok'] is True and scan['diagnostics'] == []
    assert receipt['diagnosticCount'] == 0
    assert receipt['ownedCount'] == len(manifest['sources']) and receipt['exclusionCount'] == len(manifest['exclusions'])
    assert receipt['edgeCount'] == len(scan['edges'])
    result = {'command':'python audit_downloads.py architecture', 'exit_code':0, 'sourceHead':HEAD, 'run_id':41382015277, 'run_attempt':1,
              'original_commands':receipt['commands'], 'inputs':len(inputs), 'owned':receipt['ownedCount'], 'exclusions':receipt['exclusionCount'],
              'edges':receipt['edgeCount'], 'diagnostics':0, 'input_closure_sha256':receipt['inputLfClosureSha256'],
              'receipt_sha256':sha((folder/'product-architecture-receipt.json').read_bytes()), 'scan_sha256':sha(scan_raw),
              'limitations':['Only downloaded original command receipts/raw/source hashes verified; no architecture product tests were rerun locally.']}
    save(OUT/'architecture-audit.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))


def native_metadata():
    # The workflow executes a synthetic PR merge. Its tree is identical to the
    # real PR head; keep a separate metadata checkout so the source HEAD stays put.
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8')
    git = lambda *args: subprocess.check_output(['git',*args],cwd=SOURCE,env=env,text=True).strip()
    head_tree, merge_tree = git('rev-parse',HEAD+'^{tree}'), git('rev-parse',MERGE+'^{tree}')
    assert head_tree == merge_tree
    parents = git('show','-s','--format=%P',MERGE).split()
    assert parents == ['5775a9e9e46bca801a9a70aaeafcdab9f597bc4d',HEAD]
    metadata = OUT/'native-verifier-git'
    if not metadata.exists():
        subprocess.run(['git','init','--bare','--quiet',str(metadata)],check=True,env=env)
        objects = Path(git('rev-parse','--path-format=absolute','--git-path','objects'))
        (metadata/'objects/info/alternates').write_text(str(objects)+'\n')
        subprocess.run(['git','--git-dir',str(metadata),'update-ref','refs/heads/native-evidence',MERGE],check=True,env=env)
        subprocess.run(['git','--git-dir',str(metadata),'symbolic-ref','HEAD','refs/heads/native-evidence'],check=True,env=env)
    env.update(GIT_DIR=str(metadata),GIT_WORK_TREE=str(SOURCE))
    input_folder = OUT/'native-original-input'
    input_folder.mkdir(exist_ok=True)
    for index in range(1,4):
        (input_folder/f'shard-{index}.json').write_bytes((OUT/'extracted'/f'native-shard-{index}'/f'shard-{index}.json').read_bytes())
    command = [sys.executable,'-B','tests/native_shard_receipts.py','--input',str(input_folder),'--parts','3','--output',str(OUT/'native-reverified.json')]
    raw_out,raw_err = OUT/'native-reverify.stdout',OUT/'native-reverify.stderr'
    with raw_out.open('wb') as output,raw_err.open('wb') as errors:
        process = subprocess.run(command,cwd=SOURCE,env=env,stdout=output,stderr=errors)
    result = {'command':command,'cwd':str(SOURCE),'env':{k:env[k] for k in ['GIT_DIR','GIT_WORK_TREE','PYTHONDONTWRITEBYTECODE','PYTHONIOENCODING']},
              'exit_code':process.returncode,'sourceHead':HEAD,'executionHead':MERGE,'tree':head_tree,'merge_parents':parents,
              'stdout_sha256':sha(raw_out.read_bytes()),'stderr_sha256':sha(raw_err.read_bytes())}
    assert process.returncode == 0,raw_err.read_text()
    reverified = read_json(OUT/'native-reverified.json')
    official = read_json(OUT/'extracted/native-complete-coverage/native-complete.json')
    assert reverified == official
    proof_folder = OUT/'extracted/native-complete-coverage/native-sharding-proof'
    proof = read_json(proof_folder/'receipt.json')
    assert proof['passed'] is True and proof['baseline_mutant_restored_exit'] == [0,1,0]
    for row in proof['rows']:
        assert row['tests'] == 1 and row['errors'] == row['skips'] == 0
        raw = (proof_folder/(row['label']+'.log')).read_text()
        if row['label'] == 'removed':
            assert row['exit'] == row['failures'] == 1 and row['assertion_failure'] is True and row['removed'] == ['c:integrity']
            assert row['failure_ids'] == ['test_unittest_runner.NativeShardCoverage.test_partition_covers_actual_suite_registry_once']
            assert 'AssertionError' in raw and 'FAILED (failures=1)' in raw
        else:
            assert row['exit'] == row['failures'] == 0 and 'OK' in raw
    result['official_reaggregation_equal'] = True
    result['summary'] = reverified
    result['official_negative_control'] = proof
    save(OUT/'native-reverify-receipt.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))


def native_control():
    command = [sys.executable,'-B','tests/native_sharding_mutation_check.py','--output',str(OUT/'native-local-negative-control')]
    env = dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
    raw_out,raw_err = OUT/'native-control.stdout',OUT/'native-control.stderr'
    with raw_out.open('wb') as output,raw_err.open('wb') as errors:
        process = subprocess.run(command,cwd=SOURCE,env=env,stdout=output,stderr=errors)
    result = {'command':command,'cwd':str(SOURCE),'exit_code':process.returncode,
              'stdout_sha256':sha(raw_out.read_bytes()),'stderr_sha256':sha(raw_err.read_bytes())}
    assert process.returncode == 0,raw_err.read_text()
    receipt = read_json(OUT/'native-local-negative-control/receipt.json')
    assert receipt['passed'] is True and receipt['baseline_mutant_restored_exit'] == [0,1,0]
    raw = (OUT/'native-local-negative-control/removed.log').read_text()
    assert 'AssertionError' in raw and 'FAILED (failures=1)' in raw
    row = receipt['rows'][1]
    assert row['failures'] == row['exit'] == 1 and row['errors'] == row['skips'] == 0
    assert row['removed'] == ['c:integrity']
    result['receipt'] = receipt
    save(OUT/'native-control-receipt.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))


def mutation_shards(snapshot):
    spec = importlib.util.spec_from_file_location('evidence_supervisor',SOURCE/'.github/scripts/mutation_evidence.py')
    supervisor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(supervisor)
    assert supervisor.head() == HEAD
    jobs = {job['name']:job for job in read_json(snapshot/'mutation-jobs.json')['jobs']}
    expected = supervisor.shards()
    seen, merged, rows = set(), {}, []
    for folder in sorted((OUT/'extracted').glob('mutation-shard-*')):
        manifest = read_json(folder/'manifest.json')
        name = manifest['shard']
        assert name in expected and name not in seen and manifest['ids'] == expected[name]
        seen.add(name)
        assert manifest['schema'] == 'geometry-mutation-ci-shard/1' and manifest['head'] == HEAD
        assert manifest['run_id'] == '41382015277' and manifest['run_attempt'] == '1' and manifest['platform'] == 'posix'
        assert manifest['tool_sha256'] == supervisor.mt.tool_hash() and manifest['supervisor_sha256'] == supervisor.supervisor_sha()
        for filename,field in [('mutants_results.json','ledger_sha256'),('cache.tar.gz','cache_sha256'),('execution.log','execution_log_sha256')]:
            assert sha((folder/filename).read_bytes()) == manifest[field]
        records = read_json(folder/'mutants_results.json')
        assert set(records) == set(expected[name]) and not set(records)&set(merged)
        for record in records.values():
            if record['verdict'] != 'retired':assert record['execution']['head'] == HEAD and record['execution']['platform'] == 'posix'
        probe = manifest['negative_cache_probe']
        assert probe['strict_exit'] == 1 and probe['id'] in expected[name] and records[probe['id']]['verdict'] != 'retired'
        guard = 'bridge executable artifact changed' if name.startswith('bridge') else 'cached binary differs from executed receipt'
        assert probe['expected'] == guard
        job = jobs[f'mutation ({name})']
        assert job['status'] == 'completed' and job['conclusion'] == 'success'
        log_path = OUT/'job-logs'/f"{job['id']}.txt"
        log_lines = log_path.read_text().splitlines()
        stale_lines = [line for line in log_lines if 'STALE '+probe['id']+'(' in line and guard in line]
        assert len(stale_lines) == 1
        stale_index = log_lines.index(stale_lines[0])
        assert any('過期 stale 1' in line for line in log_lines[max(0,stale_index-3):stale_index])
        assert any('過期 stale 0' in line for line in log_lines[stale_index+1:stale_index+5])
        assert any(line.endswith(' '+HEAD) and 'Z ' in line for line in log_lines)
        cache = OUT/'mutation-shard-local-check'/name
        if not cache.exists():
            cache.mkdir(parents=True)
            with tarfile.open(folder/'cache.tar.gz','r:gz') as archive:
                archive.extractall(cache,filter='data')
        mutants = supervisor.selected(expected[name])
        supervisor.require_binaries(mutants,records,cache)
        supervisor.strict_check(mutants,folder/'mutants_results.json',cache)
        raw_markers = 0
        if name.startswith('bridge'):
            import mutation_bridge
            for rid,record in records.items():
                if record['verdict']=='retired':continue
                execution = record['execution']
                base_dir = cache/'_bridge-baseline'/HEAD
                mutant_dir = cache/rid
                receipts = [(base_dir,execution['baseline']), (mutant_dir,execution['restored'])]
                receipts += [(mutant_dir,trial) for trial in execution.get('mutant_attempts') or [execution['mutant']]]
                work_marker = execution['baseline']['command'][3].split('/_bridge-baseline/')[0] if '/_bridge-baseline/' in execution['baseline']['command'][3] else None
                for raw_folder,receipt in receipts:
                    markers = [line.removeprefix('GEOMETRY_BRIDGE_MUTATION_RESULT ') for line in (raw_folder/receipt['stdout_file']).read_text(errors='replace').splitlines() if line.startswith('GEOMETRY_BRIDGE_MUTATION_RESULT ')]
                    assert len(markers)==1
                    # Structured success/failure method data has no filesystem
                    # paths except portable traceback details. Canonicalize
                    # runner paths exactly as the unchanged official backend.
                    normalized = markers[0]
                    for old,new in [('/home/runner/work/geometry-axiom/geometry-axiom','<repo>'),('/home/runner/work/_temp/mutation-evidence/cache/_bridge-work/'+HEAD+'/repo','<work>'),('/home/runner/work/_temp/mutation-evidence/cache','<cache>')]:
                        normalized = normalized.replace(old,new)
                    assert json.loads(normalized,object_pairs_hook=unique) == receipt['result'],(rid,receipt['stdout_file'])
                    raw_markers += 1
        rows.append({'shard':name,'ids':manifest['ids'],'records':len(records),'counts':dict(Counter(record['verdict'] for record in records.values())),
                     'binary_bytes_and_sidecars_verified':True,'strict_exit':0,'negative_probe':probe,'negative_probe_log':stale_lines[0],
                     'job_id':job['id'],'job_log_sha256':sha(log_path.read_bytes()),'bridge_raw_markers_reparsed':raw_markers})
        merged.update(records)
    result={'command':'python audit_downloads.py mutation '+str(snapshot),'exit_code':0,'head':HEAD,'run_id':41382015277,'run_attempt':1,
            'complete':seen==set(expected),'downloaded_shards':len(rows),'records':len(merged),'counts':dict(Counter(row['verdict'] for row in merged.values())),
            'shards':rows,'missing_shards':sorted(set(expected)-seen)}
    save(OUT/'mutation-shard-audit.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))


def mutation_verify():
    command = [sys.executable,'-B','.github/scripts/mutation_evidence.py','verify','--artifacts',str(OUT/'extracted'),'--out',str(OUT/'mutation-local-verified')]
    raw_out,raw_err = OUT/'mutation-verify.stdout',OUT/'mutation-verify.stderr'
    with raw_out.open('wb') as output,raw_err.open('wb') as errors:
        process = subprocess.run(command,cwd=SOURCE,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=output,stderr=errors)
    result = {'command':command,'cwd':str(SOURCE),'exit_code':process.returncode,
              'stdout_sha256':sha(raw_out.read_bytes()),'stderr_sha256':sha(raw_err.read_bytes())}
    assert process.returncode == 0,raw_err.read_text()
    local = read_json(OUT/'mutation-local-verified/summary.json')
    official = read_json(OUT/'extracted/mutation-complete-evidence/summary.json')
    local_ledger = (OUT/'mutation-local-verified/mutants_results.json').read_bytes()
    official_ledger = (OUT/'extracted/mutation-complete-evidence/mutants_results.json').read_bytes()
    assert local == official and local_ledger == official_ledger
    assert (OUT/'mutation-local-verified/summary.json').read_bytes() == (OUT/'extracted/mutation-complete-evidence/summary.json').read_bytes()
    result['head'] = HEAD
    result['summary'] = local
    result['official_summary_and_ledger_byte_equal'] = True
    result['ledger_sha256'] = sha(local_ledger)
    result['summary_sha256'] = sha((OUT/'mutation-local-verified/summary.json').read_bytes())
    result['limitations'] = ['Verification reads original artifact binary bytes and sidecars without executing or rebuilding downloaded binaries.']
    save(OUT/'mutation-verify-receipt.json',result)
    print(json.dumps({key:value for key,value in result.items() if key!='summary'},ensure_ascii=False,indent=2))
    print(json.dumps({key:value for key,value in local.items() if key!='shards'},ensure_ascii=False,indent=2))


def terminal_logs(snapshot):
    rows=[]
    for kind,run_id in [('integration',41382015317),('mutation',41382015277)]:
        jobs=read_json(snapshot/f'{kind}-jobs.json')['jobs']
        archive_path=OUT/f'official-run-logs/{kind}-{run_id}.zip'
        with zipfile.ZipFile(archive_path) as archive:
            for job in jobs:
                sanitized=job['name'].replace('/','_')
                paths=[name for name in archive.namelist() if re.fullmatch(r'\d+_'+re.escape(sanitized)+r'\.txt',name)]
                assert len(paths)==1,(job['name'],paths)
                zipped=archive.read(paths[0])
                direct=(OUT/f'job-logs/{job["id"]}.txt').read_bytes()
                assert zipped==direct,(job['name'],len(zipped),len(direct))
                rows.append({'run_id':run_id,'job_id':job['id'],'name':job['name'],'archive_member':paths[0],
                             'bytes':len(direct),'sha256':sha(direct),'byte_equal':True})
    save(OUT/'official-run-log-audit.json',{'command':'python audit_downloads.py terminal-logs '+str(snapshot),'exit_code':0,'jobs':rows})
    print(len(rows),'terminal run ZIP whole-job logs byte-equal to direct endpoint originals')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode',choices=['extract','architecture','native','native-control','mutation','mutation-verify','terminal-logs'])
    parser.add_argument('snapshot',nargs='?')
    args = parser.parse_args()
    if args.mode == 'extract':extract(Path(args.snapshot))
    elif args.mode == 'architecture':architecture()
    elif args.mode == 'native':native_metadata()
    elif args.mode == 'native-control':native_control()
    elif args.mode == 'mutation-verify':mutation_verify()
    elif args.mode == 'terminal-logs':terminal_logs(Path(args.snapshot))
    else:mutation_shards(Path(args.snapshot))
