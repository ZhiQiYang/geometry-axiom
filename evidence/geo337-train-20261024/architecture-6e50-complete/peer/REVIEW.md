架構與合流原件對抗審查通過。實際來源 `6e50aef65513b7b38f93228919272c6d40d6c196`；三條原裁判 exit 0/0/0，205 與18測試零skip；604來源逐Git/raw/LF核對，唯一變動references.inc。九組原guard重新0/1/0，兩neutral通過。51條原架構命令、2條outer與16條merge命令之原始流、環境、SHA及exit逐筆核對。manifest/scan不變，只有report/receipt衍生檔變更。

合流腳本對child remote tip未加assert，但保留stdout本次確為S2c463；此靜態缺口已揭露，沒有改寫原件或重跑合流。實際架構執行M不可改標後續採用SHA；不宣稱runtime/performance/ledger完成。
