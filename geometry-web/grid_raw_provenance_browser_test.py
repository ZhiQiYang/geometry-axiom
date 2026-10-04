"""Required #45 raw interpretation/provenance gate against real Chromium/native.

Use an isolated service and clean frozen worktree via GEOMETRY_VERIFY_ROOT,
GEOMETRY_TEST_URL and a dedicated TEMP GEOMETRY_RAW_PIN_OUT. The fixture is
created through the actual empty project/grid entry; no private documents.
Playwright file chooser automation does not certify a physical OS chooser/IME.
"""
import json
import os
import subprocess
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from playwright.sync_api import sync_playwright

root = Path(os.environ['GEOMETRY_VERIFY_ROOT']).resolve()
url = os.environ['GEOMETRY_TEST_URL']
address = urllib.parse.urlparse(url)
assert address.scheme == 'http' and address.hostname == '127.0.0.1' and address.port not in (None, 8765)
out = Path(os.environ['GEOMETRY_RAW_PIN_OUT']).resolve()
assert out.is_relative_to(Path(tempfile.gettempdir()).resolve()) and out != Path(tempfile.gettempdir()).resolve()
out.mkdir(parents=True, exist_ok=True)
runtime = json.load(urllib.request.urlopen(url + 'runtime'))
assert runtime['fresh'] and Path(runtime['root']).resolve() == root
head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
tree = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD^{tree}'], text=True).strip()
assert not subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain']).strip()
checks, errors = [], []
result = {'head': head, 'tree': tree, 'runtime': runtime, 'coverage':
          'True v10 ZIP/file-menu/create-entry/raw editing/save/native preview/confirm. Public API fixture setup and undo/redo. No physical OS chooser/IME claim.'}


def js(page, body):
    return page.evaluate('async()=>{' + body + '}')


def check(label, value):
    checks.append({'label': label, 'pass': value is True})
    print(('PASS ' if value is True else 'FAIL ') + label, flush=True)
    assert value is True, label


def settled(page):
    page.wait_for_function('!ReferenceWorkspace.busy&&!oc.busy')


def load(page, file):
    if not page.locator('#btnOpenProject').is_visible():
        page.locator('#fileMenuBtn').click()
    with page.expect_file_chooser() as chooser:
        page.locator('#btnOpenProject').click()
    chooser.value.set_files(file)
    settled(page)


def entry(page):
    if page.locator('#mobileCreateObject').is_visible():
        page.locator('#mobileCreateObject').click()
        page.locator('#btnQuickGrid').click()
    else:
        page.locator('#btnNewGridSystem').click()
    page.wait_for_function("InfiniteGridWorkspace.isOpen&&$('igUStep')&&!$('igUStep').disabled")


def snapshot(page):
    return js(page, "return {raw:ReferenceWorkspace.readFeatureAttachment('grid-draft'),world:(await apiRequest('dump')).text,undo:ReferenceWorkspace.history.undo.length,revision:(await apiRequest('engineering-read')).revision};")


def watch(page):
    js(page, "window.__rawCommands=[];const original=window.apiRequest;window.apiRequest=async(command,...args)=>{if(/^line (preview|confirm) /.test(command))__rawCommands.push(command);return original(command,...args);};")


def reject(page, label, before):
    page.locator('#igSaveSource').click()
    settled(page)
    after = snapshot(page)
    check(label + ' rejects before native preview/confirm and preserves raw/World/history/revision',
          not page.locator('dialog.reference-impact[open]').count() and after == before and
          js(page, 'return __rawCommands.length===0;'))
    check(label + ' explains explicit reselection', js(page, "return /重新選取/.test($('igDraftNote').textContent);"))


def parameter(page, operations):
    page.evaluate("""async operations=>{const r=await EngineeringAdapter.read();const p=await EngineeringAdapter.preview({expectedRevision:r.revision,operations});if(!p.valid)throw Error(JSON.stringify(p));const done=await apiRequest('engineering-confirm '+p.token);if(!done.ok)throw Error(JSON.stringify(done));await renderObjects();}""", operations)


def put(value):
    return {'op': 'put-parameter', 'value': {'id': 801, 'name': '原始尺寸', 'fields': [
        {'id': 1, 'name': '間距', 'type': 'dimension', 'input': str(value)}]}}


def field_pin(page):
    return js(page, "const row=(await apiRequest('objects')).parameters.find(row=>row.id===801);return {kind:'parameter-field',parameterId:801,fieldId:1,fingerprint:await GeometryProject.sha(new TextEncoder().encode(JSON.stringify([row.card.id,row.card.fields.find(field=>field.id===1)])))};")


