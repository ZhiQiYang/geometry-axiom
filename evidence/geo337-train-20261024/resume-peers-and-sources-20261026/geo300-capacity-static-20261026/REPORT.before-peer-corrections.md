# #300／#348：不編譯的前置與逾時定位盤點

本次只讀 Git／GitHub 原件並執行純記憶體來源比對、原 generator 與原 Python batch 建構；分析 exit 0。沒有編譯、產品執行、效能重抽、修改產品／ref／PR 或清理。初版分析腳本的一個 SyntaxError exit 1 原稿與分類另存；修正工具後完成，不是產品紅燈或反證。

來源固定：候選 F `cbf0fb621888596aa14ad5f2349b503e23b1b72d`；#348 head `9a8584f57be7935604c3bad4c2481945a6ec3d9f`。交接審查取自 `6e0d142fe1afa8f325d927ac3c5afb1ac3e2902c:handoff/pr-reviews/348.md`，最新審查時間 2026-10-26T08:55:17Z。API 於 10:22～10:27 UTC 唯讀。這些是當時快照，不能外推後續 writer 狀態。

## 結論與最小下一步

三個前置已有產品實作；目前缺的是把新列車已有修正同步進容量鏈並收齊受影響驗收。不要再重寫一套 contact_order／去重／依賴索引。#348 的兩個核心檔剛好缺少下表四項優化，已用新 F 既有測試中的撤回片段在記憶體反向還原，再逐 bytes 與 #348 GitHub 原件比對相同。此等價範圍只有兩個指定 C 檔，不是整個分支。

建議下一個可執行步驟：在 root 指定的獨占容量續作分支，先一般 merge 修好的 #346／#347 鏈及新列車 F，保留容量 512 與安全哨兵修正，核對四個既有優化與其測試都保留；固定新 SHA 後，先跑原 source-index／wood-contact-world／contact-sources 與既有撤回控制，再針對同一個四命令 N512 preload 做定位。正式兩方法的原 600 秒限制與完整 payload 保留；分段診斷只用於定位，不代替正式整批通過。

## 三個前置在 F 的實際狀態

| 前置 | F 的位置與作法 | 邊界／還沒證明的事 |
|---|---|---|
| contact_order 線性查找 | `geometry-templates/woodworking/native/contact_world.c:15–53`：兩倍容量的 open-address ID 索引，完整 ID 比對；sorting 取最後一筆 order，earlier 判斷取最小 order | 超容量仍線性 fallback；碰撞最壞仍可能線性，不能宣稱一般最壞 O(1)。沒有 512 實測收益 |
| 擋面兩兩去重 | 同檔 `:120–193` 建完整座標平面排序與 prefix-maximum 索引；`:227–268` 在 bounded／indexed／unique 啟用快路，最後一次 stable compaction | 正常索引部分 O(F log F)，排序比較還受 ID hash 探測成本影響；duplicate／overflow 的排序、pairwise fallback 仍保留，不能宣稱 whole collector／load 全部線性 |
| geo_eval_depend | `geometry-core/kernel/source.c:63–115,183–223,271–276`：node／edge hash、完整 key identity、cached hint、缺失 edge 的 empty-slot reuse | optional 索引 allocation failure 保留線性後備；新增 node 的 provider 搜尋仍線性於 provider 數；優化每次查找，不等於降低驗證呼叫量 |

四個已存在、#348 尚缺的精確來源：

| 改動 | 完整提交 | F 產品位置 | 現有測試 |
|---|---|---|---|
| 重用已探得 edge 空槽 | `9430bae568feb98805072930c92f9a03a1250d4e` | `source.c:76–115,212–223` | `tests/test_geo261_source_index.py` 的 `EDGE_PROBE_REUSE_EDITS`；碰撞、重建、配置後備、ordered edges |
| provider hint 混合 | `81b6c388f8b73e9aaf885b1d948e5f306b77bafd` | `source.c:188–198` | 同檔 `:169` 起 provider-hint 全段 0/1/0、完整 provider 與 key 中間 byte 控制 |
| 已單調序列略過重排 | `aa16e73d6e1f2965e0a911581e2a545aaaf66870` | `contact_world.c:82–92` | `tests/test_geo261_wood_contact_world.py:281–318`；完整欄位、ties、反向／最後／中間 inversion、uint64 |
| 已排序平面範圍重用 | `7c4a40a71fe46242c302efaa85f1a4d13df0c19a` | `contact_world.c:135–177` | 同檔 `:339` 起，完整 whole withdrawal＋linear oracle＋work count |

