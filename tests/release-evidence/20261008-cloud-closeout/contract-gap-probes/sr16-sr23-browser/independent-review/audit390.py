"""Read retained evidence only; never import or execute product/probe code."""
import copy, datetime, hashlib, json, pathlib, zipfile
BASE=pathlib.Path('/workspace/closure-evidence/sr16-sr23-browser-r1')
P=BASE/'390'
OUT=pathlib.Path(__file__).parent/'390-independent.json'
def read(n):return json.loads((P/n).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def world(v):
    r=copy.deepcopy({k:v[k] for k in ('dump','objects','references','assembly-read')})
    for k in ('dump','assembly-read'):r[k].pop('revision',None)
    return r
def project(v):return {k:v['project'][k] for k in ('id','name','manifest','sources','models','assemblyDrafts','engineeringDrafts')}
checks=[]
def check(name,value):checks.append({'name':name,'passed':bool(value)})
http=[json.loads(s) for s in (P/'http-raw.jsonl').read_text().splitlines()]
traces={}
for name in ('trace-3.zip','trace-4.zip'):
    with zipfile.ZipFile(P/name) as z:
        traces[name]=[json.loads(s) for s in z.read('trace.trace').splitlines()]
def trace_calls(name, predicate):
    rows=traces[name];after={r['callId']:(i+1,r) for i,r in enumerate(rows) if r.get('type')=='after'}
    return [{'line':i+1,'before':r,'afterLine':after.get(r['callId'],(None,None))[0],'after':after.get(r['callId'],(None,None))[1]} for i,r in enumerate(rows) if r.get('type')=='before' and predicate(r)]
ident=read('authored-identities.json')
commands=[]
for i,r in enumerate(http):
    try:q=json.loads(r['requestBody']);cmd=q.get('cmd','')
    except (ValueError,TypeError,AttributeError):continue
    if cmd.startswith(('line guide 23 ','line guide 24 ','line place 103 ','line place 104 ','line preview grid-binding ','line preview grid-system ')):
        reply=json.loads(r['responseBody']);commands.append({'line':i+1,'at':r['at'],'phase':r['phase'],'cmd':cmd,'ok':reply.get('ok'),'previewToken':reply.get('preview',{}).get('token'),'previewValid':reply.get('preview',{}).get('valid')})
positions={key:next(r['line'] for r in commands if r['cmd'].startswith(key)) for key in ('line guide 23 ','line place 103 ','line preview grid-binding 2 ','line guide 24 ','line place 104 ')}
check('Face1 guide and direct timber succeed before second binding, then face2 references precede source edit',list(positions.values())==sorted(positions.values()) and all(r['ok'] for r in commands) and positions['line place 104 ']<next(r['line'] for r in commands if r['phase']=='SR16-invalid-source'))
one=read('face1-refs-authored.json');two=read('face2-refs-authored.json');before=read('before-source-edit.json');after=read('after-source-edit.json')
check('Face1 snapshot contains exactly binding1, guide23/timber103 and no later references', [b['id'] for b in one['objects']['gridBindings']]==[1] and any(g['id']==23 for g in one['references']['guides']) and not any(g['id']==24 for g in one['references']['guides']) and any(t['id']==103 for t in one['references']['timbers']) and not any(t['id']==104 for t in one['references']['timbers']))
check('Second snapshot contains both bindings and both references',set(b['id'] for b in two['objects']['gridBindings'])=={1,2} and {23,24}.issubset(g['id'] for g in two['references']['guides']) and {103,104}.issubset(t['id'] for t in two['references']['timbers']))
preview=read('sr16-native-preview.json')['preview'];ui=read('sr16-ui-preview.json')
check('SR16 only timber104 has the concrete span rejection; both bindings shown and Confirm disabled',preview['valid'] is False and len(preview['violations'])==1 and preview['violations'][0]['timber']==104 and preview['violations'][0]['clause']=='R6/I5/I6' and '沒有合法跨距' in preview['violations'][0]['actual'] and set(x['id'] for x in preview['gridBindings'])=={1,2} and set(ui['bindings'])=={1,2} and ui['confirmDisabled'] is True)
for left,right in [('sr16-before-preview.json','sr16-pending.json'),('sr16-before-preview.json','sr16-cancelled.json'),('sr23-before-preview.json','sr23-cancelled.json')]:
    a,b=read(left),read(right)
    check(left+' == '+right+' full native plus serialized history',all(a[k]==b[k] for k in ('dump','objects','references','assembly-read','history')))
pins=trace_calls('trace-3.zip',lambda r:r.get('method')=='evaluateExpression' and '__srPins.get(id)' in r.get('params',{}).get('expression',''))
check('Three original identity-preserving history evaluations and one single transaction evaluation returned true',len(pins)==4 and all(r['after']['result']=={'value':{'b':True}} for r in pins))
def decode(v):
    if 'o' in v:return {x['k']:decode(x['v']) for x in v['o']}
    if 'a' in v:return [decode(x) for x in v['a']]
    for key in ('s','n','b'): 
        if key in v:return v[key]
    return v
ui_trace=trace_calls('trace-3.zip',lambda r:r.get('method')=='evaluateExpression' and 'confirmDisabled:document' in r.get('params',{}).get('expression',''))
ui_values=[decode(x['after']['result']['value']) for x in ui_trace]
check('Original trace UI evaluations equal retained preview JSON, with disabled true then false then false',len(ui_values)==3 and ui_values==[read(f) for f in ('sr16-ui-preview.json','sr23-cancel-ui-preview.json','sr23-confirm-ui-preview.json')] and [x['confirmDisabled'] for x in ui_values]==[True,False,False])
check('Source edit serializes exactly pitch600/400 to900/600 and no other definition changes',before['dump']['text'].count('u repeat 0 600 v repeat 0 400')==1 and before['dump']['text'].replace('u repeat 0 600 v repeat 0 400','u repeat 0 900 v repeat 0 600')==after['dump']['text'])
movement=[]
for g,t,length in ((23,103,240),(24,104,540)):
    gs=[next(x for x in v['references']['guides'] if x['id']==g) for v in (before,after)]
    ts=[next(x for x in v['references']['timbers'] if x['id']==t) for v in (before,after)]
    check('Existing guide%d and timber%d move exactly with stable typed references'%(g,t),[x['off'] for x in gs]==[300,400] and gs[0]['expression']==gs[1]['expression'] and [x['geometry']['centerline'] for x in ts]==[400,500] and [x['geometry']['length'] for x in ts]==[length,length] and ts[0]['definition']==ts[1]['definition'])
    movement.append({'guide':g,'offsets':[x['off'] for x in gs],'timber':t,'centerlines':[x['geometry']['centerline'] for x in ts],'length':length})
for a,b in [('undone.json','before-source-edit.json'),('redone.json','after-source-edit.json'),('saved.json','before-save.json'),('project-reopened.json','saved.json'),('open-undone.json','fresh-profile-empty.json'),('open-redone.json','project-reopened.json')]:
    check(a+' == '+b+' complete World except transaction revision',world(read(a))==world(read(b)))
for a,b in [('saved.json','before-save.json'),('project-reopened.json','saved.json'),('open-undone.json','fresh-profile-empty.json'),('open-redone.json','project-reopened.json')]:check(a+' == '+b+' complete project contract',project(read(a))==project(read(b)))
for f in ('new-empty.json','fresh-profile-empty.json'):
    v=read(f);check(f+' genuinely empty',v['dump']['text']=='' and not v['canvasCards'] and all(not x for k,x in v['objects'].items() if k!='ok') and all(not v['references'][k] for k in ('guides','grids','timbers','specs','datums')) and all(not v['assembly-read']['state'][k] for k in ('rules','bindings','instances')) and all(not v['project'][k] for k in ('models','sources','engineeringDrafts','assemblyDrafts')) and v['project']['id']!=read('saved.json')['project']['id'])
with zipfile.ZipFile(P/'sr23-project.gcanvas') as z:
    check('Saved artifact World equals retained saved World; full manifest equals pre-save expected manifest',z.read('world.scene').decode()==read('saved.json')['dump']['text'] and json.loads(z.read('manifest.json'))==read('expected-archive-manifest.json')==read('archive-manifest.json'))
clicks=trace_calls('trace-3.zip',lambda r:r.get('method')=='click' and r.get('params',{}).get('selector') in ['#refGuideCreate','#tbPlace','#igSaveBinding','#igSaveSource','#btnSaveProject','#btnUndo','#btnRedo'])
check('Relevant UI trace clicks completed without force',len(clicks)>=13 and all(x['after'] is not None and not x['after'].get('error') and not x['before']['params'].get('force') for x in clicks))
download=[{'line':i+1,'event':r} for i,r in enumerate(traces['trace-3.zip']) if r.get('type')=='event' and r.get('method')=='download']
opening=trace_calls('trace-4.zip',lambda r:r.get('method')=='setInputFiles' or (r.get('method')=='click' and r.get('params',{}).get('selector')=='#btnOpenProject'))
check('Actual Save download and fresh-context Open chooser setInputFiles are retained',len(download)==1 and len(opening)==2 and opening[0]['before']['method']=='click' and opening[1]['before']['params']['localPaths']==[str(P/'sr23-project.gcanvas')] and all(x['after'] and not x['after'].get('error') for x in opening))
uploads=[{'line':i+1,**r} for i,r in enumerate(http) if '/upload' in r['url']]
check('Formal Open sends saved World to prepare then confirms token186 successfully',uploads[-2]['url'].endswith('/upload/prepare') and uploads[-2]['requestBody']==read('saved.json')['dump']['text'] and json.loads(uploads[-2]['responseBody'])['token']==186 and uploads[-1]['url'].endswith('/upload/confirm') and uploads[-1]['requestBody']=='186' and json.loads(uploads[-1]['responseBody'])['ok'] is True)
events=read('inputs-first-browser.json');reopened_events=read('inputs-reopened-browser.json')
check('Save/Open trusted input and chooser change retained',any(x['id']=='btnSaveProject' and x['type']=='click' and x['trusted'] for x in events) and any(x['id']=='btnOpenProject' and x['type']=='click' and x['trusted'] for x in reopened_events) and any(x['id']=='projectFile' and x['type']=='change' and x['trusted'] for x in reopened_events))
receipt=json.loads((BASE/'receipt.json').read_text())
report={'schema':'geometry-sr16-sr23-independent-raw-review/1','reviewer':'/root/remote_inventory/sanitizer_driver_review','reviewedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'390px only; retained raw and trace read-only, no product execution','head':receipt['expectedHead'],'scriptSha256':sha(BASE/'executed-probe.py'),'reportedExitCode':receipt['exitCode'],'checks':checks,'blockers':[x['name'] for x in checks if not x['passed']],'authoredIdentities':ident,'httpUiSequence':commands,'sr16Violation':preview['violations'],'historyPinTrace':pins,'sourceEditMovement':movement,'uiTraceClicks':[{'line':x['line'],'callId':x['before']['callId'],'selector':x['before']['params']['selector'],'afterLine':x['afterLine']} for x in clicks],'saveDownload':download,'openChooserTrace':opening,'uploadSequence':[{'line':x['line'],'at':x['at'],'url':x['url'],'status':x['status']} for x in uploads],'sourceHashes':{str(f.relative_to(BASE)):sha(f) for f in sorted(P.iterdir()) if f.is_file()},'limits':['Author-provided pass counts were not used to determine findings.','Boundary, placement and legal physical supports were explicit API prerequisites; source/rule/binding/guide/direct-rule timber operations were UI-authored.','Save uses an explicitly selected download fallback; this does not validate a native OS save picker.','The Open chooser is automated setInputFiles on the real product file input, followed by product prepare/confirm; no internal load call substitutes for it.','Trusted Chromium390 input is not physical-phone or IME acceptance.','Snapshots preserve serialized history; exact history entry/frame identity is corroborated by original browser evaluate return values in trace.','Successful World comparisons exclude only dump/assembly-read transaction revision; refusal/cancel comparisons retain every field.']}
report['uiPreviewTrace']=[{'callId':x['before']['callId'],'line':x['line'],'afterLine':x['afterLine'],'bindings':v['bindings'],'guides':v['guides'],'confirmDisabled':v['confirmDisabled'],'fullTextMatchesRetainedJson':True} for x,v in zip(ui_trace,ui_values)]
OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'blockers':report['blockers'],'receipt':str(OUT),'sha256':sha(OUT)}))
