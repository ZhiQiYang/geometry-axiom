"""Record fixed-commit pure checks. Never launches Chrome or native tests."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

SOURCE=Path('/tmp/geometry-canvas-shards-20261102')
HEAD='6c7a7b1ece271f0f3e66fdbb361f55c49c8e7343'
OUT=Path(__file__).resolve().parent/('commit-'+HEAD)
OUT.mkdir(exist_ok=False)
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
git=lambda *args:subprocess.check_output(['git',*args],cwd=SOURCE,text=True).strip()
assert git('rev-parse','HEAD')==HEAD and not git('status','--porcelain=v1')
commands=[
 ('new-node',['node','--test','--test-reporter=spec','tests/test_canvas_shards.js'],0),
 ('new-python',[sys.executable,'-B','tests/test_canvas_evidence.py'],0),
 ('original-pure-cdp',['node','--test','--test-reporter=spec','tests/test_cdp_floor.js','tests/test_cdp_evaluation.js','tests/test_cdp_settle.js'],0),
 ('plan',['node','tests/helpers/canvas_shards.js','plan'],0),
 ('architecture',[sys.executable,'-B','tests/architecture_contract.py','--root','.','--manifest','geometry-core/domain-decoupling/product-architecture.json'],1),
]
receipt={'source':str(SOURCE),'head':HEAD,'tree':git('rev-parse','HEAD^{tree}'),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'commands':[],'environment':{'python':sys.version,'node':subprocess.check_output(['node','--version'],text=True).strip(),'platform':sys.platform,
 'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8'},'browser_shards':'UNRUN','original_full_new_source':'UNRUN',
 'upstream_merges':'PENDING root-approved PR363 then PR344 then this canvas commit',
 'pending_registry':['PY_NEEDS test_canvas_evidence []','NODE_PURE_TEST_FILES node:canvas_shards tests/test_canvas_shards.js'],
 'observed_new_test_counts':{'node':19,'python':12},'original_pure_cdp_count':32}
for label,command,expected_exit in commands:
 stdout,stderr=OUT/(label+'.stdout'),OUT/(label+'.stderr')
 with stdout.open('wb') as output,stderr.open('wb') as errors:
  process=subprocess.run(command,cwd=SOURCE,env=env,stdout=output,stderr=errors,timeout=120)
 row={'label':label,'command':command,'cwd':str(SOURCE),'head':HEAD,'exit_code':process.returncode,'expected_exit':expected_exit,
      'stdout':stdout.name,'stderr':stderr.name,'stdout_sha256':hashlib.sha256(stdout.read_bytes()).hexdigest(),
      'stderr_sha256':hashlib.sha256(stderr.read_bytes()).hexdigest()}
 assert process.returncode==expected_exit,(label,stderr.read_text())
 if label=='architecture':
  scan=json.loads(stdout.read_bytes());assert [item['code'] for item in scan['diagnostics']]==['EXCLUSION_DIGEST']
  assert scan['diagnostics'][0]['path']=='geometry-web/cdp_test.js'
  row['expected_unresolved_diagnostic']=scan['diagnostics']
 receipt['commands'].append(row)
 print(label,'exit',process.returncode)
assert git('rev-parse','HEAD')==HEAD and not git('status','--porcelain=v1')
receipt.update(source_clean_after=True,completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pure_checks_passed=True)
(OUT/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(OUT/'receipt.json')
