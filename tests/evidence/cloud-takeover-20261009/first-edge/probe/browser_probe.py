import argparse, datetime, hashlib, json, os, pathlib, subprocess, sys, traceback, urllib.request
from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path(os.environ['GEOMETRY_EVIDENCE_REPO']).resolve()
parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:18971/')
parser.add_argument('--out', required=True)
parser.add_argument('--only', choices=['all','handles','edges'], default='all')
parser.add_argument('--width',type=int,choices=[1400,390])
args = parser.parse_args()
OUT = pathlib.Path(args.out); OUT.mkdir(parents=True,exist_ok=False)
records=[]
def save(name,data): (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def identity(label):
    commands=[]
    for cmd in [['pwd'],['git','status','--short'],['git','rev-parse','HEAD'],['git','diff','--binary'],['git','rev-parse','origin/main']]:
        p=subprocess.run(cmd,cwd=REPO,capture_output=True,text=True)
        commands.append({'argv':cmd,'stdout':p.stdout,'stderr':p.stderr,'exitCode':p.returncode})
    runtime=json.load(urllib.request.urlopen(args.url+'runtime'))
    data={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'commands':commands,'runtime':runtime,
      'sourceSha256':{f:hashlib.sha256((REPO/f).read_bytes()).hexdigest() for f in ['geometry-web/app.js','geometry-web/space-workspace.js']},
      'scriptSha256':{f:hashlib.sha256((BASE/f).read_bytes()).hexdigest() for f in ['browser_probe.py','browser_instrumentation.js']}}
    save(label+'.json',data);return data

def wait(page,expr): page.wait_for_function(expr,timeout=12000)
def click(page,selector): page.locator(selector).click(timeout=7000)
def type_value(page,selector,value):
    click(page,selector);page.keyboard.press('Control+A');page.keyboard.insert_text(value)
def fixture(page,lines):
    result=page.evaluate('''async lines => { await setView3(false); resetSceneFocus(); const out=[await api('reset')]; for(const l of lines)out.push(await api('line '+l)); await renderObjects();return out; }''',lines)
    if any(r.get('ok') is not True for r in result): raise RuntimeError('Fixture refused: '+json.dumps(result))
    wait(page,"connection.phase==='ready' && !oc.busy")
    return result
def drawer(page,side,opened,face=False):
    if page.viewport_size['width']>900: return
    current=page.evaluate('(s)=>document.body.classList.contains("drawer-"+s+"-open")',side)
    if current==opened:return
    if opened:
        trigger=('#workspaceToggle'+side.title()) if face else '#toggle'+side.title()
        if not page.locator(trigger).is_visible() and side=='right' and not face and page.locator('#inspectorContent').is_visible():return
        click(page,trigger)
    else:page.keyboard.press('Escape')
    wait(page,f'document.body.classList.contains("drawer-{side}-open")==={str(opened).lower()}')
def dump(page):return page.evaluate("async()=>{const r=await api('dump');if(!r.ok)throw Error(JSON.stringify(r));return r.text;}")
def surface(i):return f'surface {i} origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000'
def audit(page):return page.evaluate('window.__closureAudit.read()')

def handle_test(page,width):
    fixture(page,[surface(711),surface(712)])
    click(page,'#btnObj');wait(page,'view3===true && workSurfaces.length===2 && !!layout')
    drawer(page,'left',True);page.locator('#workSurf').select_option('711');drawer(page,'left',False)
    before_dump=dump(page)
    page.evaluate("__closureAudit.arm('projection',711)")
    click(page,'[data-v3-tool="edit"]');wait(page,"__closureAudit.gate.phase==='held'")
    click(page,'[data-v3-tool="view"]')
    drawer(page,'left',True);page.locator('#workSurf').select_option('712');drawer(page,'left',False)
    click(page,'[data-v3-tool="edit"]')
    wait(page,"__closureAudit.draws.some(x=>x.bid===712 && x.phase==='settled')")
    read="()=>({tool,editBid,editToken,groups:previewGs.filter(g=>g.isConnected).length,handles:document.querySelectorAll('#world polygon[stroke-dasharray=\"8 4\"],#world circle[fill=\"#c0392b\"]').length})"
    before=page.evaluate(read);page.screenshot(path=str(OUT/f'handles-{width}-B-before.png'))
    page.evaluate('__closureAudit.gate.release()');wait(page,"__closureAudit.draws.every(x=>x.phase==='settled') && __closureAudit.gate.phase==='released'")
    after=page.evaluate(read);after_dump=dump(page)
    page.screenshot(path=str(OUT/f'handles-{width}-after-A.png'))
    return {'ok':before['handles']>0 and after==before and before_dump==after_dump,'before':before,'after':after,'worldUnchanged':before_dump==after_dump,'audit':audit(page)}

def edge_test(page,width,scope,mode):
    bid=731
    fixture(page,[surface(bid)+' hole 3000,1000 3500,1000 3500,1500 3000,1500',f'canvas-pos boundary {bid} 30 30'])
    drawer(page,'left',True);click(page,f'.object-row[data-kind="boundary"][data-id="{bid}"]');drawer(page,'left',False)
    drawer(page,'right',True)
    if scope=='face':
        click(page,'#inspEnter');wait(page,f'oc.edit?.bid==={bid}')
        drawer(page,'right',True,True);click(page,'#faceInspectorTabs [data-fi-tab="prop"]')
    prefix='edge' if scope=='face' else 'mainEdge'
    selector='#'+prefix+'Length0';sibling='#'+prefix+'Length1'
    page.locator(selector).wait_for(state='visible',timeout=12000)
    before_dump=dump(page)
    page.evaluate('s=>window.__originalEdge=document.querySelector(s)',selector)
    page.evaluate("__closureAudit.arm('edge',731)")
    submitted='4200' if mode=='success-sibling' else '2000'
    type_value(page,selector,submitted);page.keyboard.press('Tab')
    wait(page,"__closureAudit.gate.phase==='held'")
    native=page.evaluate('__closureAudit.gate.nativeReply')
    if bool(native.get('ok')) != (mode=='success-sibling') or native.get('preview'):
        raise RuntimeError('Native response did not meet fixture requirement: '+json.dumps(native))
    if mode=='same-input-new-value':type_value(page,selector,'5151')
    elif mode.startswith('replacement'):
        # Explicit redraw fault injection through the real product renderer.
        # Interactions and native response remain real; this is not a claim that
        # a particular user action is the redraw trigger.
        page.evaluate('renderFaceInspector()' if scope=='face' else 'renderInspector()')
        wait(page,'!window.__originalEdge.isConnected')
        if mode=='replacement-new-value':type_value(page,selector,'5151')
    elif mode=='success-sibling':type_value(page,sibling,'4242')
    read='''p=>({input:{value:document.querySelector('#'+p+'Length0').value,model:document.querySelector('#'+p+'Length0').defaultValue},sibling:{value:document.querySelector('#'+p+'Length1').value,model:document.querySelector('#'+p+'Length1').defaultValue},focus:document.activeElement?.id,originalConnected:window.__originalEdge.isConnected})'''
    before=page.evaluate(read,prefix)
    page.evaluate('__closureAudit.gate.release()')
    wait(page,"__closureAudit.gate.phase==='released' && __closureAudit.changes.length>0 && __closureAudit.changes.every(x=>x.phase==='settled')")
    after=page.evaluate(read,prefix);after_dump=dump(page)
    if mode=='success-sibling':
        ok=after['input']=={'value':'4200','model':'4200'} and after['sibling']=={'value':'4242','model':'3000'} and after_dump!=before_dump
    else:
        expected='4000' if mode=='replacement-rejected-value' else '5151'
        ok=after['input']=={'value':expected,'model':'4000'} and after_dump==before_dump
    page.screenshot(path=str(OUT/f'edges-{width}-{scope}-{mode}.png'))
    return {'ok':ok,'scope':scope,'mode':mode,'before':before,'after':after,'worldUnchanged':before_dump==after_dump,'audit':audit(page),'redrawInjection':mode.startswith('replacement')}

initial_identity=identity('before')
if initial_identity['runtime'].get('fresh') is not True:
    raise RuntimeError('Service runtime is not fresh; stop before browser launch: '+json.dumps(initial_identity['runtime']))
try:
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,chromium_sandbox=True)
        save('browser.json',{'version':browser.version,'sandbox':True,'launchArgumentsRequested':[]})
        tests=[]
        for width in ([args.width] if args.width else [1400,390]):
            if args.only!='edges':tests.append((f'handles-{width}',width,lambda p,w=width:handle_test(p,w)))
            if args.only!='handles':
                for scope in ('main','face'):
                    for mode in ('same-input-new-value','replacement-rejected-value','replacement-new-value','success-sibling'):
                        tests.append((f'edges-{width}-{scope}-{mode}',width,lambda p,w=width,s=scope,m=mode:edge_test(p,w,s,m)))
        for name,width,fn in tests:
            ctx=browser.new_context(viewport={'width':width,'height':900 if width>900 else 844})
            page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            ctx.tracing.start(screenshots=True,snapshots=True,sources=True)
            row={'name':name,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
            try:
                response=page.goto(args.url,wait_until='domcontentloaded',timeout=30000)
                if response.status != 200:raise RuntimeError('Product entry HTTP '+str(response.status))
                wait(page,"typeof api==='function' && connection.phase==='ready'")
                page.evaluate((BASE/'browser_instrumentation.js').read_text())
                row.update(fn(page));row['pageErrors']=errors
                if errors:row['ok']=False
            except Exception as error:
                row.update({'ok':False,'preconditionOrHarnessError':str(error),'traceback':traceback.format_exc(),'pageErrors':errors})
                try:row['audit']=audit(page);page.screenshot(path=str(OUT/(name+'-error.png')))
                except Exception:pass
            finally:
                records.append(row);save(name+'.json',row);save('results.json',records)
                ctx.tracing.stop(path=str(OUT/(name+'-trace.zip')));ctx.close()
            print(json.dumps({'name':name,'ok':row['ok'],'harnessError':row.get('preconditionOrHarnessError')},ensure_ascii=False),flush=True)
        browser.close()
finally:
    identity('after')
exit_code=1 if any(not r.get('ok') for r in records) else 0
save('receipt.json',{'argv':sys.argv,'exitCode':exit_code,'tests':len(records),'results':'results.json','original173ProbeRecovered':False,'scope':'Real sandboxed Chromium; actual native replies delayed without altering payload; fixture setup uses api, replacement redraw explicitly injected via product renderer; not full product acceptance'})
sys.exit(exit_code)
