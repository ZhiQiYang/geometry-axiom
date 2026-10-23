# P88 階段完成與接手狀態

正式 F `3d681636902371ecc528b20f51eea33e272581c9` 的完整 canvas 連續三次為 0／0／0，原生 rAF 有效撤回／恢復反證為 0／1／0；主代理的其餘受影響項目已完成。最新 handoff `b7e23a2579c5bdcf057d3ad6d04b064ac098a5c6` 的 head a05a21a 複審結論是「改完 1 項可合併」；唯一剩餘動作為套用 live PR 正文並回讀核對，因此仍 `READY-TO-MERGE=false`。驗收 E=`5a76d815c843d7ffb06bd1be769d4c5255c72b66`，待套用主正文 D=`e008dc52510d8cdb34fe07c796835f2667e0ebaa`／SHA256 `77fad4a11a92827d4b5d2b95423215c98dc13ecccce5c33e8c70e156c688e1f8`。

本階段依最新使用者指示收尾後停止，交由接手者完成 live 動作；不再開新監看或測試。原 API GET exit 1／Forbidden 完整保留，沒有更新嘗試。官方網路草稿已保存 api.github.com、仍 requires_publish=true，未套用且不能宣稱 API 恢復。公開 NEXT 為 a3018515644451367ef94f667082c9bd4881538f；原始審查、交接與獨立 peer 見 review-refresh-20261023T145327Z。

以下為依時間保留的歷史紀錄；舊待跑／未讀新複審描述不代表目前狀態。

| 項目 | 受驗來源 | 結果 |
| --- | --- | --- |
| 原完整 canvas 1 | `13d02c1db7022145a52ee063286a558e595eb212` | exit 1；P88=99；原 exact-focus predicate 逾時；1071.906 s |
| 原完整 canvas 2 | 同上 | exit 0；2267/0；P88=143、P73=69；golden matched；1754.826 s |
| 原完整 canvas 3 | 同上 | exit 0；2267/0；P88=143、P73=69；golden matched；1739.477 s |
| 診斷 fixed／withdrawn／restored | F13 + 明列記憶體 source variants | 原測試 exit 1／1／1；driver exit 2；proof=false；工具位移預條件未成立 |
| source 語法／diff 檢查 | 候選 P88 bytes `8106476b6eb2271111caa835a863b72eced4bab3b2ef77244f28534d83ca0a52` | `node --check geometry-web/grid_rule_lines_test.js` exit 0；`git diff --check` exit 0 |
| source 普通推送／remote 核對 | `8bce9239c014f070740455556c8ee1176c500af3` | exit 0／0 |
| 新 F 正式驗收 | `3d681636902371ecc528b20f51eea33e272581c9` | 三次完整 canvas 已啟動，結果待跑完；不得將候選診斷或原 F13 綠燈冒充此項 |

原失敗 assertion：

```text
UI condition timed out at === P88. 原生來源子線顯示、完整引用、兩面及正式重開 ===: document.activeElement===document.querySelector("#refGuideMode")
```

原失敗後 active element 為 `refGuideRatio`。原三輪沒有 pointerdown 目標追蹤，因此不能直接宣稱當次一定是滑鼠先點錯，而非點後重排／焦點轉移。三次結果完整保留，皆在原 35 分鐘內。第一輪 launcher 未將 `NODE_OPTIONS` 列入環境白名單；未設定 preload，但不能用事後 shell 狀態證明原 process 的環境。第二、三輪明確 `env -u NODE_OPTIONS -u PYTHONOPTIMIZE`。

候選只改 P88 的定位準備，使用原 helper 的 probe hook 等待版面與確認 hit target；沒有改產品、其他測試模組、原 check 行、golden、12 次嘗試上限或 CI 時限。準備與 exact-focus check 共用原 25 秒，新增的矩形觀測並非新增嘗試次數；沒有 DOM focus／click 或寫值。主代理已合入 immutable source commit，帳本與架構影響由主代理依規則統一處理。

真查詢診斷的守門沒有成立：查詢回傳後確實觀察到 `paintQuery`／`renderFaceInspector` 換節點、scroll `25 → 0 → 25`，但釋放後兩 frame 的舊點仍命中 `refGuideMode`，沒有後續目標 mouseDown。工具自己拋錯，不能稱為「拿掉修正，原斷言轉紅」；fixed／restored 也尚未走到該位置的穩定 probe。未再改該工具、人工移位或重抽湊 0／1／0。原自然紅的精確觸發仍未證。

原三輪完整 stdout／stderr／commands／environment／SHA 已由主代理推至整合分支 `evidence/geo261-final-13d02c1d/`。本子分支另附三階段診斷的完整原命令、收據、streams、trace、來源變體與工具快照之壓縮封存，`MANIFEST.json` 列每檔 bytes／SHA256，`ROUNDTRIP.json` 證實解壓後逐檔一致；僅排除 phase/tmp 的編譯執行檔、Chrome profile/cache 與 runtime scratch，沒有刪原機器檔案。

獨立對抗審查已核 source `8bce9239` 與候選 v5 全等，未見放寬斷言、golden、嘗試上限或時限；三個真查詢診斷階段未證成因果的限制也各有審查。主代理已在 F 上跑原帳本檢查及架構三條，全部 exit 0。三輪 canvas 使用已審 `98025b20…` 錄製器，獨立埠、暫存目錄與 profile，所有結果保留；不重跑未受影響項目。

摘要欄名更正：v1 摘錄使用不存在的 `response_json_unchanged` 而輸出 null；原三個 trace 的正確欄名為 `parsed_json_unchanged`，其值均 true。`ACTUAL_QUERY_OBSERVATIONS_v2.json` 使用正確欄名；v1 與原壓縮包保留，沒有改原 trace 或測試判定。此處只核對 parsed JSON，沒有宣稱 HTTP wire bytes 完全相同。

