"""Run M1 counterexamples against old/new analyzers without altering raw evidence.

Each case changes a copy of the archived observations. The old analyzer must
accept it, the new analyzer must reject it for the named semantic reason, and
both must accept the unchanged seven cohorts. No product/browser is executed.
"""
import argparse
import copy
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tarfile
import time

parser=argparse.ArgumentParser()
parser.add_argument('archive',type=pathlib.Path)
parser.add_argument('directory',type=pathlib.Path)
args=parser.parse_args()
out=args.directory.resolve()
out.mkdir(parents=True,exist_ok=False)
repo=pathlib.Path(__file__).resolve().parents[3]
new=pathlib.Path(__file__).with_name('analyze.py')
old=out/'analyze-before-M1.py'
old.write_bytes(subprocess.check_output(['git','show','940d25f1a26703461c2cf28b36aaf457e58150fd:tests/diagnostics/request_wait_segments/analyze.py'],cwd=repo))
with tarfile.open(args.archive) as archive:
 members=[m for m in archive.getmembers() if m.name.startswith('cohorts-drained/')]
 assert members and all(m.isdir() or m.isfile() for m in members)
 archive.extractall(out/'source',members=members,filter='data')
source=out/'source/cohorts-drained'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(folder,name):return json.loads((folder/name).read_text())
def save(folder,name,value):
 (folder/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def events(folder):return [json.loads(line) for line in (folder/'server-events.jsonl').read_text().splitlines()]
def save_events(folder,rows):
 (folder/'server-events.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in rows))
def request_ids(folder):
 browser=load(folder,'browser-events.json')
 mutation=next(r for r in browser if r['event']=='fetch_begin' and r.get('command','').startswith('line surface '))
 receipt=next(r for r in browser if r['event']=='fetch_begin' and r.get('receipt'))
 return mutation,receipt
def mutate(folder,kind):
 if kind=='late-native':
  rows=events(folder);donor=events(source/'receipt18')
  original,_=request_ids(folder);sample,_=request_ids(source/'receipt18')
  for row in donor:
   if row.get('request')==sample['id'] and (row['event'].startswith(('stdin_','response_queue_')) or row['event']=='native_response_arrived' and row['bytes']>0):
    row=copy.deepcopy(row);row['request']=original['id'];rows.append(row)
  save_events(folder,rows)
 elif kind in ['wrong-receipt','not-cancelled','missing-timeout','missing-guard','unexpected-timeout']:
  rows=load(folder,'browser-events.json')
  if kind=='wrong-receipt':
   next(r for r in rows if r['event']=='fetch_begin' and r.get('receipt'))['receipt']='different-request-id'
  elif kind=='not-cancelled':
   mutation,_=request_ids(folder)
   next(r for r in rows if r['event']=='api_end' and r['id']==mutation['call'])['result']={'ok':True}
  elif kind=='missing-timeout':
   row=next(r for r in rows if r['event']=='fetch_error' and r['id']=='fetch-28');rows.remove(row)
  elif kind=='missing-guard':
   row=next(r for r in rows if r['event']=='api_end' and r['command'].startswith('line boundary '));rows.remove(row)
  else:
   row=next(r for r in rows if r['event']=='fetch_begin')
   rows.append({'event':'fetch_error','id':row['id'],'call':row.get('call'),'name':'TimeoutError','message':'counterexample','ms':row['ms']+15000})
  save(folder,'browser-events.json',rows)
 elif kind=='not-ready':
  result=load(folder,'result.json');result['state']['phase']='error';save(folder,'result.json',result)
 elif kind in ['repeat-write','repeat-reply','wrong-server-receipt']:
  rows=events(folder);mutation,receipt=request_ids(folder)
  if kind=='wrong-server-receipt':
   next(r for r in rows if r['event']=='request_body' and r['request']==receipt['id'])['receipt']='different-request-id'
  else:
   event='stdin_write_begin' if kind=='repeat-write' else 'native_response_arrived'
   row=next(r for r in rows if r['event']==event and r.get('request')==mutation['id'] and (event!='native_response_arrived' or r['bytes']>0))
   rows.append(copy.deepcopy(row))
  save_events(folder,rows)
 else:raise ValueError(kind)

def execute(script,folder,dest):
 start=time.monotonic_ns()
 process=subprocess.Popen([sys.executable,str(script),str(folder)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 stdout,stderr=process.communicate()
 record={'argv':[sys.executable,str(script),str(folder)],'pid':process.pid,'exit':process.returncode,'elapsed_ms':(time.monotonic_ns()-start)/1e6,'analyzer_sha256':sha(script)}
 dest.mkdir(parents=True,exist_ok=True)
 (dest/'stdout').write_bytes(stdout);(dest/'stderr').write_bytes(stderr)
 (dest/'result.json').write_text(json.dumps(record,indent=2)+'\n')
 return record,stderr.decode()

cases=[('unchanged',None,None,None),
 ('runtime-late-native','runtime18','late-native','cancelled-before-native'),
 ('runtime-wrong-receipt','runtime18','wrong-receipt','same-receipt-id'),
 ('runtime-wrong-server-receipt','runtime18','wrong-server-receipt','server-receipt-identity'),
 ('runtime-not-ready','runtime18','not-ready','receipt-ready'),
 ('runtime-not-cancelled','runtime18','not-cancelled','receipt-result-body'),
 ('receipt-repeat-write','receipt18','repeat-write','exactly-once-native'),
 ('receipt-repeat-reply','receipt18','repeat-reply','exactly-once-native'),
 ('receipt-wrong-receipt','receipt18','wrong-receipt','same-receipt-id'),
 ('receipt-not-ready','receipt18','not-ready','receipt-ready'),
 ('bridge-missing-timeout','bridge18','missing-timeout','exact-timeout-blocked-counts'),
 ('native-missing-guard','native18','missing-guard','exact-timeout-blocked-counts'),
 ('baseline-unexpected-timeout','baseline','unexpected-timeout','exact-timeout-blocked-counts')]
records=[]
for name,case,kind,reason in cases:
 folder=out/'work'/name;shutil.copytree(source,folder)
 changed={}
 if case:
  before={f.name:sha(f) for f in (folder/case).iterdir() if f.is_file()}
  mutate(folder/case,kind)
  inputs=out/'cases'/name/'inputs';inputs.mkdir(parents=True)
  for file in (folder/case).iterdir():
   if file.is_file() and sha(file)!=before[file.name]:
    changed[file.name]={'before_sha256':before[file.name],'after_sha256':sha(file)}
    shutil.copyfile(file,inputs/file.name)
  assert changed,name
 old_result,_=execute(old,folder,out/'cases'/name/'before')
 new_result,error=execute(new,folder,out/'cases'/name/'after')
 record={'case':name,'cohort':case,'mutation':kind,'expected_rejection':reason,'changed_inputs':changed,'before':old_result,'after':new_result}
 records.append(record)
 assert old_result['exit']==0,(name,'old analyzer should accept this counterexample')
 assert new_result['exit']==(1 if case else 0),(name,error)
 if case:assert reason in error,(name,error)
 print(name,'before',old_result['exit'],'after',new_result['exit'],'reason',reason,flush=True)
 shutil.rmtree(folder)
summary={'archive_sha256':sha(args.archive),'before_analyzer_sha256':sha(old),'after_analyzer_sha256':sha(new),'unchanged_accepted':True,'counterexamples_rejected':len(cases)-1,'results':records}
(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
shutil.copyfile(new,out/'analyze.executed.py')
