from pathlib import Path

OUT = Path(__file__).resolve().parent
previous = (OUT / 'pr340-terminal-audit.py').read_text()
prefix = previous[:previous.index("native = load(DATA / 'native-reverify-receipt.json')")]
prefix = prefix.replace('DATA = OUT.parent', "DATA = OUT.parent.parent / 'pr345'")
prefix = prefix.replace('/tmp/geometry-pr340-20261102','/tmp/geometry-pr345-20261102')
prefix = prefix.replace('b3a248607d7eb68d3167abbb926cf491d9b35a26','577b2e81967b3019352f65df5ffe6dc48eb6202f')
prefix = prefix.replace('fc1c9f565a2e15660e931b3884dca2220cb1b7b2','f75739691f4e0d8fb73e82c22074922d8766e601')
prefix = prefix.replace('41382015317','41382891799').replace('41382015277','41382891805')
api = r'''
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

'''
body = previous[previous.index("verify = load(DATA / 'mutation-verify-receipt.json')"):previous.index("browser_report = load(OUT / 'pr340-final-native-browser-check.json')")]
suffix = r'''
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
'''
(OUT / 'pr345-mutation-terminal-audit.py').write_text(prefix+api+body+suffix)
