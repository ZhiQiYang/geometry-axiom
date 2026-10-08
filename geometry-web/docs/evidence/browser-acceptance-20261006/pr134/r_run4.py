import sys, json, traceback
from r_lib import *
width = int(sys.argv[1]); height = int(sys.argv[2]); port = int(sys.argv[3]) if len(sys.argv) > 3 else 8872
gate("pr134d-" + str(width))
R = {}
def sec(name):
    def deco(fn):
        try: R[name] = fn()
        except Exception: R[name] = {"EXC": traceback.format_exc()[-1200:]}
    return deco
with sync_playwright() as pw:
    ctx, page, errs = launch(pw, (width, height), f"134d-{width}")
    h = mk(page, port); h.open_app(); h.fresh()
    bad = []
    page.on('response', lambda r: bad.append((r.status, r.url)) if r.status >= 400 else None)
    dump = lambda: h.query('dump')['text']
    histlen = lambda: h.ev("ReferenceWorkspace.history.undo.length")
    sid, grids, _, _ = build_world(h, width)
    h.leave(); h.ctl(f'#objectList .object-row[data-kind="grid-system"][data-id="{sid}"]'); h.ctl('#gridObjectOpen'); h.wait("$('infiniteGridWorkspace').open&&!$('igRuleAdd').disabled")
    h.leave()  # defaults are already u=600 v=400
    for id_, edge in [(81, 'e0'), (82, 'e2')]:
        h.fixture(f"timber {id_} 20 20 role boundary"); h.fixture(f"place {id_} on 1 at-face {edge} +u +n")
    for id_, pos in [(91, 120), (92, 480)]:
        h.fixture(f"spec support_{id_} {pos}"); h.fixture(f"guide {id_} 1 v spec:support_{id_}"); h.fixture(f"timber {id_} 20 20 role primary"); h.fixture(f"place {id_} on 1 at-line guide {id_} +v +n")
    h.face(1); h.focus_cell(CELLS[0]); h.ctl('#faceInspectorTabs [data-fi-tab="components"]')
    expr = f"gridrule:{grids[0]}:{sid}:1:-2:1:v:0"
    @sec("R-09.guide")
    def _():
        h.choose('#refGuideAxis', 'u'); h.choose('#refGuideMode', 'source'); h.choose('#refGuideSource', expr); h.ctl('#refGuideCreate'); h.settled()
        h.wait("fe.guides.some(g=>g.expression===%s)" % json.dumps(expr))
        ok = any(g['expression'] == expr and g['axis'] == 'u' and g['off'] == 200 for g in h.query('references')['guides'])
        # wrong source
        w = dump(); hc = histlen()
        h.choose('#refGuideMode', 'advanced'); h.fill('#refGuideExpr', f"gridrule:{grids[0]}:{sid+99}:1:-2:1:v:0"); h.ctl('#refGuideCreate'); h.impact()
        rej = h.ev("$('impact-confirm').disabled&&document.querySelector('.reference-impact').textContent.includes('WRONG_SOURCE')")
        zero = dump() == w
        page.screenshot(path=str(OUT / f"r09_wrong_source_{width}.png"))
        h.cancel(); hc_same = histlen() == hc; h.choose('#refGuideMode', 'source')
        return {"ok": ok and rej and zero and hc_same, "true_gridrule_guide": ok, "wrong_source_rejected": rej, "zero_write": zero, "history_unchanged_after_cancel": hc_same}
    @sec("R-10")
    def _():
        h.focus_cell(CELLS[0]); anchor = f"at-line rule {grids[0]} {sid} 1 -2 1 v 0"
        h.choose('#tbAnchor', anchor); h.fill('#tbA', '20'); h.fill('#tbB', '20'); h.choose('#tbDir', '+u'); h.choose('#tbRole', 'secondary')
        h.ctl('#tbNewSegmentDetails > summary'); h.fill('#tbSelector', 'between t91 t9999')
        w = dump(); hc = histlen(); h.ctl('#tbPlace'); h.settled()
        h.wait("$('toastRegion').textContent.includes('cannot be reconstructed')")
        rej_zero = dump() == w and histlen() == hc
        kept = h.ev("(a)=>$('tbAnchor').value===a&&$('tbA').value==='20'&&$('tbB').value==='20'&&$('tbRole').value==='secondary'&&$('tbSelector').value==='between t91 t9999'", anchor)
        h.fill('#tbSelector', 'between t91 t92'); h.ctl('#tbPlace'); h.settled()
        h.wait("fe.timbers.some(t=>t.definition?.anchor===%s)" % json.dumps(anchor))
        delta = histlen() - hc
        nt = lambda: len(h.query('references')['timbers'])
        n_with = nt(); h.leave(); h.ctl('#btnUndo'); h.settled(); n_undo = nt(); h.ctl('#btnRedo'); h.settled(); n_redo = nt()
        single = (n_with - n_undo == 1 and n_redo == n_with); h.face(1)
        t = [t for t in h.query('references')['timbers'] if t['definition']['anchor'] == anchor][0]
        geo = t['role'] == 'secondary' and t['geometry']['A'] == 20 and t['geometry']['B'] == 20 and t['geometry']['dir'] == '+u' and t['definition']['selector'] == 'between t91 t92'
        h.focus_cell(CELLS[0]); cnt = h.ev("document.querySelector('[data-rule-summary=\"1\"]').textContent")
        page.screenshot(path=str(OUT / f"r10_placed_{width}.png"))
        return {"ok": rej_zero and kept and single and geo and '1 參考線／1 角材' in cnt, "rejected_zero_write": rej_zero, "form_kept": kept, "retry_single_step": single, "history_len_delta(unreliable if capped)": delta, "timbers_with_undo_redo": [n_with, n_undo, n_redo], "geometry": geo, "summary": cnt[:120]}
    @sec("R-11")
    def _():
        h.leave(); h.ctl(f'#objectList .object-row[data-kind="grid-system"][data-id="{sid}"]'); h.ctl('#gridObjectOpen'); h.wait("$('infiniteGridWorkspace').open&&!$('igRuleAdd').disabled")
        before = dump(); hc = histlen(); h.fill('#igUStep', '500'); h.ctl('#igSaveSource'); h.impact()
        dis = h.ev("document.querySelector('#impact-confirm').disabled")
        txt = h.ev("document.querySelector('.reference-impact').innerText.slice(0,300)")
        page.screenshot(path=str(OUT / f"r11_impact_locked_{width}.png"))
        h.cancel()
        return {"ok": dis is True and dump() == before and histlen() == hc, "confirm_disabled": dis, "text": txt}
    # R-15 delayed newid: delay POST /api 'newid' then switch context
    @sec("R-15.newid_back")
    def _():
        h.leave(); h.face(1); h.ctl('[data-face-tool="timber"]')
        released = {"go": False}
        gate_js = """()=>{window.__held=[];const of=window.fetch;window.__of=of;window.fetch=function(u,o){try{if(String(u).endsWith('/api')&&o&&typeof o.body==='string'&&/^\\s*newid/.test(o.body)){return new Promise(res=>{window.__held.push(()=>res(of.call(this,u,o)))})}}catch(e){}return of.apply(this,arguments)};return true}"""
        h.ev(gate_js)
        w = dump(); hc = histlen()
        # trigger a flow that requests newid: new timber via form uses newid
        h.fill('#tbA', '20'); h.fill('#tbB', '20')
        h.ctl('#tbPlace'); page.wait_for_timeout(800)
        held = h.ev("window.__held.length")
        h.ctl('#workspaceBackButton'); page.wait_for_timeout(500)
        h.ev("window.__held.forEach(f=>f());window.__held=[]"); page.wait_for_timeout(1500)
        h.ev("window.fetch=window.__of")
        return {"info_only": True, "held_newid_requests": held, "world_unchanged": dump() == w, "history_unchanged": histlen() == hc, "note": "placement form may not use newid; held==0 means recipe did not exercise the guarded path"}
    R["console_errors"] = errs; R["http_4xx"] = bad
    ctx.close()
(OUT / f"r_run4_{width}.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(R, ensure_ascii=False)[:3800])
