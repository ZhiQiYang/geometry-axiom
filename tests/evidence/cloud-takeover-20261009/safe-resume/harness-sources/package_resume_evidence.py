"""Preserve all original Resume receipts and their exact source/artifact bytes."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

BASE=Path(__file__).resolve().parent
HEAD='128afbec9240f36ae149682830e6b3a96ea02101'
ROOT=Path('<resume-repository-root>')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def copy_exact(source,destination):
    assert not destination.exists(),destination
    destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,destination)
    assert sha(source)==sha(destination)
    return {'originalPath':str(source),'copyPath':str(destination),'bytes':source.stat().st_size,'sha256':sha(source)}
def main():
    packet=BASE/'resume-128afbec-evidence-packet';assert not packet.exists();packet.mkdir()
    rows=[]
    for suffix in ['', '-r2','-r3','-r4']:
        source=BASE/f'after-resume-128afbec{suffix}-20261009'
        receipt=json.loads((source/'receipt.json').read_text());row={'attempt':suffix or 'r1','receipt':receipt,'files':[]}
        for file in sorted(source.rglob('*')):
            if file.is_file():row['files'].append(copy_exact(file,packet/source.name/file.relative_to(source)))
        temp=Path(f'<isolated-test-directory>')
        if temp.exists():
            for file in sorted(temp.rglob('*')):
                if file.is_file():row['files'].append(copy_exact(file,packet/source.name/'original-temp-artifacts'/file.relative_to(temp)))
        else:row['unexecutedArtifacts']='No artifacts: rejected before browser launch' if suffix=='-r3' else 'unknown: source unavailable'
        rows.append(row)
    receipt=rows[-1]['receipt'];assert receipt['before']['git']['head']==receipt['after']['git']['head']==HEAD
    assert receipt['probeCensus']['completed'] and receipt['probeCensus']['pass']==4 and receipt['probeCensus']['fail']==0
    assert receipt['execution']['exitCode']==0 and receipt['problems']==[]
    source_rows=[]
    for relative,digest in receipt['before']['sources'].items():
        raw=subprocess.check_output(['git','-C',str(ROOT),'show',HEAD+':'+relative]);assert hashlib.sha256(raw).hexdigest()==digest
        destination=packet/'executed-source-closure'/relative;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(raw)
        source_rows.append({'path':str(destination),'sha256':digest,'testedHead':HEAD})
    harness_rows=[]
    for file in [BASE/'run_resume_gate_identity.py',BASE/'run_resume_gate_identity_v2.py',BASE/'cdp_execution_identity.py',BASE/'resume_pause_browser.cjs',
                 *sorted((BASE/'originals').glob('resume-pause-browser-*.cjs')),
                 BASE/'resume-selector-correction.json',BASE/'resume-calibration-fixture-correction.json',
                 BASE/'resume-native-context-identity-correction.json',BASE/'resume-early-request-log-correction.json',Path(__file__)]:
        harness_rows.append(copy_exact(file,packet/'harness-sources'/file.name))
    script=BASE/'resume_pause_browser.cjs'
    assert sha(script)==receipt['before']['executionFiles'][str(script)]
    runner=BASE/'run_resume_gate_identity_v2.py';assert sha(runner)==receipt['before']['executionFiles'][str(runner)]
    result=json.loads((packet/'after-resume-128afbec-r4-20261009/original-temp-artifacts/results.json').read_text())
    review={'schema':'geometry-resume-executor-packet/1','checkedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'reviewerRole':'Same executor byte consistency review, not an independent actor','testedHead':HEAD,'dirty':False,
        'validScope':{'cases':4,'pass':4,'fail':0,'completed':True,'exitCode':0,'assertions':56,
            'perCase':[{'name':row['name'],'assertions':len(row['assertions']),'pass':sum(a['passed'] for a in row['assertions'])} for row in result]},
        'history':'r1 hidden return-selector and r2 inconsistent calibration fixture failed before Pause/Resume; r3 identity preflight rejected expected retained native B. Original logs/receipts/bytes preserved, not summed.',
        'limitations':['Confirmed metadata calibration/draft setters are synthetic fixture preparation; no physical calibration, IME or device claim.',
                       'Four same-parent same-native-session explicit Pause/Resume lifecycles only; not abrupt reload, restart, cross-profile/origin recovery, old Undo transport or full CDP.',
                       'Unconfirmed transient tools are not promised restored.'],
        'attempts':rows,'executedSourceClosure':source_rows,'harnessSources':harness_rows}
    target=packet/'executor-review.json';target.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'packet':str(packet),'reviewSha256':sha(target),'validCases':4,'assertions':56,'sourceFiles':len(source_rows),'harnessFiles':len(harness_rows)}))
if __name__=='__main__':main()
