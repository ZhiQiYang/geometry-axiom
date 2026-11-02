"""Fixed-head pure checks after the permitted A -> E -> canvas merge."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

SOURCE=Path('/tmp/geometry-canvas-shards-20261102')
HEAD='e45670d9bb864dcf6b5a07fd4ccf11c188e54818'
OUT=Path(__file__).resolve().parent/('gates-'+HEAD)
OUT.mkdir(exist_ok=False)
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
def git(*args):return subprocess.check_output(['git',*args],cwd=SOURCE,text=True).strip()
assert git('rev-parse','HEAD')==HEAD and not git('status','--porcelain=v1')
commands=[
 ('canvas-node',['node','--test','--test-reporter=spec','tests/test_canvas_shards.js']),
 ('original-pure-cdp',['node','--test','--test-reporter=spec','tests/test_cdp_floor.js','tests/test_cdp_evaluation.js','tests/test_cdp_settle.js']),
 ('architecture-cli',[sys.executable,'-B','tests/architecture_contract.py','--root','.','--manifest','geometry-core/domain-decoupling/product-architecture.json']),
 ('architecture-unit',[sys.executable,'-B','tests/test_architecture_contract.py']),
 ('architecture-product',[sys.executable,'-B','tests/test_product_architecture.py']),
 ('current-plan',['node','tests/helpers/canvas_shards.js','plan']),
]
receipt={'head':HEAD,'tree':git('rev-parse','HEAD^{tree}'),'source':str(SOURCE),'commands':[],
 'environment':{'node':subprocess.check_output(['node','--version'],text=True).strip(),'python':sys.version,'platform':sys.platform,
                'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8'},
 'unchanged_python_control':{'rerun':False,'original_head':'6c7a7b1ece271f0f3e66fdbb361f55c49c8e7343','original_tests':12,
   'reason':'Both test_canvas_evidence.py and canvas_evidence.py are byte-identical to that already tested commit; old result is not relabeled as a new execution.'},
 'UNRUN':['actual canvas shards','same-source original full browser gate','real harness false assertion 0/1/0','native/build/full census','fresh mutation execution or official artifact verification'],
 'expected_and_ledger':'Preserved original source values; future final source adoption pending root.'}
for label,command in commands:
 stdout,stderr=OUT/(label+'.stdout'),OUT/(label+'.stderr')
 with stdout.open('wb') as output,stderr.open('wb') as errors:
  process=subprocess.run(command,cwd=SOURCE,env=env,stdout=output,stderr=errors,timeout=180)
 row={'label':label,'command':command,'cwd':str(SOURCE),'head':HEAD,'exit_code':process.returncode,
      'stdout':stdout.name,'stderr':stderr.name,'stdout_sha256':hashlib.sha256(stdout.read_bytes()).hexdigest(),
      'stderr_sha256':hashlib.sha256(stderr.read_bytes()).hexdigest()}
 receipt['commands'].append(row);(OUT/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
 assert process.returncode==0,(label,stderr.read_text(),stdout.read_text()[:1000])
 if label in ('canvas-node','original-pure-cdp'):
  raw=stdout.read_text();match=re.search(r'(?:^|\n)ℹ tests (\d+)\b',raw);assert match
  row['tests']=int(match[1]);assert re.search(r'(?:^|\n)ℹ fail 0\b',raw) and re.search(r'(?:^|\n)ℹ skipped 0\b',raw)
 elif label in ('architecture-unit','architecture-product'):
  raw=stderr.read_text();match=re.search(r'Ran (\d+) tests? in ',raw);assert match
  row['tests']=int(match[1]);assert '\nOK\n' in raw and not re.search(r'\bskipped=[1-9]\d*',raw)
 elif label=='architecture-cli':
  scan=json.loads(stdout.read_bytes());assert scan['ok'] is True and scan['diagnostics']==[]
  row.update(diagnostics=0,edges=len(scan['edges']),sources=len(scan['sources']))
 elif label=='current-plan':
  plan=json.loads(stdout.read_bytes());units=[x for x in plan['units'] if x['id']=='assembly-bay-repeat'];assert len(units)==1 and units[0]['owner']=='extensions' and units[0]['sections']==['R06']
  row['current_golden_sections']=len(plan['golden']['sections']);row['current_golden_assertions']=plan['golden']['total'];row['plan_sha256']=plan['sha256']
 print(label,'exit',process.returncode,'tests',row.get('tests',''))
assert git('rev-parse','HEAD')==HEAD and not git('status','--porcelain=v1')
receipt.update(source_clean_after=True,all_requested_affected_checks_passed=True)
(OUT/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(OUT/'receipt.json')
