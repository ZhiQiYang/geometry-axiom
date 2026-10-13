"""Trusted pointer/keyboard regression gate for definition-diagram ownership.

Requires GEOMETRY_VERIFY_ROOT, GEOMETRY_TEST_URL and
GEOMETRY_GRID_INTERACTION_OUT (a dedicated directory below TEMP).
Use an explicitly isolated native service: this creates synthetic QA grids.
Pointer cases edit the input and click once without Enter/Tab/blur preparation.
"""
import json
import os
import subprocess
import tempfile
import traceback
import urllib.parse
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

root = Path(os.environ['GEOMETRY_VERIFY_ROOT']).resolve()
url = os.environ['GEOMETRY_TEST_URL']
address = urllib.parse.urlparse(url)
assert address.scheme == 'http' and address.hostname == '127.0.0.1' and address.port not in (None, 8765), 'Explicit isolated loopback service required'
assert not subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain']).strip(), 'Frozen worktree must be clean'
runtime = json.load(urllib.request.urlopen(urllib.parse.urljoin(url, 'runtime')))
assert runtime['fresh'] and Path(runtime['root']).resolve() == root, 'Frozen runtime does not match worktree'
out = Path(os.environ['GEOMETRY_GRID_INTERACTION_OUT']).resolve()
assert out != Path(tempfile.gettempdir()).resolve() and out.is_relative_to(Path(tempfile.gettempdir()).resolve()), 'Dedicated TEMP evidence directory required'
out.mkdir(parents=True, exist_ok=True)
records, cases, errors, console, commands = [], [], [], [], []


def check(label, value, detail=None):
    records.append({'label': label, 'pass': value is True, 'detail': detail})
    print(('PASS ' if value is True else 'FAIL ') + label, flush=True)


def js(page, body):
    return page.evaluate('async()=>{' + body + '}')


def snapshot(page):
    return js(page, """return {native:(await apiRequest('dump')).text,
      project:ReferenceWorkspace.getProjectState(),model:ReferenceWorkspace.getModelOperationState(),
      undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length,
      raw:ReferenceWorkspace.readFeatureAttachment('grid-draft')};""")


def ready(page):
    page.wait_for_function("InfiniteGridWorkspace.isOpen && $('igName') && !$('igName').disabled")


def settled(page):
    page.wait_for_function("!oc.busy && !ReferenceWorkspace.busy && !document.querySelector('dialog.reference-impact[open]')")


def setup(page):
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('console', lambda message: console.append({'type': message.type, 'text': message.text}) if message.type in ('error', 'warning') else None)
    page.on('dialog', lambda dialog: dialog.accept())

    def requested(request):
        if urllib.parse.urlparse(request.url).path == '/api' and request.post_data:
            data = json.loads(request.post_data)
            if 'cmd' in data:
                commands.append(data['cmd'])

    page.on('request', requested)
    page.goto(url)
    page.wait_for_function("connection.phase==='ready'")


def open_source(page, grid_id):
    row = page.locator(f'.object-row[data-kind="grid-system"][data-id="{grid_id}"]')
    if not row.is_visible():
        page.locator('#toggleLeft').click()
    row.dblclick()
    ready(page)
    if page.locator('#paramGridLessonClose').is_visible():
        page.locator('#paramGridLessonClose').click()


def focus_matches(page, axis, key):
    return page.locator(f'.ig-axis[data-ig-axis="{axis}"] [data-ig-field="{key}"]').evaluate("node=>node.classList.contains('is-focus')")


def pointer_case(page, touch, label, edited, value, target, axis, key):
    # Geometry may move during editing. Scrolling/measuring does not blur the
    # edited input; the first trusted pointer action itself must commit change.
    page.locator('#' + edited).fill(value)
    control = page.locator(target)
    control.evaluate("node=>node.scrollIntoView({block:'center',behavior:'instant'})")
    before = snapshot(page)
    check(label + ' edited input owns focus before pointer', js(page, f"return document.activeElement.id==={json.dumps(edited)};"))
    page.evaluate("window.qaPressed=null;window.qaPressedConnected=null;window.qaClicked=null;window.qaClickCount=0;")
    rect = control.bounding_box()
    x, y = rect['x'] + rect['width'] / 2, rect['y'] + rect['height'] / 2
    hit = page.evaluate("({x,y})=>document.elementFromPoint(x,y)?.closest('button,input,select')?.id || document.elementFromPoint(x,y)?.closest('[data-ig-chip]')?.dataset.igChip", {'x': x, 'y': y})
    visible_target = control.evaluate("(node,p)=>document.elementFromPoint(p.x,p.y)?.closest('button,input,select')===node", {'x': x, 'y': y})
    check(label + ' measured center hits actual target control', visible_target, {'point': [x, y], 'hit': hit})
    assert visible_target, label + ' measured target is covered'
    (page.touchscreen.tap if touch else page.mouse.click)(x, y)
    after = snapshot(page)
    pointer = page.evaluate("({pressed:window.qaPressedKey,connected:window.qaPressedConnected,sameClick:window.qaClicked===window.qaPressed,clicks:window.qaClickCount})")
    check(label + ' first pointer focuses chosen field', focus_matches(page, axis, key), {'target': target, 'point': [x, y], 'hit': hit, 'pointer': pointer})
    check(label + ' original pressed control receives one click', pointer['connected'] is True and pointer['sameClick'] is True and pointer['clicks'] == 1, pointer)
    check(label + ' edited value retained verbatim', page.locator('#' + edited).input_value() == value)
    check(label + ' native / raw / revision / dirty / undo / redo unchanged by click', after == before)
    cases.append({'label': label, 'edited': edited, 'value': value, 'target': target, 'touch': touch, 'before': before, 'after': after, 'pointer': pointer})


