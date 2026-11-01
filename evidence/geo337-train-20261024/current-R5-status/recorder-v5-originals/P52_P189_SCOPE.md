# P52／P-189 的限定影響檢查（只讀，未重跑）

本輪發現的是#323 v4 `geo323_record.py` 的FILE目的地及`recorded_run`落盤被原sample timer包住；不能把所有有父程序錄製器的測時都歸為同一缺陷。

P-189正式工具 `/tmp/train337-final-p52-p189-prep/p189/scale_compare2.py` 的`one_load`原本就用stdin/stdout/stderr三PIPE。它在原Popen之後記t0，`communicate(timeout=a.timeout)`後立刻計dt，**再**呼叫`record_loadfile_sample`落盤/hash。因此沒有發現#323這兩個直接偏差。父層`p189_verify.run`與run_special外層的錄製時間不是36筆sample的dt來源。原full因exact assertion1沒有進timing；獨立timing tail沿同一scale腳本，不解除full紅。不能將P189的啟動時間範圍改成#323的範圍或更換其原門檻。

P52的正式結果來自原Node `p52_probe.cjs`：click前`process.hrtime.bigint()`至`appearedMs`，另有browser `performance.now()`診斷。父層Python recorder等待整個Node退出的wall並非各sample的appear時間。原probe在計`appearedMs`後才log該sample。P52父程序原本shared.command也以普通log檔等待；沒有把#323的PIPE呼叫改成FILE的同一替換套在P52 sample內。原P52還有自身的25ms查詢間隔與CDP流程，這是其原測量方法，本草稿不改它。

結論僅是：靜讀這些固定原碼，未發現P52/P189沿用#323同一個sample timer／錄製器偏差。這不宣稱所有觀察或排程影響為零，也不免除後續產品來源改動所需的正式重跑。未修改任何P52/P189工具、樣本、閾值或結果；原P520、P189full1/timing0及overallfalse照保。

本次讀取的完整小來源及SHA在`scope-originals/`與`SCOPE_PINS.json`；沒有讀取大型原raw archive或重抽樣。
