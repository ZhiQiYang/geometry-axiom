from common import *
INFO = """() => { const e=document.activeElement; if(!e) return null; const r=e.getBoundingClientRect(), cs=getComputedStyle(e);
 let fv=null; try{fv=e.matches(':focus-visible')}catch(x){fv='err'}
 return {id:e.id,tag:e.tagName.toLowerCase(),cls:String(e.className).slice(0,40),tool:e.dataset?e.dataset.faceTool||'':'',text:(e.textContent||e.title||'').trim().slice(0,14),
  inDialog:!!e.closest('dialog.sm-workspace'), inFaceTools:!!e.closest('#faceWorkspaceTools'), focusVisible:fv,
  outline:cs.outlineWidth+' '+cs.outlineStyle+' '+cs.outlineColor, outlineOffset:cs.outlineOffset, boxShadow:cs.boxShadow.slice(0,80),
  x:+r.x.toFixed(0),y:+r.y.toFixed(0),w:+r.width.toFixed(0),h:+r.height.toFixed(0)}; }"""
res = {"sha": "d6b4b450d741fcbbfd75c51631915d3082926990", "viewport": "1382x804"}
mem_gate("t1")
with sync_playwright() as pw:
    ctx, page, errors = session(pw, VIEWS["1382x804"], "t1")
    try:
        open_app(page)
        # ---- 3D 建模
        page.click("#fileMenuBtn"); page.wait_for_timeout(300)
        page.click("#btnModelLibraryMenu"); page.wait_for_timeout(1500)
        if page.evaluate("() => { const e=document.getElementById('smLibraryPanel'); return !!e && !e.hidden; }"):
            page.click("#smBackToBuild"); page.wait_for_timeout(800)
        page.evaluate("() => { if(document.activeElement && document.activeElement!==document.body) document.activeElement.blur(); }")
        res["sm_before_tab_active"] = page.evaluate("() => document.activeElement.tagName")
        seq = []
        for i in range(6):
            page.keyboard.press("Tab"); page.wait_for_timeout(120)
            seq.append(page.evaluate(INFO))
        res["sm_tab_seq"] = seq
        page.screenshot(path=str(SHOTS / "t1-sm-first-tab.png"), clip={"x": 0, "y": 0, "width": 1382, "height": 300})
        page.keyboard.press("Escape"); page.wait_for_timeout(500)
        if page.evaluate("() => !!document.querySelector('dialog.sm-workspace[open]')"):
            page.click("#smClose"); page.wait_for_timeout(500)
        # ---- 面內
        load_example(page)
        res["face_entered"] = enter_face(page)
        d = page.locator('#feSelectionSummary [data-guidance-dismiss]')
        if d.count() and d.first.is_visible(): d.first.click(); page.wait_for_timeout(400)
        page.evaluate("() => { if(document.activeElement && document.activeElement!==document.body) document.activeElement.blur(); }")
        res["face_before_tab_active"] = page.evaluate("() => document.activeElement.tagName")
        seq = []
        for i in range(30):
            page.keyboard.press("Tab"); page.wait_for_timeout(100)
            seq.append(page.evaluate(INFO))
        res["face_tab_seq"] = seq
        res["face_toolbar_stops"] = [s for s in seq if s and s["inFaceTools"]]
        res["errors"] = errors[:10]
    except Exception as ex:
        res["exception"] = str(ex)[:400]
    finally:
        save("t1_focus.json", res); ctx.close()
print(json.dumps({k: res[k] for k in res if k not in ("sm_tab_seq","face_tab_seq","face_toolbar_stops")}, ensure_ascii=False))
print("SM first:", res.get("sm_tab_seq", [None])[0])
print("FACE first:", res.get("face_tab_seq", [None])[0])
for s in res.get("face_toolbar_stops", []): print("TB", s["id"], s["tool"], s["focusVisible"], s["outline"])
