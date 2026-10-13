# 52c34a6 原 archive 的 ASCII 傳輸

本目錄只補可讀傳輸與純檔案核驗。沒有重跑診斷、執行封存 binary，或改動原 archive／summary／manifest／verification；不計為新測試。

- 原來源 commit：`52c34a6d6faef1d3cdaf52d52b6f8edb66eda012`
- 原檔：`tests/evidence/ui209-recovery-20261013/raw.tar.xz`
- 原 Git blob：`00a97cc9649ea82f03291f29113506ccabd8ee7c`
- 原長度：**2865276 bytes**
- 原 SHA-256：`89a7ea908a7fb3d0957d1103d45f00b11c5de55d2a305b589b5a5bfcf7d6f5ba`
- 原外層 manifest：53321 bytes，SHA-256 `317572989637967e5b0ba7974b1dc5d396976ace00886dcef4f919846158ccb8`，328 個成員。

[index.json](index.json) 明列 80 段的順序、檔名、base64 起迄（0-based，end exclusive）、文字檔長度／SHA-256、解碼片段長度／SHA-256。base64 共 3820368 字元；前79段各48000字元，末段28368字元。各 `.b64.txt` 只有一行 base64 加一個 LF；`file_sha256` 包含 LF，base64 offsets 不含 LF。

GitHub connector 可用 `fetch_file`、`encoding="utf-8"` 讀本目錄的 index、[reconstruct.py](reconstruct.py) 及 index 所列文字檔，ref 指向包含此目錄的精確 transport commit。每檔最多48001 bytes，無須讀二進位或依賴 public raw URL。不要再對原2.86MB archive 呼叫 `fetch_file(base64)`。只需取本目錄一次，無需另找 PR base64 留言。

保留原目錄結構；另取[原 manifest](https://github.com/ZhiQiYang/geometry-axiom/blob/52c34a6d6faef1d3cdaf52d52b6f8edb66eda012/tests/evidence/ui209-recovery-20261013/manifest.json)為 `transport/../manifest.json`。單一命令重建及核驗：

```sh
python3 tests/evidence/ui209-recovery-20261013/transport/reconstruct.py /tmp/ui209-52c34a6.raw.tar.xz
```

輸出檔必須尚不存在。工具依序驗 ASCII checksum／片段 checksum／原 archive checksum，再讀 tar 內所有成員，拒絕重複、遺漏、多出或非 regular-file 成員，逐一比對原 manifest 的 length/hash；`binaries/` 成員再與其檔名的宣告 SHA 比較。它只讀 bytes，不解壓、載入或執行 payload。成功輸出會列 `parts_verified:80`、`members_verified:328`、一份封存 binary 的實際 hash、`payloads_executed:false`。

這項檢查與 `ui209_summarize.py` 不同：summarize 由日誌重算摘要、比對收據中的來源／binary hash 宣告、驗歷史 ZIP payload；它不核外層328成員及封存 binary bytes。原 [verification.json](../verification.json) 是前次額外檔案核驗的收據，本次提供可獨立重做的純檔案入口。

另依原 raw 更正報告對 P88 兩輪的混用：固定1280×900的 `p88-wheel-02` 在受控重建前可點、之後新節點在視窗外；舊 `.ig-settings` scrollTop805、新 `.ig-settings` scrollTop0。這不改動52c34a6的任何數據，也不將受控重建當成歷史WSL根因。精確 node、rect、hit 數值見[更正後報告](../README.md)。
