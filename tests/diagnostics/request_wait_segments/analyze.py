"""Correlate clocks by diagnostic IDs; never subtract browser/server clocks."""
import argparse,collections,hashlib,json,pathlib
p=argparse.ArgumentParser();p.add_argument('directory',type=pathlib.Path);args=p.parse_args();root=args.directory
def span(rows,start,end):
 a=[r['mono_ns'] for r in rows if r['event']==start];b=[r['mono_ns'] for r in rows if r['event']==end]
 return (max(b)-min(a))/1e6 if a and b else None
def duration(rows,event,field):
 a=[r[field] for r in rows if r['event']==event and field in r];return sum(a) if a else None
summaries=[]
for folder in sorted(root.iterdir()):
 if not folder.is_dir():continue
 result=json.loads((folder/'result.json').read_text());assert not result.get('harness_error'),result
 assert result.get('drain',{}).get('complete'),folder
 assert result['native_before_cleanup']=={'native_returncode':None,'bridge_failure':None},folder
 assert result['server_exit']=={'code':0,'signal':None},folder
 for tool,digest in result['tool_hashes'].items():
  assert hashlib.sha256((folder/(tool+'.executed')).read_bytes()).hexdigest()==digest,(folder,tool)
 events=[json.loads(line) for line in (folder/'server-events.jsonl').read_text().splitlines()]
 browser=json.loads((folder/'browser-events.json').read_text());requests=collections.defaultdict(list)
 for event in events:requests[event.get('request')].append(event)
 fetched={r['id']:r for r in browser if r['event']=='fetch_begin'}
 headers={r['id']:r for r in browser if r['event']=='fetch_headers'}
 failures=[r for r in browser if r['event']=='fetch_error']
 api=[r for r in browser if r['event']=='api_end'];blocked=[];all_requests=[]
 for call in api:
  if call['phase_before']=='error' and call['result'].get('transport') and not any(r.get('call')==call['id'] for r in fetched.values()):
   blocked.append({'call':call['id'],'command':call['command'],'error':call['result'].get('error'),'fetches':0})
 for identifier,request in fetched.items():
  rows=requests[identifier];failure=next((r for r in failures if r['id']==identifier),None);head=headers.get(identifier)
  end=failure or head
  fresh=duration(rows,'fresh_exit','elapsed_ms');runtime_wait=duration(rows,'runtime_lock_acquired','wait_ms')
  row={'id':identifier,'call':request.get('call'),'command':request.get('command'),'receipt':request.get('receipt'),'browser_fetch_ms':end['ms']-request['ms'] if end else None,'fetch_error':failure,'stages':{
   'runtime_lock_wait_ms':runtime_wait,'fresh_total_ms':fresh,'fresh_body_approx_ms':fresh-runtime_wait if fresh is not None and runtime_wait is not None else None,
   'receipt_lock_wait_ms':duration(rows,'receipt_lock_acquired','wait_ms'),'bridge_lock_wait_ms':duration(rows,'bridge_lock_acquired','wait_ms'),
   'stdin_write_ms':duration(rows,'stdin_write_end','elapsed_ms'),'stdin_flush_ms':duration(rows,'stdin_flush_end','elapsed_ms'),
   'response_queue_wait_ms':duration(rows,'response_queue_end','elapsed_ms'),'http_write_ms':duration(rows,'http_write_end','elapsed_ms'),'http_total_ms':span(rows,'http_enter','http_exit')},
   'native_responses':[r for r in rows if r['event']=='native_response_arrived' and r['bytes']>0],
   'http_write_errors':[r for r in rows if r['event']=='http_write_error'],'browser_headers_received':head is not None,'server_events':len(rows),'absent_stage_means':'not entered, not measured zero'}
  assert rows,identifier
  all_requests.append(row)
 timed_out=[r for r in all_requests if r['fetch_error'] and r['fetch_error']['name'] in ['TimeoutError','AbortError']]
 late_signals=[r for r in browser if r['event']=='fetch_abort' and r['id'] in headers and headers[r['id']]['ms']<r['ms']]
 console=json.loads((folder/'console.json').read_text());errors=[r for r in console if r['type'] in ['error','pageerror']]
 summary={'case':folder.name,'p7_pass':result.get('p7_pass'),'phase':result['state']['phase'],'error':result['state']['error'],'wall_ms':result['wall_ms'],'server_exit':result['server_exit'],
  'timeouts':timed_out,'blocked_before_fetch':blocked,'requests':all_requests,'late_signal_for_already_received_headers':len(late_signals),'console_errors':errors,
  'source_identity':result['runtime'],'tool_hashes':result['tool_hashes'],'native_pid':result['ready']['native_pid'],'binary_sha256':result['ready']['binary_sha256']}
 (folder/'analysis.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');summaries.append(summary)
by={s['case']:s for s in summaries}
for name in ['baseline','renderer-cpu20','bridge3','receipt18']:assert by[name]['p7_pass'],name
for name,stage in [('bridge18','bridge_lock_wait_ms'),('native18','response_queue_wait_ms')]:
 s=by[name];assert not s['p7_pass'] and s['phase']=='error' and '15 秒' in s['error']
 assert any(t['stages'][stage]>17000 for t in s['timeouts']),name
 for t in s['timeouts']:
  assert t['stages']['response_queue_wait_ms'] is not None and t['native_responses'],(name,t['id'],'missing real late native response')
 assert all(any(b['command']==cmd for b in s['blocked_before_fetch']) for cmd in ['dump','boundary 1','references 1'])
assert any(r['stages']['runtime_lock_wait_ms'] is not None and r['stages']['runtime_lock_wait_ms']>17000 for r in by['runtime18']['requests'])
assert any(r['stages']['receipt_lock_wait_ms'] is not None and r['stages']['receipt_lock_wait_ms']>17000 for r in by['receipt18']['requests'])
assert len({s['binary_sha256'] for s in summaries})==1
(root/'analysis.json').write_text(json.dumps(summaries,ensure_ascii=False,indent=2)+'\n')
for s in summaries:
 print(s['case'],'P7',s['p7_pass'],'phase',s['phase'],'real rejected fetches',len(s['timeouts']),'guarded calls',len(s['blocked_before_fetch']))
 for t in s['timeouts']:print(' ',t['id'],t['command'] or t['receipt'],round(t['browser_fetch_ms'],3),{k:round(v,3) if v is not None else None for k,v in t['stages'].items()})
