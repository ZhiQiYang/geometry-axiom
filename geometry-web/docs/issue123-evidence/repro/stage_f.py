from common import *

MEASURE = """() => {
  const q = s => document.querySelector(s);
  const R = e => { if(!e) return null; const r=e.getBoundingClientRect(); return {x:+r.x.toFixed(1),y:+r.y.toFixed(1),w:+r.width.toFixed(1),h:+r.height.toFixed(1),b:+r.bottom.toFixed(1),r:+r.right.toFixed(1)}; };
  const vis = e => { if(!e) return false; const cs=getComputedStyle(e); return !e.hidden && cs.display!=='none' && cs.visibility!=='hidden' && e.getClientRects().length>0; };
  const dlg = q('dialog.sm-workspace');
  const names = ['.sm-header','.sm-source-actions','.sm-steps','.sm-stage','.sm-stage-head','.sm-view-tools','.sm-view-direction','.sm-display-options','.sm-canvas-wrap','#smWelcome','#smWelcome h2','#smWelcome p','#smWelcomeTry','#smWelcome small','.sm-metrics','.sm-setup','.sm-setup-footer','.workspace-project-header','#smClose'];
  const out = {dialog: R(dlg), vh: innerHeight, vw: innerWidth, els:{}};
  for (const n of names) { const e=q(n); out.els[n] = e ? Object.assign({vis:vis(e)}, R(e)) : null; }
  // overlaps: welcome children vs sibling bands
  const bands = ['.sm-stage-head','.sm-view-tools','.sm-view-direction','.sm-display-options','.sm-metrics'];
  const kids = ['#smWelcome h2','#smWelcome p','#smWelcomeTry','#smWelcome small','#smWelcome .sm-wire-cube'];
  const ov = [];
  const inter = (a,b) => a && b && !(a.r<=b.x || b.r<=a.x || a.b<=b.y || b.b<=a.y);
  for (const k of kids) { const ek=q(k); if(!vis(ek)) continue; const rk=R(ek);
    for (const b of bands) { const eb=q(b); if(!vis(eb)) continue; const rb=R(eb); if(inter(rk,rb)) ov.push(k+' x '+b); } }
  out.overlaps = ov;
  // welcome clipping inside canvas-wrap
  const w=R(q('#smWelcome')), c=R(q('.sm-canvas-wrap'));
  out.welcomeVsCanvas = w && c ? {welcomeH:w.h, canvasH:c.h, overflowTop:+(c.y-w.y).toFixed(1), overflowBottom:+(w.b-c.b).toFixed(1)} : null;
  const wel = q('#smWelcome'); out.welcomeScroll = wel ? {scrollH:wel.scrollHeight, clientH:wel.clientHeight} : null;
  out.dialogScroll = dlg ? {scrollH:dlg.scrollHeight, clientH:dlg.clientHeight} : null;
  out.mediaCompact = matchMedia('(min-width:721px) and (max-height:800px)').matches;
  return out;
}"""

BUTTONS = """() => [...document.querySelectorAll('dialog.sm-workspace button, dialog.sm-workspace select, dialog.sm-workspace input')].filter(e=>{const cs=getComputedStyle(e);return !e.hidden&&cs.display!=='none'&&cs.visibility!=='hidden'&&e.getClientRects().length}).map(e=>{const r=e.getBoundingClientRect(),cs=getComputedStyle(e);return {tag:e.tagName.toLowerCase(),id:e.id,cls:(e.className||'').toString().slice(0,40),text:(e.textContent||e.value||'').trim().replace(/\\s+/g,' ').slice(0,18),h:+r.height.toFixed(1),w:+r.width.toFixed(1),y:+r.y.toFixed(0),bg:cs.backgroundColor,color:cs.color,br:cs.borderRadius,accent:cs.accentColor,fs:cs.fontSize}})"""

