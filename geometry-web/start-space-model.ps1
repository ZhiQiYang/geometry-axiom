param(
    [ValidateRange(1024, 65535)][int]$Port = 18835,
    [ValidatePattern('^[A-Za-z0-9._-]+$')][string]$Distro = 'Ubuntu-24.04',
    [switch]$VerifyOnly,
    [switch]$NoBrowser
)
$ErrorActionPreference = 'Stop'
if ($VerifyOnly -and -not $PSBoundParameters.ContainsKey('Port')) { $Port = 18836 }

# Check Windows localhost as well as Linux below. Otherwise an older Windows
# service can hide the new WSL server behind exactly the same browser URL.
$spacePortProbe = [System.Net.Sockets.TcpClient]::new()
try {
    $spaceConnect = $spacePortProbe.ConnectAsync('127.0.0.1', $Port)
    try { $null = $spaceConnect.Wait(500) } catch { }
    $spacePortBusy = $spacePortProbe.Connected
} finally {
    $spacePortProbe.Dispose()
}
if ($spacePortBusy) { throw "連接埠 $Port 已有服務，未啟動另一份版本。請保留現有服務，或使用 -Port 指定空閒連接埠。" }
$spacePortReservation = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
try {
    $spacePortReservation.Server.ExclusiveAddressUse = $true
    $spacePortReservation.Start()
} catch {
    throw "連接埠 $Port 無法使用，未啟動另一份版本。請使用 -Port 指定空閒連接埠。"
} finally {
    $spacePortReservation.Stop()
}

# Pass every path as its own native argument; no paths become shell source.
$spaceRepo = Split-Path -Parent $PSScriptRoot
$spaceLinuxOutput = & wsl.exe -d $Distro --user root --exec wslpath -u $spaceRepo.Replace('\', '/')
if ($LASTEXITCODE -ne 0 -or !$spaceLinuxOutput) { throw '無法取得 WSL 專案路徑；需要已安裝的 Ubuntu-24.04。' }
$spaceLinuxRepo = ($spaceLinuxOutput -join "`n").Trim()
$spaceRuntime = '/tmp/geometry-space-model-' + [Guid]::NewGuid().ToString('N')
& wsl.exe -d $Distro --user root --exec mkdir -m 700 $spaceRuntime
if ($LASTEXITCODE -ne 0) { throw '無法建立專用執行目錄。' }

Write-Host '正在編譯目前版本的幾何核心與 3D 建模引擎…'
& wsl.exe -d $Distro --user root --exec gcc -std=c11 -O1 "$spaceLinuxRepo/geometry-web/web_bridge.c" -lm -o "$spaceRuntime/bridge"
if ($LASTEXITCODE -ne 0) { throw '幾何核心編譯失敗，服務未啟動。' }
& wsl.exe -d $Distro --user root --exec gcc -std=c11 -O1 "$spaceLinuxRepo/geometry-core/model_base.c" -lm -o "$spaceRuntime/model-base"
if ($LASTEXITCODE -ne 0) { throw '3D 建模引擎編譯失敗，服務未啟動。' }

# Keep the server and both native engines in the same Linux environment.
# The supervisor owns one process group and never stops other local services.
$spaceSupervisor = @'
import json
import os
from pathlib import Path
import resource
import signal
import socket
import subprocess
import sys
import time
from urllib.request import Request, urlopen

repo, runtime, port_text, verify_text = sys.argv[1:]
Path(runtime, "supervisor.pid").write_text(str(os.getpid()), encoding="ascii")
port = int(port_text)
verify_only = verify_text == "1"
url = "http://127.0.0.1:" + str(port)
process = None
log = None

def fetch(path, body=None):
    request = Request(url + path,
                      data=None if body is None else json.dumps(body).encode("utf-8"),
                      headers={} if body is None else {"Content-Type": "application/json"})
    with urlopen(request, timeout=120) as response:
        if response.headers.get("X-Geometry-Release") != "engineering-spec-v1-20260928":
            raise RuntimeError("The responding service is not the expected engineering-spec-v1 release.")
        return json.load(response)

try:
    # A busy port is a failure, never permission to stop somebody else's process.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        probe.bind(("127.0.0.1", port))
    soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
    target = max(soft, 64 * 1024 * 1024)
    if hard != resource.RLIM_INFINITY:
        target = min(target, hard)
    resource.setrlimit(resource.RLIMIT_STACK, (target, hard))
    env = dict(os.environ)
    env["GEOMETRY_BRIDGE"] = str(Path(runtime) / "bridge")
    env["GEOMETRY_MODEL_BASE"] = str(Path(runtime) / "model-base")
    env.pop("GEOMETRY_BRIDGE_WSL", None)
    env.pop("GEOMETRY_MANAGED_PREVIEW", None)
    if verify_only:
        env["GEOMETRY_FEEDBACK_DIR"] = str(Path(runtime) / "verification-feedback")
    log = open(Path(runtime) / "server.log", "wb")
    process = subprocess.Popen([sys.executable, "-u", str(Path(repo) / "geometry-web/serve.py"), str(port)],
                               cwd=repo, env=env, stdout=log, stderr=subprocess.STDOUT,
                               start_new_session=True)
    # Loading local vendor files from a Windows-mounted drive can be slow on
    # a cold start. Keep checking the owned process while allowing that startup.
    deadline = time.monotonic() + 120
    while True:
        if process.poll() is not None:
            raise RuntimeError("Server exited during startup; inspect " + str(Path(runtime) / "server.log"))
        try:
            examples = fetch("/model/space-examples")
            break
        except OSError:
            if time.monotonic() >= deadline:
                raise RuntimeError("Server startup timed out.")
            time.sleep(0.15)
    if examples.get("schema") != "geometry-space-examples/1" or len(examples.get("examples", [])) < 3:
        raise RuntimeError("Built-in examples are unavailable.")
    capabilities = fetch("/model/capabilities")
    if "geometry-space-preview/2" not in capabilities.get("space_preview_schemas", []):
        raise RuntimeError("The service does not advertise timber space modeling.")
    engineering = fetch("/engineering/read", {})
    if not engineering.get("ok") or "engineering-spec/1" not in engineering.get("state", {}).get("capabilities", []):
        raise RuntimeError("The native engine does not support the engineering specification release.")
    original = fetch("/api", {"cmd": "dump"})
    example = examples["examples"][0]
    candidate = {key: example[key] for key in ("base_scene", "placement_id", "settings")}
    candidate.update(mode="plan", obstacles=[])
    preview = fetch("/model/space-preview", candidate)
    summary = preview.get("summary", {})
    if (not preview.get("ok") or summary.get("volume_mm3") != "33600000000"
            or summary.get("wall_volume_mm3") != "4032000000"):
        raise RuntimeError("3D preview verification failed: " + json.dumps(preview, ensure_ascii=False)[:1500])
    timber_example = next((item for item in examples["examples"] if item.get("id") == "timber-frame"), None)
    if not timber_example or not timber_example.get("timbers"):
        raise RuntimeError("The ready-to-use timber frame example is missing.")
    timber_input = {key: timber_example[key] for key in ("base_scene", "placement_id", "settings", "timbers")}
    timber_input.update(mode="plan", obstacles=[])
    timber_preview = fetch("/model/space-preview", timber_input)
    timber_package = timber_preview.get("timbers", {})
    timber_meshes = timber_package.get("derived", {}).get("objects", [])
    if (not timber_preview.get("ok") or timber_preview.get("schema") != "geometry-space-preview/2"
            or len(timber_meshes) != len(timber_example["timbers"])
            or timber_preview.get("summary", {}).get("timber_count") != len(timber_meshes)):
        raise RuntimeError("Timber preview is incomplete.")
    for mesh in timber_meshes:
        z_values = [point[2] for point in mesh.get("vertices_mm", [])]
        if not z_values or min(z_values) != 2500 or max(z_values) != 2533:
            raise RuntimeError("Timber geometry does not preserve the z=2500 bottom and 33mm thickness.")
    verified = fetch("/model/verify", timber_package)
    if verified.get("manifest", {}).get("geometry_sha256") != timber_package["manifest"]["geometry_sha256"]:
        raise RuntimeError("Timber exchange package verification failed.")
    after = fetch("/api", {"cmd": "dump"})
    if not original.get("ok") or after != original:
        raise RuntimeError("Preview must leave the bridge world unchanged.")
    print("SPACE_MODEL_VERIFIED " + json.dumps({"release": "engineering-spec-v1-20260928", "port": port,
          "examples": len(examples["examples"]), "room_volume_mm3": summary["volume_mm3"],
          "wall_volume_mm3": summary["wall_volume_mm3"], "timber_count": len(timber_meshes),
          "timber_z_mm": [2500, 2533], "source_unchanged": True}), flush=True)
    if not verify_only:
        print("SPACE_MODEL_READY", flush=True)
        while process.poll() is None:
            time.sleep(0.5)
        raise RuntimeError("The modeling service stopped unexpectedly.")
except KeyboardInterrupt:
    print("Space modeling service stopped.", flush=True)
finally:
    if process is not None:
        # Kill only the new session created above, including its bridge child.
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=5)
    if log is not None:
        log.close()
