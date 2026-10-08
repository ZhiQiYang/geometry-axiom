"""Q38 fresh-browser archive acceptance with independently authored native bytes.

Fixture creation uses public native preview/confirm APIs. Save, New, Open and
history use real browser controls. It complements the UI authoring gate, the
35-case model-library gate and the 33-case ordinary save gate; counts stay separate.
The unavailable headless OS save dialog is explicitly disabled to exercise the
product's download fallback; no native OS picker claim is made.
"""
import base64
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
from urllib.parse import urlsplit
from urllib.request import urlopen
import zipfile

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
URL = os.environ["GEOMETRY_TEST_URL"].rstrip("/") + "/"
OUT = Path(os.environ["GEOMETRY_Q38_SAVE_OUT"]).resolve()
parsed = urlsplit(URL)
assert parsed.scheme == "http" and parsed.hostname == "127.0.0.1" and parsed.port not in (None, 8765)
assert parsed.path == "/" and not (parsed.query or parsed.fragment or parsed.username or parsed.password)
assert not OUT.is_relative_to(ROOT) and OUT != Path("/")
assert not OUT.exists() or not any(OUT.iterdir()), "Evidence directory must be new or empty"
OUT.mkdir(parents=True, exist_ok=True)
EXPECTED = 18
checks, errors = [], []
page, browser = None, None
phase = "identity"


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def literal(value):
    return {"kind": "literal", "value": value}


PROFILES = [
    {"id": 1, "name": "保存凹形", "outline": [[0, 0], [400, 0], [400, 60], [60, 60], [60, 250], [0, 250]]},
    {"id": 2, "name": "零構件斷面", "outline": [[-10, -20], [10, -20], [10, 20], [-10, 20]]},
    {"id": 3, "name": "未使用空斷面", "outline": [[0, 0], [10, 0], [10, 20], [0, 20]]},
]
MEMBERS = [
    {"id": 7, "profileId": 1, "kind": "timber", "A": literal(27), "B": literal(33), "orientation": "A-v", "u0": 0, "v0": 0},
    {"id": 8, "profileId": 1, "kind": "panel", "panelSpec": "calcium-silicate-6", "width": 346, "orientation": "thickness-v", "u0": 33, "v0": 0},
]
HOST = {"kind": "space-wall-values", "sourceDescription": "依已刪空間天花板取值，不隨空間變動",
        "frame": {"origin": [100, 200, 2700], "U": "+X", "V": "+Y", "N": "+Z"},
        "region": {"outline": [[0, 0], [5000, 0], [5000, 4000], [0, 4000]],
                   "holes": [[[1000, 1000], [1100, 1000], [1100, 1100], [1000, 1100]]]}}
RUNS = [
    {"id": 12, "profileId": 1, "length": literal(2400), "placement": {"kind": "simple", "host": HOST, "dir": "+v", "p": 20, "q": 30, "up": "+Z"}},
    {"id": 13, "profileId": 1, "length": literal(2001), "placement": None},
    {"id": 14, "profileId": 2, "length": literal(50), "placement": None},
]
RECORDS = [(kind, item) for kind, values in (("profile", PROFILES), ("member", MEMBERS), ("run", RUNS)) for item in values]
WORLD = "requires section-profile/1\n" + "".join("section-profile " + kind + " " + base64.b64encode(canonical(item).encode()).decode() + "\n" for kind, item in RECORDS)


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def identity():
    def git(*args):
        return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()
    runtime = json.load(urlopen(URL + "runtime", timeout=10))
    assert runtime["fresh"] is True and Path(runtime["root"]).resolve() == ROOT
    return {"head": git("rev-parse", "HEAD"), "tree": git("rev-parse", "HEAD^{tree}"),
            "status": git("status", "--porcelain=v1", "--untracked-files=all"), "runtime": runtime}


def check(label, actual, expected=True):
    passed = actual == expected
    checks.append({"name": label, "pass": passed})
    print(("PASS " if passed else "FAIL ") + label, flush=True)
    assert passed, f"{label}: {actual!r} != {expected!r}"


def js(body, arg=None):
    return page.evaluate("async arg=>{" + body + "}", arg)


def native(command):
    return js("const r=await apiRequest(arg);if(!r.ok)throw Error(JSON.stringify(r));return r;", command)


def world():
    return native("dump")["text"]


def ready():
    page.wait_for_function("connection.phase==='ready'&&!ReferenceWorkspace.busy&&!oc.busy")


def menu(selector):
    page.locator("#fileMenuBtn").click()
    page.locator(selector).click()
    ready()


def history(kind):
    page.locator("#btnUndo" if kind == "undo" else "#btnRedo").click()
    ready()


def wait_world(value):
    page.wait_for_function("async expected=>{const r=await fetch('/api',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cmd:'dump'})}).then(r=>r.json());return r.ok&&r.text===expected;}", arg=value)


