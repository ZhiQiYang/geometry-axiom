#!/usr/bin/env python3
"""Private SR16/SR23 probe. Preparation only until the sole browser owner executes.

API mutations seed only boundaries, placements and physical timber supports.
Source/rule/bindings/applied grids/guides/direct-rule-line timbers are authored
through existing controls: first face + its references, then the second face.
Both references precede source edits. No force clicks or test-driven retries.
"""
from __future__ import annotations
import argparse, copy, datetime, hashlib, importlib.metadata, importlib.util
import json, os, pathlib, re, signal, subprocess, sys, traceback, zipfile
from urllib.parse import urlsplit

sys.dont_write_bytecode=True
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def write(p,v): pathlib.Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def world(v):
    x=copy.deepcopy({k:v[k] for k in ('dump','objects','references','assembly-read')})
    for k in ('dump','assembly-read'): x[k].pop('revision',None)
    return x
def project(v): return {k:v['project'][k] for k in ('id','name','manifest','sources','models','assemblyDrafts','engineeringDrafts')}
def segments(value): return sorted(tuple(sorted(tuple(point) for point in segment)) for segment in value)
def expected_archive(snapshot):
    # Independent, bounded input-to-container contract. This is computed before
    # Save, never inferred from downloaded output. Native rule definitions need
    # /11; a retained typed grid draft /2 upgrades to /13 (project-store:170-177).
    m=copy.deepcopy(snapshot['project']['manifest']);scene=snapshot['dump']['text']
    assert {line for line in scene.splitlines() if line.startswith('requires ')}=={'requires grid-subdivision-rules/1'}
    required={'grid-subdivision-rules/1'};format_number=11
    for item in m.get('featureAttachments',{}).get('records',[]):
        assert item['kind']=='grid-draft' and item['value']['schema'] in ('grid-editor-draft/1','grid-editor-draft/2'),item
        required.add(item['value']['schema'])
        if item['value']['schema']=='grid-editor-draft/2':format_number=13
    assert not m.get('models') and not m.get('faceProjections') and not m.get('assemblyDrafts') and not m.get('engineeringDrafts')
    m.update(format=f'geometry-canvas/{format_number}',sceneHash=hashlib.sha256(scene.encode()).hexdigest(),requiredCapabilities=sorted(required),models=[],faceProjections=[])
    return m
