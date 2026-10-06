# 沿用 issue123-evidence/repro/common.py,改:port 8861、ROOT=geo123c、每次 fresh profile、記憶體守門
import json, os, shutil, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(os.environ["USERPROFILE"]) / "AppData/Local/Temp/geo123c"
OUT = Path(r"D:/geometry-axiom-123tests/geometry-web/docs/issue123-c-pending-tests")
SHOTS = OUT / "screenshots"
URL = "http://127.0.0.1:8861/"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
VIEWS = {"1382x804": (1382, 804), "390x844": (390, 844)}


def free_mb():
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1024"],
                         capture_output=True, text=True).stdout.strip()
    return float(out)


def mem_gate(label="", limit=800, wait_s=600):
    t0 = time.time()
    while True:
        m = free_mb()
        if m >= limit:
            return m
        if time.time() - t0 > wait_s:
            raise RuntimeError(f"資源受阻:可用記憶體 {m:.0f}MB < {limit}MB ({label})")
        time.sleep(15)


def fresh_profile(tag):
    p = ROOT / f"profile-{tag}"
    shutil.rmtree(p, ignore_errors=True)
    return p


def session(pw, size, tag):
    prof = fresh_profile(tag)
    ctx = pw.chromium.launch_persistent_context(
        str(prof), executable_path=CHROME, headless=True,
        viewport={"width": size[0], "height": size[1]}, device_scale_factor=1,
        args=["--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
              "--disable-background-networking", "--disable-sync"])
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append("pageerror: " + str(e)[:200]))
    page.on("console", lambda m: errors.append("console." + m.type + ": " + m.text[:200]) if m.type == "error" else None)
    return ctx, page, errors


def open_app(page, timeout=90000):
    page.goto(URL, wait_until="domcontentloaded", timeout=timeout)
    page.wait_for_function("typeof apiRequest==='function' && document.getElementById('app') && !document.getElementById('app').inert", timeout=timeout)
    page.wait_for_timeout(600)


def load_example(page):
    page.click("#fileMenuBtn"); page.wait_for_timeout(300)
    page.click("#exampleMenuBtn"); page.wait_for_timeout(300)
    page.click("#btnEx"); page.wait_for_timeout(5000)


def enter_face(page):
    c = page.locator('.ocard[data-kind="boundary"]').first
    c.click(); page.wait_for_timeout(800); c.dblclick(delay=90); page.wait_for_timeout(3500)
    return page.evaluate("() => !document.getElementById('objectWorkspace').hidden")


def save(name, data):
    (OUT / "measurements" / name).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
