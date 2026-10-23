連線成功恢復後，`connection.error` 仍留著先前 upload/confirm 的失敗字串，會污染 ready 狀態診斷及下一次 loading 的修改拒絕訊息。這份修正只在完整恢復成功、轉為 ready 時清除舊錯誤；恢復失敗仍保留新錯誤與編輯停用。

本 draft 疊在 `codex/train-337-continue-20261024`，不改 #339／其他 owner 分支、公理、決策、保存格式、時限或 golden。P53／P61 的三條既有 browser 斷言保留原幾何／來源／只讀守門並加驗 error 為空，未增減 check 呼叫或調整 golden 計數。新增獨立 pure-Node suite `node:connection_recovery` 9 方法；只新增對應 expected=9，其餘 entries 不變。

唯一 current-state 矩陣：

| 項目 | 來源／原退出碼 | 結果及範圍 |
|---|---|---|
| 產品 SHA | c1113f6fd6c52a55d7df1a30ecd1684fe87b661c | base 2d1570691e4a29aafebdc0a4e739787d3fcdddaa；恰五檔，普通 push／ls-remote 同 |
| Evidence head | d2c583179219dafe2f575ef158c45f3cf17bd186 | evidence/issue320-final-c1113f6f/；只封原件與狀態，不重標為新產品實跑 |
| 單元 baseline | 原 clean 產品 SHA；Node exit 0 | 9 pass／0 fail／0 skip |
| 精確撤回唯一產品 clear | 同 SHA 的具名 working-tree variant；Node exit 1 | 6 pass／3 正常具名 ERR_ASSERTION／0 skip；測試不改 |
| 還原 | 原 clean 產品 SHA；Node exit 0 | 9 pass／0 fail／0 skip，app bytes／HEAD／五檔 stage listing 還原 |
| 獨立 source／actual peer | 281 checks／exit 0／findings=[] | 核五 Git blobs、17 原命令與 streams、正常 0/1/0、P53/P61 與 expected 增量；只到 unit 範圍 |
| 真 P53／P61 UI 與完整 canvas | UNRUN | 等 root 獨占時槽；原正式入口／golden／時限均保留，本次 VM 不能替代 |
| 其餘五 browser job | UNRUN | 最終列車依實際影響與正式清單排程，不沿用舊 SHA 冒本件已跑 |
| 完整 native | UNRUN | 9 unit 不是全 native；正式 registry 已登記新 suite |
| mutate.py --check／完整帳本 | UNRUN | root 唯一統籌最終來源判定及必要整份重產；本 owner 未產全帳本 |
| 架構三原裁判／四檔收據 | UNRUN | app.js 為 H 層來源，交 root 按新來源閉包檢查／Linux 重產，不冒舊收據已更新 |
| 允許 skip | 已跑 9 unit 每 phase 0 | 沒有額外 skip；setup、crash、timeout 或語法錯不計反證偵測 |

真原命令為 `node --test --test-reporter=spec tests/test_connection_recovery.js`，baseline／撤回／恢復均在原 300 秒子時限內完整跑九案。測試直接擷取並執行 app.js 的原 `connectionFailed`、`recoverConnection`、`apiRequest` 函式；DOM、傳輸與 ReferenceWorkspace 合作者是明示替身，沒有真瀏覽器、HTTP 或原生核心。本輪也未把原 owner guard 替身宣稱為真 owner 整合驗收。

反證分別指出成功恢復殘留、併發重試完成殘留、下一次 loading 回聲已恢復舊錯誤；另保留初次握手及 recoverLoad／握手／物件讀取／surface／restore 失敗控制，證明仍失敗時不會清錯並放行。撤回只移除唯一 `connection.error = ""`，原測試 bytes 全保，失敗為三個正常斷言而非 timeout 或工具錯誤。

完整原件包 `raw/originals-and-peer-c1113f6f.tar.gz` SHA-256 `7406d5cd2b6e94b9ab2889130b5f1392c36049700aac8fd5a3e3d856ca4d0f5b`，逐成員 bytes／hash 與原檔還原核對。原17筆 proof 命令、各自退出碼／stdout／stderr／環境／來源、五 Git inputs、withdrawn app 與還原證據、source publication、工具與獨立 peer 全保。MANIFEST 明確排除自身，沒有 self-index 迴圈。

原 setup 失敗亦保留：首 sparse payload 使用 literal backslash-n 未物化、feedback CLI 缺少薄工作樹 import、首次 git add 拒絕 sparse 外新 leaf；限定補正後完成，沒有將它們冒作產品紅或挑掉。peer 首版自身 P61 替換比對過廣的 false finding 亦保原，修 checker 後 281／0，沒有重測 subject。

最外 proof driver 的 process 0 由原 host exec 返回；未另捕捉 top-wrapper stdout/stderr，不補造事前外層收據。三條 Node 原 CLI 的完整 streams 與退出碼均有獨立 c387 原件。最大未定是正式瀏覽器／真傳輸／原生恢復路徑；本 draft 不標 READY、不自行合併。
