"""Independent service-restart recovery of the unchanged formal Q38 archive.

No fixture creation, reset, New, Save, history mutation or archive rewriting.
The archive contains copied-host and unplaced runs, not a live placement host.
"""
from contextlib import contextmanager
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import traceback
from urllib.request import Request, urlopen
import zipfile
from playwright.sync_api import sync_playwright

# Current-run bindings are captured by run_q38_restart.py from a verified same-head
# producer and two services it actually starts. Historical receipts stay immutable.
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--binding', required=True, type=Path)
args = parser.parse_args()
def interrupted(signum, _frame):
    raise InterruptedError('received signal ' + str(signum))
signal.signal(signal.SIGTERM, interrupted)
CONFIG = json.loads(args.binding.read_text())
ROOT = Path(CONFIG['root'])
BASE = args.binding.parent
URL = CONFIG['url']
OUT = Path(CONFIG['output'])
ARCHIVE = Path(CONFIG['archive'])
BASELINE = Path(CONFIG['baseline'])
HEAD = CONFIG['head']
TREE = CONFIG['tree']
RUNTIME = CONFIG['restart']['after']['runtime']['version']
ARCHIVE_SHA = CONFIG['archiveSha256']
PID = CONFIG['restart']['after']['runtime']['pid']
SESSION = CONFIG['restart']['after']['runtime']['session']
DEFAULT_LINES = [
    "surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000",
    "timber 1 27 33 role boundary", "place 1 on 1 at-face e0 +u +n",
    "timber 2 27 33 role boundary", "place 2 on 1 at-face e2 +u +n",
    "spec 主支中線 500", "guide 1 1 v spec:主支中線",
    "timber 3 27 33 role primary", "place 3 on 1 at-line guide 1 +v +n",
]
DEFAULT_WORLD = """boundary 1 outline 0,0 4000,0 4000,3000 0,3000
placement 1 on boundary 1 origin 0 0 2500 u +x v +y
spec 主支中線 500
timber 1 27 33 role boundary
timber 2 27 33 role boundary
timber 3 27 33 role primary
guide 1 1 v spec:主支中線
place 1 on 1 at-face e0 +u +n
# R18 角材 1: onBoundary=true coversEdge=true boundaryEdge=0
place 2 on 1 at-face e2 +u +n
# R18 角材 2: onBoundary=true coversEdge=true boundaryEdge=2
place 3 on 1 at-line guide 1 +v +n
# R18 角材 3: onBoundary=false coversEdge=false boundaryEdge=-1
"""
EXPECTED = [
    "archive bytes match the previously recorded formal SHA256",
    "same clean product starts in the explicitly new native-service process and session",
    "restarted native World equals the committed built-in default and has no Q38 records without seeding",
    "fresh browser reaches the actual product and preserves the original default World without Q38 records",
    "no fixture creation reset or import occurs before the trusted Open action",
    "trusted Open invokes the actual project file chooser",
    "complete manifest from the recovered World and metadata equals the original archive manifest",
    "full reopened World equals original archive and formal model source bytes",
    "all typed profiles members runs and copied-host details match original source records",
    "seven rebuilt meshes including all geometry metadata equal the complete formal baseline package",
    "reopened native-run UI displays copied-host world model and local sibling correctly",
    "archive and baseline files are unchanged after recovery",
    "clean head tree runtime process session and browser health remain stable",
]
assert not OUT.exists(), "A new recovery evidence directory is required"
OUT.mkdir(parents=True)
(OUT / "harness.py").write_bytes(Path(__file__).read_bytes())
checks, requests, errors = [], [], []
phase = "before-browser"
browser = page = None


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def http(path, payload=None):
    request = URL + path
    if payload is not None:
        request = Request(request, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def native(command):
    result = http("api", {"cmd": command})
    assert result["ok"], result
    return result


def identity():
    def git(*args):
        return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()
    return {"head": git("rev-parse", "HEAD"), "tree": git("rev-parse", "HEAD^{tree}"),
            "status": git("status", "--porcelain=v1", "--untracked-files=all"), "runtime": http("runtime")}


def check(value, detail=None):
    name = EXPECTED[len(checks)]
    checks.append({"name": name, "pass": value is True, "detail": detail})
    print(("PASS " if value is True else "FAIL ") + name, flush=True)
    assert value is True, name + ": " + repr(detail)


def js(body, arg=None):
    return page.evaluate("async arg=>{" + body + "}", arg)


def observe(request):
    if request.method == "POST":
        try:
            payload = request.post_data_json
        except Exception:
            payload = request.post_data
        requests.append({"phase": phase, "url": request.url, "payload": payload})


@contextmanager
def playwright_evidence():
    driver = sync_playwright().start()
    try:
        yield driver
    except Exception:
        if page is not None:
            try:
                page.screenshot(path=str(OUT / "failed.png"), full_page=True)
                write("failed-ui.json", {"text": page.locator("body").inner_text(), "world": native("dump")["text"]})
            except Exception:
                pass
        raise
    finally:
        driver.stop()


receipt = {"schema": "geometry-q38-service-restart-recovery/1", "command": [sys.executable, *sys.argv],
           "harnessSha256": sha(__file__), "root": str(ROOT), "url": URL, "archive": str(ARCHIVE),
           "baseline": str(BASELINE), "expectedChecks": EXPECTED,
           "priorDelivery": CONFIG["producerBindingPath"],
           "restartIdentity": str(args.binding),
           "limitations": ["This is a new 13-check restart-recovery run, not a rerun or recount of the prior 18-check gate.",
                           "The unchanged archive contains one copied host and two unplaced runs; it contains no live placement host.",
                           "Native state starts at reference_default_world from committed transactions.inc, with no Q38 records. Only actual Open imports the original archive; no fixture is seeded.",
                           "The web_bridge comment naming room_a.scene is historical; actual initialization uses reference_default_world and differs from that file.",
                           "Linux Chromium file chooser only. No Save or native OS save-picker operation occurs."]}
code = 1
try:
    formal = CONFIG["producer"]
    receipt["archiveSha256Before"] = sha(ARCHIVE)
    receipt["baselineSha256Before"] = sha(BASELINE)
    check(receipt["archiveSha256Before"] == ARCHIVE_SHA == formal["artifactsSha256"][str(ARCHIVE)] and
          receipt["baselineSha256Before"] == formal["artifactsSha256"][str(BASELINE)])
    baseline = json.loads(BASELINE.read_text())
    with zipfile.ZipFile(ARCHIVE) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        world = archive.read("world.scene").decode("utf-8")
    assert manifest["format"] == "geometry-canvas/16" and manifest["requiredCapabilities"] == ["section-profile/1"]
    typed = {"profile": [], "member": [], "run": []}
    for line in world.splitlines():
        tokens = line.split()
        if tokens[0] == "section-profile":
            typed[tokens[1]].append(json.loads(base64.b64decode(tokens[2])))
    receipt["fixtureScope"] = {"profiles": len(typed["profile"]), "members": len(typed["member"]), "runs": len(typed["run"]),
                              "copiedHosts": 1, "livePlacementHosts": 0, "unplacedRuns": 2}
    before = receipt["before"] = identity()
    runtime = before["runtime"]
    recorded_restart = CONFIG["restart"]["after"]["runtime"]
    receipt["sinceOriginalArchive"] = {"formalHead": formal["head"], "formalTree": formal["tree"],
        "changedFiles": subprocess.check_output(["git", "-C", str(ROOT), "diff", "--name-only", formal["head"], HEAD], text=True).splitlines()}
    check(before["head"] == HEAD and before["tree"] == TREE and before["status"] == "" and
          receipt["sinceOriginalArchive"]["changedFiles"] == [] and formal["head"] == HEAD and
          runtime["pid"] != CONFIG["restart"]["before"]["runtime"]["pid"] and
          runtime["session"] != CONFIG["restart"]["before"]["runtime"]["session"] and
          runtime == recorded_restart and runtime["fresh"] is True and runtime["root"] == str(ROOT) and
          runtime["pid"] == PID and runtime["session"] == SESSION and runtime["pid"] != formal["runtime"]["pid"] and
          runtime["session"] != formal["runtime"]["session"] and runtime["version"] == RUNTIME, before)
    receipt["worldBeforeBrowser"] = native("dump")["text"]
    source = (ROOT / "geometry-core/transactions.inc").read_text()
    initializer = re.search(r"static bool reference_default_world\(World \*world\).*?const char \*lines\[\]=\{(.*?)\};", source, re.S)
    declared_lines = re.findall(r'"([^"\n]*)"', initializer.group(1))
    initial_state = native("section-profile-read")["state"]
    receipt["startupDefinition"] = {"source": "geometry-core/transactions.inc:629", "sourceSha256": sha(ROOT / "geometry-core/transactions.inc"),
                                    "declaredLines": declared_lines, "typedState": initial_state,
                                    "expectedCanonicalWorld": DEFAULT_WORLD}
    check(declared_lines == DEFAULT_LINES and receipt["worldBeforeBrowser"] == DEFAULT_WORLD and
          all(initial_state[k] == [] for k in ("profiles", "members", "runs")))
    with playwright_evidence() as driver:
        browser = driver.chromium.launch(executable_path=CONFIG["chromium"], headless=True, chromium_sandbox=True, args=[])
        receipt["browser"] = {"version": browser.version, "executable": CONFIG["chromium"], "sandbox": True,
                              "profile": "new Playwright-owned temporary browser process/profile; no persisted context"}
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        page.on("request", observe)
        page.on("dialog", lambda dialog: dialog.accept())
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        page.goto(URL)
        page.wait_for_function("connection.phase==='ready'&&!ReferenceWorkspace.busy&&!oc.busy")
        navigation_state = native("section-profile-read")["state"]
        check(page.title() == "構形 Canvas · 工程規格與空間建模" and page.url == URL and native("dump")["text"] == DEFAULT_WORLD and
              all(navigation_state[k] == [] for k in ("profiles", "members", "runs")))
        mutations = [r for r in requests if (type(r["payload"]) is dict and
                     re.match(r"^(reset|default|line |loadfile |load-commit |section-profile-confirm |engineering-confirm |assembly-confirm )", str(r["payload"].get("cmd", ""))))
                     or r["url"].endswith(("/section-profile/preview", "/engineering/preview", "/assembly/preview"))]
        check(not mutations, mutations)
        phase = "open-original-archive"
        with page.expect_file_chooser() as selecting:
            page.locator("#fileMenuBtn").click()
            page.locator("#btnOpenProject").click()
        chooser = selecting.value
        check(chooser.element.get_attribute("id") == "projectFile")
        chooser.set_files(ARCHIVE)
        page.wait_for_function("id=>ReferenceWorkspace.context().id===id&&!ReferenceWorkspace.busy", arg=manifest["projectId"])
        phase = "verify-recovered-data"
        actual_manifest = js("const metadata=await ReferenceWorkspace.manifest();const r=await fetch('/api',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cmd:'dump'})}).then(r=>r.json());if(!r.ok)throw Error(JSON.stringify(r));const bytes=await GeometryProject.pack(r.text,metadata,new Map(),fflate);return JSON.parse(new TextDecoder().decode(fflate.unzipSync(bytes)['manifest.json']));")
        write("recovered-manifest.json", actual_manifest)
        check(actual_manifest == manifest, {"actual": actual_manifest, "expected": manifest})
        actual_world = native("dump")["text"]
        (OUT / "recovered-world.scene").write_text(actual_world, encoding="utf-8")
        check(actual_world == world == baseline["definitions"]["base_scene"])
        state = native("section-profile-read")["state"]
        write("recovered-native-state.json", state)
        actual_values = [[r["value"] for r in state[key]] for key in ("profiles", "members", "runs")]
        expected_values = [typed[k] for k in ("profile", "member", "run")]
        placements = [r["placement"] for r in typed["run"]]
        check(actual_values == expected_values and sum(p is None for p in placements) == 2 and
              sum(p is not None and p.get("host", {}).get("kind") == "space-wall-values" for p in placements) == 1 and
              not any(p and p.get("host", {}).get("kind") == "placement" for p in placements))
        rebuilt = http("model", {"definitions": {"base_scene": actual_world, "extensions": []}, "request": baseline["request"]})
        verified = http("model/verify", rebuilt)
        write("recovered-model.json", rebuilt)
        check(len(rebuilt.get("derived", {}).get("objects", [])) == 7 and rebuilt == baseline == verified)
        page.locator("#fileMenuBtn").click(); page.locator("#btnModelLibraryMenu").click()
        page.locator('[data-sp-open-run="12"]').click()
        page.wait_for_function("!document.getElementById('spExportModel').disabled")
        check("世界座標" in page.locator("#spCoordinateSpace").inner_text() and "7120800 mm³" in page.locator("#spModelSummary").inner_text() and
              "未定位" in page.locator('[data-sp-run="13"]').inner_text() and "依已刪空間天花板取值" in page.locator("#sectionProfileWorkspace").inner_text())
        page.screenshot(path=str(OUT / "recovered-copied-host-model.png"), full_page=True)
        receipt["archiveSha256After"] = sha(ARCHIVE)
        receipt["baselineSha256After"] = sha(BASELINE)
        check(receipt["archiveSha256Before"] == receipt["archiveSha256After"] == ARCHIVE_SHA and
              receipt["baselineSha256Before"] == receipt["baselineSha256After"])
        receipt["after"] = identity()
        check(receipt["after"] == before and not errors and sha(__file__) == receipt["harnessSha256"], errors)
        browser.close(); browser = page = None
    assert [c["name"] for c in checks] == EXPECTED and all(c["pass"] for c in checks)
    code = 0
except Exception:
    receipt["error"] = traceback.format_exc()
    print(receipt["error"], file=sys.stderr)
finally:
    if browser is not None:
        try:
            browser.close()
        except Exception:
            pass
    summary = {"schema": "geometry-q38-service-restart-recovery-result/1", "completed": code == 0,
               "expected": len(EXPECTED), "passed": sum(c["pass"] for c in checks), "failed": 0 if code == 0 else 1, "ok": code == 0}
    write("result.json", {**summary, "checks": checks, "errors": errors})
    receipt.update(exitCode=code, phase=phase)
    write("run.json", receipt)
    write("browser-requests.json", requests)
    print("Q38_SERVICE_RESTART_RECOVERY_RESULT " + json.dumps(summary), flush=True)
sys.exit(code)
