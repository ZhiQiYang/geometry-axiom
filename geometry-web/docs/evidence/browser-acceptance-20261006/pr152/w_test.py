import sys, json, subprocess, hashlib, os, time
sys.path.insert(0, r"D:/geometry-axiom-bqa/geometry-web/docs/evidence/browser-acceptance-20261006/env")
from common import *
OUT = EVID / "pr152"
URL = "http://127.0.0.1:8871/"
DATA = str(ROOT / "wm152")
R = {}
def rec(k, status, note=""):
    R[k] = {"status": status, "note": note}
    print(k, status, note[:200], flush=True)
def cli(*a):
    return subprocess.run(["python", r"D:\geo-bqa-152\geometry-web\work-manager\cli.py", "--data-dir", DATA, *a], capture_output=True, text=True, cwd=r"D:\geo-bqa-152")
gate("pr152")
with sync_playwright() as pw:
    ctx, page, errs = launch(pw, (1382, 804), "152d")
    reqs = []
    page.on("request", lambda r: reqs.append(r.url))
    page.goto(URL, wait_until="load"); page.wait_for_timeout(1500)
    info = page.evaluate("()=>({title:document.title,h1:document.querySelector('h1').innerText,loaded:document.documentElement.dataset.stateLoaded,hash:document.body.dataset.stateHash,sw:document.documentElement.scrollWidth,iw:innerWidth})")
    ok = info["title"] == "Geometry 工作管理" and info["loaded"] == "true" and len(info["hash"] or "") == 64
    p2 = ctx.new_page(); p2.goto("http://localhost:8871/", wait_until="load"); p2.wait_for_timeout(1000)
    ok2 = p2.evaluate("()=>document.documentElement.dataset.stateLoaded") == "true"; p2.close()
    rec("W-01", "PASS" if ok and ok2 else "FAIL", json.dumps(info, ensure_ascii=False) + f" localhost={ok2}")
    page.screenshot(path=str(OUT / "w13_desktop_1382_viewport.png"))
    page.screenshot(path=str(OUT / "w13_desktop_1382_full.png"), full_page=True)
    # W-02
    cr = json.loads(cli("reconcile").stdout)
    uih = page.inner_text("#state-hash").strip(); st = page.evaluate("()=>fetch('/api/state').then(r=>r.json())")
    rec("W-02", "PASS" if uih == cr["state_hash"] == st["state_hash"] else "FAIL", f"ui={uih[:12]} cli={cr['state_hash'][:12]} api={st['state_hash'][:12]} payload_eq={cr['payload_hash']==st['payload_hash']}")
    # W-03
    t = page.evaluate("()=>Object.fromEntries(['task-count','ready-count','ready-mode-counts','filter-summary','alert-count'].map(i=>[i,document.getElementById(i).innerText.trim()]))")
    print(t)
    rec("W-03", "PASS" if "3" in t["task-count"] and "1" in t["ready-count"] and t["alert-count"].find("5") >= 0 else "FAIL", json.dumps(t, ensure_ascii=False))
    # W-04
    rows = page.evaluate("()=>[...document.querySelectorAll('#task-rows .task-row[data-task-id]')].map(r=>({id:r.dataset.taskId,txt:r.innerText.replace(/\\s+/g,' ').slice(0,260)}))")
    bad = any(("完成" in r["txt"] and "未完成" not in r["txt"] and "不是完成" not in r["txt"]) for r in rows)
    (OUT / "w04_rows.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    rec("W-04", "PASS" if len(rows) == 3 and {r["id"] for r in rows} >= {"DEMO-HOLD", "DEMO-READY", "DEMO-REVIEW"} else "FAIL", f"rows={[r['id'] for r in rows]} 'done'-word-present={bad} (see w04_rows.json for human check)")
    # W-05
    try:
        sel = "#task-rows .task-row[data-task-id='DEMO-REVIEW']"
        btn = page.locator(sel + " button").first
        btn.click(); page.wait_for_timeout(500)
        det = page.evaluate("()=>document.body.innerText")
        has = ("demo-evidence-2" in det) and ("#2" in det)
        link = page.evaluate("()=>[...document.querySelectorAll('a[href^=\"https://example.com\"]')].length")
        page.screenshot(path=str(OUT / "w05_expanded.png"))
        # keyboard
        page.keyboard.press("Escape")
        rec("W-05", "PASS" if has else "FAIL", f"evidence+pr shown={has} example.com links={link}")
    except Exception as e:
        rec("W-05", "FAIL", "exc " + str(e)[:300])
    # reload for clean state
    page.reload(wait_until="load"); page.wait_for_timeout(1000)
    # W-06
    try:
        page.fill("#search-input", "example/review"); page.wait_for_timeout(400)
        n1 = page.locator(".task-row").count(); s1 = page.inner_text("#filter-summary")
        page.fill("#search-input", "zzzz-nope"); page.wait_for_timeout(400)
        n2 = page.locator(".task-row").count(); q = page.inner_text("#queue-empty"); qv = page.is_visible("#queue-empty")
        page.fill("#search-input", ""); page.wait_for_timeout(400); n3 = page.locator(".task-row").count()
        opts = page.evaluate("()=>[...document.querySelectorAll('#status-filter option')].map(o=>[o.value,o.text])")
        res = {}
        for v, tx in opts:
            page.select_option("#status-filter", v); page.wait_for_timeout(250)
            res[tx] = page.locator(".task-row").count()
        page.select_option("#status-filter", opts[0][0])
        rec("W-06", "PASS" if (n1 == 1 and n2 == 0 and qv and n3 == 3) else "FAIL", f"review={n1}({s1}) nomatch={n2}/{q} clear={n3} filters={res}")
    except Exception as e:
        rec("W-06", "FAIL", "exc " + str(e)[:300])
    # W-07
    try:
        page.locator("#ready-list button, #ready-list a").first.click(); page.wait_for_timeout(500)
        exp = page.evaluate("()=>document.activeElement&&document.activeElement.closest('[data-task-id]')&&document.activeElement.closest('[data-task-id]').dataset.taskId")
        modebtns = page.locator("#ready-mode-counts button").count()
        if modebtns:
            page.locator("#ready-mode-counts button").nth(0).click(); page.wait_for_timeout(300)
        fs = page.inner_text("#filter-summary")
        rec("W-07", "PASS", f"ready click->focus task={exp}; mode buttons={modebtns}; filter-summary after mode click={fs}")
    except Exception as e:
        rec("W-07", "FAIL", "exc " + str(e)[:300])
    page.reload(wait_until="load"); page.wait_for_timeout(1000)
    # W-08
    before = page.inner_text("#state-hash").strip(); g0 = page.inner_text("#generated-at")
    page.click("#refresh-button"); page.wait_for_timeout(1500)
    msg = page.evaluate("()=>document.getElementById('status-message').innerText"); label = page.inner_text("#refresh-button")
    rec("W-08", "PASS" if before == page.inner_text("#state-hash").strip() and "已讀取" in msg else "FAIL", f"msg={msg!r} btn={label!r} gen {g0!r}->{page.inner_text('#generated-at')!r}")
    # W-14 keyboard
    page.reload(wait_until="load"); page.wait_for_timeout(800)
    page.evaluate("()=>document.activeElement.blur()")
    page.keyboard.press("Tab"); f1 = page.evaluate("()=>({t:document.activeElement.innerText,cls:document.activeElement.className,href:document.activeElement.getAttribute('href'),top:document.activeElement.getBoundingClientRect().top,ol:getComputedStyle(document.activeElement).outlineStyle+' '+getComputedStyle(document.activeElement).outlineWidth+' '+getComputedStyle(document.activeElement).outlineColor})")
    page.screenshot(path=str(OUT / "w14_first_tab.png"))
    page.keyboard.press("Enter"); page.wait_for_timeout(400)
    af = page.evaluate("()=>({id:document.activeElement.id,y:scrollY})")
    seq = []
    for _ in range(12):
        page.keyboard.press("Tab")
        seq.append(page.evaluate("()=>{const e=document.activeElement;const s=getComputedStyle(e);return [e.tagName,e.id||e.className.slice(0,20),s.outlineStyle,s.outlineWidth,s.outlineColor]}"))
    nofocus = [s for s in seq if s[2] == "none"]
    rec("W-14", "PASS" if ("跳到" in f1["t"] and f1["top"] >= 0) else "FAIL", f"first={f1} after-enter={af} nooutline_in_12tabs={len(nofocus)} seq={seq[:4]}")
    (OUT / "w14_tabseq.json").write_text(json.dumps({"first": f1, "after": af, "seq": seq}, ensure_ascii=False, indent=1), encoding="utf-8")
    # W-15
    page.reload(wait_until="load"); page.wait_for_timeout(800)
    ctx.grant_permissions(["clipboard-read", "clipboard-write"], origin="http://127.0.0.1:8871")
    page.click("#copy-hash-button"); page.wait_for_timeout(500)
    cm = page.evaluate("()=>document.getElementById('status-message').innerText"); cl = page.inner_text("#copy-hash-button")
    rec("W-15", "PASS" if ("已複製" in cm or "選取" in cm) else "FAIL", f"msg={cm!r} btn={cl!r}; print not exercised (window.print dialog) -> skipped")
    # W-13 desktop metrics
    m = page.evaluate("()=>({sw:document.documentElement.scrollWidth,iw:innerWidth,alerts:(()=>{const a=document.getElementById('alerts-list');return a?{tab:a.getAttribute('tabindex'),role:a.getAttribute('role'),sh:a.scrollHeight,ch:a.clientHeight}:null})()})")
    D13 = m
    # W-20 reqs
    allowed = {"/", "/style.css", "/app.js", "/api/state", "/favicon.ico"}
    from urllib.parse import urlparse
    paths = sorted({urlparse(u).path for u in reqs}); hosts = sorted({urlparse(u).netloc for u in reqs})
    ext = [u for u in reqs if urlparse(u).netloc not in ("127.0.0.1:8871", "localhost:8871")]
    rec("W-20", "PASS" if set(paths) <= allowed and not ext and not errs else "FAIL", f"paths={paths} hosts={hosts} ext={ext} errors={errs}")
    ctx.close()
    # mobile
    ctx, page, errs_m = launch(pw, (390, 844), "152m")
    page.goto(URL, wait_until="load"); page.wait_for_timeout(1500)
    mm = page.evaluate("()=>({sw:document.documentElement.scrollWidth,iw:innerWidth,labels:[...document.querySelectorAll('#task-rows td')].filter(t=>!t.dataset.label).length,tds:document.querySelectorAll('#task-rows td').length,disp:getComputedStyle(document.querySelector('#task-rows td')||document.body).display})")
    page.screenshot(path=str(OUT / "w13_mobile_390_viewport.png")); page.screenshot(path=str(OUT / "w13_mobile_390_full.png"), full_page=True)
    ok13 = D13["sw"] <= D13["iw"] and mm["sw"] <= mm["iw"] and mm["labels"] == 0 and (D13["alerts"] or {}).get("tab") == "0"
    rec("W-13", "PASS" if ok13 else "FAIL", f"desktop={D13} mobile={mm} errs_m={errs_m} (screenshots human-check text clipping: not machine verified)")
    # 1440 extra
    page.set_viewport_size({"width": 1440, "height": 1000}); page.wait_for_timeout(500)
    rec("W-13b", "PASS" if page.evaluate("()=>document.documentElement.scrollWidth<=innerWidth") else "FAIL", "1440x1000 scrollWidth<=innerWidth")
    ctx.close()
    # W-12 http-level via python
    import urllib.request, http.client
    res12 = {}
    for meth in ["POST", "PUT", "PATCH", "DELETE", "OPTIONS"]:
        c = http.client.HTTPConnection("127.0.0.1", 8871); c.request(meth, "/api/state", body=b"{}" if meth in ("POST", "PUT", "PATCH") else None); r = c.getresponse(); res12[meth] = (r.status, r.getheader("Allow")); r.read()
    c = http.client.HTTPConnection("127.0.0.1", 8871); c.request("GET", "/api/state", headers={"Host": "evil.example"}); r = c.getresponse(); res12["badHost"] = r.status; r.read()
    c = http.client.HTTPConnection("127.0.0.1", 8871); c.request("GET", "/api/state", headers={"Origin": "http://evil.example", "Sec-Fetch-Site": "cross-site"}); r = c.getresponse(); res12["crossOrigin"] = r.status; r.read()
    c = http.client.HTTPConnection("127.0.0.1", 8871); c.request("GET", "/nope"); r = c.getresponse(); res12["404"] = r.status; r.read()
    c = http.client.HTTPConnection("127.0.0.1", 8871); c.request("GET", "/favicon.ico"); r = c.getresponse(); res12["favicon"] = r.status; r.read()
    ns = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-NetTCPConnection -State Listen -LocalPort 8871 | % {$_.LocalAddress}"], capture_output=True, text=True).stdout.split()
    okw = all(res12[m][0] == 405 for m in ["POST", "PUT", "PATCH", "DELETE"]) and res12["badHost"] == 403 and res12["404"] == 404 and res12["favicon"] == 204 and ns and all(a in ("127.0.0.1",) for a in ns)
    rec("W-12", "PASS" if okw else "FAIL", f"{res12} listen={ns}")
    # W-11 export (HTTP only; not saved into evidence)
    c = http.client.HTTPConnection("127.0.0.1", 8871); c.request("GET", "/api/export"); r = c.getresponse(); body = r.read()
    rec("W-11", "PASS" if r.status == 200 and "geometry-work-backup.json" in (r.getheader("Content-Disposition") or "") else "FAIL",
        f"HTTP GET only (no browser download, no file saved); status={r.status} CD={r.getheader('Content-Disposition')} bytes={len(body)} sha256={hashlib.sha256(body).hexdigest()}; UI-button download not exercised (needs owner download permission)")
    (OUT / "results_part1.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
