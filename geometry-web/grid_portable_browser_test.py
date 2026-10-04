"""Required manual #45 gate: actual Chromium, native service and complete ZIP.

Requires GEOMETRY_VERIFY_ROOT, GEOMETRY_TEST_URL and
GEOMETRY_GRID_PORTABLE_BROWSER_OUT (a dedicated directory below TEMP).
The service must be explicitly isolated: this gate resets its own scene.
Playwright file-input/download automation does not verify a physical OS chooser.
"""
import base64
import hashlib
import json
import os
import subprocess
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from playwright.sync_api import sync_playwright

root=Path(os.environ['GEOMETRY_VERIFY_ROOT']).resolve()
head=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
tree=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD^{tree}'],text=True).strip()
assert not subprocess.check_output(['git','-C',str(root),'status','--porcelain']).strip(),'Frozen worktree is dirty'
url=os.environ['GEOMETRY_TEST_URL']
address=urllib.parse.urlparse(url)
assert address.scheme=='http' and address.hostname=='127.0.0.1' and address.port not in (None,8765),'Explicit isolated loopback service required'
runtime=json.load(urllib.request.urlopen(urllib.parse.urljoin(url,'runtime')))
assert runtime['fresh'] and Path(runtime['root']).resolve()==root,'Service does not match frozen worktree'
out=Path(os.environ['GEOMETRY_GRID_PORTABLE_BROWSER_OUT']).resolve()
assert out!=Path(tempfile.gettempdir()).resolve() and out.is_relative_to(Path(tempfile.gettempdir()).resolve()),'Evidence must use a dedicated directory below TEMP'
out.mkdir(parents=True,exist_ok=True)
pdf=root/'tests/fixtures/issue77-two-rooms.pdf'  # self-authored repository fixture
pdf_bytes=pdf.read_bytes()
pdf_hash=hashlib.sha256(pdf_bytes).hexdigest()
checks=[]
errors=[]
def check(label,value):
    checks.append({'label':label,'pass':value is True})
    print(('PASS ' if value is True else 'FAIL ')+label,flush=True)
    assert value is True,label
def js(page,body):return page.evaluate('async()=>{'+body+'}')
def draft(page):return js(page,"return ReferenceWorkspace.readFeatureAttachment('grid-draft');")
def dump(page):return js(page,"return (await apiRequest('dump')).text;")
def settled(page):page.wait_for_function("!oc.busy && !ReferenceWorkspace.busy && !document.querySelector('dialog.reference-impact[open]')")
def ready_editor(page):page.wait_for_function("document.getElementById('igName') && !document.getElementById('igName').disabled && InfiniteGridWorkspace.isOpen")
def create_entry(page):
 if page.locator('#mobileCreateObject').is_visible():
  page.locator('#mobileCreateObject').click();page.locator('#btnQuickGrid').click()
 else:page.locator('#btnNewGridSystem').click()
def preview(page):
 try:page.wait_for_selector('dialog.reference-impact[open]',timeout=7000)
 except Exception:
  print('PREVIEW_FAILURE '+json.dumps(js(page,"return {status:$('igStatus')?.textContent,trace:window.rawStatusTrace,raw:ReferenceWorkspace.readFeatureAttachment('grid-draft'),busy:oc.busy,referenceBusy:ReferenceWorkspace.busy,sourceButton:$('igSaveSource')?.disabled,dialogClass:$('infiniteGridWorkspace')?.className,projectState:ReferenceWorkspace.getProjectState(),featurePending:ReferenceWorkspace.featureConfirmationPending()};"),ensure_ascii=False),flush=True)
  raise
