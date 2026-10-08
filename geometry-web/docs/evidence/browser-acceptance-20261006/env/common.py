# bqa common helpers. Local Windows 11. Uses playwright (geo2a-venv, read-only reuse).
import json, os, shutil, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(os.environ["USERPROFILE"]) / "AppData/Local/Temp/geobqa"
EVID = Path(r"D:/geometry-axiom-bqa/geometry-web/docs/evidence/browser-acceptance-20261006")
def sample():
    out = subprocess.run(["powershell","-NoProfile","-Command",
      "$o=Get-CimInstance Win32_OperatingSystem; $c=(Get-CimInstance Win32_Processor|Measure-Object LoadPercentage -Average).Average; "
      "$t=Get-Process|Sort-Object WS -Descending|Select -First 5|%{\"$($_.ProcessName):$($_.Id)\"}; "
      "\"$([int]($o.FreePhysicalMemory/1024))|$c|$($t -join ',')\""],capture_output=True,text=True).stdout.strip().split("|")
    return {"free_mb":int(out[0]),"cpu_pct":float(out[1] or 0),"top5":out[2],"t":time.strftime("%H:%M:%S")}
def gate(label, limit=800, wait_s=900):
    t0=time.time(); bad=0
    while True:
        s=sample()
        with open(ROOT/"resource.log","a") as f: f.write(json.dumps({"label":label,**s})+"\n")
        if s["free_mb"]>=limit and s["cpu_pct"]<70: return s
        if time.time()-t0>wait_s: raise RuntimeError("BLOCKED:resource "+json.dumps(s))
        time.sleep(20)
def launch(pw, size, tag, channel=None):
    prof=ROOT/f"profile-{tag}"; shutil.rmtree(prof,ignore_errors=True)
    kw=dict(headless=True,viewport={"width":size[0],"height":size[1]},device_scale_factor=1,
            args=["--disable-gpu","--no-first-run","--disable-extensions","--disable-background-networking"],
            accept_downloads=True, downloads_path=str(ROOT/f"dl-{tag}"))
    if channel: kw["channel"]=channel
    ctx=pw.chromium.launch_persistent_context(str(prof),**kw)
    page=ctx.pages[0] if ctx.pages else ctx.new_page()
    errs=[]
    page.on("pageerror",lambda e:errs.append("pageerror: "+str(e)[:300]))
    page.on("console",lambda m:errs.append("console.error: "+m.text[:300]) if m.type=="error" else None)
    return ctx,page,errs
