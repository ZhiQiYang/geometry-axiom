import sys,json
sys.path.insert(0,r"D:/geometry-axiom-bqa/geometry-web/docs/evidence/browser-acceptance-20261006/env")
from common import *
with sync_playwright() as pw:
    ctx,page,e=launch(pw,(390,844),"152p"); page.goto("http://127.0.0.1:8871/",wait_until="load"); page.wait_for_timeout(1200)
    print(json.dumps(page.evaluate("()=>[...document.querySelectorAll('#task-rows td')].filter(t=>!t.dataset.label).map(t=>({row:t.closest('tr').dataset.taskId,html:t.outerHTML.slice(0,200),text:t.innerText.slice(0,60)}))"),ensure_ascii=False,indent=1))
    print(json.dumps(page.evaluate("()=>[...document.querySelectorAll('#task-rows th, #task-rows thead th, table thead th')].length"))); ctx.close()
