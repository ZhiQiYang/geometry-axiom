from common import *
exec(open(Path(__file__).with_name("t1_focus.py"), encoding="utf-8").read().split("res = {")[0].replace("from common import *", ""))
res = {"sha": "d6b4b450d741fcbbfd75c51631915d3082926990"}
mem_gate("t1b")
with sync_playwright() as pw:
    ctx, page, errors = session(pw, VIEWS["1382x804"], "t1b")
    try:
        open_app(page)
        # 3D 重複:第一次 Tab 的 activeElement 與 body 的關係
        page.click("#fileMenuBtn"); page.wait_for_timeout(300)
        page.click("#btnModelLibraryMenu"); page.wait_for_timeout(1500)
        if page.evaluate("() => { const e=document.getElementById('smLibraryPanel'); return !!e && !e.hidden; }"):
            page.click("#smBackToBuild"); page.wait_for_timeout(800)
        page.evaluate("() => document.activeElement && document.activeElement.blur()")
        seq = []
        for i in range(3):
            page.keyboard.press("Tab"); page.wait_for_timeout(150)
            seq.append(page.evaluate(INFO))
        res["sm_repeat"] = seq
        page.keyboard.press("Escape"); page.wait_for_timeout(500)
        if page.evaluate("() => !!document.querySelector('dialog.sm-workspace[open]')"):
            page.click("#smClose"); page.wait_for_timeout(500)
        load_example(page)
        res["face_entered"] = enter_face(page)
        d = page.locator('#feSelectionSummary [data-guidance-dismiss]')
        if d.count() and d.first.is_visible(): d.first.click(); page.wait_for_timeout(400)
        page.keyboard.press("Tab"); page.wait_for_timeout(100)  # 讓最近互動為鍵盤
        res["tool_buttons"] = page.evaluate("() => [...document.querySelectorAll('#faceWorkspaceTools button, #faceWorkspaceTools [data-face-tool]')].map(b=>({id:b.id,tool:b.dataset.faceTool||'',text:(b.title||b.textContent).trim().slice(0,12),vis:b.getClientRects().length>0}))")
        page.evaluate("() => document.querySelector('[data-face-tool=\"select\"]').focus()")
        seq = [page.evaluate(INFO)]
        for i in range(9):
            page.keyboard.press("Tab"); page.wait_for_timeout(100)
            seq.append(page.evaluate(INFO))
        res["toolbar_walk"] = seq
        page.screenshot(path=str(SHOTS / "t1b-face-toolbar-focus.png"), clip={"x": 0, "y": 100, "width": 700, "height": 120})
        res["errors"] = errors[:10]
    except Exception as ex:
        res["exception"] = str(ex)[:400]
    finally:
        save("t1b_toolbar.json", res); ctx.close()
for s in res.get("sm_repeat", []): print("SM", s["id"], s["tag"], s["inDialog"], s["focusVisible"], s["outline"])
for s in res.get("toolbar_walk", []): print("TB", s["id"], s["tool"], s["inFaceTools"], s["focusVisible"], s["outline"], s["outlineOffset"])
print(res.get("tool_buttons"), res.get("exception"))
