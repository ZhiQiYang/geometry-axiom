# GEO-261 候選根集合與原生來源綁定修正（Topic 15）

本分支補上產品缺陷：完整性旗標為真，原解碼器仍可能接受漏根／多根／錯誤關聯，以及數值和型別相同卻綁錯身分的 root ref。修正後先由獨立 snapshot 目錄導出完整關聯集合，與 roots 做 exact-set 比較；真正原生程序回應還必須符合本 H adapter 的 provider/key 綁定及 COMPLETE 狀態。

基底 `e9c1509cf89e6f35d298743ec5e3368370316cf7`；測試支援 `21b11b302518f49cda344b834c218b097077b11b`；產品修正 `11b6cb5246eefff4af7f82caf0efd0824998e0ad`。分支 `codex/geo261-fix-root-catalog-20261018`。本報告只認這個修正分支的本題測試，沒有宣稱 integration／全量驗收通過。

## 修改與斷言保留

C snapshot 直接從 canonical parameter store 加入身分目錄 `parameter_fields`（parameterId、fieldId、name）；沒有從 graph roots 倒造 expected，也不把參數運算或第二個 parser 搬入 H。generic 解碼由 placement、solid、spec、parameter field、profile-run/member 五類 snapshot 目錄推導完整 association set，重複目錄身分也拒絕。真正 native loader 固定走私有 native decoder，再驗 H 所有的 `app.model-snapshot` provider/fingerprint/key 與 COMPLETE；沒有可關閉選項或舊快照 fallback。generic 的 opaque key（含 NUL/FF）與 typed INCOMPLETE 仍保留。

依據是 SSOT K/H 分工（opaque key 與公開交換解析）、I31/I32 來源完整後才能構造，以及 R30；這是落實既有契約，不新增條文裁定。修改恰八檔：三個既有 H 產品來源、一份 `MODEL-SOURCES.md` 契約及四測試。對原八檔提案逐 raw hash 核對完全一致。四套原59方法名稱及全部原302個 assertion call AST 均保留，修後65方法／327個 assertion calls；不是放寬斷言。原 `NativeSourceTests` 21方法也保留。

[固定來源與原斷言核對](readonly-review/source-assertion-review.json)、[真 Git 提交／patch 對應](readonly-review/git-artifacts.json)。

## 修前、修後與共同恢復

| 原件 | 測試 SHA | 方法結果 | unittest時間 |
|---|---|---|---:|
| [修前exact-set](before-exact-set/command.stderr) | 21b11b30 | 1方法失敗；7個subTest均`ModelError not raised` | 0.024s |
| [修前native binding](before-native-binding/command.stderr) | 21b11b30 | 1方法1失敗；`ModelError not raised` | 0.008s |
| [修後host/runtime](after-pure/command.stderr) | 11b6cb52 | 43/43，零skip | 10.053s |
| [修後selfbuilding sources](after-native-sources/command.stderr) | 11b6cb52 | 12/12，零skip | 12.936s |
| [修後真default-native](after-default-native/command.stderr) | 11b6cb52 | 10/10，零skip | 22.765s |
| [共同恢復host/runtime](restored-pure/command.stderr) | 11b6cb52 | 43/43，零skip | 5.587s |
| [共同恢復selfbuilding sources](restored-native-sources/command.stderr) | 11b6cb52 | 12/12，零skip | 9.819s |
| [共同恢復真default-native](restored-default-native/command.stderr) | 11b6cb52 | 10/10，零skip | 20.288s |

修後與最終共同恢復各為四套65/65。恢復段是四個控制共用的同來源完整正控制，沒有聲稱每個控制後立即各重跑。以上與下表全部時間僅為功能收據；修前兩段、修後純測及其他段落可能與外部效能建置重疊，不據此比較效能倍率。

[建置原輸出](after-build/command.stdout) 真重建 bridge/model-base，exit0；其後真正 default-native 明設兩條 registry 路徑，每方法前後仍執行原 `require_fresh` 與 source/binary identity 守門。三個 authored scenes 的期望根身分直接取自測試寫下的場景，分別4／3／12個，沒有把 producer roots當唯一oracle。