result = {'schema': 'geometry-grid-definition-interaction/1',
          'head': subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip(),
          'tree': subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD^{tree}'], text=True).strip(),
          'runtime': runtime, 'url': url, 'root': str(root),
          'coverage': 'Trusted first mouse/touch clicks immediately after editing, keyboard Enter/Tab/Escape, inline errors, native/raw/project/history equality. No pre-blur in pointer cases; no physical IME claim.'}
try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=os.environ.get('GEOMETRY_CHROME', '/usr/bin/chromium'), headless=True, args=['--no-sandbox'])
        for width, height, touch in [(1400, 1000, False), (390, 844, True)]:
            context = browser.new_context(viewport={'width': width, 'height': height}, is_mobile=touch, has_touch=touch)
            page = context.new_page()
            setup(page)
            page.locator('#mobileCreateObject' if touch else '#btnCreateObject').click()
            page.locator('#btnQuickGrid').click()
            ready(page)
            if page.locator('#paramGridLessonClose').is_visible():
                page.locator('#paramGridLessonClose').click()
            name = f'QA first-click {width} {os.getpid()}'
            page.locator('#igName').fill(name)
            page.locator('#igUStep').fill('1830')
            page.locator('#igVStep').fill('400')
            page.locator('#igSaveSource').click()
            page.wait_for_selector('dialog.reference-impact[open]')
            page.locator('#impact-confirm').click()
            settled(page)
            ready(page)
            grid_id = js(page, f"return oc.gridSystems.find(grid=>grid.name==={json.dumps(name)}).id;")
            baseline = snapshot(page)['native']
            page.evaluate("""()=>{if(window.qaPointerInstalled)return;window.qaPointerInstalled=true;
              document.addEventListener('pointerdown',event=>{window.qaPressed=event.target.closest('button,input,select');window.qaPressedKey=qaPressed?.dataset.igChip||qaPressed?.id;},true);
              document.addEventListener('pointerup',()=>{window.qaPressedConnected=!!qaPressed?.isConnected;},true);
              document.addEventListener('click',event=>{window.qaClicked=event.target.closest('button,input,select');window.qaClickCount++;},true);
            }""")
            check(f'{width} identity / meaningful UI / no framework overlay', page.url == url and bool(page.title()) and page.locator('#igDefStage').is_visible() and page.locator('vite-error-overlay,nextjs-portal').count() == 0)
            for edited, value, target, axis, key in [
                ('igVPhase', '-50', '[data-ig-chip="u:step"]', 'u', 'step'),
                ('igUPhase', '120', '[data-ig-chip="v:step"]', 'v', 'step'),
                ('igVPhase', '-51', '[data-ig-chip="u:phase"]', 'u', 'phase'),
                ('igUPhase', '121', '[data-ig-chip="v:phase"]', 'v', 'phase'),
                ('igVStep', '915', '[data-ig-chip="u:step"]', 'u', 'step'),
                ('igUStep', '1900', '[data-ig-chip="v:step"]', 'v', 'step'),
                ('igName', name + ' draft', '[data-ig-chip="u:phase"]', 'u', 'phase'),
                ('igVPhase', '-52', '#igUHead', 'u', 'step'),
                ('igUPhase', '122', '#igVHead', 'v', 'step'),
                ('igVPhase', '-53', '#igUStep', 'u', 'step'),
                ('igUPhase', '123', '#igVStep', 'v', 'step'),
            ]:
                pointer_case(page, touch, f'{width} {edited} -> {target}', edited, value, target, axis, key)
            page.locator('#igName').scroll_into_view_if_needed()
            page.screenshot(path=str(out / f'{width}-repeat-first-click.png'))

            # Keyboard paths are separate tests; pointer cases above never use
            # these keys to finish editing before the first click.
            page.locator('#igVPhase').fill('-70')
            before = snapshot(page)
            page.keyboard.press('Enter')
            check(f'{width} Enter keeps raw value / editor / native / history', snapshot(page) == before and js(page, 'return InfiniteGridWorkspace.isOpen;') and page.locator('#igVPhase').input_value() == '-70')
            page.keyboard.press('Tab')
            check(f'{width} Tab moves focus without extra draft/native/history writes', snapshot(page) == before and js(page, "return document.activeElement.id!=='igVPhase';"))
            page.locator('#igName').click()
            for _ in range(40):
                page.keyboard.press('Tab')
                if js(page, "return document.activeElement.dataset.igChip==='u:step';"):
                    break
            check(f'{width} real Tab reaches live dimension button', js(page, "return document.activeElement.dataset.igChip==='u:step';"))
            before = snapshot(page)
            page.keyboard.press('Enter')
            check(f'{width} Enter activates focused chip without losing field/raw/history', focus_matches(page, 'u', 'step') and snapshot(page) == before)

            page.locator('#igVPhase').fill('-72')
            before = snapshot(page)
            page.keyboard.press('Escape')
            page.wait_for_function('!InfiniteGridWorkspace.isOpen')
            check(f'{width} Escape closes while preserving edited raw/native/history', snapshot(page) == before)
            open_source(page, grid_id)
            check(f'{width} ordinary library reopen retains escaped raw value', page.locator('#igVPhase').input_value() == '-72')
            pointer_case(page, touch, f'{width} reopened editor first click', 'igVPhase', '-73', '[data-ig-chip="u:step"]', 'u', 'step')

            pointer_case(page, touch, f'{width} invalid v spacing -> valid u chip', 'igVStep', '1e', '[data-ig-chip="u:step"]', 'u', 'step')
            check(f'{width} inline invalid field remains located', page.locator('#igVStep').get_attribute('aria-invalid') == 'true' and bool(page.locator('#igVStepErr').inner_text()))
            before = snapshot(page)
            page.locator('#igSaveSource').click()
            page.wait_for_function("!oc.busy && !ReferenceWorkspace.busy && $('igVStep').getAttribute('aria-invalid')==='true'")
            check(f'{width} invalid preview has zero native/raw/history writes', snapshot(page) == before and page.locator('dialog.reference-impact[open]').count() == 0 and js(page, "return document.activeElement.id==='igVStep';"))
            page.screenshot(path=str(out / f'{width}-inline-error.png'))
            pointer_case(page, touch, f'{width} corrected spacing first click', 'igVStep', '900', '[data-ig-chip="v:step"]', 'v', 'step')

            for axis in ('U', 'V'):
                page.locator(f'#ig{axis}Source input[value="repeat-panel"]').check()
                for suffix, value in [('Panel', '400'), ('Gap', '5'), ('Anchor', '-100')]:
                    page.locator(f'#ig{axis}{suffix}').fill(value)
            for edited, value, target, axis, key in [
                ('igVAnchor', '-99', '[data-ig-chip="u:panel"]', 'u', 'panel'),
                ('igUAnchor', '-98', '[data-ig-chip="v:panel"]', 'v', 'panel'),
                ('igVGap', '7', '[data-ig-chip="u:anchor"]', 'u', 'anchor'),
                ('igUPanel', '401', '[data-ig-chip="v:anchor"]', 'v', 'anchor'),
            ]:
                pointer_case(page, touch, f'{width} panel {edited} -> {target}', edited, value, target, axis, key)
            page.locator('#igName').scroll_into_view_if_needed()
            page.screenshot(path=str(out / f'{width}-panel-first-click.png'))
            before = snapshot(page)
            command_start = len(commands)
            page.locator('#igSaveSource').click()
            page.wait_for_selector('dialog.reference-impact[open]')
            preview = snapshot(page)
            check(f'{width} actual preview has zero native writes and preserves raw/dirty/history', preview['native'] == before['native'] and preview['project'] == before['project'] and preview['raw'] == before['raw'] and preview['undo'] == before['undo'] and preview['redo'] == before['redo'])
            check(f'{width} preview sends only read/preview commands', all(command.split(' ', 1)[0] in ['dump', 'objects', 'references', 'newid'] or command.startswith('line preview ') for command in commands[command_start:]), commands[command_start:])
            page.keyboard.press('Escape')
            settled(page)
            ready(page)
            check(f'{width} preview Escape cancels with full snapshot unchanged', snapshot(page) == before)
            check(f'{width} entire native baseline unchanged through all edits/focus/preview', snapshot(page)['native'] == baseline)
            page.locator('#igClose').click()
            context.close()
        browser.close()
    check('No uncaught browser exceptions or warning/error console messages', not errors and not console, {'errors': errors, 'console': console})
    result['completed'] = True
except Exception as error:
    errors.append('HARNESS: ' + str(error))
    traceback.print_exc()
    result['completed'] = False
    try:
        page.screenshot(path=str(out / 'harness-failure.png'))
    except Exception:
        pass
finally:
    result.update(passed=sum(record['pass'] for record in records), failed=sum(not record['pass'] for record in records), checks=records, cases=cases, exceptions=errors, consoleWarningsErrors=console)
    (out / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ['schema', 'head', 'tree', 'runtime', 'completed', 'passed', 'failed', 'exceptions']}, ensure_ascii=False), flush=True)
raise SystemExit(0 if result['completed'] and not result['failed'] and not errors and not console else 1)
