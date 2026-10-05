# 用法: svc.ps1 start <exportDir> | svc.ps1 stop
# 只記錄/只停自己啟動的 serve.py PID 及其子程序(bridge/conhost);不按名稱殺。
param([string]$Action,[string]$Export)
$W="$env:USERPROFILE\AppData\Local\Temp\geo123c"; $Q="$env:USERPROFILE\AppData\Local\Temp\geometry-qa\bin"
if($Action -eq 'start'){
  Remove-Item "$W\fb\*" -Recurse -Force -ErrorAction SilentlyContinue
  $env:GEOMETRY_FEEDBACK_DIR="$W\fb"; $env:GEOMETRY_BRIDGE="$Q\bridge-c5955d469b13.exe"; $env:GEOMETRY_MODEL_BASE="$Q\model-base-079eda49f0df.exe"
  $env:TEMP="$W\tmp"; $env:TMP="$W\tmp"
  $p=Start-Process python -ArgumentList "$Export\geometry-web\serve.py","8861" -PassThru -WindowStyle Hidden -RedirectStandardOutput "$W\serve.out" -RedirectStandardError "$W\serve.err"
  Start-Sleep 6
  $kids=Get-CimInstance Win32_Process | ? {$_.ParentProcessId -eq $p.Id} | % { "$($_.Name):$($_.ProcessId)" }
  "$($p.Id)|$Export|$($kids -join ',')" | Add-Content "$W\pids.log"
  Set-Content "$W\serve.pid" $p.Id
  try{ (Invoke-RestMethod http://127.0.0.1:8861/runtime) | ConvertTo-Json -Compress }catch{ "runtime check failed: $($_.Exception.Message)" }
  "serve pid=$($p.Id) kids=$($kids -join ',')"
}
if($Action -eq 'stop'){
  $id=[int](Get-Content "$W\serve.pid")
  $kids=Get-CimInstance Win32_Process | ? {$_.ParentProcessId -eq $id}
  foreach($k in $kids){ Stop-Process -Id $k.ProcessId -Force -ErrorAction SilentlyContinue; "stopped child $($k.Name):$($k.ProcessId)" }
  Stop-Process -Id $id -Force -ErrorAction SilentlyContinue; "stopped serve $id"
  Add-Content "$W\pids.log" "STOPPED $id + $(($kids|%{$_.ProcessId}) -join ',')"
}
