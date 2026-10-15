param(
    [ValidateRange(1024, 65535)][int]$Port = 8765,
    [ValidatePattern('^[A-Za-z0-9._-]+$')][string]$Distro = 'Ubuntu-24.04'
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
# 在同一個 PowerShell 視窗重跑時，上一次啟動設定的 GEOMETRY_MODEL_BASE 仍在，
# 會被當成「使用者已指定」而跳過編譯、沿用可能已失效的舊執行檔。
# 只清本腳本自己設定過的值（符合本腳本的 runtime 路徑格式）；使用者明示的覆寫保留。
$launcherModelBase = '^(/var/tmp/geometry-runtime|/tmp/geometry-tests)/axiom-runtime-[0-9a-f]{32}/model-base$'
if ("$env:GEOMETRY_MODEL_BASE" -match $launcherModelBase) {
    Remove-Item Env:GEOMETRY_MODEL_BASE -ErrorAction SilentlyContinue
    Remove-Item Env:GEOMETRY_MODEL_BASE_WSL_DISTRO -ErrorAction SilentlyContinue
}
$portProbe = [System.Net.Sockets.TcpClient]::new()
try {
    $null = $portProbe.ConnectAsync('127.0.0.1', $Port).Wait(500)
    $portBusy = $portProbe.Connected
} catch { $portBusy = $false } finally { $portProbe.Dispose() }
if ($portBusy) {
    & python (Join-Path $PSScriptRoot 'runtime_version.py') --probe $Port
    if ($LASTEXITCODE -ne 0) { throw "連接埠 $Port 上的服務無法證明是目前版本。請先保存專案，再重啟；未開啟舊服務。" }
    Write-Host "目前版本已在執行：http://localhost:$Port/"
    exit 0
}
$linuxRepoOutput = & wsl.exe -d $Distro --user root --exec wslpath -u $repo.Replace('\', '/')
if ($LASTEXITCODE -ne 0 -or !$linuxRepoOutput) { throw '無法取得 WSL 專案路徑。' }
$linuxRepo = $linuxRepoOutput.Trim()
# 執行檔放在 /var/tmp，不放 /tmp：WSL 開了 systemd，閒置自動關閉後重開時，
# tmpfiles 的「D /tmp」會清空 /tmp，剛編譯的 web_bridge／model-base 會在下一次
# wsl.exe 呼叫前消失（橋接器已結束、空間建模元件無法執行）。/var/tmp 開機時不清空。
$runtimeRoot = '/var/tmp/geometry-runtime'
$runtime = "$runtimeRoot/axiom-runtime-" + [Guid]::NewGuid().ToString('N')
& wsl.exe -d $Distro --user root --exec mkdir -p $runtimeRoot
if ($LASTEXITCODE -ne 0) { throw '無法建立執行檔目錄。' }
# 只清本腳本自己留下、超過 7 天的舊執行檔目錄。
& wsl.exe -d $Distro --user root --exec find $runtimeRoot -mindepth 1 -maxdepth 1 -type d -name 'axiom-runtime-*' -mtime +7 -exec rm -rf '{}' +
& wsl.exe -d $Distro --user root --exec mkdir -p $runtime
if ($LASTEXITCODE -ne 0) { throw '無法建立執行檔目錄。' }
Write-Host '正在編譯目前的幾何核心…'
& wsl.exe -d $Distro --user root --exec gcc -std=c11 -O1 "$linuxRepo/geometry-web/web_bridge.c" -lm -o "$runtime/web_bridge"
if ($LASTEXITCODE -ne 0) { throw '編譯失敗，服務未啟動。' }
$baseTransport = & python -c 'import sys; sys.path.insert(0, sys.argv[1]); from modeling.base import startup_base_transport; print(startup_base_transport())' (Join-Path $repo 'geometry-core')
if ($LASTEXITCODE -ne 0 -or !$baseTransport) { throw '無法確認空間建模元件的啟動設定。' }
if ($baseTransport.Trim() -eq 'wsl') {
    Write-Host '正在編譯空間建模元件…'
    & wsl.exe -d $Distro --user root --exec gcc -std=c11 -O1 "$linuxRepo/geometry-core/model_base.c" -lm -o "$runtime/model-base"
    if ($LASTEXITCODE -ne 0) { throw '空間建模元件編譯失敗，服務未啟動。' }
    $env:GEOMETRY_MODEL_BASE = "$runtime/model-base"
    $env:GEOMETRY_MODEL_BASE_WSL_DISTRO = $Distro
}
$env:GEOMETRY_BRIDGE = "wsl.exe -d $Distro --user root -- $runtime/web_bridge"
$env:GEOMETRY_BRIDGE_WSL = '1'
& python -c 'import sys; sys.path.insert(0, sys.argv[1]); from modeling.base import load_base; load_base(str())' (Join-Path $repo 'geometry-core')
if ($LASTEXITCODE -ne 0) { throw '空間建模元件無法執行，服務未啟動。' }
Write-Host "請開啟 http://localhost:$Port/ （Ctrl+C 結束）"
& python (Join-Path $PSScriptRoot 'serve.py') $Port
exit $LASTEXITCODE
