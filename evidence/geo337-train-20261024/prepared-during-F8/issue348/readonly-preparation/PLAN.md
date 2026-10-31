# #348：下一個最小指令階段診斷（尚未實作、尚未執行）

兩個原 600 秒紅燈，現在只能定位到同一個**首次四指令批次**，不能指名 `loadfile`，更不能說已跑到 sequential replay。這份準備沒有新產品測試、C 編譯、profile 或 browser；不改產品、原收集器、斷言、golden、時限與任何分支。

## 原件界線

- 原執行來源 F0f：`0f695866c0ba12d2c70dfd7d40628d0fda0f905f`。H7 `command-000079`／`000083`，均 `TimeoutExpired(...,600)`、`completed_process_returned=false`、`returncode=null`；不能寫成正常 exit 1。H7 外層 exit 1 是另一層結果。
- 兩個原 stdin 完全相同：`loadfile <...>/timber-capacity-512-placed.scene\ndump\nobjects\nreferences\n`，140 bytes，SHA256 `6589eb1c26654effdceee204dd0871d688f8a10c5bbe663ffc974983d63339ff`。同一原 ELF 的收據 hash 為 `050123dadc7e7082ff211fd1469594ddc49188b565a3d707309f682583681841`；該收據明列 `payload_retained=false`。
- 原 `stdout/stderr captured=false`，沒有原 partial 檔。不從「沒有保存」推成「子程序確實沒有輸出」。兩次之間的 64 首次載入與兩次 canonical replay 是原 CompletedProcess 0；本次只讀並保留，不重跑或重抽。
- F73 `73b21e64dce72f0d16ca29e18559c51815b9724d` 重驗的是 sentinel 影響項，不含這兩個 placed512 方法。F0f 的紅不能移標 F73 或目前列車 F8。
- 已保留的 512 fixture 為 45,154 bytes、SHA256 `760a7169ea3577341b4b0ec1b56ea39c21c85c777434325ec906debe0a816f10`。原 supplement 明說是在第一個 timeout 後、第二次執行中取樣；不能冒稱第一次執行前已封存的相同 bytes。後續每次正式或診斷都要在執行前另封存實際 fixture。
- 原相關編譯是 **`-O0`**（完整 argv 見 FACTS）。改成 `-O2` 得到結果，不能替代原 H7，也不能將它稱為相同 gate 通過。

## 已排除的一個假修法

原 `observe_bridge_bytes.py:327–333` 已將 `result` 或原 `failure` 的 `.stdout/.stderr` 送入 `retain()`，並重新拋出原例外。單純補一個 `except TimeoutExpired` 存同樣 attributes，不會提供當次原本沒有的資料。保留這份原 collector，不重寫歷史收據。

## 最小的下一步

先等 root 排定新的診斷時槽。full123 獨占時只做本準備，不啟動新程序。新的診斷來源必須另固定可解析 SHA；若已合列車前置，就明寫新 SHA，不能重貼 F0f 的身份。

1. 使用未改的四指令原順序、同一 single-family N512 fixture bytes、單一 fresh bridge、原整批 `timeout=600`、原環境與 `-O0`。不得拆成四個新程序、四個 600 秒、依序重置 timeout、減小 N 或只跑到第一個綠指令。新路徑變更僅在記錄中對照；完整實際 stdin 重新封存，不對輸出做正規化。
2. 額外編一個**診斷專用 ELF**，僅觀察主 loop 的 stdin `fgets` 已回傳，以及 stdout `fflush` 的進入／回傳。最小候選是獨立小 TU 的 `--wrap=fgets`／`--wrap=fflush`：精確過濾 `stream==stdin` 或 `stream==stdout`，每次恰好呼叫原函式一次，原結果與 `errno` 都不改。不得修改或攔截 scene 檔案的 `fgets`、tmpfile flush、測試回應或公理。
3. 事件寫到獨立預開的普通檔案 FD，使用原 stdout/stderr 以外的通道，保存 ordinal、event、monotonic timestamp、原函式結果。主 loop 在 F0f `web_bridge.c:1032` 讀下一行、`:1183` 每個 handler 後 `fflush(stdout)`；早期錯誤分支也 flush。不採用 stdout marker、`stdbuf`、PTY 或每指令互動重送，以免改協定與緩衝條件。若 ELF 的符號未走上述兩個 wrapper（例如 compiler fortify/inlining），視為診斷無效，不把缺事件當負證據。
4. 原 `subprocess.run`、整批 600 秒與 kill/reap 路徑保留。事件在發生時落盤，timeout 後仍可讀，不依靠 child 正常 exit 或 gprof 終止檔。不得從只收到 read 事件推定處理完成；必須有配對的 stdout flush-return 才可說該 handler 已走完，且仍須核對原 stdout 的完整 JSON 行，才能說它成功回應。
5. 先以無產品的合成 protocol 測試驗證觀察器：正常四行／分段 JSON／某指令不回／stderr 大量輸出／EOF／原 timeout exception 身份／觀察器 I/O 失敗。撤回一個指定 command-boundary 事件必須令觀察器完備性檢查紅，恢復後綠。這只驗工具；不得算產品撤回反證。未完成此工具自證與獨審前不執行 N512。
6. 下一次 N512 診斷只跑一次，保存所有事件與完整／partial raw streams，不因紅就換輸入重抽。其耗時不混進既有正式數值，更不改 R8 的 36 樣本。記錄 compile/link flags、source/ELF/fixture hash、real exit 或 TimeoutExpired、事件缺失與 observer fault；任何 observer fault 都讓診斷不可判，不將它當產品失敗的根因。