def expect_lines(u,v):
    # Hand arithmetic: physical vertex(100,200) anchors cell(-2,1), fraction0.
    # Its bounds do not move when pitch changes; right/bottom change by U/V.
    return {('u',0):(100+u//3,[[[100+u//3,200],[100+u//3,200+v]]]),
            ('u',1):(100+2*u//3,[[[100+2*u//3,200],[100+2*u//3,200+v]]]),
            ('v',0):(200+v//2,[[[100,200+v//2],[100+u,200+v//2]]])}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=pathlib.Path,default=pathlib.Path('/workspace/geometry-axiom'))
    p.add_argument('--url',required=True);p.add_argument('--head',required=True)
    p.add_argument('--out',required=True,type=pathlib.Path)
    p.add_argument('--chrome',default='/usr/bin/chromium')
    p.add_argument('--bridge',type=pathlib.Path,default=pathlib.Path('/tmp/geometry-tests/bridge'))
    p.add_argument('--model-base',type=pathlib.Path,default=pathlib.Path('/tmp/geometry-tests/model-base'))
    p.add_argument('--width',type=int,choices=(1400,390),action='append')
    a=p.parse_args();root=a.root.resolve();out=a.out.resolve();widths=a.width or [1400,390]
    address=urlsplit(a.url)
    if address.scheme!='http' or address.hostname not in ('127.0.0.1','localhost') or address.port in (None,8765) or address.path!='/' or any((address.query,address.fragment,address.username,address.password)):p.error('Explicit isolated loopback HTTP URL required; port 8765 is reserved')
    if not re.fullmatch('[0-9a-f]{40}',a.head) or len(set(widths))!=len(widths):p.error('Full SHA and distinct widths required')
    if out.is_relative_to(root):p.error('Evidence must be outside checkout')
    out.mkdir(parents=True,exist_ok=False);(out/'executed-probe.py').write_bytes(pathlib.Path(__file__).read_bytes())
    receipt={'schema':'geometry-sr16-sr23-browser/1','started':now(),'argv':[sys.executable,*sys.argv],'cwd':str(pathlib.Path.cwd()),
             'scriptSha256':sha(__file__),'expectedHead':a.head,'sandbox':True,'cases':[],'exitCode':1,
             'limits':['Only API-authored boundary/placement/physical support prerequisites; all source/rule/binding/downstream-reference operations use existing UI.',
                       'Actual trusted Chromium input and download/file chooser; not physical phone, IME or native OS save picker.',
                       'World successful Undo/Redo/reopen comparisons exclude only top-level native transaction revision; cancellation compares full raw native responses.',
                       'Source pitch edit changes U600→900 and V400→600 together so guide u0 and direct timber v0 both move.',
                       'Fresh browser/profile after actual New; no service restart or full CDP rerun claim.']}
    browser=context=page=None;case_out=out;phase='identity';errors=[];network_errors=[];row=None;launch_count=0
    def signal_stop(*_):raise InterruptedError('Probe interrupted; owned browser cleanup required')
    signal.signal(signal.SIGTERM,signal_stop)
    spec=importlib.util.spec_from_file_location('sr_release',root/'tests/release_gate.py')
    release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)
    def identity(label):
        commands=[]
        for cmd in (['pwd'],['git','rev-parse','HEAD'],['git','rev-parse','HEAD^{tree}'],['git','rev-parse','origin/main'],['git','status','--porcelain=v1','--untracked-files=all'],['git','diff','--binary','HEAD']):
            r=subprocess.run(cmd,cwd=root,capture_output=True,text=True,timeout=20)
            commands.append({'command':cmd,'stdout':r.stdout,'stderr':r.stderr,'exitCode':r.returncode})
        write(out/(label+'-commands.json'),commands)
        assert all(r['exitCode']==0 for r in commands) and commands[1]['stdout'].strip()==a.head and commands[4]['stdout']==''
        env=dict(os.environ,GEOMETRY_TEST_BRIDGE=str(a.bridge.resolve()),GEOMETRY_BRIDGE=str(a.bridge.resolve()),GEOMETRY_MODEL_BASE=str(a.model_base.resolve()))
        value=release.snapshot(root,a.url,env);write(out/(label+'-identity.json'),value)
        assert not value['problems'] and value['git']['head']==a.head
        ps=subprocess.run(['ps','-eo','pid=,ppid='],capture_output=True,text=True,timeout=20)
        write(out/(label+'-processes.json'),{'command':ps.args,'stdout':ps.stdout,'stderr':ps.stderr,'exitCode':ps.returncode})
        assert ps.returncode==0
        children=[int(line.split()[0]) for line in ps.stdout.splitlines() if int(line.split()[1])==value['runtime']['pid']]
        live=[{'pid':pid,'executable':str(pathlib.Path('/proc',str(pid),'exe').resolve()),'sha256':sha(pathlib.Path('/proc',str(pid),'exe'))} for pid in children]
        write(out/(label+'-live-children.json'),live)
        assert len([x for x in live if x['executable']==str(a.bridge.resolve()) and x['sha256']==sha(a.bridge)])==1
        return value
    def ready():page.wait_for_function("connection.phase==='ready'&&!ReferenceWorkspace.busy&&!oc.busy&&pendingApiResults.size===0",timeout=30000)
    def native(cmd,require_ok=True):
        r=page.evaluate('async cmd=>await apiRequest(cmd)',cmd)
        with (case_out/'explicit-native.jsonl').open('a') as f:f.write(json.dumps({'at':now(),'phase':phase,'command':cmd,'result':r},ensure_ascii=False)+'\n')
        if require_ok:assert r.get('ok') is True,(cmd,r)
        return r
    def snap(label):
        value={k:native(k) for k in ('dump','objects','references','assembly-read')}
        value['project']=page.evaluate('''async()=>{const c=ReferenceWorkspace.context();return {id:c.id,name:c.name,manifest:await ReferenceWorkspace.manifest(),sources:[...c.sources].map(([id,v])=>[id,Array.from(v.bytes)]),models:ReferenceWorkspace.getSpaceModels(),assemblyDrafts:ReferenceWorkspace.getAssemblyDrafts(),engineeringDrafts:ReferenceWorkspace.getEngineeringDrafts(),dirty:c.dirty,saved:c.saved,downloaded:c.downloaded}}''')
        value['history']=page.evaluate('(()=>{const h=ReferenceWorkspace.history;return {undo:h.undo.length,redo:h.redo.length,limit:h.limit,frame:h.frame,groupOpen:h.group!==null}})()')
        value['canvasCards']=page.locator('.ocard[data-kind][data-id]').evaluate_all("ns=>ns.map(n=>n.dataset.kind+':'+n.dataset.id).sort()")
        write(case_out/(label+'.json'),value);(case_out/(label+'.scene')).write_text(value['dump']['text'])
        return value
    def check(name,ok):
        r={'name':name,'passed':ok is True,'at':now(),'phase':phase};row['checks'].append(r);write(case_out/'result.json',row)
        print(('PASS ' if r['passed'] else 'FAIL ')+name,flush=True);assert r['passed'],name
    def ctl(selector):
        if page.evaluate('innerWidth<=900'):
            kind=page.evaluate("s=>{const n=document.querySelector(s);return n?.closest('#objectList')?'left':n?.closest('#inspectorContent')?'right':n?.closest('.face-inspector-panel')?'face':null}",selector)
            if kind=='left' and not page.evaluate("document.body.classList.contains('drawer-left-open')"):page.locator('#toggleLeft').click(timeout=10000)
            if kind=='right' and page.evaluate("document.body.classList.contains('canvas-composition')&&document.body.classList.contains('drawer-left-open')"):page.locator('#toggleLeft').click(timeout=10000)
            if kind=='face' and not page.evaluate("document.body.classList.contains('drawer-right-open')"):page.locator('#workspaceToggleRight').click(timeout=10000)
        if page.evaluate("s=>document.querySelector(s)?.closest('#createObjectPop')?.hidden===true",selector):page.locator('#mobileCreateObject' if page.evaluate('innerWidth<=900') else '#btnCreateObject').click(timeout=10000)
        page.locator(selector).click(timeout=10000)
    def fill(selector,text):
        ctl(selector);page.wait_for_function('s=>document.activeElement===document.querySelector(s)',arg=selector,timeout=10000)
        page.keyboard.press('Control+A');page.keyboard.insert_text(str(text));page.keyboard.press('Tab')
        page.wait_for_function('v=>document.querySelector(v.s).value===v.value',arg={'s':selector,'value':str(text)},timeout=10000)
    def choose(selector,value):
        options=page.locator(selector).evaluate("n=>[...n.options].filter(o=>!o.disabled).map(o=>o.value)")
        assert str(value) in options,(selector,value,options)
        ctl(selector);page.wait_for_function('s=>document.activeElement===document.querySelector(s)',arg=selector)
        page.keyboard.press('Home')
        for _ in range(options.index(str(value))):page.keyboard.press('ArrowDown')
        page.keyboard.press('Enter');page.wait_for_function('v=>document.querySelector(v.s).value===v.value',arg={'s':selector,'value':str(value)})
    def impact():page.wait_for_function("!!document.querySelector('.reference-impact[open]')",timeout=30000)
    def resolve_impact(approved):
        ctl('#impact-confirm' if approved else '.reference-impact .impact-actions button:first-child')
        page.wait_for_function("!document.querySelector('.reference-impact[open]')",timeout=30000);ready()
    def leave():
        if page.evaluate("!!document.querySelector('#infiniteGridWorkspace')?.open"):ctl('#igClose')
        if page.evaluate('!!oc.focus'):ctl('#workspaceBackButton')
        ready()
    def menu(selector):ctl('#fileMenuBtn');ctl(selector)
    def empty(v):
        return v['dump']['text']=='' and not v['canvasCards'] and all(not val for key,val in v['objects'].items() if key!='ok') and all(not v['references'][key] for key in ('guides','grids','timbers','specs','datums')) and all(not v['assembly-read']['state'][key] for key in ('rules','bindings','instances')) and all(not v['project'][key] for key in ('models','assemblyDrafts','engineeringDrafts','sources'))
    def new_project(label):
        leave();old_id=page.evaluate('ReferenceWorkspace.context().id')
        with page.expect_response(lambda r:urlsplit(r.url).path=='/upload' and r.request.method=='POST' and r.request.post_data=='reset\n',timeout=30000) as response:menu('#btnNewProject')
        assert response.value.status==200 and response.value.json()['ok'] is True
        page.wait_for_function("id=>ReferenceWorkspace.context().id!==id&&document.querySelector('#status').textContent.startsWith('✓ 已建立空白新專案')",arg=old_id,timeout=30000);ready()
        value=snap(label);assert empty(value),value;return value
    def fixture(command):
        assert command.split()[0] in ('boundary','placement','spec','guide','timber','place'),command
        result=native('line '+command,require_ok=False)
        if result.get('preview'):
            assert result['preview']['valid'],result
            native('line confirm '+str(result['preview']['token']))
        else:assert result.get('ok') is True,(command,result)
    def pin():
        return page.evaluate("(()=>{const h=ReferenceWorkspace.history;window.__srPins||=new Map();const id=window.__srPins.size;window.__srPins.set(id,{undo:h.undo.slice(),redo:h.redo.slice(),limit:h.limit,frame:h.frame});return id})()")
    def history_unchanged(token):
        return page.evaluate("id=>{const h=ReferenceWorkspace.history,b=__srPins.get(id),same=(a,z)=>a.length===z.length&&a.every((e,i)=>e===z[i]);return h.limit===b.limit&&h.frame===b.frame&&same(h.undo,b.undo)&&same(h.redo,b.redo)}",token)
    def history_single(token):
        return page.evaluate("id=>{const h=ReferenceWorkspace.history,b=__srPins.get(id),r=b.undo.slice(Math.max(0,b.undo.length+1-h.limit));return h.limit===b.limit&&h.group===null&&h.redo.length===0&&h.undo.length===r.length+1&&h.undo.slice(0,-1).every((v,i)=>v===r[i])&&!b.undo.includes(h.undo.at(-1))}",token)
    def open_source(sid):
        leave();ctl(f'#objectList .object-row[data-kind="grid-system"][data-id="{sid}"]');ctl('#gridObjectOpen')
        page.wait_for_function("document.querySelector('#infiniteGridWorkspace').open&&!document.querySelector('#igRuleAdd').disabled",timeout=30000)
    def focus_face(bid):
        leave();ctl(f'#objectList .object-row[data-kind="boundary"][data-id="{bid}"]');ctl('#inspEnter')
        page.wait_for_function('bid=>oc.edit?.bid===bid&&GridRuleLines.entries().some(l=>l.segments.length)',arg=bid,timeout=30000)
        ctl('#faceInspectorTabs [data-fi-tab="components"]');choose('[data-rule-focus-key]','1');fill('[data-rule-cell-i]','-2');fill('[data-rule-cell-j]','1');ctl('[data-rule-exact]')
        page.wait_for_function("GridRuleLines.entries().length===3&&GridRuleLines.entries().every(l=>l.cell.join(',')==='-2,1'&&l.ruleKey===1)&&document.querySelector('[data-rule-focus-status]').textContent.includes('已核對')",timeout=30000)
    def source_preview(label):
        def is_source(r):
            if urlsplit(r.url).path!='/api' or r.request.method!='POST':return False
            try:return str(json.loads(r.request.post_data)['cmd']).startswith('line preview grid-system ')
            except (KeyError,ValueError,TypeError):return False
        with page.expect_response(is_source,timeout=30000) as response:ctl('#igSaveSource')
        raw=response.value.json();write(case_out/(label+'-native-preview.json'),raw);impact()
        assert response.value.status==200 and raw.get('preview'),raw
        ui=page.evaluate("({bindings:[...document.querySelectorAll('[data-impact-binding]')].map(n=>Number(n.dataset.impactBinding)),guides:[...document.querySelectorAll('[data-impact-guide]')].map(n=>Number(n.dataset.impactGuide)),confirmDisabled:document.querySelector('#impact-confirm').disabled,text:document.querySelector('.reference-impact').textContent})")
        write(case_out/(label+'-ui-preview.json'),ui);page.screenshot(path=str(case_out/(label+'-preview.png')),full_page=True)
        return raw['preview'],ui
    def geometry(label,sid,records,u,v):
        value=snap(label);o=value['objects'];refs=value['references'];sys0=next(x for x in o['gridSystems'] if x['id']==sid)
        check(label+' source pitch and rule identity',sys0['uDefinition']['step']==u and sys0['vDefinition']['step']==v and len(sys0['rules'])==1 and sys0['rules'][0]['ruleKey']==1 and sys0['rules'][0]['divisions']==[3,2])
        for r in records:
            bid=r['face'];binding=next(x for x in o['gridBindings'] if x['id']==r['binding']);grid=next(x for x in refs['grids'] if x['id']==r['grid'])
            check(label+f' face{bid} binding/applied ownership',binding['system']==sid and binding['boundary']==bid and binding['cell']==['-2','1'] and binding['translation']==[100+2*u,200-v] and grid['surface']==bid and grid['sourceSystem']==sid and grid['bindingId']==r['binding'])
            q=native(f"grid-rule-query grid {r['grid']} rule 1 cell -2 1");write(case_out/(label+f'-face{bid}-query.json'),q)
            actual={(l['axis'],l['innerIndex']):(l['coordinate'],segments(l['segments'])) for l in q['lines']}
            expected={key:(coordinate,segments(parts)) for key,(coordinate,parts) in expect_lines(u,v).items()}
            check(label+f' face{bid} exact complete rule-line arithmetic',q['bounds']==[100,200,100+u,200+v] and len(q['lines'])==3 and actual==expected)
            guide=next(x for x in refs['guides'] if x['id']==r['guide']);timber=next(x for x in refs['timbers'] if x['id']==r['timber'])
            check(label+f' face{bid} existing guide follows u0',guide['expression']==r['expression'] and guide['axis']=='v' and guide['off']==100+u//3 and segments(guide['segments'])==segments([[[100+u//3,200],[100+u//3,1800]]]))
            g=timber['geometry'];check(label+f' face{bid} existing direct v0 timber follows exact legal supports',timber['definition']['anchor']==r['anchor'] and timber['definition']['selector']==r['selector'] and timber['role']=='secondary' and g['centerline']==200+v//2 and g['length']==r['length'] and g['A']==g['B']==20 and g['dir']=='+u')
        return value
    def close_browser():
        nonlocal browser,context,page
        active=sys.exc_info()[0] is not None;cleanup=[]
        if context:
            try:context.tracing.stop(path=str(case_out/f'trace-{launch_count}.zip'))
            except BaseException:cleanup.append(traceback.format_exc())
            try:context.close()
            except BaseException:cleanup.append(traceback.format_exc())
        if browser:
            try:browser.close()
            except BaseException:cleanup.append(traceback.format_exc())
        browser=context=page=None
        if cleanup:
            receipt.setdefault('cleanupErrors',[]).extend(cleanup)
            if not active:raise RuntimeError('Owned browser cleanup failed')
    def launch(driver,width):
        nonlocal browser,context,page,launch_count
        launch_count+=1;browser=driver.chromium.launch(executable_path=a.chrome,headless=True,chromium_sandbox=True)
        context=browser.new_context(viewport={'width':width,'height':1000 if width==1400 else 844},accept_downloads=True)
        context.add_init_script("Object.defineProperty(window,'showSaveFilePicker',{value:undefined,configurable:true});window.__srInputs=[];for(const t of ['pointerdown','click','keydown','input','change'])addEventListener(t,e=>__srInputs.push({type:t,trusted:e.isTrusted,key:e.key||null,id:e.target.id||null,tag:e.target.tagName,at:e.timeStamp}),true);")
        context.tracing.start(screenshots=True,snapshots=True,sources=True);page=context.new_page();page.set_default_timeout(30000)
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('console',lambda m:errors.append('console: '+m.text) if m.type=='error' else None)
        def dialog(d):
            allow=d.type=='confirm' and (d.message.startswith('建立一份空白新專案，切換為新的專案識別及「未命名專案」。') or d.message=='目前專案有尚未保存的變更。要離開目前專案嗎？')
            with (case_out/'dialogs.jsonl').open('a') as f:f.write(json.dumps({'at':now(),'type':d.type,'message':d.message,'accepted':allow},ensure_ascii=False)+'\n')
            if allow:d.accept()
            else:errors.append('Unexpected dialog: '+d.message);d.dismiss()
        def network(req):
            if urlsplit(req.url).path not in ('/api','/runtime','/upload','/upload/prepare','/upload/confirm','/upload/cancel'):return
            try:
                res=req.response();item={'at':now(),'phase':phase,'url':req.url,'method':req.method,'requestBody':req.post_data,'status':res.status,'responseBody':res.body().decode()}
                with (case_out/'http-raw.jsonl').open('a') as f:f.write(json.dumps(item,ensure_ascii=False)+'\n')
            except (KeyboardInterrupt,InterruptedError):raise
            except Exception:network_errors.append(traceback.format_exc())
        page.on('dialog',dialog);page.on('requestfinished',network)
        response=page.goto(a.url,wait_until='domcontentloaded',timeout=30000);assert response.status==200;ready()
        assert page.title()=='構形 Canvas · 工程規格與空間建模' and page.evaluate('oc.on===true')
        receipt.setdefault('launches',[]).append({'index':launch_count,'width':width,'version':browser.version,'sandbox':True,'profile':'new Playwright-owned browser process/profile','savePicker':'explicit download fallback'})
    try:
        receipt['python']=sys.version;receipt['playwright']=importlib.metadata.version('playwright');receipt['before']=identity('before')
        from playwright.sync_api import sync_playwright
        with sync_playwright() as driver:
            for width in widths:
                case_out=out/str(width);case_out.mkdir();errors.clear();network_errors.clear();row={'width':width,'started':now(),'checks':[],'passed':False};receipt['cases'].append(row)
                try:
                    phase='boundary-support-fixture';launch(driver,width);new_project('initial-empty')
                    for bid,first,stops in ((1,1,(120,380)),(2,21,(120,680))):
                        fixture(f'boundary {bid} outline 100,200 2100,200 2100,1800 100,1800');fixture(f'placement {bid} on boundary {bid} origin 0 0 0 u +x v +y')
                        for tid,edge in ((first+80,'e0'),(first+81,'e2')):
                            fixture(f'timber {tid} 20 20 role boundary');fixture(f'place {tid} on {bid} at-face {edge} +u +n')
                        for offset,x in enumerate(stops):
                            tid=first+offset;fixture(f'spec support_position_{tid} {x}');fixture(f'guide {tid} {bid} v spec:support_position_{tid}');fixture(f'timber {tid} 20 20 role primary');fixture(f'place {tid} on {bid} at-line guide {tid} +v +n')
                    assert page.evaluate('async()=>await renderObjects()') is True;ready();snap('boundary-support-fixture')
                    phase='ui-source-rule';ctl('#btnQuickGrid' if width==390 else '#btnNewGridSystem');page.wait_for_function("!!document.querySelector('#igName')&&!document.querySelector('#igName').disabled")
                    fill('#igName',f'SR16 SR23 {width}');fill('#igUStep','600');fill('#igVStep','400');ctl('#igMainAlong input[value="none"]');ctl('#igSaveSource');impact();resolve_impact(True)
                    systems=native('objects')['gridSystems'];assert len(systems)==1;sid=systems[0]['id']
                    ctl('#igRuleAdd');fill('#igRuleName','Shared physical-support rule');fill('#igRuleU','3');fill('#igRuleV','2');ctl('#igRulePreview');impact();resolve_impact(True)
                    records=[]
                    for bid,first,length in ((1,1,240),(2,21,540)):
                        phase=f'ui-face{bid}-binding-before-refs'
                        if bid==2:open_source(sid)
                        before_ids={b['id'] for b in native('objects')['gridBindings']};ctl('#igNewBinding');choose('#igBoundary',bid);page.wait_for_function("document.querySelector('#igVertex').options.length>1&&!document.querySelector('#igCellI').disabled")
                        choose('#igVertex','outer:0');fill('#igCellI','-2');fill('#igCellJ','1');ctl('[data-ig-anchor="0,0"]');ctl('#igSaveBinding');impact();resolve_impact(True)
                        added=[b for b in native('objects')['gridBindings'] if b['id'] not in before_ids];assert len(added)==1;binding=added[0]['id']
                        choose('#igSurface',bid);ctl('#igApplyBinding');impact();resolve_impact(True)
                        grid=next(g['id'] for g in native('references')['grids'] if g['bindingId']==binding)
                        phase=f'ui-face{bid}-guide-direct-before-next-binding';focus_face(bid)
                        expression=f'gridrule:{grid}:{sid}:1:-2:1:u:0';choose('#refGuideAxis','v');choose('#refGuideMode','source');choose('#refGuideSource',expression);ctl('#refGuideCreate');ready()
                        page.wait_for_function('e=>fe.guides.some(g=>g.expression===e)',arg=expression,timeout=30000)
                        guide=next(g['id'] for g in native('references')['guides'] if g['expression']==expression and g['surface']==bid)
                        focus_face(bid);anchor=f'at-line rule {grid} {sid} 1 -2 1 v 0';selector=f'between t{first} t{first+1}'
                        choose('#tbAnchor',anchor);fill('#tbA','20');fill('#tbB','20');choose('#tbDir','+u');choose('#tbRole','secondary')
                        if not page.locator('#tbNewSegmentDetails').evaluate('n=>n.open'):ctl('#tbNewSegmentDetails > summary')
                        fill('#tbSelector',selector);ctl('#tbPlace');ready();page.wait_for_function('a=>fe.timbers.some(t=>t.definition?.anchor===a)',arg=anchor,timeout=30000)
                        timber=next(t for t in native('references')['timbers'] if t['definition']['anchor']==anchor)
                        records.append({'face':bid,'binding':binding,'grid':grid,'guide':guide,'timber':timber['id'],'expression':expression,'anchor':anchor,'selector':selector,'length':length})
                        check(f'face{bid} guide and direct reference exist before the next source/binding operation',timber['geometry']['length']==length and len(native('objects')['gridBindings'])==bid)
                        snap(f'face{bid}-refs-authored');write(case_out/'authored-identities.json',{'source':sid,'ruleKey':1,'records':records})
                    phase='baseline-complete';leave();baseline=geometry('before-source-edit',sid,records,600,400)
                    phase='SR16-invalid-source';open_source(sid);fill('#igUStep','300');cancel_base=snap('sr16-before-preview');token=pin();preview,ui=source_preview('sr16')
                    check('SR16 both native and rendered impact contain the two actual bindings',set(x['id'] for x in preview['gridBindings'])==set(r['binding'] for r in records)==set(ui['bindings']))
                    check('SR16 only second physical component violates and Confirm is disabled',preview['valid'] is False and preview['violations'] and {x['timber'] for x in preview['violations']}=={records[1]['timber']} and ui['confirmDisabled'] is True)
                    pending=snap('sr16-pending');check('SR16 preview preserves full raw native World and history',all(pending[k]==cancel_base[k] for k in ('dump','objects','references','assembly-read')) and history_unchanged(token))
                    resolve_impact(False);cancelled=snap('sr16-cancelled');check('SR16 Cancel preserves raw World references ownership and exact history entries',all(cancelled[k]==cancel_base[k] for k in ('dump','objects','references','assembly-read')) and history_unchanged(token))
                    phase='SR23-positive-cancel-confirm';fill('#igUStep','900');fill('#igVStep','600');positive_base=snap('sr23-before-preview');token=pin();preview,ui=source_preview('sr23-cancel')
                    check('SR23 legal preview contains both bindings and both preexisting guide updates',preview['valid'] is True and not ui['confirmDisabled'] and set(ui['bindings'])=={r['binding'] for r in records} and {r['guide'] for r in records}.issubset(set(ui['guides'])))
                    resolve_impact(False);cancelled=snap('sr23-cancelled');check('SR23 positive Cancel preserves full raw native snapshots and history',all(cancelled[k]==positive_base[k] for k in ('dump','objects','references','assembly-read')) and history_unchanged(token))
                    preview,ui=source_preview('sr23-confirm');assert preview['valid'] is True and not ui['confirmDisabled'];resolve_impact(True)
                    check('SR23 one common history transaction updates source and descendants',history_single(token));leave();changed=geometry('after-source-edit',sid,records,900,600)
                    assert baseline['dump']['text'].count('u repeat 0 600 v repeat 0 400')==1
                    expected_scene=baseline['dump']['text'].replace('u repeat 0 600 v repeat 0 400','u repeat 0 900 v repeat 0 600')
                    check('SR23 serialized World changes only the existing source pitches',expected_scene!=baseline['dump']['text'] and changed['dump']['text']==expected_scene)
                    for r in records:
                        phase=f'SR23-face{r["face"]}-rendered-updated-lines';focus_face(r['face']);rendered=page.evaluate('GridRuleLines.entries().map(l=>({ref:l.ref,segments:l.segments}))');write(case_out/f'after-face{r["face"]}-rendered-lines.json',rendered)
                        check(f'SR23 face{r["face"]} actual exact-cell display reflects current native rule segments',len(rendered)==3 and all(x['ref']['appliedGridId']==r['grid'] and x['ref']['systemId']==sid for x in rendered) and sorted(segments(x['segments']) for x in rendered)==sorted(segments(x[1]) for x in expect_lines(900,600).values()))
                    phase='SR23-history';leave();ctl('#btnUndo')
                    page.wait_for_function("document.querySelector('#status').textContent.startsWith('✓ 已復原')&&!oc.busy",timeout=30000);ready()
                    undone=geometry('undone',sid,records,600,400);check('SR23 one UI Undo restores complete World and all references',world(undone)==world(baseline))
                    ctl('#btnRedo');page.wait_for_function("document.querySelector('#status').textContent.startsWith('✓ 已重做')&&!oc.busy",timeout=30000);ready()
                    redone=geometry('redone',sid,records,900,600);check('SR23 one UI Redo restores complete changed World and all references',world(redone)==world(changed))
                    phase='SR23-save';before_save=snap('before-save');expected_manifest=expected_archive(before_save)
                    write(case_out/'expected-archive-manifest.json',expected_manifest)
                    with page.expect_download(timeout=60000) as download:menu('#btnSaveProject')
                    archive=case_out/'sr23-project.gcanvas';download.value.save_as(archive);assert download.value.failure() is None
                    page.wait_for_function("!ReferenceWorkspace.busy&&ReferenceWorkspace.context().downloaded===true&&document.querySelector('#status').textContent.startsWith('已產生專案下載')",timeout=60000);saved=snap('saved')
                    with zipfile.ZipFile(archive) as z:manifest=json.loads(z.read('manifest.json'));scene=z.read('world.scene').decode()
                    write(case_out/'archive-manifest.json',manifest)
                    check('SR23 real Save preserves native World and saves complete versioned manifest contract',world(saved)==world(before_save) and project(saved)==project(before_save) and scene==saved['dump']['text'] and manifest==expected_manifest)
                    phase='SR23-clear';newblank=new_project('new-empty');check('SR23 New truly clears all grids references timbers and project payload',empty(newblank) and newblank['project']['id']!=saved['project']['id'])
                    write(case_out/'inputs-first-browser.json',page.evaluate('__srInputs'));close_browser();phase='SR23-fresh-browser';launch(driver,width);fresh=snap('fresh-profile-empty');check('SR23 fresh browser starts from genuinely empty native World',empty(fresh) and fresh['project']['id']!=saved['project']['id'])
                    phase='SR23-formal-open'
                    with page.expect_response(lambda r:urlsplit(r.url).path=='/upload/confirm' and r.request.method=='POST',timeout=60000) as response:
                        with page.expect_file_chooser(timeout=10000) as chooser:menu('#btnOpenProject')
                        assert chooser.value.element.get_attribute('id')=='projectFile';chooser.value.set_files(str(archive))
                    assert response.value.status==200 and response.value.json()['ok'] is True
                    page.wait_for_function("document.querySelector('#projectFile').value===''&&document.querySelector('#status').textContent.startsWith('✓ 已開啟專案')&&!ReferenceWorkspace.busy&&!oc.busy",timeout=60000);ready()
                    reopened=geometry('project-reopened',sid,records,900,600)
                    check('SR23 formal chooser Open restores full World references and full project payload',world(reopened)==world(saved) and project(reopened)==project(saved))
                    phase='SR23-open-history';ctl('#btnUndo');page.wait_for_function("document.querySelector('#status').textContent.startsWith('✓ 已復原')&&!oc.busy",timeout=30000);ready()
                    open_undone=snap('open-undone');check('SR23 one UI Undo after fresh Open restores original fresh empty context and all data',empty(open_undone) and world(open_undone)==world(fresh) and project(open_undone)==project(fresh))
                    ctl('#btnRedo');page.wait_for_function("document.querySelector('#status').textContent.startsWith('✓ 已重做')&&!oc.busy",timeout=30000);ready()
                    open_redone=geometry('open-redone',sid,records,900,600)
                    check('SR23 one UI Redo after fresh Open restores the complete reopened World and project',world(open_redone)==world(reopened) and project(open_redone)==project(reopened))
                    check('No uncaught console or raw network-capture errors',not errors and not network_errors);write(case_out/'inputs-reopened-browser.json',page.evaluate('__srInputs'));row['passed']=True;row['archiveSha256']=sha(archive)
                except BaseException:
                    row['failedPhase']=phase;row['error']=traceback.format_exc()
                    if page:
                        try:page.screenshot(path=str(case_out/'failed.png'),full_page=True);write(case_out/'inputs-failed.json',page.evaluate('__srInputs'))
                        except BaseException:row['failureCaptureError']=traceback.format_exc()
                    raise
                finally:
                    original_failure=sys.exc_info()[0] is not None;cleanup_failure=None
                    try:close_browser()
                    except BaseException:cleanup_failure=traceback.format_exc();row['cleanupError']=cleanup_failure
                    row['errors']=list(errors);row['networkErrors']=list(network_errors)
                    row['cleanupErrors']=list(receipt.get('cleanupErrors',[]))
                    if errors or network_errors or cleanup_failure or row['cleanupErrors']:row['passed']=False
                    row['finished']=now();write(case_out/'result.json',row)
                    if not original_failure and not row['passed']:raise RuntimeError('Case failed including browser-close callbacks; see preserved result and cleanup errors')
        assert len(receipt['cases'])==len(widths) and all(r['passed'] for r in receipt['cases']);receipt['exitCode']=0
    except BaseException:receipt['error']=traceback.format_exc();receipt['failedPhase']=phase
    finally:
        if 'before' in receipt:
            try:
                receipt['after']=identity('after');differences=release.compare_snapshots(receipt['before'],receipt['after'])
                receipt['identityDifferences']=differences
                if differences:receipt['exitCode']=1
            except BaseException:receipt['afterIdentityError']=traceback.format_exc();receipt['exitCode']=1
        receipt['finished']=now();write(out/'receipt.json',receipt)
    print(json.dumps({'out':str(out),'exitCode':receipt['exitCode'],'cases':[{'width':r['width'],'passed':r['passed'],'checks':len(r['checks'])} for r in receipt['cases']]}));return receipt['exitCode']
if __name__=='__main__':sys.exit(main())
