#!/usr/bin/env python3
"""Post-run receipt/source/semantic review only. Does not execute any product."""
import hashlib,json,re
from pathlib import Path
RAW=Path('/workspace/closure-evidence/sr62-sanitizer-mutations-r1')
PREP=Path('/workspace/closure-evidence/final-contract-probes/native-sanitizer-mutations')
OUT=Path(__file__).resolve().parent
def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
checks=[]
def check(name,passed,detail=None):checks.append({'name':name,'passed':bool(passed),'detail':detail})
summary=read(RAW/'summary.json');plan=read(RAW/'executed-plan.json')
check('terminal original summary retained failed automation outcome',summary['complete'] and summary['passed'] is False and summary['liveStatusBefore']==summary['liveStatusAfter']=='' and summary['liveHead']==plan['head']=='d8642b2e684038cbb8e24aba057c44e7aac1b231')
check('executed source harness unchanged from source-reviewed freeze',sha(RAW/'executed-run.py')=='744f4f84b23a2d08463fe861f17fc48304dded406d4e65365d52643b973b50d1' and sha(RAW/'executed-oracle_runner.py')=='b8deb88dba4699a9627aaf30d74f25c43f4e2ee7511cc1b5b88ffae1ab974085' and sha(RAW/'executed-plan.json')==summary['planSha256']=='0470f60a70a67ee50c850db7c55793ece7b82dafc9fd6a772aa02496afe11cf9')
for row in plan['sourceFiles']:
    check('pristine source '+row['path'],sha(RAW/'pristine-source'/row['path'])==row['sha256'])
compiles=[('baseline',summary['baselineCompile'])]+[(r['id'],r['compile']) for r in summary['mutations']]
for name,c in compiles:
    check(name+' actual serial sanitizer compile',c['exitCode']==0 and not c.get('timeout') and all(flag in c['command'] for flag in plan['compileFlags']) and c['command'][-1]=='-lm')
    for stream in ('stdout','stderr'):
        check(name+' compiler '+stream+' raw hash',sha(RAW/(('baseline' if name=='baseline' else name)+'-compile.'+stream))==c[stream+'Sha256'])
previous=None
for name,c in compiles:
    if previous:check(name+' compile starts after prior compile',c['startedAt']>previous)
    previous=c['startedAt']
baseline=read(RAW/'baseline/result.json')
check('new baseline54 original tests completed cleanly',baseline['testsRun']==54 and baseline['failures']==baseline['errors']==0 and baseline['sessions']==45 and not baseline['skipped'] and not baseline['expectedFailures'] and not baseline['unexpectedSuccesses'] and not baseline['unhealthySessions'] and summary['baseline']['command']['exitCode']==0)
sessions=[]
for path in sorted(RAW.glob('*/session-*/transport.json')):
    rec=read(path);folder=path.parent
    stderr=(folder/'stderr.raw').read_bytes()
    stdout=[json.loads(line) for line in (folder/'stdout.raw').read_text().splitlines()]
    replies=[r['response'] for r in rec['commands'] if 'response' in r]
    ok=(rec['exitCode']==0 and not rec['cleanupErrors'] and not rec['sanitizerDiagnostic']
        and not rec.get('stopTimeout') and not rec['unexpectedStdoutTail']
        and hashlib.sha256(stderr).hexdigest()==rec['stderrSha256']
        and not re.search(rb'AddressSanitizer|LeakSanitizer|UndefinedBehaviorSanitizer|runtime error:',stderr)
        and stdout==replies)
    check(str(path.relative_to(RAW))+' healthy native plus full stdout/stderr',ok)
    sessions.append({'path':str(path.relative_to(RAW)),'sha256':sha(path),'stderrSha256':sha(folder/'stderr.raw'),'stdoutSha256':sha(folder/'stdout.raw'),'exitCode':rec['exitCode']})
