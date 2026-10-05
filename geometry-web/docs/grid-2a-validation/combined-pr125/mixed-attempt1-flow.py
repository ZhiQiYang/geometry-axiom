from pathlib import Path
from urllib.request import urlopen
import hashlib, json, subprocess, traceback, zipfile
from playwright.sync_api import sync_playwright

ROOT = Path('/workspace/pr130-integration')
OUT = Path('/tmp/pr130-combined-20261004/mixed')
OUT.mkdir(exist_ok=True)
URL = 'http://127.0.0.1:8845/'
IDENTITY = json.loads((OUT.parent/'identity.json').read_text())
assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT).strip()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() == IDENTITY['testedHead']
runtime = json.load(urlopen(URL+'runtime'))
assert runtime['fresh'] and runtime['version'] == IDENTITY['services']['mixed']['runtime']['version']
records, errors, console, requests = [], [], [], []

def check(label, ok, detail=None):
    records.append({'label':label,'pass':bool(ok),'detail':detail})
    (OUT/'checks.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    print(('PASS ' if ok else 'FAIL ')+label,flush=True)
    assert ok, label

def js(page, body): return page.evaluate('async()=>{'+body+'}')
def dump(page): return js(page,"return (await apiRequest('dump')).text")
def settled(page): page.wait_for_function("!oc.busy && !ReferenceWorkspace.busy && !document.querySelector('dialog.reference-impact[open]')")
def ready(page): page.wait_for_function("InfiniteGridWorkspace.isOpen && $('igName') && !$('igName').disabled")
def state(page): return js(page,"return {native:(await apiRequest('dump')).text,project:ReferenceWorkspace.getProjectState(),model:ReferenceWorkspace.getModelOperationState(),raw:ReferenceWorkspace.readFeatureAttachment('grid-draft'),undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length};")
def shot(page, name): page.screenshot(path=str(OUT/(name+'.png')))
def setup(page):
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('console',lambda m:console.append({'type':m.type,'text':m.text}) if m.type in ['error','warning'] else None)
    page.on('dialog',lambda d:d.accept())
    page.on('request',lambda r:requests.append(json.loads(r.post_data)['cmd']) if r.url.endswith('/api') and r.post_data and 'cmd' in json.loads(r.post_data) else None)
    page.goto(URL)
    page.wait_for_function("connection.phase==='ready' && window.FaceContextMenu && window.InfiniteGridWorkspace")
def menu(page, target):
    page.locator('#mobileCreateObject' if page.locator('#mobileCreateObject').is_visible() else '#btnCreateObject').click()
    node = page.locator(target)
    if target == '#btnQuickGrid' and page.viewport_size['width'] == 390:
        box = node.bounding_box()
        hit = page.evaluate('(r)=>document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)?.id',box)
        if hit == 'fbButton':
            check('390 base feedback overlay documented; real unobscured lower edge used',True,{'centerHit':hit,'rect':box})
            node.click(position={'x':40,'y':box['height']-6})
            return
    node.click()
def library(page, kind, object_id):
    row = page.locator(f'.object-row[data-kind="{kind}"][data-id="{object_id}"]')
    if not row.is_visible(): page.locator('#toggleLeft').click()
    row.dblclick()
def open_grid(page, gid): library(page,'grid-system',gid); ready(page)
def close_grid(page): page.locator('#igClose').click(); page.wait_for_function('!InfiniteGridWorkspace.isOpen')
def preview(page): page.locator('#igSaveSource').click(); page.wait_for_selector('dialog.reference-impact[open]')
def confirm(page): page.locator('#impact-confirm').click(); settled(page); ready(page)
def cancel(page): page.locator('dialog.reference-impact[open] .impact-actions button').first.click(); settled(page)
def open_face(page):
    library(page,'boundary',1)
    page.wait_for_function("oc.focus?.t==='face' && oc.edit?.bid===1")
    page.locator('[data-face-tool="select"]').click()
    page.locator('#feZoomFit').click()
def leave_face(page):
    page.locator('#workspaceBackButton').click()
    page.wait_for_function('!oc.focus')
def right(page, u=4000, v=1000):
    point=page.evaluate('([u,v])=>{const r=$("faceEditorSvg").getBoundingClientRect();return {x:r.left+fe.panX+u*fe.zoom,y:r.top+fe.panY+v*fe.zoom};}',[u,v])
    page.mouse.click(point['x'],point['y'],button='right')
    page.locator('#feCtxMenu').wait_for(state='visible')
def notch(page, u=4000, v=1000, dist='900', width='1200', depth='600'):
    right(page,u,v)
    page.locator('#feCtxMenu [data-fe-act="op:notch"]').click()
    page.locator('#feOpPanel').wait_for(state='visible')
    page.locator('[data-fe-anchor="start"]').click()
    for key,value in [('dist',dist),('w',width),('d',depth)]: page.locator(f'#feOpPanel [data-fe-param="{key}"]').fill(value)

completed = False
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    try:
        for width,height in [(1400,1000),(390,844)]:
            prefix=str(width)
            context=browser.new_context(viewport={'width':width,'height':height},accept_downloads=True)
            context.add_init_script('window.showSaveFilePicker=undefined')
            page=context.new_page(); setup(page)
            check(prefix+' exact page identity, meaningful shell and no framework overlay',page.title()=='構形 Canvas · 工程規格與空間建模' and page.locator('#btnCanvasView').count()==1 and page.locator('vite-error-overlay,nextjs-portal').count()==0)
            # Synthetic isolated native fixture only; subsequent routes and transactions use real UI.
            js(page,"for(const cmd of ['reset','line surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000']){const r=await api(cmd);if(!r.ok)throw Error(r.error);}await renderObjects();")
            open_face(page); initial=dump(page); notch(page)
            check(prefix+' B numeric preview is correct and native read-only',js(page,'return feOpRect()')==[3400,900,4000,2100] and dump(page)==initial)
            shot(page,prefix+'-01-B-preview')
            page.locator('#feOpCancel').click()
            check(prefix+' B cancel preserves entire scene and retains menu',dump(page)==initial and page.locator('#feCtxMenu').is_visible())
            page.keyboard.press('Escape'); leave_face(page)
            check(prefix+' leaving B clears operation/menu before 2a',js(page,'return !fe.op && !FaceContextMenu.open && !oc.focus'))

            menu(page,'#btnNewParameter'); page.wait_for_selector('#paramQuick')
            if page.locator('#paramGridLessonClose').is_visible(): page.locator('#paramGridLessonClose').click()
            page.locator('#paramName').fill('Combined QA 915/1830')
            page.locator('#paramQuick').fill('(915,1830)'); page.locator('#paramParse').click()
            page.locator('#paramPreview').click(); page.wait_for_function("!ParameterUI.previewing && !$('paramConfirm').disabled")
            check(prefix+' parameter preview preserves existing face',dump(page)==initial)
            page.locator('#paramConfirm').click(); page.wait_for_function('!ParameterUI.pending')
            card=js(page,"return oc.parameters.find(p=>p.name==='Combined QA 915/1830').card")
            pid=card['id']; wid=next(f['id'] for f in card['fields'] if f['name']=='寬'); lid=next(f['id'] for f in card['fields'] if f['name']=='長')
            check(prefix+' real parameter card has 915 and 1830',[f['value']['num'] for f in card['fields']]==['915','1830'])
            if page.locator('#btnNewGridSystem').is_visible(): page.locator('#btnNewGridSystem').click()
            else: menu(page,'#btnQuickGrid')
            ready(page); page.locator('#igName').fill('Combined 2a grid')
            page.locator('#igUStepSource').select_option(f'{pid}:{lid}'); page.locator('#igVStepSource').select_option(f'{pid}:{wid}')
            page.wait_for_function("$('igUStep').value==='1830' && $('igVStep').value==='915'")
            page.locator('#igVPhase').fill('-50'); before_click=state(page)
            target=page.locator('[data-ig-chip="u:step"]'); target.evaluate("n=>n.scrollIntoView({block:'center'})")
            check(prefix+' input remains active before first chip click',js(page,"return document.activeElement.id==='igVPhase'"))
            target.click()
            check(prefix+' first chip click highlights u with raw/history/native unchanged',page.locator('.ig-axis[data-ig-axis="u"] [data-ig-field="step"]').evaluate("n=>n.classList.contains('is-focus')") and state(page)==before_click)
            page.locator('#igUHead').click()
            before_grid=dump(page); preview(page)
            check(prefix+' 2a preview preserves complete face plus parameter',dump(page)==before_grid)
            cancel(page)
            check(prefix+' 2a cancel retains refs and world',dump(page)==before_grid and page.locator('#igUStepSource').input_value()==f'{pid}:{lid}')
            preview(page); confirm(page)
            gid=js(page,"return oc.gridSystems.find(g=>g.name==='Combined 2a grid').id")
            check(prefix+' grid commits exact u/v parameter sources alongside face',f'u repeat 0 param:{pid}:{lid} v repeat -50 param:{pid}:{wid}' in dump(page) and 'placement 1 ' in dump(page))
            page.locator('[data-ig-add-stagger="u"]').click(); page.locator('#igUStaggerSource').select_option(f'{pid}:{wid}')
            page.wait_for_function("$('igUStagger').value==='915'"); preview(page); confirm(page)
            with_stagger=dump(page); close_grid(page); open_grid(page,gid)
            check(prefix+' phase source survives close/library reopen',page.locator('#igUStaggerSource').input_value()==f'{pid}:{wid}' and f'stagger param:{pid}:{wid}' in dump(page))
            page.locator('[data-ig-remove-stagger="u"]').click(); close_grid(page); open_grid(page,gid)
            check(prefix+' draft phase removal/reopen preserves saved source',dump(page)==with_stagger)
            preview(page); cancel(page)
            check(prefix+' canceled removal keeps saved phase source',dump(page)==with_stagger)
            preview(page); confirm(page)
            check(prefix+' confirmed removal preserves step source tokens','stagger ' not in dump(page) and f'param:{pid}:{lid}' in dump(page) and f'param:{pid}:{wid}' in dump(page))
            shot(page,prefix+'-02-2a-coexisting-face'); close_grid(page)

            open_face(page); before_notch=dump(page); notch(page)
            check(prefix+' B reopens after 2a and previews without changing grid or refs',dump(page)==before_notch and js(page,'return feOpRect()')==[3400,900,4000,2100])
            page.locator('#feOpApply').click(); page.wait_for_function('!fe.op && oc.bmap[1][0].verts.length===8')
            expected_vertices=[[0,0],[4000,0],[4000,900],[3400,900],[3400,2100],[4000,2100],[4000,3000],[0,3000]]
            after_notch=dump(page)
            check(prefix+' B confirm has exact notch vertices and preserves grid refs',js(page,'return oc.bmap[1][0].verts')==expected_vertices and f'param:{pid}:{lid}' in after_notch and f'param:{pid}:{wid}' in after_notch)
            page.locator('#faceUndoButton').click(); page.wait_for_function('oc.bmap[1][0].verts.length===4')
            check(prefix+' single B undo restores full world including grid',dump(page)==before_notch)
            page.locator('#faceRedoButton').click(); page.wait_for_function('oc.bmap[1][0].verts.length===8')
            check(prefix+' single B redo restores full combined world',dump(page)==after_notch)
            shot(page,prefix+'-03-B-confirmed-with-grid')
            with page.expect_download() as event: page.locator('[data-project-action="save"]:visible').click()
            archive=OUT/(prefix+'-combined.gcanvas'); event.value.save_as(archive)
            with zipfile.ZipFile(archive) as z:
                scene=z.read('world.scene').decode(); manifest=json.loads(z.read('manifest.json'))
                check(prefix+' actual Save yields real ZIP with both features exactly',scene==after_notch and manifest['format']=='geometry-canvas/6' and 'grid-system ' in scene and 'boundary 1 ' in scene,{'names':z.namelist(),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()})
            context.close()

            context=browser.new_context(viewport={'width':width,'height':height},accept_downloads=True)
            context.add_init_script('window.showSaveFilePicker=undefined')
            page=context.new_page(); setup(page)
            page.locator('#fileMenuBtn').click(); page.locator('#btnNewProject').click(); settled(page)
            page.wait_for_function('oc.gridSystems.length===0 && oc.parameters.length===0 && oc.objects.length===0')
            check(prefix+' fresh-context File New proves empty native before reopen',dump(page)=='')
            if not page.locator('#btnOpenProject').is_visible(): page.locator('#fileMenuBtn').click()
            with page.expect_file_chooser() as event: page.locator('#btnOpenProject').click()
            event.value.set_files(archive); settled(page); page.wait_for_function("oc.gridSystems.some(g=>g.name==='Combined 2a grid')")
            check(prefix+' actual chooser restores complete combined native byte-for-byte',dump(page)==scene)
            open_grid(page,gid)
            check(prefix+' reopened 2a keeps bound source identities and values',page.locator('#igUStepSource').input_value()==f'{pid}:{lid}' and page.locator('#igVStepSource').input_value()==f'{pid}:{wid}' and page.locator('#igUStep').input_value()=='1830' and not page.locator('#igUStagger').is_visible())
            page.locator('#igUPhase').fill('200'); before_edit=dump(page); preview(page)
            check(prefix+' reopened source preview preserves notched face and world',dump(page)==before_edit)
            cancel(page); check(prefix+' reopened source cancel preserves full world',dump(page)==before_edit)
            preview(page); confirm(page); after_edit=dump(page); close_grid(page)
            page.locator('#btnUndo').click(); settled(page)
            check(prefix+' grid undo after reopen restores complete combined saved world',dump(page)==scene)
            page.locator('#btnRedo').click(); settled(page)
            check(prefix+' grid redo after reopen restores exact source transaction and face',dump(page)==after_edit)
            open_face(page); notch(page,4000,2500,'100','400','200'); preview_native=dump(page)
            page.keyboard.press('Escape')
            check(prefix+' reopened B Escape cancels preview and preserves both features',dump(page)==preview_native and js(page,'return !fe.op && FaceContextMenu.open'))
            page.keyboard.press('Escape')
            check(prefix+' second B Escape closes only the menu',dump(page)==after_edit and js(page,'return !FaceContextMenu.open'))
            shot(page,prefix+'-04-reopened-final-face'); leave_face(page); open_grid(page,gid)
            shot(page,prefix+'-05-reopened-final-grid')
            check(prefix+' both workspaces retain unique control IDs',js(page,"return ['feCtxMenu','feOpPanel','igDefStage','igUHead','igVHead'].every(id=>document.querySelectorAll('#'+id).length===1)"))
            check(prefix+' final viewport has no horizontal document overflow',js(page,'return document.documentElement.scrollWidth<=innerWidth'))
            context.close()
        check('all mixed desktop/mobile page errors and warning/error console messages absent',not errors and not console,{'errors':errors,'console':console})
        completed=True
    except Exception as error:
        traceback.print_exc(); errors.append('HARNESS_OR_PRODUCT: '+str(error))
        try: shot(page,'failure')
        except Exception: pass
    finally:
        browser.close()
        (OUT/'result.json').write_text(json.dumps({'schema':'geometry-pr125-pr130-mixed-browser/1','head':IDENTITY['testedHead'],'tree':IDENTITY['testedTree'],'runtime':runtime,'completed':completed,'passed':sum(r['pass'] for r in records),'failed':sum(not r['pass'] for r in records),'errors':errors,'console':console,'requests':requests,'coverage':'Actual mouse/keyboard/UI/ZIP/chooser and history at desktop and 390px; synthetic native fixture setup only. No physical OS chooser/IME/phone claim.'},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'completed':completed,'passed':sum(r['pass'] for r in records),'failed':sum(not r['pass'] for r in records),'errors':errors,'console':console},ensure_ascii=False),flush=True)
raise SystemExit(not completed or any(not r['pass'] for r in records) or bool(errors) or bool(console))
