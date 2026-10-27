from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json

OUT=Path('/tmp/geo337-recovery-native-focused-actual-peer-20261026')
OWN=Path('/dev/shm/geometry-axiom-geo337-20261025')
ROOT=OWN/'geo337-native-final-focused-20261026'
OUTER=OWN/'native-focused-root-original-20261026'
TOOL='6248a86b6ac174a6c624f64c14186862c841aea5efdd387c8d81b80766b80893'
HARNESS='1aca97bbcdc0823b3ea13930b7e802f2aa02784e5fadcab5ca97c01f0ef0747d'
RUNNER='78c6a4c203402450c63d86f890a7fbc909afe230f7c5976da54e45b5a84c5f0b'
errors=[];checks=0
def check(v,label):
    global checks
    checks+=1
    if not v:errors.append(label)
def H(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
def within(p):return Path(p).is_relative_to(ROOT)

summary=read(ROOT/'RESULT.json');outer=read(OUTER/'RESULT.json')
check(summary['exit_code']==0 and summary['failed']==[],'focused actual terminal')
check(outer['exit_code']==0 and not outer['source_transition_executed'] and not outer['native_executed'],'outer true0 and no production transition')
for n,pin in [('original-module.py',TOOL),('original-harness.py',HARNESS),('runner.py',RUNNER)]:
    check(H((ROOT/n).read_bytes())==pin,'original frozen '+n)
check(summary['original_module_sha256']==TOOL and summary['original_harness_sha256']==HARNESS and summary['runner_sha256']==RUNNER,'result exact pins')
source=(ROOT/'original-module.py').read_bytes()
runner_ast=ast.parse((ROOT/'runner.py').read_bytes())
mutations=next(ast.literal_eval(n.value) for n in ast.walk(runner_ast) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='mutations' for t in n.targets))
check(set(mutations)=={'unknown','hook','ignored','observation'},'exact original mutation set')
for case,(old,new) in mutations.items():
    check(source.count(old.encode())==1,'unique original anchor '+case)
    check((ROOT/('guard-withdrawn-'+case+'.py')).read_bytes()==source.replace(old.encode(),new.encode(),1),'exact single guard withdrawal '+case)
expected=[('new-focused-baseline','focused',0)]
for case in ['unknown','hook','ignored','observation']:
    expected.extend([(case+'-before',case,0),(case+'-withdrawn',case,1),(case+'-restored',case,0)])
check(len(summary['phases'])==len(expected)==13,'exact13 phases')
expected_errors={'unknown':'actual non-evidence difference not exact allowlist','hook':'executable Git hook refused: post-merge',
                 'filter':'executable or redirected Git configuration refused: filter.synthetic.smudge','worktree':'executable or redirected Git configuration refused: core.worktree',
                 'sparse':'effective original non-cone sparse configuration: core.sparseCheckoutCone','promisor':'configuration refused: remote.origin.promisor',
                 'ignored':'ignored path set changed','observation':'explicit approved remote observation argv'}
