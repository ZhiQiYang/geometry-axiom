成功恢復連線時清除 `connection.error` 的過時錯誤，保留所有恢復失敗、編輯停用及協定守門。這是 #320 的唯一替代實作線 #344；不更改公理、決策、保存格式、golden 或時限。

本次新來源 S=`7b45013da647b791acda8f5977475e4123d5f8c4` 只在既有 P53／P61 三個完整 CDP checks 補強非空錯誤 seed 與故障／恢復診斷；三個 check 的名稱、呼叫數和所有原幾何／來源 predicates 均保留。相對舊證據 Ed2c 只改 `geometry-web/cdp_test.js`，app、九案 unit、registry、expected 與 golden 的原 bytes 全同。新來源已一般 push 且 remote 同 SHA。

唯一 current-state 矩陣：

| 項目 | 來源／原退出碼 | 結果及範圍 |
|---|---|---|
| 產品／本次受測 SHA | S=`7b45013da647b791acda8f5977475e4123d5f8c4` | parent Ed2c；本輪只增加三個既有 CDP checks 的 seed／診斷，未換協定或 golden |
| Evidence head | E=`42790be40eee56efada08de84ab2acb1681df981` | `evidence/issue320-final-7b45013d/`；純證據，不冒 E 重新實跑 |
| 原九案 baseline | S；Node exit 0 | 9 tests／9 pass／0 fail／0 skip |
| 撤回唯一 ready error clear | 同 S 明示 working-tree app variant；Node exit 1 | 9 tests／6 pass／3 正常具名 ERR_ASSERTION／0 skip；不改測試 |
| 原 app 還原 | S；Node exit 0 | 9 tests／9 pass／0 fail／0 skip；app bytes／HEAD／選定 stage listing／clean 全還原 |
| 新 S 獨立 source／actual peer | 365 checks／process 0／findings=[] | 17 inner＋14 source publication＋1 outer 原 streams、五 Git inputs、正常 0/1/0；只到 VM 定向範圍 |
| 真 CDP 提案靜審 | 49 checks／0 | 三 checks 以外 bytes 同、原四 predicates／兩真 fetch 順序／1600／dump／source 全保；靜審不算 browser pass 或 kill |
| 受控撤回來源／三phase準備 | V=`082feb0662fea32131f3f7fb8ca451679ab6421d`；靜審226／0 | V單親S且僅clearline差異，三phase clean S／V／S；不是CDP實跑或正式驗收通過 |
| 真 P53／P61 與完整 canvas | **UNRUN** | 原 default 整 canvas／35min／完整 golden／獨占；不得以 VM 取代 |
| 其餘五 browser job | **UNRUN** | 不沿用 root L 或舊 source 結果冒本件同源綠 |
| 完整 native | **UNRUN** | 新 Node suite 的九案不代完整 registry／native |
| mutation check／完整帳本 | **UNRUN** | root 統籌最終閉包與必要全量重產，本 owner 未產帳本 |
| 架構三原裁判／四檔 | **UNRUN** | app 為 H 層來源，待本件最終來源的原三裁判與 schema 影響判定 |
| 舊來源歷史 | Sc111；原 Node 0/1/0、actual peer281/0 | 原 E=`d2c583179219dafe2f575ef158c45f3cf17bd186` 的原件保持不動；不把舊執行轉標新 S |
| 允許 skip | 已跑九案三階段均 0 | 無新增；setup／crash／timeout 不能代正常反證 |

原命令 `node --test --test-reporter=spec tests/test_connection_recovery.js`，每階段仍原 300 秒子時限。三個撤回斷言原文為 `successful recovery kept stale error`、`completed retry kept stale error`、`loading echoed stale error`。測試執行 app.js 精確原函式 spans，但 DOM、transport 與 ReferenceWorkspace 是明示替身；這不是實際瀏覽器、HTTP 或原生恢復驗收，也不代表真 owner guard 的 loading 入口已驗。

新 S 的真 proof 有事前 outer REQUEST、原 driver 的獨立 c387 stdout/stderr／exit、17 inner commands 及五 inputs；舊 Sc111 的最外 host-only 觀察限制仍只屬原歷史，沒有補造。最初新 launcher 缺 output mkdir，在 request／subject 啟動前 FileNotFoundError；原 helper 與分類保留，只補 mkdir 後才首次執行 Node。peer 首版把 request 的 null 結束碼 placeholder 與 final exit 比較造成32個假 finding，原 checker／report 保留；r2修 schema 後365／0，未重測 subject。peer 的 `originalVMTestCounts=[9,6,9]` 欄實際是 pass counts，總 tests 每階段均9，細項五欄已核；不把它誤稱 tests 總數。

完整包 `raw/cdp-proposal-and-original-nine-vm-7b45013d.tar.gz` 為331成員、2,319,362 bytes，SHA-256 `9985cb1dbaba3220c5f83af506ec41f89acdba0913384678930ad0b41a9d59f6`；逐成員 bytes/hash 對原檔 roundtrip。包含新 CDP 準備、source push／ls-remote、VM／outer完整原流、初始環境錯誤、兩份獨立 peer 與工具。MANIFEST 排自身；舊 Sc111 歷史原包仍在舊 prefix。

三次原 full canvas 的獨立 port／TMP／profile、完整35min與 golden 已機械綁定，並獨立靜審226／0；真正完整source／fixtures／runtime與磁碟尚未物化，全部CDP仍UNRUN，下一步等root獨占時槽與原preparer完成來源準備。P53 真403／reload／Retry，P61 未送達及已送達回應遺失的兩原注入、dump／source／PDF／1600／scene assertions 全保。fixed／restored 須原完整 matched；mutant 須命中三個具名 stale-error 正常斷言並保其餘協定診斷，預期 golden mismatch不能冒新產品缺陷，也不能以 crash／driver clean-check失敗代 kill。原正式 driver 要求 clean SHA，沒有修改該validator；撤回專用公開V以S為唯一parent，只有app clearline差異，全部其餘Git blobs／modes相同。三phase真execution SHA分別S／V／S，V不能冒S或產品驗收SHA；dirty前置被擋也不能冒真CDP反證。HTTP19681/2/3、CDP9731/2/3與獨立scratch/profile全列原binding。

真 CDP、完整 native／browser、帳本／架構仍未完成；本 draft 不標 READY，不 force push，不合併 PR，不改其他 owner 分支。

本輪準備／公開V原18命令／原patch／三driver完整diff／226靜審／前次1585公開核對與計數釐清note，見 `evidence/issue344-real-cdp-preparation-7b45013d/`；小包逐成員bytes/hash roundtrip。這批沒有新增Node、Chrome、C、HTTP或產品測試執行。
