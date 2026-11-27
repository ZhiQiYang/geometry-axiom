"""Execute the shipping withdrawal driver with controlled child outcomes.

The fake child is only an oracle adversary; these are not product/browser
withdrawals or timing receipts. It emits real reporter-shaped outcomes while
the parent source mutations and return-code decisions execute unmodified.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('case',choices=['wrong-failure','skip','cancel','valid'])
args=parser.parse_args()
source=ROOT/'tests/diagnostics/r03_preview_length_withdrawals.py'
with tempfile.TemporaryDirectory(prefix='r2054-judge-') as directory:
    root=Path(directory)
    for relative in ['tests/diagnostics/r03_preview_length_withdrawals.py',
                     'tests/test_r03_preview_length.js']:
        target=root/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/relative,target)
    (root/'geometry-web').mkdir()
    (root/'geometry-web/framing-template-workspace.css').write_text('.ft-workspace .ft-results [data-ft-length]{white-space:nowrap;overflow-wrap:normal;word-break:normal}\n')
    (root/'geometry-web/framing-template-workspace.js').write_text('<td data-ft-length>${m.length}</td>\n')
    subprocess.run(['git','init','-q',str(root)],check=True)
    subprocess.run(['git','-C',str(root),'-c','user.name=test','-c','user.email=test@example.invalid','commit','-q','--allow-empty','-m','fixture'],check=True)
    fake=root/'bin';fake.mkdir()
    child=fake/'child.py'
    child.write_text('''import json,os,pathlib,sys
r=pathlib.Path.cwd()
css=(r/'geometry-web/framing-template-workspace.css').read_text()
js=(r/'geometry-web/framing-template-workspace.js').read_text()
bad_css='.ft-workspace .ft-results [data-ft-length]{white-space:nowrap;overflow-wrap:normal;word-break:normal}' not in css
bad_cell='<td data-ft-length>${m.length}</td>' not in js
bad=bad_css or bad_cell
names=json.loads(os.environ['R2054_TEST_NAMES'])
failed={names[2]:'R03_PREVIEW_LENGTH_POLICY'} if bad_css else {names[0]:'R2054_LENGTH_SEMANTIC_CELL',names[1]:'R2054_LENGTH_REORDERED_SEMANTICS'} if bad_cell else {}
case=os.environ['R2054_CONTRACT_CASE']
if bad and case=='wrong-failure':failed={names[3]:'UNRELATED_ASSERTION'}
for name in names:
 err={'name':'AssertionError','code':'ERR_ASSERTION','failureType':'testCodeFailure','message':failed[name]} if name in failed else None
 print(json.dumps({'type':'test:fail' if err else 'test:pass','name':name,'nesting':0,'skip':bool(bad and case=='skip' and name==names[-1]),'todo':False,'error':err}))
print(json.dumps({'type':'test:summary','data':{'success':not bad,'counts':{'tests':len(names),'passed':len(names)-len(failed),'failed':len(failed),'cancelled':int(bad and case=='cancel'),'skipped':int(bad and case=='skip'),'todo':0}}}))
sys.exit(int(bad))
''')
    node=fake/('node.cmd' if os.name=='nt' else 'node')
    node.write_text(('@"'+sys.executable+'" "'+str(child)+'" %*\n') if os.name=='nt' else '#!'+sys.executable+'\nexec(compile(open('+repr(str(child))+').read(),'+repr(str(child))+',"exec"))\n')
    node.chmod(0o755)
    names=[]
    import re
    for match in re.finditer(r"^test\('([^']+)'",(ROOT/'tests/test_r03_preview_length.js').read_text(),re.M):names.append(match.group(1))
    env=dict(os.environ,PATH=str(fake)+os.pathsep+os.environ['PATH'],R2054_CONTRACT_CASE=args.case,R2054_TEST_NAMES=json.dumps(names))
    run=subprocess.run([sys.executable,'-B','tests/diagnostics/r03_preview_length_withdrawals.py','--out',str(root/'out')],cwd=root,env=env,capture_output=True,timeout=60)
    expected=0 if args.case=='valid' else 1
    assert run.returncode==expected, 'R2054_WITHDRAWAL_REJECTS_'+args.case.upper().replace('-','_')+': exit='+str(run.returncode)+'\n'+run.stdout.decode()+run.stderr.decode()
    if expected:
        assert 'R03_LENGTH_NODE_RESULT' in run.stderr.decode(), 'R2054_WITHDRAWAL_FAILS_AT_RESULT_JUDGE\n'+run.stderr.decode()
    print('R2054_JUDGE_CONTRACT '+args.case+' PASS')