'@

$spacePreviousEncoding = $OutputEncoding
try {
    $OutputEncoding = [System.Text.UTF8Encoding]::new($false)
    $spaceVerifyFlag = if ($VerifyOnly) { '1' } else { '0' }
    $spaceSupervisor | & wsl.exe -d $Distro --user root --exec tee "$spaceRuntime/supervisor.py" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw '無法寫入專用啟動程式。' }
    & wsl.exe -d $Distro --user root --exec python3 "$spaceRuntime/supervisor.py" $spaceLinuxRepo $spaceRuntime $Port $spaceVerifyFlag | ForEach-Object {
        if ($_ -eq 'SPACE_MODEL_READY') {
            $spaceUrl = "http://127.0.0.1:$Port/#engineering-spec-v1"
            Write-Host ''
            Write-Host '工程規格版已啟動，工程來源與空間、角材 3D 預覽驗證通過。'
            Write-Host "開啟：$spaceUrl"
            Write-Host '保持此視窗開啟；按 Ctrl+C 結束這個服務。'
            if (!$NoBrowser) { Start-Process $spaceUrl }
        } else {
            Write-Host $_
        }
    }
    $spaceExitCode = $LASTEXITCODE
} finally {
    # A PowerShell interruption must also stop the supervisor if WSL did not
    # receive the console signal. Verify its unique runtime argument first.
    $spaceCleanup = 'import os,sys,signal; from pathlib import Path; p=Path(sys.argv[1]); pid=int(p.read_text()) if p.exists() else 0; c=Path(sys.argv[2],str(pid),sys.argv[3]); owned=pid>0 and c.exists() and os.fsencode(sys.argv[4]) in c.read_bytes().split(bytes([0])); os.kill(pid,signal.SIGINT) if owned else None'
    & wsl.exe -d $Distro --user root --exec python3 -c $spaceCleanup "$spaceRuntime/supervisor.pid" /proc cmdline $spaceRuntime
    $OutputEncoding = $spacePreviousEncoding
}
if ($spaceExitCode -ne 0) { throw "第一版啟動或驗證失敗（代碼 $spaceExitCode）；未停止任何其他服務。" }
if ($VerifyOnly) { Write-Host '驗證完成，專用測試服務已停止。' }
