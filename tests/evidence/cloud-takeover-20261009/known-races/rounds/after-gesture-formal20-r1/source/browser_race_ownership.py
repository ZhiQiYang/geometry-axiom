"""Independent bounded race controls; requires an exclusive browser slot.

Synthetic fixtures use native API. All navigation, typing and pointer gestures
are trusted Playwright input. No force clicks, retries or edited native replies.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import traceback
from urllib.parse import urlsplit
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parent
A_INITIAL = 'boundary 731 outline 0,0 4000,0 4000,3000 0,3000 hole 3000,1000 3500,1000 3500,1500 3000,1500'
A_EXPECTED = 'boundary 731 outline 0,0 4200,0 4200,3000 0,3000 hole 3000,1000 3500,1000 3500,1500 3000,1500'
B_INITIAL = 'boundary 732 outline 0,0 4000,0 4000,3000 0,3000'
B_DRAG = 'boundary 732 outline 200,100 4000,100 4000,3000 200,3000'
B_NEXT_DRAG = 'boundary 732 outline 300,200 4000,200 4000,3000 300,3000'
B_HOLE = B_INITIAL + ' hole 100,100 400,100 400,400 100,400'


def stamp(): return datetime.now(timezone.utc).isoformat()
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--url', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--expected-head', required=True)
    parser.add_argument('--width', type=int, choices=[1400, 390], action='append')
    parser.add_argument('--only', choices=['all', 'same-edit-up', 'bhit-active-B', 'cross-B-drag', 'cross-B-hole', 'zoom', 'pointercancel', 'lostcapture', 'old-up-new-gesture'], default='all')
    parser.add_argument('--scope', choices=['main', 'face'])
    args = parser.parse_args()
    root, out = args.root.resolve(), args.out.resolve()
    parsed = urlsplit(args.url)
    assert parsed.scheme == 'http' and parsed.hostname in ['127.0.0.1','localhost'] and parsed.port not in [None,8765]
    assert parsed.path == '/' and not any([parsed.query,parsed.fragment,parsed.username,parsed.password])
    assert len(args.expected_head)==40 and all(c in '0123456789abcdef' for c in args.expected_head)
    assert not out.is_relative_to(root)
    out.mkdir(parents=True, exist_ok=False)
    records = []

    def save(name, value): (out/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    def command(argv):
        p=subprocess.run(argv,cwd=root,capture_output=True,text=True,timeout=15)
        return {'argv':argv,'exitCode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    def identity(label):
        commands=[command(a) for a in [['pwd'],['git','status','--short'],['git','rev-parse','HEAD'],['git','rev-parse','HEAD^{tree}'],['git','diff','--binary'],['git','diff','--cached','--binary']]]
        with urlopen(args.url+'runtime',timeout=10) as response:
            raw=response.read();(out/(label+'-runtime.raw.json')).write_bytes(raw)
            runtime=json.loads(raw)
        value={'utc':stamp(),'commands':commands,'runtime':runtime,'runtimeBodySha256':hashlib.sha256(raw).hexdigest(),
            'sourceSha256':{str(p.relative_to(root)):sha(p) for p in [root/'geometry-web/app.js',root/'geometry-web/space-workspace.js',root/'geometry-web/app.css',root/'geometry-web/index.html']},
            'scriptSha256':{name:sha(BASE/name) for name in ['browser_race_ownership.py','browser_race_ownership_instrumentation.js']}}
        save(label+'.json',value);return value
    def wait(page, expression): page.wait_for_function(expression, timeout=15000)
    def click(page, selector): page.locator(selector).click(timeout=7000)
    def bounded(page, expression, arg=None):
        return page.evaluate('''async arg=>{let timer;try{return await Promise.race([('''+expression+''')(arg),new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('Supplement observation deadline (60000 ms)')),60000);})]);}finally{clearTimeout(timer);}}''',arg)
    def dump(page, name, stage):
        text=bounded(page,"async()=>{const r=await api('dump');if(!r.ok)throw Error(JSON.stringify(r));return r.text;}")
        (out/f'{name}-world-{stage}.scene').write_text(text)
        return text
    def state(page): return page.evaluate('__raceSupplement.state()')
    def audit(page): return page.evaluate('__raceSupplement.read()')
    def drawers_closed(page):
        if page.evaluate("document.body.classList.contains('drawer-left-open')||document.body.classList.contains('drawer-right-open')"):
            page.keyboard.press('Escape')
            wait(page,"!document.body.classList.contains('drawer-left-open')&&!document.body.classList.contains('drawer-right-open')")
    def drawer(page, side, face=False):
        if page.viewport_size['width']>900:return
        if page.evaluate('(s)=>document.body.classList.contains("drawer-"+s+"-open")',side):return
        drawers_closed(page)
        trigger=('#workspaceToggle' if face else '#toggle')+side.title()
        if side=='right' and not face and not page.locator(trigger).is_visible() and page.locator('#inspectorContent').is_visible():return
        click(page,trigger)
        wait(page,f'document.body.classList.contains("drawer-{side}-open")')
    def fixture(page):
        lines=['surface 731 origin 0 0 2500 u +x v +y outline '+A_INITIAL.split(' outline ',1)[1],
            'surface 732 origin 0 0 2500 u +x v +y outline '+B_INITIAL.split(' outline ',1)[1],
            'canvas-pos boundary 731 30 30','canvas-pos boundary 732 310 30']
        result=bounded(page,'''async lines=>{const replies=[await api('reset')];for(const line of lines)replies.push(await api('line '+line));await renderObjects();return replies;}''',lines)
        assert all(r.get('ok') is True for r in result),result
        wait(page,"connection.phase==='ready'&&!oc.busy&&oc.faces.length===2")
        return {'commands':lines,'replies':result,'setupIsApi':True}
    def enter_three(page, bid, chosen_tool='edit'):
        drawers_closed(page)
        if page.evaluate('oc.focus!==null'):
            click(page,'#workspaceBackButton');wait(page,"oc.focus===null&&oc.edit===null")
        if not page.evaluate('view3'):
            click(page,'#btnObj');wait(page,"view3&&workSurfaces.length===2&&!!layout")
        drawer(page,'left')
        click(page,'#workSurf');page.keyboard.press('Home')
        if bid==732:page.keyboard.press('ArrowDown')
        page.keyboard.press('Enter')
        wait(page,f'document.querySelector("#workSurf").value==="{bid}"')
        drawers_closed(page)
        click(page,f'[data-v3-tool="{chosen_tool}"]')
        if chosen_tool=='edit':
            wait(page,f"editBid==={bid}&&editDrag===null&&__raceSupplement.draws.some(x=>x.bid==={bid}&&x.token===editToken&&x.phase==='settled')&&__raceSupplement.draws.every(x=>x.phase==='settled')")
        else:wait(page,f'tool==="{chosen_tool}"&&rectStart===null')
    def vertex_point(page):
        handle=page.locator('#world circle[fill="#c0392b"]').first
        handle.wait_for(state='visible',timeout=15000);box=handle.bounding_box();assert box, 'No visible vertex box'
        point={'x':box['x']+box['width']/2,'y':box['y']+box['height']/2}
        usable=page.evaluate('''p=>{const hit=document.elementFromPoint(p.x,p.y);return {canvas:!!hit&&cv.contains(hit),inViewport:p.x>=0&&p.y>=0&&p.x<innerWidth&&p.y<innerHeight,v:screenToView(p.x,p.y)?.v};}''',point)
        assert usable['canvas'] and usable['inViewport'] and usable['v']==2,usable
        return point
    def native_point(page, bid, u, v):
        # Native projection determines the intended integer coordinates. DOM CTM
        # converts that native result to a trusted pointer location; no JS edit
        # function or production unmap function supplies the expected geometry.
        return bounded(page,'''async arg=>{const r=await api(`proj 2 ${arg.u} ${arg.v} ${arg.bid}`);if(!r.ok)throw Error(JSON.stringify(r));const view=layout.views[2];const p=new DOMPoint(r.x+view.tx,r.y+view.ty).matrixTransform(world.getScreenCTM());const hit=document.elementFromPoint(p.x,p.y);if(!hit||!cv.contains(hit)||p.x<0||p.y<0||p.x>=innerWidth||p.y>=innerHeight)throw Error('Native target is not an unobstructed canvas point');return {x:p.x,y:p.y,native:r,u:arg.u,v:arg.v,bid:arg.bid};}''',{'bid':bid,'u':u,'v':v})
    def down(page, point):
        old=page.evaluate('__raceSupplement.downs.length');page.mouse.move(point['x'],point['y']);page.mouse.down(button='left');return old
    def completed_down(page, old):wait(page,f"__raceSupplement.downs.length==={old+1}&&__raceSupplement.downs[{old}].phase==='settled'&&__raceSupplement.moves.every(x=>x.phase==='settled')")
    def completed_up(page):wait(page,"__raceSupplement.ups.length>0&&__raceSupplement.ups.every(x=>x.phase==='settled')")
    def release(page):
        page.evaluate('__raceSupplement.gate.release()')
        wait(page,"__raceSupplement.gate.phase==='released'&&__raceSupplement.downs.every(x=>x.phase==='settled')&&__raceSupplement.moves.every(x=>x.phase==='settled')&&__raceSupplement.ups.every(x=>x.phase==='settled')&&__raceSupplement.changes.every(x=>x.phase==='settled')&&__raceSupplement.draws.every(x=>x.phase==='settled')")
    def complete_B(page, name, before, kind, second=False):
        target=native_point(page,732,300 if second else 200,200 if second else 100) if kind=='drag' else native_point(page,732,400,400)
        old_moves=page.evaluate('__raceSupplement.moves.length')
        page.mouse.move(target['x'],target['y'])
        wait(page,f"__raceSupplement.moves.length>{old_moves}&&__raceSupplement.moves.every(x=>x.phase==='settled')")
        active=state(page)
        if kind=='drag':
            expected_vertices=[[300,200],[4000,200],[4000,3000],[300,3000]] if second else [[200,100],[4000,100],[4000,3000],[200,3000]]
            assert active['editDrag']['loops'][0]['verts']==expected_vertices,active
        else:assert active['rectStart']=={'u':100,'v':100},active
        draft_dump=dump(page,name,'B-live-after-move');assert draft_dump==before,'B preview prematurely mutated World'
        page.mouse.up(button='left');completed_up(page)
        wait(page,"__raceSupplement.draws.every(x=>x.phase==='settled')")
        after=dump(page,name,'B-finished')
        replacement=(B_NEXT_DRAG if second else B_DRAG) if kind=='drag' else B_HOLE
        previous=B_DRAG if second else B_INITIAL
        assert before.splitlines().count(previous)==1,'No unique fixed B line before completion'
        expected=before.replace(previous,replacement,1)
        (out/f'{name}-world-B-finished-expected.scene').write_text(expected)
        assert after==expected,'B completion did not make only the fixed intended geometry change'
        assert state(page)['editDrag'] is None and state(page)['rectStart'] is None,state(page)
        return {'target':target,'draftState':active,'worldUnchangedUntilUp':True,'exactBWorld':True}
    def held_bhit(page,name,active_B):
        setup=fixture(page);enter_three(page,731)
        original=dump(page,name,'before');point=vertex_point(page)
        page.evaluate("__raceSupplement.arm('bhit',731)");index=down(page,point)
        wait(page,"__raceSupplement.gate.phase==='held'&&__raceSupplement.downs[0].phase==='running'")
        native=page.evaluate('__raceSupplement.gate.nativeReply');assert native.get('ok') is True,native
        page.mouse.up(button='left');completed_up(page)
        assert state(page)['editDrag'] is None
        if active_B:
            click(page,'[data-v3-tool="view"]');enter_three(page,732)
            bpoint=vertex_point(page);bindex=down(page,bpoint);completed_down(page,bindex)
            assert state(page)['editDrag'] is not None and state(page)['editBid']==732,state(page)
        before=state(page);before_dump=dump(page,name,'before-release')
        page.screenshot(path=str(out/(name+'-before-release.png')))
        release(page);after=state(page);after_dump=dump(page,name,'released')
        assert before==after,'Stale A bhit changed the current gesture/editor/presentation'
        assert before_dump==original and after_dump==original,'Read-only bhit changed World'
        completion=complete_B(page,name,original,'drag') if active_B else None
        observed=audit(page)
        assert observed['downs'][index]['trusted'] and observed['ups'][0]['trusted'],observed
        if active_B:assert observed['downs'][bindex]['trusted'] and observed['ups'][-1]['trusted'],observed
        return {'ok':True,'fixture':setup,'heldNativeReply':native,'before':before,'after':after,'exactWorldUnchangedAtRelease':True,'BCompletion':completion,'audit':observed}
    def cancellation(page,name,mode):
        setup=fixture(page);enter_three(page,731)
        original=dump(page,name,'before');point=vertex_point(page)
        page.evaluate("__raceSupplement.arm('bhit',731)")
        if mode=='pointercancel':
            # CDP generates genuine UA touch/pointer events. No dispatchEvent.
            session=page.context.new_cdp_session(page)
            session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':point['x'],'y':point['y'],'radiusX':1,'radiusY':1,'id':0}]})
        else:down(page,point)
        wait(page,"__raceSupplement.gate.phase==='held'&&__raceSupplement.downs[0].phase==='running'")
        native=page.evaluate('__raceSupplement.gate.nativeReply');assert native.get('ok') is True,native
        if mode=='pointercancel':
            session.send('Input.dispatchTouchEvent',{'type':'touchCancel','touchPoints':[]})
            wait(page,"__raceSupplement.events.some(e=>e.type==='pointercancel'&&e.trusted)")
        else:
            # Explicit capture-loss injection through the native DOM API; the
            # subsequent real mouse move makes the UA emit lostpointercapture.
            pointer=page.evaluate('__raceSupplement.downs[0].pointerId')
            assert page.evaluate('(id)=>cv.hasPointerCapture(id)',pointer),'Canvas did not actually own pointer capture'
            page.evaluate('(id)=>cv.releasePointerCapture(id)',pointer)
            page.mouse.move(point['x']+1,point['y']+1)
            wait(page,"__raceSupplement.events.some(e=>e.type==='lostpointercapture'&&e.trusted)")
            wait(page,"__raceSupplement.moves.every(x=>x.phase==='settled')")
        before=state(page);assert before['editDrag'] is None and before['rectStart'] is None,before
        release(page);after=state(page)
        assert before==after,'Cancelled pending A hit revived drag or changed presentation'
        assert dump(page,name,'released')==original,'Cancellation changed World'
        if mode=='lostcapture':page.mouse.up(button='left');completed_up(page)
        observed=audit(page)
        assert observed['downs'][0]['trusted'],observed
        return {'ok':True,'fixture':setup,'before':before,'after':after,'heldNativeReply':native,'exactWorldUnchanged':True,
            'cancellationOrigin':'UA touchCancel from CDP' if mode=='pointercancel' else 'Explicit DOM capture-release plus real trusted mouse move',
            'audit':observed}
    def old_up_new_gesture(page,name):
        setup=fixture(page);enter_three(page,732)
        original=dump(page,name,'before');point=vertex_point(page)
        index=down(page,point);completed_down(page,index)
        target=native_point(page,732,200,100);old_moves=page.evaluate('__raceSupplement.moves.length')
        page.mouse.move(target['x'],target['y'])
        wait(page,f"__raceSupplement.moves.length>{old_moves}&&__raceSupplement.moves.every(x=>x.phase==='settled')")
        assert state(page)['editDrag']['loops'][0]['verts']==[[200,100],[4000,100],[4000,3000],[200,3000]]
        page.evaluate("__raceSupplement.arm('up-boundary',732)")
        page.mouse.up(button='left')
        wait(page,"__raceSupplement.gate.phase==='held'&&__raceSupplement.ups.length===1&&__raceSupplement.ups[0].phase==='running'&&editDrag===null")
        native=page.evaluate('__raceSupplement.gate.nativeReply');assert native.get('ok') is True and not native.get('preview'),native
        expected=original.replace(B_INITIAL,B_DRAG,1)
        (out/f'{name}-world-first-B-expected.scene').write_text(expected)
        assert dump(page,name,'old-up-held')==expected,'First B native commit differs from fixed geometry'
        new_point=vertex_point(page);new_index=down(page,new_point);completed_down(page,new_index)
        before=state(page);assert before['editDrag'] is not None and before['editBid']==732,before
        release(page);after=state(page)
        assert before==after,'Old pointer-up completion changed the later same-editor gesture'
        assert dump(page,name,'old-up-released')==expected
        completion=complete_B(page,name,expected,'drag',second=True)
        observed=audit(page)
        assert len(observed['downs'])==2 and all(r['trusted'] for r in observed['downs']),observed
        assert len(observed['ups'])==2 and all(r['trusted'] and r['phase']=='settled' for r in observed['ups']),observed
        return {'ok':True,'fixture':setup,'beforeNewGesture':before,'afterOldUp':after,'exactFirstBWorld':True,'BCompletion':completion,'audit':observed}
    def cross_B(page,name,scope,kind):
        setup=fixture(page)
        drawer(page,'left');click(page,'.object-row[data-kind="boundary"][data-id="731"]');drawers_closed(page);drawer(page,'right')
        if scope=='face':
            click(page,'#inspEnter');wait(page,"oc.edit?.bid===731&&oc.focus?.t==='face'");drawer(page,'right',True);click(page,'#faceInspectorTabs [data-fi-tab="prop"]')
        selector='#edgeLength0' if scope=='face' else '#mainEdgeLength0'
        page.locator(selector).wait_for(state='visible',timeout=15000)
        original=dump(page,name,'before');assert original.splitlines().count(A_INITIAL)==1
        expected_A=original.replace(A_INITIAL,A_EXPECTED,1)
        (out/f'{name}-world-A-expected.scene').write_text(expected_A)
        page.evaluate("__raceSupplement.arm('boundary',731)")
        click(page,selector);page.keyboard.press('Control+A');page.keyboard.insert_text('4200');page.keyboard.press('Tab')
        wait(page,"__raceSupplement.gate.phase==='held'");native=page.evaluate('__raceSupplement.gate.nativeReply')
        assert native.get('ok') is True and not native.get('preview'),native
        assert dump(page,name,'A-held')==expected_A,'A native response did not match fixed exact World'
        enter_three(page,732,'edit' if kind=='drag' else 'hole')
        point=vertex_point(page) if kind=='drag' else native_point(page,732,100,100)
        index=down(page,point);completed_down(page,index)
        before=state(page)
        if kind=='drag':assert before['editDrag'] is not None and before['editBid']==732,before
        else:assert before['rectStart']=={'u':100,'v':100} and before['tool']=='hole',before
        assert dump(page,name,'B-live')==expected_A
        page.screenshot(path=str(out/(name+'-B-live.png')))
        release(page);after=state(page)
        assert before==after,'A late successful submission changed B live work'
        assert dump(page,name,'A-released')==expected_A,'A release changed native World'
        completion=complete_B(page,name,expected_A,kind)
        observed=audit(page)
        assert len(observed['changes'])==1 and observed['changes'][0]['trusted'] and observed['changes'][0]['value']=='4200' and observed['changes'][0]['phase']=='settled',observed
        assert observed['gate']['command']=='line '+A_EXPECTED,observed
        assert observed['downs'][index]['trusted'] and observed['ups'][-1]['trusted'],observed
        return {'ok':True,'scope':scope,'BWork':kind,'fixture':setup,'heldNativeReply':native,'beforeB':before,'afterB':after,'BCompletion':completion,'exactAWorld':True,'audit':observed}
    def zoom(page,name):
        setup=fixture(page);page.keyboard.press('f');click(page,'#zoomInButton')
        card=page.locator('.ocard[data-kind="boundary"][data-id="731"]')
        box=card.bounding_box();assert box,'No visible card after trusted fit/zoom'
        # Choose rendered header space; no forced click or synthesized selection.
        point={'x':box['x']+box['width']*0.25,'y':box['y']+min(18,box['height']*0.1)}
        usable=page.evaluate('p=>!!document.elementFromPoint(p.x,p.y)?.closest(".ocard[data-id=\"731\"]")',point)
        assert usable,'Card target is obstructed'
        page.mouse.click(point['x'],point['y']);wait(page,"oc.sel?.id===731&&oc.sel.kind==='boundary'&&oc.focus===null")
        assert page.evaluate('ocCardClick!==null'),'First card click was not eligible for double-click recognition'
        original=dump(page,name,'before-zoom')
        before=page.evaluate('({zoom:oc.zoom,panX:oc.panX,panY:oc.panY,focus:oc.focus,selection:structuredClone(oc.selection)})')
        expected=page.evaluate('''()=>{const r=ocv.getBoundingClientRect(),b=[-10,-10,610,290];const zoom=Math.min(r.width/((b[2]-b[0])*1.4),r.height/((b[3]-b[1])*1.4));return {zoom,panX:r.width/2-(b[0]+b[2])/2*zoom,panY:r.height/2-(b[1]+b[3])/2*zoom};}''')
        old=page.evaluate('__raceSupplement.events.length');click(page,'#btnZoom')
        after=page.evaluate('({zoom:oc.zoom,panX:oc.panX,panY:oc.panY,focus:oc.focus,selection:structuredClone(oc.selection),consumed:ocConsumedClick,opening:ocObjectOpening})')
        observed=audit(page);events=observed['events'][old:]
        assert len([e for e in events if e['type']=='click' and e['id']=='btnZoom' and e['trusted']])==1,events
        for key in ['zoom','panX','panY']:assert abs(after[key]-expected[key])<1e-7,(key,after,expected)
        assert any(abs(before[k]-after[k])>1e-7 for k in ['zoom','panX','panY']),'Normal zoom click was swallowed'
        assert after['focus'] is None and after['selection']==before['selection'] and after['consumed'] is None and not after['opening'],after
        assert dump(page,name,'after-zoom')==original,'Zoom mutated World'
        return {'ok':True,'fixture':setup,'before':before,'after':after,'expectedFit':expected,'normalTrustedSingleClick':True,'exactWorldUnchanged':True,'audit':observed}

    before=identity('before')
    assert all(c['exitCode']==0 for c in before['commands']),before
    assert before['commands'][1]['stdout']=='' and before['commands'][2]['stdout'].strip()==args.expected_head,before
    assert before['runtime'].get('fresh') is True,before['runtime']
    widths=args.width or [1400,390]
    modes=['same-edit-up','bhit-active-B','cross-B-drag','cross-B-hole','zoom','pointercancel','lostcapture','old-up-new-gesture'] if args.only=='all' else [args.only]
    cases=[(width,mode,scope) for width in widths for mode in modes for scope in (([args.scope] if args.scope else ['main','face']) if mode.startswith('cross-B') else [None])]
    exit_code=1
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,chromium_sandbox=True)
            save('browser.json',{'version':browser.version,'executable':'/usr/bin/chromium','executableSha256':sha('/usr/bin/chromium'),'sandbox':True,'launchArgumentsRequested':[]})
            try:
                for width,mode,scope in cases:
                    name=f'{mode}-{width}'+('-'+scope if scope else '')
                    row={'name':name,'width':width,'mode':mode,'scope':scope,'started':stamp()}
                    context=browser.new_context(viewport={'width':width,'height':900 if width>900 else 844},has_touch=mode=='pointercancel')
                    context.tracing.start(screenshots=True,snapshots=True,sources=True)
                    page=context.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
                    try:
                        response=page.goto(args.url,wait_until='domcontentloaded',timeout=30000)
                        assert response.status==200,response.status
                        wait(page,"typeof api==='function'&&connection.phase==='ready'")
                        page.evaluate((BASE/'browser_race_ownership_instrumentation.js').read_text())
                        if mode in ['same-edit-up','bhit-active-B']:row.update(held_bhit(page,name,mode=='bhit-active-B'))
                        elif mode.startswith('cross-B'):row.update(cross_B(page,name,scope,'drag' if mode=='cross-B-drag' else 'hole'))
                        elif mode in ['pointercancel','lostcapture']:row.update(cancellation(page,name,mode))
                        elif mode=='old-up-new-gesture':row.update(old_up_new_gesture(page,name))
                        else:row.update(zoom(page,name))
                        if errors:row['ok']=False
                    except Exception as error:
                        row.update(ok=False,error=str(error),traceback=traceback.format_exc(),preconditionOrHarnessError=None if isinstance(error,AssertionError) else str(error))
                        try:row.update(failureState=state(page),audit=audit(page));page.screenshot(path=str(out/(name+'-error.png')))
                        except Exception:row['captureError']=traceback.format_exc()
                    finally:
                        row.update(finished=stamp(),pageErrors=errors);records.append(row);save(name+'.json',row);save('results.json',records)
                        context.tracing.stop(path=str(out/(name+'-trace.zip')));context.close()
                    print(json.dumps({'name':name,'ok':row.get('ok'),'error':row.get('error')},ensure_ascii=False),flush=True)
            finally:browser.close()
        after=identity('after')
        assert before['commands']==after['commands'],'Checkout changed during supplementary probe'
        assert before['sourceSha256']==after['sourceSha256'] and before['scriptSha256']==after['scriptSha256'],'Executed source changed'
        for key in ['version','pid','session']:assert before['runtime'][key]==after['runtime'][key],('Runtime changed',key)
        exit_code=0 if len(records)==len(cases) and all(r.get('ok') is True for r in records) else 1
    finally:
        census={'expected':len(cases),'actual':len(records),'pass':sum(r.get('ok') is True for r in records),'fail':sum(r.get('ok') is not True for r in records)}
        files=[p for p in sorted(out.iterdir()) if p.is_file() and p.name!='receipt.json']
        save('receipt.json',{'schema':'geometry-takeover-race-supplement/1','argv':[sys.executable,*sys.argv],'exitCode':exit_code,'expectedHead':args.expected_head,
            'scope':'Supplemental synthetic native fixtures; same-edit pointer-up/cancel/capture loss; stale A bhit with B live gesture; held A edge success with B live drag/new hole draft; old pointer-up native commit with later same-editor gesture; normal zoom single-click. Capture loss explicitly injected through DOM API; touchCancel emitted through CDP as genuine UA events. Desktop and 390 viewport, not full CDP/Space, physical-device or IME acceptance.',
            'census':census,'results':'results.json','resultsSha256':sha(out/'results.json') if (out/'results.json').exists() else None,
            'artifacts':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in files]})
    return exit_code


if __name__=='__main__':sys.exit(main())
