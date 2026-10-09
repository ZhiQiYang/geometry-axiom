#!/usr/bin/env python3
"""Read-only source/artifact checks, with scratch output only; no product execution."""
from pathlib import Path
import collections, datetime, hashlib, json, subprocess, sys
HERE=Path(__file__).parent
ROOT=Path('<workspace-path>')
BASE='243326b512896ace70e068f62c8f3d6397f6000d'
sha=lambda data:hashlib.sha256(data).hexdigest()
load=lambda p:json.loads(p.read_text())
receipt=load(HERE/'source-preparation-receipt.json')
record=load(HERE/'source-followup.json')
report=(HERE/'issue123-43-source-followup-243326.md').read_bytes()
checks=[]
def check(name,value,detail=None):
 checks.append({'name':name,'ok':bool(value),**({'detail':detail} if detail is not None else {})})
check('complete frozen source SHA exact',record['sourceSHA']==receipt['requestedFullSourceSHA']==BASE)
check('original preparation checkout clean before and after',receipt['observedHeadBefore']==receipt['observedHeadAfter']==BASE and receipt['dirtyBefore']==receipt['dirtyAfter']=='')
ids=[x['id'] for x in record['items']]
expected=['X'+str(n) for n in range(1,8)]+['B'+str(n) for n in range(1,9)]+['C'+str(n) for n in range(1,8)]+['D'+str(n) for n in range(1,5)]+['E'+str(n) for n in range(1,7)]+['G'+str(n) for n in range(1,5)]+['F'+str(n) for n in range(1,8)]
check('all original43 unique IDs in original order',ids==expected and len(ids)==len(set(ids))==43)
check('portable S0-S6 original issue sentences exact',set(record['portableOriginalPhases'])=={'S'+str(n) for n in range(7)} and all(v in load(HERE/'authority/issue123-original.json')['body'] for v in record['portableOriginalPhases'].values()))
for source in receipt['sources']:
 retained=Path(source['retainedPath']).read_bytes()
 original=subprocess.check_output(['git','show',BASE+':'+source['path']],cwd=ROOT)
 check('immutable source exact: '+source['path'],retained==original and sha(retained)==source['sha256'] and len(retained)==source['bytes'])
for authority in receipt['authority']:
 check('historical authority unchanged: '+Path(authority['path']).name,sha(Path(authority['path']).read_bytes())==sha(Path(authority['retainedPath']).read_bytes())==authority['sha256'])
check('all43 original640 raw table lines preserved',all(x['historical640']['rawLine'].encode() in report for x in record['items']))
check('historical A-map retained without repo rewrite',receipt['historicalAMapChanged'] is False)
refs=[r for item in record['items'] for r in item['sourceReferences']]
check('all source references real exact anchors at full frozen SHA',all('line' in r and r['fullSourceSHA']==BASE and ('/blob/'+BASE+'/') in r['url'] and r['needle'] in (HERE/'source'/r['path']).read_text() and (HERE/'source'/r['path']).read_text()[:(HERE/'source'/r['path']).read_text().find(r['needle'])].count('\n')+1==r['line'] for r in refs),{'references':len(refs),'missing':len(receipt['unknownSourceAnchors'])})
check('actual native-compatible DOM/function/token names used',all(s.encode() in report for s in ['spacePlanMetrics','.space-plan-strip','syncV3PlaneControls','--beam','workSurf','v3ToolbarSurf','igBoundarySection','gridObjectDelete']) and '--type-beam'.encode() not in report)
check('title vertical pending retained X2/B1',all(next(x for x in record['items'] if x['id']==id)['sourceStatus']=='SOURCE_PENDING' for id in ['X2','B1']) and record['sourcePending']['rawDiagnosticOriginalReceivedByThisSubtask'] is False)
check('private/unadopted/policy unknown not newly specified',all('UNKNOWN' in next(x for x in record['items'] if x['id']==id)['sourceStatus'] for id in ['B8','C5','C6','C7','G1','G2']) and all(x['privateZIPCompared'] is False for x in record['items']))
check('no all43 or native-contract-change claim',record['all43ProductAccepted'] is False and record['nativeContractsChanged'] is False and all(x['browserAcceptanceAt243']['entireItemAccepted'] is False for x in record['items']))
for evidence in receipt['evidenceSourcesRead']:
 check('retained existing evidence exact: '+Path(evidence['retainedPath']).name,sha(Path(evidence['path']).read_bytes())==sha(Path(evidence['retainedPath']).read_bytes())==evidence['sha256'])
supp=record['limited243ReadEvidence']
check('actual four-scope failed acceptance preserved',supp['originalPassed']==185 and supp['originalFailed']==2 and supp['exitCode']==1 and supp['acceptanceCompleted'] is False and supp['allDeclaredGroupsAttempted'] is True)
check('four-scope group census preserves actual187',sum(x['passed'] for x in supp['groupCensus'].values())==180 and sum(x['failed'] for x in supp['groupCensus'].values())==2)
check('row new downstream and390 not reached',supp['groupCensus']['row-blur']['mobile390NotReached'] is True and 'not reached' in supp['rowLimit'])
check('S2 desktop/mobile boundary exact',supp['groupCensus']['s2']['desktopPassed']==84 and supp['groupCensus']['s2']['mobile390PassedSetupChecks']==2 and supp['groupCensus']['s2']['mobile390DownstreamNotReached'] is True)
space=record['fullSpace243']
check('full Space original228/0complete exit0 exact',space['sourceSHA']==BASE and space['passed']==228 and space['failed']==0 and space['completed'] is True and space['exitCode']==0 and space['canonicalLogCount']==1)
check('full Space explicit omitted timber scope retained',space['scope']['mode']=='full-space-suite' and space['scope']['filters']==[] and space['scope']['omitted']==['timber-material','timber-source-guards'])
check('font19 and title-width only never vertical proof',space['fontLayout']=={'expected':19,'passed':19,'failed':0,'completed':True} and space['doesNotVerifyTitleVerticalBounds'] is True)
check('subtask performs no product execution or writes',all(receipt[key] is False for key in ['browserExecuted','nativeExecuted','serviceExecuted','repoWrites','formalTestWrites','gitWrites','newHeadBrowserPassClaimed']))
check('report and structured artifact hashes exact',sha(report)==receipt['reportSHA256'] and sha((HERE/'source-followup.json').read_bytes())==receipt['structuredSHA256'])
result={'schema':'geometry-issue123-43-source-artifact-validation/1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'frozenSourceSHA':BASE,'observedHeadAtValidation':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),'observedDirtyAtValidation':subprocess.check_output(['git','status','--short'],cwd=ROOT).decode(),'checks':checks,'passed':sum(x['ok'] for x in checks),'failed':sum(not x['ok'] for x in checks),'artifactValidationOnly':True,'browserExecuted':False,'nativeExecuted':False,'repoWritten':False}
(HERE/'validation-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False))
if result['failed']:
 print(json.dumps([x for x in checks if not x['ok']],ensure_ascii=False));sys.exit(1)
