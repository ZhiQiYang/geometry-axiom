from pathlib import Path
import argparse,json,sys
from binding_guards import validate_counts,validate_q38_source,EXPECTED_EIGHT
p=argparse.ArgumentParser();p.add_argument('--registry',type=Path,required=True);p.add_argument('--q38',type=Path,required=True);a=p.parse_args()
try:
 count=validate_counts(json.loads(a.registry.read_text())['suites'],EXPECTED_EIGHT)
 ids=validate_q38_source(a.q38.read_bytes())
 print(json.dumps({'metadata_only':True,'formal_executed':False,'registered_eight_count':count,'q38_ids':ids,'exit_code':0}));raise SystemExit(0)
except RuntimeError as e:
 print(json.dumps({'metadata_only':True,'formal_executed':False,'error':str(e),'exit_code':1}));raise SystemExit(1)
