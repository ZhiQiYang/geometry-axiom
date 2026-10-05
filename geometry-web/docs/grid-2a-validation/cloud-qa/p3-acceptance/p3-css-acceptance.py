from pathlib import Path
from playwright.sync_api import sync_playwright
from urllib.request import urlopen
import hashlib, itertools, json, os, subprocess, traceback

ROOT=Path('/workspace/pr130-fix')
OUT=Path(os.environ.get('QA_OUT','/tmp/pr130-qa-e06ff2a/p3-acceptance')); OUT.mkdir(exist_ok=True)
SETTLED=os.environ.get('QA_SETTLED_INPUT')=='1'
URL='http://127.0.0.1:8806/'
HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
records=[]; cases=[]; errors=[]; console=[]
def check(label, ok, detail=None):
    records.append({'label':label,'pass':bool(ok),'detail':detail})
    print(('PASS ' if ok else 'FAIL ')+label,flush=True)
def dump(page):return page.evaluate("async()=>(await apiRequest('dump')).text")
def ready(page):page.wait_for_function("InfiniteGridWorkspace.isOpen && $('igName') && !$('igName').disabled")
def top(page):page.locator('#igName').scroll_into_view_if_needed()
def metrics(page):
    return page.evaluate("""()=>{const stage=$('igDefStage'),s=stage.getBoundingClientRect();return {stage:{x:s.x,y:s.y,width:s.width,height:s.height},chips:[...stage.querySelectorAll('[data-ig-chip]')].map(n=>{const r=n.getBoundingClientRect(),c=getComputedStyle(n);return {key:n.dataset.igChip,text:n.textContent,direct:n.parentElement===stage,position:c.position,left:n.style.left,top:n.style.top,rect:{x:r.x,y:r.y,width:r.width,height:r.height},offset:[r.x-s.x,r.y-s.y]};}),wide:document.documentElement.scrollWidth>innerWidth,empty:stage.querySelector('.ig-def-empty')?.textContent||null};}""")
def setup(page):
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('console',lambda m:console.append({'type':m.type,'text':m.text}) if m.type in ['warning','error'] else None)
    page.on('dialog',lambda d:d.accept())
    page.goto(URL);page.wait_for_function("connection.phase==='ready'")
