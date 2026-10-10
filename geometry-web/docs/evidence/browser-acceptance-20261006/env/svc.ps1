# usage: svc.ps1 start <worktree> <port> | svc.ps1 stop <port>
# Only starts/stops own recorded PID (+ its direct children). Never kills by name.
param([string]$Action,[string]$Arg1,[int]$Port)
$W="$env:USERPROFILE\AppData\Local\Temp\geobqa"; $Q="$env:USERPROFILE\AppData\Local\Temp\geometry-qa\bin"
New-Item -ItemType Directory -Force "$W\tmp-$Port","$W\fb-$Port" | Out-Null
if($Action -eq 'start'){
  Remove-Item "$W\fb-$Port\*" -Recurse -Force -ErrorAction SilentlyContinue
  $env:GEOMETRY_FEEDBACK_DIR="$W\fb-$Port"; $env:GEOMETRY_BRIDGE="$Q\bridge-c5955d469b13.exe"; $env:GEOMETRY_MODEL_BASE="$Q\model-base-079eda49f0df.exe"
  $env:TEMP="$W\tmp-$Port"; $env:TMP="$W\tmp-$Port"
  $p=Start-Process python -ArgumentList "$Arg1\geometry-web\serve.py","$Port" -PassThru -WindowStyle Hidden -RedirectStandardOutput "$W\serve-$Port.out" -RedirectStandardError "$W\serve-$Port.err"
  Start-Sleep 6
  $kids=Get-CimInstance Win32_Process | ? {$_.ParentProcessId -eq $p.Id} | % { "$($_.Name):$($_.ProcessId)" }
  "$($p.Id)|$Arg1|$Port|$($kids -join ',')" | Add-Content "$W\pids.log"
  Set-Content "$W\serve-$Port.pid" $p.Id
  "serve pid=$($p.Id) kids=$($kids -join ',')"
}
if($Action -eq 'stop'){
  $id=[int](Get-Content "$W\serve-$Port.pid")
  $kids=Get-CimInstance Win32_Process | ? {$_.ParentProcessId -eq $id}
  foreach($k in $kids){ Stop-Process -Id $k.ProcessId -Force -ErrorAction SilentlyContinue; "stopped child $($k.Name):$($k.ProcessId)" }
  Stop-Process -Id $id -Force -ErrorAction SilentlyContinue; "stopped serve $id"
  Add-Content "$W\pids.log" "STOPPED $id + $(($kids|%{$_.ProcessId}) -join ',')"
}