def launch(driver):
    global browser, page
    browser = driver.chromium.launch(executable_path=os.environ.get("GEOMETRY_CHROME", "/usr/bin/chromium"),
                                     headless=True, args=["--no-sandbox"])
    receipt.setdefault("browserLaunches", []).append({"version": browser.version,
        "executable": os.environ.get("GEOMETRY_CHROME", "/usr/bin/chromium"),
        "profile": "new Playwright-owned temporary browser profile; no persisted user context"})
    context = browser.new_context(viewport={"width": 1440, "height": 1000}, accept_downloads=True)
    context.add_init_script("window.__q38OriginalSavePicker=typeof window.showSaveFilePicker;Object.defineProperty(window,'showSaveFilePicker',{configurable:true,writable:true,value:undefined});")
    page = context.new_page()
    page.on("dialog", lambda dialog: dialog.accept())
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.goto(URL)
    ready()
    receipt["browserLaunches"][-1]["savePicker"] = js("return {originalType:window.__q38OriginalSavePicker,testType:typeof window.showSaveFilePicker,mode:'explicit-download-fallback'};")
    assert receipt["browserLaunches"][-1]["savePicker"]["testType"] == "undefined"


@contextmanager
def evidence_playwright():
    driver = sync_playwright().start()
    try:
        yield driver
    except Exception:
        if page is not None:
            try:
                page.screenshot(path=str(OUT / "failed.png"), full_page=True)
                write("failed-state.json", {"world": world(), "text": page.locator("body").inner_text()})
            except Exception:
                pass
        raise
    finally:
        driver.stop()


def model():
    package = js("const r=await fetch('/model',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(arg)}).then(r=>r.json());if(!r.manifest)throw Error(JSON.stringify(r));return r;",
                 {"definitions": {"base_scene": WORLD, "extensions": []}, "request": {"roots": [{"kind": "profile-run", "id": i} for i in (12, 13, 14)], "role": "geometry", "target": "solid-set", "allow_partial": False}})
    actual = []
    for obj in package["derived"]["objects"]:
        details = obj["section_profile"]
        actual.append([obj["root"]["id"], obj["member_path"], obj["role"], details["coordinate_space"], obj["volume_mm3"], details["material_volume_mm3"], details["bounds_mm"]])
    expected = [
        [12, [], "reference", "world", "84960000", "0", [[120, 230, 2450], [520, 2630, 2700]]],
        [12, [7], "geometry", "world", "2138400", "2138400", [[120, 230, 2673], [153, 2630, 2700]]],
        [12, [8], "geometry", "world", "4982400", "4982400", [[153, 230, 2694], [499, 2630, 2700]]],
        [13, [], "reference", "local", "70835400", "0", [[0, 0, 0], [400, 250, 2001]]],
        [13, [7], "geometry", "local", "1782891", "1782891", [[0, 0, 0], [33, 27, 2001]]],
        [13, [8], "geometry", "local", "4154076", "4154076", [[33, 0, 0], [379, 6, 2001]]],
        [14, [], "reference", "local", "40000", "0", [[-10, -20, 0], [10, 20, 50]]],
    ]
    assert actual == expected, (actual, expected)
    verified = js("return await fetch('/model/verify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(arg)}).then(r=>r.json());", package)
    assert verified == package
    return package


receipt = {"schema": "geometry-q38-save-roundtrip/1", "command": [sys.executable, *sys.argv],
           "harnessSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           "environment": {key: os.environ.get(key) for key in ("GEOMETRY_TEST_URL", "GEOMETRY_Q38_SAVE_OUT", "GEOMETRY_CHROME")},
           "limitations": ["Native public preview/confirm APIs create the fixture; UI authoring belongs to the separate Q38 browser gate.",
                           "showSaveFilePicker is explicitly disabled before page load to select the product download fallback; real Chromium download and file chooser are exercised, with no native OS save picker, physical mobile or IME claim.",
                           "All native Q38 definitions are covered; reference image/PDF attachments and draft payloads are outside this fixture."]}