`ANALYSIS.json` 與兩份 `*-to-F.diff` 保留 exact 反向比對結果。新 F 的 `source.c` SHA256 `64c7a6223be0e824232bc0ec0139a3728606fb9666a991a951b5aa9357cf3e09`；#348 為 `678877fab2d5acac05d7a1400c9068210beb7844c60c4b8fb30bda693e4f1e2a`。新 F 的 `contact_world.c` 為 `83fd46c25acead96ebc724f673f405176fdc5463296fd8b3b77b72fd66f7798b`；#348 為 `4862b7c956b5944276d2ee3de6915704945da2899a50a29ba2a5e20150e7478a`。

這輪未重新執行上述 C suites 或宣告它們在 F 通過。原 R8 有效樣本由主代理保留，未抽新樣本。

## 兩個原 600 秒逾時的確切範圍

已核原 F0f `0f695866c0ba12d2c70dfd7d40628d0fda0f905f` 的 H7 command **79、83**，兩份 receipt/input 均與已發布 RAW_INDEX 的 size/hash 相同。兩次輸入完全相同（140 bytes，SHA256 `6589eb1c26654effdceee204dd0871d688f8a10c5bbe663ffc974983d63339ff`）：

```
loadfile /workspace/geo348-F0f695866-formal-tmp/geometry-tests/geo261-n1a-9m6ewo1y/timber-capacity-512-placed.scene
dump
objects
references
```

原實耗分別 **600.1147615909576、600.1130447387695 秒**，均 `TimeoutExpired`、`completed_process_returned=false`、`returncode=null`。兩者 `stdout.captured=false`、`stderr.captured=false`，不能把沒有捕捉誤寫為零 bytes，也不能還原出最後已完成命令。因此已知共同卡在同一四命令 preload batch；尚不知道 loadfile、dump、objects 或 references 各花多少時間。這兩個原輸入不是 1048 命令 sequential-history batch，不能宣稱已跑到 undo/redo。

`tests/test_geo261_timber_capacity_host.py:144–151` 將整個 payload 送給 `_bridge.run_once(..., timeout=600)`；`:236–254` 的 load/replay 各是四命令 batch（每個 count 有一次 load、兩次 canonical replay）；`:256–271` 的 sequential 方法先跑同樣四命令 preload，之後才送原 DSL 與 history。600 秒是每次 batch 的 timeout，不是 loadfile 單項或整個 unittest 方法的新門檻。

本次以原 generator 純記憶體生成 N=64/128/256/512，只核字串與 metadata。N512 為 45,154 bytes、1,026 條 DSL（1 surface＋1 grid＋512 timber＋512 place），SHA256 `760a7169ea3577341b4b0ec1b56ea39c21c85c777434325ec906debe0a816f10`。原 AST 建構的 sequential batch 是 **1,048 命令**（reset＋1026 DSL＋21 後續）。這不是 bridge 幾何接受證據，也不是本輪 fixture 重新驗收。

後續診斷可先在既有 observer 的 TimeoutExpired 路徑保留 exception 的 stdout/stderr 屬性與是否為 None；如需即時每列完成時間，使用旁觀紀錄，保持原一份 payload／原 600 秒 timeout，不切段冒作正式通過。若仍無任何完成列，需要另作明確標記的定位執行；不得據此取最好樣本取代原紅。

## 仍未完成與來源限制

- #348 最新審查明列相對目前 #347 head `2e8a6ed20325aa4842dcd0f89eacd598662be598` behind 2，需先修 #346→#347 鏈；本輪未 merge，也未重新計算所有祖先。API 同時顯示 #343／#346／#347／#348 皆 open draft。
- 512 placed 兩方法、#297 probe、完整 native、六 browser、最終帳本／架構與容量效能仍缺；不能將 W7／H 定向三方法或純 Python 生成器替代。
- #300 [原留言](https://github.com/ZhiQiYang/geometry-axiom/issues/300#issuecomment-6287833218) 的 N128/256/512 ≤2×main 是其「提議」。本輪不把它自行升格為新批准門檻；先保留既有測試、診斷與等價性要求。
- F 的 `BACKLOG.md:442–447` 仍是 2026-10-19「未開始／#288尚未合併」歷史；本輪只指出已過期，不刪舊文、不擅自關 issue。
- 本代理對 `/tmp` 唯一新增此資料目錄與唯讀工具，沒有新 checkout／Git objects；#348 head 本地 `cat-file -e` 退出128（物件未在 provider），後續使用 GitHub 原 raw/blob API，不 fetch 或寫 object store。
- 未直接核整份 F0f tar 的6369成員，本次只依已發布固定索引核4個 exact 原件；原封包完整性審查仍以既有收據為準。

待另一代理對抗審查；未推送本目錄，由主代理決定收進證據。沒有 READY-TO-MERGE 宣告。
