"""Prove K2a M01/M03 in Chromium by replacing only the served workspace JS."""
from pathlib import Path
import json
import os
import subprocess
import tempfile
import hashlib

root = Path(__file__).resolve().parents[1]
out = Path(tempfile.gettempdir()) / 'k2aa-browser-mutants-review'
out.mkdir(exist_ok=True)
command = ['node', str(root / 'tests/k2a_drafts_browser.cjs')]
if os.environ.get('GEOMETRY_ISOLATED_SERVICE') != '1' or not os.environ.get('GEOMETRY_TEST_URL'):
    raise SystemExit('Require GEOMETRY_ISOLATED_SERVICE=1 and an explicitly isolated GEOMETRY_TEST_URL')
baseline = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=180)
(out / 'baseline.log').write_text(baseline.stdout + baseline.stderr)
assert baseline.returncode == 0, baseline.stdout + baseline.stderr
source = (root / 'geometry-web/grid-system-workspace.js').read_text()
cases = [
    ('M01-replacement-dialog', 'const collection=ReferenceWorkspace.readGridDrafts(),saved=collection.drafts;',
     'const collection=ReferenceWorkspace.readGridDrafts(),saved=collection.drafts;if(saved.length)window.confirm("取代舊草稿？");'),
    ('M03-fresh-continuation-id', 'draftId:restored?.draftId||crypto.randomUUID()', 'draftId:crypto.randomUUID()'),
    ('M15-cancel-updates-pin', "if(!window.confirm('重新取得基底；之後仍須預覽與確認。", "if(window.confirm('重新取得基底；之後仍須預覽與確認。"),
]
cases += [
    ('M13-small-touch-target','min-height:44px;width:100%','min-height:1px;width:100%','k2a_drafts_browser.cjs','M13 chooser touch targets remain at least 44px'),
    ('M13-overflow','width:min(480px,calc(100vw - 24px))','width:2000px;max-width:none','k2a_drafts_browser.cjs','M13 chooser fits viewport'),
    ('M15-rule-raw-redraw', 's.ruleDraft=next.ruleDraft?copy(next.ruleDraft):null;', '', 'k2a_rule_repin_browser.cjs', 'accepted repin redraw preserves latest rule raw'),
    ('M15-rule-comparison', "if(s.mode==='source'&&s.ruleDraft){", 'if(false){', 'k2a_rule_repin_browser.cjs', 'two-way comparison includes latest rule raw and current rule'),
    ('M15-rule-literal-comparison', "if(/^igRule[UV]$/.test(id))return number>=1n&&number<=65n&&number===BigInt(other);", "if(/^igRule[UV]$/.test(id))return value===actual;", 'k2a_rule_repin_browser.cjs', 'M15 parsed-equivalent rule divisions are omitted'),
]
messages={'M01-replacement-dialog':'coexisting drafts never ask to replace another draft','M03-fresh-continuation-id':'M03 continuation retains original draftId','M15-cancel-updates-pin':'M15 cancellation preserves complete draft'}
results = []
for case in cases:
    name,before,after=case[:3]
    command=['node',str(root/'tests'/(case[3] if len(case)>3 else 'k2a_drafts_browser.cjs'))]
    expected=case[4] if len(case)>3 else messages[name]
    baseline=subprocess.run(command,cwd=root,capture_output=True,text=True,timeout=180)
    (out/(name+'-baseline.log')).write_text(baseline.stdout+baseline.stderr)
    assert baseline.returncode==0,baseline.stdout+baseline.stderr
    assert source.count(before) == 1
    mutant = out / (name + '.js')
    mutant.write_text(source.replace(before, after))
    build=subprocess.run(['node','--check',str(mutant)],capture_output=True,text=True)
    (out/(name+'-build.log')).write_text(build.stdout+build.stderr)
    assert build.returncode==0,build.stdout+build.stderr
    env = dict(os.environ, GEOMETRY_GRID_WORKSPACE_SOURCE=str(mutant))
    run = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True, timeout=180)
    (out / (name + '.log')).write_text(run.stdout + run.stderr)
    restored=subprocess.run(command,cwd=root,capture_output=True,text=True,timeout=180)
    (out/(name+'-restored.log')).write_text(restored.stdout+restored.stderr)
    assert restored.returncode==0,restored.stdout+restored.stderr
    result = {'id': name, 'command':command,'expected_assertion':expected,'exit': run.returncode, 'detected': run.returncode != 0 and 'AssertionError' in run.stdout + run.stderr and expected in run.stdout+run.stderr,'restored_exit':restored.returncode,'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'judge_sha256':hashlib.sha256(Path(command[1]).read_bytes()).hexdigest(),'build_exit':build.returncode,'raw_logs':{suffix:hashlib.sha256((out/(name+suffix+'.log')).read_bytes()).hexdigest() for suffix in ['-baseline','-build','','-restored']}}
    results.append(result)
    print(json.dumps(result), flush=True)
(out / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
assert all(result['detected'] for result in results), results
