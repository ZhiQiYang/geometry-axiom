#!/usr/bin/env python3
"""Read saved traces only; no browser or native process is started."""
import hashlib,json
from pathlib import Path
import zipfile
RAW=Path('/workspace/closure-evidence/sr16-sr23-browser-r1')
OUT=Path(__file__).resolve().parent
result=[]
for width in ('1400','390'):
    http=[json.loads(line) for line in (RAW/width/'http-raw.jsonl').read_text().splitlines()]
    seen=set();history=[];single=[];downloads=[];inputs=[];trace_members=[]
    for path in sorted((RAW/width).glob('trace-*.zip')):
        with zipfile.ZipFile(path) as z:
            networks=[json.loads(line)['snapshot'] for line in z.read('trace.network').splitlines()]
            for row in networks:
                request=row['request'];response=row['response'];pd=request.get('postData',{})
                if pd.get('_sha1'):
                    body=z.read('resources/'+pd['_sha1']).decode()
                else:body=pd.get('text')
                response_sha=response.get('content',{}).get('_sha1')
                if response_sha:
                    response_body=z.read('resources/'+response_sha).decode()
                    seen.add((request['url'],request['method'],body,response['status'],response_body))
            events=[json.loads(line) for line in z.read('trace.trace').splitlines()]
            before={r['callId']:r for r in events if r.get('type')=='before'}
            for row in events:
                if row.get('type')=='after' and row.get('callId') in before:
                    start=before[row['callId']];expression=start.get('params',{}).get('expression','')
                    if '__srPins' in expression:
                        item={'trace':path.name,'callId':row['callId'],'expression':expression,
                              'result':row.get('result'),'error':row.get('error')}
                        if 'same=' in expression:history.append(item)
                        if 'h.undo.slice(0,-1)' in expression:single.append(item)
                    if start.get('method')=='setInputFiles':
                        inputs.append({'trace':path.name,'callId':row['callId'],'params':start.get('params'),'error':row.get('error')})
                if row.get('type')=='event' and row.get('method')=='download':downloads.append({'trace':path.name,'event':row})
            trace_members.append({'path':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                                 'traceMemberSha256':hashlib.sha256(z.read('trace.trace')).hexdigest(),
                                 'networkMemberSha256':hashlib.sha256(z.read('trace.network')).hexdigest()})
    unmatched=[]
    for i,row in enumerate(http,1):
        if (row['url'],row['method'],row['requestBody'],row['status'],row['responseBody']) not in seen:
            unmatched.append({'line':i,'path':row['url'],'method':row['method'],'phase':row['phase']})
    passed=(not unmatched and len(history)==3 and len(single)==1
        and all(r['result']=={'value':{'b':True}} and not r['error'] for r in history+single)
        and len(downloads)==1 and len(inputs)==1 and not inputs[0]['error'])
    result.append({'width':int(width),'passed':passed,'httpRows':len(http),'unmatchedHttpRows':unmatched,
                   'identityReferenceEqualityCalls':history,'singleTransactionCalls':single,
                   'downloadEvents':downloads,'setInputFiles':inputs,'privateTraces':trace_members})
report={'schema':'geometry-sr16-sr23-trace-independent-audit/1','passed':all(r['passed'] for r in result),
        'widths':result,'noProductExecution':True,'publication':'Trace ZIP files remain private; only hashes and bounded audit statements may publish.'}
(OUT/'trace-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'widths':[{'width':r['width'],'httpRows':r['httpRows'],'unmatched':r['unmatchedHttpRows'],'historyPins':len(r['identityReferenceEqualityCalls']),'single':len(r['singleTransactionCalls']),'downloads':len(r['downloadEvents']),'fileInputs':len(r['setInputFiles'])} for r in result]}))
