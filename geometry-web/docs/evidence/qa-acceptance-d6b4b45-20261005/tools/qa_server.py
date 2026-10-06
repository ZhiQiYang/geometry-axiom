# -*- coding: utf-8 -*-
"""隔離服務管理:  python qa_server.py start|stop|status|probe <port>

start : 用 QA worktree 的 geometry-web/serve.py 在 <port> 起服務(背景、脫離終端),
        所有可寫資料隔離到 %TEMP%\\geometry-qa\\ 之下:
          feedback -> fb-<port>\\      TEMP/TMP -> tmp-<port>\\      log -> run\\<port>.log
        記 PID 到 run\\<port>.json;等到 /runtime 可連再返回;最後自動跑 runtime_version.py --probe。
stop  : 只停「run\\<port>.json 記的那個 PID(及其子行程 = bridge)」,且先核對該 PID 的命令列
        確實是 serve.py <port>;絕不按名稱殺行程。
status: 印 PID、是否存活、埠是否在聽。
probe : 直接跑 runtime_version.py --probe <port>。
埠限制:預設只允許 8800-8899 且目前沒人在聽;用環境變數 QA_ALLOW_ANY_PORT=1 才放寬(不建議)。
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

QA = Path(os.environ.get("TEMP", ".")) / "geometry-qa"
RUN = QA / "run"
PATHS = QA / "bin" / "paths.json"


def listening(port):
    out = subprocess.run(["netstat", "-ano", "-p", "tcp"], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if "LISTENING" in line and re.search(rf"[:\]]{port}\s", line):
            return line.split()[-1]
    return None


def pid_cmdline(pid):
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        f"(Get-CimInstance Win32_Process -Filter 'ProcessId={pid}').CommandLine"],
                       capture_output=True, text=True)
    return r.stdout.strip()


def start(port):
    if not (8800 <= port <= 8899) and os.environ.get("QA_ALLOW_ANY_PORT") != "1":
        sys.exit(f"拒絕:埠 {port} 不在 8800-8899(防止誤碰使用者既有服務)")
    if listening(port):
        sys.exit(f"拒絕:埠 {port} 已有行程在聽(PID {listening(port)});換一個埠,不要動它")
    if not PATHS.exists():
        sys.exit("找不到 bin\\paths.json,請先跑 python build_qa.py")
    cfg = json.loads(PATHS.read_text(encoding="utf-8"))
    repo = Path(cfg["repo"])
    RUN.mkdir(parents=True, exist_ok=True)
    fb, tmp = QA / f"fb-{port}", QA / f"tmp-{port}"
    fb.mkdir(parents=True, exist_ok=True)
    tmp.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update({
        "GEOMETRY_BRIDGE": cfg["bridge"],
        "GEOMETRY_MODEL_BASE": cfg["model-base"],
        "GEOMETRY_MODEL_UPDATE_BRIDGE": cfg["bridge"],
        "GEOMETRY_FEEDBACK_DIR": str(fb),
        "TEMP": str(tmp), "TMP": str(tmp),
        "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1",
    })
    for k in ("GEOMETRY_BRIDGE_WSL", "GEOMETRY_MODEL_BASE_WSL_DISTRO", "GEOMETRY_MANAGED_PREVIEW", "GEOMETRY_TEST_BRIDGE"):
        env.pop(k, None)
    log = open(RUN / f"{port}.log", "wb")
    flags = 0x00000008 | 0x00000200 | 0x08000000  # DETACHED | NEW_PROCESS_GROUP | NO_WINDOW
    p = subprocess.Popen([sys.executable, str(repo / "geometry-web" / "serve.py"), str(port)], env=env,
                         cwd=str(repo), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                         creationflags=flags, close_fds=True)
    (RUN / f"{port}.json").write_text(json.dumps({"pid": p.pid, "port": port, "feedback": str(fb), "tmp": str(tmp),
                                                  "bridge": cfg["bridge"], "model_base": cfg["model-base"],
                                                  "started": time.strftime("%F %T")}, ensure_ascii=False, indent=1))
    for _ in range(60):
        if p.poll() is not None:
            sys.exit(f"serve.py 啟動即結束(exit={p.returncode});見 {RUN / (str(port) + '.log')}")
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/runtime", timeout=2).read()
            break
        except Exception:
            time.sleep(0.5)
    else:
        sys.exit("等 /runtime 逾時;見 log")
    print(f"started http://localhost:{port}/  PID={p.pid}  feedback={fb}")
    return 0


def stop(port):
    f = RUN / f"{port}.json"
    if not f.exists():
        sys.exit(f"沒有 {f};這個埠不是 qa_server 起的,拒絕處理")
    pid = json.loads(f.read_text(encoding="utf-8"))["pid"]
    cmd = pid_cmdline(pid)
    if not cmd:
        print(f"PID {pid} 已不存在")
    elif "serve.py" in cmd and re.search(rf"serve\.py\W+{port}\b", cmd):
        r = subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, text=True)
        print(r.stdout.strip() or r.stderr.strip())
    else:
        sys.exit(f"PID {pid} 命令列不是 serve.py {port}(PID 可能被重用),拒絕殺:{cmd[:120]}")
    time.sleep(1)
    print("埠仍在聽" if listening(port) else f"埠 {port} 已釋放")
    f.rename(RUN / f"{port}.stopped.json")


def status(port):
    f = RUN / f"{port}.json"
    print(f.read_text(encoding="utf-8") if f.exists() else "no record")
    print("listening PID:", listening(port))


def probe(port):
    cfg = json.loads(PATHS.read_text(encoding="utf-8"))
    r = subprocess.run([sys.executable, str(Path(cfg["repo"]) / "geometry-web" / "runtime_version.py"), "--probe", str(port)])
    return r.returncode


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("start", "stop", "status", "probe"):
        sys.exit(__doc__)
    port = int(sys.argv[2])
    sys.exit({"start": start, "stop": stop, "status": status, "probe": probe}[sys.argv[1]](port) or 0)
