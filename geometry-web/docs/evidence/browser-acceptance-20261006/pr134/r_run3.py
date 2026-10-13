import sys, json, traceback
from r_lib import *
width = int(sys.argv[1]); height = int(sys.argv[2]); port = int(sys.argv[3]) if len(sys.argv) > 3 else 8872
gate("pr134c-" + str(width))
R = {}
def sec(name):
    def deco(fn):
        try: R[name] = fn()
        except Exception: R[name] = {"EXC": traceback.format_exc()[-900:]}
    return deco
with sync_playwright() as pw:
    ctx, page, errs = launch(pw, (width, height), f"134c-{width}")
    h = mk(page, port); h.open_app(); h.fresh()
    posts = []
    page.on("request", lambda r: posts.append(r.post_data or "") if r.method == "POST" and r.url.endswith("/api") else None)
    dump = lambda: h.query('dump')['text']
    histlen = lambda: h.ev("ReferenceWorkspace.history.undo.length")
    # R-12 first: a face with NO source rule
    @sec("R-12")
    def _():
        h.fixture("boundary 1 outline 0,0 1200,0 1200,800 0,800"); h.fixture("placement 1 on boundary 1 origin 0 0 0 u +x v +y")
        n0 = len(posts)
        h.ctl('#objectList .object-row[data-kind="boundary"][data-id="1"]'); h.ctl('#inspEnter'); h.wait("oc.edit?.bid==1"); page.wait_for_timeout(1500)
        h.ctl('[data-face-tool="grid"]'); page.wait_for_timeout(800); h.ctl('[data-face-tool="select"]'); page.wait_for_timeout(500)
        q = [p for p in posts[n0:] if 'grid-rule-query' in p]
        page.screenshot(path=str(OUT / f"r12_plain_face_{width}.png"))
        return {"ok": len(q) == 0, "posts_after_enter": len(posts) - n0, "rule_queries": len(q)}
    h.fresh()
    sid, grids, _, _ = build_world(h, width)
    h.face(1); h.focus_cell(CELLS[0])
    @sec("R-09.options")
    def _():
        h.ctl('[data-face-tool="timber"]')
        opts = h.ev("[...$('tbAnchor').options].map(o=>o.text)")
        hit = [o for o in opts if '來源規則' in o or sid and 'Native' in o]
        return {"ok": len(hit) > 0, "n_options": len(opts), "rule_options": hit[:4]}
    @sec("R-10")
    def _():
        h.choose('#tbAnchor', f"at-line rule {grids[0]} {sid} 1 {' '.join(CELLS[0])} u 0")
        h.fill('#tbA', '20'); h.fill('#tbB', '20'); h.choose('#tbRole', 'primary'); h.choose('#tbDir', '+v')
        c0 = h.query('objects'); t0 = len(c0.get('timbers', [])); hc = histlen()
        h.ctl('#tbPlace'); page.wait_for_timeout(1500); h.settled()
        t1 = len(h.query('objects').get('timbers', [])); toast = h.ev("(document.querySelector('.toast')||{}).textContent||''")
        page.screenshot(path=str(OUT / f"r10_place_{width}.png"))
        return {"placed": t1 - t0, "history_delta": histlen() - hc, "toast": toast[:160], "ok": (t1 - t0 == 1 and histlen() - hc == 1)}
    @sec("R-11")
    def _():
        # source now referenced by timber placed on rule line: source edit preview must not allow confirm
        h.leave(); h.ctl(f'#objectList .object-row[data-kind="grid-system"][data-id="{sid}"]'); h.ctl('#gridObjectOpen'); h.wait("$('infiniteGridWorkspace').open&&!$('igRuleAdd').disabled")
        before = dump(); hc = histlen(); h.fill('#igUStep', '900'); h.ctl('#igSaveSource'); page.wait_for_timeout(1200)
        op = h.ev("!!document.querySelector('.reference-impact[open]')")
        dis = h.ev("(document.querySelector('#impact-confirm')||{}).disabled")
        txt = h.ev("(document.querySelector('.reference-impact')||{innerText:''}).innerText.slice(0,260)")
        page.screenshot(path=str(OUT / f"r11_impact_{width}.png"))
        if op: h.cancel()
        return {"impact_open": op, "confirm_disabled": dis, "zero_write": dump() == before and histlen() == hc, "text": txt, "ok": op and dis is True and dump() == before}
    @sec("R-17.keyboard")
    def _():
        h.leave(); h.face(1); h.ctl('#faceInspectorTabs [data-fi-tab="components"]'); h.wait("!!document.querySelector('[data-rule-exact]')")
        h.ctl('[data-rule-cell-i]'); page.keyboard.press('Control+a'); page.keyboard.type('-2'); page.keyboard.press('Tab'); page.keyboard.press('Control+a'); page.keyboard.type('1')
        seq = []
        for _i in range(3):
            page.keyboard.press('Tab'); seq.append(h.ev("(()=>{const e=document.activeElement;return [e.tagName,e.id||'',e.getAttribute('data-rule-exact')!==null?'exact':'']})()"))
        # focus exact and press Enter
        h.ev("document.querySelector('[data-rule-exact]').focus()"); page.keyboard.press('Enter'); page.wait_for_timeout(800)
        done = h.ev("document.querySelector('[data-rule-focus-status]').textContent")
        ol = h.ev("(()=>{document.querySelector('[data-rule-exact]').focus();const s=getComputedStyle(document.querySelector('[data-rule-exact]'));return s.outlineStyle+' '+s.outlineWidth})()")
        hit_tab = h.ev("[...document.querySelectorAll('.face-rule-hit')].map(n=>n.tabIndex).slice(0,3)")
        return {"ok": '已核對' in done or '完成' in done, "tab_seq": seq, "status_after_enter": done, "exact_outline": ol, "face-rule-hit_tabIndex": hit_tab}
    R["console_errors"] = errs
    ctx.close()
(OUT / f"r_run3_{width}.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(R, ensure_ascii=False)[:3500])
