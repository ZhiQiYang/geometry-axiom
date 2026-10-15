# K2a-A 有界歷史容量相容（2026-10-12 臺北時間）

回覆 ChatGPT 6113090394、dot 6113125187、6113571884 與授權更正 6113762903 的 B1；採用使用者明示批准及 [P-059 裁決](https://github.com/ZhiQiYang/geometry-axiom/pull/201#issuecomment-6113440823)的有界歷史標記例外。B1 已修；B2 正式整合／WSL 七組仍未驗，不將 PR 宣稱可合併。

修改前：精確 base `49c391f2afbcee17bb2647fce74c3c5532a01527` 寫出並讀回 `/13` 真 ZIP；20 個 grid-binding 引用、各 raw ≤4096 字元，附件 envelope 131071 bytes、draft 130954 bytes。新 reader 在讀取時加 240-byte 預留，因 131194 >131072 拒絕，原 importBytes 在 API/fetch 0 次時失敗。原始 ZIP、base script 與失敗收據保留在上一輪 boundary/legacy 證據；本輪先驗容量紅，再修正。

修改後：stored 讀取／保存與新接納分開。stored 仍先驗 plain JSON、白名單、型別、份數、每個 lost 必須 true、孤兒與目標規則；僅在 byte oracle 移除 lost/orphan 及因補標而升出的單份集合外殼，並重算相應格式／能力增量。去除標記後各層仍須通過原 128 KiB／1 MiB／8 MiB 上限。物理讀取先有有限最大標記額度，完整驗證再按實際結構核對，不把額度送給 raw 或一般 payload。保存資料從不套用去標投影，raw、ruleDraft、lost、orphans 原樣保留；重開不依檔名、年代或新增可信布林辨識。

既有合法集合的 record 保留集合 byte 上限；個別 draft 仍以 128 KiB 驗去標 payload，單份 /13 附件仍保留原 record/envelope 128 KiB 限制。補孤兒不能一律把既有集合套回單份外殼上限，這個過度拒絕已先驗指定容量 AssertionError 紅，再修並加突變。第一輪 4b44 上的完整非瀏覽器通過收據另存 initial；f891 的第二輪在發現空附件正規化可能隱去 unrelated metadata 後主動中止，原 log 封存為 interrupted，不當作通過。最終 977150 修正：byte oracle 保留全部其他 manifest 欄位，讀取在任何正規化／copy 之前先核對原始未標記內容；空附件的移除不能當網格標記容量。這個守門的兩個指定突變皆紅。

新草稿及有內容變更的 setGridDraft 仍依現行接納與最壞預留。只有已存在、完整內容相同且通過有限 JSON 驗證的歷史 flush 才視為原樣持續保存，不推進 history；多 1 byte 編輯仍拒，state/history/raw 不變。正式 editor writer 是新增／修改接納入口；pack 是已接納資料的持續保存入口。預留的個別、集合、集合 record、完整專案拒例全部保留。

原生證據：在乾淨程式 head `977150daae71e6bc27feaf33f3386904448be64a` 上，原登記 ZIP gate 37 assertions、Native lifecycle gate 42 assertions，共 79。before/after head/tree/status/來源 SHA、fresh runtime、兩個不同原生 session、實際 bridge PID/exe/SHA 全符。真 base ZIP→原 importBytes/native upload/objects 首次缺失掃描→20 個 lost＋孤兒→真保存 ZIP（131907 bytes）→另一原生 session 冷開；raw/ruleDraft/flags/世界 dump 完整相同，保存格式 /17 含 grid-editor-drafts/1。browser file picker 是收集真保存 bytes 的替身，原生服務與原 workspace/pack/unpack 未替換。VM 的掃描／unchanged flush／one-byte writer 原子拒例另列，未冒充原生 E2E。

補充 TEMP 原生保存檔觀測另外保留 native-marked.gcanvas 與完整 original/marked/cold 資料：逐項比對 draftId、baseRef、去掉 lost 的 inputRefs（kind/id/指紋）、rawForm、ruleDraft；+1 byte 拒例當下 API=0、state/history 不變。父程序用 subprocess.run 自動記 returncode=0、腳本與 stdout SHA。觀測時只有 expected／證據 metadata 尚未提交，未假稱整棵 checkout clean；三個產品來源 SHA 前後都等於 977150，兩個 live runtime 都 fresh。API 計數 wrapper 只轉交原 apiRequest，不替換回覆；picker 只接收真正保存 bytes。此 TEMP 補充不算登記 gate、正式 CDP 或 WSL，也不加到 79 assertions，父程序收據只屬該補充，沒有借給原登記 gates。

新增七項測試在原已登記 test_grid_drafts_lifecycle_capacity.js、test_reference_workspace_races.js，ZIP 斷言加在原登記 browser gate。完整非瀏覽器 83 suites：2649 pass／0 fail／1 允許 GDI skip；Node 684/684。run_all.expected.json 由 --build --update-expected 自動產生，未手改。完整測試與 browser 期間沒有修改程式／測試或提交，只有完整流程完成後自動 expected 與新證據另行提交。這不是正式 WSL 七組，也不是候選整合樹的收據。

十二個指定突變各有 baseline 綠、node --check build 綠、指定 AssertionError 紅、restored 綠且 0 skip：取消 stored read、放行 1 raw byte、取消 legacy scan 例外、拒 unchanged flush、放行 changed flush、放行 1 manifest byte、丟掉保存 lost、取消新接納預留、縮小既有集合 record 上限、放行 1 collection byte、跳過原始 manifest 上限、隱去 unrelated metadata。取消例外的紅燈訊息明示容量。突變只在隔離 JS 副本，原產品檔沒有帶變異；raw logs、driver、前後錨點與 source SHA 都已封存。

M1 的共用 P2 修正保留，完整原 handler/writer 回歸再次過；上一輪三個 M1 突變仍是其原 head 的歷史收據，沒有宣稱本輪重跑。current_geometry.c 與 mutants_results.json 未改；mutate 無新覆蓋。原 mutate.py --check 用獨立空 MUTATE_CACHE 的 clean-checkout metadata 模式：40 killed／1 crashed／4 equivalent／3 retired／0 stale；未重新執行 48 個核心突變，也沒手編帳本。上一輪 default TEMP mismatch 失敗仍保留，沒有刪除他線快取。

未驗／阻擋 B2：唯一整合 owner 回收既有 K1 bundle 的 merge-resolution／terminal 修正；#199 合併後以 merge commit 納入；凍結正式整合最終 SHA 再驗完整 CDP／完整非瀏覽器／正式或代理 WSL 七組。#199 本輪查詢仍 open/unmerged，head e837a9308642a54ba55d7d399eb66805e1d5984e，已讀最新條文 diff（D57、R54 等），未提前合併。完整 CDP 的 54f 舊收據不當作目前 RW 完整 UI 通過。其他三個 browser gates 本輪未重跑。未執行 WSL。

CI 受帳號計費阻擋,正式合併裁判由本機 WSL 收據提供。GEO-219：無新入口。公理／白話／閱讀器／BACKLOG／決策佇列均未改。維持 draft；base axiom/adopt-drafts-topology-k2a-20261011；K2a-B 疊本分支；依看板 K2a-B/PF 暫停。未合併、force push 或關 PR/issue。

| 驗收 | 本輪狀態與理由 |
|---|---|
| M01 | 過：原生 ZIP gate 的兩份並存回歸 |
| M02 | 過：一般 ZIP 及 base 近限舊 ZIP 補標／保存／原生冷開，raw 相同 |
| M03 | 過：完整非瀏覽器同 draftId 續開回歸 |
| M04 | 過：Native 確認移除／Undo，原 handler VM Undo／Redo |
| M05 | 非瀏覽器 pin 守門過；專項 UI 本輪未驗 |
| M06 | 過：Native 刪除／Undo／Redo、匯入首次缺失掃描 |
| M07 | 過：完整非瀏覽器同目標整份拒例 |
| M08 | 過：完整非瀏覽器第 17 份拒例 |
| M09 | 過：完整非瀏覽器草稿引用拒例 |
| M10 | 過：一般三格式、歷史近限包升 /17 重存及原生冷開 |
| M11 | 過：完整 format／capability 負例與精確容量拒例 |
| M12 | 過：晚到／抹旗標／純移除拒例；共用 P2 回歸及 changed legacy flush 原子拒絕 |
| M13 | 既有 1280/390 收據保留；本輪該 browser gate 未驗 |
| M14 | 過：Native 同 ID 不復活回歸 |
| M14b | 過：一般及近限歷史 lost 真保存／原生冷開，拒同卡重取回歸 |
| M15 | 非瀏覽器 repin 回歸過；專項兩方 UI 本輪未驗 |

## 範圍外改動

project-store.js 的歷史容量投影、讀取／pack 模式及 ZIP manifest decoder 有限物理上限，是本次使用者批准／P-059 的必要實作；沒有把舊五行授權冒稱為任意廣泛放寬。reference-workspace.js 在 featureProposal 增加 storedGrid（只由 grid 自動缺失掃描傳 true），manifest/exportSnapshot 各一行傳 persistence 模式；這些共用區段合計少於 20 行，理由是補標後須能完成原保存流程，測試與十二個指定突變見本輪收據。其他附件 proposal 仍走原預留。其餘 RW 改動位於已授權的 replaceGridDrafts/setGridDraft。

完整原始 suite／mutant logs 以 tar.gz 封存，inventory.json 列每個成員 raw SHA；browser receipts 的 gzip 亦逐項列 raw／stored SHA。code head 與交付 metadata head 分開記錄。前輪證據不覆寫。
