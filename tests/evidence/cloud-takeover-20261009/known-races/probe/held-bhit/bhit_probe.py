import os
import argparse, datetime, hashlib, json, pathlib, subprocess, sys, traceback, urllib.request
from playwright.sync_api import sync_playwright

BASE=pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path(os.environ['GEOMETRY_EVIDENCE_REPO']).resolve()
parser=argparse.ArgumentParser()
parser.add_argument('--url',default='http://127.0.0.1:18971/')
parser.add_argument('--out',required=True)
parser.add_argument('--width',type=int,choices=[1400,390])
args=parser.parse_args()
OUT=pathlib.Path(args.out);OUT.mkdir(parents=True,exist_ok=False)
records=[]
def save(name,data): (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def identity(label):
    commands=[]
    for cmd in [['pwd'],['git','status','--short'],['git','rev-parse','HEAD'],['git','diff','--binary'],['git','rev-parse','origin/main']]:
        p=subprocess.run(cmd,cwd=REPO,capture_output=True,text=True)
        commands.append({'argv':cmd,'stdout':p.stdout,'stderr':p.stderr,'exitCode':p.returncode})
    data={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'commands':commands,
      'runtime':json.load(urllib.request.urlopen(args.url+'runtime',timeout=10)),
      'sourceSha256':{f:hashlib.sha256((REPO/f).read_bytes()).hexdigest() for f in ['geometry-web/app.js','geometry-web/space-workspace.js']},
      'scriptSha256':{f:hashlib.sha256((BASE/f).read_bytes()).hexdigest() for f in ['bhit_probe.py','bhit_instrumentation.js']}}
    save(label+'.json',data);return data
def wait(page,expr):page.wait_for_function(expr,timeout=12000)
def click(page,selector):page.locator(selector).click(timeout=7000)
def drawer(page,opened):
    if page.viewport_size['width']>900:return
    current=page.evaluate('document.body.classList.contains("drawer-left-open")')
    if current==opened:return
    if opened:click(page,'#toggleLeft')
    else:page.keyboard.press('Escape')
    wait(page,f'document.body.classList.contains("drawer-left-open")==={str(opened).lower()}')
def dump(page):return page.evaluate("async()=>{const r=await api('dump');if(!r.ok)throw Error(JSON.stringify(r));return r.text;}")
def surface(i):return f'surface {i} origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000'
def run_case(page,width):
    fixture=page.evaluate('''async lines=>{await setView3(false);resetSceneFocus();const out=[await api('reset')];for(const line of lines)out.push(await api('line '+line));await renderObjects();return out;}''',[surface(711),surface(712)])
    if any(x.get('ok') is not True for x in fixture):raise RuntimeError('Fixture refused: '+json.dumps(fixture))
    wait(page,"connection.phase==='ready'&&!oc.busy")
    click(page,'#btnObj');wait(page,'view3===true&&workSurfaces.length===2&&!!layout')
    drawer(page,True);page.locator('#workSurf').select_option('711');drawer(page,False)
    click(page,'[data-v3-tool="edit"]')
    wait(page,"editBid===711&&editDrag===null&&__bhitAudit.draws.some(x=>x.bid===711&&x.phase==='settled')")
    before_dump=dump(page)
    handle=page.locator('#world circle[fill="#c0392b"]').first
    handle.wait_for(state='visible',timeout=12000)
    box=handle.bounding_box()
    if not box:raise RuntimeError('A vertex handle has no rendered box')
    point={'x':box['x']+box['width']/2,'y':box['y']+box['height']/2}
    usable=page.evaluate('''p=>{const el=document.elementFromPoint(p.x,p.y);return {inViewport:p.x>=0&&p.x<innerWidth&&p.y>=0&&p.y<innerHeight,canvas:!!el&&cv.contains(el),tag:el?.tagName};}''',point)
    if not usable['inViewport'] or not usable['canvas']:raise RuntimeError('A handle pointer location is obstructed: '+json.dumps(usable))
    page.evaluate('__bhitAudit.arm(711)')
    page.mouse.move(point['x'],point['y']);page.mouse.down(button='left')
    wait(page,"__bhitAudit.gate.phase==='held'&&__bhitAudit.downs.length===1&&__bhitAudit.downs[0].phase==='running'")
    native=page.evaluate('__bhitAudit.gate.nativeReply')
    if native.get('ok') is not True:raise RuntimeError('Native bhit did not find the pointed handle: '+json.dumps(native))
    # Complete the real pointer gesture while the native response remains held.
    page.mouse.up(button='left')
    wait(page,"__bhitAudit.ups.length===1&&__bhitAudit.ups[0].phase==='settled'&&editDrag===null&&__bhitAudit.gate.phase==='held'")
    click(page,'[data-v3-tool="view"]')
    drawer(page,True);page.locator('#workSurf').select_option('712');drawer(page,False)
    click(page,'[data-v3-tool="edit"]')
    wait(page,"editBid===712&&editDrag===null&&__bhitAudit.draws.some(x=>x.bid===712&&x.phase==='settled')&&__bhitAudit.gate.phase==='held'")
    before=page.evaluate('__bhitAudit.state()')
    if before['handles']<=0:raise RuntimeError('B has no completed handles before releasing A')
    page.screenshot(path=str(OUT/f'bhit-{width}-B-before.png'))
    page.evaluate('__bhitAudit.gate.release()')
    wait(page,"__bhitAudit.gate.phase==='released'&&__bhitAudit.downs.length===1&&__bhitAudit.downs.every(x=>x.phase==='settled')")
    after=page.evaluate('__bhitAudit.state()');after_dump=dump(page)
    observed=page.evaluate('__bhitAudit.read()')
    page.screenshot(path=str(OUT/f'bhit-{width}-after-A.png'))
    trusted=len(observed['pointers'])==2 and all(x['trusted'] for x in observed['pointers']) and observed['downs'][0]['trusted'] and observed['ups'][0]['trusted']
    return {'ok':before==after and after['editDrag'] is None and before_dump==after_dump and trusted,
      'before':before,'after':after,'worldUnchanged':before_dump==after_dump,'trustedPointerDownAndUp':trusted,
      'point':point,'hitTest':usable,'fixture':fixture,'audit':observed}

initial=identity('before')
if initial['runtime'].get('fresh') is not True:raise RuntimeError('Service is not fresh; no browser launched')
try:
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,chromium_sandbox=True)
        save('browser.json',{'version':browser.version,'sandbox':True,'launchArgumentsRequested':[]})
        for width in ([args.width] if args.width else [1400,390]):
            name=f'bhit-{width}'
            ctx=browser.new_context(viewport={'width':width,'height':900 if width>900 else 844})
            page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            ctx.tracing.start(screenshots=True,snapshots=True,sources=True)
            row={'name':name,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
            try:
                response=page.goto(args.url,wait_until='domcontentloaded',timeout=30000)
                if response.status!=200:raise RuntimeError('Product entry HTTP '+str(response.status))
                wait(page,"typeof api==='function'&&connection.phase==='ready'")
                page.evaluate((BASE/'bhit_instrumentation.js').read_text())
                row.update(run_case(page,width));row['pageErrors']=errors
                if errors:row['ok']=False
            except Exception as error:
                row.update({'ok':False,'preconditionOrHarnessError':str(error),'traceback':traceback.format_exc(),'pageErrors':errors})
                try:row['audit']=page.evaluate('__bhitAudit.read()');page.screenshot(path=str(OUT/(name+'-error.png')))
                except Exception:pass
            finally:
                records.append(row);save(name+'.json',row);save('results.json',records)
                ctx.tracing.stop(path=str(OUT/(name+'-trace.zip')));ctx.close()
            print(json.dumps({'name':name,'ok':row['ok'],'harnessError':row.get('preconditionOrHarnessError')},ensure_ascii=False),flush=True)
        browser.close()
finally:identity('after')
exit_code=1 if any(not x.get('ok') for x in records) else 0
save('receipt.json',{'argv':sys.argv,'exitCode':exit_code,'scope':'Native bhit reply held unchanged after trusted pointerdown; trusted pointerup occurs while held; A edit to view to B edit; wait actual original canvasDown promise; synthetic fixtures, not full product acceptance.'})
sys.exit(exit_code)
