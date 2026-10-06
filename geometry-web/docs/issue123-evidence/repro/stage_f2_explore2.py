from common import *

res = {}
with sync_playwright() as pw:
    ctx, page, errors = session(pw, VIEWS["1382x804"])
    try:
        open_app(page)
        # --- F1 hit-testing in 3D welcome state (real layout, no clicks)
        page.click("#fileMenuBtn"); page.wait_for_timeout(300)
        page.click("#btnModelLibraryMenu"); page.wait_for_timeout(1500)
        if page.evaluate("() => { const e=document.getElementById('smLibraryPanel'); return !!e && !e.hidden; }"):
            page.click("#smBackToBuild"); page.wait_for_timeout(800)
        res["f1_hit"] = page.evaluate("""() => {
          const R = e => { const r=e.getBoundingClientRect(); return {x:r.x,y:r.y,r:r.right,b:r.bottom,w:r.width,h:r.height}; };
          const t = document.getElementById('smWelcomeTry'); const rt = R(t);
          const segs = [...document.querySelectorAll('.sm-view-segment button')].map(b => ({text:b.textContent.trim(), r:R(b)}));
          const inter = (a,b)=>Math.max(0,Math.min(a.r,b.r)-Math.max(a.x,b.x))*Math.max(0,Math.min(a.b,b.b)-Math.max(a.y,b.y));
          const overlaps = segs.map(s=>({text:s.text, overlapPx2:+inter(rt,s.r).toFixed(0)})).filter(o=>o.overlapPx2>0);
          const pt = (x,y)=>{ const e=document.elementFromPoint(x,y); return e ? (e.id||e.className||e.tagName).toString().slice(0,40) : null; };
          const cx = (rt.x+rt.r)/2;
          const probes = [0.25,0.5,0.75,0.95].map(f=>({atFractionOfButtonHeight:f, y:+(rt.y+rt.h*f).toFixed(1), topmost:pt(cx, rt.y+rt.h*f)}));
          return {tryRect:rt, segmentRects:segs.map(s=>({t:s.text,x:+s.r.x.toFixed(0),r:+s.r.r.toFixed(0),y:+s.r.y.toFixed(0),b:+s.r.b.toFixed(0)})), overlaps, probes};
        }""")
        page.keyboard.press("Escape"); page.wait_for_timeout(500)
        if page.evaluate("() => !!document.querySelector('dialog.sm-workspace[open]')"):
            page.click("#smClose"); page.wait_for_timeout(500)
        # --- scene exploration: default example via File > examples
        page.click("#fileMenuBtn"); page.wait_for_timeout(300)
        page.click("#exampleMenuBtn"); page.wait_for_timeout(300)
        page.click("#btnEx"); page.wait_for_timeout(5000)
        res["afterExample"] = page.evaluate("""() => ({
          dialogs: [...document.querySelectorAll('dialog[open]')].map(d=>d.className||d.id),
          status: document.getElementById('status')?.textContent?.slice(0,80),
          rows: [...document.querySelectorAll('#objectList .object-row')].map(r=>({kind:r.dataset.kind,id:r.dataset.id,text:r.textContent.trim().replace(/\\s+/g,' ').slice(0,36)})) })""")
        page.screenshot(path=str(SHOTS / "explore-example-1382.png"))
        res["errors"] = errors[:10]
    finally:
        save("stage_f2_explore2.json", res)
        ctx.close()
print(json.dumps(res, ensure_ascii=False)[:3800])
