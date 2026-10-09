"""Real first-center input against an explicitly isolated native web service.

Run with --url http://127.0.0.1:<test-port>/ --out /tmp/<evidence>.
--repro runs only the original 390px mouse/touch path, with the same oracle.
No forced clicks, pre-blur, second-click retries or alternate target edges.
Fixture reset is synthetic; tested actions use real browser input. This does
not certify a physical phone, soft keyboard, OS chooser or non-Chromium browser.
"""
import argparse
import json
from pathlib import Path
import subprocess
import traceback
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def run(args):
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    url = args.url.rstrip('/') + '/'
    runtime = json.load(urlopen(url + 'runtime'))
    assert runtime['fresh'] and Path(runtime['root']).resolve() == ROOT
    report = {
        'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'url': url, 'runtime': runtime, 'browserPath': 'Browser plugin not available; existing Playwright/Chromium',
        'coverage': 'Synthetic isolated reset; real mouse/touch/keyboard UI; no physical-phone claim',
        'records': [], 'errors': [], 'console': [], 'requests': [], 'completed': False,
    }

    def check(label, ok, detail=None):
        report['records'].append({'label': label, 'pass': bool(ok), 'detail': detail})
        (out / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        print(('PASS ' if ok else 'FAIL ') + label, flush=True)
        return bool(ok)

    def js(page, body):
        return page.evaluate('async()=>{' + body + '}')

    def protected(page):
        return js(page, "const m=ReferenceWorkspace.getModelOperationState();return {native:(await apiRequest('dump')).text,history:{context:m.context,frame:m.frame,undo:m.undo,redo:m.redo,undoLength:ReferenceWorkspace.history.undo.length,redoLength:ReferenceWorkspace.history.redo.length,entries:ReferenceWorkspace.history.undo.map(e=>({kind:e.kind,action:e.action}))}};")

    def geometry(page, selector):
        return page.locator(selector).evaluate("n=>{const r=n.getBoundingClientRect(),s=getComputedStyle(n),x=r.x+r.width/2,y=r.y+r.height/2;return {rect:{x:r.x,y:r.y,width:r.width,height:r.height},style:{left:s.left,right:s.right,top:s.top,bottom:s.bottom,zIndex:s.zIndex},hit:document.elementFromPoint(x,y)?.closest('button')?.id,stack:document.elementsFromPoint(x,y).map(e=>e.id||e.tagName)}}")

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=args.chromium, headless=True, args=['--no-sandbox'])
        report['browserVersion'] = browser.version
        try:
            for width, height, mode in ([(390, 844, m) for m in ['mouse', 'touch']] if args.repro else
                                       [(w, h, m) for w, h in [(390, 844), (900, 900), (1400, 1000)] if args.width is None or args.width == w for m in ['mouse', 'touch']]):
                prefix = f'{width}-{mode}'
                context = browser.new_context(viewport={'width': width, 'height': height}, has_touch=mode == 'touch')
                page = context.new_page()
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                page.on('console', lambda m: report['console'].append({'type': m.type, 'text': m.text}) if m.type in ['warning', 'error'] else None)
                page.on('request', lambda r: report['requests'].append({'url': r.url, 'body': r.post_data}) if r.method == 'POST' else None)

                def click(selector, scroll=True):
                    node = page.locator(selector)
                    if selector != '#btnQuickGrid':
                        # Ordinary controls use Playwright's normal visibility
                        # and layout settling. Grid input below is deliberately
                        # raw, so its original blocked first click cannot retry.
                        (node.tap if mode == 'touch' else node.click)()
                        return
                    r = node.bounding_box()
                    assert r and r['width'] and r['height'], selector
                    x, y = r['x'] + r['width'] / 2, r['y'] + r['height'] / 2
                    if mode == 'touch':
                        page.touchscreen.tap(x, y)
                    else:
                        page.mouse.click(x, y)

                def open_menu():
                    trigger = '#mobileCreateObject' if width <= 900 else '#btnCreateObject'
                    click(trigger, scroll=False)
                    page.locator('#createObjectPop').wait_for(state='visible')
                    return trigger

                def ready_grid():
                    page.wait_for_function("InfiniteGridWorkspace.isOpen && $('igName') && !$('igName').disabled")

                def settled():
                    page.wait_for_function("!oc.busy && !ReferenceWorkspace.busy && !document.querySelector('dialog.reference-impact[open]')")

                def shot(suffix):
                    page.screenshot(path=str(out / f'{prefix}-{suffix}.png'))

                try:
                    page.goto(url)
                    page.wait_for_function("connection.phase==='ready' && window.ParameterUI && window.InfiniteGridWorkspace")
                    check(prefix + ' page identity / meaningful shell / no framework overlay',
                          page.title() == '構形 Canvas · 工程規格與空間建模' and page.locator('#mobileCreateObject').count() == 1 and page.locator('vite-error-overlay,nextjs-portal').count() == 0)
                    js(page, "const r=await apiRequest('reset');if(!r.ok)throw Error(r.error);await renderObjects();")
                    open_menu(); click('#btnNewParameter', scroll=False)
                    page.wait_for_selector('#paramName')
                    if page.locator('#paramGridLessonClose').is_visible():
                        click('#paramGridLessonClose')
                    page.locator('#paramName').fill('Issue123 parameter')
                    page.locator('#paramQuick').fill('(915,1830)'); click('#paramParse')
                    click('#paramPreview')
                    page.wait_for_function("!ParameterUI.previewing && !$('paramConfirm').disabled")
                    click('#paramConfirm'); page.wait_for_function('!ParameterUI.pending')
                    page.locator('#paramName').fill('Issue123 edited parameter')
                    click('#paramPreview')
                    page.wait_for_function("!ParameterUI.previewing && !$('paramConfirm').disabled")
                    click('#paramConfirm'); page.wait_for_function('!ParameterUI.pending')
                    baseline = protected(page)
                    click('#paramName')
                    check(prefix + ' parameter field active immediately before Create', js(page, "return document.activeElement.id==='paramName'"))
                    trigger = open_menu()
                    grid, feedback, menu = [geometry(page, s) for s in ['#btnQuickGrid', '#fbButton', '#createObjectPop']]
                    overlap = page.evaluate("()=>{const m=$('createObjectPop'),a=m.getBoundingClientRect(),b=$('fbButton').getBoundingClientRect(),l=Math.max(a.left,b.left),r=Math.min(a.right,b.right),t=Math.max(a.top,b.top),d=Math.min(a.bottom,b.bottom);if(l>=r||t>=d)return {overlap:false,ok:true};const x=(l+r)/2,y=(t+d)/2,hit=document.elementFromPoint(x,y);return {overlap:true,ok:m.contains(hit),point:[x,y],hit:hit?.closest('button')?.id}}")
                    check(prefix + ' menu owns its actual overlap with collapsed feedback', overlap['ok'], overlap)
                    shot('menu')
                    # Record the trusted first pointer and click targets; do not
                    # let locator auto-wait hide an intercepted center input.
                    js(page, "window.__issue123Events=[];for(const type of ['pointerdown','click'])document.addEventListener(type,e=>window.__issue123Events.push({type,id:e.target.closest('button')?.id,pointerType:e.pointerType||'',trusted:e.isTrusted}),{capture:true});")
                    click('#btnQuickGrid', scroll=False)
                    page.wait_for_function("(InfiniteGridWorkspace.isOpen && $('igName') && !$('igName').disabled) || !$('fbPanel').hidden")
                    events = js(page, 'return window.__issue123Events')
                    opened = js(page, "return InfiniteGridWorkspace.isOpen && $('fbPanel').hidden")
                    check(prefix + ' first center pointer and click each reach grid exactly once',
                          opened and [e['id'] for e in events if e['type'] == 'pointerdown' and e['trusted']] == ['btnQuickGrid'] and [e['id'] for e in events if e['type'] == 'click' and e['trusted']] == ['btnQuickGrid'],
                          {'body': js(page, 'return document.body.className'), 'grid': grid, 'feedback': feedback, 'menu': menu, 'events': events, 'gridOpen': opened})
                    shot('first-center')
                    after_navigation = protected(page)
                    bh, ah = baseline['history'], after_navigation['history']
                    expected_history = (ah == bh if not opened else
                        ah['context'] == bh['context'] and ah['frame'] == bh['frame'] and ah['redo'] == bh['redo'] and ah['redoLength'] == bh['redoLength'] and
                        ah['undoLength'] == bh['undoLength'] + 1 and ah['entries'][:-1] == bh['entries'] and ah['entries'][-1] == {'kind': 'local', 'action': '編輯網格草稿'})
                    check(prefix + ' native unchanged; only the existing initial raw-draft history entry allowed', after_navigation['native'] == baseline['native'] and expected_history,
                          {'before': baseline, 'after': after_navigation})
                    if not opened or args.repro:
                        continue
                    ready_grid(); click('#igClose'); page.wait_for_function('!InfiniteGridWorkspace.isOpen')
                    # Reopen after Escape and drawer switches. Every visible
                    # menu-item center must belong to that item's own subtree.
                    for drawer in (['left', 'right', 'closed'] if width <= 900 else ['desktop']):
                        if drawer == 'left':
                            click('#toggleLeft', scroll=False)
                        elif drawer in ['right', 'closed']:
                            if js(page, "return document.body.classList.contains('drawer-left-open')"):
                                click('[data-close-panel="left"]:visible', scroll=False)
                            if drawer == 'right':
                                row = page.locator('.object-row[data-kind="parameter"]').first
                                if not row.is_visible(): click('#toggleLeft', scroll=False)
                                row.dblclick()
                                page.wait_for_function("document.body.classList.contains('drawer-right-open')")
                        if width <= 900:
                            check(prefix + ' actual ' + drawer + ' drawer state', js(page, f"return {json.dumps(drawer)}==='closed' ? !document.body.classList.contains('drawer-left-open') && !document.body.classList.contains('drawer-right-open') : document.body.classList.contains('drawer-'+{json.dumps(drawer)}+'-open')"))
                        before = protected(page)
                        trigger = open_menu()
                        centers = page.locator('#createObjectPop [role="menuitem"]').evaluate_all("nodes=>nodes.map(n=>{const r=n.getBoundingClientRect(),hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return {id:n.id,hit:hit?.closest('button')?.id,ok:n.contains(hit)}})")
                        check(prefix + ' ' + drawer + ' all menu centers unobscured', all(n['ok'] for n in centers), centers)
                        page.keyboard.press('Escape')
                        check(prefix + ' ' + drawer + ' Escape closes menu and restores trigger', js(page, f"return $('createObjectPop').hidden && document.activeElement.id==={json.dumps(trigger[1:])}"))
                        open_menu(); click('#btnQuickGrid', scroll=False); ready_grid()
                        check(prefix + ' ' + drawer + ' reopen first center opens grid without native/history write', protected(page) == before)
                        click('#igClose'); page.wait_for_function('!InfiniteGridWorkspace.isOpen')
                        if drawer == 'right':
                            page.keyboard.press('Escape')
                    # Preserve a dirty parameter form while feedback is opened,
                    # written, toggled and cancelled using existing semantics.
                    row = page.locator('.object-row[data-kind="parameter"]').first
                    if width <= 900 and not row.is_visible(): click('#toggleLeft', scroll=False)
                    row.dblclick()
                    if width <= 900:
                        page.wait_for_function("document.body.classList.contains('drawer-right-open')")
                    page.wait_for_selector('#paramName')
                    page.locator('#paramName').fill('Uncommitted parameter draft')
                    before_feedback = protected(page)
                    click('#fbButton', scroll=False); page.locator('#fbPanel').wait_for(state='visible')
                    page.locator('#fbNote').fill('Unsubmitted feedback draft')
                    open_menu(); page.keyboard.press('Escape')
                    check(prefix + ' feedback note survives menu Escape and parameter draft survives overlay',
                          page.locator('#fbNote').input_value() == 'Unsubmitted feedback draft' and page.locator('#paramName').input_value() == 'Uncommitted parameter draft' and protected(page) == before_feedback)
                    page.keyboard.press('F8'); page.locator('#fbPanel').wait_for(state='hidden')
                    page.keyboard.press('F8'); page.locator('#fbPanel').wait_for(state='visible')
                    page.locator('#fbNote').fill('Esc cancels this feedback only')
                    page.keyboard.press('Escape'); page.locator('#fbPanel').wait_for(state='hidden')
                    check(prefix + ' feedback button/F8/Esc preserve dirty parameter and native/history',
                          page.locator('#paramName').input_value() == 'Uncommitted parameter draft' and protected(page) == before_feedback)
                    page.wait_for_function("!ParameterUI.previewing && !$('paramConfirm').disabled")
                    click('#paramDiscard'); page.wait_for_function('!ParameterUI.pending')
                    # A grid draft is retained on return; feedback remains
                    # accessible on the canvas and reopen restores raw inputs.
                    open_menu(); click('#btnQuickGrid', scroll=False); ready_grid()
                    page.locator('#igName').fill('Issue123 grid draft')
                    page.locator('#igUStep').fill('915')
                    page.locator('#igVStep').fill('1830')
                    before_grid = protected(page)
                    click('#igClose'); page.wait_for_function('!InfiniteGridWorkspace.isOpen')
                    raw = js(page, "return ReferenceWorkspace.readFeatureAttachment('grid-draft')")
                    click('#fbButton', scroll=False); page.locator('#fbPanel').wait_for(state='visible')
                    page.locator('#fbNote').fill('Grid draft remains pending')
                    page.keyboard.press('Escape'); page.locator('#fbPanel').wait_for(state='hidden')
                    check(prefix + ' feedback retains raw grid draft and native/history', js(page, "return ReferenceWorkspace.readFeatureAttachment('grid-draft')") == raw and protected(page) == before_grid)
                    open_menu(); click('#btnQuickGrid', scroll=False); ready_grid()
                    check(prefix + ' first center reopen restores exact grid inputs', [page.locator(s).input_value() for s in ['#igName', '#igUStep', '#igVStep']] == ['Issue123 grid draft', '915', '1830'])
                    click('#igSaveSource'); page.wait_for_selector('dialog.reference-impact[open]')
                    check(prefix + ' grid preview preserves native/history', protected(page) == before_grid)
                    shot('preview')
                    click('dialog.reference-impact[open] .impact-actions button:first-child'); settled(); ready_grid()
                    check(prefix + ' grid preview cancel preserves draft/native/history', protected(page) == before_grid and page.locator('#igName').input_value() == 'Issue123 grid draft')
                    click('#igSaveSource'); page.wait_for_selector('dialog.reference-impact[open]')
                    click('#impact-confirm'); settled(); ready_grid()
                    committed = protected(page)
                    (out / f'{prefix}-confirmed.scene').write_text(committed['native'])
                    check(prefix + ' confirm writes exactly one grid and one history transaction',
                          sum(line.startswith('grid-system ') for line in committed['native'].splitlines()) == 1 and
                          'u repeat 0 915 v repeat 0 1830' in committed['native'] and
                          ''.join(line + '\n' for line in committed['native'].splitlines() if not line.startswith(('grid-system ', 'canvas-pos grid-system '))) == before_grid['native'] and
                          committed['history']['undoLength'] == before_grid['history']['undoLength'] + 1 and
                          committed['history']['entries'][:-1] == before_grid['history']['entries'] and committed['history']['entries'][-1]['kind'] == 'core' and
                          js(page, "return ReferenceWorkspace.readFeatureAttachment('grid-draft')") is None,
                          {'before': before_grid, 'after': committed})
                    shot('confirmed'); click('#igClose'); page.wait_for_function('!InfiniteGridWorkspace.isOpen')
                    click('#btnUndo', scroll=False); settled()
                    check(prefix + ' grid undo restores exact pre-confirm native', protected(page)['native'] == before_grid['native'])
                    click('#btnRedo', scroll=False); settled()
                    check(prefix + ' grid redo restores exact confirmed native', protected(page)['native'] == committed['native'])
                except Exception:
                    report['errors'].append({'scenario': prefix, 'traceback': traceback.format_exc()})
                    shot('failure')
                finally:
                    context.close()
            report['completed'] = True
        finally:
            browser.close()
    report['passed'] = sum(r['pass'] for r in report['records'])
    report['failed'] = sum(not r['pass'] for r in report['records'])
    (out / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ['completed', 'passed', 'failed', 'errors', 'console']}, ensure_ascii=False), flush=True)
    return int(bool(report['failed'] or report['errors'] or report['console'] or not report['completed']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--chromium', default='/usr/bin/chromium')
    parser.add_argument('--repro', action='store_true')
    parser.add_argument('--width', type=int, choices=[390, 900, 1400])
    raise SystemExit(run(parser.parse_args()))
