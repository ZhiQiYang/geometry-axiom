# usage: wm_svc.ps1 start|stop  (port 8871, data dir in TEMP). Only own PID.
param([string]$Action)
$W="$env:USERPROFILE\AppData\Local\Temp\geobqa"; $D="$W\wm152"
if($Action -eq 'start'){
  $p=Start-Process python -ArgumentList "D:\geo-bqa-152\geometry-web\work-manager\cli.py","--data-dir",$D,"serve","--port","8871" -PassThru -WindowStyle Hidden -RedirectStandardOutput "$W\wm-8871.out" -RedirectStandardError "$W\wm-8871.err" -WorkingDirectory D:\geo-bqa-152
  Set-Content "$W\wm-8871.pid" $p.Id; Add-Content "$W\pids.log" "$($p.Id)|wm152|8871"; Start-Sleep 3; "pid=$($p.Id)"
} else {
  $id=[int](Get-Content "$W\wm-8871.pid"); Stop-Process -Id $id -Force -ErrorAction SilentlyContinue; "stopped $id"; Add-Content "$W\pids.log" "STOPPED $id"
}
