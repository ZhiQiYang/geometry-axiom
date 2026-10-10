"""Read-only census of a terminal committed-caption receipt; never runs browsers."""
from pathlib import Path
from collections import Counter
import argparse,datetime,hashlib,json,sys

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--expected-sha',required=True)
parser.add_argument('--expected-probe-sha256',required=True)
parser.add_argument('--gate',type=Path,required=True)
parser.add_argument('--probe',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
assert len(args.expected_sha)==40 and all(c in '0123456789abcdef' for c in args.expected_sha)
assert len(args.expected_probe_sha256)==64 and all(c in '0123456789abcdef' for c in args.expected_probe_sha256)
assert not args.output.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
g=json.loads(args.gate.read_bytes());p=json.loads(args.probe.read_bytes())
run=p['run'];b=g['before'];a=g['after'];rows=p['results'];node=g['executionIdentity']['node'];chrome=g['executionIdentity']['browser']
log=Path(g['log']['path']);probe_log=Path(run['rawLogPath']);checks=[]
def check(name,ok,detail=None):checks.append({'name':name,'ok':ok is True,**({'detail':detail} if detail is not None else {})})
passed=sum(r.get('ok') is True for r in rows);failed=len(rows)-passed;counts=Counter(r['group'] for r in rows)
check('full original sourceSHA clean before/after exactly bound',b['git']==a['git'] and b['git']['head']==run['head']==run['headAfter']==args.expected_sha and b['git']['status']==run['dirty']==run['dirtyAfter']=='')
runtimes=[b['runtime'],a['runtime'],run['runtimeBefore'],run['runtimeAfter']]
check('runtime fresh same source/session/root/pid throughout actual command',all(x['fresh'] is True for x in runtimes) and all(len({str(x.get(k)) for x in runtimes})==1 for k in ['schema','root','version','session','pid']) and b['sourceVersion']==a['sourceVersion'])
check('actual Node executable bytes command cwd and childpid exact',node['sha256']==b['executables']['node']['sha256'] and node['executable']==b['executables']['node']['resolved'] and node['cmdline']==g['command'] and node['cwd']==b['root'] and node['pid']==g['execution']['pid'])
check('actual sandboxed Chromium ELF bytes owned profile exact',chrome['sha256']==b['executables']['actual-chrome']['sha256'] and chrome['executable']==b['executables']['actual-chrome']['resolved'] and chrome['sandboxDisabledFlagsAbsent'] is True and chrome['ownedProfile'].startswith('/tmp/playwright_chromium') and all(x not in {'--no-sandbox','--disable-setuid-sandbox'} and not x.startswith('--type=') for x in chrome['cmdline']))
check('captured source/runner/executables/native/livebridge unchanged',g['executionIdentity']['errors']==[] and all(b[k]==a[k] for k in ['executables','sources','executionFiles','runnerSHA256','configuredNativeCore','liveBridge','native']) and bool(b['liveBridge']) and b['liveBridge'][0]['sha256']==b['native']['bridge']['sha256'] and all(x['state']=='fresh' for x in b['native'].values()))
check('actual terminal command no timeout/interruption/identity problems',not g['execution']['timedOut'] and not g['execution']['interrupted'] and g['problems']==[])
check('original rawlogs and probeJSON match declared immutable SHA',sha(log)==g['log']['sha256'] and sha(args.probe)==g['acceptanceResult']['probeSHA256'] and sha(probe_log)==run['rawLogSHA256'])
canonical=[json.loads(s[len('UI123_RESULT '):]) for s in log.read_text().splitlines() if s.startswith('UI123_RESULT ')]
c=canonical[0] if len(canonical)==1 else {}
check('one original UI123_RESULT canonical record',len(canonical)==1)
check('all positive total/pass/fail census agrees exactly',len(rows)>0 and p['passed']==g['acceptanceResult']['passed']==c.get('passed')==passed and p['failed']==g['acceptanceResult']['failed']==c.get('failed')==failed and passed+failed==len(rows),{'passed':passed,'failed':failed,'total':len(rows),'groups':dict(counts)})
groups=p['groupResults'];scope=run['scope'];omitted=['colors','headers','components','v3','grid-mobile','model']
check('sole caption scope preserved; original six explicitly omitted',[r['group'] for r in groups]==['caption'] and scope['included']==['caption'] and scope['omitted']==omitted and c.get('scope')==scope and run['commandEnvironment']['GEOMETRY_UI123_GROUPS']==g['scopeEnvironment']['GEOMETRY_UI123_GROUPS']=='caption')
check('all exact positive group counts/results preserved',set(counts)=={'preflight','caption','final'} and all(r['checks']==counts[r['group']] and r['checks']>0 and r['ok']==all(x['ok'] is True for x in rows if x['group']==r['group']) for r in groups) and c.get('groupResults')==groups)
success=failed==0
check('attempt completion and acceptance remain correctly distinct',p['completed'] is True and c.get('completed') is True and g['acceptanceResult']['attemptedAllGroups'] is True and g['acceptanceResult']['completed']==g['probeVerified']==success and run['exitCode']==c.get('exitCode')==g['execution']['exitCode']==g['gateExitCode']==(0 if success else 1))
prov=g['testSourceProvenance'];expected_probe=str(Path(b['root'])/'tests/issue123_caption_browser.cjs')
check('actual explicitly pinned committed caption executes without source override',prov['productFullSHA']==args.expected_sha and prov['productDirtyBefore']=='' and prov['executedProbe']==prov['formalCandidateProbe']==g['command'][1]==expected_probe and prov['sourceOverride'] is False and prov['approvedOverrideExpectedSHA256'] is None and prov['executedProbeSHA256']==prov['formalCandidateProbeSHA256']==run['scriptSHA256']==b['sources']['tests/issue123_caption_browser.cjs']==args.expected_probe_sha256 and prov['productBeforeAfterIdentityMatches'] is True)
check('actual64b31 formal runner identity exact',b['runnerSHA256']=='64b31cc10e836649c7d957ad2a36991482447c8e30b9cfb89cc666740d51a277')
check('probe critical product and native source bytes agree',all(b['sources'][name]==digest==a['sources'][name] for name,digest in run['sources'].items()) and run['executables']['bridge']['sha256']==b['native']['bridge']['sha256'] and run['executables']['modelBase']['sha256']==b['native']['model-base']['sha256'])
check('original seven widths/fixture/source policy unchanged',run['captionSourceProvenance']['widths']==[1382,1160,900,680,600,560,390] and scope['mode']=='caption-only-seven-width-normal-input' and 'all 43 checklist items' in scope['notCovered'] and 'private ZIP pixel/reference comparison' in scope['notCovered'])

def positive(name,count=1):
    found=[r for r in rows if r['name']==name];return len(found)==count and all(r.get('ok') is True for r in found)
coverage=[]
for width in [1382,1160,900,680,600,560,390]:
    names=['original six-surface source ownership and normal face entry '+str(width),
           'normal input selects original pan pointer '+str(width),'normal input selects original select pointer '+str(width),
           'normal input selects original pan Tab+Enter '+str(width),'normal input selects original select Shift+Tab+Enter '+str(width),
           'real Tab reaches exact original last PAN '+str(width),'real Shift+Tab reaches exact original first SELECT '+str(width),
           'actual trusted pointer keyboard and native button activation '+str(width),'entire original native dump unchanged after caption and normal gestures '+str(width)]
    for label in ['entered','pointer PAN to SELECT','keyboard PAN','keyboard SELECT']:
        names.extend([s+label+' '+str(width) for s in ['fixture exact original title and nonempty owner caption ','actual caption vertical/horizontal bounds ','exact eight original top-level toolbar controls ','bounded normal toolbar and live canvas retain original sizes (mobile44) ']])
    names.extend(['real '+key+' remains in original nav '+label+' '+str(width)+' step'+str(step) for key,label in [('Tab','last PAN'),('Shift+Tab','first SELECT')] for step in range(7)])
    complete=all(positive(name) for name in names)
    reached=sum(any(r['name']==name for r in rows) for name in names)
    coverage.append({'width':width,'completeOriginalNormalContract':complete,'requiredOriginalNames':len(names),'reached':reached,'nativeUnchangedPassed':positive('entire original native dump unchanged after caption and normal gestures '+str(width))})
    check('width'+str(width)+' completeness correctly limited by actual receipt',complete if success else True,coverage[-1])
    if complete:
        events_file=args.probe.parent/('caption-'+str(width)+'-trusted-normal-input.json')
        events=json.loads(events_file.read_bytes())
        check('actual archived trusted normal inputs '+str(width),len(events)>0 and all(e.get('trusted') is True for e in events) and all(any(e.get('type')=='keydown' and e.get('key')=='Enter' and e.get('tool')==tool for e in events) for tool in ['pan','select']) and any(e.get('type')=='keydown' and e.get('key')=='Tab' and e.get('shiftKey') is False for e in events) and any(e.get('type')=='keydown' and e.get('key')=='Tab' and e.get('shiftKey') is True for e in events))
check('success implies every originalwidth complete; failure remains uncompleted',all(x['completeOriginalNormalContract'] for x in coverage) if success else not all(x['completeOriginalNormalContract'] for x in coverage))
premise_names=['initial canvas lesson has one normal reachable dismissal','normal first-use dismissal hides lesson and preserves exact native source']
premise_rows={name:[r for r in rows if r['name']==name] for name in premise_names}
check('normal first-use premise paired positivity exactly preserved when executed',len(premise_rows[premise_names[0]])==len(premise_rows[premise_names[1]]) and len(premise_rows[premise_names[0]])<=7 and all(r.get('ok') is True for found in premise_rows.values() for r in found),{'counts':{name:len(found) for name,found in premise_rows.items()}})
archive=args.gate.parent/'executed-sources';manifest=archive/'manifest.json'
check('actual executed source archive present',manifest.is_file())
if manifest.is_file():
    m=json.loads(manifest.read_bytes());entries=m['entries']
    check('all archived frozen beforeSource bytes exact',all((archive/name).is_file() and sha(archive/name)==digest for name,digest in b['sources'].items()))
    check('all manifest entries/receiptSHA/fullSHA provenance exact',all(sha(archive/r['path'])==r['sha256'] for r in entries) and m['fullSHA']==args.expected_sha and m['receiptSHA256']==sha(args.gate) and m['testSourceProvenance']==prov)
    check('committedcaption originalbytes and actualrunner archived exact',sha(archive/'tests/issue123_caption_browser.cjs')==run['scriptSHA256'] and sha(archive/'run_formal_caption_gate.py')==b['runnerSHA256'])
bad=[r for r in rows if r.get('ok') is not True]
artifacts=[args.gate,args.probe,log,probe_log]+([manifest] if manifest.is_file() else [])
report={'schema':'geometry-committed-caption-independent-census/1','checkedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceFullSHA':args.expected_sha,'expectedExecutedProbeSHA256':args.expected_probe_sha256,'sourceDirty':'','readOnlyExistingEvidence':True,
        'executor':{'path':sys.executable,'sha256':sha(sys.executable),'command':sys.orig_argv,'scriptSHA256':sha(__file__)},
        'checks':checks,'integrityVerified':all(r['ok'] for r in checks),'passedIntegrityChecks':sum(r['ok'] for r in checks),'totalIntegrityChecks':len(checks),
        'recordedAcceptance':{'passed':passed,'failed':failed,'exitCode':g['execution']['exitCode'],'attemptCompleted':p['completed'],'acceptanceCompleted':g['acceptanceResult']['completed'],'scope':['caption'],'widthCoverage':coverage,'originalFailures':bad},
        'artifacts':[{'path':str(p),'sha256':sha(p)} for p in artifacts],'browserExecuted':False,'nativeExecuted':False,'repoModified':False,
        'limits':['Expected execution source is explicitly pinned and original strong seven-width assertions/fixture remain separately reviewed; first-use normal entry premise is separately identified','A sole caption group attempt ending is not all sevenwidth acceptance; actual perwidth full normal inputs/native endpoint only claimed where original names all passed','No formalSIX/fullCDP/fullSpace/all43/privateZIP/golden/physicalmobile/IME/OS-picker claim','Failure details are original getter fields only; no absent bbox/clientLeft is invented','Historical102ff27/1 and bb7 failures are kept independently; no aggregation or SHA rebinding']}
args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'report':str(args.output),'sha256':sha(args.output),'integrityVerified':report['integrityVerified'],'integrityChecks':[report['passedIntegrityChecks'],report['totalIntegrityChecks']],'recorded':[passed,failed],'actualAcceptance':g['probeVerified'],'failedIntegrityChecks':[r for r in checks if not r['ok']]},ensure_ascii=False))
sys.exit(0 if report['integrityVerified'] else 1)