HELP = """() => { const sels=['.sm-help','.sm-guide','.sm-guide p','.sm-guide li','.sm-view-direction','.sm-source-summary','.sm-welcome small','.sm-steps small','.sm-display-options small','.sm-gesture','.sm-metrics small','.sm-section p'];
  const out=[]; for (const s of sels) for (const e of document.querySelectorAll(s)) { const cs=getComputedStyle(e); if(!e.getClientRects().length||e.hidden) continue;
    const lh=parseFloat(cs.lineHeight)||parseFloat(cs.fontSize)*1.2, r=e.getBoundingClientRect(); const txt=(e.textContent||'').trim().replace(/\\s+/g,' ');
    out.push({sel:s,fs:cs.fontSize,lh:cs.lineHeight,color:cs.color,chars:txt.length,lines:Math.round(r.height/lh),w:+r.width.toFixed(0),text:txt.slice(0,34)}); }
  return out; }"""

res = {}
with sync_playwright() as pw:
    ctx, page, errors = session(pw, VIEWS["1382x804"])
    try:
        open_app(page)
        page.click("#fileMenuBtn"); page.wait_for_timeout(300)
        page.click("#btnModelLibraryMenu"); page.wait_for_timeout(1500)
        res["opened"] = page.evaluate("() => ({dialogOpen: !!document.querySelector('dialog.sm-workspace[open]'), libraryVisible: (()=>{const e=document.getElementById('smLibraryPanel');return !!e&&!e.hidden})(), mainHidden: document.getElementById('smMain')?.hidden})")
        if res["opened"]["libraryVisible"]:
            page.click("#smBackToBuild"); page.wait_for_timeout(800)
        res["afterBuild"] = page.evaluate("() => ({welcomeVisible: (()=>{const e=document.getElementById('smWelcome');return !!e&&!e.hidden&&e.getClientRects().length>0})()})")
        for name, (w, h) in VIEWS.items():
            page.set_viewport_size({"width": w, "height": h}); page.wait_for_timeout(900)
            r = {"measure": page.evaluate(MEASURE)}
            if name == "1382x804":
                r["controls"] = page.evaluate(BUTTONS); r["help"] = page.evaluate(HELP)
            page.screenshot(path=str(SHOTS / f"F-3d-welcome-{name}.png"))
            res[name] = r
        # keyboard reachability at 1382x804: Tab through the dialog, record focus targets and whether they are within the viewport
        page.set_viewport_size({"width": 1382, "height": 804}); page.wait_for_timeout(600)
        seq = []
        page.evaluate("document.querySelector('#smClose')?.focus()")
        for i in range(40):
            info = page.evaluate("""() => { const e=document.activeElement; if(!e) return null; const r=e.getBoundingClientRect(); const cs=getComputedStyle(e);
              return {id:e.id,tag:e.tagName.toLowerCase(),text:(e.textContent||'').trim().slice(0,14),y:+r.y.toFixed(0),b:+r.bottom.toFixed(0),h:+r.height.toFixed(0),inView:r.bottom>0&&r.y<innerHeight&&r.right>0&&r.x<innerWidth,
              outline:cs.outlineWidth+' '+cs.outlineStyle+' '+cs.outlineColor, inDialog: !!e.closest('dialog.sm-workspace')}; }""")
            seq.append(info)
            page.keyboard.press("Tab")
        res["tabOrder1382"] = seq
        page.focus("#smWelcomeTry") if page.query_selector("#smWelcomeTry") else None
        res["focusOutlineWelcomeTry"] = page.evaluate("() => { const e=document.activeElement; const cs=getComputedStyle(e); return {id:e.id,outlineWidth:cs.outlineWidth,outlineStyle:cs.outlineStyle,outlineColor:cs.outlineColor,outlineOffset:cs.outlineOffset}; }")
        res["errors"] = errors[:10]
    finally:
        save("stage_f.json", res)
        ctx.close()
print("done; keys:", list(res.keys()))
