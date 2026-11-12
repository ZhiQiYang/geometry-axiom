# 相鄰有序face runs省工候選：測試綠，尚未解除H7

產品cff51164fe0293c8046aa66d86016cd0be333a08；只增加7行，兩個已排序run可穩定串接時memcpy，未改公共face順序、rank/group、fresh Fenwick/active或幾何結論。原53項W/contact/memo/capacity回歸exit0。172場景plain/trace共344新程序exit0，完整有序graph與固定B原件全等，不重跑B。

測試提交b05288e2be691dd5229937ab6c9a1f555b3f64e2只增加test_geo300_contact_face_runs.py與run_all登錄，產品與原53模組／graph裁判無變。新增8項exit0、0fail/error/skip；三個撤回各baseline0/mutant1/restored0，具名紅分別是有序run比較數、非排序輸入完整順序、相等鍵原ordinal穩定性。128/127比較數n−1是固定merge-tree結構，不是新增效能門檻；原最大比較上限完全保留。

一次新N256執行34.299473135秒exit0，原placed_geometry全過。沿固定8b現成baseline34.701295152秒與完整stdout/stderr，逐byte全等；未重抽baseline，這不是交錯正式效能樣本。只約1.2%差，不能據此稱H7原1200已可過。未再重跑未改source的20分鐘套件，也未採入正式產品。

固定原件含所有command/exit/source、build、測試原流、具名撤回、ELF、fixture與review。正式產品F2/C、8b H7原逾時、上游鏈及完整ledger/architecture/native/browser未完成狀態皆保留。下一步依已證約90% node-hint miss評估單一較大generic cache，不帶入沒有收益證據的hash tag，不放寬時限。
