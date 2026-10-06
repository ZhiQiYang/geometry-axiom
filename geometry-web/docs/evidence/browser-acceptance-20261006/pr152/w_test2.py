import sys, json, subprocess, time, shutil
sys.path.insert(0, r"D:/geometry-axiom-bqa/geometry-web/docs/evidence/browser-acceptance-20261006/env")
from common import *
OUT = EVID / "pr152"; URL = "http://127.0.0.1:8871/"; R = {}; PIDS = []
CLI = r"D:\geo-bqa-152\geometry-web\work-manager\cli.py"
def rec(k, s, n=""): R[k] = {"status": s, "note": n}; print(k, s, n[:220], flush=True)
def start(data):
    p = subprocess.Popen(["python", CLI, "--data-dir", data, "serve", "--port", "8871"], cwd=r"D:\geo-bqa-152", stdout=open(ROOT / "wm2.out", "ab"), stderr=open(ROOT / "wm2.err", "ab"))
    PIDS.append(p.pid); time.sleep(3); return p
def stop(p): p.kill(); p.wait()
def cli(data, *a): return subprocess.run(["python", CLI, "--data-dir", data, *a], capture_output=True, text=True, cwd=r"D:\geo-bqa-152")
D = str(ROOT / "wm152")
# main service (pid 28880) must be stopped first, by recorded pid
subprocess.run(["powershell", "-NoProfile", "-Command", "Stop-Process -Id 28880 -Force"]); time.sleep(1)
gate("pr152-p2")
with sync_playwright() as pw:
    p = start(D)
    ctx, page, errs = launch(pw, (1382, 804), "152e")
    page.goto(URL, wait_until="load"); page.wait_for_timeout(1000)
    h0 = page.inner_text("#state-hash").strip(); rows0 = page.locator(".task-row").count()
    stop(p); page.click("#refresh-button"); page.wait_for_timeout(1500)
    vis = page.is_visible("#fetch-error"); txt = page.inner_text("#fetch-error") if vis else ""
    kept = page.locator(".task-row").count() == rows0 and page.inner_text("#state-hash").strip() == h0
    page.screenshot(path=str(OUT / "w09_fetch_error.png"))
    p = start(D); page.click("#refresh-button"); page.wait_for_timeout(1500)
    rec_ok = not page.is_visible("#fetch-error")
    rec("W-09", "PASS" if vis and "狀態讀取失敗" in txt and kept and rec_ok else "FAIL", f"error visible={vis} text={txt!r} kept={kept} recovered={rec_ok}")
    # W-16 reopen
    stop(p); p = start(D); page.reload(wait_until="load"); page.wait_for_timeout(1000)
    h1 = page.inner_text("#state-hash").strip(); ok16 = h1 == h0 and page.locator(".task-row").count() == 3
    # export + restore via HTTP -> CLI
    import http.client
    c = http.client.HTTPConnection("127.0.0.1", 8871); c.request("GET", "/api/export"); body = c.getresponse().read()
    bk = ROOT / "wm152-backup.json"; bk.write_bytes(body)
    rd = str(ROOT / "wm152-restored"); shutil.rmtree(rd, ignore_errors=True)
    r1 = cli(rd, "restore", str(bk)); r2 = cli(rd, "reconcile")
    ph = json.loads(r2.stdout)["payload_hash"] if r2.returncode == 0 else None
    orig = json.loads(cli(D, "reconcile").stdout)["payload_hash"]
    rec("W-16", "PASS" if ok16 and ph == orig else "FAIL", f"reopen same hash={h1==h0}; restore rc={r1.returncode}/{r1.stderr[:100]!r} payload eq={ph==orig}")
    ctx.close(); stop(p)
    # W-10 XSS
    xd = str(ROOT / "wm152xss"); p = start(xd)
    ctx, page, errs = launch(pw, (1382, 804), "152x"); page.goto(URL, wait_until="load"); page.wait_for_timeout(1500)
    r = page.evaluate("()=>({xss:window.__xss,imgs:document.querySelectorAll('img').length,scripts:[...document.scripts].map(s=>s.src||'inline').length,jsLinks:[...document.querySelectorAll('a')].filter(a=>/^javascript:/i.test(a.getAttribute('href')||'')).length,text:document.body.innerText.includes('<img src=x')})")
    page.screenshot(path=str(OUT / "w10_xss.png"))
    rec("W-10", "PASS" if r["xss"] is None and r["imgs"] == 0 and r["text"] and r["jsLinks"] == 0 else "FAIL", f"title injection only (javascript: URL import rejected by CLI validation, see w10_url_import_rejected.txt) {r} errs={errs}")
    ctx.close(); stop(p)
    # W-18 empty
    ed = str(ROOT / "wm152empty"); shutil.rmtree(ed, ignore_errors=True); p = start(ed)
    ctx, page, errs = launch(pw, (1382, 804), "152y"); page.goto(URL, wait_until="load"); page.wait_for_timeout(1500)
    r = page.evaluate("()=>({tc:document.getElementById('task-count').innerText,src:document.getElementById('source-mode').innerText,cov:document.getElementById('coverage-overview-summary').innerText,rows:document.querySelectorAll('.task-row').length})")
    page.screenshot(path=str(OUT / "w18_empty.png"))
    rec("W-18", "PASS" if r["rows"] == 0 and "尚未" in r["cov"] else "FAIL", f"{r} errs={errs}")
    ctx.close(); stop(p)
(OUT / "results_part2.json").write_text(json.dumps({"results": R, "own_pids": PIDS}, ensure_ascii=False, indent=1), encoding="utf-8")