事件型態：`stdin_line_returned(i)`、`stdout_flush_enter(i)`、`stdout_flush_return(i,rc)`、`stdin_eof`／`stdin_error`。`fgets` 回 NULL 必須同時保存 `feof(stdin)`／`ferror(stdin)`，不能把讀取錯誤寫成正常 EOF。`i=1..4` 對應 loadfile/dump/objects/references。來源與 wrapper 符號先核對；只對這個固定四行批次解讀。

| 最後可核事件 | 能說的事 | 不能說的事 |
|---|---|---|
| 沒有第一個 stdin-return | 啟動／初始化／第一個讀取邊界之前未取得事件，或觀察器失效 | `loadfile` 卡住 |
| stdin-return(i)，沒有 flush-enter(i) | 進入第 i 個主 loop 指令後，尚未到該次外層 flush；須排除事件漏失 | 該指令裡某個函式已被證實耗時 |
| flush-enter(i)，無 flush-return(i) | 阻塞可能在 flush／輸出端；核 pipe 消費與 I/O | 幾何計算是瓶頸 |
| flush-return(i) 且完整原 JSON 行存在 | 第 i 個 handler／flush 已結束；JSON 的 ok 另核 | 下一個指令或整批已通過 |
| 四個 flush-return 都有、仍 timeout | 四個 handler 已回來；查 EOF、最後輸出 drain／退出／收集路徑 | 把 timeout 直接歸給 loadfile |

## 只作候選的超線性路徑

以下行號固定在 F0f；完整原來源與 SHA 在 `source-F0f/`／FACTS，未由新來源反推舊執行。

| 優先序 | 可見靜態路徑 | 最小後續觀察 |
|---|---|---|
| 1 | `parse_scene_file` (`current_geometry.c:10038,10108`) 每行 `apply_scene_line`；`apply_reference_place` (`references.inc:792–848`) 每次 `place` 無條件走 `reference_checked`→`world_revalidate`。每次重驗又走 `reference_check_all` (`:641–684`) 的每料兩兩 overlap；成功完成 N 個 place 時，這個遍歷結構可能累積至 Σk²，即立方成長，而不只是檔尾那一次重驗。 | 若第一指令未返回，再在**診斷版**記錄 parse line ordinal、world_revalidate begin/end、reference_check_all begin/end 與實際 member 數。不可跳過中間驗證或改錯誤 precedence。 |
| 2 | 同一重驗內，已放置且前置 anchor／host／footprint 讀取成功的 member 會 `collect_stop_faces`；各 contact query 會蒐集 facts、建立 collection、逐 face 建 feature/dependency (`contact_sources.c:91–108,166–190`)。即使單次 K 查找已索引，query／face／dependency 的**呼叫總數**仍可能成長。`reference_sources_begin_candidate` (`references.inc:689–700`) 每輪重建並 reset graph，不能假定跨輪 cache 可共用。 | 計數 rebuild/query/faces/source calls/node/edge；分開看呼叫成本與次數，保留 graph 順序與 candidate 身份。 |
| 3 | `reference_dump` (`references.inc:898–901`) 為每個輸出 member 再掃所有 members 找最早 order，為二次選取。`eng_definition_hash` 也使用 canonical dump，loadfile 成功回覆、dump、references 都要算 hash。 | 若卡在 dump/references 或 loadfile 後半，再區分 dump 與 definition-hash 邊界；維持 canonical 原 bytes/order。 |
| 4 | `reference_timber_index` (`references.inc:175–178`) 線性查找，被 provider descriptor/read 等路徑使用；contact query linked list 也線性 (`contact_sources.c:60–61`)。 | 先量 probe 次數；不少 query 是剛插入的 head，不能僅看 for-loop 就宣稱退化根因。 |
| 5 | 大容量的 World snapshot、`ReferenceEval local={0}` (`references.inc:717`)、facts allocation/zero 及反覆 rebuild 增加固定容量成本。 | 分別記 memcpy/zero bytes 與次數，對照 F8 已有 H 初始化修正；不能把 F8 的改善貼回 F0f。 |

已存在的優化不要當作漏做：F0f `source.c` 已有 node/edge hash indices；`contact_world.c` 已有 contact order 索引、stable member sort 與 indexed dedup。正常 unique／bounded 分支不能泛稱仍用舊 O(n²) 去重；fallback 只在原條件不成立時使用，是否命中須有數據。這份靜態準備沒有判定哪一路占 600 秒，也沒有提出放寬容量、工法、公理、錯誤診斷或 comparator 的方案。

## 完成診斷之後仍要做

有證據指出根因後才作最小產品修正、撤回／恢復反證；由 root 依來源影響處理帳本、架構與正式重驗。原512的 load/dump/objects/references、獨立 placed 幾何 oracle、canonical 完整 bytes、sequential replay 與 513/history 拒絕全部保留。診斷成功不會將兩個原紅收據改綠。