def save_zip(page,width,label,delay=False):
    check(f'{width} {label} complete-project save enabled',not page.locator('#projectBar [data-project-action="save"]').is_disabled())
    if delay:
        before=dump(page);raw=draft(page);history=js(page,'return ReferenceWorkspace.history.undo.length;')
        js(page,"window.rawOriginalPack=GeometryProject.pack;window.rawSavedControl=$('igUStep');GeometryProject.pack=async(...args)=>{const bytes=await window.rawOriginalPack(...args);await new Promise(resolve=>window.rawReleasePack=resolve);return bytes;};")
    with page.expect_download() as info:
        page.locator('#projectBar [data-project-action="save"]').click()
        if delay:
            page.wait_for_function("typeof window.rawReleasePack==='function'")
            check(f'{width} save locks raw while actual ZIP delivery is delayed',page.locator('#igUStep').is_disabled() and js(page,'return ReferenceWorkspace.busy;') and draft(page)==raw)
            page.keyboard.press('Escape')
            check(f'{width} trusted Escape retains saving editor and raw',js(page,"return InfiniteGridWorkspace.isOpen && $('igUStep')===window.rawSavedControl;") and draft(page)==raw and page.locator('#igUStep').is_disabled())
            js(page,'await InfiniteGridWorkspace.create();')
            check(f'{width} ordinary reopen during save retains same locked owner',js(page,"return InfiniteGridWorkspace.isOpen && $('igUStep')===window.rawSavedControl;") and draft(page)==raw and page.locator('#igUStep').is_disabled())
            check(f'{width} saving owner race preserves native World and undo',dump(page)==before and js(page,'return ReferenceWorkspace.history.undo.length;')==history)
            js(page,'window.rawReleasePack();GeometryProject.pack=window.rawOriginalPack;delete window.rawOriginalPack;delete window.rawReleasePack;delete window.rawSavedControl;')
    file=out/f'{width}-{label}.gcanvas';info.value.save_as(file);settled(page)
    if delay:check(f'{width} finished save restores raw editing on same owner',not page.locator('#igUStep').is_disabled() and draft(page)==raw)
    with zipfile.ZipFile(file) as z:
        m=json.loads(z.read('manifest.json'))
        check(f'{width} {label} real ZIP native scene present','world.scene' in z.namelist())
        check(f'{width} {label} format10 and one grid raw record',m['format']=='geometry-canvas/10' and len(m['featureAttachments']['records'])==1)
        check(f'{width} {label} exact raw persisted',m['featureAttachments']['records'][0]['value']==draft(page))
        check(f'{width} {label} one original PDF source retained',len(m['sources'])==1 and m['sources'][0]['hash']==pdf_hash)
        check(f'{width} {label} original PDF bytes retained',z.read(m['sources'][0]['path'])==pdf_bytes)
    return file
def open_bytes(page,file):
    encoded=base64.b64encode(file.read_bytes()).decode()
    return page.evaluate("async encoded=>{return ReferenceWorkspace.importBytes(Uint8Array.from(atob(encoded),c=>c.charCodeAt(0)),'raw-check.gcanvas');}",encoded)

