import sys,json
sys.path.insert(0,r"D:/geometry-axiom-bqa/geometry-web/docs/evidence/browser-acceptance-20261006/env")
from common import *
(ROOT).mkdir(exist_ok=True)
res={"resource":gate("p1")}
channel=sys.argv[1] if len(sys.argv)>1 else None
out={}
with sync_playwright() as pw:
    try:
        ctx,page,errs=launch(pw,(1382,804),"p1"+(channel or "chromium"),channel)
        out["browser_version"]=ctx.browser.version if ctx.browser else "persistent"
        page.goto("http://127.0.0.1:8870/",wait_until="domcontentloaded",timeout=90000)
        page.wait_for_timeout(4000)
        out["title"]=page.title()
        out["dom"]=page.evaluate("()=>({app:!!document.getElementById('app'),inert:document.getElementById('app')&&document.getElementById('app').inert,fileMenu:!!document.getElementById('fileMenuBtn'),apiRequest:typeof apiRequest,scrollW:document.documentElement.scrollWidth,innerW:innerWidth})")
        out["runtime_in_page"]=page.evaluate("()=>fetch('/runtime').then(r=>r.json())")
        out["errors"]=errs
        page.screenshot(path=str(EVID/"env"/f"p1_home_{channel or 'chromium'}.png"))
        ctx.close(); out["ok"]=True
    except Exception as e:
        out["ok"]=False; out["error"]=str(e)[:1500]
print(json.dumps({**res,**out},ensure_ascii=False,indent=1))
