from pathlib import Path
import argparse
import hashlib,json,subprocess,sys

ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser(description='Actual T/P and named oracle withdrawals; no Chromium receipt')
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
OUT=args.out.resolve()
OUT.mkdir(parents=True,exist_ok=False)
BASE='00c62a81c48bcdf45b004506ff8511000bc0c6f7'
PFILES=['tests/diagnostics/r03_preview_length_withdrawals.py','tests/diagnostics/r16_canvas_extension.cjs',
        'tests/native_sharding_mutation_check.py','tests/test_boundary_pair_browser_scope.js',
        'tests/test_canvas_shards.js','tests/test_unittest_runner.py',
        'tests/diagnostics/r03_preview_length_projection_mutations.py']
original={name:(ROOT/name).read_bytes() for name in PFILES}
command=['node','--test','--test-reporter=./tests/diagnostics/r03_preview_length_reporter.cjs','tests/test_r03_preview_length.js']
def run(label,expected,failures=None):
    done=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=60)
    (OUT/(label+'.stdout.jsonl')).write_bytes(done.stdout)
    (OUT/(label+'.stderr.log')).write_bytes(done.stderr)
    rows=[json.loads(line) for line in done.stdout.decode().splitlines()]
    summary=[row['data'] for row in rows if row['type']=='test:summary']
    actual={row['name']:row['error'] for row in rows if row['type']=='test:fail'}
    assert done.returncode==expected,(label,done.returncode,done.stderr)
    assert len(summary)==1 and summary[0]['counts']['tests']==18 and summary[0]['counts']['cancelled']==0 and summary[0]['counts']['skipped']==0 and summary[0]['counts']['todo']==0,(label,summary)
    assert not done.stderr,(label,done.stderr)
    assert set(actual)==set(failures or {}),(label,actual)
    for name,marker in (failures or {}).items():
        err=actual[name]
        assert err['name']=='AssertionError' and err['code']=='ERR_ASSERTION' and err['failureType']=='testCodeFailure',(label,err)
        assert err['message'].splitlines()[0].startswith(marker),(label,err)
    return {'label':label,'exit':done.returncode,'counts':summary[0]['counts'],'failed':actual,
            'stdout_sha256':hashlib.sha256(done.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(done.stderr).hexdigest()}

wrong={
 'R2054_WITHDRAWAL_JUDGE rejects a passed marker plus an unrelated AssertionError':'R2054_WITHDRAWAL_JUDGE_wrong-failure',
 'R2054_WITHDRAWAL_JUDGE rejects a skipped test':'R2054_WITHDRAWAL_JUDGE_skip',
 'R2054_WITHDRAWAL_JUDGE rejects cancellation':'R2054_WITHDRAWAL_JUDGE_cancel',
}
history={'R2054_HISTORICAL_CANVAS_VIEW validates the complete registry then keeps the unchanged historical scope':'Got unwanted exception: R2054_HISTORY_NO_PER_PR_EXCEPTION'}
native={'R2054_NATIVE_HISTORY rejects a fabricated new row with matching cost but no original receipt':'R2054_FAKE_COST_MUST_NOT_EXEMPT'}
ownership={'R2054_BROWSER_OWNERSHIP uses a new checked service per phase and never the caller URL':'R2054_BROWSER_OWNERSHIP'}
records=[]
try:
    for name in PFILES:
        (ROOT/name).write_bytes(subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT))
    records.append(run('T-only',1,{**wrong,**history,**native,**ownership}))
finally:
    for name,raw in original.items():(ROOT/name).write_bytes(raw)
records.append(run('T-plus-P',0))

def mutate(name,relative,before,after,expected):
    target=ROOT/relative;raw=target.read_bytes()
    assert raw.count(before)==1,(name,'exact anchor',raw.count(before))
    phases=[]
    try:
        phases.append(run(name+'.baseline',0))
        target.write_bytes(raw.replace(before,after,1))
        phases.append(run(name+'.withdrawn',1,expected))
    finally:
        target.write_bytes(raw)
        assert target.read_bytes()==raw
    phases.append(run(name+'.restored',0))
    assert [p['exit'] for p in phases]==[0,1,0]
    return {'name':name,'path':relative,'original_sha256':hashlib.sha256(raw).hexdigest(),'phases':phases}
withdrawals=[]
withdrawals.append(mutate('R2054_RESTORE_GLOBAL_TEXT_KILL','tests/diagnostics/r03_preview_length_withdrawals.py',
 b"                    row['node_result'] = judge_node(completed, phase, name)",
 b"                    if phase == 'withdrawn':\n                        assert 'AssertionError' in output + errors and marker in output + errors",
 wrong))
withdrawals.append(mutate('R2054_RESTORE_PER_PR_CANVAS_EXCEPTION','tests/test_canvas_shards.js',
 b'const touchInput = r16Extension.registeredBeforeTouch(registered);',
 b"const lengthInput = lengthExtension.project(golden, plan);\nconst touchInput = r16Extension.beforeTouch(lengthInput.golden, lengthInput.plan);",
 history))
# The historical-call probe resolves only the captured caller lines; the
# restored old helper binding is supplied by that probe as in the old file.
withdrawals.append(mutate('R2054_SKIP_ORIGINAL_NATIVE_RECEIPT','tests/test_unittest_runner.py',
 b"verified = native_registry.timing_profile(run_all.ROOT)['added']",
 b'verified = added',native))
withdrawals.append(mutate('R2054_OMIT_SERVICE_PID_PROOF','tests/diagnostics/r03_preview_length_withdrawals.py',
 b"runtime.get('pid') == process.pid and runtime.get('fresh') is True",
 b"runtime.get('fresh') is True",ownership))
result={'schema':'r03-preview-review-fix-verification/1','base':BASE,'command':command,'browserExecuted':False,
        'records':records,'withdrawals':withdrawals}
(OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'base':BASE,'T':records[0]['counts'],'P':records[1]['counts'],
                  'withdrawals':{w['name']:[p['exit'] for p in w['phases']] for w in withdrawals},'browserExecuted':False},indent=2))
