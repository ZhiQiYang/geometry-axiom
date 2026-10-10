from pathlib import Path
import ast,datetime,hashlib,json,sys
U=Path('<workspace-path>')
OUT=U/'source43-inverse-execution-source-index';assert not OUT.exists();OUT.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rows=[]
config=[
 ('original-base-failed-before-receipt','review_source43_public_v3_inverse.py','source43-v3-independent-inverse/review.raw.log',None,1,'TypeError at review-log hash; tool cad899 exit1; no receipt fabricated.'),
 ('direct-r2-executed-437-pass-4-fail','review_source43_public_v3_inverse_r2.py','source43-v3-independent-inverse-r2/review.raw.log','source43-v3-independent-inverse-r2/receipt.json',1,'Tool365d12 actualexit1; direct Python script, no helper dynamically executes this reviewer.'),
 ('diagnostic-caller-executed','diagnose_source43_inverse_v3.py',None,'source43-v3-independent-inverse-diagnostic.json',0,'Tool1c7799 actualexit0; caller selects only functions/constants/import AST nodes from immutable r2. sourceSHA256 in original diagnostic names the r2 helper, not the diagnostic caller.'),
 ('direct-v4-executed-445-pass-0-fail','review_source43_public_v4_inverse.py','source43-v4-independent-inverse/review.raw.log','source43-v4-independent-inverse/receipt.json',0,'Toolea9fee actualexit0; direct Python script, no dynamic external helper.')
]
for role,name,raw,receipt,exitcode,note in config:
 p=U/name;copy=OUT/'source-bytes'/name;copy.parent.mkdir(exist_ok=True);copy.write_bytes(p.read_bytes());tree=ast.parse(p.read_bytes())
 imports=[]
 for node in ast.walk(tree):
  if isinstance(node,ast.Import):imports.extend(x.name for x in node.names)
  if isinstance(node,ast.ImportFrom):imports.append(node.module)
 row={'role':role,'actualExecutedSource':str(p),'sourceSHA256':sha(p),'sourceBytes':p.stat().st_size,'immutableCopy':str(copy),'immutableCopySHA256':sha(copy),'directImports':sorted(set(imports)),'nonStdlibImportDependencies':[],'actualToolReportedExitCode':exitcode,'toolProvenance':note,'originalRaw':None,'originalReceipt':None}
 if raw:
  f=U/raw;row['originalRaw']={'path':str(f),'sha256':sha(f),'bytes':f.stat().st_size}
 if receipt:
  f=U/receipt;d=json.loads(f.read_bytes());row['originalReceipt']={'path':str(f),'sha256':sha(f),'bytes':f.stat().st_size}
  row['actualCommandRecorded']=d.get('actualCommand',d.get('command'))
  row['originalRecordedPython']=d.get('actualPython');row['originalRecordedPythonSHA256']=d.get('actualPythonSHA256')
  row['originalRecordedSourceSHA256']=d.get('scriptSHA256',d.get('sourceSHA256'))
  if role!='diagnostic-caller-executed':assert d['scriptSHA256']==sha(p)
 if role=='diagnostic-caller-executed':
  helper=U/'review_source43_public_v3_inverse_r2.py';row['dynamicPureFunctionHelper']={'path':str(helper),'sha256':sha(helper),'role':'Original r2 AST functions/constants/imports only; no reviewer top-level or product run','statementTypes':['Import','ImportFrom','FunctionDef','limited Assign']}
  assert json.loads((U/receipt).read_bytes())['sourceSHA256']==sha(helper)
 rows.append(row)
index={'schema':'geometry-source43-inverse-execution-source-closure/1','preparedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actor':'/root/ui_tail_contract','actualIndexCommand':sys.orig_argv,'actualIndexPython':str(Path('/proc/self/exe').resolve()),'actualIndexPythonSHA256':sha('/proc/self/exe'),'indexMakerSourceSHA256':sha(__file__),'roles':rows,'originalsModified':False,'productRerun':False,'limits':['Only source bytes/raw/receipt role index; no product/browser/native execution or original receipt changes.','Diagnostic original live Python exe/hash was not captured and remains unknown; current index Python does not fill that historic gap.','The original failed437/4 scope and v4 accepted445/0 scope stay separate; counts are publication metadata checks, not product assertions.']}
p=OUT/'index.json';p.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'index':str(p),'sha256':sha(p),'roles':len(rows),'sourceCopies':4})); 

