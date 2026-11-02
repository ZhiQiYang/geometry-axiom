#348 dot 11/01 native 逾時補丁只讀採入準備

固定 #348 head `86c8f0bbe68275e2948d3b1959207aba4225e0c7`、main `fca3f1a80f1dab564f5dd4c01c9e1226eaf09e2d`。原留言 ID `6562374661`（2026-11-01T18:54:09Z）全文 SHA256 `ce67285305a18bdde026adf20269ec97a4c54414cbcde446d05e9bc661f69cfb`。抽出的 V1 patch 為 25,791 bytes，SHA256 `6d565611531ab061b051115e762250d14439608578c07b23080dd93c2364e019`，與原文完全一致。

結論：五leaf在目前#348都未包含V1，16個hunk的舊內容與blob身分精確。不能將整包直接套到新main：

| Leaf | #348／main狀態 | 可行採入候選 |
|---|---|---|
| contact_world.c | #348舊blob精確；main已改Fenwick bounds／ordinal介面，整塊context不符 | 正式合流後人工移植plane maximum充分條件快路徑與immutable order；保留main現有fallback／ordinal，不能整檔覆蓋 |
| geo300_contact_order_fast_harness.c | #348五hunk精確；main無檔 | 與產品及Python instrumentation一起採入，保留原collector逐欄位oracle |
| test_geo261_native_kernel.py | #348與main同blob；兩hunk唯一命中 | keyword-only optimized=False，預設仍O0／Od；O2只供明選。六test方法AST不變 |
| test_geo261_timber_capacity_host.py | #348三hunk精確；main無檔 | 原#348完整H7合流後local cached NativeBuild(optimized=True)；八方法AST不變、512/513／fresh replay／token/history不減 |
| test_geo300_contact_order_fast.py | #348五hunk精確；main無檔 | counter、plane組合與六個新增撤回，連同原兩控制；合流後先重核replace_one實際唯一錨點，仍七方法 |

product／harness／fast-suite三檔是配套；共用helper／H7兩檔是配套。main comparator與dot基底instrument錨點不同，不先補假錨點或回退既有優化。快路徑只為同平面真實單一面充分見證；歧義、規模／探測不符仍完整fallback。新增局部order陣列的stack／成本本輪未量，不改16MiB。

受影響gate：真contact全欄位／八組具名0-1-0候選、source/Reading-A與load重建、完整native／strict census、ledger C include閉包、architecture派生來源、512/513與#297正式產品gate。原comment所述120 stale／3retired及expected缺口是舊候選歷史，不能直接當新main結果，也不能手改hash或expected結案。

原H7 T=`256747c5c8f8f8934eeb08ae404dee1f67591508`，outer1142.271674／exit0只保留，本輪不重跑不移標。dot V0完整243/243雖1677.950801秒未逾時，仍exit1，5456pass／2fail／1skip；V1整輪native與123ledger重產均未做。本輪未下載其動態archives核收。dot兩個既有fail保留；R16原紅亦保留，但本次body與7comments沒有R16標籤，沒有自行把它等同這兩fail。

35min／2100s、H7 1200s、batch600s、16MiB全部不變；I33必CAPACITY整筆拒絕、不截斷。不減512/513、fresh replay、preview、undo/redo覆蓋。

下一步：等340真main，由root沿既有列車逐張正式合流、固定新source後，再按上表移植及排原限制正式gates。這輪只存五個唯一source paths（七個存在版本）；current_geometry／references／reference_sources外部呼叫者，以及registry/expected、ledger/architecture與其他NativeBuild消費者列ADDITIONAL_VERIFICATION，沒有擴讀第六leaf。

所有patch apply、編譯／測試／runtime／ledger／architecture／512／成本均UNRUN。沒有改任何source、分支或PR，沒有推送；root維持348 owner。詳細來源／hash／hunk／AST見ADOPTION_PREPARATION.json與HUNK_ANALYSIS.json。
