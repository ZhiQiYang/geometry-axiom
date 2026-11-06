"""Pure metadata/protocol controls only; never imports NativeBuild or compiles C."""
from pathlib import Path
import argparse,copy,json,sys
P=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser();p.add_argument('--withdraw-source-guard',action='store_true');a=p.parse_args()
 source=(P/'run_costs.py').read_text()
 if a.withdraw_source_guard:
  old="need(d['source_sha']==SOURCE,'exact F8 source identity')"
  assert source.count(old)==1;source=source.replace(old,'pass # isolated metadata guard withdrawal')
 namespace={'__name__':'_cost_metadata_only','__file__':str(P/'run_costs.py')}
 exec(compile(source,str(P/'run_costs.py'),'exec'),namespace)
 make=namespace['plan'];validate=namespace['validate_plan'];parse=namespace['inspect_output'];checks=[]
 def check(name,fn,should_raise):
  raised=False
  try:fn()
  except Exception:raised=True
  checks.append(dict(name=name,passed=raised==should_raise))
 check('baseline-complete-plan',lambda:validate(make()),False)
 edits=[('wrong-source','source_sha','0'*40),('missing-withdrawn','variants',('fixed','restored')),('missing-positive','positive_cases',namespace['POSITIVE'][:-1]),('missing-fallback','cases',make()['cases'][:-4]),('discarded-sample','scored_triplets',6),('changed-runtime-timeout','run_timeout',21),('invented-threshold','performance_thresholds_added',True),('false-historical-completion','Sc493_whole_withdrawal_executed',True)]
 for name,key,value in edits:
  d=copy.deepcopy(make());d[key]=value;check(name,lambda d=d:validate(d),True)
 raw=b'MODE diagnostic=false performance_sample=true\nMETA case=none n=8 admitted=16 capacity=2432 fallback=0 face_size=64\nTIME cpu_ns=1 wall_ns=2 cpu_resolution_ns=1 wall_resolution_ns=1\n'+b'FACE 1 0 42 -1 0 0 0 0 27\n'*16
 check('timing-protocol',lambda:parse(raw,False,'none',8),False)
 check('missing-full-face-stream',lambda:parse(raw.replace(b'FACE 1 0 42 -1 0 0 0 0 27\n',b''),False,'none',8),True)
 check('diagnostic-not-performance',lambda:parse(raw,True,'none',8),True)
 check('duplicate-time-record',lambda:parse(raw+b'TIME cpu_ns=1 wall_ns=2 cpu_resolution_ns=1 wall_resolution_ns=1\n',False,'none',8),True)
 check('invalid-clock-number',lambda:parse(raw.replace(b'cpu_ns=1',b'cpu_ns=-1'),False,'none',8),True)
 failures=[x['name']for x in checks if not x['passed']]
 result=dict(exit=1 if failures else 0,checks=len(checks),failures=failures,withdraw_source_guard=a.withdraw_source_guard,C_executed=False,product_mutation_proof=False,details=checks)
 print(json.dumps(result,ensure_ascii=False));return result['exit']
if __name__=='__main__':raise SystemExit(main())
