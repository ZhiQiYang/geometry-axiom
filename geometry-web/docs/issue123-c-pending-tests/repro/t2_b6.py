from common import *
M = """() => {
 const R = e => { if(!e) return null; const r=e.getBoundingClientRect(); return {x:+r.x.toFixed(1),y:+r.y.toFixed(1),r:+r.right.toFixed(1),b:+r.bottom.toFixed(1),w:+r.width.toFixed(1),h:+r.height.toFixed(1)}; };
 const card=document.getElementById('feSelectionSummary'), vp=document.getElementById('faceEditorViewport');
 const cs=getComputedStyle(card);
 const rendered=!card.hidden&&cs.display!=='none'&&card.getClientRects().length>0;
 const dims=[...document.querySelectorAll('#faceEditorSvg .fe-edge-dim')].map(e=>({t:e.textContent,...R(e)})).filter(d=>d.w>0);
 dims.sort((a,b)=>a.y-b.y);
 const vr=vp.getBoundingClientRect(), bb=fe.fittedBounds||fe.lastFitBounds||(window.loopsBBox&&oc.focus?loopsBBox(oc.bmap[oc.focus.id]):[0,0,0,0]), ringTop=vr.top+fe.panY+bb[1]*fe.zoom, ringBottom=vr.top+fe.panY+bb[3]*fe.zoom;
 const loops=[...document.querySelectorAll('#faceEditorSvg path, #faceEditorSvg polygon')].map(e=>({c:String(e.getAttribute('class')),...R(e)})).filter(d=>d.w>20).sort((a,b)=>a.y-b.y).slice(0,3);
 const c=R(card), top=dims[0];
 const ia=d=>Math.max(0,Math.min(c.r,d.r)-Math.max(c.x,d.x))*Math.max(0,Math.min(c.b,d.b)-Math.max(c.y,d.y));
 const allInter=rendered?dims.map(d=>({t:d.t,area:+ia(d).toFixed(1),y:d.y,x:d.x})).filter(d=>d.area>0):[];
 const inter = (c&&top&&rendered) ? Math.max(0,Math.min(c.r,top.r)-Math.max(c.x,top.x))*Math.max(0,Math.min(c.b,top.b)-Math.max(c.y,top.y)) : null;
 return {rendered, hidden:card.hidden, count:card.dataset.count, open:card.classList.contains('guidance-open'), dynamic:card.dataset.guidanceDynamic,
  card:c, viewport:R(vp), topDim:top, topDims3:dims.slice(0,3), ringTopComputed:+ringTop.toFixed(1), ringBottomComputed:+ringBottom.toFixed(1), loopsTop:loops,
  zoom:fe.zoom, panY:fe.panY, viewportSize:fe.viewportSize, intersectionArea:inter, allDimIntersections:allInter, fittedBoundsNull:fe.fittedBounds==null,
  cardBottomMinusRingTop: c? +(c.b-ringTop).toFixed(1):null}; }"""
res = {"sha": "d6b4b450d741fcbbfd75c51631915d3082926990", "viewport": "1382x804"}
mem_gate("t2")
with sync_playwright() as pw:
    ctx, page, errors = session(pw, VIEWS["1382x804"], "t2")
    try:
        open_app(page); load_example(page)
        res["entered_1"] = enter_face(page)
        res["first_visit"] = page.evaluate(M)
        d = page.locator('#feSelectionSummary [data-guidance-dismiss]')
        res["dismiss_visible"] = bool(d.count() and d.first.is_visible())
        if res["dismiss_visible"]: d.first.click(); page.wait_for_timeout(500)
        res["after_dismiss_0sel"] = page.evaluate(M)
        page.click("#workspaceBackButton"); page.wait_for_timeout(1500)
        res["left"] = page.evaluate("() => document.getElementById('objectWorkspace').hidden")
        res["lesson_read_flag"] = page.evaluate("() => { try { return Object.keys(localStorage).filter(k=>/guid/i.test(k)).map(k=>k+'='+localStorage.getItem(k).slice(0,80)); } catch(e){return String(e);} }")
        res["entered_2"] = enter_face(page)
        res["reenter_0sel"] = page.evaluate(M)   # 卡片在初次 fit 時的狀態:此刻 0 選為 hidden → viewportSize.top 即 fit 時 inset
        rows = page.locator('#faceLayerList [data-timber-id]'); res["timberRows"] = rows.count()
        rows.first.click(); page.wait_for_timeout(900)
        res["reenter_1sel"] = page.evaluate(M)
        page.screenshot(path=str(SHOTS / "t2-b6-reenter-1sel-1382.png"), clip={"x": 240, "y": 100, "width": 520, "height": 260})

        # ---- 變體 B:離開再進,以畫布上真實點擊選 1 支角材(列表點擊會平移鏡頭,見 reenter_1sel 的 panY 變化)
        page.keyboard.press("Escape"); page.click("#workspaceBackButton"); page.wait_for_timeout(1500)
        res["entered_3"] = enter_face(page)
        res["reenter3_0sel"] = page.evaluate(M)
        res["svg_timber_candidates"] = page.evaluate("() => [...document.querySelectorAll('#faceEditorSvg [class*=timber]')].slice(0,12).map(e=>{const r=e.getBoundingClientRect();return {tag:e.tagName,cls:String(e.getAttribute('class')),id:e.dataset.timberId,x:r.x,y:r.y,w:r.width,h:r.height};})")
        cand = [c for c in res["svg_timber_candidates"] if c["w"] > 3 and c["h"] > 3]
        if cand:
            c0 = cand[0]; page.mouse.click(c0["x"] + c0["w"]/2, c0["y"] + c0["h"]/2); page.wait_for_timeout(900)
            res["reenter3_1sel_canvas"] = page.evaluate(M)
            page.screenshot(path=str(SHOTS / "t2-b6-reenter-1sel-canvasclick.png"), clip={"x": 240, "y": 100, "width": 700, "height": 300})
        c = res["reenter_1sel"]
        res["verdict"] = {"intersectionArea": c["intersectionArea"], "cardBottom": c["card"] and c["card"]["b"], "topDimTop": c["topDim"] and c["topDim"]["y"],
                          "ringTop": c["ringTopComputed"], "allDimIntersections": c["allDimIntersections"], "fittedBoundsNull": c["fittedBoundsNull"], "fitInsetTop": c["viewportSize"] and c["viewportSize"].get("top")}
        res["errors"] = errors[:10]
    except Exception as ex:
        res["exception"] = str(ex)[:400]
    finally:
        save(os.environ.get("T2_OUT","t2_b6.json"), res); ctx.close()
print(json.dumps(res.get("verdict"), ensure_ascii=False), res.get("exception"), res.get("timberRows"), res.get("left"), res.get("lesson_read_flag"))
for k in ("first_visit","after_dismiss_0sel","reenter_0sel","reenter_1sel"):
    v = res.get(k); 
    if v: print(k, v["rendered"], v["count"], v["card"], v["topDim"], v["ringTopComputed"], (v["viewportSize"] or {}).get("top"))
