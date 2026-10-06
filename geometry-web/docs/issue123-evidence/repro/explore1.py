import sys
from common import *

out = {}
with sync_playwright() as pw:
    ctx, page, errors = session(pw, VIEWS["1382x804"])
    try:
        open_app(page)
        out["title"] = page.title()
        # real user path: File menu
        page.click("#fileMenuBtn"); page.wait_for_timeout(400)
        out["fileMenuItems"] = page.evaluate("[...document.querySelectorAll('#fileMenuPop button')].map(b=>({id:b.id,text:b.textContent.trim().replace(/\\s+/g,' ').slice(0,40),vis:!!(b.offsetParent)}))")
        page.click("#exampleMenuBtn"); page.wait_for_timeout(300)
        out["exampleItems"] = page.evaluate("[...document.querySelectorAll('#exampleMenuPop button')].map(b=>({id:b.id,text:b.textContent.trim().replace(/\\s+/g,' ').slice(0,50)}))")
        page.click("#sceneMenuBtn"); page.wait_for_timeout(300)
        out["sceneItems"] = page.evaluate("[...document.querySelectorAll('#sceneMenuPop button')].map(b=>({id:b.id,text:b.textContent.trim().replace(/\\s+/g,' ').slice(0,60),data:b.dataset}))")
        page.screenshot(path=str(SHOTS / "explore-menu-1382.png"))
        page.keyboard.press("Escape"); page.keyboard.press("Escape")
        out["errors"] = errors[:10]
    finally:
        save("explore1.json", out)
        ctx.close()
print(json.dumps(out, ensure_ascii=False)[:3500])
