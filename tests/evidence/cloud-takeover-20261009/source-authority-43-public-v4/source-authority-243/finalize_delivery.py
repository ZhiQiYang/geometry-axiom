#!/usr/bin/env python3
"""Register already completed scratch source/artifact commands and hashes."""
from pathlib import Path
import datetime, hashlib, json, subprocess, sys
HERE=Path(__file__).parent
ROOT=Path('<workspace-path>')
sha=lambda data:hashlib.sha256(data).hexdigest()
def file(path):
 p=Path(path);b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':sha(b)}
load=lambda path:json.loads(Path(path).read_text())
source=load(HERE/'source-preparation-receipt.json')
validation=load(HERE/'validation-result.json')
assert validation['passed']==56 and validation['failed']==0
prepareLog=file(HERE/'prepare-followup.execution.raw.log')
source['rawLog']=prepareLog
source['shellCommand']='python3 prepare_followup.py > prepare-followup.execution.raw.log 2>&1'
source['completedCommandExitObserved']=0
(HERE/'source-preparation-receipt.json').write_text(json.dumps(source,ensure_ascii=False,indent=2)+'\n')
pythonPath=Path(sys.executable).resolve()
executionFile={'path':str(pythonPath),'sha256':sha(pythonPath.read_bytes()),'version':sys.version}
commands=[
 {'purpose':'immutable full-SHA source read and scratch documentation preparation','argv':[sys.executable,str(HERE/'prepare_followup.py')],'shellCommand':source['shellCommand'],'cwd':str(HERE),'exitCode':0,'executionFile':executionFile,'sourceScript':file(HERE/'prepare_followup.py'),'rawLog':prepareLog},
 {'purpose':'source/artifact-only validation; not a product test','argv':[sys.executable,str(HERE/'validate_package.py')],'shellCommand':'python3 validate_package.py > validation.execution.raw.log 2>&1','cwd':str(HERE),'exitCode':0,'executionFile':executionFile,'sourceScript':file(HERE/'validate_package.py'),'rawLog':file(HERE/'validation.execution.raw.log'),'result':file(HERE/'validation-result.json'),'passed':56,'failed':0},
 {'purpose':'preserved first artifact-check attempt, with two checker bookkeeping errors corrected; not a product failure','argv':[sys.executable,str(HERE/'artifact-validation-first-attempt/validate_package.py')],'originalExecutionPath':str(HERE/'validate_package.py'),'cwd':str(HERE),'exitCode':1,'executionFile':executionFile,'sourceScript':file(HERE/'artifact-validation-first-attempt/validate_package.py'),'rawLog':file(HERE/'artifact-validation-first-attempt/validation.execution.raw.log'),'result':file(HERE/'artifact-validation-first-attempt/validation-result.json'),'passed':54,'failed':2,'corrections':['Validate actual token names only in current follow-up, retaining historical old names unchanged.','Count the four scope rows plus the original four preflight and three final checks:185/2=187.']}
]
artifacts=[file(HERE/name) for name in ['README.md','issue123-43-source-followup-243326.md','source-followup.json','source-preparation-receipt.json','validation-result.json']]
receipt={'schema':'geometry-issue123-43-source-followup-delivery/1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'frozenSourceSHA':source['requestedFullSourceSHA'],'observedHeadAtDelivery':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),'observedDirtyAtDelivery':subprocess.check_output(['git','status','--short'],cwd=ROOT).decode(),'sourceIdentity':'29 immutable git show full243 files, not a rebinding to later source','itemCount':43,'nativeDOMNamesChecked':True,'sourceAnchorsMissing':0,'historicalAuthoritiesPreserved':source['originalAuthorityUnchanged'],'originalAMapEdited':False,'commands':commands,'artifacts':artifacts,'sourcePreparationReceipt':file(HERE/'source-preparation-receipt.json'),'originalEvidenceRead':source['evidenceSourcesRead'],'bounded243Evidence':{'supplement':'185/2 exit1 acceptance:false, all four groups attempted; plan16/0 and BOM44/0 desktop/390 complete, row32/1 blocked downstream and390, S2 desktop84/0 plus mobile2/1 setup only','fullSpace':'228/0 exit0 completed:true, explicit two timber omissions, oldfont/titleWidth oracle only'},'sourcePending':['X2/B1 title vertical bounds; root planned future nowrap/hidden/ellipsis, not implemented or accepted at frozen243'],'unknown':['Original0b37 title diagnostic JSON/path unreceived by this subtask; measurements are parent-reported.','Private ZIP and pixel targets, unadopted removals and policy remain decisions/unknown.','Same-version formal #54 full ten/six-negative/six-cost, latest formal six, fullCDP and item-wide all43 acceptance are not established by this package.'],'browserExecuted':False,'nativeExecuted':False,'serviceExecuted':False,'repoWritten':False,'formalTestsWritten':False,'gitWritten':False,'all43Accepted':False,'publicCopyNeedsRootReview':True,'generator':{'script':file(Path(__file__)),'argv':[sys.executable,str(Path(__file__))],'cwd':str(HERE),'executionFile':executionFile}}
(HERE/'delivery-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'prepared':True,'document':str(HERE/'issue123-43-source-followup-243326.md'),'documentSHA256':sha((HERE/'issue123-43-source-followup-243326.md').read_bytes()),'items':43,'sourceFiles':29,'artifactChecks':{'passed':56,'failed':0},'newBrowserExecuted':False},ensure_ascii=False))