result={'schema':'geometry-grid-raw-browser/1','head':head,'tree':tree,'runtime':runtime,'root':str(root),'url':url,
 'coverage':'Actual Chromium app/native/full ZIP with trusted raw inputs and confirmation; public API setup/import/undo used. No physical IME/OS chooser claim.'}
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=os.environ.get('GEOMETRY_CHROME','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
  for width in (1280,390):
   context=browser.new_context(viewport={'width':width,'height':900},accept_downloads=True)
   page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(url);page.wait_for_function("connection.phase==='ready'")
   page.evaluate("window.showSaveFilePicker=undefined")
   check(f'{width} actual app shell',page.title()=='構形 Canvas · 工程規格與空間建模' and page.locator('#objectWorkspace').count()==1)
   js(page,"const r=await apiRequest('line reset');if(!r.ok)throw Error(r.error);await renderObjects();")
   js(page,"const r=await apiRequest('line boundary 1 outline 0,0 5000,0 5000,4000 0,4000');if(!r.ok)throw Error(r.error);await renderObjects();ReferenceWorkspace.chooseFile(1);")
   page.locator('#referenceFile').set_input_files(pdf)
   page.wait_for_function("!$('refApply').disabled")
   page.locator('#refTarget').select_option('1');page.locator('#refApply').click()
   page.wait_for_function("!$('referenceDialog').open && !ReferenceWorkspace.busy")
   js(page,"if(oc.focus)await leaveFocus();await renderObjects();")
   before=dump(page)
   create_entry(page);ready_editor(page)
   page.locator('#igUSource').select_option('repeat-panel');page.locator('#igUPanel').fill('not-a-panel');page.locator('#igUSource').select_option('repeat')
   for selector,value in {'igName':'  未完成網格  ','igUStep':'1e','igUPhase':'-','igVStep':' 00400 ','igUStagger':'  '}.items():
    page.locator('#'+selector).fill(value)
   raw=draft(page)
   check(f'{width} source captures incomplete/inactive/whitespace strings',raw['rawForm']['igUStep']=='1e' and raw['rawForm']['igUPhase']=='-' and raw['rawForm']['igName']=='  未完成網格  ' and raw['rawForm']['igUPanel']=='not-a-panel' and raw['rawForm']['igVStep']==' 00400 ')
   check(f'{width} source raw has no World side effect',dump(page)==before)
   page.locator('#igSaveSource').click();settled(page)
   check(f'{width} invalid raw refused before native preview',not page.locator('dialog.reference-impact[open]').count() and dump(page)==before and draft(page)==raw)
   archive=save_zip(page,width,'source',delay=True)
   page.locator('#igClose').click();page.wait_for_function('!InfiniteGridWorkspace.isOpen')
   check(f'{width} returning to canvas retains raw',draft(page)==raw)
   context.close()
   context=browser.new_context(viewport={'width':width,'height':900},accept_downloads=True)
   page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(url);page.wait_for_function("connection.phase==='ready'");page.evaluate("window.showSaveFilePicker=undefined")
   open_bytes(page,archive)
   check(f'{width} fresh browser import preserves raw exactly',draft(page)==raw)
   create_entry(page);ready_editor(page)
   check(f'{width} existing create entry resumes source raw',page.locator('#igUStep').input_value()=='1e' and page.locator('#igUPhase').input_value()=='-' and page.locator('#igName').input_value()=='  未完成網格  ')
   for selector,value in {'igName':'正式網格','igUStep':'600','igUPhase':'0','igUStagger':'','igVStep':'400','igVPhase':'0','igVStagger':''}.items():page.locator('#'+selector).fill(value)
   publish_raw=draft(page);native_before=dump(page);undo_before=js(page,'return ReferenceWorkspace.history.undo.length;')
   js(page,"window.rawStatusTrace=[];new MutationObserver(records=>{for(const r of records)if(r.target.id==='igDraftNote')for(const n of r.addedNodes)window.rawStatusTrace.push(n.textContent);}).observe($('igDraftNote'),{childList:true});")
   page.locator('#igSaveSource').click();preview(page)
   check(f'{width} true native preview preserves World and raw',dump(page)==native_before and draft(page)==publish_raw)
   page.locator('dialog.reference-impact[open] .impact-actions button:first-child').click();settled(page)
   check(f'{width} cancelling true preview retains raw and World',dump(page)==native_before and draft(page)==publish_raw and js(page,'return ReferenceWorkspace.history.undo.length;')==undo_before)
   page.locator('#igSaveSource').click();preview(page);page.locator('#impact-confirm').click();settled(page);ready_editor(page)
   native=js(page,"return (await apiRequest('objects')).gridSystems;")
   check(f'{width} native confirm publishes and clears matching raw together',len(native)==1 and native[0]['name']=='正式網格' and draft(page) is None and js(page,'return ReferenceWorkspace.history.undo.length;')==undo_before+1)
   source_id=native[0]['id']
   page.locator('#igClose').click();page.wait_for_function('!InfiniteGridWorkspace.isOpen')
   js(page,"const r=await apiRequest('line undo');if(!r.ok)throw Error(r.error);await renderObjects();")
   check(f'{width} one undo restores full raw and removes new source',draft(page)==publish_raw and len(js(page,"return (await apiRequest('objects')).gridSystems;"))==0)
   js(page,"const r=await apiRequest('line redo');if(!r.ok)throw Error(r.error);await renderObjects();")
   check(f'{width} one redo restores published source and clears raw',draft(page) is None and js(page,"return (await apiRequest('objects')).gridSystems;")==native)
   js(page,f'await InfiniteGridWorkspace.openSystem({source_id});');ready_editor(page)
   page.locator('#igNewBinding').click();page.wait_for_selector('#igBoundary');page.wait_for_function("!$('igBoundary').disabled")
   page.locator('#igBoundary').select_option('1');page.wait_for_selector('[data-ig-vertex="outer:0"]');page.locator('#igVertex').select_option('outer:0')
   page.locator('.ig-rational summary').click()
   page.locator('#igCellI').fill('-');page.locator('#igCellJ').fill(' 03 ');page.locator('#igAnchorUD').fill('0')
   binding_raw=draft(page);binding_world=dump(page)
   check(f'{width} binding captures exact incomplete strings and typed pins',binding_raw['kind']=='binding' and binding_raw['rawForm']['igCellI']=='-' and binding_raw['rawForm']['igCellJ']==' 03 ' and binding_raw['rawForm']['igAnchorUD']=='0' and {r['kind'] for r in binding_raw['inputRefs']}=={'grid-system','boundary'})
   page.locator('#igSaveBinding').click();settled(page)
   check(f'{width} incomplete binding cannot publish',dump(page)==binding_world and draft(page)==binding_raw and not page.locator('dialog.reference-impact[open]').count())
   archive=save_zip(page,width,'binding')
   page.locator('#igClose').click();page.wait_for_function('!InfiniteGridWorkspace.isOpen');open_bytes(page,archive)
   # Hold an actual native boundary response during restoration. No fake
   # geometry/producer result replaces the fetched native data.
   js(page,"window.rawOriginalFetch=window.fetch;window.rawHoldBoundary=true;window.fetch=async(...args)=>{const response=await window.rawOriginalFetch(...args);const body=args[1]?.body&&JSON.parse(args[1].body);if(body?.cmd==='boundary 1'&&window.rawHoldBoundary){window.rawHoldBoundary=false;await new Promise(resolve=>window.rawReleaseBoundary=resolve);}return response;};")
   before_init=dump(page);history_init=js(page,'return ReferenceWorkspace.history.undo.length;')
   create_entry(page);page.wait_for_function("typeof window.rawReleaseBoundary==='function'")
   check(f'{width} restoration locks actual raw controls',page.locator('#igCellI').is_disabled() and page.locator('#igSaveBinding').is_disabled())
   refused=js(page,"try{await ReferenceWorkspace.save();return false;}catch(error){return /還原/.test(error.message);}")
   check(f'{width} initializing save explicitly rejects before ZIP/native change',refused and draft(page)==binding_raw and dump(page)==before_init and js(page,'return ReferenceWorkspace.history.undo.length;')==history_init)
   js(page,"window.rawReleaseBoundary();delete window.rawReleaseBoundary;window.fetch=window.rawOriginalFetch;delete window.rawOriginalFetch;")
   page.wait_for_function("InfiniteGridWorkspace.isOpen && $('igCellI') && !$('igCellI').disabled")
   check(f'{width} create entry resumes binding exact raw/provenance',draft(page)==binding_raw and page.locator('#igCellI').input_value()=='-' and page.locator('#igAnchorUD').input_value()=='0')
   page.locator('.ig-rational summary').click()
   page.locator('#igCellI').fill('-2');page.locator('#igCellJ').fill('1');page.locator('#igAnchorUD').fill('1')
   valid_binding=draft(page);undo_before=js(page,'return ReferenceWorkspace.history.undo.length;')
   page.locator('#igSaveBinding').click();preview(page);page.locator('#impact-confirm').click();settled(page)
   page.wait_for_function("$('igBoundary') && !$('igBoundary').disabled")
   bindings=js(page,"return (await apiRequest('objects')).gridBindings;")
   check(f'{width} binding confirm publishes one native record and clears raw',len(bindings)==1 and bindings[0]['cell']==['-2','1'] and draft(page) is None and js(page,'return ReferenceWorkspace.history.undo.length;')==undo_before+1)
   page.locator('#igClose').click();js(page,"const r=await apiRequest('line undo');if(!r.ok)throw Error(r.error);await renderObjects();")
   check(f'{width} binding one undo restores raw/native vertex provenance',draft(page)==valid_binding and len(js(page,"return (await apiRequest('objects')).gridBindings;"))==0)
   js(page,"const r=await apiRequest('line redo');if(!r.ok)throw Error(r.error);await renderObjects();")
   check(f'{width} binding one redo restores native and clears raw',draft(page) is None and js(page,"return (await apiRequest('objects')).gridBindings;")==bindings)
   # The real native mutation succeeds; only delivery of its response and
   # first receipt is lost. Recovery must read that request, never resend it.
   js(page,f'await InfiniteGridWorkspace.openSystem({source_id});');ready_editor(page)
   page.locator('#igName').fill('回執網格')
   receipt_raw=draft(page);receipt_before=dump(page);receipt_history=js(page,'return ReferenceWorkspace.history.undo.length;')
   page.locator('#igSaveSource').click();preview(page)
   js(page,"window.rawOriginalFetch=window.fetch;window.rawTransport={drop:true,holdReceipts:true,confirms:[],receipts:[]};window.fetch=async(...args)=>{const body=args[1]?.body&&JSON.parse(args[1].body),f=window.rawTransport;const response=await window.rawOriginalFetch(...args);if(body?.cmd?.startsWith('line confirm ')){f.confirms.push({command:body.cmd,requestId:body.requestId});f.executed=await response.clone().json();if(f.drop){f.drop=false;throw new TypeError('probe dropped real confirm reply');}}if(body?.receipt){f.receipts.push(body.receipt);if(f.holdReceipts)throw new TypeError('probe dropped real receipt reply');}return response;};")
   page.locator('#impact-confirm').click()
   page.wait_for_function("connection.phase==='error' && !oc.busy && ReferenceWorkspace.featureConfirmationPending()")
   executed=js(page,"const response=await window.rawOriginalFetch('/api',{method:'POST',headers:{'Content-Type':'application/json','X-Geometry-Version':pageRuntimeVersion},body:JSON.stringify({cmd:'dump'})});return (await response.json()).text;")
   check(f'{width} lost reply native executed once while raw/history remain pending',executed!=receipt_before and draft(page)==receipt_raw and js(page,'return ReferenceWorkspace.history.undo.length;')==receipt_history and js(page,'return window.rawTransport.confirms.length===1 && window.rawTransport.executed.ok;'))
   check(f'{width} unknown outcome locks actual raw controls and permits return',page.locator('#igName').is_disabled() and page.locator('#igSaveSource').is_disabled() and not page.locator('#igClose').is_disabled())
   blocked=js(page,"const token=ReferenceWorkspace.getProjectState().contextToken;let save=false,write=false;try{await ReferenceWorkspace.save();}catch(error){save=true;}try{ReferenceWorkspace.setFeatureAttachment('grid-draft',null,token);}catch(error){write=true;}return save&&write;")
   check(f'{width} unknown confirmation lease rejects save and raw write',blocked and draft(page)==receipt_raw)
   page.locator('#igClose').click();page.wait_for_function('!InfiniteGridWorkspace.isOpen')
   check(f'{width} returning with unknown result retains raw and lease',draft(page)==receipt_raw and js(page,'return ReferenceWorkspace.featureConfirmationPending();'))
   js(page,'window.rawTransport.holdReceipts=false;')
   page.locator('#connectionRetry').click()
   page.wait_for_function("connection.phase==='ready' && !connection.recovering && !ReferenceWorkspace.featureConfirmationPending()")
   transport=js(page,'return window.rawTransport;')
   check(f'{width} recovery reads exact request receipt without second mutation',len(transport['confirms'])==1 and len(transport['receipts'])>=2 and set(transport['receipts'])=={transport['confirms'][0]['requestId']})
   check(f'{width} recovered confirm clears raw and records exactly one native undo',draft(page) is None and js(page,'return ReferenceWorkspace.history.undo.length;')==receipt_history+1 and not js(page,'return InfiniteGridWorkspace.isOpen;'))
   js(page,'window.fetch=window.rawOriginalFetch;delete window.rawOriginalFetch;')
   js(page,"const r=await apiRequest('line undo');if(!r.ok)throw Error(r.error);await renderObjects();")
   check(f'{width} recovered operation one undo restores raw and original World',draft(page)==receipt_raw and dump(page)==receipt_before)
   js(page,"const r=await apiRequest('line redo');if(!r.ok)throw Error(r.error);await renderObjects();")
   check(f'{width} recovered operation one redo clears raw and restores committed World',draft(page) is None and dump(page)==executed)
   page.screenshot(path=str(out/f'{width}-canvas.png'))
   context.close()
  browser.close()
 check('no unexpected browser exceptions',errors==[])
 result.update(completed=True,passed=len(checks),failed=0,checks=checks,exceptions=errors)
except Exception as e:
 try:print('FAIL_STATE '+json.dumps(js(page,"return {gridOpen:InfiniteGridWorkspace.isOpen,referenceBusy:ReferenceWorkspace.busy,operationBusy:oc.busy,status:$('status')?.textContent,gridStatus:$('igStatus')?.textContent,projectState:ReferenceWorkspace.getProjectState()};"),ensure_ascii=False),flush=True)
 except Exception:pass
 result.update(completed=False,passed=sum(c['pass'] for c in checks),failed=sum(not c['pass'] for c in checks),checks=checks,exceptions=errors,error=str(e))
 raise
finally:
 (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
 print(json.dumps({k:v for k,v in result.items() if k not in ('checks',)},ensure_ascii=False),flush=True)
