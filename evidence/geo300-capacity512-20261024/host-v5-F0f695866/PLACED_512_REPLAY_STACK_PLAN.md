# #348：真正放置、重放、堆疊與擴容量測的靜態計畫

狀態：僅靜讀／設計；沒有執行 generator、編譯、產品、browser、性能或大型 I/O。公開 S=`400a6d0ca50f3aca104fb569c77c8ef753c93355`、E=`391f44da1c3e37e50c7a25a8a855b93c2865062c`、D=`fd206036052bfb4f8c7ea0025c31b1b2a21cc4b8`；新 draft 已為 #348。以下執行前先納入未放置計數的測試修正，再固定新的可解析 F。不能將現有 73 個 AST 方法或 512 個未放置宣告當作 512 支實際放置通過。

## 已讀規則及可用來源

已讀 S 的 `決策佇列.md` 2026-10-12～15、10-22、10-23、10-24，`geometry-templates/woodworking/FIELD-RULES.md`，以及 SSOT 的 D11、D15、I19–I22、R6、R19。本計畫不改條文、決策或數值規則。主支兩端須頂已鋪邊界材側面、副支頂較高優先級料、邊界整條覆蓋、矩形不重疊等條件不因 512 放寬；不把 367 的既有生成間距變成新通用門檻。

原 P-189 generator 是 `/tmp/train337-final-p52-p189-prep/p189/gen_scene.py`（原 `p189_verify.py:22` 的 GEN）。本輪逐段靜讀，未執行或改寫。它的 `single` 家族本來就接受 N=512：一個矩形承載面、兩支 boundary、m 支內部 primary、兩支沿牆 primary、餘下 secondary；總可配置數 `4+m+(m+1)*r`，只裁掉尾端 secondary，使總數恰為 N。先 boundary，再 primary，最後 secondary；副支只依賴前面的主支，尾端裁掉不產生反向依賴。

沿用截面 27×33、z=2500、主支中線起點 916／間距 918、副支起點 363／間距 367、負側 13 正側 14。主支固定段 y=[27,H−27]；副支所在 bay 端點由相鄰主支的實際側面決定；不把格線當擋面。m≤60、r≤60，原格線每軸容量 64 不需增加；單房只用一個 surface/grid，不碰 RC32、boundary16、placement16 的其他上限。房間 W/H、選出的 m/r 與尾端裁切數在執行時由原 generator 輸出封存，不在這份未執行文件捏造實際數字。

原 `build_room` 保存每筆 ID、role、timber/place 指令及 rect；`check_room` 只是 Python 幾何自檢，不等於核心接受。舊 `--selftest` 也只比對已知 calib，不能替代新 N512 執行。新驗收要另以來源 DSL 數值及本節幾何關係獨立核對真 bridge 回傳，避免只拿同一 generator 的 rect 自證。

可用真讀取端：`references`（`reference_bridge.inc::json_references_world`）提供已放置 timbers 的 geometry／definition；`objects` 亦只列已放置 timbers。geometry 含 surface、centerline、length、u/v、dir/side、A/B、origin、axes，可從三維原點與長軸／截面軸四角重建 UV footprint。`dump` 直接串接 `world_dump_dsl`→`reference_dump`，先輸出全部 timber 宣告，再依真放置 order 輸出 place；回覆含 revision 與 definition_sha256。`engineering-read` 呼叫 geometry=false，不當作全宣告／幾何列表。

## 既有 64 與新 512 分開

1. 原 64 witnesses、所有既有 golden／時限照原 suite 保留；原 P-189 的 N16/32/48/64 三方門檻與 loadfile+dump 原 bytes 比較原樣保留。不能用「新容量」跳過它。
2. 新放置驗收先用同一原 generator 的 single N64 校準，再增 N128、256、512。每個 case 明列自己是新場景，不能把 N512 的前 64 支稱為舊 N64 fixture：planner 選出的房間尺寸／主支數可能不同。
3. 執行前釘 generator 原 bytes/hash、source F、全編譯 closure、編譯器／flags、binary hash、環境、16 MiB stack、原測試 timeout。小文本設計不設新的耗時或倍數通過門檻。測試增加後 registry 僅精確增加真正方法數，原 entries 不移位；root 最後統一處理帳本。