check('all expected native process receipts preserved',len(sessions)==55)
rows=[]
for spec,run in zip(plan['mutations'],summary['mutations'],strict=True):
    mid=spec['id'];observed=read(RAW/mid/'result.json');restored=read(RAW/(mid+'-restored')/'result.json')
    expected_line=189 if mid in ('M62-1','M62-3') else spec['expectedAssertionLine']
    check(mid+' exactly one original semantic AssertionError',run['oracle']['command']['exitCode']==1 and observed['tests']==[spec['test']] and observed['testsRun']==1 and observed['failures']==1 and observed['errors']==0 and not observed['skipped'] and not observed['expectedFailures'] and not observed['unhealthySessions'] and len(observed['details'])==1 and observed['details'][0]['exception']=='AssertionError' and any(f['file']==str(RAW/'pristine-source/tests/test_grid_subdivision_oracle.py') and f['line']==expected_line for f in observed['details'][0]['frames']))
    check(mid+' unchanged target passes after byte-exact pristine restoration',run['restoredOracle']['command']['exitCode']==0 and restored['tests']==observed['tests'] and restored['testsRun']==1 and restored['failures']==restored['errors']==0 and not restored['skipped'] and not restored['unhealthySessions'] and restored['binarySha256']==run['restoredBinarySha256']==summary['pristineBinarySha256'])
    for name in (mid,mid+'-restored'):
        cmd=read(RAW/(name+'.command.json'))
        check(name+' actual64MiB/leak halt environment',cmd['stackBytes']==67108864 and cmd['environment']['ASAN_OPTIONS']=='detect_leaks=1:halt_on_error=1:abort_on_error=1' and cmd['environment']['UBSAN_OPTIONS']=='halt_on_error=1:print_stacktrace=1')
        for stream in ('stdout','stderr'):check(name+' oracle '+stream+' hash',sha(RAW/(name+'.'+stream))==cmd[stream+'Sha256'])
    for source in plan['sourceFiles']:
        expected=spec['afterSha256'] if source['path']==spec['path'] else source['sha256']
        check(mid+' isolated source '+source['path'],sha(RAW/(mid+'-source')/source['path'])==expected)
    actual=read(RAW/mid/'session-000/transport.json')['commands'];control=read(RAW/(mid+'-restored')/'session-000/transport.json')['commands']
    proof={}
    if mid in ('M62-1','M62-3'):
        match=(lambda c:'divide 7 2' in c) if mid=='M62-1' else (lambda c:c.startswith('line grid-binding 0 on-boundary 1 from-system 1 '))
        bad=next(r for r in actual if match(r['command']));good=next(r for r in control if match(r['command']))
        reason='DIVISION_NOT_EXACT' if mid=='M62-1' else 'WRONG_SOURCE'
        proof={'command':bad['command'],'mutantOk':bad['response']['ok'],'mutantPreviewValid':bad['response']['preview']['valid'],
               'mutantViolations':bad['response']['preview']['violations'],'restoredViolations':good['response']['preview']['violations']}
        check(mid+' exact rejected-operation preview branch proof',bad['command']==good['command'] and bad['response']['ok'] is False and bad['response']['preview']['valid'] is True and bad['response']['preview']['violations']==[] and good['response']['preview']['valid'] is False and any(reason in v['actual'] for v in good['response']['preview']['violations']))
        if mid=='M62-1':
            src=bad['response']['preview']['gridSystems'][0]['after']
            check(mid+' actual 600/7 nonintegral source',src['uDefinition']['step']==600 and src['rules'][0]['divisions']==[7,2] and '(divisions=(7, 2))' in observed['details'][0]['test'])
        else:
            preview=bad['response']['preview']
            check(mid+' actual mismatched source identity with same rule key',preview['gridBindings'][0]['before']['system']==0 and preview['gridBindings'][0]['after']['system']==1 and preview['guides'][0]['after']['expression']=='gridrule:10:0:1:-2:1:u:0')
    elif mid=='M62-2':
        dumps=[r['response']['text'] for r in actual if r['command']=='dump']
        last=dumps[-1];proof={'dump':last}
        check(mid+' serialized rule lost while source and allocator retained','grid-system 0 ' in last and 'grid-source-rule-highwater 0 next 2' in last and 'grid-source-rule 0 key 1' not in last)
    elif mid=='M62-4':
        query=next(r['response'] for r in actual if r['command'].startswith('grid-rule-query binding'))
        line=next(r for r in query['lines'] if r['axis']=='u' and r['innerIndex']==0)
        proof={'actualLine':line,'literalExpectedSegments':[[[300,200],[300,250]],[[300,550],[300,600]]]}
        check(mid+' actual hole ignored in the returned line',line['coordinate']==300 and line['segments']==[[[300,200],[300,600]]])
    else:
        load=next(r for r in actual if r['command'].startswith('loadfile '));scene=(RAW/mid/'session-000'/load['loadedInput']['path']).read_text()
        proof={'input':scene,'response':load['response'],'inputSha256':load['loadedInput']['sha256']}
        check(mid+' actual missing capability accepted','grid-source-rule-highwater 0 next 1' in scene and 'requires ' not in scene and load['response']['ok'] is True and hashlib.sha256(scene.encode()).hexdigest()==load['loadedInput']['sha256'])
    rows.append({'id':mid,'originalAutoVerdict':run['verdict'],'reviewedSemanticVerdict':'SEMANTIC_ASSERTION_KILL',
                 'originalPin':spec['expectedAssertionLine'],'actualAssertionLine':expected_line,'proof':proof,
                 'resultSha256':sha(RAW/mid/'result.json'),'restoredResultSha256':sha(RAW/(mid+'-restored')/'result.json')})
