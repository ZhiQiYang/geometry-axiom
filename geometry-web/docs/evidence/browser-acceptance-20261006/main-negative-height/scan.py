import sys, json, traceback
sys.path.insert(0, r"D:/geometry-axiom-bqa/geometry-web/docs/evidence/browser-acceptance-20261006/pr134")
from r_lib import *
OUT = EVID / "main-negative-height"
width = int(sys.argv[1]); height = int(sys.argv[2]); port = int(sys.argv[3]) if len(sys.argv) > 3 else 8875
gate("negh-" + str(width))
R = {"viewport": [width, height], "setup": {}, "options": [], "notes": []}
with sync_playwright() as pw:
    ctx, page, errs = launch(pw, (width, height), f"negh-{width}")
    h = mk(page, port); h.open_app(); h.fresh()
    # --- scene (fixture commands = apiRequest 'line ...', as in existing harness) ---
    cmds = [
        'boundary 1 outline 0,0 1200,0 1200,800 0,800 hole 170,80 170,280 230,280 230,80',
        'placement 1 on boundary 1 origin 0 0 0 u +x v +y',
        'grid 1 on 1 main-along v u 400 800 v 300 600',
        'subgrid 0 parent 1 cell u min line:0 v min line:0 divisions u 2 v 2',
        'spec s_a 120', 'spec s_b 1190', 'spec s_c 5', 'spec s_d 1500', 'spec s_e -300', 'spec s_f 5000',
        'guide 11 1 v spec:s_a', 'guide 12 1 v spec:s_b', 'guide 13 1 v spec:s_c',
        'guide 14 1 v spec:s_d', 'guide 15 1 v spec:s_e', 'guide 16 1 u spec:s_c', 'guide 17 1 u spec:s_f',
        'timber 81 20 20 role boundary', 'place 81 on 1 at-face e0 +u +n',
    ]
    for c in cmds:
        try: h.fixture(c); R["setup"][c] = "ok"
        except Exception as e: R["setup"][c] = "FAIL " + str(e)[:200]
    page.wait_for_timeout(500)
    R["setup"]["state"] = h.ev("({grids:fe?.grids?.length,guides:null})") if False else None
    try:
        page.evaluate("async()=>{await enterFocus('face',1);feSetTool('timber');}")
        page.wait_for_timeout(800)
    except Exception as e:
        R["setup"]["enter"] = "FAIL " + str(e)[:300]
    R["setup"]["state"] = h.ev("({tool:fe.tool,grids:fe.grids.map(g=>[g.id,g.kind,g.bounds||null]),guides:fe.guides.map(g=>[g.id,g.axis,g.off]),timbers:fe.timbers.length,bid:oc.edit&&oc.edit.bid})")
    values = h.ev("[...$('tbAnchor').options].map(o=>o.value)")
    R["anchor_values"] = values
    page.screenshot(path=str(OUT / f"s0_face_{width}.png"))
    for A in (20, 2000):
        for v in values:
            n0 = len(errs)
            res = h.ev("""(a)=>{const [val,A]=a;const sel=$('tbAnchor');sel.value=val;sel.dispatchEvent(new Event('input',{bubbles:true}));sel.dispatchEvent(new Event('change',{bubbles:true}));
              $('tbA').value=String(A);$('tbB').value=String(A);for(const id of ['tbA','tbB']){$(id).dispatchEvent(new Event('input',{bubbles:true}));$(id).dispatchEvent(new Event('change',{bubbles:true}));}
              try{drawFaceEditor();}catch(e){var thrown=String(e)}
              const bands=[...document.querySelectorAll('.fe-anchor-band')].map(r=>['x','y','width','height'].map(k=>r.getAttribute(k)));
              let info=null,cr=null;try{info=feAnchorLineInfo(oc.edit.bid,val);cr=feAnchorCrossRange(oc.edit.bid,val,A)}catch(e){info='EXC '+e}
              return {selected:sel.value===val,bands,info,cr,thrown:typeof thrown==='undefined'?null:thrown}}""", [v, A])
            page.wait_for_timeout(120)
            res["value"] = v; res["A"] = A
            res["errors"] = errs[n0:]
            res["negative"] = any(float(x) < 0 for b in res["bands"] for x in b[2:] if x not in (None, ''))
            R["options"].append(res)
        if A == 20: page.screenshot(path=str(OUT / f"s1_last_A20_{width}.png"))
    R["console_errors_all"] = errs
    ctx.close()
(OUT / f"scan_{width}.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
neg = [(o["A"], o["value"]) for o in R["options"] if o["negative"] or o["errors"]]
print("OPTIONS", len(R["options"]), "NEG/ERR", neg)