## 放置及序列重放：正式必驗，不以 load_ok 代替

對每個 N 的單一原 scene，保存 generator argv／stdout／stderr／exit、原 scene bytes 與每筆 metadata：

- 路徑 A：新 bridge 進程執行原 `loadfile scene`，再 `dump`、`objects`、`references`。必是真 exit=0、load_ok=true；恰 N 個宣告及 N 個 placed ID=1..N，沒有遺漏、重複或額外成員。角色／surface／順序也精確驗證。
- 路徑 B：另一新進程先 `reset`，按 scene 原順序逐條發 `line <statement>`，只略過原注解及空白；每條必 ok=true，拒絕未處理 preview／token。每次宣告再放置，檢查 64、65、127、128、255、256、511、512 中本 case 達到的關卡（只在完整 place 後查）。末尾同樣讀 dump／objects／references。`cmd_line` 回覆不包含整個世界，但仍逐筆保原 stdin/stdout/stderr 與真終態，不讓 Popen 管線藏在 passive subprocess.run observer 裡。
- 路徑 A／B 比較 canonical dump 的 **text UTF-8 bytes** 及 definition_sha256，並逐個比較 geometry／definition；不能比較不同編輯路徑的整個 JSON raw 並假裝 revision 應相同。原完整 JSON 都封存，revision 各自保存。
- 路徑 C：把 A 的 dump.text 原 bytes 寫成 replay.scene，兩個新進程各走同一個 `loadfile replay.scene`＋`dump`。同一新進程初始化與同一 protocol 下，兩份完整 stdout 必逐 bytes 相同；再驗 replay dump.text 等於 A dump.text，geometry/ID/role 等於 A。這是新 F 內部 round-trip／determinism，不冒稱舊 64-cap base 也接受 512。
- 各角材獨立重建矩形、驗正長、在房間內、無正面積重疊；兩支邊界覆蓋完整原邊，主支端面在 boundary 側面，副支端面在已放相鄰主支側面。核 geometry 不能只核宣告數或只依賴 `ok:true`。優先沿原獨立 oracle／現有幾何工具做，若需新 helper，先對抗審其座標／負向軸處理。

以上不宣稱完整施工場景：原 generator 會裁掉尾端副支，SSOT R19(b) 允許施工中。沒有 RC／凹角／partial-end fixture，不拿矩形結果覆蓋 #318 的閱讀 A 範圍。

## 512 滿容量／513 拒絕／歷史

真 F 的 512 placed 世界保存完整 dump 回覆後送 `line timber 513 27 33 role primary`：必正常 ok=false、原容量錯誤「角材的數量超過上限」、原 dump **整個回覆** 等同（含 revision/hash）、objects/references 仍為原 512。再送不完整 `line timber`，原容量優先拒絕契約仍同樣驗。可另外送原 generator N513 場景到已有 512 世界，驗 whole-load 拒絕且回滾，不把容量錯誤當壞幾何。

用原 metadata 的 leaf secondary 做 delete→undo→拒絕513→redo→undo：delete 真變 511；undo 回 512；拒絕不能清掉 pending redo；redo 真回先前 511 文本；最後 undo 回原 512 文本與幾何。undo/redo 的 revision 自增不拿來比較歷史完整回覆，只有**沒有提交的拒絕**才要求完整 dump 回覆原樣。