def select_mode(page,axis,mode):
    p='ig'+axis.upper()
    page.locator('#'+p+'Source input[value="'+mode+'"]').check()
    fields=[('Step','1830' if axis=='u' else '400'),('Phase','120' if axis=='u' else '-50')] if mode=='repeat' else [('Panel','400'),('Gap','5'),('Anchor','-100')] if mode=='repeat-panel' else []
    for suffix,value in fields:
        page.locator('#'+p+suffix+'Source').select_option('')
        page.locator('#'+p+suffix).fill(value)

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    try:
        context=browser.new_context(viewport={'width':1400,'height':1000})
        page=context.new_page();setup(page)
        page.locator('#btnCreateObject').click();page.locator('#btnQuickGrid').click();ready(page)
        if page.locator('#paramGridLessonClose').is_visible():page.locator('#paramGridLessonClose').click()
        page.locator('#igName').fill('QA P3 chip positions')
        page.locator('#igUStep').fill('1830');page.locator('#igVStep').fill('400')
        page.locator('#igSaveSource').click();page.wait_for_selector('dialog.reference-impact[open]')
        page.locator('#impact-confirm').click();page.wait_for_function("!oc.busy && !ReferenceWorkspace.busy && !document.querySelector('dialog.reference-impact[open]')")
        ready(page);baseline=dump(page)
        gid=page.evaluate("oc.gridSystems.find(g=>g.name==='QA P3 chip positions').id")
        check('actual preview/confirm provides a nonempty native baseline','grid-system ' in baseline,{'sha256':hashlib.sha256(baseline.encode()).hexdigest(),'gridId':gid})
        page.locator('#igClose').click();page.wait_for_function('!InfiniteGridWorkspace.isOpen');context.close()
        for width,height,touch in [(1400,1000,False),(390,844,True)]:
            context=browser.new_context(viewport={'width':width,'height':height},is_mobile=touch,has_touch=touch)
            page=context.new_page();setup(page)
            check(f'{width} page identity / meaningful app / no error overlay',page.url==URL and bool(page.title()) and page.locator('#btnUndo').count()==1 and page.locator('vite-error-overlay,nextjs-portal').count()==0,{'title':page.title(),'url':page.url,'touch':touch})
            row=page.locator(f'.object-row[data-kind="grid-system"][data-id="{gid}"]')
            if not row.is_visible():page.locator('#toggleLeft').click()
            row.dblclick();ready(page)
            if SETTLED and page.locator('#paramGridLessonClose').is_visible():page.locator('#paramGridLessonClose').click()
            for um,vm in itertools.product(['repeat','repeat-panel','none'],repeat=2):
                name=f'{width}-{um}-{vm}'; select_mode(page,'u',um);select_mode(page,'v',vm)
                # Separate bounded positioning test: finish input editing using
                # trusted Tab. The first-run failures and before/after first-
                # click reproduction are retained, not rewritten as passes.
                if SETTLED:page.keyboard.press('Tab')
                top(page)
                m=metrics(page);expected=[]
                for axis,mode in [('u',um),('v',vm)]:
                    if mode!='none':expected.extend([axis+(':panel' if mode=='repeat-panel' else ':step'),axis+(':anchor' if mode=='repeat-panel' else ':phase')])
                check(name+' visible chip set',sorted(c['key'] for c in m['chips'])==sorted(expected),m)
                check(name+' absolute dimensions / relative nested phases',all(c['position']==('absolute' if c['direct'] else 'relative') for c in m['chips']))
                check(name+' no horizontal overflow',not m['wide'])
                if not expected:check(name+' unsupported empty axes show explicit empty state',m['empty']=='至少設定一軸。')
                clicks=[]
                for key in expected:
                    top(page); c=next(c for c in metrics(page)['chips'] if c['key']==key);r=c['rect']
                    x,y=r['x']+r['width']/2,r['y']+r['height']/2
                    hit=page.evaluate('({x,y})=>document.elementFromPoint(x,y)?.closest("[data-ig-chip]")?.dataset.igChip',{'x':x,'y':y})
                    check(name+' center hit '+key,hit==key,{'point':[x,y],'hit':hit})
                    (page.touchscreen.tap if touch else page.mouse.click)(x,y)
                    axis,field=key.split(':');field='phase' if field=='phase' else field
                    focus=page.locator(f'.ig-axis[data-ig-axis="{axis}"] [data-ig-field="{field}"]').evaluate("n=>n.classList.contains('is-focus')")
                    chip=page.locator('[data-ig-chip="'+key+'"]')
                    check(name+' actual '+('touch' if touch else 'mouse')+' focus '+key,focus and chip.get_attribute('aria-pressed')=='true')
                    clicks.append({'key':key,'point':[x,y],'hit':hit,'fieldFocus':focus})
                    if touch:
                        top(page); c=next(c for c in metrics(page)['chips'] if c['key']==key);r=c['rect']
                        hx,hy=r['x']+r['width']/2,r['y']-5
                        haloHit=page.evaluate('({x,y})=>document.elementFromPoint(x,y)?.closest("[data-ig-chip]")?.dataset.igChip',{'x':hx,'y':hy})
                        check(name+' expanded touch hit '+key,haloHit==key,{'point':[hx,hy],'hit':haloHit})
                        if haloHit==key:
                            page.touchscreen.tap(hx,hy)
                            check(name+' expanded touch focus '+key,page.locator(f'.ig-axis[data-ig-axis="{axis}"] [data-ig-field="{field}"]').evaluate("n=>n.classList.contains('is-focus')"))
                top(page);final=metrics(page)
                for c in final['chips']:
                    if not c['direct']:continue
                    r=c['rect'];s=final['stage'];left=float(c['left'].removesuffix('px'));tt=float(c['top'].removesuffix('px'))
                    anchored=abs(r['x']+r['width']/2-(s['x']+1+left))<0.1
                    anchored=anchored and abs((r['y']+r['height']/2 if c['key'].startswith('v:') else r['y'])-(s['y']+1+tt))<0.1
                    check(name+' supplied stage coordinate applied '+c['key'],anchored,c)
                check(name+' entire saved native World unchanged',dump(page)==baseline)
                page.screenshot(path=str(OUT/(name+'.png')))
                cases.append({'name':name,'viewport':[width,height],'modes':[um,vm],'initial':m,'final':final,'clicks':clicks,'nativeUnchanged':dump(page)==baseline,'screenshot':name+'.png'})
            page.locator('#igClose').click();page.wait_for_function('!InfiniteGridWorkspace.isOpen');context.close()
    except Exception as e:
        errors.append('HARNESS: '+str(e));traceback.print_exc()
        try:page.screenshot(path=str(OUT/'harness-failure.png'))
        except Exception:pass
    finally:
        browser.close()
    runtime=json.load(urlopen(URL+'runtime'))
    result={'schema':'geometry-pr130-p3-css-acceptance/1','testedHead':HEAD,'runtime':runtime,'url':URL,'browser':'Chromium via Playwright; Browser plugin not available','inputEditingCompletedWithTrustedTab':SETTLED,'cases':cases,'checks':records,'passed':sum(r['pass'] for r in records),'failed':sum(not r['pass'] for r in records),'browserErrors':errors,'consoleWarningsErrors':console,'scope':'Draft mode switching, positioned chips, trusted center/touch-halo focus and saved native World equality; no new full-CDP/portable/provenance claim.'}
    (OUT/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['testedHead','runtime','passed','failed','browserErrors','consoleWarningsErrors']}),flush=True)
    raise SystemExit(1 if result['failed'] or errors or console or len(cases)!=18 else 0)