try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=os.environ.get('GEOMETRY_CHROME', '/usr/bin/chromium'),
                                    headless=True, args=['--no-sandbox'])
        for width in (1280, 390):
            for case in ('unknown-enum', 'missing-pin', 'wrong-pin', 'recreated-pin'):
                label = f'{width} {case}'
                context = browser.new_context(viewport={'width': width, 'height': 900}, accept_downloads=True)
                page = context.new_page()
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.on('dialog', lambda dialog: dialog.accept())
                page.goto(url)
                page.wait_for_function("connection.phase==='ready'")
                js(page, 'await ReferenceWorkspace.newProject();')
                settled(page)
                entry(page)
                page.locator('#igClose').click()
                saved_pin = None
                if case != 'unknown-enum':
                    parameter(page, [put(600)])
                    saved_pin = field_pin(page)
                    if case == 'recreated-pin':
                        parameter(page, [{'op': 'delete-parameter', 'id': 801}])
                        parameter(page, [put(700)])
                        check(label + ' native delete/recreate changes actual field evidence', field_pin(page) != saved_pin)
                archive = page.evaluate("""async ({kind,pin})=>{const loaded=await GeometryProject.unpack(await ReferenceWorkspace.exportBytes(),fflate);const raw=loaded.manifest.featureAttachments.records[0].value;Object.assign(raw.rawForm,{igName:'原始來源',igUSource:kind==='unknown-enum'?'bogus':'repeat',igUStep:'600',igUPhase:'0',igUPanel:'600',igUGap:'0',igUAnchor:'0',igUStagger:'',igVStep:'400',igVPhase:'0'});if(kind!=='unknown-enum')raw.rawForm.igUStepSource='801:1';raw.inputRefs=kind==='wrong-pin'?[{...pin,fingerprint:'0'.repeat(64)}]:kind==='recreated-pin'?[pin]:[];return Array.from(await GeometryProject.pack(loaded.scene,loaded.manifest,loaded.sources,fflate));}""", {'kind': case, 'pin': saved_pin})
                file = out / f'{width}-{case}.gcanvas'
                file.write_bytes(bytes(archive))
                load(page, file)
                before = snapshot(page)
                entry(page)
                check(label + ' passive restore retains exact raw and provenance',
                      js(page, "return ReferenceWorkspace.readFeatureAttachment('grid-draft');") == before['raw'])
                watch(page)
                reject(page, label, before)
                page.evaluate('window.showSaveFilePicker=undefined')
                with page.expect_download() as download:
                    page.locator('#projectBar [data-project-action="save"]').click()
                persisted = out / f'{width}-{case}-persisted.gcanvas'
                download.value.save_as(persisted)
                settled(page)
                with zipfile.ZipFile(persisted) as z:
                    manifest = json.loads(z.read('manifest.json'))
                    check(label + ' true ZIP saves original raw/pins and unchanged native World',
                          manifest['featureAttachments']['records'][0]['value'] == before['raw'] and
                          z.read('world.scene').decode() == before['world'])
                context.close()
                context = browser.new_context(viewport={'width': width, 'height': 900}, accept_downloads=True)
                page = context.new_page()
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.on('dialog', lambda dialog: dialog.accept())
                page.goto(url)
                page.wait_for_function("connection.phase==='ready'")
                load(page, persisted)
                entry(page)
                reopened = snapshot(page)
                check(label + ' fresh browser formal ZIP reopen preserves raw and World',
                      reopened['raw'] == before['raw'] and reopened['world'] == before['world'])
                watch(page)
                reject(page, label + ' reopened', reopened)
                if case == 'unknown-enum':
                    page.locator('#igUSource').select_option('repeat-panel')
                else:
                    page.locator('#igUStepSource').select_option('')
                    page.locator('#igUStepSource').select_option('801:1')
                    selected = js(page, "return ReferenceWorkspace.readFeatureAttachment('grid-draft');")
                    check(label + ' explicit reselection records the selected current field evidence',
                          selected['inputRefs'] == [field_pin(page)])
                selected = snapshot(page)
                check(label + ' explicit reselection only changes owned raw', selected['world'] == reopened['world'] and
                      selected['undo'] == reopened['undo'] and selected['revision'] == reopened['revision'])
                page.locator('#igSaveSource').click()
                page.wait_for_selector('dialog.reference-impact[open]')
                check(label + ' true native preview remains detached', snapshot(page) == selected)
                page.locator('dialog.reference-impact[open] .impact-actions button:first-child').click()
                settled(page)
                check(label + ' cancelling preview preserves raw and native state', snapshot(page) == selected)
                page.locator('#igSaveSource').click()
                page.wait_for_selector('dialog.reference-impact[open]')
                page.locator('#impact-confirm').click()
                settled(page)
                after = snapshot(page)
                check(label + ' confirm publishes and clears raw in exactly one undo entry',
                      after['raw'] is None and after['world'] != selected['world'] and after['undo'] == selected['undo'] + 1)
                page.locator('#igClose').click()
                js(page, "const r=await apiRequest('line undo');if(!r.ok)throw Error(JSON.stringify(r));await renderObjects();")
                undone = snapshot(page)
                check(label + ' one native undo restores complete raw and original World',
                      undone['raw'] == selected['raw'] and undone['world'] == selected['world'])
                js(page, "const r=await apiRequest('line redo');if(!r.ok)throw Error(JSON.stringify(r));await renderObjects();")
                redone = snapshot(page)
                check(label + ' one native redo republishes and clears raw', redone['raw'] is None and redone['world'] == after['world'])
                context.close()
        browser.close()
    check('no unexpected browser exceptions', errors == [])
    result.update(completed=True, checks=checks, passed=len(checks), failed=0, exceptions=errors)
except Exception as error:
    result.update(completed=False, checks=checks, passed=sum(c['pass'] for c in checks),
                  failed=sum(not c['pass'] for c in checks), exceptions=errors, error=str(error))
    raise
finally:
    (out / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k not in ('checks', 'runtime')}, ensure_ascii=False), flush=True)
