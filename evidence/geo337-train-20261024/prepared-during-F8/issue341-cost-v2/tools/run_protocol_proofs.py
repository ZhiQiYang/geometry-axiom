from pathlib import Path
import hashlib,importlib.util,json,os,sys
P=Path(__file__).resolve().parent;O=P/'protocol-original-capture';assert not O.exists()
cap=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py');assert hashlib.sha256(cap.read_bytes()).hexdigest()=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
s=importlib.util.spec_from_file_location('capture',cap);c=importlib.util.module_from_spec(s);s.loader.exec_module(c);env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONOPTIMIZE',None);r=c.Recorder(O,env,'75a1e93811a52b69385cbdaf6a09d773ed9052ad');results=[]
for guard in ('source','count','identity','numeric','duplicates'):
 steps=[]
 for phase in ('fixed','withdrawn','restored'):
  script=P/('test_metadata_guards.py'if guard=='source'else'test_output_guards.py');args=[sys.executable,'-B',str(script)]
  if phase=='withdrawn':args+=['--withdraw-source-guard']if guard=='source'else['--withdraw',guard]
  row,out,err=r.run(args,cwd=P,check=False,timeout=20,source_variant='pure metadata/protocol; no C or performance')
  expected=1 if phase=='withdrawn'else 0
  assert row['actual_process_returncode']==expected and not err,(guard,phase,row,out,err)
  body=json.loads(out);assert body['exit']==expected
  steps.append({'phase':phase,'exit':expected,'failures':body['failures'],'command':row['directory']})
 results.append({'guard':guard,'phases':steps})
c.dump(O/'RESULT.json',{'exit':0,'source_sha':'75a1e93811a52b69385cbdaf6a09d773ed9052ad','groups':results,'C_executed':False,'product_mutation_proof':False});print(json.dumps({'exit':0,'groups':5,'phase_exits':[[p['exit']for p in g['phases']]for g in results]}))
