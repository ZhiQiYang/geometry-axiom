param(
    [ValidateRange(1024, 65535)][int]$Port = 8765,
    [ValidatePattern('^[A-Za-z0-9._-]+$')][string]$Distro = 'Ubuntu-24.04'
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$linuxRepoOutput = & wsl.exe -d $Distro --user root --exec wslpath -u $repo.Replace('\', '/')
if ($LASTEXITCODE -ne 0 -or !$linuxRepoOutput) { throw '無法取得 WSL 專案路徑。' }
$linuxRepo = $linuxRepoOutput.Trim()
$runtime = '/opt/geometry/axiom-runtime'
& wsl.exe -d $Distro --user root --exec mkdir -p $runtime
if ($LASTEXITCODE -ne 0) { throw '無法建立執行檔目錄。' }
Write-Host '正在編譯目前的幾何核心…'
& wsl.exe -d $Distro --user root --exec gcc -std=c11 -O1 "$linuxRepo/geometry-web/web_bridge.c" -lm -o "$runtime/web_bridge"
if ($LASTEXITCODE -ne 0) { throw '編譯失敗，服務未啟動。' }
$env:GEOMETRY_BRIDGE = "wsl.exe -d $Distro --user root -- $runtime/web_bridge"
$env:GEOMETRY_BRIDGE_WSL = '1'
Write-Host "請開啟 http://localhost:$Port/ （Ctrl+C 結束）"
& python (Join-Path $PSScriptRoot 'serve.py') $Port
exit $LASTEXITCODE
