# 本次量測的服務啟動方式（記錄用範本；路徑需依環境調整）
# 原則：獨立 port、獨立 TEMP/feedback、獨立匯出目錄，不共用也不停止他人服務。

$Export = "$env:TEMP\geo123\main-d6b4b45"          # git archive 匯出 d6b4b450 的目錄
$Work   = "$env:TEMP\geo123"                        # 獨立工作目錄
$env:GEOMETRY_FEEDBACK_DIR = "$Work\fb"
$env:GEOMETRY_BRIDGE    = "<預先驗證的 bridge.exe 路徑>"     # 本次沿用內容雜湊 c5955d469b13
$env:GEOMETRY_MODEL_BASE = "<預先驗證的 model-base.exe 路徑>" # 本次沿用內容雜湊 079eda49f0df
$env:TEMP = "$Work\tmp"; $env:TMP = "$Work\tmp"

$p = Start-Process -FilePath "python.exe" `
     -ArgumentList "$Export\geometry-web\serve.py","8851" `
     -PassThru -WindowStyle Hidden `
     -RedirectStandardOutput "$Work\serve.out" -RedirectStandardError "$Work\serve.err"
if (-not $p.HasExited) { $p.PriorityClass = 'BelowNormal' }
# 驗證：Invoke-RestMethod http://127.0.0.1:8851/runtime 應回 fresh:true、version=e2f2ee7baaf7…
