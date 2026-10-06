import re
from common import *

TERMS = ["cell", "格內位置", "對齊頂點", "對齊格子", "對齊邊界", "對齊位置", "主支", "副支", "主網格", "副網格", "子網格", "格子", "配置設定", "網格配置", "網格來源", "頂點", "九宮", "錨點"]

def text_of(page, sel):
    return page.evaluate("s => { const e=document.querySelector(s); return e ? e.innerText : null; }", sel)

def term_report(txt):
    if not txt: return None
    counts = {t: len(re.findall(re.escape(t) if t != "cell" else r"(?i)cell", txt)) for t in TERMS}
    lines = [l.strip() for l in txt.splitlines() if l.strip() and any((t.lower() in l.lower()) for t in TERMS)]
    return {"counts": {k: v for k, v in counts.items() if v}, "lines": lines[:40], "chars": len(txt)}

STEP = {}
res = {"steps": STEP}
def mark(k, v=True): STEP[k] = v; save("stage_g.json", res)

with sync_playwright() as pw:
    ctx, page, errors = session(pw, VIEWS["1382x804"], profile=ROOT / "chrome-profile-g")
    dialogs = []
    def on_dialog(d):
        dialogs.append({"type": d.type, "message": d.message[:120]}); res["nativeDialogs"] = dialogs
        d.dismiss()
    page.on("dialog", on_dialog)
    try:
        open_app(page)
        page.click("#fileMenuBtn"); page.wait_for_timeout(300)
        page.click("#exampleMenuBtn"); page.wait_for_timeout(300)
        page.click("#btnEx"); page.wait_for_timeout(4500)
        # ---- B6 comparison on main canvas: ocSelectionSummary with 0 and 1 selected (real click on card)
        res["oc_0sel"] = page.evaluate("""() => { const e=document.getElementById('ocSelectionSummary'); const cs=getComputedStyle(e); return {hidden:e.hidden, rendered:!e.hidden&&cs.display!=='none'&&e.getClientRects().length>0, count:e.dataset.count, text:e.innerText.slice(0,60)}; }""")
        page.locator('.ocard[data-kind="boundary"]').first.click(); page.wait_for_timeout(900)
        res["oc_1sel"] = page.evaluate("""() => { const e=document.getElementById('ocSelectionSummary'); const cs=getComputedStyle(e); return {hidden:e.hidden, rendered:!e.hidden&&cs.display!=='none'&&e.getClientRects().length>0, count:e.dataset.count, text:e.innerText.slice(0,60)}; }""")
        mark("oc_selection")
        # ---- open the full grid workspace by the real entry button
        page.click("#btnNewGridSystem"); page.wait_for_timeout(2500)
        res["grid_open"] = page.evaluate("() => ({open: !!document.querySelector('dialog.ig-workspace[open]'), title: document.getElementById('igTitle')?.textContent})")
        mark("grid_open")
        if res["grid_open"]["open"]:
            for name, (w, h) in VIEWS.items():
                page.set_viewport_size({"width": w, "height": h}); page.wait_for_timeout(1000)
                res.setdefault("ig_zoom", {})[name] = {s: rect(page, s) for s in [".ig-zoombar", "#igZoomOut", "#igZoom", "#igZoomIn", "#igFit", ".ig-hint", ".ig-canvas", ".ig-header"]}
                res["ig_zoom"][name]["zoomText"] = page.evaluate("() => document.getElementById('igZoom')?.textContent")
                page.screenshot(path=str(SHOTS / f"X6-grid-{name}.png"))
            page.set_viewport_size({"width": 1382, "height": 804}); page.wait_for_timeout(800)
            res["g4_workspace_source_text"] = term_report(text_of(page, "dialog.ig-workspace"))
            mark("grid_zoom_and_text")
            # create the source through the real form: name + preview + confirm
            page.fill("#igName", "G3 驗證網格"); page.wait_for_timeout(400)
            en = page.evaluate("() => { const b=document.getElementById('igSaveSource'); return {disabled:b.disabled, hidden:b.hidden, text:b.textContent}; }")
            res["igSaveSource_state"] = en
            if not en["disabled"]:
                page.click("#igSaveSource")
                try:
                    page.wait_for_selector("dialog.reference-impact[open] #impact-confirm", timeout=40000)
                    res["impact_dialog"] = True
                    res["impact_text"] = page.evaluate("() => document.querySelector('dialog.reference-impact[open]').innerText.slice(0,160)")
                    page.screenshot(path=str(SHOTS / "G-impact-dialog-1382.png"))
                    page.click("#impact-confirm")
                except Exception as ex:
                    res["impact_dialog"] = False; res["impact_wait_error"] = str(ex)[:160]
                try:
                    page.wait_for_function("() => { const b=document.getElementById('igClose'); return b && !b.disabled; }", timeout=40000)
                except Exception as ex:
                    res["close_wait_error"] = str(ex)[:160]
            mark("source_created_attempt")
            page.click("#igClose"); page.wait_for_timeout(1500)
            res["after_close"] = page.evaluate("() => ({dialogOpen: !!document.querySelector('dialog.ig-workspace[open]'), rows:[...document.querySelectorAll('#objectList .object-row')].map(r=>r.dataset.kind+':'+r.dataset.id)})")
            mark("closed")
            # ---- G3: select the grid-system card, measure inspector actions
            gs = page.locator('.ocard[data-kind="grid-system"]')
            if gs.count():
                gs.first.click(); page.wait_for_timeout(1200)
                for name, (w, h) in VIEWS.items():
                    page.set_viewport_size({"width": w, "height": h}); page.wait_for_timeout(900)
                    if w < 900 and not page.evaluate("() => !!document.querySelector('#gridInlineInspector')?.getClientRects().length"):
                        pass
                    r = {s: rect(page, s) for s in ["#gridInlineInspector", ".gi-header", ".gi-actions", "#gridObjectOpen", "#gridObjectNewBinding", "#gridObjectDelete"]}
                    r["deleteStyle"] = page.evaluate("""() => { const e=document.getElementById('gridObjectDelete'); if(!e) return null; const cs=getComputedStyle(e), p=getComputedStyle(e.parentElement); return {color:cs.color,bg:cs.backgroundColor,border:cs.borderColor,fs:cs.fontSize,fw:cs.fontWeight,parentGap:p.gap}; }""")
                    res.setdefault("gi", {})[name] = r
                    page.screenshot(path=str(SHOTS / f"G3-inspector-{name}.png"))
                page.set_viewport_size({"width": 1382, "height": 804}); page.wait_for_timeout(700)
                # hover state of delete (real pointer move)
                if page.locator("#gridObjectDelete").count():
                    page.hover("#gridObjectDelete"); page.wait_for_timeout(300)
                    res["gi_delete_hover"] = page.evaluate("() => { const cs=getComputedStyle(document.getElementById('gridObjectDelete')); return {color:cs.color,bg:cs.backgroundColor}; }")
                    page.mouse.move(5, 400)
                    res["gi_delete_keyboard"] = None
                res["g4_inspector_source_text"] = term_report(text_of(page, "#gridInlineInspector"))
                # does the delete button ask for confirmation? (do NOT click it)
                mark("inspector")
                # ---- binding mode through the inspector's own button
                if page.locator("#gridObjectNewBinding").count():
                    page.click("#gridObjectNewBinding"); page.wait_for_timeout(2500)
                    res["g4_workspace_binding_text"] = term_report(text_of(page, "dialog.ig-workspace"))
                    res["binding_controls"] = page.evaluate("""() => ({boundary: [...(document.getElementById('igBoundary')?.options||[])].map(o=>o.value+':'+o.textContent.trim().slice(0,20)), vertex: [...(document.getElementById('igVertex')?.options||[])].length, anchors: document.querySelectorAll('[data-ig-anchor]').length,
                       anchorKind: (()=>{const a=document.querySelector('[data-ig-anchor]'); return a?{tag:a.tagName,text:a.textContent.trim().slice(0,12),w:a.getBoundingClientRect().width,h:a.getBoundingClientRect().height}:null;})()})""")
                    page.screenshot(path=str(SHOTS / "G4-binding-workspace-1382.png"))
                    mark("binding_workspace_text")
                    page.click("#igClose"); page.wait_for_timeout(1200)
        # ---- G4 third place: face editor grid pane (information for a source-backed grid)
        page.locator('.ocard[data-kind="boundary"]').first.dblclick(); page.wait_for_timeout(2500)
        if page.evaluate("() => !document.getElementById('objectWorkspace').hidden"):
            page.click('[data-face-tool="grid"]'); page.wait_for_timeout(1200)
            res["g4_face_grid_pane_text"] = term_report(text_of(page, "#faceInspectorContent"))
            page.screenshot(path=str(SHOTS / "G4-face-grid-pane-1382.png"))
            mark("face_grid_pane")
        res["errors"] = errors[:10]
    except Exception as ex:
        res["exception"] = str(ex)[:400]
    finally:
        save("stage_g.json", res)
        ctx.close()
print("done", list(res.keys()), res.get("exception"))
