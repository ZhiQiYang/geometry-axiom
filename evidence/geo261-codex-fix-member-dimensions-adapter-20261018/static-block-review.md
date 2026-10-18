# 02 member dimensions：固定來源靜態核對

固定基底 `e9c1509cf89e6f35d298743ec5e3368370316cf7`，候選補丁 `02-member-reference-host-dimensions.patch`（1204 bytes，SHA-256 `636c9de8d3f60e8645ed17e80e7669ade435e688860c895fc5e9ad2753199622`）。本次只讀固定 Git bytes 與外部原件；沒有 apply、checkout、編譯或執行產品測試。兩個 hunk 的 old side 與基底逐行相同，僅在記憶體重建新 bytes；重新產生的 unified diff 逐 byte 等於原補丁。機器可讀身份見 `static-block-review.json`。

分類為「舊函式形狀預期未承接 H 來源組裝」：原測試針對已抽離 W 策略的薄函式禁止迴圈，後續合法 H 來源尺寸材料化直接加在同一函式，導致形狀守門轉紅。修正把該責任完整抽為清楚的 H helper，讓原薄函式繼續委派 W；不是把 W 演算法搬回 H，也沒有放寬測試。

## 身份與控制流

| 原區塊 | bytes／SHA-256 | 核對 |
|---|---|---|
| references.inc:595–612，完整尺寸材料化 | 1192／`e6b8dd54e1084874508e5c3b45412313a4d733ebc6756871edcd0cdfecd7b503` | 搬入 `app_member_reference_materialize_dimensions`，逐 byte 保留。 |
| 原 :613 W compute／place 尾段 | 281／`41d880b00fd7bcda810d7078c9865c00dda87ddd6040cb95d7a96b5a5af0b2a8` | 原順序與內容不變；仍在材料化成功後執行。 |
| 原 `reference_place_geometry` | JSON 另列完整身份 | 完整原函式保留。 |

原檔 62691 bytes／SHA `9e03de08c9638a4668cca521dc525f6e63e3e6d862476b6f41ccf60e6fed80b9`；記憶體重建為 62953 bytes／SHA `3f8fe931e88f3a69df3a1720d9ddc5103c246c3312b560a059e87c7c218b12ac`。行尾維持原 LF；不涉及 `current_geometry.c`。

- `!use_current_values` → `!app_assembly_saved_dimensions(...)` → `wanted[i]` 的 `&&` 短路順序不變。即使後面的 wanted 為 false，也不擅自交換 saved-dimensions 的觀察順序。
- owned 查詢失敗仍立即返回 false；owned dimensions 雙值取得成功後，才依序寫 `size_a`、`size_b`。
- 非 owned 分支仍先 bind engineering sources，然後 field 0 → field 1。明示 binding 優先於 definition dimension；任一 provider 失敗即 false。若 field 1 失敗，field 0 已完成的 `size_a` 寫入仍保持原狀，沒有新增局部原子性或復原行為。
- 原本區塊內的 false 改為 helper false，呼叫點立即 false；成功路徑新增 `return true`，再進原 W compute。compute false 仍短路；`place` 為 false 仍不呼叫 place，為 true 才呼叫原 `reference_place_geometry`。
- 沒有新增迴圈、求值、快取或來源解析演算法。新 helper 是 `static`，不擴張公開 API。

## 契約與歷史依據

以下行號均對固定 e9 版本，舊提案的 H 行號 79 已過時；現行 H 正文在 75。

- `公理層.md:75`：H 組裝 K/W、持有執行期狀態、使用 typed graph／候選接口，但不得自行重算可提交幾何。這個 helper 只消費既有權威 provider 回傳尺寸；W 放置策略與 K 計算保持原 owner。
- `公理層.md:1214–1223`（I9）：來源按依賴解析，候選完成前驗每個登記型別的終態，未完成角材不能提交。此次沒有取消任何來源失敗或終態拒絕。
- `geometry-core/domain-decoupling/PRODUCT-ARCHITECTURE.md:176–181` 明列 H reference adapter 透過登記 K/W provider 組裝 placement、member 與其他事實，W 保留策略責任。
- `product-architecture.json` 明列 `geometry-core/references.inc` 為 H，purpose 為 `Host reference definition parsing/rebuild scheduling and K/W source composition`；補丁沒有新增來源檔或改分類。
- `6ea2d3b58e71e100aad1630b751df8ce099eb668` 抽離 member reference／placement 策略並加入薄 wrapper 形狀斷言；`2ba81689dc78005d5347644186049d10e7f56fb3` 加入 typed candidate graph 共用與尺寸來源迴圈；`138595e04282266c2fe860ddbf9b6a9fa4f49070` 再讓 owned 查詢消費 canonical source。這是後加 H 組裝未與原函式邊界分開，不是條文未定案。

`tests/test_geo261_member_reference.py:52–56` 的 `wood_member_reference_compute`／place 委派檢查、原 `assertNotRegex(... for|while ...)` 全保留，:67–68 compute-before-place 斷言也保留。四個回歸測試檔與 W 模組均未修改；所有 18 個既有 W guard controls 與真 bridge 原子交易負控仍由原 suite 執行。獨立第二位 reviewer 已核同一固定基底與補丁，未見阻擋。

## 已完成 before 與後續界線

`before` 的真命令為四個 unittest 模組：member_reference 11、host_authority 18、definition_sources 7、assembly_graph_product 4。共 40 run、39 pass、1 failure、0 error／skip；unittest 32.519 秒、外層 32.762827 秒。唯一失敗為 `MemberReferenceBoundary.test_actual_reference_and_main_consumers_delegate_the_policy`，原 line 56 的禁迴圈斷言命中 `for(`。29 個 receipt-listed 原件 bytes／SHA 全符，HEAD／source／status stable，沒有 timeout、interruption 或 launch error。

after、撤回及恢復結果在本靜態文件形成時尚未核收；後續報告必須取真正完成的 receipt。撤回同一薄函式形狀斷言轉紅，只證明本次責任邊界修復可被原守門偵測，不能把它誇大成新增產品語義或證明所有幾何結果。40 項定向回歸也不取代最新來源全量、瀏覽器、mutation 或產品架構驗收。
