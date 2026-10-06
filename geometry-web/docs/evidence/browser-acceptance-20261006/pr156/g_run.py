import sys, json, traceback
sys.path.insert(0, r"D:/geometry-axiom-bqa/geometry-web/docs/evidence/browser-acceptance-20261006/pr134")
from r_lib import *
OUT = EVID / "pr156"
port = int(sys.argv[1]); tag = sys.argv[2]; widths = [int(x) for x in sys.argv[3].split(",")]
gate("g-" + tag)
R = {}
HOLD = """(stage)=>{window.__held=[];window.__of=window.__of||window.fetch;const of=window.__of;window.fetch=function(u,o){try{if(String(u).endsWith('/api')&&o&&typeof o.body==='string'){const c=JSON.parse(o.body).cmd||'';if(stage==='snap'&&/^snap /.test(c)||stage==='newid'&&/^newid/.test(c)){return new Promise(res=>{window.__held.push(()=>res(of.call(this,u,o)))})}}}catch(e){}return of.apply(this,arguments)};return true}"""
UNHOLD = "()=>{if(window.__of)window.fetch=window.__of}"
with sync_playwright() as pw:
    for width in widths:
        height = 804 if width > 900 else 844
        ctx, page, errs = launch(pw, (width, height), f"g-{tag}-{width}")
        h = mk(page, port); h.open_app()
        dump = lambda: h.query('dump')['text']
        nguides = lambda: len(h.query('references')['guides'])
        def setup():
            h.fresh()
            h.fixture("boundary 1 outline 0,0 1200,0 1200,800 0,800"); h.fixture("placement 1 on boundary 1 origin 0 0 0 u +x v +y")
            h.fixture("spec support_1 400"); h.fixture("spec support_2 300")
            h.ctl('#objectList .object-row[data-kind="boundary"][data-id="1"]'); h.ctl('#inspEnter'); h.wait("oc.edit?.bid==1"); page.wait_for_timeout(1500)
            h.ctl('[data-face-tool="guide"]')
        def center():
            return tuple(h.ev("()=>{const b=$('faceEditorViewport').getBoundingClientRect();return [b.left+fe.panX+400*fe.zoom,b.top+fe.panY+300*fe.zoom]}"))
        def gesture(entry):
            x, y = center()
            if entry == 'picker':
                page.mouse.click(x, y); page.wait_for_timeout(300)
                page.locator('#feGuidePick button[data-axis="u"]').click()
            else:
                page.mouse.move(x, y); page.mouse.down(); page.mouse.move(x + 30, y, steps=3); page.mouse.move(x + 90, y, steps=3); page.mouse.up()
        def run(name, stage, entry, back=True, reenter=False, hold=True):
            try:
                setup(); g0 = nguides(); w0 = dump(); hc = h.ev("ReferenceWorkspace.history.undo.length")
                if hold: h.ev(HOLD, stage)
                gesture(entry); page.wait_for_timeout(700)
                held = h.ev("(window.__held||[]).length") if hold else 0
                if back:
                    h.ctl('#workspaceBackButton'); page.wait_for_timeout(500)
                    if reenter:
                        h.ctl('#objectList .object-row[data-kind="boundary"][data-id="1"]'); h.ctl('#inspEnter'); h.wait("oc.edit?.bid==1"); page.wait_for_timeout(800)
                if hold: h.ev("(window.__held||[]).forEach(f=>f());window.__held=[]")
                page.wait_for_timeout(2000); h.ev(UNHOLD)
                g1 = nguides(); same = dump() == w0
                focus = h.ev("oc.focus?JSON.stringify(oc.focus):null")
                page.screenshot(path=str(OUT / f"g_{tag}_{name}_{width}.png"))
                return {"held": held, "guides_before": g0, "guides_after": g1, "world_unchanged": same, "focus_after": focus, "history_len_same": h.ev("ReferenceWorkspace.history.undo.length") == hc}
            except Exception:
                try: h.ev(UNHOLD)
                except Exception: pass
                return {"EXC": traceback.format_exc()[-700:]}
        # G-01/G-02 baseline happy path
        for entry in ('picker', 'drag'):
            R[f"G-01/02.happy.{entry}.{width}"] = run(f"happy_{entry}", None, entry, back=False, hold=False)
        # undo/redo for the last happy guide
        try:
            setup(); g0 = nguides(); gesture('picker')
            for _i in range(25):
                page.wait_for_timeout(200)
                if nguides() > g0: break
            g1 = nguides()
            h.leave(); h.ctl('#btnUndo'); h.settled(); g2 = nguides(); h.ctl('#btnRedo'); h.settled(); g3 = nguides()
            R[f"G-01.undo_redo.{width}"] = {"counts(before,after,undo,redo)": [g0, g1, g2, g3], "ok": [g0, g1, g2, g3] == [g0, g0 + 1, g0, g0 + 1]}
        except Exception: R[f"G-01.undo_redo.{width}"] = {"EXC": traceback.format_exc()[-500:]}
        for stage in ('snap', 'newid'):
            for entry in ('picker', 'drag'):
                R[f"G-03.{stage}.{entry}.{width}"] = run(f"back_{stage}_{entry}", stage, entry)
        R[f"G-04.reenter.snap.picker.{width}"] = run("reenter_snap_picker", 'snap', 'picker', reenter=True)
        R[f"G-04.reenter.newid.drag.{width}"] = run("reenter_newid_drag", 'newid', 'drag', reenter=True)
        # G-07 newid rejection
        try:
            setup(); g0 = nguides(); w0 = dump()
            h.ev("""()=>{window.__of=window.__of||window.fetch;const of=window.__of;window.fetch=function(u,o){try{if(String(u).endsWith('/api')&&o&&typeof o.body==='string'&&/^newid/.test(JSON.parse(o.body).cmd)){return Promise.resolve(new Response(JSON.stringify({ok:false,error:'injected newid failure'}),{status:200,headers:{'Content-Type':'application/json'}}))}}catch(e){}return of.apply(this,arguments)}}""")
            gesture('picker'); page.wait_for_timeout(1200); h.ev(UNHOLD)
            toast = h.ev("document.getElementById('toastRegion').textContent")
            R[f"G-07.newid_reject.{width}"] = {"ok": nguides() == g0 and dump() == w0, "toast": toast[:120], "injection": "fetch override (test instrument)"}
        except Exception: R[f"G-07.newid_reject.{width}"] = {"EXC": traceback.format_exc()[-500:]}
        R[f"console_errors.{width}"] = errs
        ctx.close()
(OUT / f"g_results_{tag}.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
for k, v in R.items(): print(k, json.dumps(v, ensure_ascii=False)[:230])
