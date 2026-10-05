import json, os, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(os.environ["USERPROFILE"]) / "AppData/Local/Temp/geo123"
SHOTS = ROOT / "shots"; SHOTS.mkdir(exist_ok=True)
PROFILE = ROOT / "chrome-profile"
URL = "http://127.0.0.1:8851/"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
VIEWS = {"1382x804": (1382, 804), "1161x804": (1161, 804), "900x804": (900, 804), "390x844": (390, 844)}


def session(pw, size, profile=PROFILE):
    ctx = pw.chromium.launch_persistent_context(
        str(profile), executable_path=CHROME, headless=True,
        viewport={"width": size[0], "height": size[1]}, device_scale_factor=1,
        args=["--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
              "--disable-background-networking", "--disable-sync"],
        has_touch=size[0] < 600, is_mobile=False)
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append("pageerror: " + str(e)[:200]))
    page.on("console", lambda m: errors.append("console." + m.type + ": " + m.text[:200]) if m.type == "error" else None)
    return ctx, page, errors


def open_app(page, timeout=90000):
    page.goto(URL, wait_until="domcontentloaded", timeout=timeout)
    page.wait_for_function("typeof apiRequest==='function' && document.getElementById('app') && !document.getElementById('app').inert", timeout=timeout)
    page.wait_for_timeout(600)


def rect(page, sel):
    return page.evaluate("""s => { const e=document.querySelector(s); if(!e) return null; const r=e.getBoundingClientRect(), cs=getComputedStyle(e);
      return {x:+r.x.toFixed(1),y:+r.y.toFixed(1),w:+r.width.toFixed(1),h:+r.height.toFixed(1),right:+r.right.toFixed(1),bottom:+r.bottom.toFixed(1),
      hidden:e.hidden||cs.display==='none'||cs.visibility==='hidden', fs:cs.fontSize, lh:cs.lineHeight, color:cs.color, bg:cs.backgroundColor, br:cs.borderRadius, pos:cs.position}; }""", sel)


def save(name, data):
    (ROOT / name).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
