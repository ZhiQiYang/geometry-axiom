#!/usr/bin/env python3
"""Derive receipts from an extracted UI209 raw archive. No product execution.

python3 tests/diagnostics/ui209_summarize.py /tmp/ui209-raw > summary.json
"""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

raw=Path(sys.argv[1])
def read(p): return json.loads(p.read_text())
def rows(p): return [json.loads(s) for s in p.read_text().splitlines()]
def sha(b): return hashlib.sha256(b).hexdigest()
def delta(a,b,field='browserMs',divisor=1): return round((b[field]-a[field])/divisor,6) if a and b else None
result={'historicalWSLRootCause':'unknown','fullRunner':False,'runs':{},'originals':{}}
for p in sorted((raw/'runs').iterdir()):
    r=read(p/'result.json');identity=read(p/'identity.json');a=rows(p/'browser.jsonl');s=rows(p/'server.jsonl')
    commands=read(p/'commands.json');command=next(c for c in commands if c['argv'][0]=='node' and 'ui209_browser.cjs' in c['argv'][1])
    assert r['exit']==identity['browserExit']==command['exit']
    assert read(p/'sources-before.json')==read(p/'sources-after.json')
    assert identity['sourcesUnchanged'] and identity['bridgeSha256']==identity['bridgeSha256After']
    target=next((x for x in a if x['event']=='fetch.begin' and x.get('hold')),None)
    fetch=[] if target is None else [x for x in a if x.get('rid')==target['rid']]
    server=[] if target is None else [x for x in s if x.get('rid')==target['rid']]
    def first(events,name): return next((x for x in events if x['event']==name),None)
    def sd(start,end): return delta(first(server,start),first(server,end),'mono_ns',1e6)
    rejected=first(fetch,'fetch.reject');aborted=first(fetch,'fetch.signal.abort')
    query_id=target['call']['id'] if target else None
    awaits=[x for x in a if x['event'].startswith('open.') and x.get('id')==query_id] if query_id else []
    begin=first(awaits,'open.begin');end=first(awaits,'open.end')
    red=r.get('firstRed');comparison=r.get('comparison',{})
    final=r.get('final') or {}
    viewport=final.get('viewport')
    entry={'sourceRef':identity['sourceRef'],'exit':r['exit'],'seconds':command['seconds'],
      'originalChecks':r['originalChecks'],'originalFailures':r['originalFailures'],
      'harnessError':r.get('harnessError'),'exceptions':r['exceptions'],'firstRed':red['message'] if red else None,
      'firstRedConnection':red['ui']['connection']['phase'] if red else None,
      'firstRedBindingHidden':red['ui']['bindingForm']['hidden'] if red and red['ui']['bindingForm'] else None,
      'firstRedViewport':red['ui']['viewport'] if red else None,'finalViewport':viewport,
      'postScreenshotViewport':r.get('postScreenshotViewport'),
      'recovery':r['recovery'],'prefixCompleted':r.get('prefixCompleted',False),
      'dumpSame':comparison.get('dumpSame'),'historyBefore':comparison.get('before',{}).get('history',{}).get('undo'),
      'historyAfter':comparison.get('after',{}).get('history'),
      'sourcesUnchanged':identity['sourcesUnchanged'],'bridgeSha256':identity['bridgeSha256'],
      'ownedServerExit':identity['serverExit'],
      'ownsEntryFalseCount':sum(x['event']=='open.owns' and not x['ok'] for x in a),
      'openGenerations':[{'id':x['id'],'options':x['options']} for x in a if x['event']=='open.begin']}
    if target:
        entry['target']={'requestId':target['rid'],'call':target['call'],
          'serverBeforeQueueMs':sd('server.request.begin','bridge.queue.enter'),
          'queueMs':sd('bridge.queue.enter','bridge.lock.acquired'),
          'injectedHoldMs':sd('injection.hold.begin','injection.hold.end'),
          'nativeResponseMs':sd('bridge.stdin.write','bridge.response.delivered'),
          'fetchRejectMs':delta(target,rejected),'signalAbortMs':delta(target,aborted),
          'abortReason':aborted.get('reason') if aborted else None,
          'abortWasAfterFetchSettled':aborted.get('settled') if aborted else None,
          'reject':{k:rejected.get(k) for k in ['name','message']} if rejected else None,
          'serverDisconnected':bool(first(server,'server.client.disconnected')),
          'openDurationMs':delta(begin,end),'openEndState':end.get('state') if end else None,
          'awaits':[{'label':x['label'],'event':x['event'],'browserMs':x['browserMs'],'ok':x.get('ok'),'error':x.get('error')} for x in awaits if x['event'].startswith('open.await.')],
          'returns':[{'line':x['line'],'value':x.get('value'),'state':x['state']} for x in awaits if x['event']=='open.return']}
    if 'replacement' in r:
        entry['replacement']={'nodeReplaced':r['replacement']['nodeReplaced'],'before':r['replacement']['before']['newBinding'],'after':r['replacement']['after']['newBinding']}
        entry['wheel']=[{'attempt':x['attempt'],'position':x['position']} for x in a if x['event']=='recovery.wheel.measure']
    result['runs'][p.name]=entry
for pr,expected in [(195,'a8dfa45bebb1aad075b585325df323ee80390ed2d9aa5f214947efc22e20ddfe'),(189,'3b8be9cc3961f58c7324d9076944f08a63b5c88cd971864014a54b1677a44993')]:
    p=raw/'originals'/str(pr);b=(p/'public.zip').read_bytes();assert sha(b)==expected
    with zipfile.ZipFile(p/'public.zip') as z:
        m=read(p/'manifest.json')['selected'] if pr==195 else json.loads(z.read('manifest.json'))
        selected=m if pr==195 else [{'member':k,**v} for k,v in m.items()]
        for item in selected:
            v=z.read(item['member']);assert len(v)==item['bytes'] and sha(v)==item['sha256']
    result['originals'][str(pr)]={'sha256':expected,'bytes':len(b),'selectedPaths':len(selected),'uniquePayloads':len(set(x['member'] for x in selected))}
    if pr==195:
        digest=sha((p/'manifest.json').read_bytes());assert digest=='5f5aff29f74bcb09a66a7059cb69f46c1baa4f16816b7feeca6403dc272cfebb'
        result['originals'][str(pr)]['manifestSha256']=digest
print(json.dumps(result,ensure_ascii=False,indent=2))