## 四個單點產品控制

| 控制 | SHA | 真紅結果 | unittest時間 |
|---|---|---|---:|
| [停用完整集合比較](control-exact-set/command.stderr) | 16bdbb00571c015b31d36b1b4add7c4ab5d50971 | 1方法、7個subTest失敗 | 0.013s |
| [停用native binding guard](control-native-binding/command.stderr) | c456b648d23df77b3eafb7a86b4398e087299872 | 2方法、7筆失敗（pure1＋真native6） | 2.304s |
| [公開native caller繞回generic](control-native-caller/command.stderr) | 3af5f08bc524c8fad0d312639d220d08a0cbb38f | 2方法、7筆失敗（pure1＋真native6） | 1.746s |
| [C欄位目錄名稱破壞](control-native-catalog/command.stderr) | 0e0d131ee7e0ac0e7235d6ea323e2ac04dae3729 | 1方法1失敗，三筆名稱不符 | 5.586s |

前三控制的原文均為 `AssertionError: ModelError not raised`。#2/#3 的真原生案例先擷取真 C 正輸出，再僅在負向輸入置換同型 ref／id；frame、region、length各兩種，共6個subTest。第一個真native紅是 profile.frame/ref；generic decode與association set仍相同，失敗出現在應由正式native邊界拒絕的assertRaises。這些控制不是只直接呼叫私有helper，也沒有用`root-catalog-fallback` sentinel充當killer。

#4 由新程序中的 selfbuilding harness 真編譯當前 `model_base.c`；執行exit0、JSON及節點唯一性已過，才於 `test_geo261_model_sources.py:106` 的獨立literal清單失敗：期望name `1/2/3`，實際三筆為`wrong-field-name`。不是編譯/setup失敗。四個控制都只改單點產品，測試bytes不變，真Git diff的hunk與已審四提案一致；未把控制提交混進正式修正。

完整人工分類、argv、時間、原始stream hash及具名錯誤在[人工台帳](readonly-review/manual-ledger.json)。所有13輪的來源／HEAD／status-diff穩定，沒有timeout或launch error；本報告對有效控制的判定來自原stderr和固定diff，不是只看exit1。

## Binary與公開證據界線

Python控制#2/#3不改C/H/INC registry閉包；在新Python process重新載入其source identity後，可合法重用仍通過freshness的相同C binaries。修後、兩控制與最後default-native前後記錄的model-base均929456 bytes、SHA `b26c798e8b3c0643cb496b1620689aa1838518315e70bbb51b5d447aeccdb8e8`；bridge均1078840 bytes、SHA `3e7ee9ec03f04c9238330e45320adae27ca109667e17842825b98cd677561f03`。#4使用另外的臨時自建binary，沒有改寫registry；其當輪registry因C控制顯示stale不構成該測試的fallback。未使用的core可能stale，沒有聲稱全部registry項目fresh。

公開包保留每輪原stdout/stderr/process/receipt、版本資訊、持久binary資料與sidecar，以及六份真Git patch／提交資訊。自建臨時native binary與各內層正常subprocess串流未另封存，不能把外層原文或registry hash冒充全部內層raw。大型`before/after.source.json`與recorder原碼仍保留外部，公開receipt只給其原記錄bytes/hash；無法僅用公開包重算未公開的完整逐檔來源清單。共用collector只核所選原件身份與整理人工claim，不替測試判綠。

環境：Debian GNU/Linux 13.6，Linux 6.18.55 x86_64／glibc2.41，gcc14.2.0，Python3.12.14，Node24.19.0，Google Chrome155.0.8059.84（另裝Chromium154.0.8037.57）；stack16MiB。版本原文在各stage的tool輸出。沒有用Chrome跑本題，版本不表示瀏覽器已驗。

## 未驗項

本題沒有執行全量run_all、六個瀏覽器job或完整mutation集合。四套方法數59→65，最終合流需真更新expected（+6）後再strict full，不能預填綠收據。snapshot及roots若同時被一致偽造，不是本題所證明的密碼學防護；也不把root集合證據等同完整graph edge／definition closure證明。Claude真正合流若採用不同產品bytes仍須依新來源重驗。
