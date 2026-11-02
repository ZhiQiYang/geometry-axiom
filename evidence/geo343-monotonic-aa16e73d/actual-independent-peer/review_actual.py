from pathlib import Path
import ast,hashlib,json,re
R=Path('/workspace/geo343-monotonic-formal-20261024');O=Path(__file__).parent
D=Path('/workspace/geo343-monotonic-sort-draft-20261024');S='aa16e73d6e1f2965e0a911581e2a545aaaf66870'
checks=[];cache={}
def check(name,v):checks.append({'check':name,'passed':bool(v)})
def sha(p):
    p=Path(p)
    if p not in cache:cache[p]=hashlib.sha256(p.read_bytes()).hexdigest()
    return cache[p]
def retained(item):
    p=Path(item['retained']);check('retained bytes '+item['sha256'],p.stat().st_size==item['bytes'] and sha(p)==item['sha256'])
    return p.read_bytes()
r=json.loads((R/'RESULT.json').read_bytes());outer=json.loads(Path('/workspace/geo343-monotonic-formal-launch-20261024/RESULT.json').read_bytes())
check('source S',r['source_sha']==outer['source_sha']==S)
check('actual primary reaper outer zero',outer['primary_exit']==outer['reaper_exit']==outer['exit']==r['exit']==0)
check('no overall errors clean source',not r['errors'] and r['source_clean_after'] is True)
check('no full/perf/ledger overclaim',r['full_native'] is r['performance'] is r['ledger_regenerated'] is False)
all_commands=[];snapshots=[];compile_count=0
for suite,methods in zip(r['suites'],[13,15,7]):
    label=suite['label'];root=R/label;obs=root/'observed';entry=json.loads((obs/'ORIGINAL_ENTRY.json').read_bytes());overview=json.loads((obs/'OBSERVATION.json').read_bytes());runner=json.loads((root/'runner.json').read_bytes())
    check('normal suite OS '+label,suite['actual_exit']==suite['command']['actual_process_returncode']==0)
    check('runner original strict '+label,runner==suite['runner'] and runner['run']==runner['total']==runner['passed']==methods and all(runner[k]==0 for k in ['failed','skipped','explicit_skipped','unrun_skipped','blocked_by_error','expected_failed','extra_errors']))
    check('entry original complete '+label,entry['original_completed'] is True and entry['original_exit']==0 and entry['source_sha']==S)
    check('source before after exact '+label,entry['source_files_before']==entry['source_files_after'])
    check('observer complete '+label,overview['observer_complete'] is True and not overview['observation_errors'] and not overview['incomplete_sessions'])
    receipts=sorted(obs.glob('command-*/receipt.json'));check('observed command count '+label,len(receipts)==overview['commands'])
    for path in receipts:
        c=json.loads(path.read_bytes());argv=c['args'][0]
        check('completed original command '+str(path),c['completed_process_returned'] is True and c['exception'] is None and type(c['returncode']) is int)
        for stream in ['stdout','stderr']:
            st=c[stream];p=path.parent/(stream+'.bin')
            if st['captured']:check('full command '+stream+' '+str(path),p.stat().st_size==st['bytes'] and sha(p)==st['sha256'])
            else:check('original inherited stderr explicit '+str(path),label=='reading-a' and stream=='stderr' and c['number'] in [61,66] and argv==['git','-C','/workspace/geo343-monotonic-work-20261024','rev-parse','HEAD'] and c['kwargs'].get('stdout')==-1 and 'stderr' not in c['kwargs'] and not c['kwargs'].get('capture_output') and not p.exists())
        if Path(argv[0]).name in ['cc','gcc','cl']:
            check('normal compile/link0 '+str(path),c['returncode']==0 and c['kwargs']['timeout']==300);compile_count+=1
        all_commands.append((label,path,c))
    for path in obs.glob('session-*/receipt.json'):
        c=json.loads(path.read_bytes());check('true bridge session terminal '+str(path),c['complete'] is True and c['actual_returncode']==0 and c['source_sha']==S)
        for stream,item in c['streams'].items():check('complete session '+stream+' '+str(path),Path(item['path']).stat().st_size==item['bytes'] and sha(item['path'])==item['sha256'])
    ss=json.loads((obs/'native-inputs/compiler-input-snapshots.json').read_bytes())
    for item in ss:
        for source in item['inputs']:retained(source)
    snapshots.extend(ss)
