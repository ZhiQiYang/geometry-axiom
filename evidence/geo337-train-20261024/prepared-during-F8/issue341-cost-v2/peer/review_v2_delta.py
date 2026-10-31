from pathlib import Path
import json,hashlib,datetime
P=Path('/tmp/geo341-cost-preparation-v2-20261025');B=Path('/tmp/geo341-cost-preparation-20261025');O=Path('/tmp/geo341-cost-tool-peer-20261025')
checks=[]
def h(b):return hashlib.sha256(b).hexdigest()
def check(n,v):checks.append({'name':n,'passed':bool(v)})
check('submitted v2 PINS',h((P/'PINS.json').read_bytes())=='008b50d645074777e38c2d2b61074d510a28e7069319b9afc79d20e2966cbeab')
for n,d in json.loads((P/'PINS.json').read_bytes()).items():check('v2 pin '+n,h((P/n).read_bytes())==d)
for name in ['fixed.c','withdrawn.c','restored.c','fixed-diagnostic.c','withdrawn-diagnostic.c','restored-diagnostic.c','cost_harness.c','INSTRUMENTATION.json','WITHDRAWAL.json','COMMAND_PLAN.json','prepare_instrumentation.py']:
 check('no C/corpus/instrumentation change '+name,(P/name).read_bytes()==(B/name).read_bytes())
old=(B/'run_costs.py').read_text();new=(P/'run_costs.py').read_text();oldparse=old[old.index('def inspect_output'):old.index('\ndef plan')];newparse=new[new.index('def inspect_output'):new.index('\ndef plan')]
normalized=new.replace(newparse,oldparse).replace('import argparse,datetime,fcntl,hashlib,importlib.util,json,os,re,resource','import argparse,datetime,fcntl,hashlib,importlib.util,json,os,resource').replace('inspect_output(stdout,True,case,n)','inspect_output(stdout,True)').replace('inspect_output(stdout,False,case,n)','inspect_output(stdout,False)')
check('driver delta only parser/re import/two actual caller arguments',normalized==old)
check('both actual callers supply requested identities',new.count('inspect_output(stdout,True,case,n)')==1 and new.count('inspect_output(stdout,False,case,n)')==1)
check('PLAN exact v2 entry','python3 -B /tmp/geo341-cost-preparation-v2-20261025/run_costs.py --owner 'in(P/'PLAN.md').read_text())
check('PLAN preserves scope','不宣稱 #341 B1 已解除'in(P/'PLAN.md').read_text())
proof=json.loads((P/'protocol-original-capture/RESULT.json').read_bytes());check('five exact protocol groups',[x['guard']for x in proof['groups']]==['source','count','identity','numeric','duplicates'])
for g in proof['groups']:
 check('true group exits '+g['guard'],[x['exit']for x in g['phases']]==[0,1,0])
 for x in g['phases']:
  d=Path(x['command']);row=json.loads((d/'result.json').read_bytes());raw=(d/'stdout.bin').read_bytes();err=(d/'stderr.bin').read_bytes();body=json.loads(raw)
  label=g['guard']+' '+x['phase'];expected=1 if x['phase']=='withdrawn' else 0
  check('true process exit '+label,row['actual_process_returncode']==expected)
  check('stdout pin '+label,h(raw)==row['stdout_sha256'])
  check('stderr pin and empty '+label,h(err)==row['stderr_sha256'] and err==b'')
  check('source fixed '+label,row['source_sha']=='75a1e93811a52b69385cbdaf6a09d773ed9052ad')
  check('declared result matches raw '+label,body['exit']==expected and body['failures']==x['failures'])
  check('no product/performance claim '+label,body['C_executed'] is False and body['product_mutation_proof'] is False)
  check('known suite count '+label,body['checks']==(14 if g['guard']=='source' else 45))
  if x['phase']!='withdrawn':check('fixed/restored all cases good '+label,not body['failures'])
# Independently exercise exactly the original peer counterexample, not producer-generated positive output.
raw=(O/'TRUNCATED_FACE.synthetic.stdout').read_bytes();anchor="need(len(fields['FACE'])==expected_faces,'complete expected FACE row count')";check('one surgical count guard',new.count(anchor)==1)
for phase,s,expected_reject in [('fixed',new,True),('withdrawn',new.replace(anchor,'pass # peer isolated count guard withdrawal'),False),('restored',new,True)]:
 ns={'__name__':'_peer_readonly_protocol','__file__':str(P/'run_costs.py')};exec(compile(s,str(P/'run_costs.py'),'exec'),ns)
 rejected=False;message=None
 try:ns['inspect_output'](raw,False,'none',8)
 except Exception as e:rejected=True;message=str(e)
 check('original counterexample '+phase,rejected==expected_reject)
 if expected_reject:check('specific count rejection '+phase,message=='complete expected FACE row count')
for dname in ['metadata-proof','metadata-original-capture']:
 for a in (B/dname).rglob('*'):
  if a.is_file():check('historical proof exact '+str(a.relative_to(B)),(P/a.relative_to(B)).read_bytes()==a.read_bytes())
failed=[x for x in checks if not x['passed']]
report={'schema':'geo341-cost-v2-adversarial-delta/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha':'75a1e93811a52b69385cbdaf6a09d773ed9052ad','subject':str(P),'pins_sha256':h((P/'PINS.json').read_bytes()),'checks':len(checks),'failed_checks':failed,'checks_performed':checks,'exit':int(bool(failed)),'passed':not failed,'resolved_finding':'TRUNCATED_FACE_FINDING.json; the original one-row none/N8 counterexample is now rejected by exact row count','original_review':str(O/'INITIAL_REVIEW.json'),'original_review_sha256':h((O/'INITIAL_REVIEW.json').read_bytes()),'writer_exit_scope':'INITIAL_REVIEW verdict was 1 while its writer completed0; INITIAL_EXIT_SCOPE.json retains this distinction','reviewer_correction':'An interim message mistakenly treated the v1 PLAN command as v2. Fresh v2 PLAN line50 is correct and subject remained unchanged; that documentation finding is withdrawn.','scope':'Permission to schedule this pinned external F8 fallback collector only after root exclusive lease and actual capacity admission; not performance acceptance.','limits':['C compilation, eight semantic cases, 14-input work/CPU/wall measurements remain UNRUN.','No product/compiler/performance/Chrome commands were executed by this reviewer.','Historical Sc493 whole-withdrawal B1 remains separate and unexecuted.','Current F8 full123 and live source/cache were untouched.','Protocol proof uses synthetic complete rows; it is not an independent geometric oracle. Original C assertions and exact cross-variant FACE comparison remain.']}
(O/'V2_REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:report[k]for k in ['checks','failed_checks','exit','passed']},ensure_ascii=False));raise SystemExit(report['exit'])
