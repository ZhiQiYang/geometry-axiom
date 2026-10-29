from pathlib import Path
import hashlib,json,re
HERE=Path(__file__).resolve().parent
F=Path('/workspace/issue128-p2-32403481-formal');S='324034812bb6effca68e0413bc0468595337b317'
checks=[];findings=[]
def h(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def check(v,n):
    checks.append({'check':n,'passed':bool(v)})
    if not v:findings.append(n)
r=read(F/'receipt.json');outer=read(Path(str(F)+'-launch')/'receipt.json');suite=read(F/'panel-native/receipt.json');ob=read(F/'panel-native/observed/receipt.json')
check(r['source']==S and r['actual_source_identity'][0]==S and r['source_after_identity']==r['actual_source_identity'] and r['source_after_clean'],'actual S initial/final clean')
check(r['completed_checkout_previous_identity'][0]=='6d9d46e8d16af75351924c6d47a078d3eb647cc0','prior E not execution')
check(r['accepted'] and suite['actual_exit']==0 and suite['original_expected_methods']==13 and suite['zero_skips'],'actual original13 exit0/0skip')
check(r['global_ledger_written'] is False and not r['wall_clock_performance_run'],'no ledger or timing claim')
check(outer['reaper_process_exit']==outer['primary_returncode']==outer['launcher_exit']==0 and not outer['metadata_problems'],'outer/reaper/primary all0')
events=[json.loads(x) for x in Path(outer['reaper_log']).read_text().splitlines()]
check(events[-1].get('event')=='完成' and events[-1]['primary_returncode']==0,'true terminal reaper')
for group,rows in [('formal',r['commands']),('outer',outer['commands'])]:
    for row in rows:
        p=Path(row['directory']);check(read(p/'result.json')==row and row['actual_process_returncode']==0 and not row['timeout_expired'],'original c387 result '+group+p.name)
        for stream in ['stdout','stderr']:
            b=(p/(stream+'.bin')).read_bytes();check(len(b)==row[stream+'_bytes'] and h(b)==row[stream+'_sha256'],'original c387 raw '+group+p.name+'/'+stream)
ids=[(Path(x['directory'])/'stdout.bin').read_text().splitlines() for x in r['commands'] if x['command']==['git','rev-parse','HEAD','HEAD^{tree}']]
check(ids==[r['completed_checkout_previous_identity'],r['actual_source_identity'],r['source_after_identity']],'original Git stdout identities')
commanddir=Path(suite['command']['directory']);stderr=(commanddir/'stderr.bin').read_text();stdout=(commanddir/'stdout.bin').read_text()
check(len(re.findall(r'^Ran 13 tests in ',stderr,re.M))==1 and re.search(r'\nOK\s*$',stderr) is not None and 'skipped' not in stderr,'original suite terminal13 OK')
check(ob['source_sha']==S and ob['original_completed'] and ob['original_exit']==0 and ob['observer_complete'] and not ob['observation_errors'] and not ob['subject_verdicts_changed'] and ob['source_tool_bytes_unchanged'],'passive observer preserved original result/source')
cmds={x['number']:x for x in ob['commands']};check(len(cmds)==len(ob['commands'])==124,'124 unique original child commands')
for n,row in cmds.items():
    check(row['completed_process_returned'] and row['exception'] is None,'normal original return '+str(n))
    for stream in ['stdout','stderr']:
        q=row[stream];b=Path(q['path']).read_bytes();check(q['captured'] and len(b)==q['bytes'] and h(b)==q['sha256'],'full original stream '+str(n)+'/'+stream)
    if 'actual_executable' in row:
        x=row['actual_executable'];check(x.get('bytes',0)>0 and len(x.get('sha256',''))==64,'actual runtime executable pin '+str(n))
compilers=[x for x in cmds.values() if Path(x['args'][0][0]).name in ['cc','gcc','clang']]
check(len(compilers)==suite['compile_commands']==93 and all(x['returncode']==0 for x in compilers),'93 actual compile/link0')
proofs=suite['control_proofs'];check(len(proofs)==14 and len({p['control'] for p in proofs})==14,'ten old plus four new distinct controls')
old=[];new=[]
for p in proofs:
    numbers=p['command_numbers'];rows=[cmds[n] if n is not None else None for n in numbers]
    exits=[x['returncode'] if x else None for x in rows]
    if numbers[-1] is None:
        old.append(p);check(exits==p['actual_exits']==[0,1,None],'old baseline/red no invented restoration '+p['control'])
        check('no per-control restored execution claimed' in p['claim'],'old scope truthful '+p['control'])
    else:
        new.append(p);check(exits==p['actual_exits']==[0,1,0] and numbers==sorted(numbers),'new actual ordered0/1/0 '+p['control'])
    check(all(x['args'][0][-1]==p['case'] for x in rows if x),'same named case '+p['control'])
    check(p['mutant_matches']==1 and p['passed'] and Path(rows[1]['args'][0][0]).name==p['control'],'intended variant identity '+p['control'])
    check(p['expected_assertion'] in Path(rows[1]['stderr']['path']).read_text() and rows[1]['returncode']==1,'normal named assertion1 '+p['control'])
check(len(old)==10 and len(new)==4,'old/new counts are not conflated')
ret=read(F/'panel-native/compile-retention/retention.json');check(len(ret)==1,'one original build-log retained')
for record in ret:
    b=Path(record['retained']).read_bytes();check(len(b)==record['bytes'] and h(b)==record['sha256'],'original build-log pin')
    for src in record['compiled_sources']:
        b=Path(src['retained']).read_bytes();check(len(b)==src['bytes'] and h(b)==src['sha256'],'original actual compiler input '+src['retained'])
sources={Path(x['retained']).name:Path(x['retained']) for rr in ret for x in rr['compiled_sources']}
before=Path('/workspace/issue128-p2-draft-20261024/before/panel_layout.c').read_bytes();after=Path('/workspace/issue128-p2-draft-20261024/after/panel_layout.c').read_bytes()
check(sources['empty-axis-work-fixed.c'].read_bytes()==after and sources['empty-axis-work-restored.c'].read_bytes()==after,'fixed and independently rebuilt restore equal accepted entire product')
check(sources['empty-axis-work-withdrawn.c'].read_bytes()==before,'withdrawal is exact entire original product, not a fabricated extra loop')
for name,expect in [('fixed',[2,2]),('withdrawn',[5000,50000000]),('restored',[2,2])]:
    row=next(x for x in cmds.values() if Path(x['args'][0][0]).name=='empty-axis-work-'+name and x['args'][0][-1]=='empty-axis-work')
    raw=Path(row['stdout']['path']).read_text();numbers=re.findall(r'empty-axis length=(\d+) phase-calls=(\d+) status=(\d+) clip-status=(\d+)',raw)
    check([int(x[0]) for x in numbers]==[10000,100000000] and [int(x[1]) for x in numbers]==expect and all(x[2:] == ('7','0') for x in numbers),'true operation counts and same status '+name)
    check('empty-axis-work phase='+name+'\n'+raw in stdout,'whole original cost output forwarded '+name)
    compile_rows=[x for x in compilers if any(Path(a).name=='empty-axis-work-'+name+'.c' for a in x['args'][0])]
    check(len(compile_rows)==1 and '-Dgeo_alternating_shift=pf_probe_alternating_shift' in compile_rows[0]['args'][0],'actual one-TU instrumentation '+name)
check(all('-Dgeo_alternating_shift=pf_probe_alternating_shift' not in x['args'][0] for x in compilers if any(Path(a).name=='grid.c' for a in x['args'][0])),'true K helper not renamed or instrumented')
missing=not Path(suite['native_execution_log']).exists()
report={'schema':'independent-issue128-p2-actual-peer/1','source_sha':S,'checks_total':len(checks),'failed_checks':len(findings),'findings':findings,'suite_methods':13,'suite_skip':0,'compiler_count':93,'original_controls':{'count':10,'actual_scope':'baseline0 and normal named assertion1; per-control restoration not claimed'},'new_controls':{'count':4,'actual_exits':[0,1,0]},'whole_optimization_withdrawal':'Exact entire original pre-P2 product bytes compiled; restored exact candidate bytes independently recompiled.','configured_native_jsonl_missing':missing,'metadata_notes':['Configured native_execution_log did not materialize; publish actual observer paths and distinguish real cleanup build-log.'] if missing else [],'limitations':['No subject rerun, global ledger, architecture, full native/browser or wall-clock performance verification.','Original captured text is UTF-8 retained text, not hidden pre-decode pipe bytes.','The pending archive publication needs its own roundtrip review.']}
(HERE/'CHECKS.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n');(HERE/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'failed':len(findings),'sha256':h((HERE/'REVIEW.json').read_bytes()),'findings':findings}))
raise SystemExit(bool(findings))