phase_report=[];baseline=[];requests=0;fixture_snapshots=0
for row,(phase,case,expected_exit) in zip(summary['phases'],expected):
    check((row['phase'],row['case'],row['expected_exit'],row['actual_exit'],row['timeout'])==(phase,case,expected_exit,expected_exit,False),'exact phase '+phase)
    p=ROOT/phase;d=read(p/'RESULT.json');cmd=read(Path(row['command_directory'])/'result.json')
    check(row['accepted_expected_outcome'] is True and cmd['actual_process_returncode']==expected_exit and cmd['timeout_expired'] is False,'phase raw terminal '+phase)
    check(d['exit_code']==expected_exit and d['harness_sha256']==HARNESS,'harness actual terminal '+phase)
    check(not d['production_roots_accessed'] and not d['product_tests_executed'] and d['all_fixture_capture_and_tmp_root']==str(p),'synthetic-only scope '+phase)
    check(d['subject_sha256']==row['module_sha256']==H(Path(d['subject_path']).read_bytes()),'phase subject exact '+phase)
    if case=='focused':
        check([x['case'] for x in d['cases']]==['positive','hook','filter','worktree','sparse','promisor','ignored','observation'],'original eight baseline cases')
    else:check([x['case'] for x in d['cases']]==[case],'exact single selected case '+phase)
    if expected_exit==1:
        expected_assertion='AssertionError: new ignored leaf must be detected after actual ff merge' if case=='ignored' else 'AssertionError: '+case+' must refuse (real guard did not stop transition)'
        check(d['failed']==[case] and d['cases'][0]['harness_exit']==1,'withdrawn actual red '+phase)
        check(d['cases'][0]['error'].strip().endswith(expected_assertion),'precise assertion '+phase)
        check(expected_assertion in (Path(row['command_directory'])/'stderr.bin').read_text(),'assertion in original stderr '+phase)
    else:check(d['failed']==[] and all(x['harness_exit']==0 for x in d['cases']),'baseline/restored harness passes '+phase)
    for c in d['cases']:
        name=c['case'];case_root=p/name;tr=case_root/('geo337-native-final-transition-'+name)
        t=read(tr/'RESULT.json');q=read(case_root/'SYNTHETIC_REQUEST.json');requests+=1
        for key in ['root','provider_repo','provider_objects','out']:
            check(within(q[key]),'synthetic path '+phase+' '+key)
        check(q['minimum_free_tmp_bytes']==q['minimum_free_output_bytes']==0,'tiny-only capacity '+phase)
        check(not t['product_gate_executed'] and not t['provider_written'] and not t['old_objects_deleted'],'transition scope '+phase+' '+name)
        check(t['tool_sha256']==d['subject_sha256'] and t['old_sha']==q['old_sha'] and t['final_sha']==q['final_sha'],'transition identities '+phase+' '+name)
        if expected_exit==1 or name=='positive':
            check(t['exit_code']==0 and t['merge_exit']==0,'actual synthetic successful merge '+phase+' '+name)
            check(t['provider_metadata_unchanged'] and t['old_refs_and_objects_preserved'] and t['all_five_fixtures_preserved'],'successful synthetic preservation '+phase+' '+name)
            before=read(tr/'MATERIALIZED_BEFORE.json');after=read(tr/'MATERIALIZED_AFTER.json')
            for path in set(before)&set(after)-{'tests/test_geo314_commit_paths.py'}:
                check(before[path]==after[path],'unchanged synthetic source leaf '+phase+' '+path)
        else:
            check(t['exit_code']==1 and expected_errors[name] in t.get('error',''),'precise actual refusal '+phase+' '+name)
            check(t['merge_exit']==(0 if name=='ignored' else None),'pre/postmerge rejection stage '+phase+' '+name)
        if (tr/'FIXTURES_BEFORE.json').exists():
            fixtures=read(tr/'FIXTURES_BEFORE.json');check(len(fixtures)==5,'five synthetic fixtures '+phase+' '+name)
            archived=sorted(tr.glob('fixture-*.bin'));check(len(archived)==5,'five fixture snapshots '+phase+' '+name)
            check(sorted(H(x.read_bytes()) for x in archived)==sorted(v['sha256'] for v in fixtures.values()),'exact fixture snapshot hashes '+phase+' '+name)
            for path,v in fixtures.items():
                b=(Path(q['root'])/path).read_bytes();check(len(b)==v['bytes'] and H(b)==v['sha256'],'current synthetic fixture '+phase+' '+path)
            fixture_snapshots+=5
        if name=='hook':
            check((case_root/'UNAUTHORIZED_HOOK_OR_FILTER_MARKER').exists()==(expected_exit==1),'hook only executes when guard removed '+phase)
        if name=='filter':check(not (case_root/'UNAUTHORIZED_HOOK_OR_FILTER_MARKER').exists(),'filter did not execute before refusal')
        if case=='focused':baseline.append({'case':name,'harness_exit':c['harness_exit'],'transition_exit':t['exit_code'],'merge_exit':t['merge_exit'],'reason':t.get('error','').strip().splitlines()[-1] if t.get('error') else 'positive accepted'})
    phase_report.append({'phase':phase,'exit':expected_exit,'command_directory':row['command_directory'],'module_sha256':row['module_sha256']})

