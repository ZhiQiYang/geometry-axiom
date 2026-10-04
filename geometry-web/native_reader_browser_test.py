"""Manual actual-browser gate for native supply versus project requirements.

Requires an explicitly isolated GEOMETRY_TEST_URL, frozen GEOMETRY_VERIFY_ROOT,
and GEOMETRY_READER_BROWSER_OUT below TEMP. Resets only that test service.
Public API supplies parameter setup; project save/open use actual UI controls.
"""
import base64
import json
import os
from pathlib import Path
import subprocess
import tempfile
import urllib.parse
import urllib.request
import zipfile
from playwright.sync_api import sync_playwright

root=Path(os.environ['GEOMETRY_VERIFY_ROOT']).resolve()
url=os.environ['GEOMETRY_TEST_URL']
address=urllib.parse.urlparse(url)
assert address.scheme=='http' and address.hostname=='127.0.0.1' and address.port not in (None,8765)
runtime=json.load(urllib.request.urlopen(urllib.parse.urljoin(url,'runtime')))
assert runtime['fresh'] and Path(runtime['root']).resolve()==root
head=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
tree=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD^{tree}'],text=True).strip()
assert not subprocess.check_output(['git','-C',str(root),'status','--porcelain']).strip()
out=Path(os.environ['GEOMETRY_READER_BROWSER_OUT']).resolve()
assert out!=Path(tempfile.gettempdir()).resolve() and out.is_relative_to(Path(tempfile.gettempdir()).resolve())
out.mkdir(parents=True,exist_ok=True)
checks=[];errors=[]
def js(page,body):return page.evaluate('async()=>{'+body+'}')
def check(label,value):
 checks.append({'label':label,'pass':value is True})
 print(('PASS ' if value is True else 'FAIL ')+label,flush=True)
 assert value is True,label
def snapshot(page):return js(page,"return {scene:(await apiRequest('dump')).text,parameters:(await apiRequest('objects')).parameters};")
def open_file(page,path):
 if not page.locator('#btnOpenProject').is_visible():page.locator('#fileMenuBtn').click()
 with page.expect_file_chooser() as chooser:page.locator('#btnOpenProject').click()
 chooser.value.set_files(path)
 page.wait_for_function('!ReferenceWorkspace.busy')
result={'schema':'geometry-native-reader-browser/1','head':head,'tree':tree,'runtime':runtime,
 'coverage':'Actual native setup, Chromium trusted project save/open, real downloaded geometry-canvas/6 ZIP; no physical OS chooser/IME claim.'}
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=os.environ.get('GEOMETRY_CHROME','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
  for width in (1280,390):
   context=browser.new_context(viewport={'width':width,'height':900},accept_downloads=True)
   page=context.new_page();page.on('pageerror',lambda error:errors.append(str(error)));page.on('dialog',lambda dialog:dialog.accept())
   page.goto(url);page.wait_for_function("connection.phase==='ready'");page.evaluate('window.showSaveFilePicker=undefined')
   js(page,"const r=await apiRequest('line reset');if(!r.ok)throw Error(r.error);await renderObjects();const request={expectedRevision:(await apiRequest('engineering-read')).revision,operations:[{op:'put-parameter',value:{id:701,name:'舊版寬度',fields:[{id:1,name:'寬',type:'dimension',input:'600'}]}}]};const preview=await EngineeringAdapter.preview(request);if(!preview.valid)throw Error(JSON.stringify(preview));const done=await EngineeringAdapter.confirm({token:preview.token});if(!done.ok)throw Error(JSON.stringify(done));await renderObjects();")
   before=snapshot(page)
   advertised=js(page,"const scene=(await apiRequest('dump')).text;const response=await fetch('/upload/prepare',{method:'POST',body:scene});const candidate=await response.json();if(!candidate.ok)throw Error(JSON.stringify(candidate));const cancelled=await fetch('/upload/cancel',{method:'POST',body:JSON.stringify(candidate.token)});if(!(await cancelled.json()).ok)throw Error('cancel failed');return candidate;")
   check(f'{width} actual native offers subdivision while old scene only needs parameters', 'grid-subdivision-rules/1' in advertised['capabilities'] and advertised['required_capabilities']==['parameters/1'])
   archive=out/f'{width}-legacy-v6.gcanvas'
   with page.expect_download() as download:page.locator('#projectBar [data-project-action="save"]').click()
   download.value.save_as(archive);page.wait_for_function('!ReferenceWorkspace.busy')
   with zipfile.ZipFile(archive) as z:
    manifest=json.loads(z.read('manifest.json'))
    check(f'{width} actual downloaded old-format archive keeps only needed capability',manifest['format']=='geometry-canvas/6' and manifest['requiredCapabilities']==['parameters/1'] and z.read('world.scene').decode()==before['scene'])
   js(page,'await ReferenceWorkspace.newProject();await renderObjects();')
   check(f'{width} replacement test starts from real empty World',snapshot(page)['parameters']==[])
   open_file(page,archive)
   check(f'{width} formal project file open restores exact old World and parameters',snapshot(page)==before)
   # Required unsupported native capabilities remain a rejection even when
   # the service advertises them. The complete forged ZIP is selected through
   # the same real file-input path; rejection must preserve the current World.
   with zipfile.ZipFile(archive) as z:entries={name:z.read(name) for name in z.namelist()}
   manifest['requiredCapabilities'].append('grid-subdivision-rules/1')
   entries['manifest.json']=json.dumps(manifest,ensure_ascii=False).encode()
   unsupported=out/f'{width}-unsupported-required.gcanvas'
   with zipfile.ZipFile(unsupported,'w',zipfile.ZIP_DEFLATED) as z:
    for name,data in entries.items():z.writestr(name,data)
   state=js(page,'return ReferenceWorkspace.getProjectState();');history=js(page,'return ReferenceWorkspace.history.undo.length;')
   open_file(page,unsupported)
   check(f'{width} unknown required capability rejects atomically through formal reader',snapshot(page)==before and js(page,'return ReferenceWorkspace.getProjectState();')==state and js(page,'return ReferenceWorkspace.history.undo.length;')==history)
   check(f'{width} DSL default/highwater without reader support stays rejected',js(page,"for(const scene of ['grid-source-rule-highwater 1 next 1','grid-source-rule-highwater 1 next 2','gridrule:1:1','subgrid 2 at-line rule 1']){let refused=false;try{GeometryProject.sceneCapabilities(scene+'\\n');}catch(error){refused=true;}if(!refused)return false;}return true;"))
   page.screenshot(path=str(out/f'{width}-restored.png'));context.close()
  browser.close()
 check('no unexpected browser exceptions',errors==[])
 result.update(completed=True,passed=len(checks),failed=0,checks=checks,exceptions=errors)
except Exception as error:
 result.update(completed=False,passed=sum(c['pass'] for c in checks),failed=sum(not c['pass'] for c in checks),checks=checks,exceptions=errors,error=str(error))
 raise
finally:
 (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
 print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False),flush=True)