code = 1
try:
    receipt["before"] = identity()
    check("clean exact runtime before archive fixture", receipt["before"]["status"], "")
    with evidence_playwright() as driver:
        launch(driver)
        check("actual nonblank product identity", [page.title(), page.url, page.locator("#btnNewProject").count()], ["構形 Canvas · 工程規格與空間建模", URL, 1])
        menu("#btnNewProject")
        wait_world("")
        phase = "native-fixture"
        revision = native("section-profile-read")["revision"]
        preview = js("return await fetch('/section-profile/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(arg)}).then(r=>r.json());",
                     {"schema": "section-profile-transaction/1", "expectedRevision": revision,
                      "operations": [{"op": "put-" + kind, "value": value} for kind, value in RECORDS]})
        check("native full fixture preview valid", preview.get("ok") is True and preview.get("preview", {}).get("valid") is True)
        native("section-profile-confirm " + str(preview["preview"]["token"]))
        js("await renderObjects();")
        wait_world(WORLD)
        check("authored complete World equals fixed source oracle", world(), WORLD)
        write("original-model.json", model())
        check("original seven meshes have exact independent identities frames bounds volumes", True)
        phase = "save"
        with page.expect_download() as downloading:
            page.locator('#projectBar [data-project-action="save"]').click()
        download = downloading.value
        archive = OUT / "q38-full.gcanvas"
        download.save_as(archive)
        assert download.failure() is None
        with zipfile.ZipFile(archive) as package:
            manifest = json.loads(package.read("manifest.json"))
            archived_world = package.read("world.scene").decode("utf-8")
        check("real Save archive declares complete Q38 format and capability", [manifest["format"], "section-profile/1" in manifest["requiredCapabilities"]], ["geometry-canvas/16", True])
        check("archive includes every authored native byte including copied host holes", archived_world, WORLD)
        write("manifest.json", manifest)
        page.screenshot(path=str(OUT / "01-saved.png"), full_page=True)
        menu("#btnNewProject")
        wait_world("")
        check("New clears native Q38 World before clean browser", world(), "")
        browser.close(); browser = None; page = None
        phase = "fresh-profile"
        launch(driver)
        check("new browser process and empty profile begin without saved native data", [world(), js("return ReferenceWorkspace.context().id===arg;", manifest["projectId"])], ["", False])
        with page.expect_file_chooser() as choosing:
            menu("#btnOpenProject")
        chooser = choosing.value
        check("trusted Open invokes actual project file chooser", chooser.element.get_attribute("id"), "projectFile")
        chooser.set_files(archive)
        page.wait_for_function("id=>ReferenceWorkspace.context().id===id&&!ReferenceWorkspace.busy", arg=manifest["projectId"])
        wait_world(WORLD)
        check("fresh-profile reopen restores fixed complete native World", world(), WORLD)
        state = native("section-profile-read")["state"]
        check("reopened values preserve copied source holes empty profiles and unplaced runs",
              [[row["value"] for row in state[key]] for key in ("profiles", "members", "runs")], [PROFILES, MEMBERS, RUNS])
        write("reopened-model.json", model())
        check("reopened seven meshes recompute exact independent material and reference oracles", True)
        menu("#btnModelLibraryMenu")
        page.locator('[data-sp-open-run="12"]').click()
        page.wait_for_function("!document.getElementById('spExportModel').disabled")
        check("reopened UI identifies world coordinates and excludes envelope from material volume",
              "世界座標" in page.locator("#spCoordinateSpace").inner_text() and "7120800 mm³" in page.locator("#spModelSummary").inner_text())
        page.screenshot(path=str(OUT / "02-fresh-reopened.png"), full_page=True)
        page.locator("#spClose").click()
        phase = "history"
        history("undo"); wait_world("")
        check("successful Q38 import Undo restores exact empty prior World", world(), "")
        history("redo"); wait_world(WORLD)
        check("successful Q38 import Redo restores all typed native definitions", world(), WORLD)
        page.screenshot(path=str(OUT / "03-redone.png"), full_page=True)
        check("no uncaught or console errors in complete save flow", errors, [])
        receipt["after"] = identity()
        def stable(value):
            return {**{k: value[k] for k in ("head", "tree", "status")},
                    "runtime": {k: value["runtime"][k] for k in ("root", "version", "pid", "session", "fresh")}}
        check("clean source runtime process and session remain identical", stable(receipt["after"]), stable(receipt["before"]))
        browser.close(); browser = None; page = None
    assert len(checks) == EXPECTED, (len(checks), EXPECTED)
    code = 0
except Exception:
    receipt["error"] = traceback.format_exc()
    print(receipt["error"], file=sys.stderr)
    if page is not None:
        try:
            page.screenshot(path=str(OUT / "failed.png"), full_page=True)
            write("failed-state.json", {"world": world(), "text": page.locator("body").inner_text()})
        except Exception:
            pass
finally:
    if browser is not None:
        try:
            browser.close()
        except Exception:
            pass
    summary = {"schema": "geometry-q38-save-roundtrip-result/1", "completed": code == 0, "expected": EXPECTED,
               "passed": sum(row["pass"] for row in checks), "failed": 0 if code == 0 else 1, "ok": code == 0}
    write("result.json", {**summary, "phase": phase, "checks": checks, "errors": errors})
    receipt["exitCode"] = code
    write("run.json", receipt)
    print("Q38_SAVE_ROUNDTRIP_RESULT " + json.dumps(summary), flush=True)
sys.exit(code)
