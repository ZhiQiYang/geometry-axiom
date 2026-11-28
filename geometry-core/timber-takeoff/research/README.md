# U476：R05 F4b S2 研究候選首片

套用基底：PR #472 `19c00180228f6dfdff65684b47160736d2fae7e9`；開工 main `48d5f3887e8cb8d222307db62dbdea287fda8442`。

交付前 #472 前進到 `efe5f471c22ae02b4a83f21571358920b5e55902`，該次只新增 12 個 `.github/evidence/architecture/` 原件，沒有改本片依賴的產品來源。T／P 仍以使用者指定的 19c0018 為測試基底；新 head 另驗套用，不能把原生研究測試寫成已在新 head 全部重跑。後續若更動真正來源，依下述 pins 與 generator 重新對帳。

本片是可執行研究候選。A 及完整 8 替換＋2 新增條文已在 issue #47 的 6794611621 核可，固定基底仍缺 S0 正式落檔。它不註冊 `timber-takeoff-sets/1` 或 `cutting-plan/2`，不接 App、正式專案附件與歷史 owner，不修改《公理層》或現有 `/1` 行為，不提升需求帳產品層級。完整設計與分片見 [本輪設計](https://github.com/ZhiQiYang/geometry-axiom/issues/47#issuecomment-7229522981)。

## 可執行內容

`candidate.cjs` 實作明示同件、逐表示核對、去重件數與長度帳，以及嚴格研究宣告保存、冷開、單步歷史、取消／no-op、revision CAS、undo／redo 和不回退的 itemKey 高水位。研究保存契約及 API 見 [CONTRACT.md](CONTRACT.md)；獨立 Python 裁判、有限窮舉與假設見 [ORACLE.md](ORACLE.md)。

儲存的研究文件只有宣告與來源 pins，沒有 A/B/L、verified、COMPLETE 或租約。模型記號須來自原保存 sourceIdentity；去身分 candidate 的新記號不能補造連續性。每個納入別名都核對，代表無權遮掉其他列失敗。來源相同但分成兩個 itemKey 為 INCOMPLETE；撤銷歸併會恢復原表示列與這個未解決狀態。

文件只選取其明列表示。來源消失的 excluded 仍保留宣告且不產生需求；來源消失的 included 回 INCOMPLETE，不能捏造 0 mm。`observation` 明列可觀測及缺失表示，raw 長度只對當次有數值的表示計算。當全部表示完整時，逐值裁判核對 `raw = excluded + physical + removedAlias`，另驗所有件與 aliases 的精確覆蓋，不能只以總和通過。

`cutting_projection.cjs` 與 `native_cutting_projection.cjs` 把已核研究 items 投影給既有 woodworking 純政策；投影 row.id 是研究用 itemKey，不宣稱為正式 timberId 或正式 `/2`。沒有實作實際採購操作、庫存異動或裁切最優性。

## T 與 P

T 的 `candidate.cjs` 是明確未實作 S2 的研究 scaffold，具實體載入點；CT01 在 `INCOMPLETE` 對 `COMPLETE` 的業務斷言紅。P 替換這個候選及它唯一的架構來源 pin。T 的其餘內容是測試、獨立裁判、原生重現工具、新夾具、說明與新增片段；不覆寫既有 suite、golden 或收據。

```sh
# 只套 T：預期 exit 1，唯一紅為具名斷言，不能把 setup 錯誤算成紅。
node --test --test-reporter=spec --test-name-pattern=U476_CT01_EXPLICIT_ONE_ITEM tests/test_r05_takeoff_study.cjs

# T + P：包括有限集合與獨立 history 模型。
node --test --test-reporter=spec tests/test_r05_takeoff_study.cjs

# 完整原件及具名撤回；每個 child 皆有固定時限。
python3 -B geometry-core/timber-takeoff/research/scan.py --candidate "$PWD/geometry-core/timber-takeoff/research/candidate.cjs" --out /tmp/u476-scan --bounded
python3 -B geometry-core/timber-takeoff/research/withdrawals.py --repo . --out /tmp/u476-constructor-withdrawals
python3 -B geometry-core/timber-takeoff/research/mutations.py --candidate "$PWD/geometry-core/timber-takeoff/research/candidate.cjs" --out /tmp/u476-checker-withdrawals --bounded
```

## 真原生原件

七個 `native_*` 工具可從指定基底既有來源重編 bridge／model-base，經真 producer、每包驗證、歷史 replay、live/input/result 三份原生圖、既有模型存檔往返，產生 single（timber 0）及 independent-control（timber 0、4）。詳見 `tests/fixtures/r05_takeoff_native.provenance.md`。本輪只以 literal A/B 普通已放置 D7 當 native 正例；參數／材料／來源閉包變更的反例另屬明示合成研究域。

```sh
python3 -B geometry-core/timber-takeoff/research/native_reproduce.py --repo . --out /tmp/u476-native --candidate geometry-core/timber-takeoff/research/candidate.cjs --fixture /tmp/u476-native-fixture.json
python3 -B geometry-core/timber-takeoff/research/native_root_withdrawal.py --native-artifacts /tmp/u476-native --out /tmp/u476-native-root-withdrawal
```

重播使用新 host epoch，故原始 incarnation／夾具 bytes 可不同；原件的來源 SHA 與生成命令完整記錄，不手改 pins 讓舊證據過關。fixture 的 sourceInputs 守門比對固定基底的 native／producer／宿主來源 bytes，generatorScripts 另釘研究工具。當 #472 改任何相關既有來源時先重新審查相容性、重跑 generator，再採入新原件；不能只搬本輪 fixture hash。

## 登錄與採納端待辦

新 `node:r05_takeoff_study` 使用自己的 `tests/suites.d` 片段，由 `native_registry.py --init-suite` 生成。expected 保持 `pending-ci-census`；本機結果不是正式成本。套用端依 `tests/FRAGMENTED-REGISTRIES.md` 派發 Native suite measurement，從官方原件匯入真計數／成本後才跑正式全集。pending 被正式守門拒絕是預期的採納依賴，沒有放寬 gate。

每個研究程式使用獨立 exact-hash 架構排除片段；不增加目錄豁免，不把 W/H 政策混入正式 K。architecture／ME／正典閱讀器的衍生收據不在本片手寫，依採納端正式流程重產。本輪不跑 Chromium；本片沒有 App 入口或 canvas 段，不宣稱 L4。

S0 應由維護端採納已核 D49、D54(c)、I59(a)、I62、R47、R48(1)、R50、§四與新增 D⟨T1⟩／I⟨T1⟩。正式 owner、附件白名單、capabilities、完整專案／方案 history、`/2` evaluator／CSV 和 App 接線均等首片套用回覆後另片，無須重問已核 A。