最新同步的 head `1999cbc` 審查仍要求撤回／恢復反證。依剛觀察到的 renderer return 與原 rAF 恢復之間短窗，另準備一組不同的明列交錯：在真正 native dispatch 的原 scroll-restore callback 入口前，單次求值原 measure expression，立即讓原 callback 依原 this／args／guard 執行，完成後才把原 p 回給 CDP。不捏造幾何或捲動、不另排／手動執行 callback，fixed／withdrawn／restored 同一排程，withdrawn 僅原 P88 bytes。此工具尚未執行；準備 v2 manifest `a6f6dc0e5f02b1090b01216de008be2864a48aa26f5ee09d48f086196b7e127b` 與獨立 peer 靜審附在 `native-raf-preparation-v2/`。須等正式三輪收齊及主代理重活排程。不能拿準備接受或前一組失敗作成功反證。

- 11:40 UTC：新 F 完整 canvas 第 1 輪 exit 0；1741.884308179011 秒，原 35 分鐘內，full 2267／0、golden matched、P88=143、P73=69、沒有 skip。第 2 輪自動接續。原 receipt SHA256：594f637f2386d09702c9021d6828bc2ee4e032097713429cea5c5bbfa32b548f。
- 原生 rAF 接續等待器已通過獨立靜審並啟動等待（session 91028）；等待正式三輪 process 終態與 source_after，之後只跑一次固定／撤回／恢復，不重抽；尚未開始反證。完整 argv／環境／雜湊與前版 metadata 修正在 native-raf-waiter-preparation/。

- 12:38:51 UTC：公開 F `3d681636902371ecc528b20f51eea33e272581c9` 的三次完整 canvas 全部完成，exit 0／0／0；每輪 full 2267／0、P88=143、P73=69、golden matched、skip=[]；1741.884308179011／1748.520241596998／1765.1202577359945 秒，全部在原 35 分鐘內。sequence driver exit 0，來源前後同 SHA、空 status、同 index。完整 step 指令／stdout／stderr、收據與 outer 已收在 final-canvas-three/；root 另封存 workflow optional artifacts。
- 12:38:58 UTC：原等待器自動啟動固定 F 的 native-rAF 三階段反證，PID 1238147，輸出 /tmp/g288p88r；目前 fixed 階段執行中，尚無反證結論。原真 query 未復現診斷仍完整保留，不因正式三輪綠而改寫。封存器與 peer 已備妥於 native-raf-archiver-preparation/。

- 12:53:28 UTC：公開 F `3d681636902371ecc528b20f51eea33e272581c9` 的新 native-rAF 受控反證全部終態。fixed／withdrawn／restored 原 outer、workflow、Node 各為 0／1／0；總 driver、outer、launcher 都為 0。固定與恢復各完成原 P88 143 斷言；撤回僅 P88 修正後，以原 `document.activeElement===document.querySelector("#refGuideMode")` 精確焦點 predicate 失敗，並非工具預條件或 CI 超時。三階段前提皆有效，source／index 前後相同乾淨。此為只跑 P88 的受控診斷，不冒正式 grid。
- 原量測真命中 mode 的 y=627.5，原 query renderer 登錄的真 native scroll-restore callback 一次完成後，舊點已命中 ratio label。撤回版原樣送出 y=627.5，焦點停在 ratio；修正版在該次唯一真實點擊前重新量測，使用 y=602.5 命中 mode。相同既有 query／原 callback，沒有手寫 scroll、rect、focus 或值，也沒有錯點後再次點擊補救。原 25 秒、12 次嘗試、斷言及 golden 不變。
- 12:55 UTC：完整原件封存完成，`native-raf-result/NATIVE_RAF_RAW.tar.gz` 22,446,502 bytes，SHA256 `3f107c0424c62844eaeac3ab6086ea75b7ebc6cc3c9e829dd61c34eedcb52e4a`；349 檔逐一 roundtrip bytes/hash 全相同。封包含各 phase 指令／環境／stdout／stderr／退出碼／SHA／trace 與全部凍結工具。各 phase/tmp 整樹（編譯產物、profile、cache、feedback）明列排除，原磁碟未刪。封存器 exit 0。
- 獨立對抗審已核 fixed／withdrawn／restored 的原 predicate、原座標、真 pointer、143 斷言、來源與時限；另附產品／測試歸因審查。新 F 正式 canvas 連續三輪 0／0／0 與兩位代理封包審查完整收錄。舊真 query 控制 1／1／1、總 driver 2 的無效反證仍原樣保留。
- 限制：本控制直接驗 measure→原 restore→click，沒有 Paint/compositor 畫面證據，也未窮盡 pointerdown→query/restore→pointerup。既有資料未建立新的產品交互紅燈；不能宣稱真人不受影響，亦不能把本次 query 回填成歷史自然紅唯一原因。最新 head ee28481 審查的同 F 其餘項目由主代理接續，這份子代理證據不宣稱 #288 全綠。未另開瀏覽器，heavy 槽已交回主代理。


2026-10-23T14:43:22Z：fresh fetch handoff acd1289／main feb502d；最後審查仍 head ee28481、明文不建議合併，因此不標 READY-TO-MERGE。主整合 a05a21a5 與正文 e008dc52 已公開，正文 hash77fad4a1 與已審原件相同；同 F 全部受影響 gate／反證原件已完成，不重跑綠燈。只讀 merge-tree 預覽 current main 可乾淨合入，並未執行 merge。監看原命令、完整 streams、環境、SHA 與獨立 peer42checks/0 收於 review-refresh-20261023T144322Z；不確定性與最新 review 阻擋原判均保留。
