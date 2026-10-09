"""Real native/normal pointer supplemental probe, never launches automatically.

Invoke only after root releases the exclusive browser slot on a frozen checkout.
"""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import traceback
from urllib.parse import urlsplit
from urllib.request import urlopen
from playwright.sync_api import sync_playwright

BASE=pathlib.Path(__file__).resolve().parent
A0='boundary 1 outline 0,0 4000,0 4000,3000 0,3000'
A1=A0+' hole 1000,1000 1400,1000 1400,1400 1000,1400'
B0='boundary 7 outline 0,0 4000,0 4000,3000 0,3000'
BV='boundary 7 outline 200,100 4000,100 4000,3000 200,3000'
BH=B0+' hole 500,500 800,500 800,800 500,800'
MODES=['normal-projection','held-A-B-vertex','held-A-B-hole','same-owner-multiselect','header-history']

def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def processes(ancestor):
    found={}
    for path in pathlib.Path('/proc').iterdir():
        if not path.name.isdecimal():continue
        try:
            stat=(path/'stat').read_text();parent=int(stat.rsplit(')',1)[1].split()[1])
            found[int(path.name)]=(parent,path)
        except (OSError,ValueError):pass
    descendants={ancestor}
    changed=True
    while changed:
        added={pid for pid,(parent,_)in found.items()if parent in descendants}-descendants
        changed=bool(added);descendants|=added
    rows=[]
    for pid in sorted(descendants):
        if pid not in found:continue
        parent,path=found[pid]
        try:
            exe=(path/'exe').resolve(strict=True);argv=(path/'cmdline').read_bytes().split(b'\0')
            rows.append({'pid':pid,'parent':parent,'exe':str(exe),'sha256':sha(exe),'argv':[v.decode(errors='replace')for v in argv if v]})
        except OSError:pass
    return rows

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=pathlib.Path,required=True);parser.add_argument('--url',required=True)
    parser.add_argument('--out',type=pathlib.Path,required=True);parser.add_argument('--expected-head',required=True)
    parser.add_argument('--only',choices=['all',*MODES],default='all');parser.add_argument('--width',type=int,choices=[1382,390])
    args=parser.parse_args();root=args.root.resolve();out=args.out.resolve()
    sys.path.insert(0,str(root/'tests'))
    import binaries
    parsed=urlsplit(args.url)
    assert parsed.scheme=='http'and parsed.hostname in['127.0.0.1','localhost']and parsed.port not in[None,8765]and parsed.path=='/'
    assert not any([parsed.query,parsed.fragment,parsed.username,parsed.password]);assert len(args.expected_head)==40
    assert not out.is_relative_to(root);out.mkdir(parents=True,exist_ok=False)
    def save(name,value):(out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    def cmd(argv):
        r=subprocess.run(argv,cwd=root,capture_output=True,text=True,timeout=10)
        assert r.returncode==0,(argv,r.stderr)
        return r.stdout
    def native_identity(name,variable):
        info=binaries.inspect_one(binaries.BY_NAME[name],pathlib.Path(os.environ[variable]))
        return {**info.as_dict(),'fingerprint':info.fingerprint,'sha256':sha(info.path),
                'sidecarSHA256':sha(info.path.with_name(info.path.name+binaries.SIDECAR_SUFFIX))}
    def identity(label):
        with urlopen(args.url+'runtime',timeout=10)as r:raw=r.read();runtime=json.loads(raw)
        (out/(label+'-runtime.raw.json')).write_bytes(raw)
        value={'at':stamp(),'pwd':cmd(['pwd']).strip(),'head':cmd(['git','rev-parse','HEAD']).strip(),'dirty':cmd(['git','status','--short']),'tree':cmd(['git','rev-parse','HEAD^{tree}']).strip(),
               'runtime':runtime,'runtimeSHA256':hashlib.sha256(raw).hexdigest(),
               'sources':{p:sha(root/p)for p in['geometry-web/app.js','geometry-web/app.css','geometry-web/index.html']},
               'scripts':{p:sha(BASE/p)for p in['projection_supplement.py','projection_instrumentation.js','fixture.json']},
               'executor':{'path':sys.executable,'resolved':str(pathlib.Path(sys.executable).resolve()),'sha256':sha(pathlib.Path(sys.executable).resolve()),'version':sys.version},
               'actualServiceProcesses':processes(runtime['pid']),
               'native':{name:native_identity(name,variable)for name,variable in [('bridge','GEOMETRY_TEST_BRIDGE'),('model-base','GEOMETRY_MODEL_BASE')]}}
        assert all(value['state']=='fresh'for value in value['native'].values()),value['native']
        bridge=value['native']['bridge']
        assert any(p['parent']==runtime['pid']and p['exe']==bridge['path']and p['sha256']==bridge['sha256']for p in value['actualServiceProcesses']),value['actualServiceProcesses']
        save(label+'.json',value);return value
    def wait(page,e):page.wait_for_function(e,timeout=15000)
    def bounded(page,e,arg=None):return page.evaluate('''async arg=>{let timer;try{return await Promise.race([('''+e+''')(arg),new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('60000 ms observation deadline')),60000);})]);}finally{clearTimeout(timer);}}''',arg)
    def dump(page,name,stage):
        value=bounded(page,"async()=>{const r=await api('dump');if(!r.ok)throw Error(JSON.stringify(r));return r.text;}")
        (out/f'{name}-world-{stage}.scene').write_text(value);return value
    def closed(page):
        if page.evaluate("document.body.classList.contains('drawer-left-open')||document.body.classList.contains('drawer-right-open')"):
            page.keyboard.press('Escape');wait(page,"!document.body.classList.contains('drawer-left-open')&&!document.body.classList.contains('drawer-right-open')")
    def drawer(page,side,face):
        trigger=('#workspaceToggle'if face else'#toggle')+side.title()
        if not page.locator(trigger).is_visible():return
        if page.evaluate('(s)=>document.body.classList.contains("drawer-"+s+"-open")',side):return
        closed(page);page.locator(trigger).click(timeout=7000)
        wait(page,f'document.body.classList.contains("drawer-{side}-open")')
    def enter(page,bid):
        if page.evaluate('!!oc.focus'):
            closed(page);page.locator('#workspaceBackButton').click(timeout=7000);wait(page,'oc.focus===null')
        drawer(page,'left',False)
        page.locator(f'.object-row[data-kind="boundary"][data-id="{bid}"]').click(timeout=7000);closed(page)
        if not page.locator('#inspEnter').is_visible():drawer(page,'right',False)
        page.locator('#inspEnter').click(timeout=7000)
        wait(page,f'oc.edit?.bid==={bid}&&!$("objectWorkspace").hidden&&__projectionSupplement.loads.every(c=>c.phase==="settled")')
    def shape(page):
        if not page.locator('#faceInspectorTabs [data-fi-tab="shape"]').is_visible():drawer(page,'right',True)
        page.locator('#faceInspectorTabs [data-fi-tab="shape"]').click(timeout=7000)
        wait(page,'fe.fiTab==="shape"')
    def point(page,u,v):
        p=page.evaluate('''([u,v])=>{const g=$('faceEditorRoot'),s=$('faceEditorSvg'),p=s.createSVGPoint();p.x=u;p.y=v;const q=p.matrixTransform(g.getScreenCTM());const h=document.elementFromPoint(q.x,q.y);return{x:q.x,y:q.y,inViewport:q.x>0&&q.y>0&&q.x<innerWidth&&q.y<innerHeight,canvas:!!h&&!!h.closest('#faceEditorViewport')};}''',[u,v])
        assert p['canvas']and p['inViewport'],p
        return p
    def settled(page):wait(page,'__projectionSupplement.apply.every(c=>c.phase==="settled")&&__projectionSupplement.loads.every(c=>c.phase==="settled")&&__projectionSupplement.downs.every(c=>c.phase==="settled")&&__projectionSupplement.ups.every(c=>c.phase==="settled")')
    def state(page):return page.evaluate('__projectionSupplement.state()')
    def fixed(before,old,new):
        assert before.splitlines().count(old)==1,'No unique exact fixture line'
        return before.replace(old,new,1)
    def finish_B(page,name,world,kind):
        target=point(page,800,800)if kind=='hole'else point(page,200,100)
        page.mouse.move(target['x'],target['y'],steps=3)
        wait(page,'fe.drag!==null')
        draft=state(page)
        if kind=='hole':assert draft['drag']=={'kind':'holeRect','x0':500,'y0':500,'x1':800,'y1':800},draft
        else:assert draft['work'][0]['verts']==[[200,100],[4000,100],[4000,3000],[200,3000]],draft
        assert dump(page,name,'B-preview')==world,'B preview prematurely wrote World'
        page.mouse.up();settled(page)
        wait(page,'fe.drag===null&&fe.work===null')
        expected=fixed(world,B0,BH if kind=='hole'else BV)
        (out/f'{name}-world-B-expected.scene').write_text(expected)
        assert dump(page,name,'B-finished')==expected,'B real completion differs from fixed exact geometry'
        return{'draft':draft,'exactBWorld':True}
    def run_case(page,name,mode):
        fixture=json.loads((BASE/'fixture.json').read_text())
        replies=bounded(page,'''async lines=>{const r=[await api('reset')];for(const line of lines)r.push(await api('line '+line));await renderObjects();return r;}''',fixture)
        assert all(r.get('ok')is True for r in replies),replies
        enter(page,1);shape(page)
        original=dump(page,name,'before')
        row={'fixtureCommands':fixture,'fixtureReplies':replies}
        if mode=='header-history':
            closed(page)
            layout=page.evaluate('''()=>{const rect=e=>{const r=e.getBoundingClientRect();return{left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height};},h=$('objectWorkspace').querySelector('.object-workspace-topbar'),a=h.querySelector('.workspace-history-tools');return{header:rect(h),history:rect(a),controls:[...a.querySelectorAll('button')].map(e=>{const r=e.getBoundingClientRect(),hit=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);return{id:e.id,...rect(e),usable:!!hit&&(hit===e||e.contains(hit))};}),actualParent:a.offsetParent?.className};}''')
            save(name+'-layout.json',layout)
            assert layout['history']['top']>=layout['header']['top']and layout['history']['bottom']<=layout['header']['bottom'],'History actions outside actual header'
            assert all(c['usable']and c['width']>=28 and c['height']>=28 for c in layout['controls']),layout
            assert dump(page,name,'after')==original
            return{**row,'layout':layout,'ok':True}
        if mode=='same-owner-multiselect':
            # A deliberately differs from all defaults: c1 off, b1 on, cut on.
            page.locator('#faceProjectionEditor .fe-ob-check[data-item-type="column"]').uncheck()
            page.locator('#faceProjectionEditor .fe-ob-check[data-item-type="beam"]').check()
            page.locator('#feCutStrip').check();before=page.evaluate('__projectionSupplement.form()');owner=page.evaluate('__projectionSupplement.state().editObject')
            closed(page);drawer(page,'left',True)
            page.locator('#faceLayerList [data-timber-id="10"] .grid-layer-open').click()
            page.locator('#faceLayerList [data-timber-id="11"] .grid-layer-open').click(modifiers=['Shift'])
            wait(page,'fe.timberSelection.size===2')
            # One ordinary left-layer click exits the same-owner multi-selection.
            page.locator('#faceLayerList [data-timber-id="10"] .grid-layer-open').click()
            wait(page,'fe.timberSelection.size===1');closed(page);shape(page)
            after=page.evaluate('__projectionSupplement.form()')
            assert page.evaluate('__projectionSupplement.state().editObject')==owner,'Fixture unexpectedly changed editor owner'
            save(name+'-forms.json',{'before':before,'after':after,'sameOwner':True})
            assert before==after,'Same-owner timber multi-selection discarded Shape projection draft'
            assert dump(page,name,'after')==original,'Draft navigation wrote World'
            return{**row,'before':before,'after':after,'ok':True}
        assert page.locator('#faceProjectionEditor .fe-ob-check[data-item-type="column"]').is_checked()
        assert not page.locator('#faceProjectionEditor .fe-ob-check[data-item-type="beam"]').is_checked()
        expected_A=fixed(original,A0,A1);(out/f'{name}-world-A-expected.scene').write_text(expected_A)
        page.evaluate('__projectionSupplement.arm("line apply-proj 1 c1")')
        page.locator('#feApplyProj').click(timeout=7000)
        wait(page,'__projectionSupplement.gate.phase==="held"')
        native=page.evaluate('__projectionSupplement.gate.nativeReply');assert native.get('ok')is True and not native.get('preview'),native
        assert dump(page,name,'A-held')==expected_A,'A actual native projection differs from exact fixed World'
        if mode=='normal-projection':
            page.evaluate('__projectionSupplement.gate.release()');settled(page)
            assert dump(page,name,'after')==expected_A
            assert page.evaluate('oc.bmap[1].length===2&&oc.edit.bid===1'),'Native projection success not rendered in same owner'
            return{**row,'nativeReply':native,'ok':True}
        kind='hole'if mode.endswith('hole')else'vertex'
        enter(page,7);closed(page)
        page.locator('[data-face-tool="'+('hole'if kind=='hole'else'select')+'"]').click(timeout=7000)
        start=point(page,500,500)if kind=='hole'else point(page,0,0)
        page.mouse.move(start['x'],start['y']);page.mouse.down()
        wait(page,'fe.drag!==null&&oc.edit.bid===7')
        before=state(page);assert before['drag']['kind']==('holeRect'if kind=='hole'else'vertex'),before
        assert dump(page,name,'B-live')==expected_A
        page.screenshot(path=str(out/(name+'-B-live.png')))
        page.evaluate('__projectionSupplement.gate.release()');settled(page)
        after=state(page);save(name+'-owners.json',{'before':before,'after':after})
        assert before==after,'A late successful apply-proj changed B live gesture/model/owner/DOM'
        assert dump(page,name,'A-released')==expected_A,'A release wrote native World again'
        completion=finish_B(page,name,expected_A,kind)
        return{**row,'nativeReply':native,'before':before,'after':after,'BCompletion':completion,'ok':True}
    before=identity('before');assert before['head']==args.expected_head and before['dirty']=='',before
    assert before['runtime']['fresh']is True and pathlib.Path(before['runtime']['root']).resolve()==root,before
    records=[];fatal=None;cases=[(w,m)for w in([args.width]if args.width else[1382,390])for m in([args.only]if args.only!='all'else MODES)]
    try:
        with sync_playwright()as pw:
            browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,chromium_sandbox=True)
            browser_processes=processes(os.getpid())
            assert any('chromium' in p['exe']and not any(a.startswith('--type=')for a in p['argv'])for p in browser_processes),browser_processes
            save('browser.json',{'version':browser.version,'launcherPath':'/usr/bin/chromium','launcherSHA256':sha('/usr/bin/chromium'),'sandbox':True,'actualOwnedProcesses':browser_processes})
            try:
                for width,mode in cases:
                    name=f'{mode}-{width}';row={'name':name,'width':width,'mode':mode,'started':stamp(),'ok':False};errors=[]
                    ctx=browser.new_context(viewport={'width':width,'height':844 if width==390 else 804})
                    page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)));ctx.tracing.start(screenshots=True,snapshots=True,sources=True)
                    try:
                        response=page.goto(args.url,wait_until='domcontentloaded',timeout=30000);assert response.status==200
                        wait(page,"typeof feApplyProj==='function'&&connection.phase==='ready'")
                        page.evaluate((BASE/'projection_instrumentation.js').read_text())
                        row.update(run_case(page,name,mode));row['audit']=page.evaluate('__projectionSupplement.read()')
                        assert not errors,errors
                        assert all(e['trusted']for e in row['audit']['events']),row['audit']['events']
                        assert len([e for e in row['audit']['events']if e['type']=='click'and e['id']=='feApplyProj'])==(1 if mode in['normal-projection','held-A-B-hole','held-A-B-vertex']else 0)
                    except Exception as e:
                        row.update(ok=False,error=str(e),traceback=traceback.format_exc(),harnessError=None if isinstance(e,AssertionError)else str(e))
                        try:row['audit']=page.evaluate('__projectionSupplement.read()');page.screenshot(path=str(out/(name+'-failed.png')))
                        except Exception as capture:row['captureError']=str(capture)
                    finally:
                        row.update(finished=stamp(),pageErrors=errors);save(name+'.json',row);records.append(row)
                        ctx.tracing.stop(path=str(out/(name+'-trace.zip')));ctx.close()
                    print(('PASS 'if row['ok']else'FAIL ')+name,flush=True)
            finally:browser.close()
    except Exception as e:fatal={'error':str(e),'traceback':traceback.format_exc()}
    after=identity('after');save('results.json',records)
    unchanged=all(before[k]==after[k]for k in['head','dirty','tree','sources','scripts'])and all(before['runtime'][k]==after['runtime'][k]for k in['pid','session','version'])
    passed=sum(r['ok']is True for r in records);completed=len(records)==len(cases)and fatal is None and unchanged;exit_code=0 if completed and passed==len(cases)else 1
    save('receipt.json',{'actor':'/root/race_review','argv':[sys.executable,*sys.argv],'exitCode':exit_code,'completed':completed,'pass':passed,'fail':len(records)-passed,'expected':len(cases),'scope':'Supplemental actual native Shape projection ownership/draft/header checks; not full CDP, Windows, golden or complete #123. API fixtures explicitly recorded, then normal trusted UI; no force click or UI retry.','before':before,'after':after,'fatal':fatal,'caseNames':[r['name']for r in records]})
    print(json.dumps({'completed':completed,'passed':passed,'failed':len(records)-passed,'exitCode':exit_code,'out':str(out)}),flush=True);return exit_code

if __name__=='__main__':sys.exit(main())