check('all original35methods',sum(x['runner']['run'] for x in r['suites'])==35)
check('332 actual compile/link zero',compile_count==332)
rows=[json.loads(line) for line in (R/'wood-contact/native-executions.jsonl').read_text().splitlines()]
check('177 original native rows',len(rows)==177)
command_rows=[(p,c) for label,p,c in all_commands if label=='wood-contact'];cursor=0
for row in rows:
    while cursor<len(command_rows) and command_rows[cursor][1]['args'][0]!=row['command']:cursor+=1
    check('native record chronological original '+str(cursor),cursor<len(command_rows))
    if cursor==len(command_rows):break
    path,c=command_rows[cursor];cursor+=1
    check('native record actual result '+str(cursor),c['returncode']==row['actual_exit'] and (path.parent/'stdout.bin').read_bytes()==row['stdout'].encode() and (path.parent/'stderr.bin').read_bytes()==row['stderr'].encode())
    check('native source/ELF/time '+str(cursor),row['source_sha']==S and row['executable_sha256']==c['executable']['sha256'] and c['kwargs']['timeout']==20)
new=[x for x in rows if 'test_monotonic_sort_' in x['test']];check('45 new original native rows',len(new)==45)
work=[]
for phase,count,exitcode in [('fixed',128,0),('withdrawn',896,1),('restored',128,0)]:
    group=[x for x in new if x['control']=='monotonic-whole' and x['phase']==phase]
    check('ten exact semantic zeros '+phase,len(group)==11 and all(x['actual_exit']==0 for x in group if x['case']!='work'))
    w=next(x for x in group if x['case']=='work');work.append({'phase':phase,'exit':w['actual_exit'],'stdout':w['stdout'],'stderr':w['stderr']})
    check('whole exact work '+phase,w['actual_exit']==exitcode and w['stdout']==f'CASE work faces=128 first=2 order_calls={count}\n' and w['stderr']==('ASSERT:monotonic-linear-order-lookups\n' if exitcode else ''))
tree=ast.parse((D/'candidate/tests/test_geo261_wood_contact_world.py').read_text());method=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='test_monotonic_sort_preserves_full_fields_and_linear_sorted_lookup_work')
controls=ast.literal_eval(next(n.value for n in method.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='controls' for t in n.targets)))
for label,before,after,case,marker in controls:
    rr=[x for x in new if x['control']==label]
    check('adjacent baseline mutant restored '+label,[(x['phase'],x['actual_exit']) for x in rr]==[('baseline',0),('mutant',1),('restored',0)])
    check('normal exact assertion '+label,rr[1]['stderr']=='ASSERT:'+marker+'\n' and all(x['case']==case for x in rr))
product=(D/'candidate/geometry-templates/woodworking/native/contact_world.c').read_bytes()
assignment=lambda name:ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)))
block=assignment('MONOTONIC_SORT_BLOCK').encode()
variants={'fixed':product,'withdrawn':product.replace(block,b''),'restored':product}
variants.update({label:product.replace(before.encode(),after.encode()) for label,before,after,_,_ in controls})
anchor=b'static uint64_t contact_order(const WoodContactWorld *world,const ContactOrderIndex *index,uint32_t id)\n{'
instrumented=b'static size_t geo_test_sort_order_calls;\n'+anchor+b'\n    ++geo_test_sort_order_calls;'
selected=[s for s in snapshots if 'actual-monotonic-included-TU-at-compile' in s['roles']]
check('seven genuine included product compile snapshots',len(selected)==7)
for label,expected in variants.items():
    name='contact-monotonic-'+label+'-source.c';items=[i for s in selected for i in s['inputs'] if Path(i['original']).name==name]
    check('unique compiled variant '+label,len(items)==1)
    actual=retained(items[0]);check('compiled actual variant exact '+label,expected.count(anchor)==1 and actual==expected.replace(anchor,instrumented))
check('whole actual removed equals U',(D/'before/geometry-templates/woodworking/native/contact_world.c').read_bytes()==variants['withdrawn'])
findings=[x['check'] for x in checks if not x['passed']]
report={'source_sha':S,'checks':len(checks),'failures':len(findings),'findings':findings,'original_methods':35,'compile_link_zero':compile_count,'new_semantic_controls':len(controls),'whole_work':work,'scope':'Independent original actual streams/compiler-input/metadata review; no subject rerun, C compilation, network, or archive rewrite. Source/evidence publication peer is separate. Full native, ledger, architecture and original final-union performance remain UNRUN for this source.','reviewer_correction':'Initial reader wrongly required a per-command stderr file for two original reading-a git check_output calls (61/66) that inherit stderr. Original captured:false plus argv/kwargs and missing-file state verified exactly; not rewritten or invented. Initial failed helper/report retained.'}
(O/'ACTUAL_REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(O/'ACTUAL_CHECKS.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False));raise SystemExit(bool(findings))