catalog=[];all_commands=[];directories=set();streams=0;stream_bytes=0;command_return_codes={}
for base in [ROOT,OUTER]:
    for aggregate in sorted(base.rglob('subcommands.json')):
        rows=read(aggregate)
        for r in rows:
            directory=Path(r['directory']);check(directory not in directories,'unique original command '+str(directory));directories.add(directory)
            check(directory.is_relative_to(base),'command location inside captured scope '+str(directory))
            check(read(directory/'result.json')==r,'command aggregate equality '+str(directory))
            q=read(directory/'request.json')
            for key in ['command','cwd','acceptance_sha','source_sha','source_variant','environment','stdin_provided','stdin_sha256','started_epoch']:
                check(q.get(key)==r.get(key),'stable original request/result '+key+' '+str(directory))
            for name in ['stdin','stdout','stderr']:
                b=(directory/(name+'.bin')).read_bytes();streams+=1;stream_bytes+=len(b)
                check(H(b)==r[name+'_sha256'],'original stream hash '+name+' '+str(directory))
                if name!='stdin':check(len(b)==r[name+'_bytes'],'original stream bytes '+name+' '+str(directory))
                catalog.append((str(directory/(name+'.bin')),len(b),H(b)))
            check(r['timeout_expired'] is False and type(r['actual_process_returncode']) is int,'real non-timeout terminal '+str(directory))
            cmd=r['command'];executable=Path(cmd[0]).name
            check(executable in {'git','python3','python','python3.12','python3.11'},'only synthetic Git/Python commands '+str(directory))
            if base==ROOT:check(within(r['cwd']),'inner original cwd stays synthetic '+str(directory))
            if executable=='git' and 'ls-remote' in cmd:check(not any('://' in arg for arg in cmd),'local synthetic observation only')
            check(not any(x in cmd for x in ['tests/run_all.py','tests/mutate.py','cc','gcc','clang']),'no product/compiler command '+str(directory))
            code=str(r['actual_process_returncode']);command_return_codes[code]=command_return_codes.get(code,0)+1
            all_commands.append(r)
check(len(directories)==1129,'complete1129 original commands')
check(streams==3387,'complete3387 original raw streams')
check(len(read(OUTER/'subcommands.json'))==1,'one outer recorded execution')
resource=read(OUTER/'RESOURCE_PLAN.json')
check(resource['focused_increment']==64*1024*1024 and resource['shared_ceiling']==2*1024**3,'original capacity limits retained')
check(resource['current_used']+resource['focused_increment']+resource['architecture_pending_reserved']<resource['shared_ceiling'],'actual root shared capacity admitted')
check(not summary['production_source_accessed'] and not summary['product_tests_executed'] and not summary['native128MiB_gate_modified'],'formal native untouched')
report={'schema':'native-recovery-focused-independent-actual-peer/1','reviewed_utc':datetime.now(timezone.utc).isoformat(),
        'exit_code':1 if errors else 0,'blocking_findings':errors,'checks':checks,'tool_sha256':TOOL,
        'original_focused_result_sha256':H((ROOT/'RESULT.json').read_bytes()),'original_outer_result_sha256':H((OUTER/'RESULT.json').read_bytes()),
        'baseline':baseline,'phases':phase_report,'withdraw_restore_exits':{x:[0,1,0] for x in mutations},
        'original_commands_verified':len(directories),'original_return_code_counts':command_return_codes,
        'original_raw_streams_verified':streams,'raw_stream_bytes_verified':stream_bytes,
        'raw_catalog_sha256':H(json.dumps(catalog,separators=(',',':')).encode()),
        'synthetic_requests_verified':requests,'synthetic_fixture_snapshots_verified':fixture_snapshots,
        'formal_source_transition_executed':False,'native_gate_executed':False,'product_test_executed':False,
        'formal_tool_runtime_proof_accepted':not errors,
        'limits':['This accepts the exact tool synthetic runtime proof, not the native product gate or real source transition.',
                  'Root must still bind actual final SHA, exact current native index/source delta, original five fixture identities, published remote observation, writer leases and actual capacity before production transition.',
                  'Tiny policy zero capacity is restricted to synthetic paths; original production64MiB and native128MiB limits remain unchanged.',
                  'This peer reads completed originals and captured commands only; it does not independently inspect production source/current index or infer absence of foreign writers.',
                  'All four expected red streams remain original red. No raw stream, fixture, index, source, lease or result was edited.']}
OUT.mkdir(exist_ok=True)
target=OUT/'REVIEW.json'
if target.exists():raise RuntimeError('refuse overwrite existing peer result')
target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['phases','baseline']},ensure_ascii=False,indent=2))
raise SystemExit(report['exit_code'])
