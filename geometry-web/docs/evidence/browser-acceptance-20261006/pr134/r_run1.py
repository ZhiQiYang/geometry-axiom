import sys, json, traceback
from r_lib import *
width = int(sys.argv[1]); height = int(sys.argv[2]); port = int(sys.argv[3]) if len(sys.argv) > 3 else 8872
gate("pr134-" + str(width))
R = {}
with sync_playwright() as pw:
    ctx, page, errs = launch(pw, (width, height), f"134-{width}")
    h = mk(page, port); h.open_app(); h.fresh()
    try:
        sid, grids, r1, r1b = build_world(h, width)
        R["R-01"] = {"sourceRuleRefNone": r1, "bindingRuleRefNone": r1b, "sid": sid, "grids": grids}
        page.screenshot(path=str(OUT / f"r01_source_{width}.png"))
        for i in range(2):
            h.face(i + 1); h.focus_cell(CELLS[i])
            lines = h.ev("GridRuleLines.entries().map(l=>({ref:l.ref,segments:l.segments,bounds:l.bounds}))")
            native = h.query(f"grid-rule-query grid {grids[i]} rule 1 cell {' '.join(CELLS[i])}")
            same = json.dumps([l['segments'] for l in lines]) == json.dumps([l['segments'] for l in native['lines']])
            fin = h.ev("[...document.querySelectorAll('.face-rule-line,.face-rule-hit')].length")
            st = h.ev("document.querySelector('[data-rule-focus-status]').textContent")
            R[f"R-02.face{i+1}"] = {"lines": len(lines), "native_same": same, "dom_nodes": fin, "status": st,
                                    "refs_ok": all(l['ref']['appliedGridId'] == grids[i] and l['ref']['systemId'] == sid and l['ref']['cellI'] == CELLS[i][0] and l['ref']['cellJ'] == CELLS[i][1] for l in lines)}
            page.screenshot(path=str(OUT / f"r02_face{i+1}_{width}.png"))
        R["console_errors"] = errs
    except Exception as e:
        R["EXC"] = traceback.format_exc()[-1800:]
        try: page.screenshot(path=str(OUT / f"exc_{width}.png"))
        except Exception: pass
    ctx.close()
(OUT / f"r_run1_{width}.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(R, ensure_ascii=False)[:2500])
