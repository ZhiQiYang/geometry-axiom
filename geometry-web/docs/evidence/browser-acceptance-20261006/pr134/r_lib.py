import sys, json
sys.path.insert(0, r"D:/geometry-axiom-bqa/geometry-web/docs/evidence/browser-acceptance-20261006/env")
from common import *
OUT = EVID / "pr134"
CELLS = [['-2', '1'], ['9007199254740993', '-9007199254740995']]


def mk(page, port):
    URL = f"http://127.0.0.1:{port}/"

    class H: pass
    h = H()

    def open_app():
        page.goto(URL, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_function("typeof apiRequest==='function' && document.getElementById('app') && !document.getElementById('app').inert", timeout=90000)
        page.wait_for_timeout(800)

    def ev(js, *a): return page.evaluate(js, *a) if a else page.evaluate(js)
    def wait(js, t=25000): page.wait_for_function(js, timeout=t)

    def fixture(cmd):
        return page.evaluate("""async(cmd)=>{let r=await apiRequest('line '+cmd);if(r.preview){if(!r.preview.valid)throw Error(JSON.stringify(r));r=await apiRequest('line confirm '+r.preview.token);}if(!r.ok)throw Error(JSON.stringify(r));await renderObjects();return true;}""", cmd)

    def settled(): wait("!oc.busy&&!ReferenceWorkspace.busy")

    def ctl(sel, **kw):
        if ev("innerWidth<=900"):
            root = page.evaluate("""(s)=>{const n=document.querySelector(s);return n?.closest('#objectList')?'left':n?.closest('#inspectorContent')?'right':n?.closest('.face-inspector-panel')?'face':n?.closest('.face-layer-panel')?'face-left':null}""", sel)
            op = lambda c: page.evaluate("(c)=>document.body.classList.contains(c)", c)
            if root == 'left' and not op('drawer-left-open'): page.click('#toggleLeft')
            if root == 'right':
                if op('canvas-composition'):
                    if op('drawer-left-open'): page.click('#toggleLeft')
                elif not op('drawer-right-open'): page.click('#toggleRight')
            if root == 'face' and not op('drawer-right-open'): page.click('#workspaceToggleRight')
            if root == 'face-left' and not op('drawer-left-open'): page.click('#workspaceToggleLeft')
            if sel.startswith('.face-rule-hit') and op('drawer-right-open'): page.click('#workspaceToggleRight')
        if page.evaluate("(s)=>document.querySelector(s)?.closest('#createObjectPop')?.hidden===true", sel):
            page.click('#mobileCreateObject' if ev("innerWidth<=900") else '#btnCreateObject')
        for attempt in range(4):
            try:
                loc = page.locator(sel).first
                loc.scroll_into_view_if_needed(timeout=8000); loc.click(timeout=8000, **kw); break
            except Exception:
                if attempt == 3: raise
                page.wait_for_timeout(400)
        page.wait_for_timeout(80)

    def fill(sel, v):
        ctl(sel); page.locator(sel).first.fill(str(v)); page.wait_for_timeout(60)

    def choose(sel, v):
        n = page.evaluate("(a)=>[...document.querySelector(a[0]).options].filter(o=>!o.disabled).findIndex(o=>o.value===a[1])", [sel, str(v)])
        if n < 0: raise Exception('Missing enabled option ' + sel + ' ' + str(v))
        ctl(sel); page.keyboard.press('Home')
        for _ in range(n): page.keyboard.press('ArrowDown')
        page.keyboard.press('Enter')
        wait("document.querySelector(%s).value===%s" % (json.dumps(sel), json.dumps(str(v)))); page.wait_for_timeout(120)

    def impact(): wait("!!document.querySelector('.reference-impact[open]')")

    def confirm():
        ctl('#impact-confirm'); wait("!document.querySelector('.reference-impact[open]')"); settled()

    def cancel():
        ctl('.reference-impact .impact-actions button:first-child'); wait("!document.querySelector('.reference-impact[open]')"); settled()

    def query(cmd): return page.evaluate("(c)=>apiRequest(c).then(r=>{if(!r.ok)throw Error(JSON.stringify(r));return r;})", cmd)

    def leave():
        if ev("$('infiniteGridWorkspace').open"): ctl('#igClose')
        if ev("!!oc.focus"): ctl('#workspaceBackButton')
        settled()

    def face(bid):
        leave(); ctl(f'#objectList .object-row[data-kind="boundary"][data-id="{bid}"]'); ctl('#inspEnter')
        wait(f"oc.edit?.bid=={bid}"); wait("GridRuleLines.entries().some(l=>l.segments.length)")

    def focus_cell(cell, rule=1):
        ctl('#faceInspectorTabs [data-fi-tab="components"]'); wait("!!document.querySelector('[data-rule-exact]')")
        choose('[data-rule-focus-key]', rule); fill('[data-rule-cell-i]', cell[0]); fill('[data-rule-cell-j]', cell[1]); ctl('[data-rule-exact]')
        wait("GridRuleLines.entries().every(l=>l.cell.join(',')==='%s'&&l.ruleKey===%d)&&document.querySelector('[data-rule-focus-status]').textContent.includes('已核對')" % (",".join(cell), rule))

    def fresh():
        leave(); ctl('#fileMenuBtn')
        page.once("dialog", lambda d: d.accept())
        ctl('#btnNewProject'); settled(); page.wait_for_timeout(500)
        assert ev("oc.gridSystems.length===0&&oc.gridBindings.length===0&&oc.faces.length===0"), 'not fresh'

    h.fresh = fresh
    for n in "open_app ev wait fixture settled ctl fill choose impact confirm cancel query leave face focus_cell".split():
        setattr(h, n, locals()[n])
    return h


def build_world(h, width):
    for bid in (1, 2):
        h.fixture(f"boundary {bid} outline " + ('0,0 1200,0 1200,800 0,800' if bid == 1 else '0,0 1200,0 1200,800 800,800 800,600 0,600 hole 170,80 170,280 230,280 230,80'))
        h.fixture(f"placement {bid} on boundary {bid} origin 0 0 {(bid-1)*2000} u +x v +y")
    h.ctl('#btnQuickGrid' if h.ev("innerWidth<=900") else '#btnNewGridSystem'); h.wait("!!$('igName')&&!$('igName').disabled")
    h.fill('#igName', f'Authored shared rule {width}'); h.ctl('#igSaveSource'); h.impact(); h.confirm()
    sid = h.query('objects')['gridSystems'][0]['id']
    h.ctl('#igRuleAdd'); h.fill('#igRuleName', 'Native inner lines'); h.ctl('#igRulePreview'); h.impact(); h.confirm()
    h.wait("!!document.querySelector('[data-ig-source-rule=\"1\"]')")
    r1 = h.ev("document.querySelectorAll('[data-ig-source-rule]').length>0&&[...document.querySelectorAll('[data-ig-source-rule]')].every(n=>n.dataset.igRuleRef==='none')")
    r1b = []
    for i in range(2):
        if i: h.ctl('#igEditSource')
        h.ctl('#igNewBinding'); h.choose('#igBoundary', i + 1); h.wait("$('igVertex').options.length>1&&!$('igCellI').disabled")
        h.choose('#igVertex', 'outer:0'); h.fill('#igCellI', CELLS[i][0]); h.fill('#igCellJ', CELLS[i][1]); h.ctl('#igSaveBinding'); h.impact(); h.confirm()
        h.wait("!!document.querySelector('[data-ig-result-rule=\"1\"]')")
        r1b.append(h.ev("[...document.querySelectorAll('[data-ig-result-rule]')].every(n=>n.dataset.igRuleRef==='none')"))
        h.choose('#igSurface', i + 1); h.ctl('#igApplyBinding'); h.impact(); h.confirm()
    refs = h.query('references'); grids = [g['id'] for g in refs['grids']]
    return sid, grids, r1, r1b
