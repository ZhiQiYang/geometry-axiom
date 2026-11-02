from pathlib import Path

OUT=Path(__file__).resolve().parent
prior=Path('/tmp/geometry-resume-20261102/ci-followup/pr340/independent-review/pr345-check-native-browser.py').read_text()
source=prior[:prior.index('import subprocess\nimport zipfile')]
source=source.replace("ROOT = OUT.parent.parent / 'pr345'",'ROOT = OUT.parents[1]')
source=source.replace('/tmp/geometry-pr345-20261102','/tmp/geometry-pr344-20261102')
source=source.replace('577b2e81967b3019352f65df5ffe6dc48eb6202f','503cfc59354893859ae9e6e4a6ab7c11d7972517')
source=source.replace('f75739691f4e0d8fb73e82c22074922d8766e601','56250470746f8a7bf6b4a235a586f2744ae3cddf')
source=source.replace('20261102T034113Z','20261102T050911Z').replace('pr345.json','pr344.json')
strict='''def strict_json(value):
    def unique(pairs):
        out = {}
        for key,item in pairs:
            if key in out:
                raise ValueError('duplicate raw marker JSON key: '+key)
            out[key]=item
        return out
    return json.loads(value,object_pairs_hook=unique)


'''
source=source.replace('def load(path):',strict+'def load(path):')
source=source.replace('json.loads(line)','strict_json(line)').replace('json.loads(line.split(" ", 1)[1])','strict_json(line.split(" ", 1)[1])')
mutants='''current_mutants=[]
for node in ast.parse(raw(SOURCE / 'tests/mutate.py')).body:
    value=None
    if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='MUTANTS' for target in node.targets):
        value=node.value
    elif isinstance(node,ast.AugAssign) and isinstance(node.target,ast.Name) and node.target.id=='MUTANTS':
        value=node.value
    if value is not None:
        require(isinstance(value,ast.List),'current mutation table literal list')
        for call in value.elts:
            fields={kw.arg:kw.value for kw in call.keywords}
            current_mutants.append(dict(id=ast.literal_eval(fields['id']),binary=ast.literal_eval(fields['binary'])if 'binary'in fields else 'core'))
require(len(current_mutants)==len({row['id']for row in current_mutants}),'current mutation ID uniqueness')
bridge_ids={row['id']for row in current_mutants if row['binary']=='bridge'}

'''
source=source.replace("expected = load(SOURCE / 'tests/run_all.expected.json')['suites']",mutants+"expected = load(SOURCE / 'tests/run_all.expected.json')['suites']")
source=source.replace('"變異表 123 筆,紀錄 123 筆" in output','f"變異表 {len(current_mutants)} 筆,紀錄 {len(current_mutants)} 筆" in output')
source=source.replace('"過期 stale 53 / 受阻 blocked 0" in output','f"過期 stale {len(bridge_ids)} / 受阻 blocked 0" in output')
source=source.replace('"掃描 8137 次建構(CI 抽樣)" in output',"re.search(r'掃描 ([1-9][0-9]*) 次建構\\(CI 抽樣\\)',output)")
suffix=r'''
import subprocess
import zipfile

require(len(browser)==6 and pending_browser==[],'six completed browser groups, no pending')
require({row['name']for row in browser}=={'browser ('+name+')'for name in ['assembly','documents','grid','space','timber','canvas']},
        'exact six current workflow browser groups')
bad_rows=[row for row in all_rows if row['failed'] or row['process_exit_code'] or row['crashed'] or row['env_problem'] or row['expected_problem']]
require(len(bad_rows)==1 and bad_rows[0]['name']=='mutation:check' and bad_rows[0]['process_exit_code']==1,
        'only one native freshness failure, no other assertion/error/exit failures')
raw_freshness_path=EXTRACTED/'native-logs-2/mutation_check.log'
freshness_raw=raw(raw_freshness_path)
stale_lines=[line for line in freshness_raw.splitlines()if line.startswith('  STALE ')]
stale_ids={re.search(r'STALE (M\d+)',line)[1]for line in stale_lines}
require(len(stale_lines)==len(stale_ids)==len(bridge_ids) and stale_ids==bridge_ids,
        'full original stale inventory exactly covers current bridge table')
require(all('bridge source/oracle restoration'in line for line in stale_lines),'stale restoration guard explicit for every bridge entry')
require(all('裁判已變('in line or 'equivalence audit oracle changed'in line for line in stale_lines),'stale oracle-change classification')
native_jobs=[]
for job in jobs:
    if not job['name'].startswith('native'):
        continue
    expected_fail=job['name']in ['native (2/3)','native complete coverage']
    require(job['status']=='completed' and job['conclusion']==('failure'if expected_fail else 'success'),job['name']+' official conclusion')
    path=ROOT/'job-logs'/(str(job['id'])+'.txt')
    lines=[line.partition('Z ')[2]for line in raw(path).splitlines()]
    require(MERGE in lines,job['name']+' execution merge')
    if job['name']=='native complete coverage':
        failure_lines=[line for line in lines if 'ValueError: 分片身分／規劃／真實退出不符'in line or '##[error]'in line]
        require(any('shard-2.json'in line for line in failure_lines)
                and any('##[error]Process completed with exit code 1.'in line for line in failure_lines),
                'official original aggregate rejects shard2 actual exit1')
    else:
        number=int(re.search(r'\((\d)/3\)',job['name'])[1])
        part=next(row for row in native if row['shard']==number)
        counts=[tuple(int(n)for n in match)for line in lines
                for match in re.findall(r'合計\(已執行、有計數者\)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+',line)]
        require(counts==[(part['total'],part['passed'],part['failed'],part['skipped'])],job['name']+' raw counted sum')
        require(any('##[error]'in line for line in lines)==expected_fail,job['name']+' error exactly matches actual conclusion')
    native_jobs.append(dict(id=job['id'],name=job['name'],conclusion=job['conclusion']))

integration=load(ROOT/'api/20261102T050911Z/integration-run.json')
mutation=load(ROOT/'api/20261102T050911Z/mutation-run.json')
require(integration['id']==41388718270 and integration['head_sha']==HEAD and integration['run_attempt']==1
        and integration['status']=='completed' and integration['conclusion']=='failure','integration terminal failure remains failure')
require(mutation['id']==41388718083 and mutation['head_sha']==HEAD and mutation['run_attempt']==1
        and mutation['status']=='completed' and mutation['conclusion']=='success','mutation terminal API success')
require({row['name']for row in jobs if row['conclusion']=='failure'}=={'native (2/3)','native complete coverage'},'only two failed integration jobs')
git=lambda *args:subprocess.check_output(['git',*args],cwd=SOURCE,text=True).strip()
require(git('rev-parse','HEAD')==HEAD and git('status','--porcelain')=='','current source fixed and clean')
tree=git('rev-parse',HEAD+'^{tree}')
parents=git('show','-s','--format=%P',MERGE).split()
require(git('rev-parse',MERGE+'^{tree}')==tree and parents==[pr['base']['sha'],HEAD],'true merge same tree and parent linkage')
require(tree=='ff068df7b220d63e64832d3648a0b81ff8cbca57','execution source tree confirmed')
require(not(EXTRACTED/'native-complete-coverage/native-complete.json').exists(),'no accepted official native aggregate')

zip_rows=[]
for artifact in load(ROOT/'api/20261102T050911Z/integration-artifacts.json')['artifacts']:
    path=ROOT/'official-zips'/f"{artifact['id']}-{artifact['name']}.zip"
    require(artifact['workflow_run']['id']==41388718270 and artifact['workflow_run']['head_sha']==HEAD,artifact['name']+' API source/run')
    require(artifact['digest']=='sha256:'+hashlib.sha256(path.read_bytes()).hexdigest(),artifact['name']+' official ZIP digest')
    with zipfile.ZipFile(path)as archive:
        require(len(archive.namelist())==len(set(archive.namelist())),artifact['name']+' unique ZIP members')
        for info in archive.infolist():
            rel=Path(info.filename)
            require(not rel.is_absolute() and '..'not in rel.parts and (info.external_attr >> 16)&0o170000!=0o120000,
                    artifact['name']+' safe original ZIP member')
            if not info.is_dir():
                require(archive.read(info.filename)==(EXTRACTED/artifact['name']/info.filename).read_bytes(),
                        artifact['name']+'/'+info.filename+' ZIP/extracted exact bytes')
        if artifact['name']=='native-complete-coverage':
            require('native-complete.json'not in archive.namelist(),'official aggregate ZIP contains no accepted native summary')
    zip_rows.append(dict(id=artifact['id'],name=artifact['name'],digest=artifact['digest']))
require(len(zip_rows)==12,'all current integration original artifacts accounted')
log_archive_path=ROOT/'official-run-logs'/f'integration-{integration["id"]}.zip'
log_receipts=[]
with zipfile.ZipFile(log_archive_path)as archive:
    for job in jobs:
        members=[name for name in archive.namelist()if re.fullmatch(r'\d+_'+re.escape(job['name'].replace('/','_'))+r'\.txt',name)]
        require(len(members)==1,job['name']+' unique original whole-job member')
        direct=ROOT/'job-logs'/(str(job['id'])+'.txt')
        require(archive.read(members[0])==direct.read_bytes(),job['name']+' original run ZIP and endpoint log equality')
        log_receipts.append(dict(id=job['id'],name=job['name'],sha256=hashlib.sha256(direct.read_bytes()).hexdigest()))

canvas=next(row for row in browser if row['name']=='browser (canvas)')
canvas_path=ROOT/'job-logs'/(str(canvas['id'])+'.txt')
canvas_lines=canvas_path.read_text().splitlines()
result_at=next(index for index,line in enumerate(canvas_lines)if 'Z CDP_RESULT {'in line)
diagnostics=[dict(line=index+1,text=line)for index,line in enumerate(canvas_lines)
             if 'Exception occurred during processing of request'in line or 'BrokenPipeError:'in line]
require(all(row['line']>result_at+1 for row in diagnostics),'server request diagnostics follow browser result in appended server log')
canvas['server_log_diagnostics']=dict(lines=diagnostics,classification='Appended server request diagnostics are retained separately from uncaught browser exceptions and controlled assertions; exact socket-closure cause is not inferred.')
report=dict(review_passed=True,overall_ci_accepted=False,native_accepted=False,browser_accepted=True,
            mutation_official_api_conclusion='success',mutation_artifact_acceptance_outside_this_review=True,
            check_count=checks,pr_head=HEAD,execution_commit=MERGE,execution_tree=tree,merge_parents=parents,
            integration_run_id=41388718270,integration_conclusion='failure',mutation_run_id=41388718083,
            current_registry_suite_count=len(registry),native_partitions=[len(plan)for plan in planned],native=native,
            counted_tests=sum(row['total']for row in native),counted_passed=sum(row['passed']for row in native),
            allowed_skips=sum(row['allowed_skips']for row in native),native_bad_rows=bad_rows,native_job_logs=native_jobs,
            python_receipts_checked=python_count,node_logs_checked=node_count,browser=browser,
            full_stale_bridge_ids=sorted(stale_ids,key=lambda rid:int(rid[1:])),stale_bridge_count=len(stale_ids),
            freshness_raw_log_sha256=hashlib.sha256(raw_freshness_path.read_bytes()).hexdigest(),
            official_negative_control=proof,official_native_complete_summary_present=False,
            integration_official_zip_count=len(zip_rows),integration_official_zips=zip_rows,
            integration_whole_job_logs_byte_equal=log_receipts,current_expected_sha256=expected_digest,current_timings_sha256=timings_digest,
            audit_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),input_sha256=inputs,
            scope='Only saved API/artifact/raw log/source and Git metadata read. Current registry/expected/timing derived at this HEAD. No network, product, Chrome, build, source/PR writes, or local negative control/test executions.')
(OUT/'native-browser-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({key:report[key]for key in ['review_passed','overall_ci_accepted','native_accepted','browser_accepted','check_count','current_registry_suite_count','native_partitions','counted_tests','counted_passed','allowed_skips','python_receipts_checked','node_logs_checked','stale_bridge_count']},ensure_ascii=False))
'''
(OUT/'check_current.py').write_text(source+suffix)
