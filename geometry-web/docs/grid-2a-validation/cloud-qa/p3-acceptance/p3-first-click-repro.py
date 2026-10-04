from playwright.sync_api import sync_playwright
from pathlib import Path
import json
OUT=Path('/tmp/pr130-qa-e06ff2a/p3-first-click-repro');OUT.mkdir(exist_ok=True)
rows=[]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 for port in [8808,8806]:
  for width,height,touch in [(1400,1000,False),(390,844,True)]:
   c=b.new_context(viewport={'width':width,'height':height},is_mobile=touch,has_touch=touch);page=c.new_page()
   page.goto(f'http://127.0.0.1:{port}/');page.wait_for_function("connection.phase==='ready'")
   page.evaluate('async()=>{await InfiniteGridWorkspace.create();}')
   page.wait_for_function("InfiniteGridWorkspace.isOpen && $('igName') && !$('igName').disabled")
   if page.locator('#paramGridLessonClose').is_visible():page.locator('#paramGridLessonClose').click()
   for sel,value in [('igUStep','1830'),('igUPhase','120'),('igVStep','400'),('igVPhase','-50')]:page.locator('#'+sel).fill(value)
   page.locator('#igName').scroll_into_view_if_needed()
   native=page.evaluate("async()=>(await apiRequest('dump')).text")
   page.evaluate("""()=>{window.qaEvents=[];for(const t of ['pointerdown','mousedown','change','focusout','focusin','mouseup','pointerup','click'])document.addEventListener(t,e=>qaEvents.push({type:t,target:e.target.id||e.target.dataset.igChip||e.target.className,tag:e.target.tagName,connected:e.target.isConnected,active:document.activeElement.id,time:performance.now()}),true);}""")
   chip=page.locator('[data-ig-chip="u:step"]');r=chip.bounding_box();point=[r['x']+r['width']/2,r['y']+r['height']/2]
   active=page.evaluate('document.activeElement.id')
   (page.touchscreen.tap if touch else page.mouse.click)(*point)
   first=page.locator('.ig-axis[data-ig-axis="u"] [data-ig-field="step"]').evaluate("n=>n.classList.contains('is-focus')")
   firstEvents=page.evaluate('qaEvents.slice()')
   page.screenshot(path=str(OUT/f'{port}-{width}-first.png'))
   # A second trusted click works once the input's change event has completed.
   r=chip.bounding_box();(page.touchscreen.tap if touch else page.mouse.click)(r['x']+r['width']/2,r['y']+r['height']/2)
   second=page.locator('.ig-axis[data-ig-axis="u"] [data-ig-field="step"]').evaluate("n=>n.classList.contains('is-focus')")
   row={'port':port,'viewport':[width,height],'touch':touch,'activeBefore':active,'firstFocus':first,'secondFocus':second,'firstEvents':firstEvents,'allEvents':page.evaluate('qaEvents'),'nativeUnchanged':page.evaluate("async()=>(await apiRequest('dump')).text")==native,'runtime':page.evaluate("async()=>await(await fetch('/runtime')).json()")}
   rows.append(row);print(json.dumps(row,ensure_ascii=False),flush=True);c.close()
 b.close()
(OUT/'results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
