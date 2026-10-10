"""Independent read-only census of three completed attempts; no browser rerun."""
from pathlib import Path
from collections import Counter
import datetime,hashlib,json,sys

DIR=Path(__file__).resolve().parent
BASE='9eb670110379ec0d726914f3e5b2d8e7237f2b9c'
SCENARIOS=['pdf-rectangle','pdf-l','pdf-notch','image-rectangle','image-l','image-notch','image-rectangle-box','pdf-l-mobile','image-notch-mobile','pdf-l-transform']
NEGATIVE=[
'image-open-doorway: explicit failure leaves original scene and no completion receipt',
'image-neighbor: connected neighbor is disclosed instead of silently excluded',
'image-neighbor: explicit search separator excludes neighbor without editing source geometry',
'native-rejection-and-source-change: core rejects self-crossing orthogonal ring without changing original',
'native-rejection-and-source-change: recalibration requires review and retains exact confirmed geometry',
'native-rejection-and-source-change: source replacement retains exact geometry and becomes unreviewed']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def validate(kind):
    gate=Path('<workspace-path>')
    probe=Path('/tmp/'+({'ui123':'geometry-ui123-9eb67011-all-six/receipt.json','room54':'geometry-room54-102ff28e-original-ten/results.json','supplement':'geometry-ui123-102ff28e-supplement-four/receipt.json'}[kind]))
    g=json.loads(gate.read_text());p=json.loads(probe.read_text());run=p['run'];b=g['before'];a=g['after'];log=Path(g['log']['path']);node=g['executionIdentity']['node'];chrome=g['executionIdentity']['browser'];checks=[]
    def check(name,ok,detail=None):checks.append({'name':name,'ok':ok is True,**({} if detail is None else {'detail':detail})})
    rows=p['results'];passed=sum(r.get('ok') is True for r in rows);failed=len(rows)-passed
    check('frozen full SHA clean checkout identity is exact before after',b['git']==a['git'] and b['git']['head']==run['head']==BASE and b['git']['status']=='' and run['headAfter']==BASE and run.get('dirty',run.get('trackedChanges'))==run.get('dirtyAfter',run.get('trackedChangesAfter'))=='')
    check('fresh runtime version session root and service pid unchanged',b['sourceVersion']==a['sourceVersion'] and all(x['fresh'] is True for x in [b['runtime'],a['runtime'],run['runtimeBefore'],run['runtimeAfter']]) and all(len({str(x.get(k)) for x in [b['runtime'],a['runtime'],run['runtimeBefore'],run['runtimeAfter']]})==1 for k in ['schema','root','version','session','pid']))
    check('actual Node bytes exact child command cwd pid match configured source',node['sha256']==b['executables']['node']['sha256'] and node['executable']==b['executables']['node']['resolved'] and node['cmdline']==g['command'] and node['cwd']==b['root'] and node['pid']==g['execution']['pid'])
    check('actual Chromium bytes match configured real executable and owned root browser',chrome['sha256']==b['executables']['actual-chrome']['sha256'] and chrome['executable']==b['executables']['actual-chrome']['resolved'] and chrome['sandboxDisabledFlagsAbsent'] is True and chrome['ownedProfile'].startswith('/tmp/playwright_chromium') and all(x not in {'--no-sandbox','--disable-setuid-sandbox'} and not x.startswith('--type=') for x in chrome['cmdline']))
    check('capture identities source runner and live native bridge remain exact',g['executionIdentity']['errors']==[] and all(b[k]==a[k] for k in ['executables','sources','executionFiles','runnerSHA256','configuredNativeCore','liveBridge','native']) and bool(b['liveBridge']) and b['liveBridge'][0]['sha256']==b['native']['bridge']['sha256'] and all(x['state']=='fresh' for x in b['native'].values()))
    check('command completed without timeout interruption or wrapper problems',not g['execution']['timedOut'] and not g['execution']['interrupted'] and g['problems']==[])
    check('raw command log and original probe JSON retain exact receipt hashes',sha(log)==g['log']['sha256'] and sha(probe)==g['acceptanceResult']['probeSHA256'])
    provenance=g['testSourceProvenance'];executed=g['command'][1]
    check('explicit executed test identity and source override provenance agree',provenance['productFullSHA']==BASE and provenance['productDirtyBefore']=='' and provenance['executedProbe']==executed and provenance['productBeforeAfterIdentityMatches'] is True)
    artifacts=[gate,log,probe]
    if kind in {'ui123','supplement'}:
        groups=['colors','headers','components','v3','grid-mobile','model'] if kind=='ui123' else ['plan','bom','row-blur','s2']
        expected=(198,0) if kind=='ui123' else (108,3)
        canonical=[json.loads(s[len('UI123_RESULT '):]) for s in log.read_text().splitlines() if s.startswith('UI123_RESULT ')];c=canonical[0] if len(canonical)==1 else {}
        counts=Counter(r['group'] for r in rows);groupRows=p['groupResults'];omitted=[] if kind=='ui123' else ['colors','headers','components','v3','grid-mobile','model']
        check('unique original UI123_RESULT canonical record',len(canonical)==1)
        check('exact positive pass fail total across every original individual check', (passed,failed)==expected and len(rows)==sum(expected) and p['passed']==c.get('passed')==g['acceptanceResult']['passed']==passed and p['failed']==c.get('failed')==g['acceptanceResult']['failed']==failed)
        check('all declared groups attempted exactly once and scope preserved', [r['group'] for r in groupRows]==groups and run['scope']['included']==groups and run['scope']['omitted']==omitted and c.get('scope')==run['scope'] and run['commandEnvironment']['GEOMETRY_UI123_GROUPS']==g['scopeEnvironment']['GEOMETRY_UI123_GROUPS']==','.join(groups))
        check('positive exact group check census matches original archived result rows',all(r['checks']==counts[r['group']] and r['checks']>0 and r['ok']==all(x['ok'] is True for x in rows if x['group']==r['group']) for r in groupRows) and c.get('groupResults')==groupRows and set(counts)==set(groups)|{'preflight','final'},dict(counts))
        check('all scope bodies attempted completion differs correctly from acceptance',p['completed'] is True and c.get('completed') is True and g['acceptanceResult']['attemptedAllGroups'] is True and g['acceptanceResult']['completed']==(failed==0) and g['probeVerified']==(failed==0) and run['exitCode']==c.get('exitCode')==g['execution']['exitCode']==g['gateExitCode']==(0 if failed==0 else 1))
        check('all probe critical product source and native executable hashes agree',all(b['sources'][name]==digest==a['sources'][name] for name,digest in run['sources'].items()) and run['executables']['bridge']['sha256']==b['native']['bridge']['sha256'] and run['executables']['modelBase']['sha256']==b['native']['model-base']['sha256'])
        check('source identity executed actual Node probe bytes matches archived provenance',run['scriptSHA256']==provenance['executedProbeSHA256'] and provenance['sourceOverride']==(kind=='supplement') and (kind=='supplement' or b['sources']['tests/issue123_adopted_slices_browser.cjs']==run['scriptSHA256']))
        probeLog=Path(run['rawLogPath']);artifacts.append(probeLog)
        check('probe own raw log SHA matches original archive',sha(probeLog)==run['rawLogSHA256'])
        check('no unclaimed broader acceptance or unexpected dialogs/errors',p['errors']==[] and run['scope']['mode']=='explicit-partial-adopted-ui-contract' and 'all 43 checklist items' in run['scope']['notCovered'] and 'private ZIP pixel/reference comparison' in run['scope']['notCovered'] and all(d.get('accepted') is True for d in p['dialogs']))
        if kind=='supplement':
            bad=[r for r in rows if r.get('ok') is not True]
            check('all three original concrete failures retained, not normalized into passes',[r['group'] for r in bad]==['bom','row-blur','s2'] and all(r['name']=='unexpected execution failure' for r in bad) and "wait" in bad[0]['error'] and "locator('#refRoomConfirm')" in bad[1]['error'] and 'disabled' in bad[1]['error'] and "locator('#igDeleteBinding')" in bad[2]['error'],bad)
        recorded={'passed':passed,'failed':failed,'exitCode':g['execution']['exitCode'],'acceptanceCompleted':g['acceptanceResult']['completed'],'allDeclaredGroupsAttempted':True,'scope':groups}
        limits=['Original scoped UI test only; no all43/privateZIP/fullCDP/fullSpace/physical phone/touch/IME claim.','Kernel sandbox internals not independently inspected; actual browser bytes and absence of disabling flags verified.']
        if kind=='supplement':limits.append('108/3 is a failed attempt; downstream assertions of three failing groups were not reached. Source corrections/precondition fixes require a separate new execution receipt.')
    else:
        canonical=[json.loads(s[len('ACCEPTANCE_RESULT '):]) for s in log.read_text().splitlines() if s.startswith('ACCEPTANCE_RESULT ')];done=[s.split()[1] for s in log.read_text().splitlines() if s.startswith('SCENARIO_DONE ')]
        check('one canonical full 273/0 record matches every original individual assertion',len(canonical)==1 and canonical[0]['ok'] is True and canonical[0]['checks']==len(rows)==passed==273 and canonical[0]['failures']==failed==0 and g['acceptanceResult']['passed']==273 and g['acceptanceResult']['failed']==0)
        check('all ten original normal scenarios completed in exact order',done==SCENARIOS and g['acceptanceResult']['normalScenariosCompleted']==done,done)
        check('positive completed exact command exit0 and gate verified',g['acceptanceResult']['completed'] is True and g['probeVerified'] is True and g['execution']['exitCode']==g['gateExitCode']==0)
        check('actual frozen formal direct-row script bytes and full command match',run['fullCommand']==g['command'] and g['command'][1]==str(Path(b['root'])/'tests/room_outline_direct_rows_browser.js') and run['sourceSHA256']['harness']==b['sources']['tests/room_outline_direct_rows_browser.js']==provenance['executedProbeSHA256'] and provenance['sourceOverride'] is False)
        sourceMap={'fixture':'tests/room_outline_fixture.js','app':'geometry-web/app.js','workspace':'geometry-web/room-outline-workspace.js','extractor':'geometry-web/room-outline.js'}
        check('fixture and product sources match exact wrapper frozen source identities',all(run['sourceSHA256'][key]==b['sources'][relative] for key,relative in sourceMap.items()))
        def result(name,count=1):
            found=[r for r in rows if r['name']==name];return len(found)==count and all(r['ok'] is True for r in found)
        for name in NEGATIVE:check('original negative reached and passed exactly once: '+name,result(name))
        for name in SCENARIOS:
            for suffix in ['Confirm creates exact ordered oracle geometry','Undo exact original','Redo exact confirmed','Open preserves exact native ordered topology','Open preserves source bytes, page, transform and calibration','Open preserves exact confirmed receipt']:
                check('original normal retained endpoint/history/save-open '+name+': '+suffix,result(name+': '+suffix,2 if name=='pdf-notch' and suffix.startswith('Open ') else 1))
        cost=p['measurements'];check('six original same-start/end cost cases actually measured in exact protocol',[m['scenario'] for m in cost]==SCENARIOS[:6] and all(m['protocol']==run['protocol']=='room-direct-row-dimensions/1' for m in cost))
        costSummary=[]
        for i,m in enumerate(cost):
            name=m['scenario'];candidate=m['candidate'];manual=m['manual']
            check(name+': same actual native starting scene assertion',result(name+': manual comparison starts from identical native scene'))
            check(name+': same calibrated source/camera/disclosures/snap/review assertion',result(name+': comparison source, camera, snap, review and disclosures share the same start'))
            check(name+': stored full initial states actually identical',candidate['start']==manual['start'] and candidate['start']['review']=='unreviewed' and candidate['start']['snap'] is False)
            check(name+': exact same reviewed geometry independent endpoint',result(name+': Confirm creates exact ordered oracle geometry') and result(name+': manual comparison ends at exact same reviewed geometry'))
            check(name+': independently receipted exact direct-row vs manual action counts',type(candidate['actions']) is int and type(manual['actions']) is int and candidate['actions']==[12,14,16][i%3] and manual['actions']==[16,20,24][i%3])
            costSummary.append({'scenario':name,'candidate':candidate['actions'],'manual':manual['actions'],'protocol':m['protocol'],'sameStart':True,'sameReviewedEnd':True,'humanTimeMeasured':False})
        check('final native runtime/source/head/console health assertions were reached',all(result(name) for name in ['console/page errors','runtime remained fresh and unchanged throughout','HEAD and test source remained unchanged throughout']) and p['errors']==[])
        recorded={'passed':273,'failed':0,'exitCode':0,'acceptanceCompleted':True,'normalScenarios':done,'negativeAssertions':NEGATIVE,'costComparisons':costSummary}
        limits=['Original #54 ten normal/six negative/six comparisons direct-row protocol only; not all Geometry or full CDP/Space.','Original room harness accepts native JavaScript dialogs generically; this validation preserves that policy and does not retrofit exact-message matching.','The original legacy select/fill/Apply counts21/27/33 remain separate from direct-row12/14/16 and manual16/20/24; P79 is a separate protocol.','Automated elapsedMs includes settling and is not human operation time; no action-floor threshold or new snapping/multi-room policy is invented.','No Windows/physical touch/IME/native OS picker/golden/private ZIP visual acceptance claim.']
    archive=gate.parent/'executed-sources';archived=[]
    check('actual committed formal6efba test source exact and nooverride',run['scriptSHA256']=='6efba5412916a31df431c557a7893019f186bf8adc3fa15aa059098367e272d1' and provenance['sourceOverride'] is False)
    check('actual executed source manifest present', (archive/'manifest.json').is_file())
    if archive.exists():
        for name,digest in b['sources'].items():
            target=archive/name
            if target.exists():archived.append({'source':name,'path':str(target),'sha256':sha(target),'expected':digest})
        check('executed-source archive matches every before product source hash',len(archived)==len(b['sources']) and all(x['sha256']==x['expected'] for x in archived),{'entries':len(archived),'beforeSources':len(b['sources'])})
        executedArchive=archive/'executed-probe.cjs'
        if not executedArchive.exists():
            for candidate in archive.rglob('*'):
                if candidate.is_file() and sha(candidate)==provenance['executedProbeSHA256']:executedArchive=candidate;break
        check('actual executed-probe bytes separately archived under matching provenance',executedArchive.is_file() and sha(executedArchive)==provenance['executedProbeSHA256'],str(executedArchive))
    report={'schema':'geometry-9eb-existing-evidence-independent-supplementary-validation/1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceSHA':BASE,'dirty':'','readOnlyExistingEvidence':True,'browserExecuted':False,'nativeExecuted':False,'repoWritten':False,'command':sys.orig_argv,'validator':{'path':str(Path(__file__).resolve()),'sha256':sha(__file__)},'python':{'path':sys.executable,'resolved':str(Path(sys.executable).resolve()),'sha256':sha(sys.executable),'version':sys.version},'originalEvidence':[{'path':str(f),'sha256':sha(f)} for f in artifacts],'checks':checks,'ok':all(c['ok'] for c in checks),'recordedAcceptance':recorded,'limits':limits,'archiveSourceEntries':archived}
    output=DIR/('supplementary-validation-9eb-'+kind+'.json');assert not output.exists();output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(output),'checks':len(checks),'ok':report['ok'],'failedChecks':[c for c in checks if not c['ok']]},ensure_ascii=False));return report['ok']
assert sys.argv[1:]==['ui123'], 'This validator only checks the actually completed formal original six at clean9eb.'
sys.exit(0 if validate('ui123') else 1)