所有 valid513 append 只在 guard 存在的正常 F 執行。撤容量 guard 的 mutant 永遠只跑原安全 missing-ID sentinel／direct API，不送會越界的 valid513。容量整體撤回若要針對真 placed 世界自證，必把唯一容量宏一致改回 64、用所有同源 aliases 真重編乾淨 bridge，然後跑新 N512 場景，預期在第 65 宣告正常容量拒絕；不混 64/512 ABI，也不把具名編譯錯當這組 runtime kill。撤回／恢復原 bytes 與精確 assert 全封存。此控制與原 7 ABI controls 分開。

## Stack 與記憶體：診斷不得混成通過

已見 `current_geometry.c` 中多個 `World backup=*world`（含 apply-proj）和擴容 scratch；未跑前不能說 512 安全。先取得正常 flags 的真 bridge／CLI 在原 16 MiB stack 下的所有上述路徑 exit；不得因 crash 偷調 stack。原 `tests/diagnostics/reference_fragment_stack.py` 的 core16／bridge8 MiB 回歸照原條件保留，不改其 30 秒／golden。

另建完全隔離的診斷 binary：與 F 同 closure，補 `-fstack-usage` 保存所有 .su，並以既有 `tests/evidence/211-cloud-bridge-stack-20261013/trace211.h` 為參考，設計／審查 entry hooks 的 observed stack high-water。原 trace 用 uintptr 相減、固定 256 frame 記錄，不能原封視為可信精確峰值：新 probe 要處理初始 top/方向、下溢、depth 超限與未成對 hooks；任何截斷必明列。原 helper 留作歷史，不改它。

報告分列：(a) sizeof(World／WoodDocument／ReferenceEval／各大 scratch)；(b) compiler 每函式 frame bytes／dynamic 標記；(c) **instrumented observed peak** 與最大呼叫鏈；(d) uninstrumented 正常執行退出碼與 RLIMIT_STACK。每函式 .su 不是整條 call-chain 峰值，instrumentation 會改 frame/layout，也漏到某些外部庫；不把它冒稱 uninstrumented 精確峰值。max RSS 只列進程記憶體，不冒稱 stack。若量測器本身不能可信判定，標 stack-peak UNKNOWN 並保原成功／失敗，繼續其他項。

## N128／256／512 探索性能

只有 root 釋放獨占槽後執行；前置 df／原來源 SHA／binary／冷熱條件與其他 worker 狀態全部留存。沿原 `scale_compare2.py` 的 loadfile 計時定義、原 3 rounds、原 600 秒 timeout、原 stdout/raw sample 保存方式，在新獨立 out 對 F 增 N128/256/512，N64作共同錨點；這些是探索樣本，不能新增 fix/base≤某倍 的政策門檻，也不能把舊 base 容量拒絕的耗時當性能分母。多個可接受 512 的同 closure 候選才可依原交錯順序比較。

報每個真樣本的 wall-time／exit／timeout／load_ok，全部回覆原 bytes；中位數及 N doubling ratio 是描述而非新 pass line。某點 600 秒 timeout 原樣標紅／未完成，不拉長時限、刪樣本或拿較小 N 冒充。loadfile 與逐條 line 的總時間分欄，不能混同負載。針對 contact_order、擋面去重、geo_eval_depend 的 source-call／probe instrumentation 必用另一 diagnostic binary／run，不混入正式 wall time；沿 #323 既有 source-calls 門檻保留在其原 N32/64，擴大 N 的新計數僅探索，不自訂新倍率。

## 出版界線

本文件及新 helper 草稿先交 backlog 對抗審。正式執行前再固定 F 並正常推；完整原流、exit、環境、fixture/tool/binary/source hashes 由原收據機制保存，當 capture 路徑沒有實際產生檔案時如實列 configured-only。原 S400/E391/Dfd206 是靜審歷史；新 F 真正未跑的欄位持續 UNRUN。任何能力宣稱須分清舊64、512未放置、512已放置、ABI與正式 native/browser/專項，沒有全綠前不標 READY-TO-MERGE。
