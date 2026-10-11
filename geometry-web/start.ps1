param(
    [ValidateRange(1024, 65535)][int]$Port = 8765,
    [ValidatePattern('^[A-Za-z0-9._-]+$')][string]$Distro = 'Ubuntu-24.04',
    # 區網測試模式（手機實機驗收；預設關閉）。開啟、改網路設定檔、裝根憑證都是使用者的安全決定，見 README「區網測試模式」。
    [ValidatePattern('^\d{1,3}(\.\d{1,3}){3}$')][string]$LanIp = '',
    [ValidateRange(1, 480)][int]$LanTtlMinutes = 120,
    [ValidateRange(1, 3)][int]$LanDevices = 1,
    [switch]$LanServeCa
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$portProbe = [System.Net.Sockets.TcpClient]::new()
try {
    $null = $portProbe.ConnectAsync('127.0.0.1', $Port).Wait(500)
    $portBusy = $portProbe.Connected
} catch { $portBusy = $false } finally { $portProbe.Dispose() }
if ($LanIp -and $Port -eq 8765) { throw '區網測試模式不得用日常埠 8765；請加 -Port 8766（或其他埠）。' }
# 區網模式下埠被占一律拒絕：否則會靜默沿用一個沒開區網的舊服務。
if ($LanIp -and $portBusy) { throw "連接埠 $Port 已有服務；區網測試模式需要新開一個服務，未啟動。" }
if ($portBusy) {
    & python (Join-Path $PSScriptRoot 'runtime_version.py') --probe $Port
    if ($LASTEXITCODE -ne 0) { throw "連接埠 $Port 上的服務無法證明是目前版本。請先保存專案，再重啟；未開啟舊服務。" }
    Write-Host "目前版本已在執行：http://localhost:$Port/"
    exit 0
}
$linuxRepoOutput = & wsl.exe -d $Distro --user root --exec wslpath -u $repo.Replace('\', '/')
if ($LASTEXITCODE -ne 0 -or !$linuxRepoOutput) { throw '無法取得 WSL 專案路徑。' }
$linuxRepo = $linuxRepoOutput.Trim()
$runtime = '/tmp/geometry-tests/axiom-runtime-' + [Guid]::NewGuid().ToString('N')
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
if ($LanIp) {
    # 手機回報不得混進 repository 的 feedback/：沒指定就用 TEMP 下的專用目錄。網路設定檔（Private）由 serve.py 自己查。
    if (-not $env:GEOMETRY_FEEDBACK_DIR) {
        $env:GEOMETRY_FEEDBACK_DIR = Join-Path ([System.IO.Path]::GetTempPath()) ('geometry-lan-feedback-' + [Guid]::NewGuid().ToString('N'))
        $null = New-Item -ItemType Directory -Path $env:GEOMETRY_FEEDBACK_DIR
    }
    Write-Host "區網測試模式的回報寫入 $env:GEOMETRY_FEEDBACK_DIR"
    $lanArgs = @('--lan', $LanIp, '--lan-ttl', $LanTtlMinutes, '--lan-devices', $LanDevices)
    if ($LanServeCa) { $lanArgs += '--lan-serve-ca' }
    & python (Join-Path $PSScriptRoot 'serve.py') $Port @lanArgs
    exit $LASTEXITCODE
}
Write-Host "請開啟 http://localhost:$Port/ （Ctrl+C 結束）"
& python (Join-Path $PSScriptRoot 'serve.py') $Port
exit $LASTEXITCODE
