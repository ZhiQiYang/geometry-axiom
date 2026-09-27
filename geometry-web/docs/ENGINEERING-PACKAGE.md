# 正式工程做法包 engineering-package/1

採用依據：使用者核准的 `geometry-core/ENGINEERING-SPEC-PROPOSAL.md` 與
`geometry-core/ENGINEERING-SPEC-API.md`，2026-09-28。此包只攜帶材料／工程做法版本，
不含面套用、尺寸綁定、幾何、未發布草稿或 UI 狀態；完整工程用 `.gcanvas/5` 保存。
原型 `engineering-spec-ui-prototype/2` 不是此格式，不自動猜測遷移。

## 格式

根物件恰有 `schema`、`materials`、`methods` 三欄：

```json
{
  "schema": "engineering-package/1",
  "materials": [],
  "methods": []
}
```

兩個目錄是完整目錄，含未使用及已封存版本。每筆恰有
`{"value":{...},"fingerprint":"64 位小寫十六進位 SHA-256","archived":false}`。
`value` 是核心回傳的原始 immutable 內容，不從 UI 標籤或展開數字重建。
材料／做法內容欄位及型別依 API 文件。面材必有 id/version/kind/name/width/length；
thickness/brand/model/notes 可省略。角材用 A/B 取代 width/length，不接受 thickness。
做法必有 id/version/name；panel/roles/gap/longAxis/mainAlong/notes 可省略。
roles 若為物件，只可有 boundary/primary/secondary，可缺少槽位；材料引用恰有
id/version，或為 null。optional 欄位省略與明示 null 都可表示未設定；匯出不得替
原始 value 補 null 或預設值，因內容指紋包含原始欄位存在與否。

最多 64 份材料版本、32 份做法版本、UTF-8 1 MiB、JSON 深度 32。
未知或重複欄位、同目錄重複 id/version、錯誤 schema 會拒絕，不忽略未知資料。
以上是包格式檢查；C 仍負責版本內容、來源引用、尺寸、容量及指紋的最終驗證。

## 匯入與匯出

匯出包含目前核心目錄的原始 value/fingerprint/archived，JS 不計算另一套指紋。
匯入依序形成所有 publish-material、所有 publish-method，再各版本的 archive
操作；包含 archived=false，以還原包內明示的封存狀態。
整批進入同一個核心候選預覽並一次確認，任一失敗不改工程與歷史。
同 id/version 同內容可冪等匯入；異內容、錯誤指紋、缺少引用或整批超過容量均拒絕。
合併不刪除既有目錄、不同 id 不依同名合併、既有面套用不自動升級。

介面匯出僅能聲明下載已開始；完整工程的磁碟保存由宿主保存流程確認。
此文件定義格式，正式服務及瀏覽器驗收結果另見專案驗收報告。