check('same pristine binary restored at both final paths',sha(RAW/'active-bridge')==sha(RAW/'pristine-bridge')==summary['pristineBinarySha256']==summary['finalRestoredBinarySha256']==summary['finallyRestoredBinarySha256'])
report={'schema':'geometry-sgr62-independent-semantic-review/1','reviewer':'/root/remote_inventory','productExecutionByReviewer':False,
        'passed':all(c['passed'] for c in checks),'rawSummarySha256':sha(RAW/'summary.json'),'originalDriverExitCode':1,
        'originalAutomationOutcome':'3 SEMANTIC_ASSERTION_KILL, 2 OTHER_FAILURE_NOT_A_KILL; original summary.passed=false retained',
        'reviewedOutcome':'New baseline54 sanitizer scope and all five required original-oracle semantic faults demonstrated; each target passes on restored pristine binary',
        'classificationCorrection':{'appliesOnlyTo':['M62-1','M62-3'],'preparedPin':187,'observedExistingAssertion':189,
          'explanation':'The original reject helper tests immediate acceptance at187 and, when the transaction transport returns ok:false/preview, separately asserts preview.valid is false at189. The private classifier pinned only187. Raw original assertions fail at189 for precisely the forbidden nonintegral rule and cross-source same-key operations. Their identical restored commands reject with DIVISION_NOT_EXACT/WRONG_SOURCE. This addendum corrects receipt classification, not fixture, product acceptance, original tests or expectations. No arbitrary error/crash is credited; no rerun or recompile was performed by reviewer.'},
        'mutations':rows,'checks':checks,'nativeSessions':sessions,
        'limits':['54 includes41 subdivision tests plus13 grid-system contract tests, with45 baseline native processes; it does not reconstruct historical152.',
                  'M62-1 and M62-3 demonstrate an incorrectly valid candidate; original oracle stops before confirming it. Do not claim an observed committed invalid World.',
                  'M62-4 selects clipping alternative, not sample-index mutation. M62-5 selects capability preflight alternative, not second-face mutation.',
                  'No browser acceptance, new product feature or approval to merge is inferred. Original failed automation round and all source/raw evidence must remain retained.']}
(OUT/'independent-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'failed':[c for c in checks if not c['passed']],'nativeSessions':len(sessions),'reviewedMutationCount':len(rows)},ensure_ascii=False))
