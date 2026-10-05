# 修前重現

原 main 缺口的 source key/highwater/impact/UI 與 raw /2 store red 原日誌保留。
`issue61-orphan-original.json`：0844b58 正式 UI 建來源/規則、保存 edit/delete raw、返回、卡片刪除來源（如有 native impact 則確認）、emptyNewGridSystem 恢復。兩案均 undefined.id、returnBound=false、projectHeader=false，raw/World 尚未被改。
`issue61-reader-original.json`：0844b58 使用真 ZIP/file chooser/native prepare，僅竄改 detached 回覆。缺 canonical、能力不符、snapshot 不完整、pin 非法四案均錯誤 confirm=1/cancel=0/snapshot=0。
這些是修前失敗證據；不將 0844 的 full 結果當修後通過。最後驗收只看本目錄 testedProductHead 的 receipts/logs。
