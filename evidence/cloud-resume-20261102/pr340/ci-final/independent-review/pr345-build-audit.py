from pathlib import Path

OUT = Path(__file__).resolve().parent
source = (OUT / 'check_current_native_browser.py').read_text()
prefix = source[:source.index('summary = load(EXTRACTED / "native-complete-coverage/native-complete.json")')]
prefix = prefix.replace('ROOT = OUT.parent', "ROOT = OUT.parent.parent / 'pr345'")
prefix = prefix.replace('/tmp/geometry-pr340-20261102', '/tmp/geometry-pr345-20261102')
prefix = prefix.replace('b3a248607d7eb68d3167abbb926cf491d9b35a26', '577b2e81967b3019352f65df5ffe6dc48eb6202f')
prefix = prefix.replace('fc1c9f565a2e15660e931b3884dca2220cb1b7b2', 'f75739691f4e0d8fb73e82c22074922d8766e601')
prefix = prefix.replace('20261102T033519Z', '20261102T034113Z').replace('pr340.json', 'pr345.json')
prefix = prefix.replace('part["commit_sha"] == MERGE and part["exit_code"] == 0', 'part["commit_sha"] == MERGE and part["exit_code"] == (1 if shard == 2 else 0)')
prefix = prefix.replace('row["ran"] and row["process_exit_code"] == 0 and row["failed"] == 0', 'row["ran"] and row["process_exit_code"] == (1 if name == "mutation:check" else 0) and row["failed"] == (1 if name == "mutation:check" else 0)')
prefix = prefix.replace('"過期 stale 0 / 受阻 blocked 0" in output', '"過期 stale 53 / 受阻 blocked 0" in output')
proof_start = source.index('proof_folder = EXTRACTED / "native-complete-coverage/native-sharding-proof"')
proof_end = source.index('native_job_logs = []')
prefix += source[proof_start:proof_end]
suffix = r'''
import subprocess
import zipfile

bad_rows = [row for row in all_rows if row['failed'] or row['process_exit_code'] or row['crashed'] or row['env_problem']]
require(len(bad_rows) == 1 and bad_rows[0]['name'] == 'mutation:check' and bad_rows[0]['process_exit_code'] == 1,
        'one explicit freshness failure preserved, not a green native aggregate')
native_job_logs = []
for job in jobs:
    if not job['name'].startswith('native'):
        continue
    if job['name'] == 'native complete coverage' and job['status'] != 'completed':
        require(job['status'] in ('queued','in_progress') and job['conclusion'] is None,
                'official complete coverage remains pending in saved snapshot')
        native_job_logs.append(dict(name=job['name'],id=job['id'],status=job['status'],conclusion=None))
        continue
    expected_failure = job['name'] in ('native (2/3)', 'native complete coverage')
    require(job['status'] == 'completed' and job['conclusion'] == ('failure' if expected_failure else 'success'),
            job['name'] + ' official actual conclusion')
    log_path = ROOT / 'job-logs' / (str(job['id']) + '.txt')
    log = raw(log_path)
    lines = [line.partition('Z ')[2] for line in log.splitlines()]
    require(MERGE in lines, job['name'] + ' actual execution merge')
    if job['name'] == 'native complete coverage':
        require(any('ValueError: 分片身分／規劃／真實退出不符' in line and 'shard-2.json' in line for line in lines)
                and any('##[error]Process completed with exit code 1.' in line for line in lines),
                'official original aggregate failed at shard 2 actual exit')
    else:
        number = int(re.search(r'\((\d)/3\)', job['name'])[1])
        part = next(part for part in native if part['shard'] == number)
        counts = [tuple(int(n) for n in match) for line in lines
                  for match in re.findall(r'合計\(已執行、有計數者\)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+', line)]
        require(counts == [(part['total'],part['passed'],part['failed'],part['skipped'])], job['name']+' actual log total')
        require(any('##[error]' in line for line in lines) == expected_failure, job['name']+' raw error matches conclusion')
    native_job_logs.append(dict(name=job['name'], id=job['id'], conclusion=job['conclusion']))

git = lambda *args: subprocess.check_output(['git',*args],cwd=SOURCE,text=True).strip()
require(git('rev-parse','HEAD') == HEAD and git('status','--porcelain') == '', 'current source stays fixed and clean')
tree = git('rev-parse',HEAD+'^{tree}')
parents = git('show','-s','--format=%P',MERGE).split()
require(git('rev-parse',MERGE+'^{tree}') == tree and parents == [pr['base']['sha'],HEAD], 'true merge objects same tree and parent links')
commit = load(ROOT / 'api/execution-commit.json')
require(commit['sha'] == MERGE and commit['tree']['sha'] == tree and [row['sha'] for row in commit['parents']] == parents,
        'official GitHub commit source metadata')
receipt = load(ROOT / 'native-rejection-receipt.json')
require(receipt['sourceHead'] == HEAD and receipt['executionHead'] == MERGE and receipt['tree'] == tree
        and receipt['merge_parents'] == parents and receipt['exit_code'] == 1 and receipt['expected_native_rejection'] is True,
        'parent original verifier actual exit 1 and source binding')
require(receipt['cwd'] == str(SOURCE) and receipt['env']['GIT_WORK_TREE'] == str(SOURCE), 'original verifier cwd and worktree')
metadata = Path(receipt['env']['GIT_DIR'])
metadata_head = subprocess.check_output(['git','--git-dir',str(metadata),'rev-parse','HEAD'],text=True).strip()
require(metadata_head == MERGE, 'original verifier metadata is true execution merge')
require(receipt['command'][1:3] == ['-B','tests/native_shard_receipts.py'], 'original unpatched verifier command')
for stream in ['stdout','stderr']:
    require(receipt[stream+'_sha256'] == hashlib.sha256((ROOT / ('native-reverify.'+stream)).read_bytes()).hexdigest(),
            'original verifier '+stream+' hash')
stderr = raw(ROOT / 'native-reverify.stderr')
require(receipt['failure'] in stderr and 'ValueError: 分片身分／規劃／真實退出不符' in stderr and 'shard-2.json' in stderr,
        'original verifier rejects genuine failing shard-2')
require(receipt['native_complete_summary_present'] is False and not (ROOT / 'native-reverified.json').exists()
        and not (EXTRACTED / 'native-complete-coverage/native-complete.json').exists(), 'no accepted local or official native-complete')
require(receipt['official_negative_control'] == proof, 'parent official coverage negative proof matches raw originals')

provenance = load(ROOT / 'provenance.json')
require(provenance['source'] == str(SOURCE) and provenance['source_head'] == HEAD
        and provenance['execution_head'] == MERGE and provenance['integration_run_id'] == 41382891799
        and provenance['mutation_run_id'] == 41382891805, 'parent provenance source/run binding')
for row in provenance['original_tools_and_workflow_bytes']:
    content = (SOURCE / row['path']).read_bytes()
    require(hashlib.sha256(content).hexdigest() == row['sha256'] and hashlib.sha256(content.replace(b'\r\n',b'\n')).hexdigest() == row['lf_sha256'],
            'parent original tool hash '+row['path'])
    require(subprocess.check_output(['git','show',HEAD+':'+row['path']],cwd=SOURCE) == content,
            'source original Git bytes '+row['path'])
require((SOURCE / '.github/scripts/mutation_evidence.py').resolve().parents[2] == SOURCE
        and 'ROOT = Path(__file__).resolve().parents[2]' in (SOURCE / '.github/scripts/mutation_evidence.py').read_text(),
        'original supervisor ROOT uses own source')

zip_rows = []
for kind, run_id in [('integration',41382891799),('mutation',41382891805)]:
    artifact_api = load(ROOT / ('api/20261102T034113Z/'+kind+'-artifacts.json'))
    for artifact in artifact_api['artifacts']:
        archive_path = ROOT / 'official-zips' / f"{artifact['id']}-{artifact['name']}.zip"
        require(artifact['workflow_run']['id'] == run_id and artifact['workflow_run']['head_sha'] == HEAD,
                artifact['name']+' artifact API source/run')
        require(artifact['digest'] == 'sha256:'+hashlib.sha256(archive_path.read_bytes()).hexdigest(),artifact['name']+' API ZIP digest')
        with zipfile.ZipFile(archive_path) as archive:
            require(len(archive.namelist()) == len(set(archive.namelist())),artifact['name']+' unique ZIP names')
            for info in archive.infolist():
                rel = Path(info.filename)
                require(not rel.is_absolute() and '..' not in rel.parts and (info.external_attr >> 16) & 0o170000 != 0o120000,
                        artifact['name']+' safe ZIP member')
                if not info.is_dir():
                    require(archive.read(info.filename) == (EXTRACTED / artifact['name'] / info.filename).read_bytes(),
                            artifact['name']+'/'+info.filename+' original ZIP/extracted bytes')
            if artifact['name'] == 'native-complete-coverage':
                require('native-complete.json' not in archive.namelist()
                        and set(archive.namelist()) == {'native-sharding-proof/'+name for name in ['baseline.json','baseline.log','removed.json','removed.log','restored.json','restored.log','receipt.json']},
                        'official native-complete-coverage ZIP is proof-only, no complete summary')
        zip_rows.append(dict(id=artifact['id'], name=artifact['name'], digest=artifact['digest'], run_id=run_id))

classification = load(ROOT / 'integration-failure-classification.json')
require(classification['bad_rows'] == bad_rows and classification['stale_count'] == 53
        and classification['classification'] == 'committed-mutation-ledger-stale', 'parent saved red classification matches all-native audit')
report = dict(audit_passed=True, native_accepted=False, native_registry_complete=True,
              check_count=checks, execution_commit=MERGE, pr_head=HEAD, execution_tree=tree,
              browser=browser, pending_browser=pending_browser, all_browser_complete=not pending_browser,
              native=native, native_bad_rows=bad_rows, native_job_logs=native_job_logs,
              python_receipts_checked=python_count,node_logs_checked=node_count,
              counted_tests=sum(row['total'] for row in native),counted_passed=sum(row['passed'] for row in native),
              original_verifier_actual_exit=receipt['exit_code'], original_verifier_failure=receipt['failure'],
              official_native_complete_summary_present=False, coverage_mutation_proof=proof,
              official_zips=zip_rows, input_sha256=inputs,
              scope='Read existing downloaded files and source/Git metadata only. No product suite, network or binary execution. Failing freshness row remains failed.')
(OUT / 'pr345-independent-native-browser-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({key:report[key] for key in ['audit_passed','native_accepted','check_count','python_receipts_checked','node_logs_checked','counted_tests','counted_passed','native_bad_rows','pending_browser']},ensure_ascii=False))
'''
(OUT / 'pr345-check-native-browser.py').write_text(prefix+suffix)
