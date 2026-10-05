import re
from common import *
exec(open(ROOT / "stage_g.py", encoding="utf-8").read().split("with sync_playwright()")[0].split("STEP = {}")[0].replace("from common import *", ""))

SUM = open(ROOT / "stage_x1.py", encoding="utf-8").read().split('SUM = """')[1].split('"""')[0]
res = {}
with sync_playwright() as pw:
    ctx, page, errors = session(pw, VIEWS["1382x804"], profile=ROOT / "chrome-profile-h")
    try:
        open_app(page)
        page.click("#fileMenuBtn"); page.wait_for_timeout(300)
        page.click("#exampleMenuBtn"); page.wait_for_timeout(300)
        page.click("#btnEx"); page.wait_for_timeout(4500)
        page.wait_for_timeout(3000); c=page.locator('.ocard[data-kind="boundary"]').first; c.click(); page.wait_for_timeout(800); c.dblclick(delay=90); page.wait_for_timeout(3500)
        res["entered"] = page.evaluate("() => !document.getElementById('objectWorkspace').hidden")
        res["first_visit"] = page.evaluate(SUM)
        d = page.locator('#feSelectionSummary [data-guidance-dismiss]')
        if d.count() and d.first.is_visible(): d.first.click(); page.wait_for_timeout(400)
        res["after_dismiss"] = page.evaluate(SUM)
        rows = page.locator('#faceLayerList [data-timber-id]'); n = rows.count(); res["timberRows"] = n
        if n >= 2:
            rows.nth(0).click(); page.wait_for_timeout(500)
            for i in range(1, n):
                rows.nth(i).click(modifiers=["Shift"]); page.wait_for_timeout(500)
            res["multi_sel"] = page.evaluate(SUM)
            page.screenshot(path=str(SHOTS / "B6-face-multisel-1382.png"))
            res["multi_inspector_text"] = (page.evaluate("() => document.getElementById('faceInspectorContent').innerText.slice(0,120)"))
        page.click('[data-face-tool="grid"]', timeout=15000); page.wait_for_timeout(1500)
        txt = page.evaluate("() => document.getElementById('faceInspectorContent').innerText")
        terms = ["cell", "格內位置", "對齊頂點", "對齊格子", "主支", "副支", "主網格", "副網格", "子網格", "格子", "頂點"]
        res["g4_face_grid_pane"] = {"chars": len(txt), "counts": {t: len(re.findall(t, txt, re.I)) for t in terms if re.search(t, txt, re.I)},
                                    "lines": [l.strip() for l in txt.splitlines() if l.strip() and any(t.lower() in l.lower() for t in terms)][:30],
                                    "activeTab": page.evaluate("() => document.querySelector('.fi-tab.active')?.textContent")}
        page.screenshot(path=str(SHOTS / "G4-face-grid-pane-1382.png"))
        res["errors"] = errors[:10]
    except Exception as ex:
        res["exception"] = str(ex)[:300]
    finally:
        save("stage_h.json", res); ctx.close()
print("done", list(res.keys()), res.get("exception"))
