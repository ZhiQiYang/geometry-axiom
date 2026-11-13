# PR #348：原 L 的 native 耗時核對與既有 profile 查因

這是既有原件的唯讀分析，沒有執行測試、編譯或新 profile，沒有修改產品、門檻或原件。此目錄在 SHM，尚非永久交付；請主代理採入必要文字。原公開證據 E：`75464e8cda864ebea6717f95853f724fb9278583`。

## 來源與真實終態

- native execution L：`7c8e9cee4ed5b3706ee919e2831a1dac0aa55ea5`。
- 原指令：`ulimit -s 16384; python3 tests/run_all.py --build --update-expected`。
- 原開始／結束：2026-10-29 16:54:59.491547–17:29:59.567513 UTC；2100.075953891 秒；程序 -9、recorder 124，expected 未變。不是整套通過。
- [公開原件](https://github.com/ZhiQiYang/geometry-axiom/tree/75464e8cda864ebea6717f95853f724fb9278583/evidence/geo300-capacity512-20261024/native-census-L7c8e9cee)：PROCESS、stdout、SCHEDULING-NOTE、COMPLETED_PYTHON_RESULTS 四份本地原件與固定 Git blobs 逐 byte 相等。
- 原 `actual-binaries-sidecars-logs.tar` SHA256：`45d8650021db66415bf876ef4a1725ee3c2be5a1b0e67bd0d587b507e83070df`。只在記憶體讀取既有 tar，未另解包／複製；102 個 JSON 與 unittest 日誌均回對 archive 成員與 hash。
- [1..4] 四個非 Python suite 已執行；[5..106] 102 個 Python suite 有完整原件，合計 1523 pass／0 fail／1 原允許 GDI skip；[107/243] H7 停於第八個方法，只有七個完成點；後續 136 項未跑。不能從此推定最後一個方法的哪個 64／512 批次中斷。

## H7 前的 18 分鐘，哪些可以量到

`SCHEDULING-NOTE.json` 保存的 /proc 起點為 H7 約 17:13:22.550000 UTC，距外層開始約 **1103.06 秒**，當時原 2100 秒預算約剩 **996.94 秒**。該起點精度有限，減法結果的小數位不是新增測量精度。

102 份原 JSON 的 `seconds` 相加 **855.05 秒**，同一批 unittest 內層日誌相加 **838.141 秒**。前者來自 `_unittest_runner.py:198–209` 的 fresh-check／import／測試／輸出前計時，四捨五入至 0.01 秒；後者是 unittest 內層計時，列印至 0.001 秒。兩者差 **16.909 秒** 不能當成整輪 runner overhead。

| 已執行 suite | JSON 秒 | unittest 秒 |
|---|---:|---:|
| test_axiom_reader | 165.56 | 165.308 |
| test_geo261_load_residual | 71.90 | 71.739 |
| test_bridge_integrity | 37.58 | 37.438 |
| test_geo261_host_facts_authority | 36.17 | 35.981 |
| test_geo261_model_base_replay | 19.72 | 19.558 |
| test_geo261_deferred_product | 19.34 | 19.179 |
| test_geo261_model_semantics_authority | 18.74 | 18.600 |
| test_geo261_host_authority | 17.20 | 17.053 |
| test_geo261_model_vertex_ledger | 15.98 | 15.824 |
| test_geo261_derived_policy_graph_product | 13.42 | 13.263 |

前十項合計 415.61 秒；77 個 `test_geo261_*` 合計 587.19 秒。完整逐項數字、原成員路徑與 hash 在 `TIMING_AUDIT.json`；`SUITE_TIMES.tsv` 列 107 個順序位置，累計欄**只累計已完成 Python JSON**，不是父程序 wall timeline。未保存的 suite 絕對開始時間與父程序 duration 都是 unknown，沒有用檔案 mtime 補造。

約 **248.01 秒** 無法按原件分配：包括六個冷建置、四個非 Python suite、父程序／直譯器／I/O 與捨入差，**不能全算編譯**。binary sidecar 的 16:55:21～16:56:34 `built_at` 是成功建置後寫入、截至秒的完成標記，不是各次編譯耗時。oracle 原日誌的 90 秒是 `selftest.py:1459` 啟動的掃描階段計時，沒有包含此前 mutants／golden，不能當整個 oracle 時間。

reader 的 165.56 秒是閱讀器 suite，不能直接歸為 K/H/W 產品熱點。load-residual／host-facts／model suites 包含編譯及產品操作，但 L 沒有各子程序耗時。bridge-integrity 的既有測試確實包含 load／dump／render／保存及 canonical reload，然而沒有逐方法時間，不能將 37.58 秒全歸給其中一個方法。

## 與已綠的獨立 H7 分開看

獨立 T：`256747c5c8f8f8934eeb08ae404dee1f67591508`，採入產品 M：`7a0e6dd81c54066995981393925fa46a815de2f8`。[原可讀結果](https://github.com/ZhiQiYang/geometry-axiom/tree/75464e8cda864ebea6717f95853f724fb9278583/evidence/geo300-capacity512-20261024/placed-h7-256747c5/readable-originals)：8／0，outer 0，**1142.271674 秒 <1200**，九個 batch 均 <600 秒。取消／新 token 案例只放 7 支，不是 512 取消。

T 中五個 512 產品批次：load 199.063163、sequential/history 214.230526、另一路 load 193.231267、canonical replay 216.363950／216.621139 秒；共 **1039.510045 秒**，占該輪 H7 內層 1142.122526 秒約 **91.02%**。九批合計 1042.317745 秒；其餘 99.804781 秒沒有足夠子階段計時，不能全稱建置。

L prefix 1103.06 加獨立 T H7 1142.27，算式會比 2100 多約 145.33 秒，且還未計後續 136 項。**這只是跨輪次規劃估算，不是同輪實測總耗時、預測或確定的 timeout 歸因。** L 在 17:14:04.935–17:14:15.134 UTC 與 R07 功能測試重疊 10.199 秒，也未作獨占效能控制；不能將全部 timeout 歸因於重疊，或把兩輪樣本拼成正式驗收。

目前可以確定：L 整體仍紅，獨立 H7 綠；T 的 load／canonical replay／history 五批確是實測的大宗產品成本，L 的既有 prefix 也有明確 suite 熱點。尚不能證明任何單一函式已是唯一剩餘瓶頸，不能估出未跑 136 項，也沒有證明現有候選足以讓 aggregate 通過。

## 現有 N128 gprof 支持的下一步

只讀 `/dev/shm/pr348-profile-m7a0e-n128` 的原 REQUEST／RESULT／gprof；來源 M 如上，原 O0 + gprof、128 支單次 placement 診斷，exit 0，wall **5.982724714 秒**、user 5.916545 秒、RSS 121528 KiB。gprof 取樣間距 0.01 秒，self 合計 **2.83 秒**，不是 wall，也不是正式 O2 樣本；不外推 512。

原 `gprof.txt` SHA256：`42e35f985d01ae9f0347258da674509318e682b06eeaef4f7736b20e7db46263`（已核 bytes）；RESULT hash：`1dd53289f85f400a43cd875aa2eb06e9e8f3282a53e5a236ec66ad795f10be73`。

| 函式 | calls | sampled self 秒 |
|---|---:|---:|
| geo_eval_depend_hint | 14089763 | 0.20 |
| geo_source_edge | 15848086 | 0.17 |
| contact_face_index_before | 24239144 | 0.13 |
| geo_source_node | 1783512 | 0.13 |
| reference_contact_facts | 77181 | 0.12 |
| geo_source_scope_end | 1279081 | 0.09 |
| geo_source_scope_record | 11051156 | 0.08 |
| contact_face_index_build | 33442 | 0.08 |

原 call graph 1067–1077、1117–1139、1154–1172 行顯示：placement-depend／contact-facts 分別送出 6283164／5422582 次 hint；hint 只落到 25189 次 source-node（約 0.179%），大部分仍呼叫 source-edge。source-node 有 1279081 次 index-append，約占 node 呼叫 71.72%。因此「再增加 hint」沒有現有數據支持；值得接續檢查的是 H 呼叫端反覆建立／登記 contact/member 依賴與 source graph 的生命週期。

具體源碼接點：`geometry-app/native/reference_sources.inc:490,502,617–663` 的定義／placement 依賴及逐 member contact-facts；`geometry-core/kernel/source.c:55,75,86,274,302,403,425` 的 scope、node、edge、hint、provider evaluation。已有 footprint cache 命中仍須登記依賴。任何候選必須維持 ordered graph、consumer/provider/key/edge-kind、candidate 世代、失敗 rollback、sealed 與 CAPACITY，不可直接跳過必要依賴。

既有 plane-run helper 對應 before+build 的 0.21 秒，只占 sampled self 約 **7.42%**；0／1／0 反證不是效能證明，perf 未跑。上述接點只是有原件支持的下一個查因方向，未實作、未宣稱可省 145 秒，也未取得新效能樣本。

本目錄核對工具 `analyze.py` 的既有執行 exit 0；`TIMING_AUDIT.json` SHA256：`c0283345230fcbf88dca52a1e7d89f9fe7e2b1fec3d4a7b1b24f526895be8f1e`。原紅燈與原 archive 保持不動。
