import sys, json, traceback, hashlib, os
from r_lib import *
width = int(sys.argv[1]); height = int(sys.argv[2]); port = int(sys.argv[3]) if len(sys.argv) > 3 else 8872
gate("pr134b-" + str(width))
R = {}
STEP = ['init']
ERRLOC = []
def sec(name):
    def deco(fn):
        STEP[0] = name
        try:
            R[name] = fn()
        except Exception:
            R[name] = {"EXC": traceback.format_exc()[-900:]}
    return deco
with sync_playwright() as pw:
    ctx, page, errs = launch(pw, (width, height), f"134b-{width}")
    h = mk(page, port); h.open_app(); h.fresh()
    cmds = []
    page.on('console', lambda m: ERRLOC.append({'step': STEP[0], 'loc': m.location, 'text': m.text[:120]}) if m.type == 'error' else None)
    page.on("request", lambda r: cmds.append(r.post_data[:80]) if r.method == "POST" and r.url.endswith("/api") and r.post_data else None)
    dump = lambda: h.query('dump')['text']
    sid, grids, _, _ = build_world(h, width)
    histlen = lambda: h.ev("ReferenceWorkspace.history.undo.length")
    for index in range(2):
        h.face(index + 1); h.focus_cell(CELLS[index])
        cell = CELLS[index]

        @sec(f"R-03.face{index+1}")
        def _():
            out = {}
            for axis in ('u', 'v'):
                h.choose('#tbAnchor', f"at-line rule {grids[index]} {sid} 1 {' '.join(cell)} {axis} 0")
                h.fill('#tbA', '20'); h.fill('#tbB', '20'); h.ctl('#tbAnchor')
                pv = h.ev("""(i)=>{const nodes=[...document.querySelectorAll('.fe-anchor-hi,.fe-anchor-band,.fe-anchor-band-label')],info=feAnchorLineInfo(i[0],$('tbAnchor').value),rect=document.querySelector('.fe-anchor-band');return {n:nodes.length,info,finite:nodes.length===3&&nodes.every(n=>[...n.attributes].filter(a=>['x','y','x1','y1','x2','y2','width','height'].includes(a.name)).every(a=>Number.isFinite(Number(a.value)))),rect:rect&&['x','y','width','height'].map(a=>Number(rect.getAttribute(a))),clip:nodes.every(n=>n.closest('[clip-path="url(#face-material-clip)"]'))}}""", [index + 1])
                b = pv['info']['bounds']; r = pv['rect']
                out[axis] = pv['finite'] and len(b) == 4 and pv['clip'] and r[0] >= b[0] and r[1] >= b[1] and r[0] + r[2] <= b[2] and r[1] + r[3] <= b[3]
            return out

        h.ctl('[data-face-tool="select"]')
        before = dump(); cnt = histlen()
        if width == 390:
            @sec(f"R-04.face{index+1}")
            def _():
                h.ctl('#faceInspectorTabs [data-fi-tab="components"]')
                s = h.ev("({controls:[...document.querySelectorAll('.grid-rule-details button,.grid-rule-details input,.grid-rule-details select')].map(n=>({id:n.id,height:n.getBoundingClientRect().height})),panel:[$('faceInspectorContent').scrollWidth,$('faceInspectorContent').clientWidth],page:[document.documentElement.scrollWidth,innerWidth]})")
                small = [c for c in s['controls'] if c['height'] < 44]
                return {"ok": not small and s['panel'][0] <= s['panel'][1] and s['page'][0] <= s['page'][1], "n": len(s['controls']), "small": small, "panel": s['panel'], "page": s['page']}

        @sec(f"R-05.face{index+1}")
        def _():
            h.ctl('#faceReferenceVisibility [data-ref-visible="all"]')
            ok = h.ev("document.querySelectorAll('.face-rule-hit').length===0&&!ReferenceVisibility.anchorVisible($('tbAnchor').value)") and dump() == before and histlen() == cnt
            h.ctl('#faceReferenceVisibility [data-ref-visible="all"]')
            return ok

        @sec(f"R-03b.pick.face{index+1}")
        def _():
            key = f"{grids[index]}:{sid}:1:{':'.join(cell)}:u:0"
            if h.ev("innerWidth<=900&&document.body.classList.contains('drawer-right-open')"): h.ctl('#workspaceToggleRight')
            if h.ev("innerWidth<=900&&document.body.classList.contains('drawer-left-open')"): h.ctl('#workspaceToggleLeft')
            pt = h.ev("""(key)=>{const line=GridRuleLines.entries().find(l=>GridRuleLines.key(l.ref)===key),box=$('faceEditorViewport').getBoundingClientRect();for(const s of line?.segments||[])for(const f of [.5,.3,.7,.15,.85]){const x=box.left+fe.panX+(s[0][0]+(s[1][0]-s[0][0])*f)*fe.zoom,y=box.top+fe.panY+(s[0][1]+(s[1][1]-s[0][1])*f)*fe.zoom,hit=document.elementFromPoint(x,y);if(hit?.classList.contains('face-rule-hit')&&hit.dataset.ruleLineKey===key)return {x,y}}return null}""", key)
            if not pt: return {"ok": False, "why": "no visible hit point"}
            rawb = h.ev("JSON.stringify(ReferenceWorkspace.readFeatureAttachment('grid-draft'))")
            page.mouse.click(pt['x'], pt['y']); page.wait_for_timeout(200)
            sel = h.ev("""(a)=>fe.ruleSelection?.appliedGridId===a[0]&&!!document.querySelector('[data-rule-label]')&&document.querySelector('[data-rule-selected]').textContent.includes(a[1])""", [grids[index], cell[0]])
            page.screenshot(path=str(OUT / f"r03_pick_face{index+1}_{width}.png"))
            return {"ok": bool(sel) and dump() == before and histlen() == cnt and h.ev("JSON.stringify(ReferenceWorkspace.readFeatureAttachment('grid-draft'))") == rawb}

        @sec(f"R-06.jump.face{index+1}")
        def _():
            loops = h.ev(f"oc.bmap[{index+1}]")
            h.ctl('[data-rule-source="1"]'); h.wait("$('infiniteGridWorkspace').open&&!!document.querySelector('[data-ig-rule-key=\"1\"].is-focus')")
            ok1 = h.ev("$('igTitle').textContent===%s" % json.dumps('Authored shared rule ' + str(width))) and dump() == before
            ok2 = json.dumps(h.ev(f"oc.bmap[{index+1}]")) == json.dumps(loops)
            page.screenshot(path=str(OUT / f"r06_jump_face{index+1}_{width}.png"))
            return {"ok": ok1 and ok2, "editor_and_zero_write": ok1, "bmap_kept": ok2}
    # source edit: R-07
    @sec("R-07")
    def _():
        h.fill('#igUStep', '1200'); before = dump(); cnt = histlen(); h.ctl('#igSaveSource'); h.impact()
        two = h.ev("document.querySelectorAll('[data-impact-binding]').length===2")
        h.cancel(); cancel_ok = dump() == before and histlen() == cnt
        h.ctl('#igSaveSource'); h.impact(); h.confirm(); changed = dump(); one = histlen() == cnt + 1
        key = h.query('objects')['gridSystems'][0]['rules'][0]['ruleKey'] == 1
        h.leave(); h.ctl('#btnUndo'); h.settled(); u = dump() == before
        h.ctl('#btnRedo'); h.settled(); r = dump() == changed
        return {"ok": two and cancel_ok and changed != before and one and key and u and r, "two_bindings_in_preview": two, "cancel_zero": cancel_ok, "single_step": one, "undo": u, "redo": r}
    # R-08 dense
    @sec("R-08")
    def _():
        sid_ = sid
        h.leave(); h.ctl(f'#objectList .object-row[data-kind="grid-system"][data-id="{sid_}"]'); h.ctl('#gridObjectOpen'); h.wait("$('infiniteGridWorkspace').open&&!$('igRuleAdd').disabled")
        h.fill('#igUStep', '6'); h.fill('#igVStep', '4'); h.ctl('#igSaveSource'); h.impact(); h.confirm(); h.face(1); w0 = dump()
        sample = h.ev("({n:GridRuleLines.entries().length,incomplete:!!$('feRuleDensity')?.textContent.includes('抽樣未完整')})")
        zero = dump() == w0
        h.focus_cell(CELLS[0]); exact = h.ev("GridRuleLines.entries().length===3&&GridRuleLines.entries().every(l=>l.ref.cellI==='-2'&&l.ref.cellJ==='1')")
        page.screenshot(path=str(OUT / f"r08_dense_{width}.png"))
        return {"ok": sample['n'] <= 96 and sample['incomplete'] and zero and exact, "sample": sample, "zero_write": zero, "exact_ok": exact}
    # R-16 save zip -> new -> open
    @sec("R-16")
    def _():
        h.leave(); dumpA = dump()
        page.evaluate("window.__sfp=Object.getOwnPropertyDescriptor(window,'showSaveFilePicker');Object.defineProperty(window,'showSaveFilePicker',{value:undefined,configurable:true})")
        with page.expect_download(timeout=30000) as dl:
            h.ctl('#projectBar [data-project-action="save"]')
        d = dl.value; tmp = ROOT / f"zip-134-{width}.gcanvas"; d.save_as(str(tmp))
        page.evaluate("if(window.__sfp)Object.defineProperty(window,'showSaveFilePicker',window.__sfp);else delete window.showSaveFilePicker")
        data = tmp.read_bytes()
        import zipfile, io
        names = zipfile.ZipFile(io.BytesIO(data)).namelist()
        h.fresh(); emp = h.ev("oc.gridSystems.length===0&&oc.gridBindings.length===0&&oc.faces.length===0")
        h.ctl('#fileMenuBtn'); h.ctl('#btnOpenProject') if False else None
        page.set_input_files('#projectFile', str(tmp)); h.settled(); h.wait("oc.gridBindings.length===2")
        same = dump() == dumpA
        h.face(1); h.focus_cell(CELLS[0]); n1 = h.ev("GridRuleLines.entries().length")
        page.screenshot(path=str(OUT / f"r16_reopened_{width}.png"))
        return {"ok": emp and same and n1 == 3, "file": tmp.name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "zip_entries": names[:12], "fresh_before_open": emp, "dump_identical": same, "reopened_face_lines": n1, "download_name": d.suggested_filename}
    R["console_errors"] = errs
    R["error_locations"] = ERRLOC
    R["post_cmds_sample"] = len(cmds)
    ctx.close()
(OUT / f"r_run2_{width}.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(R, ensure_ascii=False)[:3500])
