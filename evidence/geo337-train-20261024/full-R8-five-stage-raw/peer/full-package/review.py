from pathlib import Path
import collections, datetime, fcntl, hashlib, json, stat, tarfile

P=Path('/tmp/geo323-r8-full-package-actual-peer-20261025')
O=Path('/tmp/geo323-r8-full-package-20261025')
D=Path('/tmp/geo323-r8-collection-preparation-20261025')
S='75a1e93811a52b69385cbdaf6a09d773ed9052ad'
def J(p):return json.loads(Path(p).read_bytes())
def H(b):return hashlib.sha256(b).hexdigest()
def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

lock=Path('/tmp/g261r3/secondary.lock').open('a+b')
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:
    print('NOT EXECUTED: secondary slot busy; no retry or sleep.');raise SystemExit(75)
try:
    assert not (P/'REVIEW.json').exists()
    package=J(O/'PACKAGE.json');inventory=J(O/'RAW_INVENTORY.json');plan=J(D/'PLAN.json');pins=J(D/'COLLECTOR_PINS.json')
    assert package['source_sha']==inventory['source_sha']==plan['source_sha']==pins['source_sha']==S
    assert package['exit']==0 and package['subject_executions']==0 and package['published'] is False
    assert package['elf_payloads_included'] is False and package['original_ELF_retained'] is True
    assert package['archive']['bytes']==31362296 and package['archive']['members']==9057
    assert package['archive']['sha256']=='4503955cefc6fb1a6491ad2a146c259e59a2185401d0fbebc09908a47e3bf9d0'
    archive=Path(package['archive']['path']);assert archive.stat().st_size==31362296 and digest(archive)==package['archive']['sha256']
    assert package['inventory']['sha256']==digest(O/'RAW_INVENTORY.json')=='1136cfce6ec822b18bec2e782ca67eb24b5d02c25e4620a9f833453efe8e2c57'
    for name,pin in pins['files'].items():assert (D/name).stat().st_size==pin['bytes'] and digest(D/name)==pin['sha256']
    assert '__FROZEN_' not in (D/'collect.py').read_text() and '__FROZEN_' not in (D/'launch.py').read_text()
    assert digest(D/'PLAN.json') in (D/'collect.py').read_text() and digest(D/'collect.py') in (D/'launch.py').read_text()
    members=inventory['members'];assert len(members)==inventory['regular_file_count']==9056
    assert sum(x['bytes'] for x in members)==inventory['logical_original_bytes']==111407792
    expected={x['name']:x for x in members};assert len(expected)==len(members)
    selected={x['name']:x for x in plan['original_files']};assert len(selected)==9050
    omitted=[x for x in plan['original_files'] if x['kind']=='ELF-hash-only'];assert len(omitted)==7
    assert len([x for x in plan['original_files'] if x['kind']=='original-payload'])==9043
    for name,item in selected.items():
        if item['kind']=='ELF-hash-only':assert name not in expected
        else:assert expected[name]['source_path']==item['path'] and expected[name]['bytes']==item['bytes']
    allowed_extras={'collection-tools/'+n for n in ['collect.py','PLAN.json','launch.py','README.md','freeze_terminal_plan.py','prepare_plan.py','R7_TO_R8_COLLECTOR.diff','PROVENANCE.json','TOOL_RESPONSE_SCOPE.json','adapt_r7.py','COLLECTOR_PINS.json']}
    allowed_extras|={'collection/SUMMARY.json','collection/EXCLUDED_ELF_PAYLOADS.json'}
    assert set(expected)-set(selected)==allowed_extras
    seen=set()
    with tarfile.open(archive,'r:gz') as tar:
        for member in tar:
            assert member.isfile() and member.name not in seen;seen.add(member.name)
            assert not member.name.startswith('/') and '..' not in Path(member.name).parts
            stream=tar.extractfile(member);h=hashlib.sha256();size=0
            with stream:
                for block in iter(lambda:stream.read(1024*1024),b''):h.update(block);size+=len(block)
            if member.name=='RAW_INVENTORY.json':assert size==(O/'RAW_INVENTORY.json').stat().st_size and h.hexdigest()==package['inventory']['sha256']
            else:
                item=expected[member.name];source=Path(item['source_path'])
                assert stat.S_ISREG(source.lstat().st_mode)
                assert member.size==size==item['bytes']==source.stat().st_size
                assert h.hexdigest()==item['sha256']==digest(source)
    assert seen==set(expected)|{'RAW_INVENTORY.json'} and len(seen)==9057
    elf=J(O/'EXCLUDED_ELF_PAYLOADS.json');assert len(elf)==7 and {x['name'] for x in elf}=={x['name'] for x in omitted}
    assert {Path(x['source_path']).parent.name for x in elf}=={'base','base-pg','base-trace','fix','fix-pg','fix-trace','main'}
    for x in elf:
        p=Path(x['source_path']);assert stat.S_ISREG(p.lstat().st_mode) and p.stat().st_size==x['bytes'] and digest(p)==x['sha256']
        with p.open('rb') as f:assert f.read(4)==b'\x7fELF'
    for pin in plan['terminal_bindings'].values():assert Path(pin['path']).stat().st_size==pin['bytes'] and digest(pin['path'])==pin['sha256']
    r=J(plan['terminal_bindings']['receipt']['path']);summary=J(O/'SUMMARY.json')
    for key in ['source_sha','base','main','stages','errors','quantitative_targets','wrapper_exit','all_executed_stage_commands_passed','all_measured_original_targets_met','all_required_stages_completed','full_acceptance_passed']:assert summary[key]==r[key]
    assert summary['outer_exit']==1 and summary['original_cli_exits']==[0,0,1,1,1]
    assert [r['stages'][x]['execution_exit'] for x in ['prepare','build','compare','perf','profile']]==[0,0,1,0,0]
    assert 'ABC_result' not in r and r['all_required_stages_completed'] is False and r['full_acceptance_passed'] is None
    target=r['quantitative_targets'];assert target['N64_fix_main']['target_met'] and target['geo_eval_source_64_32']['target_met'] and all(x['target_met'] for x in target['small_N_no_regression']['points'].values())
    assert summary['published'] is False and summary['no_subject_executed'] is True
    assert summary['source_preparation_entries']==447 and summary['excluded_elf_count']==7
    perf=J(plan['terminal_bindings']['performance']['path']);assert len(perf['samples'])==36
    scope=plan['tool_response_scope'];assert scope==J(D/'TOOL_RESPONSE_SCOPE.json') and scope['tool_session_id']==62076 and not scope['stdout_stderr_reconstructed']
    responses=[]
    for x in scope['supplied_api_files']:
        p=Path(x['path']);assert p.stat().st_size==x['bytes'] and digest(p)==x['sha256'];responses.append(J(p))
    assert len(responses)==4 and len([x for x in responses if x.get('exit_code')==1])==1
    assert all(x.get('session_id')==62076 for x in responses if 'exit_code' not in x)
    outer=J(D/'collection-outer/RESULT.json');rows=J(D/'collection-outer/subcommands.json')
    assert outer['source_sha']==S and outer['exit']==0 and not outer['source_subject_executed']
    assert [x['phase'] for x in outer['steps']]==['freeze','collect'] and [x['exit'] for x in outer['steps']]==[0,0]
    assert len(rows)==2
    for row in rows:
        d=Path(row['directory']);assert J(d/'result.json')==row and row['actual_process_returncode']==0 and not row['timeout_expired']
        assert row['source_sha']==row['acceptance_sha']==S
        for n in ['stdout','stderr']:assert digest(d/(n+'.bin'))==row[n+'_sha256'] and (d/(n+'.bin')).stat().st_size==row[n+'_bytes']
        assert digest(d/'stdin.bin')==row['stdin_sha256']
    execution=J(D/'execution/RESULT.json');assert execution['actual_process_exit']==0 and execution['source_sha']==S and execution['subject_executed'] is False
    for n in ['stdout','stderr']:assert digest(D/'execution'/n)==execution[n+'_sha256']
    assert J(D/'COLLECTION_TOOL_INITIAL.json')['session_id']==4837 and J(D/'COLLECTION_TOOL_FINAL.json')['exit_code']==0
    assert J(D/'COLLECTOR_RESULT.json')==package
    report={'schema':'geo323-r8-full-package-actual-peer/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':0,'findings':[],
        'source_sha':S,'archive_sha256':package['archive']['sha256'],'archive_bytes':31362296,'members':9057,'original_bytes_verified':111407792,
        'all_selected_members_and_originals_match':True,'elf_payloads_retained_and_hash_only':7,'product_execution_exit':1,'compare_execution_exit':1,'performance_targets_all_met':True,
        'original_stage_exits':[0,0,1,0,0],'original_cli_exits':[0,0,1,1,1],'ABC_result_present':False,'all_required_stages_completed':False,'full_acceptance_passed':None,
        'collection_exits':[0,0],'collection_tool_exit':0,'product_reruns':0,'published':False,
        'bindings':{str(p):digest(p) for p in [O/'PACKAGE.json',O/'RAW_INVENTORY.json',D/'PLAN.json',D/'COLLECTOR_PINS.json',D/'collection-outer/RESULT.json',D/'COLLECTION_TOOL_INITIAL.json',D/'COLLECTION_TOOL_FINAL.json',P/'review.py']},
        'limits':['Archive preservation success does not resolve exact comparison or required CI blockers.','Historical preparation README/PROVENANCE intentionally retain original unexecuted state; actual results establish completion separately.','No subject rerun, Git write, source/receipt deletion or threshold change.']}
    (P/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'exit_code':0,'review':str(P/'REVIEW.json'),'sha256':digest(P/'REVIEW.json')}))
finally:
    fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
