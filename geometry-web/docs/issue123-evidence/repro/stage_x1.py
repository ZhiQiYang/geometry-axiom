from common import *

SUM = """() => { const e=document.getElementById('feSelectionSummary'); if(!e) return null; const r=e.getBoundingClientRect(), cs=getComputedStyle(e);
  const vp=document.getElementById('faceEditorViewport').getBoundingClientRect();
  const rendered = !e.hidden && cs.display!=='none' && e.getClientRects().length>0;
  return {hidden:e.hidden, rendered, count:e.dataset.count, guidanceKey:e.dataset.guidanceKey, dynamic:e.dataset.guidanceDynamic, open:e.classList.contains('guidance-open'),
    x:+r.x.toFixed(0),y:+r.y.toFixed(0),w:+r.width.toFixed(0),h:+r.height.toFixed(0), coversPctOfViewport: rendered ? +((r.width*r.height)/(vp.width*vp.height)*100).toFixed(1) : 0,
    text:(e.querySelector('strong')?.textContent||'')+' | '+(e.querySelector('small')?.textContent||''), helpBtn: (()=>{const h=document.getElementById('feSelectionSummaryHelp'); return h?{hidden:h.hidden,text:h.textContent}:null;})()}; }"""

R = lambda page, sels: {s: rect(page, s) for s in sels}
res = {"main": {}, "face": {}, "v3": {}}
with sync_playwright() as pw:
    ctx, page, errors = session(pw, VIEWS["1382x804"])
    try:
        open_app(page)
        page.click("#fileMenuBtn"); page.wait_for_timeout(300)
        page.click("#exampleMenuBtn"); page.wait_for_timeout(300)
        page.click("#btnEx"); page.wait_for_timeout(5000)
        # ---- main canvas, 4 viewports
        for name, (w, h) in VIEWS.items():
            page.set_viewport_size({"width": w, "height": h}); page.wait_for_timeout(900)
            res["main"][name] = R(page, ["#zoomOutButton", "#zoomLevelButton", "#zoomInButton", "#btnZoom", "#homeButton", "#snapToggle", "#gridToggle", ".canvas-controls", ".minimap-shell", "#canvasViewport"])
            page.screenshot(path=str(SHOTS / f"X6-main-{name}.png"))
        page.set_viewport_size({"width": 1382, "height": 804}); page.wait_for_timeout(700)
        # ---- 3-view overlay
        page.click("#btnObj"); page.wait_for_timeout(2500)
        for name, (w, h) in VIEWS.items():
            page.set_viewport_size({"width": w, "height": h}); page.wait_for_timeout(900)
            res["v3"][name] = R(page, ["#v3ZoomBar", "#v3ZoomOut", "#v3ZoomLevel", "#v3ZoomIn", "#v3ZoomFit", ".canvas-controls", "#canvasViewport"])
            res["v3"][name]["mainControlsDisplay"] = page.evaluate("() => getComputedStyle(document.getElementById('zoomOutButton').closest('.canvas-controls')).display")
            page.screenshot(path=str(SHOTS / f"X6-v3-{name}.png"))
        page.set_viewport_size({"width": 1382, "height": 804}); page.wait_for_timeout(600)
        page.click("#btnCanvasView"); page.wait_for_timeout(1500)
        # ---- enter face workspace by real double click on the face card
        card = page.locator('.ocard[data-kind="boundary"]').first
        card.dblclick(); page.wait_for_timeout(2500)
        res["face"]["entered"] = page.evaluate("() => ({workspaceVisible: !document.getElementById('objectWorkspace').hidden, faceLayout: !document.getElementById('faceWorkspaceLayout').hidden, title: document.getElementById('workspaceTitle').textContent})")
        if res["face"]["entered"]["workspaceVisible"]:
            for name, (w, h) in VIEWS.items():
                page.set_viewport_size({"width": w, "height": h}); page.wait_for_timeout(1000)
                res["face"][name] = R(page, [".face-canvas-controls", "#feZoomOut", "#feZoomLevel", "#feZoomIn", "#feZoomFit", "#faceSnapToggle", "#faceGridToggle", "#faceGridSizeSelect", "#faceCoordinateReadout", "#faceEditorViewport", ".object-workspace-topbar"])
                res["face"][name]["summary"] = page.evaluate(SUM)
                page.screenshot(path=str(SHOTS / f"X6-B6-face-{name}-firstvisit.png"))
            page.set_viewport_size({"width": 1382, "height": 804}); page.wait_for_timeout(800)
            # B6 states: first visit (unseen lesson) already captured above at each viewport; now dismiss as a user would
            res["face"]["b6_first_visit_1382"] = page.evaluate(SUM)
            dismiss = page.locator('#feSelectionSummary [data-guidance-dismiss]')
            if dismiss.count() and dismiss.first.is_visible():
                dismiss.first.click(); page.wait_for_timeout(500)
            res["face"]["b6_after_dismiss_0sel"] = page.evaluate(SUM)
            page.screenshot(path=str(SHOTS / "B6-face-after-dismiss-1382.png"))
            # keyboard reachability for the face header and tools
            seq = []
            page.evaluate("document.getElementById('workspaceBackButton').focus()")
            for i in range(22):
                seq.append(page.evaluate("""() => { const e=document.activeElement, r=e.getBoundingClientRect(); const cs=getComputedStyle(e);
                  return {id:e.id,text:(e.textContent||e.title||'').trim().slice(0,10),tool:e.dataset?.faceTool||'',x:+r.x.toFixed(0),r:+r.right.toFixed(0),y:+r.y.toFixed(0),inView:r.right>0&&r.x<innerWidth&&r.bottom>0&&r.y<innerHeight,outline:cs.outlineStyle+' '+cs.outlineWidth}; }"""))
                page.keyboard.press("Tab")
            res["face"]["tab1382"] = seq
            # B6 with a real selection: place one timber via the UI (timber tool + length + click)
            tb = {}
            try:
                page.click('[data-face-tool="timber"]'); page.wait_for_timeout(700)
                tb["tbLenPresent"] = page.evaluate("() => !!document.getElementById('tbLen')")
                if tb["tbLenPresent"]:
                    page.fill("#tbLen", "1000"); page.wait_for_timeout(300)
                    vp = page.locator("#faceEditorViewport").bounding_box()
                    page.mouse.click(vp["x"] + vp["width"] * 0.5, vp["y"] + vp["height"] * 0.5); page.wait_for_timeout(1800)
                tb["after"] = page.evaluate("() => ({status: document.getElementById('status')?.textContent?.slice(0,90), timberRows: document.querySelectorAll('#faceLayerList [data-timber-id]').length, hint: document.getElementById('faceCanvasHint')?.textContent?.slice(0,80)})")
                page.click('[data-face-tool="select"]'); page.wait_for_timeout(500)
                rows = page.locator('#faceLayerList [data-timber-id]')
                tb["rowCount"] = rows.count()
                if tb["rowCount"]:
                    rows.first.click(); page.wait_for_timeout(800)
                    res["face"]["b6_1sel"] = page.evaluate(SUM)
                    page.screenshot(path=str(SHOTS / "B6-face-1sel-1382.png"))
            except Exception as ex:
                tb["error"] = str(ex)[:200]
            res["face"]["timberAttempt"] = tb
        res["errors"] = errors[:10]
    finally:
        save("stage_x1.json", res)
        ctx.close()
print("done", list(res.keys()), list(res["face"].keys()))
